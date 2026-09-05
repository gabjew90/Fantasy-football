"""Projections as an INPUT: external stat lines, scored in league settings.

DECISIONS 2026-09-02 #21 (simplification): the engine's edge is roster-aware
timing -- slots still needed, value against the slot a player fills, value
against what is freely available later, timing against the other rosters.
None of that needs our projections to beat consensus, and the FantasyPros
comparison showed they do not. So the projection layer stops being a model
and becomes an input. Everything downstream is unchanged.

Two sources, one schema:

    sleeper_id · name · pos · team · pts17 · source · as_of · line

  * pts17 is the stat line scored with the league yaml's scoring, as a
    17-game season total -- the convention every source is put on before the
    engine's own `projections.games` (16) scaling is applied ONCE, at the
    end, for everyone. Sleeper's `gp` (18) is a week count and is ignored.
  * `line` is the raw stat dict (Sleeper-style keys) as JSON, kept so the
    number can be audited back to its inputs.

Sources:
  sheet   the FantasyPros draft sheet's position tabs (data/external/
          DraftSheets_2026_*.xlsx, committed read-only). The consensus AVG
          line per player; the high/low expert lines are ignored here. Names
          are resolved to Sleeper ids through the same matcher the market
          table uses.
  sleeper https://api.sleeper.app/projections/nfl/<season>?season_type=
          regular&position[]=POS -- Rotowire's lines, refreshed regularly.
          The source for every draft after this one.

Precedence is the config's order (2026: sheet, then Sleeper for players the
sheet lacks). Every row says which source it came from and when.

Non-starters go to zero (the one tail rule): a player the depth chart lists
behind his position's starters, whom the market also does not rank as a
starter (or does not rank at all), projects 0 whatever his per-game talent.
`contingent_of` names the starter ahead of him so the informational handcuff
column still works. See DECISIONS #21 for the WR caveat.
"""

from __future__ import annotations

import datetime as dt
import json
import logging
import re
from pathlib import Path

import polars as pl

from .consensus import POSITIONS as SLEEPER_POSITIONS
from .consensus import ConsensusUnavailable, fetch_position
from .role import GATED, STARTERS, depth_orders
from .seasondata import score_projection

log = logging.getLogger("draftkit")

LINE_GAMES = 17.0
# Each source's own games convention, MEASURED 2026-09-02 (plan A2 pre-check):
# the source's season line divided by 17 x Sleeper's week-1 line for five
# healthy starters (Gibbs, Allen, Nacua, Bowers, B. Robinson). The sheet and
# ESPN sit at ~0.98 -- full-season totals; Sleeper/Rotowire at ~0.92 -- its
# season line already embeds about one missed game. A source that already
# discounts games is EXCLUDED from the games table's per-row scale (it keeps
# the uniform `games`), so nobody is discounted twice. Five players is thin;
# re-measure when the table is re-derived.
SOURCE_GAMES_CONVENTION = {
    "fantasypros_sheet": {"ratio": 0.98, "already_discounted": False},
    "espn_projections": {"ratio": 0.98, "already_discounted": False},
    "sleeper_rotowire": {"ratio": 0.92, "already_discounted": True},
    # The DraftSheet tab's own PTS (user decision 2026-09-04, DECISIONS #45):
    # the sheet's Zscore Projection, an average of its Aggregate LOW/AVG/HIGH
    # and the ECR tab's Pts. The Aggregate lines are the tab line / 17 x
    # (16 - RISK-tab missed games by ECR rank), so the number is ALREADY a
    # 16-game total less a durability haircut. Basis 16 and discounted, so
    # proj_pts equals the page's number and no games scale touches it twice.
    # basis_games is NOT fixed here: from_sheet reads it off the workbook's
    # Aggregate formula and carries it per row in `pts_basis` (DECISIONS #54)
    "fantasypros_sheet_headline": {"ratio": None, "already_discounted": True},
}
DISCOUNTED_SOURCES = tuple(k for k, v in SOURCE_GAMES_CONVENTION.items() if v["already_discounted"])


def source_basis_expr() -> pl.Expr:
    """Per-row games basis of the `source` column: the season length its
    line is stated on (LINE_GAMES unless the convention table says
    otherwise). projections.external_projection divides by THIS, not by the
    constant, so a source stated on 16 games is not rescaled as if it were 17."""
    expr = pl.lit(LINE_GAMES)
    for name, conv in SOURCE_GAMES_CONVENTION.items():
        if conv.get("basis_games") is not None:
            expr = pl.when(pl.col("source") == name).then(pl.lit(float(conv["basis_games"]))).otherwise(expr)
    # a row that states its own basis (pts_basis) wins over the table
    return pl.coalesce(pl.col("pts_basis"), expr)


SCHEMA = {"sleeper_id": pl.Utf8, "name": pl.Utf8, "pos": pl.Utf8, "team": pl.Utf8,
          "pts17": pl.Float64, "source": pl.Utf8, "as_of": pl.Utf8, "line": pl.Utf8}
# what combine() emits: the schema plus the dispersion across sources (plan A1)
# `pts17_sd` is DISAGREEMENT BETWEEN SOURCES and `n_sources` counts them.
# `pts17_band` is a different quantity: ONE source's own stated uncertainty,
# from a high/low line it publishes alongside its base line. Conflating the
# two would make pts17_sd mean two things and would quietly defeat the
# n_sources >= 2 guard, so the band gets its own column and is null for a
# source that publishes no range.
DISPERSION = {"n_sources": pl.Int64, "pts17_sd": pl.Float64, "pts17_hi": pl.Float64,
              "pts17_lo": pl.Float64, "pts17_band": pl.Float64,
              # not a dispersion: the season length THIS row's pts17 is stated
              # on when the source decides it per workbook (the DraftSheet
              # headline, read off the Aggregate formula: 16 in the 09-02
              # copy, 17 in the 09-04 copy). Null means the source table /
              # LINE_GAMES. Carried here because this is the set of optional
              # per-row columns every path must preserve (DECISIONS #54).
              "pts_basis": pl.Float64}
SCHEMA_COMBINED = {**SCHEMA, **DISPERSION}

# Column layout of each sheet position tab (0-based, after Player, Team).
# The header names repeat ("YDS" twice), so the mapping is positional.
SHEET_COLS = {
    "QB": ["pass_att", "pass_cmp", "pass_yd", "pass_td", "pass_int",
           "rush_att", "rush_yd", "rush_td", "fum_lost"],
    "RB": ["rush_att", "rush_yd", "rush_td", "rec", "rec_yd", "rec_td", "fum_lost"],
    "WR": ["rec", "rec_yd", "rec_td", "rush_att", "rush_yd", "rush_td", "fum_lost"],
    "TE": ["rec", "rec_yd", "rec_td", "fum_lost"],
}


def empty() -> pl.DataFrame:
    return pl.DataFrame(schema=SCHEMA)


def _frame(rows: list[dict], schema: dict | None = None) -> pl.DataFrame:
    schema = schema or SCHEMA
    if not rows:
        return pl.DataFrame(schema=schema)
    keys = set().union(*(r.keys() for r in rows))
    rows = [{k: r.get(k) for k in schema} for r in rows] if keys != set(schema) else rows
    return pl.DataFrame(rows, schema=schema)


# ------------------------------------------------------------------ sheet

def sheet_bump_column(ws_formulas) -> int | None:
    """0-based index of the tab's ROOKIE BUMP column, located by formula shape.

    The sheet adds a per-position rookie adjustment to every projection:

        ppg   = raw scored line / 17
        bump  = IF(rookie, MAX(0, k * (cap - ppg)), 0)     per game
        total = raw scored line + bump * 17

    with k/cap of 0.258/14.9 at RB and 0.28/12.0 at WR, and no bump at QB or
    TE. Reading Excel's own cached product (the `= <T> * 17` column) rather
    than re-deriving it from those constants means a re-published sheet with
    different coefficients is followed automatically, and there is no second
    copy of somebody else's numbers to go stale in this repo.
    """
    for col in range(1, (ws_formulas.max_column or 0) + 1):
        v = ws_formulas.cell(row=3, column=col).value
        if isinstance(v, str) and re.fullmatch(r"=[A-Z]+\d+\*17", v.strip()):
            return col - 1
    return None


def parse_sheet_tab(rows: list[tuple], pos: str, bump_col: int | None = None) -> list[dict]:
    """A player row carries the name; the 'high' and 'low' rows that follow
    are the same expert's own range for him and are ATTACHED to him.

    They used to be skipped. The sheet's own Aggregate tab averages low, base
    and high, so throwing two of the three away meant the loader never
    reproduced the number the spreadsheet itself reports.

    Returns [{name, team, line, line_hi, line_lo, bump}]: the extremes are
    None when absent, and `bump` is the tab's rookie adjustment in season
    points (0.0 for a veteran, None when the column was not located).
    """
    cols = SHEET_COLS[pos]
    out: list[dict] = []
    for r in rows[1:]:
        name = r[0] if len(r) > 0 else None
        named = isinstance(name, str) and name.replace("\xa0", "").replace("Â", "").strip()
        marker = str(r[1]).strip().lower() if len(r) > 1 and isinstance(r[1], str) else ""
        line = {k: float(r[2 + i]) for i, k in enumerate(cols)
                if len(r) > 2 + i and isinstance(r[2 + i], (int, float))}
        if not named:
            # an unnamed row marked high/low belongs to the player above it;
            # anything else is the spacer row (a non-breaking space)
            if marker in ("high", "low") and out and line:
                out[-1][f"line_{marker[:2]}"] = line
            continue
        bump = None
        if bump_col is not None and len(r) > bump_col:
            b = r[bump_col]
            bump = float(b) if isinstance(b, (int, float)) else 0.0
        out.append({"name": name.strip(), "team": r[1] if len(r) > 1 else None,
                    "line": line, "line_hi": None, "line_lo": None, "bump": bump})
    return out


def _sheet_name_key(name) -> str:
    return str(name).replace("\xa0", " ").replace("Â", "").strip()


def parse_draftsheet(rows: list[tuple]) -> dict[str, float]:
    """The DraftSheet tab's PTS per player name: the number the sheet's
    reader sees. The tab lays out several position blocks side by side, each
    headed by a NAME ... PTS row; a block ends at its first blank NAME cell."""
    out: dict[str, float] = {}
    for i, r in enumerate(rows):
        hdr = [str(c).strip() if c is not None else "" for c in r]
        if "NAME" not in hdr:
            continue
        for j, h in enumerate(hdr):
            if h != "NAME" or "PTS" not in hdr[j:]:
                continue
            pts = hdr.index("PTS", j)
            for rr in rows[i + 1:]:
                name = rr[j] if j < len(rr) else None
                if not (isinstance(name, str) and _sheet_name_key(name)):
                    break
                v = rr[pts] if pts < len(rr) else None
                if isinstance(v, (int, float)):
                    out.setdefault(_sheet_name_key(name), float(v))
    return out


# ---- the workbook's own inputs (DECISIONS #54) --------------------------
# Everything the DraftSheet headline is built from, read from the workbook so
# the number can be REPRODUCED under the league's rules rather than copied off
# a page that was rendered under whatever the Scoring tab happened to say.

# Scoring-tab row label -> draftkit scoring key. Yards rows state yards PER
# POINT (inverted below); the three PPR rows must agree (one `rec` key).
_SHEET_SCORING = {"PassYDS": ("pass_yd", True), "RushYDS": ("rush_yd", True), "RecYDS": ("rec_yd", True),
                  "PassTDs": ("pass_td", False), "RushTDS": ("rush_td", False), "RecTDS": ("rec_td", False),
                  "INTS": ("pass_int", False), "FL": ("fum_lost", False), "RB PPR": ("rec", False)}


def sheet_scoring(wb) -> dict:
    """The Scoring tab as a draftkit scoring dict. Informational: the loader
    scores lines with the LEAGUE yaml; this is what the workbook was set to,
    so a difference can be reported instead of silently shipped."""
    if "Scoring" not in wb.sheetnames:
        return {}
    raw: dict[str, float] = {}
    for r in wb["Scoring"].iter_rows(min_row=1, max_row=40, values_only=True):
        if r and isinstance(r[0], str) and len(r) > 1 and isinstance(r[1], (int, float)):
            raw[r[0].strip()] = float(r[1])
    out: dict[str, float] = {}
    for label, (key, invert) in _SHEET_SCORING.items():
        if label in raw:
            out[key] = (1.0 / raw[label] if raw[label] else 0.0) if invert else raw[label]
    for label in ("WR PPR", "TE PPR"):
        if label in raw and "rec" in out and abs(raw[label] - out["rec"]) > 1e-9:
            out[f"rec_{label.split()[0].lower()}"] = raw[label]   # per-position PPR the loader cannot score
    return out


def sheet_updated(wb) -> str | None:
    """The Scoring tab's 'Updated:' date (ISO), the workbook's own as-of."""
    if "Scoring" not in wb.sheetnames:
        return None
    for r in wb["Scoring"].iter_rows(min_row=1, max_row=3, max_col=3, values_only=True):
        if r and isinstance(r[0], str) and r[0].strip().lower().startswith("updated") and len(r) > 1:
            v = r[1]
            if isinstance(v, dt.datetime):
                return v.date().isoformat()
            if isinstance(v, dt.date):
                return v.isoformat()
            if isinstance(v, str) and v.strip():
                return v.strip()[:10]
    return None


def sheet_headline_spec(wf) -> dict:
    """How THIS workbook builds the DraftSheet headline, read off the
    Aggregate tab's formulas (a formulas-mode workbook):

      games       the season length its LOW/AVG/HIGH lines are scaled to,
                  `line / 17 * (games - missed)`: 16 in the 09-02 copy,
                  17 in the 09-04 default copy. Read on EVERY row of every
                  position block and taken by majority, because the 09-04
                  copy has 17 in QB/RB/WR and in one TE row with the other
                  49 TE rows still on 16 (a half-applied template edit);
                  `games_by_pos` says what each block mostly says and
                  `off_basis_positions` names the blocks that disagree with
                  the workbook majority. The loader reproduces every
                  position on the ONE majority basis, so the page's stale
                  block does not become a position tilt on the board;
      avg_form    how the headline averages: `low_avg_high_ecr` (four-way)
                  or `mid_avg_ecr` (mean of low/high, then AVG, then the
                  ECR-slot points, three-way), by majority the same way;
      rank_window per position, how many ECR slots the block ranks for the
                  ECR-slot points (`LARGE($G$3:$G$52, k)` -> 50).

    Raises when the shapes are not recognised: a copy this loader cannot
    read is a loud error, never a silent fallback to the page."""
    from collections import Counter
    ws = wf["Aggregate"]
    rows = list(ws.iter_rows(min_row=1, max_row=160))

    def val(r, c):
        cells = rows[r - 1] if r - 1 < len(rows) else ()
        return getattr(cells[c - 1], "value", None) if c - 1 < len(cells) else None

    width = max((len(r) for r in rows), default=0)
    # each block: its LOW column (row-2 header) and its position (row-3 slot cell, five to the left)
    blocks: list[tuple[str, int]] = []
    pts_cols: dict[int, str] = {}
    for c in range(1, width + 1):
        h = val(2, c)
        if h == "LOW":
            slot = val(3, c - 5)
            pos = "".join(ch for ch in str(slot or "") if ch.isalpha())
            if pos in SHEET_COLS:
                blocks.append((pos, c))
        if isinstance(h, str) and h.endswith("Pts") and h[:-3] in SHEET_COLS:
            pts_cols[c] = h[:-3]
    if not blocks:
        raise ValueError("Aggregate tab: no position blocks with a LOW column found; cannot reproduce the headline")
    games_by_pos: dict[str, float] = {}
    forms: Counter = Counter()
    all_games: Counter = Counter()
    for pos, c in blocks:
        g: Counter = Counter()
        for r in range(3, len(rows) + 1):
            v = val(r, c)
            if isinstance(v, str) and v.startswith("="):
                m = re.search(r"/17\*\((\d+(?:\.\d+)?)-", v)
                if m:
                    g[float(m.group(1))] += 1
            z = val(r, c + 3)          # LOW, AVG, HIGH, then the headline
            if isinstance(z, str) and z.startswith("=") and "AVERAGE(" in z and "ECR!" in z:
                forms["mid_avg_ecr" if z.replace(" ", "").startswith("=AVERAGE(AVERAGE(") else "low_avg_high_ecr"] += 1
        if g:
            games_by_pos[pos] = g.most_common(1)[0][0]
            all_games.update(g)
    if not all_games or not forms:
        raise ValueError("Aggregate tab formulas not recognised (games basis / headline average): "
                         "cannot reproduce the DraftSheet headline from this workbook")
    # one vote per block (three blocks on 17 outvote one on 16 whatever their
    # row counts); a tie between block majorities falls back to row counts
    votes = Counter(games_by_pos.values())
    top = votes.most_common()
    if len(top) > 1 and top[0][1] == top[1][1]:
        games = all_games.most_common(1)[0][0]
    else:
        games = top[0][0]
    windows: dict[str, int] = {}
    for c, pos in pts_cols.items():
        v = val(3, c)
        m = re.search(r"LARGE\(\$[A-Z]+\$(\d+):\$[A-Z]+\$(\d+)", str(v or ""))
        if m:
            windows[pos] = int(m.group(2)) - int(m.group(1)) + 1
    return {"games": games, "avg_form": forms.most_common(1)[0][0],
            "games_by_pos": games_by_pos,
            "off_basis_positions": sorted(p for p, g in games_by_pos.items() if g != games),
            "rank_window": {p: int(windows.get(p, 50 if p in ("QB", "TE") else 100)) for p in SHEET_COLS}}


def sheet_risk(wb) -> dict[str, float]:
    """RISK tab: ECR position slot ('WR14') -> projected missed games."""
    out: dict[str, float] = {}
    for r in wb["RISK"].iter_rows(min_row=1, max_row=1000, max_col=2, values_only=True):
        if r and isinstance(r[0], str) and len(r) > 1 and isinstance(r[1], (int, float)):
            out[r[0].strip()] = float(r[1])
    return out


def sheet_ecr_slots(wb) -> dict[str, str]:
    """ECR tab: player name key -> position slot ('WR14')."""
    out: dict[str, str] = {}
    for r in wb["ECR"].iter_rows(min_row=2, max_row=2000, max_col=5, values_only=True):
        if r and isinstance(r[2], str) and isinstance(r[4], str) and r[2].strip():
            out.setdefault(_sheet_name_key(r[2]), r[4].strip())
    return out


def _slot_number(slot: str | None, pos: str) -> int | None:
    if not slot or not slot.startswith(pos):
        return None
    try:
        return int(slot[len(pos):])
    except ValueError:
        return None


def reproduce_headline(rows: list[dict], slots: dict[str, str], risk: dict[str, float], spec: dict) -> dict[str, float]:
    """The DraftSheet PTS per sleeper_id, rebuilt from the tab lines the way
    the workbook builds it (Aggregate tab, verified cell for cell against
    both 2026 copies in tests/test_sheet_parity.py):

        f        = (games - missed[slot]) / 17
        LOW/AVG/HIGH = scored low / base / high line x f
        ECRpts   = the k-th largest AVG in the position's block, k = the
                   player's own ECR slot, block = slots 1..rank_window (a
                   slot whose player has no tab line counts as 0)
        headline = AVERAGE(LOW, AVG, HIGH, ECRpts)               four-way
                or AVERAGE(AVERAGE(LOW, HIGH), AVG, ECRpts)      three-way

    `rows` are from_sheet's scored tab rows (_base/_lo/_hi in league
    scoring). A player with no ECR slot at his tab position, no RISK entry
    for it, or a slot beyond the block is not on the DraftSheet and gets no
    headline here (from_sheet estimates him at the position's median ratio).
    The workbook's team count, roster and auction settings do not enter:
    they move VBD and PS on the page, never PTS."""
    games, form, windows = float(spec["games"]), spec["avg_form"], spec["rank_window"]
    out: dict[str, float] = {}
    for pos in SHEET_COLS:
        win = int(windows.get(pos, 50))
        by_slot: dict[int, dict] = {}
        for r in rows:
            if r["pos"] != pos:
                continue
            slot = slots.get(_sheet_name_key(r["name"]))
            k = _slot_number(slot, pos)
            if k is None or slot not in risk:
                continue
            by_slot.setdefault(k, {**r, "_k": k, "_missed": float(risk[slot])})
        block = [(by_slot[k]["_base"] / LINE_GAMES * (games - by_slot[k]["_missed"])) if k in by_slot else 0.0
                 for k in range(1, win + 1)]
        ranked = sorted(block, reverse=True)
        for k, r in by_slot.items():
            if k > win:
                continue
            f = (games - r["_missed"]) / LINE_GAMES
            low = (r["_lo"] if r["_lo"] is not None else r["_base"]) * f
            avg = r["_base"] * f
            high = (r["_hi"] if r["_hi"] is not None else r["_base"]) * f
            ecr_pts = ranked[k - 1]
            if form == "mid_avg_ecr":
                out[r["sleeper_id"]] = ((low + high) / 2.0 + avg + ecr_pts) / 3.0
            else:
                out[r["sleeper_id"]] = (low + avg + high + ecr_pts) / 4.0
    return out


def from_sheet(path: Path, scoring: dict, index, as_of: str, line: str = "tab",
               report: dict | None = None) -> tuple[pl.DataFrame, list[str]]:
    """The sheet's consensus lines in the common schema. `index` is a
    SleeperIndex (name, pos, team -> sleeper_id). Returns (frame, unmatched);
    `report`, when given, is filled with what the workbook said about itself.

    line="tab": the position tab's line scored in LEAGUE settings plus the
    rookie bump (the tab's own AVG cell), a 17-game total, source
    `fantasypros_sheet`. line="headline": the DraftSheet tab's PTS, the
    number the sheet's reader sees, REPRODUCED from the tab lines, the ECR
    slots, the RISK haircuts and the workbook's own Aggregate formulas
    (reproduce_headline / sheet_headline_spec), never copied off the page.
    That is what makes a default-settings copy of the workbook usable for a
    league whose settings differ (DECISIONS #54): the league yaml's scoring
    is applied to the lines, and the workbook's team count, roster and
    auction cells do not enter. Source `fantasypros_sheet_headline`, basis
    = the workbook's games (pts_basis). A tab player the DraftSheet does not
    list is brought onto that basis at his position's median headline/tab
    ratio; the count is logged. The as-of is the workbook's 'Updated:' cell
    when it has one.
    """
    if line not in ("tab", "headline"):
        raise ValueError(f"sheet_line must be tab or headline, got {line!r}")
    import openpyxl
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    # a second pass for FORMULAS: the rookie-bump column sits at no fixed
    # letter, and the headline's games basis / average form live in formulas
    wf = openpyxl.load_workbook(path, read_only=True, data_only=False)
    rep = report if report is not None else {}
    upd = sheet_updated(wb)
    if upd:
        as_of = upd
    rep["sheet_as_of"] = as_of
    ss = sheet_scoring(wb)
    rep["sheet_scoring_diffs"] = {k: (v, float(scoring.get(k, 0.0))) for k, v in ss.items()
                                  if abs(v - float(scoring.get(k, 0.0))) > 1e-9}
    spec = risk = slots = None
    if line == "headline":
        for tab in ("ECR", "RISK", "Aggregate"):
            if tab not in wb.sheetnames:
                raise ValueError(f"{path.name} has no {tab} tab; sheet_line: headline is reproduced from it")
        spec, risk, slots = sheet_headline_spec(wf), sheet_risk(wb), sheet_ecr_slots(wb)
        rep["headline_spec"] = spec
    rows, unmatched, bumped = [], [], 0
    for pos in SHEET_COLS:
        bump_col = sheet_bump_column(wf[pos])
        for p in parse_sheet_tab(list(wb[pos].iter_rows(values_only=True)), pos, bump_col):
            sid = index.match(p["name"], pos, p["team"])
            if not sid:
                unmatched.append(f"{p['name']} ({pos})")
                continue
            # the sheet's own number is the scored line PLUS its rookie bump;
            # reading only the line under-projects every rookie by up to 65
            # points against the spreadsheet this source exists to carry
            bump = float(p.get("bump") or 0.0)
            if bump:
                bumped += 1
            base = float(score_projection(p["line"], scoring)) + bump
            # the source's own range, as a one-sigma-equivalent. Population sd
            # of {low, base, high} -- the SAME estimator combine(mode="mean")
            # uses across sources, so the two dispersion numbers are at least
            # on one scale even though they measure different things.
            # the sheet adds the same bump to low, base and high, so it
            # shifts the trio without widening it: the band is unchanged
            lo = float(score_projection(p["line_lo"], scoring)) + bump if p.get("line_lo") else None
            hi = float(score_projection(p["line_hi"], scoring)) + bump if p.get("line_hi") else None
            trio = [x for x in (lo, base, hi) if x is not None]
            band = None
            if len(trio) == 3:
                mu = sum(trio) / 3.0
                band = (sum((x - mu) ** 2 for x in trio) / 3.0) ** 0.5
            rows.append({"sleeper_id": str(sid), "name": p["name"], "pos": pos, "team": p["team"],
                         "pts17": base, "_base": base, "_lo": lo, "_hi": hi,
                         "source": "fantasypros_sheet", "as_of": as_of,
                         "line": json.dumps(p["line"], sort_keys=True),
                         "pts17_band": band, "pts_basis": None})
    if bumped:
        log.info("sheet: rookie bump applied to %d players", bumped)
    if line == "headline":
        games = float(spec["games"])
        hl = reproduce_headline(rows, slots, risk, spec)
        no_headline = 0
        for r in rows:
            r["source"], r["pts_basis"] = "fantasypros_sheet_headline", games
            h = hl.get(r["sleeper_id"])
            if h is None:
                no_headline += 1
                r["pts17"] = None            # estimated below
            else:
                r["pts17"] = h
                # the sheet's range, carried in the headline's own units:
                # the same relative spread around the number it reports
                if r["pts17_band"] is not None and r["_base"] > 0:
                    r["pts17_band"] = r["pts17_band"] * h / r["_base"]
        # A tab player the DraftSheet does not list (no ECR slot at his tab
        # position, or one beyond the block) gets the tab line brought onto
        # the headline's basis by his position's median headline/tab ratio.
        # Leaving him on the 17-game tab basis promoted Ja'Kobi Lane 64 value
        # ranks on the 2026-09-04 build for no reason but the basis.
        ratio: dict[str, float] = {}
        for pos in SHEET_COLS:
            rs = sorted(r["pts17"] / r["_base"] for r in rows
                        if r["pos"] == pos and r["pts17"] is not None and r["_base"] > 0)
            ratio[pos] = rs[len(rs) // 2] if rs else games / LINE_GAMES
        for r in rows:
            if r["pts17"] is None:
                r["pts17"] = r["_base"] * ratio[r["pos"]]
                if r["pts17_band"] is not None:
                    r["pts17_band"] = r["pts17_band"] * ratio[r["pos"]]
        # self-check against the page the workbook rendered: exact when the
        # Scoring tab matches the league, off by the rescoring when it does
        # not (which is the point); the parity tests hold the exact case
        off = set(spec.get("off_basis_positions") or [])
        if off:
            log.warning("sheet: the %s block(s) of the Aggregate tab still carry a %s-game formula while the "
                        "workbook majority is %g; reproduced on %g for every position, so the page's %s numbers "
                        "will read lower than the board's", ",".join(sorted(off)),
                        "/".join(f"{spec['games_by_pos'][p]:g}" for p in sorted(off)), games, games, ",".join(sorted(off)))
        if "DraftSheet" in wb.sheetnames:
            page = parse_draftsheet(list(wb["DraftSheet"].iter_rows(values_only=True)))
            diffs = [abs(hl[r["sleeper_id"]] - page[_sheet_name_key(r["name"])]) for r in rows
                     if r["sleeper_id"] in hl and _sheet_name_key(r["name"]) in page and r["pos"] not in off]
            rep["headline_parity"] = {"compared": len(diffs),
                                      "max_abs_diff": round(max(diffs), 4) if diffs else None,
                                      "over_0_05": sum(1 for d in diffs if d > 0.05),
                                      "skipped_positions": sorted(off)}
        log.info("sheet: DraftSheet headline reproduced for %d players (games %s, %s), %d estimated from "
                 "the tab line at the position's median ratio", len(rows) - no_headline, games,
                 spec["avg_form"], no_headline)
    for r in rows:
        for k in ("_base", "_lo", "_hi"):
            r.pop(k, None)
    return (_frame(rows, {**SCHEMA, "pts17_band": pl.Float64, "pts_basis": pl.Float64})
            .unique(subset="sleeper_id", keep="first"), unmatched)


# ---------------------------------------------------------------- sleeper

def from_sleeper(season: int, scoring: dict, raw_dir: Path, getter=None,
                 ttl: int | None = None) -> pl.DataFrame:
    """Sleeper's season stat lines in the common schema (rows with no stat
    line beyond ADP placeholders are unprojected and left out)."""
    rows = []
    kw = {}
    if getter is not None:
        kw["getter"] = getter
    if ttl is not None:
        kw["ttl"] = ttl
    for pos in SLEEPER_POSITIONS:
        for r in fetch_position(season, pos, raw_dir, **kw):
            stats = r.get("stats") or {}
            line = {k: v for k, v in stats.items()
                    if not k.startswith("adp_") and not k.startswith("pos_adp") and k != "gp"
                    and v is not None}
            if not line:
                continue
            p = r.get("player") or {}
            upd = r.get("updated_at") or r.get("last_modified")
            as_of = (dt.datetime.fromtimestamp(upd / 1000, tz=dt.timezone.utc).date().isoformat()
                     if upd else "")
            rows.append({"sleeper_id": str(r.get("player_id")),
                         "name": " ".join(x for x in (p.get("first_name"), p.get("last_name")) if x) or None,
                         "pos": p.get("position") or pos, "team": r.get("team"),
                         "pts17": float(score_projection(line, scoring)),
                         "source": "sleeper_rotowire", "as_of": as_of,
                         "line": json.dumps(line, sort_keys=True)})
    return _frame(rows).unique(subset="sleeper_id", keep="first")


# ------------------------------------------------------------------- espn

def from_espn(season: int, scoring: dict, raw_dir: Path, id_map: pl.DataFrame, index,
              getter=None, ttl: int | None = None) -> tuple[pl.DataFrame, list[str]]:
    """ESPN's season lines in the common schema (plan A1). Ids resolve through
    the id map's espn_id first, then the same name matcher the market table
    uses; unmatched names are RETURNED. Team is left to the board (the feed
    carries a numeric proTeamId)."""
    from . import espn as E
    from .market import _attach_sleeper_ids
    kw = {}
    if getter is not None:
        kw["getter"] = getter
    if ttl is not None:
        kw["ttl"] = ttl
    parsed = E.parse_players(E.fetch_projections(season, raw_dir, **kw), season)
    if not parsed:
        return empty(), []
    df = pl.DataFrame({"espn_id": [p["espn_id"] for p in parsed], "name": [p["name"] for p in parsed],
                       "pos": [p["pos"] for p in parsed], "team": [None] * len(parsed)},
                      schema={"espn_id": pl.Utf8, "name": pl.Utf8, "pos": pl.Utf8, "team": pl.Utf8})
    df, unmatched = _attach_sleeper_ids(df, index, id_map, via_fp_id=True, id_col="espn_id")
    as_of = E.cache_as_of(raw_dir, season)
    rows = []
    for p, sid in zip(parsed, df["sleeper_id"].to_list()):
        if not sid:
            continue
        rows.append({"sleeper_id": str(sid), "name": p["name"], "pos": p["pos"], "team": None,
                     "pts17": float(score_projection(p["line"], scoring)),
                     "source": "espn_projections", "as_of": as_of,
                     "line": json.dumps(p["line"], sort_keys=True)})
    return _frame(rows).unique(subset="sleeper_id", keep="first"), unmatched


# ------------------------------------------------------------------ union

def _with_dispersion_single(f: pl.DataFrame) -> pl.DataFrame:
    """One source: no cross-source disagreement by construction. Its own band
    is carried through untouched when it published one."""
    for c in ("pts17_band", "pts_basis"):
        if c not in f.columns:
            f = f.with_columns(pl.lit(None, dtype=pl.Float64).alias(c))
    f = f.with_columns(pl.lit(1, dtype=pl.Int64).alias("n_sources"), pl.lit(0.0).alias("pts17_sd"),
                       pl.col("pts17").alias("pts17_hi"), pl.col("pts17").alias("pts17_lo"))
    # a source that already carries pts17_band leaves it mid-frame, so the
    # canonical order is restored explicitly rather than depending on which
    # columns each source happened to supply
    return f.select(list(SCHEMA_COMBINED))


def combine(frames: list[pl.DataFrame], mode: str = "first", scoring: dict | None = None) -> pl.DataFrame:
    """mode 'first': first source wins per player; later sources fill the
    gaps (the 2026 default; byte-identical to before plan A1, plus the four
    dispersion columns at their single-source values).
    mode 'mean': the equal-weight per-stat MEAN of every source that carries
    the player, scored ONCE (`scoring` required); a stat a source omits
    counts as 0 for that source. Because scoring is linear the scored mean
    equals the mean of the per-source pts17, so the dispersion columns are
    the population std / max / min of the per-source scores."""
    frames = [f for f in frames if f.height]
    if mode == "first":
        out = pl.DataFrame(schema=SCHEMA_COMBINED)
        for f in frames:
            add = f.filter(~pl.col("sleeper_id").is_in(out["sleeper_id"].to_list())) if out.height else f
            add = _with_dispersion_single(add)
            out = pl.concat([out, add], how="vertical") if out.height else add
        return out
    if mode != "mean":
        raise ValueError(f"unknown combine mode {mode!r}")
    if scoring is None:
        raise ValueError("combine(mode='mean') needs the league scoring")
    if not frames:
        return pl.DataFrame(schema=SCHEMA_COMBINED)
    allrows = pl.concat(frames, how="vertical")
    out = []
    for sid, g in allrows.group_by("sleeper_id", maintain_order=True):
        sid = sid[0] if isinstance(sid, tuple) else sid
        lines = [json.loads(x) for x in g["line"].to_list()]
        n = len(lines)
        keys = sorted({k for ln in lines for k in ln})
        mean_line = {k: sum(float(ln.get(k, 0.0)) for ln in lines) / n for k in keys}
        scores = [float(score_projection(ln, scoring)) for ln in lines]
        mu = sum(scores) / n
        sd = (sum((s - mu) ** 2 for s in scores) / n) ** 0.5
        first = g.row(0, named=True)
        out.append({"sleeper_id": str(sid),
                    "name": next((x for x in g["name"].to_list() if x), first["name"]),
                    "pos": next((x for x in g["pos"].to_list() if x), first["pos"]),
                    "team": next((x for x in g["team"].to_list() if x), None),
                    "pts17": float(score_projection(mean_line, scoring)),
                    "source": "mean(" + ",".join(sorted(set(g["source"].to_list()))) + ")",
                    "as_of": max((x for x in g["as_of"].to_list() if x), default=""),
                    "line": json.dumps(mean_line, sort_keys=True),
                    "pts_basis": None,
                    "pts_basis": None,
                    "pts_basis": None,
                    "n_sources": n, "pts17_sd": sd, "pts17_hi": max(scores), "pts17_lo": min(scores),
                    # the mean of the sources that published a range. Combining
                    # a within-source band with cross-source disagreement (in
                    # quadrature, say) is a modelling choice and is NOT made
                    # here: the two stay separate columns.
                    "pts17_band": (lambda b: sum(b) / len(b) if b else None)(
                        [float(x) for x in g["pts17_band"].to_list() if x is not None]
                        if "pts17_band" in g.columns else [])})
    return pl.DataFrame(out, schema=SCHEMA_COMBINED)


def load_external(cfg, index, getter=None) -> tuple[pl.DataFrame, dict]:
    """The configured sources, in order, in the common schema. Report says
    what each contributed and what the sheet could not match."""
    p = cfg.get("projections") or {}
    ext = p.get("external") or {}
    scoring = {k: float(v) for k, v in (cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {}).items()}
    if not scoring:
        raise ValueError("league yaml carries no scoring block")
    mode = str(ext.get("combine", "first"))
    frames, report = [], {"sources": [], "sheet_unmatched": [], "espn_unmatched": [], "combine": mode}
    for name in ext.get("sources") or ["sleeper"]:
        if name == "sheet":
            path = Path(cfg.root) / str(ext.get("sheet_path", ""))
            if not path.exists():
                report["sources"].append({"source": "sheet", "rows": 0, "error": f"missing {path.name}"})
                continue
            report["sheet"] = {}
            f, unmatched = from_sheet(path, scoring, index, as_of=str(ext.get("sheet_as_of", "")),
                                      line=str(ext.get("sheet_line", "tab")), report=report["sheet"])
            report["sheet_unmatched"] = unmatched
            if report["sheet"].get("sheet_scoring_diffs"):
                log.warning("sheet: the workbook's Scoring tab differs from the league yaml on %s; "
                            "lines are scored with the league's settings",
                            sorted(report["sheet"]["sheet_scoring_diffs"]))
        elif name == "sleeper":
            try:
                f = from_sleeper(int(cfg["season"]), scoring, cfg.path("raw"), getter=getter)
            except ConsensusUnavailable as e:
                report["sources"].append({"source": "sleeper", "rows": 0, "error": str(e)})
                continue
        elif name == "espn":
            from .espn import EspnUnavailable
            from .ids import load_id_map
            try:
                f, unmatched = from_espn(int(cfg["season"]), scoring, cfg.path("raw"),
                                         load_id_map(cfg.path("raw")), index)
                report["espn_unmatched"] = unmatched
            except EspnUnavailable as e:
                report["sources"].append({"source": "espn", "rows": 0, "error": str(e)})
                continue
        else:
            raise ValueError(f"unknown projection source {name!r}")
        report["sources"].append({"source": name, "rows": f.height,
                                  "as_of": (f["as_of"].drop_nulls().max() if f.height else None)})
        frames.append(f)
    out = combine(frames, mode=mode, scoring=scoring)
    report["total"] = out.height
    return out, report


# -------------------------------------------------------- non-starter rule

def zero_non_starters(df: pl.DataFrame, depth: pl.DataFrame, teams: int,
                      starters: dict | None = None) -> pl.DataFrame:
    """proj_pts -> 0 for players the depth chart lists behind the starters
    AND the market does not rank as a starter (or does not rank at all).
    Adds `contingent_of` (the order-1 player at the same team/position) and
    `non_starter` (bool). df needs sleeper_id, pos, team, ecr, adp, proj_pts.

    Positions with a single ordered depth chart only (role.GATED: QB, RB,
    TE). Sleeper's receiver chart is per slot (LWR/RWR/SWR), so a WR "order"
    is not an overall depth and WR is left alone."""
    st = starters or STARTERS
    dcols = ["sleeper_id", "depth_order"] + (["depth_pos"] if "depth_pos" in depth.columns else [])
    d = df.join(depth.select(dcols), on="sleeper_id", how="left")
    if "depth_pos" not in d.columns:
        d = d.with_columns(pl.col("pos").alias("depth_pos"))
    d = d.with_columns(
        pl.coalesce(pl.col("ecr"), pl.col("adp")).rank(method="ordinal").over("pos").alias("_mkt_rank"))
    starters_expr = pl.col("pos").replace_strict(st, default=None, return_dtype=pl.Int64)
    depth_backup = (pl.col("pos").is_in(list(GATED)) & (pl.col("depth_pos") == pl.col("pos"))
                    & pl.col("depth_order").is_not_null() & (pl.col("depth_order") > starters_expr))
    market_backup = pl.col("_mkt_rank").is_null() | (pl.col("_mkt_rank") > starters_expr * teams)
    gate = depth_backup & market_backup
    # the starter he is contingent on: order 1 at the same team and chart position
    ones = (d.filter((pl.col("depth_order") == 1) & (pl.col("depth_pos") == pl.col("pos")))
              .select("team", "pos", pl.col("name").alias("contingent_of"))
              .unique(subset=["team", "pos"], keep="first"))
    d = d.join(ones, on=["team", "pos"], how="left")
    d = d.with_columns(
        gate.alias("non_starter"),
        pl.when(gate).then(pl.col("contingent_of")).otherwise(None).alias("contingent_of"),
        pl.when(gate & pl.col("proj_pts").is_not_null()).then(0.0).otherwise(pl.col("proj_pts")).alias("proj_pts"),
    )
    return d.drop("_mkt_rank", "depth_order", "depth_pos")


def depth_table(raw_dir: Path) -> pl.DataFrame | None:
    return depth_orders(raw_dir)

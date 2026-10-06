"""Question tools for props: the engine's numbers for one question at a time.

`nfl.py props game` answers with the engine's full prop guide -- right for "break
down KC at MIA", wrong for "is the Kelce over any good?". These tools read the
files the engine already writes for every game it prices (shadow log, betting
card, TD board, ladder, player parameters, fantasy points, the 'if he's out'
scenario logs, and the report's own words for a player's role) and print only
what the question needs:

  player   every line priced for one player, with the engine's read on him
  line     the engine's probability at any line the user names (the ladder)
  best     the research rows for a game (role-shift flags first), or the slate's leads
  matchup  the game frame: spread, total, implied points, weather, designations,
           each team's projected volume

A game is priced once and reused for TTL_MIN minutes (lines move; `--fresh`
re-prices). Every answer carries the snapshot time and the engine's honesty
lines that apply to it -- no row carries a bet label (the model has not shown
it adds anything beside the book's price); anytime TD gets no fair odds; a Questionable player is priced as
playing -- because the engine's contract travels with its numbers, not with a
report.

This module computes no probability. Every number is read from an engine file.
Stdlib plus pandas, and core.fetch only.

It lives in core/, not props/: the installed chat harness unpacks a release
by its OWN copy of the file rules (skill/release.py as of its build), and a
harness built at nfl-v1.0 only knows core/, fantasy/, draftkit/, manager/,
props/engine/ and leagues/. As props/ask.py it was never unpacked, the lock
check failed, and chat ran the vendored nfl-v1.0 (DECISIONS #121).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "props" / "engine" / "scripts"
TTL_MIN = 20

LABEL = {"player_receptions": "catches", "player_reception_yds": "rec yds", "player_rush_yds": "rush yds",
         "player_pass_yds": "pass yds", "player_anytime_td": "anytime TD"}
STAT_ALIASES = {"catches": "catches", "receptions": "catches", "rec": "catches", "recs": "catches",
                "rec yds": "rec yds", "receiving yards": "rec yds", "receiving": "rec yds",
                "rush yds": "rush yds", "rushing yards": "rush yds", "rushing": "rush yds",
                "pass yds": "pass yds", "passing yards": "pass yds", "passing": "pass yds"}
SLEEPER_TO_NFLVERSE = {"LAR": "LA"}
UNVALIDATED = ("No bet labels: the model has not shown it adds anything beside the book's price (the report's first "
               "line quotes the current graded record; labels return only when the model's weight is clearly above "
               "zero), so a gap between them is information, "
               "not an edge -- and a big gap was usually the model missing something. (Catches and receiving "
               "yards ARE calibrated on 2022-25 outcomes -- a model 85% has won about 84-85%; rushing yards nearly so, one "
               "probability band 3.2 points off against a 3-point limit -- so they are not guesses; they are "
               "untested against the book. QB passing yards beat the naive baseline in both test seasons but two "
               "probability bands miss by under a point, so they do not fully pass that test yet.)")
TD_V0_RULE = ("This TD row is anytime_td_v0, the fallback (v1 could not run: no market implied total); it runs "
              "about 1.3 points low on average, so a gap in the book's favour is partly the model's.")
NEW_TEAM_RULE = ("He changed teams: one or two games of new-team evidence, so the book knows his role better "
                 "than the model -- the model's known weak spot, above all for anytime TD.")
TD_RULE = ("Anytime TD (anytime_td_v1, prototype): quote the model, the market and their blend -- no fair "
           "odds and no 'take it at' price; the gap that matters is the blend against the market.")
PASS_YDS_RULE = ("QB passing yards (pass_yds_v0): his receivers' yards in the same simulation times a "
                 "starter's usual share -- right on average and the right width on 2022-25, its edge over "
                 "the no-shrinkage version early-season only (DECISIONS #105).")


class AskError(ValueError):
    """The question cannot be answered as asked; the message says why."""


@dataclass
class AskResult:
    text: str
    data: dict
    record: dict = field(default_factory=dict)
    report_path: None = None

    def render(self, as_json: bool) -> str:
        return json.dumps(self.data, indent=1, default=str) if as_json else self.text


# ------------------------------------------------------------------ runs

def root() -> Path:
    """The session cache's props folder: $NFL_CACHE, else the system temp dir.
    Never $NFL_OUT -- the engine writes a dozen files per game, and that is
    the folder the user downloads from."""
    return Path(os.environ.get("NFL_CACHE") or Path(tempfile.gettempdir()) / "nfl_cache") / "props"


def season_week(season: int | None = None, week: int | None = None) -> tuple[int, int]:
    g = schedule()
    s = season or int(g[g.gameday.notna()].season.max())
    if week:
        return s, int(week)
    gs = g[(g.season == s) & (g.game_type == "REG")]
    unplayed = gs[gs.result.isna()]
    return s, int(unplayed.week.min()) if not unplayed.empty else int(gs.week.max())


def schedule() -> pd.DataFrame:
    from core import fetch as F
    return pd.read_csv(F.schedule(), low_memory=False)


def game_of(team: str, season: int, week: int) -> tuple[str, str]:
    t = SLEEPER_TO_NFLVERSE.get(team, team)
    g = schedule()
    g = g[(g.season == season) & (g.week == week) & (g.game_type == "REG")
          & ((g.away_team == t) | (g.home_team == t))]
    if g.empty:
        raise AskError(f"{team} has no game in {season} week {week} (a bye)")
    return str(g.away_team.iloc[0]), str(g.home_team.iloc[0])


def parse_game(s: str) -> tuple[str, str]:
    if not s or "@" not in s:
        raise AskError(f"a game is AWAY@HOME, not '{s}'")
    a, h = (x.strip().upper() for x in s.split("@", 1))
    return SLEEPER_TO_NFLVERSE.get(a, a), SLEEPER_TO_NFLVERSE.get(h, h)


def slug(season: int, week: int, away: str, home: str) -> str:
    return f"{season}_wk{week:02d}_{away}_{home}"


def _age_min(p: Path) -> float | None:
    if not p.exists():
        return None
    return (dt.datetime.now().timestamp() - p.stat().st_mtime) / 60


def price_game(season: int, week: int, away: str, home: str, *, fresh: bool = False) -> dict:
    """Price the game with the engine unless a run younger than TTL_MIN exists.
    {slug, dir, age_min, ran}. The engine's own error is the AskError's text."""
    d = root()
    s = slug(season, week, away, home)
    log = d / f"shadow_log_{s}.csv"
    age = _age_min(log)
    if not fresh and age is not None and age < TTL_MIN:
        return {"slug": s, "dir": d, "age_min": age, "ran": False}
    d.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(SCRIPTS / "score_game.py"), "--away", away, "--home", home,
           "--season", str(season), "--week", str(week), "--workdir", str(d / "work")]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "NFL_OUT": str(d)})
    wrote = log.exists() and (age is None or _age_min(log) < age)
    if r.returncode == 0 and not wrote:
        # the engine writes its shadow log only when a book posted lines: a
        # clean run without one is "nothing posted", not a failure -- and an
        # older log beside it is out of date, so it is never served
        raise AskError(f"no book has posted player props for {away}@{home} yet (the engine ran and priced "
                       "nothing); `nfl.py status` shows how many lines each game has")
    if r.returncode != 0:
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
        raise AskError(f"the engine could not price {away}@{home} (exit {r.returncode}): " + " / ".join(tail)[:400])
    return {"slug": s, "dir": d, "age_min": _age_min(log), "ran": True}


def price_slate(season: int, week: int, *, fresh: bool = False) -> dict:
    d = root()
    card = d / f"slate_card_{season}_wk{week:02d}.csv"
    runs = d / f"slate_runs_{season}_wk{week:02d}.csv"
    age = _age_min(runs)
    if not fresh and age is not None and age < TTL_MIN:
        return {"dir": d, "age_min": age, "ran": False}
    d.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, str(SCRIPTS / "score_week.py"), "--season", str(season), "--week", str(week),
           "--skip-started", "--workdir", str(d / "work")]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                       env={**os.environ, "NFL_OUT": str(d)})
    if r.returncode != 0 or not runs.exists():
        tail = (r.stderr or r.stdout or "").strip().splitlines()[-3:]
        raise AskError(f"the engine could not price the slate (exit {r.returncode}): " + " / ".join(tail)[:400])
    return {"dir": d, "age_min": _age_min(runs), "ran": True, "card": card}


def _csv(d: Path, name: str) -> pd.DataFrame | None:
    p = d / name
    if not p.exists():
        return None
    try:
        return pd.read_csv(p)
    except (pd.errors.EmptyDataError, ValueError):
        return None


def load(run: dict) -> dict:
    d, s = run["dir"], run["slug"]
    out = {k: _csv(d, f"{k}_{s}.csv") for k in
           ("shadow_log", "betting_card", "bet_card", "td_board", "ladder", "player_params", "fantasy_points",
            "research")}
    rep = d / f"report_{s}.md"
    out["report"] = rep.read_text(encoding="utf-8", errors="replace") if rep.exists() else ""
    out["scenarios"] = {p.stem.rsplit("_out_", 1)[1]: _safe_csv(p)
                        for p in sorted((d / "scenarios").glob(f"shadow_log_{s}_out_*.csv"))}
    return out


def _safe_csv(p: Path) -> pd.DataFrame | None:
    try:
        return pd.read_csv(p)
    except (pd.errors.EmptyDataError, ValueError):
        return None


# ------------------------------------------------------------------ the report's own words

def section(report: str, heading: str, level: int = 2) -> list[str]:
    """The lines under a heading (exact text after the #s), up to the next
    heading of the same or a higher level. [] when the heading is absent."""
    lines = report.splitlines()
    mark = "#" * level + " "
    start = next((i for i, ln in enumerate(lines) if ln.strip() == mark + heading), None)
    if start is None:
        return []
    out = []
    for ln in lines[start + 1:]:
        if re.match(r"^#{1,%d} " % level, ln):
            break
        out.append(ln)
    return out


def player_section(report: str, name: str) -> list[str]:
    """The engine's paragraph on one player: '### Name — SLOT' up to the next heading."""
    lines = report.splitlines()
    start = next((i for i, ln in enumerate(lines) if ln.startswith(f"### {name} — ")), None)
    if start is None:
        return []
    out = [lines[start][4:]]
    for ln in lines[start + 1:]:
        if ln.startswith("#"):
            break
        out.append(ln)
    return [x for x in out if x.strip()]


def headline(report: str) -> str:
    """The report's first bold line: how many lines were priced, and that none carries a bet label."""
    return next((ln for ln in report.splitlines() if ln.startswith("**")), "")


def frame(report: str) -> dict:
    head = section(report, "Game header")
    bullets = []
    for ln in head:
        if ln.startswith("<details>"):
            break
        if ln.startswith("- **"):
            bullets.append(ln[2:])
    teams = []
    for ln_i, ln in enumerate(report.splitlines()):
        m = re.match(r"^## (\S+) \((away|home)\)$", ln)
        if m:
            nxt = next((x for x in report.splitlines()[ln_i + 1:] if x.strip()), "")
            teams.append({"team": m.group(1), "side": m.group(2), "offense": nxt.strip()})
    thesis = next((ln for ln in report.splitlines() if ln.startswith("**Game-script thesis.**")), "")
    title = report.splitlines()[:2] if report else []
    return {"title": " ".join(t.lstrip("# ").strip() for t in title), "bullets": bullets, "teams": teams,
            "thesis": thesis}


# ------------------------------------------------------------------ names

def norm(s: str) -> str:
    s = str(s or "").lower().strip()
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"[-/]", " ", s)
    return " ".join(w for w in s.split() if w not in ("jr", "sr", "ii", "iii", "iv", "v"))


def match(name: str, candidates: list[str]) -> list[str]:
    """Exact normalized name first; else every candidate with the name as a
    whole word (a last name) or, for several words, as a substring."""
    want = norm(name)
    exact = [c for c in candidates if norm(c) == want]
    if exact:
        return list(dict.fromkeys(exact))
    return list(dict.fromkeys(c for c in candidates if want in norm(c).split()
                              or (len(want.split()) > 1 and want in norm(c))))


def team_of(name: str) -> tuple[str, str]:
    """(full name, team) from Sleeper's player table, for a player no priced
    game in the cache names yet."""
    from core import fetch as F
    players = json.loads(F.sleeper_players().read_text(encoding="utf-8"))
    rows: dict[str, list[str]] = {}          # full name -> the team of EVERY active player holding it
    for p in players.values():
        if p.get("team") and p.get("position") in ("QB", "RB", "WR", "TE") and p.get("active"):
            rows.setdefault(p.get("full_name") or "", []).append(p.get("team"))
    hits = match(name, list(rows))
    if not hits:
        raise AskError(f"no active QB/RB/WR/TE named '{name}'")
    both = [(h, t) for h in hits for t in rows[h]]
    if len(both) > 1:
        raise AskError(f"'{name}' matches more than one player: "
                       + ", ".join(f"{h} ({t})" for h, t in both[:6])
                       + ". Use the full name, and --game AWAY@HOME when two share it.")
    return both[0]


def locate(name: str, season: int, week: int, game: str | None, fresh: bool) -> tuple[dict, dict, str]:
    """(run, files, the player's name as the engine writes it)."""
    if game:
        away, home = parse_game(game)
    else:
        # a game already priced this session that names him -- by his FULL
        # name only: a partial one ("Williams") matching the one game priced
        # so far says nothing about the fifteen that are not, so it goes to
        # the league-wide lookup, which lists every match
        found = []
        for p in sorted(root().glob(f"player_params_{season}_wk{week:02d}_*.csv")):
            pp = _safe_csv(p)
            if pp is not None and norm(name) in {norm(x) for x in pp["name"].astype(str)}:
                found.append(p.stem.split(f"_wk{week:02d}_", 1)[1])
        if len(found) == 1:
            away, home = found[0].split("_", 1)
        else:
            full, team = team_of(name)
            away, home = game_of(team, season, week)
    run = price_game(season, week, away, home, fresh=fresh)
    files = load(run)
    names = sorted(set((files["player_params"]["name"].astype(str).tolist() if files["player_params"] is not None else [])
                       + (files["shadow_log"]["player"].astype(str).tolist() if files["shadow_log"] is not None else [])))
    hits = match(name, names)
    if not hits:
        raise AskError(f"the engine priced {away}@{home} but has no lines or role for '{name}' "
                       "(not a priced starter, or no book posted his props)")
    if len(hits) > 1:
        raise AskError(f"'{name}' matches more than one player in {away}@{home}: {', '.join(hits)}")
    return run, files, hits[0]


# ------------------------------------------------------------------ tools

def _when(run: dict, files: dict) -> str:
    sl = files.get("shadow_log")
    snap = str(sl["logged_at_utc"].iloc[0]) if sl is not None and not sl.empty else "unknown"
    src = ", ".join(sorted(set(sl["book"].astype(str)))) if sl is not None and not sl.empty else "no book"
    return (f"prices from {src}, snapshot {snap} ({run['age_min']:.0f} min old; "
            f"{'priced just now' if run['ran'] else '`--fresh` re-prices'})")


def _record(run: dict, what: str) -> dict:
    return {"manifest": {"entries": [{"name": f"props run {run.get('slug', 'slate')}", "source": "props engine",
                                      "status": "fresh" if run["ran"] else "cached",
                                      "age_h": round((run.get("age_min") or 0) / 60, 2), "detail": what}]}}


def _line_row(r, rs: pd.DataFrame | None) -> dict:
    lab = LABEL.get(r.market, r.market)
    out = {"market": lab, "book": r.book, "line": None if pd.isna(r.line) else float(r.line),
           "p_model": round(float(r.p_model), 3), "p_novig_same_side": round(float(r.p_novig), 3),
           "side": r.side, "price": int(r.price) if not pd.isna(r.price) else None,
           "flag": None if pd.isna(r.flag) else r.flag, "model": r.model_state}
    if r.market == "player_anytime_td":
        out.update(td_model=r.td_model, p_market=_f(r.p_market), p_blend=_f(r.p_blend), blend_w=_f(r.blend_w))
    elif rs is not None and len(rs):
        b = rs[(rs.player == r.player) & (rs.market == r.market) & (rs.line == r.line) & (rs.book == r.book)]
        if not b.empty:
            b = b.iloc[0]
            out.update(research_fields(b))
    return out


def research_fields(b) -> dict:
    """One research row (research_*.csv) as the answer's fields."""
    get = lambda k: b[k] if k in b.index else None
    return {"price_over": None if pd.isna(get("price_over")) else int(get("price_over")),
            "price_under": None if pd.isna(get("price_under")) else int(get("price_under")),
            "median": _f(get("median")), "p10": _f(get("p10")), "p90": _f(get("p90")),
            "p_over_model": _f(get("p_over_model")), "p_over_book": _f(get("p_over_book")),
            "implied": _f(get("implied")), "projected": _f(get("projected")),
            "unit": get("unit") if isinstance(get("unit"), str) else None,
            "over_needs": _f(get("over_needs")), "under_needs": _f(get("under_needs")),
            "look": get("look") if isinstance(get("look"), str) else None,
            "preview": get("preview") if isinstance(get("preview"), str) else None,
            "be_over": _f(get("be_over")), "be_under": _f(get("be_under")),
            "last_game": {k: _f(get(k)) for k in ("snap", "snap_base", "ts", "ts_base", "cs", "cs_base",
                                                  "tn", "tn_base", "cn", "cn_base")},
            "backfield": ({k[3:]: _f(get(k)) for k in ("bf_early", "bf_early_base", "bf_passdown", "bf_passdown_base",
                                                        "bf_i5_base", "bf_i5_n", "bf_i5_team")}
                          if get("bf_early") is not None and not pd.isna(get("bf_early")) else None),
            "catch_yards": get("catch_yards") if isinstance(get("catch_yards"), str) else None,
            "carry_yards": get("carry_yards") if isinstance(get("carry_yards"), str) else None,
            "qb_yards": get("qb_yards") if isinstance(get("qb_yards"), str) else None,
            "rush_rec": get("rush_rec") if isinstance(get("rush_rec"), str) else None,
            "flags": get("flags") if isinstance(get("flags"), str) else ""}


def research_text(x: dict, label: str, book: str = "", line=None) -> str:
    """The research fields as one sentence: prices, projection, the two Over
    chances, what the line implies, flags."""
    def odds(a):
        return "—" if a is None else (f"+{a}" if a > 0 else f"{a}")
    ln = "" if line is None else f"{line:g} "
    bits = [f"{ln}{label}" + (f" at {book}" if book else "")
            + f" (O {odds(x.get('price_over'))} / U {odds(x.get('price_under'))})"]
    if x.get("median") is not None:
        bits.append(f"our projection {x['median']:.0f} ({x['p10']:.0f} to {x['p90']:.0f})")
    if x.get("p_over_model") is not None:
        bits.append(f"Over {x['p_over_model']:.0%} model / {x['p_over_book']:.0%} book")
    if x.get("implied") is not None:
        bits.append(f"the line implies {x['implied']:.1f} {x.get('unit') or ''} (we project {x['projected']:.1f})")
    if x.get("unit") and (x.get("be_over") is not None or x.get("be_under") is not None):
        u = x["unit"]
        def side(word, v, be, fmt):     # no price posted is not the same as a search out of range
            if be is None:
                return f"the {word} has no price posted"
            return f"the {word}'s break-even is outside the search range" if v is None else f"the {word} pays " + fmt.format(v=v, u=u)
        bits.append("if the model's numbers are right, at these prices "
                    + side("Over", x.get("over_needs"), x.get("be_over"), "above {v:.1f} {u}") + ", "
                    + side("Under", x.get("under_needs"), x.get("be_under"), "at {v:.1f} {u} or fewer"))
    if x.get("look"):
        bits.insert(0, f"WORTH A LOOK ({x['look']}), not a bet")
    if x.get("preview"):
        bits.append(x["preview"])
    lg = x.get("last_game") or {}
    if lg.get("snap") is not None:
        rush = label == "rush yds"
        share = ("carries", lg.get("cs"), lg.get("cs_base")) if rush else ("targets", lg.get("ts"), lg.get("ts_base"))
        n, nb = (lg.get("cn"), lg.get("cn_base")) if rush else (lg.get("tn"), lg.get("tn_base"))
        pc = lambda v: "—" if v is None else f"{100*v:.0f}%"
        bits.append(f"last game snaps {pc(lg['snap'])} (earlier {pc(lg.get('snap_base'))}), {share[0]} {pc(share[1])}"
                    + ("" if n is None else f" / {n:.0f}")
                    + f" (earlier {pc(share[2])}" + ("" if nb is None else f" / {nb:.1f} a game") + ")")
    bf = x.get("backfield")
    if bf and label in ("rush yds", "catches", "rec yds"):
        pc = lambda v: "—" if v is None else f"{100*v:.0f}%"
        bits.append(f"backfield jobs last game: early-down carries {pc(bf.get('early'))} (earlier "
                    f"{pc(bf.get('early_base'))}), passing-down targets {pc(bf.get('passdown'))} (earlier "
                    f"{pc(bf.get('passdown_base'))}), inside-5 carries {int(bf.get('i5_n') or 0)} of "
                    f"{int(bf.get('i5_team') or 0)}")
    if x.get("catch_yards") and label == "rec yds":
        # once per player: the read is the same on his catches row (DECISIONS #164)
        bits.append(f"catches and yards: {x['catch_yards']}")
    if x.get("carry_yards") and label == "rush yds":
        bits.append(f"carries and yards: {x['carry_yards']}")
    if x.get("rush_rec") and label == "rush yds":
        bits.append(f"rushing + receiving yards: {x['rush_rec']}")
    if x.get("qb_yards") and label == "pass yds":
        bits.append(f"completions and yards: {x['qb_yards']}")
    if x.get("flags"):
        bits.append(f"flags: {x['flags']}")
    return "; ".join(bits)


def _f(v):
    return None if v is None or pd.isna(v) else round(float(v), 3)


def player(name: str, *, season: int | None = None, week: int | None = None, game: str | None = None,
           fresh: bool = False) -> AskResult:
    season, week = season_week(season, week)
    run, files, full = locate(name, season, week, game, fresh)
    sl, pp, fp = files["shadow_log"], files["player_params"], files["fantasy_points"]
    rows = [] if sl is None else [_line_row(r, files["research"]) for r in sl[sl.player == full].itertuples()]
    role = {}
    if pp is not None and not pp[pp.name == full].empty:
        x = pp[pp.name == full].iloc[0]
        role = {"team": x.team, "slot": x.slot, "status": x.status, "questionable": bool(x.questionable),
                "new_team": bool(x.new_team), "prior_team": x.prior_team, "snap_pct": _f(x.snap_pct)}
    pts = {}
    if fp is not None and not fp[fp.player == full].empty:
        x = fp[fp.player == full].iloc[0]
        pts = {k: _f(x[k]) for k in ("median", "p10", "p20", "p80", "p90", "mean", "p_td") if k in x}
    ladder = files["ladder"]
    lad = {}
    if ladder is not None:
        for st, d in ladder[ladder.player == full].groupby("stat"):
            lad[st] = {float(t): round(float(p), 3) for t, p in zip(d.threshold, d.p_at_or_below)}
    # the 'if he's out' runs: how a Questionable teammate's absence moves HIS lines
    moves = []
    for gsis, S in files["scenarios"].items():
        if S is None or sl is None:
            continue
        who = pp[pp.gsis_id == gsis].name.iloc[0] if pp is not None and (pp.gsis_id == gsis).any() else gsis
        if who == full:
            continue
        j = sl[sl.player == full].merge(S[["book", "market", "player", "side", "line", "p_model"]],
                                        on=["book", "market", "player", "side", "line"], suffixes=("", "_out"))
        for r in j.itertuples():
            if abs(r.p_model_out - r.p_model) >= 0.01:
                moves.append({"if_out": who, "market": LABEL.get(r.market, r.market), "side": r.side,
                              "line": None if pd.isna(r.line) else float(r.line),
                              "p_if_he_plays": round(float(r.p_model), 3), "p_if_out": round(float(r.p_model_out), 3)})
    text_role = player_section(files["report"], full)
    rules = [UNVALIDATED]
    if any(r["market"] == "anytime TD" for r in rows):
        rules.append(TD_RULE)
    if any(r["market"] == "pass yds" for r in rows):
        rules.append(PASS_YDS_RULE)
    if any(r.get("td_model") == "anytime_td_v0" for r in rows):
        rules.append(TD_V0_RULE)
    if role.get("new_team"):
        rules.append(NEW_TEAM_RULE)
    if role.get("questionable"):
        rules.append(f"{full} is Questionable: every number is priced as if he plays his normal role, and his "
                     "props void if he sits. Neither case is weighted by how likely he is to play.")
    if any("role up" in (r.get("flags") or "") or "role down" in (r.get("flags") or "") for r in rows):
        rules.append("Role-shift flag: last game his snaps moved while his targets had not caught up. Since "
                     "props-v1.29 the projection already moves his target share for it (the snap-change rule); "
                     "the flag marks a role change worth researching, not a model miss. Before that rule, "
                     "in "
                     "2022-25 that pattern beat (role up) or missed (role down) the model's next-week catches "
                     "projection by about half a catch; whether the book also reacts late is untested.")
    data = {"player": full, "game": run["slug"], "when": _when(run, files), "role": role, "fantasy_points": pts,
            "lines": rows, "ladder": lad, "if_teammate_out": moves, "engine_on_him": text_role, "rules": rules}
    L = [f"{frame(files['report'])['title']} -- {_when(run, files)}", ""]
    L += text_role or [f"{full}" + (f" -- {role.get('slot')}, {role.get('team')}" if role else "")]
    L += [""]
    if pts:
        L.append(f"Fantasy points (PPR, joint simulation): median {pts.get('median'):.1f}, 10th-90th "
                 f"{pts.get('p10'):.1f} to {pts.get('p90'):.1f}" + (f"; scores a TD in {pts['p_td']:.0%}" if pts.get("p_td") is not None else "") + ".")
    if rows:
        L.append("Every line priced for him:")
        for r in rows:
            if r["market"] == "anytime TD":
                L.append(f"- anytime TD at {r['book']} {r['price']:+d}: model {r['p_model']:.0%}, market "
                         f"{(r.get('p_market') or 0):.0%}, blend {(r.get('p_blend') or 0):.0%} "
                         f"({r.get('td_model')})" + (f"; {r['flag']}" if r.get("flag") else "") + ".")
                continue
            if r.get("p_over_model") is not None:
                L.append("- " + research_text(r, r["market"], r["book"], r["line"]) + ".")
            else:
                L.append(f"- {r['line']:g} {r['market']} at {r['book']}: model {r['p_model']:.0%} vs book "
                         f"{r['p_novig_same_side']:.0%} on the {r['side']}" + (f"; {r['flag']}" if r.get("flag") else "") + ".")
    else:
        L.append("No book posted a line for him in this run.")
    if moves:
        L += ["", "If a Questionable teammate sits (the engine's 'if he's out' run):"]
        for m in moves:
            ln = "" if m["line"] is None else f"{m['line']:g} "
            L.append(f"- {m['if_out']} out: {m['side']} {ln}{m['market']} {m['p_if_he_plays']:.0%} -> {m['p_if_out']:.0%}")
    if lad:
        L += ["", "Alternate lines: `nfl.py props line \"" + full + "\" <stat> <line>` (stats: "
              + ", ".join(sorted(lad)) + ")."]
    L += [""] + [f"Rule: {x}" for x in rules]
    return AskResult("\n".join(L) + "\n", data, _record(run, f"props player {full}"))


def line(name: str, stat: str, value: float, *, season: int | None = None, week: int | None = None,
         game: str | None = None, fresh: bool = False) -> AskResult:
    """P(over) / P(under) at a line, from the engine's ladder. A line the
    ladder does not carry is answered with the two it does carry around it --
    never interpolated."""
    st = STAT_ALIASES.get(" ".join(str(stat).lower().replace("_", " ").split()))
    if st is None:
        raise AskError(f"unknown stat '{stat}'; one of: catches, rec yds, rush yds, pass yds")
    season, week = season_week(season, week)
    run, files, full = locate(name, season, week, game, fresh)
    lad = files["ladder"]
    d = None if lad is None else lad[(lad.player == full) & (lad.stat == st)].sort_values("threshold")
    if d is None or d.empty:
        raise AskError(f"the engine has no {st} ladder for {full} (not modelled for his position, or no sims)")
    v = float(value)
    # The ladder holds P(stat <= t) at its thresholds: whole numbers for
    # catches (t = k), half-points for yards (t = k + 0.5, the same P(stat <= k)).
    # So cdf(k) = P(stat <= k) for a whole k is one lookup, and a line reads:
    #   x.5 line      under = cdf(x)
    #   whole line k  under = cdf(k - 1), push = cdf(k) - cdf(k - 1)
    off = 0.0 if st == "catches" else 0.5
    grid = {round(float(t) - off, 6): float(p) for t, p in zip(d.threshold, d.p_at_or_below)}

    def cdf(k):
        return grid.get(round(float(k), 6))

    whole = float(v).is_integer()
    need = [v - 1, v] if whole else [float(int(v // 1))]
    data = {"player": full, "stat": st, "line": v, "when": _when(run, files)}
    head = f"{full}, {st} -- {_when(run, files)}"
    if all(cdf(k) is not None for k in need):
        if whole:
            pu, pp = cdf(v - 1), cdf(v) - cdf(v - 1)
            po = 1 - cdf(v)
            data.update(p_under=round(pu, 3), p_push=round(pp, 3), p_over=round(po, 3))
            txt = (f"{head}\nAt {v:g}: over {po:.0%}, exactly {v:g} (a push) {pp:.0%}, under {pu:.0%} "
                   "(the engine's ladder).")
        else:
            pu = cdf(need[0])
            data.update(p_under=round(pu, 3), p_over=round(1 - pu, 3))
            txt = f"{head}\nAt {v:g}: over {1 - pu:.0%}, under {pu:.0%} (the engine's ladder)."
    else:
        ks = sorted(grid)
        lo = [k for k in ks if k + 0.5 < v][-1:]
        hi = [k for k in ks if k + 0.5 > v][:1]
        near = [(k + 0.5, grid[k]) for k in lo + hi]
        data.update(p_under=None, p_over=None, nearest=[{"line": ln, "p_under": round(pu, 3)} for ln, pu in near])
        txt = (f"{head}\nThe ladder does not carry {v:g}; the nearest lines it does: "
               + "; ".join(f"at {ln:g} over {1 - pu:.0%}, under {pu:.0%}" for ln, pu in near)
               + ". (Not interpolated.)")
    books = files["shadow_log"]
    if books is not None:
        posted = books[(books.player == full) & (books.market.map(LABEL) == st)]
        if not posted.empty:
            txt += " Posted: " + "; ".join(f"{r.book} {r.line:g}" for r in posted.itertuples()) + "."
    txt += f"\nRule: {UNVALIDATED}" + (f"\nRule: {PASS_YDS_RULE}" if st == "pass yds" else "")
    return AskResult(txt + "\n", data, _record(run, f"props line {full} {st} {v:g}"))


def best(game: str | None = None, *, slate: bool = False, market: str | None = None, n: int = 8,
         survival: bool = False, season: int | None = None, week: int | None = None,
         fresh: bool = False) -> AskResult:
    """Research rows, never a bet list. For a game: every priced line with the
    receiving role-shift flags first, then the TD board. For the slate: the
    leads across games (slate_research), flagged rows first."""
    if survival:
        raise AskError("the must-win pick is off: no picks until the record shows the model adds something "
                       "beside the book's price (DECISIONS #142). `props best --slate` gives the research leads.")
    season, week = season_week(season, week)
    mk = None if not market else STAT_ALIASES.get(" ".join(market.lower().replace("_", " ").split()),
                                                  "anytime TD" if "td" in market.lower() else market)
    if slate:
        run = price_slate(season, week, fresh=fresh)
        C = _csv(run["dir"], f"slate_research_{season}_wk{week:02d}.csv")
        if C is None or C.empty:
            raise AskError("the slate run wrote no research rows")
        C = _flagged_first(C)
        if mk:
            C = C[C["market"].map(LABEL) == mk]
        C = C.head(n)
        data = {"scope": "slate", "rows": C.to_dict("records")}
        L = [f"{season} week {week} slate -- run {run['age_min']:.0f} min old"
             + ("" if run["ran"] else "; `--fresh` re-prices every game (minutes)"), ""]
        L += [_research_row_text(r) for r in C.to_dict("records")] or ["- no rows" + (f" for {mk}" if mk else "")]
        L += [f"Rule: {UNVALIDATED}"]
        return AskResult("\n".join(L) + "\n", data, _record(dict(run, slug="slate"), "props best slate"))
    if not game:
        raise AskError("name a game (AWAY@HOME) or pass --slate")
    away, home = parse_game(game)
    run = price_game(season, week, away, home, fresh=fresh)
    files = load(run)
    rs, td = files["research"], files["td_board"]
    if rs is not None and mk:
        rs = rs[rs.market.map(LABEL) == mk]
    rows = [] if rs is None else _flagged_first(rs).head(n).to_dict("records")
    tds = [] if (td is None or (mk and mk != "anytime TD")) else td.head(n).to_dict("records")
    data = {"scope": "game", "game": run["slug"], "when": _when(run, files), "headline": headline(files["report"]),
            "research": rows, "td_board": tds}
    L = [f"{frame(files['report'])['title']} -- {_when(run, files)}", headline(files["report"]), ""]
    L += ["Research rows (receiving role-shift flags first):"] + ([_research_row_text(r) for r in rows]
                                                                 or ["- no priced lines"])
    if tds:
        L += ["", "Anytime TD board:"] + [
            f"- {r['player']} ({r['team']}) {r['book']} {int(r['price']):+d}: model {r['p_model']:.0%}, market "
            f"{r['p_market']:.0%}, blend {r['p_blend']:.0%}"
            + (f"; {r['flag']}" if isinstance(r.get("flag"), str) else "") for r in tds]
        L += [f"Rule: {TD_RULE}"]
    L += [f"Rule: {UNVALIDATED}"]
    return AskResult("\n".join(L) + "\n", data, _record(run, f"props best {away}@{home}"))


def _flagged_first(R: pd.DataFrame) -> pd.DataFrame:
    """Research rows with the receiving role-shift flags first, then by team and player."""
    fl = R["flags"].fillna("") if "flags" in R else pd.Series("", index=R.index)
    return (R.assign(_f=(~fl.str.contains("role up|role down")).astype(int))
             .sort_values(["_f", "team", "player", "market"]).drop(columns="_f"))


def _research_row_text(r: dict) -> str:
    """One research row (a dict from research_*.csv) as a line of text."""
    x = research_fields(pd.Series(r))
    game = f" [{r['game']}]" if r.get("game") else ""
    return f"- {r['player']} ({r['team']}){game}: " + research_text(x, LABEL.get(r["market"], r["market"]),
                                                                    r.get("book", ""), r.get("line"))


def matchup(game: str, *, season: int | None = None, week: int | None = None, fresh: bool = False) -> AskResult:
    season, week = season_week(season, week)
    away, home = parse_game(game)
    run = price_game(season, week, away, home, fresh=fresh)
    files = load(run)
    fr = frame(files["report"])
    q = section(files["report"], "If a Questionable player is out")
    data = {"game": run["slug"], "when": _when(run, files), "frame": fr, "headline": headline(files["report"]),
            "questionable_out": q}
    L = [f"{fr['title']} -- {_when(run, files)}", ""] + [f"- {b}" for b in fr["bullets"]]
    L += [""] + [f"{t['team']} ({t['side']}): {t['offense']}" for t in fr["teams"]]
    if fr["thesis"]:
        L += ["", fr["thesis"]]
    if q:
        L += ["", "If a Questionable player is out:"] + [x for x in q if x.strip()]
    L += ["", headline(files["report"]), f"Rule: {UNVALIDATED}"]
    return AskResult("\n".join(L) + "\n", data, _record(run, f"props matchup {away}@{home}"))

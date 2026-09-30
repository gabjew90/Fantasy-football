"""Game logs: what a player actually did, week by week, and last season.

Usage (fantasy.evidence) says what a player was GIVEN -- snaps, shares. The
box score says what he did with it, and "why did he score so low?" is a box
score question: the 2026-09-28 session answered Vele, Likely, Moore, Worthy
and others by reading nflverse CSVs from the cache by hand, and computed
"half-PPR without the touchdowns" by hand too. This module prints both.

Points are the LEAGUE's scoring (core.scoring over nflverse columns, the
same weights the scenario and the scorecard use); "no TD" is the same
scoring with every touchdown weight set to zero -- what the week was worth
on volume alone. Source: nflverse player_stats_week, regular season only.
A team defense or kicker has no row here and gets no log.
"""

from __future__ import annotations

import pandas as pd

from core import fetch as F
from core.scoring import NFLVERSE_BASE, nflverse_weights, score_frame, unmodelled_keys

LOG_WEEKS = 6
RECEIVING = ("targets", "receptions", "receiving_yards", "receiving_tds")
RUSHING = ("carries", "rushing_yards", "rushing_tds")
PASSING = ("attempts", "completions", "passing_yards", "passing_tds", "passing_interceptions")
LABEL = {"targets": "Tgt", "receptions": "Rec", "receiving_yards": "Rec yds", "receiving_tds": "Rec TD",
         "carries": "Car", "rushing_yards": "Rush yds", "rushing_tds": "Rush TD", "attempts": "Att",
         "completions": "Cmp", "passing_yards": "Pass yds", "passing_tds": "Pass TD", "passing_interceptions": "INT"}


# kicker and team-defense scoring: never part of a skill player's points
# (not "st_": st_td, st_fum_rec and st_ff also score an offensive player's
# returns and special-teams plays, and the note must name them)
NOT_OFFENSE = ("def_", "fgm", "fgmiss", "xpm", "xpmiss", "pts_allow", "blk_kick", "sack", "safe", "int",
               "fum_rec", "ff", "yds_allow", "tkl", "qb_hit", "pass_def")


def not_counted(scoring: dict) -> list[str]:
    """League scoring keys for an OFFENSIVE player that the nflverse columns
    cannot price (yardage bonuses, return yards...): the log's points leave
    them out, so they can sit below the platform's -- said wherever the
    points are shown. Kicker and defense keys are not his and are not listed."""
    return [k for k in unmodelled_keys(scoring) if float(scoring.get(k) or 0) != 0
            and not any(k == p or k.startswith(p) for p in NOT_OFFENSE)]


def columns_for(pos: str | None) -> tuple:
    if pos == "QB":
        return PASSING + ("carries", "rushing_yards", "rushing_tds")
    if pos == "RB":
        return RUSHING + RECEIVING
    return RECEIVING + ("carries", "rushing_yards")


def load(season: int, manifest=None) -> pd.DataFrame:
    d = pd.read_csv(F.nflverse("player_stats_week", season, manifest=manifest), low_memory=False)
    return d[d["season_type"] == "REG"] if "season_type" in d.columns else d


def _weights(scoring: dict, touchdowns: bool = True) -> dict:
    w = nflverse_weights(scoring, base=NFLVERSE_BASE)
    return w if touchdowns else {c: v for c, v in w.items() if not c.endswith("_tds")}


def game_log(stats: pd.DataFrame, gsis: str, pos: str | None, scoring: dict, weeks: int = LOG_WEEKS) -> list[dict]:
    """His last `weeks` games: opponent, the box score columns for his
    position, points in league scoring and points without touchdowns."""
    d = stats[stats["player_id"] == gsis].sort_values("week").tail(weeks)
    if d.empty:
        return []
    pts, no_td = score_frame(d, _weights(scoring)), score_frame(d, _weights(scoring, touchdowns=False))
    cols = [c for c in columns_for(pos) if c in d.columns]
    return [{"week": int(r["week"]), "opp": r.get("opponent_team"),
             **{c: (None if pd.isna(r[c]) else int(r[c])) for c in cols},
             "pts": round(float(p), 1), "pts_no_td": round(float(n), 1)}
            for (_, r), p, n in zip(d.iterrows(), pts, no_td)]


def season_summary(stats: pd.DataFrame, gsis: str, pos: str | None, scoring: dict) -> dict | None:
    """A season in per-game terms: games, points and points without TDs per
    game, and the box score columns per game (touchdowns as totals)."""
    d = stats[stats["player_id"] == gsis]
    if d.empty:
        return None
    n = int(d["week"].nunique())
    cols = [c for c in columns_for(pos) if c in d.columns]
    out = {"season": int(d["season"].iloc[0]), "games": n, "team": d.sort_values("week")["team"].iloc[-1],
           "pts_per_game": round(float(score_frame(d, _weights(scoring)).sum()) / n, 1),
           "pts_no_td_per_game": round(float(score_frame(d, _weights(scoring, touchdowns=False)).sum()) / n, 1)}
    for c in cols:
        tot = float(pd.to_numeric(d[c], errors="coerce").fillna(0).sum())
        out[c] = int(tot) if c.endswith("_tds") or c == "passing_interceptions" else round(tot / n, 1)
    return out


def log_table(log: list[dict], pos: str | None) -> list[str]:
    primary = {"QB": PASSING, "RB": RUSHING}.get(pos, RECEIVING)
    cols = [c for c in columns_for(pos) if log and c in log[0]]
    cols = [c for c in cols if c in primary or any((g.get(c) or 0) for g in log)]
    L = ["| Wk | Opp | " + " | ".join(LABEL[c] for c in cols) + " | Pts | Pts without TDs |",
         "|---" * (len(cols) + 4) + "|"]
    for g in log:
        L.append(f"| {g['week']} | {g.get('opp') or '--'} | "
                 + " | ".join("--" if g.get(c) is None else str(g[c]) for c in cols)
                 + f" | {g['pts']} | {g['pts_no_td']} |")
    return L


def summary_line(s: dict, pos: str | None) -> str:
    primary = {"QB": PASSING, "RB": RUSHING}.get(pos, RECEIVING)
    cols = [c for c in columns_for(pos) if c in s and (c in primary or s.get(c))]
    per = ", ".join(f"{s[c]} {LABEL[c].lower()}" for c in cols if not (c.endswith("_tds") or c == "passing_interceptions"))
    tds = ", ".join(f"{s[c]} {LABEL[c].lower()}" for c in cols if c.endswith("_tds") or c == "passing_interceptions")
    return (f"{s['season']} ({s['team']}): {s['games']} games, {s['pts_per_game']} pts per game "
            f"({s['pts_no_td_per_game']} without TDs); per game {per}; season {tds}.")


# ------------------------------------------------------------------ the full weekly stat line
#
# One table per player: what he was GIVEN (snap share, target / carry share,
# air-yard share, WOPR -- fantasy.evidence, the engine's usage) beside what he
# DID with it (the box score, air yards, aDOT, yards after catch, first
# downs), a row per game and a season row. The 2026-09-30 session: the user
# asked twice for "the full stats", and chat pulled air yards, aDOT and YAC
# from nflverse outside the engine because no command printed them.

STAT_LINE = {
    "REC": {"usage": ("snap_pct", "tgt_share", "ay_share", "wopr", "i10_tgt"),
            "box": ("targets", "receptions", "receiving_yards", "receiving_air_yards", "adot",
                    "receiving_yards_after_catch", "receiving_first_downs", "receiving_tds", "carries",
                    "rushing_yards")},
    # a back: the workload (snap, carry and target share), the goal-line role
    # (carries and targets inside the 10 -- where his touchdowns come from),
    # the rushing (yards per carry, runs of 10+ yards, first downs, EPA per
    # carry: how well the carries went, not just how many) and the receiving
    "RB": {"usage": ("snap_pct", "carry_share", "tgt_share", "i10_car", "i10_tgt"),
           "box": ("carries", "rushing_yards", "ypc", "rushing_10", "rushing_first_downs", "epa_per_carry",
                   "rushing_tds", "targets", "receptions", "receiving_yards", "receiving_yards_after_catch",
                   "receiving_tds")},
    "QB": {"usage": ("snap_pct", "carry_share"),
           "box": ("attempts", "completions", "passing_yards", "passing_air_yards", "passing_tds",
                   "passing_interceptions", "sacks_suffered", "carries", "rushing_yards", "rushing_tds")},
}
SECONDARY = {"REC": ("carries", "rushing_yards")}          # shown only when not all zero
USAGE_LABEL = {"snap_pct": "Snap %", "tgt_share": "Tgt share", "ay_share": "Air-yd share", "wopr": "WOPR",
               "carry_share": "Carry share", "i10_car": "Inside-10 car", "i10_tgt": "Inside-10 tgt"}
USAGE_COUNTS = ("i10_car", "i10_tgt")          # usage that is a count, not a share: summed in the season row
DERIVED = ("adot", "ypc", "epa_per_carry")
FLOAT_BOX = ("rushing_epa",)                  # kept to two decimals, never rounded to a whole number
BOX_LABEL = dict(LABEL, receiving_air_yards="Air yds", adot="aDOT", receiving_yards_after_catch="YAC",
                 receiving_first_downs="1st downs", rushing_first_downs="Rush 1st downs", ypc="YPC",
                 passing_air_yards="Pass air yds", sacks_suffered="Sacked", receiving_yards="Rec yds",
                 rushing_10="10+ yd runs", epa_per_carry="EPA/carry")


def _kind(pos: str | None) -> str:
    return "QB" if pos == "QB" else "RB" if pos == "RB" else "REC"


def _derived(row: dict) -> dict:
    tg, car = row.get("targets") or 0, row.get("carries") or 0
    row["adot"] = None if not tg or row.get("receiving_air_yards") is None else round(row["receiving_air_yards"] / tg, 1)
    row["ypc"] = None if not car or row.get("rushing_yards") is None else round(row["rushing_yards"] / car, 1)
    row["epa_per_carry"] = (None if not car or row.get("rushing_epa") is None
                            else round(row["rushing_epa"] / car, 2))
    return row


def stat_line(stats: pd.DataFrame, gsis: str, pos: str | None, scoring: dict, usage_by_week: dict,
              season_usage: dict | None = None, weeks: int | None = None) -> dict | None:
    """{kind, rows: [per game, oldest first], season: {...}}. A week with
    usage but no box-score row (stats not published yet) keeps its usage and
    shows the box as missing; a week with neither is not a game he played."""
    kind = _kind(pos)
    spec = STAT_LINE[kind]
    d = stats[stats["player_id"] == gsis].sort_values("week") if stats is not None else stats
    have = d is not None and not d.empty
    raw = [c for c in spec["box"] if c not in DERIVED]
    if "epa_per_carry" in spec["box"]:
        raw.append("rushing_epa")                       # read to derive EPA per carry
    box = {}
    if have:
        pts, no_td = score_frame(d, _weights(scoring)), score_frame(d, _weights(scoring, touchdowns=False))
        for (_, r), p, n in zip(d.iterrows(), pts, no_td):
            box[int(r["week"])] = dict({c: (None if c not in r or pd.isna(r[c]) else
                                            round(float(r[c]), 2) if c in FLOAT_BOX else int(round(float(r[c]))))
                                        for c in raw}, opp=r.get("opponent_team"),
                                       pts=round(float(p), 1), pts_no_td=round(float(n), 1))
    # every game of the season by default: the rows add up to the season row,
    # and "the full data" means no early weeks cut off
    wks = sorted(set(box) | {int(w) for w in usage_by_week})
    wks = wks[-weeks:] if weeks else wks
    if not wks:
        return None
    rows = []
    for w in wks:
        # a week with usage but no box row (stats not published yet) keeps every
        # box field, empty -- the same keys every row, for the table and the JSON
        empty = dict({c: None for c in raw}, opp=None, pts=None, pts_no_td=None)
        r = {"week": w, **{m: (usage_by_week.get(w) or {}).get(m) for m in spec["usage"]}, **(box.get(w) or empty)}
        rows.append(_derived(r))
    season = {m: (season_usage or {}).get(m) for m in spec["usage"] if m not in USAGE_COUNTS}
    for m in spec["usage"]:
        if m in USAGE_COUNTS:                           # a count: the season is the sum, not the mean
            season[m] = int(sum((usage_by_week.get(w) or {}).get(m) or 0 for w in usage_by_week))
    if have:
        for c in raw:
            tot = pd.to_numeric(d[c], errors="coerce").fillna(0).sum() if c in d.columns else None
            season[c] = None if tot is None else (round(float(tot), 2) if c in FLOAT_BOX else int(tot))
        season["pts"] = round(float(score_frame(d, _weights(scoring)).sum()), 1)
        season["pts_no_td"] = round(float(score_frame(d, _weights(scoring, touchdowns=False)).sum()), 1)
        season["games"] = int(d["week"].nunique())
    return {"kind": kind, "rows": rows, "season": _derived(season)}


def _fmt(v, col) -> str:
    if v is None:
        return "--"
    if col in USAGE_COUNTS:
        return str(int(v))
    if col in USAGE_LABEL:
        return f"{v:.2f}" if col == "wopr" else f"{100 * v:.0f}"
    if col == "epa_per_carry":
        return f"{v:+.2f}"
    return f"{v:g}" if isinstance(v, float) else str(v)


def stat_line_table(sl: dict) -> list[str]:
    spec = STAT_LINE[sl["kind"]]
    every = sl["rows"] + [sl["season"]]
    box = [c for c in spec["box"] if c not in SECONDARY.get(sl["kind"], ()) or any((r.get(c) or 0) for r in every)]
    cols = list(spec["usage"]) + box
    head = ["Wk", "Opp"] + [USAGE_LABEL.get(c) or BOX_LABEL.get(c, c) for c in cols] + ["Pts", "Pts without TDs"]
    L = ["| " + " | ".join(head) + " |", "|---" * len(head) + "|"]
    for r in sl["rows"]:
        L.append(f"| {r['week']} | {r.get('opp') or '--'} | " + " | ".join(_fmt(r.get(c), c) for c in cols)
                 + f" | {_fmt(r.get('pts'), 'pts')} | {_fmt(r.get('pts_no_td'), 'pts')} |")
    s = sl["season"]
    g = s.get("games")
    L.append(f"| **Season**{f' ({g} g)' if g else ''} | | " + " | ".join(_fmt(s.get(c), c) for c in cols)
             + f" | {_fmt(s.get('pts'), 'pts')} | {_fmt(s.get('pts_no_td'), 'pts')} |")
    return L

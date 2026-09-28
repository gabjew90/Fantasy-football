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


def not_counted(scoring: dict) -> list[str]:
    """League scoring keys the nflverse columns cannot price (yardage
    bonuses, return yards...): the game log's points leave them out, so they
    can sit below the platform's -- said wherever the points are shown."""
    return [k for k in unmodelled_keys(scoring) if float(scoring.get(k) or 0) != 0]


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

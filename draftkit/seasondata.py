"""In-season data layer (season spec Tasks 1-2).

Thin network edge + persistence: NFL schedule/byes/kickoffs (nflverse),
Sleeper weekly projections/stats/league state, points-allowed inputs, and
usage deltas. All decision math lives in weekly.py; everything here is
fetch, normalize, persist — with last-good degradation on failure.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl

from .sleeper import BASE, get_json

ALL_TEAMS = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GBP", "HOU", "IND", "JAC", "KCC", "LAC", "LAR", "LVR", "MIA",
    "MIN", "NEP", "NOS", "NYG", "NYJ", "PHI", "PIT", "SEA", "SFO", "TBB",
    "TEN", "WAS",
}

# nflverse team codes -> the Sleeper-style codes used across draftkit
_TEAM_MAP = {"LA": "LAR", "LV": "LVR", "NO": "NOS", "NE": "NEP", "GB": "GBP",
             "KC": "KCC", "SF": "SFO", "TB": "TBB", "WSH": "WAS", "JAX": "JAC"}

EARLY_DAYS_EXCLUDED = ("Saturday", "Sunday", "Monday")


def _norm_team(code: str) -> str:
    return _TEAM_MAP.get(code, code)


def load_schedule(cfg, season: int) -> pl.DataFrame:
    """Long-format REG schedule: one row per team-game. Cached to parquet."""
    cache = Path(cfg.path("processed")) / f"schedule_{season}.parquet"
    if cache.exists():
        return pl.read_parquet(cache)
    import nflreadpy as nfl

    s = nfl.load_schedules([season]).filter(pl.col("game_type") == "REG")
    rows = []
    for r in s.select("week", "away_team", "home_team", "gameday",
                      "weekday", "gametime").iter_rows(named=True):
        away, home = _norm_team(r["away_team"]), _norm_team(r["home_team"])
        base = {"week": int(r["week"]), "gameday": r["gameday"],
                "weekday": r["weekday"], "gametime": r["gametime"] or ""}
        rows.append({**base, "team": away, "opp": home, "is_home": False})
        rows.append({**base, "team": home, "opp": away, "is_home": True})
    out = pl.DataFrame(rows).select(
        "week", "team", "opp", "gameday", "weekday", "gametime", "is_home"
    )
    out.write_parquet(cache)
    return out


def byes(schedule: pl.DataFrame, week: int) -> set[str]:
    playing = set(schedule.filter(pl.col("week") == week)["team"].to_list())
    return ALL_TEAMS - playing


def early_games(schedule: pl.DataFrame, week: int) -> pl.DataFrame:
    """Games that kick before the weekend — players in them lock early.

    Week 1 of 2026 contains a WEDNESDAY game, so this is schedule-driven,
    never calendar-assumed.
    """
    return schedule.filter(
        (pl.col("week") == week) & ~pl.col("weekday").is_in(EARLY_DAYS_EXCLUDED)
    )

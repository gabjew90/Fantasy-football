"""Week games with real kickoff datetimes (PT), from the nflverse schedule."""

from __future__ import annotations

import polars as pl

from draftkit import seasondata

from .clock import kickoff_pt


def week_games(schedule: pl.DataFrame, week: int) -> list[dict]:
    """Unique games for the week: {'teams': frozenset, 'kickoff': aware-PT dt}."""
    seen, games = set(), []
    wk = schedule.filter(pl.col("week") == week)
    for r in wk.iter_rows(named=True):
        key = frozenset((r["team"], r["opp"]))
        if key in seen:
            continue
        seen.add(key)
        games.append({"teams": key, "kickoff": kickoff_pt(r["gameday"], r["gametime"])})
    games.sort(key=lambda g: g["kickoff"])
    return games


def load(cfg, season: int) -> pl.DataFrame:
    return seasondata.load_schedule(cfg, season)

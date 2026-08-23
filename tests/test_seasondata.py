"""Season data layer — pure logic tested on fixtures, no network."""

import polars as pl

from draftkit.seasondata import _norm_team, byes, early_games

SCHED = pl.DataFrame([
    {"week": 1, "team": "NEP", "opp": "SEA", "gameday": "2026-09-09", "weekday": "Wednesday", "gametime": "19:00", "is_home": False},
    {"week": 1, "team": "SEA", "opp": "NEP", "gameday": "2026-09-09", "weekday": "Wednesday", "gametime": "19:00", "is_home": True},
    {"week": 1, "team": "SFO", "opp": "LAR", "gameday": "2026-09-10", "weekday": "Thursday", "gametime": "20:15", "is_home": False},
    {"week": 1, "team": "LAR", "opp": "SFO", "gameday": "2026-09-10", "weekday": "Thursday", "gametime": "20:15", "is_home": True},
    {"week": 1, "team": "CHI", "opp": "CAR", "gameday": "2026-09-13", "weekday": "Sunday", "gametime": "13:00", "is_home": False},
    {"week": 1, "team": "CAR", "opp": "CHI", "gameday": "2026-09-13", "weekday": "Sunday", "gametime": "13:00", "is_home": True},
    {"week": 2, "team": "CHI", "opp": "GBP", "gameday": "2026-09-20", "weekday": "Sunday", "gametime": "13:00", "is_home": True},
])


def test_team_normalization():
    assert _norm_team("LA") == "LAR"
    assert _norm_team("KC") == "KCC"
    assert _norm_team("JAX") == "JAC"
    assert _norm_team("DET") == "DET"  # unmapped codes pass through


def test_byes_are_missing_teams():
    out = byes(SCHED, 2)
    assert "SEA" in out and "NEP" in out and "CHI" not in out
    # everyone not playing in week 2 is on bye relative to this fixture
    assert "CAR" in out


def test_early_games_include_wednesday():
    e = early_games(SCHED, 1)
    teams = set(e["team"].to_list())
    assert teams == {"NEP", "SEA", "SFO", "LAR"}  # Wed AND Thu, not Sunday
    assert early_games(SCHED, 2).height == 0

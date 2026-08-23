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


# ---- Task 2: fetchers (getter injected, no network) ----

from draftkit.seasondata import injury_map, rival_budgets, score_projection, weekly_projections

SCORING = {"pass_td": 4.0, "pass_yd": 0.04, "rec": 1.0, "rush_yd": 0.1}


def test_projection_scoring_uses_league_settings():
    stats = {"pass_td": 2, "pass_yd": 250, "bonus_rec_te": 1.0}  # unknown keys ignored
    assert score_projection(stats, SCORING) == 2 * 4.0 + 250 * 0.04


def test_placeholder_projections_detected():
    fake = {"1": {"adp_dd_ppr": 1000.0}, "2": {"adp_std": 999.0}}
    out = weekly_projections(SCORING, "2026", 1, getter=lambda url: fake)
    assert out is None  # adp-only payload = projections not published yet


def test_live_projections_scored():
    fake = {"1": {"pass_td": 2.0, "pass_yd": 250.0}, "2": {"rec": 5.0, "rush_yd": 30.0}}
    out = weekly_projections(SCORING, "2026", 1, getter=lambda url: fake)
    assert out == {"1": 18.0, "2": 8.0}


def test_budget_read():
    rosters = [
        {"roster_id": 1, "owner_id": "u1", "settings": {"waiver_budget_used": 37}},
        {"roster_id": 2, "owner_id": "u2", "settings": {}},
    ]
    b = rival_budgets(rosters, budget=100)
    assert b[1] == 63 and b[2] == 100


def test_injury_map():
    players = {"10": {"injury_status": "Questionable"}, "11": {"injury_status": None}, "T1": "junk"}
    m = injury_map(players)
    assert m["10"] == "Questionable" and m.get("11", "") == "" and "T1" not in m

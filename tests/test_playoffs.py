"""Bye-aware playoff Monte Carlo + regime (season spec Task 4)."""

import numpy as np
import pytest

from draftkit.playoffs import regime, simulate_season, team_week_strength

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1}


def _p(pid, pos, team, pts):
    return {"sleeper_id": pid, "pos": pos, "team": team, "weekly": pts}


ROSTER = [
    _p("q1", "QB", "BUF", 20), _p("r1", "RB", "SFO", 15), _p("r2", "RB", "DET", 14),
    _p("r3", "RB", "MIA", 10), _p("w1", "WR", "CIN", 13), _p("w2", "WR", "SEA", 12),
    _p("w3", "WR", "DAL", 9), _p("t1", "TE", "ARI", 8), _p("k1", "K", "PHI", 7),
    _p("d1", "DEF", "HOU", 6), _p("r4", "RB", "NYJ", 5),  # bench
]


def test_bye_zeroes_a_starter():
    full = team_week_strength(ROSTER, byes=set(), slots=SLOTS, flex=2)
    on_bye = team_week_strength(ROSTER, byes={"SFO"}, slots=SLOTS, flex=2)
    # r1 (15) leaves the lineup; bench r4 (5) backfills the flex: net -10
    assert full - on_bye == pytest.approx(10.0)


def test_simulate_monotone_and_locked():
    rng = np.random.default_rng(3)
    # 3-team toy league, 2 remaining weeks, top-1 makes "playoffs"
    strengths = {1: {14: 120.0, 15: 120.0}, 2: {14: 100.0, 15: 100.0}, 3: {14: 80.0, 15: 80.0}}
    matchups = {14: [(1, 2)], 15: [(1, 3)]}
    records = {1: (10, 0), 2: (2, 8), 3: (0, 10)}  # team 1 already clinched on wins
    odds = simulate_season(strengths, matchups, records, playoff_teams=2,
                           sims=300, sigma=20.0, rng=rng,
                           points_for={1: 1400.0, 2: 1100.0, 3: 900.0})
    assert odds[1] > 0.99          # clinched under any simulation
    assert odds[1] >= odds[2] > odds[3]  # 2 holds the tiebreak edge over 3


def test_regime_thresholds():
    cfg = {"regime_safe": 0.85, "regime_comfortable": 0.60, "regime_bubble": 0.25}
    assert regime(0.9, cfg) == "SAFE"
    assert regime(0.7, cfg) == "COMFORTABLE"
    assert regime(0.4, cfg) == "BUBBLE"
    assert regime(0.1, cfg) == "LONGSHOT"

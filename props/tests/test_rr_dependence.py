"""props/tools/rr_dependence.py on worlds with a known answer, before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import rr_dependence as RD  # noqa: E402


def _world(rho_fav=0.0, rho_dog=0.0, n_games=600, seed=0):
    """Backs whose rushing and receiving residuals correlate rho_fav when favoured by 7+ and
    rho_dog when an underdog by 7+, zero elsewhere; PIT uniform (a right-width sum)."""
    rng = np.random.default_rng(seed)
    rows, games = [], []
    for g in range(n_games):
        spread = float(rng.choice([-10.0, -5.0, 0.0, 5.0, 10.0]))
        games.append({"game_id": f"g{g}", "home_team": "H", "spread_line": spread})
        for team, own in (("H", spread), ("A", -spread)):
            rho = rho_fav if own >= 7 else rho_dog if own <= -7 else 0.0
            z1, z2 = rng.normal(size=2)
            rows.append({"season": 2024 + g % 2, "game_id": f"g{g}", "team": team, "rr_pop": True,
                         "mean_rush_model": 60.0, "mean_yds_model": 20.0,
                         "act_rush_yards": 60.0 + 25 * z1,
                         "act_rec_yards": 20.0 + 15 * (rho * z1 + np.sqrt(1 - rho ** 2) * z2),
                         "pit_rr": float(rng.uniform())})
    return pd.DataFrame(rows), pd.DataFrame(games)


def test_spread_is_the_teams_own_and_buckets_have_closed_edges():
    R = pd.DataFrame({"game_id": ["a", "a"], "team": ["H", "A"]})
    g = pd.DataFrame({"game_id": ["a"], "home_team": ["H"], "spread_line": [7.0]})
    assert RD.own_spread(R, g).tolist() == [7.0, -7.0]
    h = pd.DataFrame({"game_id": ["2024-09-08_H_A"], "team": ["A"]})
    gg = pd.DataFrame({"game_id": ["2024_01_A_H"], "gameday": ["2024-09-08"], "away_team": ["A"],
                       "home_team": ["H"], "spread_line": [3.5]})
    assert RD.own_spread(h, gg).tolist() == [-3.5], "the harness id: gameday_home_away"
    b = RD.bucket_of(pd.Series([7.0, 3.0, 2.5, 0.0, -3.0, -7.0, -12.0]))
    assert b.tolist() == ["favoured by 7+", "favoured by 3-7", "within 3", "within 3", "underdog by 3-7",
                          "underdog by 7+", "underdog by 7+"]


def test_independent_draws_read_zero_and_a_script_dependence_is_found_where_it_lives():
    R, g = _world(rho_fav=-0.4)
    out = RD.dependence(R, g, reps=300)
    assert abs(out["pooled"]["corr"]) < 0.15
    fav = out["by_spread"]["favoured by 7+"]
    assert fav["corr_ci"][1] < 0, "the favoured bucket's negative dependence is detected"
    close = out["by_spread"]["within 3"]
    assert close["corr_ci"][0] < 0 < close["corr_ci"][1], "no dependence where there is none"
    assert 0.15 < out["pooled"]["outside_80"] < 0.25, "a right-width sum reads about 20% outside"
    assert set(out["by_season"]) == {2024, 2025} and out["unmatched_spread"] == 0


def test_a_missing_pit_is_left_out_of_the_width_share_not_counted_inside():
    R, g = _world()
    R["pit_rr"] = 0.95                              # every PIT outside the range
    R.loc[R.index[: len(R) // 2], "pit_rr"] = np.nan
    out = RD.dependence(R, g, reps=50)
    assert out["pooled"]["outside_80"] == pytest.approx(1.0), "half missing must not read as 50% outside"

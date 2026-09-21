"""The expected-points model's arithmetic, on frames small enough to check by hand.

The evaluation that says whether the model is any GOOD lives in
scripts/xfp_eval.py and runs against real seasons. These pin the properties
that would corrupt that evaluation silently if they regressed: the spread's
sign, the efficiency cap, goal-line carries never exceeding total carries, and
the blend falling back correctly when one side of it is missing.
"""

from __future__ import annotations

import numpy as np
import polars as pl
import pytest

from manager import xfp

PPR = {"rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1,
       "rush_td": 6.0, "fum_lost": -2.0}


def _carries(rows):
    return pl.DataFrame(rows, schema={"season": pl.Int64, "week": pl.Int64, "game_id": pl.Utf8,
                                      "team": pl.Utf8, "opp": pl.Utf8, "zone": pl.Utf8,
                                      "player_id": pl.Utf8, "yards": pl.Float64,
                                      "td": pl.Float64, "fum": pl.Int8}, orient="row")


def _targets(rows):
    return pl.DataFrame(rows, schema={"season": pl.Int64, "week": pl.Int64, "game_id": pl.Utf8,
                                      "team": pl.Utf8, "opp": pl.Utf8, "zone": pl.Utf8,
                                      "player_id": pl.Utf8, "catch": pl.Float64,
                                      "yards": pl.Float64, "td": pl.Float64, "fum": pl.Int8},
                        orient="row")


POS = pl.DataFrame({"season": [2025] * 3, "player_id": ["rb", "wr", "qb"],
                    "pos": ["RB", "WR", "QB"]})


# ------------------------------------------------------------ touch values

def test_carry_value_is_the_mean_points_per_carry_in_its_zone():
    c = _carries([
        (2025, 1, "g", "A", "B", "out10", "rb", 4.0, 0.0, 0),    # 0.4
        (2025, 1, "g", "A", "B", "out10", "rb", 6.0, 0.0, 0),    # 0.6
        (2025, 1, "g", "A", "B", "in5", "rb", 2.0, 1.0, 0),      # 6.2
        (2025, 1, "g", "A", "B", "in5", "rb", 1.0, 0.0, 1),      # 0.1 - 2 = -1.9
    ])
    v = xfp.touch_values(c, _targets([]), POS, PPR)
    assert v["carry"]["out10"]["pts"] == pytest.approx(0.5)
    assert v["carry"]["in5"]["pts"] == pytest.approx((6.2 - 1.9) / 2)
    assert v["carry"]["in5"]["td_pts"] == pytest.approx(3.0)


def test_a_quarterback_run_does_not_set_the_value_of_a_running_back_carry():
    """Designed QB runs and sneaks score very differently; the framework is a
    running-back model, so they are excluded from the calibration."""
    c = _carries([
        (2025, 1, "g", "A", "B", "in5", "rb", 1.0, 0.0, 0),
        (2025, 1, "g", "A", "B", "in5", "qb", 1.0, 1.0, 0),
    ])
    v = xfp.touch_values(c, _targets([]), POS, PPR)
    assert v["carry"]["in5"]["n"] == 1
    assert v["carry"]["in5"]["pts"] == pytest.approx(0.1)


def test_target_value_counts_the_catch_point_and_is_split_by_position():
    t = _targets([
        (2025, 1, "g", "A", "B", "out10", "wr", 1.0, 10.0, 0.0, 0),   # 2.0
        (2025, 1, "g", "A", "B", "out10", "wr", 0.0, 0.0, 0.0, 0),    # 0.0
        (2025, 1, "g", "A", "B", "out10", "rb", 1.0, 5.0, 0.0, 0),    # 1.5
    ])
    v = xfp.touch_values(_carries([]), t, POS, PPR)
    assert v["target"]["WR"]["pts"] == pytest.approx(1.0)
    assert v["target"]["RB"]["pts"] == pytest.approx(1.5)


# ------------------------------------------------------------------ lines

def test_the_spread_sign_gives_the_favourite_the_larger_implied_total():
    """nflverse spread_line is positive when the HOME side is favoured. Get
    this backwards and every favourite is projected to throw more."""
    s = pl.DataFrame({"season": [2025], "week": [1], "game_id": ["g"], "game_type": ["REG"],
                      "home_team": ["H"], "away_team": ["A"],
                      "spread_line": [7.0], "total_line": [45.0]})
    L = {r["team"]: r for r in xfp.team_lines(s).iter_rows(named=True)}
    assert L["H"]["implied"] == pytest.approx(26.0) and L["H"]["tspread"] == 7.0
    assert L["A"]["implied"] == pytest.approx(19.0) and L["A"]["tspread"] == -7.0


def test_the_volume_regression_recovers_known_coefficients():
    rng = np.random.default_rng(0)
    n = 400
    implied = rng.uniform(15, 30, n)
    spread = rng.uniform(-10, 10, n)
    teams = [f"T{i}" for i in range(n)]
    lines = pl.DataFrame({"season": [2025] * n, "week": [1] * n, "team": teams,
                          "implied": implied, "tspread": spread})
    tv = pl.DataFrame({"season": [2025] * n, "week": [1] * n, "team": teams,
                       "carries": 20 + 0.1 * implied + 0.5 * spread,
                       "targets": 30 + 0.4 * implied - 0.6 * spread,
                       "in5": np.ones(n), "z6_10": np.ones(n)})
    co = xfp.fit_volume(tv, lines)
    assert co["carries"] == pytest.approx([20, 0.1, 0.5], abs=1e-6)
    assert co["targets"] == pytest.approx([30, 0.4, -0.6], abs=1e-6)


# ------------------------------------------------------------------ blend

@pytest.mark.parametrize("cur,n,pri,k,expect", [
    (0.5, 30.0, 0.2, 30.0, 0.35),     # equal weight
    (None, 0.0, 0.2, 30.0, 0.2),      # no current evidence: the prior
    (0.5, 30.0, None, 30.0, 0.5),     # no prior (rookie): the observation
    (0.5, 0.0, 0.2, 30.0, 0.2),       # zero current opportunity counts as none
])
def test_the_blend_falls_back_when_either_side_is_missing(cur, n, pri, k, expect):
    d = pl.DataFrame({"c": [cur], "n": [n], "p": [pri], "k": [k]},
                     schema={"c": pl.Float64, "n": pl.Float64, "p": pl.Float64, "k": pl.Float64})
    got = d.select(xfp._blend(pl.col("c"), pl.col("n"), pl.col("p"), pl.col("k")))[0, 0]
    assert got == pytest.approx(expect)


# ---------------------------------------------------------------- project

def _one_team_world(in5_share_cur=0.9):
    """One RB on team A, a prior season and one current week."""
    keys = {"team": ["A"], "player_id": ["rb"]}
    pg_pri = pl.DataFrame({"season": [2025], "week": [1], **keys,
                           "carries": [15], "in5": [1], "z6_10": [1], "targets": [4]})
    tv_pri = pl.DataFrame({"season": [2025], "week": [1], "team": ["A"],
                           "carries": [25], "in5": [2], "z6_10": [2], "targets": [35]})
    pg_cur = pl.DataFrame({"season": [2026], "week": [1], **keys,
                           "carries": [5], "in5": [int(in5_share_cur * 10)], "z6_10": [0],
                           "targets": [2]})
    tv_cur = pl.DataFrame({"season": [2026], "week": [1], "team": ["A"],
                           "carries": [25], "in5": [10], "z6_10": [2], "targets": [35]})
    played = lambda s: pl.DataFrame({"season": [s], "week": [1], **keys})  # noqa: E731
    lines = pl.DataFrame({"season": [2026], "week": [2], "game_id": ["g"], "team": ["A"],
                          "opp": ["B"], "implied": [24.0], "tspread": [3.0]})
    coefs = {"carries": [25, 0, 0], "targets": [35, 0, 0], "in5": [2, 0, 0], "z6_10": [2, 0, 0]}
    values = {"carry": {z: {"pts": 1.0, "td_pts": 0.5} for z in xfp.ZONES},
              "target": {p: {"pts": 1.5, "td_pts": 0.3} for p in xfp.POSITIONS}}
    pos = pl.DataFrame({"season": [2026], "player_id": ["rb"], "pos": ["RB"]})
    return dict(week_lines=lines, coefs=coefs, values=values, pg_cur=pg_cur, tv_cur=tv_cur,
                played_cur=played(2026), pg_pri=pg_pri, tv_pri=tv_pri,
                played_pri=played(2025), pos=pos)


def test_goal_line_carries_never_exceed_total_carries():
    """Zone shares are estimated independently of the total, so on a tiny
    sample a back can be projected more goal-line carries than carries. The
    outside-10 remainder must bottom out at zero, not go negative and
    subtract points."""
    w = _one_team_world(in5_share_cur=1.0)
    p = xfp.project(**w, k=1.0)
    assert p["x_out10"].min() >= 0.0


@pytest.mark.parametrize("talent,matchup,expect", [
    (1.5, 1.5, 1.10), (0.5, 0.5, 0.90), (1.05, 1.02, 1.071)])
def test_efficiency_moves_the_projection_at_most_ten_percent(talent, matchup, expect):
    """The framework's guard: noisy efficiency must not override role."""
    w = _one_team_world()
    t = pl.DataFrame({"player_id": ["rb"], "talent": [talent]})
    m = pl.DataFrame({"opp": ["B"], "pos": ["RB"], "matchup": [matchup]})
    p = xfp.project(**w, talent=t, matchup=m)
    assert p["eff_mult"][0] == pytest.approx(expect)
    assert p["xfp"][0] == pytest.approx(p["xfp_base"][0] * expect)


def test_a_larger_prior_weight_pulls_the_share_back_toward_last_season():
    w = _one_team_world()
    near = xfp.project(**w, k=1.0)["s_carries"][0]      # ~ this season: 5/25 = 0.20
    far = xfp.project(**w, k=10_000.0)["s_carries"][0]   # ~ last season: 15/25 = 0.60
    assert near == pytest.approx(0.2, abs=0.02)
    assert far == pytest.approx(0.6, abs=0.01)


def test_fantasy_points_use_the_league_scoring():
    s = pl.DataFrame({"receptions": [5], "receiving_yards": [60.0], "receiving_tds": [1],
                      "rushing_yards": [40.0], "rushing_tds": [0], "rushing_fumbles_lost": [1],
                      "receiving_fumbles_lost": [0], "passing_yards": [0.0], "passing_tds": [0],
                      "passing_interceptions": [0]})
    # 5 + 6 + 6 + 4 - 2
    assert s.select(xfp.fantasy_points(s, PPR))[0, 0] == pytest.approx(19.0)

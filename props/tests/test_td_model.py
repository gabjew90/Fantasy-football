"""Layer 1 of the touchdown model: team TD distributions and channels.

These pin what the layer-1 backtest depends on to be honest: channels that are
exclusive and exhaustive, zero-touchdown games that are counted rather than
silently dropped, distributions that sum to one, a dispersion fit that
actually reports Poisson when the data are Poisson, and the spread's sign.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

pd = pytest.importorskip("pandas")
import td_model as T  # noqa: E402


def _pbp(rows):
    cols = ["game_id", "season", "week", "season_type", "posteam", "defteam", "td_team",
            "touchdown", "pass_touchdown", "rush_touchdown", "yardline_100",
            "rusher_player_id", "play_type"]
    return pd.DataFrame(rows, columns=cols)


# ------------------------------------------------------------------ channels

def test_every_touchdown_lands_in_exactly_one_channel():
    rows = [
        ("g", 2025, 1, "REG", "A", "B", "A", 1, 0, 1, 1, "qb1", "run"),     # QB sneak
        ("g", 2025, 1, "REG", "A", "B", "A", 1, 0, 1, 3, "rb1", "run"),     # rush inside 5
        ("g", 2025, 1, "REG", "A", "B", "A", 1, 0, 1, 40, "rb1", "run"),    # rush from distance
        ("g", 2025, 1, "REG", "A", "B", "A", 1, 1, 0, 12, None, "pass"),    # red-zone pass
        ("g", 2025, 1, "REG", "A", "B", "A", 1, 1, 0, 55, None, "pass"),    # explosive pass
        ("g", 2025, 1, "REG", "A", "B", "B", 1, 0, 0, 30, None, "pass"),    # pick-six by B
        ("g", 2025, 1, "REG", "A", "B", None, 0, 0, 0, 30, None, "pass"),   # not a TD
        ("g", 2025, 1, "POST", "A", "B", "A", 1, 1, 0, 5, None, "pass"),    # playoffs: excluded
    ]
    got = T.classify_tds(_pbp(rows), qb_ids={"qb1"})
    assert got["channel"].tolist() == ["qb_rush", "rush_in5", "rush_far",
                                       "pass_rz", "pass_far", "dst_other"]
    # the pick-six belongs to the team that SCORED it, not the offence
    assert got.iloc[-1]["team"] == "B"


def test_a_quarterback_sneak_is_a_qb_rush_even_from_the_one():
    """Channel order matters: a QB rush from the 1 must not be filed as a
    running back's goal-line carry, or rush_in5 absorbs every sneak."""
    rows = [("g", 2025, 1, "REG", "A", "B", "A", 1, 0, 1, 1, "qb1", "run")]
    assert T.classify_tds(_pbp(rows), {"qb1"})["channel"].item() == "qb_rush"


# ---------------------------------------------------------------- team games

def _sched():
    return pd.DataFrame({"game_id": ["g"], "season": [2025], "week": [1], "game_type": ["REG"],
                         "home_team": ["H"], "away_team": ["A"], "home_score": [24],
                         "away_score": [3], "spread_line": [7.0], "total_line": [45.0]})


def test_a_team_that_scores_no_touchdowns_is_a_row_with_zero_not_a_missing_row():
    """Dropping shutouts would bias every mean upward and every CRPS with it."""
    tds = pd.DataFrame({"game_id": ["g"] * 3, "season": [2025] * 3, "week": [1] * 3,
                        "team": ["H"] * 3, "channel": ["rush_in5", "pass_rz", "pass_far"]})
    tg = T.team_games(_sched(), tds).set_index("team")
    assert tg.loc["H", "tds"] == 3 and tg.loc["A", "tds"] == 0


def test_the_favourite_gets_the_larger_implied_total():
    tg = T.team_games(_sched(), pd.DataFrame(columns=["game_id", "season", "week", "team", "channel"]))
    tg = tg.set_index("team")
    assert tg.loc["H", "implied"] == pytest.approx(26.0)
    assert tg.loc["A", "implied"] == pytest.approx(19.0)


# ------------------------------------------------------------- distributions

@pytest.mark.parametrize("r", [None, 2.0, 50.0])
def test_every_distribution_row_sums_to_one(r):
    pmf = T.count_pmf([0.5, 2.5, 6.0], r)
    assert pmf.sum(axis=1) == pytest.approx([1, 1, 1])


def test_a_huge_dispersion_parameter_is_poisson():
    assert T.count_pmf([2.5], 1e7) == pytest.approx(T.count_pmf([2.5]), abs=1e-6)


def test_crps_is_zero_for_a_certain_correct_forecast_and_grows_with_distance():
    certain_two = np.zeros((1, T.MAX_TD + 1)); certain_two[0, 2] = 1.0
    assert T.crps_count(certain_two, [2])[0] == pytest.approx(0.0)
    assert T.crps_count(certain_two, [4])[0] > T.crps_count(certain_two, [3])[0] > 0


def test_the_dispersion_fit_reports_poisson_when_the_data_are_poisson():
    """The framework asserts touchdowns are overdispersed. The fit must be able
    to say 'no', or the backtest would confirm the assumption by construction."""
    rng = np.random.default_rng(0)
    mu = rng.uniform(1.5, 3.5, 4000)
    y = rng.poisson(mu)
    r = T.fit_dispersion(mu, y)
    assert r is None or r > 100


def test_the_dispersion_fit_finds_overdispersion_when_it_is_there():
    rng = np.random.default_rng(1)
    mu = rng.uniform(1.5, 3.5, 4000)
    r_true = 4.0
    y = rng.negative_binomial(r_true, r_true / (r_true + mu))
    assert T.fit_dispersion(mu, y) == pytest.approx(r_true, rel=0.35)


# -------------------------------------------------------------------- ratios

def test_the_ratio_shrinks_toward_the_league_by_a_points_pseudo_count():
    hist = pd.DataFrame({"team": ["A", "B"], "tds": [10, 2], "points": [70, 70]})
    by, league = T.ratios(hist, k_points=70)
    assert league == pytest.approx(12 / 140)
    # A: (10 + 70 * 12/140) / (70 + 70)
    assert by["A"] == pytest.approx((10 + 6) / 140)
    _, lg = T.ratios(hist, None)
    assert lg == pytest.approx(league)


def test_channel_shares_sum_to_one_and_shrink_toward_the_league_mix():
    hist = pd.DataFrame({"team": ["A", "B"], **{c: [0, 0] for c in T.CHANNELS}})
    hist.loc[0, "pass_far"] = 4
    hist.loc[1, "rush_in5"] = 4
    shares, league = T.channel_shares(hist, alpha=4.0)
    assert shares.sum(axis=1).to_numpy() == pytest.approx([1.0, 1.0])
    assert league["pass_far"] == pytest.approx(0.5)
    # A saw only explosive passes; with alpha = its own sample, halfway to league
    assert shares.loc["A", "pass_far"] == pytest.approx((4 + 4 * 0.5) / 8)


# ---------------------------------------------------- underdispersion (binomial)

def test_the_binomial_shape_has_less_spread_than_poisson_at_the_same_mean():
    """Layer 1 found team touchdowns UNDERdispersed. The binomial is the shape
    that can say so; a negative binomial can only add spread."""
    k = np.arange(T.MAX_TD + 1)
    for P in (T.count_pmf([2.5], n=11), T.count_pmf([2.5])):
        assert (P[0] * k).sum() == pytest.approx(2.5, abs=1e-6)
    var = lambda P: (P[0] * k ** 2).sum() - 2.5 ** 2  # noqa: E731
    assert var(T.count_pmf([2.5], n=11)) == pytest.approx(2.5 * (1 - 2.5 / 11), abs=1e-6)
    assert var(T.count_pmf([2.5], n=11)) < var(T.count_pmf([2.5]))


def test_many_trials_is_poisson():
    assert T.count_pmf([2.5], n=100_000) == pytest.approx(T.count_pmf([2.5]), abs=1e-4)


def test_the_trial_fit_recovers_n_and_reports_poisson_when_there_is_no_underdispersion():
    rng = np.random.default_rng(2)
    mu = rng.uniform(1.5, 3.5, 5000)
    assert T.fit_trials(mu, rng.binomial(11, mu / 11)) == pytest.approx(11, abs=2)
    n = T.fit_trials(mu, rng.poisson(mu))
    assert n is None or n >= 40


def test_elasticity_bends_the_curve_without_moving_it_at_the_reference_total():
    mu = T.team_mean([24.0, 30.0], [0.11, 0.11], ref_implied=24.0, gamma=0.25)
    assert mu[0] == pytest.approx(24 * 0.11)            # unchanged at the reference
    assert mu[1] > 30 * 0.11                             # high totals convert more
    assert T.team_mean([30.0], [0.11], 24.0, 0.0)[0] == pytest.approx(3.3)

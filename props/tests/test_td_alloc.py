"""Layer 2 of the touchdown model: who scores, given the team's touchdowns.

These pin what the allocation backtest depends on: opportunities tagged with
the same channels touchdowns are, team denominators that run only over games
the player played, the three reallocation modes doing what they claim, an
'other' bucket that never disappears, and the scoring probability's algebra.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

pd = pytest.importorskip("pandas")
import td_alloc as A  # noqa: E402


def _pbp(rows):
    cols = ["game_id", "season", "week", "season_type", "posteam", "play_type",
            "rusher_player_id", "receiver_player_id", "yardline_100", "qb_kneel",
            "two_point_attempt"]
    d = pd.DataFrame(rows, columns=cols)
    # columns opportunities() reads for expected-TD weighting; no scores here
    return d.assign(rush_touchdown=0, pass_touchdown=0, td_team=d["posteam"], air_yards=8.0)


# ----------------------------------------------------------- opportunities

def test_opportunities_carry_the_same_channels_touchdowns_do():
    rows = [
        ("g", 2025, 1, "REG", "A", "run", "qb", None, 40, 0, 0),    # QB carry, anywhere
        ("g", 2025, 1, "REG", "A", "run", "rb", None, 3, 0, 0),     # rush_in5
        ("g", 2025, 1, "REG", "A", "run", "rb", None, 8, 0, 0),     # rush_far (and car_i10)
        ("g", 2025, 1, "REG", "A", "pass", None, "wr", 15, 0, 0),   # pass_rz
        ("g", 2025, 1, "REG", "A", "pass", None, "wr", 60, 0, 0),   # pass_far
        ("g", 2025, 1, "REG", "A", "run", "qb", None, 70, 1, 0),    # kneel: dropped
        ("g", 2025, 1, "REG", "A", "pass", None, "wr", 2, 0, 1),    # two-point: dropped
    ]
    o = A.opportunities(_pbp(rows), {"qb"})
    assert o["channel"].tolist() == ["qb_rush", "rush_in5", "rush_far", "pass_rz", "pass_far"]
    # a red-zone target whose air yards reach the end zone is pass_ez
    ez = _pbp([("g", 2025, 1, "REG", "A", "pass", None, "wr", 6, 0, 0)])   # air 8 >= 6
    assert A.opportunities(ez, {"qb"})["channel"].tolist() == ["pass_ez"]
    # the engine's split is inside-10 vs not, independent of the new channels
    assert o["engine"].tolist() == ["car_all", "car_i10", "car_i10", "tgt_all", "tgt_all"]


def test_the_engine_overall_share_counts_inside_10_plays_too():
    """The engine's `target_share` is over ALL targets. If inside-10 targets
    were only in tgt_i10, the baseline would be scored on a wrong share."""
    rows = [("g", 2025, 1, "REG", "A", "pass", None, "wr", 5, 0, 0),
            ("g", 2025, 1, "REG", "A", "pass", None, "wr", 50, 0, 0)]
    c = A.counts(A.opportunities(_pbp(rows), set()), "engine").iloc[0]
    assert c["tgt_all"] == 2 and c["tgt_i10"] == 1


# ------------------------------------------------------------------ shares

def _cnt(rows):
    return pd.DataFrame(rows, columns=["season", "week", "game_id", "team", "player_id", "pass_rz"])


def _played(rows):
    return pd.DataFrame(rows, columns=["season", "week", "game_id", "team", "player_id"])


def test_a_week_out_does_not_dilute_his_share():
    """Team denominators run over the games HE played. Counting the week he
    missed would halve a starter's share after one injury."""
    pri = _cnt([(2024, 1, "p1", "A", "wr", 5), (2024, 1, "p1", "A", "x", 5),
                (2024, 2, "p2", "A", "x", 10)])           # wr missed week 2
    played = _played([(2024, 1, "p1", "A", "wr"), (2024, 1, "p1", "A", "x"),
                      (2024, 2, "p2", "A", "x")])
    s = A.blended_shares(_cnt([]), pri, _played([]), played, ["pass_rz"], 1.0, {"pass_rz": 10.0})
    assert s.loc["wr", "pass_rz"] == pytest.approx(0.5)


def test_a_prior_from_another_team_counts_half():
    pri = _cnt([(2024, 1, "p1", "A", "wr", 5), (2024, 1, "p1", "A", "x", 5)])
    cur = _cnt([(2025, 1, "q1", "B", "wr", 0), (2025, 1, "q1", "B", "y", 10)])
    pl_pri = _played([(2024, 1, "p1", "A", "wr"), (2024, 1, "p1", "A", "x")])
    pl_cur = _played([(2025, 1, "q1", "B", "wr"), (2025, 1, "q1", "B", "y")])
    s = A.blended_shares(cur, pri, pl_cur, pl_pri, ["pass_rz"], 1.0, {"pass_rz": 10.0})
    # k = 1 game x 10 opps x 0.5 (moved): (0 + 5 * 0.5) / (10 + 5)
    assert s.loc["wr", "pass_rz"] == pytest.approx(2.5 / 15)


# ------------------------------------------------------------- reallocation

SH = pd.DataFrame({"team": ["A"] * 4, "rush_in5": [0.5, 0.1, 0.1, 0.2]},
                  index=["rb1", "rb2", "wr1", "te1"])
POS = {"rb1": "RB", "rb2": "RB", "wr1": "WR", "te1": "TE"}


def test_none_sends_an_inactive_players_share_to_other():
    s = A.reallocate(SH, {"rb2", "wr1", "te1"}, POS, ["rush_in5"], "none")
    assert s.loc["rb2", "rush_in5"] == pytest.approx(0.1)
    assert s["rush_in5"].sum() == pytest.approx(0.4)


def test_position_gives_the_rb1s_goal_line_work_to_the_rb2():
    s = A.reallocate(SH, {"rb2", "wr1", "te1"}, POS, ["rush_in5"], "position")
    assert s.loc["rb2", "rush_in5"] == pytest.approx(0.6)
    assert s.loc["wr1", "rush_in5"] == pytest.approx(0.1)   # untouched


def test_all_spreads_it_pro_rata_across_every_active():
    s = A.reallocate(SH, {"rb2", "wr1", "te1"}, POS, ["rush_in5"], "all")
    assert s["rush_in5"].sum() == pytest.approx(0.9)
    assert s.loc["te1", "rush_in5"] / s.loc["rb2", "rush_in5"] == pytest.approx(2.0)


def test_there_is_always_an_other_bucket():
    big = pd.DataFrame({"team": ["A", "A"], "pass_rz": [0.7, 0.6]}, index=["a", "b"])
    s = A.reallocate(big, {"a", "b"}, {"a": "WR", "b": "WR"}, ["pass_rz"], "none")
    assert s["pass_rz"].sum() == pytest.approx(0.99)


# ----------------------------------------------------------------- p_score

def test_p_score_is_one_minus_the_chance_every_touchdown_went_elsewhere():
    s = pd.DataFrame({"rush_in5": [0.5], "pass_rz": [0.2]}, index=["rb"])
    p = A.p_score(s, {"rush_in5": 2, "pass_rz": 1})["rb"]
    assert p == pytest.approx(1 - 0.5 ** 2 * 0.8)
    assert A.p_score(s, {"rush_in5": 0, "pass_rz": 0})["rb"] == pytest.approx(0.0)


# ------------------------------------------------ offseason movers (review fix)

def _week1_mover():
    """An RB who held 60% of team A's rush_in5 last season, active for B in
    week 1 -- no current-season games yet, so history alone says team A."""
    pri = pd.DataFrame([(2024, 1, "p1", "A", "rb", 6), (2024, 1, "p1", "A", "x", 4)],
                       columns=["season", "week", "game_id", "team", "player_id", "rush_in5"])
    pl_pri = _played([(2024, 1, "p1", "A", "rb"), (2024, 1, "p1", "A", "x")])
    empty_c = pri.iloc[0:0]
    return pri, pl_pri, empty_c


def test_a_week_one_mover_carries_his_old_role_at_half_weight():
    """THE REVIEW FINDING. Inferred from history, his team was A and 'moved'
    was False, so A's 60% entered B at full weight."""
    pri, pl_pri, empty = _week1_mover()
    s = A.blended_shares(empty, pri, _played([]), pl_pri, ["rush_in5"], 1.0,
                         {"rush_in5": 10.0}, current_team={"rb": "B"})
    assert s.loc["rb", "team"] == "B" and s.loc["rb", "pri_team"] == "A"
    # with no current evidence the blend is the prior itself; the half weight
    # shows up as soon as there is ANY current evidence, and the flag is right
    assert s.loc["rb", "rush_in5"] == pytest.approx(0.6)


def test_the_team_he_left_sees_his_share_as_vacated_not_as_an_active_player():
    pri, pl_pri, empty = _week1_mover()
    s = A.blended_shares(empty, pri, _played([]), pl_pri, ["rush_in5"], 1.0,
                         {"rush_in5": 10.0}, current_team={"rb": "B", "x": "A"})
    a = A.candidates(s, "A", ["rush_in5"])
    b = A.candidates(s, "B", ["rush_in5"])
    assert "rb" in a.index and "rb" in b.index
    # on A he can never be active, so his 0.6 is vacated share for A's backs...
    got = A.reallocate(a, {"x"}, {"rb": "RB", "x": "RB"}, ["rush_in5"], "position")
    assert got.loc["x", "rush_in5"] == pytest.approx(0.99)      # 0.4 + 0.6, capped
    # ...and with no reallocation it goes to 'other', not to anybody on A
    none = A.reallocate(a, {"x"}, {"rb": "RB", "x": "RB"}, ["rush_in5"], "none")
    assert none.loc["x", "rush_in5"] == pytest.approx(0.4)


def test_the_moved_role_weight_is_a_real_setting():
    """0.5 was an untuned assumption; the backtest now tunes it."""
    pri, pl_pri, _ = _week1_mover()
    cur = pd.DataFrame([(2025, 1, "q1", "B", "rb", 1), (2025, 1, "q1", "B", "y", 9)],
                       columns=["season", "week", "game_id", "team", "player_id", "rush_in5"])
    pl_cur = _played([(2025, 1, "q1", "B", "rb"), (2025, 1, "q1", "B", "y")])
    full = A.blended_shares(cur, pri, pl_cur, pl_pri, ["rush_in5"], 1.0, {"rush_in5": 10.0},
                            current_team={"rb": "B"}, moved_weight=1.0)
    assert full.loc["rb", "rush_in5"] == pytest.approx((1 + 10 * 0.6) / 20)


# ------------------------------------------------------------ Beta share

def test_a_beta_share_matches_the_worked_example():
    """The review's example: s = 0.25, three team touchdowns, c = 20.
    Fixed share 1 - 0.75^3 = 0.578; Beta(5, 15): 1 - (15*16*17)/(20*21*22) = 0.558."""
    assert A.p_score_given([0.25], 3, None)[0] == pytest.approx(1 - 0.75 ** 3)
    assert A.p_score_given([0.25], 3, 20.0)[0] == pytest.approx(1 - (15 * 16 * 17) / (20 * 21 * 22))
    assert A.p_score_given([0.25], 3, 20.0)[0] == pytest.approx(0.558, abs=0.0005)


def test_a_varying_share_lowers_p_score_where_the_top_bins_ran_high():
    """Jensen: (1 - s)^k is convex, so a share that varies game to game gives
    a LOWER chance of scoring than its mean share whenever the team scores
    more than once. The gap is NOT monotonic in the share: it is zero for a
    single team touchdown (E[1 - s] = 1 - q exactly), largest at mid-to-high
    shares, and vanishes as P(score) approaches 1. At three team touchdowns
    that puts the correction in the 0.45-0.70 range, where the rebuild ran
    high."""
    q = np.array([0.05, 0.25, 0.90])
    fixed, beta = A.p_score_given(q, 3, None), A.p_score_given(q, 3, 20.0)
    assert (beta < fixed).all()
    gap = fixed - beta
    assert gap[1] > gap[0] and gap[1] > gap[2]          # peaks in the middle
    assert A.p_score_given(q, 1, 20.0) == pytest.approx(A.p_score_given(q, 1, None))


def test_huge_concentration_is_the_fixed_share_and_zero_share_never_scores():
    assert A.p_score_given([0.3], 4, 1e9)[0] == pytest.approx(A.p_score_given([0.3], 4, None)[0], abs=1e-6)
    assert A.p_score_given([0.0], 4, 20.0)[0] == pytest.approx(0.0)
    assert A.p_score_given([0.3], 0, 20.0)[0] == pytest.approx(0.0)


def test_the_unconditional_probability_mixes_over_the_team_count():
    """P(none) = sum_k P(N = k) * E[(1 - s)^k]. With a fixed share and a
    binomial count this collapses to (1 - p*q)^n, the closed form."""
    import td_model as T
    pmf = T.count_pmf([2.4], n=10)[0]
    got = A.p_score_dist([0.2], pmf, None)[0]
    assert got == pytest.approx(1 - (1 - 0.24 * 0.2) ** 10, abs=1e-9)
    assert A.p_score_dist([0.2], pmf, 20.0)[0] < got


# ------------------------------------------------------------- slot prior

def test_a_player_with_no_history_gets_his_slots_league_share():
    cnt = pd.DataFrame([(2024, 1, "g", "A", "rb1", 8), (2024, 1, "g", "A", "rb2", 2)],
                       columns=["season", "week", "game_id", "team", "player_id", "rush_in5"])
    played = _played([(2024, 1, "g", "A", "rb1"), (2024, 1, "g", "A", "rb2")])
    slots = pd.DataFrame({"season": [2024, 2024], "week": [1, 1], "team": ["A", "A"],
                          "player_id": ["rb1", "rb2"], "slot": ["RB1", "RB2"]})
    prior = A.slot_prior(cnt, played, slots, ["rush_in5"])
    assert prior.loc["RB1", "rush_in5"] == pytest.approx(0.8)

    shares = pd.DataFrame({"team": ["B"], "pri_team": ["B"], "rush_in5": [0.3], "pri_rush_in5": [0.3]},
                          index=["vet"])
    act = pd.DataFrame({"player_id": ["vet", "rookie", "nobody"], "team": ["B", "B", "B"],
                        "slot": ["RB2", "RB1", None]})
    out = A.fill_no_history(shares, act, prior, ["rush_in5"])
    assert out.loc["vet", "rush_in5"] == pytest.approx(0.3)       # history kept
    assert out.loc["rookie", "rush_in5"] == pytest.approx(0.8)    # RB1's league share
    assert out.loc["nobody", "rush_in5"] == pytest.approx(0.0)    # no slot, no 'OTHER' row here
    # the slot share runs 2.5x high on no-history players, so it can be scaled
    scaled = A.fill_no_history(shares, act, prior, ["rush_in5"], scale=0.4)
    assert scaled.loc["rookie", "rush_in5"] == pytest.approx(0.32)
    assert scaled.loc["vet", "rush_in5"] == pytest.approx(0.3)    # history never scaled


def test_a_mover_with_current_games_is_blended_at_half_weight():
    pri, pl_pri, _ = _week1_mover()
    cur = pd.DataFrame([(2025, 1, "q1", "B", "rb", 1), (2025, 1, "q1", "B", "y", 9)],
                       columns=["season", "week", "game_id", "team", "player_id", "rush_in5"])
    pl_cur = _played([(2025, 1, "q1", "B", "rb"), (2025, 1, "q1", "B", "y")])
    s = A.blended_shares(cur, pri, pl_cur, pl_pri, ["rush_in5"], 1.0, {"rush_in5": 10.0},
                         current_team={"rb": "B"})
    # k = 1 game x 10 x 0.5: (1 + 5 * 0.6) / (10 + 5)
    assert s.loc["rb", "rush_in5"] == pytest.approx(4.0 / 15)

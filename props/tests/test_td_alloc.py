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
    return pd.DataFrame(rows, columns=cols)


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


def test_a_mover_with_current_games_is_blended_at_half_weight():
    pri, pl_pri, _ = _week1_mover()
    cur = pd.DataFrame([(2025, 1, "q1", "B", "rb", 1), (2025, 1, "q1", "B", "y", 9)],
                       columns=["season", "week", "game_id", "team", "player_id", "rush_in5"])
    pl_cur = _played([(2025, 1, "q1", "B", "rb"), (2025, 1, "q1", "B", "y")])
    s = A.blended_shares(cur, pri, pl_cur, pl_pri, ["rush_in5"], 1.0, {"rush_in5": 10.0},
                         current_team={"rb": "B"})
    # k = 1 game x 10 x 0.5: (1 + 5 * 0.6) / (10 + 5)
    assert s.loc["rb", "rush_in5"] == pytest.approx(4.0 / 15)

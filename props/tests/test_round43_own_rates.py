"""Round 43 (reports/round43_own_rates.md): a player's catch rate, yards per target and yards per
carry from his own last 10 games, long plays capped at his own 90th percentile.

Known answers: the window is his last 10 games with a target / carry strictly before the game,
across seasons; a thin window returns None (the caller keeps the blend); the cap is the luck
cap's own rule (research.player_luck_line / luck_free_rate)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))


@pytest.fixture
def bt():
    pytest.importorskip("scipy")
    import backtest as BT
    return BT


def _rec(rows):
    """rows: (season, week, gsis_id, complete, yards) per target."""
    return pd.DataFrame(rows, columns=["season", "week", "gsis_id", "complete", "yards"])


def _run(rows):
    return pd.DataFrame(rows, columns=["season", "week", "gsis_id", "yards"])


def test_off_changes_nothing_and_the_arms_are_the_registered_ones(bt):
    assert bt.OWN_ARMS["off"] == ()
    assert set(bt.OWN_ARMS) == {"off", "catch_rate", "ypt", "ypc", "all"}
    assert bt.OWN_ARMS["all"] == ("catch_rate", "ypt", "ypc")


def test_the_window_is_his_last_ten_games_before_the_game_across_seasons(bt):
    rows = []
    # 2025 weeks 1-12: 3 targets a game, 2 caught for 10 yards each
    for w in range(1, 13):
        rows += [(2025, w, "P", 1, 10.0), (2025, w, "P", 1, 10.0), (2025, w, "P", 0, np.nan)]
    # 2026 weeks 1-2: 4 targets, 1 caught for 4 yards
    for w in (1, 2):
        rows += [(2026, w, "P", 1, 4.0)] + [(2026, w, "P", 0, 0.0)] * 3
    # 2026 week 3 (the game itself) and week 4 (the future) must not count
    rows += [(2026, 3, "P", 1, 99.0)] * 5 + [(2026, 4, "P", 1, 99.0)] * 5
    rec_ix, run_ix = bt.own_play_index(_rec(rows), None)
    o = bt.own_window_rates(rec_ix, run_ix, "P", (2026, 3))
    # window: 2025 weeks 5-12 (8 games: 24 targets, 16 catches of 10) + 2026 weeks 1-2 (8 targets, 2 of 4)
    assert o["n_tg"] == 32
    assert o["catch_rate"] == pytest.approx(18 / 32)
    # 18 catches: his 90th percentile is 10, nothing above it, so yards a target = 168 / 32
    assert o["ypt"] == pytest.approx((16 * 10 + 2 * 4) / 32)
    assert o["ypc"] is None and o["n_ca"] == 0


def test_long_catches_are_capped_at_his_own_90th_percentile(bt):
    import research as RSCH
    rows = []
    for w in range(1, 11):
        rows += [(2025, w, "P", 1, 8.0), (2025, w, "P", 0, np.nan), (2025, w, "P", 0, np.nan)]
    rows[0] = (2025, 1, "P", 1, 80.0)          # one breakaway
    rec_ix, _ = bt.own_play_index(_rec(rows), None)
    o = bt.own_window_rates(rec_ix, {}, "P", (2026, 1))
    catches = [80.0] + [8.0] * 9
    cap = float(np.percentile(catches, RSCH.LUCK_PCT["catch"]))
    assert o["ypt"] == pytest.approx(sum(min(c, cap) for c in catches) / 30)
    assert o["ypt"] < sum(catches) / 30, "the breakaway is trimmed"


def test_a_thin_window_keeps_the_blend(bt):
    rows = [(2026, w, "P", 1, 9.0) for w in (1, 2, 3)] * 6          # 18 targets: under 20
    runs = [(2026, w, "P", 4.0) for w in (1, 2, 3)] * 13             # 39 carries: under 40
    rec_ix, run_ix = bt.own_play_index(_rec(rows), _run(runs))
    o = bt.own_window_rates(rec_ix, run_ix, "P", (2026, 4))
    assert o["n_tg"] == 18 and o["catch_rate"] is None and o["ypt"] is None
    assert o["n_ca"] == 39 and o["ypc"] is None
    assert bt.own_window_rates(rec_ix, run_ix, "NOBODY", (2026, 4))["ypt"] is None


def test_yards_per_carry_is_his_capped_runs(bt):
    import research as RSCH
    runs = []
    for w in range(1, 11):
        runs += [(2025, w, "B", 3.0)] * 4 + [(2025, w, "B", 60.0 if w == 5 else 5.0)]
    _, run_ix = bt.own_play_index(None, _run(runs))
    o = bt.own_window_rates({}, run_ix, "B", (2026, 1))
    v = [y for _, _, _, y in runs]
    cap = float(np.percentile(v, RSCH.LUCK_PCT["run"]))
    assert o["n_ca"] == 50
    assert o["ypc"] == pytest.approx(sum(min(x, cap) for x in v) / 50)


def test_the_long_play_add_back_is_plain_over_capped_by_position(bt):
    import research as RSCH
    rows = [(2025, w, "W", 1, y) for w, y in enumerate([5.0] * 9 + [50.0], start=1)]
    rows += [(2025, w, "R", 1, 4.0) for w in range(1, 11)]             # no long play: factor 1
    rows += [(2025, 1, "X", 1, 9.0)]                                     # too few catches: left out
    rec = _rec(rows)
    f = bt.own_uplift(rec, None, {"W": "WR", "R": "RB", "X": "TE"})
    v = [5.0] * 9 + [50.0]
    cap = float(np.percentile(v, RSCH.LUCK_PCT["catch"]))
    assert f["catch"]["WR"] == pytest.approx(sum(v) / sum(min(x, cap) for x in v))
    assert f["catch"]["RB"] == pytest.approx(1.0)
    assert "TE" not in f["catch"]
    assert f["catch"]["ALL"] == pytest.approx((sum(v) + 40.0) / (sum(min(x, cap) for x in v) + 40.0))
    assert f["run"] == {}


def test_the_add_back_reads_each_players_final_ten_games_only(bt):
    # weeks 1-5: one 90-yard catch a game; weeks 6-15: 6 yards a catch -- only the last 10 count
    rows = [(2025, w, "W", 1, 90.0) for w in range(1, 6)] + [(2025, w, "W", 1, 6.0) for w in range(6, 16)]
    f = bt.own_uplift(_rec(rows), None, {"W": "WR"})
    assert f["catch"]["WR"] == pytest.approx(1.0), "the early long catches are outside the window"


def test_under_ten_catches_is_his_plain_average_with_no_add_back(bt):
    rows = [(2026, w, "P", 1, y) for w, y in ((1, 5.0), (2, 40.0), (3, 7.0))]
    rows += [(2026, w, "P", 0, np.nan) for w in (1, 2, 3)] * 6          # 21 targets, 3 catches
    rec_ix, _ = bt.own_play_index(_rec(rows), None)
    o = bt.own_window_rates(rec_ix, {}, "P", (2026, 4), uplift_catch=1.2)
    assert o["n_tg"] == 21 and o["ypt"] == pytest.approx((5.0 + 40.0 + 7.0) / 21)


def test_the_add_back_multiplies_the_capped_yards_only(bt):
    rows = [(2025, w, "P", 1, 6.0) for w in range(1, 11)] * 2 + [(2025, w, "P", 0, np.nan) for w in range(1, 11)]
    rec_ix, _ = bt.own_play_index(_rec(rows), None)
    a = bt.own_window_rates(rec_ix, {}, "P", (2026, 1))
    b = bt.own_window_rates(rec_ix, {}, "P", (2026, 1), uplift_catch=1.1)
    assert b["ypt"] == pytest.approx(1.1 * a["ypt"]) and b["catch_rate"] == a["catch_rate"]


def test_no_catch_in_a_full_window_is_zero_yards_a_target(bt):
    rows = [(2026, w, "P", 0, np.nan) for w in range(1, 5)] * 6        # 24 targets, none caught
    rec_ix, _ = bt.own_play_index(_rec(rows), None)
    o = bt.own_window_rates(rec_ix, {}, "P", (2026, 5))
    assert o["catch_rate"] == 0.0 and o["ypt"] == 0.0


def _sel():
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
    import round43_select as R43
    return R43


def _frame(pc, line=3.5, act=4.0):
    return pd.DataFrame({"season": [2024, 2024], "team": ["A", "B"], "week": [3, 3], "gsis_id": ["p", "q"],
                         "L_rec": [line, line], "act_receptions": [act, act], "pc_rec": pc, "pu_rec": pc,
                         "pc_rec_exact": [1.0, 1.0]})


def test_seed_average_means_the_chances_and_keeps_everything_else():
    R43 = _sel()
    out = R43.seed_average([_frame([0.2, 0.6]), _frame([0.4, 0.8]).iloc[::-1]])
    assert out.pc_rec.tolist() == pytest.approx([0.3, 0.7]) and out.pu_rec.tolist() == pytest.approx([0.3, 0.7])
    assert out.L_rec.tolist() == [3.5, 3.5] and out.pc_rec_exact.tolist() == [1.0, 1.0]


def test_seeds_that_disagree_on_a_line_or_an_outcome_are_refused():
    R43 = _sel()
    with pytest.raises(ValueError, match="L_rec"):
        R43.seed_average([_frame([0.2, 0.6]), _frame([0.2, 0.6], line=4.5)])
    with pytest.raises(ValueError, match="act_receptions"):
        R43.seed_average([_frame([0.2, 0.6]), _frame([0.2, 0.6], act=2.0)])
    other = _frame([0.2, 0.6]).assign(gsis_id=["p", "z"])
    with pytest.raises(ValueError, match="different player-games"):
        R43.seed_average([_frame([0.2, 0.6]), other])


def test_a_pickle_from_the_wrong_arm_is_refused(tmp_path):
    R43 = _sel()
    rows = _frame([0.2, 0.6]).assign(own_rates="off")
    for part, season in (("sel", 2024), ("con", 2026)):
        pd.to_pickle({"kind": "harness", "results": rows.assign(season=season)}, tmp_path / f"r43_ypt_s0_{part}.pkl")
    with pytest.raises(ValueError, match="own_rates"):
        R43.load(tmp_path, "ypt", 0)
    for part, season in (("sel", 2024), ("con", 2026)):
        pd.to_pickle({"kind": "harness", "results": rows.assign(season=season, own_rates="ypt")},
                     tmp_path / f"r43_ypt_s0_{part}.pkl")
    assert len(R43.load(tmp_path, "ypt", 0)) == 4


def test_the_stand_in_lines_read_the_shipped_rates(bt):
    """Every arm is scored at the shipped engine's lines: the line arithmetic reads cr_ship /
    ypt_ship / ypc_ship, the draws read the arm's own rates."""
    import inspect
    src = inspect.getsource(bt.run_season)
    assert 'half(mu_t[k_] * crL_[k_]), "yds": half(SC_Y * mu_t[k_] * yptL_[k_])' in src
    assert "ypc_all = test_act.ypc_ship" in src
    assert "receiving_given_targets(g, N, T, float(cr_[k_]), float(ypt_[k_])" in src
    assert "rushing_given_carries(g, N, C, float(ypc_[i])" in src
    assert "exp_y = (sum(mu_t[k_] * yptL_[k_]" in src

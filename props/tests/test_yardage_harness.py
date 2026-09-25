"""The rushing sampler the scorer and the harness share, and the harness's
own arithmetic.

The rushing draw used to live inline in score_game.py, so the backtest could
only have graded a second copy of it -- which is how the receiving harness once
measured a sampler that never priced a prop. It now lives in
model.simulate_team_rush and both call it. These tests pin what the draw must
do; the harness tests skip where scipy is absent (the capture runner), so they
can never block a slate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402

RESID = np.linspace(-4.0, 4.0, 201)          # a symmetric, zero-mean carry residual grid


def test_rush_draws_split_one_team_total_and_never_exceed_it():
    rng = np.random.default_rng(7)
    car, yds, team = M.simulate_team_rush(rng, 4000, 26.0, 30.0, [0.55, 0.25, 0.05], [4.5, 4.0, 3.0], RESID)
    total = np.sum(car, axis=0)
    assert np.all(total <= team), "players plus the 'other' bucket split the team's carries"
    assert car[0].mean() == pytest.approx(26.0 * 0.55, rel=0.05)
    assert yds[0].mean() == pytest.approx(26.0 * 0.55 * 4.5, rel=0.06), "yards = carries x (ypc + zero-mean residual)"
    assert np.corrcoef(car[0], car[1])[0, 1] < np.corrcoef(car[0], team)[0, 1], \
        "teammates compete for one total; each shares the team's variance"


def test_a_player_with_no_share_gets_no_carries_and_the_draw_is_seeded():
    a = M.simulate_team_rush(np.random.default_rng(3), 500, 25.0, 30.0, [0.6, 0.0], [4.0, 4.0], RESID)
    b = M.simulate_team_rush(np.random.default_rng(3), 500, 25.0, 30.0, [0.6, 0.0], [4.0, 4.0], RESID)
    assert not a[0][1].any() and not a[1][1].any()
    assert all(np.array_equal(x, y) for x, y in zip(a[0] + a[1], b[0] + b[1]))


def test_the_scorer_calls_the_shared_rush_sampler():
    src = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    assert "MODEL.simulate_team_rush(" in src
    assert "MODEL.simulate_qb_passing(" in src, "passing yards come from the shared sampler the harness grades"
    assert "rng.choice(resid" not in src, "a second inline copy of the rushing draw is back"


@pytest.fixture
def backtest():
    pytest.importorskip("scipy")
    import backtest as BT
    return BT


def _frame(gains, season=2024):
    rows = []
    for g, gain in enumerate(gains):
        for p in range(6):
            rows.append({"season": season, "game_id": f"g{g}", "week": 5 + g % 10,
                         "crps_rec_model": 1.0, "crps_rec_baseA": 1.0 + gain,
                         "act_receptions": 3.0, "mean_rec_model": 3.0, "pit_rec": 0.5})
    return pd.DataFrame(rows)


def test_the_game_block_interval_excludes_zero_only_for_a_consistent_gain(backtest):
    s = backtest.summarize(_frame([0.05] * 40), "rec")
    assert s["gain"] == pytest.approx(0.05) and s["ci"][0] > 0
    s = backtest.summarize(_frame([0.05, -0.05] * 20), "rec")
    assert s["ci"][0] < 0 < s["ci"][1]


def test_bias_is_flagged_on_the_mean_ratio_or_the_pit(backtest):
    d = _frame([0.0] * 20)
    assert not backtest.summarize(d, "rec")["biased"]
    assert backtest.summarize(d.assign(mean_rec_model=2.7), "rec")["biased"], "actual 11% above the model"
    assert backtest.summarize(d.assign(pit_rec=0.55), "rec")["biased"]


def test_rushing_is_scored_on_its_fixed_population_only(backtest):
    d = _frame([0.0] * 12).assign(crps_rush_model=1.0, crps_rush_baseA=1.2, act_rush_yards=40.0,
                                  mean_rush_model=40.0, pit_rush=0.5)
    d["rush_pop"] = [i % 2 == 0 for i in range(len(d))]
    assert backtest.summarize(d, "rush")["n"] == len(d) // 2


def test_width_counts_outcomes_outside_the_model_p10_p90(backtest):
    d = _frame([0.0] * 20)
    n = len(d)
    d["pit_rec"] = [(i + 0.5) / n for i in range(n)]            # uniform PIT: a calibrated model
    assert backtest.summarize(d, "rec")["outside_p10_p90"] == pytest.approx(0.20, abs=0.01)
    d["pit_rec"] = [0.02 if i % 3 == 0 else 0.5 for i in range(n)]   # a third land below p10: too narrow
    assert backtest.summarize(d, "rec")["outside_p10_p90"] == pytest.approx(1 / 3, abs=0.01)


def _verdict_inputs(backtest, gain, pit, gap):
    frames = []
    for season in (2024, 2025):
        d = _frame([gain] * 30, season=season)
        d["pit_rec"] = pit(len(d))
        frames.append(d)
    rel = pd.DataFrame({"market": "receptions", "side": ["Over", "Under"] * 3,
                        "bucket": ["60-70", "60-70", "70-80", "70-80", "80-90", "80-90"],
                        "n": 100, "p_model_mean": 0.75, "hit_rate": 0.75 + gap})
    return pd.concat(frames, ignore_index=True), rel


def test_the_verdict_needs_all_four_parts(backtest):
    uniform = lambda n: [(i + 0.5) / n for i in range(n)]
    narrow = lambda n: [0.02 if i % 3 == 0 else 0.5 + 0.3 * (i % 2) for i in range(n)]
    res, rel = _verdict_inputs(backtest, 0.05, uniform, 0.0)
    assert backtest.market_verdict(res, rel, [2024, 2025], "rec")["passes"]
    res, rel = _verdict_inputs(backtest, 0.05, narrow, 0.0)
    v = backtest.market_verdict(res, rel, [2024, 2025], "rec")
    assert not v["passes"] and not v["width_ok"] and v["beats_baseline_each_test_season"]
    res, rel = _verdict_inputs(backtest, 0.05, uniform, -0.05)
    v = backtest.market_verdict(res, rel, [2024, 2025], "rec")
    assert not v["passes"] and v["width_ok"] and not v["calibration_ok"]
    res, rel = _verdict_inputs(backtest, 0.0, uniform, 0.0)
    assert not backtest.market_verdict(res, rel, [2024, 2025], "rec")["beats_baseline_each_test_season"]


def test_priors_are_never_built_into_the_engine(backtest, tmp_path):
    with pytest.raises(SystemExit, match="refusing"):
        backtest.ensure_priors(1999, backtest.RES, build=True)
    assert backtest.priors_cache_dir().name.startswith("priors-")


def _rec(width, seed=11, n=20000):
    out, _ = M.simulate_team_game(np.random.default_rng(seed), n, 34.0, 35.0, {"a": 0.25, "b": 0.15},
                                  {"a": 0.65, "b": 0.6}, {"a": 8.5, "b": 7.0}, 1.08, width=width)
    return out["a"]


def test_width_off_is_the_old_sampler_draw_for_draw():
    for off in (None, {}, dict(M.WIDTH_OFF)):
        r, y = _rec(off)
        r0, y0 = _rec(None)
        assert np.array_equal(r, r0) and np.array_equal(y, y0)


@pytest.mark.parametrize("width", [{"share_conc_targets": 10.0}, {"catch_conc": 10.0}, {"eff_sd_rec": 0.4}])
def test_each_receiving_width_setting_keeps_the_mean_and_widens(width):
    r0, y0 = _rec(None)
    r, y = _rec(width)
    assert y.mean() == pytest.approx(y0.mean(), rel=0.03) and r.mean() == pytest.approx(r0.mean(), rel=0.03)
    assert y.std() > y0.std() * 1.03


@pytest.mark.parametrize("width", [{"share_conc_carries": 10.0}, {"eff_sd_rush": 0.4}])
def test_each_rushing_width_setting_keeps_the_mean_and_widens(width):
    def run(w):
        return M.simulate_team_rush(np.random.default_rng(5), 20000, 26.0, 30.0, [0.55, 0.2], [4.5, 4.0], RESID,
                                    width=w)[1][0]
    y0, y = run(None), run(width)
    assert y.mean() == pytest.approx(y0.mean(), rel=0.03)
    assert y.std() > y0.std() * 1.03


def test_width_settings_are_validated_never_silently_misread():
    assert M.validate_width({"share_conc_targets": 40.0, "eff_sd_rush": 0.3, "note": "x"}) == \
        {"share_conc_targets": 40.0, "eff_sd_rush": 0.3}
    for bad in ({"share_conc_targets": 0}, {"catch_conc": -5}, {"eff_sd_rec": -0.1}, {"share_conc": 40}):
        with pytest.raises(ValueError):
            M.validate_width(bad)


def test_the_shipped_width_file_is_valid():
    import json
    f = ENGINE.parent / "resources" / "width_params.json"
    assert M.validate_width(json.loads(f.read_text(encoding="utf-8")))


def test_the_harness_grades_the_shipped_sampler_unless_told_off(backtest):
    from types import SimpleNamespace
    assert backtest.width_of(SimpleNamespace(width=None)) == backtest.width_of(
        SimpleNamespace(width=str(backtest.SHIPPED_WIDTH)))
    assert backtest.width_of(SimpleNamespace(width="off")) == {}
    assert backtest.width_of(SimpleNamespace(width='{"eff_sd_rush": 0.2}')) == {"eff_sd_rush": 0.2}


def test_ties_are_settings_not_measurably_worse_than_the_best(backtest):
    rows = [{"season": 2022, "game_id": f"g{g}", "x": 0.0} for g in range(60) for _ in range(5)]
    base = pd.DataFrame(rows)
    rng = np.random.default_rng(0)
    noise = rng.normal(0, 0.05, len(base))
    frames = [base.assign(x=noise),
              base.assign(x=rng.normal(0, 0.05, len(base)) + 0.001),    # a hair worse, within its own noise
              base.assign(x=noise + 0.2)]                                # clearly worse
    flags = backtest.tie_flags(frames, lambda i: frames[i]["x"], best=0)
    assert flags == [True, True, False], "a hair worse ties; clearly worse does not"


def test_a_saved_run_says_what_it_is(backtest, tmp_path):
    f = tmp_path / "t.pkl"
    pd.to_pickle({"kind": "width_tuning", "grid": [], "frames": []}, f)
    assert backtest.load_run(f, "width_tuning")["grid"] == []
    with pytest.raises(SystemExit, match="not a harness run"):
        backtest.load_run(f, "harness")


def _rush(**kw):
    return M.simulate_team_rush(np.random.default_rng(9), 5000, 26.0, 30.0, [0.5, 0.15, 0.1], [4.5, 5.6, 4.0],
                                RESID, **kw)


def test_qb_grid_and_kneels_move_only_the_qb():
    base_car, base_y, base_tc = _rush()
    qb_grid = RESID * 0.5          # zero-mean, a different shape, the league grid's length
    kneels = [-1.0] * 100 + [0.0] * 101                          # a kneel-yards grid
    car, y, tc = _rush(player_resid=[None, qb_grid, None], player_kneel=[None, kneels, None])
    assert np.array_equal(tc, base_tc) and all(np.array_equal(a, b) for a, b in zip(car, base_car))
    assert np.array_equal(y[0], base_y[0]) and np.array_equal(y[2], base_y[2]), "the RBs' numbers do not move"
    assert not np.array_equal(y[1], base_y[1])
    assert (y[1] - base_y[1]).mean() < 0, "kneel-downs only ever take yards away here"


def test_a_qb_grid_of_another_length_is_refused():
    with pytest.raises(ValueError, match="length"):
        _rush(player_resid=[None, np.zeros(11), None])


def test_the_kneel_grid_follows_the_teams_own_spread():
    P = {"qb_kneel_yards_by_spread": {"edges": [-3.0, 3.0, 7.0], "grids": [["dog"], ["pk"], ["fav"], ["big"]]}}
    assert M.kneel_grid(P, -6.5) == ["dog"] and M.kneel_grid(P, 0.0) == ["pk"]
    assert M.kneel_grid(P, 3.0) == ["fav"] and M.kneel_grid(P, 10.0) == ["big"]
    assert M.kneel_grid(P, None) is None and M.kneel_grid({}, 3.0) is None


def test_the_qb_first_split_keeps_every_mean_and_is_off_until_set():
    shares, ypc = [0.45, 0.2, 0.12], [4.5, 4.0, 5.6]
    off = M.simulate_team_rush(np.random.default_rng(4), 20000, 26.0, 30.0, shares, ypc, RESID,
                               width={"share_conc_carries": 20.0}, qb_index=2)
    base = M.simulate_team_rush(np.random.default_rng(4), 20000, 26.0, 30.0, shares, ypc, RESID,
                                width={"share_conc_carries": 20.0})
    assert all(np.array_equal(a, b) for a, b in zip(off[1], base[1])), "qb_index alone changes nothing"
    on = M.simulate_team_rush(np.random.default_rng(4), 20000, 26.0, 30.0, shares, ypc, RESID,
                              width={"share_conc_carries": 20.0, "share_conc_qb": 80.0}, qb_index=2)
    for j, q in enumerate(shares):
        assert on[0][j].mean() == pytest.approx(26.0 * q, rel=0.04)
    assert on[0][2].std() < base[0][2].std(), "his own, tighter swing than the RB-tuned Dirichlet gave him"


def test_book_spread_becomes_the_teams_own_positive_when_favoured():
    # a book's 'KC -7' at home is home_spread -7: KC is favoured by 7
    assert M.own_spread_from_book(-7.0, is_home=True) == 7.0
    assert M.own_spread_from_book(-7.0, is_home=False) == -7.0
    assert M.own_spread_from_book(None, is_home=True) is None


def test_no_spread_yet_uses_the_pooled_kneel_grid():
    P = {"qb_kneel_yards_by_spread": {"edges": [-3.0, 3.0, 7.0], "grids": [[1], [2], [3], [4]], "pooled": [0]}}
    assert M.kneel_grid(P, None) == [0] and M.kneel_grid(P, float("nan")) == [0]


def test_the_starter_is_the_qb_with_the_carries_not_the_slot():
    # QB1 ruled out and removed: the backup keeps his QB2 slot and is the starter
    assert M.starter_qb_index(["RB1", "QB2", "WR1"], [0.5, 0.12, 0.02]) == 1
    assert M.starter_qb_index(["QB", "QB", "RB"], [0.02, 0.15, 0.5]) == 1
    assert M.starter_qb_index(["RB", "WR"], [0.5, 0.1]) is None


def test_with_slots_the_starter_is_the_depth_charts_qb_not_a_running_backup():
    # a running backup (20%+ of carries, no QB slot) out-carries the starter
    pos, rs = ["QB", "QB", "RB"], [0.04, 0.22, 0.5]
    assert M.starter_qb_index(pos, rs) == 1, "without slots: carries"
    assert M.starter_qb_index(pos, rs, slots=["QB1", "PROXY", "RB1"]) == 0
    # QB1 ruled out and removed: the highest QB left starts, whatever his slot
    assert M.starter_qb_index(["QB", "QB"], [0.02, 0.2], slots=["QB2", "PROXY"]) == 0
    # two with no QB slot: carries decide
    assert M.starter_qb_index(["QB", "QB"], [0.02, 0.2], slots=["PROXY", "PROXY"]) == 1


def test_carry_shares_rescale_toward_the_realistic_total_leaving_the_qb_alone():
    shares, ypc = [0.30, 0.15, 0.12], [4.5, 4.0, 5.6]           # they sum to 0.57: 'other' would take 43%
    run = lambda w, qb=None: M.simulate_team_rush(np.random.default_rng(8), 20000, 26.0, 30.0, shares, ypc,
                                                  RESID, width=w, qb_index=qb)
    off = run(None)
    full = run({"rush_other_share": 0.12, "rush_norm_strength": 1.0}, qb=2)
    # the backs are scaled to 1 - 0.12 - 0.12 = 0.76 of the carries; the QB keeps his 12%
    assert (full[0][0].mean() + full[0][1].mean()) / 26.0 == pytest.approx(0.76, rel=0.03)
    assert full[0][2].mean() == pytest.approx(off[0][2].mean(), rel=0.03)
    same = run({"rush_other_share": 0.12, "rush_norm_strength": 0.0}, qb=2)
    assert all(np.array_equal(a, b) for a, b in zip(same[1], run(None, qb=2)[1])), "strength 0 = off"


def test_rescaling_settings_are_validated():
    assert M.validate_width({"rush_other_share": 0.1, "rush_norm_strength": 0.5})
    for bad in ({"rush_other_share": 1.2}, {"rush_norm_strength": 2.0}, {"rush_other_share": -0.1}):
        with pytest.raises(ValueError):
            M.validate_width(bad)


def test_the_tuner_adds_markets_on_their_own_populations_relative_to_their_baselines(backtest):
    f = pd.DataFrame({"crps_rush_model": [10.0, 20.0, 5.0, float("nan")],
                      "crps_qbrush_model": [float("nan"), float("nan"), 4.0, 8.0],
                      "rush_pop": [True, True, False, False], "qb_pop": [False, False, True, True]})
    out = backtest.composite_rows(f, ("rush", "qbrush"), {"rush": 10.0, "qbrush": 4.0})
    assert list(out) == [1.0, 2.0, 1.0, 2.0], "each row scored on its own market, relative to its own base"
    none = f.assign(rush_pop=False, qb_pop=False)
    assert backtest.composite_rows(none, ("rush", "qbrush"), {"rush": 10.0, "qbrush": 4.0}).isna().all()


# ---- QB passing (plan step 4) ----------------------------------------------
def _team(seed=11, n=20000, **kw):
    rng = np.random.default_rng(seed)
    out, tt = M.simulate_team_game(rng, n, 34.0, 35.0, {"a": 0.25, "b": 0.15, "qb": 0.0},
                                   {"a": 0.65, "b": 0.6, "qb": 0.5}, {"a": 8.5, "b": 7.0, "qb": 5.0}, 1.08, **kw)
    return rng, out, tt


def test_asking_for_the_other_bucket_costs_no_draw_and_moves_no_receiver():
    _rng0, base, tt0 = _team()
    _rng1, out, tt1 = _team(return_other=True)
    other = out.pop(M.OTHER)
    assert np.array_equal(tt0, tt1) and set(out) == set(base)
    assert all(np.array_equal(out[k][0], base[k][0]) and np.array_equal(out[k][1], base[k][1]) for k in base)
    assert other.mean() == pytest.approx(34.0 * 0.60, rel=0.03), "the bucket holds the 60% no one else covers"


def test_qb_passing_is_his_receivers_plus_the_other_bucket_and_moves_no_one():
    rng, out, _tt = _team(return_other=True)
    other = out.pop(M.OTHER)
    ys = [y for _r, y in out.values()]
    before = rng.bit_generator.state
    tracked_only = M.simulate_qb_passing(rng, len(other), ys, None, None, 1.08)
    assert rng.bit_generator.state == before, "the QB's draws come from a child stream"
    assert np.allclose(tracked_only, sum(ys)), "with nothing else on, exactly the receivers' total"
    rates = {"catch_rate": 0.67, "ypt": 6.3}
    full = M.simulate_qb_passing(rng, len(other), ys, other, rates, 1.08)
    assert (full - tracked_only).mean() == pytest.approx(other.mean() * 6.3, rel=0.05)
    assert (full >= tracked_only).all()


def test_the_starter_share_and_the_passing_swing_are_off_until_given():
    rng, out, _tt = _team(return_other=True)
    other = out.pop(M.OTHER)
    ys = [y for _r, y in out.values()]
    rates = {"catch_rate": 0.67, "ypt": 6.3}
    base = M.simulate_qb_passing(rng, len(other), ys, other, rates, 1.08)
    share = M.simulate_qb_passing(rng, len(other), ys, other, rates, 1.08, starter_share=[0.5] * 10 + [1.0] * 30)
    assert share.mean() == pytest.approx(base.mean() * 0.875, rel=0.03)
    wide = M.simulate_qb_passing(rng, len(other), ys, other, rates, 1.08, width={"eff_sd_pass": 0.25})
    assert wide.mean() == pytest.approx(base.mean(), rel=0.02), "the swing keeps the mean"
    assert wide.std() > base.std() * 1.05
    with pytest.raises(ValueError):
        M.validate_width({"eff_sd_pass": -0.1})


def test_passing_is_graded_on_the_starting_qb_only(backtest):
    assert backtest.POPULATION["pass"] == "pass_pop"
    d = pd.DataFrame({"season": 2024, "week": 5, "game_id": [f"g{i}" for i in range(4)],
                      "pass_pop": [True, False, True, False], "crps_pass_model": [40.0, np.nan, 50.0, np.nan]})
    assert list(backtest.market_rows(d, "pass").crps_pass_model) == [40.0, 50.0]


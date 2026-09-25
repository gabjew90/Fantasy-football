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

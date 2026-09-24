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

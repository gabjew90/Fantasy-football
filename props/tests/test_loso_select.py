"""props/tools/loso_select.py on worlds with a known answer, before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import loso_select as LS  # noqa: E402


def _frame(truth, y, noise, seed):
    rng = np.random.default_rng(seed)
    n = len(truth)
    pc = np.clip(truth + rng.normal(0, noise, n), 0.02, 0.98) if noise else truth
    return pd.DataFrame({"season": np.repeat([2022, 2023, 2024, 2025], n // 4), "team": "T",
                         "week": np.tile(np.arange(n // 4), 4), "gsis_id": "p", "game_id": np.arange(n) // 3,
                         "mean_tgt": 6.0, "L_rec": 4.5, "act_receptions": np.where(y, 5.0, 4.0),
                         "pc_rec": pc, "pu_rec": 0.5, "rush_pop": False, "mean_car_model": 0.0})


def _world(n=8000, seed=0):
    rng = np.random.default_rng(seed)
    truth = np.clip(0.5 + rng.normal(0, 0.15, n), 0.05, 0.95)
    return truth, rng.uniform(size=n) < truth


def test_a_truly_better_setting_wins_out_of_fold():
    truth, y = _world()
    frames = [_frame(truth, y, 0.12, 1), _frame(truth, y, 0.0, 2), _frame(truth, y, 0.25, 3)]
    out = LS.loso(frames, [0, 1, 2], 0, "receptions", "c", reps=200)
    assert all(f["pick"] == 1 for f in out["folds"]), "the right setting is picked in every fold"
    assert out["oof_gain"] > 0 and out["oof_ci"][0] > 0


def test_a_grid_of_pure_noise_shows_the_winners_curse():
    """Ten settings that are each the shipped one plus independent noise of the same size:
    the in-sample pick looks at least as good as shipped, the out-of-fold gain does not."""
    truth, y = _world(seed=4)
    frames = [_frame(truth, y, 0.08, 10 + k) for k in range(10)]
    out = LS.loso(frames, list(range(10)), 0, "receptions", "c", reps=200, tie=0.0)
    assert out["in_sample_gain"] >= 0
    assert out["oof_gain"] < out["in_sample_gain"] + 1e-12
    assert out["oof_ci"][0] < 0 < out["oof_ci"][1] or out["oof_gain"] <= 0, "no real gain out of fold"


def test_the_shipped_setting_is_kept_within_the_tie():
    truth, y = _world(seed=5)
    frames = [_frame(truth, y, 0.0, 1), _frame(truth, y, 0.0, 2)]
    assert LS.pick(frames, [0, 1], 0, "receptions", "c") == 0

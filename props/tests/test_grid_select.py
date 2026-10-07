"""props/tools/grid_select.py on worlds with a known answer, before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import grid_select as GS  # noqa: E402


def _frame(truth, y, noise, seed, n_seasons=4):
    rng = np.random.default_rng(seed)
    n = len(truth)
    pc = np.clip(truth + rng.normal(0, noise, n), 0.02, 0.98) if noise else truth
    return pd.DataFrame({"season": np.repeat(np.arange(2022, 2022 + n_seasons), n // n_seasons), "team": "T",
                         "week": np.tile(np.arange(n // n_seasons), n_seasons), "gsis_id": "p",
                         "game_id": np.arange(n) // 3, "mean_tgt": 6.0, "L_rec": 4.5,
                         "act_receptions": np.where(y, 5.0, 4.0), "pc_rec": 0.5, "pu_rec": pc,
                         "rush_pop": False, "mean_car_model": 0.0})


def _world(seed=0, n=8000):
    rng = np.random.default_rng(seed)
    truth = np.clip(0.5 + rng.normal(0, 0.15, n), 0.05, 0.95)
    return truth, rng.uniform(size=n) < truth


def test_a_better_setting_is_picked_detected_confirmed_and_guards_block_on_missing_markets():
    truth, y = _world()
    grid = [{"k": None}, {"k": 1.0}, {"k": 2.0}]
    frames = [_frame(truth, y, 0.12, 1), _frame(truth, y, 0.0, 2), _frame(truth, y, 0.25, 3)]
    r = GS.run(grid, frames, 0, "receptions", "u", [2022, 2023, 2024], [2025], ("k",), reps=300,
               min_move=0, required=("receptions",))
    assert r["pick"] == 1 and r["detectable"] and r["confirmed"] and r["ship"]
    assert r["loso"]["oof_gain"] > 0
    full = GS.run(grid, frames, 0, "receptions", "u", [2022, 2023, 2024], [2025], ("k",), reps=300, min_move=0)
    assert not full["ship"] and full["guards"]["logloss_u"]["status"] == "blocked", "missing markets block a ship"


def test_eligibility_and_the_tie_go_to_shipped_or_the_nearest_setting():
    truth, y = _world(seed=4)
    grid = [{"k": None}, {"k": 1.0}, {"k": 2.0}]
    frames = [_frame(truth, y, 0.12, 1), _frame(truth, y, 0.0, 2), _frame(truth, y, 0.0, 3)]
    r = GS.run(grid, frames, 0, "receptions", "u", [2022, 2023, 2024], [2025], ("k",), reps=200,
               eligible=[True, False, True], min_move=0, required=("receptions",))
    assert r["pick"] == 2 and 1 not in r["candidates"], "an ineligible setting is never picked"
    d = GS.knob_distance(grid, 0, ("k",))
    assert d == {0: 0, 1: 1, 2: 2}
    same = GS.run(grid, [frames[1], frames[1], frames[1]], 0, "receptions", "u", [2022, 2023, 2024], [2025],
                  ("k",), reps=200, required=("receptions",))
    assert same["pick"] == 0 and not same["ship"], "identical settings: shipped stays"

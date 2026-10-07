"""props/tools/paired_crps.py on known answers."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

import paired_crps as PC  # noqa: E402


def _ref(n=400):
    rng = np.random.default_rng(1)
    return pd.DataFrame({"season": 2024, "team": "T", "week": np.arange(n) % 17 + 1, "gsis_id": [f"p{i}" for i in range(n)],
                         "game_id": np.arange(n) // 4, "crps_rec_model": rng.uniform(0.8, 1.2, n),
                         "crps_yds_model": rng.uniform(10, 16, n), "rush_pop": False, "rr_pop": False,
                         "pass_pop": False})


def test_self_is_zero_and_a_better_candidate_gains_only_where_it_changed():
    ref = _ref()
    same = PC.pair(ref, ref, reps=100)
    assert all(v["gain"] == 0 and v["missing"] == 0 for v in same.values())
    cand = ref.copy()
    mask = pd.Series(np.arange(len(ref)) < 100, index=ref.index)
    cand.loc[mask, "crps_rec_model"] -= 0.1                  # better on the first 100 rows only
    sub = PC.pair(ref, cand, rows=mask, reps=200)["receptions"]
    allr = PC.pair(ref, cand, reps=200)["receptions"]
    assert sub["n"] == 100 and sub["gain"] == pytest.approx(0.1) and sub["ci"][0] > 0
    assert allr["gain"] == pytest.approx(0.1 * 100 / len(ref))


def test_new_team_rows_come_from_last_seasons_team(tmp_path):
    ref = pd.DataFrame({"season": [2024, 2024, 2024], "team": ["A", "B", "A"], "gsis_id": ["x", "y", "z"]})
    pd.DataFrame({"gsis_id": ["x", "y", "z"], "team_prior": ["A", "A", None]}).to_csv(
        tmp_path / "priors_2023_players.csv", index=False)
    assert PC.new_team_mask(ref, tmp_path).tolist() == [False, True, False]

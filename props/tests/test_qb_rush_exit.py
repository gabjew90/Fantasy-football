"""Round 20: the starting QB's rushing scaled by the same starter-share draw
his passing yards use (model.simulate_qb_passing(..., return_share=True),
model.QB_RUSH_EXIT)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402

GRID = np.linspace(0.2, 1.0, 51)


def _pass(return_share, seed=7):
    rng = np.random.default_rng(seed)
    ys = [np.full(500, 80.0), np.full(500, 60.0)]
    return M.simulate_qb_passing(rng, 500, ys, np.full(500, 4), {"catch_rate": 0.6, "ypt": 6.0}, 1.06,
                                 starter_share=GRID, return_share=return_share)


def test_returning_the_share_changes_no_passing_number():
    plain = _pass(False)
    total, share = _pass(True)
    assert np.array_equal(plain, total), "the same draws, whether or not the share is handed back"
    assert share.shape == (500,) and set(np.round(share, 6)) <= set(np.round(GRID, 6))


def test_no_starter_grid_means_a_full_game():
    rng = np.random.default_rng(1)
    total, share = M.simulate_qb_passing(rng, 100, [np.full(100, 50.0)], None, None, 1.06, return_share=True)
    assert np.array_equal(share, np.ones(100)) and np.allclose(total, 50.0)


def test_both_call_sites_hand_the_share_to_the_rushing():
    sg = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    bt = (ENGINE / "backtest.py").read_text(encoding="utf-8")
    assert "return_share=True" in sg and re.search(r'\["rush_yards"\] \* _qs', sg), "the scorer scales his rushing"
    assert "return_share=True" in bt and "rushM[i] * qshareM[k_]" in bt, "the harness does the same"

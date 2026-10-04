"""Round 23: target share reacts to last week's snap change (model.snap_react,
reports/snap_react.md)."""

from __future__ import annotations

import math
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402


def test_off_and_missing_inputs_leave_the_share_alone():
    assert M.snap_react(0.2, 0.9, 0.6, None) == 0.2, "gamma None = off"
    assert M.snap_react(0.2, float("nan"), 0.6, 0.5) == 0.2
    assert M.snap_react(0.2, 0.9, None, 0.5) == 0.2
    assert M.snap_react(0.2, 0.9, 0.03, 0.5) == 0.2, "a base under 5% of snaps says nothing"
    assert M.snap_react(0.2, 0.0, 0.6, 0.5) == 0.2


def test_the_share_moves_with_the_snap_ratio_to_the_power_gamma():
    assert math.isclose(M.snap_react(0.2, 0.9, 0.6, 0.5), 0.2 * (1.5 ** 0.5))
    assert math.isclose(M.snap_react(0.2, 0.63, 0.9, 1.0), 0.14)
    assert M.snap_react(0.2, 0.6, 0.6, 1.0) == 0.2, "no snap change, no move"


def test_the_move_is_clipped():
    lo, hi = M.SNAP_REACT_CLIP
    assert math.isclose(M.snap_react(0.2, 1.0, 0.2, 1.0), 0.2 * hi)
    assert math.isclose(M.snap_react(0.2, 0.1, 0.9, 1.0), 0.2 * lo)


def test_scorer_and_harness_call_the_same_rule():
    sg = (ENGINE / "score_game.py").read_text(encoding="utf-8")
    bt = (ENGINE / "backtest.py").read_text(encoding="utf-8")
    assert "MODEL.snap_react(ts, u_sr[\"snap\"], u_sr[\"snap_base\"], MODEL.SNAP_REACT," in sg
    assert "gamma_up=MODEL.SNAP_REACT_UP" in sg
    assert "u_sr[\"week\"] == WEEK - 1" in sg, "last week must be the week before this one"
    assert "M.snap_react(ts, r.get(\"snap_last\"), r.get(\"snap_base\"), sr_gamma, gamma_up=sr_up)" in bt
    assert "prev[-1, 0] != W - 1" in bt and "len(prev) < 3" in bt, "the same LAST/BASE as the scorer"


def test_a_separate_exponent_for_a_snap_increase():
    assert math.isclose(M.snap_react(0.2, 0.9, 0.6, 0.5, gamma_up=0.25), 0.2 * 1.5 ** 0.25), "increase: gamma_up"
    assert math.isclose(M.snap_react(0.2, 0.6, 0.9, 0.5, gamma_up=0.25), 0.2 * (0.6 / 0.9) ** 0.5), "decrease: gamma"
    assert M.snap_react(0.2, 0.9, 0.6, 0.5) == M.snap_react(0.2, 0.9, 0.6, 0.5, gamma_up=None), "None = round 23"


def test_completions_add_the_receivers_catches_and_never_move_the_parent_stream():
    import numpy as np
    rng = np.random.default_rng(1)
    before = np.random.default_rng(1).random()
    c = M.simulate_qb_completions(rng, 4000, [np.full(4000, 5.0), np.full(4000, 3.0)], np.full(4000, 4),
                                  {"catch_rate": 0.5, "ypt": 6.0})
    assert abs(c.mean() - 10.0) < 0.1, "5 + 3 + half of 4 depth targets"
    assert float(np.all(c == np.round(c))) == 1.0, "whole catches"
    assert rng.random() == before, "spawn does not advance the parent stream"

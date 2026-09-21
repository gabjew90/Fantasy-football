"""The shadow market blend: fitted on settled v1 anytime-TD calls within one
engine version; silent below MIN_CALLS; recovers known weights."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
pd = pytest.importorskip("pandas")
import blend  # noqa: E402


def _calls(n, seed=0, b_model=0.4, b_market=0.8):
    rng = np.random.default_rng(seed)
    lm, lk = rng.normal(-1.5, 0.8, n), rng.normal(-1.5, 0.8, n)
    p = 1 / (1 + np.exp(-(0.1 + b_model * lm + b_market * lk)))
    return pd.DataFrame({"market": "player_anytime_td", "td_model": "anytime_td_v1",
                         "p_model": 1 / (1 + np.exp(-lm)), "p_novig": 1 / (1 + np.exp(-lk)),
                         "won": (rng.random(n) < p).astype(int), "event_id": rng.integers(0, n // 8, n),
                         "week": rng.integers(1, 10, n)})


def test_too_few_calls_prints_no_weight():
    out = "\n".join(blend.blend_section(_calls(100)))
    assert "not estimated below" in out and "logit(model)" not in out


def test_the_fit_recovers_known_weights():
    d = _calls(20000, seed=1)
    X = np.column_stack([np.ones(len(d)), blend._logit(d["p_model"]), blend._logit(d["p_novig"])])
    w = blend.fit(X, d["won"].to_numpy(float))
    assert w[1] == pytest.approx(0.4, abs=0.08) and w[2] == pytest.approx(0.8, abs=0.08)


def test_only_v1_anytime_calls_enter():
    d = pd.concat([_calls(50), _calls(50).assign(td_model="anytime_td_v0"),
                   _calls(50).assign(market="player_receptions")])
    assert len(blend.v1_td_calls(d)) == 50


def test_the_section_reports_weights_and_out_of_sample_loss():
    out = "\n".join(blend.blend_section(_calls(800, seed=2), reps=50))
    assert "logit(market)" in out and "Leave-one-week-out log loss" in out

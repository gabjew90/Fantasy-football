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


def test_each_book_gets_its_own_intercept():
    a = _calls(600, seed=3).assign(book="sleeper")
    b = _calls(600, seed=4).assign(book="draftkings")
    out = "\n".join(blend.blend_section(pd.concat([a, b]), reps=30))
    assert "books draftkings, sleeper" in out


def _yard_calls(n, seed=0, b_model=0.3, b_market=1.0):
    rng = np.random.default_rng(seed)
    lk = rng.normal(0.1, 0.25, n)
    lm = lk + rng.normal(0.15, 0.3, n)          # the model leans off the market
    p = 1 / (1 + np.exp(-(b_model * lm + b_market * lk)))
    return pd.DataFrame({"market": rng.choice(list(blend.YARDAGE_MARKETS), n), "book": "sleeper",
                         "p_model": 1 / (1 + np.exp(-lm)), "p_novig": 1 / (1 + np.exp(-lk)),
                         "won": (rng.random(n) < p).astype(float), "event_id": rng.integers(0, n // 20, n),
                         "week": rng.integers(1, 8, n)})


def test_yardage_calls_get_their_own_section_and_pushes_drop_out():
    d = _yard_calls(900, seed=5)
    d.loc[:9, "won"] = np.nan                       # pushes
    assert len(blend.yardage_calls(pd.concat([d, _calls(40)]))) == 890
    out = "\n".join(blend.blend_section(d, reps=30))
    assert "settled yardage calls" in out and "per market" in out and "Leave-one-week-out" in out
    assert "0 settled anytime_td_v1 calls" in out


def test_thin_yardage_record_prints_no_weight():
    out = "\n".join(blend.blend_section(_yard_calls(120)))
    assert "120 settled yardage calls" in out and "logit(model)" not in out


def test_one_settled_week_says_so_instead_of_nan():
    out = "\n".join(blend.blend_section(_yard_calls(600, seed=7).assign(week=2), reps=20))
    assert "needs at least two (1 settled so far)" in out and "nan" not in out


def test_a_tiny_or_one_sided_market_shares_the_base_intercept():
    d = _yard_calls(900, seed=8).assign(market="player_receptions")
    tiny = _yard_calls(200, seed=9).head(12).assign(market="player_pass_yds", won=0.0)   # all lost: separable
    out = "\n".join(blend.blend_section(pd.concat([d, tiny], ignore_index=True), reps=20))
    assert "912 settled yardage calls" in out and "fit failed" not in out
    w_line = next(l for l in out.splitlines() if l.startswith("| logit(model)"))
    assert "inf" not in w_line and "nan" not in w_line
    assert len(blend._level_dummies(np.array(["a"] * 40 + ["b"] * 5), np.r_[np.ones(20), np.zeros(25)])) == 0


def test_one_market_family_fits_without_a_market_dummy():
    d = _yard_calls(700, seed=10).assign(market="player_reception_yds")
    out = "\n".join(blend.blend_section(d, reps=20))
    assert "700 settled yardage calls" in out and "logit(market)" in out


def test_a_failed_fit_is_reported_not_raised(monkeypatch):
    def boom(*_a, **_k):
        raise np.linalg.LinAlgError("Singular matrix")
    monkeypatch.setattr(blend, "fit", boom)
    out = "\n".join(blend.blend_section(_yard_calls(400, seed=11), reps=5))
    assert "the blend fit failed (LinAlgError" in out


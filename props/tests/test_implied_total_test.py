"""Tier 3 implied-total test (reports/implied_total_test.md): checked on worlds with a
known answer before the real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import implied_total_test as IT  # noqa: E402


def _world(b_true, seed=0):
    rng = np.random.default_rng(seed)
    rows = []
    for season in (2022, 2023, 2024, 2025):
        for t in range(32):
            for w in range(1, 18):
                ratio = np.exp(rng.normal(0, 0.12))
                act = 180 * ratio ** b_true * np.exp(rng.normal(-0.35 ** 2 / 2, 0.35))
                rows.append({"season": season, "team": f"T{t}", "week": w, "ratio": ratio,
                             "receivers' receiving yards|act": act, "receivers' receiving yards|mod": 180.0})
    return pd.DataFrame(rows)


def _verdict(d):
    rng = np.random.default_rng(1)
    per = {p: IT.slope(d[d.season.isin(ss)], "receivers' receiving yards", 400, rng)
           for p, ss in IT.BI.PERIODS.items()}
    return per, IT.verdict(per)


def test_a_model_that_ignores_real_market_information_is_caught():
    per, v = _verdict(_world(0.6))
    assert all(abs(p["b"] - 0.6) < 0.25 for p in per.values())
    assert v == "the implied total carries information the model lacks"


def test_a_model_that_already_uses_it_reads_does_not():
    _per, v = _verdict(_world(0.0))
    assert v == "it does not"


def test_implied_ratio_uses_only_earlier_games():
    imp = pd.DataFrame({"season": 2023, "team": "KC", "week": [1, 2, 3], "implied": [24.0, 30.0, 27.0]})
    r = IT.implied_ratios(imp)
    assert r.week.tolist() == [2, 3]
    assert r.ratio.tolist() == [30.0 / 24.0, 27.0 / 27.0], "week 3 against the mean of weeks 1-2"

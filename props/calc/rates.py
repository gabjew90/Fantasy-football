"""The per-play rates, each with a known-answer test
(props/tests_ci/test_calc_sanity.py). Every input is checked for missing values."""

from __future__ import annotations

import numpy as np

from .checks import finite, require


def yards_per_carry(yards) -> float:
    finite("carry yards", yards)
    return float(np.mean(np.asarray(yards, dtype=float)))


def catch_rate(caught) -> float:
    a = np.asarray(caught, dtype=float)
    finite("caught flags", a)
    require(set(np.unique(a)) <= {0.0, 1.0}, "caught flags must be 0 or 1")
    return float(a.mean())


def yards_per_target(yards, caught) -> float:
    """Receiving yards per target, an incompletion counting as 0 yards
    (nflverse leaves NaN there). A catch with missing yards is an error."""
    y = np.asarray(yards, dtype=float)
    f = np.asarray(caught, dtype=float)
    require(len(y) == len(f) and len(y) > 0, "yards and caught flags must be the same, non-empty length")
    finite("caught flags", f)
    require(set(np.unique(f)) <= {0.0, 1.0}, "caught flags must be 0 or 1")
    c = f == 1.0
    require(np.isfinite(y[c]).all(), "a catch has missing or infinite receiving yards")
    return float(np.where(c, np.nan_to_num(y, nan=0.0), 0.0).mean())


def blend(own_sum: float, n: int, baseline: float, k: float) -> float:
    """w * own + (1 - w) * baseline with w = n / (n + k), written as
    (own_sum + k * baseline) / (n + k)."""
    finite("baseline", [baseline])
    require(n >= 0 and k > 0, "n must be 0 or more and k above 0")
    return (own_sum + k * baseline) / (n + k)

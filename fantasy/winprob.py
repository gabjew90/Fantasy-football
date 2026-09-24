"""Win probability for a weekly matchup, from the players' ranges.

Each starter's week is drawn from his projection's quantiles (an inverse CDF
that is linear between p10/p25/p50/p75/p90, with tails extended at the slope
of the neighbouring segment, the upper one wider because fantasy weeks are
right-skewed). A lineup's total is the sum; P(win) is the share of draws in
which mine beats theirs.

This is the user's start/sit rule with the arithmetic done: when I am likely
to win, the lineup that maximises P(win) is the one whose bad weeks are least
bad; when I am likely to lose, the one whose good weeks are best. Nothing
here encodes "floor" or "ceiling" as a mode -- they fall out of maximising
the probability.

Assumptions, stated wherever a P(win) is shown: players are independent (no
same-game or same-team correlation yet -- a stack's variance is understated),
and the opponent starts the lineup they have set, or their best-by-mean one
when they have not set a full one.
"""

from __future__ import annotations

import zlib

import numpy as np

from .contract import QUANTILES

N_DRAWS = 20000
_U = np.array([0.0, *QUANTILES, 1.0])


def _knots(q: dict, mean: float | None = None) -> np.ndarray:
    """Inverse-CDF knots at _U, CENTRED on `mean` and floored.

    Centred: the quantiles come from the range model, whose residuals carry
    the source's bias (2025 outcomes ran under Sleeper's projections), so the
    raw distribution's mean is not the projection the lineup was chosen on.
    P(win) and the headline totals must describe the same expectation, so
    the shape is kept and its location moved to `mean` (code review
    2026-09-24). Floored: the lower tail never runs below min(p10, 0) --
    extending it past a zero floor drew weeks the range model itself rules
    out."""
    p10, p25, p50, p75, p90 = (float(q[x]) for x in QUANTILES)
    floor = min(p10, 0.0)                        # from the ORIGINAL range, not the shifted one
    lo = max(p10 - (p25 - p10) * (0.10 / 0.15), floor)
    hi = p90 + (p90 - p75) * (0.10 / 0.15) * 1.5
    k = np.array([lo, p10, p25, p50, p75, p90, hi])
    if mean is None:
        return k

    def mean_at(shift):
        s = np.maximum(k + shift, floor)
        return float(np.sum(np.diff(_U) * (s[:-1] + s[1:]) / 2))
    # the floored mean rises monotonically with the shift: bisect for the shift
    # that puts it on `mean` (a floor can make an exact hit impossible only for
    # a mean below the floor itself, where the lowest shift is the answer)
    a, b = -abs(hi - floor) - abs(float(mean)) - 1.0, abs(hi - floor) + abs(float(mean)) + 1.0
    for _ in range(60):
        mid = (a + b) / 2
        if mean_at(mid) < float(mean):
            a = mid
        else:
            b = mid
    return np.maximum(k + (a + b) / 2, floor)


def draws(proj, n: int = N_DRAWS, seed: int = 0) -> np.ndarray:
    """n draws of one player's week. A projection without a range (mean only)
    is drawn as its mean; a zero projection (out, bye) as zero. The seed is
    per player, so every candidate lineup sees the same draw for the same
    player (common random numbers: the comparison between lineups is not
    swamped by simulation noise)."""
    if proj is None or not proj.quantiles:
        return np.full(n, float(proj.mean) if proj is not None else 0.0)
    rng = np.random.default_rng(seed)
    return np.interp(rng.random(n), _U, _knots(proj.quantiles, proj.mean))


def _seed(pid: str, base: int) -> int:
    return (zlib.crc32(str(pid).encode()) + base) % (2 ** 32)


def lineup_total(pids, projections: dict, n: int = N_DRAWS, base_seed: int = 1) -> np.ndarray:
    tot = np.zeros(n)
    for pid in pids:
        tot += draws(projections.get(str(pid)), n, _seed(pid, base_seed))
    return tot


def p_win(mine, theirs, projections: dict, n: int = N_DRAWS) -> float:
    """P(my lineup outscores theirs). Ties count half."""
    a = lineup_total(mine, projections, n, base_seed=1)
    b = lineup_total(theirs, projections, n, base_seed=2)
    return float(np.mean(a > b) + 0.5 * np.mean(a == b))

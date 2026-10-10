"""The calculator: the chance a player clears a line given his workload W,
and the searches that turn a price back into a workload or a rate.

Every draw is fixed in advance (common random numbers, one seed), so the
chance is a smooth function of W and of his rate, the searches are plain
bisections, and the same inputs always give the same card.

Rushing yards: carries ~ negative binomial (mean W, spread carry_r); each
  carry gains his yards per carry plus a residual drawn from real RB carries
  (centred on zero); the game total is multiplied by one good-day/bad-day
  factor (lognormal, mean 1, sd day_sd).
Receptions: targets ~ negative binomial (mean W, spread target_r); each target
  is caught at his catch rate.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

MAX_COUNT = {"carries": 80, "targets": 40, "completions": 60}
SEARCH_MAX = {"carries": 45.0, "targets": 25.0, "completions": 45.0}
BISECT_STEPS = 40


@dataclass(frozen=True)
class Draws:
    """Fixed random numbers for one workload type."""
    gamma: np.ndarray      # (sims,) Gamma(r, 1/r): the game's workload multiplier, mean 1
    u_count: np.ndarray    # (sims,) uniform: picks the count from the Poisson
    u_play: np.ndarray     # (sims, max) uniform: per-play draws (catch or not, which residual)
    z_day: np.ndarray      # (sims,) standard normal: the good-day/bad-day factor


def make_draws(kind: str, r: float, sims: int, seed: int) -> Draws:
    # one stream per workload type, so adding a market never shifts another's draws
    rng = np.random.default_rng([seed, list(MAX_COUNT).index(kind)])
    return Draws(gamma=rng.gamma(r, 1.0 / r, sims), u_count=rng.random(sims),
                 u_play=rng.random((sims, MAX_COUNT[kind])), z_day=rng.standard_normal(sims))


def poisson_inverse(u: np.ndarray, lam: np.ndarray, kmax: int) -> np.ndarray:
    """The Poisson(lam) count at cumulative probability u, capped at kmax.
    Increasing in lam for a fixed u, which keeps the chance smooth in W."""
    lam = np.maximum(lam, 1e-12)
    pmf = np.exp(-lam)
    cdf = pmf.copy()
    n = np.zeros(lam.shape, dtype=int)
    for k in range(1, kmax + 1):
        n += cdf < u
        pmf = pmf * lam / k
        cdf = cdf + pmf
    return n


def counts(draws: Draws, w: float, kmax: int) -> np.ndarray:
    """Negative-binomial counts with mean w (gamma-Poisson)."""
    return poisson_inverse(draws.u_count, w * draws.gamma, kmax)


def fixed_counts(draws: Draws, n: int) -> np.ndarray:
    """No workload variation: exactly n plays in every simulated game."""
    return np.full(draws.gamma.shape, int(n))


def day_factor(draws: Draws, sd: float) -> np.ndarray:
    """Lognormal with mean 1 and standard deviation `sd`."""
    s = np.sqrt(np.log1p(sd * sd))
    return np.exp(s * draws.z_day - s * s / 2)


# ------------------------------------------------------------------ outcomes

def receptions(draws: Draws, n: np.ndarray, catch_rate: float) -> np.ndarray:
    caught = np.concatenate([np.zeros((len(n), 1)), np.cumsum(draws.u_play < catch_rate, axis=1)], axis=1)
    return caught[np.arange(len(n)), n]


# ------------------------------------------------------------------ the model

@dataclass
class Model:
    """One player-market with his rates and the pools it draws from."""
    market: str                      # rush_yds | receptions
    kind: str                        # carries | targets
    draws: Draws
    rate: float                      # ypc (rushing) or catch rate (receptions)
    residuals: np.ndarray | None = None
    day_sd: float = 0.0
    _resid_run: np.ndarray | None = field(default=None, init=False, repr=False)
    _counts: dict = field(default_factory=dict, init=False, repr=False)

    def _counts_at(self, w: float) -> np.ndarray:
        """Counts for average workload w, computed once per w (the rate search
        evaluates the same w many times)."""
        if w not in self._counts:
            self._counts[w] = counts(self.draws, w, MAX_COUNT[self.kind])
        return self._counts[w]

    def _rushing(self, n: np.ndarray, ypc: float) -> np.ndarray:
        if self._resid_run is None:       # independent of W and of the rate: built once
            res = self.residuals
            idx = np.minimum((self.draws.u_play * len(res)).astype(int), len(res) - 1)
            self._resid_run = np.concatenate([np.zeros((len(idx), 1)), np.cumsum(res[idx], axis=1)], axis=1)
        resid_sum = self._resid_run[np.arange(len(n)), n]
        return day_factor(self.draws, self.day_sd) * (n * ypc + resid_sum)

    def outcome(self, n: np.ndarray, rate: float | None = None) -> np.ndarray:
        r = self.rate if rate is None else rate
        if self.market == "rush_yds":
            return self._rushing(n, r)
        if self.market == "receptions":
            return receptions(self.draws, n, r)
        raise ValueError(f"market {self.market} is not built yet")

    def chance_over(self, line: float, w: float, rate: float | None = None) -> float:
        return float(np.mean(self.outcome(self._counts_at(w), rate) > line))

    def chance_over_fixed(self, line: float, n: int, rate: float | None = None) -> float:
        return float(np.mean(self.outcome(fixed_counts(self.draws, n), rate) > line))

    def outcomes_fixed(self, n: int, rate: float | None = None) -> np.ndarray:
        return self.outcome(fixed_counts(self.draws, n), rate)

    def workload_range(self, w: float, lo_pct: float, hi_pct: float) -> tuple[float, float]:
        n = counts(self.draws, w, MAX_COUNT[self.kind])
        return float(np.percentile(n, lo_pct)), float(np.percentile(n, hi_pct))


def _bisect(f, lo: float, hi: float, target: float) -> float | None:
    """x in [lo, hi] with f(x) = target for an increasing f; None if out of reach."""
    flo, fhi = f(lo), f(hi)
    if target <= flo:
        return lo
    if target > fhi:
        return None
    for _ in range(BISECT_STEPS):
        mid = (lo + hi) / 2
        if f(mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def workload_for(model: Model, line: float, p_over: float) -> float | None:
    """The average workload W at which the Over's chance is p_over (None when
    even the search's top workload falls short)."""
    return _bisect(lambda w: model.chance_over(line, w), 0.0, SEARCH_MAX[model.kind], p_over)


def rate_for(model: Model, line: float, p_over: float, w: float) -> float | None:
    """The rate (yards per carry, catch rate) at which the Over's chance at
    average workload w is p_over."""
    hi = 1.0 if model.market == "receptions" else 25.0
    lo = 0.0 if model.market == "receptions" else -5.0
    return _bisect(lambda r: model.chance_over(line, w, rate=r), lo, hi, p_over)

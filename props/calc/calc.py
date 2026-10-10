"""The calculator: the chance a player clears a line given his workload W,
and the searches that turn a price back into a workload or a rate.

Every draw is fixed in advance (common random numbers, one seed), so the
same inputs always give the same card and the searches are plain bisections.
The chance searched is the Over's share of the decided games (a push is void,
as Sleeper treats it); it rises with W and with his rate, in small steps
(counts are whole plays and rushing yards whole yards).

Rushing yards: carries ~ negative binomial (mean W, spread carry_r); each
  carry gains his yards per carry plus a residual drawn from real RB carries
  (centred on zero); the game total is multiplied by one good-day/bad-day
  factor (lognormal, mean 1, sd day_sd).
Receptions: targets ~ negative binomial (mean W, spread target_r); each target
  is caught at his catch rate.
Receiving yards: targets and catches as receptions; each catch gets a depth
  (short / medium / deep) from his own mix of catches by depth, and yards drawn
  from real catches by his position at that depth, all scaled so a catch
  averages his yards per target / catch rate. The rate searched is yards a
  target (an incompletion counts as 0). No good-day factor (design note #7).
"""

from __future__ import annotations

import functools
from dataclasses import dataclass, field
from types import MappingProxyType

import numpy as np

from . import settings as _settings
from .checks import DataError

# one random stream per workload type, by a fixed id (never by the order of a
# yaml mapping), so adding or reordering anything never shifts another's draws
STREAM = {"carries": 0, "targets": 1, "completions": 2}


@dataclass(frozen=True)
class Limits:
    """The search and simulation bounds from settings.yaml (fixed_not_tuned)."""
    max_count: dict
    search_max: dict
    rate_range: dict
    bisect_steps: int

    @classmethod
    def from_fixed(cls, fixed: dict) -> "Limits":
        ro = MappingProxyType                     # read-only, so a shared default cannot be changed in place
        return cls(ro({k: int(v) for k, v in fixed["max_count"].items()}),
                   ro({k: float(v) for k, v in fixed["search_max"].items()}),
                   ro({k: (float(v[0]), float(v[1])) for k, v in fixed["rate_range"].items()}),
                   int(fixed["bisect_steps"]))


@functools.lru_cache(maxsize=1)
def default_limits() -> Limits:
    """settings.yaml's bounds, read on first use (not when the module is
    imported, so a command that never simulates does not depend on them)."""
    return Limits.from_fixed(_settings.load()["fixed"])


@dataclass(frozen=True)
class Draws:
    """Fixed random numbers for one workload type."""
    gamma: np.ndarray      # (sims,) Gamma(r, 1/r): the game's workload multiplier, mean 1
    u_count: np.ndarray    # (sims,) uniform: picks the count from the Poisson
    u_play: np.ndarray     # (sims, max) uniform: per-play draws (catch or not, which residual)
    z_day: np.ndarray      # (sims,) standard normal: the good-day/bad-day factor
    limits: "Limits"       # the bounds these draws were made for (the model reads them from here)
    u_depth: np.ndarray | None = None   # (sims, max) uniform: each catch's depth (receiving yards only)
    u_yard: np.ndarray | None = None    # (sims, max) uniform: which real catch it draws its yards from


def make_draws(kind: str, r: float, sims: int, seed: int, limits: Limits | None = None,
               yards: bool = False) -> Draws:
    """yards: also draw each catch's depth and yards, from a separate stream, so
    the receptions draws are the same with or without them."""
    limits = limits or default_limits()
    rng = np.random.default_rng([seed, STREAM[kind]])
    base = dict(gamma=rng.gamma(r, 1.0 / r, sims), u_count=rng.random(sims),
                u_play=rng.random((sims, limits.max_count[kind])), z_day=rng.standard_normal(sims), limits=limits)
    if yards:
        y = np.random.default_rng([seed, STREAM[kind], 1])
        base.update(u_depth=y.random((sims, limits.max_count[kind])), u_yard=y.random((sims, limits.max_count[kind])))
    return Draws(**base)


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


# ------------------------------------------------------------------ the model

@dataclass
class Model:
    """One player-market with his rates and the pools it draws from."""
    market: str                      # rush_yds | receptions | rec_yds
    kind: str                        # carries | targets
    draws: Draws
    rate: float                      # ypc (rushing), catch rate (receptions), yards a target (rec_yds)
    residuals: np.ndarray | None = None
    day_sd: float = 0.0
    catch: float | None = None       # rec_yds: his catch rate, held fixed
    depth_mix: tuple | None = None   # rec_yds: his share of catches short / medium / deep
    catch_pools: tuple | None = None  # rec_yds: real catch yards at his position, per depth, as arrays
    _yards: np.ndarray | None = field(default=None, init=False, repr=False)   # running base yards
    _resid_run: tuple | None = field(default=None, init=False, repr=False)    # (residuals id, sums)
    _day: tuple | None = field(default=None, init=False, repr=False)          # (day_sd, factors)
    _caught: tuple | None = field(default=None, init=False, repr=False)       # (catch rate, running catches)
    _counts: dict = field(default_factory=dict, init=False, repr=False)

    @property
    def limits(self) -> Limits:
        """One source: the bounds the draws were made with."""
        return self.draws.limits

    def _counts_at(self, w: float) -> np.ndarray:
        """Counts for average workload w, computed once per w (the rate search
        evaluates the same w many times)."""
        if w in self._counts:
            self._counts[w] = self._counts.pop(w)            # most recently used last
        else:
            if len(self._counts) >= 64:   # the three searches share their first midpoints; keep the recent ones
                self._counts.pop(next(iter(self._counts)))
            self._counts[w] = counts(self.draws, w, self.limits.max_count[self.kind])
        return self._counts[w]

    def _rushing(self, n: np.ndarray, ypc: float) -> np.ndarray:
        res = self.residuals
        if self._resid_run is None or self._resid_run[0] is not res:   # rebuilt if the residuals change
            idx = np.minimum((self.draws.u_play * len(res)).astype(int), len(res) - 1)
            self._resid_run = (res, np.concatenate([np.zeros((len(idx), 1)), np.cumsum(res[idx], axis=1)], axis=1))
        resid_sum = self._resid_run[1][np.arange(len(n)), n]
        if self._day is None or self._day[0] != self.day_sd:          # rebuilt if day_sd changes
            self._day = (self.day_sd, day_factor(self.draws, self.day_sd))
        # whole yards, as the box score counts them (so a whole-number line can push);
        # on a half-point line this changes nothing
        return np.floor(self._day[1] * (n * ypc + resid_sum) + 0.5)

    def outcome(self, n: np.ndarray, rate: float | None = None) -> np.ndarray:
        r = self.rate if rate is None else rate
        if self.market == "rush_yds":
            return self._rushing(n, r)
        if self.market == "receptions":
            if self._caught is None or self._caught[0] != r:     # per catch rate, not per workload
                self._caught = (r, np.concatenate([np.zeros((len(n), 1)),
                                                   np.cumsum(self.draws.u_play < r, axis=1)], axis=1))
            return self._caught[1][np.arange(len(n)), n]
        if self.market == "rec_yds":
            base, mean_mix = self._receiving_base()
            scale = (r / self.catch) / mean_mix          # a catch then averages r / catch rate yards
            # whole yards, as the box score counts them
            return np.floor(scale * base[np.arange(len(n)), n] + 0.5)
        raise ValueError(f"market {self.market} is not built yet")

    def _receiving_base(self) -> tuple:
        """Running unscaled receiving yards per simulated game (built once):
        play j is caught at his catch rate, its depth drawn from his mix and its
        yards from the real catches at that depth. Returns (running sums,
        the mix's average catch)."""
        if self._yards is None:
            d = self.draws
            if d.u_depth is None or d.u_yard is None:
                raise DataError("receiving-yards draws are missing (make_draws(..., yards=True))")
            mix = np.asarray(self.depth_mix, dtype=float)
            if not (np.isfinite(mix).all() and mix.min() >= 0 and abs(mix.sum() - 1) < 1e-9):
                raise DataError(f"his depth mix {self.depth_mix} is not a set of shares summing to 1")
            pools = [np.sort(np.asarray(p, dtype=float)) for p in self.catch_pools]
            mean_mix = float(sum(m * p.mean() for m, p in zip(mix, pools) if m > 0))
            if not mean_mix > 0:
                raise DataError(f"the average catch at his depth mix is {mean_mix:.2f} yards; cannot scale to it")
            bucket = np.searchsorted(np.cumsum(mix)[:-1], d.u_depth, side="right")
            y0 = np.zeros(d.u_yard.shape)
            for b, p in enumerate(pools):
                m = bucket == b
                if m.any():
                    y0[m] = p[np.minimum((d.u_yard[m] * len(p)).astype(int), len(p) - 1)]
            caught = d.u_play < self.catch
            run = np.cumsum(np.where(caught, y0, 0.0), axis=1)
            self._yards = (np.concatenate([np.zeros((len(run), 1)), run], axis=1), mean_mix)
        return self._yards

    def outcomes_fixed(self, n: int, rate: float | None = None) -> np.ndarray:
        return self.outcome(fixed_counts(self.draws, n), rate)


@dataclass(frozen=True)
class Solution:
    """Where an increasing f reaches a target inside [lo, hi].
    status "ok": at `value`; "low": already at lo (any value in range reaches
    it); "high": not even at hi (no value in range reaches it)."""
    value: float | None
    status: str


def _bisect(f, lo: float, hi: float, target: float, steps: int) -> Solution:
    flo, fhi = f(lo), f(hi)
    if target <= flo:
        return Solution(lo, "low")
    if target > fhi:
        return Solution(None, "high")
    a, b = lo, hi
    for _ in range(steps):
        mid = (a + b) / 2
        if f(mid) < target:
            a = mid
        else:
            b = mid
    return Solution((a + b) / 2, "ok")


def _share(out: np.ndarray, line: float) -> float:
    po, pu = float(np.mean(out > line)), float(np.mean(out < line))
    if po + pu == 0:
        raise DataError(f"no simulated game is decided at line {line}: every outcome equals it")
    return po / (po + pu)


def over_share(model: Model, line: float, w: float, rate: float | None = None) -> float:
    """The Over's share of the decided games, P(over) / (P(over) + P(under)).
    A push is void (Sleeper drops a pushed leg), so it counts for neither
    side; on a half-point line this is just P(over)."""
    return _share(model.outcome(model._counts_at(w), rate), line)


def side_result(side: str, status: str) -> str:
    """What a search result means for one side: "ok" (a value was found),
    "always" (that side wins often enough anywhere in range) or "never".
    Searches solve for the Over's share, so for the Under "low" (the Over
    already clears at the bottom of the range) means never, "high" always."""
    if status == "ok":
        return "ok"
    if side == "over":
        return "always" if status == "low" else "never"
    return "never" if status == "low" else "always"


def solve_workload(model: Model, line: float, p: float) -> Solution:
    """The average workload W at which over_share is p. For the Under's target
    t, pass 1 - t."""
    lim = model.limits
    return _bisect(lambda w: over_share(model, line, w), 0.0, lim.search_max[model.kind], p, lim.bisect_steps)


def solve_rate(model: Model, line: float, p: float, w: float) -> Solution:
    """The rate at which over_share at average workload w is p."""
    lo, hi = model.limits.rate_range[model.market]
    return _bisect(lambda r: over_share(model, line, w, rate=r), lo, hi, p, model.limits.bisect_steps)

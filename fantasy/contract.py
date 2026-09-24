"""The projection contract: every projection is a distribution.

A source returns, per player and horizon, a mean and -- when it knows them --
quantiles at QUANTILES. A mean-only source leaves `quantiles` empty; the range
model (fantasy/dispersion.py) supplies a calibrated range for it, and says it
did. Consumers read the distribution, so "floor" and "ceiling" are computed
percentiles, never adjectives.

Why the contract is a distribution from day one (plan section 3): if the
interface were a single number, adding dispersion or correlation later would
break every consumer and invite a second engine beside the first. With a
distribution, it is a version bump behind the same interface.

Uncertainty is reported in three separate parts, never folded into one:
  source disagreement   how far the sources' means spread (report column)
  dispersion            how far one week's outcome scatters around a mean
  role uncertainty      whether the role itself holds (the evidence table)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

QUANTILES: tuple[float, ...] = (0.10, 0.25, 0.50, 0.75, 0.90)
WEEK = "week"
REST_OF_SEASON = "ros"


FANTASY_POSITIONS = ("QB", "RB", "WR", "TE", "K", "DEF")


def fantasy_position(player: dict | None) -> str | None:
    """The position a player is scored at. Sleeper lists a two-way player's
    defensive slot first (Travis Hunter: fantasy_positions ['DB', 'WR']), so
    the first FANTASY position wins, not the first listed one; a fullback is
    scored as an RB."""
    p = player or {}
    listed = [x for x in (p.get("fantasy_positions") or []) if x] + [p.get("position")]
    for x in listed:
        if x == "FB":
            return "RB"
        if x in FANTASY_POSITIONS:
            return x
    return None


class ContractError(ValueError):
    """A source returned something the contract does not allow."""


@dataclass(frozen=True)
class Projection:
    player_id: str                    # Sleeper id: the one id the fantasy side keys on
    source: str                       # registry component name
    horizon: str                      # WEEK or REST_OF_SEASON
    mean: float
    quantiles: dict = field(default_factory=dict)   # {q: points} for q in QUANTILES, or {}
    detail: dict = field(default_factory=dict)      # source-specific inputs and flags
    range_from: str = ""              # who supplied the quantiles: the source, or the range model

    def q(self, level: float) -> float | None:
        return self.quantiles.get(level)

    @property
    def floor(self) -> float | None:
        """The 10th percentile: the bad-week outcome the start/sit rule compares."""
        return self.q(0.10)

    @property
    def ceiling(self) -> float | None:
        """The 90th percentile: the good-week outcome."""
        return self.q(0.90)


@dataclass
class SourceResult:
    source: str
    horizon: str
    projections: dict = field(default_factory=dict)  # player_id -> Projection
    notes: list = field(default_factory=list)        # what degraded, what was not covered
    available: bool = True                            # False: the source produced nothing usable


def validate(p: Projection) -> Projection:
    """Raise ContractError unless `p` is coherent: finite mean, known horizon,
    quantiles either absent or complete, finite and non-decreasing."""
    if not p.player_id:
        raise ContractError("projection without a player id")
    if p.horizon not in (WEEK, REST_OF_SEASON):
        raise ContractError(f"{p.player_id}: unknown horizon {p.horizon!r}")
    if not (isinstance(p.mean, (int, float)) and math.isfinite(p.mean)):
        raise ContractError(f"{p.player_id}: non-finite mean {p.mean!r}")
    if p.quantiles:
        if set(p.quantiles) != set(QUANTILES):
            raise ContractError(f"{p.player_id}: quantiles {sorted(p.quantiles)} != {list(QUANTILES)}")
        vals = [p.quantiles[q] for q in QUANTILES]
        if not all(math.isfinite(v) for v in vals):
            raise ContractError(f"{p.player_id}: non-finite quantile")
        if any(b < a - 1e-9 for a, b in zip(vals, vals[1:])):
            raise ContractError(f"{p.player_id}: quantiles decrease {vals}")
        if not p.range_from:
            raise ContractError(f"{p.player_id}: quantiles without range_from")
    return p

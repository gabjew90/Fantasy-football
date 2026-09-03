"""Weekly projection composer (season spec §1, revised).

The baseline is market-grade (Sleeper weekly projection, or season/16 when
placeholders are live); the edge layers MODIFY the number with hard caps:

    weekly = base × matchup_mult(±cap) × (1 + adj) × availability

- matchup_mult: opponent points-allowed ratio vs league average, shrunk hard
  early season (weeks/(weeks+shrink)); capped ±matchup_cap. Halve the cap in
  config if the week 1-3 regression shows Sleeper's baseline is already
  matchup-aware (double-count guard from the external review).
- adj: a multiplicative adjustment slot; the only caller (briefs.py) passes
  0.0. The usage-trend factor that once filled it was removed 2026-09-02
  (never wired to data).
- availability: hard gate. Out/IR/PUP/Suspended = 0. Questionable plays.

Pure functions; every network/frame concern lives in seasondata.py.
"""

from __future__ import annotations

GATED_OUT = ("Out", "IR", "PUP", "Sus", "Suspended", "NA", "COV")


def shrunk_ratio(ratio: float, weeks: int, shrink_weeks: int) -> float:
    w = weeks / (weeks + shrink_weeks)
    return w * ratio + (1.0 - w) * 1.0


def matchup_mult(ratio: float | None, weeks: int, cap: float, shrink_weeks: int) -> float:
    if ratio is None:
        return 1.0
    return min(1.0 + cap, max(1.0 - cap, shrunk_ratio(ratio, weeks, shrink_weeks)))


def compose(base: float, mult: float, adj: float, status: str) -> float:
    if status in GATED_OUT:
        return 0.0
    return base * mult * (1.0 + adj)

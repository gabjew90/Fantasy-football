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


# ------------------------------------------------------------ rest of season

def weeks_remaining(week: int, last_week: int) -> int:
    """Fantasy weeks left INCLUDING the current one, floored at zero.

    `last_week` is the championship week, not week 18: a week-10 waiver claim
    is bought for the title, and points scored after the league has crowned a
    winner are worth nothing.
    """
    return max(0, int(last_week) - int(week) + 1)


def ros_prorate(season_pts: float, week: int, last_week: int) -> float:
    """A season projection, cut down to the part of it still ahead.

    The field the manager calls `ros` held a SEASON TOTAL at every week, which
    is wrong by inspection at every week past the first: in week 14 it valued
    a free agent for eleven games he can no longer play, and the bid model,
    the league-winner classification and the drop comparison all read it.

    Deliberately no `games` parameter, though the plan named one. Dividing a
    16-game projection by 16 while the fantasy season runs `last_week` weeks
    makes week 1 return 17/16 of the season total, and the acceptance
    criterion for this change is that week 1 reproduces today's numbers
    exactly. Spreading the season total evenly across the fantasy weeks does
    that, and the bye it ignores is already handled as its own zero.
    """
    total = max(1, int(last_week))
    return float(season_pts or 0.0) * weeks_remaining(week, last_week) / total

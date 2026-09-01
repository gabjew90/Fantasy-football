"""In-season age decay for ROS values (post-v2 item 4).

A 31-year-old RB's rest-of-season value should erode faster across the year
than a 24-year-old's. Draft-day age handling exists as capped standing tilts;
this is the in-season analog.

SCOPE — displays and trade logic ONLY. This must never modify tiers.csv
projections, VORP, or any draft-layer number. It is applied where a ROS
value is *shown or compared* (trade radar, waiver ROS comparisons), not
where it is *computed*. Keep it that way.

Status: conventional-wisdom-shaped and UNVALIDATED, same standing as the
Module 4 variance assumptions. Revisit once 2026 actuals accumulate.
"""

from __future__ import annotations

# age at which decay starts, by position (RB earliest, QB/TE latest)
DEFAULT_THRESHOLDS = {"RB": 27, "WR": 30, "TE": 31, "QB": 33}
DEFAULT_CAP = 0.10          # most a player can lose across a full season
DEFAULT_PER_YEAR = 0.02     # fraction per year above threshold, at season end
SEASON_WEEKS = 17


def decay_factor(pos: str, age: float | None, week: int, cfg: dict | None = None) -> float:
    """Multiplier (<=1.0) on a ROS value. 1.0 when off, ageless, or young."""
    cfg = cfg or {}
    # OPT-IN. This adjustment is conventional-wisdom-shaped and
    # unvalidated (see the module docstring), and an unvalidated
    # adjustment that is on by default is on in leagues nobody chose it
    # for. Turn it on explicitly per league, or not at all.
    if not cfg.get("enabled", False):
        return 1.0
    if age is None or pos is None:
        return 1.0
    thresholds = {**DEFAULT_THRESHOLDS, **(cfg.get("thresholds") or {})}
    thr = thresholds.get(pos)
    if thr is None or float(age) <= thr:
        return 1.0
    cap = float(cfg.get("cap", DEFAULT_CAP))
    per_year = float(cfg.get("per_year", DEFAULT_PER_YEAR))
    years_over = float(age) - thr
    # grows with weeks elapsed: nothing in week 1, full effect by season end
    elapsed = max(0.0, min(1.0, (int(week) - 1) / float(SEASON_WEEKS - 1)))
    drop = min(cap, years_over * per_year) * elapsed
    return round(1.0 - drop, 4)


def apply(ros: float | None, pos: str, age: float | None, week: int,
          cfg: dict | None = None) -> float | None:
    if ros is None:
        return None
    return round(float(ros) * decay_factor(pos, age, week, cfg), 1)


def note(pos: str, age: float | None, week: int, cfg: dict | None = None) -> str:
    """Short annotation when the decay is material, else empty."""
    f = decay_factor(pos, age, week, cfg)
    if f >= 0.995:
        return ""
    return f"age {age:.0f} {pos}: ROS value decayed {(1 - f) * 100:.0f}% (unvalidated)"

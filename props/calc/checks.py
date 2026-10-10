"""Loud checks. A failed check raises DataError; nothing falls back silently.
Explicit raises, not `assert`, so they hold under `python -O`."""

from __future__ import annotations

import numpy as np
import pandas as pd


class DataError(RuntimeError):
    """The inputs are wrong or incomplete; the card must not be built on them."""


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise DataError(msg)


def finite(name: str, x) -> None:
    """No missing or infinite values in a rate or a pool."""
    a = np.asarray(x, dtype=float)
    require(a.size > 0, f"{name} is empty")
    bad = int((~np.isfinite(a)).sum())
    require(bad == 0, f"{name} has {bad} missing or infinite values")


def no_missing(name: str, values) -> None:
    """No missing values (an empty input is allowed here, unlike `finite`)."""
    s = pd.Series(values)
    if s.isna().any():
        raise DataError(f"{name}: {int(s.isna().sum())} missing values")


def kicked_off_before(name: str, game_ids, kickoffs: dict, cutoff) -> None:
    """No play from the priced week or later, checked against an independent
    source: every game feeding an input must have kicked off (by the
    schedule's kickoff time) before the priced week's first kickoff."""
    ids = set(game_ids)
    unknown = sorted(str(g) for g in ids if g not in kickoffs)
    require(not unknown, f"{name}: {len(unknown)} games are not on the schedule (e.g. {unknown[:2]})")
    late = sorted(str(g) for g in ids if kickoffs[g] >= cutoff)
    require(not late, f"{name}: {len(late)} games kick off at or after the priced week (e.g. {late[:2]})")


def utc(x, what: str) -> pd.Timestamp:
    """A timestamp that must carry a time zone; a naive or empty one fails loudly."""
    try:
        t = pd.Timestamp(x)
    except (TypeError, ValueError) as ex:
        raise DataError(f"{what} {x!r} is not a readable time") from ex
    require(not pd.isna(t), f"{what} is empty")
    require(t.tzinfo is not None, f"{what} {x!r} has no time zone")
    return t


def number(x, what: str) -> float:
    if isinstance(x, (bool, str)) or x is None:     # true, "65.5" or null in a saved row is malformed
        raise DataError(f"{what} {x!r} is not a number")
    try:
        v = float(x)
    except (TypeError, ValueError) as ex:
        raise DataError(f"{what} {x!r} is not a number") from ex
    require(np.isfinite(v), f"{what} {v} is empty or infinite")
    return v


def multiplier(x, what: str) -> float:
    v = number(x, what)
    require(v > 1, f"{what} {v} is not a payout multiplier (must be above 1)")
    return v


def line_value(x, what: str) -> float:
    v = number(x, what)
    require(v > 0, f"{what} {v} is not above 0")
    return v


def in_range(name: str, value: float, lo_hi) -> None:
    lo, hi = lo_hi
    require(lo <= value <= hi, f"{name} = {value:.3f} is outside its plausible range {lo}-{hi}")

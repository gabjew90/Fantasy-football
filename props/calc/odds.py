"""Price arithmetic. Sleeper quotes a payout multiplier per side (1.80 pays
1.80 per 1 staked, stake included), which is decimal odds."""

from __future__ import annotations


def break_even(multiplier: float) -> float:
    """The win rate at which a side pays back its stake on average."""
    if multiplier <= 1:
        raise ValueError(f"a payout multiplier must be above 1, got {multiplier}")
    return 1.0 / multiplier


def no_vig(mult_over: float, mult_under: float) -> float:
    """The Over's chance with the book's margin taken out proportionally."""
    po, pu = break_even(mult_over), break_even(mult_under)
    return po / (po + pu)


def american_from_multiplier(multiplier: float) -> int:
    """1.80 -> -125, 2.50 -> +150."""
    if multiplier <= 1:
        raise ValueError(f"a payout multiplier must be above 1, got {multiplier}")
    profit = multiplier - 1.0
    return round(100 * profit) if profit >= 1 else round(-100 / profit)


def multiplier_from_american(american: float) -> float:
    """-125 -> 1.80, +150 -> 2.50."""
    if -100 < american < 100:
        raise ValueError(f"American odds are -100 or below, or +100 or above; got {american}")
    return 1 + (american / 100 if american > 0 else 100 / -american)


def fmt_american(american: int) -> str:
    return f"+{american}" if american > 0 else str(american)


def entry_cost(total_payout: float, legs: int) -> dict:
    """A Power Play pays `total_payout` per 1 staked only if every leg wins.
    per_leg: the hit rate each leg needs to break even; coin_flip_loss: the
    average loss per 1 staked if every leg is a coin flip."""
    if legs < 1 or total_payout <= 1:
        raise ValueError("an entry needs at least one leg and a payout above 1")
    return {"per_leg": (1.0 / total_payout) ** (1.0 / legs),
            "coin_flip_loss": 1.0 - total_payout * 0.5 ** legs}

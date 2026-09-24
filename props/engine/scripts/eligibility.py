"""One definition of "is this prop playable", used everywhere.

WHY THIS FILE EXISTS. The scorer had three different answers to that question
and they disagreed with each other:

  1. `clears_edge_rule_if_validated` -- gap >= min_gap AND ER >= min_er,
     computed from the posted price. Written to the shadow log and therefore
     to the permanent record.
  2. `is_play` on the betting card -- whether the book's line sits past a
     threshold on the sample distribution, with NO price term at all. The
     threshold was derived from `P_NEEDED = (1 + min_er) / (1 + 100/110)`,
     which assumes every prop is priced at -110. Props routinely are not: at
     -140 the break-even win probability is 4.5 points higher, so the card
     counted lines as playable that the edge rule rejected. This was the
     number the report showed the reader ("N of M posted props are at a line
     we'd play").
  3. the ladder's `sort_values("ER").iloc[0]` -- best ER, no other test.

And `model_state` -- the MODEL_UNVALIDATED marker -- gated nothing at all. It
was a string written beside the row while the card went on calling the prop a
play. A status that does not change an outcome is a comment.

So: one function, three call sites, and model status is a REASON like any
other. The rules are ordered from cheapest to most specific so the first
reason returned is the most fundamental one.

Stdlib only, on purpose: this is imported by the live scorer, by the
backtest, and by tests, and it must not drag numpy into any of them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ---------------------------------------------------------------- model status

# Per market: the model that prices it, and whether that model has survived a
# holdout against REAL sportsbook lines.
#
# Nothing is validated. The 2025 reliability table (`calibration_2025.csv`)
# was built by placing synthetic lines at fixed offsets from the model's own
# median, so it measures whether the distribution is self-consistent near its
# own centre -- not whether the model beats a book. It also reuses each
# player-week 8-10 times, so its `n` column overstates the evidence by about
# an order of magnitude. It is not a validation and does not appear here.
#
# A market moves out of this dict when a holdout against posted lines exists.
MODEL_STATUS = {
    # These strings are written to every record row as model_state, so they
    # stay fixed across releases: the evidence changes, the label does not. The
    # 2022-25 yardage harness (reports/yardage_harness.md) now backtests all
    # three yardage markets -- unbiased on average, too narrow, so tail
    # probabilities run high -- which the reports say in words.
    "player_receptions": "receiving_hier_v2, MODEL_UNVALIDATED (PROTOTYPE)",
    "player_reception_yds": "receiving_hier_v2, MODEL_UNVALIDATED (PROTOTYPE)",
    "player_rush_yds": "rush_yds_v0, MODEL_UNVALIDATED (no backtest)",
    # v1: outcome-backtested (2024-25, end-to-end log loss -0.0034 vs v0's
    # structure), still UNVALIDATED against posted lines -- so it prices no
    # fair odds and is never eligible. See model_registry.md.
    "player_anytime_td": "anytime_td_v1, MODEL_UNVALIDATED (PROTOTYPE)",
}

# Markets whose model has passed a holdout against posted lines. Empty, and it
# stays empty until `props/record` holds enough settled calls to answer the
# question. Adding a market here is a deliberate act with a measurement behind
# it, which is why it is a named constant and not a flag.
VALIDATED_MARKETS: frozenset[str] = frozenset()

# The book's number disagreeing with the model by more than this is treated as
# the book holding information the model lacks, not as an edge.
LARGE_GAP = 0.10


def model_status(market: str) -> str:
    """The model label for a market. Unknown markets are unvalidated too."""
    return MODEL_STATUS.get(market, f"{market}: no model, MODEL_UNVALIDATED")


def _missing(x: float | None) -> bool:
    """None, or NaN.

    NaN MATTERS HERE. Every comparison against NaN is False, so a NaN expected
    return would sail through `er < min_er` and be reported as clearing the
    edge rule. A missing number must fail closed, not open. Written without
    numpy so this module stays stdlib.
    """
    return x is None or x != x


def payout(american: float) -> float:
    """Profit per 1 unit staked at an American price."""
    return american / 100.0 if american > 0 else 100.0 / (-american)


def expected_return(p_win: float, american: float, p_push: float = 0.0) -> float:
    """Return per 1 unit staked. A push returns the stake, so it is neither a
    win nor a loss -- dropping the p_push term overstates the loss side and
    understates ER on integer lines."""
    return p_win * payout(american) - (1.0 - p_win - p_push)


@dataclass(frozen=True)
class Verdict:
    """Why a prop is or is not playable.

    `eligible` is the enforced answer: it requires a validated model. `priced`
    is the same test with the model-status rule suspended -- "would this clear
    the edge rule if the model were trusted" -- which is what the record's
    `clears_edge_rule_if_validated` column has always meant and what makes the
    logged rows useful before anything is validated.
    """

    eligible: bool
    priced: bool
    status: str
    er: float | None
    reasons: tuple[str, ...] = field(default_factory=tuple)

    @property
    def why(self) -> str:
        return "; ".join(self.reasons)


def evaluate(market: str, *, p_win: float, price: float | None,
             gap: float | None, p_push: float = 0.0,
             new_team: bool = False, questionable: bool = False,
             min_gap: float = 0.03, min_er: float = 0.03,
             er: float | None = None) -> Verdict:
    """The one eligibility test.

    `er` may be passed when the caller already computed it (the scorer does,
    from the same formula); otherwise it is derived from `price` and `p_win`.
    Passing it keeps one arithmetic path rather than two that can drift.
    """
    status = model_status(market)
    reasons: list[str] = []

    # --- price first: without a posted price there is no expected return to
    # test, and a price-blind "play" is the defect this function exists to
    # remove.
    if _missing(price) or _missing(p_win):
        reasons.append("no posted price")
        computed_er = None
    else:
        computed_er = er if not _missing(er) else expected_return(p_win, price, p_push)
        if _missing(computed_er):
            reasons.append("expected return could not be computed")
        elif computed_er < min_er:
            reasons.append(f"ER {computed_er:+.3f} below {min_er:+.3f} at {price:+.0f}")

    # --- the model's own disagreement with the book has to be big enough to
    # be worth acting on, and not so big that the book is obviously ahead.
    if _missing(gap):
        reasons.append("no book probability to compare against")
    else:
        if gap < min_gap:
            reasons.append(f"gap {gap:+.3f} below {min_gap:+.3f}")
        if abs(gap) > LARGE_GAP:
            reasons.append(f"gap {gap:+.3f} wider than {LARGE_GAP:.2f}: "
                           f"the book likely holds information the model lacks")

    # --- role: the model's share estimates are what price the prop, and these
    # two conditions are where those estimates are known to be weakest.
    if new_team:
        reasons.append("role prior weak: player changed teams")
    if questionable:
        reasons.append("regime unresolved: listed Questionable")

    priced = not reasons

    # --- model status last, so the reasons list leads with the substantive
    # objection when there is one. This is the rule that `priced` suspends.
    if market not in VALIDATED_MARKETS:
        reasons.append(f"model not validated against posted lines ({status})")

    return Verdict(eligible=not reasons, priced=priced, status=status,
                   er=computed_er, reasons=tuple(reasons))

"""One eligibility test, and the three answers it replaced.

The scorer used to decide "is this a play" three different ways. The one the
reader saw -- `is_play` on the betting card -- was price-blind: it compared
the book's line against the sample distribution using a threshold derived
from an ASSUMED -110, while the real price sat unused in the same frame. At
-140 the break-even probability is 4.5 points higher, so the card called
props playable that the edge rule in the same run rejected.

These tests pin the behaviour that replaced it, and in particular the two
properties that are easy to regress: price actually moves the answer, and
model status is enforced rather than merely recorded.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import eligibility as E  # noqa: E402


def _ok(**kw):
    """A prop that clears everything except model status."""
    base = dict(market="player_receptions", p_win=0.60, price=-110.0,
                gap=0.05, new_team=False, questionable=False)
    base.update(kw)
    return E.evaluate(**base)


# --------------------------------------------------------------- the arithmetic

def test_expected_return_accounts_for_the_push():
    """An integer line can push, which returns the stake. Dropping the push
    term counts it as a loss and understates ER on exactly the lines where
    pushes happen."""
    no_push = E.expected_return(0.55, -110.0)
    with_push = E.expected_return(0.55, -110.0, p_push=0.10)
    assert with_push > no_push
    # 0.55 * (100/110) - (1 - 0.55 - 0.10)
    assert with_push == pytest.approx(0.55 * (100 / 110) - 0.35)


def test_payout_matches_american_odds_both_directions():
    assert E.payout(100.0) == pytest.approx(1.0)
    assert E.payout(-110.0) == pytest.approx(100 / 110)
    assert E.payout(150.0) == pytest.approx(1.5)


# ------------------------------------------------------------- price is not free

def test_the_same_edge_is_a_play_at_one_price_and_not_at_another():
    """THE DEFECT THIS FUNCTION EXISTS TO REMOVE. Identical model, identical
    gap, identical everything except what the book is charging."""
    cheap = _ok(price=-110.0)
    dear = _ok(price=-160.0)
    assert cheap.priced, cheap.why
    assert not dear.priced
    assert "ER" in dear.why and "-160" in dear.why


def test_a_prop_with_no_posted_price_is_never_playable():
    """A price-blind 'play' is what the card used to emit."""
    v = _ok(price=None)
    assert not v.priced and not v.eligible
    assert "no posted price" in v.why
    assert v.er is None


def test_the_caller_may_pass_its_own_er_and_it_is_used_verbatim():
    """The scorer computes ER once, with the push term, when it builds the
    row. Recomputing here from a rounded p_win would let the two drift."""
    v = _ok(er=0.99)
    assert v.er == 0.99 and v.priced


# --------------------------------------------------------- model status enforced

def test_nothing_is_eligible_because_nothing_is_validated():
    """`model_state` used to be a string written beside a row while the card
    went on calling the prop a play. A status that changes no outcome is a
    comment, not a gate."""
    v = _ok()
    assert v.priced, "it clears the edge rule"
    assert not v.eligible, "but no market is validated"
    assert "not validated" in v.why
    assert E.VALIDATED_MARKETS == frozenset()


def test_priced_suspends_only_the_status_rule_not_the_others():
    """`clears_edge_rule_if_validated` is the record's long-standing column
    and has to keep meaning what it says: the edge rule, minus the status
    gate, and nothing else forgiven."""
    v = _ok(new_team=True)
    assert not v.priced and not v.eligible
    assert "changed teams" in v.why


def test_validating_a_market_makes_it_eligible(monkeypatch):
    """The gate is a real switch, not a hardcoded False."""
    monkeypatch.setattr(E, "VALIDATED_MARKETS", frozenset({"player_receptions"}))
    assert _ok().eligible
    assert not _ok(market="player_rush_yds").eligible


def test_every_priced_market_has_a_status_and_an_unknown_one_is_unvalidated():
    for market in ("player_receptions", "player_reception_yds",
                   "player_rush_yds", "player_anytime_td"):
        assert "MODEL_UNVALIDATED" in E.model_status(market)
    assert "MODEL_UNVALIDATED" in E.model_status("player_something_new")


# ------------------------------------------------------------------ role checks

@pytest.mark.parametrize("kw,needle", [
    ({"new_team": True}, "changed teams"),
    ({"questionable": True}, "Questionable"),
    ({"gap": 0.01}, "below"),
    ({"gap": 0.25}, "wider than"),
    ({"gap": None}, "no book probability"),
])
def test_each_role_and_gap_condition_names_itself(kw, needle):
    """A refusal a human cannot read is a refusal that gets overridden."""
    v = _ok(**kw)
    assert not v.priced
    assert needle in v.why


def test_a_wide_gap_is_the_book_knowing_something_not_a_bigger_edge():
    """The tier rule has always said this; now it is enforced in the same
    place the edge is computed rather than in display text."""
    v = _ok(gap=0.30)
    assert not v.priced
    assert str(E.LARGE_GAP) in v.why or "0.10" in v.why


def test_reasons_accumulate_rather_than_short_circuiting():
    """Fixing one objection should not reveal a second one a week later."""
    v = _ok(price=-400.0, gap=0.30, new_team=True, questionable=True)
    assert len(v.reasons) >= 4


# ---------------------------------------------------------------- import safety

def test_eligibility_imports_without_numpy_or_pandas():
    """It is imported by the live scorer, the backtest and these tests. A
    heavyweight import here would be paid on every capture."""
    src = (ENGINE / "eligibility.py").read_text(encoding="utf-8")
    assert "import numpy" not in src and "import pandas" not in src


# ------------------------------------------------------------ fail closed on NaN

@pytest.mark.parametrize("field", ["price", "gap", "p_win"])
def test_a_nan_input_fails_closed_rather_than_sailing_through(field):
    """Every comparison against NaN is False, so `er < min_er` would report a
    NaN expected return as clearing the edge rule. pandas produces NaN freely
    -- one missing price in a merge is enough -- and the failure is silent and
    in the direction of placing a bet."""
    v = _ok(**{field: float("nan")})
    assert not v.priced and not v.eligible, f"NaN {field} cleared the edge rule"


def test_a_nan_er_is_recomputed_because_that_cannot_invent_anything():
    """`er` is an optimisation, not an input: the caller passes the number it
    already computed so the two paths cannot drift. A NaN there means only
    that the caller had nothing to pass, and recomputing runs the SAME formula
    over price and p_win, which are themselves checked above. Failing closed
    here would reject a prop whose numbers are all present and fine."""
    v = _ok(er=float("nan"), price=-110.0, p_win=0.60)
    assert v.er == pytest.approx(E.expected_return(0.60, -110.0))
    assert v.priced


def test_a_nan_er_still_fails_closed_when_the_price_it_would_use_is_bad():
    """The recovery above is only safe because the inputs are validated first."""
    v = _ok(er=float("nan"), price=float("nan"))
    assert not v.priced and v.er is None

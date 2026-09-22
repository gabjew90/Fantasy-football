"""Layer 4 (the market blend) and the cross-game TD parlay builder."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
pd = pytest.importorskip("pandas")
import td_builder as TB  # noqa: E402
import td_market as TM  # noqa: E402


def test_the_blend_sits_between_model_and_market_on_the_logit_scale():
    b = float(TM.blend(0.40, 0.20))
    assert 0.20 < b < 0.40
    assert float(TM.blend(0.30, 0.30)) == pytest.approx(0.30)
    assert float(TM.blend(0.40, 0.20, w=1.0)) == pytest.approx(0.40)


def test_two_sided_is_exact_and_one_way_loses_the_provisional_hold():
    assert TM.market_prob(0.25, True) == 0.25
    assert TM.market_prob(0.25, False) == pytest.approx(0.25 / (1 + TM.ONE_WAY_HOLD))


def test_fair_odds_round_trip():
    assert TM.american_from_prob(0.5) == -100
    assert TM.american_from_prob(0.2) == 400
    assert TM.decimal_from_american(150) == pytest.approx(2.5)
    assert TM.decimal_from_american(-200) == pytest.approx(1.5)


def _boards():
    rows = [("G1", "A", "T1", "draftkings", 300, 0.40, 0.24, 0.32),     # edge 33%, +EV
            ("G1", "B", "T2", "draftkings", 250, 0.34, 0.27, 0.30),     # edge 11%: fails floor
            ("G2", "C", "T3", "draftkings", 280, 0.38, 0.25, 0.32),     # edge 28%, +EV
            ("G3", "D", "T5", "draftkings", 400, 0.30, 0.18, 0.24),     # edge 33%, +EV
            ("G3", "E", "T6", "sleeper", 350, 0.30, 0.20, 0.26)]        # edge 30%, +EV, same game as D
    return pd.DataFrame(rows, columns=["game", "player", "team", "book", "price", "p_model", "p_market", "p_blend"])


def test_only_legs_past_the_floor_on_their_own_are_candidates():
    legs = TB.candidate_legs(_boards())
    assert "B" not in set(legs["player"])
    assert set(legs["player"]) == {"A", "C", "D", "E"}


def test_parlays_use_one_leg_per_game_and_multiply_independent_legs():
    P = TB.build(_boards())
    assert not P["players"].str.contains(r"D \(T5\) \+ E \(T6\)").any()        # same game G3: never together
    for r in P.itertuples():
        assert len(set(r.games.split(" / "))) == r.legs
    top3 = P[P["legs"] == 3].iloc[0]
    assert top3["p_fair"] == pytest.approx(0.32 * 0.32 * 0.26) or top3["p_fair"] == pytest.approx(0.32 * 0.32 * 0.24)
    assert top3["min_payout_decimal"] == pytest.approx(round(1 / top3["p_fair"], 2))
    one_book = P[(P["legs"] == 2) & (P["book"] == "draftkings")].iloc[0]
    assert np.isfinite(one_book["book_product_decimal"])
    with_sleeper = P[P["players"].str.contains("E \(T6\)")]
    assert with_sleeper["book_product_decimal"].isna().all()                  # Sleeper pays from a table


def test_no_qualifying_leg_says_so_plainly():
    b = _boards().assign(p_blend=0.20)
    text = "\n".join(TB.markdown(TB.build(b), TB.candidate_legs(b)))
    assert "No anytime-TD leg on the slate clears the edge floor" in text

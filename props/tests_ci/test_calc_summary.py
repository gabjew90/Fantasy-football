"""The entry summary (props/calc/summary.py) on hand-made legs."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from props.calc import odds, summary  # noqa: E402


def _leg(name, market, side, bar, ask, team, opp, mult, game="2026_05_TB_DAL"):
    return {"name": name, "market": market, "side": side, "bar": bar, "ask": ask, "team": team, "opp": opp,
            "game_id": game, "mult": mult, "status": "ok"}


LEGS = [_leg("Javonte Williams", "rush_yds", "over", 17.4, 1.5, "DAL", "TB", 1.80),
        _leg("CeeDee Lamb", "receptions", "over", 10.87, -0.5, "DAL", "TB", odds.multiplier_from_american(-128)),
        _leg("Bucky Irving", "rec_yds", "over", 3.09, -0.5, "TB", "DAL", odds.multiplier_from_american(-122)),
        _leg("Dak Prescott", "pass_yds", "over", 25.99, -0.5, "DAL", "TB", odds.multiplier_from_american(-128))]


def test_the_summary_by_hand():
    text = summary.render(LEGS, 5.0, 50.0, payout_from_legs=False)
    lines = text.splitlines()
    assert lines[:3] == ["YOUR $5 ENTRY · 4 LEGS", "Return if all win: $50.00", "Includes your $5 stake."]
    # biggest ask first: Williams (+1.5), then the three at -0.5 in the order given
    flat = " ".join(lines)
    block = flat[flat.index("WHAT EACH NEEDS"):flat.index("FIT CHECK")]
    assert block.index("Javonte Williams: ~17 carries, about 1.5 more than recent.") < block.index("CeeDee Lamb")
    assert "Bucky Irving: ~3.1 targets, about 0.5 fewer than recent." in block
    # Williams' Over needs Dallas ahead; Lamb and Prescott need Dallas behind; Irving needs Tampa behind
    fit = flat[flat.index("FIT CHECK"):flat.index("PRICE CHECK")]
    assert fit.count("These lean on opposite game stories.") == 4         # W-L, W-P, L-I, I-P; L-P and W-I agree
    assert fit.startswith("FIT CHECK Javonte Williams: more runs while ahead. CeeDee Lamb: more throws from behind. "
                          "These lean on opposite game stories.")
    assert fit.rstrip().endswith("Both can win. Check your case for each.")
    assert "Javonte Williams: more than 55.6 wins in 100." in flat        # -125: 1 / 1.80
    # each of 4 legs must win (5/50)^(1/4) = 56.2% for the entry to break even
    assert "All must win more than 56.2 in 100." in lines
    assert "All 4 win: 1 entry in 16." in lines
    assert "Average loss: $1.88 per $5 entry." in lines                   # 5 - 50/16
    assert flat.endswith(summary.LEGEND + " " + summary.FOLLOW_UPS)
    assert max(len(x) for x in lines) <= 40
    assert "%" not in text


def test_no_opposing_pairs_and_a_payout_from_the_legs():
    legs = [LEGS[1], LEGS[3]]                     # both need Dallas behind
    text = summary.render(legs, 5.0, summary.payout_from_legs(5.0, legs), payout_from_legs=True)
    assert "No opposing pairs found." in text
    assert "worked out from the legs' own prices" in " ".join(text.splitlines())
    assert summary.payout_from_legs(5.0, legs) == pytest.approx(5.0 * legs[0]["mult"] * legs[1]["mult"])
    other_game = [LEGS[0], {**LEGS[1], "game_id": "2026_05_X_Y"}]
    assert "No opposing pairs found." in summary.render(other_game, 5.0, 20.0, False)


def test_out_of_range_legs_money_and_a_player_with_two_legs():
    never = {**LEGS[0], "bar": None, "ask": None, "result": "never", "top": 45.0}
    text = summary.render(LEGS[1:] + [never], 5.0, 54.0, False)
    flat = " ".join(text.splitlines())
    block = flat[flat.index("WHAT EACH NEEDS"):flat.index("FIT CHECK")]
    assert block.index("Javonte Williams: no workload up to 45 carries clears it.") < block.index("CeeDee Lamb")
    assert "Average loss: $1.63 per $5 entry." in flat                 # 54/16 - 5 = -1.625 -> half up
    two = [LEGS[0], {**LEGS[0], "market": "rec_yds", "ask": 1.0}]
    assert "Javonte Williams (rushing): more runs while ahead." in " ".join(summary.render(two, 5, 20, False).splitlines())
    with pytest.raises(ValueError):
        summary.render(LEGS, 0.0, 0.0, True)


def test_leg_view_takes_the_cards_own_ask():
    from props.calc import calc, card
    c = {"solutions": {"needed_over": calc.Solution(26.76, "ok")}, "usual": 26.25, "search_max": 45.0,
         "mult_over": 1.78}
    v = summary.leg_view("Dak Prescott", "pass_yds", "over", c, "DAL", "TB", "g")
    assert v["ask"] == card.work_ask(26.76, 26.25) == 0.5 and v["result"] == "ok"      # 27 - 26.3 = 0.7 -> 0.5
    c2 = {**c, "solutions": {"needed_under": calc.Solution(None, "high")}, "mult_under": 1.9}
    v2 = summary.leg_view("Dak Prescott", "pass_yds", "under", c2, "DAL", "TB", "g")
    assert v2["bar"] is None and v2["result"] == "always"            # an Under's "high" = always

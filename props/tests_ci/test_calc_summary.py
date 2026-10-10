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
    assert "Opposite game stories: Williams and Lamb; Williams and Prescott; Lamb and Irving; Irving and Prescott." \
        in " ".join(lines)
    assert "Javonte Williams: more runs while ahead." in lines and "Bucky Irving: more throws from behind." in lines
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

"""The standard trade framework: re-solve both lineups, name every seat move.

A package's effect is not "two left, two arrived". The lineup re-solves
globally, so a trade can pull a player up off the bench who was never part of
it -- and that promotion is a real part of the price. Pricing a deal without
it produces a number nobody can reconstruct.
"""

from __future__ import annotations

import pytest

from manager import marginal

SHAPE = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 2}


def p(pid, pos, val, name=None):
    return {"sleeper_id": pid, "pos": pos, "weekly": val, "name": name or pid}


# A roster shaped like the 2026-09-08 vincenzo31 case: four receivers for two
# WR slots, a bench back who is next in line for a flex.
THEM = [p("qb", "QB", 291), p("rb1", "RB", 287), p("rb2", "RB", 249),
        p("wr1", "WR", 239), p("wr2", "WR", 207), p("wr3", "WR", 206),
        p("wr4", "WR", 184), p("te1", "TE", 143),
        p("bench_rb", "RB", 170), p("bench_wr", "WR", 158)]


def test_a_bench_player_pulled_into_the_lineup_is_reported():
    """Losing two receivers frees a flex the bench back now claims. He is not
    in the trade, and omitting him makes the point total unexplainable."""
    mv = marginal.slot_moves(
        THEM, SHAPE,
        arriving=[p("in_rb", "RB", 228), p("in_te", "TE", 182)],
        departing=[p("wr1", "WR", 239), p("wr4", "WR", 184)])
    promoted = [x["sleeper_id"] for x in mv["promoted"]]
    assert promoted == ["bench_rb"], mv["promoted"]
    assert {x["sleeper_id"] for x in mv["arrived"]} == {"in_rb", "in_te"}
    assert {x["sleeper_id"] for x in mv["departed"]} == {"wr1", "wr4"}


def test_the_four_movement_lists_are_disjoint_and_explain_the_delta():
    mv = marginal.slot_moves(
        THEM, SHAPE,
        arriving=[p("in_rb", "RB", 228), p("in_te", "TE", 182)],
        departing=[p("wr1", "WR", 239), p("wr4", "WR", 184)])
    ids = [x["sleeper_id"] for grp in ("departed", "benched", "arrived", "promoted")
           for x in mv[grp]]
    assert len(ids) == len(set(ids)), "a player appears in two movement lists"
    # every seat change is accounted for: out-of-lineup and into-lineup balance
    left = len(mv["departed"]) + len(mv["benched"])
    came = len(mv["arrived"]) + len(mv["promoted"])
    assert left == came, (mv["departed"], mv["benched"], mv["arrived"], mv["promoted"])
    gone = sum(x["weekly"] for x in mv["departed"] + mv["benched"])
    added = sum(x["weekly"] for x in mv["arrived"] + mv["promoted"])
    assert mv["delta"] == pytest.approx(added - gone, abs=0.05)


def test_a_squeezed_starter_is_not_confused_with_a_traded_one():
    """Adding a player without sending one back benches somebody. He stayed on
    the roster, so he is `benched`, not `departed`."""
    mv = marginal.slot_moves(THEM, SHAPE, arriving=[p("star", "RB", 400)])
    assert not mv["departed"]
    assert len(mv["benched"]) == 1
    assert mv["arrived"][0]["sleeper_id"] == "star"


def test_nothing_moves_when_the_arrival_cannot_crack_the_lineup():
    mv = marginal.slot_moves(THEM, SHAPE, arriving=[p("scrub", "WR", 5)])
    assert mv["delta"] == 0.0
    assert not mv["arrived"] and not mv["benched"] and not mv["promoted"]


def test_slot_moves_honours_a_non_weekly_key():
    roster = [dict(p("a", "RB", 0), ros=300), dict(p("b", "RB", 0), ros=100)]
    mv = marginal.slot_moves(roster, {"slots": {"RB": 1}, "flex": 0}, key="ros")
    assert mv["total_before"] == 300.0
    assert mv["before"][0]["sleeper_id"] == "a"


# ------------------------------------------------------- wired into the Deal

MINE = [p("mqb", "QB", 285), p("mrb1", "RB", 331), p("mrb2", "RB", 255),
        p("mrb3", "RB", 228), p("mwr1", "WR", 207), p("mte1", "TE", 196),
        p("mte2", "TE", 182), p("mwr2", "WR", 168), p("mbench", "RB", 146)]


def test_deal_totals_come_from_the_same_solve_as_the_movements():
    """If the points were computed separately from the seat list they could
    drift, and the walkthrough would contradict the headline number."""
    d = marginal.price(MINE, THEM, [MINE[3], MINE[6]], [THEM[3], THEM[6]], SHAPE)
    assert d.mine_before == d.my_moves["total_before"]
    assert d.mine_after == d.my_moves["total_after"]
    assert d.my_delta == d.my_moves["delta"]
    assert d.theirs_before == d.their_moves["total_before"]
    assert d.their_delta == d.their_moves["delta"]


def test_explain_names_the_promotion_and_both_sides():
    d = marginal.price(MINE, THEM, [MINE[3], MINE[6]], [THEM[3], THEM[6]], SHAPE)
    body = marginal.explain(d, me="you", them="vincenzo31")
    assert "you:" in body and "vincenzo31:" in body
    if d.their_moves["promoted"]:
        assert "PROMOTED off the bench" in body


def test_explain_survives_a_deal_with_no_market_data():
    d = marginal.price(MINE, THEM, [MINE[3]], [THEM[3]], SHAPE)
    body = marginal.explain(d)
    assert "give" in body and "⚠" not in body

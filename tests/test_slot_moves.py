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
    gone = sum(x["weekly"] for x in mv["departed"] + mv["benched"])
    added = sum(x["weekly"] for x in mv["arrived"] + mv["promoted"])
    assert mv["delta"] == pytest.approx(added - gone, abs=0.05)


def test_seats_need_not_balance_when_the_roster_shrinks():
    """An earlier version of the test above asserted len(out) == len(in), which
    is only true while the roster can still fill every slot. Trade a player
    away with nothing back on a thin roster and a seat simply goes empty."""
    thin = [p("a", "RB", 300), p("b", "RB", 200)]
    mv = marginal.slot_moves(thin, {"slots": {"RB": 2}, "flex": 0},
                             departing=[p("a", "RB", 300)])
    assert len(mv["departed"]) == 1
    assert not mv["arrived"] and not mv["promoted"]
    assert mv["delta"] == -300.0


def test_a_generator_of_arrivals_is_not_silently_consumed():
    """`arriving` is read twice -- once for the id set, once for the
    post-trade roster. A generator was exhausted by the first pass, so the
    incoming players vanished and the package priced at 0 with no error."""
    star = p("star", "RB", 500)
    from_list = marginal.slot_moves(THEM, SHAPE, arriving=[star])
    from_gen = marginal.slot_moves(THEM, SHAPE, arriving=(x for x in [star]))
    assert from_gen["delta"] == from_list["delta"] != 0
    assert [x["sleeper_id"] for x in from_gen["arrived"]] == ["star"]


def test_the_same_player_cannot_arrive_and_depart():
    with pytest.raises(ValueError, match="both arriving and departing"):
        marginal.slot_moves(THEM, SHAPE, arriving=[p("wr1", "WR", 239)],
                            departing=[p("wr1", "WR", 239)])


def test_a_duplicate_row_cannot_fill_two_fixed_slots():
    """RB 300 + RB 100 with two RB slots is 400. Handing slot_moves an
    arriving player who is already rostered used to return 600, because the
    fixed-slot loop had no seen-id check while the flex loop did."""
    r = [p("x", "RB", 300), p("y", "RB", 100)]
    mv = marginal.slot_moves(r, {"slots": {"RB": 2}, "flex": 0},
                             arriving=[p("x", "RB", 300)])
    assert mv["total_after"] == 400.0
    assert [q["sleeper_id"] for q in mv["after"]] == ["x", "y"]


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

"""Waiver backfill, the depth replay, and the two acceptance gates.

Three additions from the 2026-09-09 framework review. The lineup recompute
was already right -- it reproduced both of that framework's worked examples
to the decimal -- so these are the parts it had that we did not.
"""

from __future__ import annotations

import pytest

from manager import marginal

TWO_FLEX = {"slots": {"RB": 2, "WR": 2}, "flex": 2}
_n = [0]


def p(pos, v, name=None):
    _n[0] += 1
    return {"sleeper_id": f"p{_n[0]}", "pos": pos, "weekly": v,
            "name": name or f"{pos}{v}"}


# --------------------------------------------------------------- backfill

def test_backfill_only_fills_spots_a_package_actually_opens():
    """NOT a replacement baseline. Bench players are already in the pool the
    optimiser solves over, so a departing starter is covered automatically.
    This is only for the spot a 2-for-1 leaves empty."""
    wv = [p("RB", 8.0), p("WR", 7.0)]
    assert marginal.backfill(0, wv) == []
    assert marginal.backfill(-1, wv) == []
    assert [x["weekly"] for x in marginal.backfill(1, wv)] == [8.0]
    assert [x["weekly"] for x in marginal.backfill(2, wv)] == [8.0, 7.0]


def test_backfill_never_hands_back_a_player_already_in_the_deal():
    wv = [p("RB", 9.0, "in the deal"), p("RB", 8.0)]
    got = marginal.backfill(1, wv, exclude=[wv[0]])
    assert [x["name"] for x in got] == [wv[1]["name"]]


def test_backfill_is_empty_without_a_pool():
    assert marginal.backfill(2, None) == []
    assert marginal.backfill(2, []) == []


def test_a_two_for_one_prices_the_opened_spot_instead_of_leaving_it_empty():
    """The spot is filled by Tuesday. Pricing it at zero understates every
    consolidation."""
    mine = [p("RB", 15.0), p("RB", 13.0), p("RB", 6.0),
            p("WR", 16.0), p("WR", 13.0), p("WR", 12.0), p("WR", 10.0)]
    theirs = [p("WR", 17.5, "star"), p("RB", 4.0), p("WR", 4.0)]
    give, get = [mine[1], mine[4]], [theirs[0]]
    wv = [p("RB", 14.0, "big waiver")]
    without = marginal.price(mine, theirs, give, get, TWO_FLEX)
    with_wv = marginal.price(mine, theirs, give, get, TWO_FLEX, waivers=wv)
    assert with_wv.my_delta > without.my_delta
    assert with_wv.my_backfill == ["big waiver"]
    assert without.my_backfill == []


def test_the_side_receiving_more_bodies_gets_no_backfill():
    mine = [p("RB", 15.0), p("WR", 16.0), p("WR", 12.0)]
    theirs = [p("RB", 14.0), p("RB", 13.0), p("WR", 11.0)]
    d = marginal.price(mine, theirs, [mine[0]], [theirs[0], theirs[1]],
                       TWO_FLEX, waivers=[p("WR", 9.0)])
    assert d.my_backfill == [], "I received a body, I did not open a spot"
    assert d.their_backfill, "they sent two and received one"


# ------------------------------------------------------------- depth_risk

def test_depth_risk_measures_what_a_trade_costs_you_when_a_starter_goes_down():
    """A package can look even on the starting lineup and quietly sell the
    depth behind it.

    The roster needs REAL bench depth for this to mean anything. An earlier
    version of this test used six players for six slots, so both pools lost
    the same 15.0 and it passed on a fixture that could not have failed."""
    mine = [p("RB", 15.0, "star"), p("RB", 13.0, "benchRB"), p("RB", 11.0),
            p("WR", 16.0), p("WR", 14.0), p("WR", 13.0, "sentWR"),
            p("WR", 12.0), p("WR", 10.0)]
    theirs = [p("WR", 17.5, "their star")]
    give = [mine[1], mine[5]]
    r = marginal.depth_risk(mine, TWO_FLEX, "RB", arriving=[theirs[0]],
                            departing=give, waivers=[p("RB", 8.0, "wv")])
    assert r["before_star"] == "star" and r["pos"] == "RB"
    assert r["extra"] > 0, (
        f"trading the bench RB away must widen the hole: {r}")


def test_the_before_pool_is_never_topped_up_from_waivers():
    """An injury does not open a roster spot. Topping the BEFORE pool up
    erased the very difference the replay measures -- with a three-deep
    waiver pool a 2-for-1 that plainly sold depth reported extra 0.0."""
    mine = [p("RB", 15.0, "star"), p("RB", 13.0, "benchRB"), p("RB", 11.0),
            p("WR", 16.0), p("WR", 14.0), p("WR", 13.0, "sentWR"),
            p("WR", 12.0), p("WR", 10.0)]
    theirs = [p("WR", 17.5, "their star")]
    give = [mine[1], mine[5]]
    deep = [p("RB", 9.0), p("RB", 8.5), p("RB", 8.0)]
    rich = marginal.depth_risk(mine, TWO_FLEX, "RB", arriving=[theirs[0]],
                               departing=give, waivers=deep)
    lean = marginal.depth_risk(mine, TWO_FLEX, "RB", arriving=[theirs[0]],
                               departing=give, waivers=deep[:1])
    assert rich["before_drop"] == lean["before_drop"], (
        "the size of the waiver pool must not change the pre-trade roster")
    assert rich["extra"] > 0 and lean["extra"] > 0


def test_depth_risk_is_zero_when_the_trade_touches_nothing_at_that_position():
    mine = [p("RB", 15.0), p("RB", 13.0), p("WR", 16.0), p("WR", 12.0)]
    r = marginal.depth_risk(mine, TWO_FLEX, "RB")
    assert r["extra"] == 0.0


def test_depth_risk_survives_a_position_nobody_holds():
    mine = [p("RB", 15.0), p("WR", 12.0)]
    r = marginal.depth_risk(mine, TWO_FLEX, "TE")
    assert r["before_drop"] == 0.0 and r["after_drop"] == 0.0


# ---------------------------------------------------------------- verdict

def _deal(mine_delta, theirs_delta, out=None, inn=None):
    mkt = None if out is None else {"out": out, "in": inn, "delta": inn - out,
                                    "pct": None, "unpriced": []}
    return marginal.Deal(100.0, 100.0 + mine_delta, 100.0,
                         100.0 + theirs_delta, market=mkt)


def test_the_threshold_ships_at_zero_because_nothing_has_measured_it():
    assert marginal.EDGE_PPG == 0.0


def test_a_zero_delta_package_is_never_send_even_at_a_zero_threshold():
    """Pure churn carries transaction risk and buys nothing."""
    v = marginal.verdict(_deal(0.0, 5.0), weeks_left=17)
    assert v["gate1"] is False and v["send"] is False


def test_gate_one_needs_my_side_up_and_theirs_not_down():
    assert marginal.verdict(_deal(17.0, 1.0), weeks_left=17)["gate1"] is True
    assert marginal.verdict(_deal(17.0, -1.0), weeks_left=17)["gate1"] is False
    assert marginal.verdict(_deal(-1.0, 5.0), weeks_left=17)["gate1"] is False


def test_season_totals_are_converted_to_per_week():
    v = marginal.verdict(_deal(17.0, 0.0), weeks_left=17)
    assert v["my_ppg"] == 1.0
    v2 = marginal.verdict(_deal(13.0, 0.0), weeks_left=17)
    assert v2["my_ppg"] == 0.76


def test_raising_the_floor_rejects_the_marginal_package():
    """+13.0 over a 17-week season is +0.76 ppg -- under the 1.0 the source
    framework suggests, over the zero we ship."""
    d = _deal(13.0, 5.0)
    assert marginal.verdict(d, weeks_left=17)["gate1"] is True
    assert marginal.verdict(d, weeks_left=17, floor_ppg=1.0)["gate1"] is False


def test_gate_two_is_about_acceptance_not_truth():
    """A package can be good for them and still be refused, because managers
    price by name recognition rather than by their own optimal lineup."""
    good_for_them = _deal(17.0, 17.0, out=5000, inn=10000)   # they get 50%
    v = marginal.verdict(good_for_them, weeks_left=17)
    assert v["gate1"] is True and v["gate2"] is False and v["send"] is False
    assert any("expect a rejection" in w for w in v["why"])


def test_gate_two_passes_when_the_market_reads_even():
    v = marginal.verdict(_deal(17.0, 5.0, out=9800, inn=10000), weeks_left=17)
    assert v["gate2"] is True and v["market_share"] == 0.98 and v["send"] is True


def test_no_market_data_does_not_block_a_deal():
    v = marginal.verdict(_deal(17.0, 5.0), weeks_left=17)
    assert v["market_share"] is None and v["gate2"] is True


def test_a_disputed_consensus_row_is_reported_alongside_the_gates():
    """A fixed floor cannot tell a real edge from one smaller than the
    sources' own disagreement; consensus.confident can."""
    noisy = {"n": 3, "spread": 60.0, "per_source": {}, "mean": 0.0}
    v = marginal.verdict(_deal(5.0, 1.0), weeks_left=17, con=noisy)
    assert v["confident"] is False
    assert any("disagreement" in w for w in v["warnings"])


def test_weeks_left_of_zero_does_not_divide_by_zero():
    assert marginal.verdict(_deal(10.0, 1.0), weeks_left=0)["my_ppg"] == 10.0


def test_a_waiver_pickup_is_not_reported_as_part_of_the_trade():
    """explain() showed "in (from the trade) RB WAIVER PICKUP" for a body the
    other manager never saw. The reader cannot check that, so it is a lie."""
    mine = [p("RB", 15.0), p("RB", 13.0, "sent"), p("WR", 16.0, "sent2"),
            p("WR", 12.0), p("WR", 10.0)]
    theirs = [p("WR", 17.5, "star")]
    d = marginal.price(mine, theirs, [mine[1], mine[2]], [theirs[0]], TWO_FLEX,
                       waivers=[p("RB", 14.0, "WAIVER PICKUP")])
    arrived = [x["name"] for x in d.my_moves["arrived"]]
    filled = [x["name"] for x in d.my_moves["backfilled"]]
    assert arrived == ["star"], arrived
    assert filled == ["WAIVER PICKUP"], filled
    body = marginal.explain(d)
    assert "waiver fill, opened spot" in body
    assert "from the trade)           RB  WAIVER PICKUP" not in body


def test_the_movement_lists_stay_disjoint_with_a_backfill():
    mine = [p("RB", 15.0), p("RB", 13.0), p("WR", 16.0), p("WR", 12.0),
            p("WR", 11.0)]
    theirs = [p("WR", 17.5)]
    d = marginal.price(mine, theirs, [mine[1], mine[4]], [theirs[0]], TWO_FLEX,
                       waivers=[p("RB", 14.0)])
    mv = d.my_moves
    ids = [x["sleeper_id"] for g in ("departed", "benched", "arrived",
                                     "backfilled", "promoted") for x in mv[g]]
    assert len(ids) == len(set(ids))


# ---------------------------------------------- gate 2 ceiling, gate 3 depth

def test_overpaying_is_reported_and_blocks_only_when_asked():
    """The ceiling was a veto until 2026-09-09. It is now a warning by
    default: market value does not score points, and the one package that
    session where both sides won ran 149% -- the ceiling rejected exactly the
    deal that got a yes. The 559% fleecing case must still be SAID, and the
    knob must still block when a caller turns it on."""
    fleeced = _deal(17.0, 5.0, out=5590, inn=1000)
    v = marginal.verdict(fleeced, weeks_left=17)
    assert v["gate2"] is True and v["send"] is True
    assert any("overpaying" in w for w in v["warnings"]), v
    assert not any("overpaying" in w for w in v["why"])

    blocked = marginal.verdict(fleeced, weeks_left=17, market_ceiling_blocks=True)
    assert blocked["gate2"] is False and blocked["send"] is False
    assert any("overpaying" in w for w in blocked["why"]), blocked


def test_lifting_the_ceiling_did_not_lift_the_floor():
    """A deal they refuse is worth nothing whatever it does to my lineup.
    That job still blocks."""
    low = _deal(17.0, 5.0, out=5000, inn=10000)
    v = marginal.verdict(low, weeks_left=17)
    assert v["gate2"] is False and v["send"] is False
    assert any("expect a rejection" in w for w in v["why"])


def test_the_ceiling_ships_as_advisory():
    assert marginal.MARKET_CEILING_BLOCKS is False
    assert marginal.verdict(_deal(1.0, 1.0), weeks_left=17)["market_ceiling_blocks"] is False


def test_the_floor_and_the_ceiling_report_different_reasons():
    low = marginal.verdict(_deal(17.0, 5.0, out=5000, inn=10000), weeks_left=17)
    high = marginal.verdict(_deal(17.0, 5.0, out=10000, inn=5000), weeks_left=17)
    assert any("expect a rejection" in w for w in low["why"])
    assert any("overpaying" in w for w in high["warnings"])


def test_an_even_market_still_passes():
    v = marginal.verdict(_deal(17.0, 5.0, out=10700, inn=10000), weeks_left=17)
    assert v["gate2"] is True, "107% is the cbarone package and it is fine"


def test_thin_after_names_a_slot_with_no_cover():
    """A wide receiver cannot legally occupy a tight end slot, so a roster
    holding exactly as many tight ends as it must start has no cover."""
    shape = {"slots": {"RB": 2, "WR": 2, "TE": 1}, "flex": 2}
    roster = [p("TE", 20.0, "te1"), p("TE", 18.0, "te2"),
              p("RB", 15.0), p("RB", 14.0), p("RB", 13.0),
              p("WR", 16.0), p("WR", 15.0), p("WR", 12.0)]
    assert marginal.thin_after(roster, shape) == []
    thin = marginal.thin_after(roster, shape, departing=[roster[1]],
                               arriving=[p("WR", 19.0)])
    assert thin == ["TE"]


def test_a_waiver_body_can_cover_a_spot_a_two_for_one_opens():
    # three backs, so only the TE room is left without cover -- an earlier
    # fixture held exactly two RBs for two RB slots and was thin at both,
    # which is what the function correctly said
    shape = {"slots": {"RB": 2, "TE": 1}, "flex": 1}
    roster = [p("TE", 20.0, "te1"), p("TE", 18.0, "te2"),
              p("RB", 15.0), p("RB", 14.0), p("RB", 13.0)]
    give = [roster[1], roster[3]]
    assert marginal.thin_after(roster, shape, departing=give,
                               arriving=[p("RB", 19.0)]) == ["TE"]
    covered = marginal.thin_after(roster, shape, departing=give,
                                  arriving=[p("RB", 19.0)],
                                  waivers=[p("TE", 9.0, "wire TE")])
    assert covered == [], "the opened spot is filled by Tuesday"


def test_gate_three_warns_but_does_not_block_by_default():
    """Turned off 2026-09-09. Whether an empty slot is disqualifying depends
    on the wire that week, a free IR slot, and how the lineup gain trades
    against a tail risk -- none of which the model holds."""
    v = marginal.verdict(_deal(17.0, 5.0, out=10000, inn=10000),
                         weeks_left=17, thin=["TE"])
    assert marginal.DEPTH_BLOCKS is False
    assert v["gate3"] is False, "the condition is still detected"
    assert v["send"] is True, "...but it no longer vetoes"
    assert any("empties a required slot" in w for w in v["warnings"])
    assert not any("empties" in w for w in v["why"])
    assert v["thin"] == ["TE"]


def test_gate_three_can_be_switched_back_on():
    v = marginal.verdict(_deal(17.0, 5.0, out=10000, inn=10000),
                         weeks_left=17, thin=["TE"], depth_blocks=True)
    assert v["send"] is False
    assert any("empties a required slot" in w for w in v["why"])


def test_a_disagreement_note_is_a_warning_not_a_veto():
    noisy = {"n": 3, "spread": 60.0, "per_source": {}, "mean": 0.0}
    v = marginal.verdict(_deal(5.0, 1.0, out=10000, inn=10000),
                         weeks_left=17, con=noisy)
    assert v["send"] is True
    assert any("disagreement" in w for w in v["warnings"])


def test_gate_three_is_silent_when_nothing_is_thin():
    v = marginal.verdict(_deal(17.0, 5.0, out=10000, inn=10000), weeks_left=17)
    assert v["gate3"] is True and v["send"] is True and v["thin"] == []
    assert v["warnings"] == []


def test_gate_three_reports_only_what_the_trade_broke():
    """thin_after is a state query and answers honestly: a one-QB league
    rosters one quarterback and streams a kicker, so all of them read
    "uncovered" every week. The live brief said "empties a required slot at
    DEF, K, QB, TE" when only the TE room was this package's doing."""
    shape = {"slots": {"QB": 1, "RB": 2, "TE": 1, "K": 1}, "flex": 1}
    roster = [p("QB", 300.0), p("K", 120.0),
              p("RB", 30.0), p("RB", 29.0), p("RB", 28.0),
              p("TE", 24.0, "te1"), p("TE", 23.0, "te2")]
    # QB and K have no cover before the trade and none after -- not news
    assert set(marginal.thin_after(roster, shape)) == {"QB", "K"}
    got = marginal.newly_thin(roster, shape, departing=[roster[6]],
                              arriving=[p("RB", 31.0)])
    assert got == ["TE"], got


def test_newly_thin_is_empty_when_a_trade_breaks_nothing():
    shape = {"slots": {"QB": 1, "RB": 2, "TE": 1}, "flex": 1}
    roster = [p("QB", 300.0), p("RB", 30.0), p("RB", 29.0), p("RB", 28.0),
              p("TE", 24.0), p("TE", 23.0)]
    assert marginal.newly_thin(roster, shape, departing=[roster[3]],
                               arriving=[p("RB", 31.0)]) == []

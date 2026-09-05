"""Two knobs from the 2026-09-04 housekeeping (DECISIONS #50):

* fallback_floor: wire -- the floor under the fallback is what the wire will
  hold (bench.waiver_ppw x 17), not the season replacement level.
* turn_look_through -- at the turn (no rival between consecutive picks) the
  survival window looks through to the following turn, and the pair planner
  prices the partner at best_now because he is certain.
"""

from draftkit import bench as B
from draftkit import planner as P
from draftkit.tracker import fallback_value
from test_slot_markets import make_tracker, player  # noqa: F401


def _board():
    # RBs by ADP; the last three are predicted undrafted (ADP past pick 150)
    rbs = [player(f"rb{i}", "RB", 60.0 - i * 4, 60.0 - i * 4, 5.0 + i * 12.0, rank=i + 1) for i in range(10)]
    for i, p in enumerate(rbs):
        p["proj_pts"] = 260.0 - i * 15.0
    wire = [player(f"rbw{i}", "RB", -30.0 - i, -30.0 - i, 160.0 + i, rank=20 + i) for i in range(3)]
    for i, p in enumerate(wire):
        p["proj_pts"] = 110.0 - i * 5.0
    qbs = [player(f"qb{i}", "QB", 40.0 - i * 5, 40.0 - i * 5, 30.0 + i * 15.0, rank=i + 1) for i in range(4)]
    for i, p in enumerate(qbs):
        p["proj_pts"] = 330.0 - i * 20.0
    return rbs + wire + qbs


def test_wire_points_is_the_kth_predicted_undrafted_player_times_17():
    t = make_tracker(_board(), [], my_slot=4, current_pick=40)
    t.draft_k = 3
    w = t._wire_points()
    # the wire RBs are rbw0..rbw2 by ADP; the 3rd best of them is rbw2 at 100 pts
    assert abs(w["RB"] - 100.0) < 1e-9
    # no QB is predicted undrafted (all ADP < 150): waiver_ppw falls back to
    # the worst remaining QB, the honest thin-wire answer
    assert w["QB"] > 0


def test_wire_floor_binds_only_when_nothing_survives_the_deadline():
    # survivors present: the floor sits below them and the answer is the
    # best survivor; position picked clean: the answer is the wire, no cliff
    surv = [200.0, 180.0]
    pool = [260.0, 245.0, 200.0, 180.0, 40.0]
    assert fallback_value(surv, pool, 100.0, "replacement") == 200.0
    assert fallback_value([], pool, 100.0, "replacement") == 100.0
    assert fallback_value([], pool, 100.0, "board_min") == 40.0      # the cliff the knob removes


def test_tracker_wire_mode_keys_every_position_and_never_exceeds_a_survivor():
    t = make_tracker(_board(), [], my_slot=4, current_pick=40)
    t.fallback_floor = "wire"
    needs = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1, "BN": 6}
    fb = t._fallback_points(needs)
    assert "RB" in fb and "QB" in fb
    t2 = make_tracker(_board(), [], my_slot=4, current_pick=40)
    t2.fallback_floor = "board_min"
    fb2 = t2._fallback_points(needs)
    # with survivors on this board the two modes agree at RB and QB
    assert abs(fb["RB"] - fb2["RB"]) < 1e-9 and abs(fb["QB"] - fb2["QB"]) < 1e-9


def test_partner_certain_prices_the_partner_at_best_now():
    cands = [(10.0, "a", {"sleeper_id": "a", "pos": "RB", "vorp": 50.0, "proj_pts": 200.0}),
             (9.0, "b", {"sleeper_id": "b", "pos": "WR", "vorp": 48.0, "proj_pts": 190.0})]
    report = {"RB": {"best_now": 50.0, "e_best_next": 20.0, "urgency": 30.0},
              "WR": {"best_now": 48.0, "e_best_next": 10.0, "urgency": 38.0}}
    needs = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1, "BN": 6}
    second = {"RB": 45.0, "WR": 40.0}
    elig = lambda pos: {"RB", "WR"}  # noqa: E731
    import copy
    exp = P.pair_rank(copy.deepcopy(cands), report, needs, second, elig)
    pv_exp = {p["sleeper_id"]: p["_pair"]["partner_pts"] for _s, _w, p in exp}
    cert = P.pair_rank(copy.deepcopy(cands), report, needs, second, elig, partner_certain=True)
    pv_cert = {p["sleeper_id"]: p["_pair"]["partner_pts"] for _s, _w, p in cert}
    # RB taken. Expected: the RB partner at min(e_best_next 20, second-best 45)
    # = 20 beats the WR partner at 10. Certain: WR at best_now 48 beats RB at
    # min(best_now 50, second-best 45) = 45.
    assert abs(pv_exp["a"] - 20.0) < 1e-9 and abs(pv_cert["a"] - 48.0) < 1e-9


def test_turn_seat_looks_through_to_the_following_turn():
    # seat 10 on the clock at pick 10: picks 10 and 11 are consecutive
    off = make_tracker(_board(), [], my_slot=10, current_pick=10)
    on = make_tracker(_board(), [], my_slot=10, current_pick=10)
    on.turn_look_through = True
    r_off = off.urgency_report()
    r_on = on.urgency_report()
    assert not getattr(off, "_look_through", False) and on._look_through
    # off: nobody between 10 and 11, every survival is exactly 1.0
    assert all(v == 1.0 for v in r_off["RB"]["survival"].values())
    # on: the window runs to pick 30, the early RBs are no longer certain
    assert min(r_on["RB"]["survival"].values()) < 1.0
    assert r_on["RB"]["urgency"] > r_off["RB"]["urgency"] == 0.0


def test_look_through_is_inert_off_the_turn():
    t = make_tracker(_board(), [], my_slot=4, current_pick=40)
    t.turn_look_through = True
    t.urgency_report()
    assert t._look_through is False

"""Cross-position comparison measures against what you'd actually end up with.

The two-pick planner used to compare positions on raw VORP LEVELS, which made
the whole engine depend on the league yaml's replacement baseline -- and that
baseline then had to be hand-fitted (Keefamania carried QB5/TE8, tuned to
minimise |VORP rank - ADP rank|) to stop the planner drafting quarterbacks too
early. Urgency was never affected: it is a difference, so the baseline cancels.

Measured 2026-09-01 over 22 draft slots: drafted-lineup projected points
spread 4.0 across QB5/TE8, QB7/TE10 and QB10/TE11 before, 0.4 after.
"""

from draftkit.planner import own_value, pair_rank
from draftkit.tracker import Tracker

from test_slot_markets import BOARD, SLOTS, make_tracker  # noqa: F401


# ---------- own_value ----------

def test_falls_back_to_slot_vorp_when_no_fallback_supplied():
    p = {"pos": "RB", "vorp": 40.0, "vorp_flex": 40.0, "proj_pts": 200.0}
    assert own_value(p, {"RB": 1}, None) == 40.0


def test_measures_points_above_the_player_you_would_end_up_with():
    p = {"pos": "QB", "vorp": 31.4, "proj_pts": 300.0}
    # you will end up with a QB projected 285 if you skip the position now,
    # so taking this one early is worth 15 -- not the 31.4 VORP says
    assert own_value(p, {"QB": 1}, {"QB": 285.0}) == 15.0


def test_a_position_missing_from_the_fallback_keeps_the_old_currency():
    p = {"pos": "DEF", "vorp": 6.0, "proj_pts": 90.0}
    assert own_value(p, {"DEF": 1}, {"QB": 285.0}) == 6.0


def test_the_same_vorp_can_be_worth_very_different_amounts():
    """The point of the whole change: one replacement number cannot say both
    'quarterbacks are streamable' and 'running backs are not'."""
    qb = {"pos": "QB", "vorp": 30.0, "proj_pts": 300.0}
    rb = {"pos": "RB", "vorp": 30.0, "proj_pts": 200.0}
    fb = {"QB": 290.0, "RB": 130.0}     # a startable QB is still there later
    assert own_value(qb, {"QB": 1}, fb) == 10.0
    assert own_value(rb, {"RB": 1}, fb) == 70.0


# ---------- Tracker._fallback_points ----------

def test_fallback_is_the_best_player_expected_to_survive_the_deadline():
    t = make_tracker(BOARD, [])
    needs = t.my_needs()
    fb = t._fallback_points(needs)
    # every position on the board has an answer
    assert {"QB", "RB", "WR", "TE"} <= set(fb)
    # and it never exceeds the best player currently available
    for pos, v in fb.items():
        avail = [p["proj_pts"] for p in t.remaining(pos)]
        if avail:
            assert v <= max(avail) + 1e-9


def test_fallback_is_worse_when_more_starters_are_still_unfilled():
    """The deadline is my S-th remaining pick, where S is the starters I still
    owe. Early on S is large, so the last chance to fill any one position is a
    long way off and almost nothing good survives to it -- which is exactly why
    an early pick is worth a lot. As the roster fills, S shrinks, the deadline
    moves closer, better players survive to it, and the marginal value of any
    single pick correctly falls.
    """
    early = make_tracker(BOARD, [])
    late = make_tracker(BOARD, ["mcbride", "my_wr1", "my_wr2", "rb_a", "rb_b",
                                "qb_a", "k_a", "def_a"])
    fb_e = early._fallback_points(early.my_needs())
    fb_l = late._fallback_points(late.my_needs())
    assert fb_e["WR"] < fb_l["WR"]


def test_no_remaining_picks_yields_no_fallback():
    t = make_tracker(BOARD, [])
    t.rounds = 0
    assert t._fallback_points(t.my_needs()) == {}


# ---------- replacement recovery ----------

def test_replacement_points_are_recovered_from_the_board():
    t = make_tracker(BOARD, [])
    repl = t._replacement_points()
    for p in t.players:
        if p["pos"] in repl:
            assert abs((p["proj_pts"] - p["vorp"]) - repl[p["pos"]]) < 1e-6
            break
    assert "FLEX" in repl


# ---------- the property this all exists for ----------

def _lineup(board_overrides, picks=()):
    t = make_tracker(BOARD, list(picks))
    for p in t.players:
        if p["pos"] in board_overrides:
            shift = board_overrides[p["pos"]]
            p["vorp"] = p["vorp"] + shift
            p["vorp_flex"] = p["vorp_flex"] + shift
    return t


def test_recommendations_are_insensitive_to_a_baseline_shift():
    """Shifting a position's replacement level shifts every VORP at that
    position by a constant. With the adaptive fallback the recommendation must
    not move; that is what makes the yaml number stop being a tuning knob.
    """
    a = _lineup({})
    b = _lineup({"QB": 25.0, "TE": -12.0})   # as if QB10/TE8 -> QB5/TE11
    assert a.adaptive_fallback and b.adaptive_fallback
    top_a = [p["sleeper_id"] for _s, _w, p in a.recommendations(top_n=3)]
    top_b = [p["sleeper_id"] for _s, _w, p in b.recommendations(top_n=3)]
    assert top_a == top_b, f"{top_a} != {top_b}"


def test_turning_the_fallback_off_restores_the_old_sensitivity():
    """Guards the A/B: if both arms behaved identically the measurement that
    justified this change would be meaningless."""
    a, b = _lineup({}), _lineup({"QB": 90.0})
    a.adaptive_fallback = b.adaptive_fallback = False
    assert Tracker.adaptive_fallback is True     # default stays on
    top_a = [p["sleeper_id"] for _s, _w, p in a.recommendations(top_n=1)]
    top_b = [p["sleeper_id"] for _s, _w, p in b.recommendations(top_n=1)]
    assert top_a != top_b, "the A/B is meaningless if both arms agree"

    # ...and the same shift leaves the adaptive arm alone
    c, d = _lineup({}), _lineup({"QB": 90.0})
    assert ([p["sleeper_id"] for _s, _w, p in c.recommendations(top_n=1)]
            == [p["sleeper_id"] for _s, _w, p in d.recommendations(top_n=1)])


# ---------- planner currency consistency ----------

def test_partner_term_is_converted_into_the_fallback_currency():
    """Mixing a VORP partner with a fallback-measured candidate would add two
    different units together."""
    cands = [(5.0, "w", {"pos": "WR", "vorp": 50.0, "proj_pts": 250.0,
                         "sleeper_id": "w"}),
             (4.0, "r", {"pos": "RB", "vorp": 50.0, "proj_pts": 200.0,
                         "sleeper_id": "r"})]
    report = {"WR": {"e_best_next": 40.0}, "RB": {"e_best_next": 40.0}}
    needs = {"WR": 2, "RB": 2, "FLEX": 1}
    # identical VORP, but the RB's fallback is far worse, so he must win
    fb = {"WR": 240.0, "RB": 130.0}
    repl = {"WR": 200.0, "RB": 150.0}
    ranked = pair_rank(cands, report, needs, {"WR": 10.0, "RB": 10.0},
                       lambda _t: {"WR", "RB"}, fallback=fb, repl=repl)
    assert ranked[0][2]["sleeper_id"] == "r"

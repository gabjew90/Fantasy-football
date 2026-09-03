"""Bench realities (draftkit/bench.py) — insurance pricing for non-starters.

The engine drafted a second quarterback in 21 of 22 replayed rosters because
bench rounds priced candidates as VORP against the STARTER baseline. A bench
player competes with the waiver wire, and is only used in the weeks a starter
is out. Both facts are league-derived; neither is per-player injury history.
"""

import pytest

from draftkit import bench as B

from test_slot_markets import BOARD, SLOTS, make_tracker, player  # noqa: F401


# ---------- weeks needed ----------

def test_first_backup_of_one_starter_is_the_base_rate():
    assert B.weeks_needed("RB", 1) == pytest.approx(B.ABSENT_WEEKS["RB"] + B.BYE_WEEKS)


def test_more_starters_means_more_weeks_but_less_than_linear():
    """Two starters' absences overlap sometimes, so the first backup behind
    two is worth less than twice the first backup behind one."""
    one, two = B.weeks_needed("RB", 1), B.weeks_needed("RB", 2)
    assert one < two < 2 * one


def test_each_additional_reserve_is_worth_much_less_than_the_last():
    """The season replay found every losing Keefamania slot had drafted a 6th
    WR -- priced as if he covered the first absence when he covered the
    third. The (n+1)th backup plays only when n+1 starters are out together."""
    first = B.weeks_needed("WR", 3, depth_ahead=0)
    second = B.weeks_needed("WR", 3, depth_ahead=1)
    third = B.weeks_needed("WR", 3, depth_ahead=2)
    assert first > second > third > 0
    assert third < 0.15 * first
    assert B.weeks_needed("WR", 3, depth_ahead=3) == 0.0   # nobody left to cover


def test_depth_flows_through_insurance_value():
    p = player("x", "WR", 0, 0, 100.0)
    p["proj_pts"] = 170.0
    fresh = B.insurance_value(p, waiver=6.0, exposure=3, depth_ahead=0)
    sixth = B.insurance_value(p, waiver=6.0, exposure=3, depth_ahead=2)
    assert sixth["value"] < 0.15 * fresh["value"]
    assert sixth["depth_ahead"] == 2


def test_weeks_needed_is_zero_with_nothing_to_cover():
    assert B.weeks_needed("QB", 0) == 0.0
    assert B.weeks_needed("K", 1) == 0.0        # not a bench position


def test_base_rates_are_position_facts_not_player_history():
    """Guards the design decision: the frequency term must not be keyed by
    player. research Q6 -- per-player games-missed was removed 2026-08-30."""
    assert set(B.ABSENT_WEEKS) == {"QB", "RB", "WR", "TE"}
    assert all(0.5 < v < 6.0 for v in B.ABSENT_WEEKS.values())
    assert B.ABSENT_WEEKS["RB"] > B.ABSENT_WEEKS["QB"]


# ---------- exposure ----------

def test_exposure_counts_flex_starters():
    """A bench RB insures an RB starting in the FLEX just as much as one in
    an RB slot."""
    got = B.starter_exposure(["RB", "RB", "RB", "WR", "WR", "TE", "QB"], SLOTS)
    assert got["RB"] == 3          # two dedicated + one in the flex
    assert got["WR"] == 2
    assert got["QB"] == 1


def test_exposure_ignores_bench_players():
    got = B.starter_exposure(["QB", "QB", "QB"], SLOTS)
    assert got == {"QB": 1}


# ---------- waiver level ----------

def _pool():
    return [player("a", "QB", 60, 60, 20.0), player("b", "QB", 40, 40, 90.0),
            player("c", "QB", 30, 30, 160.0), player("d", "QB", 25, 25, 170.0),
            player("e", "QB", 20, 20, None)]


def test_waiver_level_is_the_kth_best_the_market_leaves_undrafted():
    ppw, name = B.waiver_ppw(_pool(), last_pick=150, k=1)
    assert name == "c" and ppw == pytest.approx(130.0 / 17)
    ppw, name = B.waiver_ppw(_pool(), last_pick=150, k=2)
    assert name == "d"


def test_missing_adp_counts_as_undrafted():
    _ppw, name = B.waiver_ppw(_pool(), last_pick=150, k=3)
    assert name == "e"


def test_thin_wire_takes_its_worst_rather_than_failing():
    _ppw, name = B.waiver_ppw(_pool(), last_pick=150, k=10)
    assert name == "e"


def test_no_projected_undrafted_falls_back_to_the_worst_remaining():
    pool = [player("a", "QB", 60, 60, 20.0), player("b", "QB", 40, 40, 90.0)]
    _ppw, name = B.waiver_ppw(pool, last_pick=150, k=3)
    assert name == "b"


# ---------- insurance value ----------

def test_edge_over_the_wire_never_goes_negative():
    p = player("x", "QB", 0, 0, 100.0)
    p["proj_pts"] = 170.0                    # 10/wk
    iv = B.insurance_value(p, waiver=12.0, exposure=1)
    assert iv["edge"] == 0.0 and iv["value"] == 0.0


def test_value_is_edge_times_weeks():
    p = player("x", "RB", 0, 0, 100.0)
    p["proj_pts"] = 170.0                    # 10/wk
    iv = B.insurance_value(p, waiver=6.0, exposure=2)
    assert iv["edge"] == pytest.approx(4.0)
    assert iv["value"] == pytest.approx(4.0 * B.weeks_needed("RB", 2))


def test_the_worked_example_prefers_rb_depth_over_a_backup_qb():
    """Real numbers from the 2026-09-01 board. On weekly edge alone the QB2
    wins (+3.8 vs +2.5); frequency of need is what flips it, which is why
    that term is load-bearing and not an elaboration."""
    qb2 = player("Lawrence", "QB", 0, 0, 100.0); qb2["proj_pts"] = 289.9
    rb = player("Gainwell", "RB", 0, 0, 100.0); rb["proj_pts"] = 154.0
    qb = B.insurance_value(qb2, waiver=225.8 / 17, exposure=1)
    r = B.insurance_value(rb, waiver=111.4 / 17, exposure=2)
    assert qb["edge"] > r["edge"], "edge alone favours the QB2 -- that is the point"
    assert r["value"] > qb["value"]


def test_handcuff_uplift_applies_and_is_capped_at_the_starters_rate():
    hc = player("backup", "RB", 0, 0, 100.0); hc["proj_pts"] = 102.0   # 6/wk
    plain = B.insurance_value(hc, waiver=5.0, exposure=2)
    lifted = B.insurance_value(hc, waiver=5.0, exposure=2, handcuff_starter_ppw=20.0)
    assert lifted["ppw"] == pytest.approx(6.0 * B.HANDCUFF_UPLIFT)
    assert lifted["value"] > plain["value"]
    capped = B.insurance_value(hc, waiver=5.0, exposure=2, handcuff_starter_ppw=7.0)
    assert capped["ppw"] == pytest.approx(7.0)


# ---------- tracker integration ----------

BENCH_BOARD = [
    # my starters: a full lineup, all slots filled
    player("my_qb", "QB", 30, 30, 40.0), player("my_rb1", "RB", 60, 60, 5.0),
    player("my_rb2", "RB", 50, 50, 15.0), player("my_wr1", "WR", 55, 42, 9.0),
    player("my_wr2", "WR", 45, 32, 12.0), player("my_te", "TE", 40, 20, 30.0),
    player("my_flex", "WR", 40, 27, 25.0),
    # bench candidates: a backup QB with big positional VORP, an RB with small
    player("qb2", "QB", 25.0, 25.0, 95.0, rank=6),
    player("rb_depth", "RB", 4.0, 4.0, 96.0, rank=30),
    player("rb_cuff", "RB", 2.0, 2.0, 120.0, rank=34),
    # the wire
    player("qb_wire", "QB", 8.0, 8.0, 160.0, rank=20),
    player("rb_wire", "RB", -20.0, -20.0, 165.0, rank=50),
    player("k_a", "K", 5.0, 5.0, 150.0), player("def_a", "DEF", 4.0, 4.0, 150.0),
] + [player(f"pad{i}", ("RB", "WR", "TE")[i % 3], -8.0 - i * 0.1,
            -20.0 - i * 0.1, 60.0 + i, rank=40 + i, tier=8) for i in range(30)]
for _p in BENCH_BOARD:
    _p["proj_pts"] = {"qb2": 280.0, "rb_depth": 150.0, "rb_cuff": 110.0,
                      "qb_wire": 230.0, "rb_wire": 95.0}.get(_p["sleeper_id"],
                                                             _p["proj_pts"])
    _p["backs_up"] = "my_rb1" if _p["sleeper_id"] == "rb_cuff" else ""
MY_LINEUP = ["my_qb", "my_rb1", "my_rb2", "my_wr1", "my_wr2", "my_te", "my_flex"]


def test_bench_mode_off_still_takes_the_backup_qb():
    t = make_tracker(BENCH_BOARD, MY_LINEUP, current_pick=101)
    t.bench_insurance = False
    top = t.recommendations(top_n=1)[0][2]
    assert top["sleeper_id"] == "qb2", "fixture must reproduce the bug"


def test_bench_mode_on_prefers_rb_insurance_over_the_backup_qb():
    t = make_tracker(BENCH_BOARD, MY_LINEUP, current_pick=101)
    t.bench_insurance = True
    recs = t.recommendations(top_n=3)
    assert recs[0][2]["pos"] == "RB"
    assert "bench insurance" in recs[0][1]


def test_handcuff_of_my_own_starter_is_recognised():
    t = make_tracker(BENCH_BOARD, MY_LINEUP, current_pick=101)
    t.bench_insurance = True
    recs = t.recommendations(top_n=3)
    rb_row = next(r for r in recs if r[2]["pos"] == "RB")
    assert rb_row[2]["sleeper_id"] == "rb_cuff"
    assert "HANDCUFF" in rb_row[1]


def test_bench_pricing_never_runs_while_a_starter_slot_is_open():
    t = make_tracker(BENCH_BOARD, MY_LINEUP[:-1], current_pick=101)   # flex open
    t.bench_insurance = True
    assert all("bench insurance" not in w for _s, w, _p in t.recommendations(top_n=5))


def test_bench_pricing_yields_to_the_must_fill_window():
    """With two picks left and K/DEF still open, every pick is owed to a
    starter -- no bench row may be offered."""
    t = make_tracker(BENCH_BOARD, MY_LINEUP + ["rb_depth"] * 0, current_pick=131)
    t.bench_insurance = True
    t.rounds = 15
    # my picks so far: 7 starters -> 8 picks left; force the window by
    # shrinking the draft so only 2 remain
    t.rounds = 9
    assert all("bench insurance" not in w for _s, w, _p in t.recommendations(top_n=5))


def test_default_is_on_and_the_ab_knob_still_exists():
    """Turned on 2026-09-01 after the season replay showed a win on both
    leagues. The knob stays so the A/B can be re-run."""
    from draftkit.tracker import Tracker
    assert Tracker.bench_insurance is True
    t = make_tracker(BENCH_BOARD, MY_LINEUP, current_pick=101)
    t.bench_insurance = False
    assert t.recommendations(top_n=1)[0][2]["sleeper_id"] == "qb2"


def test_wire_never_names_a_zeroed_or_out_player():
    """The 2026-09-03 Josh Jacobs defect: an availability-'out' player with a
    zeroed projection was the wire floor, so RB insurance was measured
    against a ghost."""
    from draftkit.bench import waiver_ppw
    healthy_deep = {"player": "Deep Back", "proj_pts": 119.0, "adp": 160.0}
    ghost = {"player": "Josh Jacobs", "proj_pts": 0.0, "adp": 37.2, "avail_status": "out"}
    ppw, name = waiver_ppw([healthy_deep, ghost], last_pick=150, k=1)
    assert name == "Deep Back" and ppw == 119.0 / 17.0

    # no viable undrafted player on the board: the worst VIABLE remaining
    # player is the floor, never the ghost
    drafted_range = {"player": "Early Back", "proj_pts": 200.0, "adp": 40.0}
    ppw, name = waiver_ppw([drafted_range, ghost], last_pick=150, k=3)
    assert name == "Early Back" and ppw == 200.0 / 17.0

    # nothing viable at all
    assert waiver_ppw([ghost], last_pick=150, k=3) == (0.0, "")


def test_wire_is_kth_best_projection_among_predicted_undrafted():
    """User find (2026-09-03 evening): the ADP>last_pick filter left the RB
    wire empty on this board and the floor fell to a 45-pt player. The wire
    must be who is actually left after the market spends its remaining
    picks in ADP order."""
    from draftkit.bench import predicted_undrafted, waiver_ppw
    rem_all = ([{"player": f"Early{i}", "pos": "RB", "proj_pts": 200.0 - i, "adp": 10.0 + i} for i in range(4)]
               + [{"player": "WireBack1", "pos": "RB", "proj_pts": 120.0, "adp": 60.0},
                  {"player": "WireBack2", "pos": "RB", "proj_pts": 110.0, "adp": 70.0},
                  {"player": "WireBack3", "pos": "RB", "proj_pts": 100.0, "adp": None},
                  {"player": "TailBack", "pos": "RB", "proj_pts": 45.0, "adp": 52.0}])
    # 4 picks left (147..150): the market takes the four Early backs; the
    # TailBack's low ADP does NOT save him from the wire set, and the wire
    # is ranked by projection, so k=3 lands on WireBack3 at 100.
    wire = predicted_undrafted(rem_all, current_pick=147, last_pick=150)
    assert wire == {"WireBack1", "WireBack2", "WireBack3", "TailBack"}
    ppw, name = waiver_ppw(rem_all, last_pick=150, k=3, wire_names=wire)
    assert name == "WireBack3" and abs(ppw - 100.0 / 17.0) < 1e-9

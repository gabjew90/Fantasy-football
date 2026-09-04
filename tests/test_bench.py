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


def test_fallback_is_floored_by_the_market_projection():
    """Winner's-curse guard (user find 2026-09-03): the fallback player is the
    max projection among ADP survivors, which selects the model's biggest
    tail over-projection; price him at min(blend, market)."""
    from draftkit.tracker import Tracker
    t = Tracker.__new__(Tracker)
    t.my_slot, t.teams, t.rounds = 5, 10, 15
    # current_pick is len(state.picks) + 1: 59 picks made puts us at pick 60
    t.state = type("S", (), {"drafted_ids": set(), "picks": [{} for _ in range(59)]})()
    t.players = [
        {"sleeper_id": "1", "pos": "RB", "player": "Tail Back", "proj_pts": 155.0, "proj_market_pts": 136.0, "adp": 107.0, "vorp": 20.0},
        {"sleeper_id": "2", "pos": "RB", "player": "Honest Back", "proj_pts": 140.0, "proj_market_pts": 141.0, "adp": 110.0, "vorp": 10.0},
        {"sleeper_id": "3", "pos": "WR", "player": "Some Wide", "proj_pts": 150.0, "proj_market_pts": "", "adp": 120.0, "vorp": 15.0},
    ]
    fb = t._fallback_points({"RB": 1, "WR": 1})
    # Tail Back's blend 155 would have been the RB fallback; floored to 136 he
    # loses to Honest Back at min(140, 141) = 140
    assert fb["RB"] == 140.0
    # no market number: the blend stands
    assert fb["WR"] == 150.0


# ---------- the market/bench seam (2026-09-04, plan item B) ------------------
# `_open_markets` never returns empty: once every slot is filled it revives all
# six positional markets on `vorp`, which is EXACTLY when bench mode is also
# active. So a player lands in the list twice -- once as a market row carrying
# `urgency + 0.001*mv`, once insurance-priced in raw season points. Keeping the
# larger number is not a comparison between two candidates, it is a coin flip
# between two rulers.
#
# The rule: prefer the BENCH row, except for an upgrade whose own projection
# beats the starter he would displace. Insurance prices a man who plays only
# when someone is out; an upgrade plays every week.
#
# The fixture is fussy for two reasons, and both were mistakes made first:
#
#  * The seam needs K AND DEF filled as well. With either still open,
#    `_open_markets` returns only that market, so no positional row exists to
#    collide with and every test below passes vacuously.
#  * A collision needs ONE player to be both his market's best by vorp and his
#    position's best by insurance -- `_bench_candidates` emits a single row per
#    position. In the original board the only such player is qb2, who is an
#    upgrade, so the knob changed nothing and the tests proved nothing.
#    `wr_depth` is the case that actually moves: market winner at WR, insurance
#    winner at WR, and projected below the weakest WR I start.

SEAM_LINEUP = MY_LINEUP + ["k_a", "def_a"]
_wr_depth = player("wr_depth", "WR", 18.0, 18.0, 100.0, rank=9)
_wr_depth["proj_pts"] = 130.0          # my weakest starting WR projects 140
_wr_depth["backs_up"] = ""
SEAM_BOARD = [dict(q) for q in BENCH_BOARD] + [_wr_depth]


def _seam_tracker(prefer_bench: bool):
    t = make_tracker(SEAM_BOARD, SEAM_LINEUP, current_pick=101)
    t.bench_insurance = True
    t.bench_row_wins_dedupe = prefer_bench
    return t


def _rows(prefer_bench: bool):
    return _seam_tracker(prefer_bench).recommendations(top_n=12)


def _row(prefer_bench: bool, sid: str):
    return next(r for r in _rows(prefer_bench) if r[2]["sleeper_id"] == sid)


def _is_bench(row) -> bool:
    from draftkit.tracker import BENCH_WHY_PREFIX
    return str(row[1]).startswith(BENCH_WHY_PREFIX)


def test_the_seam_fixture_really_revives_the_positional_markets():
    t = _seam_tracker(True)
    markets = [m for m, _members, _v in t._open_markets(t.my_needs())]
    assert set(markets) >= {"QB", "RB", "WR", "TE"}, markets


def test_the_seam_fixture_really_prices_one_player_two_ways():
    """Without a genuine collision the knob is untested. wr_depth must be both
    the WR market's pick and the WR insurance pick."""
    t = _seam_tracker(False)
    needs, counts = t.my_needs(), t._my_pos_counts()
    cands: list = []
    added, _upgrades = t._bench_candidates(cands, needs, counts, 11, 6, False)
    assert added
    assert any(c[2]["sleeper_id"] == "wr_depth" for c in cands), \
        "wr_depth is not the WR insurance row -- the collision is gone"
    assert _row(False, "wr_depth") is not None


def test_no_player_carries_two_currencies_at_once():
    for prefer_bench in (False, True):
        ids = [r[2]["sleeper_id"] for r in _rows(prefer_bench)]
        assert len(ids) == len(set(ids)), f"duplicate row, prefer_bench={prefer_bench}"


def test_the_knob_actually_changes_which_ruler_a_backup_is_measured_on():
    """Today the market row wins purely because 24.3 > 20.9 -- two numbers in
    different units. With the knob on, insurance wins because insurance is the
    right question for a bench player."""
    assert not _is_bench(_row(False, "wr_depth")), "fixture no longer reproduces it"
    assert _is_bench(_row(True, "wr_depth"))


def test_the_upgrade_is_identified_by_beating_the_starter_he_displaces():
    """qb2 projects 280 against my starting QB's 130, so he is not a backup at
    all. wr_depth projects 130 against my weakest WR starter's 140, so he is."""
    t = _seam_tracker(True)
    added, upgrade_ids = t._bench_candidates(
        [], t.my_needs(), t._my_pos_counts(), 11, 6, False)
    assert added
    assert "qb2" in upgrade_ids
    assert "wr_depth" not in upgrade_ids


def test_an_upgrade_keeps_his_market_row_rather_than_being_priced_as_a_backup():
    """The failure this exception exists to prevent: pricing a man who starts
    every week as one who plays ~3 weeks a season."""
    assert not _is_bench(_row(True, "qb2"))


def test_the_preference_is_symmetric_not_a_bolted_on_exception():
    """First cut only blocked market->bench for an upgrade, so an upgrade whose
    BENCH row happened to sort first kept it anyway. Whichever way the scores
    fall, the ruler is chosen by what the player is."""
    for prefer_bench in (False, True):
        rows = _rows(prefer_bench)
        assert rows == sorted(rows, key=lambda r: -r[0]), "greedy order broken"


def test_the_default_is_todays_behaviour():
    """B ships off, and off means the old rule verbatim: first row wins per
    player, which after the score sort is the larger number regardless of
    which currency it is denominated in."""
    from draftkit.tracker import Tracker
    assert Tracker.bench_row_wins_dedupe is False
    t = _seam_tracker(False)
    assert t.bench_row_wins_dedupe is False
    for sid in ("wr_depth", "qb2", "rb_depth"):
        assert not _is_bench(_row(False, sid)), sid
    assert _is_bench(_row(False, "rb_cuff"))   # his bench row simply scores higher

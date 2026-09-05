"""Bench rows: the survival drop-off, the contingency term, and the band
tiebreak (2026-09-04, user-approved design; DECISIONS #47). All three are
behind knobs that default to today's behaviour.
"""

import copy

from draftkit import bench as B
from test_bench import BENCH_BOARD, MY_LINEUP
from test_slot_markets import make_tracker, player  # noqa: F401


def _fake_report(surv: dict[str, dict[str, float]]):
    """An urgency report with only what the bench path reads (survival) plus
    the keys the revived positional markets touch on the same call."""
    def rep():
        out = {}
        for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
            out[pos] = {"urgency": 0.0, "best_now": 0.0, "e_best_next": 0.0,
                        "survival": surv.get(pos, {})}
        return out
    return rep


def _bench_tracker(board=BENCH_BOARD, **knobs):
    t = make_tracker(board, MY_LINEUP, current_pick=101)
    t.bench_insurance = True
    for k, v in knobs.items():
        setattr(t, k, v)
    return t


# ------------------------------------------------------------ contingency

def test_contingency_prices_the_role_shift_for_a_rivals_backup():
    p = {"pos": "RB", "proj_pts": 110.0}
    base = B.insurance_value(p, waiver=5.0, exposure=3, depth_ahead=2)
    with_c = B.insurance_value(p, waiver=5.0, exposure=3, depth_ahead=2,
                               contingency_weeks=B.ABSENT_WEEKS["RB"],
                               contingency_starter_ppw=250.0 / 17.0,
                               my_weakest_ppw=140.0 / 17.0)
    own = 110.0 / 17.0
    expect = max(0.0, min(own * B.HANDCUFF_UPLIFT, 250.0 / 17.0) - 140.0 / 17.0) * B.ABSENT_WEEKS["RB"]
    assert with_c["contingency"] > 0
    assert abs(with_c["contingency"] - expect) < 1e-9
    assert abs(with_c["value"] - (base["value"] + expect)) < 1e-9


def test_contingency_is_zero_when_he_would_not_start_over_my_weakest():
    p = {"pos": "RB", "proj_pts": 60.0}          # 3.5 a week, x1.46 = 5.2, below my 8.2
    r = B.insurance_value(p, waiver=1.0, exposure=3, contingency_weeks=3.13,
                          contingency_starter_ppw=15.0, my_weakest_ppw=140.0 / 17.0)
    assert r["contingency"] == 0.0


def test_contingency_never_stacks_on_my_own_handcuff():
    p = {"pos": "RB", "proj_pts": 110.0}
    r = B.insurance_value(p, waiver=5.0, exposure=3, handcuff_starter_ppw=250.0 / 17.0,
                          contingency_weeks=3.13, contingency_starter_ppw=250.0 / 17.0,
                          my_weakest_ppw=140.0 / 17.0)
    assert r["handcuff"] and r["contingency"] == 0.0


def test_a_rivals_backup_is_always_priced_for_the_role_shift():
    """Staged bench (2026-09-05): the offensive term is part of insurance, no
    knob. The same back priced with and without a rival starter to inherit."""
    def board_with(backs_up):
        board = [copy.deepcopy(p) for p in BENCH_BOARD if p["sleeper_id"] not in ("rb_cuff", "rb_depth")]
        rival = player("rival_rb", "RB", 70, 70, 3.0)
        rival["proj_pts"] = 250.0
        cuff2 = player("rb_cuff2", "RB", 2.5, 2.5, 121.0, rank=35)
        cuff2["proj_pts"] = 110.0
        cuff2["backs_up"] = backs_up
        return board + [rival, cuff2]
    plain = _bench_tracker(board_with(""))
    cuff = _bench_tracker(board_with("rival_rb"))
    for t in (plain, cuff):
        t.state.drafted_ids.add("rival_rb")        # on a rival's roster, not on the wire
    row_plain = next(r for r in plain.recommendations(10) if r[2]["sleeper_id"] == "rb_cuff2")
    row_cuff = next(r for r in cuff.recommendations(10) if r[2]["sleeper_id"] == "rb_cuff2")
    assert row_cuff[2]["_staged"]["insurance"] > row_plain[2]["_staged"]["insurance"]
    assert "role shift if rival_rb goes down" in row_cuff[1]
    assert "role shift" not in row_plain[1]


# --------------------------------------------------------- survival drop-off

def test_timing_multiplier_takes_the_scarce_item_first():
    """Staged bench: score = insurance x (1 - survival). rb_cuff (my handcuff)
    is the bigger insurance number but certain to be there next turn, so he
    scores 0 and waits; qb2 is smaller and 20% to survive, so he goes now."""
    surv = {"RB": {"rb_depth": 1.0, "rb_cuff": 1.0}, "QB": {"qb2": 0.2}}
    t = _bench_tracker()
    t.urgency_report = _fake_report(surv)
    rows = t.recommendations(5)
    top = rows[0]
    assert top[2]["sleeper_id"] == "qb2", [(r[2]["sleeper_id"], round(r[0], 2)) for r in rows]
    assert "timing: 20% he is still there" in top[1] and "BENCH STAGED" in top[1]
    cuff = next(r for r in rows if r[2]["sleeper_id"] == "rb_cuff")
    assert cuff[0] == 0.0 and cuff[2]["_staged"]["insurance"] > top[2]["_staged"]["insurance"]


def test_bench_score_is_insurance_times_one_minus_survival():
    surv = {"RB": {"rb_cuff": 0.5, "rb_depth": 1.0}, "QB": {"qb2": 1.0}}
    t = _bench_tracker()
    t.urgency_report = _fake_report(surv)
    row = next(r for r in t.recommendations(10) if r[2]["sleeper_id"] == "rb_cuff")
    ins = row[2]["_staged"]["insurance"]
    assert ins > 0 and abs(row[0] - 0.5 * ins) < 0.06


def test_missing_survival_counts_as_certain():
    surv = {"RB": {}, "QB": {"qb2": 0.2}}      # nothing about the RBs: they survive
    t = _bench_tracker(bench_survival_discount=True)
    t.urgency_report = _fake_report(surv)
    rows = {r[2]["sleeper_id"]: r for r in t.recommendations(10)}
    assert rows["rb_cuff"][0] == 0.0
    assert "100% he is still there" in rows["rb_cuff"][1]


# ------------------------------------------- raw value, ceiling tiebreak (#55)

def _pool(board, my_extra=()):
    """A tracker in bench mode at pick 101 over `board` plus my full lineup."""
    t = make_tracker(board, MY_LINEUP + list(my_extra), current_pick=101)
    t.bench_insurance = True
    return t


def test_insurance_value_returns_the_raw_edge_alongside_the_floored_one():
    below = B.insurance_value({"pos": "RB", "proj_pts": 77.0}, waiver=82.0 / 17.0, exposure=2)
    above = B.insurance_value({"pos": "WR", "proj_pts": 117.0}, waiver=100.0 / 17.0, exposure=3)
    assert below["edge"] == 0.0 and below["value"] == 0.0
    assert below["edge_raw"] < 0 and below["value_raw"] < 0
    assert above["value_raw"] == above["value"] > 0


def _rod_sutton_board():
    """Room 10790713 pick 105: Rodriguez (RB, 77 pts, below an 82-pt wire,
    band 22) against Sutton (WR, 117 pts, above a 100-pt wire, band 4)."""
    board = [copy.deepcopy(p) for p in BENCH_BOARD if p["sleeper_id"] not in ("rb_depth", "rb_cuff", "qb2", "wr_depth")]
    def mk(pid, pos, pts, adp, band, rank):
        q = player(pid, pos, pts - 100.0, pts - 100.0, adp, rank=rank)
        q["proj_pts"], q["proj_band"], q["backs_up"] = pts, band, ""
        return q
    board += [mk("rodriguez", "RB", 77.0, 130.7, 22.3, 40), mk("sutton", "WR", 116.6, 105.9, 4.2, 45)]
    # the wire: three RBs and three WRs the market leaves undrafted
    for i, pts in enumerate((82.0, 81.0, 80.0)):
        board.append(mk(f"rb_wire{i}", "RB", pts, 140.0 + i, 5.0, 50 + i))
    for i, pts in enumerate((100.0, 99.0, 98.0)):
        board.append(mk(f"wr_wire{i}", "WR", pts, 140.0 + i, 5.0, 60 + i))
    return board


def test_a_back_below_the_wire_sorts_below_a_receiver_above_it():
    """The defect of the 09-04 review: Rodriguez, Randall and Tracy went
    over Sutton and Pittman because everyone priced at 0-2 points was a tie
    and the widest band won. Ranked on the raw value, a man below the wire
    is negative: he is not the RB row at all (the wire's own best back is),
    and the receiver above his wire heads the bench list."""
    t = _pool(_rod_sutton_board())
    bench = [r for r in t.recommendations(10) if str(r[1]).startswith("bench insurance")]
    ids = [r[2]["sleeper_id"] for r in bench]
    assert bench and ids[0] == "sutton", [(r[2]["sleeper_id"], round(r[0], 2)) for r in bench]
    # the staged bench pools every position: Rodriguez (negative insurance)
    # never sits above anyone at or above his wire
    if "rodriguez" in ids:
        rod = next(r for r in bench if r[2]["sleeper_id"] == "rodriguez")
        assert rod[2]["_staged"]["insurance"] < 0
        assert all(r[2]["_staged"]["insurance"] >= 0 for r in bench[:ids.index("rodriguez")]), ids
    # and priced directly, the wire's own back is worth about nothing, Rodriguez less
    t2 = _pool(_rod_sutton_board())
    cands: list = []
    t2._bench_candidates(cands, t2.my_needs(), t2._my_pos_counts(), 11, 8, False)
    by = {c[2]["sleeper_id"]: c[2]["_staged"]["insurance"] for c in cands}
    assert by["sutton"] > 0


def _twins_board(**edits):
    board = [copy.deepcopy(p) for p in BENCH_BOARD if p["sleeper_id"] not in ("rb_depth", "rb_cuff", "qb2", "wr_depth")]
    def mk(pid, **kw):
        q = player(pid, "RB", 10.0, 10.0, 120.0, rank=30)
        q["proj_pts"], q["backs_up"] = 110.0, ""
        q.update(kw)
        return q
    board += [mk("twin_a", **edits.get("a", {})), mk("twin_b", **edits.get("b", {}))]
    for i, pts in enumerate((82.0, 81.0, 80.0)):
        board.append(mk(f"rb_wire{i}", proj_pts=pts, adp=140.0 + i, sleeper_id=f"rb_wire{i}", player=f"rb_wire{i}"))
    return board


def test_bench_ties_break_on_the_ceiling_never_the_width():
    # same raw value; the higher published high line wins
    t = _pool(_twins_board(a={"proj_hi": 120.0, "proj_band": 30.0}, b={"proj_hi": 135.0, "proj_band": 5.0}))
    assert t.recommendations(5)[0][2]["sleeper_id"] == "twin_b", "ceiling, not width"
    # no high line: projection plus half the band stands in
    t = _pool(_twins_board(a={"proj_hi": None, "proj_band": 10.0}, b={"proj_hi": None, "proj_band": 30.0}))
    assert t.recommendations(5)[0][2]["sleeper_id"] == "twin_b"
    # no range on one side: a published ceiling beats none (staged bench,
    # 2026-09-05: a lottery ticket with a known upside over one with no range)
    t = _pool(_twins_board(a={"proj_hi": None, "proj_band": None}, b={"proj_hi": 140.0, "proj_band": 5.0}))
    assert t.recommendations(5)[0][2]["sleeper_id"] == "twin_b"


def test_knobs_are_registered_and_default_off():
    from draftkit.tracker import Tracker
    names = {n for n, _ in Tracker.ENGINE_KNOBS}
    assert {"bench_survival_discount", "bench_contingency"} <= names
    assert Tracker.bench_survival_discount is False and Tracker.bench_contingency is False


# ---------------------------------------------------------- two-pick form

def test_the_last_bench_pick_ranks_on_insurance_alone():
    """With no bench pick after this one there is nothing to wait for: the
    timing multiplier is dropped and rb_cuff (the bigger insurance number,
    certain to survive) is the row, not the 20% qb2."""
    surv = {"RB": {"rb_cuff": 1.0, "rb_depth": 1.0}, "QB": {"qb2": 0.2}}
    # 7 starters + 5 bench rostered, K and DEF still owed, so picks_left is 3
    # and no bench pick follows this one; the five bench bodies are WR/TE pads
    last = make_tracker(BENCH_BOARD, MY_LINEUP + ["pad1", "pad2", "pad4", "pad5", "pad7"], current_pick=131)
    last.bench_insurance = True
    last.urgency_report = _fake_report(surv)
    rows = last.recommendations(5)
    assert rows and rows[0][2]["sleeper_id"] == "rb_cuff", [r[2]["sleeper_id"] for r in rows]
    assert "insurance alone (last bench pick)" in rows[0][1] and "timing:" not in rows[0][1]


def test_zero_insurance_falls_through_to_the_ceiling_over_the_wire():
    """When every candidate's insurance rounds to zero the ceiling alone
    ranks, over the position's wire so positions compare, never board order."""
    board = _twins_board(a={"proj_pts": 80.0, "proj_hi": 84.0, "proj_band": 4.0},
                         b={"proj_pts": 80.0, "proj_hi": 130.0, "proj_band": 50.0})
    # only the twins and the wire stay as bench candidates; the wire is three
    # 80-point backs the market leaves, so k=3 is 80 and everyone's edge is 0
    keep = set(MY_LINEUP) | {"twin_a", "twin_b"}
    board = [q for q in board if q["sleeper_id"] in keep or q["sleeper_id"].startswith("rb_wire")]
    for q in board:
        if q["sleeper_id"].startswith("rb_wire"):
            q["proj_pts"], q["adp"] = 80.0, None
    t = _pool(board)
    rows = [r for r in t.recommendations(6) if str(r[1]).startswith("bench insurance")]
    assert rows, "no bench rows"
    assert all(r[2]["_staged"]["insurance"] <= 1e-9 for r in rows), [(r[2]["sleeper_id"], r[2]["_staged"]) for r in rows]
    assert rows[0][2]["sleeper_id"] == "twin_b" and "zero insurance everywhere: ceiling over the wire" in rows[0][1]


def test_a_man_below_the_wire_never_wins_a_ceiling_tie():
    """Review 2026-09-05: raw +1.1 against raw -0.6 is inside BENCH_TIE, and
    the sub-wire man has the wider range; he still may not take the row."""
    board = _twins_board(a={"proj_pts": 83.0, "proj_hi": 86.0, "proj_band": 3.0},
                         b={"proj_pts": 79.0, "proj_hi": 140.0, "proj_band": 40.0})
    # pin the wire. The market spends its 50 remaining picks in ADP order, so
    # give it 60 receivers to spend them on: the twins (ADP 120) get drafted,
    # the three no-ADP backs (82/81/80) are the RB wire and its k=3 is 80.
    # The fixture's other backs go, so the twins are the RB shortlist.
    keep = set(MY_LINEUP) | {"twin_a", "twin_b"}
    board = [q for q in board if q["sleeper_id"] in keep or q["sleeper_id"].startswith("rb_wire")]
    for q in board:
        if q["sleeper_id"].startswith("rb_wire"):
            q["adp"] = None
    for i in range(60):
        f = player(f"wrf{i}", "WR", -40.0, -40.0, 100.0 + i, rank=40 + i)   # not 'filler': the synthetic tracker names rival picks filler<n>
        f["proj_pts"], f["backs_up"] = 60.0, ""
        board.append(f)
    t = _pool(board)
    rb = next(r for r in t.recommendations(8) if str(r[1]).startswith("bench insurance") and r[2]["pos"] == "RB")
    assert rb[2]["sleeper_id"] == "twin_a" and rb[2]["_staged"]["insurance"] > 0, (rb[2]["sleeper_id"], rb[1][:160])


def test_tie_break_knob_rejects_a_misspelt_value():
    import pytest
    from draftkit.tracker import Tracker
    t = object.__new__(Tracker)
    with pytest.raises(ValueError):
        t.apply_engine_cfg({"tie_break": "touchdown"})
    t.apply_engine_cfg({"tie_break": "touchdowns"})
    assert t.tie_break == "touchdowns"


def test_published_range_reads_lines_then_band_then_nothing():
    from draftkit.boardrow import published_range
    assert published_range({"proj_pts": 170.0, "proj_lo": 150.0, "proj_hi": 199.8, "proj_band": 20.1}) == (150.0, 199.8)
    assert published_range({"proj_pts": 170.0, "proj_lo": 170.0, "proj_hi": 170.0, "proj_band": 10.0}) == (165.0, 175.0)
    assert published_range({"proj_pts": 170.0, "proj_lo": 170.0, "proj_hi": 170.0, "proj_band": None}) == (None, None)
    assert published_range({"proj_pts": 170.0, "proj_lo": None, "proj_hi": 180.0, "proj_band": None}) == (None, 180.0)


def test_a_handcuff_is_uplifted_only_in_his_own_starters_weeks():
    """Room 10796348 pick 73 (DECISIONS #58): Monangai (115 pts) backing up
    our flex Swift was priced at the uplifted rate across all 9.6 RB cover
    weeks and beat Pollard (142) 47 to 35. Split, the uplift covers Swift's
    ~4 absences and his own rate the other ~5.5: about 33, and Pollard's
    35 is the row."""
    wire = 80.4 / 17.0
    mon = B.insurance_value({"pos": "RB", "proj_pts": 115.2}, waiver=wire, exposure=3, handcuff_starter_ppw=174.4 / 17.0,
                            split_handcuff=True)
    pol = B.insurance_value({"pos": "RB", "proj_pts": 141.9}, waiver=wire, exposure=3, split_handcuff=True)
    old = B.insurance_value({"pos": "RB", "proj_pts": 115.2}, waiver=wire, exposure=3, handcuff_starter_ppw=174.4 / 17.0)
    assert old["value_raw"] > pol["value_raw"], "the #8 pricing (knob off) still has Monangai over Pollard"
    assert mon["handcuff"] and 0 < mon["handcuff_weeks"] < mon["weeks"]
    assert 30 < mon["value_raw"] < 36 and pol["value_raw"] > mon["value_raw"], (mon["value_raw"], pol["value_raw"])
    # a handcuff still beats a same-rate non-handcuff: the uplift is real in his starter's weeks
    twin = B.insurance_value({"pos": "RB", "proj_pts": 115.2}, waiver=wire, exposure=3, split_handcuff=True)
    assert mon["value_raw"] > twin["value_raw"]
    # the knob is registered and off by default
    from draftkit.tracker import Tracker
    assert ("handcuff_split", bool) in Tracker.ENGINE_KNOBS and Tracker.handcuff_split is False

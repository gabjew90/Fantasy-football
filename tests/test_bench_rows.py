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


def test_tracker_contingency_knob_raises_a_rivals_backup_and_says_why():
    # without my own handcuff on the board, the rival's backup is the RB row
    board = [copy.deepcopy(p) for p in BENCH_BOARD if p["sleeper_id"] not in ("rb_cuff", "rb_depth")]
    rival = player("rival_rb", "RB", 70, 70, 3.0)
    rival["proj_pts"] = 250.0
    cuff2 = player("rb_cuff2", "RB", 2.5, 2.5, 121.0, rank=35)
    cuff2["proj_pts"] = 110.0
    cuff2["backs_up"] = "rival_rb"
    board += [rival, cuff2]
    off = _bench_tracker(board, bench_contingency=False)
    on = _bench_tracker(board, bench_contingency=True)
    for t in (off, on):
        t.state.drafted_ids.add("rival_rb")        # on a rival's roster, not on the wire
    row_off = next(r for r in off.recommendations(10) if r[2]["sleeper_id"] == "rb_cuff2")
    row_on = next(r for r in on.recommendations(10) if r[2]["sleeper_id"] == "rb_cuff2")
    assert row_on[0] > row_off[0]
    assert "role shift if rival_rb goes down" in row_on[1]
    assert "role shift" not in row_off[1]


# --------------------------------------------------------- survival drop-off

def test_survival_discount_ranks_bench_rows_on_cost_of_waiting():
    # rb_cuff (my handcuff) is the bigger insurance number but certain to be
    # there next turn; qb2 is smaller and 20% to survive. Raw insurance takes
    # rb_cuff (the shipped behaviour); the drop-off takes qb2 now, rb_cuff later.
    surv = {"RB": {"rb_depth": 1.0, "rb_cuff": 1.0}, "QB": {"qb2": 0.2}}
    off = _bench_tracker(bench_survival_discount=False)
    off.urgency_report = _fake_report(surv)
    on = _bench_tracker(bench_survival_discount=True)
    on.urgency_report = _fake_report(surv)
    assert off.recommendations(5)[0][2]["sleeper_id"] == "rb_cuff"
    top = on.recommendations(5)[0]
    assert top[2]["sleeper_id"] == "qb2"
    assert "waiting likely costs" in top[1] and "20% he is still there" in top[1]


def test_survival_discount_is_the_expected_best_operator_not_one_minus_s():
    # rb_cuff at 50% with rb_depth (a close second) certain to be there:
    # waiting costs P(first gone) x the GAP to the second, not (1 - s) x his
    # whole value.
    surv = {"RB": {"rb_cuff": 0.5, "rb_depth": 1.0}, "QB": {"qb2": 1.0}}
    off = _bench_tracker(bench_survival_discount=False)
    off.urgency_report = _fake_report(surv)
    on = _bench_tracker(bench_survival_discount=True)
    on.urgency_report = _fake_report(surv)
    value = {r[2]["sleeper_id"]: r[0] for r in off.recommendations(10)}["rb_cuff"]
    cost = {r[2]["sleeper_id"]: r[0] for r in on.recommendations(10)}["rb_cuff"]
    assert value > 0
    assert 0.0 <= cost < 0.25 * value          # (1 - s) x value would be 0.5 x value


def test_missing_survival_counts_as_certain():
    surv = {"RB": {}, "QB": {"qb2": 0.2}}      # nothing about the RBs: they survive
    t = _bench_tracker(bench_survival_discount=True)
    t.urgency_report = _fake_report(surv)
    rows = {r[2]["sleeper_id"]: r for r in t.recommendations(10)}
    assert rows["rb_cuff"][0] == 0.0
    assert "100% he is still there" in rows["rb_cuff"][1]


# --------------------------------------------------------------- band tiebreak

def test_band_breaks_a_bench_near_tie_from_the_upside_round():
    board = copy.deepcopy(BENCH_BOARD)
    twin = copy.deepcopy(next(p for p in board if p["sleeper_id"] == "rb_cuff"))
    twin.update(sleeper_id="rb_cuff_wide", player="rb_cuff_wide", adp=121.0, proj_band=30.0)
    for p in board:
        p.setdefault("proj_band", 5.0)
    board.append(twin)
    off = _bench_tracker(board, late_round_dispersion=False)
    on = _bench_tracker(board, late_round_dispersion=True)
    off.upside_from_round = on.upside_from_round = 8            # pick 101 is round 11
    assert off.recommendations(5)[0][2]["sleeper_id"] == "rb_cuff"
    assert on.recommendations(5)[0][2]["sleeper_id"] == "rb_cuff_wide"


def test_band_tiebreak_stays_out_before_the_upside_round():
    board = copy.deepcopy(BENCH_BOARD)
    twin = copy.deepcopy(next(p for p in board if p["sleeper_id"] == "rb_cuff"))
    twin.update(sleeper_id="rb_cuff_wide", player="rb_cuff_wide", adp=121.0, proj_band=30.0)
    board.append(twin)
    on = _bench_tracker(board, late_round_dispersion=True)
    on.upside_from_round = 14
    assert on.recommendations(5)[0][2]["sleeper_id"] == "rb_cuff"


def test_knobs_are_registered_and_default_off():
    from draftkit.tracker import Tracker
    names = {n for n, _ in Tracker.ENGINE_KNOBS}
    assert {"bench_survival_discount", "bench_contingency"} <= names
    assert Tracker.bench_survival_discount is False and Tracker.bench_contingency is False

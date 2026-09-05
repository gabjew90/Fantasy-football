"""The shown-row survival calibration (2026-09-05) and the two stage-1
softenings: the relative urgency band and the flat-board exception."""

import pytest

from draftkit.staged import URGENCY_FLOOR, URGENCY_REL, staged_rank
from draftkit.tracker import Tracker, calibrate_survival
from test_staged import FALLBACK, NEEDS, REPL, _p, _report

KNOTS = [(0.16, 0.14), (0.40, 0.21), (0.60, 0.43), (0.81, 0.73), (0.96, 0.88)]


def test_calibration_interpolates_through_the_knots_and_the_implied_ends():
    assert calibrate_survival(0.40, KNOTS) == pytest.approx(0.21)
    assert calibrate_survival(0.60, KNOTS) == pytest.approx(0.43)
    assert calibrate_survival(0.50, KNOTS) == pytest.approx(0.32)          # halfway between 0.21 and 0.43
    assert calibrate_survival(0.0, KNOTS) == 0.0 and calibrate_survival(1.0, KNOTS) == 1.0
    assert calibrate_survival(0.98, KNOTS) == pytest.approx(0.88 + 0.12 * 0.5)
    assert calibrate_survival(0.7, []) == 0.7                              # empty = identity


def test_the_map_is_monotone_and_bounded():
    xs = [i / 100 for i in range(101)]
    ys = [calibrate_survival(x, KNOTS) for x in xs]
    assert all(0.0 <= y <= 1.0 for y in ys)
    assert all(b >= a - 1e-12 for a, b in zip(ys, ys[1:]))


def test_the_tracker_applies_it_to_shown_survival_and_keeps_raw():
    from test_slot_markets import BOARD, make_tracker
    t = make_tracker(BOARD, [], current_pick=21)
    t.apply_engine_cfg({"survival_calibration": [list(k) for k in KNOTS]})
    rep = t.urgency_report()
    seen = 0
    for _m, u in rep.items():
        if not isinstance(u, dict):
            continue
        for sid, s in (u.get("survival") or {}).items():
            raw = (u.get("survival_raw") or {}).get(sid)
            if raw is None:
                continue
            assert s == pytest.approx(calibrate_survival(raw, KNOTS))
            seen += 1
    assert seen > 0


def test_a_bad_knot_is_refused():
    t = object.__new__(Tracker)
    with pytest.raises(ValueError):
        t.apply_engine_cfg({"survival_calibration": [[0.4]]})
    with pytest.raises(ValueError):
        t.apply_engine_cfg({"survival_calibration": [[1.4, 0.2]]})
    t.apply_engine_cfg({})
    assert t.survival_calibration == []


def _rank(cands, urg, surv, rnd=3):
    market_of = {c[2]["sleeper_id"]: c[2]["pos"] for c in cands}
    return staged_rank(cands, _report(surv), NEEDS, rnd, urg, market_of,
                       {pos: 0.0 for pos in REPL}, lambda pos: {"QB", "RB", "WR", "TE"},
                       fallback=FALLBACK, repl=REPL)


def test_a_market_within_the_relative_band_is_live():
    """Room 10801633 pick 22: TE 21.6 vs WR 15.4 (within 30%), London 62.5 vs
    McBride 43.2 on value. The receiver must be compared, and wins."""
    te = _p("te", "TE", 175.7, lo=161.0, hi=190.0)     # value 75.7 over the TE fallback
    wr = _p("wr", "WR", 190.4, lo=180.0, hi=200.0)     # value 60.4
    te["proj_pts"] = 143.2                             # value 43.2, as in the room
    out = _rank([(21.6, "t", te), (15.4, "w", wr)], {"TE": 21.6, "WR": 15.4}, {"TE": {"te": 0.2}, "WR": {"wr": 0.01}})
    assert out[0][2]["sleeper_id"] == "wr"
    assert "urgency picked TE/WR" in out[0][1] and "value picked him (60.4 vs 43.2" in out[0][1]


def test_a_market_outside_both_bands_stays_dead():
    te = _p("te", "TE", 143.2)
    wr = _p("wr", "WR", 190.4)
    out = _rank([(30.0, "t", te), (15.0, "w", wr)], {"TE": 30.0, "WR": 15.0}, {})
    assert out[0][2]["sleeper_id"] == "te" and f"or {URGENCY_REL:.0%}" in out[1][1]


def test_a_flat_board_lets_the_pair_lead():
    """Room 10801633 pick 19: QB 6.5 was the top urgency in a two-pick window
    and decided the position. Under URGENCY_FLOOR the pair leads instead."""
    qb = _p("qb", "QB", 325.0)      # value 65 over the QB fallback
    wr = _p("wr", "WR", 200.0)      # value 70
    out = _rank([(6.5, "q", qb), (0.4, "w", wr)], {"QB": 6.5, "WR": 0.4}, {"QB": {"qb": 0.83}, "WR": {"wr": 0.81}})
    assert f"STAGED (flat: top urgency 6.5 under {URGENCY_FLOOR:g})" in out[0][1]
    assert all(p["_staged"]["mode"] == "flat" for _s, _w, p in out)

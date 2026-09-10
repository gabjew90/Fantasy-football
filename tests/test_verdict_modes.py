"""Step 5 of the slot-based trade plan: verdict(mode=) and Deal.acceptance.

Two questions verdict() can ask about HIS side. "points": his lineup delta
in MY projections must be >= 0 -- the original gate. "slots": accepts(),
in HIS currencies. The mechanism lands here with "points" still the
default, because the radar does not pass a rank panel yet; the flip is
step 7.
"""

from __future__ import annotations

import pytest

from manager import marginal

_n = [0]


def _deal(mine, theirs, out=None, inn=None, acceptance=None):
    mkt = None if out is None else {"out": out, "in": inn, "delta": inn - out,
                                    "pct": None, "unpriced": []}
    return marginal.Deal(100.0, 100.0 + mine, 100.0, 100.0 + theirs,
                         market=mkt, acceptance=acceptance)


YES = {"accept": True, "test1": True, "test2": True, "why": ["an upgrade"]}
NO_UPGRADE = {"accept": False, "test1": False, "test2": True, "why": ["he sits"]}
MARKET_DOWN = {"accept": False, "test1": True, "test2": False, "why": ["down 1,717"]}


def test_mode_ships_as_points_until_the_radar_supplies_a_panel():
    """A slots default today would reject every production package with
    "not computed" -- the radar passes no rank panel to price() yet."""
    assert marginal.MODE == "points"
    assert marginal.verdict(_deal(17.0, 5.0), weeks_left=17)["mode"] == "points"


def test_slots_mode_reads_acceptance_and_never_his_lineup_delta():
    """His lineup delta is MY model of his team, and he does not use it. A
    package he accepts on rank and market passes gate 1 even when my
    projections say he loses fifty."""
    v = marginal.verdict(_deal(17.0, -50.0, acceptance=YES), weeks_left=17, mode="slots")
    assert v["gate1"] is True and v["send"] is True
    p = marginal.verdict(_deal(17.0, -50.0, acceptance=YES), weeks_left=17, mode="points")
    assert p["gate1"] is False


def test_slots_mode_with_no_acceptance_refuses_to_guess():
    v = marginal.verdict(_deal(17.0, 5.0), weeks_left=17, mode="slots")
    assert v["gate1"] is False and v["send"] is False
    assert any("not computed" in w for w in v["why"]), v["why"]


def test_slots_mode_rejection_names_the_test_that_failed():
    a = marginal.verdict(_deal(17.0, 5.0, acceptance=NO_UPGRADE), weeks_left=17, mode="slots")
    assert any("no positional upgrade" in w for w in a["why"]), a["why"]
    b = marginal.verdict(_deal(17.0, 5.0, acceptance=MARKET_DOWN), weeks_left=17, mode="slots")
    assert any("market drops" in w for w in b["why"]), b["why"]


def test_points_mode_is_the_gate_that_shipped():
    assert marginal.verdict(_deal(17.0, 5.0), weeks_left=17, mode="points")["gate1"] is True
    v = marginal.verdict(_deal(17.0, -1.0), weeks_left=17, mode="points")
    assert v["gate1"] is False
    assert any("them" in w for w in v["why"]), v["why"]


def test_my_side_still_has_to_gain_in_slots_mode():
    v = marginal.verdict(_deal(-1.0, 5.0, acceptance=YES), weeks_left=17, mode="slots")
    assert v["gate1"] is False
    assert any(w.startswith("lineup: me") for w in v["why"]), v["why"]


def test_the_market_floor_is_advisory_in_slots_mode_and_blocks_in_points():
    """The floor asked "will he refuse". In slots mode accepts() Test 2 --
    his starters' market must not drop -- answers that, so the band is
    information. In points mode it still blocks."""
    low = _deal(17.0, 5.0, out=5000, inn=10000, acceptance=YES)
    s = marginal.verdict(low, weeks_left=17, mode="slots")
    assert s["gate2"] is True and s["send"] is True
    assert any("expect a rejection" in w for w in s["warnings"]), s
    p = marginal.verdict(low, weeks_left=17, mode="points")
    assert p["gate2"] is False and p["send"] is False
    assert any("expect a rejection" in w for w in p["why"]), p


def test_an_unknown_mode_is_an_error_not_a_default():
    with pytest.raises(ValueError, match="mode"):
        marginal.verdict(_deal(17.0, 5.0), weeks_left=17, mode="vibes")


def test_verdict_carries_mode_and_acceptance_in_its_return():
    v = marginal.verdict(_deal(17.0, 5.0, acceptance=YES), weeks_left=17, mode="slots")
    assert v["mode"] == "slots" and v["acceptance"] is YES


# ------------------------------------------------------- price(ranks=)

def _r(pos, pts, name, ov):
    _n[0] += 1
    return {"sleeper_id": f"vm{_n[0]}", "pos": pos, "weekly": pts, "name": name, "_ov": ov}


SHAPE = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 1}


def _fixture():
    theirs = [_r("QB", 30, "qb", 50), _r("RB", 20, "rb1", 20), _r("RB", 10, "rb2", 120),
              _r("WR", 22, "wr1", 15), _r("WR", 21, "wr2", 25), _r("WR", 19, "wr3", 40),
              _r("TE", 12, "te", 80)]
    mine = [_r("QB", 28, "myqb", 60), _r("RB", 18, "javonte", 43), _r("RB", 17, "myrb2", 70),
            _r("WR", 20, "mywr1", 30), _r("WR", 15, "mywr2", 90), _r("TE", 11, "myte", 100)]
    ranks = {p["sleeper_id"]: {"overall": p["_ov"], "positional": None, "pos": p["pos"],
                               "panel": 100, "source": "t", "list": "ALL"}
             for p in mine + theirs}
    market = {p["sleeper_id"]: 1000 for p in mine + theirs}
    return mine, theirs, ranks, market


def test_price_attaches_acceptance_when_given_a_rank_panel():
    """Javonte (RB, overall 43) starts for them over rb2 (overall 120):
    UPGRADE. Flat market and the same number of starters: Test 2 passes."""
    mine, theirs, ranks, market = _fixture()
    javonte, wr3 = mine[1], theirs[5]
    d = marginal.price(mine, theirs, [javonte], [wr3], SHAPE,
                       market_values=market, ranks=ranks)
    assert d.acceptance is not None
    assert d.acceptance["accept"] is True
    assert d.acceptance["tags"][javonte["sleeper_id"]] == marginal.UPGRADE
    v = marginal.verdict(d, weeks_left=17, mode="slots")
    assert v["gate1"] is True


def test_price_without_a_rank_panel_leaves_acceptance_none():
    mine, theirs, ranks, market = _fixture()
    d = marginal.price(mine, theirs, [mine[1]], [theirs[5]], SHAPE, market_values=market)
    assert d.acceptance is None
    assert marginal.verdict(d, weeks_left=17, mode="slots")["gate1"] is False

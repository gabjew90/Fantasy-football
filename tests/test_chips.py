"""Step 6 of the slot-based trade plan: chips.

A chip is a player who is CHEAP FOR ME TO SELL and HAS A BUYER -- both.
`true_cost` is the lineup drop after the position-aware backfill a 2-for-1
actually earns; `rank_buyers` are the teams for whom he is a positional
upgrade in THEIR currency (he starts for them and beats their worst
incumbent at his position on overall rank). Opt-in through ranks=; the
surplus ranking is unchanged without it.
"""

from __future__ import annotations

from manager import marginal

_n = [0]


def _r(pos, pts, name, ov=None):
    _n[0] += 1
    return {"sleeper_id": f"ch{_n[0]}", "pos": pos, "weekly": pts, "name": name, "_ov": ov}


def _ranks(*rosters):
    return {p["sleeper_id"]: {"overall": p["_ov"], "positional": None, "pos": p["pos"],
                              "panel": 100, "source": "t", "list": "ALL"}
            for r in rosters for p in r if p.get("_ov") is not None}


SHAPE = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 1}


def _fillers(tag, ov=50):
    """RB/RB/WR/WR/TE + a flex WR so every roster fills its seats."""
    return [_r("RB", 15, f"{tag}rb1", ov), _r("RB", 13, f"{tag}rb2", ov),
            _r("WR", 14, f"{tag}wr1", ov), _r("WR", 12, f"{tag}wr2", ov),
            _r("TE", 9, f"{tag}te", ov), _r("WR", 11, f"{tag}flex", ov)]


def _by_name(rows):
    return {r["player"]["name"]: r for r in rows}


def test_true_cost_is_the_drop_after_the_position_aware_backfill():
    """Caleb on cost_to_lose is his whole 29.4: the seat is empty. With a
    27.5 QB on the wire the seat is refilled and he costs 1.9."""
    caleb = _r("QB", 29.4, "caleb", 65)
    mine = [caleb] + _fillers("m")
    love = _r("QB", 27.5, "love", 70)
    with_wire = _by_name(marginal.tradeable(mine, {}, SHAPE, waivers=[love]))
    assert with_wire["caleb"]["cost"] == 29.4
    assert with_wire["caleb"]["true_cost"] == 1.9
    plain = _by_name(marginal.tradeable(mine, {}, SHAPE))
    assert plain["caleb"]["true_cost"] == plain["caleb"]["cost"] == 29.4


def test_a_buyer_is_found_in_the_buyers_currency_not_mine():
    """Three rivals. A starts a QB worse on points AND ranked below Caleb:
    a buyer in both currencies. B starts a QB worse on points but ranked
    ABOVE him: points says buyer, the board says filler. C starts a better
    QB: Caleb sits, nobody's buyer."""
    caleb = _r("QB", 29.4, "caleb", 65)
    mine = [caleb] + _fillers("m")
    a = [_r("QB", 28.0, "a_qb", 90)] + _fillers("a")
    b = [_r("QB", 28.0, "b_qb", 40)] + _fillers("b")
    c = [_r("QB", 31.0, "c_qb", 90)] + _fillers("c")
    ranks = _ranks(mine, a, b, c)
    rows = _by_name(marginal.tradeable(mine, {"A": a, "B": b, "C": c}, SHAPE, ranks=ranks))
    assert rows["caleb"]["buyers"] == 2, rows["caleb"]
    assert rows["caleb"]["rank_buyers"] == ["A"], rows["caleb"]


def test_chips_rank_cheap_with_a_buyer_first_and_unbought_last():
    """x: cheap once a wire QB backfills, and a rival would start him as an
    upgrade. y: a starting RB, expensive to lose, also wanted. z: a free
    bench RB nobody would start. Order: x, y, ... z last."""
    x = _r("QB", 29.4, "x", 65)
    y = _r("RB", 20.0, "y", 10)
    z = _r("RB", 5.0, "z", 250)
    mine = [x, y, z] + _fillers("m")
    rival = [_r("QB", 28.0, "r_qb", 90), _r("RB", 12.0, "r_rb1", 100),
             _r("RB", 11.0, "r_rb2", 110)] + _fillers("r")[2:]
    wire = [_r("QB", 27.5, "love", 70)]
    ranks = _ranks(mine, rival)
    rows = marginal.tradeable(mine, {"R": rival}, SHAPE, waivers=wire, ranks=ranks)
    order = [r["player"]["name"] for r in rows]
    by = _by_name(rows)
    assert by["x"]["rank_buyers"] == ["R"] and by["y"]["rank_buyers"] == ["R"]
    assert by["z"]["rank_buyers"] == []
    assert order.index("x") < order.index("y") < order.index("z"), order
    assert order[-1] == "z" or by[order[-1]]["rank_buyers"] == [], order


def test_without_a_rank_panel_the_surplus_ranking_is_unchanged():
    """The original contract: free-and-wanted first, unwanted last, and no
    rank_buyers at all."""
    star = _r("RB", 20.0, "star")
    spare = _r("RB", 12.0, "spare")
    mine = [star, spare]
    shape = {"slots": {"RB": 1}, "flex": 0}
    rows = marginal.tradeable(mine, {"rival": [_r("RB", 1.0, "r1")]}, shape)
    assert rows[0]["player"]["name"] == "spare"
    assert all(r["rank_buyers"] is None for r in rows)
    assert all(r["true_cost"] == r["cost"] for r in rows)


def test_a_kicker_or_defence_is_never_a_chip():
    """Live on 2026-09-10 the chip list opened with the Vikings DEF at a cost
    of -11.0 -- departing him admitted a better wire DEF to the backfill --
    and the kicker second. Streamed positions are not chips, whatever the
    wire says about them."""
    dst = _r("DEF", 100.0, "my def", 120)
    k = _r("K", 130.0, "my k", 110)
    mine = [dst, k] + _fillers("m")
    shape = dict(SHAPE, slots=dict(SHAPE["slots"], DEF=1, K=1))
    wire = [_r("DEF", 130.0, "better def", 90), _r("K", 140.0, "better k", 80)]
    rival = [_r("DEF", 50.0, "r_def", 200), _r("K", 60.0, "r_k", 200)] + _fillers("r")
    ranks = _ranks(mine, rival, wire)
    rows = marginal.tradeable(mine, {"R": rival}, shape, waivers=wire, ranks=ranks)
    names = [r["player"]["name"] for r in rows]
    assert "my def" not in names and "my k" not in names, names
    assert all(r["player"]["pos"] not in ("K", "DEF") for r in rows)

"""Step 4 of the slot-based trade plan: does it look like a win to HIM.

Two tests, both must pass. He is modelled on perception -- the rank panel
and the trade market -- over the players that land in a slot he uses.
Points never enter it. Fixtures are the measured 2026-09-09 shapes with the
numbers rounded; assertions are on the quantities verified by hand.
"""

from __future__ import annotations

from manager import marginal

_n = [0]


def _a(pos, pts, name, ov=None, mkt=0):
    _n[0] += 1
    return {"sleeper_id": f"acc{_n[0]}", "pos": pos, "weekly": pts, "name": name,
            "_ov": ov, "_mkt": mkt}


def _tables(*rosters):
    ranks = {p["sleeper_id"]: {"overall": p["_ov"], "positional": None, "pos": p["pos"],
                               "panel": 100, "source": "t", "list": "ALL"}
             for r in rosters for p in r if p.get("_ov") is not None}
    market = {p["sleeper_id"]: p["_mkt"] for r in rosters for p in r}
    return ranks, market


ONE_FLEX = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 1}
TWO_FLEX = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 2}


def _cbarone():
    """Starters under ONE_FLEX: hurts, hampton, warren, stbrown, smith,
    goedert, mcmillan (flex). Market 27,800. Bench: moore, meyers, goff."""
    return [_a("QB", 31, "hurts", 57, 2700), _a("RB", 24, "hampton", 25, 6700),
            _a("RB", 17, "warren", 74, 2000), _a("WR", 30, "stbrown", 5, 8200),
            _a("WR", 23, "smith", 23, 4100), _a("WR", 22, "mcmillan", 36, 3400),
            _a("WR", 19, "moore", 52, 2500), _a("TE", 16, "goedert", 119, 700),
            _a("WR", 17, "meyers", 108, 400), _a("QB", 28, "goff", 90, 2000)]


def _ayat():
    """Starters under TWO_FLEX: allen, hubbard, monangai, chase, nabers,
    pitts, flowers + wilson (flex). Market 34,873. Bench: tyson."""
    return [_a("QB", 36, "allen", 10, 9000), _a("RB", 14, "hubbard", 100, 900),
            _a("RB", 14, "monangai", 120, 885), _a("WR", 32, "chase", 3, 9600),
            _a("WR", 23, "nabers", 20, 5100), _a("WR", 23, "flowers", 30, 4114),
            _a("WR", 23, "wilson", 30, 3774), _a("TE", 19, "pitts", 60, 1500),
            _a("WR", 12, "tyson", 200, 540)]


def _find(roster, name):
    return next(p for p in roster if p["name"] == name)


# ------------------------------------------------------------- the St. Brown deal

def test_st_brown_deal_test1_passes_on_henry_and_test2_fails_on_market():
    his = _cbarone()
    henry = _a("RB", 24, "henry", 38, 6528)
    caleb = _a("QB", 29, "caleb", 65, 2662)
    ranks, market = _tables(his, [henry, caleb])
    out = marginal.accepts(his, ONE_FLEX, arriving=[henry, caleb],
                           departing=[_find(his, "stbrown")], ranks=ranks, market=market)
    assert out["tags"][henry["sleeper_id"]] == marginal.UPGRADE   # 38 beats Warren at 74
    assert out["tags"][caleb["sleeper_id"]] == marginal.SITS      # Hurts 31 > Caleb 29
    assert out["test1"] is True
    assert out["starters_market_before"] == 27800
    # St. Brown 8200 out, Henry 6528 in, Moore 2500 into the flex, McMillan slides to WR2
    assert out["starters_market_after"] == 26628
    assert out["test2"] is False
    assert out["accept"] is False
    assert out["net_rank"] == -11.0                                # 339 -> 350 on overall rank


def test_test2_never_counts_a_player_who_does_not_start():
    """Caleb at 2,662 or at 0 must give the same starters-market: he sits."""
    outs = []
    for caleb_mkt in (2662, 0):
        his = _cbarone()
        henry = _a("RB", 24, "henry", 38, 6528)
        caleb = _a("QB", 29, "caleb", 65, caleb_mkt)
        ranks, market = _tables(his, [henry, caleb])
        outs.append(marginal.accepts(his, ONE_FLEX, arriving=[henry, caleb],
                                     departing=[_find(his, "stbrown")],
                                     ranks=ranks, market=market)["starters_market_after"])
    assert outs[0] == outs[1] == 26628


# -------------------------------------------------------- the Javonte deals

def test_javonte_for_wilson_straight_is_accepted():
    """Javonte (RB, overall 43) beats their worst starting RB (Monangai,
    120): UPGRADE. Their starters' market rises 1,086. Both tests pass, no
    sweetener needed. The net-rank flag is -13: a rankings-reader would
    refuse, which is reported and not gated."""
    his = _ayat()
    javonte = _a("RB", 22, "javonte", 43, 4860)
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["tags"][javonte["sleeper_id"]] == marginal.UPGRADE
    assert out["starters_market_before"] == 34873
    assert out["starters_market_after"] == 35959
    assert out["test1"] is True and out["test2"] is True and out["accept"] is True
    assert out["net_rank"] == -13.0
    assert any("rankings-reader" in w for w in out["why"])


def test_deebo_starts_but_is_tagged_filler_and_the_deal_passes_on_javonte():
    """Deebo (WR, overall 141) fills flex 2 over Monangai (14 points) and is
    worse than every WR they had (worst starter overall 30): FILLER. The
    package is accepted on Javonte alone."""
    his = _ayat()
    javonte = _a("RB", 22, "javonte", 43, 4860)
    deebo = _a("WR", 15, "deebo", 141, 782)
    ranks, market = _tables(his, [javonte, deebo])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte, deebo],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["tags"][deebo["sleeper_id"]] == marginal.FILLER
    assert out["tags"][javonte["sleeper_id"]] == marginal.UPGRADE
    assert out["test1"] is True and out["test2"] is True and out["accept"] is True


# ----------------------------------------------------------------- rejections

def test_a_package_where_nobody_i_send_starts_fails_test1_whatever_the_market():
    his = _cbarone()
    caleb = _a("QB", 29, "caleb", 65, 2662)
    ranks, market = _tables(his, [caleb])
    out = marginal.accepts(his, ONE_FLEX, arriving=[caleb],
                           departing=[_find(his, "meyers")], ranks=ranks, market=market)
    assert out["tags"][caleb["sleeper_id"]] == marginal.SITS
    assert out["test1"] is False and out["accept"] is False


def test_an_unranked_player_who_starts_is_filler_not_an_upgrade():
    """No panel row means UNRANKED (300): he cannot beat any incumbent, so a
    rank the panel never published is never read as an upgrade."""
    his = _cbarone()
    mystery = _a("RB", 24, "mystery", None, 6528)
    ranks, market = _tables(his, [mystery])
    assert mystery["sleeper_id"] not in ranks
    out = marginal.accepts(his, ONE_FLEX, arriving=[mystery],
                           departing=[_find(his, "stbrown")], ranks=ranks, market=market)
    assert out["tags"][mystery["sleeper_id"]] == marginal.FILLER
    assert out["test1"] is False


def test_a_player_with_no_market_value_counts_as_zero():
    his = _cbarone()
    henry = _a("RB", 24, "henry", 38, 6528)
    ranks, market = _tables(his, [henry])
    market.pop(henry["sleeper_id"])
    out = marginal.accepts(his, ONE_FLEX, arriving=[henry],
                           departing=[_find(his, "stbrown")], ranks=ranks, market=market)
    assert out["starters_market_after"] == 26628 - 6528


def test_the_panel_size_is_the_smallest_among_players_touched():
    his = _ayat()
    javonte = _a("RB", 22, "javonte", 43, 4860)
    ranks, market = _tables(his, [javonte])
    ranks[javonte["sleeper_id"]]["panel"] = 3
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["panel"] == 3


def test_accept_is_both_tests_and_classes_are_carried():
    his = _ayat()
    javonte = _a("RB", 22, "javonte", 43, 4860)
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["accept"] == (out["test1"] and out["test2"])
    assert out["classes"]["received"][javonte["sleeper_id"]] == marginal.STARTS
    assert out["classes"]["given"][_find(his, "wilson")["sleeper_id"]] == marginal.STARTED


# ------------------------------------------- the floor when the panel is silent

def test_an_unranked_incumbent_is_left_out_of_the_floor_not_counted_as_300():
    """Review 2026-09-10: on the mirror fallback a name collision can drop a
    starter from the panel. UNRANKED is 300, and max() over the incumbents
    would have made any ranked body I send an upgrade over a WR1. Monangai
    unranked: Javonte is still judged against Hubbard (100) and is an
    UPGRADE. Both RBs unranked: the seat cannot be judged, FILLER, said so."""
    his = _ayat()
    _find(his, "monangai")["_ov"] = None
    javonte = _a("RB", 22, "javonte", 43, 4860)
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["tags"][javonte["sleeper_id"]] == marginal.UPGRADE
    assert any("overall 100" in w for w in out["why"]), out["why"]

    his = _ayat()
    _find(his, "monangai")["_ov"] = None
    _find(his, "hubbard")["_ov"] = None
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["tags"][javonte["sleeper_id"]] == marginal.FILLER
    assert out["test1"] is False and out["accept"] is False
    assert any("not on the panel" in w for w in out["why"]), out["why"]


def test_filling_an_empty_seat_is_still_an_upgrade():
    """No TE on his roster at all: a ranked TE I send fills the seat, and
    that IS an upgrade -- there is no incumbent to be unranked."""
    his = [p for p in _cbarone() if p["pos"] != "TE"]
    te = _a("TE", 12, "kmet", 150, 600)
    ranks, market = _tables(his, [te])
    out = marginal.accepts(his, ONE_FLEX, arriving=[te],
                           departing=[_find(his, "meyers")], ranks=ranks, market=market)
    assert out["tags"][te["sleeper_id"]] == marginal.UPGRADE


def test_a_fractional_net_rank_under_half_a_point_is_not_flagged():
    """Mirror ranks are fractional. -0.3 printed as "worse by 0 rank-points"."""
    his = _ayat()
    _find(his, "wilson")["_ov"] = 30.3
    javonte = _a("RB", 22, "javonte", 43, 4860)
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["net_rank"] == -12.7
    assert any("rankings-reader" in w for w in out["why"])
    his = _ayat()
    _find(his, "wilson")["_ov"] = 42.7          # javonte 43 in for 42.7: net -0.3
    ranks, market = _tables(his, [javonte])
    out = marginal.accepts(his, TWO_FLEX, arriving=[javonte],
                           departing=[_find(his, "wilson")], ranks=ranks, market=market)
    assert out["net_rank"] == -0.3
    assert not any("rankings-reader" in w for w in out["why"]), out["why"]

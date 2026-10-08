"""FantasyCalc as a standing second opinion, on the league's own format.

The format is a LEAGUE FACT. Hardcoding it shipped once already: Keefamania
is 10-team half-PPR and was priced on Omnibeta's 12-team full-PPR market with
no error raised anywhere. These tests pin the derivation, not the numbers --
the numbers come off a live API.
"""

from __future__ import annotations

from manager import marginal, market


class Cfg(dict):
    def __init__(self, *a, league_name=None, **kw):
        super().__init__(*a, **kw)
        self.league_name = league_name


class FakeStore:
    def __init__(self):
        self.d = {}

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


KEEFA = Cfg({"expected": {"teams": 10, "scoring": {"rec": 0.5},
                          "roster": ["QB", "WR", "WR", "RB", "RB", "TE",
                                     "W/R/T", "K", "DEF"]}}, league_name="keefamania")
OMNI = Cfg({"expected": {"teams": 12, "scoring": {"rec": 1.0},
                         "roster": ["QB", "RB", "RB", "WR", "WR", "TE",
                                    "FLEX", "FLEX", "K", "DEF"]}}, league_name="omnibeta")


# ------------------------------------------------------------ league_format

def test_each_league_is_priced_on_its_own_market():
    assert market.league_format({"cfg": KEEFA}) == (10, 0.5, 1, False)
    assert market.league_format({"cfg": OMNI}) == (12, 1.0, 1, False)


def test_live_roster_count_beats_the_yaml():
    """A league that added a team mid-season is 13 teams, whatever yaml says."""
    fmt = market.league_format({"cfg": OMNI, "rosters": [{}] * 13})
    assert fmt.teams == 13


def test_superflex_is_detected_from_the_roster_tokens():
    """numQbs is the parameter that matters most -- 1 -> 2 moves values ~59%
    on average -- and a yaml-only context has no live slot map to read."""
    for token in ("SUPER_FLEX", "SUPERFLEX", "Q/W/R/T", "OP"):
        cfg = Cfg({"expected": {"teams": 12, "scoring": {"rec": 1.0},
                                "roster": ["QB", "RB", "WR", token]}})
        assert market.league_format({"cfg": cfg}).qbs == 2, token


def test_superflex_is_detected_from_a_live_slot_map():
    fmt = market.league_format({"cfg": OMNI, "slots": {"QB": 1, "SUPER_FLEX": 1}})
    assert fmt.qbs == 2


def test_a_one_qb_league_is_not_mistaken_for_superflex():
    assert market.league_format({"cfg": OMNI, "slots": {"QB": 1, "FLEX": 2}}).qbs == 1


def test_the_query_and_label_say_what_was_asked_for():
    fmt = market.league_format({"cfg": KEEFA})
    assert fmt.params() == {"isDynasty": "false", "numQbs": 1,
                            "numTeams": 10, "ppr": 0.5}
    assert "10-team" in fmt.label() and "0.5 PPR" in fmt.label() and "1QB" in fmt.label()


def test_the_cache_key_separates_formats():
    """Two leagues sharing one cache entry is the original defect wearing a
    different hat."""
    store = FakeStore()
    market.fetch(store, {"cfg": KEEFA})
    market.fetch(store, {"cfg": OMNI})
    assert len({k for k in store.d if k.startswith("fantasycalc:")}) == 2


# -------------------------------------------------------------------- price

VALS = {"a": 6565, "b": 1598, "c": 648, "x": 7119, "y": 1095, "z": 1860}


def _p(pid, name):
    return {"sleeper_id": pid, "name": name, "pos": "RB", "weekly": 100.0}


def test_price_totals_both_sides():
    pkg = market.price(VALS, [_p("a", "Henry")], [_p("x", "Saquon")])
    assert (pkg["out"], pkg["in"], pkg["delta"]) == (6565, 7119, 554)
    assert pkg["pct"] == 8.4


def test_an_unpriced_player_is_named_not_scored_zero():
    """Only the top ~199 have rows. Counting a deep-wire piece as 0 would make
    every wire-involving deal look like a steal."""
    pkg = market.price(VALS, [_p("a", "Henry"), _p("nope", "Deep Wire Guy")],
                       [_p("x", "Saquon")])
    assert pkg["out"] == 6565, "the missing player must not contribute 0 silently"
    assert pkg["unpriced"] == ["Deep Wire Guy"]
    assert "unpriced: Deep Wire Guy" in market.annotate(pkg)


def test_annotate_is_silent_with_nothing_to_say():
    assert market.annotate(None) == ""
    assert market.annotate({"out": 0, "in": 0, "delta": 0, "pct": None,
                            "unpriced": []}) == ""


# --------------------------------------------------- wired into Deal pricing

SHAPE = {"slots": {"RB": 1}, "flex": 1}


def test_a_deal_carries_the_market_without_blending_it():
    mine = [_p("a", "Henry"), _p("c", "Spare")]
    theirs = [_p("x", "Saquon"), _p("y", "Pierce")]
    d = marginal.price(mine, theirs, [mine[0]], [theirs[0]], SHAPE,
                       market_values=VALS)
    assert d.market_delta == 554
    assert d.my_delta == 0.0, "lineup points are untouched by the market number"


def test_no_market_values_means_no_market_fields():
    mine, theirs = [_p("a", "Henry")], [_p("x", "Saquon")]
    d = marginal.price(mine, theirs, [mine[0]], [theirs[0]], SHAPE)
    assert d.market is None and d.market_delta is None and d.disputed is False


def test_disagreement_between_the_two_instruments_is_flagged():
    """The 2026-09-08 Barkley package: lineup points said -10.0, the market
    said +1263. Averaging them would have hidden exactly the thing worth
    knowing, so Deal carries both and says they disagree."""
    mine = [_p("a", "Henry"), _p("b", "Fannin")]
    theirs = [_p("x", "Saquon"), _p("z", "Kraft")]
    mine[0]["weekly"] = 300.0          # my side loses lineup points...
    theirs[0]["weekly"] = 200.0
    d = marginal.price(mine, theirs, [mine[0]], [theirs[0]], SHAPE,
                       market_values=VALS)
    assert d.my_delta < 0 and d.market_delta > 0   # ...while the market gains
    assert d.disputed is True
    assert "disagree" in str(d)


def test_agreement_is_not_flagged():
    mine = [_p("a", "Henry")]
    theirs = [_p("x", "Saquon")]
    mine[0]["weekly"] = 100.0
    theirs[0]["weekly"] = 200.0
    d = marginal.price(mine, theirs, [mine[0]], [theirs[0]], SHAPE,
                       market_values=VALS)
    assert d.my_delta > 0 and d.market_delta > 0 and d.disputed is False

"""The radar prices its own suggestions instead of just naming them.

Until 2026-09-08 trade_radar said who to text and about what, and stopped
there -- the brief never said what the package would do to either lineup,
which is the only thing that decides whether to send it. manager/marginal
existed for exactly that and had no callers outside tests.
"""

from __future__ import annotations

from manager import trade_radar


def p(pid, pos, ros, name=None):
    return {"sleeper_id": pid, "pos": pos, "ros": ros, "weekly": 0.0,
            "name": name or pid, "team": "SF"}


MINE = [p("mqb", "QB", 285), p("mrb1", "RB", 331), p("mrb2", "RB", 228),
        p("mwr1", "WR", 207), p("mte1", "TE", 196), p("mte2", "TE", 182),
        p("mwr2", "WR", 168)]
# four receivers for two WR slots, a bench back stuck behind them, and the
# worst startable TE in the league -- the vincenzo31 shape
THEIRS = [p("tqb", "QB", 291), p("trb1", "RB", 287), p("trb2", "RB", 249),
          p("twr1", "WR", 239), p("twr2", "WR", 207), p("twr3", "WR", 206),
          p("twr4", "WR", 184), p("tte1", "TE", 143), p("tbench", "RB", 170)]


def _ctx():
    return {"my_rid": 1, "roster_players": {1: MINE, 2: THEIRS},
            "slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 2,
            "flex_slots": None, "users_by_rid": {1: "me", 2: "them"}}


def _opp(**kw):
    base = {"mgr": "them", "rid": 2,
            "give_p": [MINE[2], MINE[5]], "get_p": [THEIRS[3], THEIRS[6]]}
    base.update(kw)
    return base


def test_the_brief_states_what_the_package_does_to_both_lineups():
    out = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "lineup effect" in out
    assert "me +" in out and "them " in out


def test_a_bench_promotion_is_named_in_the_brief():
    """The whole reason the framework re-solves: their tight end loses the
    spot and a back nobody traded comes up off the bench."""
    out = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "loses the spot" in out
    assert "comes off the bench" in out


def test_it_prices_on_rest_of_season_not_this_week():
    """An in-season brief is about the points still to play for."""
    ctx = _ctx()
    out = "\n".join(trade_radar._priced(ctx, _opp(), {}))
    assert "rest-of-season" in out
    # every row carries weekly 0.0, so a weekly-keyed price would be all zeros
    assert "me +0.0" not in out


def test_the_market_line_appears_only_with_values():
    vals = {"mrb2": 4890, "mte2": 1598, "twr1": 4746, "twr4": 1569}
    with_market = "\n".join(trade_radar._priced(_ctx(), _opp(), vals))
    without = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "market" in with_market and "market" not in without


def test_a_desperation_row_with_no_concrete_ask_still_prices_the_offer():
    out = trade_radar._priced(_ctx(), _opp(get_p=[]), {})
    assert out and "lineup effect" in out[0]


def test_a_missing_roster_degrades_to_silence_not_a_traceback():
    """A brief that dies in an email is worse than one missing a line."""
    assert trade_radar._priced(_ctx(), _opp(rid=999), {}) == []
    assert trade_radar._priced(_ctx(), {"mgr": "x"}, {}) == []


def test_a_pricing_failure_is_logged_and_swallowed(monkeypatch, caplog):
    import logging
    from manager import marginal

    def boom(*a, **kw):
        raise RuntimeError("solver exploded")

    monkeypatch.setattr(marginal, "price", boom)
    with caplog.at_level(logging.WARNING, logger="manager"):
        assert trade_radar._priced(_ctx(), _opp(), {}) == []
    assert "could not price" in caplog.text, "swallowed silently, not logged"


def test_an_unidentified_row_does_not_break_the_lineup_solve():
    """optimal_lineup's new duplicate guard must not read sleeper_id off rows
    the old code never touched -- one without an id that never starts was
    fine at flex=0 and has to stay fine."""
    from draftkit.lineup import optimal_lineup
    roster = [{"pos": "RB", "weekly": 100, "sleeper_id": "a"},
              {"pos": "RB", "weekly": 1}]
    assert [x.get("sleeper_id") for x in optimal_lineup(roster, {"RB": 1}, 0)] == ["a"]

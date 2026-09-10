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
            "flex_slots": None, "users_by_rid": {1: "me", 2: "them"},
            "weeks_left": 17}


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
    # match the annotation itself, not the word: the points line now carries a
    # "not the market values quoted above" disclaimer that mentions it too
    assert "out /" in with_market and "in (" in with_market
    assert "out /" not in without


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


# ------------------------------------------- the gates reach the brief itself

def test_the_brief_states_a_verdict_not_just_a_number():
    """The gate stack existed for a day with no production caller: _priced
    passed no waivers and never called verdict(), so a brief could recommend
    a package that overpaid 559% on market with nothing to say so."""
    out = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "SEND" in out or "hold" in out
    assert "/wk)" in out, "the per-week figure is what a threshold is set against"


def test_a_blocking_reason_is_marked_and_a_warning_is_not():
    ctx = _ctx()
    # market far below the floor -> gate 2 blocks
    vals = {"mrb2": 100, "mte2": 100, "twr1": 9000, "twr4": 9000}
    blocked = "\n".join(trade_radar._priced(ctx, _opp(), vals))
    assert "hold" in blocked and "⚠" in blocked
    assert "expect a rejection" in blocked


def test_the_waiver_pool_is_built_once_and_cached_on_the_context():
    ctx = _ctx()
    assert "_wv_pool" not in ctx
    trade_radar._priced(ctx, _opp(), {})
    assert "_wv_pool" in ctx, "300 rows rebuilt per opportunity is waste"
    ctx["_wv_pool"] = [{"sleeper_id": "sentinel", "pos": "RB", "ros": 1.0,
                        "weekly": 0.0, "name": "sentinel"}]
    trade_radar._priced(ctx, _opp(), {})
    assert ctx["_wv_pool"][0]["sleeper_id"] == "sentinel", "cache was rebuilt"


def test_a_context_with_no_player_index_degrades_to_an_empty_pool():
    """The test ctx has no `players`/`trow`, which is what a half-built
    context looks like. It must not take the brief down."""
    ctx = _ctx()
    assert trade_radar._waiver_pool(ctx) == []
    assert trade_radar._priced(ctx, _opp(), {}), "still prices without a wire"


def test_radar_hands_verdict_the_consensus_row_for_the_biggest_piece():
    """`confident` was None on every package the radar had ever priced.

    verdict() has taken a `con` row since the gate shipped, and the only
    production caller never passed one, so the noise test was dead code in
    the field while its unit tests passed. Assert the wiring, not just the
    helper: a big edge on a player the sources argue about must come back
    with the warning attached.
    """
    from manager import marginal, trade_radar as tr

    noisy = {"n": 2, "mean": 255.8, "spread": 60.0}
    give = [{"sleeper_id": "1", "pos": "RB", "name": "Big", "ros": 255.8,
             "consensus": noisy},
            {"sleeper_id": "2", "pos": "TE", "name": "Small", "ros": 180.9,
             "consensus": {"n": 2, "mean": 180.9, "spread": 1.0}}]
    get = [{"sleeper_id": "3", "pos": "WR", "name": "In", "ros": 229.4,
            "consensus": {"n": 2, "mean": 229.4, "spread": 0.5}}]

    assert tr._biggest_row(give, get) is noisy
    assert tr._biggest_row([], []) is None
    # a row that apply() never rescaled carries no consensus key
    assert tr._biggest_row([{"sleeper_id": "9", "ros": 400.0}], []) is None

    deal = marginal.Deal(100.0, 116.5, 100.0, 102.7,
                         give=["Big"], get=["In"])
    v = marginal.verdict(deal, 17, con=tr._biggest_row(give, get))
    assert v["confident"] is False
    assert any("disagreement" in w for w in v["warnings"])



# ---------------------------- step 7 (2026-09-10): slots mode in the brief

def _panel():
    """Overall ranks for the fixture. mrb2 (RB, 30) beats their worst
    starting RB (trb2, 40); mte2 (TE, 80) beats tte1 (120). Both UPGRADE."""
    ov = {"mqb": 50, "mrb1": 5, "mrb2": 30, "mwr1": 33, "mte1": 45, "mte2": 80, "mwr2": 70,
          "tqb": 50, "trb1": 20, "trb2": 40, "twr1": 10, "twr2": 35, "twr3": 36, "twr4": 60,
          "tte1": 120, "tbench": 150}
    return {k: {"overall": v, "positional": None, "pos": None, "panel": 181,
                "source": "t", "list": "ALL"} for k, v in ov.items()}


def test_with_a_rank_panel_the_brief_judges_his_side_and_says_offer():
    """OFFER, not SEND: his side is a prediction that a position-by-position
    manager plausibly says yes, and my side is a mean with a range."""
    ctx = _ctx()
    ctx["_rank_panel"] = _panel()
    out = "\n".join(trade_radar._priced(ctx, _opp(), {}))
    assert "OFFER" in out and "SEND" not in out
    assert "his side: accepts" in out
    assert "UPGRADE" in out


def test_without_a_rank_panel_the_brief_holds_and_says_why():
    """Never a silent fall back to the points gate."""
    out = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "hold" in out
    assert "not computed" in out
    assert "his side: not judged" in out


def test_the_range_across_sources_is_printed_beside_the_mean():
    ctx = _ctx()
    ctx["_rank_panel"] = _panel()
    give0 = dict(MINE[2], consensus={"per_source": {"a": 228.0, "b": 200.0}})
    ctx["roster_players"][1] = [give0 if x is MINE[2] else x for x in MINE]
    out = "\n".join(trade_radar._priced(ctx, _opp(give_p=[give0, MINE[5]]), {}))
    assert "range " in out and " to " in out and "/wk" in out
    assert "n/a" not in out
    plain = "\n".join(trade_radar._priced(_ctx(), _opp(), {}))
    assert "range n/a" in plain


def test_the_rank_panel_is_fetched_once_and_cached_on_the_context():
    ctx = _ctx()
    assert "_rank_panel" not in ctx
    trade_radar._priced(ctx, _opp(), {})
    assert "_rank_panel" in ctx, "the panel is fetched per opportunity"
    sentinel = _panel()
    ctx["_rank_panel"] = sentinel
    trade_radar._priced(ctx, _opp(), {})
    assert ctx["_rank_panel"] is sentinel, "cache was rebuilt"


def test_chips_name_who_would_start_him_as_an_upgrade():
    ctx = _ctx()
    ctx["_rank_panel"] = _panel()
    out = "\n".join(trade_radar._chips_lines(ctx))
    assert "chips" in out
    assert "buyers: them" in out


def test_chips_degrade_without_a_panel():
    out = "\n".join(trade_radar._chips_lines(_ctx()))
    assert "no rank panel" in out

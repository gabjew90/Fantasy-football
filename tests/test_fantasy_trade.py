"""The trade command's pieces: names, return weeks, and fitting a roster after the trade."""

from __future__ import annotations

import pytest

from fantasy import trade as TR

ROSTERS = {1: [{"sleeper_id": "a", "name": "A.J. Brown"}, {"sleeper_id": "b", "name": "Josh Allen"}],
           2: [{"sleeper_id": "c", "name": "Courtland Sutton"}, {"sleeper_id": "d", "name": "Josh Allen"}]}


def test_names_match_through_punctuation_and_only_on_the_right_side():
    assert TR.resolve(["AJ Brown"], ROSTERS, within={1}) == {"a": 1}
    assert TR.resolve(["courtland sutton"], ROSTERS, within={2}) == {"c": 2}
    with pytest.raises(TR.TradeError, match="no rostered player"):
        TR.resolve(["Courtland Sutton"], ROSTERS, within={1})
    with pytest.raises(TR.TradeError, match="more than one"):
        TR.resolve(["Josh Allen"], ROSTERS)


def test_return_weeks_come_from_name_colon_week():
    assert TR.parse_back(["A.J. Brown:8", "Sutton:6"]) == {"aj brown": 8, "sutton": 6}
    with pytest.raises(TR.TradeError, match="NAME:WEEK"):
        TR.parse_back(["A.J. Brown"])


def test_an_overfull_roster_drops_its_cheapest_unprotected_player_never_the_arrival():
    rate = {"a": 10.0, "b": 2.0, "c": 1.0, "new": 0.5}
    ids, dropped, added = TR.settle_roster(["a", "b", "c", "new"], 3, rate, protected={"c"}, locked={"new"})
    assert dropped == ["b"] and "new" in ids and "c" in ids and not added


def test_an_open_spot_takes_the_free_agent_who_helps_the_lineup_not_the_top_rate():
    rate = {"a": 10.0, "qb_fa": 18.0, "wr_fa": 9.0}
    helps = {"wr_fa": 9.0, "qb_fa": 0.0}                    # a second QB never starts
    value = lambda ids: sum(helps.get(p, rate.get(p, 0.0)) for p in ids)
    ids, dropped, added = TR.settle_roster(["a"], 2, rate, set(), set(), ["qb_fa", "wr_fa"], value=value)
    assert added == ["wr_fa"] and not dropped


def _value(rates):
    # a toy lineup: the sum of the two best rates, the same every week (weeks 5-6)
    def v(ids):
        wk = sum(sorted((rates.get(p, 0.0) for p in ids), reverse=True)[:2])
        return 2 * wk, {5: wk, 6: wk}
    return v


def test_each_side_is_its_after_minus_its_before_with_the_playoff_weeks_split():
    rates = {"a": 10.0, "b": 6.0, "x": 12.0}
    me = TR.evaluate_side(["a", "b"], {"b"}, {"x"}, limit=2, reserve=set(), rate=rates, protected=set(),
                          free=[], value=_value(rates), upside_value=_value(rates), weeks=[5, 6], playoff=6)
    assert me["gain"] == pytest.approx(2 * (22 - 16)) and me["playoff_gain"] == pytest.approx(22 - 16)
    them = TR.evaluate_side(["x", "y"], {"x"}, {"b"}, limit=2, reserve=set(), rate=dict(rates, y=3.0),
                            protected=set(), free=[], value=_value(dict(rates, y=3.0)),
                            upside_value=_value(dict(rates, y=3.0)), weeks=[5, 6], playoff=6)
    assert them["gain"] < 0


def test_an_ir_stash_does_not_count_toward_the_roster_limit():
    rates = {"a": 10.0, "b": 6.0, "ir": 9.0, "x": 12.0, "y": 11.0}
    me = TR.evaluate_side(["a", "b", "ir"], {"b"}, {"x", "y"}, limit=3, reserve={"ir"}, rate=rates,
                          protected=set(), free=[], value=_value(rates), upside_value=_value(rates),
                          weeks=[5, 6], playoff=6)
    assert me["dropped"] == [] , "a, x, y fill the three active spots; the IR stash stays"


def test_the_verdict_follows_the_standing():
    side = {"gain": -2.0, "upside_gain": 8.0}
    assert TR.verdict_for(side, contender=True)[0] == "roughly even"
    assert TR.verdict_for(side, contender=False) == ("worth it", "upside (you are behind)")


def test_yahoo_status_codes_read_as_the_same_statuses():
    from fantasy import waiver as WV
    assert WV.miss_weeks("O") == WV.miss_weeks("Out") == 1
    assert WV.miss_weeks("IR-R") == WV.miss_weeks("IR") == 4
    assert WV.miss_weeks("PUP-R") == 4 and WV.miss_weeks("Q") == 0 and WV.miss_weeks(None) == 0


def test_the_drop_is_whoever_costs_the_lineup_least_not_the_lowest_rate():
    rate = {"qb": 20.0, "def": 6.0, "wr_bench": 7.0, "new": 12.0}
    starts = {"qb", "def", "new"}                           # the only defense starts every week
    value = lambda ids: sum(rate[p] for p in ids if p in starts)
    ids, dropped, _ = TR.settle_roster(["qb", "def", "wr_bench", "new"], 3, rate, set(), {"new"}, value=value)
    assert dropped == ["wr_bench"], "the bench WR goes, not the lowest-rated starting defense"

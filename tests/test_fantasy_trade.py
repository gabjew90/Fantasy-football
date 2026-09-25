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

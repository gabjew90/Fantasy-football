"""DECISIONS #225: the card starts from the market. The line restated as workload, the workload a
Power Play leg needs on each side, a view relative to the line averaged over a range, and the
efficiency grid. Known answers on hand-built inputs."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import research as RS  # noqa: E402
import scenario as SC  # noqa: E402


def test_the_hurdle_is_the_entry_payout_spread_over_its_legs():
    assert RS.pp_hurdle(4) == pytest.approx(10 ** -0.25)            # 0.5623
    assert RS.pp_hurdle(5) == pytest.approx(20 ** -0.2)             # 0.5493
    assert RS.pp_hurdle() == pytest.approx(RS.pp_hurdle(RS.POWER_PLAY["default_legs"]))
    assert round(RS.pp_hurdle(), 3) == 0.562


def test_the_power_play_workloads_solve_the_hurdle_on_each_side():
    # a share_over rising linearly in k: P = 0.5 at k = 1, +0.1 per 0.2 of k; work = 10 carries x k
    share_over = lambda k: 0.5 + 0.5 * (k - 1.0)
    work = lambda k: 10.0 * k
    RS.LAST_EDGES.clear()
    RS._hurdle_cache(share_over, work)
    h = RS.pp_hurdle()
    assert RS.LAST_EDGES["pp_over_needs"] == pytest.approx(10 * (1 + 2 * (h - 0.5)), abs=0.01)
    assert RS.LAST_EDGES["pp_under_needs"] == pytest.approx(10 * (1 - 2 * (h - 0.5)), abs=0.01)
    assert RS.LAST_EDGES["pp_hurdle"] == pytest.approx(h) and RS.LAST_EDGES["pp_legs"] == 4
    # the same anchor shift as the market-implied volume: the main run 2 points above the search
    RS._hurdle_cache(share_over, work, engine_p=0.52)
    assert RS.LAST_EDGES["pp_over_needs"] == pytest.approx(10 * (1 + 2 * (h - 0.52)), abs=0.01)
    # out of range: the edge and the workload where it ran out
    RS._hurdle_cache(lambda k: 0.3, work)
    assert RS.LAST_EDGES["pp_over_needs"] is None and RS.LAST_EDGES["pp_over_edge"] == "max"
    assert RS.LAST_EDGES["pp_over_limit"] == pytest.approx(10 * RS.K_HI)


def test_the_cell_gives_both_sides_and_how_far_apart_they_sit():
    r = {"unit": "carries", "pp_over_needs": 16.62, "pp_under_needs": 14.16}
    assert RS.pp_cell(r) == "Over above 16.6 carries · Under at 14.2 or fewer (2.5 carries apart)"
    edge = {"unit": "carries", "pp_over_needs": None, "pp_over_edge": "max", "pp_over_limit": 19.04,
            "pp_under_needs": 16.4}
    assert RS.pp_cell(edge) == ("Over: needs more than 19.0 carries (about all the work the simulation gives "
                                "him) · Under at 16.4 or fewer")
    assert RS.pp_cell({"unit": "targets"}) is None and RS.pp_cell({}) is None


def test_the_grid_shows_a_leg_at_each_rate_and_says_carries_are_the_opinion():
    rows = [{"market": "player_rush_yds", "line": 59.5, "unit": "carries"}]
    vol = [{"market": "player_rush_yds", "pp_grid": [
        {"key": "capped", "rate": 3.6, "pp_over_needs": None, "pp_over_edge": "max", "pp_over_limit": 19.0,
         "pp_under_needs": 16.4},
        {"key": "season", "rate": 3.9, "pp_over_needs": 18.0, "pp_under_needs": 15.3},
        {"key": "engine", "rate": 4.2, "pp_over_needs": 16.6, "pp_under_needs": 14.2}]}]
    L = RS.pp_grid_table(rows, vol)
    text = "\n".join(L)
    assert "carries and targets are the opinion to form" in text
    assert "| | Rushing yards 59.5 |" in text
    assert ("| At his rate this season | at 3.9 a carry: Over above 18.0 carries · Under at 15.3 or fewer "
            "(2.7 carries apart) |") in text
    assert "| At his luck-capped rate | at 3.6 a carry: Over: needs more than 19.0 carries" in text
    assert RS.pp_grid_table(rows, [{"market": "player_rush_yds", "pp_grid": []}]) == []


def test_a_view_relative_to_the_line_parses_and_resolves():
    rules = SC.parse(["Woody Marks: carries=+2/+4/+6", "Nico Collins: targets=-1", "HOU: pass=-3"], {"DAL", "HOU"})
    assert rules[0]["relative"] == [2.0, 4.0, 6.0] and rules[0]["value"] is None
    assert rules[1]["relative"] == [-1.0]
    filled = SC.fill_relative(rules, {("Woody Marks", "carries"): 14.4, ("Nico Collins", "targets"): 8.2})
    assert filled[0]["values"] == [16.4, 18.4, 20.4] and filled[0]["value"] == 18.4
    assert filled[0]["relative_to"] == 14.4 and "the line assumes 14.4: 16.4/18.4/20.4" in filled[0]["text"]
    assert filled[1]["value"] == pytest.approx(7.2) and "values" not in filled[1]
    assert filled[2] == rules[2], "a team rule is untouched"
    assert SC.as_assume(filled)[:2] == ["Woody Marks: carries=18.4", "Nico Collins: targets=7.2"]


def test_a_relative_view_with_no_line_or_below_zero_is_refused():
    rules = SC.parse(["Woody Marks: carries=+3"], {"DAL", "HOU"})
    with pytest.raises(ValueError, match="no priced rushing line"):
        SC.fill_relative(rules, {("Woody Marks", "carries"): None})
    with pytest.raises(ValueError, match="no workload"):
        SC.fill_relative(SC.parse(["Woody Marks: carries=-20"], {"DAL", "HOU"}), {("Woody Marks", "carries"): 9.7})
    with pytest.raises(ValueError, match="signs every value"):
        SC.parse(["Woody Marks: carries=+2/4/+6"], {"DAL", "HOU"})
    # an unsigned value is still a level, as before
    assert SC.parse(["Woody Marks: carries=14"], {"DAL", "HOU"})[0]["value"] == 14.0


def test_a_range_is_averaged_one_four_one():
    assert SC.range_average(0.40, 0.55, 0.70) == pytest.approx((0.40 + 4 * 0.55 + 0.70) / 6)
    assert SC.range_average(None, 0.55, 0.70) == 0.55, "an end missing: the expected alone"
    assert SC.range_average(0.4, None, 0.7) is None

"""The waiver command's pieces: standing, byes, the season gain, the role cause."""

from __future__ import annotations

import pandas as pd
import pytest

from fantasy import waiver as WV

SLOTS = {"QB": 1, "WR": 1}
FLEX = [frozenset({"RB", "WR", "TE"})]


def test_standing_ranks_by_wins_then_losses_then_points():
    rosters = [{"roster_id": 1, "settings": {"wins": 1, "losses": 1, "fpts": 200}},
               {"roster_id": 2, "settings": {"wins": 2, "losses": 0, "fpts": 150}},
               {"roster_id": 3, "settings": {"wins": 1, "losses": 1, "fpts": 250}},
               {"roster_id": 4, "settings": {"wins": 0, "losses": 2, "fpts": 300}}]
    assert WV.standing(rosters, 2) == {"rank": 1, "teams": 4, "record": "2-0", "contender": True, "unavailable": False}
    assert WV.standing(rosters, 3)["rank"] == 2 and WV.standing(rosters, 1)["rank"] == 3
    assert WV.standing(rosters, 1)["contender"] is False


def test_byes_are_the_weeks_a_team_has_no_game():
    games = pd.DataFrame([{"season": 2026, "game_type": "REG", "week": w, "home_team": "A", "away_team": "B"}
                          for w in (3, 4, 6)] + [{"season": 2026, "game_type": "REG", "week": 5,
                                                   "home_team": "B", "away_team": "C"}])
    b = WV.byes_by_team(games, 2026, range(3, 7))
    assert b["A"] == {5} and b["B"] == set() and b["C"] == {3, 4, 6}


def test_the_season_gain_counts_only_weeks_the_add_would_start():
    rates = {"qb": 20.0, "wr1": 15.0, "wr2": 14.0, "bench": 3.0}
    pos = {"qb": "QB", "wr1": "WR", "wr2": "WR", "bench": "WR", "add": "WR"}
    team = {"qb": "Q", "wr1": "X", "wr2": "Y", "bench": "Z", "add": "W"}
    weeks, byes = [5, 6, 7], {"X": {6}}
    base, _ = WV.season_gain(rates, pos, team, SLOTS, FLEX, weeks, byes)
    # a 10-point WR only starts the week wr1 is on bye: he replaces the 3-point bench WR once
    tot, wk = WV.season_gain(dict(rates, add=10.0), pos, team, SLOTS, FLEX, weeks, byes, drop="bench")
    assert tot - base == pytest.approx(10.0 - 3.0)
    assert wk[5] == wk[7] == pytest.approx(49.0) and wk[6] == pytest.approx(44.0)
    # a 16-point WR starts every week over wr2
    tot2, _ = WV.season_gain(dict(rates, add=16.0), pos, team, SLOTS, FLEX, weeks, byes, drop="bench")
    assert tot2 - base == pytest.approx((16 - 14) * 2 + (16 - 3))


def test_the_role_cause_names_a_teammate_absent_since_the_role_grew():
    rows = []
    for w in range(1, 6):
        rows.append({"gsis_id": "backup", "team": "SF", "week": w, "snap_pct": 0.2 if w < 4 else 0.8})
        if w < 4:
            rows.append({"gsis_id": "starter", "team": "SF", "week": w, "snap_pct": 0.8})
        rows.append({"gsis_id": "wr", "team": "SF", "week": w, "snap_pct": 0.9})
    u = pd.DataFrame(rows)
    pos = {"backup": "RB", "starter": "RB", "wr": "WR"}
    assert WV.role_cause("backup", u, pos) == "starter"
    assert WV.role_cause("wr", u, pos) is None, "a different position is not the cause"


def test_all_zero_standings_are_unavailable_not_a_tie_for_first():
    rosters = [{"roster_id": i, "settings": {}} for i in (1, 2, 3)]
    st = WV.standing(rosters, 2)
    assert st["unavailable"] and st["rank"] is None and st["contender"]


def test_a_protected_player_is_never_the_cut_and_ties_go_to_the_cheapest():
    ev = {"qb2": {"mean": {"snap_pct": 0.93}, "role_change": {}},              # a starting QB on my bench
          "wr5": {"mean": {"snap_pct": 0.94}, "role_change": {"tgt_share": {"changed": True, "diff": -0.1}}},
          "rb4": {"mean": {"snap_pct": 0.27}, "role_change": {}},
          "rb5": {"mean": {"snap_pct": 0.38}, "role_change": {}}}
    prot = WV.protected_cuts(list(ev), ev)
    assert prot == {"qb2"}, "a falling role is not protected"
    order = WV.cut_order(list(ev), prot, {"wr5": 7.0, "rb4": 4.8, "rb5": 5.8, "qb2": 16.7})
    assert order == ["rb4", "rb5", "wr5"] and "qb2" not in order


def test_a_player_expected_to_miss_weeks_scores_nothing_in_them():
    rates = {"qb": 20.0, "wr1": 15.0, "wr2": 14.0, "bench": 3.0}
    pos = {"qb": "QB", "wr1": "WR", "wr2": "WR", "bench": "WR", "add": "WR"}
    team = {k: k.upper() for k in list(pos)}
    weeks = [5, 6, 7, 8]
    base, _ = WV.season_gain(rates, pos, team, SLOTS, FLEX, weeks, {})
    # a 16-point WR on IR until week 7 only helps in weeks 7 and 8
    tot, _ = WV.season_gain(dict(rates, add=16.0), pos, team, SLOTS, FLEX, weeks, {}, drop="bench",
                            out_until={"add": 7})
    assert tot - base == pytest.approx((16 - 14) * 2)


def test_every_command_reads_the_record_from_the_league_view():
    from fantasy import league as LG
    rosters = [{"roster_id": 1, "settings": {"wins": 1, "losses": 1, "fpts": 200}},
               {"roster_id": 2, "settings": {"wins": 2, "losses": 0, "fpts": 150}}]
    assert WV.standing is LG.standing
    view = LG.LeagueView(league="x", platform="sleeper", season=2026, week=3, my_rid=1, opp_rid=2, my_name="me",
                         opp_name="them", my_players=[], opp_players=[], my_starters=[], opp_starters=[],
                         slots=None, flex_slots=None, info={}, scoring_yaml={}, scoring_platform={},
                         ctx={"rosters": rosters})
    assert view.standing["record"] == "1-1" and view.standing["rank"] == 2


def test_the_lineup_report_states_the_record_unmistakably():
    from fantasy.lineup import record_line
    assert record_line({"record": "1-1", "rank": 8, "teams": 10, "unavailable": False}) == \
        "**Record:** 1-1, 8th of 10 teams."
    assert "2nd of 12" in record_line({"record": "3-0", "rank": 2, "teams": 12, "unavailable": False})
    assert "11th of 12" in record_line({"record": "0-3", "rank": 11, "teams": 12, "unavailable": False})
    assert "not available" in record_line({"record": "0-0", "rank": None, "teams": 12, "unavailable": True})


def test_a_team_behind_stands_pat_only_when_no_add_clears_the_threshold():
    """Keefamania, 2026 week 3: the upside leader added +0.7 while five other
    adds cleared +5, and the report said STAND PAT."""
    from fantasy import waiver as WV
    rows = [{"add": "sutton", "drop": "ej", "gain": 0.7, "ros_upside": 20.0},
            {"add": "henry", "drop": "ej", "gain": 7.4, "ros_upside": 12.0},
            {"add": "strange", "drop": "ej", "gain": 6.9, "ros_upside": 13.0},
            {"add": "nobody", "drop": None, "gain": 9.0, "ros_upside": 30.0}]
    ranked, stand_pat = WV.rank_adds(rows, "season", contender=False)
    assert not stand_pat
    assert [r["add"] for r in ranked] == ["strange", "henry", "sutton"], \
        "adds that clear come first, by upside among them; no cut, no add"
    ranked, stand_pat = WV.rank_adds([rows[0]], "season", contender=False)
    assert stand_pat and ranked[0]["add"] == "sutton"
    ranked, _ = WV.rank_adds(rows, "season", contender=True)
    assert [r["add"] for r in ranked] == ["henry", "strange", "sutton"], "a contender ranks by gain"


def test_the_season_gain_says_which_weeks_the_add_starts():
    from fantasy import waiver as WV
    rates = {"a": 10.0, "b": 8.0, "bench": 2.0}
    pos = {"a": "WR", "b": "WR", "bench": "WR", "add": "WR"}
    team = {"a": "AAA", "b": "BBB", "bench": "CCC", "add": "DDD"}
    starts = []
    WV.season_gain(dict(rates, add=7.0), pos, team, {"WR": 2}, [], [3, 4, 5, 6], {"AAA": {5}},
                   drop="bench", starts_of="add", starts=starts)
    assert starts == [5], "he starts only in the week the WR1 is on bye"
    assert WV.week_spans([3, 4, 5, 9, 11, 12]) == "3-5, 9, 11-12" and WV.week_spans([]) == "none"


def test_an_unreachable_consensus_source_is_a_failed_input():
    from core.manifest import Manifest
    from fantasy import waiver as WV
    m = Manifest("t")
    WV.record_consensus_failures(m, ["fantasypros: fantasypros unavailable (HTTPError)", "consensus over 2 live sources"])
    e = m.get("fantasypros (rest-of-season consensus)")
    assert e["status"] == "failed" and "HTTPError" in e["detail"]


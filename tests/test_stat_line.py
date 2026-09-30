"""fantasy.boxscore.stat_line: the full weekly stat line (DECISIONS #128) --
the engine's usage beside the box score, a row per game and a season row."""

from __future__ import annotations

import types

import pandas as pd

from fantasy import boxscore as BX
from fantasy import waiver as WV

HALF = {"rec": 0.5, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "rush_td": 6.0}


def _stats():
    base = dict(season=2026, season_type="REG", team="TEN", carries=0, rushing_yards=0, rushing_tds=0,
                receiving_first_downs=0)
    return pd.DataFrame([
        dict(base, player_id="wr", week=1, opponent_team="NYJ", targets=6, receptions=5, receiving_yards=38,
             receiving_air_yards=23, receiving_yards_after_catch=13, receiving_first_downs=3, receiving_tds=0),
        dict(base, player_id="wr", week=3, opponent_team="NYG", targets=11, receptions=7, receiving_yards=57,
             receiving_air_yards=62, receiving_yards_after_catch=35, receiving_first_downs=4, receiving_tds=1)])


USAGE = {1: {"snap_pct": 0.82, "tgt_share": 0.21, "ay_share": 0.14, "wopr": 0.42},
         2: {"snap_pct": 0.53, "tgt_share": 0.06, "ay_share": 0.05, "wopr": 0.12},
         3: {"snap_pct": 0.63, "tgt_share": 0.31, "ay_share": 0.28, "wopr": 0.67}}


def test_the_stat_line_joins_usage_and_the_box_score_by_week():
    sl = BX.stat_line(_stats(), "wr", "WR", HALF, USAGE, {"snap_pct": 0.66, "tgt_share": 0.2, "ay_share": 0.16,
                                                          "wopr": 0.4})
    assert sl["kind"] == "REC" and [r["week"] for r in sl["rows"]] == [1, 2, 3]
    wk1, wk2, wk3 = sl["rows"]
    assert wk1["adot"] == 3.8 and wk3["adot"] == 5.6 and wk3["receiving_yards_after_catch"] == 35
    assert wk2["targets"] is None and wk2["snap_pct"] == 0.53, "usage but no box row: box missing, usage kept"
    s = sl["season"]
    assert s["targets"] == 17 and s["receiving_air_yards"] == 85 and s["adot"] == 5.0 and s["games"] == 2
    assert s["pts"] == round(12 * 0.5 + 9.5 + 6, 1) and s["pts_no_td"] == round(12 * 0.5 + 9.5, 1)


def test_the_table_shows_usage_and_box_and_hides_an_all_zero_secondary_column():
    table = BX.stat_line_table(BX.stat_line(_stats(), "wr", "WR", HALF, USAGE))
    head = table[0]
    for col in ("Snap %", "Tgt share", "Air-yd share", "WOPR", "Tgt", "Air yds", "aDOT", "YAC", "1st downs"):
        assert col in head, col
    assert "Rush yds" not in head, "a receiver who never ran the ball"
    assert "| 2 | -- | 53 | 6 | 5 | 0.12 | -- |" in "\n".join(table)
    assert table[-1].startswith("| **Season** (2 g)")


def test_a_back_gets_carries_ypc_and_first_downs():
    d = pd.DataFrame([dict(season=2026, season_type="REG", team="DAL", player_id="rb", week=3, opponent_team="BAL",
                           carries=19, rushing_yards=98, rushing_tds=1, rushing_first_downs=7, targets=3,
                           receptions=2, receiving_yards=5, receiving_tds=0)])
    sl = BX.stat_line(d, "rb", "RB", HALF, {3: {"snap_pct": 0.76, "carry_share": 0.63, "tgt_share": 0.08}})
    assert sl["rows"][0]["ypc"] == 5.2 and "Rush 1st downs" in BX.stat_line_table(sl)[0]


def test_only_offensive_scoring_is_listed_as_not_counted():
    left = BX.not_counted({"rec": 0.5, "pass_td_40p": 2.0, "fgm_40_49": 4.0, "def_td": 6.0, "pts_allow_0": 10.0,
                           "sack": 1.0})
    assert left == ["pass_td_40p"]


def test_waivers_name_the_scored_adds_that_gain_nothing():
    view = types.SimpleNamespace(season=2026, week=4)
    gate = types.SimpleNamespace(line=lambda: "LEAGUE DATA GATE: PASS")
    m = types.SimpleNamespace(summary_line=lambda: "inputs")
    info = {"a": {"name": "Jordan Addison", "team": "MIN", "pos": "WR"},
            "b": {"name": "Wan'Dale Robinson", "team": "TEN", "pos": "WR"}}
    ranked = [{"add": "a", "drop": "x", "gain": 0.7, "ros_upside": 1.0, "start_weeks": [5]}]
    md = WV.markdown("keefamania", view, "season", ("WR",), {"record": "1-0", "rank": 3, "teams": 10,
                     "contender": True}, gate, ranked, [], set(), {}, {}, info, {}, True, m, [],
                     scored={"candidates": 80, "improving": 1, "no_cut": [], "no_gain": ["b"]})
    assert "**Scored, no gain for your lineup:** Wan'Dale Robinson (TEN, WR)." in md
    assert "not named anywhere in this report was outside that pool" in md


def test_every_game_of_the_season_is_a_row_and_a_trade_keeps_both_teams():
    base = dict(season=2026, season_type="REG", carries=0, rushing_yards=0, rushing_tds=0, receptions=3,
                receiving_yards=30, receiving_air_yards=20, receiving_yards_after_catch=10, receiving_first_downs=1,
                receiving_tds=0)
    rows = [dict(base, player_id="wr", week=w, team="BUF" if w <= 4 else "KC", opponent_team="X", targets=5)
            for w in range(1, 10)]
    usage = {w: {"snap_pct": 0.8, "tgt_share": 0.2, "ay_share": 0.2, "wopr": 0.44} for w in range(1, 10)}
    sl = BX.stat_line(pd.DataFrame(rows), "wr", "WR", HALF, usage)
    assert [r["week"] for r in sl["rows"]] == list(range(1, 10)), "no early weeks cut off"
    assert sl["season"]["targets"] == 45 == sum(r["targets"] for r in sl["rows"]), "rows add up to the season"
    assert BX.stat_line(pd.DataFrame(rows), "wr", "WR", HALF, usage, weeks=3)["rows"][0]["week"] == 7


def test_special_teams_scoring_is_named_when_not_counted():
    left = BX.not_counted({"rec": 0.5, "st_td": 6.0, "st_fum_rec": 2.0, "def_td": 6.0})
    assert left == ["st_fum_rec"], "st_td is counted (special_teams_tds); an uncounted st_ key is named"


def test_a_back_gets_goal_line_work_explosive_runs_and_epa_per_carry():
    d = pd.DataFrame([dict(season=2026, season_type="REG", team="DAL", player_id="rb", week=w, opponent_team="X",
                           carries=c, rushing_yards=y, rushing_10=ex, rushing_first_downs=fd, rushing_epa=epa,
                           rushing_tds=td, targets=3, receptions=2, receiving_yards=12,
                           receiving_yards_after_catch=14, receiving_tds=0)
                      for w, c, y, ex, fd, epa, td in ((1, 12, 41, 0, 2, 1.39, 1), (3, 19, 98, 3, 7, -0.9, 1))])
    usage = {1: {"snap_pct": 0.71, "carry_share": 0.67, "tgt_share": 0.17, "i10_car": 3, "i10_tgt": 1},
             3: {"snap_pct": 0.76, "carry_share": 0.63, "tgt_share": 0.08, "i10_car": 4, "i10_tgt": 0}}
    sl = BX.stat_line(d, "rb", "RB", HALF, usage, {"snap_pct": 0.74, "carry_share": 0.65, "tgt_share": 0.12})
    wk3 = sl["rows"][1]
    assert wk3["rushing_10"] == 3 and wk3["epa_per_carry"] == round(-0.9 / 19, 2) and wk3["rushing_epa"] == -0.9
    s = sl["season"]
    assert s["i10_car"] == 7 and s["i10_tgt"] == 1, "goal-line work is a count: summed, not averaged"
    assert s["rushing_epa"] == 0.49 and s["epa_per_carry"] == round(0.49 / 31, 2)
    head = BX.stat_line_table(sl)[0]
    for col in ("Inside-10 car", "Inside-10 tgt", "10+ yd runs", "EPA/carry", "YAC", "YPC"):
        assert col in head, col
    assert "| 3 | X | 76 | 63 | 8 | 4 | 0 |" in "\n".join(BX.stat_line_table(sl))


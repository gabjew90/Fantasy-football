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

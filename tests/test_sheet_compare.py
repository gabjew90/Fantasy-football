"""Step 0 of the projection overhaul: the sheet reader and the comparison.

The script is the acceptance test for item 1, so its own arithmetic must be
right first: tab parsing (a player row followed by 'high'/'low' rows), league
scoring of a stat line, the games convention, and the rank correlation.
"""

from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("sc", ROOT / "scripts" / "sheet_compare.py")
sc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sc)

HALF = {"rec": 0.5, "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0,
        "rush_yd": 0.1, "rec_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0, "fum_lost": -2.0}


def test_parse_tab_pairs_each_player_with_its_high_and_low_rows():
    rows = [
        ("Player", "Team", "ATT", "YDS", "TDS", "REC", "YDS", "TDS", "FL", "FPTS"),
        ("\xa0", None, None, None, None, None, None, None, None, None),
        ("Jahmyr Gibbs", "DET", 275.2, 1383.7, 13.8, 71.3, 581.1, 4.1, 1.1, 337.4),
        (None, "high", 283.5, 1422, 15, 74, 625, 5, 1, 367.1),
        (None, "low", 260, 1300, 12, 65, 520, 3, 2, 300.0),
        ("Bijan Robinson", "ATL", 300, 1400, 12, 60, 500, 3, 1, 320.0),
        (None, "high", 310, 1500, 14, 65, 550, 4, 1, 340.0),
    ]
    out = sc.parse_tab(rows, "RB")
    assert [p["name"] for p in out] == ["Jahmyr Gibbs", "Bijan Robinson"]
    g = out[0]
    assert g["avg"]["rush_yd"] == 1383.7 and g["avg"]["rec"] == 71.3 and g["avg"]["fum_lost"] == 1.1
    assert g["high"]["rec_yd"] == 625 and g["low"]["rush_td"] == 12
    assert out[1]["low"] is None, "a missing low row stays None, never the previous player's"


def test_scoring_matches_the_sheets_own_half_ppr_points():
    """The RB tab's FPTS column is the sheet's half-PPR score of the same line;
    scoring the parsed line with Keefamania's settings must reproduce it."""
    line = {"rush_att": 275.2, "rush_yd": 1383.7, "rush_td": 13.8, "rec": 71.3,
            "rec_yd": 581.1, "rec_td": 4.1, "fum_lost": 1.1}
    pts = sc.score_projection(line, HALF)
    # 138.37 + 82.8 + 35.65 + 58.11 + 24.6 - 2.2 = 337.33
    assert abs(pts - 337.33) < 0.05


def test_spearman_handles_perfect_reversed_and_ties():
    assert abs(sc.spearman([1, 2, 3, 4], [1, 2, 3, 4]) - 1.0) < 1e-9
    assert abs(sc.spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1.0) < 1e-9
    r = sc.spearman([1, 2, 2, 4], [1, 3, 2, 4])
    assert 0.7 < r < 1.0
    assert math.isnan(sc.spearman([1, 2], [2, 1]))


def test_compare_scales_the_sheet_to_the_boards_games_and_joins_on_normalised_names():
    sheet = {"RB": [
        {"name": "Brian Thomas Jr.", "team": "JAX", "avg": {"rush_yd": 170.0, "rush_td": 17.0}, "high": None, "low": None},
        {"name": "Ja'Marr Chase", "team": "CIN", "avg": {"rush_yd": 850.0}, "high": None, "low": None},
        {"name": "Kenneth Walker III", "team": "SEA", "avg": {"rush_yd": 500.0}, "high": None, "low": None},
        {"name": "Nobody Here", "team": "FA", "avg": {"rush_yd": 10.0}, "high": None, "low": None},
    ]}
    board = pl.DataFrame({"player": ["JaMarr Chase", "Brian Thomas", "Kenneth Walker"],
                          "pos": ["RB", "RB", "RB"], "proj_pts": [80.0, 100.0, 60.0]})
    res = sc.compare(sheet, board, HALF, games=16.0)["RB"]
    assert res["matched"] == 3 and res["unmatched"] == ["Nobody Here"]
    by = {r["name"]: r for r in res["rows"]}
    # 170*0.1 + 17*6 = 119 season pts on 17 games -> 112 on 16
    assert abs(by["Brian Thomas"]["sheet_pts"] - 119.0 * 16 / 17) < 1e-6
    assert by["Brian Thomas"]["sheet_rank"] == 1 and by["Brian Thomas"]["board_rank"] == 1
    assert by["JaMarr Chase"]["board_rank"] == 2 and by["JaMarr Chase"]["sheet_rank"] == 2
    assert abs(res["spearman_all"] - 1.0) < 1e-9

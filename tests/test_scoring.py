import polars as pl

from draftkit.dataset import SCORING, fantasy_points_expr


def test_full_ppr_wr_line():
    # 6 rec, 90 yds, 1 TD, 1 fumble lost -> 6 + 9 + 6 - 2 = 19
    row = {c: 0.0 for c in SCORING}
    row.update({"receptions": 6, "receiving_yards": 90, "receiving_tds": 1,
                "receiving_fumbles_lost": 1})
    df = pl.DataFrame([row]).with_columns(fantasy_points_expr())
    assert abs(df["fpts"][0] - 19.0) < 1e-9


def test_qb_line():
    # 300 pass yds, 2 TD, 1 INT, 20 rush yds -> 12 + 8 - 1 + 2 = 21
    row = {c: 0.0 for c in SCORING}
    row.update({"passing_yards": 300, "passing_tds": 2, "passing_interceptions": 1,
                "rushing_yards": 20})
    df = pl.DataFrame([row]).with_columns(fantasy_points_expr())
    assert abs(df["fpts"][0] - 21.0) < 1e-9

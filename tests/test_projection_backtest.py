"""Item 2's harness: the arithmetic that adjudicates the blend must be right
before its verdict is trusted."""

from __future__ import annotations

import datetime as dt
import importlib.util
import math
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bt", ROOT / "scripts" / "projection_backtest.py")
bt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bt)

HALF = {"rec": 0.5, "pass_yd": 0.04, "pass_td": 4.0, "rush_yd": 0.1, "rush_td": 6.0,
        "rec_yd": 0.1, "rec_td": 6.0, "fum_lost": -2.0}


def test_score_arm_ignores_rows_the_arm_did_not_project_and_reports_n():
    r = bt.score_arm([100.0, None, 300.0, 250.0], [110.0, 50.0, 280.0, 260.0])
    assert r["n"] == 3
    assert abs(r["mae"] - (10 + 20 + 10) / 3) < 1e-9
    assert abs(r["spearman"] - 1.0) < 1e-9
    assert math.isnan(bt.score_arm([1.0, None], [1.0, 2.0])["mae"])


def test_alpha_grid_endpoints_are_the_pure_arms_and_the_optimum_is_found():
    model = [100.0, 200.0, 300.0, 400.0]
    market = [400.0, 300.0, 200.0, 100.0]
    actual = [100.0, 200.0, 300.0, 400.0]          # the model is exactly right
    g = bt.alpha_grid(model, market, actual, step=0.5)
    assert [x["alpha"] for x in g] == [0.0, 0.5, 1.0]
    assert g[-1]["mae"] == 0.0 and abs(g[-1]["spearman"] - 1.0) < 1e-9
    assert abs(g[0]["spearman"] + 1.0) < 1e-9
    # rows where either arm is missing are excluded from every alpha
    g2 = bt.alpha_grid(model + [None], market + [50.0], actual + [10.0], step=1.0)
    assert all(x["n"] == 4 for x in g2)


def test_week1_lines_scores_scales_and_drops_late_updates():
    cutoff = bt.week1_cutoff_ms(2025)
    rows = [
        {"player_id": "1", "updated_at": cutoff - 1000,
         "stats": {"gp": 1, "rush_yd": 100.0, "rush_td": 1.0, "rec": 2.0, "adp_dd_ppr": 5.0}},
        {"player_id": "2", "updated_at": cutoff + 1000,
         "stats": {"gp": 1, "rush_yd": 50.0}},                       # revised after week 1
        {"player_id": "3", "updated_at": cutoff - 1000,
         "stats": {"gp": 1, "adp_dd_ppr": 400.0, "pos_adp_dd_ppr": 40.0}},   # placeholder only
    ]
    df, rep = bt.week1_lines(rows, HALF, cutoff)
    assert rep == {"kept": 1, "dropped_late": 1, "blank": 1, "bulk_restamp": False}
    assert df["sleeper_id"].to_list() == ["1"]
    assert abs(df["lines"][0] - (10 + 6 + 1) * 17) < 1e-9


def test_week1_lines_keeps_a_bulk_restamped_snapshot_and_says_so():
    """Sleeper touched every 2025 week-1 row on 2025-10-06; the lines were
    still projections. One stamp on (nearly) every row is a touch, not an
    in-season revision, and must not empty the consensus arm."""
    cutoff = bt.week1_cutoff_ms(2025)
    late = cutoff + 30 * 86_400_000
    rows = [{"player_id": str(i), "updated_at": late, "stats": {"rush_yd": 10.0 * i}} for i in range(1, 21)]
    df, rep = bt.week1_lines(rows, HALF, cutoff)
    assert rep["bulk_restamp"] is True and rep["kept"] == 20 and rep["dropped_late"] == 0
    # but a lone late row among on-time rows is still dropped
    rows2 = [{"player_id": str(i), "updated_at": cutoff - 1000, "stats": {"rush_yd": 10.0}} for i in range(1, 20)]
    rows2.append({"player_id": "99", "updated_at": late, "stats": {"rush_yd": 10.0}})
    df2, rep2 = bt.week1_lines(rows2, HALF, cutoff)
    assert rep2["bulk_restamp"] is False and rep2["dropped_late"] == 1 and rep2["kept"] == 19


def test_week1_cutoff_is_noon_on_the_wednesday_after_week_one():
    """Sleeper stamps week-1 rows through Tuesday UTC (2024: 03:45 Tue); a
    midnight-Tuesday cutoff dropped all of them."""
    ms = bt.week1_cutoff_ms(2025)
    d = dt.datetime.fromtimestamp(ms / 1000, tz=dt.timezone.utc)
    assert d.weekday() == 2 and d.month == 9 and 6 <= d.day <= 13 and d.hour == 12
    ms24 = bt.week1_cutoff_ms(2024)
    d24 = dt.datetime.fromtimestamp(ms24 / 1000, tz=dt.timezone.utc)
    assert (d24.month, d24.day, d24.hour) == (9, 11, 12)   # 2024: Thu Sep 5 -> Wed Sep 11
    assert dt.datetime(2024, 9, 10, 3, 45, tzinfo=dt.timezone.utc).timestamp() * 1000 < ms24


def test_season_actuals_sums_league_points_and_counts_games():
    weekly = pl.DataFrame({
        "player_id": ["a", "a", "b"],
        "rushing_yards": [100.0, 50.0, 0.0], "rushing_tds": [1.0, 0.0, 0.0],
        "receptions": [0.0, 2.0, 5.0], "receiving_yards": [0.0, 20.0, 60.0],
    })
    scoring = {"rushing_yards": 0.1, "rushing_tds": 6.0, "receptions": 1.0, "receiving_yards": 0.1}
    out = bt.season_actuals(weekly, scoring)
    got = {r["gsis_id"]: r for r in out.iter_rows(named=True)}
    assert abs(got["a"]["actual"] - (10 + 6 + 5 + 2 + 2)) < 1e-9 and got["a"]["games_actual"] == 2
    assert abs(got["b"]["actual"] - 11.0) < 1e-9 and got["b"]["games_actual"] == 1

"""The positional missed-games table (plan A2): differential around the
pooled mean, keyed by market rank, DATA MISSING when absent."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import polars as pl

from draftkit import games_table as G

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("dab", ROOT / "scripts" / "derive_absence_bands.py")
dab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dab)

TABLE = {"bands": {"RB": {"1-2": {"mean": 2.0, "median": 2, "n": 40}, "3-4": {"mean": 4.0, "median": 4, "n": 40}},
                   "QB": {"1-2": {"mean": 3.0, "median": 3, "n": 40}}},
         "pooled_mean": 3.0}


class _Cfg:
    root = ROOT

    def __init__(self, d):
        self._d = d

    def get(self, k, default=None):
        return self._d.get(k, default)


def test_games_expr_is_differential_around_the_pooled_mean_and_uniform_off_table():
    df = pl.DataFrame({"pos": ["RB", "RB", "RB", "QB", "K", "WR"], "_r": [1, 4, 9, 2, 1, None]},
                      schema={"pos": pl.Utf8, "_r": pl.Int64})
    g = df.with_columns(G.games_expr(16.0, TABLE).alias("g"))["g"].to_list()
    assert g == [17.0, 15.0, 16.0, 16.0, 16.0, 16.0]      # 16-(2-3), 16-(4-3), off-table, at the mean, K, null rank
    assert df.with_columns(G.games_expr(16.0, None).alias("g"))["g"].to_list() == [16.0] * 6


def test_band_uses_the_market_rank_not_the_projection():
    df = pl.DataFrame({"pos": ["RB", "RB"], "_r": [1, 4], "proj_pts": [100.0, 300.0]})
    a = df.with_columns(G.games_expr(16.0, TABLE).alias("g"))["g"].to_list()
    b = df.with_columns(pl.col("proj_pts").reverse()).with_columns(G.games_expr(16.0, TABLE).alias("g"))["g"].to_list()
    assert a == b == [17.0, 15.0]


def test_missing_or_disabled_table_is_data_missing_and_uniform(capsys, tmp_path):
    assert G.load(_Cfg({"projections": {"games_table": {"enabled": False}}})) is None
    cfg = _Cfg({"projections": {"games_table": {"enabled": True, "path": "data/processed/nope.json"}}})
    assert G.load(cfg) is None and "DATA MISSING" in capsys.readouterr().err
    p = tmp_path / "t.json"
    p.write_text(json.dumps(TABLE), encoding="utf-8")
    cfg2 = _Cfg({"projections": {"games_table": {"enabled": True, "path": str(p)}}})
    cfg2.root = Path("/")
    t = G.load(cfg2)
    assert t is not None and t["pooled_mean"] == 3.0


def test_band_table_reproduces_means_from_a_synthetic_weekly_frame():
    # prior season 2024 ranks RBs a > b > c > d by total; next season games 16/14/12/10
    rows = []
    for pid, prior_pts, games in (("a", 300, 16), ("b", 200, 14), ("c", 100, 12), ("d", 50, 10)):
        rows.append({"pid": pid, "player": pid, "pos": "RB", "team": "T", "season": 2024, "week": 1, "fpts": float(prior_pts)})
        for w in range(1, games + 1):
            rows.append({"pid": pid, "player": pid, "pos": "RB", "team": "T", "season": 2025, "week": w, "fpts": 10.0})
    wk = pl.DataFrame(rows)
    t = dab.band_table(wk, [(2024, 2025)], bands={"RB": [(1, 2), (3, 4)]})
    assert t["bands"]["RB"]["1-2"] == {"mean": 1.0, "median": 1.0, "n": 2}     # missed 0 and 2
    assert t["bands"]["RB"]["3-4"] == {"mean": 5.0, "median": 5.0, "n": 2}     # missed 4 and 6
    assert t["pooled_mean"] == 3.0 and t["pooled_n"] == 4


def test_committed_table_has_every_cell_with_enough_players():
    p = ROOT / "data" / "processed" / "absence_bands.json"
    if not p.exists():
        import pytest
        pytest.skip("table not derived yet")
    t = json.loads(p.read_text(encoding="utf-8"))
    for pos, spans in dab.BANDS.items():
        for lo, hi in spans:
            cell = t["bands"][pos][f"{lo}-{hi}"]
            assert cell["n"] >= 30, (pos, lo, hi, cell)
    assert 2.0 < t["pooled_mean"] < 5.0

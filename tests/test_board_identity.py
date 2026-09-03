"""The identity harness (plan A0) must call a copy identical and name what
moved when something did; every projection step's 'flag off' claim rests
on it."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("bi", ROOT / "scripts" / "board_identity.py")
bi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bi)


def _board():
    return pl.DataFrame({"player": ["A", "B", "C"], "sleeper_id": ["1", "2", "3"], "pos": ["RB", "WR", "TE"],
                         "proj_pts": [200.0, 150.0, 100.0], "vorp": [50.0, 20.0, 5.0],
                         "tier": [1, 2, 3], "value_rank": [1, 2, 3], "adp": [3.0, 10.0, 40.0]})


def test_identical_copy_reports_nothing():
    assert bi.compare(_board(), _board()) == []


def test_added_columns_are_allowed_but_moved_values_and_missing_rows_are_drift():
    ref = _board()
    new = _board().with_columns(pl.lit(1.5).alias("proj_sd"))
    lines = bi.compare(new, ref)
    assert [x for x in lines if not x.startswith("note:")] == []
    assert any("new columns" in x and "proj_sd" in x for x in lines)
    moved = _board().with_columns(pl.when(pl.col("sleeper_id") == "2").then(151.0).otherwise(pl.col("proj_pts")).alias("proj_pts"))
    assert any(x.startswith("proj_pts: 1 rows moved") for x in bi.compare(moved, ref))
    fewer = _board().head(2)
    lines = bi.compare(fewer, ref)
    assert any(x.startswith("row count 3 -> 2") for x in lines) and any("1 left the board" in x for x in lines)
    reordered = _board().sort("sleeper_id", descending=True)
    assert any("other columns differ" in x for x in bi.compare(reordered, ref))   # order is part of identity


def test_parse_set_nests_and_types_values():
    got = bi.parse_set(["projections.source=external", "projections.games_table.enabled=true",
                        "engine.sims=200", "engine.dispersion_lambda=0.5"])
    assert got == {"projections": {"source": "external", "games_table": {"enabled": True}},
                   "engine": {"sims": 200, "dispersion_lambda": 0.5}}

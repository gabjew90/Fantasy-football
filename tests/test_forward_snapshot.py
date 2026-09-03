"""The forward snapshot's leakage guard (plan A1): a row whose earliest
source date is after kickoff is refused, per source, not by a pooled max."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fsnap", ROOT / "scripts" / "forward_snapshot.py")
fsnap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fsnap)


def test_leakage_rows_flags_any_source_dated_after_kickoff():
    df = pl.DataFrame({"name": ["ok", "late_espn", "late_model", "blank"],
                       "sleeper_as_of": ["2026-09-02", "2026-09-02", "2026-09-02", None],
                       "espn_as_of": ["2026-09-02", "2026-09-14", None, None],
                       "sheet_as_of": ["2026-09-01", "2026-09-01", "2026-09-01", None],
                       "model_built": ["2026-09-02", "2026-09-02", "2026-09-11", "2026-09-02"]})
    bad = fsnap.leakage_rows(df, kickoff="2026-09-10")
    assert bad["name"].to_list() == ["late_espn", "late_model"]
    assert fsnap.leakage_rows(df.head(1)).height == 0

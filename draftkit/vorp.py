"""Phase 3b — VORP against 2-FLEX-corrected replacement baselines."""

from __future__ import annotations

import polars as pl


def add_vorp(df: pl.DataFrame, baselines: dict[str, int]) -> pl.DataFrame:
    """VORP = proj_pts - proj_pts of the replacement-rank player at position."""
    df = df.filter(pl.col("proj_pts").is_not_null() & pl.col("pos").is_in(list(baselines)))
    df = df.with_columns(
        pl.col("proj_pts")
        .rank(method="ordinal", descending=True)
        .over("pos")
        .alias("pos_rank")
    )
    repl = (
        df.filter(
            pl.col("pos_rank")
            == pl.col("pos").replace_strict(baselines, default=None, return_dtype=pl.Int64)
        )
        .select("pos", pl.col("proj_pts").alias("replacement_pts"))
    )
    # if a position pool is smaller than its baseline rank, use the last player
    missing = [p for p in baselines if p not in repl["pos"].to_list()]
    if missing:
        fallback = (
            df.filter(pl.col("pos").is_in(missing))
            .group_by("pos")
            .agg(pl.col("proj_pts").min().alias("replacement_pts"))
        )
        repl = pl.concat([repl, fallback])
    df = df.join(repl, on="pos", how="left")
    return df.with_columns((pl.col("proj_pts") - pl.col("replacement_pts")).alias("vorp"))

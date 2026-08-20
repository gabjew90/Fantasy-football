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
    # Final spec §2: QB/TE replacement = mean of positional ranks 10-14
    # (smooths streaming reality and single-projection outliers);
    # RB/WR/K/DEF use the baseline rank directly.
    SMOOTHED = {"QB": (10, 14), "TE": (10, 14)}
    repl_rows = []
    for pos, baseline in baselines.items():
        grp = df.filter(pl.col("pos") == pos)
        if grp.height == 0:
            continue
        if pos in SMOOTHED:
            lo, hi = SMOOTHED[pos]
            window = grp.filter(pl.col("pos_rank").is_between(lo, hi))
            if window.height == 0:
                window = grp.filter(pl.col("pos_rank") == grp["pos_rank"].max())
            repl_rows.append(
                {"pos": pos, "replacement_pts": float(window["proj_pts"].mean())}
            )
        else:
            at_rank = grp.filter(pl.col("pos_rank") == baseline)
            pts = (
                float(at_rank["proj_pts"][0])
                if at_rank.height
                else float(grp["proj_pts"].min())
            )
            repl_rows.append({"pos": pos, "replacement_pts": pts})
    repl = pl.DataFrame(repl_rows)
    df = df.join(repl, on="pos", how="left")
    return df.with_columns((pl.col("proj_pts") - pl.col("replacement_pts")).alias("vorp"))

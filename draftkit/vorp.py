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
    # QB/TE replacement is SMOOTHED across a window rather than read off a
    # single rank: one projection outlier at the exact baseline would other-
    # wise move every VORP at the position.
    #
    # The window is anchored to the league's CONFIGURED baseline. It used to
    # be hardcoded to ranks 10-14 for every league, which silently made
    # `replacement_baselines.QB` and `.TE` dead settings -- editing them
    # changed nothing, and the "baselines are derived per league, never
    # copied" guarantee did not actually hold for these two positions. A
    # 10-team league and a superflex league got the same QB replacement.
    # Found 2026-08-31 while calibrating Keefamania's QB baseline.
    SMOOTH_SPAN = 4          # baseline .. baseline+4 inclusive
    SMOOTHED = ("QB", "TE")
    repl_rows = []
    for pos, baseline in baselines.items():
        grp = df.filter(pl.col("pos") == pos)
        if grp.height == 0:
            continue
        if pos in SMOOTHED:
            lo, hi = baseline, baseline + SMOOTH_SPAN
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

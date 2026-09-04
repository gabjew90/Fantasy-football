"""Phase 3b — VORP against 2-FLEX-corrected replacement baselines."""

from __future__ import annotations

import polars as pl


def add_vorp(df: pl.DataFrame, baselines: dict[str, int]) -> pl.DataFrame:
    """VORP = proj_pts - proj_pts of the replacement-rank player at position."""
    df = df.filter(pl.col("proj_pts").is_not_null() & pl.col("pos").is_in(list(baselines)))
    # Ordinal ranks break ties by row order, and row order after the joins is
    # not stable between runs: two 0-point QBs swapped ranks 57/58 on an
    # otherwise identical rebuild (2026-09-02), which is exactly the noise a
    # byte-identical check must not have to explain. Sort first.
    tie = ["sleeper_id"] if "sleeper_id" in df.columns else []
    df = df.sort(["pos", "proj_pts", *tie], descending=[False, True, *([False] * len(tie))])
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
    df = df.with_columns((pl.col("proj_pts") - pl.col("replacement_pts")).alias("vorp"))

    # SLOT-CONDITIONAL VALUE.
    #
    # VORP answers "how much better than a replacement at his position", which
    # is the right question only for a player filling that position's dedicated
    # slot. A player who will start in the FLEX is not competing with
    # replacement at his own position -- he is competing with the RB or WR you
    # would otherwise put in that slot.
    #
    # Getting this wrong overvalues every flex-bound tight end by the gap
    # between the two baselines. That gap is flex_repl minus the position's
    # own replacement, so it is PER POSITION and zero for whichever position
    # sets the flex baseline: on the 2026-09-04 Keefamania board TE 38.0,
    # WR 18.1, RB 0.0. Brock Bowers scores +61.9 as a tight end but only
    # +29.1 as a flex starter, and Colston Loveland goes from +19.4 to -13.4
    # -- correctly, he should not start over an RB24. That single error is what made the engine
    # recommend two elite TEs, and a hand-written "TE2 must beat the best flex
    # alternative" rule in the browser driver was papering over it.
    #
    # Added as a SEPARATE column. `vorp` keeps its meaning so the in-season
    # manager and season artifacts are untouched; only the draft path uses it.
    FLEX_ELIGIBLE = ("RB", "WR", "TE")
    flex_repl = max(
        (r["replacement_pts"] for r in repl_rows if r["pos"] in FLEX_ELIGIBLE),
        default=None,
    )
    if flex_repl is None:
        return df.with_columns(pl.col("vorp").alias("vorp_flex"))
    return df.with_columns(
        pl.when(pl.col("pos").is_in(list(FLEX_ELIGIBLE)))
        .then(pl.col("proj_pts") - flex_repl)
        .otherwise(pl.col("vorp"))
        .alias("vorp_flex")
    )

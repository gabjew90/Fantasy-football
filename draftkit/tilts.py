"""Standing ADP tilts (v2 item 1.6, research Q8) — small and few.

Persistent market inefficiencies applied as capped projection nudges:
mid-round TE trap, early/mid non-rushing QB overpricing, late rushing-QB
value, elite-TE premium, recency overhang on prior top-5 finishers. Every
tilt lives in the LEAGUE yaml under `tilts:` with an off switch; each
factor and the combined effect are capped (default 10%, research Q5).

Rushing-QB proxy: hv_touches (high-value touches — for QBs, goal-line
carries) >= 15. Documented free-data stand-in for rushing yardage share.
August-injury damping is deferred: it needs day-over-day ADP attribution
the snapshot history can't yet label as injury-driven (flagged, not faked).
"""

from __future__ import annotations

import polars as pl

RUSH_QB_HV = 15.0


def apply_tilts(df: pl.DataFrame, tcfg: dict | None,
                prior_top5_ids: set[str] | None = None
                ) -> tuple[pl.DataFrame, int]:
    """Nudge proj_pts per the configured tilts. Returns (df, rows_tilted).

    Expects columns: pos, adp, proj_pts, hv_touches, sleeper_id.
    """
    if not tcfg or not tcfg.get("enabled"):
        if "tilt" not in df.columns:
            df = df.with_columns(pl.lit(0.0).alias("tilt"))
        return df, 0
    cap = float(tcfg.get("cap", 0.10))
    adp = pl.col("adp").fill_null(999.0)
    hv = pl.col("hv_touches").fill_null(0.0)
    te_rank = (pl.when(pl.col("pos") == "TE").then(adp).otherwise(None)
               .rank(method="ordinal").over("pos"))

    tilt = pl.lit(0.0)
    tilt = tilt - pl.when((pl.col("pos") == "TE") & adp.is_between(40, 90)) \
        .then(float(tcfg.get("mid_te_fade", 0))).otherwise(0.0)
    tilt = tilt + pl.when((pl.col("pos") == "TE") & (te_rank <= 3)) \
        .then(float(tcfg.get("elite_te_boost", 0))).otherwise(0.0)
    tilt = tilt - pl.when((pl.col("pos") == "QB") & (adp < 90) & (hv < RUSH_QB_HV)) \
        .then(float(tcfg.get("nonrush_qb_fade", 0))).otherwise(0.0)
    tilt = tilt + pl.when((pl.col("pos") == "QB") & (adp > 90) & (hv >= RUSH_QB_HV)) \
        .then(float(tcfg.get("rush_qb_late_boost", 0))).otherwise(0.0)
    if prior_top5_ids:
        tilt = tilt - pl.when(pl.col("sleeper_id").cast(pl.Utf8).is_in(
            [str(x) for x in prior_top5_ids])) \
            .then(float(tcfg.get("top5_regression", 0))).otherwise(0.0)

    df = df.with_columns(tilt.clip(-cap, cap).alias("tilt"))
    df = df.with_columns(
        (pl.col("proj_pts") * (1.0 + pl.col("tilt"))).alias("proj_pts"))
    return df, int((df["tilt"].abs() > 1e-9).sum())


def prior_top5_by_pos(usage: pl.DataFrame) -> set[str]:
    """sleeper_ids of last season's top-5 positional finishers (recency
    overhang candidates), from the usage table's total fantasy points."""
    if "fpts_total" not in usage.columns or "sleeper_id" not in usage.columns:
        return set()
    out: set[str] = set()
    for pos in ("QB", "RB", "WR", "TE"):
        top = (usage.filter((pl.col("pos") == pos) & pl.col("sleeper_id").is_not_null())
               .sort("fpts_total", descending=True).head(5))
        out |= {str(x) for x in top["sleeper_id"].to_list()}
    return out

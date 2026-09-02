"""Phase 3c — gap-based tiers with cliff flags, and the tiers.csv deliverable.

Tier construction: within each position, sort by VORP and look at the drop
between consecutive players. A drop bigger than (mean + break_z * std) of that
position's drops starts a new tier. A drop bigger than (mean + cliff_z * std)
additionally flags the player *above* the gap with cliff_flag=1 — "last chair
before the music stops."
"""

from __future__ import annotations

import numpy as np
import polars as pl


def assign_tiers(
    values: list[float], break_z: float = 0.5, cliff_z: float = 1.0
) -> tuple[list[int], list[bool]]:
    """Pure function over a descending-sorted value list. Returns (tier, cliff)."""
    n = len(values)
    if n == 0:
        return [], []
    if n == 1:
        return [1], [False]
    gaps = np.array([values[i] - values[i + 1] for i in range(n - 1)])
    mean, std = float(gaps.mean()), float(gaps.std())
    # near-uniform gaps (std within float noise of zero) -> one tier
    meaningful = std > 1e-9 * max(1.0, abs(mean))
    break_thresh = mean + break_z * std
    cliff_thresh = mean + cliff_z * std
    tiers = [1]
    cliffs = [False] * n
    for i, g in enumerate(gaps):
        nxt = tiers[-1] + 1 if (meaningful and g > break_thresh) else tiers[-1]
        tiers.append(nxt)
        if meaningful and g > cliff_thresh:
            cliffs[i] = True  # player above the gap is the cliff edge
    return tiers, cliffs


def build_tiers(df: pl.DataFrame, cfg) -> pl.DataFrame:
    tcfg = cfg["tiers"]
    pools = cfg.pool_sizes
    # ADP-based inclusion: rank cutoffs are fragile against anything that
    # reshuffles ranks (durability haircut, overrides), so the board must
    # additionally contain every player the market actually drafts — else the
    # Monte Carlo rivals can't take them and urgency is systematically
    # overstated. no_market rows are always included for the manual eyeball.
    adp_within = float(tcfg.get("adp_include_within", 0) or 0)
    frames = []
    for pos, pool in pools.items():
        grp_all = df.filter(pl.col("pos") == pos).sort("vorp", descending=True)
        grp = grp_all.head(pool)
        if adp_within and grp_all.height > grp.height:
            cond = pl.col("adp").is_not_null() & (pl.col("adp") <= adp_within)
            if "no_market_flag" in df.columns:
                # flag, not proj_source: an override flips the source to
                # "override" and must not evict an activated no_market player
                cond = cond | pl.col("no_market_flag")
            elif "proj_source" in df.columns:
                cond = cond | (pl.col("proj_source") == "no_market")
            extra = grp_all.filter(
                cond & ~pl.col("sleeper_id").is_in(grp["sleeper_id"])
            )
            if extra.height:
                grp = pl.concat([grp, extra]).sort("vorp", descending=True)
        if grp.height == 0:
            continue
        tiers, cliffs = assign_tiers(
            grp["vorp"].to_list(), float(tcfg["break_z"]), float(tcfg["cliff_z"])
        )
        grp = grp.with_columns(
            pl.Series("tier", tiers, dtype=pl.Int64),
            pl.Series("cliff_flag", cliffs, dtype=pl.Boolean),
        )
        frames.append(grp)
    out = pl.concat(frames)
    # overall value rank by VORP; adp_delta = adp - value rank
    out = out.with_columns(
        pl.col("vorp").rank(method="ordinal", descending=True).alias("value_rank")
    ).with_columns((pl.col("adp") - pl.col("value_rank")).alias("adp_delta"))
    return out.sort("value_rank")


def add_handcuff_info(df: pl.DataFrame) -> pl.DataFrame:
    """UI-only handcuff columns for RBs (never an engine input).

    The market blend already prices handcuff option value, so any explicit
    contingency bump would double-count on top of an unvalidated adjustment
    (spec §2 quarantine). These columns exist so the human can see, in the
    bench rounds, who backs up a fragile (low exp_games) or currently-flagged
    starter — the systematically underpriced archetype the durability
    haircut's one-sided ledger creates.
    """
    name_col = "player" if "player" in df.columns else "name"
    rbs = df.filter((pl.col("pos") == "RB") & pl.col("team").is_not_null())
    # an "out"-zeroed starter must not be dethroned by his own backup in this
    # heuristic — exclude zeroed rows from starter determination so the backup
    # keeps his backs_up/starter_avail tag when the starter is flagged out
    candidates = rbs
    if "avail_status" in df.columns:
        healthy = rbs.filter(pl.col("avail_status").fill_null("") != "out")
        # keep a team's row set non-empty even if every RB is out
        candidates = healthy if healthy.height else rbs
    starters = (
        candidates.sort("vorp", descending=True)
        .group_by("team", maintain_order=True)
        .first()
        .select(
            "team",
            pl.col(name_col).alias("backs_up"),
            pl.col("exp_games").alias("starter_exp_games"),
            pl.col("avail_status").alias("starter_avail"),
        )
    )
    df = df.join(starters, on="team", how="left")
    # only backup RBs carry the columns; starters themselves, non-RBs, and
    # zeroed-out players (nonsense as "handcuffs") don't
    is_backup_rb = (pl.col("pos") == "RB") & (pl.col(name_col) != pl.col("backs_up"))
    if "avail_status" in df.columns:
        is_backup_rb = is_backup_rb & (pl.col("avail_status").fill_null("") != "out")
    return df.with_columns(
        pl.when(is_backup_rb).then(pl.col("backs_up")).otherwise(None).alias("backs_up"),
        pl.when(is_backup_rb).then(pl.col("starter_exp_games")).otherwise(None).alias("starter_exp_games"),
        pl.when(is_backup_rb).then(pl.col("starter_avail")).otherwise(None).alias("starter_avail"),
    )


def build_disagreements(tiers: pl.DataFrame, adp_within: float, per_side: int = 15) -> pl.DataFrame:
    """The override-pass worklist: biggest model-vs-market rank gaps among
    players the market actually drafts (ADP inside the draft).

    rank_gap = adp_rank - value_rank. Negative -> model_fade (market drafts him
    far earlier than the model would: ask "did something change for 2026 that
    2025 data can't see?"). Positive -> model_target (the late-round sheet).
    K/DEF excluded; no_market rows have no ADP and exclude themselves.
    """
    pool = tiers.filter(
        pl.col("adp").is_not_null()
        & (pl.col("adp") <= adp_within)
        & ~pl.col("pos").is_in(["K", "DEF"])
    ).with_columns(
        pl.col("adp").rank(method="ordinal").cast(pl.Int64).alias("adp_rank"),
        pl.col("value_rank").cast(pl.Int64),
    )
    pool = pool.with_columns(
        (pl.col("adp_rank") - pl.col("value_rank")).alias("rank_gap"),
        pl.when(pl.col("adp_rank") < pl.col("value_rank"))
        .then(pl.lit("model_fade"))
        .otherwise(pl.lit("model_target"))
        .alias("direction"),
    )
    fades = pool.filter(pl.col("rank_gap") < 0).sort("rank_gap").head(per_side)
    targets = pool.filter(pl.col("rank_gap") > 0).sort("rank_gap", descending=True).head(per_side)
    name_col = "player" if "player" in tiers.columns else "name"
    cols = [name_col, "pos", "team", "direction", "rank_gap", "value_rank",
            "adp_rank", "adp", "tier", "vorp", "proj_pts", "exp_games",
            "rookie_flag", "proj_source"]
    return pl.concat([fades, targets]).select([c for c in cols if c in pool.columns])


def add_upside_flags(df: pl.DataFrame) -> pl.DataFrame:
    """v2 item 1.5 role-quality gate: ceiling that comes from a PATH TO
    VOLUME, never cosmetic variance. Qualifies (with the reason labeled):
      - contingent volume: a handcuff (backs_up someone)
      - RB receiving profile: tprr >= 0.15
      - market-validated rookie: rookie_flag with ADP inside the top 120
        (the free-data proxy for day-1/2 draft capital)
    Air-yards/TD-rate gates await the opportunity rebuild (2.1) — the free
    weekly data lacks both columns; absence is labeled, not faked."""
    reasons = (
        pl.when(pl.col("backs_up").is_not_null())
        .then(pl.lit("contingent volume"))
        .when((pl.col("pos") == "RB") & (pl.col("tprr").fill_null(0) >= 0.15))
        .then(pl.lit("RB receiving profile"))
        .when(pl.col("rookie_flag") & (pl.col("adp").fill_null(999) <= 120))
        .then(pl.lit("rookie w/ market-backed capital"))
        .otherwise(None)
    )
    return df.with_columns(reasons.alias("upside_why")).with_columns(
        pl.col("upside_why").is_not_null().alias("upside_flag"))


TIERS_COLUMNS = [
    "player",
    "sleeper_id",
    "pos",
    "team",
    "bye",
    "proj_pts",
    "vorp",
    "vorp_flex",
    "tier",
    "cliff_flag",
    "pos_rank",
    "value_rank",
    "ecr",
    "adp",
    "adp_delta",
    "proj_source",
    "avail_status",
    "exp_games",
    "rookie_flag",
    "backs_up",
    "starter_exp_games",
    "starter_avail",
    "wopr",
    "tprr",
    "yprr",
    "hv_touches",
    "routes_proxy",
    "upside_flag",
    "upside_why",
    "alpha_used",
    # projection overhaul item 1: the blend's parts and the parallel source,
    # so a board can be graded component by component (scripts/sheet_compare.py)
    "proj_model_pts",
    "proj_market_pts",
    "proj_consensus_pts",
    "market_source_used",
    "backs_up_pos",
    "starter_fragility",
    "starter_fragility_label",
]


def write_tiers_csv(tiers: pl.DataFrame, path) -> None:
    out = tiers.rename({"name": "player"}).select(
        [c for c in TIERS_COLUMNS if c in tiers.rename({"name": "player"}).columns]
    )
    out = out.with_columns(
        pl.col("proj_pts").round(1),
        pl.col("vorp").round(1),
        pl.col("adp_delta").round(1),
        pl.col("exp_games").round(1),
        pl.col("wopr").round(3),
        pl.col("tprr").round(3),
        pl.col("yprr").round(2),
    )
    out.write_csv(path)

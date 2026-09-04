"""Phase 3c — gap-based tiers with cliff flags, and the tiers.csv deliverable.

Two methods, selected by `tiers.method`.

`gap_sd` (the original, still the default): within each position, sort by VORP
and look at the drop between CONSECUTIVE players. A drop bigger than
(mean + break_z * std) of that position's drops starts a new tier; bigger than
(mean + cliff_z * std) also flags the player above it as a cliff.

`anchor_frac` is the SPREADSHEET'S OWN RULE, adopted rather than reinvented: a
new tier starts when the drop from the TIER'S TOP PLAYER exceeds a fixed
fraction of the position's best value (the sheet uses 0.2 of the best VBD).

It exists because gap_sd has two failure modes that compound at any position
with one dominant player, measured on the 2026 boards:

  * ONE HUGE GAP POISONS THE BAR. Josh Allen sits 211 points clear at QB. That
    single gap drags the gap std to 39.2, putting the break bar at 32.0, and
    no gap between two ACTUAL quarterbacks can clear it. Result: 27 of 29 QBs
    in one tier. TE does the same (25 of 31), and Omnibeta's model board puts
    76 of 94 receivers in one tier.
  * STAIRCASE DRIFT. Comparing against the PREVIOUS player lets many small
    steps accumulate with no bound on a tier's own spread. That QB tier ran
    from VORP 21.7 down to -27.4.

Measured, widest within-tier spread, gap_sd -> anchor_frac: QB 94 -> 13,
TE 77 -> 12, WR 52 -> 20, RB 67 -> 29 on the Keefamania sheet board.

CLIFFS ARE UNCHANGED AND SHARED. Only the grouping was defective, and
mean + cliff_z * std is outlier-inflated in exactly the way a cliff wants.
"""

from __future__ import annotations

import numpy as np
import polars as pl

TIER_METHODS = ("gap_sd", "anchor_frac")


def assign_tiers(
    values: list[float], break_z: float = 0.5, cliff_z: float = 1.0,
    method: str = "gap_sd", break_frac: float = 0.20,
) -> tuple[list[int], list[bool]]:
    """Pure function over a descending-sorted value list. Returns (tier, cliff).

    CLIFFS ARE IDENTICAL IN BOTH METHODS. Only the tier grouping differs, and
    only the grouping was defective.

    `break_z`/`cliff_z` are z-scores on the gap distribution (gap_sd).
    `break_frac` is a FRACTION OF THE POSITION'S BEST VALUE (anchor_frac).
    Separate names because the units differ: reusing break_z would make 0.5
    mean "half a standard deviation" in one method and "half the best player
    on the board" in the other.
    """
    if method not in TIER_METHODS:
        raise ValueError(f"tiers.method {method!r} not in {TIER_METHODS}")
    n = len(values)
    if n == 0:
        return [], []
    if n == 1:
        return [1], [False]
    gaps = np.array([values[i] - values[i + 1] for i in range(n - 1)])

    # ---- cliffs: unchanged, shared, and deliberately outlier-sensitive -----
    # A cliff is one enormous step, so mean + cliff_z * std is inflated in
    # exactly the way that suits it: when a single gap dwarfs the rest, only
    # that gap should flag. It reads 1 cliff at QB, which is correct -- Allen
    # is the only real cliff there.
    mean, std = float(gaps.mean()), float(gaps.std())
    meaningful = std > 1e-9 * max(1.0, abs(mean))
    cliff_thresh = mean + cliff_z * std
    cliffs = [meaningful and float(g) > cliff_thresh for g in gaps] + [False]

    # ---- tiers -------------------------------------------------------------
    if method == "gap_sd":
        break_thresh = mean + break_z * std
        tiers = [1]
        for g in gaps:
            tiers.append(tiers[-1] + 1 if (meaningful and g > break_thresh) else tiers[-1])
        return tiers, cliffs

    # anchor_frac: the spreadsheet's rule. A new tier starts when the drop from
    # the TIER'S OWN TOP PLAYER exceeds a fixed fraction of the position's best
    # value. (The sheet uses 0.2 of the best VBD; same shape, same default.)
    #
    # It replaces gap_sd because gap_sd has two failure modes that compound at
    # any position with one dominant player, measured on the 2026 boards:
    #
    #   ONE HUGE GAP POISONS THE BAR. Josh Allen sits 211 points clear at QB.
    #   That single gap drags the gap std to 39.2, putting the break bar at
    #   32.0, and no gap between two ACTUAL quarterbacks can clear it. Result:
    #   27 of 29 QBs in one tier. TE does the same (25 of 31).
    #
    #   STAIRCASE DRIFT. Comparing against the PREVIOUS player lets many small
    #   steps accumulate with no bound on a tier's own spread. That QB tier ran
    #   from VORP 21.7 down to -27.4.
    #
    # Anchoring fixes both: a tier's internal spread is bounded by
    # construction, and the position's top value is stable against one outlier
    # in a way the gap std is not.
    top = float(values[0])
    if not np.isfinite(top) or top <= 1e-9:
        # the best player at this position is worth nothing over replacement,
        # so there is no tier structure to describe
        return [1] * n, cliffs
    break_thresh = max(break_frac, 1e-9) * top
    tiers, anchor = [1], top
    for v in values[1:]:
        if anchor - v > break_thresh:
            tiers.append(tiers[-1] + 1)
            anchor = v
        else:
            tiers.append(tiers[-1])
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
            grp["vorp"].to_list(), float(tcfg["break_z"]), float(tcfg["cliff_z"]),
            str(tcfg.get("method", "gap_sd")),
            float(tcfg.get("break_frac", 0.20)),
        )
        grp = grp.with_columns(
            pl.Series("tier", tiers, dtype=pl.Int64),
            pl.Series("cliff_flag", cliffs, dtype=pl.Boolean),
        )
        frames.append(grp)
    out = pl.concat(frames)
    # overall value rank by VORP; adp_delta = adp - value rank. Ties broken
    # by sleeper_id so a rebuild from the same inputs is byte-identical.
    tie = ["sleeper_id"] if "sleeper_id" in out.columns else []
    out = out.sort(["vorp", *tie], descending=[True, *([False] * len(tie))])
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


def finish_board(df: pl.DataFrame, cfg, baselines: dict[str, int] | None = None) -> pl.DataFrame:
    """Projection frame -> the board frame the tracker drafts from: VORP,
    tiers, handcuff and upside flags, contingency map. ONE spelling of the
    sequence, shared by cmd_tiers and every replay/bake-off script (review
    2026-09-02: three hand-synchronised copies had already drifted -- the
    projection-source gate's copy skipped the contingency map)."""
    from .fragility import add_contingency_map
    from .vorp import add_vorp

    df = add_vorp(df, baselines if baselines is not None else cfg.baselines)
    return add_contingency_map(add_upside_flags(add_handcuff_info(build_tiers(df, cfg))))


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
    "role_share",
    # projections as an input (DECISIONS #21): where the number came from and
    # the one tail rule's outputs
    "proj_as_of",
    # plan A1: how many sources carried the player and how far they disagree
    # (points, same basis as proj_pts); dispersion is read only by the
    # late-round objective (plan A3), never by VORP or tiers
    "n_sources",
    "proj_sd",
    "proj_hi",
    "proj_lo",
    # the SOURCE's own stated range (external.DISPERSION), distinct from
    # proj_sd's disagreement BETWEEN sources
    "proj_band",
    "non_starter",
    "contingent_of",
    "backs_up_pos",
    "starter_fragility",
    "starter_fragility_label",
    # DECISIONS #35: Yahoo's default overall rank (o_rank), the list an
    # autopick seat walks. Informational -- read by the tracker as `yrank`
    # for the list-walking autopick component, never by VORP or tiers.
    "yahoo_rank",
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
        *[pl.col(c).round(1) for c in ("proj_sd", "proj_hi", "proj_lo", "proj_band")
          if c in out.columns],
        *[pl.col(c).round(0) for c in ("yahoo_rank",) if c in out.columns],
    )
    out.write_csv(path)

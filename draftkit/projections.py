"""Phase 3a — projections.

Design: the projection function is deliberately swappable (register a new one
in PROJECTION_FNS). The default is a transparent two-part blend:

1. model: 2025 league-scored PPG, shrunk toward the positional mean by games
   played (ppg * g/(g+k) + pos_mean * k/(g+k)), then nudged by usage — a
   within-position regression of PPG on WOPR + high-value touches, so a player
   whose usage supported more points than they scored gets credit and vice
   versa.
2. market-implied: a per-position log curve fit of blended veteran projections
   against ECR, used at full weight for players with no 2025 data (rookies,
   injury returns, K/DEF) and at (1 - alpha) for everyone else.

This is intentionally humble: with no paid projections, the market curve
carries the information we can't model, and the model term is where the edge
lives (usage vs. draft cost).
"""

from __future__ import annotations

import numpy as np
import polars as pl

from .config import SKILL_POSITIONS


def _usage_adjusted_ppg(usage: pl.DataFrame, shrink_k: float) -> pl.DataFrame:
    """Shrink PPG by games and blend with a usage-implied PPG within position."""
    out = []
    for pos in usage["pos"].unique().to_list():
        grp = usage.filter(pl.col("pos") == pos)
        if pos not in SKILL_POSITIONS or grp.height < 12:
            out.append(
                grp.with_columns(pl.col("ppg").alias("model_ppg"))
            )
            continue
        pos_mean = float(grp.filter(pl.col("games") >= 4)["ppg"].mean() or 0.0)
        grp = grp.with_columns(
            (
                pl.col("ppg") * (pl.col("games") / (pl.col("games") + shrink_k))
                + pos_mean * (shrink_k / (pl.col("games") + shrink_k))
            ).alias("shrunk_ppg")
        )
        # usage regression: ppg ~ wopr + hv_touches_per_game (QB: skip, usage
        # cols are receiving-centric)
        if pos == "QB":
            grp = grp.with_columns(pl.col("shrunk_ppg").alias("model_ppg"))
            out.append(grp)
            continue
        fit = grp.filter(
            (pl.col("games") >= 6) & pl.col("wopr").is_not_null()
        ).with_columns((pl.col("hv_touches") / pl.col("games")).alias("hvpg"))
        if fit.height >= 15:
            X = np.column_stack(
                [
                    np.ones(fit.height),
                    fit["wopr"].fill_null(0).to_numpy(),
                    fit["hvpg"].fill_null(0).to_numpy(),
                ]
            )
            y = fit["ppg"].to_numpy()
            beta, *_ = np.linalg.lstsq(X, y, rcond=None)
            grp = grp.with_columns((pl.col("hv_touches") / pl.col("games")).alias("hvpg"))
            usage_ppg = (
                beta[0]
                + beta[1] * grp["wopr"].fill_null(0).to_numpy()
                + beta[2] * grp["hvpg"].fill_null(0).to_numpy()
            )
            grp = grp.with_columns(pl.Series("usage_ppg", usage_ppg))
            grp = grp.with_columns(
                (0.65 * pl.col("shrunk_ppg") + 0.35 * pl.col("usage_ppg")).alias("model_ppg")
            )
        else:
            grp = grp.with_columns(pl.col("shrunk_ppg").alias("model_ppg"))
        out.append(grp)
    aligned = []
    all_cols = ["model_ppg"]
    for g in out:
        aligned.append(g.select(["gsis_id"] + all_cols))
    return usage.join(pl.concat(aligned), on="gsis_id", how="left")


def _market_curve(df: pl.DataFrame) -> pl.DataFrame:
    """Fit proj_model_pts ~ a + b*ln(ecr) per position on veterans; predict all.

    ADP stands in for ECR when ECR is missing (comparable rank scales), so
    ADP-only players still get a projection path instead of silently dropping.
    """
    preds = np.full(df.height, np.nan)
    ecr_expr = (
        pl.coalesce(pl.col("ecr"), pl.col("adp")) if "adp" in df.columns else pl.col("ecr")
    )
    ecr = df.select(ecr_expr.alias("_e"))["_e"].to_numpy().astype(float)
    for pos in df["pos"].unique().to_list():
        mask = (df["pos"] == pos).to_numpy()
        fitmask = (
            mask
            & np.isfinite(ecr)
            & df["proj_model_pts"].is_not_null().to_numpy()
            & (df["games"].fill_null(0) >= 8).to_numpy()
        )
        if fitmask.sum() >= 6:
            x = np.log(ecr[fitmask])
            y = df["proj_model_pts"].to_numpy()[fitmask].astype(float)
            b, a = np.polyfit(x, y, 1)
            predmask = mask & np.isfinite(ecr)
            preds[predmask] = a + b * np.log(ecr[predmask])
    return df.with_columns(pl.Series("proj_market_pts", preds).fill_nan(None))


def _no_market_fallback(market: pl.DataFrame, usage: pl.DataFrame, floor: float) -> pl.DataFrame:
    """Veterans with real 2025 production but no market row at all.

    The market refusing to rank a productive player is an opinion, not a fact;
    these rows let the stats model hold its own opinion (flagged no_market so
    they get a manual eyeball, and the live engine ignores them unless the
    user activates them via overrides.csv).
    """
    have = market["sleeper_id"].drop_nulls().cast(pl.Utf8).to_list()
    cand = usage.filter(
        pl.col("sleeper_id").is_not_null()
        & pl.col("pos").is_in(list(SKILL_POSITIONS))
        & (pl.col("fpts_total") >= floor)
        & ~pl.col("sleeper_id").cast(pl.Utf8).is_in(have)
    )
    if cand.height == 0:
        return market.head(0)
    return cand.select(
        pl.col("sleeper_id").cast(pl.Utf8),
        pl.col("name"),
        pl.col("pos"),
        pl.col("team_2025").alias("team"),
    ).unique(subset="sleeper_id").with_columns(
        pl.lit(None, dtype=pl.Float64).alias("ecr"),
        pl.lit(None, dtype=pl.Float64).alias("ecr_sd"),
        pl.lit(None, dtype=pl.Float64).alias("adp"),
        pl.lit(None, dtype=pl.Int64).alias("bye"),
    )


def _apply_availability(df: pl.DataFrame, av: pl.DataFrame) -> pl.DataFrame:
    """Availability sweep results (data/external/availability.csv).

    status "out" zeroes the projection (player stays on the board so the draft
    room shows him as dead weight); "compromised" only carries a flag for a
    manual look. Applied after overrides, deliberately: "out" is a fact, not a
    view, so it supersedes even a manual override.
    """
    av = av.select(
        pl.col("sleeper_id").cast(pl.Utf8),
        pl.col("status").cast(pl.Utf8).str.to_lowercase().str.strip_chars().alias("avail_status"),
    ).unique(subset="sleeper_id")
    df = df.join(av, on="sleeper_id", how="left")
    return df.with_columns(
        pl.when(pl.col("avail_status") == "out")
        .then(0.0)
        .otherwise(pl.col("proj_pts"))
        .alias("proj_pts")
    )


def default_projection(cfg, usage: pl.DataFrame, market: pl.DataFrame) -> pl.DataFrame:
    """Return market frame + proj_pts, proj_source, and carried usage metrics."""
    p = cfg["projections"]
    shrink_k = float(p["shrink_k"])
    alpha = float(p["model_alpha"])
    games = float(p["expected_games"])

    no_market_ids: list[str] = []
    floor = float(p.get("no_market_floor", 0) or 0)
    if floor:
        fb = _no_market_fallback(market, usage, floor)
        if fb.height:
            no_market_ids = fb["sleeper_id"].to_list()
            market = pl.concat([market, fb], how="diagonal_relaxed")

    usage = _usage_adjusted_ppg(usage, shrink_k)
    u = usage.filter(pl.col("sleeper_id").is_not_null()).select(
        "sleeper_id",
        "games",
        "ppg",
        "model_ppg",
        "wopr",
        "target_share",
        "air_yards_share",
        "tprr",
        "yprr",
        "routes_proxy",
        "hv_touches",
        "offense_snap_pct",
        "avg_separation",
        "exp_games",
        "team_2025",
    ).unique(subset="sleeper_id")

    df = market.join(u, on="sleeper_id", how="left")
    df = df.with_columns((pl.col("model_ppg") * games).alias("proj_model_pts"))
    df = _market_curve(df)

    # K/DEF have no offensive stat lines, so neither the model nor the fitted
    # market curve covers them. Assign a synthetic projection from ECR rank
    # within position — a gentle linear decline, which correctly yields small
    # VORP spreads (K/DEF are near-fungible and shouldn't out-rank skill picks).
    kdef_base = {"K": (150.0, 1.5), "DEF": (135.0, 2.0)}
    # ADP stands in for a missing ECR here too, so a K/DEF present only in
    # the ADP feed still gets a projection instead of silently dropping
    df = df.with_columns(
        pl.coalesce(pl.col("ecr"), pl.col("adp"))
        .rank(method="ordinal").over("pos").alias("_ecr_pos_rank")
    )
    df = df.with_columns(
        pl.when(
            pl.col("pos").is_in(list(kdef_base))
            & pl.col("proj_market_pts").is_null()
            & pl.coalesce(pl.col("ecr"), pl.col("adp")).is_not_null()
        )
        .then(
            pl.col("pos").replace_strict(
                {k: v[0] for k, v in kdef_base.items()}, default=None
            )
            - pl.col("pos").replace_strict(
                {k: v[1] for k, v in kdef_base.items()}, default=None
            )
            * (pl.col("_ecr_pos_rank") - 1)
        )
        .otherwise(pl.col("proj_market_pts"))
        .alias("proj_market_pts")
    ).drop("_ecr_pos_rank")
    # a K who once threw a lateral shouldn't get a stats-based projection
    df = df.with_columns(
        pl.when(pl.col("pos").is_in(list(kdef_base)))
        .then(None)
        .otherwise(pl.col("proj_model_pts"))
        .alias("proj_model_pts")
    )

    # v2 item 1.7 — alpha by player type: trust the stats model more for
    # stable-role veterans (12+ games, same team) and the market more for
    # players in new situations. Committee detection needs the opportunity
    # rebuild (2.1); until then new-team + rookie carry the volatility class.
    a_cfg = p.get("alpha_by_type") or {}
    a_stable = float(a_cfg.get("stable_veteran", alpha))
    a_vol = float(a_cfg.get("volatile", alpha))
    # team_2025 is an nflverse code (GB, KC, SF...); market team uses the
    # Sleeper-style codes (GBP, KCC, SFO...). Without this mapping every
    # player on ~10 franchises was a false "new team" (code review 2026-08-30).
    from .seasondata import _TEAM_MAP
    team25 = pl.col("team_2025").replace(_TEAM_MAP)
    new_team = (team25.is_not_null() & pl.col("team").is_not_null()
                & (team25 != pl.col("team")))
    alpha_col = (
        pl.when(new_team).then(a_vol)
        .when((pl.col("games").fill_null(0) >= 12) & ~new_team).then(a_stable)
        .otherwise(alpha)
    )
    df = df.with_columns(alpha_col.alias("_alpha"))
    df = df.with_columns(
        pl.when(pl.col("proj_model_pts").is_not_null() & pl.col("proj_market_pts").is_not_null())
        .then(pl.col("_alpha") * pl.col("proj_model_pts")
              + (1 - pl.col("_alpha")) * pl.col("proj_market_pts"))
        .when(pl.col("proj_model_pts").is_not_null())
        .then(pl.col("proj_model_pts"))
        .otherwise(pl.col("proj_market_pts"))
        .alias("proj_pts"),
        pl.when(pl.col("proj_model_pts").is_not_null() & pl.col("proj_market_pts").is_not_null())
        .then(pl.lit("blend"))
        .when(pl.col("proj_model_pts").is_not_null())
        .then(pl.lit("model_only"))
        .when(pl.col("proj_market_pts").is_not_null())
        .then(pl.lit("market_implied"))
        .otherwise(pl.lit("none"))
        .alias("proj_source"),
    )
    df = df.with_columns(
        pl.when(pl.col("proj_source") == "blend").then(pl.col("_alpha"))
        .when(pl.col("proj_source") == "model_only").then(1.0)
        .otherwise(0.0)
        .round(2)
        .alias("alpha_used")
    ).drop("_alpha")
    # no_market_flag survives overrides (which flip proj_source to "override")
    # so the board's unconditional inclusion can't lose an ACTIVATED player
    df = df.with_columns(
        pl.col("sleeper_id").is_in(no_market_ids).alias("no_market_flag")
        if no_market_ids else pl.lit(False).alias("no_market_flag")
    )
    if no_market_ids:
        df = df.with_columns(
            pl.when(pl.col("sleeper_id").is_in(no_market_ids))
            .then(pl.lit("no_market"))
            .otherwise(pl.col("proj_source"))
            .alias("proj_source")
        )

    # Durability haircut REMOVED (v2 plan 1.3, research Q6): games-missed
    # history is near-zero predictive year over year, and the haircut moved
    # real draft values off folklore. exp_games stays as an informational
    # column with ZERO projection effect. If durability ever returns it is
    # position x workload x injury-type with heavy shrinkage — not this year.
    df = df.with_columns(
        pl.col("exp_games").fill_null(16.0).alias("exp_games"),
    ).with_columns(
        (
            pl.col("proj_model_pts").is_null()
            & ~pl.col("pos").is_in(["K", "DEF"])
        ).alias("rookie_flag"),
    )

    # optional overrides: data/external/overrides.csv (sleeper_id or name, proj_pts)
    # Overrides are ABSOLUTE point values in the LEAGUE'S OWN SCORING, so they
    # must be league-scoped: a full-PPR research projection forced onto a
    # half-PPR board overstates pass-catchers by ~15-20% (code review 8/31).
    ov_path = cfg.scoped(cfg.path("external") / "overrides.csv")
    if ov_path.exists():
        ov = pl.read_csv(ov_path, infer_schema_length=1000)
        if "sleeper_id" in ov.columns and "proj_pts" in ov.columns:
            # keep="last": a hand-edited duplicate row means the later line is
            # the revision, and a non-unique join would multiply the player
            ov = ov.select(
                pl.col("sleeper_id").cast(pl.Utf8),
                pl.col("proj_pts").cast(pl.Float64).alias("proj_override"),
            ).unique(subset="sleeper_id", keep="last")
            df = df.join(ov, on="sleeper_id", how="left").with_columns(
                pl.when(pl.col("proj_override").is_not_null())
                .then(pl.lit("override"))
                .otherwise(pl.col("proj_source"))
                .alias("proj_source"),
                pl.coalesce(pl.col("proj_override"), pl.col("proj_pts")).alias("proj_pts"),
            ).drop("proj_override")

    av_path = cfg.path("external") / "availability.csv"
    if av_path.exists():
        av = pl.read_csv(av_path, infer_schema_length=1000)
        if "sleeper_id" in av.columns and "status" in av.columns:
            df = _apply_availability(df, av)
    if "avail_status" not in df.columns:
        df = df.with_columns(pl.lit(None, dtype=pl.Utf8).alias("avail_status"))

    return df


PROJECTION_FNS = {"default": default_projection}

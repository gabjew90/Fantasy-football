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
        # usage regression: ppg ~ wopr + hv_touches_per_game. WOPR and
        # high-value touches are receiving and goal-line metrics, so until
        # 2026-09-02 QBs skipped this step and a QB's model term was his
        # shrunk 2025 PPG alone. The shrink pulls every high scorer toward
        # the positional mean and nothing gave credit back for the volume
        # that produced the points -- so rushing QBs (Daniels 8.3 carries a
        # game, Lamar 5.2) sat below pocket veterans with more 2025 games
        # (Stafford 1.7). QBs now get their own regression on rushing
        # volume and snap share (projection overhaul, usage-side fix 2).
        if pos == "QB":
            if all(c in grp.columns for c in ("carries", "offense_snap_pct")):
                fit = grp.filter((pl.col("games") >= 6) & pl.col("offense_snap_pct").is_not_null())
                if fit.height >= 15:
                    X = np.column_stack([
                        np.ones(fit.height),
                        (fit["carries"].fill_null(0) / fit["games"]).to_numpy(),
                        fit["offense_snap_pct"].fill_null(0).to_numpy(),
                    ])
                    beta, *_ = np.linalg.lstsq(X, fit["ppg"].to_numpy(), rcond=None)
                    usage_ppg = (beta[0]
                                 + beta[1] * (grp["carries"].fill_null(0) / grp["games"]).to_numpy()
                                 + beta[2] * grp["offense_snap_pct"].fill_null(0).to_numpy())
                    grp = grp.with_columns(pl.Series("usage_ppg", usage_ppg)).with_columns(
                        (0.65 * pl.col("shrunk_ppg") + 0.35 * pl.col("usage_ppg")).alias("model_ppg"))
                    out.append(grp)
                    continue
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
    """Dispatch on projections.source (DECISIONS 2026-09-02 #21).

    external  (config default) -- stat lines from outside, scored in league
              settings: draftkit/external.py. The projection is an INPUT.
    model     the retired 2025-usage + log(ECR) blend below. Off by default;
              it has never beaten the external source out of sample and the
              burden of proof is on it (scripts/projection_backtest.py).
    Test fixtures that carry no `source` get the legacy path, so they test
    what they were written to test."""
    source = str((cfg.get("projections") or {}).get("source", "model"))
    if source == "external":
        return external_projection(cfg, usage, market)
    if source != "model":
        raise ValueError(f"projections.source must be external or model, got {source!r}")
    return model_projection(cfg, usage, market)


def external_projection(cfg, usage: pl.DataFrame, market: pl.DataFrame) -> pl.DataFrame:
    """proj_pts from external stat lines; the engine does everything else."""
    import sys

    from . import external as X
    from .ids import SleeperIndex
    from .sleeper import SleeperClient

    p = cfg["projections"]
    games = float(p.get("games", p.get("expected_games", 16.0)))
    players = SleeperClient(cfg.path("raw")).players()
    lines, rep = X.load_external(cfg, SleeperIndex(players))
    for s in rep["sources"]:
        print(f"  projections <- {s['source']}: {s['rows']} players"
              + (f" (as of {s['as_of']})" if s.get("as_of") else "")
              + (f"  !! {s['error']}" if s.get("error") else ""), file=sys.stderr)
    if rep["sheet_unmatched"]:
        print(f"  sheet names not matched to Sleeper ({len(rep['sheet_unmatched'])}): "
              + ", ".join(rep["sheet_unmatched"][:12]) + (" …" if len(rep["sheet_unmatched"]) > 12 else ""),
              file=sys.stderr)

    # the board is the union of the market table and the projected players:
    # a projected player the market does not rank still exists (no ADP, so
    # the survival sim treats him as always available)
    ext = lines.select("sleeper_id", pl.col("name").alias("name_ext"), pl.col("pos").alias("pos_ext"),
                       pl.col("team").alias("team_ext"), "pts17", "source", pl.col("as_of").alias("proj_as_of"))
    df = market.join(ext, on="sleeper_id", how="full", coalesce=True).with_columns(
        pl.coalesce(pl.col("name"), pl.col("name_ext")).alias("name"),
        pl.coalesce(pl.col("pos"), pl.col("pos_ext")).alias("pos"),
        pl.coalesce(pl.col("team"), pl.col("team_ext")).alias("team"),
    ).drop("name_ext", "pos_ext", "team_ext")
    df = df.with_columns((pl.col("pts17") * games / X.LINE_GAMES).alias("proj_pts"),
                         pl.coalesce(pl.col("source"), pl.lit("none")).alias("proj_source")).drop("pts17", "source")

    # K/DEF: no stat lines in either source; the synthetic ECR-linear
    # projection stays (near-fungible positions, small VORP spreads)
    kdef_base = {"K": (150.0, 1.5), "DEF": (135.0, 2.0)}
    df = df.with_columns(pl.coalesce(pl.col("ecr"), pl.col("adp")).rank(method="ordinal").over("pos").alias("_r"))
    df = df.with_columns(
        pl.when(pl.col("pos").is_in(list(kdef_base)) & pl.col("proj_pts").is_null() & pl.col("_r").is_not_null())
        .then(pl.col("pos").replace_strict({k: v[0] for k, v in kdef_base.items()}, default=None)
              - pl.col("pos").replace_strict({k: v[1] for k, v in kdef_base.items()}, default=None) * (pl.col("_r") - 1))
        .otherwise(pl.col("proj_pts")).alias("proj_pts"),
        pl.when(pl.col("pos").is_in(list(kdef_base)) & (pl.col("proj_source") == "none") & pl.col("_r").is_not_null())
        .then(pl.lit("kdef_synthetic")).otherwise(pl.col("proj_source")).alias("proj_source"),
    ).drop("_r")

    # carried usage metrics: display and handcuff columns only, never an input
    keep = ["sleeper_id", "games", "ppg", "wopr", "target_share", "air_yards_share", "tprr", "yprr",
            "routes_proxy", "hv_touches", "offense_snap_pct", "avg_separation", "exp_games", "team_2025"]
    u = (usage.filter(pl.col("sleeper_id").is_not_null())
              .select([c for c in keep if c in usage.columns]).unique(subset="sleeper_id"))
    df = df.join(u, on="sleeper_id", how="left")
    for c in keep[1:]:
        if c not in df.columns:
            df = df.with_columns(pl.lit(None, dtype=pl.Float64).alias(c))
    df = df.with_columns(pl.col("exp_games").fill_null(16.0),
                         (pl.col("games").is_null() & ~pl.col("pos").is_in(["K", "DEF"])).alias("rookie_flag"),
                         pl.lit(0.0).alias("alpha_used"),
                         pl.lit(False).alias("no_market_flag"))

    # the one tail rule
    df = df.with_columns(pl.lit(False).alias("non_starter"), pl.lit(None, dtype=pl.Utf8).alias("contingent_of"))
    if p.get("non_starters_zero", True):
        depth = X.depth_table(cfg.path("raw"))
        if depth is None:
            print("  NON-STARTER RULE SKIPPED: no players_nfl.json cache (run `players`)", file=sys.stderr)
        else:
            teams = int((cfg.get("expected") or {}).get("teams") or (cfg.get("market") or {}).get("teams") or 12)
            df = X.zero_non_starters(df.drop("non_starter", "contingent_of"), depth, teams)
            print(f"  non-starters zeroed: {int(df['non_starter'].sum())}", file=sys.stderr)

    # unprojected skill players the market drafts: loud, never silent
    adp_in = float((cfg.get("tiers") or {}).get("adp_include_within", 150) or 150)
    missing = df.filter(pl.col("proj_pts").is_null() & pl.col("adp").is_not_null() & (pl.col("adp") <= adp_in)
                        & ~pl.col("pos").is_in(list(kdef_base)))
    if missing.height:
        print(f"  UNPROJECTED but drafted (ADP <= {adp_in:g}): "
              + ", ".join(f"{n} ({ps} {a:.0f})" for n, ps, a in missing.select("name", "pos", "adp").iter_rows()),
              file=sys.stderr)
    return _finish(cfg, df)


def _finish(cfg, df: pl.DataFrame) -> pl.DataFrame:
    """Overrides (confirmed rows only) and the availability sweep -- protocol
    steps shared by both projection paths."""
    from . import overrides as _ov_mod
    ov = _ov_mod.read(cfg.scoped(cfg.path("external") / "overrides.csv"))
    if ov is not None:
        ov, _candidates = _ov_mod.split(ov)
        if ov.height:
            ov = ov.select(pl.col("sleeper_id").cast(pl.Utf8),
                           pl.col("proj_pts").cast(pl.Float64).alias("proj_override")).unique(subset="sleeper_id", keep="last")
            df = df.join(ov, on="sleeper_id", how="left").with_columns(
                pl.when(pl.col("proj_override").is_not_null()).then(pl.lit("override")).otherwise(pl.col("proj_source")).alias("proj_source"),
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


def model_projection(cfg, usage: pl.DataFrame, market: pl.DataFrame) -> pl.DataFrame:
    """RETIRED 2026-09-02 (DECISIONS #21): the 2025-usage + log(ECR) blend.
    Kept behind projections.source: model for the backtest and for the day
    it earns its way back. Returns market frame + proj_pts, proj_source."""
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

    # Role gate (projection overhaul, usage-side fix 1, 2026-09-02): a per-game
    # rate cannot say "he will not start". Scale the MODEL term by the share
    # of weeks a depth-chart backup can expect the role, and only when the
    # market rank agrees he is a backup. Applied AFTER the curve fit so the
    # market curve is still fitted on ungated veteran points. See role.py.
    df = df.with_columns(pl.lit(1.0).alias("role_share"))
    rg = p.get("role_gate") or {}
    if rg.get("enabled"):
        from . import role as _role
        depth = _role.depth_orders(cfg.path("raw"))
        if depth is None:
            import sys
            print("  ROLE GATE SKIPPED: no players_nfl.json cache (run `players`)", file=sys.stderr)
        else:
            teams = int((cfg.get("expected") or {}).get("teams")
                        or (cfg.get("market") or {}).get("teams") or 12)
            df = _role.apply_role_gate(df.drop("role_share"), depth, teams,
                                       starters=rg.get("starters"))

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

    # Projection overhaul item 1 (2026-09-02): consensus stat lines scored in
    # league settings, joined by Sleeper id as a PARALLEL column. Off unless
    # the config enables it (test fixtures have no consensus block and stay
    # byte-identical). With market_source == "stat_lines" the column REPLACES
    # the log-rank curve wherever it exists; the curve remains the fallback
    # for players Rotowire does not project. Either way the column is written
    # so the board can be graded against the sheet component by component.
    c_cfg = p.get("consensus") or {}
    source = str(p.get("market_source", "ecr_curve"))
    df = df.with_columns(pl.lit(None, dtype=pl.Float64).alias("proj_consensus_pts"),
                         pl.lit("ecr_curve").alias("market_source_used"))
    if c_cfg.get("enabled"):
        from . import consensus as _cons
        try:
            cons, _rep = _cons.load_consensus(cfg)
        except _cons.ConsensusUnavailable as e:
            import sys
            print(f"  CONSENSUS UNAVAILABLE ({e}); proj_consensus_pts empty"
                  + (", market_source stat_lines falls back to ecr_curve" if source == "stat_lines" else ""),
                  file=sys.stderr)
        else:
            df = (df.drop("proj_consensus_pts")
                    .join(cons.select("sleeper_id", "proj_consensus_pts", "adp_sleeper"),
                          on="sleeper_id", how="left"))
            if source == "stat_lines":
                df = df.with_columns(
                    pl.when(pl.col("proj_consensus_pts").is_not_null())
                    .then(pl.lit("stat_lines")).otherwise(pl.lit("ecr_curve"))
                    .alias("market_source_used"),
                    pl.coalesce(pl.col("proj_consensus_pts"), pl.col("proj_market_pts"))
                    .alias("proj_market_pts"),
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
    # Projection overhaul item 2 (backtest, DECISIONS #20): a per-position CAP
    # on the usage weight. Over 2023->2024 and 2024->2025, in both leagues,
    # every step of alpha above zero made the WR projection worse on MAE and
    # on rank correlation; RB/QB/TE optima flipped between seasons and are
    # left alone. The cap sits under the player-type alpha, never above it.
    caps = {str(k).upper(): float(v) for k, v in (p.get("alpha_cap_by_position") or {}).items()}
    if caps:
        cap_col = pl.col("pos").replace_strict(caps, default=None, return_dtype=pl.Float64)
        alpha_col = pl.min_horizontal(alpha_col, pl.coalesce(cap_col, pl.lit(1.0)))
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
    # Only CONFIRMED rows are applied. A `candidate` row is inert and the
    # model's number stands -- see draftkit/overrides.py for why freshness is
    # enforced structurally rather than by remembering to check.
    from . import overrides as _ov_mod
    ov_path = cfg.scoped(cfg.path("external") / "overrides.csv")
    ov = _ov_mod.read(ov_path)
    if ov is not None:
        ov, _candidates = _ov_mod.split(ov)
        if ov.height:
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

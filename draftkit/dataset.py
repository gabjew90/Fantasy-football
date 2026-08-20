"""Phase 2 — predictive dataset from nflverse (via nflreadpy).

Outputs two parquet files in data/processed:
- team_context.parquet: offensive EPA/play, neutral pass rate, pace
- usage.parquet: per-player 2025 usage + efficiency metrics and league-scored
  fantasy points per game

Route data caveat: nflverse participation (true routes run) ended after 2023, so
TPRR/YPRR here use proxy routes = offensive snaps x team dropback rate and are
flagged `routes_proxy = true`.
"""

from __future__ import annotations

import polars as pl

# League scoring (verified against Sleeper scoring_settings 2026-08-19).
# Applied to nflverse weekly stat columns.
SCORING = {
    "passing_yards": 0.04,
    "passing_tds": 4.0,
    "passing_interceptions": -1.0,
    "rushing_yards": 0.1,
    "rushing_tds": 6.0,
    "receptions": 1.0,
    "receiving_yards": 0.1,
    "receiving_tds": 6.0,
    "passing_2pt_conversions": 2.0,
    "rushing_2pt_conversions": 2.0,
    "receiving_2pt_conversions": 2.0,
    "sack_fumbles_lost": -2.0,
    "rushing_fumbles_lost": -2.0,
    "receiving_fumbles_lost": -2.0,
    "special_teams_tds": 6.0,
}


def fantasy_points_expr() -> pl.Expr:
    expr = pl.lit(0.0)
    for col, w in SCORING.items():
        expr = expr + pl.col(col).fill_null(0.0).cast(pl.Float64) * w
    return expr.alias("fpts")


SEASON_GAMES = 17  # NFL regular-season length; 16 is the projection convention


def build_durability(active_weekly: pl.DataFrame, seasons: tuple[int, ...]) -> pl.DataFrame:
    """exp_games = clamp(16 - avg games missed over played seasons, 12, 16).

    Only seasons the player actually appeared in count toward the average
    (a 2025 debut is not 'missed' 2023). 2026 rookies have no rows at all and
    are handled downstream (exp_games null -> 16, rookie_flag).
    """
    per_season = (
        active_weekly.filter(pl.col("season").is_in(list(seasons)))
        .group_by("player_id", "season")
        .agg(pl.len().alias("games"))
        .with_columns(
            (SEASON_GAMES - pl.col("games")).clip(lower_bound=0).alias("missed")
        )
    )
    return (
        per_season.group_by("player_id")
        .agg(pl.col("missed").mean().alias("avg_missed"))
        .with_columns(
            (16.0 - pl.col("avg_missed")).clip(lower_bound=12.0, upper_bound=16.0)
            .alias("exp_games")
        )
        .rename({"player_id": "gsis_id"})
        .select("gsis_id", "avg_missed", "exp_games")
    )


def build_team_context(pbp: pl.DataFrame) -> pl.DataFrame:
    """Offensive EPA/play, neutral pass rate (Q1-Q3, WP 20-80%), plays/game."""
    plays = pbp.filter(
        (pl.col("play_type").is_in(["pass", "run"])) & pl.col("posteam").is_not_null()
    )
    neutral = plays.filter(
        (pl.col("qtr") <= 3) & (pl.col("wp") >= 0.2) & (pl.col("wp") <= 0.8)
    )
    ctx = (
        plays.group_by("posteam")
        .agg(
            pl.len().alias("plays"),
            pl.col("game_id").n_unique().alias("games"),
            pl.col("epa").mean().alias("off_epa_play"),
            (pl.col("play_type") == "pass").mean().alias("pass_rate"),
        )
        .with_columns((pl.col("plays") / pl.col("games")).alias("plays_per_game"))
    )
    npr = neutral.group_by("posteam").agg(
        (pl.col("play_type") == "pass").mean().alias("neutral_pass_rate")
    )
    # team dropback rate for the route proxy (uses all plays incl. scrambles/sacks)
    dbr = plays.group_by("posteam").agg(
        pl.col("qb_dropback").fill_null(0).mean().alias("dropback_rate"),
        pl.col("qb_dropback").fill_null(0).sum().alias("dropbacks"),
    )
    return (
        ctx.join(npr, on="posteam", how="left")
        .join(dbr, on="posteam", how="left")
        .rename({"posteam": "team"})
        .sort("off_epa_play", descending=True)
    )


def build_high_value_touches(pbp: pl.DataFrame) -> pl.DataFrame:
    """Carries + targets inside the opponent 10 (high-leverage TD equity)."""
    inside10 = pbp.filter(pl.col("yardline_100") <= 10)
    rz_rush = (
        inside10.filter(pl.col("rusher_player_id").is_not_null())
        .group_by(pl.col("rusher_player_id").alias("gsis_id"))
        .agg(pl.len().alias("hv_carries"))
    )
    rz_tgt = (
        inside10.filter(pl.col("receiver_player_id").is_not_null())
        .group_by(pl.col("receiver_player_id").alias("gsis_id"))
        .agg(pl.len().alias("hv_targets"))
    )
    return rz_rush.join(rz_tgt, on="gsis_id", how="full", coalesce=True).with_columns(
        (pl.col("hv_carries").fill_null(0) + pl.col("hv_targets").fill_null(0)).alias(
            "hv_touches"
        )
    )


def build_usage(cfg) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Pull nflverse data and compute season-level player usage metrics."""
    import nflreadpy as nfl

    season = int(cfg["stats_season"])
    durability_seasons = (season - 2, season - 1, season)
    weekly_all = nfl.load_player_stats(list(durability_seasons)).filter(
        pl.col("season_type") == "REG"
    )
    weekly = weekly_all.filter(pl.col("season") == season)
    pbp = nfl.load_pbp([season]).filter(pl.col("season_type") == "REG")

    team_ctx = build_team_context(pbp)
    hv = build_high_value_touches(pbp)

    carries_col = "carries" if "carries" in weekly.columns else "rushing_attempts"

    def _active(df: pl.DataFrame) -> pl.DataFrame:
        return df.with_columns(fantasy_points_expr()).filter(
            (
                (
                    pl.col(carries_col).fill_null(0)
                    + pl.col("targets").fill_null(0)
                    + pl.col("passing_yards").fill_null(0).abs()
                    + pl.col("receptions").fill_null(0)
                )
                > 0
            )
            | (pl.col("fpts") != 0)
        )

    active = _active(weekly)
    active_all = _active(weekly_all)

    player = (
        active.group_by("player_id")
        .agg(
            pl.col("player_display_name").last().alias("name"),
            pl.col("position").last().alias("pos"),
            pl.col("team").last().alias("team_2025"),
            pl.len().alias("games"),
            pl.col("fpts").sum().alias("fpts_total"),
            pl.col("fpts").mean().alias("ppg"),
            pl.col("targets").sum().alias("targets"),
            pl.col("receptions").sum().alias("receptions"),
            pl.col("receiving_yards").sum().alias("rec_yards"),
            pl.col("receiving_air_yards").sum().alias("air_yards"),
            pl.col(carries_col).sum().alias("carries"),
            pl.col("rushing_yards").sum().alias("rush_yards"),
            pl.col("target_share").mean().alias("target_share"),
            pl.col("air_yards_share").mean().alias("air_yards_share"),
            pl.col("wopr").mean().alias("wopr"),
        )
        .rename({"player_id": "gsis_id"})
    )

    # snap counts -> route proxy
    snaps = nfl.load_snap_counts([season])
    snaps_agg = (
        snaps.filter(pl.col("game_type") == "REG")
        .group_by("pfr_player_id")
        .agg(
            pl.col("offense_snaps").sum().alias("offense_snaps"),
            pl.col("offense_pct").mean().alias("offense_snap_pct"),
            pl.col("team").last().alias("snap_team"),
        )
    )

    from .ids import load_id_map

    id_map = load_id_map(cfg.path("raw"))
    gsis_pfr = id_map.filter(pl.col("gsis_id").is_not_null()).select(
        "gsis_id", "pfr_id", pl.col("sleeper_id").cast(pl.Utf8)
    ).unique(subset="gsis_id")

    player = player.join(gsis_pfr, on="gsis_id", how="left")
    player = player.join(snaps_agg, left_on="pfr_id", right_on="pfr_player_id", how="left")

    # proxy routes: offensive snaps x team dropback rate
    team_dbr = team_ctx.select("team", "dropback_rate")
    player = player.join(team_dbr, left_on="team_2025", right_on="team", how="left")
    player = player.with_columns(
        (pl.col("offense_snaps").fill_null(0) * pl.col("dropback_rate").fill_null(0.55))
        .alias("proxy_routes")
    ).with_columns(
        pl.when(pl.col("proxy_routes") > 50)
        .then(pl.col("targets") / pl.col("proxy_routes"))
        .otherwise(None)
        .alias("tprr"),
        pl.when(pl.col("proxy_routes") > 50)
        .then(pl.col("rec_yards") / pl.col("proxy_routes"))
        .otherwise(None)
        .alias("yprr"),
        pl.lit(True).alias("routes_proxy"),
    )

    player = player.join(hv, on="gsis_id", how="left").with_columns(
        pl.col("hv_touches").fill_null(0),
        pl.col("hv_carries").fill_null(0),
        pl.col("hv_targets").fill_null(0),
    )

    # NGS receiving: season-level separation as a soft signal (week 0 = season row)
    try:
        ngs = nfl.load_nextgen_stats(stat_type="receiving")
        ngs = ngs.filter((pl.col("season") == season) & (pl.col("week") == 0)).select(
            pl.col("player_gsis_id").alias("gsis_id"),
            pl.col("avg_separation"),
            pl.col("avg_cushion"),
        ).unique(subset="gsis_id")
        player = player.join(ngs, on="gsis_id", how="left")
    except Exception:
        player = player.with_columns(
            pl.lit(None, dtype=pl.Float64).alias("avg_separation"),
            pl.lit(None, dtype=pl.Float64).alias("avg_cushion"),
        )

    durability = build_durability(active_all, durability_seasons)
    player = player.join(durability, on="gsis_id", how="left")

    return player, team_ctx


def run(cfg) -> dict:
    processed = cfg.path("processed")
    player, team_ctx = build_usage(cfg)
    player.write_parquet(processed / "usage.parquet")
    team_ctx.write_parquet(processed / "team_context.parquet")
    return {
        "players": player.height,
        "with_sleeper_id": player.filter(pl.col("sleeper_id").is_not_null()).height,
        "teams": team_ctx.height,
    }

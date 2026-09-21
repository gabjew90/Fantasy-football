"""Expected fantasy points for RB/WR/TE: projected opportunity x value per touch.

The start/sit framework proposed 2026-09-21, built as numbers rather than a
checklist:

  1. OPPORTUNITY. Team carries, targets and goal-line carries come from a
     regression on the game's implied total and spread. The player's share of
     each is his current-season share blended toward his prior-season role,
     with the blend weight a tunable pseudo-count.
  2. VALUE PER TOUCH. A carry outside the 10, from the 6-10, inside the 5,
     and a target by position, each worth its mean fantasy points in the
     LEAGUE'S scoring, calibrated on the prior season's play-by-play.
  3. EFFICIENCY. Player talent (prior-season points over expected) times
     matchup (the opponent's points allowed over expected), each shrunk, the
     product capped at +/-10% so noisy efficiency cannot override role.
  4. RANGE. The share of expected points that comes from touchdowns, the
     framework's variance proxy.

Nothing here reads the future: `project()` is handed data strictly before the
week it predicts, and the calibration inputs are the previous season. Research
module -- nothing in the live manager calls it. It earns a place in the lineup
path only by beating the consensus it would replace, on the record.
"""

from __future__ import annotations

import numpy as np
import polars as pl

POSITIONS = ("RB", "WR", "TE")
ZONES = ("out10", "z6_10", "in5")
VOLUMES = ("carries", "targets", "in5", "z6_10")

# The framework's no-spreadsheet heuristic, verbatim and uncalibrated, so it
# can be scored beside the model it was offered as a shortcut for.
HEURISTIC = {"carries": 0.5, "i10": 1.3, "targets": 1.5}


def _zone() -> pl.Expr:
    y = pl.col("yardline_100")
    return (pl.when(y <= 5).then(pl.lit("in5"))
            .when(y <= 10).then(pl.lit("z6_10"))
            .otherwise(pl.lit("out10")))


def opportunities(pbp: pl.DataFrame) -> tuple[pl.DataFrame, pl.DataFrame]:
    """(carries, targets): one row per opportunity, regular season only.

    Kneels and scrambles are not carries in any sense the framework means --
    a scramble is a broken pass play, a kneel is the clock -- and two-point
    tries are not scored as yardage. The same definition feeds both the
    player's numerator and the team's denominator, so a share cannot be
    inflated by counting one and not the other.
    """
    base = pbp.filter((pl.col("season_type") == "REG")
                      & (pl.col("two_point_attempt").fill_null(0) != 1))
    common = [pl.col("season"), pl.col("week"), pl.col("game_id"),
              pl.col("posteam").alias("team"), pl.col("defteam").alias("opp"),
              _zone().alias("zone")]
    carries = (base.filter((pl.col("play_type") == "run")
                           & pl.col("rusher_player_id").is_not_null()
                           & (pl.col("qb_kneel").fill_null(0) != 1)
                           & (pl.col("qb_scramble").fill_null(0) != 1))
               .select(*common,
                       pl.col("rusher_player_id").alias("player_id"),
                       pl.col("rushing_yards").fill_null(0).alias("yards"),
                       pl.col("rush_touchdown").fill_null(0).alias("td"),
                       ((pl.col("fumble_lost").fill_null(0) == 1)
                        & (pl.col("fumbled_1_player_id") == pl.col("rusher_player_id")))
                       .fill_null(False).cast(pl.Int8).alias("fum")))
    targets = (base.filter((pl.col("play_type") == "pass")
                           & pl.col("receiver_player_id").is_not_null())
               .select(*common,
                       pl.col("receiver_player_id").alias("player_id"),
                       pl.col("complete_pass").fill_null(0).alias("catch"),
                       pl.col("receiving_yards").fill_null(0).alias("yards"),
                       (pl.col("pass_touchdown").fill_null(0)
                        * pl.col("complete_pass").fill_null(0)).alias("td"),
                       ((pl.col("fumble_lost").fill_null(0) == 1)
                        & (pl.col("fumbled_1_player_id") == pl.col("receiver_player_id")))
                       .fill_null(False).cast(pl.Int8).alias("fum")))
    return carries, targets


def positions(stats: pl.DataFrame) -> pl.DataFrame:
    """(season, player_id) -> RB/WR/TE. position_group folds fullbacks into RB."""
    col = "position_group" if "position_group" in stats.columns else "position"
    return (stats.filter(pl.col(col).is_in(POSITIONS))
            .group_by(["season", "player_id"])
            .agg(pl.col(col).mode().first().alias("pos")))


def fantasy_points(stats: pl.DataFrame, scoring: dict) -> pl.Expr:
    """Actual points from nflverse weekly stats in the league's scoring."""
    s = lambda k: float(scoring.get(k, 0.0))  # noqa: E731
    f = lambda c: pl.col(c).fill_null(0)  # noqa: E731
    return (s("rec") * f("receptions") + s("rec_yd") * f("receiving_yards")
            + s("rec_td") * f("receiving_tds") + s("rush_yd") * f("rushing_yards")
            + s("rush_td") * f("rushing_tds")
            + s("fum_lost") * (f("rushing_fumbles_lost") + f("receiving_fumbles_lost"))
            + s("pass_yd") * f("passing_yards") + s("pass_td") * f("passing_tds")
            + s("pass_int") * f("passing_interceptions"))


def _carry_pts(scoring):
    return (float(scoring.get("rush_yd", 0)) * pl.col("yards")
            + float(scoring.get("rush_td", 0)) * pl.col("td")
            + float(scoring.get("fum_lost", 0)) * pl.col("fum"))


def _target_pts(scoring):
    return (float(scoring.get("rec", 0)) * pl.col("catch")
            + float(scoring.get("rec_yd", 0)) * pl.col("yards")
            + float(scoring.get("rec_td", 0)) * pl.col("td")
            + float(scoring.get("fum_lost", 0)) * pl.col("fum"))


def touch_values(carries: pl.DataFrame, targets: pl.DataFrame,
                 pos: pl.DataFrame, scoring: dict) -> dict:
    """Mean fantasy points per touch, and the touchdown part of it.

    Carries by field zone, restricted to RB/WR/TE rushers so quarterback
    designed runs do not set the value of a running back's carry. Targets by
    position, because a running back's target is a checkdown and a wide
    receiver's is not -- the framework's single ~1.5 averages over that.
    """
    # Filtered HERE, not left to the caller: positions() happens to drop QBs
    # already, but a function whose correctness depends on how its input was
    # prepared elsewhere is one refactor away from pricing a sneak as a
    # running-back carry.
    pos = pos.filter(pl.col("pos").is_in(POSITIONS))
    c = carries.join(pos, on=["season", "player_id"], how="inner").with_columns(
        pts=_carry_pts(scoring),
        td_pts=float(scoring.get("rush_td", 0)) * pl.col("td"))
    t = targets.join(pos, on=["season", "player_id"], how="inner").with_columns(
        pts=_target_pts(scoring),
        td_pts=float(scoring.get("rec_td", 0)) * pl.col("td"))
    out = {"carry": {}, "target": {}}
    for r in c.group_by("zone").agg(pl.col("pts").mean(), pl.col("td_pts").mean(),
                                    pl.len().alias("n")).iter_rows(named=True):
        out["carry"][r["zone"]] = {"pts": r["pts"], "td_pts": r["td_pts"], "n": r["n"]}
    for r in t.group_by("pos").agg(pl.col("pts").mean(), pl.col("td_pts").mean(),
                                   pl.len().alias("n")).iter_rows(named=True):
        out["target"][r["pos"]] = {"pts": r["pts"], "td_pts": r["td_pts"], "n": r["n"]}
    return out


def team_volume(carries: pl.DataFrame, targets: pl.DataFrame) -> pl.DataFrame:
    """(season, week, team) -> carries, targets, in5, z6_10."""
    c = carries.group_by(["season", "week", "team"]).agg(
        pl.len().alias("carries"),
        (pl.col("zone") == "in5").sum().alias("in5"),
        (pl.col("zone") == "z6_10").sum().alias("z6_10"))
    t = targets.group_by(["season", "week", "team"]).agg(pl.len().alias("targets"))
    return c.join(t, on=["season", "week", "team"], how="full", coalesce=True).fill_null(0)


def player_games(carries: pl.DataFrame, targets: pl.DataFrame) -> pl.DataFrame:
    """(season, week, team, player_id) -> carries, in5, z6_10, targets."""
    c = carries.group_by(["season", "week", "team", "player_id"]).agg(
        pl.len().alias("carries"),
        (pl.col("zone") == "in5").sum().alias("in5"),
        (pl.col("zone") == "z6_10").sum().alias("z6_10"))
    t = targets.group_by(["season", "week", "team", "player_id"]).agg(
        pl.len().alias("targets"))
    return (c.join(t, on=["season", "week", "team", "player_id"], how="full",
                   coalesce=True).fill_null(0))


def team_lines(schedule: pl.DataFrame) -> pl.DataFrame:
    """(season, week, team) -> implied team total and spread from its side.

    nflverse `spread_line` is positive when the HOME team is favoured, so the
    home side's implied total is (total + spread) / 2. `tspread` is positive
    for the favourite on either side.
    """
    s = schedule.filter(pl.col("game_type") == "REG").filter(
        pl.col("spread_line").is_not_null() & pl.col("total_line").is_not_null())
    home = s.select("season", "week", "game_id", pl.col("home_team").alias("team"),
                    pl.col("away_team").alias("opp"),
                    ((pl.col("total_line") + pl.col("spread_line")) / 2).alias("implied"),
                    pl.col("spread_line").alias("tspread"))
    away = s.select("season", "week", "game_id", pl.col("away_team").alias("team"),
                    pl.col("home_team").alias("opp"),
                    ((pl.col("total_line") - pl.col("spread_line")) / 2).alias("implied"),
                    (-pl.col("spread_line")).alias("tspread"))
    return pl.concat([home, away])


def fit_volume(tv: pl.DataFrame, lines: pl.DataFrame) -> dict:
    """OLS of each team volume on [1, implied total, spread]: step 1's
    'favourites run more, underdogs drop back more', as coefficients."""
    d = tv.join(lines, on=["season", "week", "team"], how="inner")
    X = np.column_stack([np.ones(d.height), d["implied"].to_numpy(), d["tspread"].to_numpy()])
    return {v: np.linalg.lstsq(X, d[v].to_numpy().astype(float), rcond=None)[0].tolist()
            for v in VOLUMES} | {"n": d.height}


def predict_volume(lines: pl.DataFrame, coefs: dict) -> pl.DataFrame:
    return lines.with_columns(**{
        f"p_{v}": (coefs[v][0] + coefs[v][1] * pl.col("implied")
                   + coefs[v][2] * pl.col("tspread")).clip(lower_bound=0.0)
        for v in VOLUMES})


def _shares(pg: pl.DataFrame, tv: pl.DataFrame, played: pl.DataFrame) -> pl.DataFrame:
    """Per player over the given games: opportunities and the team's
    opportunities in the games HE PLAYED, so a week out injured does not
    dilute his share."""
    keys = ["season", "week", "team", "player_id"]
    team = tv.rename({v: f"team_{v}" for v in VOLUMES})
    d = (played.select(keys)
         .join(team, on=["season", "week", "team"], how="inner")
         .join(pg.select(*keys, *VOLUMES), on=keys, how="left")
         .with_columns(*[pl.col(v).fill_null(0) for v in VOLUMES]))
    return d.group_by("player_id").agg(
        pl.col("team").sort_by("week").last().alias("team"),
        pl.col("team").mode().first().alias("main_team"),
        *[pl.col(v).sum() for v in VOLUMES],
        *[pl.col(f"team_{v}").sum() for v in VOLUMES],
        pl.len().alias("games"))


def _blend(cur: pl.Expr, n_cur: pl.Expr, pri: pl.Expr, k: pl.Expr) -> pl.Expr:
    """(n_cur * cur + k * pri) / (n_cur + k), with either side allowed missing."""
    return (pl.when(cur.is_null() | (n_cur <= 0)).then(pri)
            .when(pri.is_null()).then(cur)
            .otherwise((n_cur * cur + k * pri) / (n_cur + k)))


def project(*, week_lines: pl.DataFrame, coefs: dict, values: dict,
            pg_cur: pl.DataFrame, tv_cur: pl.DataFrame, played_cur: pl.DataFrame,
            pg_pri: pl.DataFrame, tv_pri: pl.DataFrame, played_pri: pl.DataFrame,
            pos: pl.DataFrame, k: float = 64.0, window: int | None = None,
            talent: pl.DataFrame | None = None, matchup: pl.DataFrame | None = None,
            cap: float = 0.10) -> pl.DataFrame:
    """Expected points for every player with a current or prior role.

    `window` limits the current-season evidence to the last N weeks played --
    the framework's 'lean on the last 3 to 4 weeks' -- and `k` is the prior's
    weight in team-opportunity units (one game is ~26 team carries, ~34 team
    targets). Small k and a short window is the framework's recency; large k
    trusts last season's role.
    """
    if window is not None and played_cur.height:
        last = played_cur.group_by("player_id").agg(pl.col("week").sort().tail(window))
        played_cur = played_cur.join(last.explode("week"), on=["player_id", "week"], how="inner")

    cur = _shares(pg_cur, tv_cur, played_cur) if played_cur.height else None
    pri = _shares(pg_pri, tv_pri, played_pri)

    rates = {"carries": "team_carries", "targets": "team_targets",
             "in5": "team_in5", "z6_10": "team_z6_10"}
    pri_s = pri.select(
        "player_id", pl.col("main_team").alias("pri_team"),
        *[(pl.col(v) / pl.col(t)).alias(f"pri_{v}") for v, t in rates.items()],
        *[pl.col(t).alias(f"pri_n_{v}") for v, t in rates.items()])
    if cur is not None:
        cur_s = cur.select(
            "player_id", pl.col("team").alias("cur_team"),
            *[(pl.col(v) / pl.col(t)).alias(f"cur_{v}") for v, t in rates.items()],
            *[pl.col(t).alias(f"cur_n_{v}") for v, t in rates.items()])
        s = cur_s.join(pri_s, on="player_id", how="full", coalesce=True)
    else:
        s = pri_s.with_columns(pl.lit(None, dtype=pl.Utf8).alias("cur_team"),
                               *[pl.lit(None, dtype=pl.Float64).alias(f"cur_{v}") for v in rates],
                               *[pl.lit(0.0).alias(f"cur_n_{v}") for v in rates])
    s = s.with_columns(
        pl.coalesce("cur_team", "pri_team").alias("team"),
        # A role carried over from ANOTHER team is a weak prior about the role
        # here, so it counts half -- the same convention the props engine uses.
        pl.when(pl.col("pri_team").is_not_null() & pl.col("cur_team").is_not_null()
                & (pl.col("pri_team") != pl.col("cur_team")))
        .then(pl.lit(k / 2)).otherwise(pl.lit(k)).alias("_k"),
        *[pl.col(f"cur_n_{v}").fill_null(0.0) for v in rates])
    s = s.with_columns(
        _blend(pl.col("cur_carries"), pl.col("cur_n_carries"), pl.col("pri_carries"), pl.col("_k")).alias("s_carries"),
        _blend(pl.col("cur_targets"), pl.col("cur_n_targets"), pl.col("pri_targets"), pl.col("_k")).alias("s_targets"))
    # Goal-line shares: the sample is tiny, so the prior is last season's zone
    # share where it rests on real volume, else the player's blended carry
    # share -- his role, which is the framework's instruction.
    for z in ("in5", "z6_10"):
        pri_z = (pl.when(pl.col(f"pri_n_{z}").fill_null(0) >= 10)
                 .then(pl.col(f"pri_{z}")).otherwise(pl.col("s_carries")))
        s = s.with_columns(_blend(pl.col(f"cur_{z}"), pl.col(f"cur_n_{z}"), pri_z,
                                  pl.col("_k")).alias(f"s_{z}"))

    vol = predict_volume(week_lines, coefs).select("team", "opp", "game_id", "implied",
                                                  "tspread", *[f"p_{v}" for v in VOLUMES])
    d = (s.join(vol, on="team", how="inner")
         .join(pos.select("player_id", "pos"), on="player_id", how="inner")
         .with_columns(*[pl.col(f"s_{v}").fill_null(0.0).clip(0.0, 1.0) for v in VOLUMES]))
    d = d.with_columns(
        (pl.col("s_carries") * pl.col("p_carries")).alias("x_carries"),
        (pl.col("s_in5") * pl.col("p_in5")).alias("x_in5"),
        (pl.col("s_z6_10") * pl.col("p_z6_10")).alias("x_z6_10"),
        (pl.col("s_targets") * pl.col("p_targets")).alias("x_targets"))
    # Zone carries are estimated independently of total carries, so on a
    # small sample the goal-line pieces can exceed the whole. Outside-10 is
    # what is left, never negative.
    d = d.with_columns((pl.col("x_carries") - pl.col("x_in5") - pl.col("x_z6_10"))
                       .clip(lower_bound=0.0).alias("x_out10"))

    cv, tvv = values["carry"], values["target"]
    tgt_pts = pl.col("pos").replace_strict({p: tvv[p]["pts"] for p in tvv}, default=0.0)
    tgt_td = pl.col("pos").replace_strict({p: tvv[p]["td_pts"] for p in tvv}, default=0.0)
    d = d.with_columns(
        (pl.col("x_out10") * cv["out10"]["pts"] + pl.col("x_z6_10") * cv["z6_10"]["pts"]
         + pl.col("x_in5") * cv["in5"]["pts"] + pl.col("x_targets") * tgt_pts).alias("xfp_base"),
        (pl.col("x_out10") * cv["out10"]["td_pts"] + pl.col("x_z6_10") * cv["z6_10"]["td_pts"]
         + pl.col("x_in5") * cv["in5"]["td_pts"] + pl.col("x_targets") * tgt_td).alias("xfp_td"),
        (HEURISTIC["carries"] * pl.col("x_carries")
         + HEURISTIC["i10"] * (pl.col("x_in5") + pl.col("x_z6_10"))
         + HEURISTIC["targets"] * pl.col("x_targets")).alias("heuristic"))

    d = d.with_columns(pl.lit(1.0).alias("talent"), pl.lit(1.0).alias("matchup"))
    if talent is not None:
        d = (d.drop("talent").join(talent.select("player_id", "talent"), on="player_id", how="left")
             .with_columns(pl.col("talent").fill_null(1.0)))
    if matchup is not None:
        d = (d.drop("matchup").join(matchup.select("opp", "pos", "matchup"),
                                    on=["opp", "pos"], how="left")
             .with_columns(pl.col("matchup").fill_null(1.0)))
    # The cap is on the PRODUCT: talent and matchup together may move the
    # projection no more than +/-10%, so a noisy efficiency read cannot
    # override the role that steps 1 and 2 established.
    d = d.with_columns((pl.col("talent") * pl.col("matchup"))
                       .clip(1.0 - cap, 1.0 + cap).alias("eff_mult"))
    return d.with_columns(
        (pl.col("xfp_base") * pl.col("eff_mult")).alias("xfp"),
        (pl.col("xfp_td") / pl.col("xfp_base")).fill_nan(0.0).alias("td_share"))


def efficiency(*, pg: pl.DataFrame, stats: pl.DataFrame, pos: pl.DataFrame,
               values: dict, scoring: dict, k_player: float = 150.0,
               k_matchup: float = 400.0) -> tuple[pl.DataFrame, pl.DataFrame]:
    """Step 3's inputs, from games strictly before the week predicted.

    talent  = a player's actual points over the points his opportunities were
              worth, shrunk toward 1 by his opportunity count (the framework's
              '100+ carries' threshold becomes a pseudo-count of 150);
    matchup = the same ratio for everything a defence allowed to a position.
    Both are ratios, so they carry efficiency and nothing about volume --
    volume is steps 1 and 2 and must not be counted twice.
    """
    cv, tvv = values["carry"], values["target"]
    tgt_pts = pl.col("pos").replace_strict({p: tvv[p]["pts"] for p in tvv}, default=0.0)
    exp = (pg.join(pos, on=["season", "player_id"], how="inner")
           .with_columns(((pl.col("carries") - pl.col("in5") - pl.col("z6_10")).clip(lower_bound=0)
                          * cv["out10"]["pts"] + pl.col("z6_10") * cv["z6_10"]["pts"]
                          + pl.col("in5") * cv["in5"]["pts"]
                          + pl.col("targets") * tgt_pts).alias("exp"),
                         (pl.col("carries") + pl.col("targets")).alias("opps")))
    act = stats.select("season", "week", "player_id", pl.col("opponent_team").alias("opp"),
                       fantasy_points(stats, scoring).alias("act"))
    d = exp.join(act, on=["season", "week", "player_id"], how="inner")
    talent = (d.group_by("player_id")
              .agg(pl.col("act").sum(), pl.col("exp").sum(), pl.col("opps").sum())
              .with_columns((1 + ((pl.col("act") / pl.col("exp")) - 1)
                             * pl.col("opps") / (pl.col("opps") + k_player))
                            .fill_nan(1.0).alias("talent")))
    matchup = (d.group_by(["opp", "pos"])
               .agg(pl.col("act").sum(), pl.col("exp").sum(), pl.col("opps").sum())
               .with_columns((1 + ((pl.col("act") / pl.col("exp")) - 1)
                              * pl.col("opps") / (pl.col("opps") + k_matchup))
                             .fill_nan(1.0).alias("matchup")))
    return talent.select("player_id", "talent"), matchup.select("opp", "pos", "matchup")

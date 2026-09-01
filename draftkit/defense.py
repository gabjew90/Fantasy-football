"""Defense quality: fantasy points allowed by position, in league scoring.

Closes two gaps at once (post-v2 item 2): the lineup brief's matchup
adjustment had no data behind it (matchup_mult was always fed 1.0), and the
trade radar's playoff-schedule arbitrage could only name opponents.

Shrunk hard toward the league mean early — weight = games/(games + k) with k
from inseason.matchup_shrink_weeks — so week-3 data barely moves anything
and the metric becomes meaningful around week 6. Unavailable or too-early
data returns None so callers print the DATA MISSING banner rather than
applying a null adjustment.
"""

from __future__ import annotations

import logging

import polars as pl

log = logging.getLogger("draftkit")

POSITIONS = ("QB", "RB", "WR", "TE")
MIN_WEEKS = 2  # below this there is nothing to shrink toward anything


def points_allowed(season: int, scoring: dict[str, float],
                   through_week: int | None = None) -> pl.DataFrame | None:
    """defense (team) x position -> fantasy points allowed per game.

    Uses nflverse weekly player stats scored with the league's own weights,
    attributing each player's output to his OPPONENT's defense.
    """
    try:
        import nflreadpy as nfl
        wk = nfl.load_player_stats([int(season)])
    except Exception as e:  # noqa: BLE001
        log.warning("defense: nflverse weekly unavailable (%s)", e.__class__.__name__)
        return None
    if wk is None or len(wk) == 0:
        return None
    wk = wk.filter(pl.col("season_type") == "REG")
    if through_week:
        wk = wk.filter(pl.col("week") <= int(through_week))
    if len(wk) == 0:
        return None

    from .dataset import fantasy_points_expr
    from .seasondata import _norm_team

    have = set(wk.columns)
    need = {"opponent_team", "position", "week"}
    if not need.issubset(have):
        log.warning("defense: weekly frame missing %s", need - have)
        return None

    wk = wk.with_columns(fantasy_points_expr(scoring)).filter(
        pl.col("position").is_in(list(POSITIONS))
        & pl.col("opponent_team").is_not_null()
    )
    if len(wk) == 0:
        return None
    per_game = (
        wk.group_by(["opponent_team", "position", "week"])
        .agg(pl.col("fpts").sum().alias("allowed"))
        .group_by(["opponent_team", "position"])
        .agg(pl.col("allowed").mean().alias("allowed_pg"),
             pl.col("week").n_unique().alias("games"))
        .rename({"opponent_team": "defense", "position": "pos"})
    )
    return per_game.with_columns(
        pl.col("defense").map_elements(_norm_team, return_dtype=pl.Utf8).alias("defense")
    )


def allowed_ratio(pa: pl.DataFrame | None, defense: str, pos: str,
                  shrink_k: float) -> float | None:
    """Opponent's points-allowed vs league average at this position, shrunk.

    1.0 = league average. >1 means this defense gives up more than average.
    None when the metric is not yet meaningful (caller degrades loudly).
    """
    if pa is None or len(pa) == 0:
        return None
    at_pos = pa.filter(pl.col("pos") == pos)
    row = at_pos.filter(pl.col("defense") == defense)
    if len(at_pos) < 8 or len(row) == 0:
        return None
    games = int(row["games"][0])
    if games < MIN_WEEKS:
        return None
    league_avg = float(at_pos["allowed_pg"].mean())
    if league_avg <= 0:
        return None
    raw = float(row["allowed_pg"][0]) / league_avg
    w = games / (games + float(shrink_k))     # same convention as weekly.py
    return 1.0 + (raw - 1.0) * w


def schedule_strength(pa: pl.DataFrame | None, schedule, team: str, pos: str,
                      weeks: tuple[int, ...], shrink_k: float) -> tuple[float | None, str]:
    """Mean opponent points-allowed ratio over `weeks` + the opponent names.

    Replaces the trade radar's qualitative "name the opponents" placeholder;
    the names are kept alongside the number.
    """
    try:
        rows = schedule.filter(
            (pl.col("team") == team) & pl.col("week").is_in(list(weeks))
        ).sort("week")
    except Exception:  # noqa: BLE001
        return None, ""
    opps = [(int(r["week"]), r["opp"]) for r in rows.iter_rows(named=True)]
    label = "; ".join(f"wk{w} vs {o}" for w, o in opps)
    if not opps:
        return None, "bye-heavy or unscheduled"
    ratios = [r for r in (allowed_ratio(pa, o, pos, shrink_k) for _w, o in opps)
              if r is not None]
    if not ratios:
        return None, label
    return sum(ratios) / len(ratios), label

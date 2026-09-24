"""The one fantasy scoring function.

Every fantasy point in the repo is computed here, from the league's own
scoring block (`expected.scoring` in leagues/<name>.yaml, Sleeper-style keys:
rec, rec_yd, rush_td, pass_int, fum_lost, ...). Two shapes of input exist and
both are served:

  score(stats, scoring)        a Sleeper-keyed stat dict: projections from
                               Sleeper / ESPN / FantasyPros / the sheet, and
                               Sleeper's weekly actuals
  nflverse_weights(scoring)    the same scoring translated to nflverse weekly
                               stat columns, for vectorised play-by-play and
                               player-stats frames (fantasy_points_expr)

It replaced the copies in draftkit.seasondata.score_projection (now an alias),
the inline sums in draftkit.consensus.score_rows and
scripts/projection_backtest.py, manager.consensus._score, and draftkit.dataset's
column map. Two remain on an allowlist that may only shrink: manager.xfp
(deleted in step 6) and the props engine's parse_scoring (props adopts core
last). tests/test_core_guardrails.py fails on any new copy.
"""

from __future__ import annotations

# Omnibeta's verified settings (Sleeper scoring_settings, 2026-08-19) in nflverse
# column form: the base a league block is laid over, so keys a league does not
# mention (2-point conversions, special-teams TDs) keep their standard values.
NFLVERSE_BASE: dict[str, float] = {
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

# league-yaml scoring keys (Sleeper-style) -> nflverse weekly stat columns
NFLVERSE_COLUMN: dict[str, str] = {
    "pass_yd": "passing_yards", "pass_td": "passing_tds",
    "pass_int": "passing_interceptions", "rush_yd": "rushing_yards",
    "rush_td": "rushing_tds", "rec": "receptions", "rec_yd": "receiving_yards",
    "rec_td": "receiving_tds",
    "pass_2pt": "passing_2pt_conversions", "rush_2pt": "rushing_2pt_conversions",
    "rec_2pt": "receiving_2pt_conversions", "st_td": "special_teams_tds",
}
# fum_lost has no single column: it maps to all three nflverse fumble columns
FUMBLE_COLUMNS = ("sack_fumbles_lost", "rushing_fumbles_lost", "receiving_fumbles_lost")


class ScoringMissing(ValueError):
    """The league yaml carries no scoring block."""


def league_scoring(cfg, required: bool = True) -> dict[str, float]:
    """The league's scoring block, Sleeper-style keys.

    Read from `scoring:` or `expected.scoring:` (the latter is what `verify`
    diffs against the live league). A missing block is an error, never a
    silent default: CLAUDE.md -- league facts live in leagues/<name>.yaml,
    and a wrong scoring system does not fail, it re-ranks every player.

    `required=False` returns {} instead of raising. It exists only to keep the
    in-season manager's historic behaviour during the consolidation (its
    consensus reported every source as unpriced rather than raising); it is
    removed when the manager moves onto fantasy/.
    """
    block = None
    if cfg is not None:
        block = cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring")
    if not block:
        if not required:
            return {}
        raise ScoringMissing(
            "league yaml carries no scoring (add scoring: or expected.scoring); "
            "refusing a silent default")
    return {str(k): float(v) for k, v in block.items()}


def score(stats: dict | None, scoring: dict) -> float:
    """Points for one Sleeper-keyed stat line under `scoring`.

    Only keys the league scores count; a stat the league does not score (or a
    None value, which Sleeper uses for 'not projected') contributes nothing.
    """
    return sum(float(scoring[k]) * float(v)
               for k, v in (stats or {}).items() if k in scoring and v is not None)


def nflverse_weights(scoring: dict, base: dict[str, float] | None = None) -> dict[str, float]:
    """Sleeper-style scoring keys -> nflverse weekly stat column weights.

    The keys Sleeper uses (`pass_yd`, `sack`, `def_td`, `bonus_rec_te`, ...)
    are not nflverse column names. Keys nflverse has no column for (kicking,
    team defense, distance bonuses such as Keefamania's pass_td_40p) are
    dropped: a documented approximation, stated in the league yaml, not a
    silent one.
    """
    out = dict(base or {})
    for k, v in (scoring or {}).items():
        col = NFLVERSE_COLUMN.get(k)
        if col:
            out[col] = float(v)
        elif k == "fum_lost":
            for c in FUMBLE_COLUMNS:
                out[c] = float(v)
    return out


def unmodelled_keys(scoring: dict) -> list[str]:
    """League scoring keys the nflverse translation drops, so a report can name
    them rather than let a bonus disappear quietly."""
    return sorted(k for k in (scoring or {})
                  if k not in NFLVERSE_COLUMN and k != "fum_lost")


def fantasy_points_expr(weights: dict[str, float] | None = None):
    """Polars expression: points from nflverse weekly columns, aliased `fpts`.
    `weights` are nflverse column weights (see nflverse_weights)."""
    import polars as pl
    expr = pl.lit(0.0)
    for col, w in (weights or NFLVERSE_BASE).items():
        expr = expr + pl.col(col).fill_null(0.0).cast(pl.Float64) * w
    return expr.alias("fpts")

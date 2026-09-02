"""Role gating for the usage model (projection overhaul, usage-side fix 1).

The stats half of the blend projects last season's per-game rate forward.
A rate cannot say "he will not start": Jameis Winston's 22 PPG over two
2025 starts became ~230 points on the board while every expert had him
near 10, because he is a QB2 in 2026. The fix is on the usage side, not
the market side -- swapping the market term (item 1) leaves the blend at
roughly 0.4 x 200 + 0.6 x 10.

Rule (one rule for every position):
  * Sleeper's depth chart gives each player an order at his position
    (players_nfl.json: depth_chart_order). A position has `starters` slots
    per team: QB 1, RB 2, WR 3, TE 1 (config projections.role_gate).
  * A player listed BEHIND the starters is projected on the share of the
    season he can expect to hold a starting role: the chance that at least
    (his depth beyond the starters) of the starters ahead of him are out in
    a given week, with each starter's weekly absence at the position's
    ex-ante base rate (bench.ABSENT_WEEKS, seasons 2019-2025). No bye term:
    this is real-world starts, not lineup replacement.
      QB2 0.15 · RB3 0.33 · RB4 0.03 · WR4 0.39 · WR5 0.07 · TE2 0.17
  * The gate applies to the MODEL term only (the market term already
    reflects whatever role the market believes), and only when the market
    agrees he is a backup: his ECR/ADP rank within position must be past
    teams x starters. Two independent sources have to say "backup" before a
    projection is cut -- a depth-chart error on a real starter cannot crush
    him on its own.
  * Unknown depth order (about 20% of rostered players) -> no gate, share 1.
  * WR is NOT gated. Sleeper's receiver chart is three sub-charts (LWR, RWR,
    SWR) with their own orders, plus unslotted receivers numbered 6-11, so
    "order" is not an overall depth: Davante Adams reads RWR 2 and Travis
    Hunter SWR 4 (2026-09-02). A gate on that would cut real starters and
    spare real backups. QB, RB and TE charts are single ordered lists; the
    gate also requires the chart position to match the fantasy position, so
    a tight end filed under the RB chart (an H-back) is left alone.
"""

from __future__ import annotations

import json
from math import comb
from pathlib import Path

import polars as pl

from .bench import ABSENT_WEEKS, FANTASY_WEEKS

STARTERS = {"QB": 1, "RB": 2, "WR": 3, "TE": 1}
GATED = ("QB", "RB", "TE")          # positions whose depth chart is one ordered list


def role_share(pos: str, order: int | None, starters: dict | None = None) -> float:
    """Expected share of weeks a player at depth `order` holds a starting role."""
    st = (starters or STARTERS).get(pos)
    if st is None or order is None or pos not in ABSENT_WEEKS or pos not in GATED:
        return 1.0
    order = int(order)
    if order <= st:
        return 1.0
    need = order - st                      # this many starters must be out
    if need > st:
        return 0.0
    q = min(1.0, ABSENT_WEEKS[pos] / FANTASY_WEEKS)
    return sum(comb(st, j) * q ** j * (1 - q) ** (st - j) for j in range(need, st + 1))


def depth_orders(raw_dir: Path) -> pl.DataFrame | None:
    """sleeper_id -> depth_chart_order from the cached Sleeper player universe.
    None when the cache is absent (the caller says so and skips the gate)."""
    p = Path(raw_dir) / "players_nfl.json"
    if not p.exists():
        return None
    data = json.loads(p.read_text(encoding="utf-8"))
    rows = [{"sleeper_id": str(pid), "depth_order": rec.get("depth_chart_order"),
             "depth_pos": rec.get("depth_chart_position")}
            for pid, rec in data.items() if isinstance(rec, dict)]
    return pl.DataFrame(rows).with_columns(pl.col("depth_order").cast(pl.Int64, strict=False))


def apply_role_gate(df: pl.DataFrame, depth: pl.DataFrame, teams: int,
                    starters: dict | None = None) -> pl.DataFrame:
    """Add role_share and scale proj_model_pts by it where BOTH the depth
    chart and the market rank say backup. df needs sleeper_id, pos, ecr,
    adp, proj_model_pts."""
    st = starters or STARTERS
    dcols = ["sleeper_id", "depth_order"] + (["depth_pos"] if "depth_pos" in depth.columns else [])
    d = df.join(depth.select(dcols), on="sleeper_id", how="left")
    if "depth_pos" not in d.columns:
        d = d.with_columns(pl.col("pos").alias("depth_pos"))
    d = d.with_columns(
        pl.coalesce(pl.col("ecr"), pl.col("adp")).rank(method="ordinal").over("pos").alias("_mkt_pos_rank"))
    # the chart position must be the fantasy position: a TE filed under the
    # RB chart, or a WR anywhere (see module docstring), is not gated
    shares = [role_share(pos, o, st) if (dp is None or dp == pos) else 1.0
              for pos, o, dp in zip(d["pos"].to_list(), d["depth_order"].to_list(), d["depth_pos"].to_list())]
    d = d.with_columns(pl.Series("role_share", shares, dtype=pl.Float64))
    starters_expr = pl.col("pos").replace_strict(st, default=None, return_dtype=pl.Int64)
    # No ECR and no ADP is not "unknown": the market has him outside every
    # list it publishes, which is the strongest backup signal there is
    # (Rattler and Mills reached the board through the no-market floor and
    # were the first players this gate was built for).
    market_backup = (pl.col("_mkt_pos_rank").is_null()
                     | (pl.col("_mkt_pos_rank") > starters_expr * teams))
    gate = (pl.col("role_share") < 1.0) & market_backup
    d = d.with_columns(
        pl.when(gate).then(pl.col("role_share")).otherwise(1.0).alias("role_share"),
        pl.when(gate & pl.col("proj_model_pts").is_not_null())
        .then(pl.col("proj_model_pts") * pl.col("role_share"))
        .otherwise(pl.col("proj_model_pts")).alias("proj_model_pts"),
    )
    return d.drop("_mkt_pos_rank", "depth_order", "depth_pos")

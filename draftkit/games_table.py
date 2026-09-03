"""The positional missed-games table, applied through the games convention
(plan 2026-09-02 A2; DECISIONS #31).

Every source's line is a 17-game total scaled once by `projections.games`
(16). This module makes that scale a per-row expression:

    games_row = games - (missed[pos, band] - pooled_mean)

INVARIANT (differential mode). The pooled mean is subtracted, so the
uniform part of absence cancels and only the cross-cell DIFFERENCES move
the board: a first-band RB (misses 2.8) gains ~0.4 games on the 16-game
basis, a fourth-band RB (misses 4.4) loses ~1.2, and the level everyone
downstream assumes (briefs divide by 16, VORP is a within-position
difference) is unchanged on average. The band comes from the PROVISIONAL
MARKET RANK computed before scaling (rank of coalesce(ecr, adp) within the
position), never from the projection being scaled -- that would be
circular. A player off the table (no rank, K/DEF, a rank past the deepest
band) gets the uniform `games`, stated rather than extrapolated. A source
that already discounts games must never pass through this scale (see
external.SOURCE_GAMES_CONVENTION); the 2026 sources do not.

Absent table -> DATA MISSING banner and uniform games; nothing invented.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl


def load(cfg) -> dict | None:
    """The table dict, or None (with a banner) when disabled or missing."""
    gt = (cfg.get("projections") or {}).get("games_table") or {}
    if not gt.get("enabled", False):
        return None
    mode = str(gt.get("mode", "differential"))
    if mode != "differential":
        raise ValueError(f"games_table.mode must be 'differential', got {mode!r}")
    path = Path(cfg.root) / str(gt.get("path", "data/processed/absence_bands.json"))
    if not path.exists():
        print(f"  GAMES TABLE: DATA MISSING ({path}) -- uniform games", file=sys.stderr)
        return None
    try:
        t = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(t.get("bands"), dict) and t.get("pooled_mean") is not None
    except Exception as e:  # noqa: BLE001
        print(f"  GAMES TABLE: DATA MISSING ({path.name} unreadable: {e}) -- uniform games", file=sys.stderr)
        return None
    return t


def cells(table: dict) -> list[tuple[str, int, int, float]]:
    """[(pos, lo, hi, mean_missed)] from the table's bands."""
    out = []
    for pos, bands in table["bands"].items():
        for label, c in bands.items():
            lo, hi = (int(x) for x in label.split("-"))
            out.append((pos, lo, hi, float(c["mean"])))
    return out


def missed_expr(table: dict, pos_col: str = "pos", rank_col: str = "_r") -> pl.Expr:
    """Per-row mean missed games for (pos, provisional rank); null off-table."""
    expr = pl.lit(None, dtype=pl.Float64)
    for pos, lo, hi, m in cells(table):
        expr = pl.when((pl.col(pos_col) == pos) & pl.col(rank_col).is_between(lo, hi)).then(pl.lit(m)).otherwise(expr)
    return expr


def games_expr(games: float, table: dict | None, pos_col: str = "pos", rank_col: str = "_r") -> pl.Expr:
    """The per-row games scale: `games` when the table is off or the row is
    off-table, else games - (missed - pooled_mean)."""
    if table is None:
        return pl.lit(float(games))
    missed = missed_expr(table, pos_col, rank_col)
    return pl.when(missed.is_not_null()).then(pl.lit(float(games)) - (missed - float(table["pooled_mean"]))) \
             .otherwise(pl.lit(float(games)))

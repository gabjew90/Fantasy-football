"""The games-table gate (plan 2026-09-02 A2; DECISIONS #31).

Applies a LEAK-FREE per-pair absence table to the projection backtest's row
export and writes twin columns (`blend_gt`, `lines_gt`) that are non-null
exactly where the base arm is, so the common set does not shrink. The
provisional rank is the ADP rank within (pair, pos) -- the same rule the
board uses, never the projection. Then scripts/source_gate.py judges
`blend_gt` against `blend` (and `lines_gt` against `lines`) on accuracy and
on the actual-points outcome replay.

    venv\\Scripts\\python.exe scripts\\games_table_gate.py --leagues keefamania,omnibeta
    venv\\Scripts\\python.exe scripts\\source_gate.py --rows reports/projection_backtest.keefamania.gt.rows.csv,reports/projection_backtest.omnibeta.gt.rows.csv --candidate blend_gt --rivals blend --out reports/games_table_gate.md
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit import games_table as GT  # noqa: E402

GAMES = 16.0
TABLE_FOR_PAIR = {"2023->2024": "absence_bands_through_2023.json", "2024->2025": "absence_bands_through_2024.json"}


def apply_table(rows: pl.DataFrame, tables: dict[str, dict], arms=("blend", "lines")) -> pl.DataFrame:
    """rows: the backtest export (pair, pos, adp, arms...). Adds `<arm>_gt` =
    arm x games_row / GAMES with games_row from that pair's table."""
    parts = []
    for pair, sub in rows.group_by("pair", maintain_order=True):
        pair = pair[0] if isinstance(pair, tuple) else pair
        table = tables.get(pair)
        sub = sub.with_columns(pl.col("adp").rank(method="ordinal").over("pos").alias("_r"))
        sub = sub.with_columns(GT.games_expr(GAMES, table).alias("_games"))
        sub = sub.with_columns(*[(pl.col(a) * pl.col("_games") / GAMES).alias(f"{a}_gt") for a in arms if a in sub.columns])
        # RB-ONLY ARM (pre-registered 2026-09-04). The pooled gate FAILED
        # (DECISIONS #31) while the games table improved RB MAE in all four
        # (league, pair) cells and worsened QB/WR/TE. `<arm>_gt_rb` applies the
        # table to running backs alone and leaves every other position on the
        # base arm, so source_gate can judge exactly that hypothesis with the
        # same two halves and no change to its verdict code:
        #   source_gate.py --rows <gt rows> --candidate blend_gt_rb --rivals blend
        sub = sub.with_columns(*[
            pl.when(pl.col("pos") == "RB").then(pl.col(f"{a}_gt")).otherwise(pl.col(a)).alias(f"{a}_gt_rb")
            for a in arms if a in sub.columns])
        parts.append(sub.drop("_r", "_games"))
    return pl.concat(parts, how="vertical_relaxed")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", default="keefamania,omnibeta")
    ap.add_argument("--tables-dir", default=str(ROOT / "data" / "processed" / "backtest"))
    a = ap.parse_args()
    tables = {}
    for pair, fname in TABLE_FOR_PAIR.items():
        p = Path(a.tables_dir) / fname
        if not p.exists():
            raise SystemExit(f"{p} missing: derive_absence_bands.py --through <year> first")
        tables[pair] = json.loads(p.read_text(encoding="utf-8"))
    for lg in a.leagues.split(","):
        src = ROOT / "reports" / f"projection_backtest.{lg}.rows.csv"
        rows = pl.read_csv(src, infer_schema_length=10000)
        out = apply_table(rows, tables)
        dst = src.with_name(f"projection_backtest.{lg}.gt.rows.csv")
        out.write_csv(dst)
        moved = out.filter((pl.col("blend_gt") - pl.col("blend")).abs() > 1e-9).height
        print(f"{lg}: {out.height} rows, {moved} with a non-uniform games scale -> {dst.name}")


if __name__ == "__main__":
    main()

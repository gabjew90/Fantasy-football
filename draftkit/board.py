"""Printable tier board: terminal render + a markdown file for printing."""

from __future__ import annotations

import polars as pl
from rich.console import Console
from rich.table import Table

POS_ORDER = ["RB", "WR", "TE", "QB", "K", "DEF"]


def print_board(tiers: pl.DataFrame, console: Console | None = None) -> None:
    console = console or Console()
    for pos in POS_ORDER:
        grp = tiers.filter(pl.col("pos") == pos).sort("pos_rank")
        if grp.height == 0:
            continue
        table = Table(title=f"{pos} tiers", show_lines=False)
        for col in ("T", "Rk", "Player", "Tm", "Bye", "Proj", "VORP", "ECR", "ADP", "Δ"):
            table.add_column(col, justify="right" if col not in ("Player", "Tm") else "left")
        last_tier = None
        for row in grp.iter_rows(named=True):
            if last_tier is not None and row["tier"] != last_tier:
                table.add_section()
            last_tier = row["tier"]
            name = row["name"] + (" ⛰" if row["cliff_flag"] else "")
            table.add_row(
                str(row["tier"]),
                str(row["pos_rank"]),
                name,
                str(row.get("team") or ""),
                str(row.get("bye") or ""),
                f"{row['proj_pts']:.0f}" if row["proj_pts"] is not None else "",
                f"{row['vorp']:.0f}" if row["vorp"] is not None else "",
                f"{row['ecr']:.0f}" if row.get("ecr") is not None else "",
                f"{row['adp']:.1f}" if row.get("adp") is not None else "",
                f"{row['adp_delta']:+.0f}" if row.get("adp_delta") is not None else "",
            )
        console.print(table)


def write_board_markdown(tiers: pl.DataFrame, path) -> None:
    lines = ["# Draft Tier Board — Omnibeta Degens (12-team, full PPR, 2 FLEX)", ""]
    lines.append("⛰ = cliff: last player before a big value drop. Δ = ADP − value rank "
                 "(positive: market lets you get them later).")
    for pos in POS_ORDER:
        grp = tiers.filter(pl.col("pos") == pos).sort("pos_rank")
        if grp.height == 0:
            continue
        lines += ["", f"## {pos}", ""]
        last_tier = None
        for row in grp.iter_rows(named=True):
            if row["tier"] != last_tier:
                lines.append(f"\n**Tier {row['tier']}**\n")
                last_tier = row["tier"]
            cliff = " ⛰" if row["cliff_flag"] else ""
            adp = f", ADP {row['adp']:.1f}" if row.get("adp") is not None else ""
            lines.append(
                f"- {row['pos_rank']}. {row['name']}{cliff} ({row.get('team') or 'FA'}, "
                f"bye {row.get('bye') or '?'}) — {row['proj_pts']:.0f} pts, "
                f"VORP {row['vorp']:.0f}{adp}"
            )
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")

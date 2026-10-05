"""Build resources/priors_{season}_play_yards.csv: every player's regular-season catch
and run yardages, one row per player and kind, for the per-player luck line
(research.player_luck_line, DECISIONS #167).

Each row: gsis_id, kind ("catch" | "run"), n, yards (space-separated whole yards,
sorted). Runs leave out QB kneel-downs, as the scorer's rushing frame does. Read by
score_game.py, so a live run never reprocesses last season's play-by-play.

    python scripts/build_play_yards.py --season 2025 --pbp <that season's pbp file, csv or csv.gz>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

RES = Path(__file__).resolve().parent.parent / "resources"
COLS = ["season_type", "play_type", "qb_kneel", "complete_pass", "receiver_player_id", "rusher_player_id",
        "receiving_yards", "rushing_yards"]


def play_yards(pbp: pd.DataFrame) -> pd.DataFrame:
    """One row per (player, kind): his sorted yardages on that kind of play."""
    if "season_type" in pbp:
        pbp = pbp[pbp.season_type == "REG"]
    cat = pbp[(pbp.play_type == "pass") & (pbp.complete_pass == 1) & pbp.receiver_player_id.notna()
              & pbp.receiving_yards.notna()][["receiver_player_id", "receiving_yards"]]
    run = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()
              & pbp.rushing_yards.notna()][["rusher_player_id", "rushing_yards"]]
    rows = []
    for kind, df, pid, y in (("catch", cat, "receiver_player_id", "receiving_yards"),
                             ("run", run, "rusher_player_id", "rushing_yards")):
        for g, s in df.groupby(pid)[y]:
            v = sorted(int(round(x)) for x in s)
            rows.append({"gsis_id": g, "kind": kind, "n": len(v), "yards": " ".join(map(str, v))})
    return pd.DataFrame(rows, columns=["gsis_id", "kind", "n", "yards"]).sort_values(["gsis_id", "kind"])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--pbp", required=True, help="the season's nflverse play-by-play file, csv or csv.gz (a local file; nothing is fetched)")
    a = ap.parse_args(argv)
    pbp = pd.read_csv(a.pbp, usecols=lambda c: c in COLS, low_memory=False)
    out = play_yards(pbp)
    path = RES / f"priors_{a.season}_play_yards.csv"
    out.to_csv(path, index=False, encoding="utf-8")
    print(f"wrote {path}: {len(out)} rows, {out.gsis_id.nunique()} players")


if __name__ == "__main__":
    main()

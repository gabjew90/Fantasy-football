"""Build resources/priors_{season}_play_yards.csv: each player's catch and run yardages
from his last LAST_GAMES regular-season games of that season, game by game, for the
luck-free check (research.luck_for, DECISIONS #167).

Each row: gsis_id, kind ("catch" | "run"), games (that many games, oldest first, as
"week:y y y;week:y y" -- whole yards), n (plays in those games). Runs leave out QB
kneel-downs, as the scorer's rushing frame does. A game appears when he had at least one
play of that kind. Read by score_game.py, so a live run never reprocesses last season.

    python scripts/build_play_yards.py --season 2025 --pbp <that season's pbp file, csv or csv.gz>
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

import research as RSCH

RES = Path(__file__).resolve().parent.parent / "resources"
LAST_GAMES = RSCH.LUCK_WINDOW      # the resource must hold at least the luck-free window
COLS = ["season_type", "week", "play_type", "qb_kneel", "complete_pass", "receiver_player_id", "rusher_player_id",
        "receiving_yards", "rushing_yards"]


def play_yards(pbp: pd.DataFrame, last_games: int = LAST_GAMES) -> pd.DataFrame:
    """One row per (player, kind): his last `last_games` games' yardages, oldest first."""
    if "season_type" in pbp:
        pbp = pbp[pbp.season_type == "REG"]
    cat = pbp[(pbp.play_type == "pass") & (pbp.complete_pass == 1) & pbp.receiver_player_id.notna()
              & pbp.receiving_yards.notna()][["week", "receiver_player_id", "receiving_yards"]]
    run = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()
              & pbp.rushing_yards.notna()][["week", "rusher_player_id", "rushing_yards"]]
    rows = []
    for kind, df, pid, y in (("catch", cat, "receiver_player_id", "receiving_yards"),
                             ("run", run, "rusher_player_id", "rushing_yards")):
        for g, d in df.groupby(pid):
            weeks = sorted(d.week.unique())[-last_games:]
            games = [(int(w), [int(round(x)) for x in d[d.week == w][y]]) for w in weeks]
            rows.append({"gsis_id": g, "kind": kind,
                         "games": ";".join(f"{w}:" + " ".join(map(str, v)) for w, v in games),
                         "n": sum(len(v) for _, v in games)})
    return pd.DataFrame(rows, columns=["gsis_id", "kind", "games", "n"]).sort_values(["gsis_id", "kind"])


def parse_games(s) -> list[list[float]]:
    """The 'games' column back into per-game lists, oldest first."""
    out = []
    for part in str(s).split(";"):
        if ":" in part:
            out.append([float(v) for v in part.split(":", 1)[1].split()])
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--pbp", required=True,
                    help="the season's nflverse play-by-play file, csv or csv.gz (a local file; nothing is fetched)")
    a = ap.parse_args(argv)
    pbp = pd.read_csv(a.pbp, usecols=lambda c: c in COLS, low_memory=False)
    out = play_yards(pbp)
    path = RES / f"priors_{a.season}_play_yards.csv"
    out.to_csv(path, index=False, encoding="utf-8")
    print(f"wrote {path}: {len(out)} rows, {out.gsis_id.nunique()} players")


if __name__ == "__main__":
    main()

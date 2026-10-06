"""Build resources/priors_{season}_play_yards.csv: each player's catch and run yardages
from his last LAST_GAMES regular-season games of that season, game by game, for the
luck-free check (research.luck_for, DECISIONS #167); and
resources/priors_{season}_share_games.csv: each player's target and carry share in his
last LAST_GAMES games, for the automatic what-if range (research.auto_range, #179).

Each row: gsis_id, kind ("catch" | "run" | "pass" -- a QB's completions), games (that many games, oldest first, as
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
        "receiving_yards", "rushing_yards", "passer_player_id", "posteam"]


def play_yards(pbp: pd.DataFrame, last_games: int = LAST_GAMES) -> pd.DataFrame:
    """One row per (player, kind): his last `last_games` games' yardages, oldest first."""
    if "season_type" in pbp:
        pbp = pbp[pbp.season_type == "REG"]
    cat = pbp[(pbp.play_type == "pass") & (pbp.complete_pass == 1) & pbp.receiver_player_id.notna()
              & pbp.receiving_yards.notna()][["week", "receiver_player_id", "receiving_yards"]]
    run = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()
              & pbp.rushing_yards.notna()][["week", "rusher_player_id", "rushing_yards"]]
    kinds = [("catch", cat, "receiver_player_id", "receiving_yards"),
             ("run", run, "rusher_player_id", "rushing_yards")]
    if "passer_player_id" in pbp:
        # a QB's completions, each at the yards it gained (the receiver's yards on the play)
        comp = pbp[(pbp.play_type == "pass") & (pbp.complete_pass == 1) & pbp.passer_player_id.notna()
                   & pbp.receiving_yards.notna()][["week", "passer_player_id", "receiving_yards"]]
        kinds.append(("pass", comp, "passer_player_id", "receiving_yards"))
    rows = []
    for kind, df, pid, y in kinds:
        for g, d in df.groupby(pid):
            weeks = sorted(d.week.unique())[-last_games:]
            games = [(int(w), [int(round(x)) for x in d[d.week == w][y]]) for w in weeks]
            rows.append({"gsis_id": g, "kind": kind,
                         "games": ";".join(f"{w}:" + " ".join(map(str, v)) for w, v in games),
                         "n": sum(len(v) for _, v in games)})
    return pd.DataFrame(rows, columns=["gsis_id", "kind", "games", "n"]).sort_values(["gsis_id", "kind"])


def share_games(pbp: pd.DataFrame, last_games: int = LAST_GAMES) -> pd.DataFrame:
    """One row per player: his share of his team's throws and runs in each of his last
    `last_games` games, oldest first, as "week:target_share:carry_share;...". A game
    appears when he had a target or a carry (play-by-play has no snaps), so a game he
    played without one is missing: the spread runs a little narrow for small roles."""
    if "season_type" in pbp:
        pbp = pbp[pbp.season_type == "REG"]
    thr = pbp[(pbp.play_type == "pass") & pbp.receiver_player_id.notna()]
    run = pbp[(pbp.play_type == "run") & (pbp.qb_kneel != 1) & pbp.rusher_player_id.notna()]
    tt = thr.groupby(["posteam", "week"]).size()
    tc = run.groupby(["posteam", "week"]).size()
    pt = thr.groupby(["receiver_player_id", "posteam", "week"]).size()
    pc = run.groupby(["rusher_player_id", "posteam", "week"]).size()
    keys = sorted(set(pt.index) | set(pc.index))
    by = {}
    for pid, team, w in keys:
        ts = pt.get((pid, team, w), 0) / tt.get((team, w), float("nan"))
        cs = pc.get((pid, team, w), 0) / tc.get((team, w), float("nan"))
        by.setdefault(pid, []).append((int(w), team, ts, cs))
    rows = []
    for pid, g in by.items():
        g = sorted(g)[-last_games:]
        rows.append({"gsis_id": pid, "team": g[-1][1],
                     "games": ";".join(f"{w}:{ts:.4f}:{cs:.4f}" for w, _, ts, cs in g)})
    return pd.DataFrame(rows, columns=["gsis_id", "team", "games"]).sort_values("gsis_id")


def parse_share_games(s) -> list[tuple[int, float, float]]:
    """The share 'games' column back into (week, target share, carry share), oldest first."""
    out = []
    for part in str(s).split(";"):
        bits = part.split(":")
        if len(bits) == 3:
            out.append((int(bits[0]), float(bits[1]), float(bits[2])))
    return out


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
    sh = share_games(pbp)
    path = RES / f"priors_{a.season}_share_games.csv"
    sh.to_csv(path, index=False, encoding="utf-8")
    print(f"wrote {path}: {len(sh)} players")


if __name__ == "__main__":
    main()

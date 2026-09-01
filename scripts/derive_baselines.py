"""Derive replacement baselines from what streaming actually returned.

Intended to replace the hand-fitted QB5/TE8 in leagues/keefamania.yaml, which
were tuned to minimise the gap between VORP rank and ADP rank -- i.e. fitted
to the market's opinion rather than derived from the format.

STATUS: BLOCKED on ownership data. See draftkit/baselines.py. Without a source
for who was rostered in each week of the prior season, the waiver pool cannot
be identified, and the cheap proxy is not merely noisy but wrong in a
direction that flatters streaming. This script reports the blocker and, with
--show-contamination, demonstrates it. It never edits the league yaml.

    python scripts/derive_baselines.py --league keefamania
    python scripts/derive_baselines.py --league keefamania --show-contamination
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import nflreadpy as nfl  # noqa: E402
import polars as pl  # noqa: E402

from draftkit import baselines as B  # noqa: E402
from draftkit.config import Config  # noqa: E402
from draftkit.dataset import fantasy_points_expr, scoring_from_cfg  # noqa: E402


def load_board(path: Path) -> list[dict]:
    df = pl.read_csv(path, infer_schema_length=2000)
    return [{"pos": (r.get("pos") or "").upper(), "adp": r.get("adp")}
            for r in df.iter_rows(named=True)]


def contamination_demo(wk: pl.DataFrame, pos: str, rostered: int,
                       first_week: int = 5, form_weeks: int = 3) -> None:
    """Show what the points-per-game roster proxy actually selects.

    Kept as runnable evidence rather than a claim in a comment: the answer
    ("Joe Burrow is on waivers") is more convincing seen than described.
    """
    grp = wk.filter(pl.col("pos") == pos)
    print(f"\n  what the PPG roster proxy calls a free {pos} "
          f"(top {rostered} by PPG held):")
    for w in range(first_week, B.FANTASY_WEEKS + 1):
        hist = grp.filter(pl.col("week") < w)
        standing = (hist.group_by("player")
                    .agg(pl.col("fpts").mean().alias("ppg"), pl.len().alias("g"))
                    .filter(pl.col("g") >= 2).sort("ppg", descending=True))
        if standing.height <= rostered:
            continue
        held = set(standing["player"].to_list()[:rostered])
        recent = (grp.filter((pl.col("week") < w) & (pl.col("week") >= w - form_weeks))
                  .group_by("player").agg(pl.col("fpts").mean().alias("m"))
                  .sort("m", descending=True))
        active = set(grp.filter(pl.col("week") == w)["player"].to_list())
        free = [p for p in recent["player"].to_list()
                if p not in held and p in active]
        if free:
            print(f"    wk{w:<3} {', '.join(free[:4])}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default=None)
    ap.add_argument("--k", type=int, default=None,
                    help="override the waiver order statistic")
    ap.add_argument("--ownership", default=None,
                    help="CSV of player,week,pct_rostered for the stats season")
    ap.add_argument("--show-contamination", action="store_true")
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    exp = cfg.get("expected") or {}
    teams = int(exp.get("teams") or 10)
    rounds = int(exp.get("rounds") or 15)
    waiver = exp.get("waivers")
    k = a.k or B.waiver_k(waiver)

    season = int(cfg.get("stats_season") or 2025)
    scoring = scoring_from_cfg(cfg)
    wk = B.weekly_points(nfl.load_player_stats([season]),
                         fantasy_points_expr(scoring))

    board = load_board(cfg.scoped(cfg.root / "tiers.csv"))
    rostered = B.rostered_counts(board, teams, rounds)
    current = cfg.baselines

    print(f"League {cfg.league_name} — {teams} teams x {rounds} rounds, "
          f"waivers {waiver!r} -> k={k}, stats season {season}")
    print("rostered by ADP (top %d): " % (teams * rounds)
          + "  ".join(f"{p}{rostered.get(p, 0)}" for p in B.STREAMABLE))

    held: dict[str, dict[int, set[str]]] = {}
    if a.ownership:
        pos_of = {r["player"]: r["pos"]
                  for r in wk.select("player", "pos").unique().iter_rows(named=True)}
        with open(a.ownership, encoding="utf-8") as fh:
            held = B.held_from_ownership(list(csv.DictReader(fh)), pos_of)

    if not held:
        print(f"\n  BLOCKED — no ownership source for {season}.")
        print("  The waiver pool cannot be identified from box scores alone.")
        print("  Supply --ownership player,week,pct_rostered, or add "
              f"{season} ADP to data/raw/adp_history/.")
        print(f"\n  baselines UNCHANGED: "
              + "  ".join(f"{p}{current.get(p)}" for p in B.STREAMABLE))
        if a.show_contamination:
            contamination_demo(wk, "QB", rostered.get("QB", 25))
        return

    fmt = {"QB": teams, "RB": rostered.get("RB", teams * 2),
           "WR": rostered.get("WR", teams * 2), "TE": teams}
    rows = B.derive(wk, held, k, fmt)
    print(f"\n{'pos':>4}{'stream ppg':>12}{'= rank':>8}{'format':>8}"
          f"{'DERIVED':>9}{'current':>9}   why")
    for pos in B.STREAMABLE:
        r = rows.get(pos)
        if not r:
            continue
        ppg = "—" if r["streaming_ppg"] is None else f"{r['streaming_ppg']:.1f}"
        rk = "—" if r["streaming_rank"] is None else str(r["streaming_rank"])
        print(f"{pos:>4}{ppg:>12}{rk:>8}{r['format']:>8}{r['baseline']:>9}"
              f"{str(current.get(pos, '—')):>9}   {r['why']}")


if __name__ == "__main__":
    main()

"""Derive the two bench-valuation base rates from multi-season nflverse.

Both feed draftkit/bench.py. Neither is per-player: per-player games-missed
history was removed from valuation on 2026-08-30 (research Q6, near-zero
year-over-year signal) and is not coming back through a side door here.

1. ABSENT WEEKS per starter-caliber player, by position.
   Starters are chosen EX ANTE -- top N at the position by the PRIOR season's
   total -- and then their games in fantasy weeks 1-17 of the NEXT season are
   counted. Choosing starters by the same season's total would condition on
   having stayed healthy (survivorship) and understate the rate. Max games in
   weeks 1-17 is 16 because everyone has a bye in that window, so
   absent_injury = 16 - games; the bye is added separately by the caller as a
   certain week. Players with zero games in the next season are excluded --
   that mixes retirements and trades with full-season injuries and cannot be
   separated from box scores -- so the rate is biased LOW. Bias direction is
   stated so nobody reads it as a ceiling.

2. HANDCUFF SHARE for running backs.
   In weeks an ex-ante starting RB is absent and his team still plays (some
   other RB on the roster has a row), take the best RB fantasy score on that
   team and divide by the absent starter's own season points-per-game. The
   median across all such weeks is the fraction of a starter's role a fill-in
   actually inherits. This is the number the insurance formula uses for a
   `backs_up` player whose starter is on MY roster; it is measured, not typed.

    python scripts/derive_bench_rates.py --league keefamania
"""

from __future__ import annotations

import argparse
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import nflreadpy as nfl  # noqa: E402
import polars as pl  # noqa: E402

from draftkit.config import Config  # noqa: E402
from draftkit.dataset import fantasy_points_expr, scoring_from_cfg  # noqa: E402

FANTASY_WEEKS = 17
MAX_GAMES = 16                      # 17 fantasy weeks minus one bye
STARTER_N = {"QB": 12, "RB": 24, "WR": 24, "TE": 12}   # starter-caliber population
POSITIONS = tuple(STARTER_N)


def prep(weekly: pl.DataFrame, fpts: pl.Expr) -> pl.DataFrame:
    return (weekly.filter((pl.col("season_type") == "REG")
                          & (pl.col("week") <= FANTASY_WEEKS)
                          & pl.col("position").is_in(list(POSITIONS)))
            .with_columns(fpts)
            .select(pl.col("player_id").alias("pid"),
                    pl.col("player_display_name").alias("player"),
                    pl.col("position").alias("pos"),
                    pl.col("team"), pl.col("season"), pl.col("week"),
                    pl.col("fpts")))


def ex_ante_starters(wk: pl.DataFrame, season: int, pos: str) -> list[str]:
    tot = (wk.filter((pl.col("season") == season) & (pl.col("pos") == pos))
             .group_by("pid").agg(pl.col("fpts").sum().alias("t"))
             .sort("t", descending=True))
    return tot["pid"].to_list()[: STARTER_N[pos]]


def absent_weeks(wk: pl.DataFrame, pairs: list[tuple[int, int]]) -> dict[str, dict]:
    out = {}
    for pos in POSITIONS:
        vals = []
        for prior, nxt in pairs:
            starters = ex_ante_starters(wk, prior, pos)
            games = (wk.filter((pl.col("season") == nxt) & pl.col("pid").is_in(starters))
                       .group_by("pid").agg(pl.len().alias("g")))
            vals += [MAX_GAMES - int(g) for g in games["g"].to_list() if g >= 1]
        out[pos] = {"mean": st.mean(vals), "median": st.median(vals),
                    "p_missed_any": sum(1 for v in vals if v > 0) / len(vals),
                    "n": len(vals)}
    return out


def handcuff_share(wk: pl.DataFrame, pairs: list[tuple[int, int]]) -> dict:
    """Share of an absent starter's ppg produced by his EX-ANTE backup.

    The backup is identified before the absence: the teammate RB with the
    most fantasy points in the weeks the starter PLAYED. Taking the best
    teammate score in the absent week instead would pick the right handcuff
    with hindsight -- that version measured a share of 1.28, i.e. the fill-in
    outscoring the starter, which is max-of-several bias and not something a
    draft pick can replicate.
    """
    shares, standalone = [], []
    for prior, nxt in pairs:
        starters = ex_ante_starters(wk, prior, "RB")
        season = wk.filter((pl.col("season") == nxt) & (pl.col("pos") == "RB"))
        for pid in starters:
            mine = season.filter(pl.col("pid") == pid)
            if mine.height < 4:
                continue
            ppg = float(mine["fpts"].mean())
            if ppg <= 0:
                continue
            team = mine.sort("week")["team"][-1]
            played = set(mine["week"].to_list())
            absent = [w for w in range(1, FANTASY_WEEKS + 1) if w not in played]
            if not absent:
                continue
            mates = season.filter((pl.col("team") == team) & (pl.col("pid") != pid))
            with_starter = (mates.filter(pl.col("week").is_in(list(played)))
                            .group_by("pid").agg(pl.col("fpts").sum().alias("t"),
                                                 pl.col("fpts").mean().alias("m"))
                            .sort("t", descending=True))
            if with_starter.height == 0:
                continue
            backup = with_starter["pid"][0]
            backup_standalone = float(with_starter["m"][0])
            fill = mates.filter((pl.col("pid") == backup) & pl.col("week").is_in(absent))
            for v in fill["fpts"].to_list():
                shares.append(float(v) / ppg)
                standalone.append(backup_standalone / ppg)
    q = st.quantiles(shares, n=4)
    return {"median": st.median(shares), "mean": st.mean(shares),
            "p25": q[0], "p75": q[2], "n_weeks": len(shares),
            "standalone_median": st.median(standalone)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--seasons", default="2019,2020,2021,2022,2023,2024,2025")
    a = ap.parse_args()
    seasons = [int(s) for s in a.seasons.split(",")]
    pairs = list(zip(seasons[:-1], seasons[1:]))

    cfg = Config.load(league=a.league)
    wk = prep(nfl.load_player_stats(seasons),
              fantasy_points_expr(scoring_from_cfg(cfg)))

    print(f"Bench base rates — season pairs {pairs}, "
          f"starters chosen ex ante by prior-season total\n")
    aw = absent_weeks(wk, pairs)
    print(f"{'pos':>4}{'N':>6}{'mean absent':>13}{'median':>8}{'P(miss any)':>13}")
    for pos in POSITIONS:
        r = aw[pos]
        print(f"{pos:>4}{r['n']:>6}{r['mean']:>13.2f}{r['median']:>8.1f}"
              f"{r['p_missed_any']:>13.0%}")
    print("\n  (injury weeks only; add 1 certain bye week. Zero-game players "
          "excluded -> biased LOW.)")

    hs = handcuff_share(wk, pairs)
    print(f"\nRB handcuff share (ex-ante backup's score / absent starter's ppg), "
          f"n={hs['n_weeks']} starter-absent weeks")
    print(f"  in absent weeks: median {hs['median']:.2f}   mean {hs['mean']:.2f}   "
          f"IQR {hs['p25']:.2f}-{hs['p75']:.2f}")
    print(f"  same backup's STANDALONE ppg / starter ppg: median "
          f"{hs['standalone_median']:.2f}   "
          f"-> inherited uplift x{hs['median'] / max(hs['standalone_median'], 1e-9):.2f}")

    print("\n# draftkit/bench.py constants")
    print("ABSENT_WEEKS = {" + ", ".join(
        f'"{p}": {aw[p]["mean"]:.2f}' for p in POSITIONS) + "}")
    print(f"HANDCUFF_SHARE = {hs['median']:.2f}")


if __name__ == "__main__":
    main()

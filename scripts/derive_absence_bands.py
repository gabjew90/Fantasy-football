"""Mean missed games by position x ex-ante rank band (plan 2026-09-02 A2).

The games convention scales every source's 17-game line by one number
(projections.games = 16). Absence is not uniform: the last band at every
position misses more games than the first. This derives the table the
differential games convention reads (draftkit/games_table.py):

  * starters chosen EX ANTE by the prior season's total (the same
    ex_ante_starters as scripts/derive_bench_rates.py, sliced into bands);
  * absent = 16 - games played in fantasy weeks 1-17 of the NEXT season
    (max 16 because everyone has a bye in that window);
  * zero-game seasons excluded -- retirements and trades cannot be told
    from full-season injuries in box scores -- so every mean is biased LOW,
    stated here so nobody reads it as a ceiling;
  * never per player: per-player durability was removed 2026-08-30
    (research Q6) and DECISIONS #21/#25 keep it out.

The pooled mean over all cells is written too; the convention subtracts it
so only cross-cell DIFFERENCES move the board (levels stay on the 16-game
basis the briefs divide by).

    venv\\Scripts\\python.exe scripts\\derive_absence_bands.py --league keefamania --export data\\processed\\absence_bands.json
    venv\\Scripts\\python.exe scripts\\derive_absence_bands.py --league keefamania --through 2023 --export data\\processed\\backtest\\absence_bands_through_2023.json
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import polars as pl  # noqa: E402

from derive_bench_rates import MAX_GAMES, ex_ante_starters, prep  # noqa: E402

BANDS = {
    "QB": [(1, 6), (7, 12), (13, 24)],
    "RB": [(1, 12), (13, 24), (25, 36), (37, 48)],
    "WR": [(1, 12), (13, 24), (25, 36), (37, 48)],
    "TE": [(1, 6), (7, 12), (13, 24)],
}


def band_label(lo: int, hi: int) -> str:
    return f"{lo}-{hi}"


def band_table(wk: pl.DataFrame, pairs: list[tuple[int, int]], bands: dict | None = None) -> dict:
    """{pos: {label: {mean, median, n}}} plus the n-weighted pooled mean."""
    bands = bands or BANDS
    out: dict = {}
    all_vals: list[int] = []
    for pos, spans in bands.items():
        out[pos] = {}
        deepest = max(hi for _lo, hi in spans)
        per_band: dict[str, list[int]] = {band_label(lo, hi): [] for lo, hi in spans}
        for prior, nxt in pairs:
            ranked = ex_ante_starters(wk, prior, pos, n=deepest)
            games = dict(wk.filter((pl.col("season") == nxt) & pl.col("pid").is_in(ranked))
                           .group_by("pid").agg(pl.len().alias("g")).iter_rows())
            for lo, hi in spans:
                for pid in ranked[lo - 1: hi]:
                    g = games.get(pid)
                    if g and g >= 1:
                        per_band[band_label(lo, hi)].append(MAX_GAMES - int(g))
        for label, vals in per_band.items():
            if vals:
                out[pos][label] = {"mean": st.mean(vals), "median": st.median(vals), "n": len(vals)}
                all_vals += vals
    return {"bands": out, "pooled_mean": st.mean(all_vals) if all_vals else None, "pooled_n": len(all_vals)}


def main() -> None:
    import nflreadpy as nfl
    from draftkit.config import Config
    from draftkit.dataset import fantasy_points_expr, scoring_from_cfg
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--seasons", default="2019,2020,2021,2022,2023,2024,2025")
    ap.add_argument("--through", type=int, default=None,
                    help="use only season pairs ending <= this season (a leak-free table for a backtest year)")
    ap.add_argument("--export", default=None)
    a = ap.parse_args()
    seasons = [int(s) for s in a.seasons.split(",")]
    pairs = [(p, n) for p, n in zip(seasons[:-1], seasons[1:]) if a.through is None or n <= a.through]
    cfg = Config.load(league=a.league)
    wk = prep(nfl.load_player_stats(sorted({s for pr in pairs for s in pr})), fantasy_points_expr(scoring_from_cfg(cfg)))
    t = band_table(wk, pairs)
    print(f"Missed games by position x ex-ante rank band; pairs {pairs}; pooled mean {t['pooled_mean']:.2f} (n {t['pooled_n']})")
    for pos, cells in t["bands"].items():
        print(f"  {pos}: " + "  ".join(f"{lab} {c['mean']:.2f} (n {c['n']})" for lab, c in cells.items()))
    if a.export:
        out = {"meta": {"seasons": seasons, "pairs": pairs, "league_scoring": a.league, "max_games": MAX_GAMES,
                        "bands": BANDS,
                        "note": "ex-ante bands by prior-season total; zero-game seasons excluded (biased low); "
                                "read by draftkit/games_table.py in differential mode"},
               **t}
        Path(a.export).parent.mkdir(parents=True, exist_ok=True)
        Path(a.export).write_text(json.dumps(out, indent=1), encoding="utf-8")
        print(f"-> {a.export}")


if __name__ == "__main__":
    main()

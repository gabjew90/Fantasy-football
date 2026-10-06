"""Does summing a back's rushing and receiving draws independently hold up inside game scripts?
(outside review 2026-10-06: a pooled residual correlation of +0.044 can hide dependence by script)

Reads a backtest.py --save-results harness pickle. For backs in the combined-yards population:

1. The correlation of the rushing residual (actual - model mean) with the receiving residual,
   pooled and by the team's pregame spread (favoured by 7+, 3-7, within 3, underdog by 3-7,
   7+), with 95% intervals resampling whole games. The model draws the two independently,
   so its own correlation is about zero.
2. The combined line's width by the same buckets: the share of games outside the model's
   80% range (PIT below 0.1 or above 0.9; 20% when right), with the same intervals. This
   validates the SUM directly, which is what a bet on the combined line rides on.

    python props/tools/rr_dependence.py <harness pickle> [--games games.csv] [--out f.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
BUCKETS = [("favoured by 7+", 7.0, 99.0), ("favoured by 3-7", 3.0, 7.0), ("within 3", -3.0, 3.0),
           ("underdog by 3-7", -7.0, -3.0), ("underdog by 7+", -99.0, -7.0)]


def own_spread(R: pd.DataFrame, games: pd.DataFrame) -> pd.Series:
    """Points each row's team is favoured by (nflverse spread_line: positive = home favoured).
    The harness writes game_id as gameday_home_away (backtest.py game_id2); nflverse ids work too."""
    g = games.copy()
    if {"gameday", "away_team", "home_team"}.issubset(g.columns):
        alt = g.assign(game_id=g.gameday.astype(str) + "_" + g.home_team + "_" + g.away_team)
        g = pd.concat([g, alt], ignore_index=True)
    g = g.drop_duplicates("game_id").set_index("game_id")[["home_team", "spread_line"]]
    j = R[["game_id", "team"]].join(g, on="game_id")
    return pd.Series(np.where(j.team == j.home_team, j.spread_line, -j.spread_line), index=R.index, dtype=float)


def bucket_of(spread: pd.Series) -> pd.Series:
    """The script bucket for each spread (edges: 7+ and 3-7 include their lower edge)."""
    out = pd.Series(None, index=spread.index, dtype=object)
    for name, lo, hi in BUCKETS:
        if lo >= 3:
            m = (spread >= lo) & (spread < hi)
        elif hi <= -3:
            m = (spread <= hi) & (spread > lo)
        else:
            m = (spread > lo) & (spread < hi)
        out[m] = name
    return out


def _boot(stat, ids, reps, rng):
    """95% interval for stat(index array) resampling whole clusters."""
    ug, inv = np.unique(ids, return_inverse=True)
    members = [np.flatnonzero(inv == k) for k in range(len(ug))]
    vals = []
    for _ in range(reps):
        pick = rng.integers(0, len(ug), len(ug))
        idx = np.concatenate([members[k] for k in pick])
        vals.append(stat(idx))
    lo, hi = np.nanpercentile(vals, [2.5, 97.5])
    return float(lo), float(hi)


def dependence(R: pd.DataFrame, games: pd.DataFrame, reps: int = 2000, seed: int = 44) -> dict:
    d = R[R.rr_pop.astype(bool)].dropna(subset=["act_rush_yards", "act_rec_yards", "mean_rush_model",
                                                "mean_yds_model", "game_id"]).copy()
    d["spread"] = own_spread(d, games)
    d["bucket"] = bucket_of(d.spread)
    d["r_rush"] = d.act_rush_yards - d.mean_rush_model
    d["r_rec"] = d.act_rec_yards - d.mean_yds_model
    d["outside"] = ((d.pit_rr < 0.1) | (d.pit_rr > 0.9)).astype(float) if "pit_rr" in d else np.nan
    rng = np.random.default_rng(seed)

    def summarise(x: pd.DataFrame) -> dict:
        ids = (x.season.astype(str) + "_" + x.game_id.astype(str)).to_numpy()
        a, b, o = x.r_rush.to_numpy(float), x.r_rec.to_numpy(float), x.outside.to_numpy(float)
        corr = lambda i: float(np.corrcoef(a[i], b[i])[0, 1]) if len(i) > 2 else np.nan
        out = {"n": int(len(x)), "games": int(len(np.unique(ids))),
               "corr": corr(np.arange(len(x))), "corr_ci": _boot(corr, ids, reps, rng)}
        ok = ~np.isnan(o)
        if ok.any():
            share = lambda i: float(np.nanmean(o[i]))
            out["outside_80"] = share(np.arange(len(x)))
            out["outside_ci"] = _boot(share, ids, reps, rng)
        return out

    res = {"pooled": summarise(d), "by_spread": {}, "by_season": {}}
    for name, _, _ in BUCKETS:
        x = d[d.bucket == name]
        if len(x) >= 30:
            res["by_spread"][name] = summarise(x)
    for s_, x in d.groupby("season"):
        res["by_season"][int(s_)] = summarise(x)
    res["unmatched_spread"] = int(d.spread.isna().sum())
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--games", default=str(CACHE / "games.csv"))
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    R = pd.read_pickle(a.results)["results"]
    out = dependence(R, pd.read_csv(a.games, low_memory=False), reps=a.reps)
    fmt = lambda v: (f"r {v['corr']:+.3f} ({v['corr_ci'][0]:+.3f}, {v['corr_ci'][1]:+.3f})"
                     + (f"; outside 80% {100 * v['outside_80']:.1f}% ({100 * v['outside_ci'][0]:.1f}-"
                        f"{100 * v['outside_ci'][1]:.1f})" if "outside_80" in v else "")
                     + f"; n {v['n']}, {v['games']} games")
    print("Rushing vs receiving residuals for backs (model: independent, r ~ 0); combined line width")
    print("  pooled           ", fmt(out["pooled"]))
    for k, v in out["by_spread"].items():
        print(f"  {k:17s}", fmt(v))
    for k, v in out["by_season"].items():
        print(f"  {k:<17d}", fmt(v))
    if out["unmatched_spread"]:
        print(f"  ({out['unmatched_spread']} back-games had no spread in games.csv)")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

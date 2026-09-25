"""Choose the market_fit pace weight on the tune seasons (plan step 5,
DECISIONS #106, reports/market_env_tuning.md).

Inputs are `backtest.py --save-results` pickles: the live run (--env history)
and one run per weight (--env market_fit --pace-weight W), all covering the
tune seasons. The rule: the SCORE is CRPS summed over the five markets, each
relative to the live model's mean; among weights not measurably worse than
the best, the smallest -- live counts as weight 0.

"Not measurably worse" is read two ways, and both are printed:
  equal   -- the score itself, resampled by whole games: each market weighs
             the same, as in the score (the test the rule means).
  rows    -- backtest.composite_rows, the tuner's per-row composite: a
             player-row weighs as many markets as it is graded in, so the
             receiving markets (about 7 rows in 8) dominate.

    python props/tools/pick_market_env.py --live live.pkl --run 0.25=w025.pkl ...
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
import backtest as B  # noqa: E402

KEYS = ["season", "team", "week", "gsis_id"]


def load(path, seasons):
    r = pd.read_pickle(path)["results"]
    return r[r.season.isin(seasons)].set_index(KEYS).sort_index()


def score_by_games(frame, base, games, ug, take=None):
    """The score (sum over markets of mean CRPS / live mean), on a resample of
    whole games given as counts per game."""
    total = 0.0
    for mk, (num, den) in frame.items():
        s = np.bincount(games[mk], weights=num, minlength=len(ug))
        c = np.bincount(games[mk], weights=den, minlength=len(ug))
        if take is not None:
            s, c = s * take, c * take
        total += (s.sum() / max(c.sum(), 1e-12)) / base[mk]
    return total


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--live", required=True)
    ap.add_argument("--run", action="append", required=True, help="WEIGHT=path.pkl")
    ap.add_argument("--seasons", default="2022,2023")
    ap.add_argument("--reps", type=int, default=2000)
    a = ap.parse_args(argv)
    seasons = [int(s) for s in a.seasons.split(",")]
    runs = {0.0: load(a.live, seasons)}
    for spec in a.run:
        w, p = spec.split("=", 1)
        runs[float(w)] = load(p, seasons)
    idx = runs[0.0].index
    mks = list(B.MARKETS)
    for w, f in runs.items():
        assert f.index.equals(idx), f"run {w} covers different player-weeks"
        for mk in mks:
            assert (f[f"crps_{mk}_model"].notna() == runs[0.0][f"crps_{mk}_model"].notna()).all(), (w, mk)
    base = {mk: runs[0.0][f"crps_{mk}_model"].mean() for mk in mks}
    ref = runs[0.0].reset_index()
    game = (ref["season"].astype(str) + "_" + ref["game_id"].astype(str)).to_numpy()
    ug, gi = np.unique(game, return_inverse=True)
    games, parts = {}, {}
    for mk in mks:
        m = ref[f"crps_{mk}_model"].notna().to_numpy()
        games[mk] = gi[m]
    for w, f in runs.items():
        parts[w] = {mk: (f[f"crps_{mk}_model"].to_numpy()[~np.isnan(f[f"crps_{mk}_model"].to_numpy())],
                         np.ones(int(f[f"crps_{mk}_model"].notna().sum()))) for mk in mks}
    score = {w: score_by_games(parts[w], base, games, ug) for w in runs}
    best = min(score, key=score.get)
    rng = np.random.default_rng(1)
    takes = [np.bincount(rng.integers(0, len(ug), len(ug)), minlength=len(ug)) for _ in range(a.reps)]
    rows = {w: B.composite_rows(runs[w].reset_index(), mks, base) for w in runs}
    print("| W | Score (live = 5) | Equal-weight vs best, 95% CI | Row composite vs best, 95% CI |")
    print("|---|---|---|---|")
    tie_eq, tie_rows = {}, {}
    for w in sorted(runs):
        dist = np.array([score_by_games(parts[w], base, games, ug, t) - score_by_games(parts[best], base, games, ug, t)
                         for t in takes])
        lo, hi = np.percentile(dist, [2.5, 97.5])
        d = ref.assign(diff=(rows[w] - rows[best])).dropna(subset=["diff"])
        rlo, rhi = B.game_block_ci(d, d["diff"])
        tie_eq[w], tie_rows[w] = (w == best or lo <= 0), (w == best or rlo <= 0)
        print(f"| {w:g} | {score[w]:.4f} | {score[w] - score[best]:+.4f} ({lo:+.4f}, {hi:+.4f}) | "
              f"{d['diff'].mean():+.4f} ({rlo:+.4f}, {rhi:+.4f}) |")
    print(f"\nbest by score: {best:g}; chosen, equal-weight test: {min(w for w in runs if tie_eq[w]):g}; "
          f"row-composite test: {min(w for w in runs if tie_rows[w]):g}")


if __name__ == "__main__":
    main()

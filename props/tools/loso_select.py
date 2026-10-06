"""Leave-one-season-out: how well does a round's SELECTION RULE do on a season it never saw?
(outside review 2026-10-06, finding 7: choosing the best of a grid on 2022-25 and reporting
its interval on the same seasons ignores the choice itself.)

A round's grid pickle (backtest.py --tune-grid ... --save-results) holds one results frame
per setting. For each held-out season: pick the setting by the round's metric on the OTHER
seasons (lowest mean log loss for the market and score; the shipped setting kept when it
sits within `tie` of the best), then score that pick against the shipped setting on the
held-out season alone (scoreboard.compare: frozen cohort, game-clustered). The pooled
out-of-fold gain estimates what the procedure is worth; the in-sample gain of the
full-data pick is printed beside it for contrast (the winner's curse is the difference).

    python props/tools/loso_select.py <grid pickle> --market "rushing yards" --score c \
        --knob eff_sd_rush [--shipped '{"eff_sd_rush": 0.3}'] [--out f.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoreboard as SB  # noqa: E402


def mean_score(R: pd.DataFrame, market: str, score: str, cohort: pd.DataFrame | None = None) -> float:
    """Mean log loss (score 'c' conversion, 'u' own volume) on the bettable population --
    or on `cohort`'s player-games, so every candidate is scored on the same rows."""
    d = SB.market_frame(R, market, cohort=cohort)
    if d.empty:
        return float("nan")
    return float(SB.logloss(d[f"p{score}"], d.y).mean())


def pick(frames, cands, shipped_i, market, score, tie=0.0005, dist=None, min_move=1.0) -> int:
    """The registered selection rule: the lowest mean log loss on the SHIPPED setting's
    cohort (one population for every candidate); ties within `tie` go to the candidate
    closest to shipped (dist: {i: distance from shipped}, shipped = 0); a pick that moves
    the Over chance by less than `min_move` points on average stays shipped."""
    cohort = SB.market_frame(frames[shipped_i], market)[SB.KEYS]
    vals = {i: mean_score(frames[i], market, score, cohort) for i in cands}
    best = min(vals.values())
    near = [i for i in cands if vals[i] - best <= tie]
    d_ = dist or {i: (0 if i == shipped_i else 1) for i in cands}
    p = min(near, key=lambda i: (d_[i], vals[i]))
    if p != shipped_i and min_move:
        c = SB.compare(frames[p], frames[shipped_i], "game", reps=10)[market]
        if c[f"move_points_{score}"] < min_move:
            return shipped_i
    return p


def loso(frames, cands, shipped_i, market, score, seasons=None, reps=2000, tie=0.0005, dist=None,
         min_move=1.0) -> dict:
    seasons = sorted(seasons or frames[shipped_i].season.unique())
    folds, diffs, ids = [], [], []
    for s in seasons:
        train = [F[F.season != s] for F in frames]
        test = [F[F.season == s] for F in frames]
        p = pick(train, cands, shipped_i, market, score, tie, dist, min_move)
        row = {"held_out": int(s), "pick": int(p)}
        if p == shipped_i:
            a0 = SB.market_frame(test[shipped_i], market)
            row.update(gain=0.0, ci=[0.0, 0.0], n=int(len(a0)))
            diffs.append(np.zeros(len(a0)))              # the procedure kept shipped: no change here
            ids.append(SB.cluster_ids(a0, "game"))
        else:
            c = SB.compare(test[p], test[shipped_i], "game", reps=reps)[market]
            row.update(gain=c[f"logloss_{score}"]["gain"], ci=c[f"logloss_{score}"]["ci"], n=c["n"])
            # the per-row differences, pooled across folds for one interval on the procedure
            a = SB.market_frame(test[shipped_i], market)
            b = SB.market_frame(test[p], market, cohort=a[SB.KEYS])
            d = b.merge(a[SB.KEYS + [f"p{score}", "y"]], on=SB.KEYS, suffixes=("", "_ref"))
            diffs.append((SB.logloss(d[f"p{score}_ref"], d.y_ref) - SB.logloss(d[f"p{score}"], d.y)).to_numpy())
            ids.append(SB.cluster_ids(d, "game"))
        folds.append(row)
    n_tot = sum(f["n"] for f in folds)
    pooled = sum(f["gain"] * f["n"] for f in folds) / n_tot if n_tot else float("nan")
    out = {"folds": folds, "oof_gain": pooled}
    if diffs:
        x, g = np.concatenate(diffs), np.concatenate(ids)   # every fold's rows, clustered by game
        out["oof_ci"] = list(SB.cluster_ci(x, g, reps, np.random.default_rng(7)))
    full = pick(frames, cands, shipped_i, market, score, tie, dist, min_move)
    out["full_pick"] = int(full)
    if full != shipped_i:
        c = SB.compare(frames[full], frames[shipped_i], "game", reps=reps)[market]
        out["in_sample_gain"], out["in_sample_ci"] = c[f"logloss_{score}"]["gain"], c[f"logloss_{score}"]["ci"]
    else:
        out["in_sample_gain"], out["in_sample_ci"] = 0.0, [0.0, 0.0]
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--market", required=True)
    ap.add_argument("--score", choices=["c", "u"], required=True)
    ap.add_argument("--knob", required=True, help="the knob the round varied (the others stay at shipped)")
    ap.add_argument("--shipped", required=True, help="JSON of the shipped values of every varied knob")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--min-move", type=float, default=1.0,
                    help="the registered minimum average move of the Over chance, in points (0 = none)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = pd.read_pickle(a.grid)
    grid, frames = d["grid"], d["frames"]
    shipped = json.loads(a.shipped)
    missing = sorted({k for k in shipped if not any(k in g for g in grid)})
    if missing:
        sys.exit(f"--shipped names knobs no grid row carries: {missing}")
    same_rest = lambda g: all(g.get(k) == v for k, v in shipped.items() if k != a.knob)
    cands = [i for i, g in enumerate(grid) if same_rest(g)]
    hit = [i for i in cands if grid[i].get(a.knob) == shipped[a.knob]]
    if not hit:
        sys.exit(f"no grid row holds the shipped setting {shipped} (candidates: {[grid[i] for i in cands]})")
    shipped_i = hit[0]
    sv = shipped[a.knob]
    num = lambda v: 0.0 if v is None else float(v)       # None = the knob off
    dist = {i: abs(num(grid[i].get(a.knob)) - num(sv)) for i in cands}
    out = loso(frames, cands, shipped_i, a.market, a.score, reps=a.reps, dist=dist, min_move=a.min_move)
    lab = lambda i: grid[i].get(a.knob)
    print(f"{a.market}, {'conversion' if a.score == 'c' else 'own volume'} log loss; knob {a.knob}, "
          f"shipped {shipped[a.knob]}; candidates {[lab(i) for i in cands]}")
    for f in out["folds"]:
        print(f"  hold out {f['held_out']}: pick {lab(f['pick'])}  gain on {f['held_out']} {f['gain']:+.5f} "
              f"({f['ci'][0]:+.5f}, {f['ci'][1]:+.5f}), n {f['n']}")
    ci = out.get("oof_ci", [0.0, 0.0])
    print(f"  OUT OF FOLD (the procedure): {out['oof_gain']:+.5f} ({ci[0]:+.5f}, {ci[1]:+.5f})")
    print(f"  in sample (pick {lab(out['full_pick'])} on all seasons): {out['in_sample_gain']:+.5f} "
          f"({out['in_sample_ci'][0]:+.5f}, {out['in_sample_ci'][1]:+.5f})")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

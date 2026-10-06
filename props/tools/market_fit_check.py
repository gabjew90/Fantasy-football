"""Market volume fit: one season or three? (reports/market_fit_pool.md, pre-registered).

For each test season S, fits build_priors' market regression on S-1 alone ("one") and
on S-3..S-1 pooled ("pooled"), predicts every team-game's throws in S (plays x pass
rate at that game's spread and total, the pass rate clipped as the engine clips it),
and compares mean squared error against the actual throws.

    python props/tools/market_fit_check.py --test 2022,2023,2024     # selection
    python props/tools/market_fit_check.py --test 2025               # confirm, once

Data: nflverse play-by-play and games.csv from the backtest cache (NFL_BACKTEST_CACHE).
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

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE / "scripts"))
import build_priors as BP  # noqa: E402

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
POOL = 3


def season_rows(season, games):
    pbp = pd.read_csv(CACHE / f"pbp_{season}.csv.gz", low_memory=False,
                      usecols=["season_type", "play_type", "receiver_player_id", "rusher_player_id",
                               "qb_kneel", "posteam", "week"])
    pbp = pbp[pbp.season_type == "REG"]
    passes, rushes = BP.throws_and_runs(pbp)
    tw = pd.DataFrame({"targets": passes.groupby(["posteam", "week"]).size(),
                       "carries": rushes.groupby(["posteam", "week"]).size()}).fillna(0).reset_index().rename(
        columns={"posteam": "team"})
    g = games[(games.season == season) & (games.game_type == "REG")]
    return BP.market_rows(g, tw)


def predict_throws(fit, rows):
    d = np.array(rows)
    fp, fr = fit["plays"], fit["pass_rate"]
    plays = fp["intercept"] + fp["per_spread_pt"] * d[:, 0] + fp["per_total_pt"] * d[:, 1]
    pr = np.clip(fr["intercept"] + fr["per_spread_pt"] * d[:, 0] + fr["per_total_pt"] * d[:, 1], 0.35, 0.75)
    return plays * pr, d[:, 2] * d[:, 3]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", required=True, help="comma-separated test seasons")
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--out", default=None, help="write the summary JSON here")
    a = ap.parse_args(argv)
    tests = [int(x) for x in a.test.split(",")]
    games = pd.read_csv(CACHE / "games.csv")
    need = sorted({s for t in tests for s in range(t - POOL, t + 1)} | {2025})
    rows = {s: season_rows(s, games) for s in need}

    # the factored fit must reproduce the shipped 2025 coefficients exactly
    shipped = json.loads((ENGINE / "resources" / "priors_2025_params.json").read_text(encoding="utf-8"))
    refit = BP.fit_market(rows[2025])
    for nm in ("plays", "pass_rate"):
        for k in ("intercept", "per_spread_pt", "per_total_pt"):
            assert abs(refit[nm][k] - shipped["market_env_fit"][nm][k]) < 1e-9, (nm, k, refit[nm][k])
    print("reproduces the shipped 2025 fit: yes", file=sys.stderr)

    rng = np.random.default_rng(20261006)
    out, err_one, err_pool = {"seasons": {}}, [], []
    for t in tests:
        one = BP.fit_market(rows[t - 1])
        pooled = BP.fit_market([r for s in range(t - POOL, t) for r in rows[s]])
        p1, y = predict_throws(one, rows[t])
        p3, _ = predict_throws(pooled, rows[t])
        e1, e3 = (p1 - y) ** 2, (p3 - y) ** 2
        err_one.append(e1); err_pool.append(e3)
        out["seasons"][t] = {"n": int(len(y)), "mse_one": float(e1.mean()), "mse_pooled": float(e3.mean()),
                             "fit_one": one, "fit_pooled": pooled}
        print(f"{t}: n={len(y)}  MSE one {e1.mean():.2f}  pooled {e3.mean():.2f}  "
              f"(pooled - one {e3.mean() - e1.mean():+.2f})")
    e1, e3 = np.concatenate(err_one), np.concatenate(err_pool)
    diff = e3 - e1
    idx = rng.integers(0, len(diff), size=(a.boot, len(diff)))
    boots = diff[idx].mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    out["all"] = {"n": int(len(diff)), "mse_one": float(e1.mean()), "mse_pooled": float(e3.mean()),
                  "diff": float(diff.mean()), "ci95": [float(lo), float(hi)]}
    print(f"all {','.join(map(str, tests))}: n={len(diff)}  MSE one {e1.mean():.2f}  pooled {e3.mean():.2f}  "
          f"pooled - one {diff.mean():+.3f}  95% CI [{lo:+.3f}, {hi:+.3f}]")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

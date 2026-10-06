"""Tier 3 (reports/implied_total_test.md, pre-registered): does the model under-use the
market's implied team total? Per market, the slope b of log(team actual / model) on
log(implied total / the team's mean implied total over its earlier games that season),
with a 95% interval resampling team-games, in 2022-23 and 2024-25.

    python props/tools/implied_total_test.py <corrected harness --save-results pickle, 2022-25> [--out f.json]
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backup_implied_total as BI  # noqa: E402

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
MARKETS = [("receivers' receiving yards", "act_rec_yards", "mean_yds_model", None),
           ("backs' rushing yards", "act_rush_yards", "mean_rush_model", "rush_pop"),
           ("starting QB passing yards", "act_pass_yards", "mean_pass_model", "pass_pop")]


def team_games(res: pd.DataFrame) -> pd.DataFrame:
    """Per team-game and market: summed actual and model means over that market's rows."""
    out = None
    for label, act, mod, pop in MARKETS:
        d = res[res[mod].notna()]
        if pop:
            d = d[d[pop].astype(bool)]
        g = d.groupby(["season", "team", "week"]).agg(**{f"{label}|act": (act, "sum"),
                                                       f"{label}|mod": (mod, "sum")})
        out = g if out is None else out.join(g, how="outer")
    return out.reset_index()


def implied_ratios(imp: pd.DataFrame) -> pd.DataFrame:
    """Adds `ratio`: implied total over the team's mean implied total in its earlier
    games that season (games without an earlier one are dropped)."""
    rows = []
    for _, g in imp.sort_values("week").groupby(["season", "team"]):
        cum = g.implied.expanding().mean().shift(1)
        rows.append(g.assign(ratio=g.implied / cum))
    return pd.concat(rows).dropna(subset=["ratio"])


def slope(d: pd.DataFrame, label: str, reps: int, rng):
    d = d[(d[f"{label}|act"] > 0) & (d[f"{label}|mod"] > 0)].dropna(subset=["ratio"])
    x = np.log(d.ratio.to_numpy(float))
    y = np.log((d[f"{label}|act"] / d[f"{label}|mod"]).to_numpy(float))
    def b_of(i):
        xi, yi = x[i], y[i]
        xc = xi - xi.mean()
        return float((xc * (yi - yi.mean())).sum() / (xc ** 2).sum())
    b = b_of(np.arange(len(x)))
    boots = [b_of(rng.integers(0, len(x), len(x))) for _ in range(reps)]
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"n": int(len(x)), "b": b, "ci": [float(lo), float(hi)], "sd_log_ratio": float(x.std())}


def verdict(per: dict) -> str:
    a, b = per["2022-23"], per["2024-25"]
    if a["b"] > 0 and b["b"] > 0 and a["ci"][0] > 0 and b["ci"][0] > 0:
        return "the implied total carries information the model lacks"
    if (a["ci"][0] <= 0 <= a["ci"][1] and b["ci"][0] <= 0 <= b["ci"][1]) or np.sign(a["b"]) != np.sign(b["b"]):
        return "it does not"
    return "unresolved"


def run(res, games, reps=2000, seed=1):
    d = implied_ratios(BI.implied_totals(games)).merge(team_games(res), on=["season", "team", "week"])
    rng = np.random.default_rng(seed)
    out = {}
    for label, *_ in MARKETS:
        per = {p: slope(d[d.season.isin(ss)], label, reps, rng) for p, ss in BI.PERIODS.items()}
        out[label] = {"periods": per, "verdict": verdict(per)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    out = run(pd.read_pickle(a.results)["results"], pd.read_csv(CACHE / "games.csv"))
    for label, v in out.items():
        print(f"\n{label}")
        for p, s in v["periods"].items():
            print(f"  {p}: {s['n']} team-games, b = {s['b']:+.3f} ({s['ci'][0]:+.3f}, {s['ci'][1]:+.3f})")
        print(f"  verdict: {v['verdict']}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

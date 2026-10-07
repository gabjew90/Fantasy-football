"""Paired whole-distribution CRPS per player-game, candidate harness run against a reference
(projection changes: the stand-in lines move, so line scores cannot compare them --
reports/priors_active_weeks.md amendment). Optionally split by the new-team players (round 37).

    python props/tools/paired_crps.py <reference pickle> <candidate pickle> [--seasons 2022,2023,2024]
        [--new-team] [--out f.json]
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

KEYS = ["season", "team", "week", "gsis_id"]
MARKETS = {"receptions": ("crps_rec_model", None), "receiving yards": ("crps_yds_model", None),
           "rushing yards": ("crps_rush_model", "rush_pop"), "rushing + receiving": ("crps_rr_model", "rr_pop"),
           "QB passing": ("crps_pass_model", "pass_pop")}


def pair(ref: pd.DataFrame, cand: pd.DataFrame, seasons=None, rows=None, reps=4000, seed=9) -> dict:
    """{market: n, missing, ref mean, gain (ref - candidate; positive = candidate better),
    95% game-clustered interval, relative gain}. rows: an optional boolean mask on `ref`
    (e.g. the new-team players) that restricts the paired player-games."""
    rng = np.random.default_rng(seed)
    out = {}
    base = ref if rows is None else ref[rows]
    for mk, (col, pop) in MARKETS.items():
        if col not in base or col not in cand or (pop is not None and pop not in base):
            continue                       # a market this run does not score
        a = base if pop is None else base[base[pop].astype(bool)]
        a = a[a[col].notna()]
        if seasons:
            a = a[a.season.isin(seasons)]
        if a.empty:
            continue
        d = a[KEYS + [col, "game_id"]].merge(cand[KEYS + [col]], on=KEYS, suffixes=("_ref", "_new"), how="left")
        miss = int(d[f"{col}_new"].isna().sum())
        d = d.dropna(subset=[f"{col}_new"])
        diff = (d[f"{col}_ref"] - d[f"{col}_new"]).to_numpy()
        lo, hi = SB.cluster_ci(diff, (d.season.astype(str) + "_" + d.game_id.astype(str)).to_numpy(), reps, rng)
        refm = float(d[f"{col}_ref"].mean())
        out[mk] = {"n": int(len(d)), "missing": miss, "ref": refm, "gain": float(diff.mean()), "ci": [lo, hi],
                   "rel": float(diff.mean() / refm) if refm else None}
    return out


def new_team_mask(ref: pd.DataFrame, priors_dir: Path) -> pd.Series:
    """Rows whose player played last season for a different team (priors team_prior), the
    population the new-team cap acts on."""
    flag = pd.Series(False, index=ref.index)
    for s in sorted(ref.season.unique()):
        f = Path(priors_dir) / f"priors_{int(s) - 1}_players.csv"
        if not f.exists():
            continue
        tp = pd.read_csv(f, usecols=["gsis_id", "team_prior"]).dropna()
        m = ref.season == s
        prior = ref.loc[m, "gsis_id"].map(dict(zip(tp.gsis_id, tp.team_prior)))
        flag.loc[m] = prior.notna() & (prior != ref.loc[m, "team"])
    return flag


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("candidate")
    ap.add_argument("--seasons", default=None)
    ap.add_argument("--new-team", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    ref, cand = (pd.read_pickle(x)["results"] for x in (a.reference, a.candidate))
    seasons = [int(x) for x in a.seasons.split(",")] if a.seasons else None
    res = {"everyone": pair(ref, cand, seasons)}
    if a.new_team:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
        import backtest as BT
        mask = new_team_mask(ref, BT.priors_cache_dir())
        res["new_team_rows"] = int(mask.sum())
        res["new_team"] = pair(ref, cand, seasons, rows=mask)
    for part in ("everyone", "new_team"):
        if part in res:
            print(f"== {part} (positive = candidate better)")
            for mk, v in res[part].items():
                print(f"  {mk:22s} n {v['n']:5d} gain {v['gain']:+.5f} ({v['ci'][0]:+.5f}, {v['ci'][1]:+.5f}) "
                      f"relative {100 * (v['rel'] or 0):+.2f}%")
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

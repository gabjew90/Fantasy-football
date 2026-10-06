"""Tier 2, part A (reports/tier2_conditional_calibration.md): each stage graded alone.

Reads a backtest --conditional --save-results pickle and reports, per stage and bucket,
the share of outcomes below the model's p10 and above its p90 (PIT < 0.1 / > 0.9),
with 95% intervals from resampling whole games. Calibrated: 10% / 10%, 20% outside.

    python props/tools/conditional_calibration.py RESULTS.pkl --seasons 2022,2023,2024 [--out f.json]
    python props/tools/conditional_calibration.py --grid GRID.pkl --flagged "stage 1: targets|..."   # part B
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

# Buckets are half-open [lo, hi). STAGE 1 is bucketed by the PROJECTED volume (the
# simulation's mean): bucketing a volume forecast by the actual volume selects on the
# outcome (a 10-target game sits above p90 by construction) -- caught on the smoke run,
# before the full run. STAGE 2 is bucketed by the actual volume, which is its input.
TGT_EDGES = [(0.5, 3.5, "1-3"), (3.5, 6.5, "4-6"), (6.5, 9.5, "7-9"), (9.5, 999, "10+")]
CAR_EDGES = [(0.5, 9.5, "1-9"), (9.5, 14.5, "10-14"), (14.5, 19.5, "15-19"), (19.5, 999, "20+")]
P_TGT_EDGES = [(0, 3.5, "under 3.5"), (3.5, 6.5, "3.5-6.5"), (6.5, 9.5, "6.5-9.5"), (9.5, 999, "9.5+")]
P_CAR_EDGES = [(0, 9.5, "under 9.5"), (9.5, 14.5, "9.5-14.5"), (14.5, 19.5, "14.5-19.5"), (19.5, 999, "19.5+")]
MARGINS = [(-99, -8.5, "lost by 9+"), (-8.5, 8.5, "within 8"), (8.5, 99, "won by 9+")]
# (label, PIT column, bucket column, bucket word, edges, population)
CHECKS = [
    ("stage 1: targets", "pit_tgt", "mean_tgt", "projected", P_TGT_EDGES, "rec"),
    ("stage 2: catches | targets", "pit_rec_c", "act_targets", "targets", TGT_EDGES, "rec"),
    ("stage 2: receiving yards | targets", "pit_yds_c", "act_targets", "targets", TGT_EDGES, "rec"),
    ("stage 1: carries (backs)", "pit_car", "mean_car_model", "projected", P_CAR_EDGES, "rb"),
    ("stage 2: rushing yards | carries (backs)", "pit_rush_c", "act_carries", "carries", CAR_EDGES, "rb"),
    ("stage 1: carries (starting QB)", "pit_car_qb", "mean_car_model", "projected", [], "qb"),
    ("stage 2: rushing yards | carries (starting QB)", "pit_rush_c", "act_carries", "carries", [], "qb"),
]


def team_margins(seasons):
    g = pd.read_csv(CACHE / "games.csv")
    g = g[g.season.isin(seasons) & (g.game_type == "REG")]
    home = g[["season", "week", "home_team", "home_score", "away_score"]].rename(columns={"home_team": "team"})
    home["margin"] = home.home_score - home.away_score
    away = g[["season", "week", "away_team", "home_score", "away_score"]].rename(columns={"away_team": "team"})
    away["margin"] = away.away_score - away.home_score
    return pd.concat([home, away])[["season", "week", "team", "margin"]]


def shares(d, reps, rng, descriptive=False):
    """(n, below p10, above p90, outside, CI of outside) with whole-game resampling."""
    lo, hi = (d.pit < 0.1).astype(float), (d.pit > 0.9).astype(float)
    out = lo + hi
    games = d.game_id.values
    ug, inv = np.unique(games, return_inverse=True)
    sums = np.bincount(inv, weights=out.values, minlength=len(ug))
    cnts = np.bincount(inv, minlength=len(ug))
    idx = rng.integers(0, len(ug), size=(reps, len(ug)))
    boot = sums[idx].sum(1) / cnts[idx].sum(1)
    c_lo, c_hi = np.percentile(boot, [2.5, 97.5])
    # final-margin buckets select on an outcome the player helped cause: shown, never judged
    verdict = ("descriptive" if descriptive else
               "too narrow" if c_lo > 0.20 else "too wide" if c_hi < 0.20 else "ok")
    return {"n": int(len(d)), "below_p10": float(lo.mean()), "above_p90": float(hi.mean()),
            "outside": float(out.mean()), "ci": [float(c_lo), float(c_hi)], "verdict": verdict}


# Part B: which knob each flagged stage may move, and the check that judges it
STAGE_KNOBS = [("stage 1: targets", "share_conc_targets"),
               ("stage 1: carries (backs)", "share_conc_carries"),
               ("stage 2: catches | targets", "catch_conc"),
               ("stage 2: receiving yards | targets", "eff_sd_rec"),
               ("stage 2: rushing yards | carries (backs)", "eff_sd_rush")]


def grid_pick(grid, frames, reps, rng, flagged):
    """Part B selection on the tune seasons: for each flagged stage, among the grid rows
    that move only that stage's knob (the shipped row included), the value whose outside-
    p10-p90 share on that stage's own check is closest to 20%. Returns (table, picks)."""
    checks = {c[0]: c for c in CHECKS}
    base = grid[0]
    table, picks = [], {}
    for label, knob in STAGE_KNOBS:
        _, pit_col, _vol, _w, _e, pop = checks[label]
        rows = []
        for cfg, R in zip(grid, frames):
            if any(cfg.get(k) != base.get(k) for k in base if k != knob):
                continue
            pops = {"rec": R.act_targets.notna(), "rb": R.rush_pop.astype(bool), "qb": R.qb_pop.astype(bool)}
            d = R[pops[pop] & R[pit_col].notna()].assign(pit=lambda x: x[pit_col])
            v = shares(d, reps, rng)
            rows.append({"stage": label, "knob": knob, "value": cfg.get(knob), "shipped": cfg is base, **v})
        table += rows
        if label in flagged:
            best = min(rows, key=lambda r: (abs(r["outside"] - 0.20), not r["shipped"]))
            picks[knob] = best["value"]
    return table, picks


def main_grid(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--flagged", required=True, help="Part A's flagged stages, '|'-separated labels")
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    saved = pd.read_pickle(a.results)
    if saved.get("kind") != "width_tuning":
        sys.exit("--grid reads a backtest --tune-width --tune-grid tier2 --save-results pickle")
    flagged = set(a.flagged.split("|"))
    unknown = flagged - {c[0] for c in CHECKS}
    if unknown:
        sys.exit(f"unknown stage labels: {sorted(unknown)}")
    table, picks = grid_pick(saved["grid"], saved["frames"], a.reps, np.random.default_rng(20261006), flagged)
    for label, knob in STAGE_KNOBS:
        print(f"\n{label} -- {knob}{'' if label in flagged else ' (not flagged: may not move)'}")
        for r in [t for t in table if t["stage"] == label]:
            v = "off" if r["value"] is None else f"{r['value']:g}"
            print(f"  {v:>6}{' (shipped)' if r['shipped'] else '          '}  outside {100 * r['outside']:.1f}%  "
                  f"[{100 * r['ci'][0]:.1f}, {100 * r['ci'][1]:.1f}]  {r['verdict']}"
                  + ("   <- picked" if label in flagged and picks.get(knob) == r["value"] else ""))
    print(f"\npicks: {picks}")
    if a.out:
        Path(a.out).write_text(json.dumps({"table": table, "picks": picks}, indent=1, default=str) + "\n",
                               encoding="utf-8")
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == "--grid":
        return main_grid(argv[1:])
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--seasons", required=True)
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    seasons = [int(x) for x in a.seasons.split(",")]
    saved = pd.read_pickle(a.results)
    R = saved["results"]
    R = R[R.season.isin(seasons)]
    if "pit_tgt" not in R:
        sys.exit("these results have no conditional columns: rerun backtest.py with --conditional")
    R = R.merge(team_margins(seasons), on=["season", "week", "team"], how="left")
    pops = {"rec": R.act_targets.notna(), "rb": R.rush_pop.astype(bool), "qb": R.qb_pop.astype(bool)}
    rng = np.random.default_rng(20261006)
    report = []
    for label, pit_col, vol_col, word, edges, pop in CHECKS:
        d0 = R[pops[pop] & R[pit_col].notna()].assign(pit=lambda x: x[pit_col])
        rows = [("all", shares(d0, a.reps, rng))]
        for lo, hi, lab in edges:
            d = d0[(d0[vol_col] >= lo) & (d0[vol_col] < hi)]
            if len(d):
                rows.append((f"{word} {lab}", shares(d, a.reps, rng)))
        for lo, hi, lab in MARGINS:
            d = d0[(d0.margin >= lo) & (d0.margin < hi)]
            if len(d):
                rows.append((lab, shares(d, a.reps, rng, descriptive=True)))
        n_nom = int(d0.margin.isna().sum())
        if n_nom:
            print(f"  ({n_nom} rows have no final score in games.csv and sit only in 'all')")
        report.append({"check": label, "rows": [{"bucket": b, **v} for b, v in rows]})
        print(f"\n{label}")
        print(f"  {'bucket':<20}{'n':>7}{'<p10':>8}{'>p90':>8}{'outside':>9}   95% CI        verdict")
        for b, v in rows:
            print(f"  {b:<20}{v['n']:>7}{100 * v['below_p10']:>7.1f}%{100 * v['above_p90']:>7.1f}%"
                  f"{100 * v['outside']:>8.1f}%   [{100 * v['ci'][0]:.1f}, {100 * v['ci'][1]:.1f}]   {v['verdict']}")
    if a.out:
        Path(a.out).write_text(json.dumps(report, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

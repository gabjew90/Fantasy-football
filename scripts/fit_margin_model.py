"""Fit and test margin_buckets_v0: the chance of three result scenarios from the closing spread.

    python scripts/fit_margin_model.py [--fit 2018-2021] [--test 2022-2025]

Pre-registered in docs/plans/2026-10-08-report-format-design.md before any result was seen:
- scenarios: the favourite by 9+, within one score (|margin| <= 8, a tie included), the underdog
  by 9+;
- model A (primary): the empirical residuals (result - spread) of the fit seasons, shifted by the
  game's spread; model B: Normal(spread, sd of those residuals); baseline: the fit seasons'
  overall scenario frequencies;
- pass: on the test seasons, 3-way log loss beats the baseline by >= 0.02, AND in each spread band
  (|s| <= 3, 3.5-7, 7.5+) each scenario's mean predicted chance is within 4 points of its observed
  frequency. A if it passes both; else B if B does; else nothing ships.

Writes props/engine/resources/margin_buckets_v0.json (the shipped model's parameters and this
test) and reports/margin_buckets_v0.md. Reads nflverse games.csv through core.fetch.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import fetch  # noqa: E402

SETTINGS = ROOT / "props" / "engine" / "resources" / "margin_settings.json"
# "comfortably" = more than one score (8 points); the engine's renderer reads the same file
COMFORT = int(json.loads(SETTINGS.read_text(encoding="utf-8"))["comfortable_margin"])
SCENARIOS = ("favourite_9plus", "within_one_score", "underdog_9plus")
BANDS = (("|s| <= 3", 0.0, 3.0), ("3.5-7", 3.5, 7.0), ("7.5+", 7.5, 99.0))
LOGLOSS_MARGIN, CAL_TOL = 0.02, 0.04
OUT_JSON = ROOT / "props" / "engine" / "resources" / "margin_buckets_v0.json"
OUT_MD = ROOT / "reports" / "margin_buckets_v0.md"


def favourite_margin(spread_line, result):
    """nflverse: spread_line > 0 means the home team is favoured by that much; result = home -
    away. Returns (s, m): the favourite's expected margin (>= 0) and its actual margin (a pick'em
    is read from the home side)."""
    s = np.asarray(spread_line, dtype=float)
    r = np.asarray(result, dtype=float)
    home_fav = s >= 0
    return np.where(home_fav, s, -s), np.where(home_fav, r, -r)


def outcome(m) -> np.ndarray:
    """0 favourite by 9+, 1 within one score, 2 underdog by 9+."""
    m = np.asarray(m, dtype=float)
    return np.where(m >= COMFORT, 0, np.where(m <= -COMFORT, 2, 1))


def probs_empirical(s, resid) -> np.ndarray:
    """Model A: the share of fitted residuals that, added to the spread, land in each scenario.
    The cut is at COMFORT - 0.5, as in model B: a shifted margin of 8.5 (a whole-number spread
    plus a half-point residual) is between a real 8 and 9, so it counts half to each side."""
    s = np.asarray(s, dtype=float)[:, None]
    m = s + np.asarray(resid, dtype=float)[None, :]
    cut = COMFORT - 0.5
    hi = (m > cut + 1e-9) + 0.5 * (np.abs(m - cut) <= 1e-9)
    lo = (m < -cut - 1e-9) + 0.5 * (np.abs(m + cut) <= 1e-9)
    hi, lo = hi.mean(1), lo.mean(1)
    return np.stack([hi, 1 - hi - lo, lo], 1)


def probs_normal(s, sd) -> np.ndarray:
    """Model B: Normal(s, sd), with the integer margins' half-point continuity (a margin of 9 is
    above 8.5)."""
    from statistics import NormalDist
    s = np.asarray(s, dtype=float)
    hi = np.array([1 - NormalDist(x, sd).cdf(COMFORT - 0.5) for x in s])
    lo = np.array([NormalDist(x, sd).cdf(-COMFORT + 0.5) for x in s])
    return np.stack([hi, 1 - hi - lo, lo], 1)


def log_loss(p, y) -> float:
    p = np.clip(p[np.arange(len(y)), y], 1e-9, 1)
    return float(-np.log(p).mean())


def calibration(p, y, s) -> list[dict]:
    rows = []
    for name, lo, hi in BANDS:
        k = (s >= lo - 1e-9) & (s <= hi + 1e-9)
        for j, sc in enumerate(SCENARIOS):
            rows.append({"band": name, "scenario": sc, "games": int(k.sum()),
                         "predicted": float(p[k, j].mean()) if k.any() else None,
                         "observed": float((y[k] == j).mean()) if k.any() else None})
    return rows


def passes(ll, ll_base, cal) -> tuple[bool, bool]:
    ok_ll = ll_base - ll >= LOGLOSS_MARGIN
    ok_cal = all(r["predicted"] is not None and abs(r["predicted"] - r["observed"]) <= CAL_TOL for r in cal)
    return ok_ll, ok_cal


def choose(verdict: dict) -> str | None:
    """A if it passes both tests; else B if B does; else nothing ships (the pre-registered order)."""
    return next((k for k in ("A_empirical", "B_normal") if all(verdict.get(k, (False, False)))), None)


def band_of(s) -> str | None:
    return next((name for name, lo, hi in BANDS if lo - 1e-9 <= s <= hi + 1e-9), None)


def seasons(arg) -> tuple[int, int]:
    a, b = (int(x) for x in arg.split("-"))
    return a, b


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--fit", default="2018-2021")
    ap.add_argument("--test", default="2022-2025")
    ap.add_argument("--games", help="a local games.csv instead of core.fetch (tests)")
    ap.add_argument("--out-json", default=str(OUT_JSON))
    ap.add_argument("--out-md", default=str(OUT_MD))
    a = ap.parse_args(argv)
    path = Path(a.games) if a.games else fetch.schedule()
    g = pd.read_csv(path, low_memory=False)
    g = g[(g.game_type == "REG") & g.result.notna() & g.spread_line.notna()]
    (f0, f1), (t0, t1) = seasons(a.fit), seasons(a.test)
    fit, test = g[g.season.between(f0, f1)], g[g.season.between(t0, t1)]
    if not len(fit) or not len(test):
        print("no games in the fit or test seasons", file=sys.stderr)
        return 2
    s_fit, m_fit = favourite_margin(fit.spread_line, fit.result)
    resid = m_fit - s_fit
    sd = float(resid.std(ddof=1))
    base = np.bincount(outcome(m_fit), minlength=3) / len(m_fit)
    s_t, m_t = favourite_margin(test.spread_line, test.result)
    y = outcome(m_t)
    pa, pb = probs_empirical(s_t, resid), probs_normal(s_t, sd)
    pbase = np.tile(base, (len(y), 1))
    ll = {"A_empirical": log_loss(pa, y), "B_normal": log_loss(pb, y), "baseline": log_loss(pbase, y)}
    cal = {"A_empirical": calibration(pa, y, s_t), "B_normal": calibration(pb, y, s_t)}
    verdict = {k: passes(ll[k], ll["baseline"], cal[k]) for k in ("A_empirical", "B_normal")}
    ship = choose(verdict)
    rec = {"model": "margin_buckets_v0", "scenarios": list(SCENARIOS), "comfortable_margin": COMFORT,
           "fit_seasons": a.fit, "test_seasons": a.test, "fit_games": int(len(fit)), "test_games": int(len(test)),
           "shipped": ship, "residual_sd": sd,
           "spread_source": "nflverse games.csv spread_line, the closing spread; a run applies it to the "
                            "spread posted at the time of the run, which can differ from the close",
           # exactly the residuals the test used (half points are real: a 3.5 spread, a 7 result)
           "residuals": sorted(float(x) for x in resid) if ship == "A_empirical" else None,
           "log_loss": ll, "baseline_frequencies": base.tolist(),
           "pass_rule": {"log_loss_margin": LOGLOSS_MARGIN, "calibration_tolerance": CAL_TOL},
           "verdict": {k: {"log_loss": v[0], "calibration": v[1]} for k, v in verdict.items()},
           "calibration": cal}
    Path(a.out_json).write_text(json.dumps(rec, indent=1), encoding="utf-8")
    L = ["# margin_buckets_v0: result scenarios from the closing spread", "",
         f"Pre-registered in docs/plans/2026-10-08-report-format-design.md. Fit {a.fit} ({len(fit)} games), "
         f"test {a.test} ({len(test)} games), regular season, nflverse closing spread_line. A report applies "
         "the model to the spread posted when it runs, which can differ from the close: the test measured "
         "closing spreads only.", "",
         f"**Shipped: {ship or 'nothing (neither model passed): the report prints not estimated'}.**", "",
         "| Model | Test log loss | Beats baseline by 0.02 | Calibration within 4 points |", "|---|---:|---|---|"]
    for k in ("A_empirical", "B_normal"):
        L.append(f"| {k} | {ll[k]:.4f} | {'yes' if verdict[k][0] else 'NO'} | {'yes' if verdict[k][1] else 'NO'} |")
    L += [f"| baseline (fit-season frequencies {', '.join(f'{x:.3f}' for x in base)}) | {ll['baseline']:.4f} | - | - |", "",
          f"Residual sd on the fit seasons: {sd:.2f} points.", ""]
    for k in ("A_empirical", "B_normal"):
        L += [f"## Calibration, {k}", "", "| Spread band | Scenario | Games | Predicted | Observed | Gap |",
              "|---|---|---:|---:|---:|---:|"]
        for r in cal[k]:
            if r["predicted"] is None:
                L.append(f"| {r['band']} | {r['scenario']} | 0 | - | - | no games (fails the rule) |")
                continue
            L.append(f"| {r['band']} | {r['scenario']} | {r['games']} | {100 * r['predicted']:.1f}% | "
                     f"{100 * r['observed']:.1f}% | {100 * (r['predicted'] - r['observed']):+.1f} |")
        L.append("")
    Path(a.out_md).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L[:12]))
    return 0


if __name__ == "__main__":
    sys.exit(main())

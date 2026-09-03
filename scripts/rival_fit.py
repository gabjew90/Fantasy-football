"""Fit the rival pick model on observed picks (plan 2026-09-03 s3, DECISIONS #35).

Input: data/processed/rival_pools.jsonl from scripts/pick_dataset.py -- per
rival pick, the candidate pool at that moment (Yahoo rank, board ADP, whether
the position fits an open starter slot) and which candidate was taken.

Likelihood: multinomial over the pool. Forms, per seat class:
  (i)   gauss_adp   weights exp(-0.5 ((pick - adp) / sigma(round))^2) x need
  (ii)  gauss_yrank the same centred on Yahoo's default rank
  (iii) mixture     pi x 1[taken == lowest-yrank candidate that fits an open
                    starter slot] + (1 - pi) x (i)   (starters-first one-hot)
  current           what the engine does today: humans = (i) at sigma 6->27,
                    need 0.15; autopick seats = (i) with sigma x 0.5 and
                    need 0.02   (the baseline every gate compares against)

Estimation: direct likelihood on the coarse grid from DECISIONS #35 (no
finer), 1-D Wilks 90% profiles for pi and the sigmas. Selection: leave-one-
room-out held-out log-likelihood per pick. Output reports/rival_fit.md + .json.

    venv\\Scripts\\python.exe scripts\\rival_fit.py
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]

GRID = {
    "sigma_early": (4.0, 6.0, 8.0, 10.0),
    "sigma_late": (15.0, 21.0, 27.0, 35.0),
    "need_damp": (0.15, 0.30, 0.45),
    "pi": tuple(round(x * 0.1, 1) for x in range(0, 11)),
    "scale": (0.75, 1.0, 1.5, 2.0),
}
CURRENT_HUMAN = {"sigma_early": 6.0, "sigma_late": 27.0, "need_damp": 0.15}
CURRENT_AUTOPICK = {"scale": 0.5, "need_damp": 0.02}
ROUNDS = 15
KDEF_EARLY_DAMP, KDEF_TYPICAL_ROUND = 0.02, 13
WILKS_90 = 2.706 / 2.0          # chi2(1) 90% quantile / 2, on the log-lik scale
EPS = 1e-12


# ---------------------------------------------------------------- data

def load_pools(path: Path) -> list[dict]:
    recs = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        d = json.loads(line)
        d["yrank_a"] = np.array([x if x is not None else 9999.0 for x in d["yrank"]], dtype=float)
        d["adp_a"] = np.array([x if x is not None else 200.0 for x in d["adp"]], dtype=float)   # the engine's own missing-ADP value
        d["fits_a"] = np.array(d["fits"], dtype=bool)
        d["kdef_a"] = np.array([p in ("K", "DEF") for p in d["pos"]], dtype=bool)
        recs.append(d)
    return recs


# ---------------------------------------------------------------- likelihood

def sigma_at(rnd: int, se: float, sl: float) -> float:
    return se + (sl - se) * (rnd - 1) / max(1, ROUNDS - 1)


def need_mult(d: dict, need_damp: float) -> np.ndarray:
    m = np.where(d["fits_a"] | (not d["starters_open"]), 1.0, need_damp)
    if d["round"] < KDEF_TYPICAL_ROUND - 1:
        m = np.where(d["kdef_a"], KDEF_EARLY_DAMP, m)
    return m


def p_gauss(d: dict, centre: np.ndarray, sigma: float, need_damp: float) -> float:
    w = np.exp(-0.5 * ((d["pick_no"] - centre) / sigma) ** 2) + 1e-9
    w = w * need_mult(d, need_damp)
    return float(w[d["taken"]] / w.sum())


def list_hit(d: dict) -> bool:
    """Is the taken candidate the lowest-yrank one that fits an open starter
    slot (any candidate when no starter is open)? Pools are sorted by yrank."""
    fits = d["fits_a"] if d["starters_open"] else np.ones(len(d["fits_a"]), dtype=bool)
    idx = np.flatnonzero(fits & (d["yrank_a"] < 9999))
    return bool(len(idx)) and int(idx[0]) == d["taken"]


def loglik(recs: list[dict], form: str, params: dict) -> float:
    total = 0.0
    for d in recs:
        se, sl, nd = params["sigma_early"], params["sigma_late"], params["need_damp"]
        sig = sigma_at(d["round"], se, sl) * params.get("scale", 1.0)
        if form == "gauss_adp":
            p = p_gauss(d, d["adp_a"], sig, nd)
        elif form == "gauss_yrank":
            p = p_gauss(d, d["yrank_a"], sig, nd)
        elif form == "mixture":
            pi = params["pi"]
            p = pi * (1.0 if list_hit(d) else 0.0) + (1.0 - pi) * p_gauss(d, d["adp_a"], sig, nd)
        else:
            raise ValueError(form)
        total += math.log(max(p, EPS))
    return total


def current_params(seat_class: str) -> tuple[str, dict]:
    """Today's engine as a (form, params) pair per class."""
    if seat_class in ("away", "instant"):
        return "gauss_adp", dict(CURRENT_HUMAN, scale=CURRENT_AUTOPICK["scale"], need_damp=CURRENT_AUTOPICK["need_damp"])
    return "gauss_adp", dict(CURRENT_HUMAN)


def grid_points(form: str, with_scale: bool):
    keys = ["sigma_early", "sigma_late", "need_damp"] + (["pi"] if form == "mixture" else []) + (["scale"] if with_scale else [])
    for combo in itertools.product(*[GRID[k] for k in keys]):
        yield dict(zip(keys, combo))


def fit(recs: list[dict], form: str, with_scale: bool) -> tuple[dict, float, dict]:
    """Best grid point, its log-lik, and the 1-D Wilks profiles."""
    best, best_ll, table = None, -math.inf, {}
    for pt in grid_points(form, with_scale):
        ll = loglik(recs, form, pt)
        table[tuple(sorted(pt.items()))] = ll
        if ll > best_ll:
            best, best_ll = pt, ll
    profiles = {}
    for k in best:
        prof = {}
        for v in GRID[k]:
            prof[v] = max(ll for key, ll in table.items() if dict(key)[k] == v)
        inside = [v for v, ll in prof.items() if best_ll - ll <= WILKS_90]
        profiles[k] = {"profile": prof, "ci90": (min(inside), max(inside))}
    return best, best_ll, profiles


# ---------------------------------------------------------------- study

def by_class(recs: list[dict]) -> dict:
    out = defaultdict(list)
    for d in recs:
        out[d["seat_class"]].append(d)
    return out


def loro(recs: list[dict], form: str, with_scale: bool, baseline: tuple[str, dict]) -> list[dict]:
    rooms = sorted({d["room"] for d in recs})
    rows = []
    for held in rooms:
        train = [d for d in recs if d["room"] != held]
        test = [d for d in recs if d["room"] == held]
        if not train or not test:
            continue
        pt, _ll, _prof = fit(train, form, with_scale)
        rows.append({"room": held, "n_test": len(test), "fitted": pt,
                     "ll_fitted_per_pick": loglik(test, form, pt) / len(test),
                     "ll_current_per_pick": loglik(test, *baseline) / len(test)})
    return rows


def fmt_pt(pt: dict) -> str:
    return ", ".join(f"{k}={v}" for k, v in pt.items())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", default=str(ROOT / "data" / "processed" / "rival_pools.jsonl"))
    ap.add_argument("--classes", default="away,human,unknown")
    ap.add_argument("--out", default=str(ROOT / "reports" / "rival_fit.md"))
    a = ap.parse_args()
    recs = load_pools(Path(a.pools))
    classes = by_class(recs)
    L = ["# Rival pick model fit (DECISIONS #35)", "",
         f"{len(recs)} rival picks over {len({d['room'] for d in recs})} rooms from {a.pools}. "
         "Multinomial likelihood over the candidate pool at each pick; grid from #35, values at grid precision; "
         "Wilks 90% intervals from 1-D profiles; selection by leave-one-room-out (LORO) log-likelihood per pick. "
         "`current` = the engine's model today.", ""]
    result = {}
    for cls in [c.strip() for c in a.classes.split(",")]:
        rs = classes.get(cls) or []
        if len(rs) < 20:
            L += [f"## {cls}: n={len(rs)} -- too few picks to fit", ""]
            continue
        with_scale = cls in ("away", "instant")
        base = current_params(cls)
        ll_cur = loglik(rs, *base) / len(rs)
        hits = sum(1 for d in rs if list_hit(d)) / len(rs)
        L += [f"## seat class `{cls}` (n={len(rs)}, rooms {len({d['room'] for d in rs})})", "",
              f"Exact list-hit share (lowest Yahoo rank among open-starter fits): {hits:.2f}. "
              f"Current engine log-lik per pick: {ll_cur:.3f}.", "",
              "| form | best grid point | log-lik / pick (in-sample) | vs current |", "|---|---|---|---|"]
        fits_out = {}
        for form in ("gauss_adp", "gauss_yrank", "mixture"):
            pt, ll, prof = fit(rs, form, with_scale)
            fits_out[form] = {"point": pt, "ll_per_pick": ll / len(rs), "profiles": {k: {"ci90": v["ci90"]} for k, v in prof.items()}}
            L.append(f"| {form} | {fmt_pt(pt)} | {ll / len(rs):.3f} | {ll / len(rs) - ll_cur:+.3f} |")
        L.append("")
        # profiles for the mixture
        mp = fits_out["mixture"]["profiles"]
        L += ["Mixture 90% intervals (grid): " + "; ".join(f"{k} in [{v['ci90'][0]}, {v['ci90'][1]}]" for k, v in mp.items()), ""]
        # LORO for the mixture and for gauss_yrank vs current
        lo_rows = {}
        for form in ("mixture", "gauss_yrank", "gauss_adp"):
            lo_rows[form] = loro(rs, form, with_scale, base)
        if lo_rows["mixture"]:
            L += ["LORO held-out log-lik per pick (fit on the other rooms, scored on the held-out room):", "",
                  "| held-out room | n | mixture | gauss_yrank | gauss_adp | current |", "|---|---|---|---|---|---|"]
            for i, r in enumerate(lo_rows["mixture"]):
                L.append(f"| {r['room']} | {r['n_test']} | {r['ll_fitted_per_pick']:.3f} | {lo_rows['gauss_yrank'][i]['ll_fitted_per_pick']:.3f} | "
                         f"{lo_rows['gauss_adp'][i]['ll_fitted_per_pick']:.3f} | {r['ll_current_per_pick']:.3f} |")
            pooled = {f: sum(r["ll_fitted_per_pick"] * r["n_test"] for r in lo_rows[f]) / sum(r["n_test"] for r in lo_rows[f]) for f in lo_rows}
            cur_pooled = sum(r["ll_current_per_pick"] * r["n_test"] for r in lo_rows["mixture"]) / sum(r["n_test"] for r in lo_rows["mixture"])
            L.append(f"| **pooled** | {sum(r['n_test'] for r in lo_rows['mixture'])} | {pooled['mixture']:.3f} | {pooled['gauss_yrank']:.3f} | {pooled['gauss_adp']:.3f} | {cur_pooled:.3f} |")
            L.append("")
            fits_out["loro"] = {"rows": lo_rows, "pooled": pooled, "current_pooled": cur_pooled}
        result[cls] = fits_out
    # G1 statement for the away class
    aw = result.get("away", {})
    if aw.get("loro"):
        g1_ll = aw["loro"]["pooled"]["mixture"] > aw["loro"]["current_pooled"]
        ci = aw["mixture"]["profiles"]["pi"]["ci90"]
        g1_ci = ci[0] > 0.0
        L += ["## G1 (pre-registered)", "",
              f"LORO mixture log-lik per pick {aw['loro']['pooled']['mixture']:.3f} vs current {aw['loro']['current_pooled']:.3f}: "
              f"{'better' if g1_ll else 'NOT better'}. pi_away 90% interval [{ci[0]}, {ci[1]}]: "
              f"{'excludes 0' if g1_ci else 'includes 0'}. **G1 {'PASS' if (g1_ll and g1_ci) else 'FAIL'}.**", ""]
        result["G1"] = {"pass": bool(g1_ll and g1_ci), "loro_mixture": aw["loro"]["pooled"]["mixture"], "loro_current": aw["loro"]["current_pooled"], "pi_ci90": ci}
    out = Path(a.out)
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    out.with_suffix(".json").write_text(json.dumps(result, indent=1, default=str), encoding="utf-8")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""dispersion_v0: a calibrated weekly range around a mean projection.

WHAT IT IS. For each position and projection size, the empirical quantiles of
(actual points - projected points), measured on Sleeper's pre-game weekly
projections against Sleeper's weekly actuals, scored in the league's own
scoring. A mean of 14.2 for a WR becomes p10/p25/p50/p75/p90 by adding that
bucket's residual quantiles. Between bucket centres the residuals are
interpolated linearly, so a 11.9 and a 12.1 projection do not jump.

WHAT IT IS NOT. Not a model of football: no usage, matchup or game script. It
answers one question -- how far does a week land from a projection of this
size at this position -- which is exactly what the start/sit rule needs to
compare a floor with a floor. Conditional on playing: a player who does not
suit up is an availability question, answered by the injury report.

VALIDATION (the harness, `python -m fantasy.dispersion fit`). Fit on one
season, scored on the next, never on the season it was fitted to:
  * coverage -- the share of outcomes below each predicted quantile should be
    the quantile itself (10% below p10, 90% below p90); with ties on a
    quantile (a TE's 0.0 weeks) it is the bracket [strictly below, at or below];
  * pinball loss against a baseline normal sized to each projection bucket and
    floored like the table -- it must beat the baseline to be `live`, which
    asks whether the empirical shape adds anything over a scaled bell curve.
The report lands in reports/dispersion_v0.<league>.md; the fitted table in
fantasy/resources/dispersion_v0.<league>.json.

Applying it to a mean from another source (market_points) assumes that source
misses by about as much as Sleeper does; the range is labelled with where it
came from so a report can say so.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import statistics
import sys
from dataclasses import replace
from pathlib import Path

from core import fetch as F
from core.manifest import Manifest
from core.scoring import league_scoring, score

from .contract import QUANTILES, Projection, fantasy_position, validate

NAME = "dispersion_v0"
ROOT = Path(__file__).resolve().parent.parent
RESOURCES = Path(__file__).resolve().parent / "resources"
POSITIONS = ("QB", "RB", "WR", "TE")
BIN_EDGES = (0.5, 3, 6, 9, 12, 15, 18, 22, 1e9)
MIN_BIN_N = 150
WEEKS = range(1, 18)          # week 18 carries resting starters; left out of the fit
_NOT_STATS = ("adp_", "pos_adp_", "pts_", "pos_rank_")


# ------------------------------------------------------------------ data

def _line(stats: dict) -> dict:
    return {k: v for k, v in (stats or {}).items()
            if not k.startswith(_NOT_STATS) and k != "gp" and v is not None}


def week_pairs(proj_rows: list, stats: dict, scoring: dict) -> list[tuple[str, float, float]]:
    """(position, projected, actual) for every player projected >= the first
    bin edge who actually played that week."""
    out = []
    for r in proj_rows or []:
        pid = str(r.get("player_id") or "")
        pos = fantasy_position(r.get("player"))
        if pos not in POSITIONS:
            continue
        proj = score(_line(r.get("stats")), scoring)
        if proj < BIN_EDGES[0]:
            continue
        a = stats.get(pid)
        if not a or not a.get("gp"):
            continue
        out.append((pos, proj, score(_line(a), scoring)))
    return out


def season_pairs(season: int, scoring: dict, *, weeks=WEEKS, cache_dir=None, manifest=None):
    pairs = []
    for w in weeks:
        proj = json.loads(F.sleeper_projections(season, w, cache_dir=cache_dir, manifest=manifest)
                          .read_text(encoding="utf-8"))
        stats = json.loads(F.sleeper_stats(season, w, cache_dir=cache_dir, manifest=manifest)
                           .read_text(encoding="utf-8"))
        pairs += week_pairs(proj, stats, scoring)
    return pairs


# ----------------------------------------------------------------- the fit

def _quantile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolated sample quantile of already-sorted values."""
    if not sorted_vals:
        raise ValueError("empty sample")
    x = q * (len(sorted_vals) - 1)
    lo = math.floor(x)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (x - lo)


def _bins_for(rows: list[tuple[float, float]]) -> list[dict]:
    """Bucket (projected, actual) rows on BIN_EDGES, merging any bucket with
    fewer than MIN_BIN_N rows into its lower neighbour (the sparse ones are the
    big projections at the top)."""
    groups = []
    for lo, hi in zip(BIN_EDGES, BIN_EDGES[1:]):
        groups.append({"lo": lo, "hi": hi, "rows": [r for r in rows if lo <= r[0] < hi]})
    merged = []
    for g in groups:
        if merged and len(g["rows"]) < MIN_BIN_N:
            merged[-1]["hi"] = g["hi"]
            merged[-1]["rows"] += g["rows"]
        else:
            merged.append(g)
    # a thin FIRST bucket folds upward
    while len(merged) > 1 and len(merged[0]["rows"]) < MIN_BIN_N:
        merged[1]["lo"] = merged[0]["lo"]
        merged[1]["rows"] = merged[0]["rows"] + merged[1]["rows"]
        merged.pop(0)
    out = []
    for g in merged:
        if not g["rows"]:
            continue
        resid = sorted(a - p for p, a in g["rows"])
        out.append({"lo": g["lo"], "hi": g["hi"], "n": len(g["rows"]),
                    "center": round(statistics.median(p for p, _ in g["rows"]), 3),
                    "resid": {str(q): round(_quantile(resid, q), 3) for q in QUANTILES}})
    return out


def fit(pairs: list[tuple[str, float, float]]) -> dict:
    table = {"model": NAME, "quantiles": list(QUANTILES), "positions": {}}
    for pos in POSITIONS:
        rows = [(p, a) for ps, p, a in pairs if ps == pos]
        if not rows:
            continue
        actual = sorted(a for _, a in rows)
        table["positions"][pos] = {"bins": _bins_for(rows), "n": len(rows),
                                   "floor": round(_quantile(actual, 0.005), 2)}
    return table


def quantiles_for(table: dict, pos: str, mean: float) -> dict | None:
    """{q: points} for a `mean` projection at `pos`, or None when the position
    was never fitted (K, DEF)."""
    t = table["positions"].get(pos)
    if not t or not t["bins"]:
        return None
    bins = t["bins"]
    if mean <= bins[0]["center"]:
        res = {q: bins[0]["resid"][str(q)] for q in QUANTILES}
    elif mean >= bins[-1]["center"]:
        res = {q: bins[-1]["resid"][str(q)] for q in QUANTILES}
    else:
        for a, b in zip(bins, bins[1:]):
            if a["center"] <= mean <= b["center"]:
                span = b["center"] - a["center"]
                w = (mean - a["center"]) / span if span > 0 else 0.0
                res = {q: (1 - w) * a["resid"][str(q)] + w * b["resid"][str(q)] for q in QUANTILES}
                break
    out, prev = {}, -1e9
    for q in QUANTILES:           # floor at the position's observed minimum, keep monotone
        v = max(t["floor"], mean + res[q], prev)
        out[q] = round(v, 2)
        prev = v
    return out


def apply(p: Projection, table: dict) -> Projection:
    """`p` with the range model's quantiles, unless it already carries its own."""
    if p.quantiles:
        return p
    pos = p.detail.get("pos")
    q = quantiles_for(table, pos, p.mean)
    if q is None:
        return p
    # the position's validation caveats travel with every range built from it
    cav = [c for c in (table.get("validation") or {}).get("caveats", []) if c.split(" ", 1)[0].rstrip(":") == pos]
    detail = dict(p.detail, range_caveats=cav) if cav else p.detail
    return validate(replace(p, quantiles=q, detail=detail,
                            range_from=f"{NAME} (fitted on sleeper_weekly errors)"))


# -------------------------------------------------------------- validation

def _normal_baseline(table: dict, pairs) -> dict:
    """The competitor the table must beat: a normal sized to each projection
    bucket (the residual mean and spread of the SAME buckets, from the same
    training pairs) and floored like the model. A single per-position normal
    was too easy to beat -- a bucketed, floored table wins against it almost
    by construction (code review 2026-09-24) -- so the gate now asks whether
    the empirical SHAPE adds anything over a scaled normal."""
    out = {}
    for pos, t in table["positions"].items():
        rows = [(p, a) for ps, p, a in pairs if ps == pos]
        buckets = []
        for b in t["bins"]:
            r = [a - p for p, a in rows if b["lo"] <= p < b["hi"]]
            if len(r) > 2:
                buckets.append((b["lo"], b["hi"], statistics.mean(r), statistics.pstdev(r)))
        if buckets:
            out[pos] = {"buckets": buckets, "floor": t["floor"]}
    return out


def _baseline_q(base: dict, p: float, q: float) -> float:
    bk = base["buckets"]
    mu, sd = next(((m, s) for lo, hi, m, s in bk if lo <= p < hi),
                  (bk[0][2], bk[0][3]) if p < bk[0][0] else (bk[-1][2], bk[-1][3]))
    return max(base["floor"], p + mu + sd * _ndtri(q))


def _ndtri(q: float) -> float:
    """Inverse standard normal CDF (Acklam's rational approximation)."""
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    lo, hi = 0.02425, 1 - 0.02425
    if q < lo:
        t = math.sqrt(-2 * math.log(q))
        return (((((c[0]*t+c[1])*t+c[2])*t+c[3])*t+c[4])*t+c[5]) / ((((d[0]*t+d[1])*t+d[2])*t+d[3])*t+1)
    if q > hi:
        t = math.sqrt(-2 * math.log(1 - q))
        return -(((((c[0]*t+c[1])*t+c[2])*t+c[3])*t+c[4])*t+c[5]) / ((((d[0]*t+d[1])*t+d[2])*t+d[3])*t+1)
    t = q - 0.5
    r = t * t
    return (((((a[0]*r+a[1])*r+a[2])*r+a[3])*r+a[4])*r+a[5])*t / (((((b[0]*r+b[1])*r+b[2])*r+b[3])*r+b[4])*r+1)


def _pinball(q: float, pred: float, actual: float) -> float:
    d = actual - pred
    return max(q * d, (q - 1) * d)


def evaluate(table: dict, test_pairs, baseline_pairs) -> dict:
    """Out-of-sample coverage and pinball loss, by position and overall, with
    the normal baseline fitted on the same training pairs as the table."""
    base = _normal_baseline(table, baseline_pairs)
    rep = {}
    for pos in list(POSITIONS) + ["ALL"]:
        rows = [(p, a, ps) for ps, p, a in test_pairs if pos in ("ALL", ps)]
        rows = [r for r in rows if r[2] in base and table["positions"].get(r[2])]
        if not rows:
            continue
        # Fantasy points have atoms (a tight end's 0.0, a floor the range sits on),
        # so coverage is a bracket: the share strictly below a quantile and the
        # share at or below it. A calibrated quantile q lies inside the bracket.
        # Counting only `<=` read 24.5% of 2025 TEs sitting exactly on a p10 of
        # 0.0 as "below p10" (2026-09-24), which is a tie, not a miss.
        below = {q: 0 for q in QUANTILES}
        below_strict = {q: 0 for q in QUANTILES}
        inside80 = pin_m = pin_b = 0.0
        widths = []
        for p, a, ps in rows:
            qm = quantiles_for(table, ps, p)
            for q in QUANTILES:
                below[q] += a <= qm[q]
                below_strict[q] += a < qm[q]
                pin_m += _pinball(q, qm[q], a)
                pin_b += _pinball(q, _baseline_q(base[ps], p, q), a)
            inside80 += qm[0.10] <= a <= qm[0.90]
            widths.append(qm[0.90] - qm[0.10])
        n = len(rows)
        rep[pos] = {"n": n, "coverage": {str(q): round(below[q] / n, 3) for q in QUANTILES},
                    "coverage_strict": {str(q): round(below_strict[q] / n, 3) for q in QUANTILES},
                    "inside_p10_p90": round(inside80 / n, 3),
                    "mean_width_p10_p90": round(statistics.mean(widths), 2),
                    "pinball_model": round(pin_m / (n * len(QUANTILES)), 4),
                    "pinball_normal": round(pin_b / (n * len(QUANTILES)), 4)}
    return rep


def _off_by(r: dict, q: float) -> float:
    """How far level q sits outside the [strictly below, at or below] bracket."""
    lo, hi = r["coverage_strict"][str(q)], r["coverage"][str(q)]
    return 0.0 if lo <= q <= hi else min(abs(q - lo), abs(q - hi))


def verdict(rep: dict, tol: float = 0.05) -> tuple[bool, list[str]]:
    """Live only if, overall, every quantile's coverage bracket is within `tol`
    of its level and the model beats the normal baseline on pinball loss."""
    why = []
    allr = rep.get("ALL")
    if not allr:
        return False, ["no test rows"]
    for q in QUANTILES:
        if _off_by(allr, q) > tol:
            why.append(f"coverage at p{int(q*100)} is {allr['coverage_strict'][str(q)]:.1%}-"
                       f"{allr['coverage'][str(q)]:.1%}, outside {q:.0%} +/- {tol:.0%}")
    if allr["pinball_model"] >= allr["pinball_normal"]:
        why.append(f"pinball {allr['pinball_model']} does not beat the normal baseline {allr['pinball_normal']}")
    return not why, why


def caveats(rep: dict, tol: float = 0.03) -> list[str]:
    """Positions whose own coverage misses by more than `tol` -- reported with
    the range, never tuned away."""
    out = []
    for pos, r in rep.items():
        if pos == "ALL":
            continue
        for q in QUANTILES:
            if _off_by(r, q) > tol:
                out.append(f"{pos} p{int(q*100)}: {r['coverage_strict'][str(q)]:.1%}-{r['coverage'][str(q)]:.1%} "
                           f"of outcomes vs {q:.0%}")
        if r["pinball_model"] >= r["pinball_normal"]:
            out.append(f"{pos}: no better than the normal baseline "
                       f"({r['pinball_model']:.3f} vs {r['pinball_normal']:.3f})")
    return out


def report_markdown(league: str, fit_season: int, test_season: int, table: dict, rep: dict,
                    ok: bool, why: list[str], manifest: Manifest) -> str:
    L = [f"# dispersion_v0 -- {league}", "",
         f"*Built {dt.date.today().isoformat()} by `python -m fantasy.dispersion fit --league {league}`. "
         f"Fitted on {fit_season} Sleeper weekly projections vs actuals (weeks {WEEKS.start}-{WEEKS.stop - 1}), "
         f"scored in {league}'s scoring; tested on {test_season}, which the fit never saw.*", "",
         f"**Verdict: {'PASS -- live' if ok else 'FAIL -- not live'}.**" + ("" if ok else " " + "; ".join(why)), "",
         "Coverage is the share of outcomes at or below each predicted quantile; a calibrated range puts 10% "
         "below p10 and 90% below p90. Pinball loss scores the whole range (lower is better) against a normal "
         "baseline: a normal sized to each projection bucket (that bucket's residual mean and spread in the "
         "same training season) and floored like the model, so the test is whether the empirical shape adds "
         "anything over a scaled bell curve.", "",
         "| Position | Test rows | below p10 | below p25 | below p50 | below p75 | below p90 | inside p10-p90 "
         "| mean width | pinball (model) | pinball (normal) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    def cov(r, q):
        lo, hi = r["coverage_strict"][q], r["coverage"][q]
        return f"{hi:.1%}" if abs(hi - lo) < 0.0005 else f"{lo:.1%}-{hi:.1%}"
    for pos, r in rep.items():
        L.append(f"| {pos} | {r['n']} | " + " | ".join(cov(r, q) for q in ("0.1", "0.25", "0.5", "0.75", "0.9"))
                 + f" | {r['inside_p10_p90']:.1%} | {r['mean_width_p10_p90']:.1f} | "
                 f"{r['pinball_model']:.3f} | {r['pinball_normal']:.3f} |")
    cav = caveats(rep)
    L += ["", "A coverage shown as a range (6.7%-31.2%) is the share strictly below the quantile and the share at "
          "or below it; they differ when outcomes tie on the quantile, as tight ends' 0.0 weeks do on a p10 of "
          "0.0. A calibrated quantile falls inside the range.", "",
          "**Position caveats** (more than 3 points off, or no better than the baseline) -- shown with every "
          "range built from this table, not tuned away:", ""]
    L += [f"- {c}" for c in cav] or ["- none"]
    L += ["", "## The fitted table (residual quantiles, points)", ""]
    for pos, t in table["positions"].items():
        L += [f"**{pos}** ({t['n']} player-weeks, floor {t['floor']})", "",
              "| projected | n | centre | p10 | p25 | p50 | p75 | p90 |", "|---|---|---|---|---|---|---|---|"]
        for b in t["bins"]:
            hi = "+" if b["hi"] >= 1e8 else f"-{b['hi']:g}"
            r = b["resid"]
            L.append(f"| {b['lo']:g}{hi} | {b['n']} | {b['center']:.1f} | {r['0.1']:+.1f} | {r['0.25']:+.1f} | "
                     f"{r['0.5']:+.1f} | {r['0.75']:+.1f} | {r['0.9']:+.1f} |")
        L.append("")
    L += ["## Leakage check", "",
          "Sleeper serves past weeks' projections with a last_modified after the week's first kickoff. A "
          "projection revised with the result would show residuals near zero; the 2024 residual spread was "
          "about 7 points per player-week (checked 2026-09-24), which pre-game projections produce. The late "
          "timestamps are the final pre-kickoff updates (inactives), which a start/sit decision also has.", "",
          f"*{manifest.summary_line().replace('inputs: ', 'Inputs: ')[:400]}...*"]
    return "\n".join(L)


def table_path(league: str) -> Path:
    return RESOURCES / f"{NAME}.{league}.json"


def load_table(league: str) -> dict | None:
    p = table_path(league)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m fantasy.dispersion")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fit", help="fit on one season, test on the next, write table + report")
    f.add_argument("--league", required=True)
    f.add_argument("--fit-season", type=int, default=2024)
    f.add_argument("--test-season", type=int, default=2025)
    a = ap.parse_args(argv)

    sys.path.insert(0, str(ROOT))
    from draftkit.config import Config
    cfg = Config.load(league=a.league)
    scoring = league_scoring(cfg)
    m = Manifest(f"{NAME} fit {a.league}")
    train = season_pairs(a.fit_season, scoring, manifest=m)
    test = season_pairs(a.test_season, scoring, manifest=m)
    table = fit(train)
    table.update({"league": a.league, "fit_season": a.fit_season, "test_season": a.test_season,
                  "built": dt.date.today().isoformat()})
    rep = evaluate(table, test, train)
    ok, why = verdict(rep)
    table["validation"] = {"passed": ok, "why": why, "overall": rep.get("ALL"), "caveats": caveats(rep)}
    RESOURCES.mkdir(parents=True, exist_ok=True)
    table_path(a.league).write_text(json.dumps(table, indent=1, sort_keys=True), encoding="utf-8")
    out = ROOT / "reports" / f"{NAME}.{a.league}.md"
    out.write_text(report_markdown(a.league, a.fit_season, a.test_season, table, rep, ok, why, m) + "\n",
                   encoding="utf-8")
    print(f"{a.league}: {len(train)} train / {len(test)} test player-weeks; "
          f"{'PASS' if ok else 'FAIL'} {'; '.join(why)}")
    print(f"wrote {table_path(a.league)} and {out}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

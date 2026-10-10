"""Tuning and the pre-registered tests (design note, "Testing"; the user's
step E2, 2026-10-10).

    python -m props.calc.harness extract --seasons 2018-2023   # cases, through player.build
    python -m props.calc.harness tune                          # grids on 2018-2023 only
    python -m props.calc.harness test  --seasons 2018-2023     # conversion, spread, round trip
    python -m props.calc.harness heldout                       # 2024-25, ONCE (refuses a second run)

Who is tested (design note): for each team and week, the lead back (the team's
carry leader over its games that season before the week) and its top three by
targets over the same games, each with at least `tested_min_prior_games`
games for that team that season before the week. Passing yards (the brief
names no group for it; the analogous choice, stated in the report): the
team's completion leader over the same games. A player who did not play in the
priced week is left out (Sleeper voids that leg). Every case is built with the
calculator's own player.build, cut at the priced week.

Grids are fixed here before any run (PRE-REGISTERED). Tuning order: the
three r settings on the spread test (coverage nearest 80%), then k_ypc with
day_sd, k_catch, k_ypr (k_catch fixed) and k_ypcomp, each on the log loss of
the conversion test's Overs.

Outputs go to props/calc/.cache/harness/ (gitignored); results are written
up in the design note by hand.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from . import calc, player, settings
from .card import half_up
from .checks import DataError, require

OUT = Path(__file__).resolve().parent / ".cache" / "harness"
HELDOUT_MARK = Path(__file__).resolve().parent / "heldout_read.json"     # committed: the read happens once
TUNE_SEASONS = tuple(range(2018, 2024))
HELDOUT_SEASONS = (2024, 2025)

# PRE-REGISTERED grids (2026-10-10, before any run)
GRIDS = {
    "carry_r": [4, 6, 8, 10, 12, 16, 20, 25, 30, 40, 60],
    "target_r": [2, 3, 4, 5, 6, 8, 10, 12, 16, 20, 30],
    "completion_r": [4, 6, 8, 10, 12, 16, 20, 25, 30, 40, 60],
    "k_ypc": [25, 50, 100, 150, 200, 300, 500, 800],
    "day_sd": [0.0, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
    "k_catch": [10, 20, 40, 60, 100, 150, 250, 400],
    "k_ypr": [10, 25, 50, 100, 150, 250, 400],
    "k_ypcomp": [25, 50, 100, 150, 250, 400, 800],
}
KIND = {"rush_yds": "carries", "receptions": "targets", "rec_yds": "targets", "pass_yds": "completions"}
R_KEY = {"carries": "carry_r", "targets": "target_r", "completions": "completion_r"}
STAT = {"rush_yds": "rush_yds", "receptions": "receptions", "rec_yds": "rec_yds", "pass_yds": "pass_yds"}
BANDS = [(0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.7), (0.7, 0.8)]
CLIP = 1e-4


def _seasons(text: str) -> tuple:
    a, _, b = text.partition("-")
    return tuple(range(int(a), int(b or a) + 1))


# ------------------------------------------------------------------ who is tested

def tested(b: player.Bundle, season: int, week: int, min_games: int) -> list[tuple]:
    """(gsis_id, team, market) for every tested player in one week."""
    g = b.games[(b.games["season"] == season)]
    before, now = g[g["week"] < week], g[g["week"] == week]
    out = []
    for team, tg in before.groupby("team"):
        played = tg.groupby("gsis_id")["game_id"].nunique()
        ok = set(played[played >= min_games].index)
        now_t = set(now.loc[now["team"] == team, "gsis_id"])
        sums = tg.groupby("gsis_id")[["carries", "targets", "completions"]].sum()
        sums = sums[sums.index.isin(ok)].sort_index()          # a tie goes to the smaller id
        if sums.empty:
            continue
        lead = sums["carries"].idxmax() if sums["carries"].max() > 0 else None
        top3 = list(sums[sums["targets"] > 0].sort_values("targets", ascending=False, kind="stable").index[:3])
        qb = sums["completions"].idxmax() if sums["completions"].max() > 0 else None
        for gid, markets in ((lead, ("rush_yds",)), (qb, ("pass_yds",))):
            if gid is not None and gid in now_t:
                out += [(gid, team, m) for m in markets]
        out += [(gid, team, m) for gid in top3 if gid in now_t for m in ("receptions", "rec_yds")]
    return out


def extract(seasons: tuple, fixed: dict, tuned: dict) -> pd.DataFrame:
    """One row per tested player-week-market: the blend inputs for every k,
    his trailing-4 average, the actual workload and stat, and the pool and
    depth mix the calculator would draw from. Built with player.build."""
    b = player.Bundle(range(min(seasons) - int(fixed["pool_seasons"]), max(seasons) + 1), fixed)
    rows, skipped = [], {}
    for season in seasons:
        weeks = sorted(b.games.loc[b.games["season"] == season, "week"].unique())
        for week in weeks:
            for gsis, team, market in tested(b, season, int(week), int(fixed["tested_min_prior_games"])):
                pl = player.build(b, gsis, gsis, team, season, int(week), tuned, fixed, market)
                if market in pl.not_enough:
                    skipped[market] = skipped.get(market, 0) + 1
                    continue
                act = b.games[(b.games["season"] == season) & (b.games["week"] == week)
                              & (b.games["gsis_id"] == gsis) & (b.games["team"] == team)]
                require(len(act) == 1, f"{gsis} has {len(act)} game rows in {season} week {week}")
                usual = pl.usual(market, int(fixed["usual_games"]))
                r = {"season": season, "week": int(week), "gsis_id": gsis, "team": team, "market": market,
                     "usual": usual, "actual_work": int(act[KIND[market]].iloc[0]),
                     "actual_stat": float(act[STAT[market]].iloc[0])}
                if market == "rush_yds":
                    x = pl.rates["ypc"]
                    r.update(own=x.own, n=x.own_n, base=x.baseline, pool_key=season)
                elif market == "receptions":
                    x = pl.rates["catch"]
                    r.update(own=x.own, n=x.own_n, base=x.baseline)
                elif market == "rec_yds":
                    x, rc = pl.rates["catch"], pl.receiving
                    r.update(own=x.own, n=x.own_n, base=x.baseline, own_yards=rc["own_yards"],
                             own_catches=rc["own_catches"], base_ypr=rc["base_ypr"], mix=rc["mix"],
                             pools=rc["pools"])
                else:
                    x, ps = pl.rates["ypcomp"], pl.passing
                    r.update(own=x.own, n=x.own_n, base=x.baseline, mix=ps["mix"], pools=ps["pools"])
                rows.append(r)
            print(f"  {season} week {week}: {len(rows)} cases so far", file=sys.stderr, flush=True)
    resid = {s: b.pools(s, int(fixed["pool_seasons"]))["rb_residuals"] for s in seasons}
    df = pd.DataFrame(rows)
    df.attrs.update(skipped=skipped, resid=resid)
    return df


# ------------------------------------------------------------------ blends and pricing

def blended(r, market: str, k: dict) -> float:
    """His blended rate at settings k, from the blend's own inputs (rates.blend)."""
    own_sum = (r["own"] or 0.0) * r["n"]
    if market == "rush_yds":
        return (own_sum + k["k_ypc"] * r["base"]) / (r["n"] + k["k_ypc"])
    if market == "receptions":
        return (own_sum + k["k_catch"] * r["base"]) / (r["n"] + k["k_catch"])
    if market == "rec_yds":
        catch = (own_sum + k["k_catch"] * r["base"]) / (r["n"] + k["k_catch"])
        ypr = (r["own_yards"] + k["k_ypr"] * r["base_ypr"]) / (r["own_catches"] + k["k_ypr"])
        return catch * ypr
    return (own_sum + k["k_ypcomp"] * r["base"]) / (r["n"] + k["k_ypcomp"])


def catch_rate(r, k: dict) -> float:
    own_sum = (r["own"] or 0.0) * r["n"]
    return (own_sum + k["k_catch"] * r["base"]) / (r["n"] + k["k_catch"])


class Pricer:
    """Simulated results at a FIXED workload n (the conversion test), with the
    calculator's own draws. Rushing uses calc.Model directly; the per-play
    markets use the same draws through a short path over the first n plays,
    checked against calc.Model on every case it is asked to (verify)."""

    def __init__(self, df: pd.DataFrame, fixed: dict, k: dict):
        self.fixed, self.k = fixed, k
        sims, seed = int(fixed["sims"]), int(fixed["seed"])
        lim = calc.Limits.from_fixed(fixed)
        self.draws = {kind: calc.make_draws(kind, k[R_KEY[kind]], sims, seed, lim, yards=kind != "carries")
                      for kind in R_KEY}
        self.rush = {s: calc.Model("rush_yds", "carries", self.draws["carries"], 4.0, res, k["day_sd"])
                     for s, res in df.attrs["resid"].items()}

    def outcomes(self, r, market: str, rate: float) -> np.ndarray:
        n = int(r["actual_work"])
        if market == "rush_yds":
            m = self.rush[r["pool_key"]]
            m.day_sd = self.k["day_sd"]
            return m.outcomes_fixed(n, rate=rate)
        d = self.draws[KIND[market]]
        if market == "receptions":
            return (d.u_play[:, :n] < rate).sum(axis=1).astype(float)
        catch = catch_rate(r, self.k) if market == "rec_yds" else 1.0
        mix = np.asarray(r["mix"], dtype=float)
        pools = [np.sort(np.asarray(p, dtype=float)) for p in r["pools"]]
        mean_mix = float(sum(w * p.mean() for w, p in zip(mix, pools) if w > 0))
        bucket = np.searchsorted(np.cumsum(mix)[:-1], d.u_depth[:, :n], side="right")
        y0 = np.zeros((len(bucket), n))
        for j, p in enumerate(pools):
            sel = bucket == j
            if sel.any():
                y0[sel] = p[np.minimum((d.u_yard[:, :n][sel] * len(p)).astype(int), len(p) - 1)]
        s = np.where(d.u_play[:, :n] < catch, y0, 0.0).sum(axis=1)
        return np.floor((rate / catch) / mean_mix * s + 0.5)

    def model(self, r, market: str) -> calc.Model:
        """The calculator's own Model for a case (round trip, and the check)."""
        rate = blended(r, market, self.k)
        if market == "rush_yds":
            return calc.Model("rush_yds", "carries", self.draws["carries"], rate,
                              self.rush[r["pool_key"]].residuals, self.k["day_sd"])
        if market == "receptions":
            return calc.Model("receptions", "targets", self.draws["targets"], rate)
        catch = catch_rate(r, self.k) if market == "rec_yds" else 1.0
        return calc.Model(market, KIND[market], self.draws[KIND[market]], rate, catch=catch,
                          depth_mix=tuple(r["mix"]), catch_pools=tuple(r["pools"]))

    def verify(self, r, market: str) -> None:
        rate = blended(r, market, self.k)
        a = self.outcomes(r, market, rate)
        b_ = self.model(r, market).outcomes_fixed(int(r["actual_work"]), rate=rate)
        # the same draws summed in another order: a last-bit difference may flip a whole-yard rounding
        # at an exact .5, so a handful of simulations may differ by one yard; nothing more
        diff = np.abs(a - b_)
        require(diff.max(initial=0) <= 1 and np.mean(diff > 0) <= 1e-3,
                f"harness path differs from calc.Model for {market} {r['gsis_id']} "
                f"(max {diff.max(initial=0)}, {np.mean(diff > 0):.4%} of simulations)")


def _share(out: np.ndarray, line: float) -> float | None:
    po, pu = float(np.mean(out > line)), float(np.mean(out < line))
    return None if po + pu == 0 else po / (po + pu)


def _quantiles(x: np.ndarray, fixed: dict) -> tuple:
    lo = np.quantile(x, fixed["range_low_pct"] / 100, method="inverted_cdf")
    hi = np.quantile(x, fixed["range_high_pct"] / 100, method="inverted_cdf")
    return float(lo), float(hi)


# ------------------------------------------------------------------ the tests

def conversion(df: pd.DataFrame, market: str, fixed: dict, k: dict, verify_every: int = 50) -> dict:
    """Actual workload plugged in; Overs at 0.8x/1.0x/1.2x of workload x
    blended rate (to the nearest half). Returns the per-line stated chances and
    outcomes, the band table, the 80% range coverage and the log loss."""
    pr = Pricer(df, fixed, k)
    d = df[(df["market"] == market) & (df["actual_work"] > 0)]
    p_all, y_all, inside = [], [], []
    for i, (_, r) in enumerate(d.iterrows()):
        rate = blended(r, market, k)
        if i % verify_every == 0:
            pr.verify(r, market)
        out = pr.outcomes(r, market, rate)
        lo, hi = _quantiles(out, fixed)
        inside.append(lo <= r["actual_stat"] <= hi)
        for sc in fixed["conversion_line_scales"]:
            line = half_up(sc * r["actual_work"] * rate, "0.5")
            if line <= 0 or r["actual_stat"] == line:
                continue                       # a line of 0, or a push (void)
            p = _share(out, line)
            if p is None:
                continue
            p_all.append(p)
            y_all.append(float(r["actual_stat"] > line))
    p, y = np.asarray(p_all), np.asarray(y_all)
    bands = []
    for lo_, hi_ in BANDS:
        m = (p >= lo_) & ((p < hi_) if hi_ < 0.8 else (p <= hi_))
        n = int(m.sum())
        bands.append({"band": f"{int(lo_ * 100)}-{int(hi_ * 100)}%", "games": n,
                      "stated": float(p[m].mean()) if n else None, "actual": float(y[m].mean()) if n else None})
    pc = np.clip(p, CLIP, 1 - CLIP)
    ll = float(-np.mean(y * np.log(pc) + (1 - y) * np.log(1 - pc))) if len(p) else None
    cov = float(np.mean(inside)) if inside else None
    band_ok = all(b["games"] >= fixed["pass_band_min_games"]
                  and abs(b["stated"] - b["actual"]) * 100 <= fixed["pass_band_points"] for b in bands)
    range_ok = cov is not None and fixed["pass_range_low"] <= cov * 100 <= fixed["pass_range_high"]
    untested = [b["band"] for b in bands if b["games"] < fixed["pass_band_min_games"]]
    return {"cases": int(len(d)), "priced_lines": int(len(p)), "bands": bands, "range_coverage": cov,
            "log_loss": ll, "pass_bands": band_ok, "pass_range": range_ok, "untested_bands": untested,
            "pass": band_ok and range_ok}


def spread(df: pd.DataFrame, market: str, fixed: dict, r_value: float) -> dict:
    """W = his trailing 4-game average: does the 80% workload range hold
    77-83% of actual workloads? Counts are the calculator's own (calc.counts)."""
    kind = KIND[market]
    lim = calc.Limits.from_fixed(fixed)
    draws = calc.make_draws(kind, r_value, int(fixed["sims"]), int(fixed["seed"]), lim)
    d = df[(df["market"] == market) & df["usual"].notna()]
    cache: dict = {}
    inside = []
    for w, a in zip(d["usual"], d["actual_work"]):
        if w not in cache:
            cache[w] = _quantiles(calc.counts(draws, float(w), lim.max_count[kind]), fixed)
        lo, hi = cache[w]
        inside.append(lo <= a <= hi)
    cov = float(np.mean(inside)) if inside else None
    ok = cov is not None and fixed["pass_range_low"] <= cov * 100 <= fixed["pass_range_high"]
    return {"cases": int(len(d)), "coverage": cov, "pass": ok}


def round_trip(df: pd.DataFrame, market: str, fixed: dict, k: dict, every: int = 10) -> dict:
    """Every `every`-th case: the workload solved for a no-vig chance p (0.45,
    0.50, 0.55; line = his trailing-4 average x blended rate, to the half), fed
    back, must return p within round_trip_points."""
    pr = Pricer(df, fixed, k)
    d = df[(df["market"] == market) & df["usual"].notna()].iloc[::every]
    errs, unsolved = [], 0
    for _, r in d.iterrows():
        m = pr.model(r, market)
        line = half_up(r["usual"] * m.rate, "0.5")
        if line <= 0:
            continue
        for p in (0.45, 0.50, 0.55):
            s = calc.solve_workload(m, line, p)
            if s.status != "ok":
                unsolved += 1
                continue
            errs.append(abs(calc.over_share(m, line, s.value) - p))
    e = np.asarray(errs)
    worst = float(e.max()) if len(e) else None
    ok = worst is not None and worst * 100 <= fixed["round_trip_points"]
    return {"checked": int(len(e)), "unsolved": unsolved, "worst_points": None if worst is None else worst * 100,
            "pass": ok}


# ------------------------------------------------------------------ tuning

def tune(df: pd.DataFrame, fixed: dict, start: dict) -> dict:
    """The pre-registered order. Returns the chosen values and every grid score."""
    require(set(df["season"]) <= set(TUNE_SEASONS), "tuning reads 2018-2023 only")
    k = dict(start)
    scores: dict = {}
    for market, key in (("rush_yds", "carry_r"), ("receptions", "target_r"), ("pass_yds", "completion_r")):
        res = {v: spread(df, market, fixed, v)["coverage"] for v in GRIDS[key]}
        scores[key] = res
        k[key] = min(res, key=lambda v: abs(res[v] - 0.80))
    res = {}
    for kv in GRIDS["k_ypc"]:
        for sd in GRIDS["day_sd"]:
            res[(kv, sd)] = conversion(df, "rush_yds", fixed, {**k, "k_ypc": kv, "day_sd": sd})["log_loss"]
    scores["k_ypc,day_sd"] = {f"{a},{b}": v for (a, b), v in res.items()}
    k["k_ypc"], k["day_sd"] = min(res, key=res.get)
    for market, key in (("receptions", "k_catch"), ("rec_yds", "k_ypr"), ("pass_yds", "k_ypcomp")):
        res = {v: conversion(df, market, fixed, {**k, key: v})["log_loss"] for v in GRIDS[key]}
        scores[key] = res
        k[key] = min(res, key=res.get)
    return {"chosen": k, "scores": scores}


def run_tests(df: pd.DataFrame, fixed: dict, k: dict) -> dict:
    out = {}
    for market in ("rush_yds", "receptions", "rec_yds", "pass_yds"):
        out[market] = {"conversion": conversion(df, market, fixed, k),
                       "spread": spread(df, market, fixed, k[R_KEY[KIND[market]]]),
                       "round_trip": round_trip(df, market, fixed, k)}
        out[market]["pass"] = all(v["pass"] for v in out[market].values() if isinstance(v, dict))
    return out


# ------------------------------------------------------------------ CLI

def _load_cases(seasons: tuple) -> pd.DataFrame:
    path = OUT / f"cases_{min(seasons)}_{max(seasons)}.pkl"
    require(path.exists(), f"no extracted cases at {path}; run extract first")
    with open(path, "rb") as fh:
        return pickle.load(fh)


def _dump(obj, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / name
    p.write_text(json.dumps(obj, indent=1, default=str), encoding="utf-8")
    return p


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m props.calc.harness")
    sub = ap.add_subparsers(dest="cmd", required=True)
    ex = sub.add_parser("extract")
    ex.add_argument("--seasons", default="2018-2023")
    sub.add_parser("tune")
    te = sub.add_parser("test")
    te.add_argument("--seasons", default="2018-2023")
    sub.add_parser("heldout")
    a = ap.parse_args(argv)
    s = settings.load()
    fixed, tuned = s["fixed"], s["tuned"]
    if a.cmd == "extract":
        seasons = _seasons(a.seasons)
        require(not set(seasons) & set(HELDOUT_SEASONS), "the held-out seasons are extracted only by heldout")
        df = extract(seasons, fixed, tuned)
        OUT.mkdir(parents=True, exist_ok=True)
        with open(OUT / f"cases_{min(seasons)}_{max(seasons)}.pkl", "wb") as fh:
            pickle.dump(df, fh)
        print(f"{len(df)} cases; not enough data (left out): {df.attrs['skipped']}")
        print(df.groupby("market").size().to_string())
        return 0
    if a.cmd == "tune":
        df = _load_cases(TUNE_SEASONS)
        res = tune(df, fixed, tuned)
        print(f"wrote {_dump({'old': tuned, **res}, 'tune.json')}")
        print(json.dumps({"old": tuned, "new": res["chosen"]}, indent=1))
        return 0
    if a.cmd == "test":
        seasons = _seasons(a.seasons)
        require(not set(seasons) & set(HELDOUT_SEASONS), "the held-out seasons are tested only by heldout")
        res = run_tests(_load_cases(seasons), fixed, tuned)
        print(f"wrote {_dump(res, 'test_' + a.seasons + '.json')}")
        print(json.dumps(res, indent=1, default=str))
        return 0
    if a.cmd == "heldout":
        if HELDOUT_MARK.exists():
            raise SystemExit(f"the held-out seasons were already read ({HELDOUT_MARK}); they are read once")
        df = extract(HELDOUT_SEASONS, fixed, tuned)
        res = run_tests(df, fixed, tuned)
        rec = {"read_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               "seasons": list(HELDOUT_SEASONS), "settings": tuned, "cases": int(len(df)),
               "not_enough": df.attrs["skipped"], "results": res}
        HELDOUT_MARK.write_text(json.dumps(rec, indent=1, default=str), encoding="utf-8")
        print(json.dumps(rec, indent=1, default=str))
        return 0
    return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except DataError as ex:
        print(f"Stopped: {ex}")
        raise SystemExit(2)

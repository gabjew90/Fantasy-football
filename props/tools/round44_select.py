"""Round 44 (reports/round44_carry_exits.md): an early-exit chance in the backs' carries split, with
a slightly wider split, judged on the rushing-yards own-volume score at the stand-in lines.

    python props/tools/round44_select.py <runs dir> [--out f.json]

<runs dir> holds backtest.py --tune-width --tune-grid carryexit --conditional --save-results
pickles r44_s<seed>_<sel|con>.pkl for seeds 0-3 (--audit-seed-offset): sel = --tune 2022,2023,2024,2025
--weeks 2-18, con = --tune 2026 --weeks 2-5 (one weeks range per run).

The rule, fixed at registration:
- the four seeds' Over chances averaged per player-game before scoring (#202); a selection gain
  under 0.3% of the shipped log loss must be positive on every seed;
- grid_select.run on the averages: rushing yards, own-volume score, ties within 0.0005 to the
  setting closest to shipped, a pick moving the Over chance under 1.8 points stays shipped;
  detectable (95% game-clustered, 10,000 resamples, decision-zone signs agree); the bet-market
  guards on both scores; confirmed on 2026 (point estimate not negative, zone signs agree);
- the tail it targets: the share of bettable backs' carries outcomes below the model's 10th
  percentile moves toward 10% and not past it (each seed's PIT, averaged over the seeds);
- rushing attempts and completions block only when wholly worse: the paired CRPS difference
  (seed-averaged per player-game, bettable backs / starting QBs, 2022-25), its 95% game-clustered
  interval wholly on the worse side;
- the spread guard: no carries band becomes too wide for sure (real / model interval wholly
  below 1, role-only stable stretches, 2022-25);
- the confirmation interval reported at 1 - 0.05/7 (the running-game family's seventh read).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402
import round43_select as R43  # noqa: E402
import scoreboard as SB  # noqa: E402

MARKET, SCORE = "rushing yards", "u"
KNOBS = ("carry_exit_rate", "share_conc_carries")
SHIPPED = {"carry_exit_rate": 0.0, "share_conc_carries": 20.0}
SEEDS = (0, 1, 2, 3)
SELECT, CONFIRM = [2022, 2023, 2024, 2025], [2026]
MIN_MOVE = 1.8           # the four-seed minimum (round 43)
SMALL = 0.003            # a gain under 0.3% of the shipped log loss must hold on every seed
CONFIRM_LEVEL = 1 - 0.05 / 7


def load(runs: Path) -> tuple[list, dict]:
    grid, frames = None, {}
    for s in SEEDS:
        parts = {}
        for part, want in (("sel", SELECT), ("con", CONFIRM)):
            # the confirmation is registered on 2026 weeks 2-5: a stale cache would grade fewer
            f = runs / f"r44_s{s}_{part}.pkl"
            if not f.exists():
                raise FileNotFoundError(f"missing {f.name}: the rule needs seeds 0-3, sel and con")
            d = pd.read_pickle(f)
            if not (isinstance(d, dict) and d.get("kind") == "width_tuning"):
                raise ValueError(f"{f.name} is not a --tune-width --save-results pickle")
            if grid is None:
                grid = d["grid"]
            elif d["grid"] != grid:
                raise ValueError(f"{f.name}: a different grid from the first file's")
            for F in d["frames"]:
                got = set(int(x) for x in F.season.unique())
                if got != set(want):
                    raise ValueError(f"{f.name}: the frames hold seasons {sorted(got)}, not {want}")
                if "pu_rush" not in F or "pit_car" not in F:
                    raise ValueError(f"{f.name}: no pu_rush / pit_car columns (run with --conditional)")
                if part == "con" and not {2, 3, 4, 5} <= set(int(x) for x in F.week.unique()):
                    raise ValueError(f"{f.name}: 2026 weeks {sorted(set(F.week.unique()))}, not 2-5 (a stale cache?)")
            parts[part] = d["frames"]
        frames[s] = [pd.concat([a_, b_], ignore_index=True) for a_, b_ in zip(parts["sel"], parts["con"])]
    return grid, frames


def soft_guard(raw, pick, shipped, seasons, col, rows) -> dict:
    """A soft guard (scoreboard: blocks only when wholly worse): the CRPS of `col`, averaged over the
    seeds per player-game, pick against shipped; gain = shipped - pick (positive = better)."""
    def avg(i):
        fs = [raw[s][i][raw[s][i].season.isin(seasons)].sort_values(SB.KEYS).reset_index(drop=True) for s in SEEDS]
        for F in fs[1:]:
            if not F[SB.KEYS].equals(fs[0][SB.KEYS]):
                raise ValueError("the seeds hold different player-games")
        out = fs[0][SB.KEYS + ["game_id", "mean_car_model", "rush_pop", "pass_pop"]].copy()
        out[col] = np.mean([F[col].to_numpy(float) for F in fs], axis=0)
        return out
    a, b = avg(pick), avg(shipped)
    if not a[SB.KEYS].equals(b[SB.KEYS]):
        raise ValueError("pick and shipped hold different player-games")
    m = rows(b) & a[col].notna() & b[col].notna()
    x = (b[col] - a[col])[m].to_numpy(float)
    ids = SB.cluster_ids(b[m], "game")
    lo, hi = SB.cluster_ci(x, ids, 10_000, np.random.default_rng(44))
    return {"n": int(m.sum()), "gain": float(x.mean()), "ci": [lo, hi], "pass": not hi < 0}


def low_tail(F: pd.DataFrame, seasons) -> float:
    """The share of bettable backs' carries outcomes below the model's 10th percentile."""
    d = F[F.season.isin(seasons) & SB.bettable(F, "rb")]
    u = d.pit_car.dropna().to_numpy(float)
    return float((u < 0.1).mean()) if len(u) else float("nan")


def spread_guard(F: pd.DataFrame, seasons, opening) -> dict:
    d = F[F.season.isin(seasons)]
    tab = SB.spread_table(SB.stable_stretches(d, "mean_car_model", "act_carries", "sd_car", opening=opening,
                                              by="role"), SB.CAR_BANDS)
    if not tab:
        raise ValueError("the carries spread check could not run (no stable stretches or no sd_car)")
    return {"bands": tab, "pass": not any(b["reading"] == "model too wide" for b in tab)}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    grid, raw = load(Path(a.runs))
    shipped_i = next(i for i, g in enumerate(grid) if all(g.get(k) == v for k, v in SHIPPED.items()))
    avg = [R43.seed_average([raw[s][i] for s in SEEDS]) for i in range(len(grid))]
    res = GS.run(grid, avg, shipped_i, MARKET, SCORE, SELECT, CONFIRM, KNOBS, min_move=MIN_MOVE)
    pick = res["pick"]
    out = {"rule": "reports/round44_carry_exits.md", "grid": grid, "shipped": shipped_i, **res}
    # the tail every setting reaches (seed-averaged), shown for all, judged on the pick
    out["low_tail_select"] = {i: float(np.mean([low_tail(raw[s][i], SELECT) for s in SEEDS]))
                              for i in range(len(grid))}
    if pick != shipped_i:
        sel = lambda F: F[F.season.isin(SELECT)]
        per = []
        for s in SEEDS:
            c = SB.compare(sel(raw[s][pick]), sel(raw[s][shipped_i]), "game", reps=2000)[MARKET]
            per.append({"seed": s, "gain": c[f"logloss_{SCORE}"]["gain"], "relative": c[f"logloss_{SCORE}"]["relative"]})
        small = abs(res["select_gain"]["relative"]) < SMALL
        out["per_seed"] = per
        out["per_seed_ok"] = (not small) or all(p_["gain"] > 0 for p_ in per)
        t0, t1 = out["low_tail_select"][shipped_i], out["low_tail_select"][pick]
        # toward 10% and not past it (amended before any run): the same side of 10% as shipped, nearer
        out["tail_ok"] = bool(abs(t1 - 0.10) < abs(t0 - 0.10) and (t1 - 0.10) * (t0 - 0.10) >= 0)
        out["soft_guards"] = {
            "rushing attempts": soft_guard(raw, pick, shipped_i, SELECT, "crps_car_model",
                                           lambda d: d.rush_pop.astype(bool) & d.mean_car_model.ge(SB.MIN_CARRIES)),
            "completions": soft_guard(raw, pick, shipped_i, SELECT, "crps_cmp_model",
                                      lambda d: d.pass_pop.astype(bool))}
        opening = SB.opening_starters(SELECT)
        if not opening:
            raise ValueError("no starting QBs found (NFL_BACKTEST_CACHE must point at the runs' play-by-play): "
                             "the spread guard's stable stretches need them")
        out["spread_guard"] = spread_guard(raw[0][pick], SELECT, opening)
        con = lambda F: F[F.season.isin(CONFIRM)]
        cc = SB.compare(con(avg[pick]), con(avg[shipped_i]), "game", level=CONFIRM_LEVEL, reps=10_000)[MARKET]
        out["confirm_gain_family_level"] = {"level": CONFIRM_LEVEL, **cc[f"logloss_{SCORE}"]}
        out["ship"] = bool(res.get("ship") and out["per_seed_ok"] and out["tail_ok"] and out["spread_guard"]["pass"]
                           and all(g["pass"] for g in out["soft_guards"].values()))
    else:
        out["ship"] = False
    text = json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(text)
    if a.out:
        Path(a.out).write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

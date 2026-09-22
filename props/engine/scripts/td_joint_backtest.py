#!/usr/bin/env python3
"""Layer 3 backtest: do players score TOGETHER the way the joint model says?

  python td_joint_backtest.py [--tune 2022,2023] [--test 2024,2025] [--also 2018,2019] [--out DIR]

Legs: players whose anytime_td_v1 price was 10%+ before kickoff. Every pair
and every three-leg combination in a game, teammates and across teams.
Outcome: all legs scored.

Models of P(all):
  leg by leg   product of anytime_td_v1 prices -- what a parlay priced leg by
               leg assumes. The baseline.
  joint        exact (td_joint): teammates share their team's count.
  joint + mix  each team's channel mix conditioned on the opponent's count
    shift      (multipliers estimated on TUNE). THE SHADOW MODEL: logged on
               every board, never rendered while parlays are gated.
  + copula     the two counts joined by a one-factor Gaussian copula, r set
               by MATCHING the pooled residual count correlation (moment
               matching; the score-pair likelihood rewarded a cusp at 0.5).
               PROVISIONAL, not in the shadow model.

Dependence alone is scored against the product of each model's OWN marginals
(the mix shift also moves single legs). Parlay gate (b) is checked here: in
every lift bucket with 1,000+ combinations, actual / predicted within 5%, in
the test era and the second era.

Every per-player input comes out of td_alloc_backtest.run, which calls td_v1.
"""

from __future__ import annotations

import argparse
import sys
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_alloc_backtest as B  # noqa: E402
import td_joint as J  # noqa: E402
import td_v1 as V  # noqa: E402

LEG_MIN = 0.10
EPS = 1e-4
R_GRID = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]


def count_loglik(d: pd.DataFrame, r: float) -> float:
    """Mean log P(actual offensive-TD pair) per game under loading r."""
    t = d.drop_duplicates(["game_id", "team"])[["game_id", "team", "n_off", "mu_team"]]
    tot = n = 0
    for _, g in t.groupby("game_id"):
        if len(g) != 2:
            continue
        P = J.joint_counts(g["mu_team"].iloc[0], g["mu_team"].iloc[1], r=r)
        tot += np.log(max(P[int(g["n_off"].iloc[0]), int(g["n_off"].iloc[1])], 1e-12))
        n += 1
    return tot / n


def ll(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    y = np.asarray(y, float)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d: pd.DataFrame, a: str, b: str, reps=2000, seed=3):
    x = pd.DataFrame({"g": d["game_id"].to_numpy(),
                      "v": ll(d[a], d["both"]) - ll(d[b], d["both"])}).groupby("g")["v"]
    s, n = x.sum().to_numpy(), x.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(s), size=(reps, len(s)))
    bs = s[idx].sum(1) / n[idx].sum(1)
    return float(s.sum() / n.sum()), *np.percentile(bs, [2.5, 97.5]).tolist()


def ci(x):
    v = "better" if x[2] < 0 else ("worse" if x[1] > 0 else "not established")
    return f"{x[0]:+.5f} ({x[1]:+.5f}, {x[2]:+.5f}) {v}"


def count_residual_corr(d: pd.DataFrame, reps=2000, seed=9):
    """Correlation of the two teams' (offensive TDs - expected) in a game."""
    t = d.drop_duplicates(["game_id", "team"])[["game_id", "team", "n_off", "mu_team"]]
    t = t.assign(r=t["n_off"] - t["mu_team"])
    g = t.groupby("game_id")["r"].agg(list)
    g = g[g.map(len) == 2]
    a = np.array([x[0] for x in g]); b = np.array([x[1] for x in g])
    r = float(np.corrcoef(a, b)[0, 1])
    idx = np.random.default_rng(seed).integers(0, len(a), size=(reps, len(a)))
    bs = [np.corrcoef(a[i], b[i])[0, 1] for i in idx]
    return r, *np.percentile(bs, [2.5, 97.5]), len(a)


def legs_by_game(d: pd.DataFrame, shift: pd.DataFrame, r: float):
    """Per game: the joint count tables and each team's legs (10%+ players)
    with their per-TD shares by opponent count. Yields (gid, P0, Pr, teams,
    info, leg_rows)."""
    pcol = f"e2e|{B.cid(B.SHIP)}"
    sch = [f"s_{c}" for c in J.CH]
    wch = [f"w_{c}" for c in J.CH]
    for gid, g in d.groupby("game_id"):
        teams = list(g["team"].unique())
        if len(teams) != 2:
            continue
        ta, tb = teams
        mu = {t: float(g.loc[g["team"] == t, "mu_team"].iloc[0]) for t in teams}
        P0 = J.joint_counts(mu[ta], mu[tb])
        Pr = J.joint_counts(mu[ta], mu[tb], r=r)
        info, legs = {}, []
        for t, axis in ((ta, 0), (tb, 1)):
            x = g[g["team"] == t]
            shares = x[sch].set_axis(J.CH, axis=1)
            mix = pd.Series(x[wch].iloc[0].to_numpy(), index=J.CH)
            q0 = J.q_by_opp(shares, J.mixes_by_opp(mix, None))
            q1 = J.q_by_opp(shares, J.mixes_by_opp(mix, shift))
            p0 = J.p_any(q0, P0, own_axis=axis)
            p1 = J.p_any(q1, P0, own_axis=axis)
            p2 = J.p_any(q1, Pr, own_axis=axis)
            keep = (x[pcol] >= LEG_MIN).to_numpy()
            info[t] = {"x": x[keep].reset_index(drop=True), "q0": q0[keep], "q1": q1[keep],
                       "p1": p1[keep], "p2": p2[keep], "pv": x.loc[keep, pcol].to_numpy()}
            legs.append(pd.DataFrame({"game_id": gid, "team": t, "scored": x["scored"], "p_v1": x[pcol],
                                      "p_joint0": p0, "p_shift": p1, "p_full": p2}))
        yield gid, P0, Pr, (ta, tb), info, pd.concat(legs, ignore_index=True)


def parlays(d: pd.DataFrame, shift: pd.DataFrame, r: float, max_legs: int = 3):
    """(pair rows, triple rows, leg rows). Every combination of 2 and 3 legs
    in a game, teammates and across teams. Models per combination:
      indep    product of anytime_td_v1 prices (leg by leg)
      ind1     product of the shifted marginals (the baseline for dependence)
      joint1   joint + mix shift, independent counts -- the shadow model
      joint2   joint + mix shift + copula (r provisional)."""
    rows, legs_out = [], []
    empty = np.zeros((0, J.OPP_BUCKETS))
    for gid, P0, Pr, (ta, tb), info, legs in legs_by_game(d, shift, r):
        legs_out.append(legs)
        pool = [(ta, i) for i in range(len(info[ta]["x"]))] + [(tb, i) for i in range(len(info[tb]["x"]))]
        for k in range(2, max_legs + 1):
            for combo in combinations(pool, k):
                A_ = [i for t, i in combo if t == ta]
                B_ = [i for t, i in combo if t == tb]
                qa1 = info[ta]["q1"][A_] if A_ else empty
                qb1 = info[tb]["q1"][B_] if B_ else empty
                qa0 = info[ta]["q0"][A_] if A_ else empty
                qb0 = info[tb]["q0"][B_] if B_ else empty
                both = int(all(info[t]["x"].loc[i, "scored"] for t, i in combo))
                kind = ("teammates" if not A_ or not B_ else "mixed") if k > 2 else \
                       ("teammates" if not A_ or not B_ else "opponents")
                rows.append({"game_id": gid, "legs": k, "kind": kind, "both": both,
                             "indep": float(np.prod([info[t]["pv"][i] for t, i in combo])),
                             "ind1": float(np.prod([info[t]["p1"][i] for t, i in combo])),
                             "joint0": J.p_all(qa0, qb0, P0),
                             "joint1": J.p_all(qa1, qb1, P0),
                             "joint2": J.p_all(qa1, qb1, Pr),
                             "joint3": J.p_all(qa0, qb0, Pr)})
    pr = pd.DataFrame(rows)
    return pr[pr["legs"] == 2], pr[pr["legs"] == 3], pd.concat(legs_out, ignore_index=True)


LIFT_BINS = [0, 0.8, 0.9, 0.97, 1.03, 1.1, 1.2, 1.5, 9]
# The shadow model, chosen on TUNE by the worst-bucket rule below (props-v1.13 run: plain joint;
# the mix shift and the copula each had a worse tune bucket). The gate tables score it.
SHADOW = "joint0"
CANDIDATES = {"joint0": "joint", "joint1": "joint + mix shift", "joint2": "joint + mix shift + copula",
              "joint3": "joint + copula"}


def worst_bucket(g: pd.DataFrame, model: str) -> float:
    """Largest |actual / predicted - 1| over lift buckets with GATE_MIN+ combinations."""
    g = g.assign(lift=g[model] / g["indep"])
    errs = [abs(h["both"].mean() / h[model].mean() - 1)
            for _b, h in g.groupby(pd.cut(g["lift"], LIFT_BINS), observed=True)
            if len(h) >= GATE_MIN and h[model].mean() > 0]
    return max(errs) if errs else float("nan")
GATE_TOL, GATE_MIN = 0.05, 1000


def ratio_ci(h: pd.DataFrame, model: str, reps: int = 400, seed: int = 21):
    """95% interval for actual / predicted, resampling GAMES: combinations in a
    game share players and a script, so they are not independent draws."""
    x = h.groupby("game_id").agg(a=("both", "sum"), m=(model, "sum"))
    a, m = x["a"].to_numpy(), x["m"].to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(a), size=(reps, len(a)))
    r = a[idx].sum(1) / m[idx].sum(1)
    return tuple(np.percentile(r, [2.5, 97.5]))


def lift_table(L, g: pd.DataFrame, model: str, label: str) -> bool:
    """Actual / predicted by lift bucket (model over the leg product). Returns
    whether every bucket with GATE_MIN+ combinations is within GATE_TOL."""
    g = g.assign(lift=g[model] / g["indep"])
    L += [f"{label} -- by the model's lift over the leg product:", "",
          "| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |",
          "|---|---|---|---|---|---|---|---|"]
    ok = True
    for b, h in g.groupby(pd.cut(g["lift"], LIFT_BINS), observed=True):
        ratio = h["both"].mean() / h[model].mean() if h[model].mean() > 0 else float("nan")
        tested = len(h) >= GATE_MIN
        # bool(): a numpy bool is never `is False`, which let a FAIL read as pass
        passed = bool(abs(ratio - 1) <= GATE_TOL) if tested else None
        ok = ok and (passed is not False)
        lo, hi = ratio_ci(h, model) if tested else (float("nan"), float("nan"))
        L.append(f"| {b} | {len(h)} | {h['game_id'].nunique()} | {h['indep'].mean():.4f} | {h[model].mean():.4f} | "
                 f"{h['both'].mean():.4f} | {ratio:.3f} ({lo:.3f}, {hi:.3f}) | {'-' if not tested else ('pass' if passed else 'FAIL')} |")
    L.append("")
    return ok


def section(L, pr: pd.DataFrame, tri: pd.DataFrame, legs: pd.DataFrame, label: str) -> dict:
    L += [f"## {label}", ""]
    chk = float((legs["p_joint0"] - legs["p_v1"]).abs().max())
    chk2 = float((legs["p_full"] - legs["p_shift"]).abs().max())
    L += [f"Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to {chk:.1e}; "
          f"the copula moves single legs by up to {chk2:.1e}. Single-leg log loss with the mix shift "
          f"{ll(legs['p_shift'], legs['scored']).mean():.5f} vs v1 {ll(legs['p_v1'], legs['scored']).mean():.5f}.", ""]
    gate = {}
    for kind, g in pr.groupby("kind"):
        L += [f"### Pairs, {kind}: {len(g)} in {g['game_id'].nunique()} games; both scored {g['both'].mean():.4f}", "",
              "| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |",
              "|---|---|---|---|---|"]
        for lab, c, base in (("leg by leg (v1 product)", "indep", None), ("joint", "joint0", "indep"),
                             ("joint + mix shift (SHADOW)", "joint1", "ind1"),
                             ("joint + mix shift + copula (provisional)", "joint2", None)):
            vs = "" if c == "indep" else ci(boot(g.rename(columns={"both": "both"}), c, "indep"))
            dep = ci(boot(g, c, base)) if base and c != "joint0" else ""
            L.append(f"| {lab} | {g[c].mean():.4f} | {ll(g[c], g['both']).mean():.5f} | {vs} | {dep} |")
        L.append("")
        gate[f"pairs {kind}"] = lift_table(L, g, SHADOW, "Shadow model")
    for kind, g in tri.groupby("kind"):
        L += [f"### Three legs, {kind}: {len(g)} in {g['game_id'].nunique()} games; all scored {g['both'].mean():.4f}", "",
              "| model | mean P(all) | log loss | vs leg product (95% CI) |", "|---|---|---|---|"]
        for lab, c in (("leg by leg (v1 product)", "indep"), ("joint + mix shift (SHADOW)", "joint1"),
                       ("joint + mix shift + copula (provisional)", "joint2")):
            vs = "" if c == "indep" else ci(boot(g, c, "indep"))
            L.append(f"| {lab} | {g[c].mean():.5f} | {ll(g[c], g['both']).mean():.5f} | {vs} |")
        L.append("")
        gate[f"three legs {kind}"] = lift_table(L, g, SHADOW, "Shadow model")
    return gate


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--also", default="2016,2017,2018,2019", help="a second era scored as-is (gate (b))")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    also = [int(x) for x in a.also.split(",")] if a.also else []
    allsz = tune + test + also
    D = B.load(sorted({x for s in allsz for x in (s, s - 1)}))
    D["starts"] = B.load_starts(sorted({x for s in allsz for x in range(s - V.V1["qb_window"], s + 1)}),
                                D["qb_ids"])
    cfgs = [B.SHIP]
    runs = {"tune": B.run(D, tune, cfgs)[0], "test": B.run(D, test, cfgs)[0]}
    if also:
        runs["also"] = B.run(D, also, cfgs)[0]
    shift = J.mix_shift(D["tg"][D["tg"]["season"].isin(tune)])
    L = ["# Layer 3: who scores together", "",
         f"Tune {tune}, test {test}" + (f", second era {also}" if also else "") + f". Legs = players priced "
         f"{LEG_MIN:.0%}+ by anytime_td_v1 ({B.cid(B.SHIP)}) before kickoff. Exact joint model (td_joint.py).", "",
         "## Channel-mix multipliers by the opponent's offensive TDs (estimated on tune)", "",
         "| opponent TDs | " + " | ".join(J.CH) + " |", "|---" * (len(J.CH) + 1) + "|"]
    for b, rr in shift.iterrows():
        L.append(f"| {b if b < J.OPP_BUCKETS - 1 else f'{b}+'} ({shift.attrs['n_tds'][b]} TDs) | "
                 + " | ".join(f"{v:.2f}" for v in rr) + " |")
    L += ["", "Each bucket shrunk toward 1 by 200 touchdowns.", "",
          "## The count correlation, and r (PROVISIONAL, not in the shadow model)", "",
          "| seasons | games | residual correlation (95% CI) |", "|---|---|---|"]
    res = {}
    for lab, d in runs.items():
        rr_, lo, hi, n = count_residual_corr(d)
        res[lab] = (rr_, n)
        L.append(f"| {lab} | {n} | {rr_:+.3f} ({lo:+.3f}, {hi:+.3f}) |")
    pooled = sum(v * n for v, n in res.values()) / sum(n for _v, n in res.values())
    mus = []
    for lab in runs:
        t = runs[lab].drop_duplicates(["game_id", "team"]).groupby("game_id")["mu_team"].agg(list)
        mus += [tuple(x) for x in t if len(x) == 2]
    r = J.r_for_corr(pooled, mus[::5])
    L += ["", f"Pooled residual correlation {pooled:+.3f}; r = {r:g} matches it (moment matching over these games' "
              f"means). Score-pair likelihood by r, for reference:", "", "| r | " + " | ".join(runs) + " |",
          "|---" * (len(runs) + 1) + "|"]
    for rg in R_GRID:
        L.append(f"| {rg:g} | " + " | ".join(f"{count_loglik(runs[k], rg):.4f}" for k in runs) + " |")
    L.append("")
    gates, combos = {}, {}
    for lab, d in runs.items():
        pr, tri, legs = parlays(d, shift, r)
        combos[lab] = pd.concat([pr, tri], ignore_index=True)
        seasons = {"tune": tune, "test": test, "also": also}[lab]
        gates[lab] = section(L, pr, tri, legs, f"{lab.title()} {seasons}")
    # THE SHADOW MODEL IS CHOSEN ON TUNE: the candidate whose worst lift bucket
    # (1,000+ combinations, pairs and three legs, teammates and across teams)
    # is closest to 1 on the tune seasons. The test eras only check it.
    L += ["## Choosing the shadow model on tune: worst |actual / predicted - 1| over large lift buckets", "",
          "| candidate | " + " | ".join(runs) + " |", "|---" * (len(runs) + 1) + "|"]
    worst = {}
    for c, name in CANDIDATES.items():
        # nanmax: a group with no large bucket must not decide the score by iteration order
        per = {lab: float(np.nanmax([worst_bucket(g, c) for _k, g in combos[lab].groupby(["legs", "kind"])] + [np.nan]))
               if combos[lab].size else float("nan") for lab in runs}
        worst[c] = per
        L.append(f"| {name} | " + " | ".join(f"{per[lab]:.3f}" for lab in runs) + " |")
    scored = {c: v for c, v in worst.items() if np.isfinite(v["tune"])}
    pick = min(scored, key=lambda c: scored[c]["tune"])
    if pick != SHADOW:
        # the gate tables above scored SHADOW; a different tune pick means they grade the wrong model
        msg = (f"MISMATCH: tune picks {CANDIDATES[pick]} but the gate tables and the live shadow use "
               f"{CANDIDATES[SHADOW]}. Set SHADOW (and score_game's JOINT_MIX_SHIFT) to the pick and rerun.")
        print(msg, file=sys.stderr)
        L += [f"**{msg}**", ""]
    L += ["", f"Chosen on tune: **{CANDIDATES[pick]}**. Gate (b) holds in an era when its worst bucket is within "
              f"{GATE_TOL:.0%}.", "", "| era | chosen model's worst bucket | gate (b) |", "|---|---|---|"]
    for lab in runs:
        if lab != "tune":
            w = worst[pick][lab]
            L.append(f"| {lab} | {w:.3f} | {'PASS' if w <= GATE_TOL else 'FAIL'} |")
    L.append("")
    L += ["## Gate (b): every lift bucket with 1,000+ combinations within 5%, shadow model", "",
          "| era | " + " | ".join(next(iter(gates.values())).keys()) + " |",
          "|---" * (len(next(iter(gates.values()))) + 1) + "|"]
    for lab, gg in gates.items():
        if lab == "tune":
            continue
        L.append(f"| {lab} | " + " | ".join("pass" if v else "FAIL" for v in gg.values()) + " |")
    path = Path(a.out) / "td_layer3.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

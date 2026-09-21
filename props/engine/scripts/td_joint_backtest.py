#!/usr/bin/env python3
"""Layer 3 backtest: do players score TOGETHER the way the joint model says?

  python td_joint_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

Population: every pair of players in a game whose anytime_td_v1 price was
10%+ before kickoff (the players a parlay would use) -- teammates and
cross-team pairs separately. Outcome: both scored.

Models of P(both):
  independent   pA x pB from anytime_td_v1 -- what a parlay priced leg by
                leg assumes. The baseline.
  joint         td_joint, exact: teammates share their team's touchdowns;
                the two teams independent. For cross-team pairs this equals
                the baseline by construction.
  joint + shift each team channel mix conditioned on the opponent
                touchdown count (multipliers estimated on TUNE).
  + correlated  the two teams' counts joined by a one-factor Gaussian copula,
    counts      loading r tuned on TUNE by the likelihood of the actual score
                pairs; each team's own distribution is unchanged.

Also measured: whether the two teams' offensive-TD counts are correlated
beyond their implied totals (the residual correlation), which decides whether
the counts may stay independent.

Every per-player input comes out of td_alloc_backtest.run, which calls td_v1:
the shares and channel mix scored here are the ones anytime_td_v1 prices.
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


def pairs(d: pd.DataFrame, shift: pd.DataFrame, r: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(pair rows, leg rows). Leg rows carry the shifted marginal as a check
    that layer 3 does not move single-leg prices."""
    pcol = f"e2e|{B.cid(B.SHIP)}"
    sch = [f"s_{c}" for c in J.CH]
    wch = [f"w_{c}" for c in J.CH]
    out, legs_out = [], []
    for gid, g in d.groupby("game_id"):
        teams = list(g["team"].unique())
        if len(teams) != 2:
            continue
        ta, tb = teams
        mu = {t: float(g.loc[g["team"] == t, "mu_team"].iloc[0]) for t in teams}
        P = J.joint_counts(mu[ta], mu[tb])                     # [k_ta, k_tb], independent
        Pr = J.joint_counts(mu[ta], mu[tb], r=r)               # copula-joined
        info = {}
        for t, axis in ((ta, 0), (tb, 1)):
            x = g[g["team"] == t]
            shares = x[sch].set_axis(J.CH, axis=1)
            mix = pd.Series(x[wch].iloc[0].to_numpy(), index=J.CH)
            q0 = J.q_by_opp(shares, J.mixes_by_opp(mix, None))
            q1 = J.q_by_opp(shares, J.mixes_by_opp(mix, shift))
            p0 = J.p_any(q0, P, own_axis=axis)
            p1 = J.p_any(q1, P, own_axis=axis)
            p2 = J.p_any(q1, Pr, own_axis=axis)
            keep = (x[pcol] >= LEG_MIN).to_numpy()
            info[t] = {"x": x[keep], "q0": q0[keep], "q1": q1[keep], "axis": axis}
            legs_out.append(pd.DataFrame({"game_id": gid, "team": t, "player_id": x["player_id"],
                                          "scored": x["scored"], "p_v1": x[pcol], "p_joint0": p0,
                                          "p_shift": p1, "p_full": p2}))
        for t in teams:                                         # teammates
            I = info[t]
            n = len(I["x"])
            for i, j in combinations(range(n), 2):
                a, b = I["x"].iloc[i], I["x"].iloc[j]
                out.append({"game_id": gid, "kind": "teammates", "pA": a[pcol], "pB": b[pcol],
                            "both": int(a["scored"] and b["scored"]),
                            "joint0": J.p_all_same_team(I["q0"][[i, j]], P, own_axis=I["axis"]),
                            "joint1": J.p_all_same_team(I["q1"][[i, j]], P, own_axis=I["axis"]),
                            "joint2": J.p_all_same_team(I["q1"][[i, j]], Pr, own_axis=I["axis"])})
        A_, B_ = info[ta], info[tb]                             # cross-team
        for i in range(len(A_["x"])):
            for j in range(len(B_["x"])):
                a, b = A_["x"].iloc[i], B_["x"].iloc[j]
                out.append({"game_id": gid, "kind": "opponents", "pA": a[pcol], "pB": b[pcol],
                            "both": int(a["scored"] and b["scored"]),
                            "joint0": J.p_pair_cross(A_["q0"][i], B_["q0"][j], P),
                            "joint1": J.p_pair_cross(A_["q1"][i], B_["q1"][j], P),
                            "joint2": J.p_pair_cross(A_["q1"][i], B_["q1"][j], Pr)})
    pr = pd.DataFrame(out)
    pr["indep"] = pr["pA"] * pr["pB"]
    return pr, pd.concat(legs_out, ignore_index=True)


def section(L, pr: pd.DataFrame, legs: pd.DataFrame, label: str):
    L += [f"## {label}", ""]
    chk = float((legs["p_joint0"] - legs["p_v1"]).abs().max())
    chk2 = float((legs["p_full"] - legs["p_shift"]).abs().max())
    L += [f"Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to "
          f"{chk:.1e}; the copula moves no single-leg price by more than {chk2:.1e}. With the mix shift, "
          f"single-leg log loss {ll(legs['p_shift'], legs['scored']).mean():.5f} vs v1 "
          f"{ll(legs['p_v1'], legs['scored']).mean():.5f} on {len(legs)} player-games.", ""]
    for kind, g in pr.groupby("kind"):
        L += [f"### {kind.title()}: {len(g)} pairs in {g['game_id'].nunique()} games; both scored "
              f"{g['both'].mean():.4f}", "",
              "| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |",
              "|---|---|---|---|---|"]
        for lab, c in (("independent (leg by leg)", "indep"), ("joint", "joint0"), ("joint + mix shift", "joint1"),
                       ("joint + mix shift + correlated counts", "joint2")):
            vs = "" if c == "indep" else ci(boot(g, c, "indep"))
            L.append(f"| {lab} | {g[c].mean():.4f} | {ll(g[c], g['both']).mean():.5f} | "
                     f"{((g[c] - g['both']) ** 2).mean():.5f} | {vs} |")
        # the lift: how far the joint model moves a pair from the product, and whether reality follows
        g = g.assign(lift=g["joint2"] / g["indep"])
        L += ["", "Binned by the full model's lift over the product: does reality move with it?", "",
              "| lift | pairs | mean independent | mean full model | actual both |", "|---|---|---|---|---|"]
        for b, h in g.groupby(pd.cut(g["lift"], [0, 0.8, 0.9, 0.97, 1.03, 1.1, 1.2, 1.5, 9]), observed=True):
            L.append(f"| {b} | {len(h)} | {h['indep'].mean():.4f} | {h['joint2'].mean():.4f} | {h['both'].mean():.4f} |")
        L.append("")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    allsz = tune + test
    D = B.load(sorted({x for s in allsz for x in (s, s - 1)}))
    D["starts"] = B.load_starts(sorted({x for s in allsz for x in range(s - V.V1["qb_window"], s + 1)}),
                                D["qb_ids"])
    cfgs = [B.SHIP]
    dtu, _ = B.run(D, tune, cfgs)
    dte, _ = B.run(D, test, cfgs)
    shift = J.mix_shift(D["tg"][D["tg"]["season"].isin(tune)])
    L = ["# Layer 3: who scores together", "",
         f"Tune {tune}, test {test}. Pairs of players priced {LEG_MIN:.0%}+ by anytime_td_v1 ({B.cid(B.SHIP)}) "
         "before kickoff; outcome = both scored. The joint model is exact (td_joint.py): teammates share their "
         "team's touchdown count; the teams are independent unless linked by the mix shift.", "",
         "## Channel-mix multipliers by the opponent's offensive TDs (estimated on tune)", "",
         "| opponent TDs | " + " | ".join(J.CH) + " |", "|---" * (len(J.CH) + 1) + "|"]
    for b, r in shift.iterrows():
        L.append(f"| {b if b < J.OPP_BUCKETS - 1 else f'{b}+'} | " + " | ".join(f"{v:.2f}" for v in r) + " |")
    L += ["", "## Are the two teams' touchdown counts correlated beyond their implied totals?", "",
          "| seasons | games | residual correlation (95% CI) |", "|---|---|---|"]
    for lab, d in (("tune", dtu), ("test", dte)):
        r, lo, hi, n = count_residual_corr(d)
        L.append(f"| {lab} | {n} | {r:+.3f} ({lo:+.3f}, {hi:+.3f}) |")
    cl_tu = {r: count_loglik(dtu, r) for r in R_GRID}
    r_best = max(cl_tu, key=cl_tu.get)
    cl_te = {r: count_loglik(dte, r) for r in R_GRID}
    L += ["", "## The copula loading r, tuned on the likelihood of the actual score pairs", "",
          "| r | latent correlation r^2 | tune: mean log P(pair) | test: mean log P(pair) |", "|---|---|---|---|"]
    for r in R_GRID:
        L.append(f"| {r:g} | {r * r:.2f} | {cl_tu[r]:.4f}{' **chosen**' if r == r_best else ''} | {cl_te[r]:.4f} |")
    L.append("")
    for lab, d in (("Tune", dtu), ("Test", dte)):
        pr, legs = pairs(d, shift, r_best)
        section(L, pr, legs, f"{lab} {tune if lab == 'Tune' else test}")
    path = Path(a.out) / "td_layer3.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

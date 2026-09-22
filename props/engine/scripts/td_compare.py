#!/usr/bin/env python3
"""Paired comparison of two anytime_td_v1 code versions, player by player.

  python td_compare.py OLD.csv NEW.csv LABEL [--out FILE]

Each CSV is the shipped model's per-player rows from one checkout (the
harness's run(), dumped with the same columns). A change to the channel
DEFINITIONS -- like splitting red-zone targets into end-zone and other --
cannot be scored inside one harness run, because the channels are global;
running both checkouts and joining on (game_id, player_id) gives a paired,
game-clustered comparison on identical players.

Reports: log loss end to end and given the team's offensive TDs; the top
calibration bins (the gate); the top-share player's realised/expected TDs,
and for the NEW version his ratio within the passing channels.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

EPS = 1e-3


def ll(p, y):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def boot(d, a, b, reps=2000, seed=5):
    x = pd.DataFrame({"g": d["game_id"], "v": ll(d[a], d["scored"]) - ll(d[b], d["scored"])}).groupby("g")["v"]
    s, n = x.sum().to_numpy(), x.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(s), size=(reps, len(s)))
    bs = s[idx].sum(1) / n[idx].sum(1)
    m, lo, hi = s.sum() / n.sum(), *np.percentile(bs, [2.5, 97.5])
    v = "better" if hi < 0 else ("worse" if lo > 0 else "not established")
    return f"{m:+.4f} ({lo:+.4f}, {hi:+.4f}) {v}"


def calib(L, d, col, lab, bins=(0, .05, .10, .20, .30, .45, .60, 1.0)):
    L += [f"{lab}:", "", "| predicted | mean predicted | actual | n |", "|---|---|---|---|"]
    for b, g in d.groupby(pd.cut(d[col], list(bins), include_lowest=True), observed=True):
        L.append(f"| {b} | {g[col].mean():.3f} | {g['scored'].mean():.3f} | {len(g)} |")
    L.append("")


def top_ratio(d, qcol):
    x = d[d["n_off"] > 0].copy()
    x["rank"] = x.groupby(["game_id", "team"])[qcol].rank(ascending=False, method="first")
    t = x[x["rank"] == 1]
    return t, float(t["tds"].sum() / (t[qcol] * t["n_off"]).sum())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("old"); ap.add_argument("new"); ap.add_argument("label")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    o, n = pd.read_csv(a.old), pd.read_csv(a.new)
    key = ["game_id", "team", "player_id"]
    d = o[key + ["pos", "scored", "tds", "n_off", "e2e", "n", "q"]].merge(
        n[key + ["e2e", "n", "q"] + [c for c in n.columns if c.startswith(("s_", "td_", "T_"))]],
        on=key, suffixes=("_old", "_new"))
    L = [f"## {a.label}", "", f"{len(d)} player-games matched ({len(o)} old, {len(n)} new rows); "
         f"actual scoring rate {d['scored'].mean():.3f}.", "",
         "| | old | new | new vs old (95% CI, game-clustered) |", "|---|---|---|---|",
         f"| log loss, end to end | {ll(d['e2e_old'], d['scored']).mean():.4f} | {ll(d['e2e_new'], d['scored']).mean():.4f} "
         f"| {boot(d, 'e2e_new', 'e2e_old')} |",
         f"| log loss, given the team's offensive TDs | {ll(d['n_old'], d['scored']).mean():.4f} | "
         f"{ll(d['n_new'], d['scored']).mean():.4f} | {boot(d, 'n_new', 'n_old')} |",
         f"| mean predicted | {d['e2e_old'].mean():.3f} | {d['e2e_new'].mean():.3f} | |", ""]
    for p, g in d.groupby("pos"):
        L.append(f"- {p}: old {ll(g['e2e_old'], g['scored']).mean():.4f}, new {ll(g['e2e_new'], g['scored']).mean():.4f} "
                 f"(n {len(g)}); mean predicted {g['e2e_old'].mean():.3f} -> {g['e2e_new'].mean():.3f} vs {g['scored'].mean():.3f}")
    L.append("")
    calib(L, d, "e2e_old", "Old, end to end")
    calib(L, d, "e2e_new", "New, end to end")
    t_old, r_old = top_ratio(d, "q_old")
    t_new, r_new = top_ratio(d, "q_new")
    L.append(f"Top-q player realised / expected TDs: old {r_old:.3f}, new {r_new:.3f}.")
    pas = [c for c in ("pass_ez", "pass_rz", "pass_far") if f"s_{c}" in t_new.columns]
    rus = [c for c in ("qb_rush", "rush_in5", "rush_far") if f"s_{c}" in t_new.columns]
    if pas:
        pr = sum(t_new[f"td_{c}"].sum() for c in pas) / sum((t_new[f"s_{c}"] * t_new[f"T_{c}"]).sum() for c in pas)
        rr = sum(t_new[f"td_{c}"].sum() for c in rus) / sum((t_new[f"s_{c}"] * t_new[f"T_{c}"]).sum() for c in rus)
        L.append(f"New version, top-q player within channels: passing {pr:.2f}, rushing {rr:.2f} "
                 "(realised / share x team channel TDs).")
    L.append("")
    text = "\n".join(L) + "\n"
    if a.out:
        with open(a.out, "a", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

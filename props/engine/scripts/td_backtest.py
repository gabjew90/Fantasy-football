#!/usr/bin/env python3
"""Layer 1 backtest: team touchdown distributions, no betting lines needed
beyond the closing spread and total nflverse already carries.

  python td_backtest.py [--tune 2022,2023] [--test 2024,2025] [--out DIR]

Walk-forward: every team-game is predicted from the prior season plus the
current season's weeks before it. Every setting is chosen on the TUNE seasons,
frozen, then scored on the TEST seasons, which never influenced a choice.

Questions it answers, each against the simpler version:
  1. Does a team-specific touchdowns-per-point ratio beat one league constant?
  2. What SHAPE is the count: Poisson, overdispersed (negative binomial), or
     underdispersed (binomial over drives)?
  3. Do high-total teams convert a larger share of points into touchdowns?
  4. Does a team-specific channel mix beat the league mix?
"""

from __future__ import annotations

import argparse
import itertools
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_model as T  # noqa: E402

NV = "https://github.com/nflverse/nflverse-data/releases/download"
GAMES = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
K_GRID = [None, 100.0, 300.0, 1000.0, 3000.0]
GAMMA_GRID = [0.0, 0.25, 0.5, 0.75, 1.0]
ALPHA_GRID = [None, 5.0, 20.0, 50.0, 100.0, 200.0, 500.0, 1000.0]
ENGINE_CONSTANT = 0.1055   # score_game's league_td_per_point: OFFENSIVE TDs per point


def fetch(url: str, name: str) -> Path:
    CACHE.mkdir(parents=True, exist_ok=True)
    dest = CACHE / name
    if not dest.exists() or dest.stat().st_size == 0:
        print(f"  fetching {name}", file=sys.stderr)
        urllib.request.urlretrieve(url, dest)
    return dest


def load(seasons: list[int]) -> pd.DataFrame:
    players = pd.read_csv(fetch(f"{NV}/players/players.csv", "players.csv"),
                          usecols=["gsis_id", "position"], low_memory=False)
    qb_ids = set(players.loc[players["position"] == "QB", "gsis_id"].dropna())
    tds = []
    for s in seasons:
        pbp = pd.read_csv(fetch(f"{NV}/pbp/play_by_play_{s}.csv.gz", f"pbp_{s}.csv.gz"),
                          usecols=T.PBP_COLS, low_memory=False)
        tds.append(T.classify_tds(pbp, qb_ids))
    sched = pd.read_csv(fetch(GAMES, "games.csv"), low_memory=False)
    sched = sched[sched["season"].isin(seasons)]
    tg = T.team_games(sched, pd.concat(tds, ignore_index=True))
    return tg[tg["implied"].notna()].reset_index(drop=True)


def check(tg: pd.DataFrame) -> str:
    """Touchdowns reconciled against the final score, in BOTH directions.

    Too many: six points a touchdown can never exceed what the team scored.
    Too few: this is the check that was missing. A team whose touchdowns fail
    to join (a franchise-code mismatch) shows up as a run of games with real
    points and zero touchdowns, and the old check could not see it. Fourteen
    points without a touchdown takes five field goals, so a franchise-season
    with several such games is a join failure, not a kicker. That is a hard
    stop: every number downstream would be built on it.
    """
    over = tg[6 * tg["tds"] > tg["points"]]
    zero = tg[(tg["tds"] == 0) & (tg["points"] >= 14)]
    per = zero.groupby(["season", "team"]).size()
    broken = per[per >= 4]
    if len(over) or len(broken):
        raise SystemExit(f"touchdowns do not reconcile with scores: {len(over)} team-games over, "
                         f"franchise-seasons with 4+ zero-TD games of 14+ points: "
                         f"{broken.to_dict()} -- check team codes")
    return (f"reconciled: 0 team-games where 6 x TDs exceeds points; {len(zero)} genuine "
            f"field-goal-only games of 14+ points, none clustered on one franchise-season.")


def walk_forward(tg: pd.DataFrame, seasons: list[int], k, gamma: float) -> pd.DataFrame:
    """Predicted mean for every team-game in `seasons`, each from data strictly
    before its own week."""
    out = []
    for s in seasons:
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            now = tg[(tg["season"] == s) & (tg["week"] == w)].copy()
            by_team, league = T.ratios(hist, k)
            ratio = now["team"].map(by_team).fillna(league) if k is not None else league
            now["mu"] = T.team_mean(now["implied"], ratio, hist["implied"].mean(), gamma)
            out.append(now)
    return pd.concat(out, ignore_index=True)


def pmf(mu, shape) -> np.ndarray:
    fam, par = shape
    return T.count_pmf(mu, r=par if fam == "NegBin" else None,
                       n=par if fam == "Binomial" else None)


def score(d: pd.DataFrame, shape) -> dict:
    P = pmf(d["mu"].to_numpy(), shape)
    return {"crps": float(T.crps_count(P, d["tds"]).mean()),
            "log": float(T.log_score(P, d["tds"]).mean()),
            "bias": float((d["mu"] - d["tds"]).mean()), "n": len(d)}


def shapes_for(d: pd.DataFrame) -> list[tuple[str, float | None]]:
    """Poisson always; each alternative only if it beats Poisson on the TUNE
    data it is fitted to."""
    out = [("Poisson", None)]
    r = T.fit_dispersion(d["mu"].to_numpy(), d["tds"].to_numpy())
    if r is not None:
        out.append(("NegBin", r))
    n = T.fit_trials(d["mu"].to_numpy(), d["tds"].to_numpy())
    if n is not None:
        out.append(("Binomial", n))
    return out


def boot_diff(a: pd.DataFrame, sa, b: pd.DataFrame, sb, reps=2000, seed=11):
    """CRPS(a) - CRPS(b), resampling whole games: both teams in one game share
    a script, so resampling team-games would overstate the certainty."""
    ca = T.crps_count(pmf(a["mu"].to_numpy(), sa), a["tds"])
    cb = T.crps_count(pmf(b["mu"].to_numpy(), sb), b["tds"])
    g = pd.DataFrame({"game": a["game_id"].to_numpy(), "d": ca - cb}).groupby("game")["d"]
    sums, cnt = g.sum().to_numpy(), g.size().to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(sums), size=(reps, len(sums)))
    boot = sums[idx].sum(1) / cnt[idx].sum(1)
    return float(sums.sum() / cnt.sum()), *np.percentile(boot, [2.5, 97.5]).tolist()


def decompose(tg: pd.DataFrame, seasons: list[int]) -> pd.DataFrame:
    """Where does the high-total shortfall come from? TDs = points x
    (TDs / point), so by implied-total quintile:

      points - implied   the MARKET side: do high-total teams beat their total?
      TDs / point        the CONVERSION side: do they turn more points into TDs?

    If the first rises and the second is flat, an elasticity on touchdowns is
    patching a points bias in the total and belongs on the points, not on the
    touchdown conversion. If the second rises, it is genuine conversion.
    """
    d = tg[tg["season"].isin(seasons)].copy()
    d["q"] = pd.qcut(d["implied"], 5, labels=False)
    g = d.groupby("q")
    out = g.agg(implied=("implied", "mean"), points=("points", "mean"),
                tds=("tds", "mean"), n=("tds", "size"))
    out["gap"] = out["points"] - out["implied"]
    # The SE of the GAP, from the spread of the gap itself. Using the spread
    # of points counted the implied totals' own variation inside each
    # quintile as noise, which inflated the SE and understated the effect.
    out["gap_se"] = (d["points"] - d["implied"]).groupby(d["q"]).std() / np.sqrt(out["n"])
    out["td_per_pt"] = g["tds"].sum() / g["points"].sum()
    off = g[list(T.OFFENSIVE)].sum().sum(axis=1)
    out["off_td_per_pt"] = off / g["points"].sum()
    return out


def channel_eval(tg: pd.DataFrame, seasons: list[int], alpha) -> tuple[float, int]:
    """Mean log loss of each actual touchdown's channel under the predicted
    mix: given that a team scored, how well was the KIND of touchdown
    anticipated. Walk-forward like the counts."""
    losses = []
    for s in seasons:
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            now = tg[(tg["season"] == s) & (tg["week"] == w)]
            shares, league = T.channel_shares(hist, alpha)
            for _, row in now.iterrows():
                p = shares.loc[row["team"]] if (alpha is not None and row["team"] in shares.index) else league
                for c in T.CHANNELS:
                    if row[c]:
                        losses += [-np.log(max(float(p[c]), 1e-9))] * int(row[c])
    return float(np.mean(losses)), len(losses)


GAMMA_FROZEN = 0.25


def wf_target(tg: pd.DataFrame, seasons: list[int], gamma: float, target: str) -> pd.DataFrame:
    """Walk-forward mean for `target` ('off_tds' or 'tds'): league
    target-per-point ratio from the history, times implied points, with
    elasticity gamma."""
    out = []
    for s in seasons:
        for w in sorted(tg.loc[tg["season"] == s, "week"].unique()):
            hist = tg[(tg["season"] == s - 1) | ((tg["season"] == s) & (tg["week"] < w))]
            now = tg[(tg["season"] == s) & (tg["week"] == w)].copy()
            ratio = hist[target].sum() / hist["points"].sum()
            now["mu"] = T.team_mean(now["implied"], ratio, hist["implied"].mean(), gamma)
            out.append(now)
    return pd.concat(out, ignore_index=True)


def _crps(d, P, y):
    return T.crps_count(P, d[y])


def _boot_rows(d, a, b, reps=2000, seed=13):
    g = pd.DataFrame({"g": d["game_id"].to_numpy(), "v": a - b}).groupby("g")["v"]
    sums, cnt = g.sum().to_numpy(), g.size().to_numpy()
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    bs = sums[idx].sum(1) / cnt[idx].sum(1)
    return float(sums.sum() / cnt.sum()), *np.percentile(bs, [2.5, 97.5]).tolist()


def frozen(tg: pd.DataFrame, tune: list[int], evals: dict[str, list[int]]) -> list[str]:
    """Score the FROZEN spec as-is, with no re-tuning on the seasons scored.

    Tuned once on TUNE: n for offensive touchdowns at gamma = 0.25, and the
    flat defence/special-teams mean. Then every evaluation set gets exactly
    those numbers. The earlier older-season check re-tuned on 2016-17 and
    so tested the PROCEDURE, not the spec that would ship.
    """
    dtu = wf_target(tg, tune, GAMMA_FROZEN, "off_tds")
    n_off = T.fit_trials(dtu["mu"].to_numpy(), dtu["off_tds"].to_numpy())
    dtu0 = wf_target(tg, tune, 0.0, "off_tds")
    n_off0 = T.fit_trials(dtu0["mu"].to_numpy(), dtu0["off_tds"].to_numpy())
    dst = float(tg.loc[tg["season"].isin(tune), "dst"].mean())
    # the previous frozen spec, on ALL touchdowns, for the Q1 comparison
    dtt = wf_target(tg, tune, GAMMA_FROZEN, "tds")
    n_tot = T.fit_trials(dtt["mu"].to_numpy(), dtt["tds"].to_numpy())

    L = ["# Layer 1, frozen spec scored as-is", "",
         f"Tuned once on {tune}: offensive touchdowns ~ Binomial(n={n_off}) with mean = implied points "
         f"x league offensive TDs-per-point x elasticity gamma={GAMMA_FROZEN}; defence and special "
         f"teams a flat {dst:.3f} per team-game. Nothing below is re-tuned on the seasons it scores.", ""]
    for label, seasons in evals.items():
        e0 = wf_target(tg, seasons, 0.0, "off_tds")          # engine today: linear, Poisson
        eg = wf_target(tg, seasons, GAMMA_FROZEN, "off_tds")
        y = e0["off_tds"]
        c_eng = T.crps_count(T.count_pmf(e0["mu"]), y)
        c_bin = T.crps_count(T.count_pmf(e0["mu"], n=n_off0), y)
        c_frz = T.crps_count(T.count_pmf(eg["mu"], n=n_off), y)
        l_eng = T.log_score(T.count_pmf(e0["mu"]), y).mean()
        l_frz = T.log_score(T.count_pmf(eg["mu"], n=n_off), y).mean()
        ci = lambda x: f"{x[0]:+.4f} ({x[1]:+.4f}, {x[2]:+.4f}) " + (  # noqa: E731
            "better" if x[2] < 0 else "worse" if x[1] > 0 else "not established")
        L += [f"## {label}: seasons {seasons[0]}-{seasons[-1]}, {len(e0)} team-games", "",
              "Offensive touchdowns (what an anytime prop settles on).", "",
              "| model | CRPS | change vs row above (95% CI, game-clustered) |", "|---|---|---|",
              f"| Engine today: league offensive ratio, linear, Poisson | {c_eng.mean():.4f} | baseline |",
              f"| + binomial n={n_off0} | {c_bin.mean():.4f} | {ci(_boot_rows(e0, c_bin, c_eng))} |",
              f"| + gamma={GAMMA_FROZEN}, binomial n={n_off} (FROZEN) | {c_frz.mean():.4f} | "
              f"{ci(_boot_rows(e0, c_frz, c_bin))} |", "",
              f"Log score: engine {l_eng:.4f}, frozen {l_frz:.4f}.", "",
              "| quintile of implied | engine predicted | frozen predicted | actual offensive TDs | n |",
              "|---|---|---|---|---|"]
        q = pd.qcut(e0["implied"], 5, labels=False)
        for k in range(5):
            m = q == k
            L.append(f"| {k + 1} | {e0.loc[m, 'mu'].mean():.3f} | {eg.loc[m, 'mu'].mean():.3f} | "
                     f"{e0.loc[m, 'off_tds'].mean():.3f} | {int(m.sum())} |")
        # ALL touchdowns: old spec (gamma on the total) vs offensive + flat D/ST
        et = wf_target(tg, seasons, GAMMA_FROZEN, "tds")
        P_old = T.count_pmf(et["mu"], n=n_tot)
        P_new = T.total_pmf(T.count_pmf(eg["mu"], n=n_off), dst)
        c_old, c_new = T.crps_count(P_old, et["tds"]), T.crps_count(P_new, et["tds"])
        kk = np.arange(P_new.shape[1])
        mean_new = (P_new * kk).sum(1)
        L += ["", "All touchdowns: gamma applied to the TOTAL (previous spec) vs gamma on offensive "
                  "touchdowns plus a flat D/ST term.", "",
              f"CRPS {c_old.mean():.4f} -> {c_new.mean():.4f}: {ci(_boot_rows(et, c_new, c_old))}.", "",
              "| quintile of implied | gamma on total | offensive + flat D/ST | actual all TDs |",
              "|---|---|---|---|"]
        for k in range(5):
            m = (q == k).to_numpy()
            L.append(f"| {k + 1} | {et.loc[m, 'mu'].mean():.3f} | {mean_new[m].mean():.3f} | "
                     f"{et.loc[m, 'tds'].mean():.3f} |")
        L.append("")
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", default="2022,2023")
    ap.add_argument("--test", default="2024,2025")
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "backtest_out"))
    ap.add_argument("--frozen", default=None,
                    help="score the frozen spec as-is on these extra seasons too, e.g. 2016,2017,2018,2019")
    a = ap.parse_args(argv)
    tune = [int(x) for x in a.tune.split(",")]
    test = [int(x) for x in a.test.split(",")]
    if a.frozen:
        extra = [int(x) for x in a.frozen.split(",")]
        tg = load(sorted(set(tune + test + extra) | {min(tune) - 1, min(extra) - 1}))
        print(check(tg), file=sys.stderr)
        L = frozen(tg, tune, {"Test": test, "Older seasons": extra})
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        (out / "td_layer1_frozen.md").write_text("\n".join(L) + "\n", encoding="utf-8")
        print(f"wrote {out / 'td_layer1_frozen.md'}", file=sys.stderr)
        return 0
    tg = load(sorted(set(tune + test) | {min(tune) - 1}))
    note = check(tg)
    print(note, file=sys.stderr)

    # ---- grid over mean model (k, gamma) and shape, chosen on TUNE --------
    wf = {}
    grid = []
    for k, g in itertools.product(K_GRID, GAMMA_GRID):
        dtu, dte = walk_forward(tg, tune, k, g), walk_forward(tg, test, k, g)
        wf[(k, g)] = (dtu, dte)
        for sh in shapes_for(dtu):
            grid.append({"k": k, "gamma": g, "shape": sh,
                         "tune": score(dtu, sh), "test": score(dte, sh)})
    best = min(grid, key=lambda x: x["tune"]["crps"])

    # ---- the ladder: engine today, then one component at a time ---------
    steps = [("Engine today: league ratio, linear, Poisson", None, 0.0, ("Poisson", None)),
             ("+ team-specific ratio", best["k"], 0.0, ("Poisson", None)),
             ("+ fitted shape", best["k"], 0.0, None),
             ("+ elasticity to implied total", best["k"], best["gamma"], best["shape"])]
    ladder, prev = [], None
    for name, k, g, sh in steps:
        if sh is None:   # the shape fitted for this (k, linear) mean on TUNE
            cands = [x for x in grid if x["k"] == k and x["gamma"] == 0.0]
            sh = min(cands, key=lambda x: x["tune"]["crps"])["shape"]
        dte = wf[(k, g)][1]
        m = score(dte, sh)
        diff = boot_diff(dte, sh, prev[0], prev[1]) if prev else None
        ladder.append((name, k, g, sh, m, diff))
        prev = (dte, sh)

    dbest = wf[(best["k"], best["gamma"])][1].copy()
    dbest["q"] = pd.qcut(dbest["mu"], 5, labels=False)
    calib = dbest.groupby("q").agg(mu=("mu", "mean"), actual=("tds", "mean"),
                                   var_actual=("tds", "var"), n=("tds", "size"))
    base_calib = wf[(None, 0.0)][1].assign(
        q=lambda d: pd.qcut(d["mu"], 5, labels=False)).groupby("q").agg(
        mu=("mu", "mean"), actual=("tds", "mean"))

    ch = [(al, *channel_eval(tg, tune, al), channel_eval(tg, test, al)[0]) for al in ALPHA_GRID]
    ch_best = min(ch, key=lambda x: x[1])
    _, league_mix = T.channel_shares(tg, None)
    te = tg[tg["season"].isin(test)]
    ratio_all = te["tds"].sum() / te["points"].sum()
    ratio_off = te[list(T.OFFENSIVE)].sum().sum() / te["points"].sum()

    dec = decompose(tg, tune + test)

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    write_report(out / "td_layer1.md", tg, note, grid, best, ladder, calib, base_calib,
                 ch, ch_best, league_mix, ratio_all, ratio_off, tune, test, dec)
    return 0


def _shape(sh):
    fam, par = sh
    return fam if par is None else (f"NegBin r={par:.1f}" if fam == "NegBin" else f"Binomial n={par}")


def _k(k):
    return "league" if k is None else f"team k={k:.0f}"


def _var(mu, sh):
    fam, par = sh
    return mu if fam == "Poisson" else (mu + mu ** 2 / par if fam == "NegBin" else mu * (1 - mu / par))


def write_report(path, tg, note, grid, best, ladder, calib, base_calib, ch, ch_best,
                 league_mix, ratio_all, ratio_off, tune, test, dec=None):
    L = ["# Layer 1: team touchdown distributions", "",
         f"Tune seasons {tune}, test seasons {test} (never used for any choice). "
         f"{len(tg)} team-games with closing lines. Walk-forward: every game predicted "
         "from the prior season plus the earlier weeks of its own.", "",
         f"Data check: {note}", "",
         "## Ablation ladder (test seasons)", "",
         "Each row adds one component to the row above, using the value chosen on the tune seasons.", "",
         "| step | CRPS | log score | bias | change vs row above (95% CI, game-clustered) |",
         "|---|---|---|---|---|"]
    for name, k, g, sh, m, diff in ladder:
        detail = f"{name} ({_k(k)}, gamma={g:g}, {_shape(sh)})"
        if diff is None:
            ch_txt = "baseline"
        else:
            d, lo, hi = diff
            verdict = "better" if hi < 0 else ("worse" if lo > 0 else "not established")
            ch_txt = f"{d:+.4f} ({lo:+.4f}, {hi:+.4f}) {verdict}"
        L.append(f"| {detail} | {m['crps']:.4f} | {m['log']:.4f} | {m['bias']:+.3f} | {ch_txt} |")

    L += ["", "## Mean calibration by predicted-mean quintile (test)", "",
          "| quintile | engine today: predicted | chosen: predicted | actual | actual variance | chosen shape's variance |",
          "|---|---|---|---|---|---|"]
    for q, row in calib.iterrows():
        L.append(f"| {int(q) + 1} | {base_calib.loc[q, 'mu']:.2f} | {row['mu']:.2f} | {row['actual']:.2f} | "
                 f"{row['var_actual']:.2f} | {_var(row['mu'], best['shape']):.2f} |")
    L += ["", "Actual variance is within-quintile, so it also contains the spread of means inside "
              "each quintile. That can only INFLATE it, which makes any shortfall against the "
              "Poisson variance conservative.", "",
          f"League TDs per point, test seasons: **{ratio_all:.4f}** all touchdowns, "
          f"**{ratio_off:.4f}** offensive only. The engine's constant ({ENGINE_CONSTANT}) is the "
          "offensive figure, so it agrees.", "",
          ]
    if dec is not None:
        L += ["## Points decomposition by implied-total quintile (all seasons in the run)", "",
              "TDs = points x TDs-per-point. A rising `points - implied` means high-total teams beat "
              "their market total (a points effect); a rising TDs-per-point means they convert more "
              "of their points into touchdowns (a conversion effect).", "",
              "| quintile | implied | actual points | points - implied (se) | TDs/point | offensive TDs/point | TDs | n |",
              "|---|---|---|---|---|---|---|---|"]
        for q, r in dec.iterrows():
            L.append(f"| {int(q) + 1} | {r['implied']:.1f} | {r['points']:.1f} | "
                     f"{r['gap']:+.2f} ({r['gap_se']:.2f}) | {r['td_per_pt']:.4f} | "
                     f"{r['off_td_per_pt']:.4f} | {r['tds']:.2f} | {int(r['n'])} |")
        L.append("")
    L += ["## Full grid, top 12 by tune CRPS", "",
          "| mean | gamma | shape | tune CRPS | test CRPS | test log score |", "|---|---|---|---|---|---|"]
    for x in sorted(grid, key=lambda x: x["tune"]["crps"])[:12]:
        tag = " **chosen**" if x is best else ""
        L.append(f"| {_k(x['k'])} | {x['gamma']:g} | {_shape(x['shape'])} | {x['tune']['crps']:.4f} | "
                 f"{x['test']['crps']:.4f} | {x['test']['log']:.4f} |{tag}")
    L += ["", "## Channel mix", "",
          "Log loss of each touchdown's actual channel under the predicted mix (lower is better).", "",
          "| mix | tune log loss | test log loss | TDs (tune) |", "|---|---|---|---|"]
    for al, lt, n, lx in ch:
        tag = " **chosen**" if al == ch_best[0] else ""
        name = "league mix" if al is None else f"team, alpha={al:.0f} TDs"
        L.append(f"| {name} | {lt:.4f} | {lx:.4f} | {n} |{tag}")
    L += ["", "League channel mix, all seasons in the run:", "", "| channel | share |", "|---|---|"]
    for c in T.CHANNELS:
        L.append(f"| {c} | {league_mix[c]:.1%} |")
    path.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {path}", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())

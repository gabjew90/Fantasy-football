# expires: 2026-11-08
"""Where do the backs' carries misses come from: the team's carries, or his share of them?

The user's question (2026-10-09), after round 28b (a wider carry split) lost on rushing attempts:
before registering another width round, find which stage of the carries draw is too narrow, and
whether game script (the score) drives it. No model change; a diagnostic on saved harness runs.

The live sampler (model.simulate_team_rush) draws a back's carries in two stages:
  1. team carries ~ NegBinomial(mean = team_carries_env, r = the season's team_carries_r);
  2. his carries given the team's: the split is QB-FIRST (model._allocate_qb_first): the starting
     QB's share Q ~ Beta(c_qb q, c_qb (1 - q)), and the rest of the team splits 1 - Q through a
     Dirichlet at c = share_conc_carries over their shares / (1 - q), so a back's share is
     (1 - Q) D with D ~ Beta(c b, c (1 - b)), b = p / (1 - q), and his carries Binomial(T, share).
This study grades each stage ALONE against what happened:
  - stage 1 on the team's actual carries (one row per team-game);
  - stage 2 on his actual carries GIVEN the team's actual carries (one row per back-game);
and, as a check that the two-stage approximation is faithful, the two stages recombined against
the harness's own carries PIT (pit_car). Then both stages' misses against the game's surprise
margin (final margin minus the margin the spread expected), the game-script question.

Approximations, stated: p is mean_car_model / team_carries_env (the sim's realised mean share,
after the share rescale) and q the same for the team's QB with the most simulated carries; a
team-game with no QB row, or a run without share_conc_qb, uses the plain Dirichlet marginal
Beta(c p, c (1 - p)). The recombined check says whether the approximation holds: if the
recombined outside-the-80%-range rate is far from pit_car's, it does not. Stage 2 is graded by
Monte Carlo (S draws a row), not a closed form.

Inputs: the --save-results pickles of a shipped-settings harness run (kind 'harness') and the
harness's frames caches (_frames_<season>_*.pkl: games and twc are read). Reads files only.
Usage: python experiments/game_script_carries.py --run RUN.pkl [--run RUN2.pkl] --frames-dir DIR
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

OUT = Path(__file__).resolve().parent / "out"
SEED = 20261009
# surprise-margin buckets, points (final margin minus the spread's expected margin, the team's view)
EDGES = [-np.inf, -14, -7, 0, 7, 14, np.inf]
LABELS = ["<= -14", "-14 to -7", "-7 to 0", "0 to 7", "7 to 14", ">= 14"]
# WHICH WAY THE SHARE MISSES (the user, 2026-10-09: too few carries or too many?). A collapse is a
# game with at most COLLAPSE x the carries his share of the team's actual total would give him (an
# early exit, a benching); a boom at least BOOM x. Counted only where that expected workload is at
# least MIN_EXPECTED carries, so a two-carry backup's one extra carry is not a "boom". Display
# thresholds, picked, not measured: the comparison is the engine's own chance of the same event.
COLLAPSE, BOOM, MIN_EXPECTED = 0.4, 1.5, 6.0


def load_frames(frames_dir: Path, season: int):
    fs = sorted(frames_dir.glob(f"_frames_{season}_*.pkl"))
    if not fs:
        sys.exit(f"no frames cache for {season} in {frames_dir}")
    games, _gm, _roles, _roster, _rec, _rush, _twt, twc, _kneel, _pas = pd.read_pickle(fs[-1])
    return games, twc


def rpit_nb(x, mu, r, rng):
    """Randomised PIT of a count x under NegBinomial(mean mu, dispersion r)."""
    p = r / (r + mu)
    lo = stats.nbinom.cdf(x - 1, r, p)
    hi = stats.nbinom.cdf(x, r, p)
    return lo + rng.random(len(x)) * (hi - lo)


def share_draws(rng, S, p, q, c, c_qb):
    """S draws of one back's share under the harness's split (the module docstring)."""
    if q is None or not np.isfinite(q) or c_qb is None or q <= 0 or q >= 1 - p:
        return rng.beta(c * p, c * (1 - p), size=S)
    b = p / (1 - q)
    Q = rng.beta(c_qb * q, c_qb * (1 - q), size=S)
    return (1 - Q) * rng.beta(c * b, c * (1 - b), size=S)


def mc_pit(draws, x, rng) -> float:
    return float((draws < x).mean() + rng.random() * (draws == x).mean())


def tails(u) -> tuple[float, float]:
    """(share below the 10th percentile, share above the 90th); 10% each when calibrated."""
    u = np.asarray(u, dtype=float)
    u = u[~np.isnan(u)]
    return (float((u < 0.1).mean()), float((u > 0.9).mean())) if len(u) else (float("nan"), float("nan"))


def outside(u) -> float:
    u = np.asarray(u, dtype=float)
    u = u[~np.isnan(u)]
    return float(((u < 0.1) | (u > 0.9)).mean()) if len(u) else float("nan")


def build(run_paths, frames_dir: Path):
    rows, metas = [], {}
    for rp in run_paths:
        o = pd.read_pickle(rp)
        if o.get("kind") != "harness":
            sys.exit(f"{rp}: not a harness --save-results pickle")
        for m in o.get("metas") or []:
            metas[int(m["season"])] = m
        rows.append(o["results"])
    seen = {}
    for rp, r_ in zip(run_paths, rows):
        for sn in r_.season.unique():
            if sn in seen:
                sys.exit(f"season {sn} is in two runs ({seen[sn]}, {rp}): pass one run per season")
            seen[sn] = rp
    res = pd.concat(rows, ignore_index=True)
    out = []
    for season, d in res.groupby("season"):
        if int(season) not in metas:
            sys.exit(f"no meta (team_carries_r, width) for {season} in the runs")
        m = metas[int(season)]
        games, twc = load_frames(frames_dir, int(season))
        d = d.merge(twc.rename(columns={"team_carries": "team_carries_act"}), on=["team", "week"], how="left")
        # the game's result from the team's side, joined on (week, team): the harness's game_id is its own
        # format (date_HOME_AWAY), not nflverse's. nflverse: result and spread_line are both from the HOME
        # team's view (spread_line > 0 = home favoured).
        g = games[games.game_type == "REG"]
        side = pd.concat([
            pd.DataFrame({"week": g.week, "team": g.home_team, "margin": g.home_score - g.away_score,
                          "expected": g.spread_line}),
            pd.DataFrame({"week": g.week, "team": g.away_team, "margin": g.away_score - g.home_score,
                          "expected": -g.spread_line})], ignore_index=True)
        if side.duplicated(["week", "team"]).any():
            sys.exit(f"{season}: a team plays twice in one week in games")
        d = d.merge(side, on=["week", "team"], how="left")
        d["surprise"] = d.margin - d.expected
        d["team_carries_r"] = float(m["team_carries_r"])
        d["conc"] = float(m["width"]["share_conc_carries"])
        d["conc_qb"] = m["width"].get("share_conc_qb")
        # the team's starting QB's simulated mean share (the QB with the most simulated carries)
        qb = d[d.slot.astype(str).str.startswith("QB")].sort_values("mean_car_model", ascending=False)
        qb = qb.drop_duplicates(["team", "week"]).assign(q=lambda x: x.mean_car_model / x.team_carries_env)
        d = d.merge(qb[["team", "week", "q"]], on=["team", "week"], how="left")
        out.append(d)
    return pd.concat(out, ignore_index=True)


def analyse(d: pd.DataFrame) -> list[str]:
    rng = np.random.default_rng(SEED)
    L = []
    miss_team = d.team_carries_act.isna().sum()
    miss_game = d.surprise.isna().sum()
    backs = d[d.rush_pop.astype(bool) & d.slot.astype(str).str.startswith("RB")
              & d.team_carries_act.notna() & (d.mean_car_model > 0)].copy()
    backs["p"] = (backs.mean_car_model / backs.team_carries_env).clip(1e-6, 0.999)

    # ---- stage 1: the team's carries, one row per team-game
    tg = d.drop_duplicates(["season", "team", "week"])
    tg = tg[tg.team_carries_act.notna()].copy()
    mu, r, x = tg.team_carries_env.to_numpy(float), tg.team_carries_r.to_numpy(float), tg.team_carries_act.to_numpy(float)
    tg["u_team"] = rpit_nb(x, mu, r, rng)
    tg["z_team"] = (x - mu) / np.sqrt(mu + mu * mu / r)

    # ---- stage 2: his carries given the team's actual carries; and the check: both stages
    # recombined against the harness's own carries PIT. Monte Carlo under the harness's split.
    S = 4000
    n = backs.team_carries_act.to_numpy(int)
    p, c = backs.p.to_numpy(float), backs.conc.to_numpy(float)
    q = backs.q.to_numpy(float)
    c_qb = backs.conc_qb.to_numpy(object)
    k = backs.act_carries.to_numpy(float)
    mu_b = backs.team_carries_env.to_numpy(float)
    r_b = backs.team_carries_r.to_numpy(float)
    u_share, z_share, u_comb = (np.empty(len(backs)) for _ in range(3))
    p_collapse, p_boom = np.full(len(backs), np.nan), np.full(len(backs), np.nan)
    for i in range(len(backs)):
        cq = None if c_qb[i] is None or c_qb[i] != c_qb[i] else float(c_qb[i])
        sh = share_draws(rng, S, p[i], q[i], c[i], cq)
        C2 = rng.binomial(n[i], sh)
        u_share[i] = mc_pit(C2, k[i], rng)
        z_share[i] = (k[i] - C2.mean()) / max(C2.std(), 1e-9)
        if n[i] * p[i] >= MIN_EXPECTED:
            # the engine's own chance of a collapse / a boom given the team's actual total
            p_collapse[i] = float((C2 <= COLLAPSE * n[i] * p[i]).mean())
            p_boom[i] = float((C2 >= BOOM * n[i] * p[i]).mean())
        T = rng.negative_binomial(r_b[i], r_b[i] / (r_b[i] + mu_b[i]), size=S)
        u_comb[i] = mc_pit(rng.binomial(T, share_draws(rng, S, p[i], q[i], c[i], cq)), k[i], rng)
    backs["u_share"], backs["z_share"], backs["u_comb"] = u_share, z_share, u_comb
    backs["p_collapse"], backs["p_boom"] = p_collapse, p_boom
    expd = n * p
    backs["collapse"] = np.where(expd >= MIN_EXPECTED, k <= COLLAPSE * expd, np.nan)
    backs["boom"] = np.where(expd >= MIN_EXPECTED, k >= BOOM * expd, np.nan)
    # NO TOUCH AT ALL (0 carries, 0 targets): mostly a late scratch or a game he never entered, which
    # the harness's roster status cannot tell from an early exit -- and Sleeper voids such a leg. Every
    # tail and event below is shown with and without them.
    backs["no_touch"] = (backs.act_carries.fillna(0) == 0) & (backs.act_targets.fillna(0) == 0)
    backs["share_res"] = np.where(n > 0, k / np.maximum(n, 1) - p, np.nan)
    qb_first = backs.q.notna() & backs.conc_qb.notna()

    L += ["# Backs' carries: which stage is too narrow, and does game script drive it", "",
          f"*Generated by experiments/game_script_carries.py (seed {SEED}). Seasons: "
          f"{', '.join(str(s) for s in sorted(d.season.unique()))}. A calibrated stage puts 20% of outcomes "
          f"outside its own 10th-90th percentile and has a mean squared standardised miss of 1.0.*", "",
          f"Rows: {len(tg)} team-games, {len(backs)} back-games "
          f"({(backs.slot == 'RB1').sum()} RB1; {int(qb_first.sum())} graded under the QB-first split). "
          f"Missing actual team carries: {miss_team} rows; missing game result: {miss_game} rows. Seasons "
          f"missing from the harness's usual 2022-25: "
          f"{', '.join(str(s) for s in sorted(set(range(2022, 2026)) - set(int(x) for x in d.season.unique()))) or 'none'}.",
          "",
          "## The two stages, graded alone", "",
          "| Stage | Rows | Outside the 80% range | Below the 10th pct | Above the 90th pct | "
          "Mean squared standardised miss |", "|---|---:|---:|---:|---:|---:|",
          f"| 1. Team carries vs the engine's team mean | {len(tg)} | {100 * outside(tg.u_team):.1f}% | "
          f"{100 * tails(tg.u_team)[0]:.1f}% | {100 * tails(tg.u_team)[1]:.1f}% | {np.mean(tg.z_team ** 2):.2f} |"]
    played = backs[~backs.no_touch]
    groups = (("all backs", backs), ("RB1", backs[backs.slot == "RB1"]), ("RB2+", backs[backs.slot != "RB1"]),
              ("all backs, touched the ball", played), ("RB1, touched the ball", played[played.slot == "RB1"]))
    for lab, sub in groups:
        lo, hi = tails(sub.u_share)
        L.append(f"| 2. His carries given the team's actual carries ({lab}) | {len(sub)} | "
                 f"{100 * outside(sub.u_share):.1f}% | {100 * lo:.1f}% | {100 * hi:.1f}% | "
                 f"{np.mean(sub.z_share ** 2):.2f} |")
    lo, hi = tails(backs.pit_car)
    L.append(f"| Both together: the harness's carries PIT (all backs) | {len(backs)} | "
             f"{100 * outside(backs.pit_car):.1f}% | {100 * lo:.1f}% | {100 * hi:.1f}% | - |")
    L += ["", f"## Collapses and booms: games with at most {COLLAPSE:g}x, or at least {BOOM:g}x, the carries "
              f"his share of the team's actual total gives him (where that is {MIN_EXPECTED:g}+)", "",
          f"Zero-touch back-games (0 carries, 0 targets; mostly scratches, which Sleeper voids): "
          f"{int(backs.no_touch.sum())} of {len(backs)}. The thresholds are not symmetric, so compare each side's "
          f"ratio (happened / expected), not the two counts.", "",
          "| Backs | Games | Collapses: happened / engine expected | Ratio | Booms: happened / engine expected | Ratio |",
          "|---|---:|---:|---:|---:|---:|"]
    for lab, sub in groups:
        e = sub[sub.collapse.notna()]
        rc = e.collapse.sum() / e.p_collapse.sum() if e.p_collapse.sum() > 0 else float("nan")
        rb = e.boom.sum() / e.p_boom.sum() if e.p_boom.sum() > 0 else float("nan")
        L.append(f"| {lab} | {len(e)} | {int(e.collapse.sum())} ({100 * e.collapse.mean():.1f}%) / "
                 f"{e.p_collapse.sum():.0f} ({100 * e.p_collapse.mean():.1f}%) | {rc:.2f} | {int(e.boom.sum())} "
                 f"({100 * e.boom.mean():.1f}%) / {e.p_boom.sum():.0f} ({100 * e.p_boom.mean():.1f}%) | {rb:.2f} |")
    L += ["", "## The check: the two stages recombined against the harness's own carries PIT", "",
          "| Back-games | Recombined: outside the 80% range | Harness pit_car: outside the 80% range |",
          "|---:|---:|---:|",
          f"| {len(backs)} | {100 * outside(backs.u_comb):.1f}% | {100 * outside(backs.pit_car):.1f}% |", "",
          "If these two differ by more than about 2 points, the stage-2 approximation (the realised mean "
          "shares, the QB-first split) is not faithful and the stage table above should not be read.", ""]

    # ---- game script
    tg["bucket"] = pd.cut(tg.surprise, EDGES, labels=LABELS)
    backs["bucket"] = pd.cut(backs.surprise, EDGES, labels=LABELS)
    L += ["## Game script: the surprise margin (final margin minus what the spread expected)", "",
          "| Surprise margin | Team-games | Team carries: actual minus engine | Team outside 80% | "
          "RB1 share: actual minus engine | RB1 share stage outside 80% | RB1 games |",
          "|---|---:|---:|---:|---:|---:|---:|"]
    rb1 = backs[backs.slot == "RB1"]
    for lab in LABELS:
        t_ = tg[tg.bucket == lab]
        b_ = rb1[rb1.bucket == lab]
        L.append(f"| {lab} | {len(t_)} | {(t_.team_carries_act - t_.team_carries_env).mean():+.1f} | "
                 f"{100 * outside(t_.u_team):.0f}% | {100 * b_.share_res.mean():+.1f} pts | "
                 f"{100 * outside(b_.u_share):.0f}% | {len(b_)} |")
    ok = tg.surprise.notna()
    corr_t = float(np.corrcoef(tg.surprise[ok], tg.z_team[ok])[0, 1]) if ok.sum() > 2 else float("nan")
    ok2 = rb1.surprise.notna() & rb1.share_res.notna()
    corr_s = float(np.corrcoef(rb1.surprise[ok2], rb1.share_res[ok2])[0, 1]) if ok2.sum() > 2 else float("nan")
    L += ["", f"Correlation with the surprise margin: team carries' standardised miss {corr_t:+.2f} "
              f"(share of its variance: {100 * corr_t ** 2:.0f}%); RB1's share miss {corr_s:+.2f} "
              f"({100 * corr_s ** 2:.0f}%).", "",
          "Read: the surprise margin is not known before the game, so it cannot be an input; what it shows is "
          "whether a stage's misses move with the score, which says what kind of width (team volume tied to "
          "the score, or the split) a round would have to add. It runs both ways: leading teams run more, and "
          "teams that run well take leads, so a correlation is an upper bound on game script, not a measure "
          "of it.", ""]
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run", action="append", required=True, help="a harness --save-results pickle (repeatable)")
    ap.add_argument("--frames-dir", required=True, help="the harness frames cache directory")
    ap.add_argument("--out", default=str(OUT / "game_script_carries.md"))
    a = ap.parse_args(argv)
    d = build([Path(p) for p in a.run], Path(a.frames_dir))
    text = "\n".join(analyse(d)) + "\n"
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(text, encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

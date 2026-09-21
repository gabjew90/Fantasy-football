"""Does the expected-points model beat consensus? Tune on 2025, test on 2026 week 2.

  python scripts/xfp_eval.py [--test-week 2] [--no-tune]

1. TUNE on a 2025 walk-forward: every week 2-18 predicted from 2024 priors and
   2025 weeks before it, over a small grid of the framework's open knobs --
   the prior's weight (k), a last-4-weeks window versus season-to-date, and
   whether the capped efficiency step is on.
2. FREEZE the configuration with the lowest pooled error.
3. TEST it on 2026 week 2, predicted from 2025 and 2026 week 1 only.

Baselines. Sleeper's weekly projection is the right comparison, but its
per-player `updated_at` is stamped at serve time, so it cannot be PROVEN to be
the pre-kickoff number. The manager's consensus snapshot committed Wed
2026-09-16 17:52 PT (state/kv.json at 0246c1c) is provably pre-kickoff but is
a season-rate figure that knows nothing about the week's matchup. Both are
scored; neither is trusted blindly.

Population: RB/WR/TE who PLAYED the week and whom Sleeper projected at 5+
points -- the pool a start/sit decision is actually made from. The model has
no injury feed, so players ruled out are excluded rather than scored as its
misses; that is stated in the report, not hidden in the filter.
"""

from __future__ import annotations

import argparse
import itertools
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import polars as pl
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

import nflreadpy as nfl  # noqa: E402

from draftkit.seasondata import weekly_projections  # noqa: E402
from manager import xfp  # noqa: E402

CACHE = REPO / "data" / "cache" / "xfp"
SNAPSHOT_COMMIT = "0246c1c"   # state: weekly Fri 09/18 09:53 PT, consensus ts Wed 17:52 PT
RELEVANT = 5.0
GRID = {"k": [16.0, 64.0, 256.0], "window": [None, 4], "eff": [False, True]}


def scoring() -> dict:
    y = yaml.safe_load((REPO / "leagues" / "omnibeta.yaml").read_text(encoding="utf-8"))
    return y["expected"]["scoring"]


# ------------------------------------------------------------------ data

class Data:
    def __init__(self, seasons):
        self.pbp = nfl.load_pbp(seasons)
        self.stats = nfl.load_player_stats(seasons).filter(pl.col("season_type") == "REG")
        self.sched = nfl.load_schedules(seasons)
        self.car, self.tgt = xfp.opportunities(self.pbp)
        self.pos = xfp.positions(self.stats)
        self.tv = xfp.team_volume(self.car, self.tgt)
        self.pg = xfp.player_games(self.car, self.tgt)
        self.lines = xfp.team_lines(self.sched)
        ids = nfl.load_ff_playerids()
        self.xwalk = (ids.filter(pl.col("sleeper_id").is_not_null() & pl.col("gsis_id").is_not_null())
                      .select(pl.col("sleeper_id").cast(pl.Utf8), pl.col("gsis_id").alias("player_id"))
                      .unique("sleeper_id"))
        self._values = {}

    def played(self, season, weeks):
        return (self.stats.filter((pl.col("season") == season) & pl.col("week").is_in(weeks)
                                  & pl.col("position_group").is_in(xfp.POSITIONS))
                .select("season", "week", pl.col("team"), "player_id"))

    def values(self, season):
        if season not in self._values:
            f = lambda d: d.filter(pl.col("season") == season)  # noqa: E731
            self._values[season] = xfp.touch_values(f(self.car), f(self.tgt), f(self.pos), SCORING)
        return self._values[season]


def sleeper_week(season: int, week: int) -> dict[str, float]:
    """Sleeper weekly projection in league scoring, cached so a rerun cannot
    silently compare against a number Sleeper has since changed."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"sleeper_{season}_wk{week:02d}.json"
    if f.exists():
        return json.loads(f.read_text(encoding="utf-8"))
    got = weekly_projections(SCORING, str(season), week) or {}
    f.write_text(json.dumps(got), encoding="utf-8")
    return got


def snapshot_consensus() -> dict[str, float]:
    """The provably pre-kickoff consensus, as a weekly rate."""
    raw = subprocess.run(["git", "show", f"{SNAPSHOT_COMMIT}:state/kv.json"], cwd=REPO,
                         capture_output=True, check=True).stdout.decode("utf-8")
    data = json.loads(raw)["consensus:omnibeta:2026"]["data"]
    return {pid: v["mean"] / 17.0 for pid, v in data.items() if v.get("mean")}


# ------------------------------------------------------------------ predict

def predict(D: Data, season: int, week: int, k: float, window, eff: bool) -> pl.DataFrame:
    prior = season - 1
    cur_weeks = list(range(1, week))
    in_s = lambda d: d.filter(pl.col("season") == season)  # noqa: E731
    in_p = lambda d: d.filter(pl.col("season") == prior)  # noqa: E731
    before = lambda d: d.filter((pl.col("season") == season) & (pl.col("week") < week))  # noqa: E731

    values = D.values(prior)
    tv_fit = pl.concat([in_p(D.tv), before(D.tv)])
    coefs = xfp.fit_volume(tv_fit, D.lines)
    week_lines = D.lines.filter((pl.col("season") == season) & (pl.col("week") == week))

    # one position per player: this season's if he has played, else last season's
    pos = (pl.concat([in_p(D.pos).with_columns(pl.lit(0).alias("_o")),
                      in_s(D.pos).with_columns(pl.lit(1).alias("_o"))])
           .sort("_o").group_by("player_id").agg(pl.col("pos").last())
           .with_columns(pl.lit(season).alias("season")))

    talent = matchup = None
    if eff:
        pg_e = pl.concat([in_p(D.pg), before(D.pg)])
        st_e = pl.concat([in_p(D.stats), before(D.stats)])
        pos_e = pl.concat([in_p(D.pos), in_s(D.pos)]).unique(["season", "player_id"])
        talent, matchup = xfp.efficiency(pg=pg_e, stats=st_e, pos=pos_e,
                                         values=values, scoring=SCORING)
    return xfp.project(
        week_lines=week_lines, coefs=coefs, values=values,
        pg_cur=before(D.pg), tv_cur=before(D.tv), played_cur=D.played(season, cur_weeks),
        pg_pri=in_p(D.pg), tv_pri=in_p(D.tv), played_pri=D.played(prior, list(range(1, 23))),
        pos=pos, k=k, window=window, talent=talent, matchup=matchup)


def frame(D: Data, season: int, week: int, cfg: dict, extra: dict | None = None) -> pl.DataFrame:
    """Predictions, actuals and baselines for one week, on the decision pool."""
    p = predict(D, season, week, cfg["k"], cfg["window"], cfg["eff"])
    act = (D.stats.filter((pl.col("season") == season) & (pl.col("week") == week)
                          & pl.col("position_group").is_in(xfp.POSITIONS))
           .select("player_id", pl.col("player_display_name").alias("name"),
                   pl.col("position_group").alias("pos_act"),
                   xfp.fantasy_points(D.stats, SCORING).alias("actual")))
    slp = pl.DataFrame({"sleeper_id": list((s := sleeper_week(season, week)).keys()),
                        "sleeper": list(s.values())}, schema={"sleeper_id": pl.Utf8, "sleeper": pl.Float64})
    slp = slp.join(D.xwalk, on="sleeper_id", how="inner")
    d = (act.join(slp.select("player_id", "sleeper", "sleeper_id"), on="player_id", how="inner")
         .join(p.select("player_id", "game_id", "xfp", "xfp_base", "heuristic", "td_share"),
               on="player_id", how="left")
         .filter(pl.col("sleeper") >= RELEVANT)
         .with_columns(pl.lit(season).alias("season"), pl.lit(week).alias("week")))
    if extra:
        for name, m in extra.items():
            d = d.join(pl.DataFrame({"sleeper_id": list(m.keys()), name: list(m.values())},
                                    schema={"sleeper_id": pl.Utf8, name: pl.Float64}),
                       on="sleeper_id", how="left")
    return d


# ------------------------------------------------------------------ score

def spearman(a, b):
    ra, rb = a.argsort().argsort(), b.argsort().argsort()
    return float(np.corrcoef(ra, rb)[0, 1]) if len(a) > 2 else float("nan")


def pairwise(d: pl.DataFrame, col: str, band=None):
    """Within position and week: of every pair whose actual scores differ,
    how often does `col` order them correctly? That is a start/sit decision.
    band=(lo, hi) restricts to pairs whose predicted gap lies in [lo, hi)."""
    right = total = 0
    for _, g in d.group_by(["season", "week", "pos_act"]):
        p, a = g[col].to_numpy(), g["actual"].to_numpy()
        i, j = np.triu_indices(len(p), 1)
        dp, da = p[i] - p[j], a[i] - a[j]
        keep = da != 0
        if band is not None:
            keep &= (np.abs(dp) >= band[0]) & (np.abs(dp) < band[1])
        right += int((np.sign(dp[keep]) == np.sign(da[keep])).sum())
        total += int(keep.sum())
    return right / total if total else float("nan"), total


def disagreements(d: pl.DataFrame, a_col: str, b_col: str):
    """On pairs where two predictors ORDER the players differently, how often
    is `a_col` right? This is the framework's step 6 question exactly: when
    the model overrides consensus, does the override pay?"""
    a_right = n = 0
    for _, g in d.group_by(["season", "week", "pos_act"]):
        A, B, y = g[a_col].to_numpy(), g[b_col].to_numpy(), g["actual"].to_numpy()
        i, j = np.triu_indices(len(y), 1)
        sa, sb, sy = np.sign(A[i] - A[j]), np.sign(B[i] - B[j]), np.sign(y[i] - y[j])
        m = (sa != sb) & (sa != 0) & (sb != 0) & (sy != 0)
        a_right += int((sa[m] == sy[m]).sum())
        n += int(m.sum())
    return a_right / n if n else float("nan"), n


def metrics(d: pl.DataFrame, col: str) -> dict:
    e = d[col].to_numpy() - d["actual"].to_numpy()
    pw, npairs = pairwise(d, col)
    return {"mae": float(np.abs(e).mean()), "rmse": float(np.sqrt((e ** 2).mean())),
            "bias": float(e.mean()), "spearman": spearman(d[col].to_numpy(), d["actual"].to_numpy()),
            "pairwise": pw, "pairs": npairs, "n": d.height}


def boot_mae_diff(d: pl.DataFrame, a: str, b: str, reps=2000, seed=7):
    """MAE(a) - MAE(b), resampling whole GAMES: players in one game share a
    script, so resampling players would overstate how much one week says."""
    rng = np.random.default_rng(seed)
    g = (d.with_columns((pl.col(a) - pl.col("actual")).abs().alias("_ea"),
                        (pl.col(b) - pl.col("actual")).abs().alias("_eb"))
         .group_by(["season", "week", "game_id"]).agg(pl.col("_ea").sum(), pl.col("_eb").sum(), pl.len()))
    ea, eb, n = g["_ea"].to_numpy(), g["_eb"].to_numpy(), g["len"].to_numpy()
    idx = rng.integers(0, len(n), size=(reps, len(n)))
    diffs = (ea[idx].sum(1) - eb[idx].sum(1)) / n[idx].sum(1)
    return float((ea.sum() - eb.sum()) / n.sum()), *np.percentile(diffs, [2.5, 97.5]).tolist()


# ------------------------------------------------------------------ run

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-week", type=int, default=2)
    ap.add_argument("--tune-weeks", default="2-18")
    ap.add_argument("--out", default=str(REPO / "reports" / "xfp_eval.md"))
    a = ap.parse_args(argv)
    lo, hi = (int(x) for x in a.tune_weeks.split("-"))

    D = Data([2024, 2025, 2026])
    configs = [dict(zip(GRID, v)) for v in itertools.product(*GRID.values())]

    # ---- tune on 2025 -------------------------------------------------
    tune = {}
    for cfg in configs:
        key = (cfg["k"], cfg["window"], cfg["eff"])
        frames = [frame(D, 2025, w, cfg) for w in range(lo, hi + 1)]
        f = pl.concat(frames).filter(pl.col("xfp").is_not_null())
        tune[key] = (metrics(f, "xfp"), f)
        print(f"tune k={cfg['k']:>5} window={str(cfg['window']):>4} eff={cfg['eff']!s:>5}: "
              f"MAE {tune[key][0]['mae']:.3f}  pairwise {tune[key][0]['pairwise']:.3f}", file=sys.stderr)
    best_key = min(tune, key=lambda k_: tune[k_][0]["mae"])
    best = dict(zip(GRID, best_key))
    f25 = tune[best_key][1]

    # ---- test on 2026 week W, frozen ----------------------------------
    snap = snapshot_consensus()
    f26 = frame(D, 2026, a.test_week, best, extra={"snapshot": snap})
    covered = f26.filter(pl.col("xfp").is_not_null())
    lost = f26.height - covered.height
    t = covered.with_columns(((pl.col("xfp") + pl.col("sleeper")) / 2).alias("blend"))
    f25b = f25.with_columns(((pl.col("xfp") + pl.col("sleeper")) / 2).alias("blend"))

    write_report(Path(a.out), tune, best, f25b, t, lost, a.test_week)
    return 0


def _row(name, m):
    return (f"| {name} | {m['mae']:.2f} | {m['rmse']:.2f} | {m['bias']:+.2f} | "
            f"{m['spearman']:.3f} | {m['pairwise']:.1%} |")


def write_report(out: Path, tune, best, f25, t, lost, W):
    L = [f"# Expected-points model vs consensus: 2025 walk-forward, 2026 week {W}", ""]
    L += ["Generated by `scripts/xfp_eval.py`. Scoring: Omnibeta (full PPR, 0.1/yd, 6/TD, "
          "-2/fumble lost). Population: RB/WR/TE who played and whom Sleeper projected at "
          f"{RELEVANT:.0f}+ points.", ""]

    L += ["## Tuning grid (2025 weeks 2-18, walk-forward)", "",
          "| k (prior weight) | window | efficiency step | MAE | pairwise |", "|---|---|---|---|---|"]
    for (k, w, e), (m, _) in sorted(tune.items(), key=lambda kv: kv[1][0]["mae"]):
        mark = " **chosen**" if (k, w, e) == tuple(best.values()) else ""
        L.append(f"| {k:.0f} | {'last 4' if w else 'season'} | {'on' if e else 'off'} | "
                 f"{m['mae']:.3f} | {m['pairwise']:.1%}{mark} |")
    L.append("")

    for title, d, cols in [
        ("2025 walk-forward (chosen configuration)", f25, ["xfp", "heuristic", "sleeper", "blend"]),
        (f"2026 week {W} (frozen, out of sample)", t,
         ["xfp", "heuristic", "sleeper", "snapshot", "blend"])]:
        d2 = d.filter(pl.all_horizontal([pl.col(c).is_not_null() for c in cols]))
        L += [f"## {title}", "", f"N = {d2.height} player-games.", "",
              "| predictor | MAE | RMSE | bias | Spearman | pairwise start/sit |",
              "|---|---|---|---|---|---|"]
        names = {"xfp": "model (xFP)", "heuristic": "framework heuristic", "sleeper": "Sleeper weekly",
                 "snapshot": "consensus season-rate (verified pre-game)", "blend": "50/50 model + Sleeper"}
        for c in cols:
            L.append(_row(names[c], metrics(d2, c)))
        diff, lo_, hi_ = boot_mae_diff(d2, "xfp", "sleeper")
        L += ["", f"MAE(model) - MAE(Sleeper) = **{diff:+.2f}**, 95% CI ({lo_:+.2f}, {hi_:+.2f}), "
                  f"game-clustered bootstrap. {'Excludes zero.' if lo_ > 0 or hi_ < 0 else 'Includes zero: no difference established.'}"]
        dr, dn = disagreements(d2, "xfp", "sleeper")
        L += [f"When model and Sleeper order a pair differently ({dn} pairs), the model is right "
              f"**{dr:.1%}** of the time.", ""]
        L += ["Pairwise accuracy by the size of the predicted gap (tests the 1.5-point coin-flip rule):", "",
              "| gap | model | Sleeper |", "|---|---|---|"]
        for band, lab in [((0, 1.5), "< 1.5"), ((1.5, 4), "1.5-4"), ((4, 999), "4+")]:
            pm, nm = pairwise(d2, "xfp", band)
            ps, ns = pairwise(d2, "sleeper", band)
            L.append(f"| {lab} | {pm:.1%} (n={nm}) | {ps:.1%} (n={ns}) |")
        err = np.abs(d2["xfp"].to_numpy() - d2["actual"].to_numpy()) / np.maximum(d2["xfp"].to_numpy(), 1)
        L += ["", f"Variance proxy: Spearman(TD share of xFP, relative miss) = "
                  f"**{spearman(d2['td_share'].to_numpy(), err):+.3f}** (positive = TD-heavy "
                  f"profiles miss by more, as the framework claims).", ""]
    if lost:
        L += [f"{lost} player(s) in the week-{W} pool had no projection from the model "
              "(no current or prior-season role) and are excluded from its rows.", ""]
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"wrote {out}", file=sys.stderr)


SCORING = scoring()

if __name__ == "__main__":
    raise SystemExit(main())

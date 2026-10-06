"""THE SCOREBOARD (reports/scoreboard.md): how the engine is judged for the way the user
bets -- he supplies the volume, the engine turns it into a chance at one line.

    python props/tools/scoreboard.py RUN.pkl [--seasons 2022,2023,2024,2025]
    python props/tools/scoreboard.py RUN.pkl --ref REF.pkl [--cluster team-season] [--seasons ...]

Reads backtest.py --conditional --save-results pickles. Per bet market, on the bettable
population (3+ projected targets; 8+ projected carries for rushing and rushing+receiving):

1. CONVERSION (main): the Over chance at a stand-in line (the pre-game expectation from inputs
   no setting moves, centred on Sleeper's lines by backtest.STANDIN_SCALE, at the half) GIVEN
   the player's actual targets / carries,
   scored by Brier and log loss against the outcome. Rows with zero actual volume have no
   conditional chance and are left out.
2. OWN VOLUME (secondary): the same lines with the engine's own volume -- the baseline the
   user's read departs from.
3. SPREAD: the game-to-game spread of targets / carries around the projection, real
   against the model's, in stable-role stretches (same team, same starting QB, same depth
   slot, 4+ games -- role only, never the projections), by volume band. Real spread includes
   undetected role drift, so it USUALLY overstates the true game-to-game spread and a model
   spread well above it is likely too wide -- an assumption about drift, not a guarantee
   (outside review, 2026-10-06).

With --ref, paired differences (positive = this run better) with 95% intervals resampling
whole games (default) or team-seasons (--cluster team-season, for changes that act on a
team all season), plus the mean move in the Over chance in points (the minimum-effect test).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

KEYS = ["season", "team", "week", "gsis_id"]
P_CLIP = (0.005, 0.995)
MARKETS = {  # market: (line col, conditional col, own-volume col, actual col, population)
    "receptions": ("L_rec", "pc_rec", "pu_rec", "act_receptions", "rec"),
    "receiving yards": ("L_yds", "pc_yds", "pu_yds", "act_rec_yards", "rec"),
    "rushing yards": ("L_rush", "pc_rush", "pu_rush", "act_rush_yards", "rb"),
    "rushing + receiving yards": ("L_rr", "pc_rr", "pu_rr", "act_rr", "rr"),
    # the starting QB, given every receiver's actual targets and the team's remaining ones
    "QB passing yards": ("L_pass", "pc_pass", "pu_pass", "act_pass_yards", "qb"),
}
MIN_TARGETS, MIN_CARRIES = 3.0, 8.0
ZONE = (0.15, 0.85)
TGT_BANDS = [(3, 5), (5, 8), (8, 11), (11, 99)]
CAR_BANDS = [(8, 12), (12, 16), (16, 20), (20, 99)]


def bettable(R: pd.DataFrame, pop: str) -> pd.Series:
    if pop == "rec":
        return R.mean_tgt.ge(MIN_TARGETS).fillna(False)
    if pop == "qb":
        return R.pass_pop.astype(bool)
    if pop == "rr":
        # the combined line is posted for pass-catching backs too: 8+ projected touches
        return R.rush_pop.astype(bool) & (R.mean_car_model.fillna(0) + R.mean_tgt.fillna(0)).ge(MIN_CARRIES)
    return R.rush_pop.astype(bool) & R.mean_car_model.ge(MIN_CARRIES).fillna(False)


def brier(p, y):
    return (p - y) ** 2


def logloss(p, y):
    p = np.clip(p, *P_CLIP)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def market_frame(R: pd.DataFrame, market: str, cohort: pd.DataFrame | None = None) -> pd.DataFrame:
    """The scored rows for one market: the bettable population with a line, a chance and an
    outcome -- or, with `cohort` (KEYS rows, the reference's population), exactly those
    player-games whatever this run's own projections say (a frozen comparison cohort)."""
    Lc, pc, pu, act, pop = MARKETS[market]
    if pc not in R:
        return R.iloc[0:0]
    if cohort is not None:
        keep = R.set_index(KEYS).index.isin(cohort.set_index(KEYS).index)
        d = R[keep & R[pc].notna() & R[Lc].notna() & R[act].notna()].copy()
    else:
        d = R[bettable(R, pop) & R[pc].notna() & R[Lc].notna() & R[act].notna()].copy()
    d["y"] = (d[act] > d[Lc]).astype(float)
    d["pc"], d["pu"], d["L"] = d[pc].astype(float), d[pu].astype(float), d[Lc].astype(float)
    return d


def cluster_ids(d: pd.DataFrame, how: str) -> np.ndarray:
    if how == "team-season":
        return (d.season.astype(str) + "_" + d.team.astype(str)).to_numpy()
    if "game_id" in d:
        return (d.season.astype(str) + "_" + d.game_id.astype(str)).to_numpy()
    return (d.season.astype(str) + "_" + d.team.astype(str) + "_" + d.week.astype(str)).to_numpy()


def cluster_ci(x: np.ndarray, ids: np.ndarray, reps: int, rng, level: float = 0.95) -> tuple[float, float]:
    ug, inv = np.unique(ids, return_inverse=True)
    sums, cnt = np.bincount(inv, weights=x, minlength=len(ug)), np.bincount(inv, minlength=len(ug))
    idx = rng.integers(0, len(ug), size=(reps, len(ug)))
    boot = sums[idx].sum(1) / cnt[idx].sum(1)
    a = 100 * (1 - level) / 2
    lo, hi = np.percentile(boot, [a, 100 - a])
    return float(lo), float(hi)


def single(R: pd.DataFrame) -> dict:
    out = {}
    for mk in MARKETS:
        d = market_frame(R, mk)
        if d.empty:
            continue
        out[mk] = {"n": int(len(d)), "over_rate": float(d.y.mean()),
                   "brier_c": float(brier(d.pc, d.y).mean()), "logloss_c": float(logloss(d.pc, d.y).mean()),
                   "brier_u": float(brier(d.pu, d.y).mean()), "logloss_u": float(logloss(d.pu, d.y).mean()),
                   "mean_pc": float(d.pc.mean())}
    return out


def compare(R: pd.DataFrame, Ref: pd.DataFrame, cluster: str, reps: int = 2000, seed: int = 11,
            level: float = 0.95, require_same_lines: bool = True) -> dict:
    rng = np.random.default_rng(seed)
    if level > 0.95:
        reps = max(reps, 10_000)      # an interval above 95% needs enough values in each tail
    out = {}
    for mk in MARKETS:
        a = market_frame(Ref, mk)
        if a.empty:
            continue                  # no evidence for this market: guard_verdict reports it missing
        # THE FROZEN COHORT (outside review, 2026-10-06): the candidate is scored on exactly the
        # reference's player-games, never on its own eligibility intersected with the reference's
        b = market_frame(R, mk, cohort=a[KEYS])
        for nm_, x_ in (("reference", a), ("candidate", b)):
            if x_.duplicated(KEYS).any():
                raise ValueError(f"{mk}: the {nm_} has duplicate player-games")
        if len(b) != len(a):
            raise ValueError(f"{mk}: the candidate scores {len(b)} of the reference's {len(a)} player-games "
                             "-- two settings must be scored on the same cohort (reports/scoreboard.md)")
        d = b.merge(a[KEYS + ["pc", "pu", "L", "y"]], on=KEYS, suffixes=("", "_ref"))
        if not (d.y == d.y_ref).all():
            raise ValueError(f"{mk}: the two runs disagree on outcomes -- not the same games")
        ids = cluster_ids(d, cluster)
        same = float((d.L == d.L_ref).mean())
        if same < 1.0 and require_same_lines:
            raise ValueError(f"{mk}: only {100 * same:.1f}% of rows share a stand-in line -- two settings "
                             "must be scored at the same lines (reports/scoreboard.md)")
        row = {"n": int(len(d)), "cluster": cluster, "same_lines": same}
        for tag, col in (("c", "pc"), ("u", "pu")):
            for nm, f in (("brier", brier), ("logloss", logloss)):
                diff = (f(d[f"{col}_ref"], d.y_ref) - f(d[col], d.y)).to_numpy()
                lo, hi = cluster_ci(diff, ids, reps, rng, level)
                base = float(f(d[f"{col}_ref"], d.y_ref).mean())
                row[f"{nm}_{tag}"] = {"gain": float(diff.mean()), "ci": [lo, hi],
                                      "relative": float(diff.mean() / base) if base else None}
        # THE DECISION ZONE (amendment): cases whose reference chance is 15-85% -- where a bet
        # at a typical price is decided -- log loss and Brier, which must agree in sign to ship
        for tag, col in (("c", "pc"), ("u", "pu")):
            z = d[(d[f"{col}_ref"] >= ZONE[0]) & (d[f"{col}_ref"] <= ZONE[1])]
            if len(z):
                zi = cluster_ids(z, cluster)
                zl = (logloss(z[f"{col}_ref"], z.y_ref) - logloss(z[col], z.y)).to_numpy()
                zb = (brier(z[f"{col}_ref"], z.y_ref) - brier(z[col], z.y)).to_numpy()
                row[f"zone_{tag}"] = {"n": int(len(z)), "share": float(len(z) / len(d)),
                                      "logloss": float(zl.mean()), "ci": list(cluster_ci(zl, zi, reps, rng, level)),
                                      "brier": float(zb.mean()), "agree": bool(np.sign(zl.mean()) == np.sign(zb.mean()))}
        row["move_points_c"] = float(100 * (d.pc - d.pc_ref).abs().mean())
        row["move_points_u"] = float(100 * (d.pu - d.pu_ref).abs().mean())
        out[mk] = row
    return out


MIN_GUARD_N = 200          # player-games a guard market needs before its score counts


def guard_verdict(c: dict, target: str | None, score: str = "logloss_c", floor: float = -0.005,
                  required=tuple(MARKETS), min_n: int = MIN_GUARD_N) -> dict:
    """A comparison's guards, complete or explicitly not (outside review, 2026-10-06):
    every required market other than `target` (None: a change judged elsewhere, e.g. the
    spread check, so every market is a guard) must be present in compare()'s output with
    min_n+ rows and a finite relative change at least `floor`. Missing, thin or non-finite
    evidence BLOCKS the verdict -- it never passes by being absent. score: "logloss_c"
    (conversion) or "logloss_u" (own volume), the path the change acts through.
    Returns {status: pass | fail | blocked, guards, missing, thin, nonfinite}."""
    guards, missing, thin, nonfinite = {}, [], [], []
    for mk in required:
        if mk == target:
            continue
        v = c.get(mk)
        if v is None:
            missing.append(mk)
            continue
        if v.get("n", 0) < min_n:
            thin.append(mk)
        rel = (v.get(score) or {}).get("relative")
        if rel is None or not np.isfinite(rel):
            nonfinite.append(mk)
            continue
        guards[mk] = float(rel)
    if target is not None and target not in c:
        missing.insert(0, target)
    status = ("blocked" if (missing or thin or nonfinite) else
              "pass" if all(g >= floor for g in guards.values()) else "fail")
    return {"status": status, "guards": guards, "missing": missing, "thin": thin, "nonfinite": nonfinite}


def stable_stretches(R: pd.DataFrame, vol: str, act: str, sd: str, opening: dict | None = None,
                     tol: float = 0.20, min_games: int = 4, by: str = "projection") -> pd.DataFrame:
    """Stable-role stretches: a player's consecutive games with one team and one starting
    QB (when `opening` maps (season, team, week) -> starter), extended while every game's
    projected volume stays within `tol` of the stretch's mean. One row per stretch of
    `min_games`+: mean projection, real residual SD (actual - projection, ddof 1), model SD
    (root mean square of the per-game simulated SD)."""
    rows = []
    d = R.dropna(subset=[vol, act, sd]).sort_values(["season", "gsis_id", "team", "week"])
    for (s_, g, t), x in d.groupby(["season", "gsis_id", "team"]):
        vals, y, m_sd = x[vol].to_numpy(float), x[act].to_numpy(float), x[sd].to_numpy(float)
        qbs = [(opening or {}).get((s_, t, int(w))) for w in x.week]
        slots = x["slot"].astype(str).tolist() if (by == "role" and "slot" in x) else [None] * len(x)
        n, i = len(x), 0
        while i < n:
            j = i + 1
            while j < n and qbs[j] == qbs[i]:
                if by == "role":
                    # stability from role alone (depth slot, team, starting QB): projections react
                    # to past outcomes, so filtering on them can favour calm stretches
                    if slots[j] != slots[i]:
                        break
                else:
                    seg = vals[i:j + 1]
                    if np.any(np.abs(seg - seg.mean()) > tol * seg.mean()):
                        break
                j += 1
            if j - i >= min_games:
                rows.append({"season": s_, "gsis_id": g, "team": t, "n": j - i, "proj": float(vals[i:j].mean()),
                             "real_sd": float(np.std(y[i:j] - vals[i:j], ddof=1)),
                             "model_sd": float(np.sqrt(np.mean(m_sd[i:j] ** 2)))})
            i = j
    return pd.DataFrame(rows, columns=["season", "gsis_id", "team", "n", "proj", "real_sd", "model_sd"])


def opening_starters(seasons, cache=None) -> dict:
    """{(season, team, week): the passer of the team's first dropback} from the backtest's
    cached play-by-play (the planned starter)."""
    import os
    import tempfile
    cache = Path(cache or os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
    out = {}
    for s_ in seasons:
        f = cache / f"pbp_{s_}.csv.gz"
        if not f.exists():
            continue
        p = pd.read_csv(f, low_memory=False, usecols=["posteam", "week", "play_type", "play_id", "passer_player_id"])
        p = p[(p.play_type == "pass") & p.passer_player_id.notna()].sort_values("play_id")
        for (t, w), pid in p.groupby(["posteam", "week"]).passer_player_id.first().items():
            out[(s_, t, int(w))] = pid
    return out


def spread_table(st: pd.DataFrame, bands, reps: int = 2000, seed: int = 5) -> list[dict]:
    rng = np.random.default_rng(seed)
    out = []
    for lo, hi in bands:
        b = st[(st.proj >= lo) & (st.proj < hi)]
        if len(b) < 10:
            continue
        r = b.real_sd.to_numpy(); m = b.model_sd.to_numpy()
        idx = rng.integers(0, len(b), size=(reps, len(b)))
        boot = np.sqrt((r[idx] ** 2).mean(1)) / np.sqrt((m[idx] ** 2).mean(1))
        ratio = float(np.sqrt((r ** 2).mean()) / np.sqrt((m ** 2).mean()))
        out.append({"band": f"{lo}-{hi if hi < 99 else '+'}", "stretches": int(len(b)),
                    "real_sd": float(np.sqrt((r ** 2).mean())), "model_sd": float(np.sqrt((m ** 2).mean())),
                    "ratio": ratio, "ci": [float(x) for x in np.percentile(boot, [2.5, 97.5])],
                    "reading": ("model too wide" if np.percentile(boot, 97.5) < 1 else
                                "model may be too narrow" if np.percentile(boot, 2.5) > 1 else "consistent")})
    return out


def load(path, seasons):
    R = pd.read_pickle(path)["results"]
    return R[R.season.isin(seasons)] if seasons else R


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--ref", default=None)
    ap.add_argument("--seasons", default=None)
    ap.add_argument("--cluster", choices=["game", "team-season"], default="game")
    ap.add_argument("--spread", action="store_true", help="also the stable-role spread check")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    seasons = [int(x) for x in a.seasons.split(",")] if a.seasons else None
    R = load(a.run, seasons)
    if "pc_rec" not in R:
        sys.exit("no scoreboard columns: rerun backtest.py with --conditional")
    out = {"single": single(R)}
    print("CONVERSION (actual volume plugged in) and OWN VOLUME, at stand-in lines, bettable players")
    for mk, v in out["single"].items():
        print(f"  {mk:26s} n={v['n']:5d}  Over rate {v['over_rate']:.3f}  Brier {v['brier_c']:.4f} / own {v['brier_u']:.4f}"
              f"  log loss {v['logloss_c']:.4f} / own {v['logloss_u']:.4f}")
    if a.ref:
        out["compare"] = compare(R, load(a.ref, seasons), a.cluster)
        print(f"\nTHIS RUN vs {Path(a.ref).name} (positive = this run better; {a.cluster}-clustered 95% CI)")
        for mk, v in out["compare"].items():
            c, u = v["logloss_c"], v["logloss_u"]
            print(f"  {mk:26s} n={v['n']:5d}  conversion log loss {c['gain']:+.5f} ({c['ci'][0]:+.5f}, {c['ci'][1]:+.5f})"
                  f" Brier {v['brier_c']['gain']:+.5f}  moves {v['move_points_c']:.2f} pts | own volume log loss "
                  f"{u['gain']:+.5f} ({u['ci'][0]:+.5f}, {u['ci'][1]:+.5f}) moves {v['move_points_u']:.2f} pts")
    if a.spread:
        out["spread"] = {}
        opening = opening_starters(sorted(R.season.unique()))
        for nm, vol, act, sd, bands, popm in (("targets", "mean_tgt", "act_targets", "sd_tgt", TGT_BANDS, None),
                                               ("carries", "mean_car_model", "act_carries", "sd_car", CAR_BANDS, "rb")):
            d = R if popm is None else R[R.rush_pop.astype(bool)]
            out["spread"][nm] = spread_table(stable_stretches(d, vol, act, sd, opening=opening, by="role"), bands)
            print(f"\nSPREAD of {nm} around the projection, stable-role stretches (real usually overstates it)")
            for b in out["spread"][nm]:
                print(f"  {b['band']:6s} stretches {b['stretches']:4d}  real {b['real_sd']:.2f}  model {b['model_sd']:.2f}"
                      f"  ratio {b['ratio']:.2f} ({b['ci'][0]:.2f}, {b['ci'][1]:.2f})  {b['reading']}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

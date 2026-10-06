"""Tier 3 diagnostic (reports/backup_qb_implied_total.md, pre-registered): in games a
backup QB STARTS, does the market's implied team total already carry the drop in his
receivers' yards and his passing yards?

    python props/tools/backup_implied_total.py <harness --save-results pickle, 2022-25> [--out f.json]

Planned start = the passer of the team's first pass attempt; primary = most earlier starts
that season (2+). b is fit on primary-QB team-games 2022-23 only: log(team actual/model) =
a + b log(implied total / the team's usual implied total in its primary starts).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
PERIODS = {"2022-23": (2022, 2023), "2024-25": (2024, 2025)}


def planned_starts(pbp: pd.DataFrame) -> pd.DataFrame:
    """(season, team, week, starter): the passer of each team-game's first dropback."""
    p = pbp[(pbp.season_type == "REG") & (pbp.play_type == "pass") & pbp.passer_player_id.notna()]
    first = p.sort_values("play_id").groupby(["season", "posteam", "week"], as_index=False).first()
    return first.rename(columns={"posteam": "team", "passer_player_id": "starter"})[
        ["season", "team", "week", "starter"]]


def backup_flags(starts: pd.DataFrame) -> pd.DataFrame:
    """Adds `primary` (most starts in the team's EARLIER games that season, 2+) and
    `backup` (starter is not the primary); rows without a primary are dropped."""
    out = []
    for (s, t), g in starts.sort_values("week").groupby(["season", "team"]):
        for _, r in g.iterrows():
            earlier = g[g.week < r.week].starter.value_counts()
            if earlier.empty or earlier.iloc[0] < 2:
                continue
            out.append({**r.to_dict(), "primary": earlier.index[0], "backup": r.starter != earlier.index[0]})
    return pd.DataFrame(out)


def implied_totals(games: pd.DataFrame) -> pd.DataFrame:
    """(season, team, week, implied): (total + own spread) / 2, spread positive = favoured
    (nflverse spread_line is the home side's, positive when home is favoured)."""
    g = games[(games.game_type == "REG") & games.spread_line.notna() & games.total_line.notna()]
    home = g.assign(team=g.home_team, implied=(g.total_line + g.spread_line) / 2)
    away = g.assign(team=g.away_team, implied=(g.total_line - g.spread_line) / 2)
    return pd.concat([home, away])[["season", "team", "week", "implied"]]


def implied_ratio(flags: pd.DataFrame, imp: pd.DataFrame) -> pd.DataFrame:
    """Adds `ratio`: this game's implied total over the team's mean implied total in its
    EARLIER primary-QB starts that season (rows without one are dropped)."""
    d = flags.merge(imp, on=["season", "team", "week"], how="inner").sort_values("week")
    out = []
    for _, g in d.groupby(["season", "team"]):
        for _, r in g.iterrows():
            base = g[(g.week < r.week) & ~g.backup.astype(bool)].implied
            if len(base):
                out.append({**r.to_dict(), "ratio": float(r.implied / base.mean())})
    return pd.DataFrame(out)


def team_residuals(res: pd.DataFrame) -> pd.DataFrame:
    """Per team-game: receivers' summed actual and model receiving yards; the starting
    QB's actual and model passing yards."""
    rec = res[res.mean_yds_model.notna()].groupby(["season", "team", "week"]).agg(
        rec_act=("act_rec_yards", "sum"), rec_mod=("mean_yds_model", "sum"))
    qb = res[res.mean_pass_model.notna()].groupby(["season", "team", "week"]).agg(
        pass_act=("act_pass_yards", "sum"), pass_mod=("mean_pass_model", "sum"))
    return rec.join(qb, how="outer").reset_index()


def fit_b(d: pd.DataFrame, act: str, mod: str):
    """The slope b from log(act/mod) = a + b log(ratio) on primary-QB team-games (equal
    weights). The LEVEL a is then set on the gap's own scale -- sum of actual = sum of
    model x exp(a) x ratio^b over the same games -- because a mean of logs sits below a
    sum-over-sum ratio by about half the noise variance (with real team-game noise, ~5%):
    the pre-registered log intercept made backups look better than expected (found on the
    first run, DISCLOSED in reports/backup_qb_implied_total.md; both numbers reported)."""
    d = d[(d[act] > 0) & (d[mod] > 0) & ~d.backup.astype(bool)]
    X = np.c_[np.ones(len(d)), np.log(d.ratio)]
    (_a_log, b), *_ = np.linalg.lstsq(X, np.log(d[act] / d[mod]), rcond=None)
    a = np.log(d[act].sum() / (d[mod] * d.ratio ** b).sum())
    return float(a), float(b), int(len(d))


def gap(d: pd.DataFrame, act: str, mod: str, a: float, b: float, reps: int, rng):
    """Backup starts: raw gap (sum actual / sum model - 1) and the remaining gap after
    the implied total ((sum actual - sum model x expected) / sum model), with a 95%
    interval resampling team-games."""
    d = d[d.backup.astype(bool) & d[act].notna() & (d[mod] > 0)]
    A, M = d[act].to_numpy(float), d[mod].to_numpy(float)
    E = np.exp(a + b * np.log(d.ratio.to_numpy(float)))
    raw = A.sum() / M.sum() - 1
    rem = (A.sum() - (M * E).sum()) / M.sum()
    idx = rng.integers(0, len(A), size=(reps, len(A)))
    boot = (A[idx].sum(1) - (M * E)[idx].sum(1)) / M[idx].sum(1)
    lo, hi = np.percentile(boot, [2.5, 97.5])
    return {"n": int(len(A)), "raw_gap": float(raw), "remaining_gap": float(rem), "ci": [float(lo), float(hi)],
            "mean_ratio": float(d.ratio.mean())}


def verdict(per: dict) -> str:
    """The pre-registered reading for one market across both periods."""
    big = max(per, key=lambda k: abs(per[k]["raw_gap"]))
    closes = abs(per[big]["remaining_gap"]) <= 0.5 * abs(per[big]["raw_gap"])
    if all(v["ci"][0] <= 0 <= v["ci"][1] for v in per.values()) and closes:
        return "the implied total carries it"
    for v in per.values():
        same_side = np.sign(v["remaining_gap"]) == np.sign(v["raw_gap"])
        if same_side and (v["ci"][1] < 0 or v["ci"][0] > 0):
            return "it does not"
    return "unresolved"


def run(res, starts, games, reps=2000, seed=1):
    flags = backup_flags(starts)
    d = implied_ratio(flags, implied_totals(games)).merge(team_residuals(res), on=["season", "team", "week"])
    rng = np.random.default_rng(seed)
    out = {}
    for label, act, mod in [("receivers' receiving yards", "rec_act", "rec_mod"),
                            ("starting QB passing yards", "pass_act", "pass_mod")]:
        tune = d[d.season.isin(PERIODS["2022-23"])]
        a, b, n_fit = fit_b(tune, act, mod)
        per = {p: gap(d[d.season.isin(ss)], act, mod, a, b, reps, rng) for p, ss in PERIODS.items()}
        out[label] = {"a": a, "b": b, "n_fit": n_fit, "periods": per, "verdict": verdict(per)}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    res = pd.read_pickle(a.results)["results"]
    seasons = sorted(res.season.unique())
    pbp = pd.concat([pd.read_csv(CACHE / f"pbp_{s}.csv.gz", low_memory=False,
                                 usecols=["season", "season_type", "week", "posteam", "play_type", "play_id",
                                          "passer_player_id"]) for s in seasons])
    out = run(res, planned_starts(pbp), pd.read_csv(CACHE / "games.csv"))
    for label, v in out.items():
        print(f"\n{label}: b = {v['b']:+.3f} (a = {v['a']:+.3f}, fit on {v['n_fit']} primary-QB team-games, 2022-23)")
        for p, g in v["periods"].items():
            print(f"  {p}: {g['n']} backup starts, implied ratio {g['mean_ratio']:.3f}, raw gap {100 * g['raw_gap']:+.1f}%,"
                  f" remaining after the implied total {100 * g['remaining_gap']:+.1f}%"
                  f" ({100 * g['ci'][0]:+.1f}, {100 * g['ci'][1]:+.1f})")
        print(f"  verdict: {v['verdict']}")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

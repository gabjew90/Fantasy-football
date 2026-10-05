"""Pre-registered 2026-10-04 (reports/rb_takeover_check.md): does a running back whose
carry share jumped (or collapsed) last week beat (or miss) the model's carry projection
the next week? Same read as reports/role_shift_check.md.

    python props/tools/rb_takeover_check.py <harness --save-results pickle>

Reads the harness's cached play-by-play (NFL_BACKTEST_CACHE, default <tmp>/nflbt).
The board's flag (research.carry_change / carry_flag) uses the same definition:
weeks in which he carried, LAST = the week just played, BASE = at least two earlier."""
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
res = pd.read_pickle(sys.argv[1])["results"]
JUMP = 0.20

rows = []
for S in (2022, 2023, 2024, 2025):
    p = pd.read_csv(CACHE / f"pbp_{S}.csv.gz", low_memory=False,
                    usecols=["season_type", "week", "posteam", "play_type", "qb_kneel", "rusher_player_id"])
    p = p[(p.season_type == "REG") & (p.play_type == "run") & (p.qb_kneel != 1) & p.rusher_player_id.notna()]
    tot = p.groupby(["posteam", "week"]).size().rename("team_car")
    mine = p.groupby(["posteam", "rusher_player_id", "week"]).size().rename("car").reset_index()
    mine = mine.join(tot, on=["posteam", "week"])
    mine["cs"] = mine.car / mine.team_car
    r = res[(res.season == S) & res.rush_pop.astype(bool)][["season", "week", "team", "gsis_id", "game_id",
                                                          "mean_car_model", "act_carries"]]
    for _, x in r.iterrows():
        h = mine[(mine.posteam == x.team) & (mine.rusher_player_id == x.gsis_id) & (mine.week < x.week)]
        if (x.week - 1) not in set(h.week):
            continue                               # LAST must be the week just played
        base = h[h.week < x.week - 1]
        if len(base) < 2:
            continue
        d = float(h[h.week == x.week - 1].cs.iloc[0] - base.cs.mean())
        rows.append(dict(season=S, week=x.week, team=x.team, d=d,
                         resid=float(x.act_carries - x.mean_car_model)))
D = pd.DataFrame(rows)
D["flag"] = np.select([D.d >= JUMP, D.d <= -JUMP], ["takeover", "demotion"], "none")


def diff_ci(d, flag, reps=2000, seed=1):
    k = d.season.astype(str) + "_" + d.team + "_" + d.week.astype(str)
    g = d.assign(k=k, f=(d.flag == flag)).groupby("k")
    keys = np.array(list(g.groups))
    parts = {kk: (x.resid.to_numpy(), x.f.to_numpy()) for kk, x in g}
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        pick = rng.choice(keys, len(keys))
        rr = np.concatenate([parts[kk][0] for kk in pick]); ff = np.concatenate([parts[kk][1] for kk in pick])
        if ff.any() and (~ff).any():
            out.append(rr[ff].mean() - rr[~ff].mean())
    pt = d[d.flag == flag].resid.mean() - d[d.flag != flag].resid.mean()
    return pt, np.percentile(out, 2.5), np.percentile(out, 97.5), int((d.flag == flag).sum())


print("| Period | Flag | Flagged backs | Flagged minus unflagged carries residual (95% CI) |")
print("|---|---|---|---|")
for per, seasons in (("2022-23", (2022, 2023)), ("2024-25", (2024, 2025))):
    d = D[D.season.isin(seasons)]
    for flag in ("takeover", "demotion"):
        pt, lo, hi, n = diff_ci(d, flag)
        print(f"| {per} | {flag} | {n} | {pt:+.2f} carries ({lo:+.2f}, {hi:+.2f}) |")
print(f"rows {len(D)}; flagged {dict(D.flag.value_counts())}")

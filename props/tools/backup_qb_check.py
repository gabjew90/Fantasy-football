"""Pre-registered 2026-10-06 (reports/backup_qb_check.md): when a backup quarterback
starts, does the model over-project his receivers and his passing?

    python props/tools/backup_qb_check.py <harness --save-results pickle>

Reads the harness's cached play-by-play (NFL_BACKTEST_CACHE, default <tmp>/nflbt).
A backup game: the team's attempts leader in that game is not its primary QB -- the
passer who led the team in attempts most often in its earlier games of the season, with
at least two such games. Team-games with no primary yet are left out of both groups."""
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
res = pd.read_pickle(sys.argv[1])["results"]


def backup_games(S):
    """{(team, week): True/False} for team-games with a primary QB; absent otherwise."""
    p = pd.read_csv(CACHE / f"pbp_{S}.csv.gz", low_memory=False,
                    usecols=["season_type", "week", "posteam", "pass_attempt", "sack", "play_type", "passer_player_id"])
    p = p[(p.season_type == "REG") & (p.play_type == "pass") & (p.pass_attempt == 1) & (p.sack != 1)
          & p.passer_player_id.notna()]
    lead = (p.groupby(["posteam", "week", "passer_player_id"]).size().rename("att").reset_index()
            .sort_values("att").groupby(["posteam", "week"]).tail(1))
    out = {}
    for team, g in lead.groupby("posteam"):
        g = g.sort_values("week")
        for _, r in g.iterrows():
            earlier = g[g.week < r.week].passer_player_id.value_counts()
            if earlier.empty or earlier.iloc[0] < 2:
                continue
            out[(team, int(r.week))] = r.passer_player_id != earlier.index[0]
    return out


rows = []
for S in (2022, 2023, 2024, 2025):
    flag = backup_games(S)
    r = res[res.season == S].copy()
    r["backup"] = [flag.get((t, int(w))) for t, w in zip(r.team, r.week)]
    rows.append(r[r.backup.notna()])
D = pd.concat(rows, ignore_index=True)
D["backup"] = D.backup.astype(bool)
D["period"] = np.where(D.season <= 2023, "2022-23", "2024-25")
D["k"] = D.season.astype(str) + "_" + D.team + "_" + D.week.astype(str)


def ratio(d, act, mod):
    d = d[d[mod].notna() & d[act].notna()]
    return float(d[act].sum() / d[mod].sum()) if d[mod].sum() > 0 else np.nan


def diff_ci(d, act, mod, reps=2000, seed=1):
    """(backup ratio - other ratio), 95% interval resampling team-games."""
    d = d[d[mod].notna() & d[act].notna()]
    g = {k: (x[act].sum(), x[mod].sum(), bool(x.backup.iloc[0])) for k, x in d.groupby("k")}
    keys = np.array(list(g))
    A = np.array([g[k][0] for k in keys]); M_ = np.array([g[k][1] for k in keys]); B = np.array([g[k][2] for k in keys])
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(reps):
        i = rng.integers(0, len(keys), len(keys))
        a, m, b = A[i], M_[i], B[i]
        if b.any() and (~b).any():
            out.append(a[b].sum() / m[b].sum() - a[~b].sum() / m[~b].sum())
    pt = A[B].sum() / M_[B].sum() - A[~B].sum() / M_[~B].sum()
    return pt, float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5)), int(B.sum())


print("| Period | Market | Backup team-games | actual / model, backup | actual / model, others | Difference (95% CI) |")
print("|---|---|---|---|---|---|")
for per in ("2022-23", "2024-25"):
    d = D[D.period == per]
    for label, act, mod in [("receiving yards", "act_rec_yards", "mean_yds_model"),
                            ("catches", "act_receptions", "mean_rec_model"),
                            ("QB passing yards", "act_pass_yards", "mean_pass_model")]:
        pt, lo, hi, n = diff_ci(d, act, mod)
        print(f"| {per} | {label} | {n} | {ratio(d[d.backup], act, mod):.3f} | {ratio(d[~d.backup], act, mod):.3f} "
              f"| {pt:+.3f} ({lo:+.3f}, {hi:+.3f}) |")

print("\nDiagnostics (not part of the rule): receiving yards actual / model by slot, all seasons")
print("| Slot | backup | others |")
print("|---|---|---|")
for sl in ("WR1", "WR2", "WR3", "TE1", "RB1", "RB2"):
    d = D[D.slot.astype(str) == sl]
    print(f"| {sl} | {ratio(d[d.backup], 'act_rec_yards', 'mean_yds_model'):.3f} | "
          f"{ratio(d[~d.backup], 'act_rec_yards', 'mean_yds_model'):.3f} |")

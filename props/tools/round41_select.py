"""Round 41 (reports/round41_receiving_roles.md): tight ends' and backs' yards shape, tight ends'
target share. Three registered stages, each on its own role's rows, then the whole-board guards.

    python props/tools/round41_select.py <receivingroles grid pickle> [--out f.json]

Stage A1  catch_shape_mult_te (1, 1.5, 2)    tight ends' receiving yards, conversion log loss
Stage A2  catch_shape_mult_rb (1, 0.75, 0.5) backs' receiving yards, conversion log loss (at A1's pick)
Stage B   te_share_mult (1, 1.03, 1.06)      tight ends' receptions, own-volume log loss (at A1, A2)
Final     the combined setting against shipped on every market and both scores (the guards),
          widths and the Over rate against the engine by role and by implied points.
Selection 2022-24; confirmation 2026 weeks 2-4 (read once).
"""
import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402
import scoreboard as SB  # noqa: E402

KN = ("catch_shape_mult_te", "catch_shape_mult_rb", "te_share_mult")
SHIPPED = {"catch_shape_mult_te": 1.0, "catch_shape_mult_rb": 1.0, "te_share_mult": 1.0}
SELECT, CONFIRM = [2022, 2023, 2024], [2026]


def role_rows(F, role):
    return F[F.slot.astype(str).str.replace(r"\d", "", regex=True) == role]


def stage(grid, frames, fixed, vary, role, market, score):
    idx = [i for i, g in enumerate(grid) if all(g[k] == v for k, v in fixed.items())]
    sub = [grid[i] for i in idx]
    ship_local = next(j for j, g in enumerate(sub) if g[vary] == SHIPPED[vary])
    fr = [role_rows(frames[i], role) for i in idx]
    res = GS.run(sub, fr, ship_local, market, score, SELECT, CONFIRM, (vary,), required=(market,), reps=10_000)
    res["global_index"] = idx[res["pick"]]
    return res


def width_by_role(F, seasons):
    out = {}
    for mk, col in (("receptions", "pit_rec_c"), ("receiving yards", "pit_yds_c")):
        f = SB.market_frame(F[F.season.isin(seasons)], mk)
        grp = f.slot.astype(str).str.replace(r"\d", "", regex=True)
        out[mk] = {r: round(100 * float(((z[col] < .1) | (z[col] > .9)).mean()), 1)
                   for r, z in f.groupby(grp) if len(z) >= 150}
    return out


def gap_by(F, seasons, keyf):
    out = {}
    for mk in ("receptions", "receiving yards"):
        f = SB.market_frame(F[F.season.isin(seasons)], mk)
        k = keyf(f)
        out[mk] = {str(r): (int(len(z)), round(100 * float(z.y.mean() - z.pu.mean()), 1))
                   for r, z in f.groupby(k, observed=True) if len(z) >= 50}
    return out


def implied_key():
    g = pd.read_csv(Path(tempfile.gettempdir()) / "nflbt" / "games.csv")
    g = g[g.game_type == "REG"]
    imp = {}
    for r in g.itertuples():
        if pd.notna(r.spread_line) and pd.notna(r.total_line):
            imp[(r.season, r.home_team, r.week)] = (r.total_line + r.spread_line) / 2
            imp[(r.season, r.away_team, r.week)] = (r.total_line - r.spread_line) / 2
    return lambda f: pd.cut(pd.Series([imp.get((s, t, w)) for s, t, w in zip(f.season, f.team, f.week)],
                                      index=f.index), [0, 18, 21, 24, 27, 99],
                            labels=["18 or less", "18-21", "21-24", "24-27", "27+"])


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = pd.read_pickle(a.grid)
    grid, frames = d["grid"], d["frames"]
    for g in grid:
        for k in KN:
            g[k] = 1.0 if g.get(k) is None else float(g[k])
    a1 = stage(grid, frames, {"catch_shape_mult_rb": 1.0, "te_share_mult": 1.0}, "catch_shape_mult_te", "TE",
               "receiving yards", "c")
    te = grid[a1["global_index"]]["catch_shape_mult_te"] if a1.get("ship") else 1.0
    a2 = stage(grid, frames, {"catch_shape_mult_te": te, "te_share_mult": 1.0}, "catch_shape_mult_rb", "RB",
               "receiving yards", "c")
    rb = grid[a2["global_index"]]["catch_shape_mult_rb"] if a2.get("ship") else 1.0
    b = stage(grid, frames, {"catch_shape_mult_te": te, "catch_shape_mult_rb": rb}, "te_share_mult", "TE",
              "receptions", "u")
    ts = grid[b["global_index"]]["te_share_mult"] if b.get("ship") else 1.0
    final = {"catch_shape_mult_te": te, "catch_shape_mult_rb": rb, "te_share_mult": ts}
    fi = next(i for i, g in enumerate(grid) if all(g[k] == final[k] for k in KN))
    si = next(i for i, g in enumerate(grid) if all(g[k] == SHIPPED[k] for k in KN))
    out = {"stage_A1_te_shape": a1, "stage_A2_rb_shape": a2, "stage_B_te_share": b, "final": final}
    if fi != si:
        sel = [frames[si][frames[si].season.isin(SELECT)], frames[fi][frames[fi].season.isin(SELECT)]]
        c = SB.compare(sel[1], sel[0], "game", reps=10_000)
        out["final_guards"] = {s: SB.guard_verdict(c, None, s, floor=-0.002) for s in ("logloss_c", "logloss_u")}
        out["final_rel"] = {mk: {s: c[mk][s]["relative"] for s in ("logloss_c", "logloss_u") if s in c[mk]}
                            for mk in c if isinstance(c[mk], dict)}
    ik = implied_key()
    role = lambda f: f.slot.astype(str).str.replace(r"\d", "", regex=True)
    for lab, i in (("shipped", si), ("final", fi)):
        out[f"width_{lab}"] = {"2022-24": width_by_role(frames[i], SELECT), "2026": width_by_role(frames[i], CONFIRM)}
        out[f"gap_role_{lab}"] = {"2022-24": gap_by(frames[i], SELECT, role), "2026": gap_by(frames[i], CONFIRM, role)}
        out[f"gap_implied_{lab}"] = gap_by(frames[i], SELECT, ik)
    print(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
                               + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

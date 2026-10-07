"""Round 40 (reports/round40_receiving_level.md): receivers' yards a catch, then passing's level.

    python props/tools/round40_select.py <receivinglevel grid pickle> [--out f.json]

Stage A  rec_ypc_mult (1, 1.02, 1.04, 1.06) at pass_scale 1.04 (shipped): receiving-yards
         CONVERSION log loss (actual targets in), every receiver
Stage B  pass_scale (1, 1.02, 1.04) at A's result: QB passing OWN-VOLUME log loss
Final    the combined setting against shipped: every market and both scores (floor -0.2%),
         receiving yards' and QB passing's Over-minus-engine by implied points and by role.
Selection 2022-24; confirmation 2026 weeks 2-4 (read once).
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402
import round41_select as R41  # noqa: E402
import scoreboard as SB  # noqa: E402

KN = ("rec_ypc_mult", "pass_scale")
SHIPPED = {"rec_ypc_mult": 1.0, "pass_scale": 1.04}
SELECT, CONFIRM = R41.SELECT, R41.CONFIRM


def stage(grid, frames, fixed, vary, market, score):
    idx = [i for i, g in enumerate(grid) if all(g[k] == v for k, v in fixed.items())]
    sub = [grid[i] for i in idx]
    ship_local = next(j for j, g in enumerate(sub) if g[vary] == SHIPPED[vary])
    res = GS.run(sub, [frames[i] for i in idx], ship_local, market, score, SELECT, CONFIRM, (vary,),
                 required=(market,), reps=10_000)
    res["global_index"] = idx[res["pick"]]
    return res


def gap(F, seasons, market, keyf):
    f = SB.market_frame(F[F.season.isin(seasons)], market)
    return {str(r): (int(len(z)), round(100 * float(z.y.mean() - z.pu.mean()), 1))
            for r, z in f.groupby(keyf(f), observed=True) if len(z) >= 50}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = pd.read_pickle(a.grid)
    grid, frames = d["grid"], d["frames"]
    for g in grid:
        g["rec_ypc_mult"] = 1.0 if g.get("rec_ypc_mult") is None else float(g["rec_ypc_mult"])
        g["pass_scale"] = 1.0 if g.get("pass_scale") is None else float(g["pass_scale"])
    sa = stage(grid, frames, {"pass_scale": 1.04}, "rec_ypc_mult", "receiving yards", "c")
    y = grid[sa["global_index"]]["rec_ypc_mult"] if sa.get("ship") else 1.0
    sb = stage(grid, frames, {"rec_ypc_mult": y}, "pass_scale", "QB passing yards", "u")
    p = grid[sb["global_index"]]["pass_scale"] if sb.get("ship") else 1.04
    final = {"rec_ypc_mult": y, "pass_scale": p}
    fi = next(i for i, g in enumerate(grid) if all(g[k] == final[k] for k in KN))
    si = next(i for i, g in enumerate(grid) if all(g[k] == SHIPPED[k] for k in KN))
    out = {"stage_A_rec_ypc": sa, "stage_B_pass_scale": sb, "final": final}
    if fi != si:
        sel = [frames[si][frames[si].season.isin(SELECT)], frames[fi][frames[fi].season.isin(SELECT)]]
        c = SB.compare(sel[1], sel[0], "game", reps=10_000)
        out["final_guards"] = {s: SB.guard_verdict(c, None, s, floor=-0.002) for s in ("logloss_c", "logloss_u")}
    ik = R41.implied_key()
    role = lambda f: f.slot.astype(str).str.replace(r"\d", "", regex=True)
    allrows = lambda f: pd.Series("all", index=f.index)
    for lab, i in (("shipped", si), ("final", fi)):
        for mk in ("receiving yards", "receptions", "QB passing yards"):
            for sl, seas in (("2022-24", SELECT), ("2026", CONFIRM)):
                out[f"gap_{lab}_{mk}_{sl}"] = {"all": gap(frames[i], seas, mk, allrows),
                                               "implied": gap(frames[i], seas, mk, ik),
                                               **({"role": gap(frames[i], seas, mk, role)} if mk != "QB passing yards" else {})}
    print(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
                               + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

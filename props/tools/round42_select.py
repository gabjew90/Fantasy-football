"""Round 42 (reports/round42_target_handoff.md): how much of an absent key player's TARGET share
the Out rule hands on, set separately for the first game out and a continuing absence.

The live rule (score_game.OUT_RULE["ts"] = (x 0.2, y 0.25)) hands on y of the absent player's
share every week. The second expert audit (DECISIONS #198) measured same-position teammates
at 1.08 x projection the first game out and 1.04 in a continuing absence: about right first,
about double later. Each teammate-game is predicted the way round 35 did it (his season-to-date
share plus the handoff of the absent player's raw share last season -- the live V0) and scored
by squared error against his actual share.

    python props/tools/round42_select.py [--out f.json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import out_rule_test as ORT  # noqa: E402

Y_FIRST = (0.25, 0.35, 0.5)          # shipped 0.25
Y_CONT = (0.25, 0.15, 0.10, 0.05)    # shipped 0.25
SHIPPED = (0.25, 0.25)
SELECT, CONFIRM = [2022, 2023, 2024], [2026]
TIE = 0.005                          # within 0.5% of the best loss: the setting closest to shipped


def collapse_y(d: pd.DataFrame, x: float, y_first: float, y_cont: float) -> pd.DataFrame:
    """ORT.collapse with V0's share and y by absence age: one row per (game, teammate)."""
    add = np.zeros(len(d))
    for _, idx in d.groupby(["season", "game_id", "absent"]).indices.items():
        g = d.iloc[idx]
        y = y_first if bool(g["first_out"].iloc[0]) else y_cont
        add[idx] = ORT.handoff(g["cur"].to_numpy(float), g["same"].to_numpy(bool), y * g["v0"].iloc[0], x)
    out = (d.assign(add=add)
             .groupby(["season", "team", "game_id", "player_id"], sort=True)
             .agg(week=("week", "first"), cur=("cur", "first"), actual=("actual", "first"),
                  add=("add", "sum"), first_out=("first_out", "all"), same=("same", "any"))
             .reset_index())
    out["pred"] = out["cur"] + out["add"]
    out["cluster"] = out["season"].astype(str) + "_" + out["team"].astype(str)
    return out


def loss(d, x, s) -> tuple[pd.DataFrame, np.ndarray]:
    f = collapse_y(d, x, *s)
    return f, (f["pred"] - f["actual"]).to_numpy() ** 2


def distance(s) -> int:
    return abs(Y_FIRST.index(s[0]) - Y_FIRST.index(SHIPPED[0])) + abs(Y_CONT.index(s[1]) - Y_CONT.index(SHIPPED[1]))


def pick(d, x) -> tuple:
    grid = [(a, b) for a in Y_FIRST for b in Y_CONT]
    m = {s: float(loss(d, x, s)[1].mean()) for s in grid}
    best = min(m.values())
    near = [s for s in grid if m[s] - best <= TIE * m[SHIPPED]]
    return min(near, key=lambda s: (distance(s), m[s])), m


def ratio_table(d, x, s) -> dict:
    """Same-position teammates: actual / predicted share, first game out and continuing."""
    f = collapse_y(d, x, *s)
    out = {}
    for nm, msk in (("first game out", f.first_out), ("continuing", ~f.first_out)):
        z = f[msk & f.same]
        out[nm] = {"n": int(len(z)), "actual_over_pred": float(z.actual.sum() / z.pred.sum()) if len(z) else None,
                   "actual_over_cur": float(z.actual.sum() / z.cur.sum()) if len(z) else None}
    return out


def main(argv=None):
    import score_game as SG
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    x, y0 = SG.OUT_RULE["ts"]
    assert (y0, y0) == SHIPPED, f"OUT_RULE ts y is {y0}, the grid assumes 0.25"
    d = ORT.build(SELECT + CONFIRM, "targets")         # 2025 is not read: round 35 used it
    sel, con = d[d.season.isin(SELECT)], d[d.season.isin(CONFIRM)]
    p, m = pick(sel, x)
    res = {"x": x, "pick": p, "loss_select": {f"{k[0]}/{k[1]}": v for k, v in m.items()},
           "ratios_shipped_select": ratio_table(sel, x, SHIPPED), "ratios_pick_select": ratio_table(sel, x, p),
           "events_select": int(sel.event.nunique()), "events_confirm": int(con.event.nunique())}
    if p != SHIPPED:
        fs, Lp = loss(sel, x, p)
        _, L0 = loss(sel, x, SHIPPED)
        res["gain_select"] = ORT.diff_ci(fs, Lp, L0)
        parts = {}
        for nm, msk in (("first game out", fs.first_out.to_numpy()), ("continuing", ~fs.first_out.to_numpy())):
            worse = float((Lp[msk] - L0[msk]).mean())
            parts[nm] = {"n": int(msk.sum()), "worse_by": worse, "ok": worse <= 0.05 * float(L0[msk].mean()),
                         "gain": ORT.diff_ci(fs[msk], Lp[msk], L0[msk])}
        res["parts"] = parts
        fc, Lpc = loss(con, x, p)
        _, L0c = loss(con, x, SHIPPED)
        res["gain_confirm"] = ORT.diff_ci(fc, Lpc, L0c) if len(fc) else None
        res["ratios_pick_confirm"] = ratio_table(con, x, p)
        oof = []
        for s_ in SELECT:
            pk, _ = pick(sel[sel.season != s_], x)
            te = sel[sel.season == s_]
            oof.append({"held_out": s_, "pick": pk,
                        "gain": float((loss(te, x, SHIPPED)[1] - loss(te, x, pk)[1]).mean())})
        res["loso"] = oof
        g = res["gain_select"]
        res["ship"] = bool(g[1] > 0 and all(v["ok"] for v in parts.values())
                           and res["gain_confirm"] is not None and res["gain_confirm"][0] >= 0)
    else:
        res["ship"] = False
    print(json.dumps(res, indent=1, default=float))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

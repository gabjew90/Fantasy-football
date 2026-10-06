"""Round 30's selection, exactly as pre-registered (reports/round30_conversion.md).

    python props/tools/round30_select.py <backtest --tune-width --tune-grid conversion --conditional --save-results pickle>

1. eff_sd_rush on the rushing-yards conversion log loss (others shipped);
2. catch_conc on the receptions conversion log loss (shape 1);
3. catch_shape_mult on the receiving-yards conversion log loss, catch_conc at step 2's pick.
Ties within 0.0005 keep the shipped value; a pick that moves the Over chance by less than
1.0 point on average stays shipped. Then each changed knob's detectability vs shipped (95%;
99% for eff_sd_rush, a running-game candidate) and the guards on the other bet markets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoreboard as SB  # noqa: E402

BASE = {"eff_sd_rush": 0.3, "catch_conc": None, "catch_shape_mult": None}
TIE, MIN_MOVE, GUARD = 0.0005, 1.0, -0.005


def pick(grid, frames, knob, market, fixed):
    """Among rows where every other round-30 knob equals `fixed`, the value with the lowest
    conversion log loss on `market`; ties and sub-minimum moves keep the shipped value."""
    base_i = next(i for i, g in enumerate(grid) if all(g.get(k) == v for k, v in {**fixed, knob: BASE[knob]}.items()))
    cands = [(i, g[knob]) for i, g in enumerate(grid)
             if all(g.get(k) == v for k, v in fixed.items() if k != knob)]
    ll = {v: SB.single(frames[i])[market]["logloss_c"] for i, v in cands}
    best_v = min(ll, key=ll.get)
    shipped_ll = ll[BASE[knob]] if BASE[knob] in ll else ll[grid[base_i][knob]]
    table = [{"value": v, "logloss_c": ll[v]} for _, v in cands]
    if best_v == BASE[knob] or shipped_ll - ll[best_v] <= TIE:
        return BASE[knob], base_i, table, None
    best_i = next(i for i, v in cands if v == best_v)
    move = SB.compare(frames[best_i], frames[base_i], "game", reps=500)[market]["move_points_c"]
    if move < MIN_MOVE:
        return BASE[knob], base_i, table, move
    return best_v, best_i, table, move


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    saved = pd.read_pickle(argv[0])
    grid = [{k: g.get(k) for k in BASE} for g in saved["grid"]]
    frames = saved["frames"]
    out = {}
    v1, i1, t1, m1 = pick(grid, frames, "eff_sd_rush", "rushing yards", {"catch_conc": None, "catch_shape_mult": None})
    v2, i2, t2, m2 = pick(grid, frames, "catch_conc", "receptions", {"eff_sd_rush": 0.3, "catch_shape_mult": None})
    v3, i3, t3, m3 = pick(grid, frames, "catch_shape_mult", "receiving yards", {"eff_sd_rush": 0.3, "catch_conc": v2})
    out["picks"] = {"eff_sd_rush": v1, "catch_conc": v2, "catch_shape_mult": v3}
    out["tables"] = {"eff_sd_rush": t1, "catch_conc": t2, "catch_shape_mult": t3}
    out["moves"] = {"eff_sd_rush": m1, "catch_conc": m2, "catch_shape_mult": m3}
    base_i = grid.index(BASE)
    # each knob against the row that differs from it in that knob alone
    ref = {"eff_sd_rush": base_i, "catch_conc": base_i,
           "catch_shape_mult": grid.index({**BASE, "catch_conc": v2})}
    checks = {}
    for knob, i, market, level in (("eff_sd_rush", i1, "rushing yards", 0.99),
                                    ("catch_conc", i2, "receptions", 0.95),
                                    ("catch_shape_mult", i3, "receiving yards", 0.95)):
        if out["picks"][knob] == BASE[knob]:
            continue
        c = SB.compare(frames[i], frames[ref[knob]], "game", level=level)
        target = c[market]["logloss_c"]
        guards = {mk: v["logloss_c"]["relative"] for mk, v in c.items() if mk != market}
        checks[knob] = {"market": market, "level": level, "gain": target["gain"], "ci": target["ci"],
                        "detectable": target["ci"][0] > 0, "move_points": c[market]["move_points_c"],
                        "guards_relative": guards,
                        "guards_ok": all(g is None or g >= GUARD for g in guards.values())}
    out["checks"] = checks
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

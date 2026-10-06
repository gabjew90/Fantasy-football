"""Round 31's selection, exactly as pre-registered (reports/round31_target_spread.md).

    python props/tools/round31_select.py <backtest --tune-width --tune-grid targetspread --conditional --save-results pickle>

Among settings whose real / model spread ratio stays at or below 1.00 in the 3-5, 5-8 and
8-11 bands (stable-role stretches), the smallest largest gap to 1; ties within 0.01 go to
the setting closer to shipped. Then the guard: own-volume log loss for receptions and
receiving yards against shipped (team-season clustered), no worse than -0.5%.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scoreboard as SB  # noqa: E402

BANDS = [(3, 5), (5, 8), (8, 11)]
SHIPPED = {"share_conc_targets": 40.0, "team_r_mult": None}
TIE, GUARD = 0.01, -0.005


def distance(cfg):
    """How far a setting is from shipped: knobs moved, then the size of the moves."""
    moved = [k for k in SHIPPED if cfg.get(k) != SHIPPED[k]]
    size = abs((cfg["share_conc_targets"] or 40) / 40 - 1) + abs((cfg["team_r_mult"] or 1) - 1)
    return (len(moved), size)


def choose(rows):
    """rows: [{cfg, ratios}] -> the chosen row by the registered rule (or None)."""
    ok = [r for r in rows if all(x <= 1.0 for x in r["ratios"])]
    if not ok:
        return None
    best = min(max(abs(x - 1) for x in r["ratios"]) for r in ok)
    tied = [r for r in ok if max(abs(x - 1) for x in r["ratios"]) <= best + TIE]
    return min(tied, key=lambda r: distance(r["cfg"]))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    saved = pd.read_pickle(argv[0])
    grid = [{k: g.get(k) for k in SHIPPED} for g in saved["grid"]]
    frames = saved["frames"]
    opening = SB.opening_starters(sorted(frames[0].season.unique()))
    rows = []
    for cfg, R in zip(grid, frames):
        tab = SB.spread_table(SB.stable_stretches(R, "mean_tgt", "act_targets", "sd_tgt", opening=opening), BANDS)
        rows.append({"cfg": cfg, "ratios": [b["ratio"] for b in tab], "bands": tab})
    pick = choose(rows)
    out = {"rows": [{"cfg": r["cfg"], "ratios": [round(x, 3) for x in r["ratios"]]} for r in rows],
           "pick": pick["cfg"] if pick else None}
    if pick and pick["cfg"] != SHIPPED:
        i, b = grid.index(pick["cfg"]), grid.index(SHIPPED)
        c = SB.compare(frames[i], frames[b], "team-season")
        out["guard"] = {mk: {"own_volume_gain": c[mk]["logloss_u"]["gain"], "ci": c[mk]["logloss_u"]["ci"],
                             "relative": c[mk]["logloss_u"]["relative"], "move_points_u": c[mk]["move_points_u"]}
                        for mk in ("receptions", "receiving yards") if mk in c}
        out["guard_ok"] = all(v["relative"] >= GUARD for v in out["guard"].values())
    print(json.dumps(out, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

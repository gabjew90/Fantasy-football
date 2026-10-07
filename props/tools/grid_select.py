"""A registered round's selection and ship test on a saved grid (rounds 34 and 36 onward).

The scoreboard's rules (reports/scoreboard.md and its amendments), computed in one place:
  1. pick on the SELECTION seasons, among the eligible settings: the lowest mean log loss for
     the round's market and score on the shipped setting's cohort, ties within `tie` to the
     setting closest to shipped, a pick moving the Over chance under `min_move` points stays
     shipped (props/tools/loso_select.pick);
  2. detectable there: the gain's interval above zero at `level` (game-clustered, 10,000
     resamples), log loss and Brier agreeing in sign in the 15-85% decision zone;
  3. guards complete or BLOCKED (scoreboard.guard_verdict), on conversion and own volume;
  4. confirmed once on the CONFIRMATION seasons: the gain not negative (and, with
     confirm_zone, the zone signs agreeing);
  5. the rule's leave-one-season-out gain over the selection seasons, beside the in-sample one.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import loso_select as LS  # noqa: E402
import scoreboard as SB  # noqa: E402


def spread_eligible(frames, seasons, opening=None, bands=SB.TGT_BANDS[:3]) -> list[bool]:
    """Per setting: the target spread at or below the real upper bound (real / model <= 1.00)
    in every band, role-only stable stretches on the given seasons."""
    out = []
    for R in frames:
        R = R[R.season.isin(seasons)]
        tab = SB.spread_table(SB.stable_stretches(R, "mean_tgt", "act_targets", "sd_tgt", opening=opening, by="role"),
                              bands)
        out.append(bool(tab) and all(b["ratio"] <= 1.0 for b in tab))
    return out


def knob_distance(grid, shipped_i, knobs) -> dict:
    """Ties go to the setting closest to shipped: the sum over knobs of how many grid steps a
    setting's value sits from the shipped one (None counts as its own step)."""
    levels = {k: sorted({g.get(k) for g in grid}, key=lambda v: (v is not None, v if v is not None else 0))
              for k in knobs}
    pos = lambda i, k: levels[k].index(grid[i].get(k))
    return {i: sum(abs(pos(i, k) - pos(shipped_i, k)) for k in knobs) for i in range(len(grid))}


def outside80(R, col) -> float | None:
    x = R[col].dropna() if col in R else pd.Series(dtype=float)
    return float(((x < 0.1) | (x > 0.9)).mean()) if len(x) else None


def run(grid, frames, shipped_i, market, score, select, confirm, knobs, eligible=None, level=0.95,
        tie=0.0005, min_move=1.0, confirm_zone=True, required=tuple(SB.MARKETS), reps=10_000,
        width_col=None) -> dict:
    sel = [F[F.season.isin(select)] for F in frames]
    con = [F[F.season.isin(confirm)] for F in frames]
    cands = [i for i in range(len(grid)) if eligible is None or eligible[i]]
    if shipped_i not in cands:
        cands = [shipped_i] + cands               # shipped is always a candidate (staying put)
    dist = knob_distance(grid, shipped_i, knobs)
    pick = LS.pick(sel, cands, shipped_i, market, score, tie=tie, dist=dist, min_move=min_move)
    out = {"pick": pick, "pick_setting": grid[pick], "candidates": cands,
           "loss_select": {i: LS.mean_score(sel[i], market, score,
                                            SB.market_frame(sel[shipped_i], market)[SB.KEYS]) for i in cands}}
    if pick == shipped_i:
        out.update(ship=False, why="the shipped setting is kept (best, within the tie, or a move under the minimum)")
        return out
    c = SB.compare(sel[pick], sel[shipped_i], "game", level=level, reps=reps)
    m = c[market]
    zone = m.get(f"zone_{score}", {})
    detect = m[f"logloss_{score}"]["ci"][0] > 0 and bool(zone.get("agree")) and zone.get("logloss", 0) > 0
    # the score under test skips its own market; the other score guards every market, the
    # round's own included (round 34: receptions conversion is a guard of an own-volume pick)
    guards = {s: SB.guard_verdict(c, market if s == f"logloss_{score}" else None, s, required=required)
              for s in ("logloss_c", "logloss_u")}
    cc = SB.compare(con[pick], con[shipped_i], "game", level=0.95, reps=reps)[market]
    czone = cc.get(f"zone_{score}", {})
    confirmed = cc[f"logloss_{score}"]["gain"] >= 0 and (not confirm_zone or bool(czone.get("agree")))
    lo = LS.loso(sel, cands, shipped_i, market, score, reps=2000, tie=tie, dist=dist, min_move=min_move)
    out.update(select_gain=m[f"logloss_{score}"], move_points=m[f"move_points_{score}"], zone=zone,
               guards=guards, confirm_gain=cc[f"logloss_{score}"], confirm_zone=czone,
               loso={"oof_gain": lo["oof_gain"], "oof_ci": lo.get("oof_ci"), "folds": lo["folds"]},
               detectable=bool(detect), confirmed=bool(confirmed),
               ship=bool(detect and all(g["status"] == "pass" for g in guards.values()) and confirmed))
    if width_col:
        out["width_select"] = {"shipped": outside80(sel[shipped_i], width_col), "pick": outside80(sel[pick], width_col)}
    return out


def main(argv=None, market=None, score=None, knobs=None, shipped=None, spread=False, width_col=None, title="",
         confirm_zone=True):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("grid")
    ap.add_argument("--select", default="2022,2023,2024")
    ap.add_argument("--confirm", default="2025")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    d = pd.read_pickle(a.grid)
    grid, frames = d["grid"], d["frames"]
    shipped_i = next(i for i, g in enumerate(grid) if all(g.get(k) == v for k, v in shipped.items()))
    sel = [int(x) for x in a.select.split(",")]
    eligible = None
    if spread:
        eligible = spread_eligible(frames, sel, SB.opening_starters(sel))
    res = run(grid, frames, shipped_i, market, score, sel, [int(x) for x in a.confirm.split(",")], knobs,
              eligible=eligible, width_col=width_col, confirm_zone=confirm_zone)
    res["eligible"] = eligible
    print(title)
    print(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)))
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
                               + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(0)

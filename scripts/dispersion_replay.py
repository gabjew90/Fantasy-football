"""The late-round dispersion objective's replay (plan 2026-09-02 A3).

Both archived 2026 drafts, every slot, the production board, flag off vs
on (the season_replay class-attribute pattern, class default restored).
Graded on projected points now and on ACTUAL 2026 points when
--actuals <rows csv> (the forward snapshot, scored in January) is given;
pick churn by round is printed as a diagnostic. Exits 0 with a plain
message while the board carries no two-source spread (combine: first),
because then the flag is inert by construction.

    venv\\Scripts\\python.exe scripts\\dispersion_replay.py --league keefamania
    venv\\Scripts\\python.exe scripts\\dispersion_replay.py --league omnibeta --actuals reports/forward_2026.omnibeta.rows.csv
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import engine_parity as EP  # noqa: E402
import draftkit.tracker as T  # noqa: E402
from slot_replay import lineup_points, replay  # noqa: E402
from draftkit.config import Config  # noqa: E402

DRAFTS = {"keefamania": ("1396184666897145856", "tiers.keefamania.csv"),
          "omnibeta": ("1395566812157984768", "tiers.csv")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, choices=list(DRAFTS))
    ap.add_argument("--actuals", default=None, help="rows csv with sleeper_id/name and actual (January)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    draft_id, board_file = DRAFTS[a.league]
    cfg = Config.load(league=a.league)
    teams, rounds_cfg, slots = EP.league_shape(cfg)
    board = EP.load_board(str(ROOT / board_file))
    with_spread = sum(1 for p in board if p.get("proj_sd") and (p.get("n_sources") or 0) >= 2)
    if with_spread == 0:
        print(f"{a.league}: no dispersion on this board (0 players with a spread from >= 2 sources); "
              "the flag is inert until combine: mean is on. Nothing to replay.")
        return 0
    log = [json.loads(x) for x in (ROOT / "data" / "logs" / f"draft_{draft_id}.jsonl").read_text(encoding="utf-8").splitlines()
           if '"type": "pick"' in x]
    log.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in log)
    key, actual = "proj_pts", None
    if a.actuals:
        import polars as pl
        rows = pl.read_csv(a.actuals, infer_schema_length=10000)
        actual = {r["name"]: float(r["actual"] or 0.0) for r in rows.select("name", "actual").iter_rows(named=True)}
        key = "actual"
    default = T.Tracker.late_round_dispersion
    per_slot, churn = [], {}
    try:
        for s in range(1, teams + 1):
            rosters = {}
            for flag in (False, True):
                T.Tracker.late_round_dispersion = flag
                rosters[flag] = replay(board, log, s, teams, rounds, True, slots=slots)
            T.Tracker.late_round_dispersion = default
            graded = {}
            for flag, chosen in rosters.items():
                pts = [dict(p, actual=actual.get(p["name"], 0.0)) for p in chosen] if actual else chosen
                graded[flag] = lineup_points(pts, slots=slots, key=key)
            per_slot.append((s, graded[False], graded[True]))
            for i, (po, pn) in enumerate(zip(rosters[False], rosters[True])):
                if po["name"] != pn["name"]:
                    churn[i + 1] = churn.get(i + 1, 0) + 1
            print(f"slot {s:>2}: off {graded[False]:.0f}  on {graded[True]:.0f}  delta {graded[True] - graded[False]:+.0f}")
    finally:
        T.Tracker.late_round_dispersion = default
    d = [on - off for _s, off, on in per_slot]
    L = [f"# Dispersion replay -- {a.league}, draft {draft_id}, ruler {key}", "",
         f"{with_spread} board players carry a >= 2-source spread. Mean delta {st.mean(d):+.1f}/slot "
         f"({100 * st.mean(d) / st.mean(off for _s, off, _on in per_slot):+.2f}%), better {sum(x > 0 for x in d)}, "
         f"worse {sum(x < 0 for x in d)}, tied {sum(x == 0 for x in d)}.", "",
         "| slot | off | on | delta |", "|---|---|---|---|"]
    L += [f"| {s} | {off:.0f} | {on:.0f} | {on - off:+.0f} |" for s, off, on in per_slot]
    L += ["", "Picks changed by pick index (our picks, 1 = our first): " + ", ".join(f"{k}: {v}" for k, v in sorted(churn.items())) or "none", ""]
    out = Path(a.out) if a.out else ROOT / "reports" / f"dispersion_replay.{a.league}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

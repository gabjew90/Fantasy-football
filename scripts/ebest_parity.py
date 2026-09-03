"""Plan B2 measurement: joint vs carry expected-best, on the parity states.

The Monte Carlo loop's e_best_next is the JOINT expectation of the best
value still alive (exact under sampling without replacement, but not
reproducible from a per-player survival vector). The carry formula
(urgency.expected_best) assumes independent survivals and IS reproducible
from the displayed vector -- it is what the JS mirror computes. Before one
becomes the definition, measure the gap on the same random mid-draft states
engine_parity uses, both leagues:

  * per market: |urgency_joint - urgency_carry| (mean, max) at the same
    survival_shrink, and how often the top-1 recommendation would change if
    urgency were taken from the carry number instead.

Pre-registered (plan B2): carry is adopted as the definition if the top-1
pick is unchanged on >= 38/40 states per league and max |delta urgency| < 2
points; otherwise the joint expectation stays the truth and the JS formula
is documented as the client-side approximation with its measured tolerance.

    venv\\Scripts\\python.exe scripts\\ebest_parity.py --states 40 --seed 7
"""

from __future__ import annotations

import argparse
import random
import statistics as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import engine_parity as EP  # noqa: E402
from draftkit import snake  # noqa: E402
from draftkit.config import Config  # noqa: E402

BOARDS = {"keefamania": "tiers.keefamania.csv", "omnibeta": "tiers.csv"}


def top1_under(t, report_key: str):
    """The engine's top recommendation when urgency is read from
    report[market][report_key] instead of 'e_best_next'. Done by swapping the
    cached report's e_best_next/urgency, then asking recommendations()."""
    rep = t.urgency_report()
    if not rep:
        return None, {}
    swapped = {}
    for m, u in rep.items():
        e = u.get(report_key, u["e_best_next"])
        swapped[m] = dict(u, e_best_next=e, urgency=u["best_now"] - e)
    t._urgency_cache = (t._urgency_cache[0], swapped)
    recs = t.recommendations(top_n=1)
    name = f"{recs[0][2]['name']}|{recs[0][2]['pos']}" if recs else None
    t._urgency_cache = (t._urgency_cache[0], rep)     # restore
    return name, {m: (u["best_now"] - u["e_best_next_joint"], u["best_now"] - u["e_best_next_carry"])
                  for m, u in rep.items() if "e_best_next_carry" in u}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--states", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--sims", type=int, default=1000)
    ap.add_argument("--out", default=str(ROOT / "reports" / "ebest_parity.md"))
    a = ap.parse_args()
    L = ["# Expected-best estimators: joint vs carry (plan B2 measurement)", "",
         f"{a.states} random mid-draft states per league (engine_parity's generator, seed {a.seed}), "
         f"sims {a.sims}, production knobs from each league's config. Per market: urgency from the joint "
         "(Monte Carlo) expectation vs the carry (independence) formula over the calibrated survival vector.", ""]
    summary = {}
    for league, board_file in BOARDS.items():
        cfg = Config.load(league=league)
        teams, rounds, slots = EP.league_shape(cfg)
        board = EP.load_board(str(ROOT / board_file))
        rng = random.Random(a.seed)
        deltas, agree, n = [], 0, 0
        worst = []
        for k in range(a.states):
            my_slot = rng.randint(1, teams)
            mine = snake.slot_pick_numbers(my_slot, teams, rounds)
            cur = mine[rng.randint(0, rounds - 3)]
            picks, pool = [], list(board)
            for pk in range(1, cur):
                _, sl = snake.pick_to_round_slot(pk, teams)
                idx = min(len(pool) - 1, max(0, int(rng.gauss(0, 4))))
                p = pool.pop(idx)
                picks.append({"pick_no": pk, "player_id": p["sleeper_id"], "draft_slot": sl,
                              "round": (pk - 1) // teams + 1})
            t = EP.make_tracker(board, picks, my_slot, slots=slots, teams=teams, rounds=rounds,
                                cfg=cfg, overrides={"sims": a.sims})
            try:
                joint_top, _ = top1_under(t, "e_best_next_joint")
                carry_top, urg = top1_under(t, "e_best_next_carry")
            except Exception as e:  # noqa: BLE001
                L.append(f"- {league} state {k}: engine raised {e!r}")
                continue
            n += 1
            agree += int(joint_top == carry_top)
            for m, (uj, uc) in urg.items():
                deltas.append(abs(uj - uc))
                worst.append((abs(uj - uc), league, k, m, uj, uc))
            if joint_top != carry_top:
                L.append(f"- {league} state {k} (slot {my_slot}, pick {cur}): joint -> {joint_top}, carry -> {carry_top}")
        worst.sort(reverse=True)
        summary[league] = {"n": n, "agree": agree, "mean": st.mean(deltas) if deltas else float("nan"),
                           "max": max(deltas) if deltas else float("nan"), "worst": worst[:5]}
    L += ["", "| league | states | top-1 unchanged | mean abs delta urgency | max abs delta | bar (>=38/40, max<2) |", "|---|---|---|---|---|---|"]
    for lg, s in summary.items():
        ok = s["agree"] >= 38 * s["n"] // 40 and s["max"] < 2.0
        L.append(f"| {lg} | {s['n']} | {s['agree']} | {s['mean']:.2f} | {s['max']:.2f} | {'PASS' if ok else 'FAIL'} |")
    L += ["", "Largest gaps (league, state, market, urgency joint, urgency carry):", ""]
    for lg, s in summary.items():
        for d, _lg, k, m, uj, uc in s["worst"]:
            L.append(f"- {lg} state {k} {m}: joint {uj:.1f} vs carry {uc:.1f} (|delta| {d:.1f})")
    md = "\n".join(L) + "\n"
    Path(a.out).write_text(md, encoding="utf-8")
    print(md)


if __name__ == "__main__":
    main()

"""Pick churn between two engine knob sets -- A DIAGNOSTIC, NEVER A VERDICT.

Replays a real draft at every slot with rivals held fixed, twice: once with
the knobs at their defaults and once with the overrides given. Reports how
many of my picks changed, by round and by position.

WHAT THIS NUMBER IS FOR. It says how far a change reaches, so a review can
tell "inert" from "reorders the first three rounds" without reading the diff.
It does not say whether the change is good. The repo's rule is explicit
(DECISIONS, "gates measure quality, not churn"): a source or knob change
passes on backtest accuracy and replay lineup points; churn is a diagnostic
by tier and never a veto. High churn on a fix that is right is expected;
zero churn on a fix that is right means it is inert on this board, which is
also worth knowing.

WHAT IT CANNOT DO. It cannot stand in for the outcome half. DECISIONS #41:
between-room spread on lineup points is 6.12pp against a 1% threshold, and
with only 2 seasons x 2 leagues more seeds do not shrink it, so effects below
~3% are unresolvable. Churn is not a way around that -- a change with lots of
churn and no measurable outcome is still undecided.

    venv\\Scripts\\python.exe scripts\\knob_churn.py --league keefamania \\
        --draft-id 1396184666897145856 --teams 10 --board tiers.keefamania.csv \\
        --set fallback_floor=replacement --set upside_boost_relative=true
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine_parity as EP  # noqa: E402
from slot_replay import load_log, parse_knob, replay  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-id", required=True)
    ap.add_argument("--teams", type=int, required=True)
    ap.add_argument("--board", default="tiers.keefamania.csv")
    ap.add_argument("--league", default=None)
    ap.add_argument("--slots", default="")
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE",
                    help="knob for the B arm; the A arm is always the defaults")
    a = ap.parse_args()

    overrides = {}
    for kv in a.set:
        k, v = kv.split("=", 1)
        overrides[k] = parse_knob(v)
    if not overrides:
        ap.error("--set is required: with no override both arms are identical")

    league_slots = None
    if a.league:
        from draftkit.config import Config
        _teams, _rounds, league_slots = EP.league_shape(Config.load(league=a.league))

    board = EP.load_board(a.board)
    log = load_log(a.draft_id)
    rounds = max(d["round"] for d in log)
    slots = ([int(x) for x in a.slots.split(",")] if a.slots
             else list(range(1, a.teams + 1)))

    print(f"Knob churn -- draft {a.draft_id}, {a.teams} teams, {rounds} rounds, "
          f"{len(slots)} slots")
    print(f"  A arm: defaults")
    print(f"  B arm: {overrides}\n")

    by_round: Counter = Counter()
    by_pos_from: Counter = Counter()
    by_pos_to: Counter = Counter()
    total = changed = 0
    per_slot = []
    for s in slots:
        arm_a = replay(board, log, s, a.teams, rounds, True, slots=league_slots)
        arm_b = replay(board, log, s, a.teams, rounds, True, slots=league_slots,
                       overrides=overrides)
        n = 0
        for i, (pa, pb) in enumerate(zip(arm_a, arm_b), start=1):
            total += 1
            if pa["name"] != pb["name"]:
                n += 1
                changed += 1
                by_round[i] += 1
                by_pos_from[pa["pos"]] += 1
                by_pos_to[pb["pos"]] += 1
        per_slot.append((s, n, len(arm_a)))
        print(f"  slot {s:>2}: {n:>2} of {len(arm_a)} picks changed")

    pct = 100.0 * changed / total if total else 0.0
    print(f"\n  TOTAL {changed} of {total} picks changed ({pct:.1f}%)")
    if changed:
        print("  by round:   " + "  ".join(
            f"R{r}:{by_round[r]}" for r in sorted(by_round)))
        print("  position left:   " + "  ".join(
            f"{p}:{by_pos_from[p]}" for p in sorted(by_pos_from)))
        print("  position taken:  " + "  ".join(
            f"{p}:{by_pos_to[p]}" for p in sorted(by_pos_to)))
    print("\n  Reminder: churn is a diagnostic. It is not evidence the B arm "
          "is better\n  or worse, and it does not substitute for the outcome "
          "half (DECISIONS #41).")


if __name__ == "__main__":
    main()

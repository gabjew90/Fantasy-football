"""Acceptance test for slot-market urgency (DECISIONS.md 2026-09-01).

Replays a real draft with OUR engine making our picks and rivals held fixed,
at every draft slot, twice: once ranking by position (slot_markets off) and
once ranking by unfilled roster slot (slot_markets on). Reports the starting
lineup we end up with and the roster shape.

The primary metric is PROJECTED POINTS of the starting lineup, not VORP.
That matters here. VORP grades a flex starter against replacement at his own
position -- which is the exact accounting error under test, so a VORP-graded
harness scores the two arms on a ruler one of them is trying to fix, and the
first run of this script duly reported a 9.1-point "regression" that was
entirely the ruler. Projected points is baseline-free: no choice of
replacement level can move it, so neither arm can grade itself. VORP is still
printed for continuity with the earlier bake-offs.

    python scripts/slot_replay.py --draft-id 1396184666897145856 --teams 10
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import engine_parity as EP  # noqa: E402
from engine_bakeoff import FLEX_OK, SLOTS, lineup_value  # noqa: E402


def lineup_points(chosen: list[dict], slots: dict | None = None, key: str = "proj_pts") -> float:
    """Points of the best legal starting lineup, on whatever ruler `key`
    names (projected points by default; actual season points in the
    projection-source gate). `slots` is the league's starter shape; the
    Keefamania default keeps the older callers unchanged.

    Baseline-free by construction, which is the whole reason it is the
    headline number: replacement levels cancel, so an engine that changes how
    it prices players cannot move this scoreboard except by drafting a
    different, better-scoring team.
    """
    slots = slots or SLOTS
    rem, flex, total = dict(slots), int(slots.get("FLEX", 0)), 0.0
    for p in sorted(chosen, key=lambda q: -float(q.get(key) or 0.0)):
        pos, v = p["pos"], float(p.get(key) or 0.0)
        if rem.get(pos, 0) > 0:
            rem[pos] -= 1
            total += v
        elif pos in FLEX_OK and flex > 0:
            flex -= 1
            total += v
    return total


def replay(board, log_picks, my_slot, teams, rounds, slot_markets, slots=None, overrides=None):
    """overrides: engine knobs set on every tracker (plan B3/B7 A/Bs)."""
    by_name = {p["name"]: p for p in board}
    taken, chosen, picks_so_far = set(), [], []

    for d in log_picks:
        if d.get("slot") != my_slot:
            if d["player"] in by_name:
                taken.add(d["player"])
            picks_so_far.append({
                "pick_no": d["pick_no"],
                "player_id": by_name.get(d["player"], {}).get("sleeper_id", "0"),
                "draft_slot": d["slot"], "round": d["round"],
            })
            continue

        avail = [p for p in board if p["name"] not in taken]
        t = EP.make_tracker(board, picks_so_far, my_slot,
                            slots=slots, teams=teams, rounds=rounds, overrides=overrides)
        t.slot_markets = slot_markets
        try:
            recs = t.recommendations(top_n=1)
            pick = by_name[recs[0][2]["name"]] if recs else avail[0]
        except Exception as e:  # noqa: BLE001
            print(f"    !! slot {my_slot} pick {d['pick_no']}: {e!r}")
            pick = avail[0]

        chosen.append(pick)
        taken.add(pick["name"])
        picks_so_far.append({"pick_no": d["pick_no"], "player_id": pick["sleeper_id"],
                             "draft_slot": my_slot, "round": d["round"]})
    return chosen


def parse_knob(k: str, v: str):
    """One `--set knob=value` pair, cast the way the engine will read it.

    The cast comes from `Tracker.ENGINE_KNOBS`, the same (name, cast) table
    `apply_engine_cfg` uses, so a knob typed here has the type it has when
    it arrives from config.yaml. Two failures this replaces, both found the
    same day:

      * every boolean knob is read through `bool(...)`, and `bool("false")`
        is True -- so `--set per_position_deadline=false` turned the knob ON
        and the A/B recorded in DECISIONS was the opposite arm;
      * the first fix cast every numeric to float, so `--set sims=200` handed
        `range(200.0)` to the survival sim, which raised on every one of our
        picks; replay() caught it and substituted the naive top-VORP fallback,
        and the scoreboard printed numbers for an arm that never ran.

    scripts/bridge_server.py casts through the Tracker class attribute and
    has always been right; knob_churn.py imports this so there is one parser.
    A name outside the table (the `pool_size` alias, a harness-only attribute)
    falls back to bool / float / str.
    """
    from draftkit.tracker import Tracker

    low = v.strip().lower()
    cast = dict(Tracker.ENGINE_KNOBS).get(k)
    if cast is bool or (cast is None and low in ("true", "false", "yes", "no")):
        return low in ("1", "true", "yes")
    if cast is not None:
        return cast(v)
    return float(v) if v.replace(".", "", 1).replace("-", "", 1).isdigit() else v


def load_log(draft_id: str) -> list[dict]:
    """The pick log for a draft, in pick order. Shared with knob_churn.py so
    the two replays cannot drift on how a log is read."""
    log = [json.loads(line) for line in
           open(f"data/logs/draft_{draft_id}.jsonl", encoding="utf-8")
           if '"type": "pick"' in line]
    log.sort(key=lambda d: d["pick_no"])
    return log


def shape(chosen) -> str:
    c = Counter(p["pos"] for p in chosen)
    return " ".join(f"{k}{c[k]}" for k in ("QB", "RB", "WR", "TE", "K", "DEF") if c[k])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-id", required=True)
    ap.add_argument("--teams", type=int, required=True)
    ap.add_argument("--board", default="tiers.keefamania.csv")
    ap.add_argument("--slots", default="")
    ap.add_argument("--league", default=None, help="starter shape from the league yaml (engine_parity.league_shape)")
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE",
                    help="engine knob override for BOTH arms (e.g. --set sigma_early=8 --set survival_shrink=1.0)")
    a = ap.parse_args()

    overrides = {}
    for kv in a.set:
        k, v = kv.split("=", 1)
        overrides[k] = parse_knob(k, v)
    league_slots = None
    if a.league:
        from draftkit.config import Config
        _teams, _rounds, league_slots = EP.league_shape(Config.load(league=a.league))
    # the shape this run grades on, passed explicitly. It used to be installed
    # by SLOTS.clear(); SLOTS.update(...), which rewrote engine_bakeoff's
    # module-level default for every other importer in the process -- fine
    # while this stayed a one-shot script, a silent cross-contamination the
    # moment a gate imports two replays.
    grading_slots = league_slots or SLOTS

    board = EP.load_board(a.board)
    log = load_log(a.draft_id)
    rounds = max(d["round"] for d in log)
    slots = ([int(x) for x in a.slots.split(",")] if a.slots
             else list(range(1, a.teams + 1)))

    print(f"Slot-market acceptance replay -- draft {a.draft_id}, {'knobs ' + str(overrides) if overrides else ''}"
          f"{a.teams} teams, {rounds} rounds")
    print(f"starters {grading_slots}\n")
    print(f"{'':>4}{'lineup projected pts':>28}{'':4}{'lineup VORP':>24}")
    print(f"{'slot':>4}{'by-pos':>10}{'by-slot':>9}{'diff':>9}{'':4}"
          f"{'by-pos':>8}{'by-slot':>8}{'diff':>8}   {'shape (by-slot)':<24}")

    rows = []
    for s in slots:
        off = replay(board, log, s, a.teams, rounds, False, slots=league_slots, overrides=overrides)
        on = replay(board, log, s, a.teams, rounds, True, slots=league_slots, overrides=overrides)
        po, pn = lineup_points(off, grading_slots), lineup_points(on, grading_slots)
        vo, vn = lineup_value(off), lineup_value(on)
        rows.append((s, po, pn, vo, vn, off, on))
        print(f"{s:>4}{po:>10.1f}{pn:>9.1f}{pn - po:>+9.1f}{'':4}"
              f"{vo:>8.1f}{vn:>8.1f}{vn - vo:>+8.1f}   {shape(on):<24}")

    d = [r[2] - r[1] for r in rows]
    dv = [r[4] - r[3] for r in rows]
    te_off = sum(1 for r in rows if sum(1 for p in r[5] if p["pos"] == "TE") >= 2)
    te_on = sum(1 for r in rows if sum(1 for p in r[6] if p["pos"] == "TE") >= 2)
    print(f"\nn={len(rows)} slots        PROJECTED POINTS (baseline-free, headline)")
    print(f"  by-slot - by-position: mean {st.mean(d):+.1f}  median {st.median(d):+.1f}  "
          f"better {sum(1 for x in d if x > 0)}  worse {sum(1 for x in d if x < 0)}  "
          f"tied {sum(1 for x in d if x == 0)}")
    print(f"                         worst {min(d):+.1f}  best {max(d):+.1f}")
    base = st.mean([r[1] for r in rows])
    print(f"  by-position mean {base:.1f}  ->  by-slot is {100 * st.mean(d) / base:+.2f}%")
    print(f"\n              VORP (position-baselined; overstates flex starters)")
    print(f"  by-slot - by-position: mean {st.mean(dv):+.1f}  "
          f"better {sum(1 for x in dv if x > 0)}  worse {sum(1 for x in dv if x < 0)}  "
          f"tied {sum(1 for x in dv if x == 0)}")
    print(f"\n  double-TE rosters: by-position {te_off}/{len(rows)}  "
          f"->  by-slot {te_on}/{len(rows)}")


if __name__ == "__main__":
    main()

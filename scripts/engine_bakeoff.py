"""Bake-off: does the browser driver draft as WELL as the Sleeper engine?

Parity (scripts/engine_parity.py) asks whether the two make the same pick.
They often do not -- 25% identical top pick -- but identical was never the
requirement. This asks the question that matters: replay the same draft with
each engine making our picks and rivals held fixed, then compare the starting
lineups we end up with.

    python scripts/engine_bakeoff.py --draft-id 1396184666897145856 --teams 10
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from draftkit import snake  # noqa: E402
from draftkit.tracker import Tracker, TrackerState  # noqa: E402

import engine_parity as EP  # noqa: E402

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}
FLEX_OK = {"RB", "WR", "TE"}


def lineup_value(chosen: list[dict]) -> float:
    """VORP of the best legal starting lineup out of what we drafted."""
    rem, flex, total = dict(SLOTS), SLOTS["FLEX"], 0.0
    for p in sorted(chosen, key=lambda q: -q["vorp"]):
        pos = p["pos"]
        if rem.get(pos, 0) > 0:
            rem[pos] -= 1
            total += p["vorp"]
        elif pos in FLEX_OK and flex > 0:
            flex -= 1
            total += p["vorp"]
    return total


def replay(board, log_picks, my_slot, teams, rounds, engine):
    """engine: 'python' (tracker.recommendations) or 'driver' (JS rank)."""
    mine_nos = [d["pick_no"] for d in log_picks if d.get("slot") == my_slot]
    by_name = {p["name"]: p for p in board}
    taken, chosen, picks_so_far = set(), [], []
    n_mine = 0

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

        n_mine += 1
        avail = [p for p in board if p["name"] not in taken]
        nxt = mine_nos[n_mine] if n_mine < len(mine_nos) else d["pick_no"] + teams

        if engine == "python":
            t = EP.make_tracker(board, picks_so_far, my_slot)
            t.teams, t.rounds = teams, rounds
            try:
                recs = t.recommendations(top_n=1)
                pick = by_name[recs[0][2]["name"]] if recs else avail[0]
            except Exception:                       # noqa: BLE001
                pick = avail[0]
        else:
            got = EP.js_rank(avail, [(p["name"], p["pos"]) for p in chosen],
                             nxt, teams=teams)
            if "err" in got or not got.get("top"):
                pick = avail[0]
            else:
                pick = by_name[got["top"][0].split("|")[0]]

        chosen.append(pick)
        taken.add(pick["name"])
        picks_so_far.append({"pick_no": d["pick_no"], "player_id": pick["sleeper_id"],
                             "draft_slot": my_slot, "round": d["round"]})
    return chosen


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-id", required=True)
    ap.add_argument("--teams", type=int, required=True)
    ap.add_argument("--board", default="tiers.keefamania.csv")
    ap.add_argument("--slots", default="")
    a = ap.parse_args()

    board = EP.load_board(a.board)
    log = [json.loads(l) for l in
           open(f"data/logs/draft_{a.draft_id}.jsonl", encoding="utf-8")
           if '"type": "pick"' in l]
    log.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in log)
    slots = ([int(x) for x in a.slots.split(",")] if a.slots
             else list(range(1, a.teams + 1)))

    print(f"Bake-off on draft {a.draft_id} — {a.teams} teams, {rounds} rounds\n")
    print(f"{'slot':>4}{'python':>10}{'driver':>10}{'diff':>9}")
    rows = []
    for s in slots:
        py = lineup_value(replay(board, log, s, a.teams, rounds, "python"))
        dv = lineup_value(replay(board, log, s, a.teams, rounds, "driver"))
        rows.append((s, py, dv))
        print(f"{s:>4}{py:>10.1f}{dv:>10.1f}{dv-py:>+9.1f}")

    d = [r[2] - r[1] for r in rows]
    print(f"\nn={len(rows)} slots")
    print(f"driver - python: mean {st.mean(d):+.1f}  median {st.median(d):+.1f}  "
          f"driver better {sum(1 for x in d if x > 0)}  worse {sum(1 for x in d if x < 0)}")
    print(f"                 worst {min(d):+.1f}  best {max(d):+.1f}")
    base = st.mean([r[1] for r in rows])
    print(f"python mean lineup {base:.1f}  ->  driver is {100*st.mean(d)/base:+.1f}%")


if __name__ == "__main__":
    main()

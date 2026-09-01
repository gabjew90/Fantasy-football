"""Parity check: does the browser driver rank like the Sleeper engine?

The Yahoo driver is a JavaScript reimplementation of draftkit/tracker.py,
because Chrome blocks the page from calling a local Python server (Private
Network Access) so the decision loop must live in the page. Any
reimplementation can drift, and drift here is silent: the driver still makes
*a* pick, it is just not the pick the validated engine would make.

This replays identical board states through both and diffs the top choice.
Nothing here touches the live draft; it is offline.

    python scripts/engine_parity.py --board tiers.keefamania.csv --states 40
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from draftkit import snake  # noqa: E402
from draftkit.tracker import Tracker, TrackerState  # noqa: E402

DRIVER = Path(__file__).resolve().parents[1] / "scripts" / "draft_driver.js"
NODE = shutil.which("node")

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}
TEAMS, ROUNDS = 10, 15


def load_board(path: str) -> list[dict]:
    out = []
    for i, r in enumerate(csv.DictReader(open(path, encoding="utf-8"))):
        def f(k, d=0.0):
            try:
                return float(r.get(k) or d)
            except (TypeError, ValueError):
                return d
        pos = (r.get("pos") or "").upper()
        if pos not in ("QB", "RB", "WR", "TE", "K", "DEF"):
            continue
        out.append({
            "sleeper_id": str(i + 1), "name": r["player"], "pos": pos,
            "team": (r.get("team") or "").upper(),
            "vorp": f("vorp"), "proj_pts": f("proj_pts"),
            "adp": f("adp") or None, "adp_delta": f("adp_delta"),
            "tier": int(f("tier", 9)), "pos_rank": int(f("pos_rank", 99)),
            "value_rank": int(f("value_rank", 999)),
            "cliff_flag": str(r.get("cliff_flag")).lower() == "true",
            "upside_flag": str(r.get("upside_flag")).lower() == "true",
            "proj_source": r.get("proj_source") or "blend",
        })
    out.sort(key=lambda p: -p["vorp"])
    return out


def make_tracker(board, picks, my_slot):
    t = object.__new__(Tracker)
    t.teams, t.rounds = TEAMS, ROUNDS
    t.slots = dict(SLOTS)
    t.my_slot = my_slot
    t.poll_seconds, t.fall_alert = 5.0, 12
    t.draft_id = "parity"
    t.sims, t.pool_size = 400, 120
    t.sigma_early, t.sigma_late = 6.0, 27.0
    t.qb2_round, t.te2_fall = 10, 12
    t.upside_from_round, t.upside_mult = 8, 1.15
    t.pool_lookback, t.pool_lookahead, t.pool_min = 12, 24, 40
    t.reach_prob, t.reach_scale = 0.0, 3.0
    t.run_window, t.run_min, t.run_boost = 5, 2, 1.5
    t.survival_shrink = 0.55
    t._urgency_cache = None
    t.rival_seeds, t.slot_to_user = {}, {}
    t.players = [dict(p) for p in board]
    t.by_id = {p["sleeper_id"]: p for p in t.players}
    t.state = TrackerState(
        picks=picks,
        drafted_ids={str(p["player_id"]) for p in picks},
        status="drafting",
    )
    return t


def js_rank(board, my_names, next_pick, teams=TEAMS):
    """Run the driver's rank() over the same state, via node."""
    compact = "\n".join(
        "|".join([p["name"], p["pos"], p["team"], f"{p['vorp']:.1f}",
                  "1" if p["upside_flag"] else "", "",
                  "" if p["adp"] is None else f"{p['adp']:.1f}"])
        for p in board
    )
    roster_txt = " ".join(
        f"{n.split()[0][0]}. {' '.join(n.split()[1:])} {po} XX Bye 9"
        for n, po in my_names
    )
    panel = f"YOUR TEAM ({len(my_names)}/15) {roster_txt}"
    harness = textwrap.dedent(f"""
        global.document = {{
          title: '', body: {{ innerText: {json.dumps(panel)} }},
          querySelector: () => null, querySelectorAll: () => [],
        }};
        global.window = global;
    """)
    call = textwrap.dedent(f"""
        DK.loadCompact({json.dumps(compact)}, {{teams: {teams}, myNextPick: {next_pick}}});
        const out = DK.rank();
        console.log(JSON.stringify(out.err ? {{err: out.err}} :
          {{top: out.top.slice(0,5).map(x => x.n + '|' + x.p)}}));
    """)
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "r.mjs"
        f.write_text(harness + DRIVER.read_text(encoding="utf-8") + call, encoding="utf-8")
        r = subprocess.run([NODE, str(f)], capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return {"err": (r.stderr or r.stdout).strip()[:200]}
    return json.loads(r.stdout.strip())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--board", default="tiers.keefamania.csv")
    ap.add_argument("--states", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--verbose", action="store_true")
    a = ap.parse_args()
    if not NODE:
        raise SystemExit("node not found")

    board = load_board(a.board)
    rng = random.Random(a.seed)
    agree_top1 = agree_pos = agree_top5 = 0
    disagreements = []

    for n in range(a.states):
        my_slot = rng.randint(1, TEAMS)
        mine = snake.slot_pick_numbers(my_slot, TEAMS, ROUNDS)
        # random point in the draft, at one of MY turns
        k = rng.randint(0, ROUNDS - 3)
        cur = mine[k]
        picks = []
        pool = list(board)
        for pk in range(1, cur):
            _, sl = snake.pick_to_round_slot(pk, TEAMS)
            # rivals take near the top with ADP noise; keeps states realistic
            idx = min(len(pool) - 1, max(0, int(rng.gauss(0, 4))))
            p = pool.pop(idx)
            picks.append({"pick_no": pk, "player_id": p["sleeper_id"],
                          "draft_slot": sl, "round": (pk - 1) // TEAMS + 1})
        mine_taken = [(p["name"], p["pos"]) for p in board
                      if p["sleeper_id"] in {str(x["player_id"]) for x in picks
                                             if x["draft_slot"] == my_slot}]

        t = make_tracker(board, picks, my_slot)
        try:
            recs = t.recommendations(top_n=5)
        except Exception as e:  # noqa: BLE001
            disagreements.append((n, my_slot, cur, f"python raised {e!r}", ""))
            continue
        py_top = [f"{p['name']}|{p['pos']}" for _s, _w, p in recs]

        nxt = next((x for x in mine if x > cur), cur + TEAMS)
        js = js_rank(pool, mine_taken, nxt)
        if "err" in js:
            disagreements.append((n, my_slot, cur, "js: " + js["err"], ""))
            continue
        js_top = js["top"]
        if not py_top or not js_top:
            continue

        if py_top[0] == js_top[0]:
            agree_top1 += 1
        if py_top[0].split("|")[1] == js_top[0].split("|")[1]:
            agree_pos += 1
        if js_top[0] in py_top:
            agree_top5 += 1
        if py_top[0] != js_top[0]:
            disagreements.append((n, my_slot, cur, py_top[0], js_top[0]))

    tot = a.states
    print(f"Parity over {tot} random mid-draft states (10-team, all slots)\n")
    print(f"  identical top pick        {agree_top1:3}/{tot}  {100*agree_top1/tot:5.1f}%")
    print(f"  same POSITION top pick    {agree_pos:3}/{tot}  {100*agree_pos/tot:5.1f}%")
    print(f"  driver pick in py top-5   {agree_top5:3}/{tot}  {100*agree_top5/tot:5.1f}%")
    if disagreements:
        print(f"\nDisagreements ({len(disagreements)}):")
        for n, sl, cur, pyp, jsp in disagreements[: (99 if a.verbose else 12)]:
            print(f"  state {n:2} slot {sl:2} pick {cur:3}:  python={pyp:28} driver={jsp}")


if __name__ == "__main__":
    main()

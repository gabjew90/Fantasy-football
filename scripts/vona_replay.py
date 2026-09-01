"""Counterfactual: would VONA have drafted better than VORP?

Replays a completed draft with the rivals' picks held FIXED and only our own
picks re-decided, then scores both rankings by CLV (closing ADP - pick slot;
positive means the market would have let you wait).

Why this test. Mock 8 reached an average of 9.4 picks past market, worst of
all on Mahomes: taken at 42 against an ADP of 102, for a 0.72/game edge over
a quarterback who was still on the board at 99. VORP cannot see that, because
it scores against a fixed replacement and the whole QB field sits inside two
points a game. VONA asks the draft-day question instead -- how much better is
this player than whoever survives to my next turn -- so a flat position
discounts itself.

CLV is the honest scorer here: it is out-of-sample (closing ADP was not an
input to the board) and it measures exactly the failure being fixed.

    python scripts/vona_replay.py --draft-id 1395566812157984768 --slot 2 --teams 12
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

SUFFIX = re.compile(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", re.IGNORECASE)

# starter slots; mirrors the driver's cfg for the league being replayed
SLOTS = {"QB": 1, "RB": 2, "WR": 3, "TE": 1, "K": 1, "DEF": 1}
FLEX = 2
FLEX_OK = {"RB", "WR", "TE"}


def norm(n: str) -> str:
    s = unicodedata.normalize("NFKD", n or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = SUFFIX.sub("", s.strip())
    return "".join(c for c in s.lower() if c.isalnum() or c == " ").strip()


def load_board(path: str) -> dict:
    out = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        try:
            v = float(r.get("vorp") or 0.0)
        except ValueError:
            v = 0.0
        try:
            a = float(r.get("adp") or 0) or None
        except ValueError:
            a = None
        out[norm(r["player"])] = {
            "n": r["player"], "p": (r.get("pos") or "").upper(), "v": v, "a": a,
        }
    return out


def needs_map(counts: dict) -> dict:
    need = {p: max(0, SLOTS.get(p, 0) - counts.get(p, 0)) for p in SLOTS}
    surplus = sum(max(0, counts.get(p, 0) - SLOTS.get(p, 0)) for p in ("RB", "WR", "TE"))
    need["FLEX"] = max(0, FLEX - surplus)
    return need


def fills_need(need: dict, pos: str) -> bool:
    if need.get(pos, 0) > 0:
        return True
    return pos in FLEX_OK and need.get("FLEX", 0) > 0


def allowed(pos: str, rnd: int, counts: dict, picks_left: int, rounds: int) -> bool:
    if pos in ("K", "DEF"):
        if picks_left > 2 or counts.get(pos, 0) >= 1:
            return False
    if pos == "QB":
        if counts.get("QB", 0) >= 2:
            return False
        if counts.get("QB", 0) >= 1 and rnd < 10:
            return False
    if pos == "TE" and counts.get("TE", 0) >= 2:
        return False
    need = needs_map(counts)
    open_starters = sum(need.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
    if picks_left <= open_starters and not fills_need(need, pos):
        return False
    kd = need.get("K", 0) + need.get("DEF", 0)
    if kd > 0 and picks_left <= kd and pos not in ("K", "DEF"):
        return False
    return True


def choose(avail: list, counts: dict, rnd: int, picks_left: int, rounds: int,
           teams: int, next_pick_no: int, mode: str):
    """Pick one player. mode='vorp' ranks on VORP, mode='vona' on VONA."""
    need = needs_map(counts)
    elig = [p for p in avail if allowed(p["p"], rnd, counts, picks_left, rounds)]
    if not elig:
        elig = list(avail)
    open_starters = sum(need.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
    urgent = picks_left <= open_starters + 1

    base = {}
    if mode == "vona":
        survive = next_pick_no + round(teams / 2)
        for pos in ("QB", "RB", "WR", "TE", "K", "DEF"):
            at = [p for p in avail if p["p"] == pos]
            pick = None
            for p in at:
                if pick is None:
                    pick = p
                if p["a"] is not None and p["a"] >= survive:
                    pick = p
                    break
            base[pos] = pick["v"] if pick else 0.0

    def score(p):
        if mode == "vona":
            vona = max(0.0, p["v"] - base.get(p["p"], 0.0))
            s = vona + p["v"] * 0.05
        else:
            s = p["v"]
        if fills_need(need, p["p"]):
            s += 12
            if urgent:
                s += 60
        return s

    return max(elig, key=score)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--draft-id", required=True)
    ap.add_argument("--slot", type=int, required=True)
    ap.add_argument("--teams", type=int, required=True)
    ap.add_argument("--board", default="tiers.csv")
    a = ap.parse_args()

    board = load_board(a.board)
    picks = []
    for line in open(f"data/logs/draft_{a.draft_id}.jsonl", encoding="utf-8"):
        d = json.loads(line)
        if d.get("type") == "pick":
            picks.append(d)
    picks.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in picks)
    mine = [d["pick_no"] for d in picks if d.get("slot") == a.slot]

    results = {}
    for mode in ("vorp", "vona"):
        taken = set()
        counts: dict = {}
        chosen = []
        n_mine = 0
        for d in picks:
            if d.get("slot") != a.slot:
                taken.add(norm(d["player"]))
                continue
            n_mine += 1
            avail = [v for k, v in board.items() if k not in taken]
            avail.sort(key=lambda p: -p["v"])
            picks_left = len(mine) - n_mine + 1
            nxt = mine[n_mine] if n_mine < len(mine) else d["pick_no"] + a.teams
            pick = choose(avail, counts, n_mine, picks_left, rounds,
                          a.teams, nxt, mode)
            counts[pick["p"]] = counts.get(pick["p"], 0) + 1
            taken.add(norm(pick["n"]))
            chosen.append((d["pick_no"], pick))
        results[mode] = chosen

    print(f"Replay of draft {a.draft_id} — slot {a.slot}, {a.teams} teams\n")
    print(f"{'pick':>4}  {'VORP ranking':26} {'CLV':>6}   {'VONA ranking':26} {'CLV':>6}")
    tot = {"vorp": [], "vona": []}
    for i in range(len(results["vorp"])):
        ov, pv = results["vorp"][i]
        _, pn = results["vona"][i]
        cv = (pv["a"] - ov) if pv["a"] else None
        cn = (pn["a"] - ov) if pn["a"] else None
        if cv is not None:
            tot["vorp"].append(cv)
        if cn is not None:
            tot["vona"].append(cn)
        print(f"{ov:>4}  {pv['n'][:24]:26} {('%+.1f' % cv) if cv is not None else '   n/a':>6}"
              f"   {pn['n'][:24]:26} {('%+.1f' % cn) if cn is not None else '   n/a':>6}")

    for m in ("vorp", "vona"):
        xs = tot[m]
        print(f"\n{m.upper():5} average CLV: {sum(xs)/len(xs):+.2f} over {len(xs)} priced picks")
    d = sum(tot["vona"]) / len(tot["vona"]) - sum(tot["vorp"]) / len(tot["vorp"])
    print(f"VONA - VORP = {d:+.2f} picks of CLV "
          f"({'VONA better' if d > 0 else 'VORP better'})")

    # CLV is only a proxy, and one biased against VONA: taking a scarce-
    # position player early reads as a "reach" even when it is right. What we
    # actually care about is the starting lineup we end up with.
    def starters_value(chosen):
        """Sum VORP of the best legal starting lineup from the drafted set."""
        pool = sorted((p for _, p in chosen), key=lambda p: -p["v"])
        remaining = dict(SLOTS)
        flex = FLEX
        total = 0.0
        for p in pool:
            pos = p["p"]
            if remaining.get(pos, 0) > 0:
                remaining[pos] -= 1
                total += p["v"]
            elif pos in FLEX_OK and flex > 0:
                flex -= 1
                total += p["v"]
        return total

    sv = {m: starters_value(results[m]) for m in ("vorp", "vona")}
    print(f"\nStarting-lineup VORP  —  VORP ranking {sv['vorp']:.1f}"
          f"  ·  VONA ranking {sv['vona']:.1f}"
          f"  ({sv['vona'] - sv['vorp']:+.1f})")


if __name__ == "__main__":
    main()

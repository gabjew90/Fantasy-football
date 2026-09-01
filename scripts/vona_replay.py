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


import math


def _norm_cdf(z: float) -> float:
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _sigma(rnd: int) -> float:
    return 6.0 + 1.5 * max(0, rnd - 1)


def survival(p: dict, next_pick: int, rnd: int) -> float:
    """Calibrated P(still on the board at our next turn). Shrink 0.55 is the
    map fitted to the Omnibeta CLV retro in urgency.py."""
    if p["a"] is None:
        return 0.5
    raw = _norm_cdf((p["a"] - next_pick) / _sigma(rnd))
    return min(0.99, max(0.01, 0.5 + (raw - 0.5) * 0.55))


def e_best_next(avail: list, pos: str, next_pick: int, rnd: int) -> float:
    carry, exp = 1.0, 0.0
    for p in avail:
        if p["p"] != pos:
            continue
        s = survival(p, next_pick, rnd)
        exp += carry * s * p["v"]
        carry *= (1 - s)
        if carry < 0.01:
            break
    return exp


def choose(avail: list, counts: dict, rnd: int, picks_left: int, rounds: int,
           teams: int, next_pick_no: int, mode: str):
    """mode='vorp' | 'vona' (binary survival) | 'pair' (ported engine)."""
    need = needs_map(counts)
    elig = [p for p in avail if allowed(p["p"], rnd, counts, picks_left, rounds)]
    if not elig:
        elig = list(avail)
    open_starters = sum(need.get(k, 0) for k in ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"))
    urgent = picks_left <= open_starters + 1

    if mode in ("pair", "pairpos"):
        NEED_DAMP = 0.6
        ebn = {q: e_best_next(avail, q, next_pick_no, rnd)
               for q in ("QB", "RB", "WR", "TE", "K", "DEF")}
        second = {}
        for q in ("QB", "RB", "WR", "TE", "K", "DEF"):
            at = [p for p in avail if p["p"] == q]
            second[q] = at[1]["v"] if len(at) > 1 else 0.0

        def needs_after(taken):
            out = dict(need)
            if out.get(taken, 0) > 0:
                out[taken] -= 1
            elif taken in FLEX_OK and out.get("FLEX", 0) > 0:
                out["FLEX"] -= 1
            return out

        def pair_score(p):
            after = needs_after(p["p"])
            c2 = dict(counts)
            c2[p["p"]] = c2.get(p["p"], 0) + 1
            best = 0.0
            for q in ("QB", "RB", "WR", "TE", "K", "DEF"):
                if not allowed(q, rnd + 1, c2, picks_left - 1, rounds):
                    continue
                e = ebn[q]
                if q == p["p"]:
                    e = min(e, second[q])
                v = e if fills_need(after, q) else e * NEED_DAMP
                best = max(best, v)
            own = p["v"] * (1.0 if fills_need(need, p["p"]) else NEED_DAMP)
            return own + best

        if mode == "pair":
            return max(elig, key=pair_score)
        # faithful planner.py: ONE candidate per position (greedy best there),
        # then pair-rank those ~6 -- not the whole board.
        best_at = {}
        for p in elig:
            cur = best_at.get(p["p"])
            gv = p["v"] - e_best_next(avail, p["p"], next_pick_no, rnd)
            if cur is None or gv > cur[0]:
                best_at[p["p"]] = (gv, p)
        cands = [v[1] for v in best_at.values()]
        return max(cands, key=pair_score)

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
    for mode in ("vorp", "vona", "pair", "pairpos"):
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
    tot = {"vorp": [], "vona": [], "pair": [], "pairpos": []}
    for m in ("vorp", "vona", "pair", "pairpos"):
        for ov, pk in results[m]:
            if pk["a"]:
                tot[m].append(pk["a"] - ov)

    for m in ("vorp", "vona", "pair", "pairpos"):
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

    sv = {m: starters_value(results[m]) for m in ("vorp","vona","pair","pairpos")}
    print(f"LINEUP vorp={sv['vorp']:.1f} vona={sv['vona']:.1f} "
          f"pair={sv['pair']:.1f} pairpos={sv['pairpos']:.1f}")


if __name__ == "__main__":
    main()

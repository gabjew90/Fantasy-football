"""Season-level replay: the first metric that can see the BENCH.

Every draft replay so far scored the projected points of the starting lineup,
which is baseline-free and honest -- and completely blind to bench decisions.
A backup QB and a bench WR both score zero on it. This harness drafts a roster
the same way, then plays a 17-week season against it and counts what the
roster actually realises, week by week, with starters going missing.

    python scripts/season_replay.py --league keefamania --sims 200
    python scripts/season_replay.py --league omnibeta  --sims 200

Two arms per draft slot: bench rounds priced by VORP (engine.bench_insurance
off) and priced as insurance (on). Same rivals, same season draws.

HOW THE GRADER STAYS INDEPENDENT OF THE FORMULA UNDER TEST
----------------------------------------------------------
draftkit/bench.py uses three constants: position absent-week MEANS, a k-th
best waiver level, and a handcuff uplift MEDIAN. A grader that fed those same
constants back in would confirm the formula by construction -- the trap this
repo has now hit three times (VORP-scored flex, tilts scored on tilted
projections, and the first draft of this very harness, which drew injuries
from the per-player exp_games column the formula was also going to use).

So this harness draws from EMPIRICAL DISTRIBUTIONS, not the means:
  * absences: a count drawn from the observed distribution of absent weeks
    for the position (data/processed/bench_rates.json, six ex-ante season
    pairs), placed uniformly across the 17 fantasy weeks around the bye.
    Never per player. The formula uses this distribution's mean; the grader
    uses its shape.
  * handcuff production: a share drawn from the observed per-week
    distribution, not the median.
  * the wire: an empty starting slot is filled by a player drawn UNIFORMLY
    from the top 2k undrafted at the position -- imperfect streaming without
    pinning it to the formula's k-th.

What it does NOT model, deliberately: weekly scoring variance (a player who
plays scores proj/17 every week), in-season pickups beyond the wire, trades.
Those are the variance-modelling items the correction pass deferred. Bench
value is what this measures, and bench value is mostly about absences.

Common random numbers: absence schedules are keyed by (sim, player), so a
player on both arms' rosters has the identical season in both. Differences
between arms are then differences in the roster, not in the dice.
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
import zlib
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np  # noqa: E402
import polars as pl  # noqa: E402

import engine_parity as EP  # noqa: E402
import draftkit.tracker as T  # noqa: E402
from slot_replay import replay  # noqa: E402

from draftkit.snake import FLEX_ELIGIBLE  # noqa: E402

WEEKS = 17
LEAGUES = {
    "keefamania": dict(board="tiers.keefamania.csv", log="1396184666897145856",
                       teams=10, rounds=15, k=3,     # rolling waiver list
                       slots={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1,
                              "K": 1, "DEF": 1}),
    "omnibeta": dict(board="tiers.csv", log="1395566812157984768",
                     teams=12, rounds=15, k=2,       # FAAB
                     slots={"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2,
                            "K": 1, "DEF": 1}),
}
STARTER_ORDER = ("QB", "RB", "WR", "TE", "K", "DEF")


def rng_for(*parts) -> np.random.Generator:
    return np.random.default_rng(zlib.crc32(":".join(map(str, parts)).encode()))


def team_byes(schedule_path: Path) -> dict[str, int]:
    """team -> bye week, from the weeks a team has no game."""
    if not schedule_path.exists():
        return {}
    s = pl.read_parquet(schedule_path)
    out = {}
    for team in s["team"].unique().to_list():
        weeks = set(s.filter(pl.col("team") == team)["week"].to_list())
        missing = [w for w in range(1, 19) if w not in weeks]
        if missing:
            out[str(team)] = int(missing[0])
    return out


def absence_schedule(p: dict, sim: int, seed: str, rates: dict,
                     byes: dict[str, int]) -> set[int]:
    """Weeks this player is unavailable in this sim: bye + injury draw."""
    bye = p.get("bye") or byes.get(str(p.get("team") or "").upper())
    out = {int(bye)} if bye and 1 <= int(bye) <= WEEKS else set()
    dist = rates["absent_weeks"].get(p["pos"])
    if not dist:
        return out
    rng = rng_for(seed, sim, p["sleeper_id"])
    n = int(rng.choice(dist))
    pool = [w for w in range(1, WEEKS + 1) if w not in out]
    if n > 0:
        out |= set(int(w) for w in rng.choice(pool, size=min(n, len(pool)),
                                              replace=False))
    return out


def wire_pool(board: list[dict], last_pick: int, k: int) -> dict[str, list[dict]]:
    """Per position: the top 2k players the market leaves undrafted."""
    out: dict[str, list[dict]] = {}
    for pos in STARTER_ORDER:
        free = sorted(
            (p for p in board if p["pos"] == pos
             and (p.get("adp") is None or float(p["adp"]) > last_pick)),
            key=lambda p: -float(p.get("proj_pts") or 0.0))
        out[pos] = free[: max(1, 2 * k)]
    return out


def week_points(roster: list[dict], week: int, absent: dict[str, set[int]],
                slots: dict, wire: dict[str, list[dict]], my_ids: set[str],
                sim: int, seed: str, rates: dict) -> tuple[float, float]:
    """(lineup points, of which from the wire) for one week."""
    by_name = {p["name"]: p for p in roster}
    pts: dict[str, float] = {}
    for p in roster:
        if week in absent[p["sleeper_id"]]:
            continue
        v = float(p.get("proj_pts") or 0.0) / WEEKS
        starter = by_name.get(str(p.get("backs_up") or ""))
        if (starter is not None and starter["pos"] == p["pos"]
                and week in absent[starter["sleeper_id"]]):
            share = float(rng_for(seed, sim, "hc", p["sleeper_id"], week)
                          .choice(rates["handcuff_share"]))
            v = float(starter.get("proj_pts") or 0.0) / WEEKS * share
        pts[p["sleeper_id"]] = v

    used: set[str] = set()
    total = wire_pts = 0.0

    def take_best(eligible):
        best = None
        for pid, v in pts.items():
            if pid in used or pid not in eligible:
                continue
            if best is None or v > pts[best]:
                best = pid
        return best

    def from_wire(pos_choices, slot_tag):
        cands = [q for pos in pos_choices for q in wire.get(pos, [])
                 if q["sleeper_id"] not in my_ids]
        if not cands:
            return 0.0
        q = cands[int(rng_for(seed, sim, "wire", slot_tag, week)
                      .integers(len(cands)))]
        return float(q.get("proj_pts") or 0.0) / WEEKS

    ids_by_pos = {pos: {p["sleeper_id"] for p in roster if p["pos"] == pos}
                  for pos in STARTER_ORDER}
    for pos in STARTER_ORDER:
        for i in range(slots.get(pos, 0)):
            pid = take_best(ids_by_pos[pos])
            if pid is None:
                w = from_wire([pos], f"{pos}{i}")
                total += w
                wire_pts += w
            else:
                used.add(pid)
                total += pts[pid]
    flex_ids = set().union(*(ids_by_pos[p] for p in FLEX_ELIGIBLE))
    for i in range(slots.get("FLEX", 0)):
        pid = take_best(flex_ids)
        if pid is None:
            w = from_wire(list(FLEX_ELIGIBLE), f"FLEX{i}")
            total += w
            wire_pts += w
        else:
            used.add(pid)
            total += pts[pid]
    return total, wire_pts


def season(roster, slots, wire, rates, byes, sims, seed) -> dict:
    my_ids = {p["sleeper_id"] for p in roster}
    totals, wires = [], []
    for sim in range(sims):
        absent = {p["sleeper_id"]: absence_schedule(p, sim, seed, rates, byes)
                  for p in roster}
        t = w = 0.0
        for week in range(1, WEEKS + 1):
            a, b = week_points(roster, week, absent, slots, wire, my_ids,
                               sim, seed, rates)
            t += a
            w += b
        totals.append(t)
        wires.append(w)
    return {"mean": st.mean(totals), "wire": st.mean(wires), "per_sim": totals}


def shape(roster) -> str:
    c = Counter(p["pos"] for p in roster)
    return " ".join(f"{k}{c[k]}" for k in ("QB", "RB", "WR", "TE", "K", "DEF") if c[k])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True, choices=list(LEAGUES))
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--rates", default="data/processed/bench_rates.json")
    ap.add_argument("--slots", default="", help="comma list of draft slots")
    a = ap.parse_args()

    L = LEAGUES[a.league]
    if not Path(a.rates).exists():
        # data/processed is not tracked; the distributions are regenerable
        raise SystemExit(
            f"{a.rates} not found. Export the empirical distributions first:\n"
            f"  python scripts/derive_bench_rates.py --league {a.league} "
            f"--export {a.rates}")
    rates = json.loads(Path(a.rates).read_text(encoding="utf-8"))
    byes = team_byes(Path("data/processed/schedule_2026.parquet"))
    board = EP.load_board(L["board"])
    log = [json.loads(line) for line in
           open(f"data/logs/draft_{L['log']}.jsonl", encoding="utf-8")
           if '"type": "pick"' in line]
    log.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in log)
    wire = wire_pool(board, L["teams"] * L["rounds"], L["k"])
    slots = ([int(x) for x in a.slots.split(",")] if a.slots
             else list(range(1, L["teams"] + 1)))

    print(f"Season replay — {a.league}: {L['teams']} teams, k={L['k']}, "
          f"{a.sims} seasons per roster, absences from empirical position "
          f"distributions\n")
    print(f"{'slot':>4}{'VORP bench':>12}{'insurance':>11}{'diff':>8}"
          f"{'wire off':>10}{'wire on':>9}   shape off -> on")
    diffs, rows = [], []
    for s in slots:
        rosters = {}
        for flag in (False, True):
            T.Tracker.bench_insurance = flag
            rosters[flag] = replay(board, log, s, L["teams"], rounds, True,
                                   slots=L["slots"])
        T.Tracker.bench_insurance = False
        off = season(rosters[False], L["slots"], wire, rates, byes, a.sims,
                     f"{a.league}:{s}")
        on = season(rosters[True], L["slots"], wire, rates, byes, a.sims,
                    f"{a.league}:{s}")
        d = on["mean"] - off["mean"]
        diffs.append(d)
        paired = [b - c for b, c in zip(on["per_sim"], off["per_sim"])]
        rows.append((s, off, on, paired))
        print(f"{s:>4}{off['mean']:>12.1f}{on['mean']:>11.1f}{d:>+8.1f}"
              f"{off['wire']:>10.1f}{on['wire']:>9.1f}   "
              f"{shape(rosters[False])} -> {shape(rosters[True])}")

    all_paired = [x for _s, _o, _n, paired in rows for x in paired]
    se = st.pstdev(all_paired) / max(1, len(all_paired)) ** 0.5
    print(f"\nn={len(diffs)} slots x {a.sims} seasons")
    print(f"insurance - VORP: mean {st.mean(diffs):+.1f} pts/season  "
          f"(paired se {se:.1f})  slots better {sum(1 for x in diffs if x > 0)}  "
          f"worse {sum(1 for x in diffs if x < 0)}  tied {sum(1 for x in diffs if x == 0)}")
    base = st.mean(o["mean"] for _s, o, _n, _p in rows)
    print(f"VORP-bench mean season {base:.1f}  ->  insurance is "
          f"{100 * st.mean(diffs) / base:+.2f}%")


if __name__ == "__main__":
    main()

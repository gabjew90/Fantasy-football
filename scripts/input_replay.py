"""Verification for "projections as an input" (DECISIONS 2026-09-02 #21).

Two boards -- the old one (model blend) and the new one (external stat
lines) -- are replayed through the SAME engine against an archived draft,
with rivals' picks held fixed and our picks made by the engine at every
slot. Reported per slot and in aggregate:

  * projected points of the starting lineup, graded on the NEW input (the
    input of record) and on the old, so neither board grades itself alone;
  * the picks that changed, by round, and the ten largest changes -- the
    gate is that changes concentrate in bench rounds and QB; if starters in
    rounds 1-6 move materially, stop and report.

Also prints the per-position rank correlation between the two boards'
proj_pts, and the players that left or joined the board.

    venv\\Scripts\\python.exe scripts\\input_replay.py --league keefamania \\
        --draft-id 1396184666897145856 --teams 10 --old data/processed/tiers.old.csv
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import engine_parity as EP  # noqa: E402
from slot_replay import lineup_points, replay  # noqa: E402

SLOTS_BY_LEAGUE = {
    "keefamania": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1},
    "omnibeta": {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1},
}


def spearman(a, b):
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    n = len(a)
    if n < 3:
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def grade(chosen, ruler_by_name, slots):
    """Lineup points of a roster graded on another board's proj_pts."""
    import slot_replay as SR
    saved = dict(SR.SLOTS)
    SR.SLOTS.clear(); SR.SLOTS.update(slots)
    try:
        return lineup_points([dict(p, proj_pts=ruler_by_name.get(p["name"], {}).get("proj_pts", 0.0)) for p in chosen])
    finally:
        SR.SLOTS.clear(); SR.SLOTS.update(saved)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--draft-id", required=True)
    ap.add_argument("--teams", type=int, required=True)
    ap.add_argument("--old", required=True, help="the old board csv (model blend)")
    ap.add_argument("--new", default=None, help="the new board csv (default: league tiers csv)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    new_path = a.new or ("tiers.csv" if a.league == "omnibeta" else f"tiers.{a.league}.csv")
    old, new = EP.load_board(a.old), EP.load_board(new_path)
    slots = SLOTS_BY_LEAGUE.get(a.league, EP.SLOTS)
    log = [json.loads(l) for l in open(f"data/logs/draft_{a.draft_id}.jsonl", encoding="utf-8")]
    log = [d for d in log if d.get("type") == "pick"]
    log.sort(key=lambda d: d["pick_no"])
    rounds = max(d["round"] for d in log)
    by_old = {p["name"]: p for p in old}
    by_new = {p["name"]: p for p in new}

    L = [f"# Input replay — {a.league}, draft {a.draft_id}", "",
         f"Old board `{a.old}` vs new board `{new_path}`; {a.teams} teams, {rounds} rounds; "
         "rivals held to the archived picks, our picks by the engine at every slot.", ""]
    # board-vs-board
    L += ["## The two boards", "", "| pos | n both | Spearman proj_pts | left the board | joined |", "|---|---|---|---|---|"]
    for pos in ("QB", "RB", "WR", "TE"):
        o = {p["name"]: p["proj_pts"] for p in old if p["pos"] == pos}
        n = {p["name"]: p["proj_pts"] for p in new if p["pos"] == pos}
        both = [k for k in o if k in n and o[k] > 0 and n[k] > 0]
        left = [k for k in o if k not in n]
        joined = [k for k in n if k not in o]
        L.append(f"| {pos} | {len(both)} | {spearman([o[k] for k in both], [n[k] for k in both]):.3f} | "
                 f"{len(left)} | {len(joined)} |")
    zeroed = [p["name"] for p in new if p["proj_pts"] == 0 and by_old.get(p["name"], {}).get("proj_pts", 0) > 0]
    L += ["", f"Zeroed on the new board (non-starter rule or availability), had points before ({len(zeroed)}): "
          + ", ".join(zeroed[:30]) + (" …" if len(zeroed) > 30 else ""), ""]

    # replay
    per_slot, changed = [], []
    for slot in range(1, a.teams + 1):
        c_old = replay(old, log, slot, a.teams, rounds, True, slots=slots)
        c_new = replay(new, log, slot, a.teams, rounds, True, slots=slots)
        row = {"slot": slot,
               "old_on_new": grade(c_old, by_new, slots), "new_on_new": grade(c_new, by_new, slots),
               "old_on_old": grade(c_old, by_old, slots), "new_on_old": grade(c_new, by_old, slots)}
        per_slot.append(row)
        my_picks = [d for d in log if d.get("slot") == slot]
        for i, (po, pn) in enumerate(zip(c_old, c_new)):
            if po["name"] != pn["name"]:
                rnd = my_picks[i]["round"] if i < len(my_picks) else i + 1
                changed.append({"slot": slot, "round": rnd, "old": po["name"] + f" ({po['pos']})",
                                "new": pn["name"] + f" ({pn['pos']})",
                                # tier of the player the OLD board took, on the old board
                                # (DECISIONS #23: churn is reported by tier, as a diagnostic)
                                "tier": int(po.get("tier") or 9),
                                "delta_new_ruler": pn["proj_pts"] - by_new.get(po["name"], {}).get("proj_pts", 0.0)})
    L += ["## Lineup points by slot", "",
          "| slot | old roster, new ruler | new roster, new ruler | Δ | old roster, old ruler | new roster, old ruler | Δ |",
          "|---|---|---|---|---|---|---|"]
    for r in per_slot:
        L.append(f"| {r['slot']} | {r['old_on_new']:.0f} | {r['new_on_new']:.0f} | {r['new_on_new'] - r['old_on_new']:+.0f} | "
                 f"{r['old_on_old']:.0f} | {r['new_on_old']:.0f} | {r['new_on_old'] - r['old_on_old']:+.0f} |")
    d_new = [r["new_on_new"] - r["old_on_new"] for r in per_slot]
    d_old = [r["new_on_old"] - r["old_on_old"] for r in per_slot]
    L += ["", f"Mean Δ on the new ruler {st.mean(d_new):+.1f} (slots better/worse {sum(x > 0 for x in d_new)}/{sum(x < 0 for x in d_new)}); "
          f"on the old ruler {st.mean(d_old):+.1f} ({sum(x > 0 for x in d_old)}/{sum(x < 0 for x in d_old)}).", ""]
    # picks that changed
    by_round = {}
    for c in changed:
        by_round[c["round"]] = by_round.get(c["round"], 0) + 1
    total_picks = a.teams * rounds
    L += ["## Picks that changed", "",
          f"{len(changed)} of {total_picks} picks changed. By round: "
          + ", ".join(f"R{r}: {by_round[r]}" for r in sorted(by_round)) + ".", "",
          f"Rounds 1-6: {sum(v for r, v in by_round.items() if r <= 6)} changes "
          f"({sum(v for r, v in by_round.items() if r <= 6) / max(1, a.teams * 6):.0%} of those picks); "
          f"rounds 7+: {sum(v for r, v in by_round.items() if r > 6)}.", ""]
    # by tier of the old pick (diagnostic, DECISIONS #23): T1-T2 are the
    # starters the brief worried about; T5+ is bench order
    by_tier = {}
    for c in changed:
        by_tier[c["tier"]] = by_tier.get(c["tier"], 0) + 1
    picks_by_tier = {}
    for slot in range(1, a.teams + 1):
        for p in replay(old, log, slot, a.teams, rounds, True, slots=slots):
            t = int(p.get("tier") or 9)
            picks_by_tier[t] = picks_by_tier.get(t, 0) + 1
    L += ["By tier of the player the old board took (changed / picks at that tier): "
          + ", ".join(f"T{t}: {by_tier.get(t, 0)}/{picks_by_tier[t]} ({by_tier.get(t, 0) / picks_by_tier[t]:.0%})"
                      for t in sorted(picks_by_tier)) + ".", "",
          "Ten largest changes (projected points, new ruler, new pick minus old pick):", "",
          "| slot | round | old pick | new pick | Δ |", "|---|---|---|---|---|"]
    for c in sorted(changed, key=lambda x: -abs(x["delta_new_ruler"]))[:10]:
        L.append(f"| {c['slot']} | {c['round']} | {c['old']} | {c['new']} | {c['delta_new_ruler']:+.0f} |")
    early = [c for c in changed if c["round"] <= 6]
    L += ["", "Round 1-6 changes:", ""] + ([f"- slot {c['slot']} R{c['round']}: {c['old']} -> {c['new']}" for c in early] or ["- none"])
    md = "\n".join(L) + "\n"
    out = Path(a.out) if a.out else Path("reports") / f"input_replay.{a.league}.{a.draft_id}.md"
    out.write_text(md, encoding="utf-8")
    print(md)
    print(f"-> {out}")


if __name__ == "__main__":
    main()

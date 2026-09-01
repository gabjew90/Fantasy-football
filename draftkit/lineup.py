"""Lineup + early-games briefs (season spec Task 6).

Start/sit against the actual weekly opponent: optimal lineup diffs only,
variance lean that ONLY breaks close calls (never overrides a clear
projection edge), inactive-risk flags ordered by kickoff (week 1 of 2026
has a Wednesday game — lock order comes from the schedule, not the
calendar), and red structural warnings first.
"""

from __future__ import annotations

FLEX_ELIGIBLE = ("RB", "WR", "TE")


def optimal_lineup(roster: list[dict], slots: dict[str, int], flex: int) -> list[dict]:
    pool = sorted(roster, key=lambda p: -(p.get("weekly") or 0.0))
    counts = {k: 0 for k in slots}
    chosen, flex_used = [], 0
    for p in pool:
        pos = p.get("pos")
        if pos in slots and counts[pos] < slots[pos]:
            counts[pos] += 1
            chosen.append(p)
    ids = {p["sleeper_id"] for p in chosen}
    for p in pool:
        if p["sleeper_id"] not in ids and p.get("pos") in FLEX_ELIGIBLE and flex_used < flex:
            flex_used += 1
            chosen.append(p)
            ids.add(p["sleeper_id"])
    return chosen


def lineup_changes(roster: list[dict], current_ids: list[str],
                   slots: dict[str, int], flex: int) -> tuple[list[str], float]:
    """Suggested swaps (only differences) + optimal projected total."""
    by_id = {str(p["sleeper_id"]): p for p in roster}
    optimal = optimal_lineup(roster, slots, flex)
    opt_ids = {p["sleeper_id"] for p in optimal}
    cur_ids = {i for i in (str(x) for x in current_ids) if i in by_id}
    changes = []
    ins = [by_id[i] for i in opt_ids - cur_ids]
    outs = [by_id[i] for i in cur_ids - opt_ids]
    ins.sort(key=lambda p: -(p.get("weekly") or 0))
    # pair each swap-in with a swap-out at the SAME position first — cross-position
    # pairing produced misleading lines like "Deebo over Harvey (+-0.2)" when the
    # real moves were Deebo->WR slot and Fannin->flex. Leftovers pair by points.
    remaining = sorted(outs, key=lambda p: (p.get("weekly") or 0))
    pairs = []
    for a in ins:
        b = next((o for o in remaining if o.get("pos") == a.get("pos")), None)
        if b:
            remaining.remove(b)
            pairs.append((a, b))
        else:
            pairs.append((a, None))
    for a, b in pairs:
        if b is None and remaining:
            b = remaining.pop(0)
        if b is None:
            changes.append(f"start {a['name']} (an active slot is empty: "
                           f"+{a.get('weekly') or 0:.1f} pts)")
            continue
        gain = (a.get("weekly") or 0) - (b.get("weekly") or 0)
        note = f"+{gain:.1f} pts" if gain >= 0.05 else "coin flip — either works"
        changes.append(f"start {a['name']} over {b['name']} ({note})")
    total = sum(p.get("weekly") or 0.0 for p in optimal)
    return changes, total


def variance_pick(a: dict, b: dict, margin: float, close_gap: float) -> dict:
    """Between two candidates: projection wins unless it's a close call, then
    the matchup margin decides — underdogs take ceiling, favorites take floor."""
    hi, lo = (a, b) if (a.get("weekly") or 0) >= (b.get("weekly") or 0) else (b, a)
    if (hi.get("weekly") or 0) - (lo.get("weekly") or 0) >= close_gap:
        return hi
    if margin < -8:   # projected underdog: chase ceiling
        return a if (a.get("stdev") or 0) >= (b.get("stdev") or 0) else b
    if margin > 8:    # projected favorite: protect floor
        return a if (a.get("stdev") or 0) <= (b.get("stdev") or 0) else b
    return hi


def render_lineup_brief(model: dict) -> str:
    m = model
    lines = [f"# Lineup Brief — week {m['week']}", ""]
    for w in m.get("warnings", []):
        lines.append(f"🔴 **{w}**")
    if m.get("warnings"):
        lines.append("")
    if m.get("stale"):
        lines += [f"⚠ STALE DATA: {', '.join(m['stale'])}", ""]
    if m.get("preseason_note"):
        lines += [f"⚠ {m['preseason_note']}", ""]
    lines += [
        f"**vs {m['opp_name']}: you {m['my_total']:.1f} — {m['opp_total']:.1f} them** · {m['lean']}",
        "",
        "## Changes",
    ]
    lines += [f"- {c}" for c in m.get("changes", [])] or []
    if not m.get("changes"):
        lines.append("- current lineup is already optimal")
    # show WHEN the opponent-defense adjustment moved a number, so a flipped
    # start/sit is explainable (post-v2 item 2)
    adj = [x for x in (m.get("matchups") or []) if abs(x["mult"] - 1.0) >= 0.02]
    if adj:
        lines += ["", "## Matchup adjustments (opponent defense)"]
        for x in sorted(adj, key=lambda y: -abs(y["mult"] - 1.0))[:6]:
            lines.append(f"- {x['name']} vs {x['opp']}: {(x['mult'] - 1.0) * 100:+.0f}% "
                         f"({x['before']:.1f} → {x['after']:.1f} pts)")
    flags = sorted(m.get("flags", []), key=lambda f: f.get("kick") or "9999")
    if flags:
        lines += ["", "## Inactive risk (by kickoff — earliest locks first)"]
        for f in flags:
            lines.append(f"- {f['kick']}: **{f['name']}** is {f['status']}"
                         + (f" — if inactive, start {f['backup']}" if f.get("backup") else ""))
    if m.get("early_mine"):
        lines += ["", "## Your starters who lock EARLY this week",
                  *[f"- **{n}**" for n in m["early_mine"]]]
    if m.get("early_teams"):
        lines += ["", f"Early-game teams this week (lock before Sunday): {', '.join(m['early_teams'])}"]
    return "\n".join(lines) + "\n"


def render_early_check(model: dict) -> str:
    m = dict(model)
    md = render_lineup_brief(m)
    return md.replace("# Lineup Brief", "# Early-Games Check (players in these games lock early)")

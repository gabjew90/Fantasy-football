"""Module 3 — lineup optimizer.

Sleeper projections (draftkit's league-scored fetch with fallback) tilted by
Vegas implied totals; the words go to the 2 FLEX spots and any decision
within ~1.5 points. Ceiling/floor mode comes from Module 4's margin. Every
Questionable starter gets a precomputed "if inactive -> start Z" row that
Module 2 consumes.
"""

from __future__ import annotations

import logging

from draftkit.lineup import lineup_changes, optimal_lineup

from . import consensus, provenance
from .vegas import implied_totals, week_window

log = logging.getLogger("manager")

FLEX_POS = ("RB", "WR", "TE")
COINFLIP = 1.5
VEGAS_UP, VEGAS_DOWN, VEGAS_MULT = 24.0, 18.0, 0.05
STDEV = {"QB": 7.0, "RB": 6.0, "WR": 6.5, "TE": 5.0, "K": 4.5, "DEF": 6.0}


def vegas_adjust(roster: list[dict], totals: dict[str, float]) -> list[dict]:
    out = []
    for p in roster:
        q = dict(p)
        t = totals.get(p.get("team") or "")
        if t is not None and q.get("weekly"):
            if t >= VEGAS_UP:
                q["weekly"] = round(q["weekly"] * (1 + VEGAS_MULT), 2)
                q["vegas"] = f"implied {t:.0f} (+{VEGAS_MULT:.0%})"
            elif t < VEGAS_DOWN:
                q["weekly"] = round(q["weekly"] * (1 - VEGAS_MULT), 2)
                q["vegas"] = f"implied {t:.0f} (-{VEGAS_MULT:.0%})"
        q["stdev"] = STDEV.get(q.get("pos"), 5.0)
        out.append(q)
    return out


def contingency_table(roster: list[dict], starters: list[dict]) -> dict[str, str]:
    """starter name -> replacement instruction, for every non-healthy starter."""
    starter_ids = {str(p["sleeper_id"]) for p in starters}
    bench = [p for p in roster if str(p["sleeper_id"]) not in starter_ids]
    table = {}
    for s in starters:
        if (s.get("status") or "") not in ("Questionable", "Doubtful", "Out"):
            continue
        pool = [b for b in bench
                if (b["pos"] == s["pos"] or (s["pos"] in FLEX_POS and b["pos"] in FLEX_POS))
                and (b.get("status") or "") in ("", "Questionable")
                and (b.get("weekly") or 0) > 0]
        if pool:
            best = max(pool, key=lambda b: b.get("weekly") or 0)
            table[s["name"]] = f"{best['name']} ({best['pos']}, {best.get('weekly', 0):.1f} pts)"
    return table


def flex_analysis(roster: list[dict], optimal: list[dict], mode: str,
                  slots: dict[str, int], flex: int) -> list[str]:
    """The decisions worth words: FLEX occupants vs alternatives within 1.5 pts.

    `slots` and `flex` are the league's own shape (draftkit/shape.py). They
    were module literals holding Omnibeta's two flex spots, so a one-flex
    league got a second flex decision it does not have."""
    opt_ids = {str(p["sleeper_id"]) for p in optimal}
    dedicated: dict[str, int] = {k: 0 for k in slots}
    flex_occ = []
    for p in sorted(optimal, key=lambda x: -(x.get("weekly") or 0)):
        if dedicated.get(p["pos"], 99) < slots.get(p["pos"], 0):
            dedicated[p["pos"]] += 1
        elif p["pos"] in FLEX_POS:
            flex_occ.append(p)
    bench = [p for p in roster if str(p["sleeper_id"]) not in opt_ids
             and p["pos"] in FLEX_POS and (p.get("weekly") or 0) > 0]
    lines = []
    for f in flex_occ[-flex:] if (flex_occ and flex) else []:
        rivals = [b for b in bench
                  if abs((b.get("weekly") or 0) - (f.get("weekly") or 0)) <= COINFLIP]
        if not rivals:
            lines.append(f"FLEX **{f['name']}** ({f.get('weekly', 0):.1f}) — clear, no one within {COINFLIP} pts")
            continue
        alt = max(rivals, key=lambda b: b.get("stdev", 5.0) if mode == "ceiling"
                  else -b.get("stdev", 5.0))
        if mode == "ceiling" and alt.get("stdev", 5) > f.get("stdev", 5):
            lines.append(f"FLEX coin flip: **{alt['name']}** over {f['name']} — "
                         f"ceiling mode wants the higher-variance play")
        elif mode == "floor" and alt.get("stdev", 5) < f.get("stdev", 5):
            lines.append(f"FLEX coin flip: **{alt['name']}** over {f['name']} — "
                         f"floor mode protects the lead")
        else:
            lines.append(f"FLEX **{f['name']}** ({f.get('weekly', 0):.1f}) over "
                         f"{alt['name']} ({alt.get('weekly', 0):.1f}) — projection edge, "
                         f"mode does not flip it")
    return lines


def build(ctx, store) -> str:
    week = ctx["week"]
    # Consensus BEFORE the optimiser: re-basing projections after the lineup
    # is chosen would show numbers that did not pick it.
    con, con_notes = consensus.build(ctx, store)
    if con and (ctx.get("scfg") or {}).get("consensus_projections", True):
        _n, _notes = consensus.apply(ctx, con)
        con_notes += _notes
    # A warning filed into a collapsed footer is a warning that is gone.
    # BOTH MARKERS. Filtering on the warning glyph alone dropped every
    # "DATA MISSING:" line, so a total projection outage rendered a brief
    # with no warning at all -- the same way the clamp warning went
    # missing on 2026-09-08 for want of a colon.
    con_warnings = [n for n in con_notes
                    if n.startswith("⚠") or n.startswith("DATA MISSING")]

    totals, v_note = implied_totals(store, window=week_window(ctx),
                                    season=(ctx.get("state") or {}).get("season"),
                                    week=ctx["week"])
    roster = vegas_adjust(ctx["roster_players"].get(ctx["my_rid"], []), totals)
    optimal = optimal_lineup(roster, ctx["slots"], flex_slots=ctx["flex_slots"])

    scout = store.get(f"scout:{week}", {})
    margin = scout.get("margin")
    if margin is None:
        mode, mode_why = "neutral", "no scout margin yet — projection decides everything"
    elif margin <= -10:
        mode, mode_why = "ceiling", f"projected down {-margin:.0f} — chase variance in coin flips"
    elif margin >= 10:
        mode, mode_why = "floor", f"projected up {margin:.0f} — protect the lead in coin flips"
    else:
        mode, mode_why = "neutral", f"margin {margin:+.0f} is close — projection decides"

    swaps, _total = lineup_changes(roster, ctx["current_starters"], ctx["slots"], flex_slots=ctx["flex_slots"])

    table = contingency_table(roster, optimal)
    store.set(f"contingency:{week}", table)

    lines = [f"# Lineup — week {week} ({mode.upper()} mode: {mode_why})", ""]
    if ctx.get("fallback"):
        lines.append("⚠ projections not yet published — season-baseline fallback values")
    if v_note:
        lines.append(f"⚠ {v_note}")
    for n in con_warnings:
        lines.append(n)
    lines.append("")
    lines.append("## Start (optimal)")
    for p in sorted(optimal, key=lambda x: -(x.get("weekly") or 0)):
        v = f" · {p['vegas']}" if p.get("vegas") else ""
        flag = f" · {p['status']}" if p.get("status") else ""
        lines.append(f"- {p['name']} ({p['pos']}) {p.get('weekly', 0):.1f}{v}{flag}")
    if swaps:
        lines += ["", "## Changes from your current lineup"]
        lines += [f"- **{c}**" for c in swaps]
    else:
        lines += ["", "current Sleeper lineup already matches — no taps needed"]
    lines += ["", "## The decisions that matter"]
    lines += [f"- {l}" for l in flex_analysis(roster, optimal, mode, ctx["slots"], ctx["flex"])] or ["- none this week"]

    # HOW FIRM IS THE GROUND. A swap worth less than the sources' own
    # disagreement about the two players is noise wearing a decimal point,
    # and the brief used to present it with the same confidence as a real
    # edge. Flagged, never suppressed: the call is still yours.
    if swaps:
        shaky = []
        by_name = {p["name"]: p for p in roster}
        for c in swaps:
            gain = 0.0
            if "(+" in c:
                try:
                    gain = float(c.split("(+", 1)[1].split(" ", 1)[0])
                except (IndexError, ValueError):
                    gain = 0.0
            named = [n for n in by_name if n in c]
            rows = [con.get(str(by_name[n]["sleeper_id"])) for n in named]
            worst = max((r.get("spread", 0.0) for r in rows if r), default=0.0)
            if rows and any(rows) and not consensus.confident(
                    {"n": 2, "spread": worst}, gain):
                shaky.append(f"{c} — sources disagree by {worst:.0f} on these two, "
                             f"which is more than the {gain:.1f} the swap gains")
        if shaky:
            lines += ["", "## Close enough to be a coin flip"]
            lines += [f"- {t}" for t in shaky]
    if table:
        lines += ["", "## If inactive → start"]
        lines += [f"- {k} → {v}" for k, v in table.items()]

    srcs = {}
    for n in con_notes:
        if n.startswith("consensus"):
            srcs["consensus"] = n.split("consensus ", 1)[-1]
        elif ":" in n:
            k, v = n.split(":", 1)
            v = v.strip()
            srcs[k.strip()] = v[len(k) + 1:].strip() if v.startswith(k.strip()) else v
    if v_note:
        srcs["vegas"] = v_note
    lines += ["", provenance.render(provenance.stamp(ctx, srcs))]
    return "\n".join(lines)

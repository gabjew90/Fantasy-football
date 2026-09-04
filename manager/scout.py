"""Module 4 — opponent scout (Friday noon PT).

Projected margin + win probability under documented variance assumptions,
their forced bad starts (bye/injury holes), and the ceiling/floor mode flag
Module 3 consumes.
"""

from __future__ import annotations

import logging
import math

from draftkit.lineup import optimal_lineup

from .lineup_opt import STDEV, vegas_adjust
from .vegas import implied_totals

log = logging.getLogger("manager")


def win_probability(margin: float, variance: float) -> float:
    if variance <= 0:
        return 0.5
    return 0.5 * (1 + math.erf(margin / math.sqrt(2 * variance)))


def build(ctx, store) -> str:
    week = ctx["week"]
    if ctx["opp_rid"] is None:
        return f"# Opponent scout — week {week}\n\nno matchup this week."
    totals, v_note = implied_totals(store)
    mine = vegas_adjust(ctx["roster_players"][ctx["my_rid"]], totals)
    theirs = vegas_adjust(ctx["roster_players"][ctx["opp_rid"]], totals)
    my_opt = optimal_lineup(mine, ctx["slots"], ctx["flex_slots"])
    their_opt = optimal_lineup(theirs, ctx["slots"], ctx["flex_slots"])
    my_total = sum(p.get("weekly") or 0 for p in my_opt)
    their_total = sum(p.get("weekly") or 0 for p in their_opt)
    margin = my_total - their_total
    variance = sum(STDEV.get(p.get("pos"), 5.0) ** 2 for p in my_opt + their_opt)
    wp = win_probability(margin, variance)

    # forced bad starts: slots they can only fill with hurt/bye players
    holes = []
    filled = {str(p["sleeper_id"]) for p in their_opt}
    for p in their_opt:
        if (p.get("status") or "") in ("Out", "Doubtful", "Questionable"):
            holes.append(f"{p['name']} ({p['pos']}) is {p['status']} and they lack a clean pivot")
        if (p.get("weekly") or 0) == 0:
            holes.append(f"{p['name']} ({p['pos']}) projects ZERO (bye/inactive) — forced start")
    n_starters = ctx["shape"].n_starters
    if len(their_opt) < n_starters:
        holes.append(f"they can only fill {len(their_opt)}/{n_starters} slots")

    mode = "ceiling" if margin <= -10 else ("floor" if margin >= 10 else "neutral")
    store.set(f"scout:{week}", {"margin": round(margin, 1), "win_prob": round(wp, 3),
                                "mode": mode})

    lines = [
        f"# Opponent scout — week {week}: {ctx['opp_name']}",
        "",
        f"**you {my_total:.1f} — {their_total:.1f} them · margin {margin:+.1f} · "
        f"win probability {wp:.0%}**",
        f"(variance model: weekly stdev by position {STDEV}; normal margin)",
        "",
    ]
    if v_note:
        lines.append(f"⚠ {v_note}")
    if ctx.get("fallback"):
        lines.append("⚠ projections not yet published — season-baseline fallback values")
    lines.append(f"## Mode for Sunday: **{mode.upper()}**")
    lines.append({"ceiling": "big underdog — prefer high-variance plays in coin flips",
                  "floor": "solid favorite — prefer floor plays in coin flips",
                  "neutral": "close matchup — projection decides coin flips"}[mode])
    if holes:
        lines += ["", "## Their holes"] + [f"- {h}" for h in holes]
    else:
        lines += ["", "no forced bad starts on their side this week"]
    return "\n".join(lines)

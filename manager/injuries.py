"""Module 2 — inactives / injury monitor.

Twice-daily sweeps alert only on CHANGES (diffed against SQLite state).
Per-slate checks at inactives time turn a starter going down into one line:
"Bench X, start Y" with minutes to lock, using Module 3's precomputed
contingency table.
"""

from __future__ import annotations

import logging
from datetime import datetime

from .clock import minutes_until

log = logging.getLogger("manager")

BAD = ("Out", "IR", "Doubtful", "Suspended", "Inactive", "PUP")


def sweep_changes(ctx, store) -> list[dict]:
    """Designation CHANGES for my rostered players since the last sweep, as
    structured rows: {pid, name, pos, old, new, note}. Each change alerts
    once (seen-gate on pid + status); the snapshot advances every call."""
    mine = ctx["roster_players"].get(ctx["my_rid"], [])
    players = ctx.get("players") or {}
    current = {str(p["sleeper_id"]): (p.get("status") or "") for p in mine}
    prev = store.get("inj_snapshot", {})
    out = []
    for pid, status in current.items():
        old = prev.get(pid, "")
        if status == old:
            continue
        p = next(x for x in mine if str(x["sleeper_id"]) == pid)
        if store.first_time(f"inj:{pid}:{status}"):
            d = players.get(pid) if isinstance(players.get(pid), dict) else {}
            note = d.get("injury_body_part") or p.get("injury_note") or ""
            out.append({"pid": pid, "name": p["name"], "pos": p["pos"],
                        "old": old, "new": status, "note": note})
    store.set("inj_snapshot", current)
    return out


def sweep(ctx, store) -> list[str]:
    """Designation CHANGES for my rostered players since the last sweep."""
    alerts = []
    for c in sweep_changes(ctx, store):
        status, old = c["new"], c["old"]
        arrow = f"{old or 'healthy'} -> {status or 'healthy'}"
        mark = "🔴" if status in BAD else ("🟢" if not status else "🟡")
        alerts.append(f"{mark} **{c['name']}** ({c['pos']}): {arrow}")
    return alerts


def slate_check(ctx, store, slate_teams: list[str],
                kickoff: datetime) -> list[str]:
    """At inactives time: any of my starters in this slate now Out/Inactive ->
    a concrete instruction with the precomputed replacement."""
    contingency = store.get(f"contingency:{ctx['week']}", {})
    mins = minutes_until(kickoff)
    mine = {str(p["sleeper_id"]): p for p in ctx["roster_players"].get(ctx["my_rid"], [])}
    out_lines = []
    for pid in ctx["current_starters"]:
        p = mine.get(str(pid))
        if not p or p.get("team") not in set(slate_teams):
            continue
        status = p.get("status") or ""
        if status in ("Out", "Inactive", "Doubtful", "Suspended"):
            repl = contingency.get(p["name"]) or "best healthy bench player at the position"
            aid = f"slate:{ctx['week']}:{pid}:{status}"
            if store.first_time(aid):
                out_lines.append(
                    f"🔴 **{p['name']} is {status}. Bench {p['name']}, start {repl}.** "
                    f"{mins} minutes until lock.")
    return out_lines

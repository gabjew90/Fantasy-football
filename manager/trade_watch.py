"""Watch OTHER managers' trades — every pending trade is a decision I have
to make: 6-of-12 veto votes, 2-day review window. A lopsided deal sliding
through review unseen costs as much as a missed waiver.

Runs inside the twice-daily sweeps and the daily healthcheck (worst-case
detection latency ~24h against the 48h window). Each trade alerts exactly
once per status (pending -> completed re-alerts) via the seen-gate.
"""

from __future__ import annotations

import logging

from .trade_radar import values

log = logging.getLogger("manager")

LOPSIDED = 0.7  # same ratio the radar uses for veto risk


def scan(ctx, store) -> list[tuple[str, str, bool]]:
    """New trade events -> [(subject, body, urgent)]."""
    from draftkit.briefs import get_transactions

    week = max(1, ctx["week"])
    try:
        txns = get_transactions(ctx["client"], ctx["cfg"].league_id, week)
    except Exception:  # noqa: BLE001
        log.warning("trade watch: transactions fetch failed")
        return []
    trades = [t for t in txns if t.get("type") == "trade"]
    if not trades:
        return []

    vals, _note = values(store)
    out = []
    for t in trades:
        tid = t.get("transaction_id", "?")
        status = t.get("status", "?")
        if not store.first_time(f"trade:{tid}:{status}"):
            continue

        # adds: player_id -> receiving roster_id
        sides: dict[int, list[str]] = {}
        for pid, rid in (t.get("adds") or {}).items():
            sides.setdefault(int(rid), []).append(str(pid))
        totals: dict[int, int] = {}
        lines = []
        for rid, pids in sides.items():
            mgr = ctx["users_by_rid"].get(rid, f"roster {rid}")
            names = []
            total = 0
            for pid in pids:
                row = ctx["player_row"](pid)
                name = row["name"] if row else pid
                v = vals.get(pid, 0)
                total += v
                names.append(f"{name} ({v})" if v else name)
            totals[rid] = total
            lines.append(f"- **{mgr}** receives: {', '.join(names)}"
                         + (f" — value {total}" if total else ""))
        picks = t.get("draft_picks") or []
        if picks:
            lines.append(f"- plus {len(picks)} draft pick(s) moving")

        verdict = ""
        tvals = [v for v in totals.values() if v > 0]
        if len(tvals) == 2 and min(tvals) > 0:
            ratio = min(tvals) / max(tvals)
            verdict = (f"\nvalue ratio {ratio:.2f} — "
                       + ("**LOPSIDED — consider your veto vote**" if ratio < LOPSIDED
                          else "within normal range, no veto case"))
        involved = " ↔ ".join(ctx["users_by_rid"].get(r, str(r)) for r in sides)
        if status == "complete":
            subject = f"Trade completed: {involved}"
            urgent = False
            tail = "\n(already processed — for your information)"
        else:
            subject = f"Trade pending review: {involved} — veto window ~2 days"
            urgent = True
            tail = ("\n2-day review window is running; 6 of 12 votes kill it. "
                    "Vote in Sleeper if this deal hurts your title odds.")
        out.append((subject, "\n".join(lines) + verdict + tail, urgent))
    return out

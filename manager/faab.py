"""FAAB accounting from league transaction history.

The roster `waiver_budget_used` field is authoritative for remaining budget;
this reconstruction from completed waiver claims powers the per-rival spend
detail and cross-checks the field (a mismatch is reported, never hidden).
"""

from __future__ import annotations


def spent_from_transactions(txns_by_week: list[list[dict]]) -> dict[int, int]:
    """roster_id -> total FAAB spent, from completed waiver claims."""
    spent: dict[int, int] = {}
    for week_txns in txns_by_week:
        for t in week_txns or []:
            if t.get("type") != "waiver" or t.get("status") != "complete":
                continue
            bid = int((t.get("settings") or {}).get("waiver_bid") or 0)
            if bid <= 0:
                continue
            # the winning roster is the one credited with the adds
            adds = t.get("adds") or {}
            rids = {int(v) for v in adds.values()} or {int(r) for r in (t.get("roster_ids") or [])}
            for rid in rids:
                spent[rid] = spent.get(rid, 0) + bid
    return spent


def crosscheck(spent: dict[int, int], rosters: list[dict]) -> list[str]:
    """Lines describing any disagreement between txn history and the field."""
    notes = []
    for r in rosters:
        rid = int(r["roster_id"])
        field = int((r.get("settings") or {}).get("waiver_budget_used") or 0)
        hist = spent.get(rid, 0)
        if field != hist:
            notes.append(f"FAAB cross-check: roster {rid} field says ${field} "
                         f"spent, transactions sum to ${hist} — using the field.")
    return notes

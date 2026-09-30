"""Sleeper's trending adds and drops: how many of its leagues added or dropped
a player in the last 24 hours, NFL-wide.

This is the waiver command's timing signal. The gain says what an add is
worth; the trending count says whether he will still be there next week.
Ollie Gordon was added in 6.4 million Sleeper leagues the day after Achane's
injury -- a now-or-never claim -- and the report priced him like any other
add (2026-09-30). No probability is modelled here: the count and the
player's rank in the list are shown as they are, and the top of the list is
called what it is, likely gone after this waiver period.
"""

from __future__ import annotations

import json

from core import fetch as F

LIMIT = 100                 # rows read per list (Sleeper serves up to this many)
GONE_RANK = 25              # a top-25 trending add is called "likely gone after this waiver period"


def load(manifest=None) -> dict:
    """{"add": {sid: count}, "drop": {sid: count}, "rank": {"add": {sid: rank}, "drop": {...}},
    "note": None | why a list is missing}. A list that cannot be read is an
    empty dict with the reason in `note` (and FAILED in the manifest) -- the
    report says trending was unavailable rather than showing every add as
    unclaimed."""
    out: dict = {"add": {}, "drop": {}, "rank": {"add": {}, "drop": {}}, "note": None}
    notes = []
    for kind in ("add", "drop"):
        try:
            rows = json.loads(F.sleeper_trending(kind, manifest=manifest, limit=LIMIT).read_text(encoding="utf-8"))
        except Exception as ex:  # noqa: BLE001 -- context, never fatal; the manifest holds the failure
            notes.append(f"Sleeper trending {kind}s unavailable ({type(ex).__name__})")
            continue
        for i, r in enumerate(rows or [], 1):
            sid = str(r.get("player_id"))
            out[kind][sid] = int(r.get("count") or 0)
            out["rank"][kind][sid] = i
    out["note"] = "; ".join(notes) or None
    return out


def fmt_count(n: int) -> str:
    """6351247 -> '6.4M'; 21159 -> '21k'; 812 -> '812'."""
    n = int(n)
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}k"
    return str(n)


def cell(sid: str, tr: dict, kind: str = "add") -> str:
    """The table cell: '6.4M (#1)' or '--'."""
    n = (tr.get(kind) or {}).get(sid)
    if n is None:
        return "--"
    return f"{fmt_count(n)} (#{tr['rank'][kind][sid]})"


def line(sid: str, tr: dict) -> str | None:
    """The player tool's sentence, or None when he is on neither list."""
    parts = []
    for kind, verb in (("add", "added"), ("drop", "dropped")):
        n = (tr.get(kind) or {}).get(sid)
        if n is not None:
            rank = tr["rank"][kind][sid]
            parts.append(f"{verb} in {fmt_count(n)} Sleeper leagues in the last 24 hours (#{rank} of trending {kind}s"
                         + (", likely gone after this waiver period" if kind == "add" and rank <= GONE_RANK else "")
                         + ")")
    if not parts:
        return None
    return "Sleeper trending: " + "; ".join(parts) + "."


def likely_gone(sids, tr: dict) -> list[str]:
    """Of `sids`, the ones in the top GONE_RANK trending adds, hottest first."""
    rank = tr.get("rank", {}).get("add") or {}
    return sorted((s for s in sids if rank.get(s, 10 ** 6) <= GONE_RANK), key=lambda s: rank[s])

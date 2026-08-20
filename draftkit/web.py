"""Phase 5 — local web dashboard. Display plumbing only: all draft logic
lives in Tracker; this module serializes it to JSON and serves one page."""

from __future__ import annotations

import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import snake
from .tracker import Tracker

POS_ORDER = ["RB", "WR", "TE", "QB", "K", "DEF"]
STARTER_KEYS = ("QB", "RB", "WR", "TE", "FLEX", "K", "DEF")


def build_state(t: Tracker) -> dict:
    """One JSON-safe snapshot of everything the dashboard renders."""
    s = t.state
    cur = t.current_pick
    total = t.teams * t.rounds
    rnd, slot_on_clock = snake.pick_to_round_slot(min(cur, total), t.teams)
    on_clock_me = t.my_slot is not None and slot_on_clock == t.my_slot and s.status == "drafting"

    my_next = None
    picks_away = None
    if t.my_slot:
        my_next = snake.next_pick_for_slot(cur, t.my_slot, t.teams, t.rounds)
        if my_next is not None:
            picks_away = my_next - cur

    cliff = t.cliff_report()
    board = []
    for pos in POS_ORDER:
        rem = t.remaining(pos)[:3]
        players = []
        for p in rem:
            d = None
            if p.get("adp") is not None:
                d = round(cur - p["adp"])
            players.append({
                "player": p["player"], "tier": p["tier"],
                "vorp": round(p["vorp"] or 0.0, 1),
                "adp_delta_live": d, "cliff": bool(p["cliff_flag"]),
            })
        c = cliff.get(pos, {})
        board.append({
            "pos": pos, "players": players,
            "before_cliff": c.get("before_cliff"),
            "demand": c.get("intervening_demand", 0),
            "urgent": bool(c.get("urgent")),
        })

    recs = []
    if t.my_slot:
        for score, why, p in t.recommendations():
            recs.append({
                "player": p["player"], "pos": p["pos"], "pos_rank": p["pos_rank"],
                "tier": p["tier"], "vorp": round(p["vorp"] or 0.0, 1), "why": why,
            })

    roster = None
    if t.my_slot:
        needs = t.my_needs()
        my_pos = t.slot_positions(t.my_slot)
        filled = {k: t.slots[k] - needs.get(k, 0) for k in STARTER_KEYS}
        bench_used = max(0, len(my_pos) - sum(filled.values()))
        drafted = [
            (t.by_id.get(str(p["player_id"]), {}).get("player")
             or f"{(p.get('metadata') or {}).get('first_name', '?')} "
                f"{(p.get('metadata') or {}).get('last_name', '')}".strip())
            for p in t.picks_for_slot(t.my_slot)
        ]
        roster = {
            "filled": filled,
            "slots": {k: t.slots[k] for k in STARTER_KEYS},
            "bench_used": bench_used, "bench_total": t.slots.get("BN", 0),
            "drafted": drafted,
        }

    fallers = [
        {"player": p["player"], "pos": p["pos"], "adp": round(p["adp"]),
         "fell": round(cur - p["adp"])}
        for p in t.fallers()
    ]

    return {
        "ok": True,
        "draft_id": t.draft_id,
        "status": s.status,
        "current_pick": cur,
        "round": rnd,
        "pick_in_round": (cur - 1) % t.teams + 1,
        "on_clock_slot": slot_on_clock,
        "on_clock_me": on_clock_me,
        "my_slot": t.my_slot,
        "my_next_pick": my_next,
        "picks_away": picks_away,
        "recommendations": recs,
        "board": board,
        "roster": roster,
        "fallers": fallers,
        "poll_error": s.last_error,
        "last_poll_age_s": round(time.time() - s.last_poll_ok) if s.last_poll_ok else None,
    }

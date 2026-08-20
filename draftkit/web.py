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


class DraftWebApp:
    """Owns Tracker instances (one per draft id) and rate-limits polling.

    No threads: /state polls Sleeper at most once per poll_seconds per draft,
    driven by browser requests. Clearing the cache (reload) is always safe —
    Tracker rebuilds full state from the picks list on the next poll.
    """

    def __init__(self, cfg, tiers_path, default_slot):
        self.cfg = cfg
        self.tiers_path = tiers_path
        self.default_slot = default_slot
        self._trackers: dict[str, Tracker] = {}
        self._last_poll: dict[str, float] = {}

    def _tracker(self, draft_id: str, slot: int | None) -> Tracker:
        if draft_id not in self._trackers:
            if slot is None:
                slot = self.default_slot if draft_id == self.cfg.draft_id else 2
            self._trackers[draft_id] = Tracker(
                self.cfg, tiers_path=self.tiers_path,
                draft_id=draft_id, my_slot=slot,
            )
        return self._trackers[draft_id]

    def state_for(self, draft_id: str, slot: int | None) -> dict:
        try:
            t = self._tracker(draft_id, slot)
        except Exception as e:  # bad mock id, Sleeper down at creation, etc.
            return {"ok": False, "error": f"could not open draft {draft_id}: {e}"[:200]}
        now = time.monotonic()
        if now - self._last_poll.get(draft_id, 0.0) >= t.poll_seconds:
            self._last_poll[draft_id] = now
            t.poll()
        state = build_state(t)
        state["tiers_built_at"] = self.tiers_mtime()
        return state

    def reload(self) -> None:
        """Forget all trackers; next request re-reads tiers.csv and rebuilds."""
        self._trackers.clear()
        self._last_poll.clear()

    def tiers_mtime(self) -> str | None:
        try:
            mt = self.tiers_path.stat().st_mtime
        except OSError:
            return None
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(mt))


def run_server(cfg, tiers_path, default_slot: int | None, port: int) -> int:
    """Serve the dashboard. Returns process exit code (3 = port already in use)."""
    from .web_page import PAGE

    app = DraftWebApp(cfg, tiers_path, default_slot)

    class Handler(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            url = urlparse(self.path)
            if url.path == "/":
                self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
            elif url.path == "/state":
                q = parse_qs(url.query)
                draft_id = (q.get("draft_id") or [cfg.draft_id])[0].strip() or cfg.draft_id
                slot_raw = (q.get("slot") or [""])[0].strip()
                slot = int(slot_raw) if slot_raw.isdigit() else None
                body = json.dumps(app.state_for(draft_id, slot)).encode("utf-8")
                self._send(200, body, "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):  # noqa: N802
            if urlparse(self.path).path == "/reload":
                app.reload()
                self._send(200, b'{"ok": true}', "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, fmt, *args):  # keep the console quiet
            pass

    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError:
        print(f"draftkit web: port {port} already in use — dashboard is already "
              f"running at http://localhost:{port}")
        return 3
    print(f"draftkit dashboard: http://localhost:{port}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0

"""Phase 5 — local web dashboard. Display plumbing only: all draft logic
lives in Tracker; this module serializes it to JSON and serves one page."""

from __future__ import annotations

import json
import threading
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

    local = bool(getattr(t, "local", False))
    all_remaining = None
    if local:
        all_remaining = [
            {"n": p["player"], "p": p["pos"]}
            for p in sorted(t.remaining(), key=lambda x: x.get("adp") or 999.0)
        ]

    return {
        "ok": True,
        "local": local,
        "all_remaining": all_remaining,
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

    ThreadingHTTPServer serves each request on its own thread, so all shared
    state (tracker cache, poll gate, tracker/draftlog mutation) is serialized
    behind one lock — build_state is cheap and polling is rate-limited, so
    serializing requests costs nothing observable.
    """

    def __init__(self, cfg, tiers_path, default_slot):
        self.cfg = cfg
        self.tiers_path = tiers_path
        self.default_slot = default_slot
        self._trackers: dict[str, Tracker] = {}
        self._last_poll: dict[str, float] = {}
        self._lock = threading.Lock()

    def _tracker(self, draft_id: str, slot: int | None) -> Tracker:
        if draft_id not in self._trackers:
            if slot is None:
                # unknown drafts start as spectator — a silent wrong-seat
                # default is worse than prompting for the slot in the footer
                slot = self.default_slot if draft_id == self.cfg.draft_id else None
            self._trackers[draft_id] = Tracker(
                self.cfg, tiers_path=self.tiers_path,
                draft_id=draft_id, my_slot=slot,
            )
        t = self._trackers[draft_id]
        # honor a slot change on an already-cached tracker (footer "apply")
        if slot is not None and t.my_slot != slot:
            t.my_slot = slot
            t._urgency_cache = None
        return t

    def state_for(self, draft_id: str, slot: int | None) -> dict:
        with self._lock:
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

    def local_action(self, draft_id: str, slot, action: str,
                     name: str = "", pos: str = "") -> dict:
        """Manual-entry writes for LOCAL drafts only (Yahoo draft day)."""
        with self._lock:
            try:
                t = self._tracker(draft_id, slot)
            except Exception as e:  # noqa: BLE001
                return {"ok": False, "error": str(e)[:200]}
            if not getattr(t, "local", False):
                return {"ok": False, "error": "not a local draft — picks come from Sleeper"}
            if action == "pick":
                out = t.source.add_pick(name, pos or None)
            elif action == "undo":
                out = t.source.undo()
            else:
                return {"ok": False, "error": f"unknown action {action}"}
            self._last_poll[draft_id] = 0.0  # next /state re-polls immediately
            return out

    def reload(self) -> None:
        """Forget all trackers; next request re-reads tiers.csv and rebuilds."""
        with self._lock:
            self._trackers.clear()
            self._last_poll.clear()

    def tiers_mtime(self) -> str | None:
        try:
            mt = self.tiers_path.stat().st_mtime
        except OSError:
            return None
        return time.strftime("%Y-%m-%d %H:%M", time.localtime(mt))


def render_log_html(log_path, draft_id: str) -> str:
    """Server-rendered play-by-play review page from the JSONL draft log."""
    import html as _html

    rows = []
    if log_path.exists():
        for line in log_path.read_text(encoding="utf-8").splitlines():
            try:
                e = json.loads(line)
            except ValueError:
                continue
            at = _html.escape(e.get("at", ""))
            if e["type"] == "status":
                rows.append(f'<div class="ev status">{at} — draft status: '
                            f'{_html.escape(str(e.get("status")))}</div>')
            elif e["type"] == "pick":
                name = _html.escape(str(e.get("player")))
                pos = _html.escape(str(e.get("pos") or "?"))
                tier = e.get("tier")
                vorp = e.get("vorp")
                vs = e.get("vs_adp")
                bits = [pos]
                if tier is not None:
                    bits.append(f"T{tier}")
                if vorp is not None:
                    bits.append(f"VORP {vorp:.0f}")
                if vs is not None:
                    bits.append(f"{'+' if vs >= 0 else ''}{vs:.0f} vs ADP")
                cls = "ev pick mine" if e.get("my_pick") else "ev pick"
                tag = " <b>← MY PICK</b>" if e.get("my_pick") else ""
                rows.append(
                    f'<div class="{cls}">{at} — <b>P{e["pick_no"]}</b> '
                    f'R{e["round"]} slot {e["slot"]}: <b>{name}</b> '
                    f'({", ".join(bits)}){tag}</div>'
                )
            elif e["type"] == "recs":
                recs = e.get("recommendations") or []
                items = "".join(
                    f'<li><b>{_html.escape(str(r["player"]))}</b> '
                    f'({_html.escape(str(r["pos"]))}, T{r["tier"]}, VORP {r["vorp"]:.0f}) '
                    f'— {_html.escape(str(r["why"]))}</li>'
                    for r in recs
                )
                rows.append(
                    f'<div class="ev recs">{at} — engine before pick '
                    f'{e["current_pick"]}:<ol>{items}</ol></div>'
                )
    body = "\n".join(rows) or "<p>No log yet — events appear once polling starts.</p>"
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>draftkit log</title>
<style>
  body {{ background: #0d1117; color: #e6edf3; font: 15px/1.5 "Segoe UI", system-ui, sans-serif;
         max-width: 1000px; margin: 0 auto; padding: 18px; }}
  h1 {{ font-size: 18px; color: #8b949e; }}
  .ev {{ padding: 5px 10px; border-left: 3px solid #30363d; margin: 3px 0; }}
  .ev.status {{ color: #d29922; border-color: #d29922; }}
  .ev.pick.mine {{ background: #172554; border-color: #58a6ff; }}
  .ev.recs {{ color: #8b949e; border-color: #21262d; font-size: 13.5px; }}
  .ev.recs ol {{ margin: 2px 0 2px 22px; }}
  .ev.recs b {{ color: #e6edf3; }}
</style></head><body>
<h1>Play-by-play — draft {_html.escape(draft_id)}</h1>
{body}
</body></html>"""


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
            elif url.path == "/log":
                q = parse_qs(url.query)
                draft_id = (q.get("draft_id") or [cfg.draft_id])[0].strip() or cfg.draft_id
                # a local draft tracker rewrites its id to local_<league>;
                # the raw query value ("None" for a yaml draft_id: null) points
                # at a file that never exists (code review 2026-08-31)
                if (str(draft_id).lower() in ("", "none", "null")
                        or str(draft_id).startswith("local")):
                    draft_id = f"local_{cfg.league_name or 'draft'}"
                log_path = cfg.path("logs") / f"draft_{draft_id}.jsonl"
                page = render_log_html(log_path, draft_id)
                self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            elif url.path == "/brief":
                import html as _html
                parts = []
                for fname in ("waiver_brief.md", "early_check.md", "lineup_brief.md"):
                    fp = cfg.root / "reports" / fname
                    if fp.exists():
                        mt = time.strftime("%a %H:%M", time.localtime(fp.stat().st_mtime))
                        body = _html.escape(fp.read_text(encoding="utf-8"))
                        parts.append(f"<h2 style='color:#8b949e'>{fname} <small>({mt})</small></h2>"
                                     f"<pre style='white-space:pre-wrap;font:14px/1.5 Segoe UI'>{body}</pre>")
                page = ("<!DOCTYPE html><html><head><meta charset='utf-8'><title>briefs</title></head>"
                        "<body style='background:#0d1117;color:#e6edf3;max-width:900px;margin:0 auto;padding:18px'>"
                        + ("".join(parts) or "<p>no briefs rendered yet</p>") + "</body></html>")
                self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
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
            url = urlparse(self.path)
            if url.path == "/reload":
                app.reload()
                self._send(200, b'{"ok": true}', "application/json")
            elif url.path in ("/pick", "/undo"):
                q = parse_qs(url.query)
                draft_id = (q.get("draft_id") or [cfg.draft_id])[0].strip() or cfg.draft_id
                slot_raw = (q.get("slot") or [""])[0].strip()
                slot = int(slot_raw) if slot_raw.isdigit() else None
                name = (q.get("name") or [""])[0]
                pos = (q.get("pos") or [""])[0]
                out = app.local_action(draft_id, slot,
                                       "pick" if url.path == "/pick" else "undo",
                                       name=name, pos=pos)
                self._send(200, json.dumps(out).encode("utf-8"), "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def log_message(self, fmt, *args):  # keep the console quiet
            pass

    # http.server enables SO_REUSEADDR, which on Windows lets a second bind to
    # an in-use port silently succeed — that would defeat the double-click
    # guard, so disable it (a restarted listener does not need it here).
    class ExclusiveServer(ThreadingHTTPServer):
        allow_reuse_address = False

    try:
        server = ExclusiveServer(("127.0.0.1", port), Handler)
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

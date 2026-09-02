"""Serve the real engine to the Yahoo draft page over local TLS.

The page cannot reach a plain-http local server: Chrome silently drops an
HTTPS page's cross-origin request to http://127.0.0.1 -- verified with an
instrumented server that logged curl's hit and nothing at all from Chrome,
and the fetch promise never settles rather than rejecting. Over TLS the same
request fails in 126ms with a normal certificate error, which is fixable.

So the page POSTs its draft state here and gets back
draftkit/tracker.py's own recommendations, live, with no staleness and no
second ranking implementation to drift.

Setup (once):
    python scripts/bridge_server.py --league keefamania
    # then open https://127.0.0.1:8443/ping in the same Chrome profile and
    # accept the certificate. It is leaf-only (CA:FALSE), valid for
    # localhost alone, and expires in 14 days.
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import threading
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import yahoo_bridge as YB  # noqa: E402
from draftkit.config import Config  # noqa: E402

TLS_DIR = ROOT / "data" / "draftrig" / "tls"
_LOCK = threading.Lock()
_STATE = {"cfg": None, "players": None, "league": None, "calls": 0}


def build_plan(state: dict, depth: int) -> dict:
    with _LOCK:
        cfg, players = _STATE["cfg"], _STATE["players"]
        # The bridge outlives page reloads; the Picks panel does not. Keep the
        # union of every view of the feed per draft (yahoo_bridge.merge_feed).
        feed_key = str(state.get("draft_key") or f"{state.get('teams')}x{state.get('my_slot')}")
        memory = _STATE.setdefault("feed", {}).setdefault(feed_key, {})
        state = dict(state, drafted=YB.merge_feed(memory, state.get("drafted") or []))
        t = YB.build_tracker(cfg, players, state)
        recs = t.recommendations(top_n=depth)
        plan = [{"n": p["name"], "p": p["pos"], "t": p["team"],
                 "v": round(float(p["vorp"] or 0.0), 1), "a": p["adp"],
                 "why": why} for _s, why, p in recs]
        # the tail past the engine's named candidates goes through the same
        # guardrails as everything else (see yahoo_bridge.depth_tail)
        plan = YB.depth_tail(t, plan, depth)
        _STATE["calls"] += 1
        return {"current_pick": t.current_pick, "my_slot": t.my_slot,
                "needs": t.my_needs(), "plan": plan, "calls": _STATE["calls"]}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def _json(self, obj, code=200):
        b = json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(b)))
        self._cors()
        self.end_headers()
        self.wfile.write(b)

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _raw(self, body: bytes, ctype: str, status: int = 200) -> None:
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.startswith("/ping"):
            self._json({"ok": True, "engine": "draftkit.tracker",
                        "league": _STATE["league"], "calls": _STATE["calls"]})
        elif self.path.startswith("/driver.js"):
            # The page loads the driver from here instead of a 60KB paste
            # through a devtools eval. Same origin as /plan, already trusted.
            self._raw((ROOT / "scripts" / "draft_driver.js").read_bytes(),
                      "application/javascript; charset=utf-8")
        elif self.path.startswith("/board.json"):
            p = ROOT / "data" / "draftrig" / f"board.{_STATE['league']}.json"
            if p.exists():
                self._raw(p.read_bytes(), "application/json; charset=utf-8")
            else:
                self._json({"err": f"export the board first: {p.name}"}, 404)
        else:
            self._json({"err": "POST draft state to /plan"}, 404)

    def do_POST(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            state = json.loads(self.rfile.read(n) or b"{}")
            depth = int(state.pop("depth", 25))
            plan = build_plan(state, depth)
            self._json(plan)
            drafted = state.get("drafted") or []
            n_mine = sum(1 for d in drafted if d.get("mine"))
            roster = state.get("my_roster") or []
            head = ", ".join(f"{x['n']} ({x['p']})" for x in (plan.get("plan") or [])[:3])
            # Log the STATE the page handed us, not just that we answered: the
            # third-TE pick of mock 11 was invisible in a log that only said
            # "served". If n_mine is 0 while roster is not, the panel's "You"
            # label was unreadable and the roster fallback is doing the work.
            print(f"  plan #{_STATE['calls']} @pick {plan.get('current_pick')} "
                  f"drafted={len(drafted)} mine={n_mine} roster={len(roster)} "
                  f"needs={plan.get('needs')} -> {head}", flush=True)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            self._json({"err": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, *a):
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default=None)
    ap.add_argument("--port", type=int, default=8443)
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    _STATE["cfg"] = cfg
    _STATE["players"] = YB.load_players(cfg)
    _STATE["league"] = a.league or "default"

    cert, keyf = TLS_DIR / "cert.pem", TLS_DIR / "key.pem"
    if not cert.exists():
        raise SystemExit(f"no certificate at {cert} — see the module docstring")
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(keyf))

    srv = ThreadingHTTPServer(("127.0.0.1", a.port), Handler)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    print(f"engine bridge: https://127.0.0.1:{a.port}  league={_STATE['league']}  "
          f"{len(_STATE['players'])} players", flush=True)
    print(f"accept the cert once at https://127.0.0.1:{a.port}/ping", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()

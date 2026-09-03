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
        page_drafted = len(state.get("drafted") or [])
        state = dict(state, drafted=YB.merge_feed(memory, state.get("drafted") or []))
        t = YB.build_tracker(cfg, players, state)
        # --set knob=value overrides (forward-test rooms, DECISIONS #35 G4):
        # applied after the config so the default never moves before the gate
        for k, v in (_STATE.get("overrides") or {}).items():
            setattr(t, k, v)
        recs = t.recommendations(top_n=depth)
        report = t.urgency_report()
        plan = YB.plan_rows(t, recs, report)
        # the tail past the engine's named candidates goes through the same
        # guardrails as everything else (see yahoo_bridge.depth_tail)
        plan = YB.depth_tail(t, plan, depth)
        _STATE["calls"] += 1
        call = _STATE["calls"]
        # the structured calibration record for this room (plan B1); logging
        # never breaks a plan
        try:
            YB.log_plan(t, recs, report, feed_key, ROOT / "data" / "logs")
            # the scrutiny sidecar: every call, the state received, the full
            # plan and every market's numbers (stress mocks 2026-09-02)
            YB.log_plan_detail(t, recs, report, plan, state, feed_key, ROOT / "data" / "logs",
                               call=call, page_drafted=page_drafted)
        except Exception:  # noqa: BLE001
            traceback.print_exc()
        return {"current_pick": t.current_pick, "my_slot": t.my_slot,
                "needs": t.my_needs(), "plan": plan, "calls": call,
                "warnings": list(getattr(t, "warnings", []) or [])}


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
        elif self.path.startswith("/net_tap.js"):
            # instrumentation only: learn how the draft client receives picks
            self._raw((ROOT / "scripts" / "net_tap.js").read_bytes(),
                      "application/javascript; charset=utf-8")
        elif self.path.startswith("/prerank.js"):
            # layer 0: the Edit Pre-Draft Ranks driver (scripts/prerank_driver.js)
            self._raw((ROOT / "scripts" / "prerank_driver.js").read_bytes(),
                      "application/javascript; charset=utf-8")
        elif self.path.startswith("/fingerprint.json"):
            # the store structure captured in the mock rooms; preflight diffs
            # the league room against it (draft-day data-shape check)
            p = ROOT / "data" / "draftrig" / "store_fingerprint.json"
            if p.exists():
                self._raw(p.read_bytes(), "application/json; charset=utf-8")
            else:
                self._json({"err": "no fingerprint captured yet: POST /fingerprint from a mock room"}, 404)
        elif self.path.startswith("/board.json"):
            p = ROOT / "data" / "draftrig" / f"board.{_STATE['league']}.json"
            if p.exists():
                self._raw(p.read_bytes(), "application/json; charset=utf-8")
            else:
                self._json({"err": f"export the board first: {p.name}"}, 404)
        else:
            self._json({"err": "POST draft state to /plan"}, 404)

    def _read_json(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n) or b"{}")

    def _save_named(self, body: dict, key: str, folder: Path, suffix: str, content: str, label: str,
                    prefix: str = "") -> None:
        """One body -> one file named by prefix + a sanitised body[key]; the
        two page-to-disk routes below share it. (The trail used to land as
        <room>.json while scripts/mock_trail.py reads mock_<room>.json --
        found when the first automatic trail posted, 2026-09-02.)"""
        name = "".join(c for c in str(body.get(key) or label) if c.isalnum() or c in "-_.")[:80]
        if prefix and name.startswith(prefix):
            prefix = ""
        out = folder / f"{prefix}{name}{suffix}"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        print(f"  {label} saved -> {out} ({out.stat().st_size} bytes)", flush=True)
        self._json({"ok": True, "path": str(out), "bytes": out.stat().st_size})

    def do_POST(self):
        if (self.path.startswith("/trail") or self.path.startswith("/fixture")
                or self.path.startswith("/players") or self.path.startswith("/fingerprint")):
            try:
                body = self._read_json()
                if self.path.startswith("/fingerprint"):
                    # the store structure of a room the driver ran in (DK.fingerprint()),
                    # kept under ONE fixed name as the baseline preflight diffs against
                    self._save_named(dict(body, name="store_fingerprint"), "name", ROOT / "data" / "draftrig", ".json",
                                     json.dumps(body, indent=1), "store_fingerprint")
                elif self.path.startswith("/players"):
                    # The room's whole player store (DK.players(): o_rank,
                    # psr_rank, avg_pick per player). scripts/
                    # yahoo_rank_from_snapshot.py turns it into the
                    # league-scoped yahoo_rank input (DECISIONS #35).
                    self._save_named(body, "source_room", ROOT / "data" / "logs" / "mocks", ".json",
                                     json.dumps(body, indent=1), "players_", prefix="players_")
                elif self.path.startswith("/trail"):
                    # End-of-mock dump from the page (DK.trail()): every pick with
                    # team ids, the managers, and our pick records (reason,
                    # best-by-projection alternative, candidates passed on).
                    # scripts/mock_trail.py renders it.
                    self._save_named(body, "room", ROOT / "data" / "logs" / "mocks", ".json",
                                     json.dumps(body, indent=1), "mock_", prefix="mock_")
                else:
                    # A page's HTML for the offline DOM tests (design 2026-09-01):
                    # the row lookup is the one reader still on the DOM, tested
                    # against real Yahoo markup without joining a room.
                    self._save_named(body, "name", ROOT / "tests" / "fixtures" / "yahoo", ".html",
                                     str(body.get("html") or ""), "page")
            except Exception as e:  # noqa: BLE001
                traceback.print_exc()
                self._json({"err": f"{type(e).__name__}: {e}"}, 500)
            return
        try:
            state = self._read_json()
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
            import time
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S")
            print(f"{stamp} plan #{plan.get('calls')} @pick {plan.get('current_pick')} "
                  f"drafted={len(drafted)} mine={n_mine} roster={len(roster)} "
                  f"needs={plan.get('needs')} -> {head}", flush=True)
            for w in plan.get("warnings") or []:
                print(f"{stamp}   WARNING plan #{plan.get('calls')}: {w}", flush=True)
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            self._json({"err": f"{type(e).__name__}: {e}"}, 500)

    def log_message(self, *a):
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default=None)
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--set", action="append", default=[], metavar="KNOB=VALUE",
                    help="engine knob override for this bridge process only (e.g. autopick_list_prob=0.3); logged on every plan")
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    _STATE["cfg"] = cfg
    overrides = {}
    for item in a.set:
        k, _, v = item.partition("=")
        if not hasattr(Tracker, k):
            raise SystemExit(f"unknown engine knob {k!r}")
        overrides[k] = type(getattr(Tracker, k))(v) if not isinstance(getattr(Tracker, k), bool) else v.lower() in ("1", "true", "yes")
    _STATE["overrides"] = overrides
    if overrides:
        print(f"engine overrides for this process: {overrides}", flush=True)
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

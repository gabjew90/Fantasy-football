# Draft-Day Web Dashboard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A one-double-click, browser-based live draft co-pilot that wraps the existing `Tracker` logic — zero terminal interaction on draft day.

**Architecture:** A stdlib `http.server` app (`draftkit/web.py`) serves a single embedded HTML page and a `/state` JSON endpoint. `/state` rate-limits calls to `Tracker.poll()` (at most once per `poll_seconds`) so there are no threads or locks; the browser polls `/state` every 2s. Trackers are cached per draft-id (mock support) and the cache is cleared by `POST /reload` (tier-tweak support). Two `.bat` launchers give the double-click entry points.

**Tech Stack:** Python 3.10 stdlib (`http.server`, `json`), existing `Tracker`/`snake` modules, vanilla HTML/CSS/JS. No new pip dependencies.

**Spec:** `docs/superpowers/specs/2026-08-19-draft-web-dashboard-design.md`. One deliberate deviation: no `refresh_status.json` — the page instead shows the `tiers.csv` build time (file mtime) and turns the banner amber when it is >12h old. Simpler, and truthful even if someone rebuilds tiers outside the launcher.

**File map:**
- Create: `draftkit/web.py` — state JSON builder + `DraftWebApp` + HTTP handler + `run_server`
- Create: `draftkit/web_page.py` — the embedded HTML page (one `PAGE` constant, no logic)
- Create: `tests/test_web_state.py` — unit tests, no network
- Modify: `draftkit/cli.py` — add `web` subcommand
- Create: `scripts/DRAFT DAY.bat`, `scripts/PLAN B.bat`

---

### Task 1: `build_state()` — the JSON snapshot builder

**Files:**
- Create: `draftkit/web.py`
- Test: `tests/test_web_state.py`

The only new "logic" in the project: turn a `Tracker` into one JSON-safe dict. Everything else is plumbing. Testable without network by constructing a `Tracker` via `object.__new__` and setting attributes directly (Tracker's `__init__` hits the Sleeper API; its methods only use instance attributes).

- [ ] **Step 1: Write the failing tests**

Create `tests/test_web_state.py`:

```python
"""Tests for the /state JSON builder — no network, Tracker built by hand."""

import time

from draftkit.tracker import Tracker, TrackerState
from draftkit.web import build_state

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1, "BN": 5}


def make_player(sleeper_id, player, pos, pos_rank, tier, vorp, adp, cliff=False):
    return {
        "sleeper_id": str(sleeper_id), "player": player, "pos": pos,
        "pos_rank": pos_rank, "tier": tier, "vorp": float(vorp),
        "adp": adp, "cliff_flag": cliff, "value_rank": pos_rank,
        "proj_pts": 200.0, "adp_delta": 0.0,
    }


PLAYERS = [
    make_player(1, "Alpha RB", "RB", 1, 1, 200.0, 1.0, cliff=True),
    make_player(2, "Beta RB", "RB", 2, 2, 150.0, 3.0),
    make_player(3, "Gamma RB", "RB", 3, 2, 140.0, 40.0),
    make_player(4, "Alpha WR", "WR", 1, 1, 160.0, 2.0),
    make_player(5, "Beta WR", "WR", 2, 1, 155.0, 5.0),
    make_player(6, "Alpha TE", "TE", 1, 1, 95.0, 25.0, cliff=True),
    make_player(7, "Alpha QB", "QB", 1, 1, 60.0, 30.0),
    make_player(8, "Alpha K", "K", 1, 1, 10.0, 120.0),
    make_player(9, "Alpha DEF", "DEF", 1, 1, 12.0, 110.0),
]


def make_tracker(picks, my_slot=2):
    t = object.__new__(Tracker)
    t.teams = 12
    t.rounds = 15
    t.slots = dict(SLOTS)
    t.my_slot = my_slot
    t.poll_seconds = 5.0
    t.kdef_round = 14
    t.fall_alert = 12
    t.draft_id = "testdraft"
    t.players = [dict(p) for p in PLAYERS]
    t.by_id = {p["sleeper_id"]: p for p in t.players}
    t.state = TrackerState(
        picks=picks,
        drafted_ids={str(p["player_id"]) for p in picks},
        last_poll_ok=time.time(),
    )
    t.state.status = "drafting"
    return t


def pick(player_id, draft_slot, pos):
    return {"player_id": str(player_id), "draft_slot": draft_slot,
            "metadata": {"position": pos}}


def test_on_the_clock_detection():
    # pick 1 made -> current pick is 2, which belongs to slot 2 (me)
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    s = build_state(t)
    assert s["current_pick"] == 2
    assert s["on_clock_me"] is True
    assert s["round"] == 1
    assert s["my_next_pick"] == 2
    assert s["picks_away"] == 0


def test_not_on_clock_and_picks_away():
    t = make_tracker([], my_slot=2)
    s = build_state(t)
    assert s["on_clock_me"] is False
    assert s["my_next_pick"] == 2
    assert s["picks_away"] == 1


def test_drafted_players_leave_board_and_recs():
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    s = build_state(t)
    names = [p["player"] for row in s["board"] for p in row["players"]]
    assert "Alpha RB" not in names
    rec_names = [r["player"] for r in s["recommendations"]]
    assert "Alpha RB" not in rec_names
    assert len(rec_names) > 0
    assert all(r["why"] for r in s["recommendations"])


def test_faller_surfaced():
    # 20 picks in, Gamma RB (ADP 40) is not a faller; Alpha WR (ADP 2) is long gone
    # so craft: 20 picks made, Beta WR (ADP 5) still available -> fell 21-5=16
    picks_ = [pick(100 + i, (i % 12) + 1, "RB") for i in range(20)]
    t = make_tracker(picks_, my_slot=2)
    s = build_state(t)
    fallers = {f["player"]: f for f in s["fallers"]}
    assert "Beta WR" in fallers
    assert fallers["Beta WR"]["fell"] >= 12


def test_poll_error_surfaced():
    t = make_tracker([], my_slot=2)
    t.state.last_error = "boom"
    s = build_state(t)
    assert s["poll_error"] == "boom"


def test_roster_fill_counts():
    # I picked an RB at pick 2
    t = make_tracker([pick(1, 1, "WR"), pick(2, 2, "RB")], my_slot=2)
    s = build_state(t)
    assert s["roster"]["filled"]["RB"] == 1
    assert s["roster"]["filled"]["QB"] == 0
    assert "Beta RB" not in s["roster"]["drafted"]  # names come from by_id
    assert s["roster"]["drafted"] == ["Alpha RB"]


def test_json_serializable():
    import json
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    json.dumps(build_state(t))
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_web_state.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'draftkit.web'`

- [ ] **Step 3: Implement `build_state` in `draftkit/web.py`**

```python
"""Phase 5 — local web dashboard. Display plumbing only: all draft logic
lives in Tracker; this module serializes it to JSON and serves one page."""

from __future__ import annotations

import time

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
```

Note: `on_clock_me` requires `status == "drafting"` (the terminal tracker only styles the header that way; the giant red banner must not fire pre-draft). `picks_away == 0` means on the clock.

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_web_state.py -v`
Expected: 7 passed. If `test_on_the_clock_detection` fails on `on_clock_me`, check the `status == "drafting"` guard — the test sets status to "drafting".

- [ ] **Step 5: Commit**

```bash
git add draftkit/web.py tests/test_web_state.py
git commit -m "Add build_state: JSON snapshot of Tracker for the web dashboard"
```

---

### Task 2: `DraftWebApp` — tracker cache, rate-limited polling, reload

**Files:**
- Modify: `draftkit/web.py` (append)
- Test: `tests/test_web_state.py` (append)

- [ ] **Step 1: Write the failing tests** (append to `tests/test_web_state.py`)

```python
class StubTracker:
    """Counts poll() calls; returns canned state via build_state monkeypatch-free."""

    def __init__(self):
        self.poll_calls = 0
        self.poll_seconds = 5.0

    def poll(self):
        self.poll_calls += 1
        return False


def test_app_rate_limits_polls(monkeypatch):
    from draftkit.web import DraftWebApp

    app = DraftWebApp.__new__(DraftWebApp)
    app._trackers = {}
    app._last_poll = {}
    stub = StubTracker()
    app._trackers["d1"] = stub
    monkeypatch.setattr("draftkit.web.build_state", lambda t: {"ok": True})

    app.state_for("d1", None)
    app.state_for("d1", None)  # immediate second call — inside poll window
    assert stub.poll_calls == 1


def test_app_reload_clears_cache():
    from draftkit.web import DraftWebApp

    app = DraftWebApp.__new__(DraftWebApp)
    app._trackers = {"d1": StubTracker()}
    app._last_poll = {"d1": 123.0}
    app.reload()
    assert app._trackers == {} and app._last_poll == {}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_web_state.py -v -k app`
Expected: FAIL — `ImportError: cannot import name 'DraftWebApp'`

- [ ] **Step 3: Implement `DraftWebApp`** (append to `draftkit/web.py`)

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\venv\Scripts\python.exe -m pytest tests/test_web_state.py -v`
Expected: 9 passed. (`state_for` on the stub works because `build_state` is monkeypatched and `tiers_mtime` isn't reached — the stub app has no `tiers_path`; if that assert-fails, move the `tiers_built_at` line above the return and give the test app a `tiers_path`... no: keep test simple by also setting `app.tiers_path = None` — `tiers_mtime` returns None via the OSError guard. Set `app.tiers_path = pathlib.Path("nonexistent-tiers.csv")` in the test if needed.)

- [ ] **Step 5: Commit**

```bash
git add draftkit/web.py tests/test_web_state.py
git commit -m "Add DraftWebApp: per-draft tracker cache with rate-limited polling"
```

---

### Task 3: HTML page (`draftkit/web_page.py`)

**Files:**
- Create: `draftkit/web_page.py`

No test (static string; correctness is validated by the Task 5 smoke test and Saturday's live mock). Dark theme, big type, phone-free fullscreen use. The page:
- polls `/state?draft_id=…&slot=…` every 2s (params only when the user set them; persisted in `localStorage`)
- giant status banner: red pulsing ON THE CLOCK / cyan countdown / amber RECONNECTING after 2 consecutive fetch failures or a `poll_error` / green DRAFT COMPLETE; browser tab title mirrors it
- recommendations (#1 extra large, with why), position board with cliff tags, roster strip, fallers strip
- footer: draft-id + slot inputs, Reload data button (`POST /reload`), heartbeat, tiers build time (amber when >12h old)

- [ ] **Step 1: Create `draftkit/web_page.py`**

```python
"""The dashboard page, embedded so `python -m draftkit web` is self-contained."""

PAGE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>draftkit</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  :root {
    --bg: #0d1117; --panel: #161b22; --edge: #30363d; --fg: #e6edf3;
    --dim: #8b949e; --red: #f85149; --amber: #d29922; --green: #3fb950;
    --cyan: #58a6ff; --purple: #bc8cff;
  }
  * { box-sizing: border-box; margin: 0; }
  body { background: var(--bg); color: var(--fg);
         font: 16px/1.45 "Segoe UI", system-ui, sans-serif; padding: 14px; }
  .banner { border-radius: 10px; padding: 18px 24px; text-align: center;
            font-size: 34px; font-weight: 800; letter-spacing: .5px;
            border: 2px solid var(--edge); background: var(--panel); }
  .banner.me { background: #67060c; border-color: var(--red); color: #fff;
               animation: pulse 1s infinite; font-size: 44px; }
  .banner.err { background: #4d3800; border-color: var(--amber); color: #ffd970; }
  .banner.done { background: #0f5323; border-color: var(--green); }
  .banner small { display: block; font-size: 15px; font-weight: 400; color: inherit; opacity: .85; }
  @keyframes pulse { 50% { filter: brightness(1.35); } }
  .cols { display: grid; grid-template-columns: 5fr 4fr; gap: 14px; margin-top: 14px; }
  @media (max-width: 1100px) { .cols { grid-template-columns: 1fr; } }
  .panel { background: var(--panel); border: 1px solid var(--edge);
           border-radius: 10px; padding: 14px 16px; }
  .panel h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 1px;
              color: var(--dim); margin-bottom: 10px; }
  .rec1 { font-size: 30px; font-weight: 800; }
  .rec1 .why, .rec .why { color: var(--dim); font-size: 15px; font-weight: 400; }
  .rec { font-size: 19px; padding: 7px 0; border-top: 1px solid var(--edge); }
  .tag { font-size: 13px; padding: 1px 8px; border-radius: 999px;
         border: 1px solid var(--edge); color: var(--dim); margin-left: 6px; }
  .pos-row { display: flex; gap: 10px; padding: 8px 0; border-top: 1px solid var(--edge);
             align-items: baseline; flex-wrap: wrap; }
  .pos-row:first-of-type { border-top: 0; }
  .pos-name { font-weight: 800; width: 44px; color: var(--cyan); font-size: 18px; }
  .pp { white-space: nowrap; }
  .pp b { font-size: 17px; }
  .pp .meta { color: var(--dim); font-size: 13px; }
  .cliffnow { color: #fff; background: var(--red); font-weight: 700;
              padding: 1px 8px; border-radius: 6px; font-size: 14px; }
  .cliffsoon { color: var(--amber); font-weight: 600; font-size: 14px; }
  .mountain { color: var(--purple); }
  .strip { margin-top: 14px; }
  .roster b { font-size: 18px; }
  .roster .full { color: var(--green); }
  .roster .open { color: var(--amber); }
  .drafted { color: var(--dim); margin-top: 6px; font-size: 15px; }
  .faller { margin-right: 18px; white-space: nowrap; }
  .faller .drop { color: var(--amber); font-weight: 700; }
  footer { display: flex; gap: 14px; align-items: center; flex-wrap: wrap;
           margin-top: 14px; color: var(--dim); font-size: 14px; }
  footer input { background: var(--bg); color: var(--fg); border: 1px solid var(--edge);
                 border-radius: 6px; padding: 6px 8px; font-size: 14px; }
  #draftId { width: 200px; }
  #slot { width: 52px; }
  footer button { background: #21262d; color: var(--fg); border: 1px solid var(--edge);
                  border-radius: 6px; padding: 6px 14px; font-size: 14px; cursor: pointer; }
  .stale { color: var(--amber); font-weight: 700; }
  #inputErr { color: var(--red); }
</style>
</head>
<body>
<div id="banner" class="banner">connecting…</div>
<div class="cols">
  <div class="panel"><h2>Pick now — best available for you</h2><div id="recs">—</div></div>
  <div class="panel"><h2>Board — top remaining by position</h2><div id="board">—</div></div>
</div>
<div class="panel strip roster" id="roster" style="display:none">
  <h2>My roster</h2><div id="rosterFill"></div><div class="drafted" id="drafted"></div>
</div>
<div class="panel strip" id="fallersPanel" style="display:none">
  <h2>Value fallers (≥ 1 round past ADP)</h2><div id="fallers"></div>
</div>
<footer>
  <label>mock draft ID (blank = real draft): <input id="draftId" placeholder=""></label>
  <label>slot: <input id="slot" type="number" min="1" max="12"></label>
  <button id="apply">apply</button>
  <button id="reload">reload tiers.csv</button>
  <span id="tiersAt"></span>
  <span id="heartbeat"></span>
  <span id="inputErr"></span>
</footer>
<script>
const $ = id => document.getElementById(id);
let fails = 0, lastOk = null;

const store = {
  get draftId() { return localStorage.getItem("dk_draft_id") || ""; },
  set draftId(v) { v ? localStorage.setItem("dk_draft_id", v) : localStorage.removeItem("dk_draft_id"); },
  get slot() { return localStorage.getItem("dk_slot") || ""; },
  set slot(v) { v ? localStorage.setItem("dk_slot", v) : localStorage.removeItem("dk_slot"); },
};
$("draftId").value = store.draftId;
$("slot").value = store.slot;
$("apply").onclick = () => { store.draftId = $("draftId").value.trim(); store.slot = $("slot").value.trim(); tick(); };
$("reload").onclick = async () => { await fetch("/reload", {method: "POST"}); tick(); };

function esc(t) { const d = document.createElement("div"); d.textContent = t ?? ""; return d.innerHTML; }

function render(s) {
  const b = $("banner");
  if (!s.ok) { $("inputErr").textContent = s.error; return; }
  $("inputErr").textContent = "";

  if (s.poll_error) {
    b.className = "banner err";
    b.innerHTML = `RECONNECTING… <small>Sleeper poll failing (${esc(s.poll_error)}) — data may be ${esc(s.last_poll_age_s)}s old. Nothing is lost; it recovers by itself.</small>`;
    document.title = "⚠ draftkit";
  } else if (s.status === "complete") {
    b.className = "banner done";
    b.textContent = "DRAFT COMPLETE — good luck in the playoffs";
    document.title = "✅ draftkit";
  } else if (s.on_clock_me) {
    b.className = "banner me";
    b.innerHTML = `YOU ARE ON THE CLOCK <small>pick ${s.current_pick} · round ${s.round}</small>`;
    document.title = "🔴 YOUR PICK";
  } else if (s.status !== "drafting") {
    b.className = "banner";
    b.innerHTML = `waiting — draft status: ${esc(s.status)} <small>pick ${s.current_pick} · slot ${s.on_clock_slot} first on the clock</small>`;
    document.title = "draftkit";
  } else {
    b.className = "banner";
    const away = s.picks_away === null ? "no picks left" : `your turn in ${s.picks_away} pick${s.picks_away === 1 ? "" : "s"}`;
    b.innerHTML = `pick ${s.current_pick} (R${s.round}.${s.pick_in_round}) — slot ${s.on_clock_slot} on the clock <small>${away}${s.my_next_pick ? " (pick " + s.my_next_pick + ")" : ""}</small>`;
    document.title = `${s.picks_away} away · draftkit`;
  }

  $("recs").innerHTML = (s.recommendations || []).map((r, i) => `
    <div class="${i === 0 ? "rec1" : "rec"}">${esc(r.player)}
      <span class="tag">${esc(r.pos)}${esc(r.pos_rank)} · T${esc(r.tier)} · VORP ${esc(r.vorp)}</span>
      <div class="why">${esc(r.why)}</div>
    </div>`).join("") || "no candidates";

  $("board").innerHTML = (s.board || []).map(row => {
    let tag = "";
    if (row.urgent) tag = `<span class="cliffnow">CLIFF NOW — ${row.before_cliff} left, ${row.demand} rivals</span>`;
    else if (row.before_cliff !== null && row.before_cliff <= 3) tag = `<span class="cliffsoon">cliff in ${row.before_cliff}</span>`;
    const ps = row.players.map(p => {
      const d = p.adp_delta_live;
      const dtxt = d !== null && Math.abs(d) >= 3 ? ` ${d > 0 ? "+" : ""}${d}v` : "";
      return `<span class="pp"><b>${esc(p.player)}</b>${p.cliff ? '<span class="mountain">⛰</span>' : ""} <span class="meta">T${p.tier}·${p.vorp}${dtxt}</span></span>`;
    }).join(" ");
    return `<div class="pos-row"><span class="pos-name">${row.pos}</span>${ps} ${tag}</div>`;
  }).join("");

  if (s.roster) {
    $("roster").style.display = "";
    $("rosterFill").innerHTML = Object.keys(s.roster.slots).map(k => {
      const f = s.roster.filled[k], m = s.roster.slots[k];
      return `<b class="${f >= m ? "full" : "open"}">${k} ${f}/${m}</b>&nbsp;&nbsp;`;
    }).join("") + `<b>BN ${s.roster.bench_used}/${s.roster.bench_total}</b>`;
    $("drafted").textContent = "drafted: " + (s.roster.drafted.join(", ") || "—");
  }

  const f = s.fallers || [];
  $("fallersPanel").style.display = f.length ? "" : "none";
  $("fallers").innerHTML = f.map(x =>
    `<span class="faller"><b>${esc(x.player)}</b> (${esc(x.pos)}, ADP ${x.adp}, <span class="drop">−${x.fell}</span>)</span>`).join("");

  const stale = s.tiers_built_at && (Date.now() - new Date(s.tiers_built_at.replace(" ", "T")).getTime() > 12 * 3600e3);
  $("tiersAt").innerHTML = s.tiers_built_at
    ? (stale ? `<span class="stale">⚠ tiers built ${esc(s.tiers_built_at)} — consider refreshing</span>` : `tiers built ${esc(s.tiers_built_at)}`)
    : "";
}

async function tick() {
  const q = new URLSearchParams();
  if (store.draftId) q.set("draft_id", store.draftId);
  if (store.slot) q.set("slot", store.slot);
  try {
    const r = await fetch("/state?" + q, {cache: "no-store"});
    const s = await r.json();
    fails = 0; lastOk = Date.now();
    render(s);
  } catch (e) {
    if (++fails >= 2) {
      $("banner").className = "banner err";
      $("banner").innerHTML = `RECONNECTING… <small>dashboard server not answering — the launcher restarts it automatically; if this persists 15s, double-click DRAFT DAY again.</small>`;
      document.title = "⚠ draftkit";
    }
  }
  $("heartbeat").textContent = lastOk ? `updated ${Math.round((Date.now() - lastOk) / 1000)}s ago` : "";
}
tick();
setInterval(tick, 2000);
</script>
</body>
</html>
"""
```

- [ ] **Step 2: Sanity check it imports**

Run: `.\venv\Scripts\python.exe -c "from draftkit.web_page import PAGE; print(len(PAGE))"`
Expected: a number > 5000, no traceback.

- [ ] **Step 3: Commit**

```bash
git add draftkit/web_page.py
git commit -m "Add embedded dashboard page"
```

---

### Task 4: HTTP server + `web` CLI subcommand

**Files:**
- Modify: `draftkit/web.py` (append)
- Modify: `draftkit/cli.py`

- [ ] **Step 1: Append the server to `draftkit/web.py`**

Add imports at the top of the file: `import json`, `from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer`, `from urllib.parse import urlparse, parse_qs`.

```python
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
```

- [ ] **Step 2: Add the `web` subcommand to `draftkit/cli.py`**

Add this command function next to `cmd_track` (it resolves the slot the same way):

```python
def cmd_web(cfg: Config, args) -> None:
    from .web import run_server

    slot = args.slot
    if slot is None:
        client = SleeperClient(cfg.path("raw"))
        slot, info = resolve_my_slot(cfg, client)
        if slot is None:
            console.print(f"[yellow]warning: {info.get('error')}; slot unresolved[/yellow]")
    sys.exit(run_server(cfg, cfg.root / "tiers.csv", slot, args.port))
```

In `main()`, register it with the other subparsers:

```python
    p = sub.add_parser("web")
    p.add_argument("--port", type=int, default=8723)
    p.add_argument("--slot", type=int, default=None, help="override my draft slot")
```

and add `"web": cmd_web,` to the dispatch dict.

- [ ] **Step 3: Run the full test suite**

Run: `.\venv\Scripts\python.exe -m pytest tests -q`
Expected: all pass (17 existing + 9 new = 26).

- [ ] **Step 4: Manual smoke test**

Run in background: `.\venv\Scripts\python.exe -m draftkit web`
Then: `Invoke-WebRequest http://localhost:8723/state | Select-Object -ExpandProperty Content`
Expected: JSON with `"ok": true`, `"status": "pre_draft"`, `"my_slot": 2`, non-empty `recommendations` and `board`.
Also `Invoke-WebRequest http://localhost:8723` → 200 with the HTML.
Then stop the server.

- [ ] **Step 5: Commit**

```bash
git add draftkit/web.py draftkit/cli.py
git commit -m "Add web subcommand: local dashboard server on port 8723"
```

---

### Task 5: Launcher scripts + desktop shortcuts

**Files:**
- Create: `scripts/DRAFT DAY.bat`
- Create: `scripts/PLAN B.bat`

- [ ] **Step 1: Create `scripts/DRAFT DAY.bat`**

```bat
@echo off
title draftkit - DRAFT DAY
cd /d "%~dp0.."
set PY=venv\Scripts\python.exe

echo.
echo === draftkit draft day ===
echo Refreshing market data (if this fails, the dashboard still opens
echo with the last good data and shows a banner about it)...
echo.
%PY% -m draftkit market
%PY% -m draftkit tiers

start "" http://localhost:8723

:loop
%PY% -m draftkit web --port 8723
if errorlevel 3 exit /b 0
echo.
echo Dashboard server stopped - restarting in 2 seconds (close this window to quit)...
timeout /t 2 /nobreak >nul
goto loop
```

Notes: `errorlevel 3` is the port-in-use exit — a second double-click just reopens the browser tab and exits instead of loop-spawning servers. The market/tiers failures are deliberately not fatal.

- [ ] **Step 2: Create `scripts/PLAN B.bat`**

```bat
@echo off
title draftkit - PLAN B (terminal tracker)
cd /d "%~dp0.."
venv\Scripts\python.exe -m draftkit track
pause
```

- [ ] **Step 3: Create desktop shortcuts** (one-time, via PowerShell)

```powershell
$sh = New-Object -ComObject WScript.Shell
foreach ($n in @("DRAFT DAY", "PLAN B")) {
  $s = $sh.CreateShortcut("$env:USERPROFILE\Desktop\$n.lnk")
  $s.TargetPath = "C:\Users\gabje\Desktop\fantasy-football\scripts\$n.bat"
  $s.WorkingDirectory = "C:\Users\gabje\Desktop\fantasy-football"
  $s.Save()
}
```

- [ ] **Step 4: End-to-end test — double-click path**

Run `scripts\DRAFT DAY.bat` (or the shortcut). Expected: market+tiers refresh output, browser opens to the dashboard, banner shows "waiting — draft status: pre_draft", recommendations and board populated, heartbeat ticking. Double-click again while running: a second tab opens, no crash, second window exits. Kill the python process: window restarts the server within 2s and the page recovers by itself.

- [ ] **Step 5: Commit**

```bash
git add "scripts/DRAFT DAY.bat" "scripts/PLAN B.bat"
git commit -m "Add one-click draft day launchers and Plan B terminal fallback"
```

---

## Self-review notes

- Spec coverage: server+endpoints (T2/T4), page with all panels+banner states (T3), launchers with auto-restart+port guard (T5), mock draft-ID box (T3 footer + T4 query params), reload for tier tweaks (T2/T3), slot resolution (T4 `cmd_web`), error handling (T2 `state_for` try/except, page `fails` counter, bat loop). Deviation from spec (no `refresh_status.json`, mtime banner instead) is called out in the header.
- The user may tweak `tiers.csv` / `Tracker.recommendations()` before Sunday: tiers.csv flows through `reload` or relaunch; scoring changes are picked up on server restart (the launcher restarts the server, so a relaunch covers both).
```

# Draft-day web dashboard — design

Date: 2026-08-19
Status: approved (Approach A + Plan-B icon)

## Goal

A zero-terminal, panic-proof draft-day co-pilot. One desktop double-click
refreshes data, starts a local web server, and opens a fullscreen browser
dashboard that tracks the live Sleeper draft and recommends picks dynamically.
Sleeper runs on the user's phone; the PC screen is 100% dashboard.

## Constraints

- Windows 11, Python 3.10 venv at `venv\`. No new heavyweight dependencies —
  the server uses the stdlib (`http.server`).
- All draft logic stays in the existing, tested `Tracker` class
  ([draftkit/tracker.py](../../../draftkit/tracker.py)). The web layer is
  display plumbing only.
- The user may tweak `tiers.csv` and the scoring in `Tracker.recommendations()`
  up to draft day; the dashboard must pick those changes up without code
  changes elsewhere.
- Draft: Sunday 2026-08-23 4:00 PM ET, 12-team snake, slot 2, 120s clock.

## Architecture

Three new pieces, all dumb plumbing:

### 1. `draftkit/web.py` — local web server

- `python -m draftkit web [--port 8723] [--draft-id X] [--slot N]` (new
  subcommand in `cli.py`).
- Stdlib `http.server.ThreadingHTTPServer`. No background threads for
  polling: `GET /state` polls Sleeper at most once per `poll_seconds`
  (rate-limited pull), so there are no locks and no stale-thread failure
  modes. The browser polls `/state` every 2 s.
- Endpoints:
  - `GET /` → the dashboard HTML (single embedded template, no static files).
  - `GET /state?draft_id=…&slot=…` → JSON snapshot: draft status, current
    pick/round, on-clock slot, my next pick + picks away, top-N
    recommendations with their "why" strings, per-position board (top 3 +
    cliff tags), roster fill, drafted names, value fallers, last-poll age,
    poll error if any, tiers.csv mtime, refresh-status banner.
  - `POST /reload` → re-read `tiers.csv` (for the user's tier tweaks;
    surfaced as a "reload data" button on the page).
- Tracker instances are created per draft_id and cached, so pasting a mock
  draft ID switches instantly and switching back costs nothing. State is
  always rebuilt from Sleeper's full picks list — restart-safe by
  construction.
- Slot resolution: real draft uses `resolve_my_slot` (same as `track`);
  mock drafts default to slot 2, overridable via the page.

### 2. Dashboard page (embedded HTML/JS, dark theme, big type)

Top-to-bottom:
- **Status banner** — giant. Red pulsing "YOU ARE ON THE CLOCK" when it's
  the user's pick; otherwise "pick N (R x.y) — your turn in K picks".
  Shows a heartbeat ("updated Ns ago") and flips to an unmissable amber
  "RECONNECTING…" state when `/state` fails or poll errors, never silently
  stale.
- **Recommendations panel** — top 5 from `Tracker.recommendations()`, #1
  rendered large, each with pos/rank, tier, VORP, and the why sentence.
- **Position board** — RB/WR/TE/QB/K/DEF rows, top 3 remaining each, with
  tier, VORP, ADP-delta, ⛰ markers, and "CLIFF NOW (n left, m rivals)" /
  "cliff in n" tags.
- **My roster strip** — slot fill (QB 0/1, RB 1/2 …) plus drafted names.
- **Value fallers strip** — players ≥12 picks past ADP.
- **Footer controls** — draft-ID box (blank = real draft; persisted in
  localStorage), slot override, reload-data button, data-freshness banner
  ("market data refreshed 2:31 PM" or "REFRESH FAILED — using cached
  Wednesday data").

### 3. Launchers (`scripts/`)

- **`DRAFT DAY.bat`** — uses the venv python. Steps: run
  `draftkit market` + `draftkit tiers` (on failure, continue and write the
  failure into `data/processed/refresh_status.json`, which the page shows as
  the cached-data banner); then `start http://localhost:8723`; then run the
  server in an auto-restart loop (`:loop … goto loop`), window minimized.
  Double-clicking again when a server is already running must not error
  (port-in-use → just reopen the browser tab).
- **`PLAN B.bat`** — opens the existing terminal tracker maximized
  (`python -m draftkit track`), for the case where the browser itself
  misbehaves.
- Written in `scripts/`, with desktop shortcuts created once during setup.

## Error handling

- Sleeper API down / wifi blip: `/state` returns last-known snapshot with
  `poll_error` set; page shows RECONNECTING banner; existing tracker backoff
  applies. Nothing crashes.
- Server dies: bat loop restarts it in ~2 s; page JS keeps retrying and
  recovers on its own.
- Market refresh fails Sunday: dashboard still launches on cached data with
  a visible banner — a stale ADP column beats no board.
- Wrong/mistyped mock draft ID: `/state` returns a clear error string the
  page displays next to the input, real draft unaffected.

## Testing

- Unit tests for the `/state` JSON builder using a `Tracker` with injected
  fake picks (no network): on-clock detection, recommendation passthrough,
  faller/cliff serialization, poll-error surfacing.
- Unit test for tiers reload (mtime change → new data served).
- Manual: Saturday live mock via the draft-ID box is the end-to-end test,
  per the runbook.

## Out of scope

- Cloud hosting, auth, multi-user.
- Any change to projections/VORP/tier math (separate, user-driven tweaks).
- Auto-picking in Sleeper (the user always makes the actual pick on phone).

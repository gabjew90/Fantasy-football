# Draft rig: foolproof and versatile — design

Date: 2026-09-01. Status: approved in conversation; implementation proceeds
without further sign-off (user instruction), through five mocks or a clean one.

## Problem

Eleven mocks, 39 logged defects, roughly 30 of them in the layer that
reconstructs draft state by reading Yahoo's screen. Mock 11 drafted four tight
ends because a layout difference (expanded stats view) made every row lookup
miss, every miss was recorded as "drafted", and the driver acted anyway. The
engine was never wrong when handed a correct state.

Two root causes: the reading layer is scraping a UI it does not control, and
it fails quietly — a bad reading produces a legal-looking state.

The user may be away during the real draft, so the floor must draft without
any of our code running.

## Design: three layers, each a strict fallback for the one above

| layer | executes | needs alive | quality |
|---|---|---|---|
| 0 · Yahoo pre-rank + Do-Not-Draft | Yahoo, server-side | nothing of ours | board order, Yahoo's positional balance, no timing |
| 1 · starred queue | Yahoo autopick, from the queue | the driver ran recently | engine plan from minutes ago |
| 2 · live pick | our click at the turn | driver + bridge now, readings sane | the engine, at the pick |

Rule: **a layer may act only when its readings pass consistency checks;
otherwise it does nothing and the layer below catches the pick.** Never a
confident click on a doubtful state.

## Findings the design rests on (verified 2026-09-01 in the user's Chrome)

- `https://pub-api.fantasysports.yahoo.com/fantasy/v3/{draftstatus,settings,teams}/nfl/<league_id>?format=rawjson`
  answers with session cookies from any Yahoo Fantasy page. `settings` carries
  roster_positions, stat_categories, position_draft_caps, draft_time,
  draft_pick_duration, waiver_rule, uses_faab. `teams` carries every team,
  manager, and a per-team `has_preranks` flag. `draftstatus` carries
  `draft_server` / `draft_port` — a dedicated live-draft server whose protocol
  is unknown and only observable during a draft.
- A mock league's endpoints return 403 once its draft completes; the real
  league's answer now.
- Edit Pre-Draft Ranks (`/f1/<league>/<team>/editprerank`) has an Import
  dialog ("Paste a list or upload a CSV"), and per-player star (My Preferred)
  and Do-Not-Draft buttons over 300 players. Clicking Import opens a native
  file chooser that freezes the tab for automation; Escape recovers it.

## Layer 0 — pre-rank and Do-Not-Draft

Source: `tiers.<league>.csv` in board order (VORP desc), with K and DEF moved
to the end so Yahoo's "fill starters first" cannot spend a mid-round pick on
them. Do-Not-Draft: every player whose availability status is out/IR/PUP/
suspended. Mechanism: per-player star and DND clicks in board order (avoids
the native dialog), then Save. Verification: `has_preranks` reads "1" for our
team via the API, and the My Preferred tab lists players in board order.
Re-run on draft morning after the board rebuild; idempotent (Reset first).

## Layer 2 — reading the wire, clicking the screen

State: the structured API for settings/teams; the live pick stream from the
draft channel once its protocol is captured (instrumented mock: network
tracking on before entering the room, capture `draft_server` traffic, and
poll `draftstatus` to learn whether it exposes picks mid-draft). If the
channel is opaque, poll `draftstatus`/the API every 2–3 s; the 60-second clock
makes that free.

The DOM is used for exactly one thing: locating the row to click. That parser
gets offline fixture tests (saved draft-room HTML in compact and expanded
layouts, on and off the clock) and a pre-clock preflight in the room.

Consistency gates before any click: pick count from the feed equals the
header's pick number minus one; our roster from the API/panel equals the
picks labelled ours; players marked gone this cycle below a threshold; the
bridge plan's `current_pick` equals the header. Any failure: no click, loud
log, next layer catches it.

## Out of scope now, recorded

Rival autopick detection (autopicking managers draft by Yahoo default rank
with positional balance — near-deterministic; collapse their survival noise).
After Saturday, if the room has absentees.

## Sequencing

1. Layer 0 built, saved, verified against the API.
2. Instrumented mock: capture the live channel; harden nothing else yet.
3. Reading layer on whichever source the mock proves; gates; fixtures; preflight.
4. Mocks until clean or five.

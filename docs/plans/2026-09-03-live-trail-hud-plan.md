# Plan: the live trail panel (heads-up display inside the Yahoo draft room)

## In plain English

While the draft runs, a small panel sits in a corner of the Yahoo draft page and prints a
time-stamped line every time the engine or the driver sees or does something. Lines are only
ever appended, newest at the bottom, like a ticker. You read it the way you read a chat: scroll
up to see what happened, leave it at the bottom to follow live. Nothing on it is clickable and it
never touches Yahoo's page; hide it with one console command if it is in the way.

What a stretch of it looks like (Pacific time):

    20:12:04  pick 23  Chris Olave (WR) taken by seat 4 in 11 s
    20:12:05  plan #44 for pick 26 (0.6 s): McBride TE 89% "safe to wait" · Achane RB 36% "waiting costs ~14" · Lamb WR 38%
    20:12:31  pick 24  De'Von Achane (RB) taken by seat 5 — a target is gone (was 36% to survive)
    20:12:44  pick 25  CeeDee Lamb (WR) taken by seat 6 INSTANTLY (autopick) — a target is gone
    20:12:45  ON THE CLOCK, pick 26 · plan #46 (0.4 s) · lineup needs QB RB WR FLEX K DEF
    20:12:45  choosing McBride TE: waiting would cost ~6 at TE, 79% to survive; top projection Josh Allen passed on purpose
    20:12:46  PICKED Trey McBride via Yahoo action, confirmed in 419 ms
    20:13:02  heartbeat sent (you are not idle)
    20:16:20  AWAY flag seen on us — cleared through setAwayStatus, 2 s
    20:18:11  GATE: not clicking — plan is for pick 66, header says 67 (bridge slow); retrying
    20:18:14  LOCAL ranking for this turn (bridge unreachable 3x)
    20:18:16  BRIDGE WARNING: 1 drafted entry matched no board player: 139 Will Reichard

## What gets built

- `scripts/draft_driver.js`
  - `narrate(kind, text)`: appends `{ts, kind, text}` to a new `S.trail` list AND the existing
    `S.log` (prefixed `NARR`), so the trail rides into the end-of-draft dump and the scrutiny
    report unchanged. Kinds: `pick`, `plan`, `turn`, `choice`, `picked`, `gate`, `away`, `heartbeat`,
    `bridge`, `fault`, `info`.
  - Narration points, each one line, plain English, no JSON:
    - a rival pick first seen: name, position, seat, seconds it took (from the first-sight stamps),
      and INSTANT when the timing label says so; if the player was in our current plan, append
      "a target is gone (was N% to survive)".
    - a plan received: call number, its age, the top three as `name pos NN% "short why"`.
    - on the clock: pick number, plan call, open lineup slots.
    - the choice: the same plain-English sentence the scrutiny report prints per pick
      (`plain_english` in scripts/mock_scrutiny.py, ported to JS: cost of waiting, survival, the
      top projection passed on purpose, skipped candidates).
    - the result: PICKED name via action|click, confirmed in N ms — or the failure and what caught it.
    - gate refusals, away detections and clears, heartbeats, bridge warnings, plan failures,
      local-ranker fallbacks, injected faults.
  - `hud(on)`: creates a fixed-position `div` (bottom-right, 420x260 px, monospace 12 px,
    dark background at 85% opacity, `pointer-events` only on its own scrollbar and a small
    header). The header shows `pick N · you're next in K · plan #M (age)`. The body is the
    trail; auto-scrolls to the bottom unless the reader has scrolled up (then a "new lines"
    marker appears until they scroll back). Times are Pacific `HH:MM:SS`. `DK.hud(false)` removes
    it; `DK.hud({corner: 'top-left', width: 520})` moves/resizes. Default ON at `run()`.
  - The panel is a `<div>` appended to `document.body` with a unique id; it survives Yahoo's
    re-renders because it is outside React's root; it is re-created if removed.
- `scripts/mock_scrutiny.py`: a "Narration" section that prints the `NARR` lines in Pacific time
  (they are already in the trail's `log`), so what you saw live and what the record says are one thing.
- Tests (`tests/test_draft_driver.py`, node + jsdom): `narrate` appends and time-stamps; the rival
  pick line says INSTANT for an instant label and names a plan target as gone; the choice line for a
  cost-of-waiting record matches the scrutiny wording; `hud(true)` creates one element and
  `hud(false)` removes it; auto-scroll flag flips when scrolled up.

## Not in scope
Anything interactive (no buttons that pick, no queue editing). A second-screen page served by the
bridge is a later, separate step.

## Order
After mock 27 finishes tonight: build, test, inject in the next room, watch it for one full draft,
then adjust wording from what actually reads well live.

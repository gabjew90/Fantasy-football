# Keefamania draft-day runbook (Yahoo, Sat Sep 5 2026, 10:00 PM EDT / 7:00 PM PT)

Three layers, each a fallback for the one above (design: docs/superpowers/specs/2026-09-01-draft-rig-foolproof-design.md).
Everything below is executed, not built. If a step is red, the layer below still drafts.

## Projection source (DECIDED — nothing to do on draft day)

`config.yaml -> projections.source` stays `model` (the 2025-usage + ECR blend
every mock drafted with). The alternative, `external` (FantasyPros sheet +
Sleeper stat lines), was put through the pre-registered quality gate on
2026-09-02 and failed both halves: its history stand-in projected 5% worse
on error and drafted lineups 1.6% worse on actual points (DECISIONS #23,
reports/source_gate.md). Do not flip it on draft morning. The sheet's
numbers stay visible on the board as `proj_consensus_pts` for the eye.

## T-2h: board and layer 0 (Yahoo's own autopick walks our list)

### Draft-morning checklist — DO NOT SKIP

Every item below is a step that was performed for the Omnibeta draft and
initially SKIPPED when onboarding Keefamania. The board pipeline running
clean does not mean the board is correct.

1. [ ] Injury sweep refresh. Cross-check data/external/availability.csv
       against LIVE Sleeper injury data (script pattern: compare
       players(refresh=True) injury_status vs the file for every top-120
       board player). Verify anything material against news before it
       moves a projection. MISS ON 8/31: Josh Jacobs sat at board rank 22
       with a full projection while on the Commissioner Exempt List since
       8/30. The draft-time injury layer is MANUAL; only the in-season
       auto-manager diffs injuries automatically.
2. [ ] Yahoo ADP re-scrape -> data/external/yahoo_adp.keefamania.csv, then
       rebuild market + tiers (the commands below).
3. [ ] Review reports/disagreements.keefamania.csv (board-vs-market
       worklist, ~30 rows). NEVER REVIEWED for this league; the equivalent
       pass for Omnibeta was a full research session.
4. [ ] Review the 9 no_market players (engine-invisible unless activated
       via an override).
5. [ ] Decide whether any Keefamania-specific overrides are needed. The
       file is league-scoped; Keefamania currently has NONE, which is
       correct-by-default (better no override than a wrong-scoring one).

The draft slot is NOT a yaml field: it comes from the room URL and is
passed to `DK.load` as `mySlot` (T-15m below).

Known accepted limitations (not fixable before Saturday):
- No rival seeds: Yahoo gives no draft history, so the Monte Carlo uses
  generic positional tendencies rather than per-manager ones.
- No `verify` command: Yahoo API access is still pending, so the league
  yaml's expected: block is a hand transcription, re-read before the draft.
- Replacement baselines are format-derived, not backtested (v2 §7).

### Build the board and load layer 0

    venv\Scripts\python.exe -m draftkit --league keefamania market
    venv\Scripts\python.exe -m draftkit --league keefamania tiers
    venv\Scripts\python.exe scripts\export_board_json.py --board tiers.keefamania.csv --out data\draftrig\board.keefamania.json
    venv\Scripts\python.exe scripts\bridge_server.py --league keefamania      # leave running

In Chrome (the profile that accepted the bridge cert):

1. Open https://127.0.0.1:8443/ping — must show `"ok":true`.
2. Open https://football.fantasysports.yahoo.com/f1/49649/3/editprerank and in DevTools console:

        (0,eval)(await (await fetch('https://127.0.0.1:8443/prerank.js')).text());
        PR.load(await (await fetch('https://127.0.0.1:8443/board.json')).json());
        await PR.import();     // expect "Imported ~228 players"
        await PR.dnd();        // availability = out
        PR.save();             // "saved as your ranked order."
        await PR.unmatched();  // expect ~12 deep-bench names (Yahoo's importer only matches its top ~300)
        await PR.addMissing(3); // repeat until left == 0: stars them via surname search, appended in board order
        await PR.preferred();   // count must equal PR.status().ordered; any hand-starred player sits at the bottom --
        // PR.moveAfter('DK Metcalf', 'Bucky Irving') puts one where the board has him (name of the player ranked just above)
        PR.save();              // again, after the touch-ups

   The last successful load is recorded in reports/prerank.keefamania.md
   (what the list looked like, what was unmatched, what was hand-starred).

3. Verify server-side from any Yahoo page:

        (await (await fetch('https://pub-api.fantasysports.yahoo.com/fantasy/v3/teams/nfl/49649?format=rawjson',{credentials:'include'})).json()).service.team_list.find(t=>t.id==3).has_preranks   // "1"

## T-15m: the room

- Enter the draft room from the league page **as soon as Yahoo opens it (30-60 minutes before the clock)** and inject the driver right away. A league room has no waiting-room countdown to race; the two lost first picks in mocks 16-17 came from a hidden waiting-room tab whose redirect never fired, and cannot happen once you are in the room with the driver running.
- **Keep the tab visible and the laptop awake** — Chrome throttles hidden tabs, and Yahoo's idle timer arms autopick on inactivity (the driver clears it through Yahoo's own setAwayStatus, but do not test it).
- Picks go through Yahoo's own `makePick` action (mock 19 onward): no search, no row, no button. If the action is unavailable the driver falls back to the row click, and either way the store must confirm the pick before it is reported (`via: action|click`, `verified: store`).
- Do NOT reload the page mid-draft. Re-evaluating the driver does not stop an old loop either; if the driver must be restarted, leave the room and re-enter, then inject again.

In the room's DevTools console:

    const B='https://127.0.0.1:8443';
    (0,eval)(await (await fetch(B+'/driver.js')).text());
    DK.load(await (await fetch(B+'/board.json')).json(), {teams:10, rounds:15, mySlot: <your slot>});
    await DK.preflight();

Preflight must show `store: true`, `my_team` set, `plan` starting "plan 25 deep", `gates.ok: true` (before pick 1 the gate may say "current pick unreadable" — fine until the header appears), `row_lookup.found: true`, `autopick_armed: false`, `client_actions` listing `makePick` and `setAwayStatus`, and `player_id_lookup` resolving a board name to a Yahoo id. A room whose `client_actions` lacks `makePick` runs on the click fallback (`via: click`), which is slower but still store-verified. Then:

    window.__dkRun = DK.run();

The driver now runs until the draft ends — there is no deadline argument by default, so a slow room cannot time it out.

### After the last pick

`await DK.trail()` runs automatically at draft end and POSTs the full trail to the bridge. If the log does not show a `trail:` line, run it by hand. Then render the report:

    venv\Scripts\python.exe scripts\mock_trail.py --room <room>

which writes reports/mocks/mock_<room>.md (every pick, our reasons, the alternatives passed on).

### Mock rooms (rehearsal only)

- Joining from the lobby tab: set `window.name = 'fandraft'` FIRST, then call `.click()` on the row's Join anchor. A plain click from an unnamed tab opens an invisible popup and you never see the room.
- Wait ~4 s, then read `location.pathname` and the "You will draft Nth" text — that N is `mySlot`.
- Filter the lobby to 10-team rooms at least 6 minutes out with at least 3 open seats; anything closer fills before the driver is injected.

## During the draft — what "healthy" looks like

- Bridge console: one line per plan request, `mine == roster`, `needs` shrinking, plan heads sensible.
- `DK.gatesOk()` → `ok: true` on the clock. `GATE FAILED -> not clicking` in the log is the design working: the queue (layer 1) takes that pick, then Yahoo's list (layer 0).
- `DK.storeState().on_clock` flips true at our turn; `DK.storeState().away_teams` should not contain `my_team` — if it does, the driver calls Yahoo's own `setAwayStatus(false)`, verifies against the store, and logs it; the Autodraft toggle click is the fallback.
- `DK.rank().source` must read `engine`. `LOCAL` means the bridge is unreachable — check the bridge window.

Operator console API (read-only unless noted):

| call | shows |
|---|---|
| `DK.state()` | pick number, on-clock flag, my roster, plan head, gate status |
| `DK.why()` | the engine's reason for the current top candidate and what it passed on |
| `DK.logs(n)` | the last n driver log lines |
| `DK.records()` | our pick records so far (what, why, best-by-projection alternative) |
| `DK.stop()` | stops the loop (only way to halt it without leaving the room) |
| `DK.trail()` | POSTs the full trail to the bridge (automatic at draft end) |

## If something is wrong

| symptom | do |
|---|---|
| bridge `/ping` fails | restart `bridge_server.py`; the driver retries every cycle |
| `/ping` shows a certificate error | the cert is leaf-only with a 14-day expiry (created 2026-09-01): rerun `scripts/make_bridge_cert.sh`, restart the bridge, and re-accept the cert in Chrome |
| `store: false` in preflight | Yahoo changed the app; the DOM readers take over automatically, but check the Picks tab is showing in the left panel |
| gates fail every cycle | let it — layers 1/0 draft; do not hand-click unless you intend to take over |
| "put into autopick mode" modal | the driver calls Yahoo's own `setAwayStatus(false)` and verifies against the store (the toggle click is the fallback); if it recurs, move the mouse in the tab yourself |
| Yahoo's position-cap modal (e.g. max TEs) | dismiss it; the engine's guardrails should never provoke it |

## After

`docs/draft-rig-mock-log.md` gets the entry; `data/logs/` has the picks; run the CLV retro when closing ADP is available.

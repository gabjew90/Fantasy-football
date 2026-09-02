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

3. Verify server-side from any Yahoo page:

        (await (await fetch('https://pub-api.fantasysports.yahoo.com/fantasy/v3/teams/nfl/49649?format=rawjson',{credentials:'include'})).json()).service.team_list.find(t=>t.id==3).has_preranks   // "1"

## T-15m: the room

- Enter the draft room from the league page **as soon as Yahoo opens it (30-60 minutes before the clock)** and inject the driver right away. A league room has no waiting-room countdown to race; the two lost first picks in mocks 16-17 came from a hidden waiting-room tab whose redirect never fired, and cannot happen once you are in the room with the driver running.
- **Keep the tab visible and the laptop awake** — Chrome throttles hidden tabs, and Yahoo's idle timer arms autopick on inactivity (the driver clears it through Yahoo's own setAwayStatus, but do not test it).
- Picks go through Yahoo's own `makePick` action (mock 19 onward): no search, no row, no button. If the action is unavailable the driver falls back to the row click, and either way the store must confirm the pick before it is reported (`via: action|click`, `verified: store`).
- Do NOT reload the page mid-draft. Re-evaluating the driver does not stop an old loop either; if the driver must be restarted, leave the room and re-enter, then inject again.

In the room's DevTools console:

    const B='https://127.0.0.1:8443';
    (0,eval)(await (await fetch(B+'/net_tap.js')).text());       // optional, passive
    (0,eval)(await (await fetch(B+'/driver.js')).text());
    DK.load(await (await fetch(B+'/board.json')).json(), {teams:10, rounds:15, mySlot: <your slot>});
    await DK.preflight();

Preflight must show `store: true`, `my_team` set, `plan` starting "plan 25 deep", `gates.ok: true` (before pick 1 the gate may say "current pick unreadable" — fine until the header appears), `row_lookup.found: true`, `autopick_armed: false`. Then:

    window.__dkRun = DK.run(3600);

## During the draft — what "healthy" looks like

- Bridge console: one line per plan request, `mine == roster`, `needs` shrinking, plan heads sensible.
- `DK.gatesOk()` → `ok: true` on the clock. `GATE FAILED -> not clicking` in the log is the design working: the queue (layer 1) takes that pick, then Yahoo's list (layer 0).
- `DK.storeState().on_clock` flips true at our turn; `DK.storeState().away_teams` should not contain `my_team` — if it does, `keepAlive()` clicks the Autodraft toggle off and logs it.
- `DK.rank().source` must read `engine`. `LOCAL` means the bridge is unreachable — check the bridge window.

## If something is wrong

| symptom | do |
|---|---|
| bridge `/ping` fails | restart `bridge_server.py`; the driver retries every cycle |
| `store: false` in preflight | Yahoo changed the app; the DOM readers take over automatically, but check the Picks tab is showing in the left panel |
| gates fail every cycle | let it — layers 1/0 draft; do not hand-click unless you intend to take over |
| "put into autopick mode" modal | the driver clicks Autodraft off; if it recurs, move the mouse in the tab yourself |
| Yahoo's position-cap modal (e.g. max TEs) | dismiss it; the engine's guardrails should never provoke it |

## After

`docs/draft-rig-mock-log.md` gets the entry; `data/logs/` has the picks; run the CLV retro when closing ADP is available.

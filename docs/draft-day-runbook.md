# Keefamania draft-day runbook (Yahoo, Sat Sep 5 2026, 10:00 PM EDT / 7:00 PM PT)

Three layers, each a fallback for the one above (design: docs/superpowers/specs/2026-09-01-draft-rig-foolproof-design.md).
Everything below is executed, not built. If a step is red, the layer below still drafts.

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
        await PR.unmatched();  // expect ~12 deep-bench names only; anything with positive VORP here gets starred by hand (search the surname on the All Players tab)

3. Verify server-side from any Yahoo page:

        (await (await fetch('https://pub-api.fantasysports.yahoo.com/fantasy/v3/teams/nfl/49649?format=rawjson',{credentials:'include'})).json()).service.team_list.find(t=>t.id==3).has_preranks   // "1"

## T-15m: the room

- Enter the draft room from the league page. **Keep the tab visible and the laptop awake** — Chrome throttles hidden tabs, and Yahoo's idle timer arms autopick on inactivity (the driver fakes activity, but do not test it).
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

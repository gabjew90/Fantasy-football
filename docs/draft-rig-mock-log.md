# Draft rig — mock log

Standing order: run mocks until a full draft completes with **15/15 engine
picks, zero Yahoo autopicks, and zero wrong-player errors**. **MET** — mocks
21, 22 and 23 each finished 15/15 under the final rig. Every mock ends with
the bug list it produced and the regression test that now covers it.

Target league: **Keefamania**, Yahoo 49649, 10 teams, half-PPR, 15 rounds,
1-minute timer, snake. Draft Sat Sep 5 2026 10:00pm EDT.

Rig: `scripts/bridge_server.py` (TLS bridge serving the engine, board and
driver), `scripts/yahoo_bridge.py` (the engine behind it),
`scripts/draft_driver.js` (in-page hands), `scripts/prerank_driver.js`
(layer 0 loader), board from `scripts/export_board_json.py`. Tests:
`tests/test_draft_driver.py`, `tests/test_prerank_driver.py` (node),
`tests/test_yahoo_bridge.py`, `tests/test_yahoo_dom.py`.

---

## Mock 1 — room 10303060, 10 teams, slot 5 — FAILED

Hand-driven, no rig. 5 of 11 picks were Yahoo's autopick.

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 1 | Autopick armed at round 1 | Left the room idle during the countdown; every Python round-trip costs 30–60s | Driver stays resident in-page |
| 2 | Autopick drafts **instantly** on turn open | Not documented anywhere; the certified wait-then-click protocol is void against it | Queue is the only actuator once armed |
| 3 | On-clock detector fired 3 picks early | Matched a **nav tab literally named "Draft"** | Match `document.title` = `YOUR TURN, DRAFT NOW` |
| 4 | Ranked already-drafted players | Player table shows drafted players unless the "Drafted" toggle is engaged | Availability by star-button absence |
| 5 | Queued a **3rd QB** behind two rostered QBs | Ranked on raw VORP; never called `_pos_allowed` | Guardrails ported into the driver + tested |

## Mock 2 — room 10304186, **12 teams**, slot 1 — FAILED

First run with the rig. Driver queued the top 5 in **6 seconds** (vs. four
rounds late in mock 1), so the residency fix works. Then four new bugs.

| # | Bug | Root cause | Fix / test |
|---|-----|-----------|------------|
| 6 | Joined a 12-team room | Read open **join links** as team count | Room list shows `X/10 Members` — filter on that |
| 7 | Marked **36 elite players "gone"** | Searched while the panel was on the Queue tab, so no row could match; read every miss as "drafted". Also burned the 60s clock, which armed autopick | `ensurePlayersTab()` + `tableLive()`; a miss is only "gone" when the table is provably live. `test_a_dead_ui_is_never_read_as_players_being_drafted` |
| 8 | Queue never held more than 4 | The star is a **toggle** — re-clicking removes the player. `queueNames()` can't see the whole queue, so the 5th was flipped in and out every cycle | Track our own clicks in `S.starred`. `test_a_queued_player_is_never_re_starred` |
| 9 | **Drafted the wrong Robinson** | `findRow`'s comment claimed it checked team; the code checked only name + position. Bijan Robinson and Brian Robinson Jr. are both `b robinson`, ATL, RB — took the −72.4 VORP one over the +91.8 one. Same bug let "J. Taylor" match a Jacksonville back instead of Jonathan Taylor (IND) | `rowMatches()` enforces team (with alias map) and splits true collisions by ADP. Export now reports collisions and warns when ADP gap < 25. Three tests |
| 10 | CDP eval timed out at 45s | Awaited the resident loop | Fire `DK.run()` **detached** |

Bug 9 is the dangerous one: silent, and it produces a plausible-looking
roster. Only the `D+` grade on the roster panel gave it away.

### Not bugs, decided deliberately
- Need-weighting is a **tiebreak, not an override**. Taking elite TE Bowers
  (68.5) over QB Allen (39.7) with 9 picks left is correct — QB supply is deep
  and `qb2_earliest_round` is 10. The must-fill override is the K/DEF rule.
- **K/DEF reservation** was added on top of the Python engine's rule: every
  other slot has many eligible players, a K slot only ever takes a kicker, so
  the last picks must be reserved or the draft ends a kicker short. The Python
  `must-fill` rule is not position-aware and does not catch this.

## Mock 3 — room 10304997, **10 teams**, slot 5 — FAILED (much closer)

First correctly-formatted run. Mock 2's fixes all held:

- **Jonathan Taylor of Indianapolis** was drafted, not the Jacksonville back.
  The team check works.
- The `ui-not-ready` guard kept the gone-set honest: **0 bad marks**, against
  36 in mock 2.
- No re-starring; the queue held a steady depth of 5 early on.

Five new bugs, all downstream of one root cause.

| # | Bug | Root cause | Fix / test |
|---|-----|-----------|------------|
| 11 | `draftTop` logged "drafted Bijan Robinson" twice; roster showed neither | Reported success straight after clicking, never checking. The click path silently no-opped and the **queue was making every real pick** — the log hid the failure being hunted | `pickLanded()`: a pick counts only when the roster grows. Test |
| 12 | A whole pick aborted as `ui-not-ready` | `tableLive()` ran with the search filter still applied, so a genuinely drafted player's empty result set looked exactly like a dead UI | `diagnoseMiss()` clears the filter and re-checks |
| 13 | Mahomes **and** Hurts queued together in round 5 | `syncQueue` only ever ADDED. Both legal at QB count 0, but the moment one landed the other was an illegal QB2 that autopick would take | `pruneQueue()` removes queued players the guardrails no longer allow. Re-ranking is only honest if it can also take things off |
| 14 | `draftTop` burned the entire 60s clock | Walked all 20 candidates at ~1.3s each — and an expired clock is what **arms autopick** | Bounded to 3 tries; skipped entirely once the autopick banner is up |
| 15 | **Queue drained 5 → 2 → 1 → 0**, then Yahoo's fallback handed us a THIRD tight end | The `S.starred` memo (which stops us toggling a player back out) never released. A player who left the queue without joining our roster was taken by a rival but stayed memoised, so refill skipped them forever | `reconcileStarred()`. Test |

Bug 15 is the important one: the guardrail violation (3 TEs, then 2 QBs) was
**not a ranking error**. The ranking was right the whole time; the queue
starved, and Yahoo's own list filled the vacuum. Roster quality tracks queue
depth almost exactly.

Final roster showed the cost: Mahomes/Goff at QB, three TEs, and K + DEF
still unfilled at 12/15 with an empty queue.

### Architecture decision
The **queue is the guaranteed actuator**, and `syncQueue` keeps its head equal
to the engine's top eligible pick — so whoever pulls the trigger, the pick is
the engine's. `draftTop` is best-effort on top of that, never a dependency.
This is the right shape given armed autopick drafts instantly.

## Mock 4 — room 10305876, 10 teams, slot 7 — FAILED

Actual picks (overall pick number): 7 McBride TE · 14 Bowers TE · 27 Rice WR ·
34 J.Williams RB · 47 Adams WR · 54 Mahomes QB · **67 Nix QB** · 74 Warren RB ·
87 Harvey RB · 94 M.Wilson WR · **107 Josh Jacobs (CEL)** · 114 Likely TE ·
127 Golden WR · 134 Dicker K · **147 McPherson K** · **DEF: empty**.

McBride at 7 was correct — the six ahead of him were gone and he was the
board's best available. Everything after round 6 is autopick damage.

| # | Bug | Root cause | Fix / test |
|---|-----|-----------|------------|
| 16 | **Every on-clock pick aborted** as `ui-not-ready`, in mocks 2, 3 AND 4 | Found only by *screenshotting the screen mid-turn*: Yahoo re-renders every row with a **"Draft" button** when it is your turn, and the star disappears. Keying on the star meant no row was ever recognised at the one moment that matters. The failed loop then burned the 60s clock, which is what armed autopick | `isPlayerRow()` accepts star **or** Draft button; `draftTop` clicks the row's own Draft button. Test |
| 17 | Driver reported an **empty queue** while five players sat in it | Same re-render: queue rows gain a "Draft" prefix, and the anchored regex matched nothing | `parseQueueRow` tolerates the prefix. Test |
| 18 | Queue held **five quarterbacks** in round 6; QB2 landed at pick 67, before the round-10 gate | `syncQueue` filled by score, which clusters by position. Only one QB was legally draftable, so the rest were pruned and the queue collapsed — starvation by a new route | The queue is a PLAN: each candidate is now checked against a roster already holding everything queued ahead of it, which diversifies for free. Test |
| 19 | Prune churn: players cut and re-added in the same cycle | `pruneQueue` keyed off top-20 membership rather than legality, so slipping to #21 caused an un-star then re-star — wasted clicks on a TOGGLE, risking queue desync | Prune on `guardrailOk` only |
| 20 | **Two TEs in the first three rounds, no RB** | The TE2 gate ("a board top-6 TE") was too easy | TE2 must also have FLEX open and clear the best available RB/WR by 10 VORP. Two tests |
| 21 | **DEF slot left empty**, two kickers drafted, and Josh Jacobs (Commissioner Exempt, zeroed) taken at 107 | All three are autopick with an exhausted queue — none came from the engine, whose board ranks Jacobs last | Downstream of 16–18 |

### Correction
An earlier reading of the roster panel said pick 1 was Rashee Rice. That was
wrong: the panel is **slot-ordered, not draft-ordered**. Rice went at 27.
Always read the Results tab's pick column.

### Direction change (user call, agreed)
Live picking becomes **primary**, the queue drops to backup. A 60-second clock
is enormous against a ~3s decision, and a pick computed at our turn sees the
real board — unlike a queue built minutes earlier, which from slot 7 held six
players who were all gone by pick 7. The queue only ever looked necessary
because the click path was broken by bug 16.

---

## Open

- On-demand/"Instant" drafts start immediately against bots, but they create a
  **real league team**, so they are not used for practice.
- Autopick, once armed, could not be turned off from the DOM: the warning
  banner carries no control and the queue-panel "Autodraft" toggle does not
  clear it. Treat arming as unrecoverable and never let the clock expire.

## Mock 6 — room 10307459, 10 teams, slot 2 — FAILED (best yet)

`1.02 McCaffrey RB · 2.19 McBride TE · 3.22 Bowers TE · 4.39 Adams WR ·
5.42 Skattebo RB · 6.59 Mahomes QB · 7.62 Warren RB · 8.79 Metcalf WR ·
9.82 Johnston WR · 10.99 Nix QB · 11.102 Corum RB · 12.119 Ferguson TE ·
13.122 Lemon WR · 14.139 Pineiro K · 15.142 Borregales K`

Good: McCaffrey at 1.02 was the board's clear #1 (26 VORP over Gibbs, 54 over
the best WR). QB2 landed at round 10, exactly on the `qb2_earliest_round`
gate. No wrong-player errors. The calibrated board showed up immediately --
McBride fell behind Nacua, Josh Allen from 20th to 28th.

| # | Bug | Root cause | Fix / test |
|---|-----|-----------|------------|
| 22 | **Empty DEF slot, two kickers, a third TE** | The board calls them "Houston Texans" -> key "h texans" -> matcher looked for "H. Texans". Yahoo renders `Texans DEF Bye 8` with NO initial, so **no defense could ever match** and the driver was structurally incapable of drafting one. The unfillable slot starved the endgame and Yahoo's fallback padded it | Defenses match on nickname alone; `searchTerm()` types the nickname. Test |
| 23 | Two TEs again (2.19, 3.22) | My own sequencing: the TE2 margin rule was written but the browser still held the mock-4 driver. Not a new engine flaw | Deployed driver v4 mid-draft |

Bug 22 is the same shape as the wrong-Robinson bug: an identity assumption
("every player has a first initial") that silently holds for 240 of 243 rows
and fails completely for the rest.

## Mock 7 — room 10310639, 10 teams, slot 1 — FIRST STRUCTURALLY VALID ROSTER

`QB2 WR6 RB4 TE1 K1 DEF1` — 15/15 with **every mandatory slot filled,
including a defense, and exactly one kicker**. First time. McCaffrey at 1.01,
and autopick stayed UNARMED for nine rounds, so the live-pick path works end
to end.

Five bugs, all found and fixed mid-draft.

| # | Bug | Root cause | Fix / test |
|---|-----|-----------|------------|
| 24 | Drafted **Brian Robinson Jr. (grade D) instead of Bijan — again** | ADP is the only thing separating them and the guard read `if (seen != null)`, so a row where Yahoo printed no ADP skipped the check *on exactly the row it existed for* | Collisions detected at board load; for a colliding entry an unreadable ADP REFUSES the row. Test |
| 25 | Queue held McBride **and** Bowers | The TE2 margin lived in `rank()`'s filter, so `syncQueue`'s simulated re-check (which calls `guardrailOk` directly) never applied it | Moved into `te2Ok()`, consulted via `guardrailOk` by every caller |
| 26 | **`rank()` returned nothing** at roster 9/15, so Yahoo took the pick and autopick armed | Stash-mute: with all starters filled `needsPosition()` is false for everyone, so the one-stash rule silences the whole board. The Python engine fixed this exact bug on shallow boards; the port reintroduced it | Labelled fallback relaxing the stash rule (never the positional guardrails). Test |
| 27 | Queue stuck at **depth 1 for four rounds** with K and DEF unfilled | The ADP pre-filter skipped anyone whose ADP was earlier than our next pick — by round 12 that is every player still available, since being a faller is why they are still there | Filter applies only while the queue is healthy (depth ≥ 3); threshold 12 → 40 picks |
| 28 | Queued defenses were **invisible**, so `reconcileStarred` marked them gone | Fixing the player table (mock 6) left the QUEUE parser still keying defenses by initial | `idKey(name, pos)` is now THE identity function, used by board load, roster parse, queue parse, prune, reconcile and the planner. Test |

Bugs 22 and 28 are the same assumption in two hiding places. The lesson is
recorded in `idKey`'s comment: a defense is called three different things by
three different parts of the page, so identity gets exactly one function.

## Mock 8 — room 10311522, 10 teams, slot 2 — **CLEAN. BAR MET.**

First run with every fix live from pick 1.

```
QB  P. Mahomes        WR  D. Adams          RB  C. McCaffrey
QB  B. Purdy (R10)    WR  R. Odunze         RB  J. Warren
                      WR  D. Metcalf        RB  R. Harvey
TE  T. McBride        WR  C. Sutton         RB  K. Gainwell
TE  B. Bowers         WR  W. Robinson
K   C. Little         DEF Steelers
```

**14 verified on-clock picks. 0 on-clock errors. Autopick NEVER armed.**

Against the standing bar:

| Criterion | Result |
|---|---|
| 15/15 engine picks | yes — 14 verified `ONCLOCK`, roster full |
| Zero Yahoo autopicks | yes — `armed: false` for the whole draft, no banner |
| Zero wrong-player errors | yes |
| Every mandatory slot filled | yes — exactly one K, exactly one DEF |
| Guardrails respected | yes — QB2 at round 10, no TE3, K/DEF held to the last two picks |

Self-corrections observed live, none needing intervention:
- Drake Maye queued as QB2 in round 6, then **pruned automatically** once
  Mahomes landed (`cut=["D. Maye QB NE"]`).
- Seattle DEF was sniped between cycles; the queue re-ranked to Eagles DEF
  and finally took the Steelers, unprompted.
- `why()` at the endgame reported `open: ["K","DEF"]` with the queue holding
  exactly those two in VORP order, every remaining TE correctly blocked.

### Bug count by mock
1 → 5 · 2 → 4 · 3 → 5 · 4 → 6 · 6 → 2 · 7 → 5 · **8 → 0**

The rig is at 192 tests. Every bug above has a regression test, so the
failures cannot silently return.

## Mock 9 — room 10313996, 10 teams, slot 4 — CLEAN (2nd consecutive), first under VONA

`QB2 WR5 RB5 TE1 K1 DEF1` · 12 verified on-clock picks · **0 errors** ·
**autopick never armed**.

Picks: 4 McCaffrey · 17 McBride · 24 Kyren Williams · 37 Skattebo ·
44 Adams · 57 Odunze · **64 Mahomes** · 77 Metcalf · 84 Sutton · 97 Purdy ·
104 Harvey · 117 Deebo · 124 Spears · 137 Chiefs DEF · 144 Butker K.

**VONA is visibly working.** Live ranking at pick 4 put James Cook III
(VORP 63.7, VONA 23.2) *above* Puka Nacua (VORP 69.0, VONA 21.0) — the lower
VORP player ranked higher because RB is the scarcer position. No QB appeared
in the top 6 at all, where VORP had Josh Allen 20th overall.

**Mahomes moved from pick 42 to pick 64** — 22 picks later, the exact
behaviour VONA was built for. Still 38 picks ahead of his ADP of 102, so the
correction is directional rather than complete.

### What CANNOT be concluded from mock 8 vs mock 9
Mock 8 was slot 2, mock 9 slot 4, against different opponents and a different
available pool. Starting-lineup VORP fell 338.8 → 296.5, but that is
overwhelmingly a draft-slot effect, not a ranking effect — slot 2 simply gets
better players. Mean reach was 9.37 → 8.66 picks, a change too small to read
through that confound either.

The controlled evidence for VONA remains the 22-replay study in
`reports/vona_validation.md`, where rivals' picks are held fixed and only our
ranking varies. Live mocks confirm VONA *behaves* as designed; they cannot
measure whether it drafts better.

---

# Architecture change (2026-09-01): the engine moved back to Python

Mocks 1-9 were driven by a JavaScript reimplementation of `tracker.py`.
Measured against the engine it was copying (`scripts/engine_bakeoff.py`) it
agreed on **25%** of top picks and lost at **8 of 10** slots. It was not a
port; it was a different algorithm wearing the same board.

`localhost` is now solved, so there is one engine again:

- The block was **mixed content**, not Private Network Access. Over http
  Chrome never sent the request at all — an instrumented server logged curl's
  hit and nothing from Chrome, and the promise never settled. Over TLS the
  same request fails in 126ms with an ordinary certificate error.
- `scripts/bridge_server.py` serves `tracker.recommendations()` on
  `https://127.0.0.1:8443` behind a leaf-only certificate (CA:FALSE,
  localhost SANs, 14-day expiry), accepted once in Chrome.
- Measured from the live draft page: **/ping 10ms, a full plan including the
  Monte Carlo 614ms**. Against a 60-second clock that is free, so the page
  asks the engine AT the pick and staleness is zero.

`draft_driver.js` keeps only what must run in the page: row matching, the
star toggle, the on-clock re-render, defenses without first names, and
keeping autopick from arming. Its ranking survives as a **labelled** fallback
— every `rank()` result carries `source`, so a downgrade is visible.

## Mock 10 — room 10408520, 10 teams, slot 10 — bug-finding run

First run on the bridge. Two verified engine picks at the turn: McBride and
Bowers, back to back at 10 and 11 — the two-pick planner taking BOTH elite
TEs, which is the exact call greedy VONA got wrong at slot 9.

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 29 | Roster showed **QB:2 in round 4** against a round-10 gate | Yahoo's pick feed gives player and pick number but never whose pick it was, so every pick defaulted to slot 0, none were attributed to us, and `my_pos_counts()` came back empty. Correct ranking over wrong state | Derive slot from pick number; prefer the panel's "You" flag |
| 30 | Bridge was told the draft was at **pick 2** while it was at pick 51 | `draftedFeed()` read the **Results** tab, which stays empty until a draft ENDS. Only caught because the fallback is labelled and reported `source: LOCAL` | Read the **Picks** panel instead |
| 31 | Picks panel **virtualises** — mid-draft it held 8-50 and had dropped 1-7 | A single read is always partial | Accumulate into a Map across cycles; never forget a pick |
| 32 | Slot arithmetic would have mis-attributed every pick | The room **reshuffled us from slot 3 to slot 10** seconds before starting | Trust the panel's "You" label over snake position |

Bug 30 is the one worth remembering: the labelled fallback is what made it
visible. A silent downgrade would have looked like a working draft.

## Mock 11 — room 10427764 "Hail Mary", 10 teams, slot 8 — the worst roster and the best run

Final roster: McBride, Bowers, Warren, Pitts (FOUR tight ends), Lawrence and
Stafford at QB, two defenses, and Yahoo put us into autopick for inactivity
during a mid-draft reload. Every one of those outcomes traced to a defect
that is now fixed and tested. The engine itself was never wrong: every time
the bridge was handed a correct state it answered sensibly (Adams / Maye /
Skattebo with TE need 0), and the depth-tail excepted, it never offered a
third tight end.

| # | Bug | Root cause | Fix |
|---|-----|-----------|-----|
| 33 | First two picks planned from an EMPTY feed (bridge thought it was pick 1) | The Picks panel's text only exists while the left panel's **Picks** tab is showing; the room opens on **Queue**. `parsePicksPanel` read nothing, so nothing was drafted and nobody was rostered | `ensureLeftTab('Picks')` before every feed read; `ensureLeftTab('Queue')` before reading the queue |
| 34 | **Every recommended player marked "gone", every cycle** (44 in the set at one point) | `findRow` capped candidate elements at 260 chars, tuned to the compact layout. This room opened in Yahoo's **expanded stats** layout where a row's text is ~400 chars, so no element with a star ever passed; other rows rendered, so `classifyMiss` said *gone*. The real recommendations vanished and the driver drafted from what was left | `ROW_TEXT_CAP = 1500`; the smallest element matching AND carrying a star/Draft button is the row |
| 35 | What was left was **tight ends and defenses** | The plan's depth-fallback tail was raw VORP order with only drafted/no_market removed -- no guardrails. With TE the shallowest position, TE3/TE4/DEF sat at the top of the tail | `yahoo_bridge.depth_tail` runs the tail through `_pos_allowed`, the same predicate as every other candidate |
| 36 | `nostar` recorded as gone | On our turn Yahoo swaps the star for a **Draft** button; a found row with no star is a UI state, not a drafted player | only `norow` marks gone |
| 37 | After a reload, plan believed it was **pick 4 in round 14** with an empty roster | The Picks panel shows only the last few picks after a reload; `refreshPlan` sent only `drafted` | The page now sends `my_roster` (roster panel) and `current_pick` (header) too; the bridge attributes roster players as ours and pads to the header's pick; both the page (sessionStorage) and the bridge (per-draft union, `merge_feed`) remember every pick seen |
| 38 | Our defense never attributed; DEF slot "open" all draft | Roster panel says "DEF Texans", board says "Houston Texans"; `key()` made "d texans" vs "h texans" | `pkey()`: defenses match on the nickname |
| 39 | Bijan/Brian collision guard silently OFF | Only `loadCompact()` built the collision set; the JSON `load()` path (bridge-served board) never did | `markCollisions()` shared by both |

Two things worth remembering beyond the table.

**The labelled fallback saved the diagnosis again.** `rank().source` said `engine`
throughout, which ruled out the local ranker in one call and pointed straight
at the gone-set. Bug 34 was found by clearing `S.gone` (`DK.reset()`),
watching the ranking snap back to Adams / Warren / Stafford / Brown, and
watching it re-poison within one sync cycle.

**Reloading the page mid-draft was my mistake, not Yahoo's.** It killed the
driver loop (Yahoo armed autopick for inactivity) and threw away the feed.
The fixes in 37 make a reload survivable; the standing rule is still do not
do it. Re-evaluating the driver in place is not a fix either -- the old loop
keeps running in its own closure.

Also seen: Yahoo enforces a per-position draft cap with a modal ("maximum
number of TEs you can draft (4)"), which blocks the click and has to be
dismissed. The driver does not yet handle that modal; with 35 fixed it should
never be provoked.

## Between mocks 11 and 12 — layer 0 and the instrumentation tap

Layer 0 (Yahoo pre-rank = our board) is set on the real league; see
DECISIONS 2026-09-01 #11 for the runbook. `scripts/prerank_driver.js` is
served by the bridge at /prerank.js. `scripts/net_tap.js` (served at
/net_tap.js) hooks WebSocket/fetch/XHR passively so mock 12 can show how the
draft client actually receives picks -- the design's layer 2 reads that
instead of the screen.

## Mock 12 — room 10430757 "Pooch Kick", 10 teams, slot 10 — clean picks, then Yahoo took the wheel

Roster: Achane, McBride, Rashee Rice, Javonte Williams, Davante Adams,
Drake Maye, Jaylen Warren, Rico Dowdle, Courtland Sutton, RJ Harvey, Kenny
Gainwell, Wan'Dale Robinson, Malik Willis (QB2, R13), Texans DEF, Pineiro K.
One tight end. Every pick through round 10 made by the engine at the turn,
verified on the roster, with the bridge's state consistent throughout
(mine == roster at every plan request).

Then from about round 11 the log reads "ON CLOCK (autopick armed) -> queue
head takes it": Yahoo had flagged us **away** for inactivity and armed
autopick. The store confirms it (`league.managers[me].away: true`). The
driver was clicking fine -- programmatic clicks are not the activity Yahoo
counts. The queue (layer 1) caught those picks, which is what it is for, and
they were still sane, but live control was lost. Fix: `keepAlive()` dispatches
synthetic mouse/keyboard activity every cycle and, if the store says we are
away or the modal is up, flips the Autodraft toggle back off.

### What mock 12 was really for: the client's own state

The draft client is React + Redux and its store is reachable by walking the
React fiber tree. It holds the draft as data -- every pick with team and
player ids, the whole player pool, the current pick and team, the clock, and
per-manager `away`/`loggedin` flags. `storeState()` now feeds the bridge
from it; the Picks panel, roster panel and header readers are the fallback
and a disagreement is logged. The row click is the only DOM dependency left.

Also confirmed live: `draftstatus` for the mock league returns the draft
server (`...sports-aws-prod-omega.aws.oath.cloud:443`) and the client's
message types (PICK_MADE, CURRENT_PICK_CHANGED, CLOCK, DRAFT_OVER, ...). The
socket itself is opened before any injected hook can see it; the store makes
that moot.

Fixtures captured to tests/fixtures/yahoo/ (crumbs redacted): the live room
in the expanded layout, the post-draft room with the Picks tab showing, and
a store snapshot. tests/test_yahoo_dom.py runs the driver's readers against
them under jsdom in seconds.

Also seen: five of the nine rivals were `away` -- autopicking from Yahoo's
default list. The rival-autopick idea has its signal.

## Mock 13 — room 10432160 "Red Zone", 10 teams, slot 6 — keepAlive held; three new defects, all in the endgame

Roster: McCaffrey, Achane, McBride, Davante Adams, Drake Maye, Jaylen Warren,
Jameson Williams, RJ Harvey, Courtland Sutton, Quentin Johnston, Kenny
Gainwell, Wan'Dale Robinson, Daniel Jones (QB2, R13), Cam Little K, Ravens
DEF. Legal at every guardrail, one TE, K and DEF filled.

Picks 6–75: every pick made live by the engine at the turn except pick 6
(the on-clock gate refused a store/header disagreement and the queue took
McCaffrey — the design working) and the store's off-by-one fixed in place.
`away` never flipped on us through round 8: keepAlive did its job.

Then pick 86 was lost, and with it live control for the rest of the draft.

| # | symptom | cause | fix |
|---|---|---|---|
| 40 | A.J. Brown led the engine's plan from pick 42 to 46 — he had gone at 17 | the bridge keyed the board on first-initial + surname; "A. Brown" is Amon-Ra St. Brown AND A.J. Brown (and "B. Robinson" is Bijan and Brian, same team), so the dict kept one and the other could never be marked drafted | `PlayerIndex`: full name first, initial key as fallback, and among namesakes the one not already accounted for. Roster attribution resolves to player ids the same way. Tests: both Browns drafted; "A. Brown" after Amon-Ra is A.J.; our A.J. does not claim their Amon-Ra |
| 41 | pick 86: driver refused all 24 candidates as `guardrail`, clock ran out, Yahoo armed autopick | a driver-only rule: "no VORP ≤ 0 pick once we hold a stash". By round 9 every remaining RB/WR is below replacement — including the bench-insurance rows the engine prices above zero on purpose. rank() had a labelled relaxation for this; draftTop never did | rule deleted from guardrailOk (the driver keeps the roster legal; whether a bench pick is worth it is bench.py's call). Dead relaxation branch removed; test updated |
| 42 | from 86 on: "AWAY/AUTOPICK detected (store=true/false alternating) -> clicked Autodraft toggle" every 2 s | keepAlive treated the "put into autopick mode" notice as the state. It is an inert banner that stays up after disarm, and the control is a toggle: off, on, off, on. autopickArmed() read the same banner, so the loop also stood itself down at every turn | store first everywhere: `autopickArmed()` and keepAlive use the store's away flag when a store exists; the banner counts only without a store, once per 30 s, and a click that ARMS autodraft is undone at once. Test: banner + store-off → not armed |
| 43 | pick 135: log said "Seattle Seahawks, verified: true"; the store says our 135 was Cam Little (K) | verification was "the roster count grew". Yahoo's autopick had taken Cam Little the instant the turn opened, our click was rejected ("not the current pick"), and the count still went up | `pickLandedStore(cand, turn)`: is the pick recorded at OUR pick number this candidate? false → reported as `pick-made-by-other-means`, never as verified; null (no store / not recorded yet) → roster-count fallback. Tested |

Picks 95, 106, 135 and 146 were made by Yahoo's autodraft (queue head or
its default list); 115 and 126 went by while I had the driver stopped to
ship the fixes. The bridge was restarted mid-draft with the namesake fix and
the driver re-injected at pick 131 — preflight clean, the Texans/Seahawks
plan correct for K/DEF — which is the recovery path the runbook describes.

Open question for mock 14: after the toggle storm the store said
`away: false` while the server still autopicked for us at 135 and 146. So
the client's flag and the server's autopick state can diverge. With the
storm gone this should not recur; if the server autopicks while the store
says not-away, the flag is not the truth and we need the server's word
(draftstatus, or the pick timing itself).

Also seen: with every rival away, the room ran a round in about ten seconds.
Our own clock is unaffected, but "N picks until your turn" is minutes of
warning in a live room and seconds in a mock.

## Mock 14 — room 10433575 "Squib Kick", 10 teams, slot 9 — clean

Roster: Achane, Chase Brown, Javonte Williams, Rashee Rice, Davante Adams,
Drake Maye, George Kittle, Jaylen Warren, Courtland Sutton, Matthew Stafford
(QB2, R10, at the gate), RJ Harvey, Wan'Dale Robinson, Woody Marks, Seahawks
DEF, Eddy Pineiro K. One TE, K and DEF in the last two rounds, legal at every
guardrail.

Fifteen of fifteen picks made by the driver at the turn, each verified
against the store (`verified: "store"`), none by the queue or by Yahoo. No
gate failed, `away` never flipped on us across 45 minutes, no autopick
banner. The bridge's state matched the room throughout (mine == roster at
every request). This is the bar set on 2026-09-01, met.

What mock 13's fixes did here, visibly:

- Round 9, pick 89: Courtland Sutton at VORP -1.7 went straight through as
  bench insurance. The rule deleted after mock 13 would have refused him and
  the 23 candidates behind him, and the clock would have run out again.
- The room ran with up to eight rivals away; the store said so and the
  driver never confused their state with ours.
- Namesakes: Amon-Ra St. Brown went at 6, A.J. Brown later; the plan never
  offered a gone player.

Nothing new broke. Two observations for the CLV retro, not the rig: the
engine opened RB-RB-RB-WR from slot 9 (Achane, Chase Brown, Javonte Williams
before Rashee Rice), and took Stafford as QB2 the first round the gate
allowed it. Both are engine judgements to grade against closing ADP, not
driver defects.

Open question from mock 13 (store `away` vs the server's autopick state)
did not arise: with no toggle storm there was nothing to desync.

## Mock 15 — room 10434811 "Pooch Kick", 10 teams, slot 8 — clean, nine humans

Roster: Achane, Chase Brown, Javonte Williams, Rashee Rice, Davante Adams,
Drake Maye, George Kittle, DK Metcalf, RJ Harvey, Matthew Stafford (QB2,
R10), Kenny Gainwell, Quentin Johnston, Woody Marks, Steelers DEF, Cairo
Santos K. Legal at every guardrail.

Fifteen of fifteen picks by the driver at the turn, each `verified: "store"`;
no gate failure, never `away`, no banner, no autopick. This room had nine
live humans (one to four away at any time), so the pacing was the real
league's — a round every three to four minutes, 30 seconds a pick — rather
than mock 14's autopick sprint. Same result.

Second clean run in a row under the bar set 2026-09-01. The opening eight
picks were identical to mock 14's from a different slot (Achane, Chase
Brown, Javonte Williams, Rashee Rice, Adams, Maye, Kittle, then the best
WR), which says the engine is deterministic given the same board and
similar rooms; whether those are the RIGHT picks is the CLV retro's
question, not the rig's.

Rig status after mocks 12–15: the store-fed driver, the bridge's resolver,
the structural-only guardrail and store-first autopick state have now been
exercised across a bot-paced room and a human-paced room without a defect.
The only DOM dependency left is the row click, which has not missed since
the expanded-layout fix in mock 11.

## Mock 16 — room 10486951 "Red Zone", 10 teams, slot 1 — 14 of 15 live; pick 1 lost to a late entry

Roster: Gibbs (Yahoo autopick, see below), McBride, Drake London, Skattebo,
D'Andre Swift, Jameson Williams, Jalen Hurts, DK Metcalf, Wan'Dale Robinson,
Mahomes (QB2, R10, at the gate), Courtland Sutton, RJ Harvey, Jakobi Meyers,
Cam Little K, Jaguars DEF. Legal at every guardrail; slot 1's back-to-back
turns (20/21, 40/41, …) handled without a gate trip.

Fourteen of fifteen picks made by the driver at the turn, each `verified:
"store"`, never `away`, no banner, no queue fallback. The driver ran from
pick 7 with the tab HIDDEN the whole draft (the pre-rank tab was in front):
turn picks landed 5-7 s after the clock opened, so Chrome's background
throttling did not bite here either (mocks 14-15 were the same).

The one miss was process, not the rig: I joined with ~4 minutes to go,
Yahoo reassigned me from seat 8 to seat 1 (seat taken), and the waiting-room
countdown in a hidden tab ran slow (it read 02:32 when the room had already
opened). Pick 1 went to Yahoo's default list (Gibbs) before the driver was
injected. Rule for Saturday, already in the runbook: be in the room and
injected BEFORE the clock, and keep the draft tab in front.

Also: preflight's `row_lookup` reported the plan head as not found because
he had just been drafted -- cosmetic; the check should pick an undrafted
player.

## Mock 17 — room 10488007 "Coin Toss", 10 teams, slot 7 — 14 of 15 live; the waiting-room trap again

Roster: Nacua (Yahoo autopick, see below), Achane, McBride, Rashee Rice,
Jaylen Warren, Jalen Hurts, Rhamondre Stevenson, Rico Dowdle, RJ Harvey, DK
Metcalf, Stafford (QB2, R11), Kenny Gainwell, Wan'Dale Robinson, Steelers
DEF, Eddy Pineiro K. Legal at every guardrail.

Fourteen of fifteen picks by the driver at the turn, `verified: "store"`,
zero gate/retry/away/queue events in the log. The fixed preflight probed an
undrafted candidate (Achane) and passed.

Pick 7 was lost the same way as mock 16's pick 1, and now the mechanism is
pinned down: a hidden waiting-room tab never redirects into the draft
client. Its countdown crawled 35 seconds in nine minutes; the room opened
on the server, the page changed to "Draft has Started! Enter Draft", and
nothing moved until I reloaded the waiting-room URL and clicked that link
(pick 13 by then). This is a Chrome background-tab effect on the waiting
room, not the draft client: once in the room the driver drafted fine hidden
in mocks 14-17. Saturday rule: draft tab in FRONT, in the room before the
clock, driver injected before pick 1 -- the runbook already says so; the
mocks have now shown twice what happens otherwise.

## Mock 18 — room 10488887 "Automatic First Down", 10 teams, slot 6 — clean, 15 of 15

Roster: Jonathan Taylor, Achane, McBride, Javonte Williams, Tetairoa
McMillan, Davante Adams, Trevor Lawrence, RJ Harvey, Kenny Gainwell,
Wan'Dale Robinson, Mahomes (QB2, R11), Alec Pierce, Jakobi Meyers, Cam
Little K, Chiefs DEF. Legal at every guardrail.

Fifteen of fifteen picks by the driver at the turn, `verified: "store"`,
zero gate / retry / away / queue events. This time the entry followed the
new rule: wall-clock start, reload the waiting-room URL a minute before it,
click "Enter Draft" the moment it appeared, inject during the 41-second
pre-draft countdown -- the driver was running before pick 1.

### Mocks 16-18 in one line each

- 16 (slot 1): 14/15 live; pick 1 lost to a late entry (waiting-room tab).
- 17 (slot 7): 14/15 live; pick 7 lost the same way, mechanism pinned down.
- 18 (slot 6): 15/15 live, in the room before the clock.

Across the three: 43 driver picks, 43 store-verified, no gate trips, never
away, no autopick banner, every roster legal. The only losses were the two
picks made before the driver was in the room, and the procedure that
prevents that is now in the runbook and was executed in mock 18. The rig is
done; what remains for Saturday is the projection-source decision
(DECISIONS #21) and following the runbook to the letter.

## Mock 19 — room 10501573 "Botched Snap", 10 teams, slot 10 — no-click picks, two injected faults, 15 of 15

First mock on the client-action pick path (DECISIONS: driver commit
a9b4ba4). Roster: McCaffrey, Achane, Rashee Rice, Garrett Wilson, Drake
Maye, Kittle, Gainwell, RJ Harvey, Aaron Jones, Wan'Dale Robinson, Mahomes
(QB2, R11), Sutton, Woody Marks, Rams DEF, McPherson K. Legal.

Fifteen of fifteen by the driver, in the room before pick 1 (entered via
the wall-clock reload). Fourteen picks went through Yahoo's own `makePick`
thunk -- no search, no row, no button -- and landed in the store in 300-530
ms; zero gate / retry / notours / queue events; never `away`.

Two faults injected on purpose, both recovered:

- Pick 70: the cached `makePick` replaced with a no-op right before the
  turn. The action was called once, timed out (3 s), the driver fell back
  to the DOM click and the store verified Gainwell as `via: click`. The
  fault then disarmed itself and pick 71 (RJ Harvey) went back through the
  action in 526 ms.
- After pick 71: our own away flag forced on with Yahoo's real
  `setAwayStatus(true)`. keepAlive saw `store=true` in the same cycle and
  cleared it with `setAwayStatus(false)` -- no toggle click -- and a
  one-second poll never caught the flag afterwards.

Proof-of-engine, from the pick records (each carries the engine's reason
and the best-available-by-projection alternative): the engine did NOT take
the top projection at any of its 15 picks. Josh Allen was the top
projection available at picks 10, 11, 30 and 31 and was passed each time
("waiting costs ~1-10 pts at QB"); he went 32nd. McCaffrey fell to 10 and
was taken as "last RB at this level, big drop after him"; Maye at 50 as the
slot fill after Allen went; rounds 7-13 were priced as bench insurance
("covers 3 RB starters ~9.6 wks, +9.1/wk over the wire ≈ 88 pts") rather
than by raw points. Pivots when a target went: McBride and London at 30/31
-> Rice and Wilson; Dobbins at 90 -> Aaron Jones.

## Mock 20 — room 10502459 "Fourth and Inches", 10 teams, slot 9 — 14 of 15; the action path's own idle-timer hole

Full trail: reports/mocks/mock_10502459.md (every manager's picks and
roster, our picks with the engine's reason, the best-by-projection
alternative and the candidates passed on).

Roster: Achane, CeeDee Lamb, McBride, Javonte Williams, Maye, Davante
Adams, Gainwell, RJ Harvey, Aaron Jones, Wan'Dale Robinson, Mahomes (QB2,
R11), Woody Marks, Michael Pittman (Yahoo autopick, see below), Dicker K,
Ravens DEF.

Fourteen of fifteen by the driver, all fourteen through `makePick`
(337-1018 ms to store confirmation), in the room before pick 1. The
fifteenth is the mock's finding: at pick 129 Yahoo had flagged us `away`
(its idle timer, ~16 minutes into the draft) and autopicked Pittman the
instant our turn opened. The driver's record is exact -- makePick(Tracy)
timed out, the click fallback found no Draft button (pick already made),
the next candidate's action returned `notours(Michael Pittman Jr.)` -- and
keepAlive cleared the flag at 15:28:06, three seconds after the pick.

Why now and not in mocks 14-18: on the click path our own typing and
clicking counted as user activity to Yahoo's client; `makePick` generates
none, so the action path removed an accidental keep-alive. Fix (driver
commit 26a8e97): keepAlive sends Yahoo's own `setAwayStatus(false)` every
240 s whether or not the flag is up, and run() calls keepAlive before the
on-clock pick attempt. Mock 19 did not hit it only because my forced
away/clear at 14:59 reset the timer by accident.

Engine narration highlights: passed on Josh Allen as the top projection at
9, 12, 29 and 32 (he went 22nd); McBride survived to 29 (71%); Maye taken
at 49 as the QB slot fill after Wilson and Skattebo went; rounds 7-12
priced as bench insurance (RJ Harvey "covers 3 RB starters ~9.6 wks, ≈ 88
pts"). Mistake count for the "three clean mocks" rule resets: 21, 22, 23.

## Mock 21 — room 10503516 "First and Ten", 10 teams, slot 4 — clean, 15 of 15 via makePick (1 of 3 after the heartbeat fix)

Full trail: reports/mocks/mock_10503516.md.

Roster: McCaffrey, McBride, Drake London, Garrett Wilson, Skattebo, Hurts,
Jaylen Warren, DK Metcalf, Carnell Tate, Mahomes (QB2, R10), Wan'Dale
Robinson, Sutton, Jakobi Meyers, Cam Little K, Browns DEF. Legal.

Fifteen of fifteen through the client's `makePick`, 259-739 ms to store
confirmation; no click fallback, no gate trip, no `notours`, never `away`.
The heartbeat fired on schedule at 15:46, 15:50, 15:54, 15:58 and 16:02,
and the round 10/11 turn (picks 97 and 104, 16-17 minutes in -- the window
that broke mock 20) went through without the flag appearing. In the room
before pick 1 via the wall-clock reload.

Narration highlights: pick 4 McCaffrey ("waiting costs ~44 at RB") with
Allen passed as the top projection; Achane went at 13 so 17 became McBride
(the 72% fallback); all three named targets vanished before 37 (Olave 30,
Allen 34, Rice 35) -> Garrett Wilson; Maye went before 57 -> Hurts for the
QB slot; rounds 7-13 priced as bench insurance with every pick record
carrying the reason and the candidates passed on.

## Mock 22 — room 10504572 "First and Ten", 10 teams, slot 9 — clean, 15 of 15 via makePick (2 of 3)

Full trail: reports/mocks/mock_10504572.md.

Roster: Achane, McBride, Chris Olave, Garrett Wilson, Jaylen Warren, Hurts,
TreVeyon Henderson, Rico Dowdle, Wan'Dale Robinson, Mahomes (QB2, R11),
Gainwell, Jakobi Meyers, Dicker K, Chiefs DEF (+ Robinson at 92). Legal.

Fifteen of fifteen through the client's `makePick`, 345-721 ms to store
confirmation; no fallback, no gate trip, never `away`. Heartbeats at
16:16, 16:20, 16:24 on schedule; the round 9/10 turn at 16-17 minutes
passed without the flag. In the room before pick 1.

Narration highlights: McCaffrey and Chase gone in the first five, so 9/12
became Achane and McBride ("waiting costs ~26 at TE, 44%"); both named
targets gone before 29/32 (A.J. Brown 22, Kyren 24) -> Olave and Garrett
Wilson; Allen passed as the top projection four times and went 33rd; Hurts
took the QB slot at 52; Rico Dowdle at 72 priced as the handcuff for our
own Warren ("covers 3 RB starters ~9.6 wks, ≈ 96 pts over the wire").

## Mock 23 — room 10505450 "Forward Progress", 10 teams, slot 8 — clean, 15 of 15 via makePick (3 of 3)

Full trail: reports/mocks/mock_10505450.md.

Roster: Achane, CeeDee Lamb, McBride, Javonte Williams, Davante Adams, Maye,
TreVeyon Henderson, RJ Harvey, Gainwell, Wan'Dale Robinson, Mahomes (QB2,
R11), Sutton, Jakobi Meyers, Eagles DEF, Pineiro K. Legal.

Fifteen of fifteen through the client's `makePick` (346-1765 ms to store
confirmation; the slow one was the final kicker in a room sprinting to
the end), no fallback, no gate trip, never `away`. Heartbeats 16:42, 16:46,
16:50 on schedule. Injected at pick 4 after a transient Chrome-extension
disconnect on the waiting-room step; no pick was lost (seat 8's first turn
was pick 8).

Narration highlights: all four of McCaffrey, Nacua, St. Brown and Taylor
went in picks 4-7 -> Achane and CeeDee Lamb at 8/13; McBride survived to 28
(65%); Maye taken at 53 while still there ("waiting costs ~10, 43%");
RJ Harvey at 73 as the 88-point insurance piece; K/DEF in the last two
rounds.

### The no-click series (mocks 19-23), settled

- 19: 15/15, click fallback and away-clear both exercised by injected faults.
- 20: 14/15 -- the action path's own hole: Yahoo's idle timer (nothing we
  do counts as activity any more) flagged us away at 16 min and autopicked
  the instant the turn opened. Fixed with a 240-s `setAwayStatus(false)`
  heartbeat and a keepAlive before every pick attempt.
- 21, 22, 23: 45/45 through `makePick`, eleven heartbeats on schedule,
  zero gate/retry/notours/away events, all three drafts crossing the
  16-minute window without the flag.

What Saturday relies on, all exercised live: the client's own makePick
with store confirmation; the DOM click as fallback (fired once, on demand,
and landed); the away clear (fired once on demand and once for real, both
before the flag could cost a pick after the heartbeat existed); entry
before the clock; and a pick record per turn carrying the engine's reason,
the best-by-projection alternative and the candidates passed on.

## Mock 24 — room 10531886 "Bump and Run", 10 teams, slot 6 — STRESS TEST, 15 of 15 legal, 13 by the driver, three injected faults

Full trail: reports/mocks/mock24_2026-09-02_2208pt_bump-and-run_room10531886_seat6_trail.md.
Scrutiny report (a plain-English reading per pick, every pick joined to its
plan call, markets, needs, away seats, skipped candidates; survival
scorecard; driver log, Pacific time): reports/mocks/
mock24_2026-09-02_2208pt_bump-and-run_room10531886_seat6_scrutiny.md, from
scripts/mock_scrutiny.py. Report names carry mock number, Pacific start
time, room name, room id and seat. First room on the reviewed code (DECISIONS #34)
and the first with the plans sidecar and the room log written live.

Roster: McCaffrey, Achane, McBride, Garrett Wilson, Davante Adams, Maye,
Jaylen Warren, Rico Dowdle (handcuff), RJ Harvey, Wan'Dale Robinson,
Mahomes (QB2, R11), Gainwell, Pittman, Cam Little K, Chiefs DEF. Legal.

The room: all ten seats open when joined, 30-second clock, seven of ten
managers away by the end -- the autopick-heavy case. Away seats mapped
live through thirteen changes ({5} -> {7} -> {} -> {4} -> ... ->
{3,4,5,7,9}); the B5 gate (non-empty away_slots in a live bridge log) is
closed.

Driver: 12 picks via makePick (median 501 ms to store confirmation, 250 to
1455), 1 via the click fallback (injected), 2 by Yahoo from our queue (see
below). Four heartbeats on schedule; three away flags detected and cleared
(one injected, two real: Yahoo flags you away when it makes your pick).

Injected faults:
- Pick 66: makePick replaced by a self-disarming no-op. The action timed
  out after 3 s, the record says `Jaylen Warren:action-timeout`, the same
  candidate landed by the click fallback, store-verified; the real action
  was back for pick 75.
- After 66: our away flag forced on with Yahoo's real setAwayStatus(true).
  keepAlive saw store=true two seconds later and cleared it with
  setAwayStatus(false); the flag never survived to a turn.
- Picks 78-86: the bridge killed. Every refresh logged `PLAN bridge
  unreachable`; at the turn the gate failed three cycles on plan-only
  reasons and the NEW local fallback fired as designed -- and then found
  the defect it was built to expose: the local ranker's availability set
  knew only S.gone and our roster, not the store's drafted list, so it
  tried Bijan Robinson and Smith-Njigba (picks 2 and 4). Both failed, the
  clock ran, and Yahoo made pick 86 from our queue: RJ Harvey, the engine's
  own queued choice. Fixed in the same hour (rank() excludes store-drafted
  players; test). Bridge restarted at pick 88; the page re-fed the new
  process from the store, plan call 4 of the new process made pick 95.

Found without injection:
- Pick 126: the plan had two rows and NO depth tail, because the reviewed
  depth_tail ran Python's full guardrail including the one-stash rule,
  which refuses every below-replacement bench player once you hold
  stashes. The page's own gone set (polluted by the fault-3 row misses)
  held both rows, the plan filtered to empty, the local ranker (still the
  old one in that page) tried drafted players again, and the queue made
  the pick: Pittman. Two fixes: the tail applies position caps + must-fill
  but not the stash rule, and with a store the store's drafted list decides
  "gone", never the page's memory.
- The first automatic trail posted at OUR roster full, three picks before
  the room ended, and under `<room>.json` instead of `mock_<room>.json`.
  Both fixed (wait for the room, up to two minutes; prefix).
- Bridge warning "dropped 1 feed entry numbered >= header pick 138": the
  store's drafted list ran one ahead of its currentPick for one call; the
  reconcile-down rule dropped a real pick for that call and the next call
  was whole. Harmless, recorded.
- The 50-70% survival bucket read 60% shown / 32% observed (n 34) in this
  room; 70-90% 80/73, 90-100% 95/94. Autopick seats take the top of
  Yahoo's list faster than a sigma-scaled human; input for the autopick
  refit stage.

Operational lessons (in the rig memory): join = `window.name='fandraft'`
then `.click()` the row's Join anchor from the lobby tab; NEVER reload the
waiting room before the bell (ec=5 drops the seat -- lost room 10528893
that way); reload after the bell and click Enter Draft; a devtools eval
dies at 45 s, so poll with <= 35-s sleeps.

## Mock 25 — room 10532940 "Pooch Kick", 10 teams, slot 3 — STRESS TEST 2, 15 of 15 legal, three injected faults, two defects found and fixed

Full trail: reports/mocks/mock25_2026-09-02_2237pt_pooch-kick_room10532940_seat3_trail.md.
Scrutiny: reports/mocks/mock25_2026-09-02_2237pt_pooch-kick_room10532940_seat3_scrutiny.md. Eight of ten seats human at the join;
five away by the end.

Roster: McCaffrey, McBride, Olave, Rashee Rice, Skattebo, Hurts, Jaylen
Warren, Gainwell, RJ Harvey, Wan'Dale Robinson, Mahomes (QB2, R11), Tyrone
Tracy, Sutton, Steelers DEF, Pineiro K. Legal. In the room before pick 1
(reload AFTER the bell, Enter Draft clicked, injected with 46 s on the
pre-draft clock).

Injected faults:
- Pick 25: full page reload, driver re-injected. Preflight after the
  reload read 30 picks and our three from the store, the bridge answered
  from its intact feed memory (plan call 28), gates clean, no warnings.
  Records from before the reload were saved first as
  mock_10532940_prereload.json and the scrutiny report merges them.
- Picks 64-87: bridge killed. Refreshes logged, the gate fell back to the
  local ranker at 78 and it PICKED this time (Gainwell via makePick, store
  verified) and again at 83 (RJ Harvey, no bad attempts). But its first
  attempt at 78 was Smith-Njigba, drafted at pick 4: the board exporter
  fused hyphenated surnames ("j smithnjigba") while the driver spaced them
  ("j njigba"), so that player never matched between board and store.
  Fixed: the exporter's normaliser now equals the driver's; a parity test
  over eleven awkward names; board re-exported.
- Picks 114-124: the store's manager id masked, so the page could not say
  which team is ours. The roster fell back to the panel (11 players,
  matching the header), the state was logged, the bridge kept attributing
  by name and the plan kept coming. The pick landed -- and the record was
  WRONG: our makePick landed Tracy at 118, but verification required the
  team id, returned "not recorded", the click path took Sutton's
  roster-count growth as proof and recorded Sutton at 118. Sutton came at
  123. The mock-13 class of error, back on a path that could not use the
  store. Fixed: the store entry at OUR pick number decides, team id or
  not (test).

Also: local-ranker records carried pick_no null and an empty reason; both
now filled (store pick number; "LOCAL ranker: VONA x, two-pick y").
Auto-trail waited for the room to finish and saved under mock_<room>.json.

Fifteen of fifteen legal; 14 driver records (11 after the reload + 3
before), 13 via makePick, 1 via click (the masked turn); no gate failure
outside the injected outage; heartbeats on schedule.

## Mock 26 — room 10534350 "First and Ten", 10 teams, slot 6 — CLEAN confirmation run, 15 of 15 via makePick, zero events

Trail and scrutiny: reports/mocks/mock26_2026-09-02_2318pt_first-and-ten_room10534350_seat6_{trail,scrutiny}.md.
No faults injected. The first full room on the code that carries every
fix from mocks 24 and 25 (local ranker excludes store-drafted players,
depth tail never empty, store decides "gone", verification by our pick
number, hyphenated-name parity).

Roster: Nacua, McBride, Olave, Etienne, Maye, Jaylen Warren, Stevenson,
Dowdle (handcuff), RJ Harvey, Wan'Dale Robinson, Mahomes (QB2, R11),
Gainwell, Pittman, Eagles DEF, McPherson K. Legal. In the room before pick
1 (reload after the bell, Enter Draft, injected with 6 s on the pre-draft
clock).

Fifteen of fifteen through makePick, 346-1156 ms to store confirmation
(median ~450), ranker = engine on every pick, plan call recorded on every
record, zero gate failures, zero local fallbacks, zero bridge warnings,
empty bridge error log, four heartbeats on schedule through the 16-minute
window. Pick 126 -- the spot that failed in mock 24 -- had a 25-row plan
with a K/DEF tail behind the engine's rows and landed in 1.2 s.

Narration highlights: McCaffrey went 4th and Taylor 5th, so 6 became
Nacua (waiting ~8 at WR, 59%); McBride at 15 after his survival fell from
97% to 58% in one turn; three RB targets (Achane, Chase Brown, Kyren)
each went the pick before ours, so the first RB was Etienne at 35 --
correctly, because by then the RB market was flat (best 26 vs expected
26); Maye at 46 when Skattebo went; Dowdle at 75 as Warren's handcuff.

Standing: one clean room on the final code, not three. Two more clean
rooms are still owed by the repo's own rule before Saturday's code is
called settled; the faults in 24 and 25 were injected, so those two do
not count toward it.

## Mock 27 — room 10584427 "Hang Time", 10 teams, slot 8 — CLEAN (2 of 3), 15 of 15 via makePick; first room with the refit instrumentation

Trail and scrutiny: reports/mocks/mock27_2026-09-03_0043pt_hang-time_room10584427_seat8_{trail,scrutiny}.md.
Six human seats at the join; one away (seat 5) most of the room.

Roster: Smith-Njigba, Achane, McBride, Garrett Wilson, Maye, Jaylen
Warren, Stevenson, Gainwell, Aaron Jones, Wan'Dale Robinson, Mahomes
(QB2, R11), Pittman, Woody Marks, Eagles DEF, Pineiro K. Legal. Led the
room on projected starting lineup from round 8 on (1473 vs 1447 at pick
78). In the room before pick 1 (reload after the bell, Enter Draft, 7 s on
the pre-draft clock).

Fifteen of fifteen through makePick (374-603 ms), five heartbeats, zero
gate / local / away events; two named bridge warnings (Kaleb Johnson and
Will Reichard are not on the 238-player board -- DATA MISSING, said aloud,
no effect). Second clean room on the final code (mock 26 was the first);
one more owed.

New this room (DECISIONS #35 instrumentation): the driver posted a
players snapshot (1195 players with Yahoo o_rank/avg_pick) through the new
/players route at preflight, stamped every rival pick's first sight, and
the label rule was found wrong on the spot -- the countdown at first sight
belongs to the NEXT turn, so every pick read "clock 30". Corrected the
same hour to time-since-previous-pick (instant <= 2.5 s with a poll gap
<= 2 s; human >= 8 s); the stamps in this room's trail allow the relabel
offline. Our own pick 13 landed 17 s after the previous pick -- the queue
sync holding the loop when the turn opens (review 2026-09-02 finding);
fine on a 60-s clock, thin on 30. Queued for iteration.

Calibration (scorecard): 30-50% shown 43 / observed 52 (n 33); 50-70%
60 / 33; 70-90% 80 / 37 (n 46); 90-100% 96 / 79 (n 97). Same shape as
mocks 24-26 in a mostly human room: the overconfidence is not only the
autopick seats.

## Mock 28 — room 10586715 "Hitch and Go", 10 teams, slot 6 — FORWARD TEST 1 of 2 (DECISIONS #35 G4): fitted autopick knobs live

Bridge started with `--set autopick_list_prob=0.3 --set autopick_need_damp=0.45`
(per-process overrides; config.yaml default unchanged). Five human seats at
the join. First room with the live trail panel and the store fingerprint
check. Scored offline afterwards: the room's realised states at BOTH knob
sets (survival log-loss, 30-70% bucket miss), plus the usual trail and
scrutiny reports. Result recorded below when the room ends.

Result (01:47-02:06 PT, 19 minutes, room ran at autopick pace): 15/15 legal,
BUT picks 6 and 15 (Nacua, Jefferson) were YAHOO autopicks: I entered the
room 2.5 minutes after the bell and injected a minute after entering; the
room ran 17 picks in that gap. Procedural failure, not code: entry and
injection are now one batch that fires when the Enter Draft link appears.
Engine picks 26-146 (13 records) all via the action path, 377-519 ms
confirm. Fingerprint matched the mock baseline. Panel on for the first
time. Five of nine rivals flagged away by round 9; timing labels recorded
instant vs human per pick. Survival scorecard at the fitted point: 50-70%
shown 63% observed 63% (n 30); 70-90% shown 83% observed 53% (n 30);
90-100% shown 96% observed 84% (n 57). The 70-90 miss is the same sign as
the current-knob rooms. To look at in scrutiny: Aaron Jones at 115 ranked
as RB insurance worth ~2 points over a WR cover. Reports:
reports/mocks/mock28_2026-09-03_0151pt_hitch-and-go_room10586715_seat6_*.md.
G4 extension (user, 02:15 PT): four more rooms alternating the live knob
set, both sets scored offline on every room.

## Mock 29 — room 10588125 "Hurry-Up Offense", 10 teams, slot 1 — FORWARD TEST 2 of 5 (DECISIONS #37: actually FITTED knobs live; the restart never took)

02:27-02:41 PT. 15/15 legal; 12 engine picks, all via the action path
(~1.0 s confirm, slower than mock 28's 0.4 s -- background tab). THREE
Yahoo autopicks, both procedural: pick 1 (Gibbs) because the entry batch
navigated to the bare draftclient URL, which skips the Enter Draft link's
auth token and leaves the client on "Error connecting to draft server"
(fixed in the runbook: click the link); picks 80-81 (RJ Harvey, Gainwell)
because the room tab was a BACKGROUND tab (created with tabs_create while
the finished room's tab stayed in front) and Chrome's timer throttling
stalled the driver loop 23 s (log silent 09:37:29-09:37:52 UTC), during
which Yahoo flagged us away and autopicked instantly. Then closing the
finished tab dissolved the Claude tab group and the live tab became
unreachable from pick 86 to the end; the driver finished on its own and
posted the trail. Rule (memory + runbook): one room tab, in front, never
close a tab while a room is live. Survival scorecard at CURRENT: 30-50%
shown 38% observed 5% (n 21); 50-70% shown 61% observed 31% (n 13);
70-90% 82% vs 80% (n 30); 90-100% 98% vs 86% (n 44). Six of nine rivals
away by round 10; 23 instant autopicks labelled. Odd: bench-insurance recs
for Tyrone Tracy carried no survival figure (s None) for several calls.
Reports: reports/mocks/mock29_2026-09-03_0228pt_hurry-up-offense_room10588125_seat1_*.md.

## Mock 30 — room 10589182 "First and Ten", 10 teams, slot 1 — FORWARD TEST 3 of 5: fitted knobs live

02:57-03:15 PT. Entry as one batch: the fetch poll matched my own league's
draft link (regex too loose), but the reload at the bell kept the seat, the
Enter Draft link was clicked at 09:57:08 UTC and the driver was in with
zero picks made. 15/15 legal; 13 engine picks via the action path (~0.95 s
confirm), pick 1 McCaffrey included. TWO Yahoo autopicks (120 Sutton, 121
Goedert): the driver loop went silent 20 s (poll gap 19995 ms, 10:13:09 to
10:13:29 UTC) with the tab IN FRONT -- the whole Chrome window is hidden
while the rig runs unattended, and Chrome's intensive wake-up throttling
(page hidden > 5 min) limits chained setTimeouts to ~1 wake-up a minute.
Yahoo flagged us away inside 4 minutes of a heartbeat and autopicked the
instant the turn opened. Fix shipped after the room: the driver's sleep
runs on a Blob Worker timer (exempt from the throttling; confirmed live on
Yahoo's page, 500 ms -> 508 ms while hidden) with a +5 s guard and a
setTimeout fallback; heartbeat 240 s -> 60 s. On league day the tab is
visible and focused, which is exempt anyway; the fix removes the
dependence. Seat 1 produced the SAME first six engine picks as mock 29
from the same seat (McBride, London, then Swift/Skattebo, G. Wilson, Hurts,
Warren): the engine is deterministic given the board. Survival scorecard
at the fitted point: 30-50% shown 39% observed 12% (n 16); 50-70% 59% vs
11% (n 18); 70-90% 81% vs 78% (n 40); 90-100% 97% vs 83% (n 54). Six of
nine rivals away by round 11. Reports:
reports/mocks/mock30_2026-09-03_0257pt_first-and-ten_room10589182_seat1_*.md.

## Mock 31 — room 10590238 "Goal Line Stand", 10 teams, slot 7 — FORWARD TEST 4 of 5 (DECISIONS #37: actually FITTED knobs live) — CLEAN

03:27-03:39 PT. First room on the throttle-proof driver (sleep via Blob
Worker, heartbeat 60 s). Entry: the in-page poll for the Enter Draft
anchor ran past the 45 s eval budget before the bell; the post-bell reload
plus click landed the driver at 10:28:01 UTC with zero picks made.
15/15 legal, 15/15 ENGINE picks via the action path, zero Yahoo
autopicks, no gate trips, no away flag on us all room (five rivals away
by round 8). Fingerprint matched. Standings by projected lineup: first
from pick 34 on. Survival scorecard at CURRENT: 30-50% shown 43% observed
38% (n 8); 50-70% 61% vs 23% (n 22); 70-90% 82% vs 63% (n 30); 90-100%
96% vs 82% (n 60). Counts as clean room 1 of 2 on the final code
(driver d967a6c+46ec997). Reports:
reports/mocks/mock31_2026-09-03_0328pt_goal-line-stand_room10590238_seat7_*.md.

## Mock 32 — room 10590944 "Pump Fake", 10 teams, slot 2 — FORWARD TEST 5 of 5: fitted knobs live — CLEAN

03:47-04:06 PT. Post-bell reload + Enter Draft click, driver in at
10:47:42 UTC with zero picks. 15/15 legal, 15/15 ENGINE picks via the
action path (415-621 ms confirm), zero Yahoo autopicks, no away flag on
us; four rivals away by round 9. Fingerprint matched; sleep via worker.
Clean room 2 of 2 on the final code. Same seat-2 opening the engine
produced elsewhere tonight (McCaffrey, McBride, London). Survival
scorecard at the fitted point: 30-50% shown 39% observed 0% (n 29);
50-70% 59% vs 41% (n 32); 70-90% 83% vs 82% (n 50); 90-100% 96% vs 92%
(n 74). Reports:
reports/mocks/mock32_2026-09-03_0347pt_pump-fake_room10590944_seat2_*.md.

Night tally (mocks 28-32): 75 legal picks, 68 by the engine, 7 to Yahoo
autopick, every one of the 7 a procedural cause now fixed (late entry x2,
bare client URL x1, background/hidden-tab throttling x4). Last two rooms
clean on the final driver.

## Mock 33 — room 10597994 "Intentional Grounding", 10 teams, slot 5 — pair A of paired-seat series: CURRENT knobs — CLEAN

07:07-07:22 PT. First room of the SAME-SEAT PAIR protocol (user: one room
per knob set from the same draft position). 15/15 legal, 15/15 engine via
the action path, zero autopicks, no away flag on us; three rivals away.
First by projected lineup at the end (1642, next 1557). The live-trail
panel was screenshotted mid-room for the user
(reports/mocks/hud_panel_mock33.png). Lobby scanner upgraded first: room
size = avatar-image cells + link cells, and the join click targets the
draft-position COLUMN, so the seat is chosen, not assigned (one click,
seat 5, size 10 confirmed). Survival scorecard at CURRENT: 30-50% shown
44% observed 27% (n 11); 50-70% 62% vs 47% (n 30); 70-90% 81% vs 76%
(n 59); 90-100% 96% vs 84% (n 67). Offline scoring, both knob sets
(g4_10597994_*.log): log-loss fitted 0.1349 vs current 0.1452 (fitted
better, sixth room of six); 30-49 bucket miss fitted -18 (n172, CI
[-24,-12]) vs current -13 (n155) — BOTH over-promise here in this room,
fitted by more. Pair B is room 10598876, same seat 5, fitted knobs.

## Mock 34 — room 10598876 "Unnecessary Roughness", 10 teams, slot 5 — NOT pair B (entry after bell; DECISIONS #37: actually CURRENT knobs live)

07:33-07:52 PT. Joined as pair B to mock 33 but the entry was interrupted
past the bell: pick 5 (Nacua) went to Yahoo's list, so per the user's
rule this room does NOT count as the pair; mock 35 (same seat 5, fitted,
must be 15/15 engine) replaces it. 14/15 engine picks via the action
path, no other misses. Offline scoring at both knob sets
(g4_10598876_*.log): fitted 0.1492 vs current 0.1594 on log-loss, fitted
better, seventh room of seven. Survival scorecard at the fitted point:
30-50% shown 43% observed 8% (n 13); 70-90% shown 80% observed 40%
(n 53). Reports:
reports/mocks/mock34_2026-09-03_0733pt_unnecessary-roughness_room10598876_seat5_*.md.

## Mock 35 — room 10600461 "Hitch and Go", 10 teams, slot 5 — CLEAN — reproducibility twin of mock 33, NOT pair B (DECISIONS #37: CURRENT knobs live, old bridge)

08:18-08:29 PT. 15/15 legal, 15/15 engine via the action path, zero
autopicks. Intended as pair B (fitted) but served by the stale CURRENT
bridge (forward6, pre-#36 code), discovered through Josh Jacobs still
naming the wire. Result reframed per #37: same seat, same model,
different room = 13/15 picks identical to mock 33 (both differences pure
availability). The engine is reproducible across rooms given the model
and seat. Chrome extension dropped ~70 s mid-room; the driver ran on
unaffected. Offline scoring (g4_10600461_*.log): fitted 0.1287 vs
current 0.1525, fitted better, eighth room of eight. Panel's new
bulleted format was live (driver.js is read from disk per injection);
the pair-math fields were not (bridge-side, stale process). Reports:
reports/mocks/mock35_2026-09-03_0818pt_hitch-and-go_room10600461_seat5_*.md.
Pair B moves to mock 36: seat 5, fitted on the VERIFIED forward9 bridge.

## Mock 36 — room 10601343 "Crackback Block", 10 teams, slot 5 — PAIR B: FITTED knobs + #36 wire fix, verified bridge (forward9) — CLEAN

08:42-09:00 PT. First room on a VERIFIED bridge (preflight call#1; port
owner a child of the launched PID). 15/15 legal, 15/15 engine, zero
autopicks. First live room for the #36 wire fix and the pair-math panel
lines, both confirmed on screen:
- plan lines carried both costs, e.g. pick 1: "McCaffrey · wait costs 11
  · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next)".
- Tracy's insurance printed ~80 (was ~105 against the ghost wire), and
  the honest wire flipped two bench picks to WR/QB insurance exactly as
  the #36 measurement predicted (85 W. Robinson over Gainwell).
Two Chrome-extension drops mid-room; the driver ran through both.

PAIR B vs mock 33 (same seat 5, CURRENT knobs), with mock 35 as the
same-model control (13/15 identical to 33):
- 36 matched 33 on 5 of 15 picks; of the 10 differences, 3 were pure
  availability, 7 were the model/wire (16 Achane over McBride, 25 McBride
  over K. Williams, 45 Skattebo over Adams, 65 Hurts a round early over
  Warren, 76 Tracy over Dowdle, 85 WR insurance over RB, 125 A. Jones
  over Meyers).
- Final lineups: 33 = 1642 pts (1st), 35 = 1642 (1st), 36 = 1665 (1st).
  The fitted+fix room came out 23 pts better, one room, not evidence by
  itself.
- Offline scoring (g4_10601343_*.log): fitted 0.1396 vs current 0.1488,
  fitted better, ninth room of nine. 30-49 bucket (observed - predicted):
  fitted -21 (n130), current -9 (n145); the fitted point still
  over-promises mid-range survival.
  (This line was corrected once: the first commit carried figures typed
  from memory. Rule: numbers enter this log only pasted from the source.)
Survival scorecard at the fitted point: 30-50% shown 44% observed 12%
(n 17); 50-70% 62% vs 39% (n 38). Reports:
reports/mocks/mock36_2026-09-03_0842pt_crackback-block_room10601343_seat5_*.md.
Note: the plans sidecar's rec rows still lack the pair fields (its
serializer is separate from plan_rows); the panel narration in the trail
preserves them. Follow-up: carry pair into plan_detail recs.

## Mock 37 — room 10611562 "Intentional Grounding II", 10 teams, slot 3 — PAIR 2A: CURRENT knobs, verified bridge (forward10) — CLEAN

13:32-13:47 PT. 15/15 legal, 15/15 engine, zero autopicks; preflight
call#1 confirmed the fresh process. First room where the plans sidecar
carries the pair math (155 rec rows with wait cost, own-now, partner,
pick cost). The #36 wire fix showed up in a current-knob room too: 83
DK Metcalf (WR insurance 18) over RJ Harvey (RB 16), the coin-flip the
measurement predicted. Four rivals away most of the room. First by
projected lineup at the end (1643, next 1569). Offline scoring, pasted
from g4_10611562_*.log: fitted objective 0.1524, current 0.1718; 30-49
bucket fitted pred 40 obs 36 (n230), current pred 40 obs 45 (n229).
Reports:
reports/mocks/mock37_2026-09-03_1332pt_intentional-grounding-ii_room10611562_seat3_*.md.
Pair 2B is mock 38: seat 3, FITTED, verified forward11.

## Mock 38 — room 10612448 "Squib Kick", 10 teams, slot 3 — PAIR 2B: FITTED knobs, verified bridge (forward11) — CLEAN

13:57-14:12 PT. 15/15 legal, 15/15 engine, zero autopicks, preflight
call#1. PAIR 2 vs mock 37 (same seat 3, current): 7 same picks, 3
availability differences, 6 model choices (18 Henry over McBride, 23
McBride shifted a round, 58 Jameson Williams before QB, 63 Hurts a slot
later, 123 Gainwell over Marks; the same earlier-RB pattern as pair 1).
Final lineups ONE point apart: 37 current 1643 (1st), 38 fitted 1642
(1st). Offline scoring, pasted from g4_10612448_*.log: fitted objective
0.1502, current 0.1669; 30-49 bucket fitted pred 39 obs 32 (n295),
current pred 39 obs 37 (n256). Eleventh room of eleven for fitted on
log-loss; the mid-band over-promise stays on the fitted side here.
Reports:
reports/mocks/mock38_2026-09-03_1357pt_squib-kick_room10612448_seat3_*.md.

Two-pair summary (33 vs 36 at seat 5; 37 vs 38 at seat 3, with 35 as the
same-model control): the models mostly want the same players, ordered
differently; the fitted one reaches a round earlier for scarce RBs. Final
lineup deltas: +23 fitted (pair 1), -1 fitted (pair 2). Draft outcomes are
a wash live; the offline split (fitted better log-loss every room, worse
30-50 honesty most rooms) is unchanged through 11 rooms.

## Mock 39 — room 10616150 "Wishbone", 10 teams, slot 7 — PAIR 3A: FITTED knobs — CLEAN — first bench rounds on the #38 wire

15:42-16:02 PT. 15/15 legal, 15/15 engine, zero autopicks. The #38
predicted-undrafted wire went live mid-room (bridge forward12 restarted
during round 3, verified port owner; one plan fetch blipped, the cached
plan covered it). Bench prices came out honest for the first time: RJ
Harvey ~18, Adams ~16, Gainwell ~5, and Mahomes-as-QB2 arrived at pick 94,
one round earlier than rooms 37/38 took him, exactly the flip the #38
re-read predicted. Offline scoring, pasted from g4_10616150_*.log: fitted
objective 0.1369, current 0.1508. Caveat for pair 3: rounds 1-6 ran on the
pre-#38 bridge, bench rounds on the fixed one; 3B runs fixed throughout
(the fix only touches bench pricing, so rounds 1-7 stay comparable).
Reports:
reports/mocks/mock39_2026-09-03_1542pt_wishbone_room10616150_seat7_*.md.

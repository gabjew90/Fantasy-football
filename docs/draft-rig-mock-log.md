# Draft rig — mock log

Standing order: run mocks until a full draft completes with **15/15 engine
picks, zero Yahoo autopicks, and zero wrong-player errors**. Every mock ends
with the bug list it produced and the regression test that now covers it.

Target league: **Keefamania**, Yahoo 49649, 10 teams, half-PPR, 15 rounds,
1-minute timer, snake. Draft Sat Sep 5 2026 10:00pm EDT.

Rig: `scripts/draft_driver.js` (in-page), board from
`scripts/export_board_json.py`, tests in `tests/test_draft_driver.py` (node).

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

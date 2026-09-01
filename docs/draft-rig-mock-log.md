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

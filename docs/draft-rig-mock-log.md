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

---

## Open

- On-demand/"Instant" drafts start immediately against bots, but they create a
  **real league team**, so they are not used for practice.
- Autopick, once armed, could not be turned off from the DOM: the warning
  banner carries no control and the queue-panel "Autodraft" toggle does not
  clear it. Treat arming as unrecoverable and never let the clock expire.

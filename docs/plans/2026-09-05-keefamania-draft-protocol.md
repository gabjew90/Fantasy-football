# Keefamania draft-day actuation protocol (hands-free)

Certified-in-progress via live mock rehearsals 2026-08-30/31. Architecture:
the QUEUE is the actuator, clicks are opportunistic, Yahoo-default autopick
is the failure state to prevent.

## The one rule
**The queue must never be empty or stale before a my-turn.** Yahoo drafts
from MY queue the instant my turn starts (autopick mode) or when the clock
expires (live mode). A queue holding the engine's ranked choices = every
pick is an engine pick, immune to all timing failures.

## Loop (validated run 2: 11/15 engine picks, vs 2/15 in run 1)
1. Extract Picks-tab feed + document.title (one JS call).
2. mock_cycle.py -> engine recs for MY next pick.
3. Star engine's top choices until queue depth >= 4 (search by SURNAME,
   verify row by INITIAL + POS + TEAM — "L. McCaffrey WR Was" cost pick
   1.02 before this rule). Remove stale entries after every my-turn.
4. Cadence: <=3 picks away -> poll every ~10s; else 40-60s.
5. On a HOLDING turn: atomic click (Players tab -> search surname -> Draft
   button in the <250-char row matching initial+pos) with queue as backstop.
6. K/DEF enter the queue ONLY after the third-to-last my-pick resolves
   (guardrail: final two picks).

## Known failure modes + fixes (from runs 1-2)
- Wrong-player star/click: row-match must include initial+pos+team. FIXED.
- Queue runs dry mid-burst (bot rooms: 6 picks/15s): keep depth >= 4 and
  refill immediately after every my-turn, not just-in-time. PROTOCOL.
- Stale queue (alternatives for a decided pick linger): rebuild after each
  my-turn. PROTOCOL.
- Yahoo remembers autopick mode across drafts: with a managed queue this is
  a FEATURE (instant engine picks); the Autodraft toggle state is not
  reliably readable — do not fight it.
- Yahoo search wants SURNAMES ("Josh Allen" finds nothing, "Allen" works).
- Feed names abbreviated + status tags (Q/CEL/PUP/IR-R): handled in
  LocalDraft.resolve.

## Saturday setup (draft 7:00 PM PT)
Morning: re-scrape Yahoo ADP -> rebuild keefamania board -> set draft slot
in yaml. Evening: dashboard (KEEFAMANIA DRAFT.bat) + me driving this
protocol via browser; user welcome but not required.

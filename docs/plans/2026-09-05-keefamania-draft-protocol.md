# Keefamania draft-day actuation protocol (hands-free)

> **SUPERSEDED 2026-09-02.** The live procedure is docs/draft-day-runbook.md:
> picks go through Yahoo's own `makePick` with store verification, the click
> is the fallback, the queue is layer 0 (DECISIONS #22; mocks 19-23). The
> loop below (queue + opportunistic clicks, `mock_cycle.py`) is the 08-31
> design and is kept as history. The draft-morning checklist at the end is
> still the checklist.

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

## Certification run 3 (2026-08-31, 10-team live room 10300777, slot 4)
RESULT: 15/15 roster filled, zero Yahoo-default autopicks. Yahoo grades:
A+ McCaffrey, A London, A Egbuka, A+ Vikings DEF, A- Reichard K, A- Hubbard,
A+ Dart, B+ Likely, B- McBride, B- Harrison.
Board integrity: 0 unresolved names, 0 gaps at every cycle after the tab
reload (feed gap-fill recovered picks 18-23 automatically).

### What made it work (vs 2/15 in run 1)
1. IN-PAGE WAIT LOOP — the single biggest fix. Poll `document.title` inside
   the page every 500ms for up to 20s instead of blind 10s sleeps between
   round-trips. Catches the turn the instant it opens; 60s clock is then
   ample (browser actions are 3-5s).
2. Draft buttons EXIST ONLY WHILE ON THE CLOCK, and the player table is
   VIRTUALIZED — off-screen rows are absent from the DOM. So: always
   search-to-filter first, and never expect a Draft button between turns.
   ("Why do you keep missing buttons" - answered.)
3. Queue 4-deep, refilled immediately after every my-turn, each entry
   verified by initial + POS + TEAM before starring.
4. Full-feed transcription every cycle (no placeholders) so the engine
   reasons on the true board.

### Survived mid-draft
The draft tab reset to about:blank around pick 5; the queue still delivered
McCaffrey at pick 4, and re-navigating + gap-filling from the feed restored
a clean board with zero manual repair.

## Draft-morning checklist (Sat 2026-09-05) — DO NOT SKIP
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
       rebuild market + tiers.
3. [ ] Review reports/disagreements.keefamania.csv (board-vs-market
       worklist, ~30 rows). NEVER REVIEWED for this league; the equivalent
       pass for Omnibeta was a full research session.
4. [ ] Review the 9 no_market players (engine-invisible unless activated
       via an override).
5. [ ] Decide whether any Keefamania-specific overrides are needed. The
       file is now league-scoped; Keefamania currently has NONE, which is
       correct-by-default (better no override than a wrong-scoring one).
6. [ ] Set me.draft_slot in leagues/keefamania.yaml once Yahoo assigns it.

Known accepted limitations (not fixable before Saturday):
- No rival seeds: Yahoo gives no draft history, so the Monte Carlo uses
  generic positional tendencies rather than per-manager ones.
- No `verify` command: Yahoo API access is still pending, so the league
  yaml's expected: block is a hand transcription, re-read before the draft.
- Replacement baselines are format-derived, not backtested (v2 §7).

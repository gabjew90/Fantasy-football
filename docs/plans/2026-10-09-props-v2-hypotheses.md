# Props engine v2: what is left to test, after checking the record

Design note. The consolidation plan's first step for a methodology change is to name the
hypothesis and the metric before writing code. Status as of 2026-10-09: one check built
(the line-consistency archive check); the rest is already done in the record or waits on a
decision.

## How this fits the repo rules

CLAUDE.md says "no parallel engines" and "improve by replacing, not adding". There is no
forked `props/engine_v2/`. Studies go in `experiments/props_v2/` (outputs gitignored, 30-day
expiry). A study that passes becomes a candidate inside `props/engine/`, registered `shadow`,
and goes through a pre-registered round judged on `reports/scoreboard.md` with the four-seed
rule (DECISIONS #188, #202).

## The data that exists (checked 2026-10-09)

| Data | Seasons | In `core.fetch` | Live in 2026 |
|---|---|---|---|
| Play-by-play, snap counts, weekly rosters, injury reports, depth charts, schedule with spread and total | through 2026 | yes | yes |
| Participation (11 on-field IDs per play) | 2016-2025 | no | no (2026 file 404; published after the season) |
| FTN charting | 2022-2026 | no | yes, no per-player routes |
| Routes run per player | none | -- | -- |
| Sleeper prop lines | 2026 weeks 2-5, decision / open / close snapshots | `sleeper_lines` | logged every capture |
| DraftKings / FanDuel lines | 2026 weeks 4-5, one snapshot per game | via `props/compare.py` (Odds API) | logged after every capture |
| Settled calls | 2026 weeks 2-4, 2,800 rows | -- | grows weekly |

## The hypotheses, against the record

### H2. The injury bump decays after the first game out -- ALREADY TESTED, NULL

Round 42 (reports/round42_target_handoff.md, DECISIONS #199) pre-registered exactly this:
y for the first game out 0.25 / 0.35 / 0.5, y for a continuing absence 0.25 / 0.15 / 0.10 /
0.05, scored per teammate-game against his season-to-date share plus the handoff, 2022-24.
Result: the shipped rule is about right in continuing absences (actual / predicted 0.99 over
1,049 teammate-games) and slightly under in the first game (1.04 over 308); handing on more
in the first game scores worse because the gain goes to fewer players than the rule spreads
it over. DECISIONS #198's "about double in a continuing absence" was the expert's rough
estimate and was superseded by this measurement. Carries already hand on only the part of the
absence not yet in a teammate's share (round 35, #192).

**What is still open:** the rule's spread across teammates (x) was not tested in round 42.
Round 42's own reading -- the first-game gain is concentrated in fewer players -- points at
the direct backup (depth chart next man up) getting more than his pro-rata part. That is a
different hypothesis from decay, and it would be its own pre-registered round.

### H3. The engine's errors are signed by game script -- MOSTLY DONE

- Calibration by the team's market-implied points: the expert audit (#197) measured it for
  every market; the implied-total test (reports/implied_total_test.md) found backs' rushing
  carries information the model lacks (slope +0.60 in both 2022-23 and 2024-25), receiving and
  passing unresolved. Round 38 (#199) scaled QB passing by implied points; round 39 (#204)
  moved backs' carries 50% toward the market.
- Calibration by role (#198): tight ends' Over ran 5-7 points above the engine; lead backs'
  receiving below.
- Final-margin buckets: tier 2 (reports/tier2_conditional_calibration.md), descriptive only,
  because the final margin selects on the outcome.
- Live cards print the measured row by implied points and by role beside every price.

**What is still open:** spread sign separated from total (implied points mixes them), crossed
with role -- the specific "trailing-team back's receptions" pattern. That is a report on the
harness rows at current settings, with buckets and a pass rule fixed first (same sign in both
test seasons and across four seeds, #202). Not built: it is a small residual of work already
done, and the user ranked it on the assumption it was new.

### Line consistency (the earlier H1) -- the archive check, built

The full version (convert each line to an implied median, compare ratios to a historical
band) is expensive and yards per catch is mostly noise (#206: half-season stability 0.57).
The user's rule: run the cheap archive check, then stop unless it surprises.

`experiments/props_v2/ypc_consistency.py`. For every player-week with both a receptions and a
receiving-yards line in one capture: S = yards line / receptions line, beside T (trailing
yards per catch, last season plus this season before the week), T0 (this season only) and E
(the engine's ratio at the same capture). Population: receptions line 3.5+ (so the ratio of
medians approximates a per-catch rate) and 20+ catches of history.

**Reading rule (fixed before the first run):**
- **Derived (stop):** R^2 of S on T is 0.80 or more, or the median |S - T| / T is under 5%.
- **Surprise (build it):** S has lower mean absolute error than both T and E against realized
  yards per catch on settled weeks, 95% interval (resampling games) excluding zero for each.
- **Neither:** stop unless the user decides otherwise.
- **No verdict** under 30 player-weeks (or under 30 settled ones, unless Derived fired), or
  with a stale or failed input.
- **The verdict on all main lines decides;** the subset where both lines are near even
  (no-vig Over 0.45-0.55) is informational.
- Intervals: 20,000 game-resampling draws under each of four seeds (#202); "better" or
  "worse" only when all four agree. Added after the code review's scratch run showed one
  interval's label (S minus T) flipping with the seed; the verdict did not depend on it.

**Result (2026-10-09, 2026 weeks 2-5, the script reviewed by the code-review skill over
eleven passes before this run).** 594 player-weeks with both lines in one capture; 294 kept
(288 with a receptions line under 3.5, 12 with under 20 catches of history); 226 settled.
The ID join ran on the roster fallback (this sandbox blocks api.sleeper.app); the review's
scratch run of the primary path gave identical IDs on all 294 rows.

| | All main lines (decides) | Both lines near even (informational) |
|---|---|---|
| R^2 of S on T | 0.673 | 0.744 |
| Median abs(S - T) / T | 9.9% | 8.4% |
| MAE vs realized: S / T / E | 3.92 / 4.12 / 4.03 | 3.93 / 4.20 / 4.18 |
| S minus T (widest four-seed interval) | -0.197 (-0.399, +0.003) | -0.275 (-0.512, -0.042) |
| S minus E | -0.116 (-0.292, +0.053) | -0.250 (-0.454, -0.044) |

**Verdict: NEITHER -- stop.** Sleeper's ratio is not just the player's history (R^2 0.67),
but on all main lines it does not beat both history and the engine.

**Post-hoc diagnostic (after the verdict, not part of the rule):** S runs lower than T and E
(10.85 vs 11.83 and 11.64) because a ratio of medians sits below a ratio of means when yards
are right-skewed, and mean absolute error rewards a median-like guess. Scaling T and E to S's
median level (x0.92, x0.94) gives MAE 3.96 and 3.89 against S's 3.92: the engine's ratio,
moved to the median, does as well as Sleeper's. The disagreement left after the level
(S - kT against actual - kT) correlates 0.16 over 226 rows. So the near-even subset's
"surprise" is mostly the median-versus-mean level, not information in the line, and it
supports comparing lines to the engine's median, which the engine already does (it prices
P(X > line) from the simulated distribution).

### The rush + receiving combo check -- not worth building

In week 5, all 27 backs with rushing, receiving and combo lines had combo = rush + receiving
+ 3.5 to 6.5 (mean 4.4, sd 0.96). Sleeper appears to build the combo line from the two
components; the check would almost never fire.

## The two additions -- already running

- **Sleeper against the sportsbooks:** `props/compare.py` since 2026-10-03 (DECISIONS #147).
  DraftKings and FanDuel, one snapshot per game inside the capture window, graded on the
  scorecard when Sleeper's line is off the consensus (0.5 catches, 2.5 yards, 5 passing
  yards) or its no-vig price is 3+ points off. Reading rule: 200+ graded discrepancies with a
  game-clustered interval above zero. 10 graded so far.
- **Closing snapshot:** the guard marks a capture within 60 minutes of kickoff `close`.
  Coverage is the problem, below.

## The capture gap (diagnosed 2026-10-09)

Week 3 has close rows only for the Sunday and Monday night games; week 4 has none for
Thursday or London. On Sunday 2026-09-27 the captures committed at 13:05, 17:46, 21:08 and
23:49 UTC. The workflow's cron is `*/15 * * * *`, but GitHub ran it only 124 times from
inception to 2026-10-09 -- roughly every 2-5 hours (for example 2026-09-26: 05:01, 09:53,
14:15, 17:54, 20:51, 23:26). GitHub treats scheduled workflows as best-effort and drops most
ticks under load. No run landed in the 60 minutes before the 17:00 or 20:05/20:25 kickoffs,
so those games have no close. Week 4's closes came from ticks that happened to land in time.

Root cause: process (relying on GitHub's cron for a 60-minute window), not code. The guard's
logic is right. Options, each a change to the only scheduled workflow, so the user decides:
1. An external scheduler (for example a cron service calling `workflow_dispatch`) at fixed
   times before each kickoff slot. Dispatch currently forces `snapshot_type=decision`, so the
   guard would need to compute the snapshot type on a dispatch too.
2. Extra cron lines at specific minutes before the standard slots (Sunday 16:05, 19:10,
   23:25 UTC; Monday and Thursday 23:20). Still best-effort; fewer ticks dropped at
   non-round minutes, not none.
3. A capture that, once it starts inside the window, waits and re-captures until 5 minutes
   before kickoff (bounded by the 20-minute job timeout, so it covers one slot per run).

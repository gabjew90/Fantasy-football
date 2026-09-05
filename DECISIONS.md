# Auto-Manager build decisions

Judgment calls made during the one-pass build, per the spec's "make the call,
document it, keep going."

## Platform
- **Python 3.10, not 3.11+.** The existing repo venv is 3.10.10 and every library
  used supports it; nothing 3.11-only is needed. Rebuilding the venv mid-season
  risks the draft-era toolchain for zero functional gain. `tzdata` added for
  Windows zoneinfo.
- **Runtime is GitHub Actions (rev 2)** — the rev-1 resident scheduler
  (APScheduler + Windows launcher + systemd unit) was built and then deleted
  when the modified spec landed; workflows in `.github/workflows/` are the
  only runtime now.
- **Same repo, new `manager/` package.** The spec says single repo; draftkit
  already owns Sleeper caching, the schedule parquet, league-scored weekly
  projections with placeholder fallback, lineup math, and ROS values (tiers.csv).
  Manager reuses those as a library and owns everything decision/delivery/scheduling.

## Delivery (rev 3 — GitHub Issues, user's call, 2026-08-27)
- **Primary backend is GitHub Issues, zero secrets**: github-actions[bot]
  opens an issue per event, @mentions the owner (mentions always notify:
  email + GitHub-app push), updates are comments on the same issue. The
  user pointed at this pattern from a prior repo; it beats SMTP here — no
  app password to mint/rotate, mobile push for [ACT NOW] alerts, and the
  issue list doubles as a decision log. Trade-off: GitHub prepends
  "[repo]" to notification subjects; the instruction still fits.
- Issues stay open (auto-closing would fire a second notification per
  event). Close them from the email/app if the list bothers you.

## Delivery (rev 2 — SMTP, superseded but kept as fallback)
- **Gmail SMTP** (`smtplib` stdlib, SSL 465) with app password; multipart
  plain+HTML via a tiny markdown converter — no email library dependency.
  Threading: the stored Message-ID is sent as In-Reply-To on updates, so an
  evolving event stays one thread. Content-hash idempotency is delivery-backend
  agnostic and survived the Discord->email swap unchanged.
- Missing SMTP secrets degrade to stdout with a banner (never crash); dry-run
  prints. Briefs also land in `reports/manager/` (untracked working copies).

## Module 0
- **Slate** = a distinct kickoff datetime (PT) among games involving my rostered
  teams or my current opponent's rostered teams. Inactives = kickoff − 90 min;
  the per-slate check fires at inactives + 10 min.
- **Plan pass rule**: for each day with a relevant slate, one lineup plan pass at
  (earliest inactives that day − 60 min), floored at 4:00 AM PT. A normal Sunday
  (10:00 AM PT slate) lands exactly at the spec's ~7:30 AM PT; a 6:30 AM PT
  international kickoff pulls it to 4:00 AM PT; the Wednesday opener gets its own
  Wednesday pass. This generalizes "earlier on international weeks" to every
  schedule quirk.
- **Missing gametime** in the schedule feed defaults to 1:00 PM ET with a logged
  warning (has not occurred in the 2026 REG schedule).

## Module 1
- **FAAB budgets**: authoritative number is the roster's `waiver_budget_used`
  field; transaction-history reconstruction (summed winning waiver bids) runs as
  a cross-check and powers the per-rival spend detail. A mismatch is reported in
  the brief rather than silently resolved (field wins).
- **Carries inside the 10 / route participation / YPRR** are not in free nflverse
  weekly data. The brief uses snap %, target share, targets, carries, receiving
  yards week-over-week and prints `DATA MISSING: inside-10 carries, routes (not
  in free nflverse weekly data)` per the degrade-gracefully rule.
- **Add ranking** blends: contingency class (inherits an injured starter's role),
  Sleeper trending count (24 h), usage deltas, ROS value from tiers.csv, and my
  positional need over the next 3 bye weeks. Weights in `manager/waiver_brief.py`.

## Module 3
- **Vegas thresholds** per spec: implied team total ≥ 24 → ×1.05, < 18 → ×0.95
  (single 5% notch; anything larger would double-count what projections already
  price in). No `ODDS_API_KEY` → `DATA MISSING: Vegas lines` and no adjustment.

## Module 4
- **Weekly positional stdev assumptions** (points, full PPR): QB 7.0, RB 6.0,
  WR 6.5, TE 5.0, K 4.5, DEF 6.0. Win probability = P(margin > 0) under a normal
  with variance = sum of both lineups' player variances. These are conventional
  fantasy-variance figures, not fitted; revisit once 2026 actuals accumulate.
- Ceiling/floor mode: |projected margin| ≥ 10 flips coin-flip decisions
  (underdog → ceiling, favorite → floor); otherwise projection decides.

## Module 5
- **Veto-risk flag**: offer/ask FantasyCalc value ratio below 0.7 (either
  direction) → "may draw veto votes." Crude by design; the spec forbids building
  a valuation model.
- **Seller window**: after week 5, a team below .500 AND ≥ 2 games out of the
  6th seed.
- **Desperation event**: a rival's optimal-lineup starter freshly Out/IR where I
  roster a same-position player worth 60–140 % of the downed starter (the
  "replacement-shaped asset"), flagged 48 h urgency.
- **Playoff-schedule arbitrage** is qualitative in v1: each target lists his
  team's weeks 15–17 opponents in the rationale. A numeric strength adjustment
  needs a defense-quality model this repo doesn't have yet; faking one would be
  worse than naming the opponents.

## Scheduling (rev 2 — GitHub Actions)
- **weekly.yml carries the PT-fixed events with BOTH possible UTC crons**
  (PDT/PST); `manager cron` guards on Pacific wall-clock inside the run and
  idempotent delivery absorbs the double fire. This avoids editing workflow
  files from within Actions (which would need a PAT with workflow scope — a
  fifth secret the spec doesn't list).
- **gate.yml runs `*/15 * * * *` but the first step is a stdlib-only guard**
  against `state/gate_hours.json` (committed by the planner: every UTC
  (weekday, hour) containing a check window + slack). Off-window ticks exit
  before Python/deps install, in seconds — this is the "derive the windows
  from the committed week plan" requirement without workflow-file rewriting.
- **A check that crashes is still marked done**: `_safe()` already emailed the
  failure with the traceback, and retrying a crashing check every 15 minutes
  for 45 minutes would spam five copies. At-least-once execution applies to
  the attempt; delivery of errors is the fallback path.
- **State is JSON files, not SQLite**: readable git diffs, painless
  `git pull --rebase`, and the Actions concurrency group (`manager-state`,
  no cancel) serializes writers. The old resident scheduler
  (APScheduler/MANAGER.bat/systemd) is deleted — the spec's runtime is Actions.
- Local Python stays 3.10 (venv); workflows pin 3.11. Both are tested by the
  same suite; nothing 3.11-only is used.

## Post-v2 item 1 — rival sampling pool (2026-08-31)
**The hypothesized bug did not reproduce, and the change shipped anyway as
modeling hygiene, not as a fix. Evidence:**

The spec expected `pool_size: 80` to starve the sim's rival pool in the late
rounds and thereby inflate survival. It does not, because the slice is the
top-80 of the REMAINING players, not of the original board. Measured over a
full 10-team Keefamania draft:

    pick  undrafted  old top-80 pool  rolling window  window ADP range
    97    138        80               119             94-151
    124   111        80               98              116-184
    144   91         80               78              124-187

The pool held exactly 80 candidates at every pick; undrafted never fell
below 91. Before/after mean survival at my own picks, rounds 10-14:
0.749/0.747, 0.720/0.717, 0.744/0.743, 0.708/0.708, 0.737/0.737 — deltas of
-0.002 to 0.000, i.e. nothing. The ADP Gaussian already assigns ~zero weight
to candidates far from the current pick, so pool composition beyond that
neighbourhood was never load-bearing.

Kept the rolling window regardless because (a) it makes the pool track the
pick instead of relying on a magic constant whose meaning was ambiguous —
the spec's other stated goal, (b) it is verified harmless, and (c) it is
strictly safer for smaller boards or deeper drafts where the fixed slice
COULD bind. `pool_size` still works as the floor (`pool_min`).

## Keefamania draft prep — disagreements + no_market review (2026-08-31)
Ran the two research passes Omnibeta got and this league initially did not.

**Overrides ported by DIRECTION, not by points.** Scoping overrides per
league (correct — they are absolute points in league scoring) deleted real
research. Ported five to half-PPR by cohort ratio and kept only those whose
INTENT still holds against the new model number: Reed/Golden/Tuten (raise),
Tyson/Allgeier (fade). Dropped three: Gainwell (the half-PPR port, 122,
lands BELOW the model's own 154 — the model already credits the role, so the
override would have silently faded a player it was written to raise),
Charbonnet (availability 'out' supersedes overrides by design), Likely (port
lands on the model; no information added).

**Systematic finding — the QB/TE streamability discount is missing.** The
model_target side of the disagreements worklist is 6 QBs and 3 TEs out of 10
rows (Mahomes rank 28 vs ADP 102, Purdy 42 vs 98, Nix 46 vs 99, Goff 61 vs
114). This is not ten separate insights, it is one structural gap: VORP over
QB10/TE11 credits a starting QB with ~31 points of value while the market
correctly prices the fact that you start one and can stream the position.
research.md Q1 called for an "explicit streamability discount on QB/TE VORP"
and it is NOT implemented (deferred to the January empirical-baseline work,
v2 item 2.2). NOT fixing it before Saturday: it is a valuation change to the
draft layer, it needs the same before/after discipline as any engine change,
and the existing guardrails (QB2 not before round 10, TE cap) already stop
the board from acting on the inflated numbers. Draft-day mitigation: treat
QB/TE model_target rows as noise, not as buy signals.

## Post-v2 item 2 — defense quality (2026-08-31)
- **Metric**: fantasy points allowed per game by defense x position, scored
  with the LEAGUE'S own weights (reuses `dataset.fantasy_points_expr`), from
  nflverse weekly player stats attributed to `opponent_team`. Shrunk toward
  the league mean with weight games/(games + `inseason.matchup_shrink_weeks`)
  — the same convention `weekly.matchup_mult` already used — so week-3 data
  barely moves anything and the metric bites around week 6.
- **Degrade, never null-adjust**: `allowed_ratio` returns None when there is
  no data, the defense is unknown, the position is uncovered, or fewer than
  2 games exist; callers then print DATA MISSING and apply no multiplier.
  Verified live: with nflverse unreachable the lineup brief still renders.
- **Consumer 1, lineup brief**: `matchup_mult` was being fed a hard-coded
  1.0 — the adjustment was a stated goal with no data behind it. It now
  receives the real ratio, capped by `inseason.matchup_cap` (0.10), and the
  brief prints every adjustment >= 2% with before/after points so a flipped
  start/sit is explainable.
- **Consumer 2, trade radar**: playoff-schedule arbitrage returns a NUMBER
  (mean weeks 15-17 opponent ratio, labelled soft/neutral/tough) alongside
  the opponent names, replacing the qualitative placeholder. Per-context
  cached so a radar run computes the dataset once.

## Post-v2 item 3 — standing contingency map (2026-08-31)
- **Informational by construction.** `draftkit/fragility.py` adds three
  display columns (backs_up_pos, starter_fragility, starter_fragility_label)
  and nothing else. Verified mechanically after wiring: proj_pts, vorp, tier
  and value_rank are byte-identical to the pre-change board on BOTH leagues,
  and a unit test asserts the function never mutates a valuation column.
- **Signals used**: position base rate (RB 0.55 > TE 0.35 > WR 0.30 > QB
  0.25), current-season workload, and injury TYPE when a designation exists
  (structural +0.15, soft-tissue +0.08, unrecognised +0). Games-missed
  history is deliberately excluded (research Q6) and the module says so in
  a comment so it survives future edits.
- **Calibration bug caught in verification**: the workload term saturated at
  18 "touches per game", but `hv_touches` counts HIGH-VALUE touches for a
  SEASON (RB p99 = 42, max 50). The term contributed ~nothing and every
  incumbent scored 0.57-0.60. Threshold moved to 40 season high-value
  touches; the range is now 0.26-0.85 and discriminates (CMC's backup 0.85
  high, backup QBs 0.26 low).
- **Depth order is inferred** from within-team, within-position board value —
  no depth-chart feed exists in free data. Players with no identifiable
  incumbent get empty fields rather than a guess. Spot-checked against real
  2026 roster moves (Kamara behind Etienne in NO, Pacheco behind Gibbs in
  DET) and the inference held.
- **Surfaces**: draft board rounds 12+ only, and waiver-brief annotations
  for high/moderate fragility.

## Post-v2 item 4 — in-season age decay (2026-08-31)
- **Scope enforced**: applied where a ROS value is SHOWN or COMPARED (trade
  radar values, waiver annotations), never where one is computed. Verified
  after wiring: tiers.csv and tiers.keefamania.csv proj_pts/vorp/tier/
  value_rank are byte-identical, on both leagues.
- **Shape**: linear in years above a position threshold (RB 27, WR 30, TE 31,
  QB 33), scaled by weeks elapsed so week 1 is a no-op and the full effect
  lands at season end, hard-capped at 10% for the season. Config under
  `inseason.age_decay` with an off switch.
- **UNVALIDATED — conventional wisdom, not evidence.** Same standing as the
  Module 4 positional variance assumptions. research.md Q5 found age is
  MOSTLY PRICED IN by the market, which is precisely why this is capped at
  10%, kept out of every valuation path, and annotated "(unvalidated)"
  wherever it shows. Revisit once 2026 actuals accumulate; delete it if the
  three-lens scoreboard shows it hurting.

## 2026-09-01 — the QB5/TE8 calibration is a design regression, not a fix

The engine is meant to be league-agnostic: point it at a league, derive that
league's parameters from format. `derive_baselines()` does that —
`round(teams × starter demand)`, flex split 45/45/10 — and it is why two
leagues with different sizes and scoring run on one codebase.

Hand-fitting QB5/TE8 for Keefamania bypassed that derivation instead of
repairing it. The measured problem was real (the board reached 35 picks past
ADP on QBs, against +2 for RB and WR), and the patch does fix that league.
But a third league onboarded tomorrow inherits the same broken QB10 and the
same 35-pick reach, and nothing in the code says so.

Kept for Saturday because the draft is four days out and the fitted value is
demonstrably better than the derived one for THIS league. Recorded here as
debt, not as a solution.

The real fix is a derivation that knows streamable positions differ: starter
demand overstates scarcity for QB/TE/K/DEF because their waiver pool stays
startable in a way RB's does not. A candidate worth testing is deriving
replacement from the SHAPE of the positional projection curve — how many
players sit within some band of the positional best — which adapts to league
size and scoring without being fitted to that league's ADP. Put to experts in
docs/expert_review_prompt.md.

Until then, `leagues/keefamania.yaml` carries a hand-tuned constant and the
comment above it must keep saying so.

## 2026-09-01 — slot-conditional VORP: correct, and inert

An expert reviewer identified a real valuation error: a player who starts in
the FLEX competes with the RB/WR you would otherwise put there, not with
replacement at his own position. Measured on the Keefamania board the gap is
37.1 points for every flex-eligible player — McBride 67.1 as a TE against
30.0 in the flex, and Loveland correctly turning negative.

Implemented as a separate `vorp_flex` column (so `vorp` keeps its meaning and
the in-season manager is untouched), carried through write_tiers_csv and both
loaders, consulted by planner.slot_vorp() and the tracker's candidate sort.

**It changed nothing.** Replaying a real 10-team draft across all ten slots:
mean −0.4 lineup VORP, four slots still taking two tight ends.

The reason is structural. The engine ranks positions by urgency, which is a
DIFFERENCE — VORP(best now) − E[VORP(best next turn)] — so a constant
baseline shift cancels exactly. Subtracting 37.1 from every tight end leaves
every gap between tight ends unchanged. The slot-conditional value survives
only in a 0.001x tiebreak, worth 0.037 points of score.

So the double-TE build was never a baseline error. It is TE2 -> TE3 being a
43-point cliff, which makes the position genuinely urgent regardless of which
slot the player fills.

Kept `vorp_flex` anyway: it is correct, free, tested, and the prerequisite for
the real fix. NOT claimed as an improvement, because it measurably is not one.

The real fix is cross-positional urgency — once the TE slot is filled,
subsequent tight ends should join the flex-eligible pool for urgency purposes
rather than remaining their own position. That changes the meaning of every
positional urgency number and touches the comparison every pick flows
through, so it is offseason work, not four-days-out work. Put back to the
expert in docs/expert_followup_prompt.md.

## 2026-09-01 (2) — urgency ranges over unfilled SLOTS, not positions

Expert's answer to the inert result above: the fix is not to reprice the
player, it is to change what urgency ranges over. Position was only ever a
proxy for "market I still need to shop in". Once a dedicated slot is filled
you have left that market, and asking what waiting costs there is a question
about a purchase you are no longer going to make.

Implemented in Tracker._open_markets: one market per UNFILLED roster slot.
A position with an open dedicated slot is its own market on `vorp`; the FLEX
slot is a single market pooling RB+WR+TE priced on `vorp_flex`. Filled
positions get no row at all. When every starter slot is full we are shopping
the bench, which stays per-position on `vorp` as before.

FLEX membership is ALL flex-eligible positions, not just the ones whose
dedicated slot is closed. A market containing only tight ends would have
cancelled the baseline shift a second time, for exactly the reason the first
attempt failed.

### Two things the measurement corrected

**The harness was grading on the ruler under test.** lineup_value() sums
`vorp` for every starter INCLUDING the flex, which is the accounting error
this whole thread is about. Graded that way the change looked like a 9.1-point
regression at one slot. The headline metric is now PROJECTED POINTS of the
starting lineup, which is baseline-free: no choice of replacement level can
move it, so neither arm can grade itself. The sign flipped.

    scripts/slot_replay.py, 22 slots across two real drafts
    10-team log: mean +1.6 pts, 2 better, 0 worse, 8 tied
    12-team log: mean +4.5 pts, 4 better, 0 worse, 8 tied
    combined:    6 slots changed, ALL improvements, none worse

Small (+0.2%) but one-directional, which is what you want from a correctness
fix rather than a tuning change.

**The double-TE build was never the elite-TE-pair I reported.** Every
surviving two-TE roster takes its second tight end in R12 or R13 -- Loveland,
Kittle, Pitts as bench stashes after all nine starter slots are full. No slot,
under either arm, drafts two elite tight ends. The te2_fall guardrail already
made that nearly unreachable: it only admits a TE2 who has fallen 12+ picks
past ADP, and a player who has fallen that far has a low probability of being
taken, hence near-zero urgency. I told the expert four slots drafted two TEs;
that count was real but it was counting bench picks, and I have corrected it.

Bench tight ends are still priced on positional `vorp` (Loveland +23.8 rather
than his -13.4 in the flex). Left alone deliberately: a bench player earns his
keep when a starter is out, and then he does fill his own position's slot, so
positional VORP is the right currency for insurance.

### What the unit tests could and could not show

A synthetic elite-TE-pair fixture would not reproduce the bug, for the reason
above. The behavioural test that does fire is a filled WR slot: planner.
slot_vorp already got the two-pick LEVEL comparison right, so what the market
change actually removes is the greedy URGENCY row -- a WR-vs-WR difference
still arguing "take him now or lose 36 points" for a slot that no longer
exists. Level and timing were two separate halves of the same error, and only
one of them was fixed in the previous session.

Kept behind `engine.slot_markets` (default on) so the A/B stays runnable.

## 2026-09-01 (3) — streaming baselines: blocked on ownership, not on logic

Expert item 2: replace the format baseline with an ORDER STATISTIC over the
residual pool -- the k-th best weekly projection among players you could
actually pick up, k=2 for FAAB and k=3 for rolling waiver priority, floored at
the format baseline so the operator can only tighten VORP. Keefamania is
"Continual rolling list", so k=3.

This matters here because Keefamania's QB5/TE8 were hand-fitted by minimising
|VORP rank - ADP rank|. That is fitting the baseline to the market's opinion,
which is the thing the expert and I both flagged as the wrong way to get a
number. Deriving it from what streaming actually returned would fix that.

Built it (draftkit/baselines.py, scripts/derive_baselines.py) and it does not
work, for a reason worth writing down.

### Two input bugs found by measuring

1. **"Rostered" counted wrong.** Counting board rows with ADP inside the last
   pick put 28 quarterbacks in a 10-team 1-QB league -- 214 players carry an
   ADP of 150 or better into a draft that makes 150 picks, because ADP is a
   mean over drafts. Fixed to the top `teams x rounds` BY ADP.

2. **K and DEF are unmeasurable.** nflverse load_player_stats has no kicking
   or team-defense columns, so every kicker scored exactly 0.0 and the
   operator cheerfully "derived" a K2 baseline. They are excluded now.

### The blocker

Identifying the WAIVER POOL needs to know who was rostered. The cheap proxy --
top N at the position by points per game to date -- is not merely noisy, it is
wrong in the direction that flatters streaming. Roster-ness is sticky from
draft day, so a drafted starter having a quiet few weeks drops out of the top
N and gets scored as a free pickup. On 2025 quarterbacks it offered:

    wk5   Sam Darnold, C.J. Stroud, Bryce Young, Trevor Lawrence
    wk8   Joe Flacco, Spencer Rattler, Tua Tagovailoa, Dillon Gabriel
    wk14  Joe Burrow, Tyrod Taylor, Cam Ward, Geno Smith

and concluded that streaming returns QB3 production. The bracket over k=1..3
and two selectors was non-monotonic (k=1 worse than k=2), which is the
signature of an estimator measuring nothing.

Doing it properly needs prior-season ADP (data/raw/adp_history only goes back
to 2026-08-19) or a percent-rostered time series. Neither is on disk.

### Decision

**Baselines unchanged for Saturday.** QB5/TE8 stay. They remain ADP-fitted and
that is still a weakness, but replacing them with a number from a measurement
I have just shown to be broken would be worse, and reverting to the format
baseline (QB10/TE11) four days out would move elite QB VORP by ~14 points
against the market's revealed pricing on the strength of no new evidence.

The module ships with the ownership set as a REQUIRED argument -- it raises
OwnershipUnavailable rather than guessing -- plus held_from_ownership() ready
for a percent-rostered feed, 18 unit tests, and the contamination reproducible
via `--show-contamination`. What is missing is an input, not logic.

Offseason: pull a percent-rostered series or archive ADP each season, then run
this over several seasons rather than one.

## 2026-09-01 (4) — QB5/TE8 kept because it MEASURABLY drafts better

The previous entry kept the hand-fitted baselines on "no evidence either way",
which was a non-answer. The ownership blocker only stops the STREAMING
derivation; it does not stop asking the operational question directly.

Baselines do not change `proj_pts`. So build the board at each candidate,
draft with each against the same fixed rivals, and score the starting lineup
on projected points -- a number identical across all three boards, which none
of them can move by re-pricing anything (scripts/baseline_bakeoff.py).

    22 draft slots, two real drafts
    current  QB5/TE8     mean 1768.8
    middle   QB7/TE10    mean 1766.1     -2.7    0 better,  4 worse, 18 tied
    format   QB10/TE11   mean 1764.8     -4.0    0 better,  6 worse, 16 tied

Monotone in the same direction and never once better. Small (0.2%), but the
question was which to ship, and the answer is not ambiguous.

This does NOT vindicate the way QB5/TE8 was originally obtained -- fitting to
|VORP rank - ADP rank| is still laundering the market's opinion, and the
number could be right for the wrong reason. What it establishes is that
replacing it with the format baseline would cost real points against real
rooms, so the honest fitting critique is not a reason to change it four days
out. Deriving it properly stays an offseason item.

### Loose thread found while measuring

Every single roster in all 22 slots drafts a second quarterback. In a 10-team
1-QB league whose baseline asserts QBs are freely streamable, a rostered QB2
is close to a wasted pick, and the two claims cannot both be right. The
qb2_earliest_round=10 gate permits it and nothing pushes back. Worth testing a
hard one-QB variant.

## 2026-09-01 (5) — the hand-fitted baseline is GONE

Correcting the previous entry, which kept QB5/TE8 because it drafted better.
It did. That was the wrong question. QB5 is a per-league magic number tuned to
that league's ADP, and a new league onboarded tomorrow would never get one --
so "baselines are derived per league, never hand-tuned" was not true, and
picking the best magic number accepted the premise instead of attacking it.

### Where the constant was actually doing its work

Disabling the two-pick planner and re-running the bake-off:

    planner ON    QB5/TE8 1768.8   QB10/TE11 1764.8   spread 4.0   6/22 differ
    planner OFF   QB5/TE8 1759.7   QB10/TE11 1760.1   spread 0.4   2/22 differ

All of it lives in pair_rank. Urgency is a DIFFERENCE, so the baseline cancels
there exactly; pair_rank sums raw VORP LEVELS across positions, and levels are
only commensurable if the baseline is right.

So QB5 was never a measurement of replacement level. It was a fudge that
suppressed quarterback level so the planner would stop drafting them early --
which is why it beat the "correct" number. Right answer, wrong reason, and
unavailable to any other league.

### The fix: measure against what you actually end up with

A season-long constant has to answer "what is the alternative to a QB?" with
one number for the whole draft. The real answer moves. In round 2 with
thirteen picks left the alternative is a startable quarterback, so an early one
is worth little. The alternative to a running back in the same league is RB40,
so he is worth a lot. One number cannot say both, which is why it had to be
fitted.

Tracker._fallback_points computes, per position, the best projected player
whose ADP says he survives to my LAST starter-filling pick (my S-th remaining
pick, S = open starter slots). planner.own_value then measures a candidate as
proj_pts - fallback[pos], and the partner term is converted out of VORP through
the market's recovered replacement level so both sides speak one currency.

No league constant enters. It adapts to teams, roster size, remaining picks and
the live board by construction.

    22 slots, three baselines (QB5/TE8, QB7/TE10, QB10/TE11)
    before   spread 4.0 pts   4-6 slots differ
    after    spread 0.4 pts   0-1 slots differ

Cost: 3.1 points against the fitted baseline, +1.3 against the format one. We
gave up an advantage that only existed because of the flaw.

### Consequences

* leagues/keefamania.yaml is now a PURE format derivation -- QB10 RB24 WR24
  TE11 K10 DEF10 is exactly what onboard.derive_baselines(10, roster) returns.
  Board rebuilt.
* onboard.slot_counts did not recognise Yahoo's "W/R/T" flex slot and silently
  dropped it from demand, so every Yahoo league was getting RB20/WR20 instead
  of RB24/WR24. Unknown STARTING slots now raise instead of vanishing.
* Behind engine.adaptive_fallback (default on) so the A/B stays runnable.

Still open: the fallback uses ADP for AVAILABILITY (who survives to a pick),
which is a structural fact rather than the market's opinion of value -- the
distinction that matters. Replacing it with the survival simulation, which
already models the room, is the offseason version.

## 2026-09-01 (6) — correction-pass Phase 1, and what the cut list got wrong

An external correction pass proposed four critical fixes, a draft-day
de-pressuring phase, and a five-item cut list. Verified each claim before
acting; Phase 1 was four for four, the cut list was three for five.

### Phase 1 — all confirmed, all fixed

1. **Stale overrides.** All five rows of overrides.keefamania.csv carried
   `date_checked: 2026-08-31` while `source` said "porting 2026-08-19
   research to half-PPR". Nothing was verified on the 31st; a ratio rescale
   happened. Added a `status` column, restored the true fact date, and made
   freshness structural: only `confirmed` rows are applied, `candidate` rows
   are INERT and reported at every build. A file with no status column is
   treated as entirely candidate -- an unmarked file predates the contract, so
   nothing in it has been checked under it. Omnibeta's eight rows carry real
   dated ESPN sources matching their date_checked and are honestly `confirmed`.
2. **Fragility keywords.** STRUCTURAL contained "foot" and "knee" -- body
   parts, not injury types -- so a knee bruise scored like a torn ACL. Removed
   both, added mcl/pcl/meniscus. Unrecognised still contributes zero, so narrow
   is the safe direction.
3. **Age decay opt-in.** decay_factor defaulted `enabled` to True. An
   unvalidated adjustment that is on by default is on in leagues nobody chose
   it for. Flipped to False and disabled explicitly; OFF for both leagues until
   2026 actuals can validate it.
4. **State hygiene.** Six commits swept state/*.json into feature commits
   (3720a78, 969e059, 6415db7, 4ec05e4, 4a6dfac, 2c30c0a) -- what `git add -A`
   does silently, and I use it habitually. Added
   scripts/check_commit_hygiene.py, a .githooks/pre-commit, and a CI job,
   because the hook is opt-in per clone and cannot be the only defence.

### Standing ADP tilts: OFF for Saturday

Not because they were measured to be bad -- they cannot be measured this way.
Tilts alter proj_pts, so a replay grades a change of belief against that same
belief and each arm wins on its own ruler: judged by the untilted model,
turning them off is +1.7 points; judged by the tilted model, -33.3. (A first
run reported +49.6 for turning them off, which was pure ruler artifact.)

What the replay does establish: 0 of 22 rosters were identical with tilts on
vs off. They are a material, unvalidated intervention on every single pick.
Carrying that blind into a real draft is a risk decision, and the answer is no.
Theses kept in the research file for re-adoption behind a CLV backtest.

### Cut list — measured, 22 slots, before deciding

    item  9  delete two-pick planner        predicted <1 pt   MEASURED -6.0, 19/22 rosters change
    item 10  delete fat-tail + run escal.   predicted ?       MEASURED  0.0,  0/22 rosters change
    item 11  delete standing ADP tilts      predicted small   NOT MEASURABLE by replay (above)

* **Item 9 rejected.** Off by 6x and the wrong sign. Its premise, "greedy
  urgency replaces it", is now specifically wrong: after 2026-09-01 pair_rank
  is where cross-position comparison happens, so deleting it does not simplify
  the engine, it removes the comparison.
* **Item 10 accepted** in principle -- zero effect on any drafted roster. Still
  needs the CLV survival check first, since those terms move the displayed
  "X% chance he's still there".
* **Item 12 is factually wrong.** There is no flex-split derivation machinery
  to delete; FLEX_SPLIT is already one hardcoded dict in onboard.py and is not
  PPR-dependent.
* **Item 13 partly stale.** The streamability discount was already deleted on
  2026-09-01 by making the engine baseline-invariant.
* **Item 14** -- DECISIONS.md has zero mentions of the nightly ADP diff, which
  by the document's own test means cut. Left alone: absence from the log may
  mean unlogged rather than unused, and that is the user's call.

The document told me to record deltas "so the cut is measured, not assumed",
then pre-stated the expected deltas. Two were wrong. CLAUDE.md now carries the
rule in the stronger form: measure BEFORE cutting, and a predicted delta is
not a measured one.

## 2026-09-01 (7) — bench realities: insurance pricing, default OFF pending (c)

Zoomed out before building. The engine's one-sentence rule -- biggest
remaining value at positions still needed, measured against what is freely
available later -- was applied to starters (slot markets, adaptive fallback)
but never to the BENCH. Bench rounds priced candidates as VORP against the
starter baseline, so a backup QB measured against QB10 read +20 when the
thing he competes with is the waiver wire, where he is +4. That is the whole
QB2 mechanism; no new subsystem, just clause 5 applied to clause 4.

### The formula (draftkit/bench.py)

    value = weeks needed x weekly edge over the wire
    weeks needed = (my starters at pos, flex included) x (position absent rate + bye)
    wire         = k-th best player the market leaves undrafted (ADP beyond
                   the last pick), k from waiver format (rolling list -> 3)
    handcuff     = backup of MY starter gets the measured uplift x1.46,
                   capped at the starter's own rate

### Two corrections taken from review before it ran

* The frequency term must NOT be per-player exp_games. That column is the
  games-missed durability haircut removed 2026-08-30 (research Q6), kept as
  informational only; my first draft put it at the centre of every bench
  decision and would then have validated it with injury draws from the same
  column. Replaced with POSITION base rates, derived ex ante over six season
  pairs (scripts/derive_bench_rates.py):

      QB 2.56  RB 3.13  WR 2.69  TE 2.93   absent weeks, injury only, + 1 bye
      (three-pair run had QB highest at 3.29 -- 35-player noise; N is now
       70/142/144/71. Zero-game seasons excluded, so biased LOW.)

* (a) waiver-level pricing and (b) frequency ship as ONE change. (a) alone
  makes the QB2 WORSE: his edge over the wire is honestly +3.8/wk, larger
  than a bench RB's +2.5, so without frequency the engine would take him
  more confidently than before. Frequency is load-bearing, not a refinement.

### Handcuff share: measured, and the first measurement was wrong

Max-of-teammates in the starter's absent week read 1.28 of the STARTER's
rate -- the fill-in outscoring the man he replaced. That is picking the right
handcuff with hindsight. The ex-ante backup (best teammate in weeks the
starter PLAYED) produces 1.06 of the starter's rate in absent weeks against
0.73 standalone: uplift x1.46 over his own projection, which is the form the
formula uses. n=277 starter-absent weeks.

### A/B on the two real logs, 22 slots

    bench_insurance   lineup pts   2+QB rosters   R10+ skill picks
    off               1815.7       22/22          RB 41  WR 21  QB 22  TE 4
    on                1815.6        0/22          RB 24  WR 64

Lineup points cannot move -- the metric scores starters only -- so this is
NOT validation, it is confirmation the mechanism fires. Two things it
surfaces, deliberately left alone rather than tuned:

* The bench tilted to WR. Three WR starters (two + flex) versus two RB
  starters means a bench WR covers more absence-weeks, and that term is
  linear in starters covered. Plausible; unproven.
* QB2 went to zero everywhere. Also plausible for a 10-team 1-QB league;
  also unproven, and a 12-team league with a thinner wire should not read 0.

Both are exactly what the season-level replay (c) exists to grade: start
lineups week by week with absences drawn from the empirical position
distribution -- sharing NO input with the formula -- and compare realised
points between insurance-priced and VORP-priced benches on both leagues'
boards. Default stays OFF until that shows a win.

## 2026-09-01 (8) — season replay verdict: insurance pricing wins where the wire is thin

scripts/season_replay.py — drafts a roster both ways, then plays 17-week
seasons against it with absences drawn from the empirical positional
distributions (never the formula's means), handcuff production from the
observed share distribution, and empty slots filled by a uniform draw from
the top 2k undrafted. Common random numbers per (sim, player). A test greps
the harness for the formula's constant names so they cannot be wired back in.

    insurance-priced bench minus VORP-priced bench, pts per season
    keefamania  10-team, 1 flex, rolling list   +2.6  (se 0.5)  5 better  5 worse   600 seasons/roster
    omnibeta    12-team, 2 flex, FAAB          +33.2  (se 1.6)  9 better  3 worse   200 seasons/roster

Omnibeta is a clear win (+1.6%). Keefamania is +0.15% -- detectable, not
meaningful, and split 5/5 at the slot level with per-slot swings of 10-28
points, so the average hides two opposite effects.

### What the split is

Read the roster shapes. Every Keefamania slot that LOST moved to a 6th WR
(slots 1, 4, 6, 8, 10: RB5-6 WR5-6). Every slot that WON moved to RB depth
(2, 5, 9, 3: RB6-7). The formula's exposure term is linear in starters
covered -- three WR starters make a bench WR look 50% more valuable than a
bench RB behind two -- but it ignores depth ALREADY on the bench. A 6th WR
behind three healthy starters and two backups plays only when three WRs are
out at once, which the empirical rates make rare. The marginal bench player
at a position covers the marginal simultaneous absence, not the first.

That is a modelling error the grader found, not a parameter to tune: the
formula should price the (n+1)th backup at P(>= n+1 starters at the position
absent in the same week), derived from the same base rates. Pre-registered
expectation if built: the 6th-WR picks disappear, Keefamania's losing slots
flip or go flat, Omnibeta does not degrade (its wins came from RB depth, which
the change should leave alone). If Omnibeta degrades, the refinement is wrong.

### Decision

engine.bench_insurance stays OFF by default. The bar was a win on both
leagues; Keefamania is not one. Turning it on for Omnibeta alone on the
strength of this replay would be choosing per league on the test set, and
Omnibeta has already drafted. Revisit after the marginal-depth refinement.

Also visible in both leagues: the insurance arm leans on the wire roughly
twice as hard (Keefamania ~50 -> ~85 pts/season). That is the QB2's bye and
injury weeks moving to waivers, priced at k=3 friction in the pool but at
zero claim cost. In a rolling-list league that cost is not zero; it is the
waiver-priority reasoning the in-season brief owes (cleanup item 4).

## 2026-09-01 (9) — depth-aware insurance pricing is ON

The pre-registered prediction from entry #8, and what happened:

    prediction                              result
    6th-WR picks disappear                  yes -- no Keefamania roster carries WR5+ on the insurance arm
    Keefamania losing slots flip or flat    yes -- 5 better / 5 worse  ->  8 better / 0 worse / 2 tied
    Omnibeta does not degrade               mostly -- 9/3/0 -> 10/1/1, but the mean fell +33.2 -> +23.9

    insurance-priced bench minus VORP-priced bench, pts per season
    keefamania   +2.6 (se 0.5)  5/5/0   ->   +12.9 (se 0.4)  8/0/2    600 seasons per roster
    omnibeta    +33.2 (se 1.6)  9/3/0   ->   +23.9 (se 1.1)  10/1/1   200 seasons per roster

The Omnibeta drop is worth being honest about rather than rounding to "held".
The earlier +33 was carried by two RB9/WR2 rosters (slots 2 and 9, +76 and
+58) that the depth term reins in to RB6-7. What remains is a smaller, more
even win with fewer losers, and the insurance arm now leans LESS on the wire
in Omnibeta where before it leaned more. I read that as the refinement
removing an over-bet rather than removing signal, but the prediction as
written said "does not degrade" and the mean did.

### Decision

engine.bench_insurance defaults ON. The bar was a win on both leagues on a
grader that shares no constant with the formula, and both clear it.

### What the QB2 turned out to be

The insurance arm still drafts a second quarterback in every Keefamania
roster. The depth term ranks the FIRST QB reserve above the SECOND RB or WR
reserve -- one starter, 3.6 expected weeks, +3.8/wk over the wire beats a
second RB reserve who plays only when both RB starters sit -- and the season
replay rewards that ordering. So the original symptom was never "a backup QB
is wrong". It was "a backup QB before the first RB reserve is wrong", which
is what the pricing now says. I had been telling the user the QB2 was close
to a wasted pick; the measured answer is narrower than that.

### Stop here

This formula was revised once after seeing the grader, with the change
pre-registered and its Omnibeta half only partly confirmed. A second revision
against the same two draft logs would be fitting the test set. The next
evidence that should move it is out of sample: 2026 actuals, or the grader
run on drafts it has not seen.

Grader limits carried forward: flat proj/17 weekly scoring (no variance), no
in-season adds beyond filling an empty slot from the wire, zero claim cost in
a rolling-list league, byes and injuries drawn independently across
teammates.

## 2026-09-01 (10) — mock 11: the driver, not the engine

Ran the first live mock on the rebuilt engine and drafted four tight ends.
Not one of them was the engine's call: every time the bridge was handed a
correct state it answered sensibly, and the one place it could have said
"TE3" -- the unguardrailed depth tail -- it now cannot. The failures were all
in the page-side driver reading Yahoo's UI, and the largest was a layout
difference (expanded stats view) that made every row lookup miss and every
miss get recorded as "drafted". Seven defects, each with a fix and a test;
docs/draft-rig-mock-log.md has the table.

Two structural changes came out of it:

* The page now sends THREE views of the draft -- the Picks feed, the roster
  panel, and the header's pick number -- and the bridge reconciles them,
  because each one fails alone. Both sides also remember every pick ever
  seen (sessionStorage in the page, a per-draft union in the bridge).
* The plan's depth tail goes through _pos_allowed like every other candidate.

Standing rules added to the checklist: never reload the draft page mid-draft
(the driver loop dies, autopick arms, and re-evaluating the driver does not
stop the old loop); never trust a single UI reading -- the layout can differ
room to room.

The mock that finally had the engine right produced the worst roster of the
eleven. That is the correct order to find things in.

## 2026-09-01 (11) — layer 0 is live: Yahoo's own autopick now walks our board

Design (docs/superpowers/specs/2026-09-01-draft-rig-foolproof-design.md):
three layers, each a strict fallback for the one above, and a layer may act
only when its readings pass consistency checks. The floor is Yahoo itself.

Done tonight, on the REAL league (49649, team 3):

* The Edit Pre-Draft Ranks page has an Import dialog that takes pasted
  `rank,name,team,position` lines and REPLACES the list in one shot. Our 240
  (board order, K/DEF last, availability=out excluded) imported as 228 in
  exact order; Save persisted it; the pub-api `teams` endpoint reads
  `has_preranks: 1` for us. Three "out" players are on Do-Not-Draft.
* Not matched by Yahoo's importer: DK Metcalf and J.K. Dobbins (initials --
  neither spelling tried landed) and ten players outside Yahoo's 300-list.
  Visible via PR.unmatched(); the two that matter can be starred by hand.
  [Corrected 2026-09-02: Metcalf and Dobbins HAD landed (ranks 76 and 85).
  PR.unmatched()'s row parser read the "K" in their names as the kicker
  position. Fixed with a test; the twelve real misses are all deep bench.]
* The star-by-star path works and keeps click order but slows as the list
  grows (0.9s/click at 50, 1.5s at 100); kept for touch-ups only.
* One rival (team 9) has pre-ranks set too.

Also found: pub-api.fantasysports.yahoo.com/fantasy/v3/{draftstatus,
settings,teams}/nfl/<league> answers with session cookies from any Yahoo
page -- settings carries roster_positions, position_draft_caps, draft_time,
draft_pick_duration, waiver_rule. That is the `verify` input we were waiting
on Yahoo's API approval for.

Draft-morning runbook for layer 0 (after the board rebuild):
    open /f1/49649/3/editprerank; eval prerank.js from the bridge;
    PR.load(board); await PR.import(); await PR.dnd(); PR.save();
    await PR.unmatched()  -> star the important gaps by hand
    confirm has_preranks == "1" via the teams endpoint.

## 2026-09-01 (12) — mock 12: the engine drafted cleanly; Yahoo's idle timer took over at round 11

Design step 2 done: the live channel was investigated and something better
was found. The draft client's Redux store is reachable from the page and
holds the entire draft as data. The driver now reads state from it and
falls back to page text loudly; only the row click still touches the DOM.
Offline DOM tests (jsdom + captured fixtures) cover the readers that remain.

Mock 12 itself: fourteen of fifteen picks sane, one TE, no guardrail
violations, every pick through round 10 made live by the engine. From round
11 Yahoo had flagged us away (inactivity -- our clicks do not count) and its
autopick drafted from our queue. The floor held, which is the design working,
but live control must not be lost to an idle timer: keepAlive() now fakes
activity each cycle and disarms Autodraft when the store says we are away.

Bar for "perfect" (user, 2026-09-01): every one of our picks made by the
engine at the turn, no autopick, gates never trip, roster passes every
guardrail. Mock 12 fails only on the autopick clause. Mock 13 tests keepAlive
and the store-fed driver together.

## 2026-09-02 (13) — mock 13: keepAlive held for eight rounds; the endgame found three more

Namesakes: the bridge keyed players on first-initial + surname, which is how
Yahoo renders a row but not an identity ("A. Brown" is two starting WRs;
"B. Robinson" two Falcons backs). A.J. Brown, gone at pick 17, led the
engine's plan for thirty picks. yahoo_bridge.PlayerIndex resolves full names
first and, for abbreviated text, picks the namesake not already accounted
for. The roster panel is attributed by player id the same way.

The driver's guardrail is now structural only. Its "no VORP ≤ 0 pick once we
hold a stash" rule refused every candidate at pick 86 — bench-insurance rows
the engine prices above zero — and the clock ran out. Whether a bench pick
is worth taking is bench.py's decision; the driver keeps the roster legal
(positions, K/DEF reservation, TE2 rule) and nothing else.

State comes from the store, never from a banner. Yahoo's "put into autopick
mode" notice outlives the disarm, and treating it as state made the driver
toggle Autodraft on and off every two seconds and stand itself down at each
turn. autopickArmed(), keepAlive() and the pick verification all read the
store first; page text is the fallback when there is no store.

Verified means verified: a pick is ours when the store records THIS player
at OUR pick number, not when the roster count grew.

Bar for "perfect" (user, 2026-09-01) — mock 13 fails on three clauses
(missed pick, autopick fired, live control lost from round 9). Two of the
three engine-side deliveries (namesakes, structural-only guardrail) are the
kind of defect that would have cost real picks on Saturday. Mock 14 runs the
fixed driver end to end; the open question is whether the store's away flag
can diverge from the server's autopick state without the toggle storm.

## 2026-09-02 (14) — mock 14: perfect on the stated bar

Fifteen of fifteen picks made by the engine at the turn, store-verified, no
autopick, no gate trip, legal roster. The three fixes from mock 13 (namesake
resolver, structural-only guardrail, store-first autopick state) were all
exercised live and held. The rig is not fragile in the way mocks 11-13
were; what remains to grade is the engine's picks, which is the CLV retro's
job once closing ADP exists.

Layer 0 on the real league is now complete: the twelve names Yahoo's importer
skipped were added by hand through the page's surname search (all deep
bench, appended in board order), and DK Metcalf -- who had been appended to
the bottom by a hand-star on 2026-09-01 -- was moved to his board position
(72) with the page's Select -> "Move after..." flow. 240 of 240, saved,
has_preranks confirmed. Both flows are ported into scripts/prerank_driver.js
(PR.addMissing, PR.moveAfter) for the draft-morning rebuild.

## 2026-09-02 (15) — mock 15: clean again, at human pace

Second consecutive perfect mock on the stated bar (15/15 live, store-
verified, no autopick, no gate trip, legal roster), this time in a room with
nine humans and a 30-second clock. The rig's failure modes from mocks 11–13
have not recurred across two full drafts. Stopping the mock series here: a
further run tells us nothing new about the rig, and the engine's choices are
graded by the CLV retro against closing ADP, not by more mocks.

Draft morning (2026-09-05): docs/draft-day-runbook.md, unchanged in shape —
rebuild board, layer 0 via PR.import/dnd/save + PR.addMissing/moveAfter
touch-ups, then the room with the driver injected from the bridge.

## 2026-09-02 (16) — projection overhaul, Step 0: the comparison reproduced, and it disagrees with the brief

scripts/sheet_compare.py reads the FantasyPros sheet's position tabs (AVG /
high / low stat lines), scores them in each league's own settings, scales
17-game lines to the board's 16-game basis, joins on the DynastyProcess
name normalisation, and reports rank correlation, bias, largest
disagreements and deep-rank bands per position. It is the acceptance test
for item 1. Reports: reports/sheet_compare.{keefamania,omnibeta}.md.

Judgment calls:
* One workbook, not two. The two attachments are byte-identical (same md5),
  both configured for Keefamania. The stat lines are format-free, so the
  Omnibeta comparison rescored the same lines in Omnibeta's scoring; only
  the sheet's Aggregate/FLEX/RISK tabs are league-configured and those are
  not used by the comparison.
* Raw AVG lines, not the Aggregate tab. The Aggregate AVG already carries the
  sheet's missed-games adjustment (about 12–15% at the top), which is a
  different convention from the board's flat 16/17. Comparing against it
  flips the sign of the top-36 bias; my first quick look (chat, earlier
  today) did exactly that and reported the board as fat everywhere. It is
  not.
* Games convention: sheet lines x 16/17. Stated in the report header.

What the numbers say (both leagues agree):
* QB rank correlation is 0.81–0.85 over the sheet's top 36, not 0.70. The
  disagreement is concentrated: Daniels 3->15, Lamar 2->11, Dart 7->16,
  Burrow 6->13 down; Stafford 15->4, Mahomes 11->5, Lawrence 8->3 up.
* The board is BELOW the sheet across the top 36 at every position (bias
  -9 to -22), and below it at RB 37–48 (-16/-20). The "RB 37 and beyond 30
  to 120 above" claim holds only from RB 49 (+17/+22) and RB 61–80
  (+64/+71). The same floor appears at TE 37+ (+42/+52) and, most extremely,
  at QB backups (Winston/Rattler/Mills: sheet ~10, board ~200). WR shows no
  tail floor at all (61–80: +0/+1).
* So the tail defect is real but starts one band deeper than the brief
  says, is absent at WR as the brief says, and its worst case is QB backups
  the sheet projects as non-starters.

Per the brief: numbers differ materially, so stop and report before item 1.

## 2026-09-02 (17) — projection overhaul, item 1: stat lines as a parallel market source

draftkit/consensus.py fetches Sleeper's season stat-line projections per
position, scores them with the league yaml's scoring key-for-key, scales the
17-game lines onto the board's expected_games basis, and joins by Sleeper id
(exact; no name matching). default_projection carries the result as
`proj_consensus_pts` and, only when `projections.market_source: stat_lines`,
substitutes it for the log-rank curve where it exists (the curve stays the
fallback for players Rotowire does not project). Default is still
`ecr_curve`: proj_pts is byte-identical to before on both boards (0 of 243 /
298 rows moved); 203 of 243 Keefamania players and the equivalent in Omnibeta
carry the column. The tiers csv now also writes proj_model_pts and
proj_market_pts so the blend can be graded part by part.

Corrections to the brief, before anyone reads the numbers:
* This is Rotowire, not consensus. Sleeper serves one shop's lines. It is
  strictly more informative than a rank curve, and it is one opinion where
  ECR was many. The FantasyPros sheet is the consensus and is a one-time
  join. Named accordingly in the code (comments) even though the column is
  called proj_consensus_pts for continuity with the brief.
* The endpoint is new to the repo. The existing client hits the WEEKLY
  projections path for the in-season manager; season totals are a different
  URL, cached under data/raw with a 12 h TTL.
* `gp` = 18 in these rows is a week count, recorded for audit, never used to
  scale. line_games = 17 is the convention; config projections.consensus.

Acceptance (scripts/sheet_compare.py --column proj_consensus_pts, both
leagues agree; Keefamania shown, Spearman over the sheet's top 36 / deep
band bias board-minus-sheet):

    pos   blend today   stat lines alone     tail (blend -> lines)
    QB    0.81          0.97                 backups +217 -> +1
    RB    0.93          0.98                 61-80: +71 -> +14
    WR    0.93          0.88                 none either way
    TE    0.88          0.88                 61-80: +67 -> +25

So the stat lines fix exactly the two things Step 0 isolated -- the QB
ordering and the deep floor at QB/RB/TE -- and are slightly WORSE than the
blend at WR (Rotowire and FantasyPros disagree at WR more than our board
does). The lines also sit 15-25 points below the sheet at RB1-36: Rotowire
is the conservative shop. None of this flips the default: per the brief the
backtest (item 2) decides which market term is default and at what weight.

## 2026-09-02 (18) — projection overhaul, usage-side fix 1: role gating

The usage half projected 2025 per-game rates forward regardless of 2026
role: Jameis Winston (two 2025 starts, 22 PPG) was ~227 on the board,
Rattler ~205, Mills ~193, against ~10-30 from every projector, because a
PPG number cannot say "he will not start". draftkit/role.py scales the
MODEL term by a depth-chart backup's expected share of starting weeks --
P(at least his depth beyond the starters are out in a week) at the
position's ex-ante absence rate (bench.ABSENT_WEEKS), no bye term -- so
QB2 0.15, RB3 0.33, RB4 0.03, TE2 0.17, QB3/TE3 0.

Judgment calls:
* Two sources must agree. The gate fires only when the market rank within
  position is also past teams x starters, OR there is no ECR/ADP at all.
  The second clause was added after the first build missed Rattler and
  Mills: they reached the board through the no-market floor, and "no rank"
  had been read as unknown when it is the market's strongest "backup".
* WR is not gated. Sleeper's receiver chart is three sub-charts (LWR/RWR/
  SWR) with their own orders plus unslotted receivers numbered 6-11; the
  order is not an overall depth (Davante Adams reads RWR 2, Travis Hunter
  SWR 4). The first build zeroed Pearsall and Calvin Austin on that. QB/RB/
  TE charts are single ordered lists; the chart position must also match
  the fantasy position (an H-back filed under RB is left alone).
* Model term only, applied after the market curve is fitted, so the curve
  is still fitted on ungated veteran points. Market-implied players (no
  2025 stats) are untouched -- that is the market half's business (item 1).
* Applied to everyone with one rule; the config carries the starters map
  (QB 1, RB 2, WR 3, TE 1) under projections.role_gate.

Effect (Keefamania / Omnibeta): 14 / 22 players gated, none of them a
starter by either source; Winston, Vidal, Knight, Theo Johnson and Tonges
fall off the Keefamania board entirely; no ungated row moved. Against the
sheet the QB 49-60 band goes +189 -> +20 and RB 61-80 +71 -> +50; what
remains in those bands is market-implied rows the gate cannot reach.
Zero-share players (QB3s) project 0 from the model term; the market curve
still gives them ~200 where it has a rank for them, which is item 1's
case in one line.

## 2026-09-02 (19) — projection overhaul, usage-side fix 2: QB rushing in the usage model

The usage regression (ppg ~ WOPR + high-value touches) is receiving- and
goal-line-centric, so QBs skipped it and a QB's model term was his shrunk
2025 PPG alone. The shrink pulls every high scorer toward the positional
mean and nothing gave credit back for the volume that made the points, so
rushing QBs with short or down 2025 seasons (Daniels 7 games, Lamar 13)
sat under pocket veterans with 17 (Stafford, Prescott). QBs now get their
own regression: ppg ~ 1 + carries per game + offense snap share, fitted on
QBs with 6+ games (41 rows), blended 0.65 shrunk / 0.35 usage like every
other position. Carries per game rather than rush yards: the two are
collinear and carries is the designed-volume signal.

Effect on the Keefamania QB order (rank before -> after): Hurts 6->3,
Lamar 11->9, Daniels 15->11, Murray 22->17, Nix 12->10 up; Stafford 4->8,
Prescott 8->13 down. Only QB rows moved. Against the sheet, QB Spearman
0.81 -> 0.86 (top 36), 0.85 -> 0.89 (all); Omnibeta 0.85 -> 0.88.

What it does not fix, on purpose: Burrow (sheet 4th, board 14th) is a
pocket passer with 8 games at 17.4 PPG in 2025; his case is the market's
expectation of a bounce-back, which is the market half's job and is what
the stat-line source carries (item 1: Burrow 6th on that column). The
blend weight between the two halves is item 2's decision.

## 2026-09-02 (20) — projection overhaul, item 2: the backtest, and what it decided

scripts/projection_backtest.py rebuilds each arm as the pipeline would have
before the target draft and scores it against that season's actuals in
league scoring, 17-game basis, over the T-preseason draftable pool (every
player FantasyFootballCalculator had an ADP for; 0 actual for anyone who
never played). Two pairs, 2023->2024 and 2024->2025, both leagues. Arms:
usage (build_usage at stats_season S, incl. the QB regression), curve (the
log-rank market term on the T-preseason ADP -- ECR history is not
archived), blend (default_projection, configured alphas), lines (Sleeper
week-1 stat lines x 17). Role gate off (no historical depth chart); no
overrides or availability sweep. Reports: reports/projection_backtest.
{keefamania,omnibeta}.md/.json/.rows.csv.

Harness judgment calls:
* Week-1 rows updated after the week-1 Wednesday noon UTC are dropped as
  in-season revisions -- unless (nearly) every row shares one later stamp,
  which is a bulk touch: Sleeper re-stamped all 835 of its 2025 week-1 rows
  on 2025-10-06 while the lines stayed fractional projections (Allen 232.8
  pass yd, 1.63 TD; not his 394-yard game). A midnight-Tuesday cutoff had
  dropped every 2024 row too (stamps run to Tue 03:45 UTC).
* Arms are also compared on the rows ALL four projected (rookies have no
  usage arm; unlined players no lines arm) -- the apples-to-apples column.

What the numbers say (both leagues, both pairs unless noted):
* No arm dominates, and QB 2025 separates nothing (every arm's rank
  correlation is about zero: Daniels 7 games, Burrow 8, Murray 5, Lamar 13).
  Consensus did not "win outright", so the usage model stays.
* The market curve is at least as good as the usage model at RB and WR,
  and usage-only is the worst WR arm in all four league-pairs.
* Rotowire's lines beat every arm on RB MAE in all four league-pairs, and
  lose at QB and TE in both pairs. Not enough to make them the default
  market term; enough to keep the parallel column.
* The alpha grid has ONE stable reading: at WR, every step of usage weight
  above 0 is worse on MAE and on rank correlation, in all four league-pairs
  (Keefamania 2024: 49.6/0.50 at 0 vs 57.3/0.38 at 1; 2025: 61.3/0.56 vs
  63.5/0.47; Omnibeta the same shape). RB flips (2024 wants 0.4-0.6, 2025
  wants 0-0.2), TE flips (0 then 1), QB is flat. Tuning those from two
  seasons would be fitting noise.

Decided:
* projections.alpha_cap_by_position: WR 0.20 -- a cap under the player-
  type alpha, never above it. 0.2 rather than the grid's 0 is the hedge
  against two seasons of evidence. Effect: only WR rows move (65 on the
  Keefamania board; Chase 231 -> 258, Adams 182 -> 155); WR rank
  correlation with the FantasyPros sheet 0.93 -> 0.96/0.97 in both leagues;
  the WR blend arm re-scored in the backtest sits within a point of the
  curve in every pair (in-sample for this choice; recorded as such).
* market_source stays ecr_curve; alphas for RB/QB/TE unchanged; the usage
  model is not reduced to a residual.

What the backtest cannot see, on the record: its population is the
drafted pool, so the deep-tail floor (QB backups, RB 49+, TE 37+) that
Step 0 found and item 1's lines fix is outside its view. The role gate now
handles the model side of that; the market side (a log-rank curve that
never decays) is still open and is the natural follow-up -- curve inside
the ADP pool, lines beyond it -- to be graded the same way once a
population that includes the tail exists (the season replay grader, not
this MAE table).

## 2026-09-02 (21) — projections become an input; the flip waits on the replay gate

The engine's edge is roster-aware timing, not projection modeling.
Projections are now an external input; the modeling code is retired pending
a backtest it has never had. (This supersedes the "projection overhaul";
items 3-5 of that brief are dropped, item 1's Sleeper adapter and the depth
chart rule are folded in.)

Built (draftkit/external.py, projections.source):
* One schema for two sources -- sleeper_id · name · pos · team · pts17 ·
  source · as_of · line. pts17 is the stat line scored in the league's own
  settings as a 17-game total; the engine's `projections.games` (16) is
  applied ONCE, at the end, for every source. Sleeper's gp=18 is ignored.
* Sources in config order, first wins per player: the FantasyPros sheet
  (data/external, read-only, as of 2026-09-01; 476 players matched to
  Sleeper ids by the market table's own matcher, 15 unmatched -- fullbacks,
  Bam Knight, two spacer rows) then Sleeper/Rotowire (555 players) for the
  gaps. K/DEF keep the synthetic ECR-linear projection (no lines exist).
* Non-starters project 0: depth-chart order past the position's starters
  AND a market rank past teams x starters (or no rank at all). WR excluded
  because Sleeper's receiver chart is per slot (LWR/RWR/SWR), not a depth;
  a TE filed under the RB chart is left alone. `contingent_of` names the
  starter ahead. 188 players zeroed in the pool, 9-13 of them on a board.
* The usage model + log(ECR) blend is `projections.source: model`, kept for
  the backtest and for the day it earns its way back. Overrides (confirmed
  only) and the availability sweep apply on both paths.

Verified (reports/input_replay.{keefamania.1396184666897145856,
omnibeta.1395566812157984768}.md; 344 tests; simulate both leagues;
manager --dry-run --module all; consumers of proj_pts read the new csv --
the only header change is three added columns):
* Board vs board rank correlation (proj_pts): QB 0.85 / 0.87, RB 0.93 /
  0.95, WR 0.97 / 0.97, TE 0.89 / 0.93 (Keefamania / Omnibeta).
* The non-starter inflation is gone (Rattler, Mills, Winston, QB3s: 0).
* Replay, our picks by the engine at every slot against the archived
  rivals: Keefamania lineup points +24 on the new ruler (9 slots of 10
  better), -25 on the old ruler; Omnibeta -1 on the new ruler (6/6), -50 on
  the old. Each board wins on its own ruler; the Omnibeta wash on the new
  ruler says the new input does not obviously draft better even by its own
  lights there.
* THE GATE TRIPPED: 63% (Keefamania) and 54% (Omnibeta) of round 1-6 picks
  change. The changes are the QB timing (Allen R3, Daniels R6 in; Maye R5
  and Kittle R6 out) and RB/WR tier order (Henry and Gibbs over Chase Brown
  and McCaffrey; Olave/JSN/Nabers/Wilson swaps). The brief says starters
  moving materially in rounds 1-6 is a stop-and-report, so the default
  stays `model` and the flip is a human call.

Line counts: projections.py 432 -> 559 (the external path and the shared
finish step were added; the model path was not deleted, per the brief),
market.py 256 -> 256, external.py 232 new. The simplification is in the
active path -- external mode is ~120 lines and no fitting -- not yet in the
file, because the retired model still lives there behind the flag.

To flip: projections.source: external, rebuild both boards, re-run
scripts/input_replay.py and read the round 1-6 list again.

## 2026-09-02 (22) — the pick is no longer a click

The Draft button dispatches Yahoo's own Redux thunk `makePick(playerId)`,
which sends `0|league|manager|pickNo|playerId` on the client's socket; the
Autodraft toggle is `setAwayStatus(bool)` (`5`/`6`). Both are reachable as
bound dispatchers on the top-level connected component's props, found by
the same React-tree walk that finds the store. The driver now picks through
`makePick`, verifies against the store that OUR pick number holds that
player, and keeps the DOM click strictly as the fallback. keepAlive clears
`away` through `setAwayStatus(false)`.

Found and fixed on the way (mock 20): the action path generates no user
activity, so Yahoo's ~15-minute idle timer flagged us away and autopicked
before the clear could run. keepAlive now heartbeats `setAwayStatus(false)`
every 240 s and runs before every on-clock attempt. Three consecutive clean
mocks followed (45/45 via the action, eleven heartbeats, no away flag).

Also on the record now: every pick carries the engine's reason, the
best-available-by-projection alternative and the candidates passed on; a
full per-manager trail per mock (scripts/mock_trail.py, reports/mocks/);
and the replay-gate redefinition (accuracy + outcome, churn by tier as a
diagnostic) recorded for the projection-source decision.

## 2026-09-02 (23) — the projection-source gate, pre-registered before it runs

DECISIONS #21 left `projections.source` on `model` because 63% / 54% of
round 1-6 picks changed under the external input. The reviewer's objection
stands: pick churn measures difference, not quality, and keeping the source
with no evidence because the one with some evidence changes picks is
backwards. The gate is redefined here BEFORE the numbers are produced, so
the result cannot move the thresholds.

Arms. `model` = the retired usage + log-rank blend (the `blend` arm of the
backtest). `external` = stat lines from outside; in history the only lines
we have are Sleeper's week-1 lines (the backtest's `lines` arm), so they
stand in for the 2026 sheet + Sleeper combination. The 2026 FantasyPros
sheet itself cannot be judged until 2026 is played; this is stated in the
report, not buried.

Test 1, accuracy (scripts/projection_backtest.py rows, both leagues, pairs
2023->2024 and 2024->2025, rows every arm projected): pooled MAE over all
four positions and both pairs, and the n-weighted mean of the per-position
Spearman. external FAILS if its pooled MAE is more than 2% above the
model's, or its weighted Spearman more than 0.02 below, in either league.
Otherwise it passes (ties pass: "not worse").

Test 2, outcome (scripts/source_gate.py): for each league and history
year, both arms are built into boards through the production code
(add_vorp, build_tiers, handcuff and upside flags) and replayed through the
SAME engine at every draft slot against rivals who draft in that year's
FantasyFootballCalculator ADP order (Omnibeta is a first-year league; no
archived 2024/2025 drafts exist, and ADP is the average of real drafts).
K/DEF are absent from the history pools and are removed from the slots for
both arms alike. Each drafted roster is graded on the ACTUAL season points
of its best legal lineup -- a ruler neither board wrote. external FAILS if
its mean lineup points over all slots, pairs and leagues are more than 1%
below the model's. Slot wins/losses and per-pair means are reported.

Diagnostic, not a gate: picks that change on the 2026 archived drafts
(scripts/input_replay.py), now also by TIER of the player the old board
took, and the ten largest.

Decision rule: both pass -> `projections.source: external`, boards rebuilt.
Either fails -> stays `model`, numbers recorded. One passes, one fails ->
reported to the human with both numbers; no flip without the call.

Not part of this gate: the Yahoo mock-room projections as a third source
(a live room is needed to read them; recorded separately when captured).

### Result (same day): STAY on `model`. Both tests failed, cleanly.

reports/source_gate.md (+ .json), scripts/source_gate.py, tests/test_source_gate.py.

* Accuracy: pooled MAE 57.8 -> 60.8 in Keefamania (+5.3%), 63.0 -> 66.0 in
  Omnibeta (+4.7%); weighted Spearman -0.011 / -0.003. Threshold was 2% /
  0.02. The cells agree with the earlier backtest: the lines win at RB in
  every cell and lose at QB, WR and (mostly) TE.
* Outcome: 44 slot-drafts, actual-points lineups. model 1563, external 1539
  (-1.55%; threshold 1%); external better in 19, worse in 25. Split by
  league: external AHEAD in both Keefamania years (+23, +83) and BEHIND in
  both Omnibeta years (-127, -51). Consistent with the accuracy cells --
  the 12-team, two-flex league leans hardest on WR depth, where the lines
  are weakest. Zero engine errors; board sizes within 10% between arms.
* Churn (diagnostic only, 2026 archived drafts, model vs external boards
  built side by side today): Keefamania 99/150 picks change, Omnibeta
  117/180. By tier of the old pick: T1 44% / 54%, and 73-93% from T3 down.
  So the churn is not confined to the bench -- but churn decided nothing
  here; the two quality tests did, and they went the same way.

What this does and does not say. It says Sleeper's week-1 lines, as a
season projection, are not better than the blend on two seasons of
evidence, and drafting from them did not produce better rosters on
average. It does NOT grade the FantasyPros sheet; that waits for 2026.
The external path stays built and selectable; the sheet and lines remain
parallel columns on the board (proj_consensus_pts) for the human eye.

Threshold honesty: had the outcome threshold been 2% the outcome half
would have passed and the decision would have been "split" -- the
accuracy half fails either way, so no threshold in the neighbourhood
flips the result.

### Correction (same day, from the code review): the rivals were not identical

The review found that Test 2's rivals drafted from each ARM'S OWN board, and
the external board lacks every player Sleeper never lined (McCaffrey and
Higgins in 2024; Rice, Godwin, Judkins in 2025 -- 7/8/10/18 per pair), so
the two arms faced different rivals and the model engine could draft
players the external arm could not. The round count was also set by the
smaller board. Both fixed: one shared rival list per year (the pool in ADP
order, taken whether or not a player is on our arm's board), depth from the
shared pool (13 rounds in all four pairs). Re-run:

* Accuracy: unchanged (it never depended on the replay).
* Outcome: model 1558, external 1540 (-1.20%, threshold 1%); external
  better in 20 of 44, worse in 24. Keefamania +13 / +98, Omnibeta -118 /
  -43. Verdict unchanged: STAY on `model`. The correction moved the number
  toward external by a third of a point per cent and did not cross the bar.

Also stated in the report now: the history rows carry no team or route
data, so the handcuff and RB-receiving upside flags are inert on the gate's
boards for both arms (only the rookie path is live).

## 2026-09-02 (24) — review of the day's code, and a prune

Review (8 finder angles, 1-vote verification, 10 findings, all confirmed)
of the mock-trail, heartbeat and gate commits. Fixed, with tests where the
defect was testable:
* the gate's rival-pool and round-count flaws above;
* heartbeat: a throwing setAwayStatus retried every ~1 s cycle and its note
  would evict the whole log; the timestamp is now stamped before the call;
* keepAlive walked the React tree every cycle when no action registry
  exists (click-path rooms); the walk now runs only when a beat is due, and
  a miss is remembered for 10 s;
* pickRecord re-ranked the post-pick state for `passed_on`; it now takes
  the decision-time list from draftTop;
* the trail producer lived in a console snippet: `DK.trail()` now composes
  the dump from the store and the retained records and POSTs it;
* scripts printed non-ASCII (Δ) and crashed when piped on Windows;
* league shape (teams, rounds, starter slots) is read from the league
  yaml's `expected:` block by one helper (engine_parity.league_shape;
  omnibeta.yaml gained its `roster:`), replacing three hand-typed tables;
* one board pipeline (draftkit.tiers.finish_board) for cmd_tiers, the
  baseline bake-off and the gate -- the gate's copy had skipped the
  contingency map;
* one lineup grader (slot_replay.lineup_points with slots/key) instead of
  three; one spearman import instead of four copies;
* input_replay counted tiers by re-running the whole replay; now one pass;
* ranks broke ties by row order, so identical rebuilds differed by a few
  tied rows; VORP and value ranks now tie-break on sleeper_id, and two
  consecutive rebuilds of the Keefamania board are byte-identical;
* runbook, protocol doc, draft-day .bat, README and package.json no longer
  describe the churn gate as pending, the poller as live, or the repo as
  single-league.

Pruned (zero readers, superseded, or one-off): the CDP poller and its .bat,
mock_cycle.py, the pre-bridge scratch boards and plan.json under
data/draftrig, the haircut board diff. .gitignore now covers the rig's and
harness's scratch. Held on purpose: vona_replay.py and its validation
report (the only controlled VONA evidence), baseline_bakeoff.py (decided a
shipped value), the availability/override research notes (provenance for
live data files).

## 2026-09-02 (25) — B1: the survival calibration record, and a defect in the old one

Plan: docs/plans/2026-09-02-final-form-and-survival-sim-plan.md (approved
today). Step B1 is the enabling layer for the refit; nothing flips.

The defect. draftlog logged `my_next_pick = next_pick_for_slot(cp)`, which
is cp ITSELF when I am on the clock, while the sim's window at that moment
runs to my FOLLOWING turn (tracker.urgency_report). clv_retro then scored
`survived = picked_at >= my_next_pick`, so every on-clock prediction graded
as survived. The n=67 behind `survival_shrink: 0.55` was scored that way.
Rescored against the real horizon (reports/survival_calibration.md), the
human room's three legacy buckets read:

| bucket | old n / observed | corrected n / observed |
|---|---|---|
| 50-69% | 9 / 44% | 5 / 0% |
| 70-89% | 19 / 68% | 10 / 30% |
| 90-100% | 28 / 75% | 40 / 82% |

Pooled over every room (n=147: one human Sleeper room, three Sleeper bot
mocks, four Yahoo autopick mocks read from the trails' prose), predicted
70-89% observed 42%, predicted 90-100% observed 86%. The sim is more
overconfident in the middle and LESS overconfident at the top than the
0.55 map assumed. The shrink is retained provisionally until step B7's
refit; B2 does not wire the decision path to it before then.

Built:
* urgency report carries `survival_raw` (Monte Carlo frequency) beside
  `survival` (calibrated, displayed); calibrate(p, 1.0) returns p exactly.
* recs events: `window_start` and `my_next_pick` from the sim's window;
  per recommendation `sleeper_id, adp, market, survival (raw),
  survival_shown, best_now, e_best_next, urgency`; per event the knob set,
  the rivals' needs and the away slots. The reconstructed (bot-burst) event
  captures the report while rewound. `DraftLog.snapshot()` is the bridge's
  per-state hook.
* the bridge: one `plan_rows` for the CLI and the server (rows carry
  s/sr/e/b), `log_plan` -> data/logs/yahoo_<room>.jsonl; the driver passes
  s/sr/e through rankFromPlan and keeps them on pick records and passed_on.
* scripts/fit_survival.py: the row builder (horizon always recomputed;
  structured field first, then shown field, then either prose phrasing
  un-shrunk by the logged shrink; trails un-shrunk by 0.55 -- an
  assumption stated in the report), `--report-only`. clv_retro delegates to
  it.
Tests: 8 new (urgency, draftlog x4, bridge x2, driver) + tests/test_fit_survival.py (5).

### B3 (same day): knobs hoisted, one read site, nothing moved

`need_damp`, `qb_filled_damp`, `qb_damp_until_round`, `kdef_early_damp`,
`kdef_typical_round` are parameters of simulate_survival (defaults = the
old constants), Tracker class attributes, and `engine:` keys at today's
values; `run_ratio`, `autopick_sigma_scale`, `rival_needs_update`,
`away_slots` are declared now and take effect in B4/B5/B6. One knob list
(`Tracker.ENGINE_KNOBS`) read by `Tracker.apply_engine_cfg`, which the
Sleeper constructor, the Yahoo bridge and `engine_parity.make_tracker(cfg=,
overrides=)` all call -- the bridge's hand copy is gone. A same-seed test
pins that the explicit defaults reproduce the implicit call exactly.

## 2026-09-02 (26) — B7: the survival refit, pre-registered before it runs

What is fitted. sigma_early, sigma_late, reach_prob, need_damp, by
coordinate search on a coarse grid: sigma (4,6,8,10) x (15,21,27,35) at
reach 0.15, then reach_prob (0, .10, .15, .25, .35), then need_damp (.15,
.30, .50). autopick_sigma_scale is fitted only once step B5 exists (it has
no effect before). Stated plainly: this yields THE BEST POINT ON THE GRID,
not identified parameters, on one human room plus bot and autopick mocks;
no value is reported finer than its grid step.

How. scripts/fit_survival.py --fit re-runs the simulation on every archived
state (every second pick, the room's real seat) with the production board
for that league, draft-day ADP from the FFC snapshot preceding the draft
(Yahoo rooms keep the board's Yahoo rank), survival_shrink 1.0, sims 200
for the search and 1000 for the confirmation; scores the RAW survival
vector of every pooled player against the room's actual picks. Objective:
mean over room types of the per-type log loss (equal weight per type, so
four autopick rooms cannot outvote the one human room). Three calibration
views are always reported: pooled, human room, autopick rooms.

Acceptance, fixed now:
* Calibration: raw predicted vs observed within 8 points in every bucket
  with n >= 15, on the pooled real-seat rows AND on the human room alone. A
  pass carried by bot/autopick rooms while a human bucket with n >= 15
  fails is SPLIT: recorded, no flip without the human's call.
* Outcome: scripts/slot_replay.py, fitted knobs vs current, identical
  harness knobs otherwise, both leagues, every slot: mean projected lineup
  points not worse (ties pass); per-slot wins/losses reported.
  keefamania: slot_replay.py --league keefamania --draft-id 1396184666897145856 --teams 10 --board tiers.keefamania.csv --set ...
  omnibeta:   slot_replay.py --league omnibeta  --draft-id 1395566812157984768 --teams 12 --board tiers.csv --set ...
* On pass: survival_shrink 1.0 and the fitted knobs into config.yaml,
  Tracker class defaults, engine_parity (shrink only), draft_driver.js
  SURVIVAL_SHRINK; then B2 wires the decision path to the calibrated vector.
* On fail: the SIGMA-ONLY refit (sigma fitted, everything else at today's
  values, shrink 1.0) becomes the default -- never 0.55, which #25 showed
  was fitted to mis-scored data. If even sigma-only fails the bar, the
  shrink is refit on the rescored rows as a stopgap and this entry says so.
Also reported, not a gate: the empirical need damp implied by rivals'
closed-slot picks against the ADP mass, by room type, next to the 0.15 in
use.

### B2 measurement (same day): joint vs carry expected-best

scripts/ebest_parity.py, 40 random mid-draft states per league, sims 1000,
production knobs. Urgency from the Monte Carlo JOINT expectation vs the
carry (independence) formula over the calibrated survival vector
(reports/ebest_parity.md):

| league | top-1 unchanged | mean abs delta urgency | max abs delta |
|---|---|---|---|
| keefamania | 39/40 | 1.2 pts | 6.8 pts |
| omnibeta | 39/40 | 1.2 pts | 8.2 pts |

The pre-registered bar was top-1 unchanged on >= 38/40 AND max delta < 2
points. The second half fails, on tight-end markets above all (a thin
market where one survivor dominates, so independence overstates the
expected best by 6-8 points). Decision, as pre-registered: the joint
expectation stays Python's definition of e_best_next; the carry formula is
the JS mirror's client-side approximation, documented with this tolerance
(mean 1.2, max 8.2 points; 1 top-1 flip in 40 per league), and the report
carries both numbers (`e_best_next_joint`, `e_best_next_carry`) so the gap
stays measurable. The decision path is wired to the calibrated vector after
B7 (below).

### B7 result (same day): the raw simulation is calibrated where the shrink said it was not; the low end splits

reports/survival_fit.md (+ .json), reports/survival_fit_point.*.json,
reports/ebest_parity.md. 8 rooms, 40,414 prediction rows per knob set at
the confirmation (sims 1000, every second state, real seats). Wall time
726 s for the search.

The first finding is about the shrink itself. With NO shrink, the raw
simulation at today's knobs is calibrated from 50% up in every view:
pooled predicted 61 / 82 / 97 vs observed 65 / 84 / 98; the human room
61 / 81 / 97 vs 68 / 84 / 97. The live 0.55 map would display that 97% as
76% against an observed 98%. #25 found the n=67 behind the shrink was
mis-scored; this confirms the direction of the error: the sim was not
overconfident at the top. Where it is off is the LOW end in the human
room: players the sim gives 20-50% survive more often than that.

Three knob sets, shrink 1.0 throughout:

| knob set | objective | human loss | calibration bar | outcome vs today (by-slot lineup pts) |
|---|---|---|---|---|
| current (6/27, reach .15, need .15) | 0.2114 | 0.2345 | human PASS (max miss 7); pooled FAIL one bucket by 1 pt (30-49: pred 41 obs 32) | identical by construction |
| sigma-only (4/27, reach .15, need .15) | 0.2097 | 0.2359 | pooled PASS; human FAIL 0-29 (22 vs 36), 30-49 (41 vs 50) | Keefamania tied 10/10; Omnibeta +9.0/slot, 3 better 0 worse 9 tied |
| fitted (4/27, reach .10, need .30) | 0.2060 | 0.2336 | pooled PASS; human FAIL 0-29 (21 vs 34), 30-49 (40 vs 52) | Keefamania -0.7/slot (0 better 1 worse 9 tied); Omnibeta +9.0/slot (3/0/9) |

Empirical need damp (closed-slot take rate against the ADP mass): human
0.44, Sleeper bots 0.31, Yahoo autopick 0.49 -- all well above the 0.15
in use; the grid's best was 0.30 (its top value was 0.50 and lost).

Applying the pre-registered rule: the fitted point is a SPLIT (pooled
passes, human buckets with n 122 and 218 fail) and also fails the outcome
half on Keefamania by 0.7 points per slot. The declared fallback, the
sigma-only refit, passes the outcome half in both leagues but shows the
same human-room split. No candidate passes both halves outright, so
nothing flips on the fitter's authority; the choice is recorded here for
the human's call:

  (A) today's knobs, shrink 1.0 -- the human room passes every bucket,
      no pick changes, the shrink is retired;
  (B) sigma-only, shrink 1.0 -- better objective and +9/slot in the
      Omnibeta replay, at the cost of the human low end;
  (C) fitted -- best objective, fails the Keefamania outcome bar.

Recommendation on the record: (A). The real rooms that matter are human
(Omnibeta) or unknown (Keefamania on Saturday; the mocks were 80-90%
autopick, the league will not be); the human-room calibration is the one
to protect, and (A) is the only set that holds it in every bucket. Either
way the 0.55 shrink is retired -- every candidate says so. B2 follows the
call: with shrink 1.0 the calibrated vector IS the raw vector and the
decision path is consistent by construction; the carry formula stays the
JS approximation (measured: mean 1.2, max 8.2 points).

### Decided (same day, the human's call): (A) -- shrink retired, knobs unchanged

`survival_shrink: 1.0` in config.yaml, the Tracker class default, the
replay harness and the in-page driver's constant. No pick changes (the
decision path never read the shrink); the displayed chances now equal what
the simulation says, which the re-scored data supports from 50% up. The
human low end (sigma / noise shape, not a shrink) stays on the list with
the need-damp evidence (empirical 0.31-0.49 vs 0.15 in use) for a later
fit on more human rooms. Any non-1.0 shrink set in future prints a
one-line warning: display and decision would disagree again.

B2 closed with it: the decision is the joint expectation over the
simulated draw; with the shrink at 1.0 the displayed vector is that draw;
`e_best_next_carry` stays in the report as the JS mirror's approximation
with its measured tolerance.

### Addendum (same day): five Yahoo results emails as rooms; the early mock log is unverified

Gmail holds five "Your Mock Draft Results" emails, all from 2026-08-31
15:45-18:56 PT (seats 3 partial, 1, 2, 4, 5). scripts/yahoo_mock_email.py
turns each into the trail shape (data/logs/mocks/mock_email<id>.json,
picks with team ids, managers, our seat, no pick records); the fit reads
them as room type `yahoo_email`. Their picks match none of the narrative
log's mocks by seat or roster (best overlap 6 of 15 names), and the first
is Yahoo's Instant Mock against bots, which the rig never used. Either
they were drafted by hand that afternoon or the log's mocks 1-9 rosters
record what the driver believed rather than what Yahoo did -- until mock
13 "verified" meant only that the roster grew. Provenance is left open in
the log; the rooms enter the fit through their RIVALS' picks only, which
are real either way.

With the five rooms added (n 65,758 rows at sims 1000): current knobs
objective 0.2022 (yahoo_email loss 0.1745), sigma-only 0.1996 (0.1692).
The email rooms behave like the autopick rooms: at the low end the sim
OVER-predicts survival for them (0-29%: predicted 25%, observed 13%),
the opposite of the human room (predicted 25%, observed 30%). So the two
room kinds pull the low end in opposite directions and no single sigma
fits both; the human view is the one the decision protects, and (A)
stands. The open item is a per-room-kind noise model (B5 gives Yahoo
autopick seats their own sigma scale; that is where this belongs).

## 2026-09-02 (27) — B5: autopick rivals are modelled as what they are

Yahoo's 'away' managers are drafted by Yahoo's autopick, which walks its
default rank and fills every starter slot before any bench slot. Before
this they were simulated as noisy humans with weak need weighting -- and
in the Yahoo mock rooms 8-9 of 10 seats were away. Now: the driver sends
each drafted pick's team id and the current away team ids; the bridge
maps team ids to draft slots through the picks (DOM path: no ids, no
mapping, every rival human -- DATA MISSING, never team id = slot);
`Tracker.away_slots` marks them and `_rival_states` flags each rival
`autopick`. In the sim an autopick rival gets sigma x autopick_sigma_scale
(0.5, a prior until fitted on the Yahoo rooms), NEVER reaches, and while
any starter slot is open a non-filling position is weighted
autopick_need_damp (0.02) -- MORE need-constrained than a human, not less.
K/DEF still wait for their rounds. On Keefamania the board's adp already
IS Yahoo's rank (the league-scoped yahoo_adp override), so the likelihood
centres on the list autopick walks. The reach draw is now consumed at
every reach_prob, so reach A/Bs and autopick on/off share one random
stream. Sleeper path: no signal, nothing flagged. Gate: tests (three sim
behaviours, the id->slot mapping and its degrade) now; one live mock to
see non-empty away_slots in the bridge log is still owed, and the
autopick stage of the refit runs after it.

## 2026-09-02 (28) — B6: a rival who picks twice in my window consumes his needs

At a snake turn every team between me and the wall picks twice inside my
window, and the sim handed each of them the same needs for both picks, so
it could give one rival two quarterbacks. Now each rival carries a
per-position multiplier VECTOR; slots that appear more than once keep a
per-sim needs copy, `snake.consume` (moved from planner, re-exported)
shrinks it by what the sim just handed them, and only that rival's LATER
picks are re-weighted. Autopick rivals are updated too -- starters-first is
a needs rule, so it matters more for them, not less. Slots that pick once
keep the precomputed vector: numerics identical to before (tested, same
seed). `rival_needs_update: false` restores the old behaviour.

Test: same slot twice with QB the only open slot -> the second QB survives
+30 points more often than against two different QB-needy rivals; with the
flag off the two cases agree within 0.1.

Perf (sims 1000, pool 100, FLEX market): before this plan 0.39 s at 9
rivals / 0.94 s at 22; after B4's relative run detector 0.55 / 1.59; after
B6, with the detector rewritten as running counts (one boolean mask per
pick instead of a Python window scan), 0.56 / 1.58 -- inside the
pre-registered <= 2x budget (0.80 / 1.88). sims stays 1000.

## 2026-09-02 (29) — B4: the run detector measured relative to expectation; the old rule keeps the default

The old detector fired on an absolute count -- two of a position in five
picks -- which in an RB/WR-heavy draft is the normal state, so the 1.5
boost was a near-constant multiplier on the two most common positions.
Built: a run is now count >= run_min AND count > run_ratio x the model's
own expected count for that position over the window (its share of the
pick mass at each pick, history picks scored on the plain ADP likelihood);
run_ratio = 0 reproduces the absolute rule exactly. Also fixed: on the
Yahoo path and in every replay the picks carry no metadata, so the
detector read "" for every real pick and never fired on history; the
position now comes from the board (Tracker._pick_pos).

Gate, pre-registered (slot_replay, both leagues, every slot, production
reach, relative vs absolute): Omnibeta identical on 12 of 12 slots;
Keefamania identical on 9 of 10 and one slot 1 point lower (mean
-0.1/slot). "Not worse on both leagues, ties pass" is not met, by a hair,
so `run_ratio` ships at 0 -- the absolute rule -- and the relative rule
stays selectable for a re-test once more rooms exist. Tests pin both
behaviours (expected-share positions never trigger at 1.5; a relative
surplus does; 0 restores the old firing).

## 2026-09-02 (30) — A1: sources averaged per stat, dispersion columns, ESPN — pre-registered, ships OFF

Built. draftkit/espn.py (public kona_player_info endpoint with the
X-Fantasy-Filter header, cache-first, stale-on-failure, a thin payload =
"filter ignored" = unavailable), external.from_espn (espn_id through the id
map first, the market's name matcher second, unmatched RETURNED),
external.combine(mode='first'|'mean'): 'mean' is the equal-weight per-stat
mean of every source carrying the player, scored ONCE (a stat one source
omits counts as 0 for it); because scoring is linear that equals the mean
of the per-source scores, so n_sources / pts17_sd / hi / lo are the spread
of those scores. Carried as n_sources / proj_sd / proj_hi / proj_lo on the
board (both paths; null for overrides and zeroed players), through the
parity loader, the bridge loader and the browser export. Config:
projections.external.combine: first (the 2026 default), sources
[sheet, sleeper]; espn is a selectable third source.

Frozen today: reports/forward_2026.<league>.rows.csv -- the 2026 arms
sleeper / espn / mean / sheet / model on the 17-game basis, one row per
board player, EACH with its own source date (sleeper_as_of, espn_as_of,
sheet_as_of, model_built). scripts/forward_snapshot.py --score (January)
joins 2026 actuals and REFUSES any row whose latest source date is after
kickoff 2026-09-10.

Gate (judged when 2026 is played; nothing flips before). Candidate `mean`
vs rivals sleeper, espn, sheet, model. Population: board players with a
2026 ADP inside the draft, rows every arm projected. Test 1: pooled MAE and
n-weighted Spearman on 2026 actuals, both leagues; Test 2: scripts/
source_gate.py --rows <forward csvs> --candidate mean --rivals
sleeper,espn,sheet,model on the archived 2026 drafts with one shared rival
list, lineups graded on 2026 actual points. Rule: mean not worse than EVERY
rival (MAE <= 1.02x, Spearman >= -0.02, outcome >= 0.99x) in both leagues.
Pass -> combine: mean and sources [sleeper, espn] (and #23's source
question reopens with these numbers). Stated plainly: ESPN has no
2023-2025 history in this repo, so the mean arm cannot be scored on the
backtest pairs; the Sleeper-only history verdict (#23) stands until then.
Mechanical pre-ship check recorded below: ESPN coverage of Sleeper-lined
players with ADP <= 180, and unmatched names.

Identity: with combine: first the four reference boards (model/external x
Keefamania/Omnibeta) must come back IDENTICAL on every existing column;
the four new columns are the only additions.

### A1 result (same day): built, frozen, identical with the flag off

* ESPN fetched live through the filter header: 193 of the 199 Sleeper-lined
  Keefamania board players (97%) and 224 of 237 on Omnibeta (95%) -- above
  the 90% pre-ship bar. Unmatched names are in the build report.
* Forward snapshots frozen: reports/forward_2026.keefamania.rows.csv (238
  rows) and .omnibeta (294), arms sleeper / espn / mean / sheet / model with
  per-source dates; the January scorer refuses any row dated after
  2026-09-10.
* Identity with combine: first, all four reference boards IDENTICAL on
  every pre-existing column; the only additions are n_sources / proj_sd /
  proj_hi / proj_lo.
* scripts/source_gate.py generalised to --candidate / --rivals / --rows
  (pass = not worse than EVERY rival); the defaults reproduce the #23 run
  (population = rows every backtest arm present projected, plus the arms
  under test).
Nothing flips: combine stays first, sources stay [sheet, sleeper], the
gate is judged on 2026 actuals.

### Reproduction check of the generalised gate (same day)

scripts/source_gate.py with its defaults against reports/source_gate.md:
Test 1 (accuracy) reproduces the #23 tables line for line. Test 2 does
not, and should not: the replay runs the CURRENT engine, which now carries
B4/B5/B6 (the relative-detector plumbing, autopick flags -- none in a
Sleeper replay -- and the within-window needs update), so the outcome
numbers move: model 1561.7, external 1536.6 (-1.61%; was -1.20%),
external better in 20 of 44, worse in 24 (unchanged). Verdict unchanged:
STAY. The generalisation's own arithmetic is pinned by tests
(tests/test_source_gate.py), not by this diff.

## 2026-09-02 (31) — A2: the positional missed-games table, pre-registered

Pre-check, measured before the table touched anything: each source's season
line over 17 x Sleeper's week-1 line for five healthy starters (Gibbs,
Allen, Nacua, Bowers, B. Robinson): FantasyPros sheet 0.98, ESPN 0.98,
Sleeper/Rotowire 0.92. The sheet and ESPN are full-season totals; Sleeper's
season line already embeds about one missed game. Recorded as
external.SOURCE_GAMES_CONVENTION; a Sleeper-sourced row keeps the uniform
scale so it is never discounted twice. Five players is thin and is said so.

The table (scripts/derive_absence_bands.py -> data/processed/
absence_bands.json, tracked): mean missed games by position x ex-ante
rank band, starters by the prior season's total, 2019-2025 pairs, zero-game
seasons excluded (biased LOW). Pooled mean 3.15 (n 839). QB 2.49 / 2.63 /
4.30; RB 2.81 / 3.46 / 3.44 / 4.39; WR 2.76 / 2.46 / 2.60 / 3.44; TE 2.78 /
3.09 / 2.79. The last band is the reliably worse one at QB, RB and WR; TE
is flat. Leak-free tables per backtest pair (through 2023: pooled 3.30;
through 2024: 3.22) for the gate.

Applied (draftkit/games_table.py, projections.games_table.enabled, OFF)
as games - (missed[pos, band] - pooled_mean): only cross-cell differences
move the board; the band comes from the provisional market rank computed
before scaling, never from the projection; off-table ranks and K/DEF keep
the uniform games; per-player durability stays forbidden. One helper feeds
all three scale sites (external, model, the consensus column at its join).

Gate, fixed before the numbers: scripts/games_table_gate.py applies the
leak-free per-pair table to the #23 rows as `blend_gt` / `lines_gt`
(non-null exactly where the base arm is); then source_gate.py --candidate
blend_gt --rivals blend (and the lines twin). Test 1: pooled MAE ratio
<= 0.99 in BOTH leagues (an improvement claim must improve) and weighted
Spearman >= -0.02. Test 2: actual-points outcome >= 0.99x over the 44
slot-drafts. Pass -> enabled: true, boards rebuilt, churn by tier recorded
as a diagnostic. Any fail -> stays off, numbers recorded. Identity with the
table off: the four reference boards must come back IDENTICAL.

### A2 result (same day): the table makes both arms LESS accurate; stays off

reports/games_table_gate.md (blend_gt vs blend), reports/
games_table_gate_lines.md (lines_gt vs lines); rows in reports/
projection_backtest.<league>.gt.rows.csv.

Test 1, pooled MAE ratio candidate / base (required <= 0.99 in both):
blend_gt 1.023 Keefamania (59.1 vs 57.8, n 254), 1.020 Omnibeta (64.3 vs
63.0, n 301); lines_gt 1.038 Keefamania (63.1 vs 60.8), 1.031 Omnibeta
(68.1 vs 66.0). Weighted Spearman within +-0.004 everywhere. FAIL, all
four cells, in the wrong direction: scaling a projection by the band's
historical absence rate adds error rather than removing it. Per cell the
table helps RB (MAE down 1-3 points in every RB cell) and hurts QB, WR and
TE, which is the pattern of a signal that is real for one position and
noise dressed as signal for the others.

Test 2, actual-points outcome over the 44 slot-drafts: blend_gt 1544.1 vs
blend 1561.7 (-1.13%, better 13 / worse 27 / tied 4) FAIL; lines_gt 1551.4
vs lines 1536.6 (+0.96%, 23 / 17 / 4) pass. The pre-registration required
BOTH tests; the accuracy half fails outright. Decision: games_table.enabled
stays false; boards untouched; identity IDENTICAL x4 with the table off.

Defect found while reading the first result, fixed before this was
recorded: source_gate.py still wrote #23-style alias keys (`blend`,
`lines`) beside the arm-named keys. For the lines_gt-vs-lines run the
alias `lines` overwrote the rival's own grade with the candidate's, so the
first outcome summary compared lines_gt with itself (44 ties, "+0.0%").
The per-slot tables were right, which is how it was caught. Aliases are
gone; every value is keyed by its arm name and render() reads the names;
regression test added; the #23 default run reproduces the committed
accuracy tables byte for byte, and its outcome half matches the
reproduction check recorded under #30 (-1.61%, stay).

## 2026-09-02 (32) — A3: dispersion in the late-round objective only, pre-registered, OFF

From upside_from_round the engine ranked a market's candidates on VORP x
1.15 for role-quality "upside" players. Built: with `late_round_dispersion`
on, a candidate whose projection carries a spread across >= 2 sources
(proj_sd, plan A1) ranks on VORP + dispersion_lambda x spread instead; the
boolean multiplier remains the rule for everyone without such a spread, so
the flag is inert by construction while combine: first (every spread is 0).
Nothing enters VORP, tiers, the planner or the fallback points. The
rationale says "sources disagree by +-N pts (k sources, lo-hi)". Mirrored
in the in-page driver's local fallback. Naming stays neutral: the word
upside describes the existing role-quality gate, not this.

Gate, fixed now: dispersion_lambda = 0.5, chosen in advance, no grid on the
outcome. scripts/dispersion_replay.py: both archived 2026 drafts, every
slot, flag off vs on on the production board, graded on 2026 ACTUAL
lineup points (the forward snapshot scored in January); projected points
and churn by pick are printed now as diagnostics. Rule: on must be
>= +0.5% mean over the 22 slots AND not worse in either league.
Prerequisite: combine: mean on the board (A1's gate); until then the
replay exits with "no dispersion on this board". Judged January 2027; off
for the 2026 drafts. Identity: flag off, four boards IDENTICAL.

### A3 result (same day): built, inert, identical

Flag off: the four reference boards IDENTICAL. dispersion_replay.py on both
leagues exits with "no dispersion on this board (0 players with a spread
from >= 2 sources)", as the entry predicted under combine: first. Tests:
off keeps the multiplier ordering; on prefers the wider spread at equal
value from round 8 only; degrades to the multiplier when sd is missing or
comes from one source. Nothing to judge until A1's mean-combine is on.

Driver parity (engine_parity.py, 40 states, seed 7, Keefamania board):
17/40 identical top pick, 20/40 same position, 24/40 in the engine's
top 5 -- and exactly the same three numbers with the driver as it was
before A3 and before B5. So this step changed nothing on the in-page
path, and 17/40 is the STANDING gap between the in-page fallback
(`rank().source == "local"`, a compact board with no markets) and the
engine the bridge serves. It is a labelled fallback, not the live path;
the gap is recorded here so nobody reads it as a regression later.

## 2026-09-02 (33) — A4: the flex split derived per league; a bench allowance; pre-registered

onboard.derive_baselines spread every flex slot RB 45 / WR 45 / TE 10, a
heuristic. Built: scripts/derive_flex_split.py walks the league's own board
(remove teams x dedicated starters per position by projected points, fill
teams x FLEX greedily; the mix of those flex starters is the split) and
`--write` persists it as `flex_split:` in the league yaml. It is a league
fact -- it depends on league size, lineup and the board -- so it is stored
per league and re-derived, never copied. Resolution in derive_baselines:
the yaml block, else FLEX_SPLIT_BY_FORMAT[format_key(scoring)] (frozen
today from the two derivations, for a league straight after onboard), else
the legacy 45/45/10 for callers that pass neither (byte-identical). `verify`
reads only `expected:`, so it ignores the block.

Derived today (model boards; the external boards as a sensitivity read):
Keefamania 10 x 1 W/R/T -> RB 0.80 / WR 0.20 / TE 0 (external 0.60 / 0.40);
Omnibeta 12 x 2 FLEX -> RB 0.333 / WR 0.667 / TE 0 (external 0.25 / 0.75).
TE never reaches a flex slot on any of the four boards. The 0.2 swing
between boards is the honest precision of the number.

Bench allowance (`bench_allowance=True`): RB/WR demand x (1 + (absent weeks
+ bye) / 17) from draftkit.bench's position base rates -- the starters a
roster expects to have out in a given week, which it insures from the
bench. QB/TE/K/DEF untouched.

Gate, fixed before the numbers: scripts/baseline_bakeoff.py per league on
its own archived 2026 draft, every slot, the league's own starter shape
(the old script graded Omnibeta on the Keefamania shape; fixed), candidates
`yaml` / `flex` / `flex+bench`, scored on projected points of the starting
lineup (baseline-free; no arm can grade itself). Rule: a candidate replaces
`replacement_baselines` in a league only if its mean >= the yaml's AND it
wins at least as many slots as it loses; ties keep the yaml. Expected small
(the planner measures against what you would end up with, so the baseline
stopped steering the draft: 0.4 pts across three candidates on 2026-09-01);
"no change" is a valid recorded result. The split is stored regardless of
the outcome; only the baselines wait on the gate, and they change per
league by re-deriving.

### A4 result (same day): Keefamania no change; Omnibeta passes by a hair and the archive rule holds

reports/baseline_bakeoff.{keefamania,omnibeta}.md.

Keefamania (10 slots): yaml QB10/RB24/WR24/TE11 mean 1831.3; flex
QB10/RB28/WR22/TE10 mean 1831.3, 0 better / 0 worse / 10 tied -- the
derived split drafts the identical ten rosters; flex+bench
QB10/RB35/WR27/TE10 mean 1829.0, 0 / 1 / 9. Keeps the yaml.

Omnibeta (12 slots): yaml QB12/RB40/WR60/TE12 mean 2172.4; flex
QB12/RB32/WR40/TE12 mean 2172.8 (+0.4), 2 better / 2 worse / 8 tied;
flex+bench QB12/RB40/WR49/TE12 mean 2167.3 (-5.1), 1 / 3 / 8. By the rule
as written, `flex` passes for Omnibeta (mean >= yaml, wins = losses).

Applied: nothing moves in either yaml. The pre-registration above missed a
standing constraint the Omnibeta yaml has carried since the draft: its
baselines "stay as drafted for the season's archive", because the in-season
manager's valuations must stay comparable to the draft-day board. Two
protocols conflict; the older, explicit one wins, and re-pricing a league
that is mid-season on a +0.4-point, 2-2-8 result is the riskier move. The
pass is recorded here and the derived block (`flex_split:` in the yaml)
stays; `flex` becomes Omnibeta's baseline at its 2027 re-onboard, which
re-derives from that season's board anyway. The bench allowance loses in
both leagues and stays off.

What the result says about the model: as predicted, the baseline stopped
steering the draft once the planner measured against what you end up with
(Tracker._fallback_points); across 22 slots and six candidates the spread
is 0.4 points. The split itself is still worth storing -- it is what
`onboard` hands a new league instead of 45/45/10 -- but it is not a lever.

## 2026-09-02 (34) — End-to-end review before the stress mocks: live-path defects fixed, stale context shed

Trigger: I forgot, mid-session, how a mock room is joined (the settled
method: `window.name = 'fandraft'` in the lobby tab, then `.click()` on the
row's Join anchor; a click from an unnamed tab opens a popup outside the
controlled tab group). The user's call: review end to end and shed stale
context so that class of mistake stops recurring. Six review angles ran in
parallel (stale prose, driver pick path, bridge-to-engine trace, dead code,
engine logic on the live path, logging); 80-odd findings; the ones below
are fixed, with a test each where a test could hold it.

Driver (scripts/draft_driver.js), the ones that lose picks:
- TE2 rule read `S.ctx`, set only by the local fallback ranker, so on the
  engine path every engine-recommended second TE was refused. Now
  `top6TeFell()` computes Python's rule from the board and the current pick.
- round / picksLeft / counts came from the roster-panel regex (cannot parse
  "A. St. Brown", IR-R tags), which drives K/DEF timing and must-fill.
  `rosterView()` prefers the store's roster and the header count.
- A store that cannot identify our team sent an empty roster (mock 11's
  failure reopened): the roster now falls back to the panel, the state is
  logged, and the gate refuses to click when neither source can say.
- Try budget: the action attempt was un-counted, so a timing-out makePick
  with no search box walked all 25 plan rows at 3 s each.
- Bridge down / plan stuck at the turn: three plan-only gate failures hand
  the turn to the labelled local ranker instead of the clock; the plan fetch
  has an 8-s abort; every failed refresh is logged.
- `run()` had a 3600-s default that expired mid-draft when injected early;
  now no deadline. The trail POST is automatic at draft end. Preflight
  reports the pick path (action vs click) and whether our team is known.
- Scrutiny: full ISO timestamps, plan call number, ranker source, plan age,
  skipped candidates and dropped plan rows on every pick record; the action
  log rides in the trail; the log ring holds 5000 lines; reset keeps it.

Bridge (scripts/yahoo_bridge.py, bridge_server.py):
- Pads only UP: a spurious entry left current_pick one ahead of the header
  for the rest of a room and the gate refused every click. Entries numbered
  at or past the header pick are dropped (ours never), over-count is a
  named warning.
- merge_feed was first-view-wins; the store's entry (carries team_id) now
  corrects a panel misread, mine flags survive.
- The URL seat is cross-checked against our own flagged picks; one
  consistent disagreeing snake slot wins (the reshuffle case).
- depth_tail ran only the position caps; now the full guardrail (must-fill,
  stash), so 2 picks left with K/DEF open offers K/DEF only.
- Unresolved drafted names and "past my first turn with no roster" are
  named warnings, returned to the page (logged as BRIDGE WARNING), printed
  with a timestamp and the call number, and written to the plans sidecar.
- log_plan's dedupe key was a tautology; it now names the state.

Engine (draftkit/tracker.py, urgency.py, draftlog.py):
- The rolling pool had a LOWER bound (cur - 20): a faller 20+ picks past
  ADP -- the bargain the engine exists for -- was outside the simulation,
  so his market's numbers ignored him and his survival clause vanished.
  No lower bound now; pool_lookback stays in the knob list, unused.
- upside_mult on a negative market value pushed the flagged player DOWN;
  now additive in |value|.
- `adp_delta or -999` read 0.0 as missing in the near-tie.
- intervening_slots() was empty exactly when I was on the clock.
- slot_markets=False now really is per-position urgency (the off arm used
  to build the FLEX row anyway). Bench rows are deduped after the merge.
- Autopick rivals: BN rode in needs so "starters full" never triggered;
  sigma floor against a zero scale; run-history seeded one pick late on the
  clock; simulate_survival's own run_ratio default matches the shipped 0.
- Yahoo pick rows in the room log now carry the name; fillers are skipped.

Shed: exportState and the poller-era set_picks, variance_pick, trend_adj +
two config keys, the disagreements worklist csv, stale runbook steps (run
budget, trail, preflight fields, away-clear, net_tap), the protocol doc's
checklist moved into the runbook, superseded banners on six historical
docs and the architecture report, the join method written into the
runbook and the rig memory.

Not changed, recorded: _fallback_points' S-th-pick deadline (heuristic,
pinned by test), the FLEX-market label on plan rows when an RB wins the
FLEX row, the laptop scheduled tasks (SEASON BRIEFS duplicates the Actions
manager; retirement owed to the user), the JS/Python guardrail asymmetry
(the driver's K/DEF reservation has no Python twin).

### Stress mocks 24 and 25 (same night): six injected faults, five defects found, all fixed

docs/draft-rig-mock-log.md carries the two entries; reports/mocks/
scrutiny_<room>.md (scripts/mock_scrutiny.py, new) joins the trail, the
plans sidecar, the room log and the bridge log per pick. Both rooms
finished 15 of 15 legal on the reviewed code. Latency via makePick:
median ~450 ms to store confirmation across 25 action picks.

Faults and what they proved: makePick no-op -> click fallback landed the
same candidate; forced away -> cleared in 2 s; bridge killed across a turn
(twice) -> refreshes logged, gate fell back to the local ranker after
three cycles as built; page reload mid-draft -> full state reconstruction
from the store and the bridge's memory, preflight clean; store identity
masked -> roster from the panel, plan kept coming, pick landed.

Defects the faults exposed (fixed the same hour, each with a test):
1. The local ranker never excluded store-drafted players (tried players
   drafted at picks 2 and 4). Now it does.
2. The reviewed depth_tail applied Python's one-stash rule and came back
   EMPTY late; the page's own gone set then filtered a two-row plan to
   nothing. Tail = position caps + must-fill; a store-backed plan row is
   "gone" only if the store says drafted.
3. The board exporter fused hyphenated surnames ("j smithnjigba") while
   the driver spaced them ("j njigba"): hyphenated players never matched
   between board and store. Normalisers made identical; parity test over
   eleven awkward names; board re-exported.
4. With the team id unknown the store could not verify a pick, the click
   path took a roster-count increase as proof and RECORDED THE WRONG
   PLAYER (Sutton for Tracy at 118) -- mock 13's error class on the one
   path that could not use the store. Verification now reads the store
   entry at OUR pick number, team id or not.
5. Auto-trail fired at our roster full (147 of 150 picks) and under the
   wrong file name; local-ranker records lacked a pick number and a
   reason. All filled.

Calibration, both rooms (scorecard in each scrutiny report): shown
survival 30-50% observed 0% (n 22) / 57% (n 7); 50-70% observed 32% (n 28)
and 32% (n 34); 70-90% 77% / 73%; 90-100% 93% / 94%. The low end is
overconfident in rooms with autopick seats (5 and 7 of 10 away at the
end). That is the input the autopick refit stage (#26, owed) was waiting
for; nothing is changed on that evidence tonight.

B5 gate closed: away_slots non-empty and moving through the whole room in
the live bridge log, both rooms.

Operational: the join is `window.name = 'fandraft'` then `.click()` on the
row's Join anchor; never reload the waiting room before the bell (ec=5
drops the seat); a devtools eval dies at 45 s. In the rig memory and the
runbook.

### Mock 26 (same night): the clean confirmation room

Room 10534350, seat 6, no faults: 15 of 15 via makePick, engine ranker on
every pick, zero gate / fallback / warning events, four heartbeats. The
mock-24 failure point (pick 126, empty tail) now shows a 25-row plan.
Count toward the three-clean-rooms rule: ONE. Mocks 24 and 25 do not count
(faults were injected). Two more clean rooms owed before the code is
called settled for 2026-09-05; if time runs out, Saturday runs on one
clean confirmation plus two fault-tested rooms, and the record says so.
Calibration in this room (three-plus autopick seats): 30-50% shown 46 /
observed 0 (n 11); 50-70% 63 / 22 (n 37); 70-90% 81 / 40 (n 43); 90-100%
96 / 81 (n 96). The overconfidence now reaches the top bucket. Three rooms
agree; the autopick refit stage moves to first in line after 2026-09-05.

## 2026-09-03 (35) — Autopick-seat refit as a measured study: pre-registration

Plan: docs/plans/2026-09-03-autopick-refit-plan.md (approved 2026-09-03).
Written BEFORE any fit runs. Evidence that prompted it: three sidecar
rooms (10531886, 10532940, 10534350) show survival overconfident with
autopick seats (30-50% shown -> 0-57% observed; 50-70% -> 22-32%; 70-90%
-> 40-77%; 90-100% -> 81-94%); away-at-pick seats take the top player by
board ADP only 5% of the time (median rank 9, n 108) against humans' 13%
(median 6, n 269); by Yahoo's own default rank (`o_rank`, read from the
draft-room store) away picks are top-1 32% -- a third walk Yahoo's list,
the rest look human. The `away` flag flickers (connection status), so it
is an impure label; Yahoo's pick records carry no auto flag.

Labels (fixed now): `instant` = first seen with clock_left >= 27 of 30 AND
poll gap <= 2000 ms (new rooms only); `human` = clock_left <= 20; `away` =
the seat's team id was in away_teams at the nearest preceding plan call
(built from team ids, never from the slot map, which is empty for a seat
until it has picked); `bot` = Sleeper mocks; `human` = the Omnibeta real
draft; `end_away` / `unknown` = the four older trails and the five email
rooms; `ours` = our own seat, excluded from every fit.

Forms compared per seat class, likelihood = multinomial over the pool
available at each pick: (i) Gaussian in ADP with sigma(round) as today;
(ii) Gaussian in o_rank; (iii) label-conditional mixture, P(list | label)
= pi_label, list component = one-hot on the lowest-o_rank alive player
that fits an open starter slot, human component = today's Gaussian with
today's need multipliers. Pre-declared branch: if the top-1-by-o_rank
share of instant/away picks does NOT rise under the starters-first
filter, the list being walked is not o_rank and the list component becomes
a tight Gaussian in o_rank (sigma 1-2) instead of a one-hot.

Grid (values reported at grid precision only): pi in 0.1 steps;
sigma_early {4,6,8,10}; sigma_late {15,21,27,35}; autopick_sigma_scale
{0.75,1.0,1.5,2.0}; autopick_need_damp {0.02,0.15,0.30}; need_damp
{.15,.30,.45}. 1-D Wilks 90% profiles for every pi and sigma. Selection by
leave-one-room-out pick-level log-likelihood per pick, not AIC.

Gates:
- G1 (primary): LORO pick-level log-lik per pick for the away/instant
  class improves over form (i) at today's knobs; the 90% CI of pi_away
  excludes 0.
- G2 (deployment): survival Bernoulli log-loss at the fitted point <=
  current, LORO, pooled AND autopick views; calibration: no bucket with
  effective n >= 30 whose cluster-bootstrap (room, window) 90% CI of
  (observed - predicted) excludes 0, pooled or autopick view. Human view
  reported; human knobs flip ONLY if the human view's log-loss improves
  and its buckets pass.
- G3 (no regression): slot_replay both Sleeper leagues, fitted vs current,
  mean lineup points not worse (autopick knobs inert there); the new
  yahoo_trail_replay on the sidecar rooms, all 10 slots, not worse.
- G4 (forward): after the freeze, TWO new mock rooms drafted live with the
  fitted knobs, fresh Yahoo ADP and o_rank captured that day; offline both
  knob sets scored on those rooms: fitted pooled survival log-loss lower,
  the 30-70% bucket miss smaller pooled, no single room worse by > 0.01.
- Decision: G1 and G2 and G3 and G4 -> autopick_list_prob,
  autopick_sigma_scale, autopick_need_damp flip in config.yaml and the
  Tracker defaults; the yahoo_rank board column ships. Any fail -> knobs
  stay; the study is recorded; yahoo_rank still ships (data, not a
  decision). If pi_away's CI from three rooms spans more than +-0.15, the
  user is asked whether to run two more fit rooms first; the mock count
  is never widened silently.

Honesty clauses: three rooms establish the SIGN of the miss, not its size;
a bucket of n 15 cannot fail an 8-point bar (binomial SE 7.7 at p 0.9),
hence the CI bar and effective n; survival rows are clustered by (room,
window) and are the deployment check, not the fitting objective; fit and
forward rooms share the board but not the ADP date -- drift measured per
room, players moving > 10 ADP picks between scrapes are unscoreable, not
misses; nothing is identified beyond its profile CI. Engine change ships
with autopick_list_prob = 0 (byte-identical) until the decision.

### #35 G1 result (2026-09-03, before any survival replay ran)

Dataset: scripts/pick_dataset.py -> 938 rival picks over 7 Yahoo rooms
(reports/rival_picks.md). Need-rule check: among away-labelled picks whose
taken player fits an open starter slot, 80% are EXACTLY the lowest Yahoo
rank that fits (vs 8% by board ADP); the pre-declared one-hot list
component stands. Only ~47% of away picks fit an open starter at all --
the other half behave like humans (the away flag is impure, as expected),
so over ALL away picks the exact-hit share is 38%.

Fit: scripts/rival_fit.py (reports/rival_fit.md), multinomial over the
pool at each pick, coarse grid, LORO by room.
- away (n 102, 3 rooms): mixture pi 0.3 [90% 0.3-0.4], sigma_early 4
  [4-6], sigma_late 27 [21-27], need_damp 0.45 [0.45], scale 0.75
  [0.75-1.0]. LORO log-lik per pick: mixture -3.005, gauss_adp -3.908,
  gauss_yrank -4.172, CURRENT -4.865. G1 PASS (better held-out, pi CI
  excludes 0).
- human (present-at-pick, n 300): mixture pi 0.2, need_damp 0.45, sigma 4
  -> 27; LORO -3.404 vs current -3.940. Humans also lean on Yahoo's
  default-sorted list. Recorded for the human sub-gate; no human knob
  moves on this alone.
- unknown (4 older trails, n 536): mixture pi 0.3; LORO -3.348 vs -4.024.

Deviation from the pre-registration, stated: the fit used ONE need_damp
grid {.15,.30,.45} for every class, so the away class's 0.45 lies outside
the pre-registered autopick_need_damp grid {0.02,0.15,0.30}. The survival
stage (G2) will evaluate autopick_need_damp over {0.15,0.30,0.45} and this
note is the record of the change. autopick_sigma_scale 0.75 is on the
pre-registered grid; autopick_list_prob 0.3 is on the pi grid.

What pi_away means: the deployable list-walk probability GIVEN the live
signal is Yahoo's away flag (impure). The timing label (new rooms) should
separate true autopicks (pi_instant expected >= 0.8) from flagged humans;
until it exists, 0.3 is the honest value for the flag we have.

### Draft-day data-shape risk (2026-09-03, user's question)

The league room has never been observed by the driver; every mock ran in
the mock client. Mitigation recorded in docs/draft-day-runbook.md: a store
structure fingerprint at preflight compared against the mock rooms'
(`data/draftrig/store_fingerprint.json`, to be captured from mock 27's
room), entry the minute the league room opens with a full idle preflight,
the four independent layers restated, keepers flagged as untested, and a
code freeze from Friday evening. The fingerprint code is a small addition
to preflight and ships with the trail panel.

### Queued (2026-09-03, user's call): multi-source board tried in mock rooms, exploratory

After the trail panel, the fingerprint check, the board rebuild and the
refit's forward rooms: build the multi-source board (projections.external
combine: mean, sources sleeper + espn, late_round_dispersion on) side by
side with the shipped board, publish the diff (movers by more than a
round; replay churn by tier on the archived drafts), then draft one or two
mock rooms on it with the same narration. Stated limits, so nobody reads
the result as evidence: a mock grades a board by its own projections and
its rivals score no real points, so these rooms can show pipeline
soundness, churn and eye-test sanity, never accuracy. The default stays on
#23's verdict; the January scoring of the frozen forward snapshot (#30)
decides 2027. Saturday drafts on the validated board regardless.

### #35 G2 result (2026-09-03 01:40 PT): log-loss half PASS, calibration half FAIL as written

scripts/fit_survival.py --fit --stage autopick --loro --sims 200 --every 2
(reports/survival_loro.md). Four sidecar rooms (24-27), leave-one-out,
coordinate fit from CURRENT on the other three.
- Every fold lands on the same point: autopick_list_prob 0.3 (one fold
  0.4), autopick_need_damp 0.45, autopick_sigma_scale 0.5 (the stage kept
  the current scale; the pick-level fit preferred 0.75 -- within its CI).
- Held-out Bernoulli log-loss, fitted vs current: 0.1520/0.1632,
  0.1688/0.1889, 0.1481/0.1585, 0.1641/0.1797; pooled 0.1582 vs 0.1726.
  Better in all four folds. The log-loss half of G2 PASSES.
- Calibration at the fitted point (cluster-bootstrap 90% CI of obs-pred,
  >= 30 clusters): 30-49% -8 [-14,-1], 50-69% -5 [-8,-2], 70-89% +2
  [0,+4] -- three buckets exclude 0. At CURRENT in the same harness the
  same buckets read 0 [-9,+9], +3 [-3,+8], +2 [0,+4]. The calibration half
  FAILS as pre-registered.
- Caveat that must ride with the result: this harness scores states
  rebuilt with the league config but 200 sims and the harness pool, and in
  it CURRENT looks calibrated -- while the four LIVE rooms (production
  knobs, 1000 sims) scored CURRENT at 90-100% shown -> 79-94% observed and
  70-90% -> 37-77%. The harness and the live scorecards disagree about the
  current model, so the harness is not a clean judge of either point. The
  live scorecards of the forward rooms (G4) are the production measurement.

Call, by the rule as written: G2 fails -> the default does NOT move on
this evidence. The forward rooms still run at the fitted point, as
pre-registered, and their live calibration (both knob sets scored offline
on the same realised states) is recorded for the decision after
2026-09-05. If the user wants the rule amended (calibration judged on the
live forward rooms rather than the harness), that is an explicit
amendment recorded here, not a reinterpretation.

### #35 G3 result (2026-09-03 01:47 PT, replays finished during mock 28)

Logs: data/processed/backtest/g3_slot_{keefamania,omnibeta}.log,
g3_trail_{10531886,10532940,10534350,10584427}.log.

- Sleeper slot_replay at the fitted point: keefamania by-slot vs by-position
  mean -1.3 (0 better / 1 worse / 9 tied), omnibeta mean -1.9 (3/4/5) --
  identical to the current-knob runs, as pre-registered: no away seats, the
  autopick branch is inert. No regression, trivially.
- Yahoo trail replay, all 10 slots, fitted minus current, mean lineup
  projected points: room 10531886 -7.4 (0 better / 2 worse / 8 tied, worst
  -45.1); 10532940 -1.9 (1/2/7, worst -31.6, best +25.2); 10534350 -1.6
  (0/1/9); 10584427 -0.5 (0/2/8). Every room slightly worse; 34 of 40 slots
  tied.
- G3 as written ("not worse"): FAIL, by 0.03% to 0.40% of lineup points.
  Reading: the fitted seat is more urgent (lower survival on list-walk
  targets), so it takes a few players a turn earlier than it needed to when
  the historical room did not actually take them; the replay holds rival
  picks fixed, so it can only ever charge urgency, never credit it. Six
  slots moved; the size is within one bench player's projection. Recorded
  as a fail; the rule is the rule.

Gate tally before G4: G1 PASS, G2 log-loss PASS / calibration FAIL, G3
FAIL. The default cannot move on this study. G4 (two forward rooms at the
fitted point, scored offline at both knob sets) still runs, because it is
the only out-of-sample live evidence and it decides whether a second study
is worth the user's mock time.

### #35 G4 interim, forward room 1 of 5 (mock 28, room 10586715, drafted at the fitted point)

Scored offline with `fit_survival.py --confirm-point ... --rooms 10586715
--confirm-sims 400 --every 1` at both knob sets (logs
data/processed/backtest/g4_10586715_{fitted,current}.log; JSON under
reports/g4/). Whole-pool survival vectors at every state, 15 windows.
- log-loss: fitted 0.1452, current 0.1601 -> fitted better by 0.015.
- 30-70% buckets (observed - predicted): fitted 30-49 -5 (n154), 50-69 -6
  (n421); current 30-49 +4 (n167), 50-69 +1 (n470). The fitted point
  over-promises survival in the middle buckets on this room; current is
  nearer zero. CI bar: both PASS (under 30 clusters, so the bar cannot flag).
- G4 per-room reading: log-loss criterion met, 30-70 miss criterion NOT met.
Extension (user, 02:15 PT): four more rooms, live knob set alternating
(room 2 = current), each scored at both points; the G4 verdict is taken on
all five together, criteria unchanged.

### #35 G4 interim, forward room 2 of 5 (mock 29, room 10588125, drafted at CURRENT)

Scored offline at both points (logs data/processed/backtest/g4_10588125_*.log),
7 windows (seat 1's pairs), whole-pool vectors.
- log-loss: fitted 0.2213, current 0.2366 -> fitted better by 0.015 (same
  size as room 1).
- 30-70% buckets (observed - predicted): fitted 30-49 -5 (n476), 50-69 -1
  (n546); current 30-49 +8 (n504), 50-69 -1 (n766). Fitted's middle-bucket
  miss is the smaller one on this room (6 vs 9 points summed).
- G4 per-room reading: both criteria met for fitted. Tally after two rooms:
  log-loss 2/2 fitted; 30-70 miss 1/2. Caveat: this room's driver lost two
  turns to a background-tab stall (Yahoo autopicked 80-81), which changes
  our roster history but not the survival rows, which are scored on rival
  behaviour between our turns.

### #35 G4 interim, forward room 3 of 5 (mock 30, room 10589182, drafted at the fitted point)

Logs data/processed/backtest/g4_10589182_*.log, 7 windows.
- log-loss: fitted 0.1973, current 0.2130 -> fitted better by 0.016.
- 30-70% buckets (observed - predicted): fitted 30-49 -1 (n392), 50-69 +1
  (n544); current 30-49 0 (n399), 50-69 +1 (n739). Tied within a point;
  current nominally smaller (1 vs 2 summed).
- Tally after three rooms: log-loss 3/3 fitted, by 0.015-0.016 each time;
  30-70 miss fitted 1, current 2 (one of them a one-point tie).
Room 4 (10590238) runs at CURRENT with the throttle-proof driver.

### #35 G4 interim, forward room 4 of 5 (mock 31, room 10590238, drafted at CURRENT; clean room)

Logs data/processed/backtest/g4_10590238_*.log, 15 windows (seat 7).
- log-loss: fitted 0.1311, current 0.1554 -> fitted better by 0.024, the
  largest margin of the four.
- 30-70% buckets (observed - predicted): fitted 30-49 -24 (n218, CI
  [-31,-15], 15 clusters), 50-69 -7 (n344); current 30-49 -4 (n262), 50-69
  +9 (n489). Fitted's middle miss is the larger (31 vs 13 summed) and its
  30-49 CI excludes zero, though under the 30-cluster bar.
- Tally after four rooms: log-loss 4/4 fitted (0.015, 0.015, 0.016,
  0.024); 30-70 miss fitted 1, current 3. The pattern from G2 holds out of
  sample: the fitted point is better at the overall score and over-promises
  survival in the 30-50 range. Room 5 (10590944, fitted) closes the set.

### #35 G4 result and the decision (2026-09-03 04:10 PT, five forward rooms)

Rooms 10586715 (fitted live), 10588125 (current), 10589182 (fitted),
10590238 (current), 10590944 (fitted); every room scored offline at BOTH
points, whole-pool survival vectors, 400 sims, every state
(data/processed/backtest/g4_<room>_{fitted,current}.log).

| room | fitted LL | current LL | delta | fitted 30-49 / 50-69 | current 30-49 / 50-69 |
|---|---|---|---|---|---|
| 10586715 | 0.1452 | 0.1601 | -0.0149 | -5 / -6 | +4 / +1 |
| 10588125 | 0.2213 | 0.2366 | -0.0153 | -5 / -1 | +8 / -1 |
| 10589182 | 0.1973 | 0.2130 | -0.0157 | -1 / +1 | +0 / +1 |
| 10590238 | 0.1311 | 0.1554 | -0.0243 | -24 / -7 | -4 / +9 |
| 10590944 | 0.1809 | 0.1977 | -0.0168 | -7 / -3 | +5 / +6 |

Pooled, n-weighted (observed - predicted): fitted 30-49 -7.1, 50-69 -2.7
(abs sum 9.8); current 30-49 +3.3, 50-69 +2.8 (abs sum 6.1).

Against the pre-registered G4 criteria:
- fitted pooled log-loss lower: PASS, and in every single room, by 0.015
  to 0.024. This is out-of-sample and unambiguous: the fitted rival model
  predicts what these rooms do better than the current one.
- 30-70% bucket miss smaller pooled: FAIL. Fitted over-promises survival
  in the 30-50 range by 7 points pooled (five of five rooms negative);
  current under-promises by 3.
- no single room worse by > 0.01: PASS (none worse at all).

G4: FAIL as written (two of three). Gate tally: G1 PASS, G2 log-loss PASS
/ calibration FAIL, G3 FAIL (small), G4 log-loss PASS / calibration FAIL.

DECISION: the default does NOT move. config.yaml and the Tracker keep
autopick_list_prob 0.0, autopick_need_damp 0.02, autopick_sigma_scale
0.5 for the 2026-09-05 draft. The yahoo_rank column stays on the board
(data). The engine change stays in the code behind its knob.

What the study established, for the record and for January: the
list-walk mixture is the better description of autopick seats (G1, G2,
G4 all say so on log-loss, in and out of sample), AND at the fitted point
it is over-confident in exactly the 30-50% range where the engine's
"wait or take" decisions live, while the current model is slightly
under-confident there. The two knob sets bracket the truth. A middle point
(autopick_list_prob 0.2, or the fitted point with a survival shrink on the
30-70 band) is the obvious next candidate, and it is a NEW pre-registered
study, not a tweak before Saturday. Reading of G3's small regression in
that light: a model that is over-confident about losing players takes
them a turn early; the fix belongs in calibration, not in abandoning the
list-walk.

Rig outcome of the same night: the last two rooms (mocks 31 and 32) were
clean, 15/15 engine picks each, on the final driver (worker sleep,
60 s heartbeat, fingerprint fix). The clean-room rule for Saturday is met.

## 2026-09-03 (36) — bench-insurance wire measured a ghost; minimal fix, measured

User question during mock review ("isn't Josh Jacobs injured?") exposed it:
waiver_ppw's fallback took the WORST REMAINING player as the wire floor
when no undrafted-by-ADP player existed at the position. On this board
that was always a player availability-zeroed to 0.0 points (Jacobs,
Commissioner Exempt; Charbonnet likewise flagged), so every RB insurance
edge in mocks 28-34 was measured against a ghost: Tracy's "+10.9/wk over
the wire" was his raw output, ~105 pts instead of an honest ~79.

Fix (draftkit/bench.py): the wire can never be a player who projects 0 or
is availability-'out'. Free list and fallback both filter to viable
players; nothing else changes. A replacement-level floor was considered
and REJECTED: measured on the night's 194 recorded bench decisions it
flipped 77 (replacement is a starter baseline, not a wire), while the
minimal fix flips 20 of 223 — all late coin-flips (RB depth vs a WR worth
±2 pts of insurance). The RB wire moves 0.0 -> 2.7/wk (Ollie Gordon II)
across all seven rooms; big calls unchanged. Test:
test_wire_never_names_a_zeroed_or_out_player. Full suite 478 green.

Also shipped, display-only: the pair stage records its arithmetic per
candidate (own-now, expected partner, pair total, pick_cost = best pair
minus this pair) through plan rows to the panel and reports, so "why not
the higher waiting-cost player" is answerable from the record (user
request after mock 32 pick 22). Panel plan lines are now one candidate
per line with BOTH costs: wait (position decay) and pick (pair regret).

## 2026-09-03 (37) — the bridge "restarts" silently failed; true arm history of the forward rooms

Mock 35's whys still named Josh Jacobs as the wire after #36 shipped,
which exposed an operations defect: the restart command filtered
Get-Process on .CommandLine, a property PowerShell 5.1 does not populate,
so the kill matched nothing; and the bridge's allow_reuse_address lets a
second Windows process bind 8443 without an error, so each new bridge
started, logged its banner, and served NOTHING (its .log shows zero plan
calls). Six zombie bridges were found and killed at 15:40 UTC.

True serving history (from plan-call counts per process log and the call
counter continuity in the room sidecars):
- forward1, FITTED knobs, pre-#36 code: served mocks 28, 29, 30, 31, 32.
- forward6, CURRENT knobs, pre-#36 code: served mocks 33, 34, 35.
All intermediate "restarts" (forward2-5, 7, 8) never served a request.

What this breaks and does not break:
- The #35 G4 verdict STANDS: its criteria are scored OFFLINE at both knob
  sets on each room's realised states, independent of the serving arm;
  and the original pre-registration wanted the forward rooms drafted live
  at the fitted point, which rooms 28-32 all were.
- Mock-log live-arm labels for 29, 31 (said current, were fitted) and 34
  (said fitted, was current) are corrected in this commit.
- Mocks 33 and 35 both ran CURRENT: the "pair" is not a model comparison
  but a same-seat same-model reproducibility check, and a strong one:
  13 of 15 picks identical across different rooms (the two differences
  were availability, RJ Harvey and Jakobi Meyers taken earlier in room
  35). Pair B (seat 5, fitted, clean) is still owed: mock 36.
- #36's wire fix and the pair-math plan fields were NOT live in any room
  yet; mock 36 is their first live room.

Restart procedure from now on (runbook + rig memory updated): kill via
CIM Win32_Process CommandLine match, confirm "listeners: 0", start with
-PassThru, and confirm the port's OwningProcess is a CHILD of the new
PID before trusting the room to it; the driver preflight call# must be
small and fresh.

## 2026-09-03 (38) — the wire is who goes undrafted, not the board's ADP tail (user find #2)

The #36 fix stopped ghosts from being the wire floor but kept the
selection: players with ADP beyond pick 150. On this board that set is
essentially empty at RB (the projected tail carries ADPs inside 150), so
the fallback landed on the worst healthy projection, Ollie Gordon II at
45 pts (2.7/wk), and every RB insurance edge from round 5 on was inflated
by ~4/wk. The user caught it from the mock reports ("Ollie Gordon at 2.8
a week is not the RB waiver wire in a 10-team league").

Fix (bench.predicted_undrafted + waiver_ppw wire_names): the market
spends its remaining (150 - current_pick) picks in ADP order on the
remaining players it ranks highest; everyone left after that IS the wire;
the baseline is the k-th best projection inside that set per position.
Test: test_wire_is_kth_best_projection_among_predicted_undrafted.

Measured re-read of mocks 37 and 38 (exact per-state wire): honest RB
wire ~118-123 pts (~7/wk), WR ~114, QB 248 (Brissett). Insurance values
compress hard (Tracy 80 -> 36; Metcalf 18 -> 7; round 11+ becomes 0-1 pt
coin flips, the true depth of a 10-team wire). Composition: Tracy still
wins his slot in both rooms; ONE real flip per room, pick 98, where
honest wires put Mahomes-as-QB2 (8) over RJ Harvey (6) — an order swap
with pick 103. Live from mock 39's bench rounds (bridge forward12,
verified port owner, restarted mid-room during round 3).

## 2026-09-03 (39) — two planner corrections from the user's read of the pair reports

1. NEAR-TIE RULE (planner.pair_rank, NEAR_TIE = 1.0). When two candidates'
   pair values are within a point, the pair is worth the same either way
   but only completes if the second player is there next turn, so the one
   LESS likely to survive goes first. Measured on the 163 recorded
   starter-phase plans of rooms 37-39: 7 flip their top pick (4%), among
   them the user's example verbatim (room 38 pick 38: Garrett Wilson 85% ->
   Cam Skattebo 75%, pairs 64.3 vs 63.5). The why gains "near tie (x pts):
   scarcer player first"; a runner-up's pick_cost is clamped at 0.
   Test: test_near_tie_goes_to_the_scarcer_player.

2. FALLBACK PRICED AT MIN(BLEND, MARKET) (tracker._fallback_points). The
   fallback ("the player you would end up with") was the MAX of our blend
   projection over the ADP survivors, which selects the model's largest tail
   over-projections by construction (winner's curse): RJ Harvey blend 155,
   market 136, consensus 118; Gainwell 154/135/121; Tracy 127/109/95. Across
   all ADP-90-150 RBs the model actually sits 18 pts UNDER the market on
   average, so this is selection, not a uniform floor bias. An inflated RB
   fallback shrank every RB candidate's own value and tilted the pair coin
   flips toward WR. The fallback now prices each survivor at the lower of
   blend and market-implied projection (proj_market_pts, newly carried into
   the engine pool by yahoo_bridge.load_players and engine_parity.load_board;
   it was never in the pool before). Test:
   test_fallback_is_floored_by_the_market_projection. Effect on recorded
   rooms not re-measured state-by-state (the fallback is not in the sidecar);
   the first live room will show it in the pair math.

Both ship with the driver update of the same commit: rival pick lines
carry the manager's name, the panel rests the client on the Board tab
between actions, and the panel is translucent with tagged, coloured lines.

## 2026-09-04 (40) — the market curve that never decayed: measured, and it does NOT ship

Pre-registered before the numbers existed; thresholds below were fixed in
advance and none moved after they were seen.

**The defect.** Pooled over both leagues and both backtest pairs, banded by
within-position ADP rank, the market term loses 60 points across RB ranks 1-13
and 7 points across ranks 37-60, while the actuals in those bands fall 118 -> 88
and are still falling. Two mechanisms compound: ln() flattens, and a
per-position curve fitted on OVERALL market rank inherits the published ADP
feed's own tail compression (RB ranks 49-72 all sit between overall ADP 148 and
174, so twelve players cost 0.12 in ln(adp) against 1.51 at the top). Third, the
fitted dependent variable is itself floored: usage at the RB tail is 127.6 and
pos_mean x 16 is 128. This was left open at #20: "a log-rank curve that never
decays is still the natural follow-up."

**Corrections recorded because they were tested and rejected before building.**
(1) Restricting the prediction to the fitted rank band moves 7 of 684 backtest
rows: the FFC feed stops near overall ADP 180 and `games >= 8` veterans reach the
end of the pool. It is kept as a production clause and labelled ungradeable here
rather than allowed to look like a pass. (2) Shrinking toward a replacement-level
anchor moves the tail UP: the mean over `games >= 4` spans 57-176 players
including every scrub and already sits below replacement level in all sixteen
cells (RB 7.20 vs 11.14 at rank 24). The anchor was left alone.

**Arms, separated on the user's instruction so a verdict names its cause.** In
`_market_curve` only, behind `projections.market_curve_tail.mode`, default off:
`blend_rank` = within-position ordinal rank as the regressor; `blend_rank_lin` =
+ `y ~ a + b*ln(r) + c*r` fitted by the same OLS on the same `games >= 8`
population; `blend_tail` = + tangent continuation past the fit, clamped at zero.
The linear term applies to RB and WR ONLY, fixed in advance on the evidence that
fitted c is stable and negative there in all four league-pairs and swings sign at
QB and TE. Choosing the list up front avoids selecting the shape on the same data
that grades the arm.

**Results.**

Deep bands (RB rank 37+, WR rank 49+), reports/tail_curve_bands.md:

| arm | keefamania deep ratio | omnibeta deep ratio | head MAE ratio | max top-12 move | deep rows moved |
|---|---|---|---|---|---|
| blend_rank | 1.017 | 0.997 | 0.998 / 0.997 | 10.8 / 15.5 | 64% / 72% |
| blend_rank_lin | 0.934 | 0.942 | 1.012 / 1.011 | 26.9 / 31.4 | 98% / 87% |
| blend_tail | 0.933 | 0.942 | 1.011 / 1.010 | 26.9 / 31.4 | 98% / 87% |

All four (league, pair) cells improve for blend_rank_lin: 0.944, 0.924, 0.954,
0.933.

Pooled accuracy, reports/tail_curve_gate.md: keefamania MAE ratio 0.996 with
Spearman -0.002, omnibeta 0.998 with +0.003. Both inside the #23 tolerances.

Outcome, the same 44 slot-drafts graded on actual lineup points: blend 1554.5,
blend_rank_lin 1530.8, delta -23.7 or **-1.53%**. Better in 25 slots, worse in
18, tied 1.

**Verdict against the pre-registered bars.**
- deep-band MAE at most 0.97 in both leagues: PASS (0.934, 0.942)
- deep-band at most 1.00 in 3 of 4 cells: PASS (4 of 4)
- anti-inertness, at least 25% of deep rows moving more than 1 pt: PASS
- head unchanged, MAE ratio at most 1.01 and no top-12 projection moving more
  than 2.0 points: **FAIL** (1.012 / 1.011, and moves of 26.9 / 31.4)
- outcome, mean lineup points at least 0.99x blend: **FAIL** (-1.53%)

**DECISION: the knob stays `mode: "off"`. Nothing ships.** config.yaml and the
Tracker are unchanged; both reference boards come back IDENTICAL under
`board_identity.py --check`.

**What was learned, which is the point of running it.**

1. The correction works on the band it targets and still drafts worse. Deep-band
   accuracy improved 6-7% and the drafted teams lost 1.53% of actual points. The
   arm wins more slots than it loses (25 to 18) and loses bigger, so it is a
   higher-variance board, not a better one.
2. This is the SECOND attempt to fix the tail by moving the projection level, and
   both failed the same half by a similar margin: the external source at -1.20%
   (#23) and this at -1.53%. Two independent routes to "lower the tail" both cost
   actual points. That is now a pattern and the next attempt should explain it
   before spending on a third.
3. The regressor swap alone is worthless: 1.017 and 0.997 deep, no material
   improvement. Had the three edits been graded as one unit, a pass would have
   been credited to it. Splitting them was the user's call and it is the only
   reason this is known.
4. **The head criterion was mis-specified and that is my error, not the arm's.**
   Any change to the regressor refits the whole curve, so "no top-12 projection
   moves more than 2.0 points" was unreachable by construction for every arm
   here, including the one that does nothing useful. It should have been stated
   as a bound on the head's ACCURACY (which passed at 1.012 against a 1.01 bar,
   a near miss) and not on projection movement. The bar is not moved
   retroactively; the outcome half fails independently and decides on its own.

**Still open, unchanged by this.** The usage-side floor (`pos_mean x 16`) is
untouched and remains the deeper cause. Any future attempt is a new
pre-registration and must first answer point 2: why lowering the tail keeps
costing lineup points even when it improves tail accuracy.


---

## #41 â€” 2026-09-03 â€” The outcome half cannot resolve the threshold it judges

**Answering point 2 of #40, and it is not the answer that was expected.**

#40 asked why two independent routes to a lower tail both lost the outcome half
by a similar margin (external source -1.20%, tail arm -1.53%) and said the next
attempt must explain it before spending on a third. The explanation is that
neither number was ever a measurement.

**What was wrong with the harness.** Rivals were pinned to exact consensus ADP,
so every replay of a pair made identical rival picks. The 44 slot-drafts behind
a verdict were therefore TWO draft universes sampled at 22 seats each, and
neighbouring seats see nearly the same board. Only our own seat varied. Reported
as "44 slot-drafts", a 1% delta claimed far more evidence than it had. Found in
a review of the harness, not of a result.

**The measurement.** `scripts/source_gate.py --seeds 5` redraws the rival room
with Gaussian ADP noise of 6 picks, the same draw handed to every arm so a
per-slot delta stays paired. The tail arm (`blend_rank_lin` vs `blend`), same
rows CSVs as #40, both leagues, both pairs:

| seed | Î” lineup points | Î” % |
|---|---|---|
| exact ADP (the #40 run) | -23.7 | **-1.53%** |
| 1 | -35.2 | -2.14% |
| 2 | -72.2 | -4.43% |
| 3 | +16.1 | **+1.09%** |
| 4 | +26.2 | **+1.69%** |

Pooled over 220 slot-drafts: blend 1572.0, blend_rank_lin 1554.2, Î” -1.13%.
Errors 0/0. Picks changed 1317 of 2860, so the arm is not inert. Better in 121
seats, worse in 94: it wins MORE often and loses bigger, consistent with #40's
higher-variance reading.

**Spread across seeds: 6.12 percentage points, against a 1% threshold.** Two of
five seeds say the tail arm is better. The per-seed standard deviation is 2.50
points of percentage, so the standard error of the mean at five seeds is 1.12% â€”
larger than the effect being judged.

**What this does and does not change.**

- It does NOT flip #40 or #23. Both applied their pre-registered rule correctly
  to the number in front of them, and the rule is not rewritten after the fact.
  Nothing ships on this entry. `market_curve_tail.mode` stays `off` and
  `projections.source` stays `model`.
- It DOES retire the "two independent routes both cost points, that is a
  pattern" reading in #40 point 2. There is no pattern. There are two draws from
  a distribution whose spread is six times the threshold, and both happened to
  land on the same side of zero. Chance does that about a quarter of the time.
- Any future entry citing the outcome half at the 1-2% scale is citing noise
  unless it reports a seed spread.

**What the outcome half is actually good for.** With five seeds it resolves
effects above roughly 3%. Below that it is a screen for gross regressions, not
an instrument. Getting the standard error to 0.25%, which would make a 1% effect
a four-sigma result, needs about 100 seeds â€” roughly eight hours at the current
cost. That is affordable overnight and is the price of any future 1% claim; it
is not worth paying for a screening run.

**Harness changes shipped with this entry** (commit `c3ce493`), each of which
would have caught something:

1. `--seeds N` and the per-seed spread table, with the report stating outright
   when the observed delta is inside the spread. It never moves the threshold.
2. Engine exceptions and an inert candidate now set `decision = invalid` and
   exit nonzero. An exception falls back to the best available player, a
   different and dumber drafting policy, so an arm that throws more often than
   another was not graded on the same engine. All four recorded runs were in
   fact 0/0 â€” luck, not a guarantee.
3. `slot_replay.py` no longer installs the league shape by mutating
   `engine_bakeoff.SLOTS` for every importer in the process.
4. `LINE_GAMES` is imported from `projection_backtest.SEASON_GAMES` instead of
   retyped, so the two cannot drift and rescale one arm against another.
5. Pool-capped replay depth is named in the report, and the limitations section
   states that `ecr` is null on the history boards, so an arm differing only
   through ECR would surface as inert rather than as a pass.


## 2026-09-04 (42) — six defects around "the alternative"; five ship as no-ops, one is deliberately unshipped

A user-supplied critique named three flaws in how the engine prices the
alternative to taking a player now. All three point at real areas. All three
get the mechanism wrong, and underneath two of them sit worse defects than the
ones alleged. Six items in total, every one behind a knob whose default is
today's behaviour, verified byte-identical on both league boards.

### The critique, corrected

**1. "The shared deadline undervalues taking a RB now." The direction is
backwards.** `fallback[pos]` enters `own_value` with a MINUS sign
(`planner.py:79`, `proj_pts - fallback[pos]`), so a LOWER fallback makes a
position look MORE valuable, not less. A later shared deadline leaves a scarce
position FEWER survivors, `max()` over that small bad set is LOW, and RB-now is
therefore PROMOTED. The code history agrees: the `min(blend, market)` floor was
added on 2026-09-03 precisely because the RB fallback ran too HIGH and tilted
pair coin-flips to WR.

Anyone reasoning about this function must carry the sign. It is the single
easiest thing to get backwards here, and getting it backwards inverts the
recommendation.

**2. "`vorp_flex` goes stale." True, and nearly harmless — but the cancellation
is MARKET-LOCAL, not global.** `flex_repl` is one constant applied to every
member of a market whose membership is exactly the flex-eligible set, so it
cancels in shortlist ordering, in the 2-point near-tie window, in urgency, and
in the `_replacement_points` round-trip (identity by construction — a "fresher"
value would BREAK the conversion at `planner.py:135`).

It does NOT cancel in two places, and both are fixed below: the `abs()` upside
boost (E) and the market/bench seam (B). **Do not cite "it cancels" as a general
property.** It cancels within one market's ordering and nowhere else.

**3. "The market -> bench handoff is where the QB2 bug lived." That case works.**
QB filled, FLEX filled, K/DEF open, round 11: `_open_markets` emits no QB row,
`_bench_candidates` fires, the backup QB is priced against the wire. Correct.
The structural instinct was right and the real seam is next door — when K and
DEF are ALSO filled, which is when `_open_markets` revives all six positional
markets while bench mode is running.

### What ships

| | defect | knob | default |
|---|---|---|---|
| A | max/min cliff in `_fallback_points` | `fallback_floor` | `board_min` |
| B | market/bench currency mixing | `bench_row_wins_dedupe` | `false` |
| C | `own_value` reverts to `slot_vorp` on an empty pool | (with A) | — |
| D | one deadline shared across positions | `per_position_deadline` | `false`, **stays off** |
| E | `abs()` upside boost is not baseline-invariant | `upside_boost_relative` | `false` |
| F | `k` keyed on waiver format at draft time | `draft_k` | `3` |

All five knobs live in `config.yaml`'s `engine:` block, not in a league file.
None of them is a fact about a league; they are engine behaviour, and the repo
rule puts behaviour in globals. A league can still override any of them through
the normal deep-merge.

**A — the cliff.** While ADP survivors exist the fallback steps DOWN as the
deadline passes each one. The instant the last survivor is crossed the operator
flips from `max` to `min` over the whole pool, ADP-None players included. ADP
order and projection order differ, so the pool minimum sits far below the last
survivor, and with the minus sign that is an instant board-wide UPWARD spike in
apparent value — firing at the scarce position, sized by whichever junk player
happens to be lowest-projected.

`replacement` treats streaming as a FLOOR UNDER EVERY ANSWER, not as the answer
when the position empties. **The first cut substituted it only in the empty
case, and the property test caught an 80-point step** — that variant merely
moved the cliff. The floor is also the truer statement: you can always stream,
so what you end up with is never worse than replacement whether or not a
draftable survivor exists.

Rejected: `bench.waiver_ppw`, which is the same idea but speaks per-week over
`FANTASY_WEEKS = 17` while `projections.games` is 16. A units assertion and a
test now pin both branches of `_fallback_points` to the season-total
convention, because that seam would otherwise break silently.

**C.** An empty pool used to `continue`, dropping the position from the dict;
`planner.own_value` then returned `slot_vorp` — a VORP LEVEL sorted against
points-above-fallback numbers in the same list. In `replacement` mode the key
always exists, so the currency cannot switch mid-sort.

**B — the seam.** Prefer the bench row, EXCEPT for an upgrade whose own
projection beats the starter he would displace: insurance prices a man who plays
only when someone is out, and pricing a genuine upgrade that way would trade an
incommensurable-currency bug for a systematic undervaluation of late upgrades.

**The preference has to be symmetric, and the first cut was not.** It blocked
market -> bench for an upgrade but never swapped an upgrade's bench row back to
his market row, so an upgrade whose bench row happened to sort first kept it.
That is the same coin flip with an exception bolted on. The regression test
that catches it exists because the first fixture did not: the seam needs K and
DEF filled too, and a collision needs one player to be both his market's best by
VORP and his position's best by insurance. In the original board the only such
player is the upgrade, so the knob changed nothing and the tests passed
vacuously.

**E.** `boost = (upside_mult - 1) * abs(mv(q))`. The `abs()` fixed a real sign
bug (a multiplier on a negative market value pushed the flagged player DOWN) but
it is non-linear, so a baseline shift reorders the shortlist — and `vorp` and
`vorp_flex` differ by a constant 30.3 points here. Measuring the span from the
market floor makes the boost a DIFFERENCE, which cancels the baseline the same
way urgency already does. Ordered first, before A, so the first board rebuild
did not run through the reordering hazard E removes.

**F — the k split, a true no-op.** `waiver_k` returned 2 for FAAB and 3 for
rolling, justified as "streaming friction as an order statistic". Both
production consumers were DRAFT-TIME. Two different quantities were sharing one
function because they share an operator:

| | what k hedges | justified by | waiver-typed? |
|---|---|---|---|
| draft-time | which undrafted player is really best | prediction error | **no** |
| in-season | someone else may win the claim | claim friction | **yes** |

`draft_k` ships at **3, today's value**. An earlier draft of this plan set 2 and
recorded in the same paragraph that it contradicted its own justification.
Shipping a number the plan argues is backwards is worse than shipping the status
quo. Deep-band MAE is 65-70 points (#40); at that error the best undrafted RB is
a coin flip among several, which argues for hedging HARDER than 3, not softer.
A derivation from that error is the thing that should move this number.
`waiver_k` keeps the format table and stays on the in-season path, where
`scripts/derive_baselines.py` replays weekly claims and claim friction is
exactly what it models. A grep test now fails if the draft path reaches
`waiver_k` again — a value test would not have, because both answered 3.

### D is implemented, measured, and deliberately NOT shipped

One deadline is summed over every open starter slot including FLEX, so a
held-open flex pushes the horizon later for QB too. With A fixed this is no
longer a correctness issue; it is a modelling disagreement, and the code comment
says so instead of picking a winner:

- **Shared is right if picks are a shared budget.** Spending one on a flex
  really does push the quarterback later, whether or not a quarterback could
  have filled that slot.
- **Per-position is right if each position has its own queue.** Positions empty
  at very different rates, and "who survives to my pick 90" is a fair question
  for TE and a meaningless one for RB.

**Nothing available can settle it.** Churn is not a verdict ("gates measure
quality, not churn"). Lineup points cannot resolve below ~3% (#41: 6.12pp
between-room spread against a 1% threshold, and with only 2 seasons x 2 leagues
more seeds do not shrink it). So this is not a knob awaiting a coin flip; it is
a documented, measured, unshipped option.

**What would unblock it:** more season pairs in the backtest (2022->2023,
2021->2022), which is its own piece of work.

### Churn, reported as a diagnostic and nothing more

`scripts/knob_churn.py`, 10-seat and 12-seat offline replays, rivals held fixed.

| arm | keefamania | omnibeta |
|---|---|---|
| A+B+E on (the shipped set, D off) | 50 / 150 (33.3%) | 20 / 180 (11.1%) |
| D alone | 49 / 150 (32.7%) | **107 / 180 (59.4%)** |

The shipped set reorders within positions rather than changing roster shape:
keefamania's churn is concentrated in rounds 2-7 and the last two rounds, and
the position mix barely moves (RB 14 out and 14 in, K and DEF 6 and 6).
Omnibeta is a third of that.

**D is a different animal, and this is the strongest argument for leaving it
off.** On omnibeta it changes 59.4% of picks and it moves ROSTER SHAPE, not just
ordering: 39 RB picks leave and 29 arrive, while 22 WR picks leave and 32
arrive — a net ten-pick swing from running back to receiver, spread across every
round. A change that large in the direction the whole engine exists to get right
is exactly the change you must not ship on a scoreboard that cannot resolve it.

**None of this is evidence either way.** It is here so a later reviewer can tell
"inert" from "reaches the early rounds" and "reorders" from "restructures the
roster" without re-deriving any of it.

### Verification

- 663 tests pass.
- `scripts/board_identity.py` IDENTICAL on both leagues with every knob at its
  default, F included.
- The A continuity property test sweeps the whole deadline range against the
  real decision function and asserts the curve never rises and never steps
  further than the gap between two adjacent players. Today's `board_min` fails
  it, which is the point: without that first test the second proves nothing.
- The stale `data/draftrig/ref_model.*.csv` references were re-cut. They
  predated the sheet-source rebuild and the `proj_band` column, so the
  documented check had been reporting drift that no uncommitted change caused.

## 2026-09-04 (43) — RB-only games table: accuracy passes, outcome unresolvable, NOT shipped

**Pre-registered before running.** DECISIONS #31 failed the games-table gate
pooled across positions, while its own per-cell table showed RB MAE improving
in all four (league, pair) cells and QB/WR/TE mostly worsening. The obvious
sub-experiment: apply the absence table to running backs alone and leave every
other position on the base arm. Arm `blend_gt_rb`, written by
`scripts/games_table_gate.py` as a sibling of `blend_gt`, judged by
`scripts/source_gate.py` unchanged with `--candidate blend_gt_rb --rivals blend`.
Same two halves, same thresholds, no gate code touched.

**Accuracy half: PASS in both leagues.** Keefamania MAE 57.8 → 57.1
(ratio 0.988), Spearman 0.476 → 0.481. Omnibeta 63.0 → 62.5 (0.992),
0.467 → 0.465. Every non-RB cell is byte-identical by construction, so the
entire pooled gain is the four RB cells: 56.0 → 54.7, 68.2 → 65.2,
59.3 → 57.8, 70.6 → 68.7.

**Outcome half: unresolvable, exactly as #41 predicts.** One seed said
+0.44% (24 better, 20 worse). Five seeds said **−0.48%**, 99 better, 110
worse, 11 tied, with a **spread across seeds of 6.87 points of percentage**.
The sign flipped between one seed and five. `resolvable: False`. The
mechanical decision string reads "flip" because both halves pass their
pre-registered thresholds; the outcome pass is a pass of a test that cannot
see a half-percent effect, and this entry does not cite it as evidence.

**What the evidence supports.** The accuracy half alone: the games table
improves RB projections and does nothing to any other position. That is a
clean, isolated, out-of-sample result on two season pairs and two leagues.

**Not shipped, and why.** The same day this ran, the user moved Keefamania to
the FantasyPros sheet alone (#44). The games table applies on the external
path too (`external_projection` scales by `games_table.games_expr`), so
turning it on for RB would rescale the sheet's running-back lines by the
absence bands. That is a defensible projection improvement and it is not
"solely the sheet". The decision belongs to the user, with this entry as the
evidence. Config knob unchanged: `projections.games_table.enabled: false`.

Artifacts: `reports/games_table_gate_rb.md` and `.json` (five-seed run),
`reports/projection_backtest.*.gt.rows.csv` with the `blend_gt_rb` column.

## 2026-09-04 (44) — Keefamania drafts on the FantasyPros sheet alone; Yahoo ADP refreshed; what the replays can and cannot say

**Decision (user).** For the real draft, Keefamania's projections come solely
from the FantasyPros consensus sheet (as of 2026-09-01). `projections.source:
external`, `sources: [sheet]`, `combine: first`, set in
`leagues/keefamania.yaml` and deliberately NOT in `config.yaml`: config is
global and Omnibeta is mid-season on the model path, so a global switch would
have silently re-priced the in-season manager. Omnibeta's board is
byte-identical to its reference after the change.

**This is a philosophy decision, recorded as one.** The external path is
built and verified end to end (2026-09-02). It has not been gated on history:
the sheet has none in the repo, and the only outside source that does
(Sleeper week-1 lines) lost to the model by 5% MAE and 1.2% lineup points
(#23). That stand-in is weak evidence about an expert panel and was never
claimed to be strong. The basis is the repo's own stated position: projections
are an input, the edge is roster-aware timing. Judged when 2026 is played.
The first follow-up is to find FantasyPros preseason projection history for
2023 and 2024, which would turn this into a measurement.

**`non_starters_zero` is off for this league.** On the first sheet build the
rule erased seven real sheet lines on drafted players and set them to zero
(Mendoza 191.6, Pacheco 103.6, Ferguson 103.0, Kamara 101.1, Sadiq 100.5,
Coleman 98.4, Njoku 86.4), declaring the panel wrong by 100% on a depth-chart
order. It was a crutch for a per-game usage rate that cannot say "he will not
start"; a consensus sheet already prices role. The separate availability rule
still zeroes `out` players (Jacobs, Charbonnet).

**The board.** 227 players against the model's 238 (191 sheet, 36 K/DEF
synthetic). The sheet omits Tyreek Hill (ADP 129), the one drafted player now
invisible to the engine; Jaydon Blue, Chubb and Pearsall are omitted but sit
outside the draft. Hollywood Brown fails the Sleeper name match and was absent
from the model board too. Shared skill players re-price at a median 1.07x
(WR 1.11x, RB 1.07x, QB 1.02x, TE 1.02x). McCaffrey #1 → #3, Allen #18 → #12,
Henry #17 → #9, Love and Jeanty enter the top 20; 108 of 224 shared players
move ten or more value ranks.

**Yahoo ADP refreshed from today's room snapshot.** The live file was the
08-31 hand scrape. Promoted the 12:07 room snapshot (players_10705481.json):
208 shared players, median move 0.3 picks, top 30 unchanged, Lloyd 120.8 →
96.9 and Jacobs 37.2 → 49.5 the only moves of ten or more, plus 19 K/DEF rows
the old file lacked. Of 221 players on both the pre- and post-refresh sheet
boards, proj_pts changed for 8, all K/DEF (their synthetic line keys on
market rank), and for zero skill positions.

**What the replays say, and what they cannot.** All three 2026-09-04 mock
rooms replayed on both boards, each roster then graded on BOTH sets of
projections:

| room | sheet-drafted minus model-drafted, on the MODEL ruler | on the SHEET ruler |
|---|---|---|
| 10703362 | −49.0 | +10.4 |
| 10704422 | −36.7 | +32.1 |
| 10705481 | −34.5 | +25.3 |

Each arm wins on its own projections and loses on the other's. This is the
"grading a change of belief against that same belief" trap already recorded
for tilts, and it means these replays are a behavioural smoke test, not
evidence for or against the switch. Only actual points can adjudicate it.

What the replays DO establish: the engine drafts a coherent roster on the
sheet board, and the shape changes. Sheet board, 30 of 30 seats across three
rooms: `QB2 RB6 WR4 TE1 K1 DEF1`. The model drafted a second TE in 10 of 30.
QB2 is 30 of 30 on both, so the source does not touch that pattern.

**First live picks on the sheet board** (room 10712781, seat 9, driver
injected with the room already at pick 9): pick 9 Derrick Henry, four seconds
after the driver started, RANKED ON 181.2 = 93.2 + 88.0; pick 12 Josh Allen,
whom the model board had passed for four rounds in room 10703362.

Commits: 9be946d (switch), afeb60d (page board), 2a2eb53 (ADP refresh).

## 2026-09-04 (45) — "the sheet" means the DraftSheet headline, not the position tab

User, reviewing room 10714820 pick 49 (Davante Adams): the page shows Adams
at 140, the board said 176.7. The board was reproducing the position tab's
AVG cell (x 16/17), which #44 recorded as "the sheet". The sheet carries
three numbers per player, from its own formulas:

* position tab AVG: the stat line scored in the Scoring tab plus the rookie
  bump, a 17-game total (Adams 187.8);
* Aggregate AVG = tab AVG / 17 x (16 - Missed Games), Missed Games from the
  RISK tab keyed by the player's ECR rank slot (QB1 2.12, WR23 3.16), a
  durability curve by rank and not player knowledge (Adams 141.9);
* DraftSheet PTS = AVERAGE(Aggregate LOW, AVG, HIGH, ECR!Pts), the sheet's
  "Zscore Projection" and the number the reader sees (Adams 140.3). ECR!Pts
  is a second line; for Allen and JSN it equals the Aggregate AVG, for Adams,
  Rice and Love it is lower.

Measured (scratch, 190 board players): headline / tab-basis median 0.82,
range 0.68-1.23; rank correlation within position 0.994 QB, 0.996 RB, 0.995
WR, 0.975 TE; five players move 5+ places. The order is the same. The gaps
are not, and the engine runs on gaps.

DECISION (user: "b"): `projections.external.sheet_line: headline` in
leagues/keefamania.yaml. Under "solely the sheet", the number the user
checks the engine against is the page's number, and matching it removes a
permanent source of confusion at no cost in order. It is NOT a measurement
of the rank-based durability haircut the headline carries: the games-table
analogue was a wash at QB/WR/TE and an improvement at RB (#31), and the
ECR!Pts term is ungated. Recorded as a definition of the input, not a
projection claim.

Implementation. `external.from_sheet(line=...)`: `tab` (unchanged default)
or `headline`, which reads `parse_draftsheet` (NAME/PTS blocks) and emits
source `fantasypros_sheet_headline`. `SOURCE_GAMES_CONVENTION` gains
`basis_games: 16.0` for it, `already_discounted: True`, and
`external_projection` divides by `source_basis_expr()` per row instead of
the 17 constant, so proj_pts equals the page and no games scale touches it
twice. A tab player the DraftSheet does not list (it VLOOKUPs the ECR tab)
is brought onto the basis at his position's median headline/tab ratio: left
on the 17-game tab line, Ja'Kobi Lane rose 64 value ranks on the first
rebuild for no reason but the basis. The band is carried at the same
relative spread. Tests: loader fixture with a DraftSheet tab, the basis
expression, and a parity test that every page player's proj_pts equals the
DraftSheet PTS on the real workbook (188 of 188; the two "misses" are
Jacobs and Charbonnet, zeroed by the `out` rule as intended). Omnibeta
byte-identical (board_identity). Suite 711 passed.

Board consequences: 225 players (189 headline incl. Lane estimated, 36 K/DEF
synthetic). Value-rank movers 10+: 34 of 225. QB compresses (Herbert up 13,
Jones down 41, Darnold down 21), TE up (Kraft, Okonkwo, Johnson), McCaffrey
falls behind Nacua/JSN/Brown at picks 3-7. The K/DEF synthetic lines
(150/135, 1.5/2.0 per rank) did NOT shrink, so K and DEF climb the value
ranks (Folk 129 -> 118); their DRAFT timing did not move (below).

Churn, tab board vs headline board, same engine, ten seats of the Omnibeta
log (scratch board_churn.py): 66 of 150 picks (44%), R1:4 R3:7 R4:7 R5:6
R6:8 R7:4 R8:7 R9:3 R10:5 R11:4 R12:6 R13:5; positions left QB10 RB33 TE3
WR20, taken QB10 RB30 TE5 WR21. K taken round 14.2 on both, DEF 14.8 on both.
Shapes: QB2 RB6 WR4 TE1 in 9 of 10 seats before, 7 of 10 after (two TE2
rosters appear). Churn is a diagnostic (gates measure quality, not churn);
the replays cannot adjudicate a projection source (#44), so no outcome
claim is made.

Point-denominated thresholds left as they were and noted: planner NEAR_TIE
1.0, the 2.0-point near-tie window and the "waiting costs" 1.0 floor in
tracker, bench insurance edges. On a scale 18% smaller they bind slightly
more often. Not retuned.

Same session, same league file: `engine.late_round_dispersion: true`
(league-scoped; Omnibeta stays false). Offline churn 0 of 150 picks vs off,
and room 10714820 (seat 9, dispersion on) showed no visible effect: the knob
picks the representative inside a market from round 8, and by then the open
markets are K and DEF. The bench path never reads the band. Recorded so
nobody credits or blames it for a pick.

Also this session (reports/survival_shown_diagnostic.md, commit 31994c7):
on the players the engine actually shows, survival is over-promised in
every bucket (81% shown / 49% survived, n=1474), and the split is distance
past ADP, not the Yahoo ranking source. Players still ahead of their ADP
are calibrated (98/97); players 5+ picks past it survive 41-46% against
93-96% shown; windows of 5+ rivals 75/22. Mechanism: the per-rival draw is a
Gaussian lottery in (pick - ADP) over the whole pool, so a faller loses
weight as he falls and every player is diluted by pool size. A `rival_draw`
study (Gaussian lottery | floored | noisy order), fitted through
survival_refit leave-one-room-out, is the next pre-registration; a display
calibration map would not reach the decision (e_best_next is the raw
simulation's joint expectation). Not run yet.

## 2026-09-04 (46) — survival: the rival draw form, pre-registered before the fit runs

Finding (reports/survival_shown_diagnostic.md, #45 tail): on the rows the
engine SHOWS, survival is over-promised in every bucket, and the split is
distance past ADP (players still ahead of their ADP calibrated 98/97;
players 5+ picks past it 93-96 shown, 41-46 survived). The whole-pool
vector #35 scored is mostly deep players who trivially survive, which is
why #35 read the current model as slightly under-confident: two
populations, and the decision rides on the shown one.

Mechanism (draftkit/urgency.py): the per-rival draw is a lottery over the
whole pool with weight = Gaussian in (pick - ADP). A faller LOSES weight
as he falls; every player is diluted by pool size.

Built, all behind `engine.rival_draw` (default `lottery` = today, byte for
byte): `floored` (distance floored at zero for players past ADP) and
`order` (lowest ADP + N(0, sigma) wins, multipliers as additive pick
penalties -sigma ln m). Harness: survival_refit gains a `shown` flag on
every row (the engine's top-8 recommendations at the state), a `--objective
shown|pool` switch, and a `rival_study` stage.

Pilot, four recent rooms, 200 sims, every third state (scratch
arm_tables.py, 449 shown rows): lottery shown log loss 0.696, floored
0.635, order 0.778; pool 0.180 / 0.175 / 0.242. Floored repairs the middle
(shown 60 -> survived 53 against 41) and leaves the top bucket where it
was (97 -> 82 under all three arms); order at sigma 6 overshoots (shown 9
-> survived 26). Read: the draw form and the noise must be fitted
JOINTLY, and the top-bucket miss is not a draw-form miss (list-walk
autopick seats, kickers especially).

PRE-REGISTRATION (before the run):

* Grid: rival_x_sigma = {lottery, floored, order} x sigma_early {6, 10,
  15, 20} (sigma_late scaled 27/6), then autopick_list_prob {0, 0.2, 0.4}
  on sidecar rooms. Coordinate search, best point on the grid.
* Objective: SHOWN log loss, mean over room types (equal weight; the one
  human room cannot be outvoted). Pool log loss reported alongside as a
  guard: a winner whose pool log loss is worse than current by more than
  0.010 does not ship.
* Confirmation at higher sims on current vs fitted, three views, shown
  and pool tables, cluster-bootstrap CI bars on the shown rows.
* Human room (sleeper_human, n small) reported separately; a point that
  wins pooled and is worse on the human room's shown log loss does not
  flip the live knob. Keefamania is a human league.
* Ship rule: LORO on the fitted point vs current, shown log loss, must win
  in a majority of held-out rooms and pooled. Then the knob moves in
  config.yaml (global: the rival model is not league-specific).
* Stated in advance: a corrected model will say "take him now" far more
  often on fallen players. That is what the record says it should do; the
  human split decides whether it holds outside autopick rooms.
* What the study cannot do: a display calibration map. e_best_next is the
  raw simulation's joint expectation; only a rival-model change reaches
  the decision.

Command: venv\Scripts\python.exe scripts\fit_survival.py --fit --stage
rival_study --objective shown --sims 100 --every 4 --confirm-sims 400
--workers 6 --fit-out reports/survival_fit_rival.md

## 2026-09-04 (47) — bench set (survival drop-off, contingency, band tiebreak): built, measured, NOT shipped

User-approved design (three items from the bench critique): rank bench
rows on cost of waiting (insurance now minus expected_best over the
position's candidates and their simulated survivals), add a contingency
term for a backup whose starter is on another roster (absence table x
uplift over my weakest starter, never stacked on my own handcuff), and
break bench near-ties (2.0 pts) on the published band from the upside
round. Knobs: engine.bench_survival_discount, engine.bench_contingency;
the tiebreak rides late_round_dispersion. Ten tests. Defaults off.

Measured on the season replay (the one grader that sees the bench:
empirical absences, wire streaming; scripts/season_replay.py --set, A arm
= insurance as shipped). reports/season_bench_knobs.md.

| arm | keefamania (10 seats) | omnibeta (12 seats) |
|---|---|---|
| all three | -17.9/season, se 1.0, 1 better 8 worse | -24.4, se 1.2, 2 better 10 worse |
| survival drop-off alone | -1.7, se 0.4, 4 better 2 worse | not run |
| contingency alone | -4.4, se 0.6, 1 better 5 worse | not run |
| band tiebreak alone | 0.0, ten identical rosters | not run |

Mechanism of the bundle's loss, visible in the roster shapes: seats end
QB1 RB7 (keefamania 8 and 9: -87 and -47; omnibeta 1, 2, 3, 11). The
contingency term inflates rival-backup RBs, the drop-off ranks them as
urgent because they do not survive, and the QB2, who always survives,
costs nothing to wait on at every turn and is never taken. Pure cost of
waiting has no notion that picks run out; the market path has the
must-fill window for that, the bench has no slot obligation. The season
grader, which streams a wire QB through the QB1's bye and absences,
punishes the missing QB2 hard, and in doing so says the round-10 QB2
the insurance formula produces is right.

DECISION: none of the three ships. All default off. What would change
it: a two-pick form for the bench (value now plus the expected best still
available at the OTHER positions next turn, so a safe large item is taken
as soon as nothing scarcer is worth more, and at the last bench pick
value is all that counts), measured the same way. Not built: the user
approved the drop-off form, and the measurement, not a redesign on the
spot, is what should reopen it. The band tiebreak is a true null here and
stays available for a board where bench near-ties are common.

Resolution note: the season replay resolves 0.4-1.2 points a season; a
-1.7 is small but real, not noise.

## 2026-09-04 (48) — availability re-verified against dated sources; Keefamania projection overrides retired; two-way players indexed

Availability (data/external/availability.csv), 33 rows re-verified today
by web search against dated reports (ESPN, NFL.com, CBS, NBC, team sites,
beat writers), notes rewritten with the source and date; the four
Sleeper-Q "flag only" rows from 8/31 with no news (Dicker, Metcalf, Evans,
Flowers) keep their date. Changes:

* to `out` (zeroed): Christian Kirk (IR, calf, 4+ games), James Conner
  (IR, foot, 4+ games), Tank Dell (must miss 4, "nowhere near ready"),
  Jordyn Tyson (IR, hamstring, 4+ games), Isiah Pacheco (IR, back, return
  "the hope"). Same rule as Charbonnet: a season-opening IR/PUP stint is a
  fact, and the `out` status has no partial-season form. Jacobs (exempt
  list, season opens on it), Charbonnet (reserve/PUP), Aiyuk
  (reserve/left squad), Higgins (IR, season) re-confirmed.
* rows removed: McCaffrey (healthy, full practice), Pittman (minor
  hamstring, no concern; a Steeler now).
* everyone else stays `compromised` with today's fact: Kamara (likely
  misses Week 1), Kittle (real chance at Week 1), Love (50-50), Egbuka and
  McMillan (not locks), Nabers (not committing), Monangai (week-to-week),
  Ty Johnson (up in the air), the rest trending to play.

Keefamania projection overrides (overrides.keefamania.csv): the five
Aug-19 candidate rows (Reed, Golden, Tuten, Tyson, Allgeier) are RETIRED,
the file is a header. Under #45 the projection is the DraftSheet headline
dated 2026-09-01, which post-dates every fact those rows carried; a
projection override against the sheet would contradict "solely the
sheet". Availability is the channel that remains. tests/test_overrides
updated to assert the retirement.

Two-way players: Sleeper's refreshed universe lists Travis Hunter as
position DB with fantasy_positions [DB, WR]; SleeperIndex bucketed by
`position` only, so the sheet's WR line for him did not match and the
board reported him UNPROJECTED at ADP 125. SleeperIndex now indexes every
fantasy position, primary holder winning a name collision. Hunter lands at
63.4 (headline basis, estimated: he is off the DraftSheet page). Sheet
names unmatched fell from 10 to 4 (three fullbacks, Hollywood Brown).

Also measured: the RB-only games table against the external proxy arm
(`lines_gt_rb` vs `lines`, reports/games_table_gate_lines_rb.md) passes
both halves (RB MAE 66.5 -> 64.1 on 2024->2025 keefamania, outcome +0.35%,
one seed). Moot on the headline basis: the sheet already carries a
rank-based durability haircut and `external_projection` excludes
discounted sources from the table. Nothing to ship; recorded so nobody
re-runs it.

Board after this: 226 players, 190 headline, 36 K/DEF synthetic, 5 zeroed
on the board (Jacobs, Tyson, Pacheco, Conner, Charbonnet; Kirk, Dell,
Aiyuk, Higgins are outside the pool). Suite 729 passed.

## 2026-09-04 (49) — the sheet's source has history after all: FantasyPros preseason consensus from the Wayback Machine gates as a flip

#44 and #45 recorded the sheet switch as a philosophy decision because the
repo held no history for it. FantasyPros' draft projections pages
(nfl/projections/<pos>.php?week=draft) are archived, and the draft page is
STATIC once the season starts: the November 2024 RB capture still shows
McCaffrey at 280.6, the December 2024 WR capture Nacua at 94.7 catches and
1,299 yards (he missed six games that year), Kelce within 3 points of his
May line. So a post-kickoff capture of the draft page is the preseason
table.

scripts/fantasypros_history.py: CDX lookup per position and season,
preference to captures in [Aug 1, kickoff], else the earliest after; the
wrapped capture parsed (Wayback rewrites URLs, never table text; the raw
id_ route sometimes returns gzip bytes); stat columns in the sheet's own
tab layout (external.SHEET_COLS), scored in league scoring so the page's
FPTS column and its scoring never enter. Captures used: 2024 QB Sep 5
(preseason), RB Nov 7, WR Dec 16, TE Dec 3 (static); 2025 QB Sep 2, RB Aug
26, WR Aug 20, TE Aug 22 (all preseason). data/external/fantasypros_history/
(8 files, 1,224 players). `--attach <league>` adds an `fpros` column to the
backtest rows (season T of each pair).

Gate (scripts/source_gate.py, candidate fpros, rivals blend and lines,
reports/fpros_gate.md): DECISION flip.
* accuracy: keefamania MAE 57.6 vs 57.8 (ratio 0.997), rho equal; omnibeta
  61.8 vs 63.0 (0.981), rho +0.021. By cell: RB on 2024->2025 is the big
  one (57.4 vs 68.2 keefamania, 58.8 vs 70.6 omnibeta), QB is worse in
  three of four cells (the model's QB regression is the better QB arm), WR
  and TE a wash.
* outcome: 44 slot-drafts, blend 1554.5 -> fpros 1700.5, +146.0 (+9.4%),
  better in 34, worse in 10; by pair +140.9, +228.8, +19.2, +208.0. The
  candidate changes 505 of 572 of our picks. One seed, rivals pinned to
  ADP, so the slot-drafts of a pair are one universe sampled at each seat.
  Prior source gates moved lineup points by about 1%; this is nine.

Reading. The gain is where the model's known weakness sat: #23 found the
board fat from RB 49 on, and the outcome half is exactly the draft that
punishes fat deep RB numbers. The consensus is not much more accurate on
MAE; it is much less wrong at the tail the engine drafts from. What the
history validates is the consensus LINE (the sheet's position tabs). The
headline transform (#45: rank-based durability haircut plus the ECR-tab
line, averaged) is not what was archived, so it stays a definition. And
the QB cells say the model's QB arm is better than the consensus; a
combine that keeps the model at QB is a candidate for 2027, not for this
draft.

Follow-up worth doing when time allows: 2023 captures exist for all four
positions (Sep 6, 2023); adding the 2022->2023 pair to the backtest would
give the gate a third season.

## 2026-09-04 (50) — housekeeping: wire floor, turn look-through, bridge double response, planner note

* `fallback_floor: wire` (new mode). #42's `replacement` floor churned 28%
  of picks on the headline board with the currency mismatch gone (the
  board carries no proj_market_pts, so _fb is the blend everywhere): the
  season baselines are drafted players by round 5, so as a floor they
  overstated what is freely available and bound in rounds 5-7 where
  nothing was empty. The wire (bench.waiver_ppw, draft_k-th
  predicted-undrafted player, x17) sits below every survivor while
  survivors exist and is the honest answer when a position is picked
  clean. Churn 8 of 150 picks, all K/DEF order in rounds 14-15. ON for
  Keefamania.
* `turn_look_through` (new knob). At the turn the survival window had zero
  rivals, every survival read 1.0 and both picks ranked on value alone.
  Now an empty window looks through to the following turn (opening after
  my consecutive pick) and pair_rank prices the partner at best_now
  (`partner_certain`). Churn 5 of 150, seats 1 and 10 only, rounds 4-6.
  ON for Keefamania. Harness note: draftlog.sim_window does not mirror the
  look-through, so the calibration record grades a turn-seat prediction
  against the short window; fix when the knob's picks are studied.
* bridge_server /plan: once the plan is on the wire, a failure in the
  post-response logging (or a client that hung up mid-write, the SSL
  EOF/BAD_LENGTH tracebacks of the day) is logged and never answered a
  second time.
* the two-pick planner's fallback note (`_planner_note`) now reaches the
  page in the plan's warnings; it used to stop on the tracker.
* not done, still open: survival_shrink rip-out, the JS local ranker, the
  two-pick bench form (#47's follow-up), merge_feed empty names,
  _pos_allowed must-fill, roster parser second copy.

Tests: tests/test_turn_and_wire.py (6). Suite 736 passed.

## 2026-09-04 (51) — the page no longer ranks; survival_shrink removed; the two-pick bench form measured and not shipped

The JS local ranker is gone (scripts/draft_driver.js, 165 lines). rank()
is now: the engine plan; else the last plan the gate dropped this turn,
kept as `stalePlan` and ranked minus everyone drafted since (source
`stale-plan`, the why prefixed "STALE PLAN (engine plan from pick N, M s
old; bridge unreachable)"); else nothing, labelled `none`, so draftTop
declines and the queue and Yahoo's list take the pick. The queue planner
still applies guardrailOk to the engine's rows, which is where the
guardrail coverage now lives in the driver tests (a stale plan listing a
QB2 before the gate or a K with ten picks left never reaches the queue).
Twelve tests that exercised the deleted ranker are gone, four are added.
Found on the way: the store-drafted check keyed on idKey folded Bijan and
Brian Robinson onto one key, so Bijan going at pick 2 marked Brian drafted
for the rest of the room; rows whose key collides on the board now match
on the whole name. The runbook and the scrutiny report know the label.

survival_shrink is removed outright: the knob, urgency.calibrate(), the
one-time warning, the logged field, the config block, the harness
override and the tests around them. `survival` and `survival_raw` remain
two keys over one vector (the page reads one, the calibration harness the
other). DECISIONS #26 retired it; nothing had read a value other than 1.0
since.

bench_two_pick (the follow-up #47 named): a bench position scores as its
insurance now plus the expected best insurance still gettable at the
OTHER bench positions next turn, value alone at the last bench pick.
Built behind a knob and measured on the season replay against insurance
as shipped:

| league | two-pick vs insurance | seats better / worse / tied |
|---|---|---|
| keefamania (10) | -0.0 / season, se 0.3 | 4 / 2 / 4 |
| omnibeta (12) | -8.2 / season, se 0.8 | 2 / 5 / 5 |

It fixes the QB2 starvation the drop-off caused (every roster keeps its
QB2) and buys nothing for it. DECISION: does not ship; default off. The
bench pricing as shipped stands, and with it the round-10 QB2 the user
asked about: the season grader has now said three times that it is the
right pick.

Bench work for a future season, if any: the bench formula's inputs are
position base rates and a wire; the only bench change the grader has
liked was the wire correction (#36). The next candidate is the grader
itself (two seasons of actuals, not a simulated season).

### #46 result (2026-09-04 21:50 PT): fit and leave-one-room-out both pass; the knob moves

Fit (scripts/fit_survival.py --fit --stage rival_study --objective shown,
41 rooms, sims 100, every 4th state, confirmation at 400;
reports/survival_fit_rival.md). Grid winner: rival_draw `order`,
sigma_early 10 / sigma_late 45, autopick_list_prob 0.2. Shown-row log
loss 0.596 against today's 0.742; pool 0.192 against 0.209 (guard
passes). Shown calibration, pooled, fitted vs current: 81% shown survives
70% (was 58%), 60% survives 45% (was 34%), 40% survives 31% (was 20%), the
top bucket 97% survives 90% (was 89%). Cost: the whole pool's bottom
bucket over-corrects (13% shown, 34% survive) and the human room's pool
under-promises its low and middle buckets by 13 to 15 points; on that
room's shown rows it is a wash at n=117.

Leave-one-room-out (--loro --stage rival_loro, a genuine refit per fold on
the coarse grid {lottery, order} x sigma {6, 10} then list-walk {0, 0.2};
reports/survival_loro_rival.md). The fitted point is the SAME in all 41
folds. Held-out shown log loss: fitted wins 35 of 41 rooms, pooled mean
0.528 against 0.613 (delta -0.085). The one human room (the Omnibeta
draft): 0.752 against 0.842, a win. Row-pooled whole-pool log loss:
0.1916 against 0.1832, worse by 0.0084, inside the 0.010 guard. The six
losses include two of today's three sheet-board rooms (10713941 +0.23,
10714820 +0.03), which is worth a look when more sheet-board rooms exist.

Against the pre-registration: objective PASS, pool guard PASS (fit and
LORO), human room PASS, LORO majority PASS, LORO pooled PASS.

DECISION: config.yaml (global; the rival model is not league-specific)
moves to rival_draw order, sigma_early 10, sigma_late 45,
autopick_list_prob 0.2. Pick churn of the point on the headline board,
ten seats of the Omnibeta log: see the line under this entry. Stated in
advance and now true: the engine will say "take him now" more often on
players past their ADP. The bridge was restarted on the new point.

Churn of the fitted point vs the old defaults, headline board, ten seats: 32
of 150 picks (21%), rounds 1-13, position-neutral (QB 5, RB 15, WR 10, TE 2
left and taken alike). The sim now takes fallers off the board sooner; the
roster shapes do not move.

## 2026-09-04 (52) — two follow-ups from the room 10726459 review

* Bench band tiebreak needs a margin. At pick 85 Pierce went over Tate on a
  band of 13.2 against 13.1 with Tate 3 projection points better; at 76
  Dowdle over Pollard and at 96 Mahomes over Dart went the same way on
  wider gaps. The tiebreak now fires only when the range is at least
  BENCH_BAND_MARGIN (20%) wider. Value still decides outside the 2-point
  tie. Test added.
* Runner-ups instead of padding. The engine always held each open market's
  #2 and #3 (the shortlist behind its representative) and threw them away,
  so with one slot open the plan was one real row and two 'padding' lines.
  Tracker keeps them (_market_alternates), yahoo_bridge.runner_up_rows
  appends them after the named rows with their own survival and gap to the
  first choice ('runner-up at TE: the engine's #2 choice there, 6 pts behind
  its first · 92% chance ...'), the driver and the scrutiny report label
  them, board-order padding remains only below that. Test added. Suite 730.

## 2026-09-05 (53) — near-ties between skill players break on projected touchdowns (user decision)

The user questioned Rice over Javonte Williams at pick 27 of room 10727517
(4.7 apart on the ranked number, 2.8 of it own-edge, both markets flat) and,
after the ECR and range comparisons, asked for projected touchdowns as the
tiebreak. Measured before building:

* 2024 and 2025 FantasyPros draft projections against actuals, same-position
  pairs projected within 6 points: the player with MORE projected touchdowns
  scored less 58% of the time at RB (273 pairs) and 57% at WR (623 pairs),
  in each season separately; QB 45% (98), TE 54% (54). Earlier ADP as the
  same tiebreak: 51-53%. Across positions, RB-vs-WR pairs within 6 points
  pick the RB 80% of the time and he scored more 49%. Touchdowns are the
  least repeatable part of a stat line, so the rule prefers the projection
  most likely to regress.
* The user weighed that against role ("javonte is gonna get the yards too,
  he's the workhorse") and reaffirmed. It ships as asked, with the evidence
  here.

What shipped. `proj_td` (rush + rec + pass touchdowns from the source stat
line; a count, no games or basis scaling) on the tiers csv and in
boardrow.ENGINE_FIELDS. Engine knobs `tie_break` (scarcity | touchdowns) and
`tie_window`, global defaults scarcity / 1.0 = today's rule byte for byte.
planner.pair_rank: for two RB/WR/TE candidates whose pairs are within
tie_window and whose touchdown counts differ, the higher count goes first
and the label reads "near tie (N pts) with X: more projected touchdowns (a
vs b)"; the rule decides that pair in either direction, so the reversed pair
cannot swap back on scarcity. A pair with a QB, K or DEF, or equal counts,
keeps the scarcity rule inside NEAR_TIE. leagues/keefamania.yaml: touchdowns,
window 5.0 (wide enough for the 4.7 that prompted it). Seven tests. Suite 737.

Measured after building, keefamania:

| instrument | result |
|---|---|
| season replay, 10 slots x 200 seasons, touchdowns vs today | -5.0 pts/season, se 0.4; 0 slots better, 4 worse, 6 tied (-0.3%) |
| churn, our first-seven-round picks in the six sheet-board rooms | 4 of 42 change |

All four changes go from a WR or TE to an RB: JSN -> McCaffrey at 7 (13.3 vs
9.6 TD), Rice -> Javonte at 27 (11.9 vs 10.5), Fannin -> Tuten at 54 (10.7
vs 5.7) and Fannin -> Judkins at 55 (8.7 vs 5.7). Two of the four take a
running back over the last TE at his tier, because tight ends score fewer
touchdowns than backs at the same value; that is a position tilt built into
the rule, not a read on those players. Restricting the comparison to RB vs
WR is one line (planner.TD_TIE_POSITIONS) if the user wants the TE timing
left alone.

DECISION: shipped for keefamania on the user's call, default off everywhere
else. The season replay is bench-neutral and cannot see a starter tiebreak
worth 4 picks in 42, so the -5 is noise-sized and not the verdict; the
instrument that can judge it is the 2026 actuals against the rooms drafted
under it.

### #53 addendum (2026-09-05 09:50 PT): reverted

The touchdown tiebreak ran for one room (10790713, seat 5). It fired once,
at pick 36: the engine's arithmetic had Etienne 0.8 ahead of Rice, the
scarcity rule would have kept Etienne (39% to survive against 59%), the
touchdown rule promoted Rice (10.5 against 8.4) and the page said so. In
hindsight Rice plus Skattebo at 45 was worth 52 of edge against 41 for the
Etienne path. One firing is an anecdote. The user reverted it the same
morning: leagues/keefamania.yaml is back on tie_break scarcity, window
1.0, today's rule byte for byte. The knob, the proj_td column and the seven
tests stay, measured and off, like the bench knobs.

## 2026-09-05 (54) — the DraftSheet headline is reproduced from the workbook's inputs under the league's rules

The user handed over the 09-04 copy of the FantasyPros workbook and said it
is the DEFAULT-settings copy: the loader has to apply Keefamania's rules and
land on the right number whatever the Scoring tab says. What the copy said:

* Scoring tab #TEAMS 12 (Keefamania is 10); roster and scoring identical to
  the league. Team count moves only VBD and PS on the page, never PTS.
* Every headline 7-9% higher than the 09-02 copy with the raw lines nearly
  unchanged (139 of 475 tab lines moved, almost all rounding; Gibbs +6
  carries, Sadiq and Mason Taylor at TE, Daniel Jones). The Aggregate
  formulas changed: LOW/AVG/HIGH scale by (17 - missed) instead of
  (16 - missed), and the headline is AVERAGE(AVERAGE(LOW,HIGH), AVG,
  ECRpts) (three-way) instead of AVERAGE(LOW, AVG, HIGH, ECRpts).
* The TE block is half-edited: row 3 says 17, rows 4-52 still say 16, and
  the cached page values follow the formulas, so on the page every tight
  end sits about 7% below where the other three positions sit. McBride
  reads 164.8 on the page and 175.7 on a consistent 17 basis.

What shipped (draftkit/external.py, projections.py, config.yaml, tests):

* `from_sheet(line="headline")` no longer copies DraftSheet PTS. It rebuilds
  it: tab low/base/high scored with the LEAGUE yaml plus the rookie bump,
  times (games - RISK missed games for the player's ECR slot) / 17; the
  ECR-slot points as the k-th largest AVG of the position's ranked block
  (k = the player's slot, window read off the LARGE range); the average in
  the workbook's form. `sheet_headline_spec` reads games, form and windows
  off the Aggregate formulas on every row of every block, takes the
  majority, and names blocks that disagree (`off_basis_positions`). The
  reproduction runs every position on the majority basis, so the stale TE
  block does not become a position tilt on the board; the CLI warns.
* The row carries its basis (`pts_basis`, new schema column; the basis
  table's fixed 16 for the headline source is gone) and
  `source_basis_expr` reads it first. The board scales 16/17 on the 09-04
  copy; the shift against the 09-02 board is (m/17)(1/17) of the line,
  under a point.
* `sheet_scoring` reads the Scoring tab into draftkit keys and the loader
  reports every difference from the league yaml (none on either copy);
  `sheet_updated` reads the 'Updated:' cell, which is now the as-of.
* Parity (tests/test_sheet_parity.py) runs over BOTH copies: tab lines
  exact on both; the reproduced headline against the page exact to the
  cent on QB/RB/WR of the 09-04 copy and on all four positions of the 09-02
  copy, one deep-tail row (Ty Simpson, QB40) 0.05 off on both from a
  VLOOKUP miss inside the workbook's own block; TE on the 09-04 copy
  flagged and confirmed stale (page/board ratio 0.85-0.96). Synthetic
  tests cover both formula forms, the reported-not-applied scoring, and a
  half-edited block.

Board rebuilt on the 09-04 copy; the diff against the 09-02 board and the
bridge restart are on the line under this entry.

DECISION: the workbook the league runs on is whatever the user downloads,
settings and all; draftkit owns the rules. If FantasyPros ships a shape the
detector does not recognise, the loader raises; it never falls back to the
page.

Board on the 09-04 copy against the 09-02 board (226 players both): mean
+1.4 points (the three-way average lifts the middle of the range; the
17-game basis cancels against the 16/17 scale within a point); 147 players
move more than 1 point, 19 more than 3, 4 more than 5 (Gibbs +7.6 on his
own line refresh); by position QB +2.3, RB +1.8, WR +1.5, TE +0.9. Value
rank moves of 5 or more inside the top 120: Garrett Wilson 55 to 46, Jaylen
Waddle 86 to 73, Bucky Irving 49 to 58, Jayden Daniels 42 to 47, ten others
by 5 to 8. AJ Dillon enters the ECR window, Adam Randall leaves it. Rice
169.9 to 170.2, Javonte 175.5 to 177.8, McBride 164.1 to 165.3 (on the
consistent basis; the page's stale TE block reads 164.8 against 175.7).
Bridge restarted on the new board and verified.

## 2026-09-05 (55) — bench ranks on the raw edge, ties break on the ceiling; starter near-ties break on the floor (user design)

Three rooms in a row (10727517, 10728751, 10790713) spent picks 105-125 on
running backs projected BELOW the waiver-wire back over receivers projected
above theirs. Mechanism, watched live at pick 105 of 10790713: once a
reserve is held, every further reserve at the position is worth 0-2 points
of insurance, the insurance formula floored a negative edge to zero so a
sub-wire back TIED a receiver worth 2, and inside that 2-point window the
late-round tiebreak preferred the wider published range. Rodriguez's range
was 22 wide on a 77-point projection; Sutton's 4 wide on 117. Every version
of Sutton outscored every version of Rodriguez and the engine still took
Rodriguez. The user specified the fix.

Shipped, no knob (the old behaviour was the defect):

* `bench.insurance_value` returns `value_raw` / `edge_raw` (edge before the
  floor x weeks) beside the floored `value` / `edge`. `_bench_candidates`
  picks each position's row and sorts across positions on the RAW value;
  the reason string still shows the floored number. A man below the wire is
  negative and cannot tie a man above it, and he is no longer the
  position's row at all: the wire's own best back (raw ~0) is.
* Bench near-ties (within BENCH_TIE 2.0 on the raw value, per position and
  across positions) go to the higher CEILING: `proj_hi`, else `proj_pts +
  proj_band / 2`, else the order is left alone. Width is gone
  (BENCH_BAND_MARGIN and the band tiebreak removed, DECISIONS #47 item 2
  and #52 item 1 superseded).
* Starter near-ties (planner.pair_rank): after the survival pass, adjacent
  rows within NEAR_TIE whose survivals are within FLOOR_SURV_TOL (5 points)
  go to the higher FLOOR when the floors differ by FLOOR_GAP (3 points) or
  more: `proj_lo`, else `proj_pts - proj_band / 2`, else left alone. The
  reason names the counterparty: "near tie (0.5 pts) with Rashee Rice:
  higher floor (161 vs 150)". A 2-point survival difference no longer
  decides a coin flip on its own.
* So that `proj_hi` / `proj_lo` ARE a ceiling and a floor: a single
  source's own published high and low lines (the sheet's high/low rows,
  scored in league settings, on the headline basis) now become
  `pts17_hi` / `pts17_lo` in combine(); with two or more sources the
  cross-source max/min stand as before. On the Keefamania board 190 skill
  rows carry hi >= pts >= lo; projections and VORP are unchanged.

Tests (tests/test_bench_rows.py, test_planner.py, test_external.py): the
raw value beside the floored one; Rodriguez against Sutton (Sutton heads the
bench list, Rodriguez is not the RB row, the wire back is); twins that tie
on the raw value break on proj_hi, then on the band fallback, and are left
alone without either, never on width; Javonte against Rice (Rice 0.5 ahead
and 2 points scarcer: the survival rule keeps him, the floor rule moves
Javonte up and says why), the rule stays out at a 20-point survival gap,
needs 3 points of floor, falls back to the band, and leaves a floorless pair
alone; the sheet's high/low become pts17_hi/lo. Three band-width tests
removed. Suite 752.

Measurements are on the lines under this entry (season replay against the
insurance arm of the 09-05 morning run; bench churn against the last four
rooms' actual picks).

Measured after building. Season replay, keefamania, 10 seats x 200 seasons,
insurance (new rules) against a VORP bench on the 09-04 board: +5.1 points
a season, paired se 0.6, 6 seats better, 3 worse, 1 tied. (The morning's
run had the old insurance rules at 1551.4 mean on the 09-02 board; the new
rules land at 1554.2 on the 09-04 board, whose VORP-bench arm is 1549.1, so
the rule and the board refresh are confounded there and only the paired
+5.1 is clean.) Bench churn against the four rooms' actual picks (24 bench
picks after pick 70, K/DEF excluded): 18 change. In room 10790713, the one
room drafted on today's board, exactly the three sub-wire backs change,
Rodriguez -> RJ Harvey (108 pts), Randall -> Rachaad White (106), Tracy ->
White, and the other three bench picks stand. In the three rooms drafted on
the 09-02 board the WR row moves Pierce -> Tate, the QB2 Mahomes -> Dart and
the first RB reserve Dowdle -> Henderson; those ride on the board refresh
(Henderson 134.9 -> 136.9 against Dowdle 128.2 -> 129.5) as much as on the
rule and are not separable here.


### #54 note (2026-09-05 11:30 PT): the league-settings copy

The user entered Keefamania's settings into the same 09-04 download
(`DraftSheets_2026_Keefamania_10tm_halfPPR_1flex_v2.xlsx`: Scoring tab 10
teams, 1/2/2/1/1 + 6 bench, scoring identical to the league yaml, Updated
2026-09-04). Checked against the default copy: 0 of 485 tab lines differ,
0 of 237 page PTS differ, the TE block is half-edited in this copy too (so
it is FantasyPros' template, not the download's settings), and
`from_sheet` yields the same headline, band, low/high lines and basis for
every one of 492 players to the cent. tiers.keefamania.csv rebuilt on it is
byte-identical. That is the direct proof of the ask: the loader applies the
league's rules to whatever copy it is handed. The v2 copy becomes the
configured sheet_path because its page (VALUE, PS, tiers) is the one that
matches the league when the user reads it; a test now holds the two copies
to one board.

## 2026-09-05 (56) — review of the morning's changes (e4065c8..HEAD): ten findings, all fixed

Eight review angles over #53-#55 plus the sheet swap, verified against the
code and the live board. What was wrong and what changed:

1. **The board sat at page x 16/17.** projections scaled every row by
   games/basis; the 09-04 headline is stated on 17, so Gibbs read 274.2 on
   the board and 291.4 on the sheet, against #45's "engine and page agree on
   every number" (true on the 09-02 copy only because its basis was 16). A
   row that STATES its own basis (pts_basis) is now taken at face value:
   proj_pts = pts17. Board now equals the page on QB/RB/WR to 0.1 (the TE
   block is on the consistent basis, #54). K/DEF synthetic lines keep the
   16 scale, so K/DEF slide a few value ranks; every skill number rises 17/16.
2. **The headline block only held Sleeper-matched rows.** The workbook's
   LARGE() block ranks every tab player; four unmatched deep names (Bam
   Knight, Connor Heyward, Riley Nowakowski, Hollywood Brown) became zeros
   and shifted the ECR-slot points of everyone below them (Guerendo 7.66 vs
   5.76). reproduce_headline now runs over every parsed tab row, matched or
   not, keyed by (pos, name). Test with an unmatched RB1.
3. **The ceiling tiebreak could promote a man below the wire** (raw -0.6
   inside 2.0 of raw +1.1). Below-wire never wins a tie against above-wire,
   per position and across positions. Test.
4. **A lineless single source read its point as a floor and a ceiling.**
   pts17_lo/hi coalesce to the point when a source publishes no lines, so
   on a Sleeper-only board the floor rule would have been "higher projection
   wins". One helper, boardrow.published_range: lines when they are a range
   (both ends on the point is not one), else the point +/- band/2, else
   None; used by the planner floor and the bench ceiling. Tests.
5. **The floor pass left a stale "scarcer player first" label** on a row it
   demoted. The touchdown, survival and floor rules are now one comparator
   in one bubble pass, one label per swap: TD (knob) inside tie_window;
   inside NEAR_TIE survivals more than 5 points apart -> scarcer first, else
   floors 3+ apart -> higher floor, else any survival difference -> scarcer.
   Same outcomes as the passes; no stale labels. Test with the order reversed.
6. **rank_window defaulted silently** to 50/100 when the LARGE() range was
   not recognised. It raises now, like the games basis and average form.
   And the page is the oracle: when the Scoring tab matches the league,
   more than two page rows at 20+ points off by >0.05 raises instead of
   shipping a board built on a misread formula.
7. **The two-pick and survival-discount arms still scored on the floored
   value.** Both now use the raw value (knobs stay off).
8. **tie_break was a free string**; a misspelling silently ran scarcity
   under the wrong log stamp. apply_engine_cfg rejects anything but
   scarcity / touchdowns. Test.
9. **Triple _line_touchdowns definition, triple pts_basis key** (a patch
   applied three times). One of each.
10. **Stale prose**: the TD rule described as live (config.yaml, tracker,
    planner), "basis 16" in external/projections, the module docstring
    saying the high/low lines are ignored, the band tiebreak said to ride
    late_round_dispersion. Rewritten. sheet_path / sheet_as_of moved from
    config.yaml to leagues/keefamania.yaml (a league fact; a league without
    one has no sheet source, reported, and a blank path can no longer open
    the repo root as a workbook).

Also from the review, recorded and not changed: the ECR-slot parser is now
one whitespace-tolerant function (_split_slot) used by the spec, RISK and
ECR readers; the bench churn artifact's 19th "change" was Mahomes vs
Mahomes II in a name compare (the entry's 18 stands); the parity module is
~40 s of the suite and could share workbook fixtures; combine(mean) carries
no basis (mean mode is off and unjudgeable before 2026 actuals, #30); the
majority-vote basis stands over a per-row basis because the page's stale TE
block would otherwise become a position tilt on the board. Suite 769.

Board after the fix (v2 workbook): every QB/RB/WR headline row equals the
page within 0.1 except the five availability-`out` players the board zeroes
(Tyson, Jacobs, Charbonnet, Pacheco, Conner); Gibbs 291.4, Rice 180.8,
Javonte 188.9, McBride 175.7 (consistent basis). K/DEF move at most 4 value
ranks (Texans 39 -> 40, Fannin 40 -> 39 the only top-40 change). Bridge
restarted on it and verified.

## 2026-09-05 (57) — the floor rule compares floors over each position's replacement

First live firing of the #55 floor rule, room 10795644 pick 31 (seat 10,
the turn, survivals to pick 50 both ~0): the pair had McBride 0.9 ahead of
Hall; raw floors 161 (TE) against 166 (RB) moved Hall up. McBride went at
33, the TE slot fell to Fannin at 70 (19 edge against McBride's 56), Hall
in the flex was worth 29 against a near-zero flex market at 70: about 8
edge points against the rule. The defect is the currency: the pair number
prices every player against his position's fallback, and the floor rule
compared raw points across positions, so a tight end's 161 (51 above the
TE he would otherwise start) lost to a back's 166 (16 above his back).

Shipped (user, 2026-09-05): planner._floor returns the published floor
MINUS fallback[pos] when the pair carries a fallback table (always, on the
live path); the label reads "higher floor over replacement (16 vs 10)".
Without a fallback (greedy path, tests) raw floors stand as before.
FLOOR_GAP 3 is now three points of floor edge. Test: an exact pair tie
where raw floors say Hall and the pair's currency says McBride, the
reverse case with the label, and the inside-the-gap case. Suite 770.
The bench ceiling rule compares raw ceilings across positions with the
same weakness in principle; bench rows are already priced against each
position's wire, so it is left as is and noted.

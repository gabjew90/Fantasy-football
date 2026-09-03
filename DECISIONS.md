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

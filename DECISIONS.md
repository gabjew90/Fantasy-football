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

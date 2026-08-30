# Draft Engine v2 — Final Improvement Plan

Merges docs/research.md (v2, 2026-08-29) with the post-draft fix list.
Where they disagreed, the disagreement is recorded, not smoothed over.

## Corrections to the research doc's repo reconciliation

1. **The games-missed durability haircut IS shipped** (config.yaml
   `expected_games`, `exp_games` in tiers.csv), not "unshipped" — the doc
   read the README only. It moved real draft values: Garrett Wilson 12.7 vs
   Davante Adams 14.0 expected games was part of why the board preferred
   Adams. Per Q6 (games-missed ≈ folklore, near-zero YoY), the doc's
   implication flips from "don't build it" to **remove it**. Honest
   corollary: the Adams-over-Wilson margin was partly folklore-driven; the
   pick stands on the 18-pt VORP gap, but thinner than defended.
2. Age adjustment: repo state matches (none built) — correct per Q5; the
   previously-planned age curve is DROPPED. The Adams-type risk is handled
   by Q8's narrower "regress prior top-5 finishers / recency overhang" tilt.
3. In-season cadence is now the Actions auto-manager (Mon/Tue/Fri/Sun +
   per-slate gate), not the old Tue/Thu/Sun schtasks. Affects nothing above.

## Fate of the prior fix list

- Survival recalibration → KEPT, sharpened: calibrate from the CLV retro
  (this room's observed reaches), not generic priors. Fat tails + run
  modeling remain implementation details.
- Two-pick joint planning → KEPT, generalized: the doc's #10 limits pairing
  to the turn; the Flowers seam happened at slot 2 (picks 26/47). Joint EV
  over (this pick, next pick) at every pick, gated on calibrated survival.
- Empirical baselines → KEPT, method upgraded (live FA snapshots + explicit
  streamability discount on QB/TE/WR VORP).
- Age curve → DROPPED (Q5). Replaced by small standing tilts (Q8).
- Risk-quantile waiting → folded into the round-dependent objective.
- NEW (from doc): remove durability haircut; demote TPRR/YPRR to
  informational (route data ended 2023 — they're proxies); opportunity-first
  projection rebuild; blend alpha by player type; FAAB overreaction damper;
  IR-aware stash loosening; live FA replacement level.

## Phase 0 — now, in-season (this league, this week)

0.1 **CLV retro script**: pick slot − closing ADP for all 180 picks; per-
    rival reach profiles. One script, run once; output feeds 1.1. Also score
    the draft log's survival predictions vs outcomes (we logged both).
0.2 **Live FA replacement level in waivers**: each Tuesday, replacement per
    position = best available FA's ROS projection from the pool already
    fetched; claim values measured against it. Self-calibrating RB scarcity.
0.3 **Injury-overreaction FAAB damper**: cap bids where the case is one
    spike week with flat snap/route/target share — the usage clauses already
    compute the evidence.
0.4 **IR-aware stash loosening**: with 1 IR slot, one injury stash is free;
    "max one zero-role stash" applies to the bench proper. Contingency
    claims behind fragile starters get the aggressive band.

## Phase 1 — before the new league's draft

1.1 **Survival recalibration** from 0.1's residuals: fat-tailed noise,
    positional-run escalation, empirical calibration map (raw 95% → ~78%
    until data says otherwise). New room starts on this room's priors,
    updates live during the draft.
1.2 **Generalized two-pick planner** on top of 1.1.
1.3 **Remove the durability haircut** (exp_games becomes an informational
    column; no projection effect). If durability ever returns it is
    position × workload × injury-type with heavy shrinkage — not this year.
1.4 **Format-derived replacement baselines**: computed from the new
    league's (teams × slots × flex × scoring), sanity-checked against
    published historical waiver depth; empirical own-league version waits
    for January data (2.2).
1.5 **Round-dependent objective**: median through ~round 7; from round 8
    maximize 85th-percentile behind a role-quality gate (contingent volume,
    year-2 + draft capital, air-yards share with TD regression). Never raw
    variance.
1.6 **Standing ADP tilts, small and few** (Q8): fade mid-round TE and
    early/mid non-rushing QB, regress prior top-5 finishers, damp August
    injury moves. Each capped ~10%.
1.7 **Blend alpha by player type**: ~65/35 stats for stable-role veterans,
    ~40/60 market for rookies/committees/new-team. Config-level.
1.8 Onboard the new league: verify-driven settings, fresh config, mock
    draft as the validation run for 1.1–1.7 (CLV scored).

## Phase 2 — offseason, gated on validation

2.1 **Opportunity-first projection rebuild** (Q2, strongest finding):
    target share/WOPR/weighted opportunity/air-yards/high-value touches →
    points, efficiency regressed hard to positional mean. Reversal gate:
    revert unless held-out MAE and rank correlation beat the points model.
2.2 **Empirical own-league baselines** from the auto-manager's accumulated
    weekly state snapshots (free backtest substrate by January).
2.3 **Slot opening books** as Monte Carlo priors (Q7: modest — priors, not
    rules), including pair-aware turn handling.

## Standing validation loop (every change, no exceptions)

(a) CLV on the next real or mock draft; (b) historical draft simulation,
slot-adjusted; (c) input MAE/rank-correlation vs a market baseline.
Single-season league results and self-graded boards validate nothing.
The three-lens scoreboard remains a public honesty device, not evidence.

---
## Status (2026-08-29, end of implementation session)
DONE: 0.1 CLV retro · 0.2 live FA replacement · 0.3 overreaction damper ·
0.4 IR-aware stash rule · 1.3 haircut removal (board diff APPROVED, merged)
· amendment A multi-league structure (onboard command ready; new-league
yaml awaits the league id) · 1.1 survival recalibration (fat tails, runs,
calibration map) · 1.2 two-pick planner (amendment B fallback) · 1.5
round objective + role gate · 1.6 standing tilts (off for Omnibeta) ·
1.7 alpha by type. 132 tests.
AWAITING USER: new league's Sleeper id (+ draft slot when known) -> item
12 onboard + mock-draft CLV acceptance run.
GATED (do not start): Phase 2 (2.1 opportunity rebuild w/ two-season
backtest gate, 2.2 January baselines, 2.3 slot books).
Flagged deviations: August-injury tilt deferred (ADP moves not yet
attributable to injury); air-yards/TD-rate upside gates deferred to 2.1
(columns absent in free weekly data); items 7-11 built before item 12's
league id arrived (structure-only, no Omnibeta numbers copied anywhere).

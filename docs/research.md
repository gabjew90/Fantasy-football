# Draft Engine Research — Updated Against Repo State (v2)

Date: 2026-08-29. Supersedes the v1 research report. Reconciled against
github.com/gabjew90/Fantasy-football (README of 2026-08-19+, draft completed
2026-08-23). Suggested location: docs/research.md.

## Context changes since v1

- The draft is complete. Draft-layer recommendations move to offseason;
  in-season recommendations are live now.
- The league HAS 1 IR slot (Out/Doubtful eligible). v1 assumed none. This
  strengthens contingent-role and injury-stash logic (Q4) by exactly one
  free roster spot.
- nflverse route participation data ended after 2023; repo TPRR/YPRR are
  proxies. Opportunity metrics from play-by-play (target share, WOPR,
  weighted opportunity, air-yards share) are unaffected.
- The board self-grade ("finished #1 of 12 on the board") is circular per
  Q9 and carries no evidential weight.

## The nine findings (verdicts unchanged from v1)

1. **Replacement level** is position-specific and RB-scarce in-season
   (validated). Startable RBs vanish from waivers by ~week 3; WR/QB/TE/K/DEF
   are streamable. Empirical baselines beat hand-set ones and slightly
   strengthen early-RB value.
2. **Opportunity >> points >> efficiency** (validated, strongest finding).
   Target share ~0.70–0.76 YoY, WOPR/air-yards share >0.70. Efficiency (YPC
   ~0.30, TD rates near zero) is noise. RB fantasy points are the least
   sticky of any position.
3. **ADP deviations** (contested/qualitative): position runs, recency bias,
   name-brand, homerism. ADP tightest rounds 4–9, noisiest round 1 and 10+.
   Sleeper's own ADP is not sharp.
4. **Ceiling over median after ~round 8** (validated with ETR caveat):
   reward ceiling that comes from a path to volume (contingent roles, year-2
   profiles, draft capital, air-yards-heavy low-TD), not cosmetic variance.
5. **Age is mostly priced in** (contested): fade premium-priced 27+ RBs off
   career years, boost late-round 30+ WRs and cratered aging QB/TE. Cap any
   adjustment at ~10%; near-zero average if ADP source is sharp.
6. **Games-missed history is weakly predictive** (largely folklore):
   near-zero YoY correlation. Position, workload, and injury type carry
   what little signal exists.
7. **Slot strategy is real but modest** (contested): the turn enables
   pair-picking before tier breaks; opening books are priors, not rules.
8. **Recurring ADP errors** (mixed): mid-round TE trap, early/mid non-rushing
   QB overpricing, recency overhang on prior top-5 finishers, August injury
   overreactions, structural WR value in PPR. Zero RB substantially
   arbitraged; exploit situationally only.
9. **Validation** (validated methodology): CLV (pick slot vs closing ADP),
   best-ball advance rates over 100+ drafts, historical draft simulation
   with slot-adjusted scoring. Never self-graded boards or single seasons.

## Repo reconciliation

Already built (no action): run-aware cliff-vs-wait timing conditioned on
rival rosters, roster-legality constraints, hard-coded late K/DEF,
configurable blend alpha, Tue/Thu/Sun in-season cadence, no age adjustment
(correct per Q5).

Unshipped and should stay unshipped: the games-missed durability haircut
(absent from README projection description — confirm in config.yaml). Per
Q6, do not build the games-missed version. If durability enters at all, it
is position x workload x injury-type with heavy shrinkage.

## Revised recommendations, priority order

### Now (in-season, active league)

1. **CLV retro on the completed draft.** Compute pick slot minus closing
   ADP for all 180 picks, yours and all 11 rivals. First real out-of-sample
   measurement of the engine, and it doubles as league-specific reach
   calibration for the survival model (replaces v1's generic round-variance
   priors with your room's observed behavior). One script, run once.
2. **Live FA-pool replacement level in waivers.py.** Compute replacement
   per position each Tuesday as the best available free agent's
   rest-of-season projection, from the actual pool the manager already
   fetches. Self-calibrating, captures RB scarcity automatically. The v1
   "estimate week-8 replacement from history" framing applies only to next
   year's draft baselines.
3. **Injury-overreaction damper in FAAB bands.** The in-season analog of
   the August ADP overreaction: cap bids on adds whose case is one spike
   week with no underlying usage change (snap/route/target share flat).
   The waiver brief's usage clauses already compute the discriminating
   evidence.
4. **Loosen the stash guardrail by one.** With 1 IR, one injury stash is
   free. Contingency claims behind fragile starters get the aggressive
   FAAB band; "max one zero-role stash" applies to the bench proper, not
   IR occupants.

### Offseason (draft engine, gated on validation)

5. **Rebuild the stats projection around opportunity metrics** — target
   share, WOPR, weighted opportunity, air-yards share, high-value touches —
   converting opportunity to points with efficiency regressed hard to
   positional mean. Route-derived metrics (TPRR/YPRR proxies) demote to
   informational columns. Reversal gate: revert if held-out-season MAE and
   rank correlation don't beat the current points-based model.
6. **Player-type-dependent blend alpha.** ~65/35 stats-heavy for
   stable-role WR/TE and workhorse RBs; ~40/60 market-heavy for rookies,
   committee backs, new-team players. Config: alpha by proj_source and
   role-stability flag.
7. **Round-dependent objective.** Median/floor through ~round 7; from
   round 8, maximize an 85th-percentile projection behind a role-quality
   gate (contingent volume, year-2 + draft capital, prior YPRR for RBs,
   air-yards share with TD regression for WRs). Never reward raw variance.
8. **Empirical draft-day replacement baselines.** Derive from observed
   mid-season waiver availability in this league (the manager's weekly
   state snapshots accumulate exactly this data through the season — free
   backtest input by January). Expect: RB baseline points lower/steeper,
   WR deeper (~WR60–66), explicit streamability discount on QB/TE VORP.
9. **Standing ADP tilts, small and few:** fade mid-round TE and early/mid
   non-rushing QB, regress prior top-5 finishers, damp August injury
   moves. Situational Zero RB via the value model only.
10. **Slot handling: pair-aware at the turn**, evaluating both turn picks
    jointly against tier breaks; opening sequences seed the Monte Carlo as
    priors.

### Standing validation loop (before trusting any change)

Every engine change ships behind: (a) CLV on the next real or mock draft,
(b) historical simulation replaying past seasons slot-adjusted, (c) input
MAE/rank-correlation vs a market baseline. Single-season league results
never validate anything; the manager's weekly snapshots are the data
substrate for (b) going forward.

## Caveats carried from v1

Evidence quality is uneven: Q2, Q1, Q9 well-supported; Q5, Q7, Q3, Q6
contested or folklore, several on small samples (30+ WR study n=27) or
paywalled models. Published numbers come mostly from best-ball; this
league's waiver wire restores in-season antifragility best-ball lacks.
Survivorship bias understates true age decline and injury risk. All
industry forecasts treated as forecasts, not results.

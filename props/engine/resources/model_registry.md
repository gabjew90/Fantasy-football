# Model Registry

This file is the only source of model state. At runtime, look the model up here by ID before pricing anything. If the ID is absent or its status is below `VALIDATED_DISTRIBUTION`, the prop is `MODEL_UNVALIDATED`. Do not upgrade a status inside a chat; a status changes only by editing this file with the evidence recorded below, and the edit is presented to the user as a file for them to save into the Project.

## Status levels
- `REJECTED`: evaluated and failed; not to be reused as a model or as a prior-strength rule.
- `PROTOTYPE`: exists as code; may have partial diagnostics; produces no fair odds.
- `VALIDATED_DISTRIBUTION`: passed distribution validation on the scoring population with the leakage guard, on an untouched test period, beating the named baselines with a reported score-difference interval. May show fair odds; must PASS.
- `VALIDATED_BETTING`: additionally passed betting validation against archived lines with reported ROI, calibration, and closing-line results. May produce `EDGE_SUFFICIENT`.
- `RETIRED`: superseded; kept for lineage.

## Promotion requirements
To `VALIDATED_DISTRIBUTION`: frozen spec (code hash or version), training and test windows, scoring population definition (archived-line or proxy, stated), N games and N player-games, CRPS (or log score) and Brier per market with 95% block-bootstrap intervals for the difference against each baseline, PIT/coverage summary, roster carryover rate on the test period, and a statement that the pre-game guard was applied.

To `VALIDATED_BETTING`: everything above plus archive coverage (rows, bookmakers, snapshot types, date range), decision-time definition, selection rule as frozen before replay, N candidate bets and N placed under the rule, hit rate, ROI with interval, closing-line value where closing rows exist, and comparison to flat and no-vig-consensus benchmarks.

## Entries

### box_score_mean_shift_v0
- Markets: player_anytime_td (probe)
- Status: `REJECTED`
- Spec: direct mean shift of historical final box scores; historical scored-at-least-once frequency as TD Yes probability
- Test: 2026 Week 2 probe, N = 8 player-games
- Result: Brier 0.261 vs 0.252 benchmark
- Notes: failed prototype. Not a reusable model and not a prior-strength rule. N is far too small to have passed even with a better score.

### receiving_hier_v1
- Markets: player_receptions, player_reception_yds
- Status: `PROTOTYPE`
- Spec: team targets → target share → catches | targets → yards | catches; hierarchical role shares with prior-season priors
- Training/test: 2025 Weeks 9 to 18 evaluated (151 games, 3,158 player-games); fold split as recorded in the prototype notebook
- Result: beat weak baselines on CRPS. Exact CRPS values and baseline definitions not recorded here; fill from the prototype output before any promotion review.
- Known defects blocking promotion:
  - scoring population was not restricted to prop-eligible players (`modeling_framework.md` scoring population rule)
  - pre-game guard not confirmed for team target volume or eligible roster
  - Week 1 roster carryover 48.5%, so the prior-season role pooling is weak at the season start; needs a regime for new-team players
  - no archived-line test; betting validation unavailable
- Next steps to `VALIDATED_DISTRIBUTION`: rerun on the eligible population under the guard, with hierarchical and rolling-utilization baselines and game-level bootstrap intervals; report roster carryover per test week.

### Round 10 (2026-09-24): the yardage harness, four seasons
`backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025`
(report: `reports/yardage_harness.md`, plan: `docs/plans/2026-09-24-yardage-harness.md`).
Each season walk-forward from priors built from the season before, live scorer
settings, the scorer's own joint samplers (rushing moved into
`model.simulate_team_rush`; score_game output byte-identical). Weeks 2-18.
Receptions, receiving yards and rushing yards all beat baseline A on both
test seasons with intervals excluding zero and are unbiased on average, and
all three are too NARROW: 26.1%, 23.0% and 32.1% of outcomes fall outside
the model's p10-p90 (20% expected), and an 85% Over wins about 75-81%. The
`calibration_2025.csv` that looked calibrated predates the joint sampler; the
round-9 code reproduces the overconfidence under the old single-season
protocol too, so this is the model, not the harness. Width is now part of
the bar; widening is the next change.

### Round 11 (2026-09-24): the width settings, props-v1.20
The round-10 finding (right on average, too narrow) traced to four things the
joint sampler held fixed within a game. Each is now a mean-preserving setting
in model.py (`WIDTH_OFF` = the old sampler draw for draw): Dirichlet variation
of a player's share of targets / carries, Beta variation of the catch rate,
and a lognormal per-game multiplier on yards per catch / per carry. Tuned on
2022-23 only (`backtest.py --tune-width`, reports/width_tuning.md): CRPS first,
and among settings not measurably worse than the best, the width closest to
20%. Chosen: target-share concentration 40; carry-share concentration 20 with a
0.3 log-sd on yards per carry; catch rate and yards per catch fixed.

2024-25 (the parameter values never saw them; the choice of which knobs to
try was made after the first harness run, which showed all four seasons too
narrow), reports/yardage_harness.md: all three pass the four checks. Outside
p10-p90: receptions 25.2% -> 19.0%, receiving yards 23.2% -> 19.2%, rushing
yards 32.3% -> 19.6%; worst 60-90% bucket 2.8 / 3.0 / 2.9 points (receiving
yards exactly at the 3-point limit). Paired CRPS against the old sampler, all
four seasons, in the report: receptions +0.0034 and rushing +0.186 (better),
receiving yards -0.024 (0.18% worse, interval excludes zero) -- the cost of
honest ranges on that market. On a live game (KC@MIA
2026 wk 3) 75-95% probabilities fall ~5 points (rushing ~8), near-the-line
ones ~2.5; means unchanged.

### rush_yds_v0
- Markets: player_rush_yds
- Status: `PROTOTYPE`
- Spec: team carries -> rush share -> per-carry yards. Team carries and rush share use the
  same hierarchical structure as `receiving_hier_v1`. Per-carry yards are resampled from the
  prior season's empirical league carry-yardage distribution (quantile grid in
  `priors_{season}_params.json`), so heavy tails and negative runs are preserved rather than
  fitted to a symmetric family. Carry counts use their own NB dispersion fit.
- Test: NONE. No backtest has been run for this market.
- Known limits:
  - QB rushing yards are excluded at scoring time: kneel-downs are dropped from the carry
    data but sportsbooks settle QB rush props including kneels, which flips short lines.
  - No opponent run-defense adjustment.
- Next step to `VALIDATED_DISTRIBUTION`: run the Gate A harness on this market.

### anytime_td_v1
- Markets: player_anytime_td
- Status: `PROTOTYPE`. Replaces anytime_td_v0 (kept only as the labelled fallback when
  v1 cannot run: no market implied total, or its inputs fail).
- Code: `scripts/td_v1.py`, the single implementation. `score_game.py` prices from it and
  `scripts/td_alloc_backtest.py` scores it, so the number validated is the number priced.
- Spec:
  - Team: offensive touchdowns ~ Binomial(10), mean = implied points x league offensive
    TDs per point x (implied / mean implied)^0.25. Offensive only; defence and special
    teams never settle an offensive player's anytime prop.
  - Who scores: each active player's share of six opportunity channels (QB rush, rush
    from the 5 in, rush beyond, END-ZONE targets -- red-zone targets whose air yards reach the
    end zone, other red-zone targets, targets beyond the 20; the end-zone split is
    props-v1.12), blended toward
    last season's role (kappa 5 games); a role from another team counts 0.25; a player
    with no history gets 0.4 x his depth-chart slot's league share; an absent player's
    share is reallocated across the active roster.
  - Channel mix: the team's (shrunk to league by 100 TDs), EXCEPT the QB-rush weight, which
    is the starting quarterback's own QB-rush touchdowns over his teams' offensive
    touchdowns in his starts over the last 3 seasons, shrunk to the league fraction by 40
    team touchdowns (props-v1.5). The starter is the active QB highest on the pre-game
    depth chart.
  - The starter's share WITHIN qb_rush is fixed at 0.92 (props-v1.9), not taken from his
    history, which ran 0.70 against 0.88 of his team's QB carries: games-played
    denominators give a fill-in backup a starter-sized share and the cap squeezes both.
    Other players' qb_rush shares are scaled to fit under the cap.
  - P(score) = 1 - sum_k P(N = k) (1 - q)^k, q = his per-touchdown share.
- Test (outcome backtest, no lines): tuned 2022-23, scored 2024-25, 15,022 player-games on
  the game-day active list. `reports/td_v1.md`, `reports/td_layer1_frozen.md`,
  `reports/td_layer2.md`.
  - End to end vs the anytime_td_v0 structure: log loss **-0.0034 (-0.0056, -0.0012)**,
    game-clustered. The previous configuration (no scaled slot prior) was NOT established
    (-0.0021, CI to +0.0000); the scaled slot prior is what took it across.
  - Split: layer 1 alone -0.0004 (established, small); allocation alone -0.0030.
  - THE CASE IS CALIBRATION. v0 under-predicts the scoring rate (0.135 vs 0.148 actual) and
    runs ~3 points low in the 0.2-0.3 band where most priced lines sit; v1 predicts 0.145.
    The cause is allocation mass: active players score 0.997 of their team's offensive
    touchdowns, v0 gives them 0.932 (absent and departed players' share never reassigned),
    v1 gives them 0.990. A systematic low bias of that size suppresses real Yes edges
    against a 25% relative edge floor -- the DET@BUF pattern, model below the book on all
    nine priced players.
  - Tested and dropped: expected-touchdown weighting (+0.0026, worse); a Beta-distributed
    share (no effect, -0.0000); a team-specific TDs-per-point ratio.
  - OUT OF SAMPLE, scored as-is on seasons no setting was chosen or inspected on: v1 as
    first shipped on 2018-19, -0.0058 (-0.0081, -0.0037) end to end vs v0 structure,
    carried entirely by allocation; v1.1 on 2016-17, -0.0055 (-0.0076, -0.0035), and
    -0.0006 (-0.0010, -0.0002) vs v1 as first shipped. `reports/td_v1_2018_19.md`,
    `reports/td_v1_2016_17.md`.
  - v1.1 (props-v1.5), the starter's QB-rush rate, tuned 2022-23 (`reports/td_v1_1_tuning.md`):
    vs v1 as first shipped, -0.0009 (-0.0016, -0.0003) end to end on 2024-25; on starting
    QBs -0.0141 (-0.0214, -0.0064). QBs new to their team as starter: -0.0171, CI to
    +0.0133, NOT established (n 67). Starting QBs are still under-predicted on average
    (0.123 vs 0.148 actual); the gain is ranking, not level. Raising the share cap above
    0.99 was tested (to 0.999) and was worse on tune at every setting: the low bin is not
    the cap.
  - v1.2 (props-v1.9), the starter's share within qb_rush, tuned 2022-23 JOINTLY with
    qb_beta (3 x 5 grid; 0.92 with qb_beta 40 best, so qb_beta is unchanged)
    (`reports/td_qb_share.md`, `reports/td_qb_share_2016_19.md`). THE CASE IS CALIBRATION:
    starting QBs predicted 0.123 vs 0.148 actual on 2024-25 become 0.158; 0.092 vs 0.117 on
    2016-19 become 0.112. Log loss: established on tune (-0.0019 end to end); on 2024-25
    -0.0004 and on 2016-19 -0.0004, both NOT established. Top bins unchanged in both eras
    (the gate); the lowest bin slips ~0.003 (backup QBs get less). Shipped vs v1 as first
    shipped: -0.0013 (-0.0029, +0.0004), not established; vs the v0 structure -0.0047
    (-0.0072, -0.0021).
  - v1.3 (props-v1.12), the END-ZONE SPLIT (`reports/td_pass_ez.md`): red-zone targets and TDs
    separated by whether the air yards reach the end zone. End-zone targets convert ~40% vs ~13%
    for other red-zone targets; primary receivers hold more of the former (0.29 vs 0.22 share),
    backs mostly the latter (checkdowns). Information, no fitted parameter. Paired vs v1.2 on
    identical players: log loss flat in all three eras (2022-23 -0.0003, 2024-25 +0.0002,
    2018-19 -0.0000, none established); position levels move toward actual in every era (RB
    0.215 -> 0.204 vs 0.186, WR 0.140 -> 0.146 vs 0.154 on 2022-23; same direction 2024-25 and
    2018-19); the 0.45-0.6 bin gap narrows in 2024-25 (0.021 -> 0.011) and 2018-19 (0.053 ->
    0.042), widens in 2022-23 (0.030 -> 0.039). The top-q player's passing-channel ratio moves
    from 0.43-0.83 to 0.81-0.86. Under six channels the shipped model vs the v0 structure is
    -0.0044 (-0.0069, -0.0019) end to end on 2024-25 (`reports/td_v1.md`).
  - A factor on the top-q player's passing shares (rank multiplier) was tuned on top of the
    split and NOT shipped (`reports/td_top_pass.md`): it takes his realised/expected to ~1.0 in
    both eras but the 0.45-0.6 bin flips to under-prediction on 2024-25 (0.505 vs 0.538), so it
    fails the top-bin gate.
  - v1.4 (props-v1.13), the SLOT PULL (`reports/td_slot_pull.md`, `reports/td_slot_pull_2018_19.md`):
    each active player's shares are shrunk 20% toward his pre-game depth-chart slot's league share
    (empirical-Bayes; players ranked by an estimated share carry its noise). Tuned on 2022-23
    JOINTLY with kappa (6 x 4 grid; 0.2 with kappa 5 best, kappa unchanged). Scored as-is:
    2024-25 -0.0060 (-0.0084, -0.0039) and 2018-19 -0.0038 (-0.0056, -0.0021) end to end vs
    v1.3, both established -- the largest single gain in the model's history. Shipped vs the
    v0 structure: -0.0105 (-0.0136, -0.0076) on 2024-25, mean predicted 0.147 vs 0.148
    (`reports/td_v1.md`). The lowest bin is fixed (0.020 vs 0.031 -> 0.030 vs 0.026). The top
    bin: 2018-19 gap +0.042 -> -0.013; 2024-25 +0.011 -> -0.025 (under-predicted, and the
    0.3-0.45 bin 0.362 vs 0.380) -- each about one standard error of a ~500-row bin.
  - Role-conditional shares (a player's share only from games in his current depth-chart
    role) tested and dropped: best variant -0.0003 on test, not established, and starting
    QBs barely moved -- weekly depth charts do not mark fill-in starts (`reports/td_role_tuning.md`).
  - The Beta share with the top bins in view (`reports/td_v1.md`): it squeezes every bin
    in proportion, so the 0.45-0.6 bin comes down (c=20: 0.499 vs 0.492 actual) only by
    pulling the 0.2-0.45 bins below their actual rates; log loss on rows priced above 0.45
    is unchanged (0.6846 fixed, 0.6846 c=20). Not carried into layer 3. The top-bin excess
    is real (2018-19 end to end: 0.507 vs 0.454 in 0.45-0.6) and has another cause.
- NOT tested against posted sportsbook lines. So: no fair odds, no "take YES at +X"
  thresholds, never eligible (eligibility.py). The benchmark for edge is log loss vs the
  no-vig market on logged lines, plus CLV on TD prices, once the record holds them.
- Known limits:
  - Most anytime-TD markets are ONE-WAY: no "won't score" side is quoted (Sleeper is the
    exception), so no-vig removal is unavailable and the comparison uses the book's raw
    implied probability, which is biased against the bet by roughly the hold. Carried over
    from anytime_td_v0 unchanged; disclose it wherever a TD gap is reported (the player
    card does, per book).
  - The lowest probability bin is still low (0.022 predicted vs 0.032 actual) -- backups
    with history and small shares, not the no-history players.
  - A player in a NEW role. For a starting quarterback the error was mostly the channel
    mix, not his share: within qb_rush a starter's share is near 1, and Miami's team mix
    after a pocket passer gave the QB-rush channel 0.063 of its touchdowns. On its first
    live board (MIA@SF 2026 week 2) v1 priced Malik Willis at 4.6% against the book's 26%;
    keyed to his own starts (4 QB-rush TDs of 10 team TDs, 2024-26) he is 19.8% on current
    inputs (9.9% on that board's Sept 18 inputs). What remains is role news the market
    has and usage data does not -- the market-as-prior layer's job.
  - Scorers are independent across teams, so it does not price correlated multi-scorer
    markets. That is layer 3.
- Live check at release: on MIA@SF 2026 week 2, every non-touchdown output of the scorer
  was byte-identical before and after the switch; summed per-touchdown share of each
  team's actives 0.990, as in the backtest.

### td_market_v0 (layer 4: the market as a prior)
- Markets: player_anytime_td (a second price beside anytime_td_v1, logged on every row).
- Status: `PROTOTYPE`, PROVISIONAL weight. Code `scripts/td_market.py`.
- Spec: logit p_blend = w logit p_model + (1 - w) logit p_market, w = 0.5 (provisional). p_market is
  de-vigged: exact for a two-sided market (Sleeper, Yes / (Yes + No)); for a one-way market a
  provisional 7% relative hold is removed from the Yes price.
- Why: the largest single-leg errors are role news the market has and usage data does not; with one
  player per team, a parlay is a bundle of single-leg opinions, so the single-leg price is where the
  remaining value is.
- Test: none yet; by design. Every priced TD row logs p_model, p_market, p_blend and blend_w through
  the record and the settled file, and the Tuesday scorecard's shadow fit (`props/blend.py`, per-book
  intercepts, game-clustered intervals, leave-one-week-out) estimates the real weight and hold once
  300 v1 calls have settled in one engine version.
- The cross-game parlay builder (`scripts/td_builder.py`, slate summary) uses p_blend: legs must
  clear the TD edge floor (25% relative, positive EV) on their own, one per game.

### td_joint_v0 (layer 3: joint touchdown probabilities)
- Markets: none priced. Correlated anytime-TD pairs and parlays stay GATED.
- Status: `PROTOTYPE` (research). Code `scripts/td_joint.py`, backtest `scripts/td_joint_backtest.py`,
  `reports/td_layer3.md`.
- Spec: exact, not simulated. Given the joint pmf of the two teams' offensive-TD counts and
  each player's per-TD share, P(A and B score) and any small parlay follow in closed form
  (inclusion-exclusion). Each team's channel mix is conditioned on the opponent's count
  (multipliers tuned on 2022-23, each bucket shrunk toward 1 by 200 TDs); the two counts are joined by a one-factor Gaussian copula,
  loading r = 0.5 tuned on the likelihood of actual score pairs, which leaves each team's
  own distribution exactly as layer 1 has it.
- Test, pairs of players priced 10%+ (tuned 2022-23, scored 2024-25; about 25,000 pairs of
  each kind):
  - teammates: P(both) 0.0594 independent -> 0.0553 joint vs 0.0543 actual; log loss -0.00032
    (-0.00067, +0.00003), NOT established (tune -0.00056, established).
  - opponents: the mix shift's DEPENDENCE alone (against the product of its own shifted
    marginals, since the shift also improves single legs) -0.00012 (-0.00020, -0.00004),
    established; against the v1 product -0.00018. With correlated counts -0.00019
    (-0.00052, +0.00016), not established, level 0.0642 vs 0.0626 actual.
  - the two teams' TD counts correlate +0.15 (+0.06, +0.23) beyond their implied totals on
    2024-25 (+0.21 on 2022-23); the copula improves the count-pair likelihood in both eras.
- SHADOW (props-v1.12): joint + mix shift (independent counts) is computed for every pair of
  anytime-TD legs priced 10%+ on every board and logged to `record/joint/` (`joint_td_*.csv`);
  nothing renders. The copula is NOT in it: its r is provisional, set by matching the pooled
  residual count correlation (+0.175 -> r = 0.43), and on pairs it is not established on
  2024-25 and worse on 2018-19 (+0.00029).
- Rerun after the end-zone split (`reports/td_layer3.md`, 2024-25 and 2018-19): three-teammate
  combinations beat the leg product in both eras (-0.00060, -0.00085, both established);
  teammate pairs established on 2018-19 (-0.00065), not on 2024-25 (-0.00033); the
  cross-team mix shift's dependence is no longer established (-0.00002) once the channels
  carry the end-zone split. Gate (b) FAILS in both eras: actual/predicted runs 0.8-0.95 in
  most large buckets, the level inherited from the legs.
- props-v1.13: the shadow model is PLAIN JOINT (teammates share their team's count), chosen on
  tune over joint + mix shift and the two copula variants by the worst large lift bucket. Rerun
  with the slot pull (`reports/td_layer3.md`): 2018-19 passes (b) for pairs and mixed three-leg
  combinations, fails three teammates; 2024-25 passes teammate pairs, fails opponents (1.076),
  mixed three legs (1.107) and three teammates. EVERY failing bucket's game-clustered 95%
  interval includes 1: pair intervals span about +-8%, three-leg intervals +-13-25%. With ~540
  games per era a 5% point tolerance is below the data's resolution (DECISIONS #88).
- props-v1.14 (DECISIONS #89): THE GATE IS A SCRIPT OUTPUT. `td_joint_backtest.py` writes
  `td_parlay_gate.json` (bundled in resources/, copied to reports/), and the scorer renders only
  what it opened. Current gate (a')/(b') and status (`reports/td_parlay_gate.json`):
  (a') per era, the 0.45-0.6 single-leg bin's 95% interval of actual minus predicted contains 0:
      PASS in 2024-25 (+0.024, -0.019 to +0.065) and 2018-19 (+0.013);
  (b') per class, pooled over 2024-25 and 2018-19 (1,056 games), OPEN if |ratio - 1| <= 5% and
      the 95% interval half-width < 10%, UNRESOLVED if the ratio is within 5% but wider, FAIL
      otherwise; classes open individually:
        cross-team pair   1.007 (0.955, 1.060)  OPEN        (joint + mix shift + copula)
        teammate pair     1.014 (0.959, 1.074)  OPEN        (joint + mix shift + copula)
        mixed 3-leg       0.991 (0.902, 1.085)  OPEN        (joint + mix shift + copula)
        three teammates   0.969 (0.861, 1.084)  UNRESOLVED  (joint)
  Each class's model is the candidate with the lowest pooled TUNE log loss for that class; the
  differences are in the fourth decimal, so all four candidates are logged in shadow and the
  graded record will settle it. A Dirichlet over each team's split of its TDs (c = 100, tuned on
  the three-teammate class of 2022-23; single-leg log loss 0.34629 -> 0.34626, no harm) moved
  three teammates from 0.926 (FAIL) to 0.969 and teammate pairs from 0.991 to 1.014.
  The report renders a "Touchdown pairs" section for the open PAIR classes only (mixed 3-leg is
  open but not rendered: the combinations explode, and pairs carry the volume). Both legs are
  PROTOTYPE, so no fair odds. Gate (d), single-leg CLV, is set aside by the user for now.
- THE PARLAY GATE as first fixed (DECISIONS #87), superseded by (a')/(b') above:
  (a) a star pass-share fix passes its top-bin gate -- the 0.45-0.6 bin within its current
      gap or better in both eras; OPEN (end-zone split shipped, rank multiplier failed);
  (b) on the pair and three-leg test, actual / predicted within 5% in every lift bucket with
      1,000+ combinations, in both eras; FAILING;
  (c) a three-leg check exists and is scored; DONE (above);
  (d) single-leg CLV on logged anytime-TD lines is at least neutral, since no API carries
      same-game-parlay prices and the pair validation rests on outcomes plus single-leg market
      evidence; NOT YET MEASURABLE (the record is filling).
- Why the gate stays closed: the joint structure is right in direction but not established
  on test, and the largest remaining pair error is inherited from the legs -- pairs of two
  high-priced players run high (0.090 vs 0.079), the top-share players' passing-channel bias
  (reports/td_diagnostics.md). Reopen after that is fixed and this backtest is rerun.
- The copula moves single-leg prices by up to 0.3 points (the mix shift interacting with
  correlated counts); v1's single-leg prices are unchanged because nothing prices from this.

### anytime_td_v0
- Markets: player_anytime_td
- Status: `SUPERSEDED` by anytime_td_v1 on 2026-09-21; retained as its fallback only.
- Spec: project team passing and rushing TDs; split each into the goal-line portion (plays
  starting inside the 10) and the long-play portion using prior-season league fractions
  (2025: 48% of passing TDs and 74% of rushing TDs from inside the 10); allocate the
  goal-line portion by inside-the-10 target/carry share and the long-play portion by overall
  target/carry share; convert to P(yes) = 1 - exp(-lambda). This is the separate touchdown
  module required by `modeling_framework.md`, NOT a historical scored-at-least-once frequency.
- Revision note: the first live version allocated ALL team TDs by inside-the-10 share. That
  under-rated explosive and high-volume players (Gibbs: 9 of 18 2025 TDs from outside the 10;
  J. Williams: 8 of 20) and over-rated goal-line specialists. Corrected 2026-09-17.
- Test: its STRUCTURE was reproduced and scored as the baseline in the anytime_td_v1
  backtests (`reports/td_v1.md`). Measured property: it runs LOW -- mean predicted 0.135
  vs 0.148 actual on 2024-25 (about 1.3 points), 0.133 vs 0.138 on 2018-19. When the
  fallback fires, the player card and the sources table say so.
- Known limits:
  - No complementary "No" side is quoted, so no-vig removal is unavailable; the comparison
    uses the bookmaker's raw implied probability and is therefore biased against the bet by
    roughly the hold. Disclose this wherever a TD gap is reported.
  - Scorer independence: players are currently drawn independently, so this cannot price
    correlated multi-scorer markets.
  - A market-anchored variant (team implied total x league TD-per-point) is computed as a
    sensitivity. Because it consumes the same book's total, it cannot then serve as evidence
    of edge against that book.
- Next step to `VALIDATED_DISTRIBUTION`: Brier/log-loss with reliability on the Gate A
  scoring population.

### (no other models)
Passing yards, passing TDs, and spreads/totals have no model. All props in those markets are
`MODEL_UNVALIDATED`.

### receiving_hier_v2 (shared model core, rounds 5-6)
- Markets: player_receptions, player_reception_yds (rushing yards runs through the same
  code path but has NO backtest; see rush_yds_v0)
- Status: `PROTOTYPE`
- Spec: same hierarchical structure as v1, now in `scripts/model.py` (shared by
  `score_game.py` and `backtest.py`), with: per-rate shrinkage constants in OPPORTUNITY
  units (team targets / own targets / carries), tuned on a held-out 2025 fold; team-level
  opponent efficiency adjustment with empirical-Bayes shrinkage; joint per-team simulation
  (one team-volume draw per sim, multinomial split, "other" bucket) for correlated
  teammate outcomes; optional market-anchored team environment (OFF by default).
- Backtest (2025; train weeks 5-8, test 9-18; ACT-only, INA voided, byes excluded;
  per-arm MLE dispersion; PAIRED game-block bootstrap on the MODEL'S OWN CRPS against a
  reference run of the v1-equivalent, positive = better than reference):

  | Change | Receptions | Reception yards | Verdict |
  |---|---|---|---|
  | Market-anchored env (team pass rate preserved) | -0.002 (-0.005,+0.002) | -0.010 (-0.050,+0.032) | no difference; NOT adopted, `--env market` optional/unvalidated |
  | Constant league-average env | -0.002 (-0.012,+0.008) | -0.017 (-0.111,+0.083) | no difference |
  | Per-rate K0, opportunity units | -0.001 (-0.005,+0.003) | +0.009 (-0.037,+0.057) | no difference; kept as the principled parameterisation |
  | Opponent (ALL variants) | see corrected table below | | prior verdicts VOID |

**Round-7 correction, opponent adjustment.** Every opponent verdict in the previous
version of this entry was invalid. `build_opponent_table` computed the league YPT
reference with `.mean()` on `receiving_yards`, which is NaN on incompletions in nflverse
PBP, so it returned yards per COMPLETION (10.9) while the per-team value was yards per
TARGET (7.3). Every defense got a raw ratio near 0.67; every receiving-yards projection
was cut 12-18% regardless of opponent. That bias, not the opponent signal, produced the
"fixed shrinkage is significantly harmful" result. Caught by a reviewer from the Under
lean in a live report (43 of 55 lines Under). Fixed by filling NaN with 0 on both sides
so numerator and denominator are both per target; league ref now 7.07 vs team mean 7.06.

Re-run after the fix (2025, train 5-8 / test 9-18, paired game-block bootstrap on the
model's own CRPS vs a history-env, no-opponent reference):

  | Variant | Receptions | Reception yards | Verdict |
  |---|---|---|---|
  | Team level, fixed k0=150 | -0.001 (-0.004,+0.002) | **+0.056 (+0.006,+0.108)** | helps; ADOPTED as default |
  | Team level, empirical-Bayes | -0.000 (-0.003,+0.002) | **+0.052 (+0.019,+0.087)** | helps; available via mode="eb" |
  | Position-group, empirical-Bayes | -0.000 (-0.002,+0.002) | +0.015 (-0.027,+0.057) | no effect; per-position samples too thin |

  On the |spread|>=7 subset all variants' intervals include zero, so the gain is a
  broad small effect rather than something concentrated in lopsided games.

**Bias diagnostic added** to `backtest.py` after this: per market, fraction of outcomes
above the model median, mean PIT, PIT decile histogram, and an automatic BIASED flag.
CRPS is insensitive to a uniform directional shift, which is why the YPT bug survived
several review rounds. Current reference run: receptions PIT mean 0.492, yards 0.498,
actual/model mean ratio 0.977 and 0.992 -- unbiased. (The "frac above median" of 0.39 on
receptions is a discreteness artifact: 22.6% of outcomes tie the integer median.)

**Round-7, market environment rebuilt properly.** The earlier "market anchoring is a
no-op" finding was also partly an artifact of the implementation: `plays` was pinned to a
league constant for every team and the pass-rate shift was hand-set at 0.015 per 7 points,
so the only thing the market actually fed was touchdowns. Rebuilt: team plays and pass
rate now come from coefficients FIT on 2025 (`market_env_fit` in the priors), blended with
the team's own pace history by `pace_weight`.

  Fitted coefficients (2025, n=544 team-games):
  plays = 47.80 + 0.146*spread + 0.201*total, R2 = 0.022
  pass rate = 0.371 - 0.0022*spread + 0.0038*total, R2 = 0.041
  The hand-set 0.015-per-7-points shift (= 0.0021/pt) was nearly identical to the fitted
  0.0022/pt, so the pass-rate shift was never the problem; pinned plays was.

  Paired game-block bootstrap vs the history reference:

  | pace_weight | Scope | Receptions | Reception yards |
  |---|---|---|---|
  | 0.25 | all games | **+0.003 (+0.000,+0.007)** | +0.030 (-0.008,+0.069) |
  | 0.25 | \|spread\|>=7 | +0.004 (-0.001,+0.009) | **+0.067 (+0.006,+0.135)** |
  | 0.50 | all games | +0.004 (-0.001,+0.009) | +0.049 (-0.009,+0.103) |
  | 0.50 | \|spread\|>=7 | +0.002 (-0.005,+0.011) | +0.099 (-0.003,+0.200) |
  | 1.00 | \|spread\|>=7 | +0.000 (-0.014,+0.015) | +0.142 (-0.019,+0.312) |

  Read this cautiously. Twelve comparisons were run; two exclude zero, where chance alone
  would give about 0.6. The point estimates are consistently positive and grow on lopsided
  games, which is the direction theory predicts, but this is suggestive rather than
  established. `--env market_fit --pace-weight 0.25` is available and NOT the default;
  promote it only if it holds up on a second season.

**Round-8 (code review), two findings on cross-season validation.**

1. *Legacy depth-chart schema was mixing return specialists into "WR1".* nflverse's
   pre-2025 format lists the same position across offense AND special teams; a WR row
   with depth_team=1 may be the starting split end or the punt returner (921 PR rows under
   position WR in 2024). Fixed in `model.normalize_depth_charts`: keep only
   formation=="Offense" and depth_position==position, then stable-sort. Now exactly one
   player per slot per team-week on 2024. This halved the 2024 receptions bias but did
   not clear it.

2. *The team-volume environment lags within-season league drift, in BOTH seasons.*
   Team targets/game rose +3.4% from weeks 1-8 to 9-18 in 2024 and fell -4.2% in 2025. An
   expanding mean lags both. Bias diagnostic (actual/model mean, receptions):

   | Env | 2024 | 2025 |
   |---|---|---|
   | expanding mean (default) | 1.045 | 0.976 |
   | trailing 4 games | 1.025 | 0.989 |
   | trailing 6 games | 1.028 | 0.985 |

   So "2025 is calibrated" was wrong; it had the same defect in the other direction. A
   trailing window converges toward 1.0 from both sides, confirming the mechanism, but
   costs CRPS (2024 1.033->1.036, 2025 1.009->1.014) because per-team 4-game means are
   noisy. Default stays expanding mean for now; `--env-window N` is available. The
   principled fix is an expanding team mean multiplied by a league-wide recent/expanding
   volume ratio (bias correction without per-team noise); not yet implemented or tested.
   A ~2.5% residual bias remains on 2024 with the window, source not yet identified.

   Consequence: cross-season validation of the market-fit and opponent findings is still
   pending. 2024 now has a sane population but a known small bias; both seasons' bias
   should be corrected before their comparison numbers are treated as a second-season
   confirmation.

**Round-9: within-season league drift correction. ADOPTED (the first change in several
rounds that improves accuracy and reduces bias at the same time).**

The per-team expanding mean is the low-variance estimate of team volume but lags
league-wide drift: total targets/game rose 3.4% inside 2024 and fell 4.2% inside 2025.
`model.league_drift_ratio` scales the expanding mean by a single league-wide
recent(3 weeks)/expanding ratio, estimated across all 32 teams so it adds almost no
variance, clipped to [0.85, 1.15] and inactive before week 5.

  | | 2024 bias (rec) | 2025 bias (rec) | 2024 CRPS | 2025 CRPS |
  |---|---|---|---|---|
  | expanding mean | 1.045 | 0.976 | 1.0329 | 1.0091 |
  | + drift correction | **1.026** | **0.995** | **1.0291** | 1.0087 |
  | per-team trailing 4 (rejected) | 1.025 | 0.989 | 1.0362 (worse) | 1.0141 (worse) |

  Paired game-block bootstrap, receptions: 2024 +0.0037 (+0.0008, +0.0067), excludes
  zero; 2025 +0.0003 (-0.0031, +0.0037). So it materially helps the season that was
  badly biased and costs nothing on the season that was mildly biased the other way.
  Insensitive to the recent-window length (2, 3, 4 and 5 give the same bias), so this is
  a mechanism, not a tuned parameter. The per-team trailing window fixed the same bias
  but cost CRPS in both seasons, which is why it was rejected in favour of separating
  LEVEL (per-team, expanding) from DRIFT (league-wide, recent).

  Live behaviour: inactive before week 5 and reported as such in the source table, so
  early-season runs are unchanged rather than corrected on a thin sample.

  Round-9 review corrections: (a) the first wiring applied the ratio to the current-
  season mean BEFORE it was blended with the prior-season team mean, which diluted the
  deployed correction to the blend weight (50% strength at week 5); now applied to the
  blended environment, and to goal-line volume and TD rates as well as targets/carries.
  (b) "Insensitive to window length" is accurate for 2024 (1.025-1.026 across 2-5) and
  slightly overstated for 2025 (0.988-0.996).

  KNOWN GAP, not fixed: the live scorer blends the current-season team environment with
  the prior-season team mean (K0=4 games). The backtest environment is current-season
  only. The prior-season blend has therefore never been validated; early-season live
  projections run an environment the backtest does not test. Either add the blend to
  `backtest.py` and test it, or drop it from `score_game.py`. Left as-is and documented
  rather than silently picked.

**Round-10: team touchdown totals anchored to the market by default.** Caught by Gabriel
on the MIN@CHI card: Swift TD Yes (-130, us 67%) and Monangai TD Yes (+180, us 43%) were
graded STRONG. Chicago's team TD projection was 3.8 = 0.8 x 2.76 (2025 avg) + 0.2 x 8
(week 1 blowout). The market implied 26 points = 2.74 TDs. Rescaling to market removes
both calls (Swift 56% vs book 57%). Change: TD totals use implied points x league
TD-per-point by default, keeping the history pass/rush split; plays and pass rate stay on
the history blend (the plays re-centre is separately unvalidated). Confidence tier caps TD
calls at MODERATE when the anchor is unavailable and annotates STRONG TD calls when the
history blend disagreed with the market by >20%. Note this anchor consumes the same book's
total and therefore cannot be cited as evidence of edge against that book's game total.

- CORRECTION of the first round-5 registry text:**Round-7, market environment rebuilt properly.** The earlier "market anchoring is a
no-op" finding was also partly an artifact of the implementation: `plays` was pinned to a
league constant for every team and the pass-rate shift was hand-set at 0.015 per 7 points,
so the only thing the market actually fed was touchdowns. Rebuilt: team plays and pass
rate now come from coefficients FIT on 2025 (`market_env_fit` in the priors), blended with
the team's own pace history by `pace_weight`.

  Fitted coefficients (2025, n=544 team-games):
  plays = 47.80 + 0.146*spread + 0.201*total, R2 = 0.022
  pass rate = 0.371 - 0.0022*spread + 0.0038*total, R2 = 0.041
  The hand-set 0.015-per-7-points shift (= 0.0021/pt) was nearly identical to the fitted
  0.0022/pt, so the pass-rate shift was never the problem; pinned plays was.

  Paired game-block bootstrap vs the history reference:

  | pace_weight | Scope | Receptions | Reception yards |
  |---|---|---|---|
  | 0.25 | all games | **+0.003 (+0.000,+0.007)** | +0.030 (-0.008,+0.069) |
  | 0.25 | \|spread\|>=7 | +0.004 (-0.001,+0.009) | **+0.067 (+0.006,+0.135)** |
  | 0.50 | all games | +0.004 (-0.001,+0.009) | +0.049 (-0.009,+0.103) |
  | 0.50 | \|spread\|>=7 | +0.002 (-0.005,+0.011) | +0.099 (-0.003,+0.200) |
  | 1.00 | \|spread\|>=7 | +0.000 (-0.014,+0.015) | +0.142 (-0.019,+0.312) |

  Read this cautiously. Twelve comparisons were run; two exclude zero, where chance alone
  would give about 0.6. The point estimates are consistently positive and grow on lopsided
  games, which is the direction theory predicts, but this is suggestive rather than
  established. `--env market_fit --pace-weight 0.25` is available and NOT the default;
  promote it only if it holds up on a second season.

**Round-8 (code review), two findings on cross-season validation.**

1. *Legacy depth-chart schema was mixing return specialists into "WR1".* nflverse's
   pre-2025 format lists the same position across offense AND special teams; a WR row
   with depth_team=1 may be the starting split end or the punt returner (921 PR rows under
   position WR in 2024). Fixed in `model.normalize_depth_charts`: keep only
   formation=="Offense" and depth_position==position, then stable-sort. Now exactly one
   player per slot per team-week on 2024. This halved the 2024 receptions bias but did
   not clear it.

2. *The team-volume environment lags within-season league drift, in BOTH seasons.*
   Team targets/game rose +3.4% from weeks 1-8 to 9-18 in 2024 and fell -4.2% in 2025. An
   expanding mean lags both. Bias diagnostic (actual/model mean, receptions):

   | Env | 2024 | 2025 |
   |---|---|---|
   | expanding mean (default) | 1.045 | 0.976 |
   | trailing 4 games | 1.025 | 0.989 |
   | trailing 6 games | 1.028 | 0.985 |

   So "2025 is calibrated" was wrong; it had the same defect in the other direction. A
   trailing window converges toward 1.0 from both sides, confirming the mechanism, but
   costs CRPS (2024 1.033->1.036, 2025 1.009->1.014) because per-team 4-game means are
   noisy. Default stays expanding mean for now; `--env-window N` is available. The
   principled fix is an expanding team mean multiplied by a league-wide recent/expanding
   volume ratio (bias correction without per-team noise); not yet implemented or tested.
   A ~2.5% residual bias remains on 2024 with the window, source not yet identified.

   Consequence: cross-season validation of the market-fit and opponent findings is still
   pending. 2024 now has a sane population but a known small bias; both seasons' bias
   should be corrected before their comparison numbers are treated as a second-season
   confirmation.

**Round-9: within-season league drift correction. ADOPTED (the first change in several
rounds that improves accuracy and reduces bias at the same time).**

The per-team expanding mean is the low-variance estimate of team volume but lags
league-wide drift: total targets/game rose 3.4% inside 2024 and fell 4.2% inside 2025.
`model.league_drift_ratio` scales the expanding mean by a single league-wide
recent(3 weeks)/expanding ratio, estimated across all 32 teams so it adds almost no
variance, clipped to [0.85, 1.15] and inactive before week 5.

  | | 2024 bias (rec) | 2025 bias (rec) | 2024 CRPS | 2025 CRPS |
  |---|---|---|---|---|
  | expanding mean | 1.045 | 0.976 | 1.0329 | 1.0091 |
  | + drift correction | **1.026** | **0.995** | **1.0291** | 1.0087 |
  | per-team trailing 4 (rejected) | 1.025 | 0.989 | 1.0362 (worse) | 1.0141 (worse) |

  Paired game-block bootstrap, receptions: 2024 +0.0037 (+0.0008, +0.0067), excludes
  zero; 2025 +0.0003 (-0.0031, +0.0037). So it materially helps the season that was
  badly biased and costs nothing on the season that was mildly biased the other way.
  Insensitive to the recent-window length (2, 3, 4 and 5 give the same bias), so this is
  a mechanism, not a tuned parameter. The per-team trailing window fixed the same bias
  but cost CRPS in both seasons, which is why it was rejected in favour of separating
  LEVEL (per-team, expanding) from DRIFT (league-wide, recent).

  Live behaviour: inactive before week 5 and reported as such in the source table, so
  early-season runs are unchanged rather than corrected on a thin sample.

  Round-9 review corrections: (a) the first wiring applied the ratio to the current-
  season mean BEFORE it was blended with the prior-season team mean, which diluted the
  deployed correction to the blend weight (50% strength at week 5); now applied to the
  blended environment, and to goal-line volume and TD rates as well as targets/carries.
  (b) "Insensitive to window length" is accurate for 2024 (1.025-1.026 across 2-5) and
  slightly overstated for 2025 (0.988-0.996).

  KNOWN GAP, not fixed: the live scorer blends the current-season team environment with
  the prior-season team mean (K0=4 games). The backtest environment is current-season
  only. The prior-season blend has therefore never been validated; early-season live
  projections run an environment the backtest does not test. Either add the blend to
  `backtest.py` and test it, or drop it from `score_game.py`. Left as-is and documented
  rather than silently picked.

**Round-10: team touchdown totals anchored to the market by default.** Caught by Gabriel
on the MIN@CHI card: Swift TD Yes (-130, us 67%) and Monangai TD Yes (+180, us 43%) were
graded STRONG. Chicago's team TD projection was 3.8 = 0.8 x 2.76 (2025 avg) + 0.2 x 8
(week 1 blowout). The market implied 26 points = 2.74 TDs. Rescaling to market removes
both calls (Swift 56% vs book 57%). Change: TD totals use implied points x league
TD-per-point by default, keeping the history pass/rush split; plays and pass rate stay on
the history blend (the plays re-centre is separately unvalidated). Confidence tier caps TD
calls at MODERATE when the anchor is unavailable and annotates STRONG TD calls when the
history blend disagreed with the market by >20%. Note this anchor consumes the same book's
total and therefore cannot be cited as evidence of edge against that book's game total.

- CORRECTION of the first round-5 registry text: it claimed market anchoring was "a
  clear, validated improvement." That was a misreading -- the model's gap to a naive
  baseline widened, but the model's own CRPS did not improve (it was fractionally worse).
  The claim was wrong and is withdrawn. Default environment is history (the round-4
  validated form).
- Opponent efficiency, second look: at the team level the data detects a real but small
  between-defense spread (~4% SD in efficiency ratio), which EB weights at roughly half
  after a full season; position-group level is thinner. Applying it changes CRPS by an
  amount indistinguishable from zero. Fixed shrinkage at any usable trust level is
  demonstrably harmful. Ship EB team-level: honest, data-weighted, inert-to-slightly-
  helpful. Do not switch to fixed shrinkage.
- K0 (opportunity units): target_share 80, catch_rate 40, ypt 160, rush_share 20, ypc 80
  (ypc hit the grid floor and was set to a documented default rather than the edge value).
- Joint simulation: marginals verified equal to closed-form means at every run (drift
  check logs a warning above 10%). CRPS backtest above is on marginals; the joint draw
  changes nothing there and exists for same-game-parlay probabilities, which have NO
  validation yet.
- Still unvalidated: anytime TD (no backtest), rushing yards (no backtest), any per-slot
  claim (round 4: nothing survives multiplicity), betting edge (needs 2026 archive).

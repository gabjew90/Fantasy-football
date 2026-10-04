# Rushing attempts: can the engine price them? (pre-registered 2026-10-03, before any run)

## Why

Sleeper posts rushing-attempts lines (65 players in the week-4 pull). The
research advice the user adopted says workload props isolate a role change
better than yardage. The engine already draws every carry
(model.simulate_team_rush) -- it has never been graded on carries.

## The test (no model change)

The yardage harness gains a "rushing attempts" market: the carries draws the
rushing simulation already makes, graded on the rushing population (backs and
anyone with 20%+ of the team's carries over his last four games; QBs are not
in it, so QB attempts with kneel-downs stay unpriced). Lines at the half, like
receptions. The draws and their order are unchanged, so every other market
must come out identical to props-v1.29's numbers.

## The bar (written before running)

Rushing attempts are priced only if, on the test seasons 2024-25, they pass the
same four-part `live` bar every priced market passed (docs/plans/2026-09-24-yardage-harness.md):

1. beat baseline A (the player's raw share, no shrinkage) on each test season,
   interval excluding zero;
2. unbiased (actual/model within 5%, PIT mean 0.47-0.53);
3. width: outcomes outside the model's p10-p90 within 0.20 +/- 0.03;
4. calibration: every 60-90% reliability bucket within 0.03 (weeks 5-18).

If a part fails, the fix is tuned on 2022-23 and read once on 2024-25 under its
own pre-registered rule; nothing is priced until the bar passes.

## Result (2026-10-03): does not pass -- not priced

Four-season harness, props-v1.29 model (round 23 on). Every other market is
identical to the decimal with the attempts market added (the draws and their
order are unchanged).

| Seasons | N | Gain over baseline A (95% CI) | Actual/model | PIT | Outside p10-p90 |
|---|---|---|---|---|---|
| 2024 all weeks | 1036 | +0.023 (-0.008, +0.056) | 1.018 | 0.499 | 0.278 |
| 2025 all weeks | 997 | +0.053 (+0.001, +0.107) | 1.034 | 0.518 | 0.259 |
| test 2024-25, weeks 2-4 | 372 | gains +0.15 to +0.18 | | | |
| test 2024-25, weeks 5-18 | 1661 | about zero | | | |

Verdict: beats baseline A each season **no**; unbiased yes; width 0.269
**no** (target 0.20 +/- 0.03); calibration worst 60-90% gap 0.060 **no** --
the 80-90% and 90%+ bands run 5-7 points optimistic on both sides.

Reading: the mean is right but the carries distribution is too narrow. Real
carries swing more game to game than the sampler's team-carries dispersion and
share concentration allow (share_conc_carries 20, team carries r ~23, both
tuned on rushing YARDS, which pass). Widening carries in the shared sampler
would also widen rushing yards, which is calibrated now, so the fix is a
carries-specific source of variance (e.g. a game-script component that moves a
back's carries and yards together), pre-registered and tuned on 2022-23 with
rushing yards held to its current bar. Not attempted today.

## Round 24 (pre-registered 2026-10-03, before any run): widen carries, hold rushing yards

Two settings move together: `share_conc_carries` (lower = a back's share of the
team's carries varies more game to game, which widens carries AND yards) and
`eff_sd_rush` (lower = less game-to-game noise in yards per carry, which
narrows yards only). Grid on 2022-23 only: share_conc_carries in {20 (shipped),
12, 8} x eff_sd_rush in {0.3 (shipped), 0.2, 0.1}.

Selection (tune seasons): keep the settings under which rushing YARDS still
pass width (0.20 +/- 0.03) and calibration (every 60-90% bucket within 0.03);
among those, the lowest rushing-attempts CRPS; ties (within 0.005) go to the
lower rushing-yards CRPS. If no setting keeps rushing yards passing, round 24
is dropped.

Ship rule (2024-25, read once): rushing attempts pass the full four-part bar,
rushing yards still pass the full bar, and rushing yards' CRPS is not worse
than props-v1.29 with a paired interval excluding zero. Otherwise attempts
stay unpriced and this report records the result.

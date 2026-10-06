# Prior-season shares over active weeks, and snap counts joined by ID (pre-registered 2026-10-06, before any run)

## Why (the second outside review, 2026-10-06; every claim checked against the code and data first)

- **Shares:** build_priors.py divided a player's targets and carries by his team's volume
  only in the weeks he had a touch, which inflates part-timers' shares (Velus Jones Jr.
  15.4% of the carries on 4 carries; 31 of 112 players with a stored carry share of 15%+ had
  under 40 carries). The fix counts the team's volume in every week the player was ACTIVE
  for that team (or touched the ball), as the harness already does for the current season.
  On the 2025 priors: those 31 players' mean carry share 20.7% -> 14.2%; backs with 150+
  carries 54.1% -> 54.0%; receivers with 100+ targets 24.2% -> 24.0%.
- **Snap counts:** the snap file and the roster spell some players differently ("Kenneth" /
  "Kenny Gainwell", "Zonovan" / "Bam Knight") and the engine joined them by name, so those
  players had no snaps (no new-team role scaling, no snap-change rule, a false "new this
  week" flag). Fixed: the roster's name by the snap file's pfr id, the name only as a
  fallback (model.snap_names_from_roster), in the scorer and the priors builder.
- **Games:** the weekly roster lists playoff weeks and bye weeks; "games" now counts active
  regular-season weeks in which the team played (2025 maximum 18: Rashid Shaheed, traded
  after New Orleans' bye and before Seattle's).

## What is run

The step 7 harness (new-team cap on), `--seasons 2022,2023,2024,2025 --tune 2022,2023 --test
2024,2025 --conditional`, with the priors rebuilt by the fixed builder (the harness builds
its own priors per season), against the step 7 run as the reference.

## Ship rule (a correction of a definition, not a tuning knob)

The fix ships -- the bundled priors_2025_*.csv rebuilt, the live board on it -- unless a bet
market (receptions, receiving yards, rushing yards, rushing + receiving, QB passing) is
worse by more than 0.5% of its own log loss (point estimate) on the conversion score or the
own-volume score (scoreboard.compare against step 7, frozen cohort). Width and bias from the
harness report are recorded beside it. A guard failure means: do not ship, find out which
players drive it.

**Amendment, 2026-10-06, before the run finished or any result was read:** the stand-in
lines are built from pre-game projections (expected targets x rates), and this fix moves
projections, so the two runs are scored at different lines and scoreboard.compare refuses
them (correctly: a log loss at a moved line is not comparable). The guard therefore uses the
whole-distribution score the harness writes per player-game -- CRPS (lower is better, no
line) -- paired on the reference's player-games, game-clustered 95% intervals: a bet market
whose mean CRPS is worse by more than 0.5% blocks the ship. The harness's width, bias and
calibration verdicts are recorded beside it, as registered.

## Result (2026-10-06)

Paired CRPS per player-game, the fix against the step 7 run (positive = the fix better;
95% intervals resampling games):

| Market | 2022-25 | Relative | Test 2024-25 | Relative |
|---|---|---|---|---|
| Receptions | -0.0008 (-0.0018, +0.0001) | -0.08% | -0.0002 (-0.0016, +0.0013) | -0.02% |
| Receiving yards | -0.0084 (-0.0190, +0.0022) | -0.06% | -0.0083 (-0.0241, +0.0071) | -0.06% |
| Rushing yards | +0.0160 (-0.0031, +0.0346) | +0.10% | +0.0182 (-0.0109, +0.0476) | +0.11% |
| Rushing + receiving | +0.0192 (-0.0050, +0.0429) | +0.10% | +0.0254 (-0.0090, +0.0589) | +0.13% |
| QB passing | -0.0357 (-0.0920, +0.0200) | -0.08% | -0.0631 (-0.1456, +0.0128) | -0.15% |

No market is worse by 0.5%: **the fix ships** (resources/priors_2025_players.csv rebuilt;
params and roles came out identical in content and were left as they were). Harness
verdicts on the test seasons: receptions bias -2.0% -> -1.0%, receiving yards -1.7% -> -0.7%;
widths essentially unchanged (receptions 18.3%, receiving yards 18.0%, rushing 23.3%,
combined 24.9% FAIL, QB passing 14.6%). The fix is a definition correction: whole-distribution
scores move by a tenth of a percent either way, and the largest change is the removal of
inflated priors for part-time players, which reach the board through backups and the Out rule.

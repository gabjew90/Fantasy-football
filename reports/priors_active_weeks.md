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

# Round 26: should a player's share lean harder on this season? (pre-registered 2026-10-05, before any run)

## Why

The user, after week 4: a player's target and carry share is a team decision, so this
season should count more than last season once a few weeks have passed. Efficiency (catch
rate, yards per target, yards per carry) is a player skill and may want a longer window
(the last 10 games) -- that is round 27, designed after this one, because the harness has
no rolling-window efficiency yet.

## The knob

Each share is blended as this season against the player's individual prior (last season
shrunk toward his slot), with this season's weight = n / (n + k0), n = his team's targets
(or carries) over the games counted. Current fixed values: target share k0 = 80 team
targets (model.K0_FIXED), carry share k0 = 40 team carries (fitted). After four games
(~130 team targets, ~100 team carries) this season already carries about 62% and 71%.

Grid (target share, carry share), lower = this season counts more; 10 / 5 is close to
"this season only" from week 2:

| Arm | target_share k0 | rush_share k0 |
|---|---|---|
| baseline (shipped) | 80 | 40 |
| B | 40 | 20 |
| C | 20 | 10 |
| D | 10 | 5 |

Run: `backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025
--k0 target_share=X,rush_share=Y` per arm, everything else shipped (props-v1.36 main).

## The rule (fixed now)

- **Selection, tune seasons 2022-23 only:** for target share, the arm with the lowest mean
  CRPS on weeks 5-18 summed over receptions and receiving yards; for carry share, the arm
  with the lowest weeks 5-18 rushing-yards CRPS. The two are chosen independently. An arm is
  eligible only if its weeks 2-4 CRPS on the same markets is no worse than baseline in the
  tune seasons.
- **Ship, 2024-25 read once:** a selected arm ships only if, on 2024-25, its weeks 5-18 CRPS
  on its markets beats baseline AND its weeks 2-4 CRPS is no worse AND no market's
  calibration verdict gets worse (PASS / INSUFFICIENT / FAIL). Otherwise the shipped value
  stays and the round is recorded as null.
- **Fresh check:** if it ships, 2026 weeks 2-4 are scored once as a sanity read, reported,
  not a gate.

## Result

(Filled in after the runs, below this line, without editing anything above.)

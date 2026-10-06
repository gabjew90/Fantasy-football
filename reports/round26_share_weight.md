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

The text above was committed before any run as 4db45da (2026-10-05 21:1x PT, tag archive/round26-prereg).

### Result (2026-10-05): null -- the shipped values stay

Selection on 2022-23 (lower CRPS is better):

| Arm (target / carry k0) | catches + rec yds, wks 5-18 | catches + rec yds, wks 2-4 | rush yds, wks 5-18 | rush yds, wks 2-4 |
|---|---|---|---|---|
| base 80 / 40 | **14.1571** | **15.4273** | 15.8883 | 16.1893 |
| B 40 / 20 | 14.1698 | 15.5375 | 15.8582 | **16.1716** |
| C 20 / 10 | 14.1914 | 15.7724 | 15.8419 | 16.3061 |
| D 10 / 5 | 14.2183 | 16.0211 | **15.8166** | 16.3903 |

- Target share: base wins weeks 5-18, and every step toward "this season only" is worse.
  Selected: 80 (no change).
- Carry share: D and C win weeks 5-18 but are worse than base in weeks 2-4, so they are
  ineligible; B (20) is the eligible winner. Selected: 20.

The would-ship configuration was run exactly (target 80, carry 20; arm E). Its tune
numbers match B's rushing and base's receiving to the decimal (separate random streams),
as expected. 2024-25, read once:

| Market | wks 5-18, base -> E | wks 2-4, base -> E |
|---|---|---|
| rushing yards | 15.9655 -> 15.9560 (better 0.010) | 16.3935 -> 16.4650 (**worse 0.072**) |
| carries | 2.7539 -> 2.7453 | 2.5590 -> 2.5684 (worse) |
| QB rushing | 8.7898 -> 8.8339 (worse) | 8.0524 -> 8.1933 (worse) |
| catches, rec yds, passing | identical | identical |

Calibration verdicts unchanged in every market. The ship rule needed weeks 2-4 no worse:
it is worse, so carry share stays at 40 and target share at 80. The early-season loss is
the cost of trusting two or three games of a backfield split; QB rushing loses because the
same constant covers the quarterback's share.

Noted during the run: backtest.py's --k0 replaced model.K0_FIXED instead of adding to it,
so a first launch compared against the wrong catch-rate / yards-per-target constants; it
was stopped and relaunched with them stated (all arms above carry ypt 80, catch rate 40).

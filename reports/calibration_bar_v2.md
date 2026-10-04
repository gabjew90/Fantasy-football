# The `live` bar, revised: intervals and a three-way verdict (pre-registered 2026-10-03, before any run)

## Why

The bar every priced market had to clear (docs/plans/2026-09-24-yardage-harness.md)
compared point estimates against fixed tolerances. A reliability band 0.032
off failed, and one 0.027 off passed, though nothing showed those two
numbers were really different. Each player-game also carries four synthetic
lines that share one outcome, and the players in a game share its script, so
counting lines as independent overstates how much the record knows. The
critique the user brought in on 2026-10-03 asked for three things, all
adopted here:

1. Every part of the bar reads a 95% interval from **resampling whole NFL
   games** (each game's players and synthetic lines stay together), and
   reports **PASS / FAIL / INSUFFICIENT DATA**, not yes/no.
2. Every verdict states the **unique games and player-games** behind it.
3. "Beats baseline A on each test season" becomes **pooled improvement with
   no material seasonal deterioration**.

## The bar (written before running)

On the test seasons 2024-25, intervals are 95%, resampling games:

| Part | PASS | FAIL | Otherwise |
|---|---|---|---|
| Baseline | pooled gain over baseline A has its whole interval above 0, and no test season's interval sits wholly below 0 | pooled interval wholly below 0, or any test season's interval wholly below 0 | INSUFFICIENT DATA |
| Bias | relative bias mean(actual - model)/mean(model) has its whole interval inside +/-5%, and PIT mean within 0.47-0.53 | interval wholly outside +/-5% | INSUFFICIENT DATA (also when the interval passes but the PIT point is outside 0.47-0.53) |
| Width | share of outcomes outside the model's p10-p90 has its whole interval inside 0.17-0.23 | interval wholly outside 0.17-0.23 | INSUFFICIENT DATA |
| Calibration | every Over/Under band at 60-70, 70-80 and 80-90% (weeks 5-18): realized hit rate minus the band's **mean predicted probability** has its whole interval inside +/-0.03 | any band's interval wholly outside +/-0.03 | INSUFFICIENT DATA |

A market **PASSES** only when all four parts pass. Any FAIL **fails** it.
Anything else is **INSUFFICIENT DATA**: the record cannot yet tell good from
bad at this tolerance. The tolerances themselves are unchanged (5%, 0.20 +/-
0.03, 0.03); only how a number is judged against them changes.

## What a verdict does

The bar decides which markets the engine prices. Today the priced markets
are receptions, receiving yards, rushing yards, QB rushing yards and QB
passing yards; rushing attempts and QB completions were measured and not
priced (reports/rush_attempts.md, reports/qb_completions.md).

- A priced market that **FAILS** under the new bar is reported as failing.
  Whether to stop pricing it is a decision brought to the user, not made in
  this run.
- A priced market at **INSUFFICIENT DATA** is reported plainly as "not shown
  to be calibrated", not as passing, and keeps its UNVALIDATED status on the
  board. No market is described as "rescued" by the new bar.
- An unpriced market that **PASSES** is not priced by this run; pricing it is
  a separate pre-registered step.

## The run

`backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025`
on the current engine (snap rule round 23 on, attempts and completions in
the harness). Calibration lines now carry their game; older saved results
cannot be re-rendered under this bar and say INSUFFICIENT DATA if tried.

## Result

(Filled in after the run, below this line, without editing anything above.)

### Result (2026-10-03): no market passes; none of the five priced markets fails

The whole harness was re-run on the current engine (round-23 snap rule on).
The verdicts below come from that run's saved results, re-rendered after the
code review added two guards: a band seen in fewer than 10 games is not
judged, and rows with no PIT are not counted as inside p10-p90. Full tables
are in reports/yardage_harness.md.

| Market | Priced? | Games / player-games | Baseline | Bias | Width | Calibration | Verdict |
|---|---|---|---|---|---|---|---|
| receptions | yes | 512 / 6551 | PASS (+0.047 to +0.069) | PASS (-2.2%, -3.9% to -0.4%) | PASS (0.184, 0.174-0.193) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |
| receiving yards | yes | 512 / 6551 | PASS (+0.713 to +1.052) | PASS (-1.8%, -4.0% to +0.5%) | PASS (0.184, 0.174-0.193) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |
| rushing yards | yes | 512 / 2033 | PASS (+0.317 to +0.770) | INSUFFICIENT DATA (+3.3%, +0.5% to +6.0%) | PASS (0.198, 0.181-0.216) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |
| QB rushing yards | yes | 510 / 940 | PASS (+0.250 to +0.641) | INSUFFICIENT DATA (-4.7%, -11.2% to +1.3%) | INSUFFICIENT DATA (0.218, 0.190-0.245) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |
| QB passing yards | yes | 510 / 940 | PASS (+0.571 to +2.381) | PASS (-2.1%, -4.7% to +0.6%) | INSUFFICIENT DATA (0.178, 0.153-0.204) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |
| rushing attempts | no | 512 / 2033 | PASS (+0.006 to +0.069) | PASS (+2.6%, +1.0% to +4.3%) | **FAIL** (0.269, 0.249-0.290) | **FAIL** (Under 70-80: -0.051, -0.071 to -0.031) | **FAIL** |
| QB completions | no | 510 / 940 | PASS (+0.008 to +0.094) | INSUFFICIENT DATA (-4.8%, -7.1% to -2.7%; PIT 0.469) | PASS (0.202, 0.178-0.228) | INSUFFICIENT DATA | **INSUFFICIENT DATA** |

Calibration bands that kept each priced market from passing (weeks 5-18; gap
= realized minus mean predicted, 95% interval resampling games):

| Market | Band | Lines | Games | Gap | 95% |
|---|---|---|---|---|---|
| receptions | Over 60-70 | 3522 | 416 | +0.018 | -0.003 to +0.041 |
| receptions | Under 60-70 | 3138 | 416 | +0.016 | +0.000 to +0.031 |
| receiving yards | Over 60-70 | 7418 | 416 | +0.020 | +0.004 to +0.036 |
| rushing yards | Over 60-70 | 2303 | 416 | +0.022 | -0.002 to +0.044 |
| rushing yards | Over 70-80 | 1948 | 416 | -0.010 | -0.035 to +0.015 |
| rushing yards | Under 60-70 | 2792 | 416 | -0.032 | -0.054 to -0.011 |
| rushing yards | Under 70-80 | 2331 | 416 | -0.013 | -0.033 to +0.006 |
| rushing yards | Under 80-90 | 1259 | 408 | -0.013 | -0.037 to +0.010 |
| QB rushing yards | all five bands | 776-1082 | 296-414 | -0.039 to +0.022 | each interval 0.07-0.10 wide |
| QB passing yards | all six bands | 14-1665 | 14-414 | -0.162 to +0.021 | each interval 0.06-0.52 wide |

What it means, plainly:

- **Every priced market beats its baseline**, clearly, pooled across both
  test seasons. That part was never in doubt.
- **No priced market is shown to be calibrated within 3 points.** Receptions
  and receiving yards come closest: five of six receiving-yards bands pass and
  four of six receptions bands; the bands that miss sit about 2 points
  under-confident, with intervals reaching just past 3.
  Rushing yards' Under 60-70 band is 3.2 points over-confident, but its
  interval does not clear the tolerance, so it is not a FAIL. The QB markets
  have about 940 player-games, too few to pin any band within 3 points.
- **Nothing priced fails.** Under the pre-registered rule that means nothing
  is withdrawn; all five stay priced and UNVALIDATED on the board, and the
  board already shows no bet labels. They are "not shown to be calibrated",
  never "passing" and never "rescued".
- **Rushing attempts fails outright** (too narrow, and Unders over-confident).
  That confirms the round-24 null with intervals. QB completions is
  INSUFFICIENT DATA, not priced.
- The old bar called receptions and receiving yards PASS on point estimates
  (worst gaps 0.027 and 0.025 on props-v1.28). With intervals, the record
  cannot tell those apart from a 4-point miss. Two test seasons hold about
  416 graded games after week 4; a 3-point band needs more games than that,
  or a wider tolerance. Either change would be a new pre-registered decision,
  not an adjustment to this run.

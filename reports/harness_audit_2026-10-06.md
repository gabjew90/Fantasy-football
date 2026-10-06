# Backtest harness audit (2026-10-06)

**Why.** The user asked how we know the earlier backtests had no code mistakes, after
today's smoke run caught one in new analysis code: stage-1 volume bucketed by the
actual volume, which selects on the outcome. The backtest harness (backtest.py) decided
every shipped model change, so it got known-answer tests: inputs whose correct result
is known in advance, run through the real code.

## 1. Model-is-truth (does the scoring invent miscalibration?)

`backtest.py --synthetic-truth`: every actual outcome is replaced by an independent
draw from the model itself (its own random streams). A correct harness must then find
every market calibrated. Run on 2022-24 with the shipped settings, then replicated with
different seeds (`--audit-seed-offset 2`).

| Market | Player-games | PIT mean (run 1 / 2) | Outside p10-p90, run 1 | Relative bias 2022-24, run 1 / run 2 (95% CI) |
|---|---|---|---|---|
| Receptions | 9,978 | 0.499 / -- | 19.9% | +0.001 (-0.015, +0.016) / -- |
| Receiving yards | 9,978 | 0.500 / -- | 20.0% | +0.005 (-0.014, +0.024) / -- |
| Rushing yards | 3,032 | 0.494 / 0.501 | 20.4% | -0.015 (-0.040, +0.013) / +0.001 (-0.027, +0.028) |
| Rushing attempts | 3,032 | 0.489 / 0.501 | 20.4% | -0.015 (-0.032, +0.001) / +0.006 (-0.010, +0.022) |
| QB rushing yards | 1,402 | 0.480 / 0.502 | 21.1% | -0.047 (-0.099, +0.005) / -0.000 (-0.052, +0.051) |
| QB passing yards | 1,402 | 0.496 / 0.490 | 21.4% | -0.008 (-0.029, +0.013) / -0.019 (-0.040, +0.001) |
| QB completions | 1,402 | 0.499 / -- | 20.8% | n/a |

**Pass.** No market fails in either run. Every pooled bias interval includes zero.
The one season-level exclusion (2024 rushing yards and carries, one correlated event
among 24 season-market cells) and QB rushing's lean in run 1 both vanish in run 2:
chance, not a bug.

**Design finding (not a bug):** even a model that is right by construction cannot
reach PASS on the calibration bar with one test season. The reliability bands'
intervals (half-width about 0.02-0.06) are wider than the +/-0.03 tolerance, which is
why every real market reads INSUFFICIENT DATA. Pooling test seasons or changing the
tolerance is the user's decision (DECISIONS #150).

## 2. Leakage (does any week read the future?)

`--audit-truncate-after W`: every frame without the weeks after W. Week W's numbers
must match a full-season run exactly.

- Week 9, 2023 and 2024: 432 player-games, every column identical.
- Week 3, 2022 and 2025: 472 player-games, every column identical.

**Pass.** Two inputs are known only around kickoff and are used as such: game-day
actives (the ACT/INA roster status) and the closing spread/total. Both are what a run
inside the last 90 minutes has.

## 3. Null comparison (do the paired intervals invent differences?)

The same model run twice, differing only in random seeds (`--audit-seed-offset 1` vs
0, 2023-24, 7,597 player-games), compared with the harness's own paired game-block
bootstrap.

**Pass.** All 14 intervals (seven markets, all games and big spreads) include zero.
Seed noise alone (independent seeds): receptions +/-0.0014, receiving yards about
+/-0.02, rushing yards +/-0.035, QB passing +/-0.15 CRPS. Comparisons between settings
use common random numbers, which cancels most of this, so it is a conservative scale.

## 4. The new conditional option is inert

A 2023-24 run with and without `--conditional`: all 64 shared result columns and the
calibration table identical.

## 5. Shipped decisions against seed noise

| Decision | Margin that decided it | Seed-noise scale | Status |
|---|---|---|---|
| #133 carry rescale | rushing yards +0.243 | +/-0.035 | well clear |
| #134 market pass weight | QB passing +0.298; catches +0.001 | +/-0.15; +/-0.0014 | QB passing clear; catches within noise (QB passing carried the decision) |
| #135 fixed ypt / catch-rate k | receiving yards +0.019 (+0.001, +0.036) | about +/-0.02 | thin: replicated on fresh seeds below |
| #136 fixed target-share k | catches +0.003, receiving yards +0.025 | +/-0.0014, +/-0.02 | catches clear; yards thin: replicated below |
| #143 snap rule | catches +0.0089 (+0.0043, +0.0136) | +/-0.0014 | clear |

Replication of #135-#136 (fixed k 80/40/80 vs the yearly fit, 2024-25, fresh seeds):
see the result line added below.

**Replication result (fresh seeds, `--audit-seed-offset 3`, 2024-25, 7,511 player-games):**
the yearly fit against the fixed constants -- catches -0.0027 (-0.0043, -0.0011),
receiving yards -0.020 (-0.044, +0.003), rushing identical (these constants do not touch
carries). The fixed constants win again, in the same direction and about the same size as
when they shipped. #135-#136 stand.

## Verdict

The harness passes all four known-answer tests, and the two thin shipped decisions
replicate on fresh random draws. What this does not cover: whether past rounds asked the
right question (a pre-registration choice), and data errors upstream of the harness
(nflverse itself). Every new tool gets the same known-answer treatment before its first
real run -- which is what caught today's stage-1 bucket error before it reached a result.

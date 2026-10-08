# margin_buckets_v0: result scenarios from the closing spread

Pre-registered in docs/plans/2026-10-08-report-format-design.md. Fit 2018-2021 (1040 games), test 2022-2025 (1087 games), regular season, nflverse closing spread_line. A report applies the model to the spread posted when it runs, which can differ from the close: the test measured closing spreads only.

**Shipped: nothing (neither model passed): the report prints not estimated.**

| Model | Test log loss | Beats baseline by 0.02 | Calibration within 4 points |
|---|---:|---|---|
| A_empirical | 0.9114 | yes | NO |
| B_normal | 0.9299 | NO | NO |
| baseline (fit-season frequencies 0.348, 0.512, 0.139) | 0.9394 | - | - |

Residual sd on the fit seasons: 13.17 points.

## Calibration, A_empirical

| Spread band | Scenario | Games | Predicted | Observed | Gap |
|---|---|---:|---:|---:|---:|
| |s| <= 3 | favourite_9plus | 436 | 27.0% | 24.3% | +2.7 |
| |s| <= 3 | within_one_score | 436 | 54.0% | 59.9% | -5.9 |
| |s| <= 3 | underdog_9plus | 436 | 19.0% | 15.8% | +3.2 |
| 3.5-7 | favourite_9plus | 425 | 34.5% | 36.2% | -1.7 |
| 3.5-7 | within_one_score | 425 | 51.5% | 55.1% | -3.6 |
| 3.5-7 | underdog_9plus | 425 | 14.0% | 8.7% | +5.3 |
| 7.5+ | favourite_9plus | 226 | 52.3% | 49.1% | +3.1 |
| 7.5+ | within_one_score | 226 | 39.7% | 46.5% | -6.8 |
| 7.5+ | underdog_9plus | 226 | 8.1% | 4.4% | +3.7 |

## Calibration, B_normal

| Spread band | Scenario | Games | Predicted | Observed | Gap |
|---|---|---:|---:|---:|---:|
| |s| <= 3 | favourite_9plus | 436 | 32.0% | 24.3% | +7.7 |
| |s| <= 3 | within_one_score | 436 | 47.4% | 59.9% | -12.4 |
| |s| <= 3 | underdog_9plus | 436 | 20.6% | 15.8% | +4.8 |
| 3.5-7 | favourite_9plus | 425 | 39.8% | 36.2% | +3.5 |
| 3.5-7 | within_one_score | 425 | 45.0% | 55.1% | -10.1 |
| 3.5-7 | underdog_9plus | 425 | 15.3% | 8.7% | +6.6 |
| 7.5+ | favourite_9plus | 226 | 55.5% | 49.1% | +6.4 |
| 7.5+ | within_one_score | 226 | 36.5% | 46.5% | -9.9 |
| 7.5+ | underdog_9plus | 226 | 8.0% | 4.4% | +3.6 |


# dispersion_v0 -- keefamania

*Built 2026-09-24 by `python -m fantasy.dispersion fit --league keefamania`. Fitted on 2024 Sleeper weekly projections vs actuals (weeks 1-17), scored in keefamania's scoring; tested on 2025, which the fit never saw.*

**Verdict: PASS -- live.**

Coverage is the share of outcomes at or below each predicted quantile; a calibrated range puts 10% below p10 and 90% below p90. Pinball loss scores the whole range (lower is better) against a normal baseline: a normal sized to each projection bucket (that bucket's residual mean and spread in the same training season) and floored like the model, so the test is whether the empirical shape adds anything over a scaled bell curve.

| Position | Test rows | below p10 | below p25 | below p50 | below p75 | below p90 | inside p10-p90 | mean width | pinball (model) | pinball (normal) |
|---|---|---|---|---|---|---|---|---|---|---|
| QB | 512 | 14.5% | 30.7% | 51.2% | 77.9% | 91.6% | 77.1% | 19.3 | 2.165 | 2.167 |
| RB | 1374 | 11.5% | 29.5% | 54.4%-54.8% | 79.0% | 90.2% | 78.7% | 12.5 | 1.405 | 1.457 |
| WR | 2158 | 8.9%-9.0% | 26.3%-26.5% | 50.4%-50.6% | 74.9%-75.0% | 90.5% | 81.6% | 11.9 | 1.301 | 1.334 |
| TE | 1181 | 7.4%-29.8% | 24.2%-36.5% | 51.2%-55.5% | 72.9%-73.0% | 89.4%-89.5% | 82.1% | 8.7 | 1.026 | 1.051 |
| ALL | 5225 | 9.8%-14.9% | 27.1%-30.0% | 51.7%-52.9% | 75.8%-75.9% | 90.3% | 80.5% | 12.1 | 1.351 | 1.384 |

A coverage shown as a range (6.7%-31.2%) is the share strictly below the quantile and the share at or below it; they differ when outcomes tie on the quantile, as tight ends' 0.0 weeks do on a p10 of 0.0. A calibrated quantile falls inside the range.

**Position caveats** (more than 3 points off, or no better than the baseline) -- shown with every range built from this table, not tuned away:

- QB p10: 14.5%-14.5% of outcomes vs 10%
- QB p25: 30.7%-30.7% of outcomes vs 25%
- RB p25: 29.5%-29.5% of outcomes vs 25%
- RB p50: 54.4%-54.8% of outcomes vs 50%
- RB p75: 79.0%-79.0% of outcomes vs 75%

## The fitted table (residual quantiles, points)

**QB** (516 player-weeks, floor 0.16)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5+ | 516 | 16.5 | -8.7 | -4.8 | -0.2 | +5.6 | +10.6 |

**RB** (1356 player-weeks, floor -1.01)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 401 | 1.6 | -1.9 | -1.2 | -0.7 | +0.8 | +3.4 |
| 3-6 | 305 | 4.3 | -3.8 | -3.0 | -1.4 | +2.0 | +6.3 |
| 6-9 | 170 | 7.3 | -5.8 | -4.4 | -1.8 | +2.6 | +8.8 |
| 9-12 | 195 | 10.5 | -7.2 | -4.4 | -0.8 | +4.6 | +9.2 |
| 12+ | 285 | 13.9 | -7.9 | -4.6 | +0.3 | +5.9 | +10.9 |

**WR** (2207 player-weeks, floor -0.49)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 656 | 1.6 | -2.4 | -1.7 | -1.0 | +0.2 | +2.6 |
| 3-6 | 498 | 4.5 | -4.4 | -3.4 | -1.7 | +1.9 | +6.9 |
| 6-9 | 467 | 7.4 | -6.3 | -4.5 | -1.0 | +3.6 | +8.6 |
| 9-12 | 406 | 10.6 | -7.7 | -5.2 | -1.0 | +4.6 | +10.2 |
| 12+ | 180 | 13.4 | -8.0 | -5.1 | -0.9 | +3.2 | +10.1 |

**TE** (1148 player-weeks, floor 0.0)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 569 | 1.4 | -1.9 | -1.3 | -0.7 | +0.4 | +3.0 |
| 3-6 | 284 | 4.5 | -4.2 | -3.0 | -0.9 | +2.4 | +6.5 |
| 6+ | 295 | 7.7 | -5.8 | -4.2 | -0.9 | +3.4 | +7.5 |

## Leakage check

Sleeper serves past weeks' projections with a last_modified after the week's first kickoff. A projection revised with the result would show residuals near zero; the 2024 residual spread was about 7 points per player-week (checked 2026-09-24), which pre-game projections produce. The late timestamps are the final pre-kickoff updates (inactives), which a start/sit decision also has.

*Inputs: sleeper projections 2024 wk1 0.1h, sleeper stats 2024 wk1 0.1h, sleeper projections 2024 wk2 0.1h, sleeper stats 2024 wk2 0.1h, sleeper projections 2024 wk3 0.1h, sleeper stats 2024 wk3 0.1h, sleeper projections 2024 wk4 0.1h, sleeper stats 2024 wk4 0.1h, sleeper projections 2024 wk5 0.1h, sleeper stats 2024 wk5 0.1h, sleeper projections 2024 wk6 0.1h, sleeper stats 2024 wk6 0.1h, sleeper ...*

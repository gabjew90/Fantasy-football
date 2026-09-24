# dispersion_v0 -- omnibeta

*Built 2026-09-24 by `python -m fantasy.dispersion fit --league omnibeta`. Fitted on 2024 Sleeper weekly projections vs actuals (weeks 1-17), scored in omnibeta's scoring; tested on 2025, which the fit never saw.*

**Verdict: PASS -- live.**

Coverage is the share of outcomes at or below each predicted quantile; a calibrated range puts 10% below p10 and 90% below p90. Pinball loss scores the whole range (lower is better) against a normal baseline: a normal sized to each projection bucket (that bucket's residual mean and spread in the same training season) and floored like the model, so the test is whether the empirical shape adds anything over a scaled bell curve.

| Position | Test rows | below p10 | below p25 | below p50 | below p75 | below p90 | inside p10-p90 | mean width | pinball (model) | pinball (normal) |
|---|---|---|---|---|---|---|---|---|---|---|
| QB | 512 | 15.0% | 32.0% | 53.9% | 79.1% | 91.4%-91.6% | 76.6% | 18.3 | 2.125 | 2.121 |
| RB | 1381 | 10.4%-10.5% | 30.1%-30.2% | 55.5%-55.7% | 78.1% | 90.4%-90.5% | 80.2% | 13.1 | 1.474 | 1.517 |
| WR | 2205 | 7.7% | 25.8%-25.9% | 50.2% | 74.7% | 91.0% | 83.3% | 13.7 | 1.465 | 1.496 |
| TE | 1226 | 6.7%-31.2% | 25.8%-37.8% | 50.4%-54.8% | 73.9%-74.1% | 89.0% | 82.3% | 10.0 | 1.179 | 1.205 |
| ALL | 5324 | 8.8%-14.5% | 27.5%-30.3% | 52.0%-53.0% | 75.8% | 90.4%-90.5% | 81.6% | 13.1 | 1.465 | 1.494 |

A coverage shown as a range (6.7%-31.2%) is the share strictly below the quantile and the share at or below it; they differ when outcomes tie on the quantile, as tight ends' 0.0 weeks do on a p10 of 0.0. A calibrated quantile falls inside the range.

**Position caveats** (more than 3 points off, or no better than the baseline) -- shown with every range built from this table, not tuned away:

- QB p10: 15.0%-15.0% of outcomes vs 10%
- QB p25: 32.0%-32.0% of outcomes vs 25%
- QB p50: 53.9%-53.9% of outcomes vs 50%
- QB p75: 79.1%-79.1% of outcomes vs 75%
- QB: no better than the normal baseline (2.125 vs 2.121)
- RB p25: 30.1%-30.2% of outcomes vs 25%
- RB p50: 55.5%-55.7% of outcomes vs 50%
- RB p75: 78.1%-78.1% of outcomes vs 75%

## The fitted table (residual quantiles, points)

**QB** (516 player-weeks, floor 0.16)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-15 | 172 | 13.6 | -6.9 | -3.8 | +0.1 | +4.4 | +8.0 |
| 15+ | 344 | 17.3 | -8.9 | -4.8 | +0.0 | +5.9 | +10.7 |

**RB** (1402 player-weeks, floor -0.4)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 398 | 1.5 | -2.0 | -1.2 | -0.6 | +0.8 | +3.2 |
| 3-6 | 298 | 4.3 | -4.2 | -3.1 | -1.4 | +1.9 | +6.5 |
| 6-9 | 173 | 7.1 | -6.2 | -4.1 | -1.3 | +3.0 | +8.4 |
| 9-12 | 178 | 10.8 | -7.1 | -4.5 | -0.7 | +4.9 | +9.5 |
| 12+ | 355 | 14.8 | -8.3 | -4.3 | +0.4 | +5.8 | +11.2 |

**WR** (2233 player-weeks, floor -0.45)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 572 | 1.7 | -2.4 | -1.8 | -1.0 | +0.5 | +3.4 |
| 3-6 | 424 | 4.5 | -4.7 | -3.4 | -1.8 | +1.7 | +7.0 |
| 6-9 | 404 | 7.5 | -6.7 | -4.4 | -1.4 | +3.5 | +8.8 |
| 9-12 | 339 | 10.2 | -7.9 | -6.0 | -1.4 | +4.2 | +9.9 |
| 12+ | 494 | 13.9 | -9.6 | -5.9 | -0.6 | +4.8 | +12.0 |

**TE** (1188 player-weeks, floor 0.0)

| projected | n | centre | p10 | p25 | p50 | p75 | p90 |
|---|---|---|---|---|---|---|---|
| 0.5-3 | 535 | 1.5 | -2.0 | -1.4 | -0.7 | +0.6 | +3.4 |
| 3-6 | 241 | 4.2 | -4.4 | -3.1 | -1.2 | +2.9 | +6.3 |
| 6+ | 412 | 8.8 | -6.7 | -4.5 | -0.8 | +4.2 | +8.7 |

## Leakage check

Sleeper serves past weeks' projections with a last_modified after the week's first kickoff. A projection revised with the result would show residuals near zero; the 2024 residual spread was about 7 points per player-week (checked 2026-09-24), which pre-game projections produce. The late timestamps are the final pre-kickoff updates (inactives), which a start/sit decision also has.

*Inputs: sleeper projections 2024 wk1 0.1h, sleeper stats 2024 wk1 0.1h, sleeper projections 2024 wk2 0.1h, sleeper stats 2024 wk2 0.1h, sleeper projections 2024 wk3 0.1h, sleeper stats 2024 wk3 0.1h, sleeper projections 2024 wk4 0.1h, sleeper stats 2024 wk4 0.1h, sleeper projections 2024 wk5 0.1h, sleeper stats 2024 wk5 0.1h, sleeper projections 2024 wk6 0.1h, sleeper stats 2024 wk6 0.1h, sleeper ...*

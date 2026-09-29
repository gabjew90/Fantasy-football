# Props scorecard — 2026

1568 calls (1665 priced lines graded, so 97 superseded by a later line).

**7 pricing models in the record (props-v1.3, props-v1.26, props-v1.0, props-v1.1, props-v1.25, props-v1.7, props-v1.18); they are not pooled.** Pass `--pool` to pool them explicitly.

## Engine props-v1.3

371 settled calls, 188 winners (50.7%), net -3942 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 96 | 53.1% | 52.4% | +0.7% | -440 |
| 55%-60% | 79 | 48.1% | 57.6% | -9.5% | -1200 |
| 60%-65% | 74 | 50.0% | 62.7% | -12.7% | -945 |
| 65%-70% | 44 | 47.7% | 67.1% | -19.4% | -772 |
| 70%-80% | 41 | 58.5% | 74.7% | -16.1% | -43 |
| 80%-101% | 11 | 63.6% | 83.4% | -19.8% | +103 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 117 | 42.7% | 59.8% | 50.3% | -2827 |
| MODERATE | 34 | 47.1% | 55.6% | 51.5% | -691 |
| WEAK | 146 | 56.2% | 66.7% | 50.5% | -209 |
| UNTIERED | 74 | 54.1% | 51.0% | 49.6% | -214 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

117 anytime-TD calls priced by the v0 fallback or by an unrecorded model are left out of the tables above and shown only here.

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [model unknown] | 117 | 24.8% | 30.4% | -4623 |
| player_reception_yds | 157 | 52.2% | 59.2% | -1113 |
| player_receptions | 157 | 47.8% | 61.7% | -2640 |
| player_rush_yds | 57 | 54.4% | 59.9% | -189 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 371 | 50.7% | 60.3% | -3942 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 2 | 371 | 50.7% | -3942 |

### Closing line value

365 calls have both snapshots. The line moved toward the call 11.0% of the time (mean move -0.04).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

0 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

371 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | +0.045 | (-0.281, +0.435) |
| logit(model) | +0.115 | (-0.692, +0.945) |
| logit(market) | +1.241 | (-0.392, +2.983) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Engine props-v1.26

66 settled calls, 31 winners (47.0%), net -1026 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 18 | 50.0% | 52.2% | -2.2% | -197 |
| 55%-60% | 11 | 72.7% | 57.7% | +15.0% | +358 |
| 60%-65% | 12 | 66.7% | 62.1% | +4.6% | +197 |
| 65%-70% | 1 | 100.0% | 68.6% | +31.4% | +77 |
| 70%-80% | 6 | 16.7% | 73.5% | -56.8% | -426 |
| 80%-101% | 2 | 100.0% | 86.7% | +13.3% | +130 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 6 | 66.7% | 60.4% | 49.8% | +118 |
| MODERATE | 6 | 50.0% | 59.0% | 50.1% | -85 |
| LEAN | 12 | 58.3% | 54.9% | 50.4% | +68 |
| WEAK | 17 | 58.8% | 66.4% | 48.0% | +111 |
| UNTIERED | 25 | 28.0% | 39.8% | 42.5% | -1239 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 15 | 6.7% | 29.9% | -1276 |
| player_pass_yds | 3 | 66.7% | 59.7% | +56 |
| player_reception_yds | 19 | 63.2% | 59.1% | +236 |
| player_receptions | 19 | 57.9% | 61.5% | +68 |
| player_rush_yds | 10 | 50.0% | 58.0% | -110 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 31 | 41.9% | 51.4% | -777 |
| no | 35 | 51.4% | 54.5% | -249 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 66 | 47.0% | -1026 |

### Closing line value

51 calls have both snapshots. The line moved toward the call 5.9% of the time (mean move +0.10).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

15 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

51 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.0

24 settled calls, 15 winners (62.5%), net +249 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 7 | 42.9% | 52.6% | -9.7% | -170 |
| 55%-60% | 6 | 100.0% | 56.6% | +43.4% | +469 |
| 60%-65% | 4 | 50.0% | 62.3% | -12.3% | -73 |
| 65%-70% | 4 | 50.0% | 67.9% | -17.9% | -63 |
| 80%-101% | 1 | 100.0% | 82.9% | +17.1% | +75 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 9 | 77.8% | 57.1% | 48.7% | +386 |
| MODERATE | 3 | 33.3% | 51.9% | 48.4% | -122 |
| WEAK | 7 | 42.9% | 66.0% | 51.1% | -172 |
| UNTIERED | 5 | 80.0% | 55.3% | 53.4% | +158 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

8 anytime-TD calls priced by the v0 fallback or by an unrecorded model are left out of the tables above and shown only here.

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [model unknown] | 8 | 37.5% | 32.1% | -88 |
| player_reception_yds | 10 | 60.0% | 57.1% | +60 |
| player_receptions | 10 | 50.0% | 58.2% | -118 |
| player_rush_yds | 4 | 100.0% | 63.7% | +307 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 24 | 62.5% | 58.7% | +249 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 2 | 24 | 62.5% | +249 |

### Closing line value

24 calls have both snapshots. The line moved toward the call 33.3% of the time (mean move +0.04).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

0 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

24 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.1

24 settled calls, 14 winners (58.3%), net +47 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 6 | 50.0% | 52.4% | -2.4% | -67 |
| 55%-60% | 8 | 75.0% | 56.9% | +18.1% | +272 |
| 60%-65% | 3 | 33.3% | 62.5% | -29.1% | -122 |
| 65%-70% | 5 | 60.0% | 67.4% | -7.4% | -9 |
| 80%-101% | 1 | 100.0% | 82.9% | +17.1% | +74 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 9 | 77.8% | 59.1% | 50.4% | +327 |
| MODERATE | 3 | 33.3% | 52.4% | 48.8% | -122 |
| WEAK | 7 | 42.9% | 66.2% | 51.2% | -170 |
| UNTIERED | 5 | 60.0% | 54.6% | 53.0% | +13 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

9 anytime-TD calls priced by the v0 fallback or by an unrecorded model are left out of the tables above and shown only here.

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [model unknown] | 9 | 33.3% | 30.7% | -177 |
| player_reception_yds | 10 | 60.0% | 57.4% | +63 |
| player_receptions | 10 | 40.0% | 59.8% | -325 |
| player_rush_yds | 4 | 100.0% | 63.4% | +309 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 24 | 58.3% | 59.4% | +47 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 2 | 24 | 58.3% | +47 |

### Closing line value

24 calls have both snapshots. The line moved toward the call 29.2% of the time (mean move -0.08).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

0 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

24 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.25

508 settled calls, 221 winners (43.5%), net -9624 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 122 | 45.1% | 52.3% | -7.2% | -2334 |
| 55%-60% | 108 | 46.3% | 57.2% | -10.9% | -1792 |
| 60%-65% | 88 | 46.6% | 62.1% | -15.5% | -1803 |
| 65%-70% | 32 | 62.5% | 66.9% | -4.4% | +183 |
| 70%-80% | 21 | 47.6% | 74.1% | -26.5% | -435 |
| 80%-101% | 5 | 80.0% | 85.0% | -5.0% | +187 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 86 | 41.9% | 59.3% | 49.5% | -2132 |
| MODERATE | 28 | 53.6% | 58.9% | 50.2% | -147 |
| LEAN | 70 | 52.9% | 53.9% | 49.5% | -236 |
| WEAK | 122 | 50.8% | 63.5% | 49.4% | -1071 |
| UNTIERED | 202 | 35.1% | 40.7% | 43.1% | -6038 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 111 | 27.0% | 31.1% | -4065 |
| player_pass_yds | 28 | 35.7% | 59.3% | -1019 |
| player_reception_yds | 148 | 50.0% | 58.0% | -1637 |
| player_receptions | 147 | 51.7% | 58.1% | -1045 |
| player_rush_yds | 74 | 41.9% | 57.6% | -1857 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 151 | 45.0% | 53.2% | -2618 |
| no | 357 | 42.9% | 51.7% | -7005 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 508 | 43.5% | -9624 |

### Closing line value

48 calls have both snapshots. The line moved toward the call 18.8% of the time (mean move +0.19).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

111 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

397 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.193 | (-0.523, +0.160) |
| logit(model) | +0.301 | (-0.490, +0.906) |
| logit(market) | +0.085 | (-1.073, +1.207) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Engine props-v1.7

31 settled calls, 12 winners (38.7%), net -1049 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 6 | 50.0% | 51.2% | -1.2% | -92 |
| 55%-60% | 5 | 40.0% | 58.8% | -18.8% | -153 |
| 60%-65% | 6 | 66.7% | 62.4% | +4.3% | +90 |
| 65%-70% | 4 | 25.0% | 66.9% | -41.9% | -222 |
| 70%-80% | 3 | 33.3% | 74.7% | -41.4% | -148 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 10 | 60.0% | 60.2% | 50.0% | +26 |
| WEAK | 10 | 20.0% | 66.0% | 50.7% | -659 |
| UNTIERED | 11 | 36.4% | 37.0% | 41.6% | -416 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 8 | 25.0% | 31.7% | -473 |
| player_reception_yds | 9 | 66.7% | 59.6% | +166 |
| player_receptions | 10 | 40.0% | 62.0% | -342 |
| player_rush_yds | 4 | 0.0% | 64.7% | -400 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 31 | 38.7% | 53.8% | -1049 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 2 | 31 | 38.7% | -1049 |

### Closing line value

17 calls have both snapshots. The line moved toward the call 23.5% of the time (mean move -0.35).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

8 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

23 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.18

410 settled calls, 179 winners (43.7%), net -7060 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 87 | 50.6% | 52.6% | -2.0% | -895 |
| 55%-60% | 68 | 50.0% | 57.5% | -7.5% | -780 |
| 60%-65% | 66 | 43.9% | 61.8% | -17.9% | -1656 |
| 65%-70% | 28 | 46.4% | 67.4% | -20.9% | -672 |
| 70%-80% | 25 | 56.0% | 72.9% | -16.9% | -206 |
| 80%-101% | 6 | 50.0% | 83.3% | -33.3% | -71 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 61 | 41.0% | 60.1% | 49.5% | -1601 |
| MODERATE | 27 | 66.7% | 59.9% | 49.5% | +594 |
| LEAN | 61 | 55.7% | 54.2% | 49.7% | +104 |
| WEAK | 84 | 41.7% | 65.9% | 50.1% | -2239 |
| UNTIERED | 177 | 37.9% | 37.5% | 41.4% | -3918 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 120 | 28.3% | 30.0% | -3895 |
| player_reception_yds | 124 | 49.2% | 58.0% | -1543 |
| player_receptions | 125 | 53.6% | 59.4% | -542 |
| player_rush_yds | 41 | 41.5% | 61.7% | -1080 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 410 | 43.7% | 50.6% | -7060 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 410 | 43.7% | -7060 |

### Closing line value

19 calls have both snapshots. The line moved toward the call 42.1% of the time (mean move +0.68).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Market blend (shadow: nothing priced from it)

120 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

290 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

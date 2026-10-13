# Props scorecard — 2026

3563 calls (3746 priced lines graded, so 183 superseded by a later line).

**11 pricing models in the record (props-v1.3, props-v1.26, props-v1.0, props-v1.1, props-v1.31, props-v1.25, props-v1.7, props-v1.18, props-v1.28, props-v1.55, props-v1.67); they are not pooled.** Pass `--pool` to pool them explicitly.

## Label gate

The research board shows no bet labels. The gate is decided only at the reviews after weeks 8, 12, 18, on the calls through that week, and opens only when both hold: the model's number earns weight beside the book's price (the whole 98.3% interval above zero), and the top-tier calls made money at Sleeper's recorded prices (the whole 98.3% interval of net per $100 above zero). Each review uses 98.3% rather than 95% because the gate looks 3 times: the looks share one 5% chance of opening on luck. Between reviews it holds; the running weight (95%) is context only.

| Pricing model | Calls | Weeks | Running weight (95% CI) | Last review | Weight at review (98.3% CI) | Top-tier net per $100 at review (98.3% CI) | Gate |
|---|---|---|---|---|---|---|---|
| props-v1.3 | 381 | 2-2 | +0.088 (-0.715, +0.926) | none yet (first after week 8) | — | — | closed |
| props-v1.26 | 438 | 3-4 | +0.251 (-0.312, +0.910) | none yet (first after week 8) | — | — | closed |
| props-v1.0 | 24 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.1 | 24 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.31 | 52 | 4-4 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.25 | 401 | 3-3 | +0.324 (-0.445, +0.920) | none yet (first after week 8) | — | — | closed |
| props-v1.7 | 23 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.18 | 292 | 3-3 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.28 | 395 | 4-4 | +0.520 (-0.215, +1.143) | none yet (first after week 8) | — | — | closed |
| props-v1.55 | 305 | 5-5 | -0.015 (-0.950, +1.223) | none yet (first after week 8) | — | — | closed |
| props-v1.67 (current) | 386 | 5-5 | -0.285 (-1.288, +0.714) | none yet (first after week 8) | — | — | closed |
| all models, pooled (context only) | 2721 | 2-5 | +0.049 (-0.299, +0.434) | none yet (first after week 8) | — | — | closed |

## Sleeper against DraftKings/FanDuel

Not the model: when Sleeper's line or price sits off the DraftKings/FanDuel consensus, the side the consensus favours, bet at Sleeper's price (reports/sleeper_vs_books.md).

| Discrepancy | Bets | Won | Win rate | Break-even | Net per $100 (95% CI) |
|---|---|---|---|---|---|
| line off | 74 | 45 | 60.8% | 60.0% | +1.6 (-13.5, +13.6) |
| price off | 2 | 2 | 100.0% | 58.6% | +70.8 (+nan, +nan) |
| both, pooled | 76 | 47 | 61.8% | 60.0% | +3.4 (-11.5, +15.5) |

76 graded discrepancies: no verdict yet: the rule needs 200+ bets and an interval above zero.

## Engine props-v1.3

381 settled calls, 191 winners (50.1%), net -4379 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 99 | 53.5% | 52.4% | +1.1% | -355 |
| 55%-60% | 82 | 47.6% | 57.6% | -10.0% | -1321 |
| 60%-65% | 76 | 48.7% | 62.7% | -14.0% | -1145 |
| 65%-70% | 46 | 45.7% | 67.1% | -21.4% | -972 |
| 70%-80% | 41 | 58.5% | 74.7% | -16.1% | -43 |
| 80%-101% | 11 | 63.6% | 83.4% | -19.8% | +103 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 123 | 42.3% | 59.8% | 50.2% | -3041 |
| MODERATE | 35 | 48.6% | 55.5% | 51.5% | -614 |
| WEAK | 149 | 55.0% | 66.5% | 50.3% | -509 |
| UNTIERED | 74 | 54.1% | 51.0% | 49.6% | -214 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

117 anytime-TD calls priced by the v0 fallback or by an unrecorded model are left out of the tables above and shown only here.

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [model unknown] | 117 | 24.8% | 30.4% | -4623 |
| player_reception_yds | 162 | 51.9% | 59.2% | -1258 |
| player_receptions | 162 | 46.9% | 61.6% | -2932 |
| player_rush_yds | 57 | 54.4% | 59.9% | -189 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 381 | 50.1% | 60.3% | -4379 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 2 | 381 | 50.1% | -4379 |

### Closing line value

365 calls have both snapshots. The line moved toward the call 11.0% of the time (mean move -0.04).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

0 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

381 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | +0.040 | (-0.289, +0.440) |
| logit(model) | +0.088 | (-0.715, +0.926) |
| logit(market) | +1.228 | (-0.444, +2.937) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Engine props-v1.26

565 settled calls, 275 winners (48.7%), net -4558 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 128 | 52.3% | 52.6% | -0.2% | -640 |
| 55%-60% | 134 | 53.7% | 57.4% | -3.6% | -694 |
| 60%-65% | 80 | 55.0% | 62.0% | -7.0% | -222 |
| 65%-70% | 41 | 61.0% | 67.1% | -6.1% | +98 |
| 70%-80% | 27 | 48.1% | 73.1% | -25.0% | -451 |
| 80%-101% | 5 | 60.0% | 85.3% | -25.3% | +6 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 108 | 58.3% | 59.3% | 50.0% | +451 |
| MODERATE | 34 | 47.1% | 60.2% | 49.9% | -592 |
| LEAN | 81 | 59.3% | 54.0% | 49.5% | +772 |
| WEAK | 127 | 54.3% | 63.2% | 48.5% | +36 |
| UNTIERED | 215 | 36.7% | 39.9% | 43.1% | -5225 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 127 | 33.9% | 30.9% | -2405 |
| player_pass_yds | 32 | 50.0% | 59.6% | -347 |
| player_reception_yds | 161 | 51.6% | 57.8% | -1328 |
| player_receptions | 161 | 52.8% | 57.9% | -641 |
| player_rush_yds | 84 | 57.1% | 59.0% | +163 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 31 | 41.9% | 51.4% | -777 |
| no | 534 | 49.1% | 52.1% | -3781 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 66 | 47.0% | -1026 |
| 4 | 499 | 48.9% | -3532 |

### Closing line value

393 calls have both snapshots. The line moved toward the call 19.8% of the time (mean move +0.18).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

127 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

438 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.101 | (-0.947, +0.767) |
| logit(model) | +0.251 | (-0.312, +0.910) |
| logit(market) | -0.058 | (-1.552, +1.356) |

Leave-one-week-out log loss on the same calls: model 0.7034, market 0.6952, blend 0.7108 (438 calls).

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

### Worth a look

No marked line has been graded yet.

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

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

0 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

24 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.31

68 settled calls, 33 winners (48.5%), net -590 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 14 | 57.1% | 52.3% | +4.9% | +49 |
| 55%-60% | 17 | 47.1% | 57.5% | -10.4% | -299 |
| 60%-65% | 13 | 53.8% | 62.2% | -8.3% | -82 |
| 65%-70% | 7 | 42.9% | 67.9% | -25.1% | -223 |
| 70%-80% | 1 | 100.0% | 72.7% | +27.3% | +78 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 20 | 45.0% | 60.4% | 50.0% | -352 |
| MODERATE | 2 | 0.0% | 62.6% | 49.7% | -200 |
| LEAN | 8 | 50.0% | 53.4% | 49.1% | -67 |
| WEAK | 11 | 63.6% | 63.4% | 49.7% | +119 |
| UNTIERED | 27 | 48.1% | 41.8% | 44.6% | -90 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 16 | 50.0% | 34.5% | +150 |
| player_pass_yds | 4 | 25.0% | 59.5% | -221 |
| player_reception_yds | 19 | 42.1% | 58.8% | -475 |
| player_receptions | 19 | 47.4% | 58.1% | -300 |
| player_rush_yds | 10 | 70.0% | 57.5% | +257 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 17 | 52.9% | 55.3% | -34 |
| no | 51 | 47.1% | 51.9% | -556 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 4 | 68 | 48.5% | -590 |

### Closing line value

52 calls have both snapshots. The line moved toward the call 15.4% of the time (mean move +0.38).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### The snap-change rule's calls

Receiving calls whose target share the rule raised, lowered, or left alone. If the rule overshoots, the raised group's miss runs negative (and the lowered group's positive).

| Market | Rule | Calls | Hit rate | Model said | Book said | Mean miss |
|---|---|---|---|---|---|---|
| catches | raised | 8 | 62.5% | 58.2% | 50.2% | +0.77 |
| catches | lowered | 10 | 40.0% | 57.0% | 49.3% | +1.30 |
| catches | not moved | 1 | 0.0% | 68.8% | 59.7% | +2.21 |
| receiving yards | raised | 8 | 50.0% | 59.2% | 49.9% | +18.25 |
| receiving yards | lowered | 10 | 40.0% | 58.8% | 49.8% | +20.08 |
| receiving yards | not moved | 1 | 0.0% | 55.2% | 49.7% | +17.28 |

A group needs about 50 calls before its numbers say anything.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

16 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

52 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.25

512 settled calls, 222 winners (43.4%), net -9844 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 125 | 44.8% | 52.3% | -7.5% | -2454 |
| 55%-60% | 109 | 45.9% | 57.2% | -11.3% | -1892 |
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
| LEAN | 71 | 53.5% | 53.9% | 49.5% | -156 |
| WEAK | 123 | 50.4% | 63.5% | 49.4% | -1171 |
| UNTIERED | 204 | 34.8% | 40.8% | 43.2% | -6238 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 111 | 27.0% | 31.1% | -4065 |
| player_pass_yds | 28 | 35.7% | 59.3% | -1019 |
| player_reception_yds | 150 | 50.0% | 57.9% | -1657 |
| player_receptions | 149 | 51.0% | 58.1% | -1245 |
| player_rush_yds | 74 | 41.9% | 57.6% | -1857 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 153 | 45.1% | 53.2% | -2638 |
| no | 359 | 42.6% | 51.7% | -7205 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 512 | 43.4% | -9844 |

### Closing line value

48 calls have both snapshots. The line moved toward the call 18.8% of the time (mean move +0.19).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

111 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

401 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.199 | (-0.528, +0.146) |
| logit(model) | +0.324 | (-0.445, +0.920) |
| logit(market) | +0.018 | (-1.122, +1.137) |

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

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

8 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

23 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.18

412 settled calls, 179 winners (43.4%), net -7260 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 87 | 50.6% | 52.6% | -2.0% | -895 |
| 55%-60% | 69 | 49.3% | 57.4% | -8.1% | -880 |
| 60%-65% | 67 | 43.3% | 61.9% | -18.6% | -1756 |
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
| WEAK | 86 | 40.7% | 65.7% | 50.1% | -2439 |
| UNTIERED | 177 | 37.9% | 37.5% | 41.4% | -3918 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 120 | 28.3% | 30.0% | -3895 |
| player_reception_yds | 125 | 48.8% | 58.0% | -1643 |
| player_receptions | 126 | 53.2% | 59.5% | -642 |
| player_rush_yds | 41 | 41.5% | 61.7% | -1080 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| no | 412 | 43.4% | 50.7% | -7260 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 412 | 43.4% | -7260 |

### Closing line value

19 calls have both snapshots. The line moved toward the call 42.1% of the time (mean move +0.68).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

120 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

292 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.28

504 settled calls, 251 winners (49.8%), net -3258 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 111 | 50.5% | 52.7% | -2.3% | -1053 |
| 55%-60% | 121 | 54.5% | 57.4% | -2.8% | -471 |
| 60%-65% | 72 | 54.2% | 62.1% | -7.9% | -477 |
| 65%-70% | 47 | 51.1% | 67.2% | -16.1% | -650 |
| 70%-80% | 22 | 72.7% | 73.0% | -0.3% | +551 |
| 80%-101% | 5 | 60.0% | 82.6% | -22.6% | -4 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 95 | 47.4% | 59.6% | 50.1% | -1431 |
| MODERATE | 25 | 44.0% | 59.5% | 49.4% | -545 |
| LEAN | 74 | 55.4% | 53.5% | 49.0% | +74 |
| WEAK | 127 | 59.8% | 63.4% | 50.0% | +867 |
| UNTIERED | 183 | 42.6% | 40.7% | 43.8% | -2222 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 109 | 37.6% | 32.0% | -1102 |
| player_pass_yds | 27 | 40.7% | 58.5% | -738 |
| player_reception_yds | 145 | 51.7% | 58.0% | -1144 |
| player_receptions | 148 | 55.4% | 59.0% | -278 |
| player_rush_yds | 75 | 56.0% | 58.7% | +4 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 122 | 54.9% | 53.8% | +93 |
| no | 382 | 48.2% | 52.5% | -3351 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 4 | 504 | 49.8% | -3258 |

### Closing line value

376 calls have both snapshots. The line moved toward the call 13.0% of the time (mean move +0.10).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

109 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

395 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.173 | (-0.511, +0.138) |
| logit(model) | +0.520 | (-0.215, +1.143) |
| logit(market) | -0.425 | (-2.049, +1.265) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Engine props-v1.55

413 settled calls, 202 winners (48.9%), net -3072 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 113 | 54.9% | 52.5% | +2.4% | -247 |
| 55%-60% | 86 | 51.2% | 57.2% | -6.0% | -828 |
| 60%-65% | 51 | 45.1% | 62.2% | -17.1% | -1115 |
| 65%-70% | 26 | 53.8% | 67.0% | -13.2% | -172 |
| 70%-80% | 11 | 81.8% | 73.9% | +7.9% | +418 |
| 80%-101% | 2 | 100.0% | 87.1% | +12.9% | +136 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 65 | 46.2% | 59.4% | 49.5% | -1127 |
| MODERATE | 13 | 30.8% | 58.2% | 48.5% | -574 |
| LEAN | 45 | 55.6% | 54.5% | 50.1% | -60 |
| WEAK | 97 | 50.5% | 61.6% | 49.1% | -851 |
| UNTIERED | 193 | 48.7% | 39.5% | 42.8% | -461 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 108 | 40.7% | 30.0% | -688 |
| player_pass_yds | 28 | 53.6% | 56.6% | -131 |
| player_reception_yds | 102 | 47.1% | 56.4% | -1655 |
| player_receptions | 103 | 50.5% | 56.7% | -1054 |
| player_rush_reception_yds | 25 | 52.0% | 57.7% | -190 |
| player_rush_yds | 47 | 63.8% | 59.7% | +646 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 249 | 51.0% | 50.3% | -697 |
| no | 164 | 45.7% | 49.7% | -2375 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 5 | 413 | 48.9% | -3072 |

### Closing line value

108 calls have both snapshots. The line moved toward the call 31.5% of the time (mean move +0.72).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### The snap-change rule's calls

Receiving calls whose target share the rule raised, lowered, or left alone. If the rule overshoots, the raised group's miss runs negative (and the lowered group's positive).

| Market | Rule | Calls | Hit rate | Model said | Book said | Mean miss |
|---|---|---|---|---|---|---|
| catches | raised | 60 | 50.0% | 55.8% | 48.5% | -0.35 |
| catches | lowered | 35 | 60.0% | 58.2% | 49.2% | +0.31 |
| catches | not moved | 8 | 12.5% | 57.6% | 51.0% | +0.63 |
| receiving yards | raised | 59 | 45.8% | 55.9% | 50.1% | -6.26 |
| receiving yards | lowered | 35 | 51.4% | 57.0% | 49.9% | +2.27 |
| receiving yards | not moved | 8 | 37.5% | 57.2% | 49.9% | -2.31 |

A group needs about 50 calls before its numbers say anything.

## Round 39 reversal check: rushing yards with market carries vs without

47 settled lines, 15 games. Board minus shadow, positive = the shadow is better:
- Log loss: board 0.6743, shadow 0.6762; difference -0.0019 (95% CI -0.0199 to +0.0147)
- Brier score: board 0.2416, shadow 0.2427; difference -0.0011 (95% CI -0.0099 to +0.0070)

The board's number stays the price until a pre-set review says otherwise.

## Round 34 reversal check: receiving at target spread 60 vs 40

205 settled lines, 15 games. Board minus shadow, positive = the shadow is better:
- Log loss: board 0.7074, shadow 0.7054; difference +0.0020 (95% CI -0.0023 to +0.0054)
- Brier score: board 0.2571, shadow 0.2561; difference +0.0010 (95% CI -0.0011 to +0.0027)

The board's number stays the price until a pre-set review says otherwise.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

108 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

305 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.037 | (-0.528, +0.359) |
| logit(model) | -0.015 | (-0.950, +1.223) |
| logit(market) | +2.814 | (+0.585, +5.036) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Engine props-v1.67

495 settled calls, 244 winners (49.3%), net -4130 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 127 | 57.5% | 52.4% | +5.1% | +373 |
| 55%-60% | 102 | 56.9% | 57.3% | -0.5% | +17 |
| 60%-65% | 75 | 52.0% | 62.2% | -10.2% | -693 |
| 65%-70% | 37 | 37.8% | 67.0% | -29.1% | -1307 |
| 70%-80% | 23 | 65.2% | 73.3% | -8.0% | +184 |
| 80%-101% | 3 | 66.7% | 86.3% | -19.7% | +34 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 88 | 48.9% | 59.9% | 50.1% | -1094 |
| MODERATE | 30 | 46.7% | 60.3% | 49.6% | -568 |
| LEAN | 53 | 58.5% | 54.4% | 49.7% | +324 |
| WEAK | 120 | 52.5% | 62.6% | 49.6% | -682 |
| UNTIERED | 204 | 45.6% | 40.2% | 43.1% | -2110 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 109 | 38.5% | 30.1% | -1299 |
| player_pass_yds | 27 | 44.4% | 56.0% | -566 |
| player_reception_yds | 137 | 49.6% | 57.4% | -1602 |
| player_receptions | 140 | 52.1% | 58.7% | -1200 |
| player_rush_reception_yds | 34 | 55.9% | 59.0% | -17 |
| player_rush_yds | 48 | 62.5% | 58.6% | +553 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 229 | 48.9% | 51.9% | -2240 |
| no | 266 | 49.6% | 51.9% | -1889 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 5 | 495 | 49.3% | -4130 |

### Closing line value

143 calls have both snapshots. The line moved toward the call 17.5% of the time (mean move -0.17).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

### The snap-change rule's calls

Receiving calls whose target share the rule raised, lowered, or left alone. If the rule overshoots, the raised group's miss runs negative (and the lowered group's positive).

| Market | Rule | Calls | Hit rate | Model said | Book said | Mean miss |
|---|---|---|---|---|---|---|
| catches | raised | 83 | 57.8% | 58.8% | 50.7% | -0.45 |
| catches | lowered | 41 | 48.8% | 58.9% | 49.1% | +0.50 |
| catches | not moved | 16 | 31.2% | 57.8% | 47.7% | +0.39 |
| receiving yards | raised | 82 | 50.0% | 56.7% | 50.0% | -6.20 |
| receiving yards | lowered | 39 | 48.7% | 58.1% | 50.0% | +4.58 |
| receiving yards | not moved | 16 | 50.0% | 59.2% | 49.9% | +0.69 |

A group needs about 50 calls before its numbers say anything.

## Round 39 reversal check: rushing yards with market carries vs without

48 settled lines, 14 games. Board minus shadow, positive = the shadow is better:
- Log loss: board 0.6986, shadow 0.7109; difference -0.0123 (95% CI -0.0306 to +0.0031)
- Brier score: board 0.2521, shadow 0.2580; difference -0.0058 (95% CI -0.0148 to +0.0017)

The board's number stays the price until a pre-set review says otherwise.

## Round 34 reversal check: receiving at target spread 60 vs 40

277 settled lines, 14 games. Board minus shadow, positive = the shadow is better:
- Log loss: board 0.7043, shadow 0.7035; difference +0.0008 (95% CI -0.0033 to +0.0050)
- Brier score: board 0.2548, shadow 0.2545; difference +0.0004 (95% CI -0.0016 to +0.0023)

The board's number stays the price until a pre-set review says otherwise.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

109 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

386 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | +0.033 | (-0.297, +0.346) |
| logit(model) | -0.285 | (-1.288, +0.714) |
| logit(market) | +2.353 | (+0.822, +4.239) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Bet journal

40 bets logged: 38 graded, 2 void (push or did not play), 0 open. Kept apart from the model's record: these are the user's handicapped bets.

**Late-line value, the first number to watch:** 29 of 40 bets got a better number than the last line Sleeper showed before kickoff (72%; 1 tied); median move your way +0.00 points (the median: one leg logged against a different product, such as a guaranteed 0.5 pick against a 226.5 line, cannot swing it). Beating the late line shows up in about 100-200 bets; the win rate needs far more. It is the last line the capture logged (usually a few hours out), not the true close.

| Bets | Won | Win rate | Break-even at these prices | Net per $100 staked |
|---|---|---|---|---|
| 38 | 21 | 55% | 56% | -2.6 |

A few dozen bets say little; about 100 is where the win rate starts to separate from luck.

**By angle** (chosen when the bet was logged):

| Angle | Bets | Graded | Won | Win rate | Break-even | Net per $100 | Beat the late line |
|---|---|---|---|---|---|---|---|
| injury redistribution | 2 | 2 | 0 | 0% | 59% | -100.0 | 1 of 2 |
| role change | 17 | 16 | 8 | 50% | 56% | -12.5 | 12 of 17 |
| teammate returning | 1 | 1 | 1 | 100% | 55% | +82.0 | 1 of 1 |
| other | 20 | 19 | 12 | 63% | 56% | +11.5 | 15 of 20 |

Each angle is its own small sample: read the late-line column first.

**Entries** (Sleeper Power Plays: every leg must hit):

| Logged | Legs | Stake | Pays (total) | Legs won / graded | Result | Net |
|---|---|---|---|---|---|---|
| week 4 (after kickoff) | Dalton Schultz under, Woody Marks under, Tyler Allgeier under, D'Andre Swift over, Luther Burden III over | $5 | $100 | 3 / 5 | lost | -5.00 |
| week 4 (after kickoff) | CeeDee Lamb yes, Ja'Marr Chase yes, Jaxon Smith-Njigba yes, Drake London yes | $5 | $103 | 1 / 4 | lost | -5.00 |
| week 4 (after kickoff) | Jahmyr Gibbs over, Amon-Ra St. Brown over, Chuba Hubbard over, Darren Waller over | $5 | $50 | 2 / 4 | lost | -5.00 |
| week 4 (after kickoff) | Ashton Jeanty under, Rashee Rice over, Courtland Sutton over, Mike Evans under | $5 | $47.5 | 1 / 3 | lost | -5.00 |
| week 4 (after kickoff) | Michael Penix Jr. over, Drake London over, Juwan Johnson over, Alvin Kamara over, Brian Robinson over, Tyler Shough over | $5 | $102.5 | 5 / 6 | lost | -5.00 |
| week 5 (after kickoff) | CeeDee Lamb over, Javonte Williams over, Bucky Irving over, Emeka Egbuka over, Jalon Daniels over | $5 | $97.5 | 2 / 5 | lost | -5.00 |
| week 5 (after kickoff) | Brock Bowers over, TreVeyon Henderson over, Devaughn Vele over, Isaiah Likely over | $5 | $50 | 2 / 3 | lost (as paid) | -5.00 |
| week 5 (after kickoff) | Trevor Lawrence under, Jalen Hurts over, Jakobi Meyers under, Parker Washington under | $5 | $37.5 | 2 / 4 | lost (as paid) | -5.00 |
| week 5 (after kickoff) | Kyren Williams over, James Cook over, Konata Mumpfield over, Tyler Higbee over | $5 | $50 | 3 / 4 | lost | -5.00 |

Entries logged after kickoff are kept but are not clean pre-game decisions; the legs are still graded one by one on the scorecard.

| Week | Player | Bet | Angle | Price | Late line | Result | Net | The change | Your scenario |
|---|---|---|---|---|---|---|---|---|---|
| 4 | Dalton Schultz | under 40.5 rec yds | teammate returning | -122 | 40.5 -130 (-0) | won | +82 | Role reads from the week-4 board: Houston redistributes around Collins and Montgomery, Love took Arizona's backfield, Chicago leans on Swift and Burden with Keenum | — |
| 4 | Woody Marks | under 36.5 rush yds | role change | -122 | 35.5 -125 (+1) | won | +82 | Role reads from the week-4 board: Houston redistributes around Collins and Montgomery, Love took Arizona's backfield, Chicago leans on Swift and Burden with Keenum | — |
| 4 | Tyler Allgeier | under 21.5 rush yds | role change | -122 | 21.5 -130 (-0) | lost | -100 | Role reads from the week-4 board: Houston redistributes around Collins and Montgomery, Love took Arizona's backfield, Chicago leans on Swift and Burden with Keenum | — |
| 4 | D'Andre Swift | over 63.5 rush yds | role change | -122 | 63.5 -132 (+0) | lost | -100 | Role reads from the week-4 board: Houston redistributes around Collins and Montgomery, Love took Arizona's backfield, Chicago leans on Swift and Burden with Keenum | — |
| 4 | Luther Burden III | over 46.5 rec yds | role change | -122 | 47.5 -127 (+1) | won | +82 | Role reads from the week-4 board: Houston redistributes around Collins and Montgomery, Love took Arizona's backfield, Chicago leans on Swift and Burden with Keenum | — |
| 4 | CeeDee Lamb | yes anytime TD | other | +113 | — | won | +113 | Anytime-TD Power Play on four lead receivers (no board read behind it; the TD model is untested) | — |
| 4 | Ja'Marr Chase | yes anytime TD | other | +113 | — | lost | -100 | Anytime-TD Power Play on four lead receivers (no board read behind it; the TD model is untested) | — |
| 4 | Jaxon Smith-Njigba | yes anytime TD | other | +113 | — | lost | -100 | Anytime-TD Power Play on four lead receivers (no board read behind it; the TD model is untested) | — |
| 4 | Drake London | yes anytime TD | other | +113 | — | lost | -100 | Anytime-TD Power Play on four lead receivers (no board read behind it; the TD model is untested) | — |
| 4 | Jahmyr Gibbs | over 4.5 catches | role change | -128 | 4.5 -143 (+0) | lost | -100 | SNF read: Carolina's reshuffled offense (Hubbard's workload, Waller as the safety valve) and Detroit's receiving roles (Gibbs' bigger share, St. Brown back to himself) | — |
| 4 | Amon-Ra St. Brown | over 7 catches | other | -128 | 6.5 -175 (-0.5) | won | +78 | SNF read: Carolina's reshuffled offense (Hubbard's workload, Waller as the safety valve) and Detroit's receiving roles (Gibbs' bigger share, St. Brown back to himself) | — |
| 4 | Chuba Hubbard | over 65.5 rush yds | role change | -128 | 65.5 -130 (+0) | won | +78 | SNF read: Carolina's reshuffled offense (Hubbard's workload, Waller as the safety valve) and Detroit's receiving roles (Gibbs' bigger share, St. Brown back to himself) | — |
| 4 | Darren Waller | over 3.5 catches | role change | -128 | 3.5 -125 (+0) | lost | -100 | SNF read: Carolina's reshuffled offense (Hubbard's workload, Waller as the safety valve) and Detroit's receiving roles (Gibbs' bigger share, St. Brown back to himself) | — |
| 4 | Ashton Jeanty | under 58.5 rush yds | other | -132 | 58.5 -132 (-0) | won | +76 | 1pm PT what-ifs: Las Vegas trails and abandons the run, Rice keeps the targets, Sutton as Nix's go-to, Evans limited | — |
| 4 | Rashee Rice | over 4.5 catches | role change | -132 | 4.5 -164 (+0) | void | +0 | 1pm PT what-ifs: Las Vegas trails and abandons the run, Rice keeps the targets, Sutton as Nix's go-to, Evans limited | — |
| 4 | Courtland Sutton | over 3 catches | role change | -132 | 3.5 +101 (+0.5) | lost | -100 | 1pm PT what-ifs: Las Vegas trails and abandons the run, Rice keeps the targets, Sutton as Nix's go-to, Evans limited | — |
| 4 | Mike Evans | under 3.5 catches | injury redistribution | -132 | 3.5 -118 (-0) | lost | -100 | 1pm PT what-ifs: Las Vegas trails and abandons the run, Rice keeps the targets, Sutton as Nix's go-to, Evans limited | — |
| 4 | Michael Penix Jr. | over 0.5 pass yds | other | -153 | 226.5 -130 (+226) | won | +65 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 4 | Drake London | over 80.5 rec yds | role change | -153 | 81.5 -130 (+1) | won | +65 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 4 | Juwan Johnson | over 4.5 catches | role change | -153 | 4.5 +105 (+0) | won | +65 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 4 | Alvin Kamara | over 35.5 rush yds | injury redistribution | -153 | 36.5 -130 (+1) | lost | -100 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 4 | Brian Robinson | over 29.5 rush yds | role change | -153 | 29.5 -130 (+0) | won | +65 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 4 | Tyler Shough | over 258.5 pass yds | other | -153 | 260.5 -128 (+2) | won | +65 | PrizePicks 6-pick Power Play (guarantee pick on Penix, demon on Juwan Johnson): Saints throwing (Shough, Johnson), London on yards over catches by the luck-free check, Brian Robinson on ordinary volume, Kamara as Etienne's replacement -- the Kamara leg needed the opposite script to the Saints passing legs | — |
| 5 | CeeDee Lamb | over 6.5 catches | role change | -123 | 6.5 -128 (+0) | lost | -100 | 5-pick Power Play on TB at DAL, logged from the user's screenshot in Q2 (angle inferred, not stated): Lamb and Williams on last game's bigger roles (target share 26% to 49%, carry share 62% to 76%), Irving and Egbuka receiving yards with Daniels starting, and a Daniels rushing guarantee pick (44.5 struck to 0.5), which counts as a leg and skews the per-leg price | — |
| 5 | Javonte Williams | over 66.5 rush yds | role change | -123 | 64.5 -125 (-2) | lost | -100 | 5-pick Power Play on TB at DAL, logged from the user's screenshot in Q2 (angle inferred, not stated): Lamb and Williams on last game's bigger roles (target share 26% to 49%, carry share 62% to 76%), Irving and Egbuka receiving yards with Daniels starting, and a Daniels rushing guarantee pick (44.5 struck to 0.5), which counts as a leg and skews the per-leg price | — |
| 5 | Bucky Irving | over 13.5 rec yds | role change | -123 | 13.5 -122 (+0) | lost | -100 | 5-pick Power Play on TB at DAL, logged from the user's screenshot in Q2 (angle inferred, not stated): Lamb and Williams on last game's bigger roles (target share 26% to 49%, carry share 62% to 76%), Irving and Egbuka receiving yards with Daniels starting, and a Daniels rushing guarantee pick (44.5 struck to 0.5), which counts as a leg and skews the per-leg price | — |
| 5 | Emeka Egbuka | over 36.5 rec yds | role change | -123 | 36.5 -132 (+0) | won | +81 | 5-pick Power Play on TB at DAL, logged from the user's screenshot in Q2 (angle inferred, not stated): Lamb and Williams on last game's bigger roles (target share 26% to 49%, carry share 62% to 76%), Irving and Egbuka receiving yards with Daniels starting, and a Daniels rushing guarantee pick (44.5 struck to 0.5), which counts as a leg and skews the per-leg price | — |
| 5 | Jalon Daniels | over 0.5 rush yds | role change | -123 | 43.5 -132 (+43) | won | +81 | 5-pick Power Play on TB at DAL, logged from the user's screenshot in Q2 (angle inferred, not stated): Lamb and Williams on last game's bigger roles (target share 26% to 49%, carry share 62% to 76%), Irving and Egbuka receiving yards with Daniels starting, and a Daniels rushing guarantee pick (44.5 struck to 0.5), which counts as a leg and skews the per-leg price | — |
| 5 | Brock Bowers | over 73.5 rec yds | other | -128 | 73.5 -133 (+0) | won | +78 | 4-pick Power Play logged from the user's screenshot after the games (reason not stated): Bowers and Likely receiving yards, Vele receiving yards, Henderson rushing yards | — |
| 5 | TreVeyon Henderson | over 46.5 rush yds | other | -128 | 46.5 -132 (+0) | void | +0 | 4-pick Power Play logged from the user's screenshot after the games (reason not stated): Bowers and Likely receiving yards, Vele receiving yards, Henderson rushing yards | — |
| 5 | Devaughn Vele | over 40.5 rec yds | other | -128 | 40.5 -132 (+0) | lost | -100 | 4-pick Power Play logged from the user's screenshot after the games (reason not stated): Bowers and Likely receiving yards, Vele receiving yards, Henderson rushing yards | — |
| 5 | Isaiah Likely | over 42.5 rec yds | other | -128 | 42.5 -130 (+0) | won | +78 | 4-pick Power Play logged from the user's screenshot after the games (reason not stated): Bowers and Likely receiving yards, Vele receiving yards, Henderson rushing yards | — |
| 5 | Trevor Lawrence | under 225.5 pass yds | other | -153 | 223.5 -127 (+2) | lost | -100 | 4-pick Power Play on PHI at JAX logged from the user's screenshot after the game (reason not stated): Lawrence passing Under, Hurts passing Over, Meyers and Washington receiving Unders | — |
| 5 | Jalen Hurts | over 186.5 pass yds | other | -153 | 188.5 -128 (+2) | won | +65 | 4-pick Power Play on PHI at JAX logged from the user's screenshot after the game (reason not stated): Lawrence passing Under, Hurts passing Over, Meyers and Washington receiving Unders | — |
| 5 | Jakobi Meyers | under 43.5 rec yds | other | -153 | 41.5 -130 (+2) | won | +65 | 4-pick Power Play on PHI at JAX logged from the user's screenshot after the game (reason not stated): Lawrence passing Under, Hurts passing Over, Meyers and Washington receiving Unders | — |
| 5 | Parker Washington | under 60.5 rec yds | other | -153 | 61.5 -125 (-1) | lost | -100 | 4-pick Power Play on PHI at JAX logged from the user's screenshot after the game (reason not stated): Lawrence passing Under, Hurts passing Over, Meyers and Washington receiving Unders | — |
| 5 | Kyren Williams | over 22.5 rec yds | other | -128 | 22.5 -130 (+0) | won | +78 | 4-pick Power Play on BUF at LA logged from the user's screenshot after the game (reason not stated): Kyren Williams receiving, Cook rushing, Mumpfield receiving and Higbee catches Overs | — |
| 5 | James Cook | over 77.5 rush yds | other | -128 | 77.5 -127 (+0) | won | +78 | 4-pick Power Play on BUF at LA logged from the user's screenshot after the game (reason not stated): Kyren Williams receiving, Cook rushing, Mumpfield receiving and Higbee catches Overs | — |
| 5 | Konata Mumpfield | over 6.5 rec yds | other | -128 | 7.5 -122 (+1) | lost | -100 | 4-pick Power Play on BUF at LA logged from the user's screenshot after the game (reason not stated): Kyren Williams receiving, Cook rushing, Mumpfield receiving and Higbee catches Overs | — |
| 5 | Tyler Higbee | over 2.5 catches | other | -128 | 2.5 -141 (+0) | won | +78 | 4-pick Power Play on BUF at LA logged from the user's screenshot after the game (reason not stated): Kyren Williams receiving, Cook rushing, Mumpfield receiving and Higbee catches Overs | — |

# Props scorecard — 2026

2621 calls (2718 priced lines graded, so 97 superseded by a later line).

**9 pricing models in the record (props-v1.3, props-v1.26, props-v1.0, props-v1.1, props-v1.31, props-v1.25, props-v1.7, props-v1.18, props-v1.28); they are not pooled.** Pass `--pool` to pool them explicitly.

## Label gate

The research board shows no bet labels. The gate is decided only at the reviews after weeks 8, 12, 18, on the calls through that week, and opens only when both hold: the model's number earns weight beside the book's price (the whole 95% interval above zero), and the top-tier calls made money at Sleeper's recorded prices (the whole 95% interval of net per $100 above zero). Between reviews it holds; the running weight is context only.

| Pricing model | Calls | Weeks | Running weight (95% CI) | Last review | Weight at review | Top-tier net per $100 at review | Gate |
|---|---|---|---|---|---|---|---|
| props-v1.3 | 371 | 2-2 | +0.115 (-0.692, +0.945) | none yet (first after week 8) | — | — | closed |
| props-v1.26 (current) | 430 | 3-4 | +0.321 (-0.211, +0.982) | none yet (first after week 8) | — | — | closed |
| props-v1.0 | 24 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.1 | 24 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.31 | 52 | 4-4 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.25 | 397 | 3-3 | +0.301 (-0.490, +0.906) | none yet (first after week 8) | — | — | closed |
| props-v1.7 | 23 | 2-2 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.18 | 290 | 3-3 | not estimated below 300 calls | none yet (first after week 8) | — | — | closed |
| props-v1.28 | 387 | 4-4 | +0.603 (-0.058, +1.209) | none yet (first after week 8) | — | — | closed |
| all models, pooled (context only) | 1998 | 2-4 | +0.156 (-0.237, +0.555) | none yet (first after week 8) | — | — | closed |

## Sleeper against DraftKings/FanDuel

Not the model: when Sleeper's line or price sits off the DraftKings/FanDuel consensus, the side the consensus favours, bet at Sleeper's price (reports/sleeper_vs_books.md).

| Discrepancy | Bets | Won | Win rate | Break-even | Net per $100 (95% CI) |
|---|---|---|---|---|---|
| line off | 8 | 5 | 62.5% | 60.1% | +8.3 (-21.4, +18.3) |
| price off | 2 | 2 | 100.0% | 58.6% | +70.8 (+nan, +nan) |
| both, pooled | 10 | 7 | 70.0% | 59.8% | +20.8 (-21.4, +31.4) |

10 graded discrepancies: no verdict yet: the rule needs 200+ bets and an interval above zero.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

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

556 settled calls, 269 winners (48.4%), net -4799 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 123 | 50.4% | 52.5% | -2.1% | -1067 |
| 55%-60% | 132 | 54.5% | 57.4% | -2.8% | -494 |
| 60%-65% | 80 | 55.0% | 62.0% | -7.0% | -222 |
| 65%-70% | 41 | 61.0% | 67.1% | -6.1% | +98 |
| 70%-80% | 27 | 48.1% | 73.1% | -25.0% | -451 |
| 80%-101% | 5 | 60.0% | 85.3% | -25.3% | +6 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 107 | 57.9% | 59.4% | 50.0% | +346 |
| MODERATE | 34 | 47.1% | 60.2% | 49.9% | -592 |
| LEAN | 80 | 58.8% | 53.9% | 49.5% | +693 |
| WEAK | 123 | 54.5% | 63.5% | 48.6% | +42 |
| UNTIERED | 212 | 36.3% | 39.8% | 43.0% | -5288 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 126 | 34.1% | 30.8% | -2305 |
| player_pass_yds | 32 | 50.0% | 59.6% | -347 |
| player_reception_yds | 157 | 51.0% | 57.9% | -1466 |
| player_receptions | 157 | 52.2% | 58.1% | -845 |
| player_rush_yds | 84 | 57.1% | 59.0% | +163 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 31 | 41.9% | 51.4% | -777 |
| no | 525 | 48.8% | 52.1% | -4022 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 3 | 66 | 47.0% | -1026 |
| 4 | 490 | 48.6% | -3773 |

### Closing line value

393 calls have both snapshots. The line moved toward the call 19.8% of the time (mean move +0.18).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

126 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

430 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.128 | (-0.986, +0.759) |
| logit(model) | +0.321 | (-0.211, +0.982) |
| logit(market) | -0.061 | (-1.589, +1.341) |

Leave-one-week-out log loss on the same calls: model 0.7032, market 0.6947, blend 0.7129 (430 calls).

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

16 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

52 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

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

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

120 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

290 settled yardage calls (receptions, receiving, rushing and QB passing yards) in this pricing model; the blend weight is not estimated below 300. The record is filling.

## Engine props-v1.28

495 settled calls, 245 winners (49.5%), net -3513 per $100 flat-staked.

### Calibration: does the model's probability mean anything?

| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |
|---|---|---|---|---|---|
| 50%-55% | 107 | 49.5% | 52.7% | -3.2% | -1203 |
| 55%-60% | 120 | 54.2% | 57.4% | -3.2% | -551 |
| 60%-65% | 71 | 54.9% | 62.1% | -7.2% | -377 |
| 65%-70% | 47 | 51.1% | 67.2% | -16.1% | -650 |
| 70%-80% | 22 | 72.7% | 73.0% | -0.3% | +551 |
| 80%-101% | 5 | 60.0% | 82.6% | -22.6% | -4 |

A bucket needs roughly 50 calls before its hit rate says anything; below that the difference is noise.

### Tier validity: is a big gap the book knowing something?

| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |
|---|---|---|---|---|---|
| STRONG | 94 | 46.8% | 59.7% | 50.1% | -1543 |
| MODERATE | 25 | 44.0% | 59.5% | 49.4% | -545 |
| LEAN | 73 | 54.8% | 53.5% | 49.0% | -4 |
| WEAK | 122 | 59.8% | 63.9% | 50.2% | +782 |
| UNTIERED | 181 | 42.5% | 40.6% | 43.8% | -2202 |

WEAK exists on the assumption the book is right when it disagrees sharply. If WEAK hits nearer the model column than the book column, that assumption is costing money and the tier rule should change.

### By market

| Market | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| player_anytime_td [anytime_td_v1] | 108 | 38.0% | 31.9% | -1002 |
| player_pass_yds | 27 | 40.7% | 58.5% | -738 |
| player_reception_yds | 141 | 51.1% | 58.1% | -1282 |
| player_receptions | 144 | 54.9% | 59.3% | -495 |
| player_rush_yds | 75 | 56.0% | 58.7% | +4 |

Receptions and receiving yards are the only backtested markets; rushing and anytime TD have no backtest at all, so their rows here are the first evidence either way.

### Priced with a Questionable teammate

| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |
|---|---|---|---|---|
| yes | 122 | 54.9% | 53.8% | +93 |
| no | 373 | 47.7% | 52.5% | -3606 |

Those rows assume the teammate played. When he sat, they graded against a line priced on the wrong roster; if 'yes' runs apart from 'no', that is the cost.

### By week

| Week | Calls | Hit rate | Net/$100 |
|---|---|---|---|
| 4 | 495 | 49.5% | -3513 |

### Closing line value

376 calls have both snapshots. The line moved toward the call 13.0% of the time (mean move +0.10).

Beating the close consistently is the signal that survives small samples. Winning without it is variance.

## Rushing yards: the board vs the market-carries shadow

0 settled backs' rushing lines carry the shadow so far; the comparison starts at 30.

### Worth a look

No marked line has been graded yet.

### Market blend (shadow: nothing priced from it)

108 settled anytime_td_v1 calls in this pricing model; the blend weight is not estimated below 300. The record is filling.

387 settled yardage calls (receptions, receiving, rushing and QB passing yards); books sleeper (an intercept per book and per market; the intercept row below is sleeper's).

| term | weight | 95% CI (game-clustered) |
|---|---|---|
| intercept | -0.226 | (-0.576, +0.108) |
| logit(model) | +0.603 | (-0.058, +1.209) |
| logit(market) | -0.392 | (-2.037, +1.286) |

No out-of-sample check yet: it holds out one week at a time and needs at least two (1 settled so far).

## Bet journal

23 bets logged: 22 graded, 1 void (push or did not play), 0 open. Kept apart from the model's record: these are the user's handicapped bets.

**Late-line value, the first number to watch:** 16 of 23 bets got a better number than the last line Sleeper showed before kickoff (70%; 1 tied); mean move your way +10.09 points. Beating the late line shows up in about 100-200 bets; the win rate needs far more. It is the last line the capture logged (usually a few hours out), not the true close.

| Bets | Won | Win rate | Break-even at these prices | Net per $100 staked |
|---|---|---|---|---|
| 22 | 12 | 55% | 55% | -3.7 |

A few dozen bets say little; about 100 is where the win rate starts to separate from luck.

**By angle** (chosen when the bet was logged):

| Angle | Bets | Graded | Won | Win rate | Break-even | Net per $100 | Beat the late line |
|---|---|---|---|---|---|---|---|
| injury redistribution | 2 | 2 | 0 | 0% | 59% | -100.0 | 1 of 2 |
| role change | 12 | 11 | 6 | 55% | 57% | -5.6 | 9 of 12 |
| teammate returning | 1 | 1 | 1 | 100% | 55% | +82.0 | 1 of 1 |
| other | 8 | 8 | 5 | 62% | 53% | +12.2 | 5 of 8 |

Each angle is its own small sample: read the late-line column first.

**Entries** (Sleeper Power Plays: every leg must hit):

| Logged | Legs | Stake | Pays (total) | Legs won / graded | Result | Net |
|---|---|---|---|---|---|---|
| week 4 (after kickoff) | Dalton Schultz under, Woody Marks under, Tyler Allgeier under, D'Andre Swift over, Luther Burden III over | $5 | $100 | 3 / 5 | lost | -5.00 |
| week 4 (after kickoff) | CeeDee Lamb yes, Ja'Marr Chase yes, Jaxon Smith-Njigba yes, Drake London yes | $5 | $103 | 1 / 4 | lost | -5.00 |
| week 4 (after kickoff) | Jahmyr Gibbs over, Amon-Ra St. Brown over, Chuba Hubbard over, Darren Waller over | $5 | $50 | 2 / 4 | lost | -5.00 |
| week 4 (after kickoff) | Ashton Jeanty under, Rashee Rice over, Courtland Sutton over, Mike Evans under | $5 | $47.5 | 1 / 3 | lost | -5.00 |
| week 4 (after kickoff) | Michael Penix Jr. over, Drake London over, Juwan Johnson over, Alvin Kamara over, Brian Robinson over, Tyler Shough over | $5 | $102.5 | 5 / 6 | lost | -5.00 |

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

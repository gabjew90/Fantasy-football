# Props scorecard — 2026

584 calls (626 priced lines graded, so 42 superseded by a later line).

**4 engine versions in the record (props-v1.1, props-v1.7, props-v1.3, props-v1.0); they are not pooled.** Pass `--pool` to pool them explicitly.

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

0 settled anytime_td_v1 calls in this engine version; the blend weight is not estimated below 300. The record is filling.

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

8 settled anytime_td_v1 calls in this engine version; the blend weight is not estimated below 300. The record is filling.

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

0 settled anytime_td_v1 calls in this engine version; the blend weight is not estimated below 300. The record is filling.

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

0 settled anytime_td_v1 calls in this engine version; the blend weight is not estimated below 300. The record is filling.

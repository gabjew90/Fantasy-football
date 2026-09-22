# The top-q player's passing-channel factor

Tune [2022, 2023], test [2024, 2025]. On top of the end-zone split. The team's top per-TD-share player's pass-channel shares are multiplied by the factor; the removed share goes to his teammates in the same channel, pro rata.

## Tune log loss, given offensive touchdowns

| factor | tune log loss |
|---|---|
| 0.7 | 0.32342 **chosen** |
| 0.8 | 0.32343 |
| 0.85 | 0.32348 |
| 0.9 | 0.32357 |
| 0.95 | 0.32369 |
| off | 0.32383 |

## Tune [2022, 2023]

| factor | given offensive TDs | end to end | vs off, end to end | top-q realised / expected |
|---|---|---|---|---|
| 0.7 | 0.3234 | 0.3505 | -0.0003 (-0.0008, +0.0003) not established | 1.013 |
| 0.8 | 0.3234 | 0.3505 | -0.0003 (-0.0007, +0.0001) not established | 0.992 |
| 0.85 | 0.3235 | 0.3506 | -0.0003 (-0.0005, +0.0000) not established | 0.978 |
| 0.9 | 0.3236 | 0.3506 | -0.0002 (-0.0004, -0.0000) better | 0.981 |
| 0.95 | 0.3237 | 0.3507 | -0.0001 (-0.0002, -0.0000) better | 0.964 |
| off | 0.3238 | 0.3508 |  | 0.926 |

### THE GATE: the top bins, end to end, each model binned by its own prediction

off:

| predicted P(score) | off: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.033 | 4671 |
| (0.05, 0.1] | 0.075 | 0.074 | 2426 |
| (0.1, 0.2] | 0.145 | 0.132 | 3633 |
| (0.2, 0.3] | 0.247 | 0.246 | 2110 |
| (0.3, 0.45] | 0.363 | 0.346 | 1529 |
| (0.45, 0.6] | 0.507 | 0.468 | 434 |
| (0.6, 1.0] | 0.633 | 0.706 | 34 |

chosen 0.7:

| predicted P(score) | chosen 0.7: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.032 | 4561 |
| (0.05, 0.1] | 0.075 | 0.073 | 2390 |
| (0.1, 0.2] | 0.145 | 0.128 | 3657 |
| (0.2, 0.3] | 0.247 | 0.243 | 2224 |
| (0.3, 0.45] | 0.361 | 0.352 | 1632 |
| (0.45, 0.6] | 0.501 | 0.496 | 359 |
| (0.6, 1.0] | 0.637 | 0.714 | 14 |


## Test [2024, 2025]

| factor | given offensive TDs | end to end | vs off, end to end | top-q realised / expected |
|---|---|---|---|---|
| 0.7 | 0.3302 | 0.3561 | -0.0004 (-0.0009, +0.0002) not established | 0.996 |
| 0.8 | 0.3303 | 0.3561 | -0.0004 (-0.0007, -0.0000) better | 0.993 |
| 0.85 | 0.3303 | 0.3561 | -0.0003 (-0.0006, -0.0000) better | 0.994 |
| 0.9 | 0.3304 | 0.3562 | -0.0002 (-0.0004, -0.0001) better | 0.990 |
| 0.95 | 0.3305 | 0.3563 | -0.0001 (-0.0002, -0.0000) better | 0.983 |
| off | 0.3307 | 0.3564 |  | 0.937 |

### THE GATE: the top bins, end to end, each model binned by its own prediction

off:

| predicted P(score) | off: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.031 | 4841 |
| (0.05, 0.1] | 0.074 | 0.076 | 2317 |
| (0.1, 0.2] | 0.146 | 0.146 | 3282 |
| (0.2, 0.3] | 0.246 | 0.243 | 2142 |
| (0.3, 0.45] | 0.364 | 0.360 | 1529 |
| (0.45, 0.6] | 0.508 | 0.497 | 606 |
| (0.6, 1.0] | 0.630 | 0.717 | 53 |

chosen 0.7:

| predicted P(score) | chosen 0.7: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.031 | 4731 |
| (0.05, 0.1] | 0.074 | 0.075 | 2276 |
| (0.1, 0.2] | 0.146 | 0.141 | 3302 |
| (0.2, 0.3] | 0.247 | 0.238 | 2268 |
| (0.3, 0.45] | 0.363 | 0.359 | 1638 |
| (0.45, 0.6] | 0.505 | 0.538 | 532 |
| (0.6, 1.0] | 0.639 | 0.783 | 23 |


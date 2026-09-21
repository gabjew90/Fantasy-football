# Role-conditional shares (NULL RESULT, not shipped -- DECISIONS #84)

Tune [2022, 2023], test [2024, 2025]. Base: anytime_td_v1.1 as shipped (props-v1.5/1.7). A player's share normally comes from every game he played; role-conditional takes it only from games in which he held his CURRENT pre-game depth-chart role (all games if he never held it). Roles: 'slot' exact (WR2 is not WR1); 'tier' QB1 / RB1 / WR1-3 / TE1 vs the rest; 'qb' the tier rule for QBs only.

## Tune log loss, given offensive touchdowns

| role | tune log loss |
|---|---|
| qb | 0.32584 **chosen** |
| off (v1.1) | 0.32604 |
| tier | 0.32841 |
| slot | 0.33329 |

## Tune [2022, 2023]

| model | given offensive TDs | end to end | vs off, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| off (v1.1) | 0.3260 | 0.3530 |  | 0.141 | 0.908 |
| qb | 0.3258 | 0.3528 | -0.0001 (-0.0006, +0.0006) not established | 0.141 | 0.908 |
| slot | 0.3333 | 0.3597 | +0.0068 (+0.0044, +0.0091) worse | 0.140 | 0.845 |
| tier | 0.3284 | 0.3553 | +0.0023 (+0.0008, +0.0039) worse | 0.141 | 0.877 |

Actual scoring rate 0.139.

### End to end: calibration, off (v1.1), binned by its own prediction

| predicted P(score) | off (v1.1): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.034 | 4269 |
| (0.05, 0.1] | 0.074 | 0.070 | 2873 |
| (0.1, 0.2] | 0.143 | 0.137 | 3679 |
| (0.2, 0.3] | 0.246 | 0.247 | 2130 |
| (0.3, 0.45] | 0.362 | 0.340 | 1372 |
| (0.45, 0.6] | 0.505 | 0.472 | 447 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |

### End to end: calibration, chosen (qb), binned by its own prediction

| predicted P(score) | chosen (qb): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.033 | 4302 |
| (0.05, 0.1] | 0.074 | 0.068 | 2833 |
| (0.1, 0.2] | 0.144 | 0.138 | 3674 |
| (0.2, 0.3] | 0.246 | 0.249 | 2133 |
| (0.3, 0.45] | 0.362 | 0.338 | 1372 |
| (0.45, 0.6] | 0.505 | 0.473 | 448 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |

### Given the team's offensive touchdowns: calibration, off (v1.1), binned by its own prediction

| predicted P(score) | off (v1.1): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.017 | 0.026 | 5519 |
| (0.05, 0.1] | 0.073 | 0.078 | 2641 |
| (0.1, 0.2] | 0.144 | 0.132 | 2999 |
| (0.2, 0.3] | 0.245 | 0.235 | 1688 |
| (0.3, 0.45] | 0.362 | 0.361 | 1301 |
| (0.45, 0.6] | 0.514 | 0.477 | 576 |
| (0.6, 1.0] | 0.696 | 0.680 | 316 |

### Given the team's offensive touchdowns: calibration, chosen (qb), binned by its own prediction

| predicted P(score) | chosen (qb): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.016 | 0.025 | 5557 |
| (0.05, 0.1] | 0.073 | 0.078 | 2600 |
| (0.1, 0.2] | 0.144 | 0.132 | 2989 |
| (0.2, 0.3] | 0.245 | 0.236 | 1693 |
| (0.3, 0.45] | 0.362 | 0.360 | 1307 |
| (0.45, 0.6] | 0.514 | 0.478 | 578 |
| (0.6, 1.0] | 0.696 | 0.680 | 316 |

### Starting quarterbacks

| model | n | predicted P(score) | actual | log loss |
|---|---|---|---|---|
| off (v1.1) | 1086 | 0.117 | 0.152 | 0.4006 |
| qb | 1086 | 0.120 | 0.152 | 0.3974 |
| slot | 1086 | 0.120 | 0.152 | 0.3973 |
| tier | 1086 | 0.120 | 0.152 | 0.3974 |

## Test [2024, 2025]

| model | given offensive TDs | end to end | vs off, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| off (v1.1) | 0.3308 | 0.3566 |  | 0.145 | 0.915 |
| qb | 0.3304 | 0.3562 | -0.0003 (-0.0009, +0.0005) not established | 0.145 | 0.916 |
| slot | 0.3370 | 0.3624 | +0.0059 (+0.0036, +0.0082) worse | 0.143 | 0.866 |
| tier | 0.3325 | 0.3582 | +0.0016 (-0.0001, +0.0035) not established | 0.144 | 0.878 |

Actual scoring rate 0.148.

### End to end: calibration, off (v1.1), binned by its own prediction

| predicted P(score) | off (v1.1): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.031 | 4354 |
| (0.05, 0.1] | 0.074 | 0.073 | 2939 |
| (0.1, 0.2] | 0.144 | 0.147 | 3314 |
| (0.2, 0.3] | 0.246 | 0.247 | 2109 |
| (0.3, 0.45] | 0.362 | 0.368 | 1357 |
| (0.45, 0.6] | 0.515 | 0.492 | 602 |
| (0.6, 1.0] | 0.637 | 0.644 | 90 |

### End to end: calibration, chosen (qb), binned by its own prediction

| predicted P(score) | chosen (qb): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.031 | 4415 |
| (0.05, 0.1] | 0.074 | 0.074 | 2838 |
| (0.1, 0.2] | 0.144 | 0.147 | 3316 |
| (0.2, 0.3] | 0.246 | 0.247 | 2129 |
| (0.3, 0.45] | 0.362 | 0.365 | 1352 |
| (0.45, 0.6] | 0.515 | 0.496 | 607 |
| (0.6, 1.0] | 0.637 | 0.644 | 90 |

### Given the team's offensive touchdowns: calibration, off (v1.1), binned by its own prediction

| predicted P(score) | off (v1.1): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.016 | 0.024 | 5490 |
| (0.05, 0.1] | 0.073 | 0.070 | 2576 |
| (0.1, 0.2] | 0.144 | 0.142 | 2886 |
| (0.2, 0.3] | 0.246 | 0.242 | 1621 |
| (0.3, 0.45] | 0.367 | 0.370 | 1360 |
| (0.45, 0.6] | 0.511 | 0.481 | 657 |
| (0.6, 1.0] | 0.706 | 0.660 | 432 |

### Given the team's offensive touchdowns: calibration, chosen (qb), binned by its own prediction

| predicted P(score) | chosen (qb): predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.016 | 0.024 | 5536 |
| (0.05, 0.1] | 0.073 | 0.069 | 2554 |
| (0.1, 0.2] | 0.145 | 0.143 | 2850 |
| (0.2, 0.3] | 0.245 | 0.240 | 1618 |
| (0.3, 0.45] | 0.366 | 0.371 | 1373 |
| (0.45, 0.6] | 0.511 | 0.479 | 655 |
| (0.6, 1.0] | 0.705 | 0.661 | 436 |

### Starting quarterbacks

| model | n | predicted P(score) | actual | log loss |
|---|---|---|---|---|
| off (v1.1) | 1088 | 0.123 | 0.148 | 0.3860 |
| qb | 1088 | 0.128 | 0.148 | 0.3824 |
| slot | 1088 | 0.128 | 0.148 | 0.3824 |
| tier | 1088 | 0.128 | 0.148 | 0.3824 |

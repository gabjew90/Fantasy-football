# The starting QB's share of his team's QB carries

Tune [2022, 2023], test [2016, 2017, 2018, 2019]. Base: anytime_td_v1.1 as shipped. From history the starter holds 0.70 of the QB-rush channel against 0.88 in reality (reports/td_diagnostics.md), because a fill-in backup's games-played denominator gives him a starter-sized share. Here the active QB highest on the pre-game depth chart gets a fixed share within qb_rush; the other players are scaled down, if needed, to fit under the cap.

## Tune log loss, given offensive touchdowns

| starter share | tune log loss |
|---|---|
| 0.92 | 0.32409 **chosen** |
| 0.88 | 0.32413 |
| 0.85 | 0.32425 |
| 0.95 | 0.32426 |
| 0.8 | 0.32454 |
| from history (v1.1) | 0.32604 |

## Tune [2022, 2023]

| starter share | given offensive TDs | end to end | vs v1.1, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| from history (v1.1) | 0.3260 | 0.3530 |  | 0.141 | 0.908 |
| 0.8 | 0.3245 | 0.3515 | -0.0015 (-0.0023, -0.0007) better | 0.141 | 0.908 |
| 0.85 | 0.3243 | 0.3512 | -0.0017 (-0.0026, -0.0008) better | 0.141 | 0.909 |
| 0.88 | 0.3241 | 0.3511 | -0.0018 (-0.0029, -0.0008) better | 0.141 | 0.909 |
| 0.92 | 0.3241 | 0.3511 | -0.0019 (-0.0031, -0.0007) better | 0.141 | 0.907 |
| 0.95 | 0.3243 | 0.3513 | -0.0017 (-0.0031, -0.0003) better | 0.141 | 0.910 |

Actual scoring rate 0.139.

### Starting quarterbacks

| starter share | n | predicted P(score) | actual | log loss | vs v1.1 |
|---|---|---|---|---|---|
| from history (v1.1) | 1086 | 0.117 | 0.152 | 0.4006 |  |
| 0.8 | 1086 | 0.132 | 0.152 | 0.3919 | -0.0086 (-0.0162, -0.0016) better |
| 0.85 | 1086 | 0.139 | 0.152 | 0.3907 | -0.0099 (-0.0182, -0.0020) better |
| 0.88 | 1086 | 0.144 | 0.152 | 0.3902 | -0.0104 (-0.0192, -0.0019) better |
| 0.92 | 1086 | 0.150 | 0.152 | 0.3898 | -0.0108 (-0.0203, -0.0015) better |
| 0.95 | 1086 | 0.154 | 0.152 | 0.3897 | -0.0109 (-0.0210, -0.0011) better |

### THE GATE: the top bins, end to end, each model binned by its own prediction

v1.1:

| predicted P(score) | v1.1: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.034 | 4269 |
| (0.05, 0.1] | 0.074 | 0.070 | 2873 |
| (0.1, 0.2] | 0.143 | 0.137 | 3679 |
| (0.2, 0.3] | 0.246 | 0.247 | 2130 |
| (0.3, 0.45] | 0.362 | 0.340 | 1372 |
| (0.45, 0.6] | 0.505 | 0.472 | 447 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |

starter share 0.92:

| predicted P(score) | starter share 0.92: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.032 | 4591 |
| (0.05, 0.1] | 0.075 | 0.071 | 2470 |
| (0.1, 0.2] | 0.144 | 0.135 | 3711 |
| (0.2, 0.3] | 0.245 | 0.248 | 2153 |
| (0.3, 0.45] | 0.363 | 0.343 | 1397 |
| (0.45, 0.6] | 0.505 | 0.475 | 451 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |


## Test [2016, 2017, 2018, 2019]

| starter share | given offensive TDs | end to end | vs v1.1, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| from history (v1.1) | 0.3111 | 0.3330 |  | 0.131 | 0.923 |
| 0.8 | 0.3107 | 0.3326 | -0.0004 (-0.0008, +0.0001) not established | 0.131 | 0.924 |
| 0.85 | 0.3106 | 0.3325 | -0.0004 (-0.0009, +0.0000) not established | 0.131 | 0.925 |
| 0.88 | 0.3106 | 0.3325 | -0.0005 (-0.0010, +0.0001) not established | 0.131 | 0.925 |
| 0.92 | 0.3107 | 0.3326 | -0.0004 (-0.0010, +0.0003) not established | 0.131 | 0.925 |
| 0.95 | 0.3108 | 0.3328 | -0.0002 (-0.0010, +0.0006) not established | 0.131 | 0.925 |

Actual scoring rate 0.129.

### Starting quarterbacks

| starter share | n | predicted P(score) | actual | log loss | vs v1.1 |
|---|---|---|---|---|---|
| from history (v1.1) | 2048 | 0.092 | 0.117 | 0.3426 |  |
| 0.8 | 2048 | 0.099 | 0.117 | 0.3416 | -0.0010 (-0.0054, +0.0032) not established |
| 0.85 | 2048 | 0.104 | 0.117 | 0.3407 | -0.0019 (-0.0067, +0.0024) not established |
| 0.88 | 2048 | 0.108 | 0.117 | 0.3403 | -0.0023 (-0.0073, +0.0022) not established |
| 0.92 | 2048 | 0.112 | 0.117 | 0.3400 | -0.0026 (-0.0079, +0.0022) not established |
| 0.95 | 2048 | 0.116 | 0.117 | 0.3399 | -0.0027 (-0.0083, +0.0025) not established |

### THE GATE: the top bins, end to end, each model binned by its own prediction

v1.1:

| predicted P(score) | v1.1: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.024 | 0.029 | 11030 |
| (0.05, 0.1] | 0.072 | 0.076 | 5393 |
| (0.1, 0.2] | 0.146 | 0.148 | 7032 |
| (0.2, 0.3] | 0.245 | 0.234 | 4448 |
| (0.3, 0.45] | 0.358 | 0.330 | 2711 |
| (0.45, 0.6] | 0.507 | 0.465 | 723 |
| (0.6, 1.0] | 0.647 | 0.528 | 127 |

starter share 0.92:

| predicted P(score) | starter share 0.92: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.029 | 11146 |
| (0.05, 0.1] | 0.073 | 0.076 | 5062 |
| (0.1, 0.2] | 0.146 | 0.146 | 7198 |
| (0.2, 0.3] | 0.245 | 0.234 | 4499 |
| (0.3, 0.45] | 0.359 | 0.331 | 2715 |
| (0.45, 0.6] | 0.507 | 0.464 | 724 |
| (0.6, 1.0] | 0.647 | 0.528 | 127 |


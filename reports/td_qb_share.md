# The starting QB's share of his team's QB carries

Tune [2022, 2023], test [2024, 2025]. Base: anytime_td_v1.1 as shipped. From history the starter holds 0.70 of the QB-rush channel against 0.88 in reality (reports/td_diagnostics.md), because a fill-in backup's games-played denominator gives him a starter-sized share. Here the active QB highest on the pre-game depth chart gets a fixed share within qb_rush; the other players are scaled down, if needed, to fit under the cap. The starter's QB-rush RATE (qb_beta, the channel weight) and his share WITHIN the channel multiply into the same probability, so they are tuned together.

## Tune log loss, given offensive touchdowns

| configuration | tune log loss |
|---|---|
| share 0.92, qb_beta 40 | 0.32409 **chosen** |
| share 0.92, qb_beta 20 | 0.32411 |
| share 0.88, qb_beta 40 | 0.32413 |
| share 0.88, qb_beta 20 | 0.32416 |
| share 0.85, qb_beta 40 | 0.32425 |
| share 0.95, qb_beta 40 | 0.32426 |
| share 0.95, qb_beta 20 | 0.32427 |
| share 0.85, qb_beta 20 | 0.32428 |
| share 0.92, qb_beta 80 | 0.32429 |
| share 0.88, qb_beta 80 | 0.32433 |
| share 0.85, qb_beta 80 | 0.32444 |
| share 0.95, qb_beta 80 | 0.32446 |
| share from history, qb_beta 40 (v1.1) | 0.32604 |
| share from history, qb_beta 20 | 0.32609 |
| share from history, qb_beta 80 | 0.32620 |

## Tune [2022, 2023]

| starter share | given offensive TDs | end to end | vs v1.1, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| share from history, qb_beta 20 | 0.3261 | 0.3530 | +0.0001 (-0.0001, +0.0003) not established | 0.141 | 0.908 |
| share 0.85, qb_beta 20 | 0.3243 | 0.3513 | -0.0017 (-0.0026, -0.0007) better | 0.141 | 0.907 |
| share 0.88, qb_beta 20 | 0.3242 | 0.3512 | -0.0018 (-0.0028, -0.0008) better | 0.141 | 0.907 |
| share 0.92, qb_beta 20 | 0.3241 | 0.3511 | -0.0019 (-0.0031, -0.0006) better | 0.141 | 0.903 |
| share 0.95, qb_beta 20 | 0.3243 | 0.3513 | -0.0017 (-0.0031, -0.0002) better | 0.141 | 0.906 |
| share from history, qb_beta 40 (v1.1) | 0.3260 | 0.3530 |  | 0.141 | 0.908 |
| share 0.85, qb_beta 40 | 0.3243 | 0.3512 | -0.0017 (-0.0026, -0.0008) better | 0.141 | 0.909 |
| share 0.88, qb_beta 40 | 0.3241 | 0.3511 | -0.0018 (-0.0029, -0.0008) better | 0.141 | 0.909 |
| share 0.92, qb_beta 40 | 0.3241 | 0.3511 | -0.0019 (-0.0031, -0.0007) better | 0.141 | 0.907 |
| share 0.95, qb_beta 40 | 0.3243 | 0.3513 | -0.0017 (-0.0031, -0.0003) better | 0.141 | 0.910 |
| share from history, qb_beta 80 | 0.3262 | 0.3531 | +0.0002 (-0.0000, +0.0003) not established | 0.141 | 0.907 |
| share 0.85, qb_beta 80 | 0.3244 | 0.3514 | -0.0016 (-0.0025, -0.0006) better | 0.141 | 0.907 |
| share 0.88, qb_beta 80 | 0.3243 | 0.3513 | -0.0017 (-0.0027, -0.0006) better | 0.141 | 0.907 |
| share 0.92, qb_beta 80 | 0.3243 | 0.3513 | -0.0017 (-0.0029, -0.0005) better | 0.141 | 0.907 |
| share 0.95, qb_beta 80 | 0.3245 | 0.3515 | -0.0015 (-0.0029, -0.0001) better | 0.141 | 0.907 |

Actual scoring rate 0.139.

### Starting quarterbacks

| starter share | n | predicted P(score) | actual | log loss | vs v1.1 |
|---|---|---|---|---|---|
| share from history, qb_beta 20 | 1086 | 0.117 | 0.152 | 0.3997 | -0.0009 (-0.0031, +0.0018) not established |
| share 0.85, qb_beta 20 | 1086 | 0.139 | 0.152 | 0.3896 | -0.0110 (-0.0196, -0.0028) better |
| share 0.88, qb_beta 20 | 1086 | 0.143 | 0.152 | 0.3891 | -0.0115 (-0.0206, -0.0027) better |
| share 0.92, qb_beta 20 | 1086 | 0.149 | 0.152 | 0.3887 | -0.0118 (-0.0215, -0.0023) better |
| share 0.95, qb_beta 20 | 1086 | 0.154 | 0.152 | 0.3886 | -0.0119 (-0.0221, -0.0018) better |
| share from history, qb_beta 40 (v1.1) | 1086 | 0.117 | 0.152 | 0.4006 |  |
| share 0.85, qb_beta 40 | 1086 | 0.139 | 0.152 | 0.3907 | -0.0099 (-0.0182, -0.0020) better |
| share 0.88, qb_beta 40 | 1086 | 0.144 | 0.152 | 0.3902 | -0.0104 (-0.0192, -0.0019) better |
| share 0.92, qb_beta 40 | 1086 | 0.150 | 0.152 | 0.3898 | -0.0108 (-0.0203, -0.0015) better |
| share 0.95, qb_beta 40 | 1086 | 0.154 | 0.152 | 0.3897 | -0.0109 (-0.0210, -0.0011) better |
| share from history, qb_beta 80 | 1086 | 0.117 | 0.152 | 0.4039 | +0.0033 (+0.0009, +0.0055) worse |
| share 0.85, qb_beta 80 | 1086 | 0.140 | 0.152 | 0.3941 | -0.0064 (-0.0149, +0.0016) not established |
| share 0.88, qb_beta 80 | 1086 | 0.144 | 0.152 | 0.3937 | -0.0069 (-0.0159, +0.0015) not established |
| share 0.92, qb_beta 80 | 1086 | 0.150 | 0.152 | 0.3933 | -0.0073 (-0.0170, +0.0018) not established |
| share 0.95, qb_beta 80 | 1086 | 0.155 | 0.152 | 0.3932 | -0.0073 (-0.0177, +0.0021) not established |

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

chosen: share 0.92, qb_beta 40:

| predicted P(score) | chosen: share 0.92, qb_beta 40: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.032 | 4591 |
| (0.05, 0.1] | 0.075 | 0.071 | 2470 |
| (0.1, 0.2] | 0.144 | 0.135 | 3711 |
| (0.2, 0.3] | 0.245 | 0.248 | 2153 |
| (0.3, 0.45] | 0.363 | 0.343 | 1397 |
| (0.45, 0.6] | 0.505 | 0.475 | 451 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |


## Test [2024, 2025]

| starter share | given offensive TDs | end to end | vs v1.1, end to end | mean predicted | top-q realised / expected |
|---|---|---|---|---|---|
| share from history, qb_beta 20 | 0.3309 | 0.3567 | +0.0001 (-0.0001, +0.0004) not established | 0.145 | 0.916 |
| share 0.85, qb_beta 20 | 0.3303 | 0.3561 | -0.0005 (-0.0015, +0.0006) not established | 0.144 | 0.911 |
| share 0.88, qb_beta 20 | 0.3303 | 0.3561 | -0.0005 (-0.0017, +0.0008) not established | 0.144 | 0.906 |
| share 0.92, qb_beta 20 | 0.3305 | 0.3563 | -0.0003 (-0.0018, +0.0012) not established | 0.144 | 0.909 |
| share 0.95, qb_beta 20 | 0.3309 | 0.3567 | +0.0001 (-0.0016, +0.0019) not established | 0.144 | 0.904 |
| share from history, qb_beta 40 (v1.1) | 0.3308 | 0.3566 |  | 0.145 | 0.915 |
| share 0.85, qb_beta 40 | 0.3302 | 0.3560 | -0.0006 (-0.0016, +0.0004) not established | 0.144 | 0.913 |
| share 0.88, qb_beta 40 | 0.3302 | 0.3560 | -0.0006 (-0.0017, +0.0006) not established | 0.144 | 0.913 |
| share 0.92, qb_beta 40 | 0.3304 | 0.3562 | -0.0004 (-0.0018, +0.0010) not established | 0.144 | 0.914 |
| share 0.95, qb_beta 40 | 0.3308 | 0.3566 | +0.0000 (-0.0017, +0.0017) not established | 0.144 | 0.910 |
| share from history, qb_beta 80 | 0.3310 | 0.3567 | +0.0002 (-0.0001, +0.0004) not established | 0.145 | 0.915 |
| share 0.85, qb_beta 80 | 0.3304 | 0.3561 | -0.0004 (-0.0014, +0.0006) not established | 0.144 | 0.915 |
| share 0.88, qb_beta 80 | 0.3304 | 0.3562 | -0.0004 (-0.0015, +0.0007) not established | 0.144 | 0.915 |
| share 0.92, qb_beta 80 | 0.3306 | 0.3563 | -0.0002 (-0.0016, +0.0011) not established | 0.144 | 0.915 |
| share 0.95, qb_beta 80 | 0.3310 | 0.3567 | +0.0002 (-0.0014, +0.0018) not established | 0.144 | 0.915 |

Actual scoring rate 0.148.

### Starting quarterbacks

| starter share | n | predicted P(score) | actual | log loss | vs v1.1 |
|---|---|---|---|---|---|
| share from history, qb_beta 20 | 1088 | 0.122 | 0.148 | 0.3845 | -0.0015 (-0.0041, +0.0014) not established |
| share 0.85, qb_beta 20 | 1088 | 0.146 | 0.148 | 0.3835 | -0.0025 (-0.0108, +0.0055) not established |
| share 0.88, qb_beta 20 | 1088 | 0.150 | 0.148 | 0.3834 | -0.0025 (-0.0112, +0.0060) not established |
| share 0.92, qb_beta 20 | 1088 | 0.156 | 0.148 | 0.3836 | -0.0023 (-0.0120, +0.0069) not established |
| share 0.95, qb_beta 20 | 1088 | 0.161 | 0.148 | 0.3839 | -0.0020 (-0.0120, +0.0079) not established |
| share from history, qb_beta 40 (v1.1) | 1088 | 0.123 | 0.148 | 0.3860 |  |
| share 0.85, qb_beta 40 | 1088 | 0.147 | 0.148 | 0.3852 | -0.0007 (-0.0084, +0.0067) not established |
| share 0.88, qb_beta 40 | 1088 | 0.152 | 0.148 | 0.3852 | -0.0007 (-0.0090, +0.0073) not established |
| share 0.92, qb_beta 40 | 1088 | 0.158 | 0.148 | 0.3855 | -0.0005 (-0.0093, +0.0084) not established |
| share 0.95, qb_beta 40 | 1088 | 0.163 | 0.148 | 0.3859 | -0.0001 (-0.0095, +0.0094) not established |
| share from history, qb_beta 80 | 1088 | 0.125 | 0.148 | 0.3895 | +0.0036 (+0.0009, +0.0061) worse |
| share 0.85, qb_beta 80 | 1088 | 0.150 | 0.148 | 0.3893 | +0.0033 (-0.0050, +0.0111) not established |
| share 0.88, qb_beta 80 | 1088 | 0.154 | 0.148 | 0.3894 | +0.0034 (-0.0053, +0.0116) not established |
| share 0.92, qb_beta 80 | 1088 | 0.161 | 0.148 | 0.3897 | +0.0038 (-0.0057, +0.0126) not established |
| share 0.95, qb_beta 80 | 1088 | 0.165 | 0.148 | 0.3902 | +0.0043 (-0.0058, +0.0135) not established |

### THE GATE: the top bins, end to end, each model binned by its own prediction

v1.1:

| predicted P(score) | v1.1: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.023 | 0.031 | 4354 |
| (0.05, 0.1] | 0.074 | 0.073 | 2939 |
| (0.1, 0.2] | 0.144 | 0.147 | 3314 |
| (0.2, 0.3] | 0.246 | 0.247 | 2109 |
| (0.3, 0.45] | 0.362 | 0.368 | 1357 |
| (0.45, 0.6] | 0.515 | 0.492 | 602 |
| (0.6, 1.0] | 0.637 | 0.644 | 90 |

chosen: share 0.92, qb_beta 40:

| predicted P(score) | chosen: share 0.92, qb_beta 40: predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.031 | 4740 |
| (0.05, 0.1] | 0.074 | 0.075 | 2393 |
| (0.1, 0.2] | 0.144 | 0.146 | 3389 |
| (0.2, 0.3] | 0.246 | 0.245 | 2179 |
| (0.3, 0.45] | 0.362 | 0.365 | 1360 |
| (0.45, 0.6] | 0.514 | 0.493 | 619 |
| (0.6, 1.0] | 0.637 | 0.644 | 90 |


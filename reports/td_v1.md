# anytime_td_v1: layer 2 and the end-to-end test

Tune [2022, 2023], test [2024, 2025]. Population: QB/RB/WR/TE on the game-day active list, 15022 player-games in test, 14.8% of whom scored. Active list covers 100.0% of snaps; 45.1% of actives hold a depth-chart slot. Five channels on raw counts; reallocation 'all'; kappa 5; moved-role weight 0.25. The engine gets the slot prior it has in production.

**Shipped configuration, scored as-is: slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf** -- the parameters in td_v1.V1, which score_game.py calls. Every rebuild number below comes out of that module.

## Where the touchdown mass goes (test, per team-game)

Summed per-touchdown share of the team's ACTIVE players, against the fraction of the team's offensive touchdowns that active players actually scored. Anything below the actual line is probability the model never gives to anyone who plays.

| | summed share of actives | of which: players with no history |
|---|---|---|
| actual: fraction of offensive TDs scored by actives | **0.997** | |
| engine | 0.932 | 0.022 |
| layer 2, no prior (previous spec) | 0.990 | 0.000 |
| layer 2, full slot prior | 0.990 | 0.025 |
| anytime_td_v1 as first shipped (props-v1.4) | 0.990 | 0.011 |
| shipped | 0.989 | 0.011 |

## Allocation, given the team's offensive touchdowns (test)

| model | log loss | vs | change (95% CI, game-clustered) |
|---|---|---|---|
| Engine (pass/rush, inside-10, slot prior) | 0.3347 | | baseline |
| previous spec: no prior, fixed share | 0.3369 | engine | +0.0022 (-0.0014, +0.0061) not established |
| full slot prior, fixed share | 0.3334 | previous spec | -0.0035 (-0.0068, -0.0006) better |
| v1 as first shipped (slot x0.4) | 0.3321 | full slot prior | -0.0013 (-0.0018, -0.0008) better |
| shipped | 0.3307 | v1 as first shipped | -0.0014 (-0.0030, +0.0004) not established |

Shipped vs engine directly: -0.0040 (-0.0066, -0.0014) better.

### Calibration given offensive touchdowns

| predicted P(score) | full slot, fixed share: predicted | shipped: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.025 | 0.015 | 0.026 | 5846 |
| (0.05, 0.1] | 0.080 | 0.073 | 0.069 | 2204 |
| (0.1, 0.2] | 0.143 | 0.145 | 0.141 | 2752 |
| (0.2, 0.3] | 0.237 | 0.247 | 0.242 | 1670 |
| (0.3, 0.45] | 0.356 | 0.367 | 0.358 | 1451 |
| (0.45, 0.6] | 0.498 | 0.514 | 0.489 | 673 |
| (0.6, 1.0] | 0.677 | 0.692 | 0.655 | 426 |

### No-history players

| model | mean predicted | actual rate | n |
|---|---|---|---|
| engine (full slot prior) | 0.089 | 0.035 | 572 |
| layer 2, full slot prior | 0.099 | 0.035 | 572 |
| layer 2, shipped | 0.045 | 0.035 | 572 |

## END TO END: what would be deployed (test)

Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. v1 = layer 1 frozen (Binomial(10), gamma 0.25) x layer 2 (slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf).

| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine (anytime_td_v0 structure) | 0.3608 | 0.1091 | 0.135 | baseline |
| v1 as first shipped (props-v1.4) | 0.3577 | 0.1085 | 0.145 | -0.0031 (-0.0054, -0.0009) better |
| v1 shipped | 0.3564 | 0.1081 | 0.145 | -0.0044 (-0.0069, -0.0019) better |

Shipped vs v1 as first shipped: -0.0013 (-0.0029, +0.0004) not established.

Actual scoring rate 0.148.

Cross terms -- each layer alone, the other as the engine has it:

| model | log loss | mean predicted | vs engine |
|---|---|---|---|
| layer 1 frozen, engine allocation | 0.3605 | 0.138 | -0.0004 (-0.0006, -0.0001) better |
| engine count model, v1 allocation | 0.3567 | 0.142 | -0.0041 (-0.0065, -0.0016) better |

### Calibration, end to end

| predicted P(score) | engine: predicted | v1: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.034 | 0.020 | 0.031 | 4841 |
| (0.05, 0.1] | 0.073 | 0.074 | 0.076 | 2317 |
| (0.1, 0.2] | 0.126 | 0.146 | 0.146 | 3282 |
| (0.2, 0.3] | 0.222 | 0.246 | 0.243 | 2142 |
| (0.3, 0.45] | 0.327 | 0.364 | 0.360 | 1529 |
| (0.45, 0.6] | 0.458 | 0.508 | 0.497 | 606 |
| (0.6, 1.0] | 0.560 | 0.630 | 0.717 | 53 |

The 0.2-0.3 band is where most priced anytime lines sit.

| position | engine | v1 | n |
|---|---|---|---|
| QB | 0.2559 | 0.2438 | 2211 |
| RB | 0.4129 | 0.4089 | 3713 |
| TE | 0.3094 | 0.3095 | 3446 |
| WR | 0.3990 | 0.3946 | 5652 |

### Starting quarterbacks, end to end

| population | n | actual rate | engine: predicted / log loss | v1 as first shipped: predicted / log loss | shipped: predicted / log loss |
|---|---|---|---|---|---|
| all starting QBs | 1088 | 0.148 | 0.096 / 0.4074 | 0.131 / 0.4000 | 0.158 / 0.3855 |
| QB new to his team as a starter | 67 | 0.104 | 0.041 / 0.3149 | 0.068 / 0.3480 | 0.134 / 0.3094 |

## The Beta share on the top bins (diagnostic, not used)

A concentration tuned on aggregate log loss can return 'no effect' even if it fixes the top bins, which are 7% of rows. Rows are binned by the SHIPPED fixed-share prediction, so every column describes the same players. c -> infinity is the fixed share.

### End to end

| predicted P(score) | c=40: predicted | c=20: predicted | c=10: predicted | fixed share: predicted | actual rate | n |
|---|---|---|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.019 | 0.019 | 0.020 | 0.031 | 4841 |
| (0.05, 0.1] | 0.073 | 0.071 | 0.068 | 0.074 | 0.076 | 2317 |
| (0.1, 0.2] | 0.143 | 0.140 | 0.135 | 0.146 | 0.146 | 3282 |
| (0.2, 0.3] | 0.240 | 0.236 | 0.228 | 0.246 | 0.243 | 2142 |
| (0.3, 0.45] | 0.357 | 0.351 | 0.340 | 0.364 | 0.360 | 1529 |
| (0.45, 0.6] | 0.500 | 0.492 | 0.478 | 0.508 | 0.497 | 606 |
| (0.6, 1.0] | 0.620 | 0.611 | 0.594 | 0.630 | 0.717 | 53 |

### Given the team's offensive touchdowns

| predicted P(score) | c=40: predicted | c=20: predicted | c=10: predicted | fixed share: predicted | actual rate | n |
|---|---|---|---|---|---|---|
| (-0.001, 0.05] | 0.015 | 0.014 | 0.014 | 0.015 | 0.026 | 5846 |
| (0.05, 0.1] | 0.072 | 0.071 | 0.069 | 0.073 | 0.069 | 2204 |
| (0.1, 0.2] | 0.143 | 0.141 | 0.137 | 0.145 | 0.141 | 2752 |
| (0.2, 0.3] | 0.242 | 0.237 | 0.229 | 0.247 | 0.242 | 1670 |
| (0.3, 0.45] | 0.359 | 0.352 | 0.339 | 0.367 | 0.358 | 1451 |
| (0.45, 0.6] | 0.502 | 0.492 | 0.473 | 0.514 | 0.489 | 673 |
| (0.6, 1.0] | 0.676 | 0.662 | 0.636 | 0.692 | 0.655 | 426 |

| share | log loss, all | log loss, rows priced above 0.45 end to end | mean predicted there |
|---|---|---|---|
| c=40 | 0.3565 | 0.6809 | 0.510 |
| c=20 | 0.3567 | 0.6815 | 0.502 |
| c=10 | 0.3572 | 0.6831 | 0.487 |
| fixed | 0.3564 | 0.6806 | 0.518 |
| actual | | | 0.514 (n 659) |

## Tuning (tune log loss, given offensive touchdowns)

| configuration | tune log loss |
|---|---|
| slot|x0.4|m0.25|qs0.92|cap0.99|qb40|c40 | 0.3238 |
| slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf | 0.3238 |
| slot|x0.4|m0.25|qs0.92|cap0.99|qb40|c20 | 0.3239 |
| slot|x0.4|m0.25|qs0.92|cap0.99|qb40|c10 | 0.3243 |
| slot|x0.4|m0.25|cap0.99|qb40|cinf | 0.3257 |
| slot|x0.4|m0.25|cap0.99|qbteam|cinf | 0.3262 |
| slot|x1|m0.25|cap0.99|qbteam|cinf | 0.3270 |
| none|x1|m0.5|cap0.99|qbteam|cinf | 0.3314 |

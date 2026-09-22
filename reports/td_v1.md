# anytime_td_v1: layer 2 and the end-to-end test

*Scored under the six channels of props-v1.12 (end-zone split), with the slot pull of props-v1.13. 'v1.0 settings (current channels)' is v1.0's allocation re-run on these channels, not the literal props-v1.4 model.*

Tune [2022, 2023], test [2024, 2025]. Population: QB/RB/WR/TE on the game-day active list, 15022 player-games in test, 14.8% of whom scored. Active list covers 100.0% of snaps; 45.1% of actives hold a depth-chart slot. Five channels on raw counts; reallocation 'all'; kappa 5; moved-role weight 0.25. The engine gets the slot prior it has in production.

**Shipped configuration, scored as-is: slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|cinf** -- the parameters in td_v1.V1, which score_game.py calls. Every rebuild number below comes out of that module.

## Where the touchdown mass goes (test, per team-game)

Summed per-touchdown share of the team's ACTIVE players, against the fraction of the team's offensive touchdowns that active players actually scored. Anything below the actual line is probability the model never gives to anyone who plays.

| | summed share of actives | of which: players with no history |
|---|---|---|
| actual: fraction of offensive TDs scored by actives | **0.997** | |
| engine | 0.932 | 0.022 |
| layer 2, no prior (previous spec) | 0.990 | 0.000 |
| layer 2, full slot prior | 0.990 | 0.025 |
| v1.0 settings (current channels) | 0.990 | 0.011 |
| shipped | 0.990 | 0.011 |

## Allocation, given the team's offensive touchdowns (test)

| model | log loss | vs | change (95% CI, game-clustered) |
|---|---|---|---|
| Engine (pass/rush, inside-10, slot prior) | 0.3347 | | baseline |
| previous spec: no prior, fixed share | 0.3369 | engine | +0.0022 (-0.0014, +0.0061) not established |
| full slot prior, fixed share | 0.3334 | previous spec | -0.0035 (-0.0068, -0.0006) better |
| v1.0 settings (current channels) (slot x0.4) | 0.3321 | full slot prior | -0.0013 (-0.0018, -0.0008) better |
| shipped | 0.3244 | v1.0 settings (current channels) | -0.0076 (-0.0102, -0.0051) better |

Shipped vs engine directly: -0.0102 (-0.0134, -0.0072) better.

### Calibration given offensive touchdowns

| predicted P(score) | full slot, fixed share: predicted | shipped: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.022 | 0.022 | 0.021 | 5172 |
| (0.05, 0.1] | 0.072 | 0.072 | 0.064 | 2626 |
| (0.1, 0.2] | 0.139 | 0.145 | 0.129 | 3022 |
| (0.2, 0.3] | 0.241 | 0.246 | 0.261 | 1788 |
| (0.3, 0.45] | 0.368 | 0.366 | 0.366 | 1447 |
| (0.45, 0.6] | 0.521 | 0.514 | 0.522 | 632 |
| (0.6, 1.0] | 0.694 | 0.687 | 0.681 | 335 |

### No-history players

| model | mean predicted | actual rate | n |
|---|---|---|---|
| engine (full slot prior) | 0.089 | 0.035 | 572 |
| layer 2, full slot prior | 0.099 | 0.035 | 572 |
| layer 2, shipped | 0.043 | 0.035 | 572 |

## END TO END: what would be deployed (test)

Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. v1 = layer 1 frozen (Binomial(10), gamma 0.25) x layer 2 (slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|cinf).

| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine (anytime_td_v0 structure) | 0.3608 | 0.1091 | 0.135 | baseline |
| v1.0 settings (current channels) | 0.3577 | 0.1085 | 0.145 | -0.0031 (-0.0054, -0.0009) better |
| v1 shipped | 0.3504 | 0.1076 | 0.147 | -0.0105 (-0.0136, -0.0076) better |

Shipped vs v1.0 settings (current channels): -0.0073 (-0.0098, -0.0049) better.

Actual scoring rate 0.148.

Cross terms -- each layer alone, the other as the engine has it:

| model | log loss | mean predicted | vs engine |
|---|---|---|---|
| layer 1 frozen, engine allocation | 0.3605 | 0.138 | -0.0004 (-0.0006, -0.0001) better |
| engine count model, v1 allocation | 0.3508 | 0.144 | -0.0100 (-0.0131, -0.0072) better |

### Calibration, end to end

| predicted P(score) | engine: predicted | v1: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.032 | 0.030 | 0.026 | 4493 |
| (0.05, 0.1] | 0.064 | 0.073 | 0.070 | 2638 |
| (0.1, 0.2] | 0.126 | 0.146 | 0.142 | 3671 |
| (0.2, 0.3] | 0.227 | 0.245 | 0.251 | 2262 |
| (0.3, 0.45] | 0.344 | 0.362 | 0.380 | 1434 |
| (0.45, 0.6] | 0.478 | 0.504 | 0.529 | 503 |
| (0.6, 1.0] | 0.579 | 0.633 | 0.905 | 21 |

The 0.2-0.3 band is where most priced anytime lines sit.

| position | engine | v1 | n |
|---|---|---|---|
| QB | 0.2559 | 0.2412 | 2211 |
| RB | 0.4129 | 0.4066 | 3713 |
| TE | 0.3094 | 0.3036 | 3446 |
| WR | 0.3990 | 0.3847 | 5652 |

### Starting quarterbacks, end to end

| population | n | actual rate | engine: predicted / log loss | v1.0 settings (current channels): predicted / log loss | shipped: predicted / log loss |
|---|---|---|---|---|---|
| all starting QBs | 1088 | 0.148 | 0.096 / 0.4074 | 0.131 / 0.4000 | 0.159 / 0.3859 |
| QB new to his team as a starter | 67 | 0.104 | 0.041 / 0.3149 | 0.068 / 0.3480 | 0.142 / 0.3183 |

## The Beta share on the top bins (diagnostic, not used)

A concentration tuned on aggregate log loss can return 'no effect' even if it fixes the top bins, which are 7% of rows. Rows are binned by the SHIPPED fixed-share prediction, so every column describes the same players. c -> infinity is the fixed share.

### End to end

| predicted P(score) | c=40: predicted | c=20: predicted | c=10: predicted | fixed share: predicted | actual rate | n |
|---|---|---|---|---|---|---|
| (-0.001, 0.05] | 0.029 | 0.028 | 0.027 | 0.030 | 0.026 | 4493 |
| (0.05, 0.1] | 0.072 | 0.070 | 0.067 | 0.073 | 0.070 | 2638 |
| (0.1, 0.2] | 0.142 | 0.140 | 0.134 | 0.146 | 0.142 | 3671 |
| (0.2, 0.3] | 0.240 | 0.235 | 0.227 | 0.245 | 0.251 | 2262 |
| (0.3, 0.45] | 0.356 | 0.350 | 0.339 | 0.362 | 0.380 | 1434 |
| (0.45, 0.6] | 0.496 | 0.488 | 0.473 | 0.504 | 0.529 | 503 |
| (0.6, 1.0] | 0.622 | 0.613 | 0.596 | 0.633 | 0.905 | 21 |

### Given the team's offensive touchdowns

| predicted P(score) | c=40: predicted | c=20: predicted | c=10: predicted | fixed share: predicted | actual rate | n |
|---|---|---|---|---|---|---|
| (-0.001, 0.05] | 0.022 | 0.021 | 0.021 | 0.022 | 0.021 | 5172 |
| (0.05, 0.1] | 0.071 | 0.070 | 0.067 | 0.072 | 0.064 | 2626 |
| (0.1, 0.2] | 0.142 | 0.140 | 0.136 | 0.145 | 0.129 | 3022 |
| (0.2, 0.3] | 0.241 | 0.237 | 0.229 | 0.246 | 0.261 | 1788 |
| (0.3, 0.45] | 0.358 | 0.350 | 0.336 | 0.366 | 0.366 | 1447 |
| (0.45, 0.6] | 0.502 | 0.491 | 0.471 | 0.514 | 0.522 | 632 |
| (0.6, 1.0] | 0.671 | 0.656 | 0.629 | 0.687 | 0.681 | 335 |

| share | log loss, all | log loss, rows priced above 0.45 end to end | mean predicted there |
|---|---|---|---|
| c=40 | 0.3505 | 0.6828 | 0.501 |
| c=20 | 0.3506 | 0.6846 | 0.493 |
| c=10 | 0.3511 | 0.6884 | 0.478 |
| fixed | 0.3504 | 0.6812 | 0.510 |
| actual | | | 0.544 (n 524) |

## Tuning (tune log loss, given offensive touchdowns)

| configuration | tune log loss |
|---|---|
| slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|c40 | 0.3190 |
| slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|cinf | 0.3191 |
| slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|c20 | 0.3191 |
| slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|c10 | 0.3195 |
| slot|x0.4|m0.25|cap0.99|qb40|cinf | 0.3257 |
| slot|x0.4|m0.25|cap0.99|qbteam|cinf | 0.3262 |
| slot|x1|m0.25|cap0.99|qbteam|cinf | 0.3270 |
| none|x1|m0.5|cap0.99|qbteam|cinf | 0.3314 |

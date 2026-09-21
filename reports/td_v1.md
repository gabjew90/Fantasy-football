# Layer 2 and the end-to-end test

Tune [2022, 2023], test [2024, 2025]. Population: QB/RB/WR/TE on the game-day active list, 15022 player-games in test, 14.8% of whom scored. Active list covers 100.0% of snaps; 45.1% of actives hold a depth-chart slot. Five channels on raw counts; reallocation 'all'; kappa 5; moved-role weight 0.25. The engine gets the slot prior it has in production.

**Shipped configuration, scored as-is: slot|x0.4|m0.25|cinf** -- the parameters in td_v1.V1, which score_game.py calls. Every rebuild number below comes out of that module.

## Where the touchdown mass goes (test, per team-game)

Summed per-touchdown share of the team's ACTIVE players, against the fraction of the team's offensive touchdowns that active players actually scored. Anything below the actual line is probability the model never gives to anyone who plays.

| | summed share of actives | of which: players with no history |
|---|---|---|
| actual: fraction of offensive TDs scored by actives | **0.997** | |
| engine | 0.932 | 0.022 |
| layer 2, no prior (previous spec) | 0.990 | 0.000 |
| layer 2, full slot prior | 0.990 | 0.024 |
| layer 2, chosen slot scale | 0.990 | 0.011 |

## Allocation, given the team's offensive touchdowns (test)

| model | log loss | vs | change (95% CI, game-clustered) |
|---|---|---|---|
| Engine (pass/rush, inside-10, slot prior) | 0.3347 | | baseline |
| previous spec: no prior, fixed share | 0.3364 | engine | +0.0018 (-0.0018, +0.0056) not established |
| full slot prior, fixed share | 0.3331 | previous spec | -0.0034 (-0.0067, -0.0005) better |
| chosen slot scale, fixed share | 0.3318 | full slot prior | -0.0013 (-0.0018, -0.0008) better |

Shipped vs engine directly: -0.0029 (-0.0052, -0.0006) better.

### Calibration given offensive touchdowns

| predicted P(score) | full slot, fixed share: predicted | chosen: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.018 | 0.016 | 0.024 | 5368 |
| (0.05, 0.1] | 0.078 | 0.073 | 0.068 | 2581 |
| (0.1, 0.2] | 0.144 | 0.144 | 0.139 | 2999 |
| (0.2, 0.3] | 0.243 | 0.246 | 0.247 | 1643 |
| (0.3, 0.45] | 0.363 | 0.367 | 0.370 | 1379 |
| (0.45, 0.6] | 0.506 | 0.512 | 0.480 | 637 |
| (0.6, 1.0] | 0.701 | 0.707 | 0.663 | 415 |

### No-history players

| model | mean predicted | actual rate | n |
|---|---|---|---|
| engine (full slot prior) | 0.089 | 0.035 | 572 |
| layer 2, full slot prior | 0.099 | 0.035 | 572 |
| layer 2, chosen | 0.045 | 0.035 | 572 |

## END TO END: what would be deployed (test)

Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. v1 = layer 1 frozen (Binomial(10), gamma 0.25) x layer 2 (slot|x0.4|m0.25|cinf).

| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine (anytime_td_v0 structure) | 0.3608 | 0.1091 | 0.135 | baseline |
| v1 | 0.3575 | 0.1085 | 0.145 | -0.0034 (-0.0056, -0.0012) better |

Actual scoring rate 0.148.

Cross terms -- each layer alone, the other as the engine has it:

| model | log loss | mean predicted | vs engine |
|---|---|---|---|
| layer 1 frozen, engine allocation | 0.3605 | 0.138 | -0.0004 (-0.0006, -0.0001) better |
| engine count model, v1 allocation | 0.3578 | 0.142 | -0.0030 (-0.0053, -0.0009) better |

### Calibration, end to end

| predicted P(score) | engine: predicted | v1: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.029 | 0.022 | 0.032 | 4189 |
| (0.05, 0.1] | 0.072 | 0.074 | 0.070 | 2945 |
| (0.1, 0.2] | 0.129 | 0.144 | 0.146 | 3517 |
| (0.2, 0.3] | 0.230 | 0.247 | 0.254 | 2115 |
| (0.3, 0.45] | 0.332 | 0.362 | 0.365 | 1326 |
| (0.45, 0.6] | 0.464 | 0.516 | 0.487 | 591 |
| (0.6, 1.0] | 0.549 | 0.636 | 0.634 | 82 |

The 0.2-0.3 band is where most priced anytime lines sit.

| position | engine | v1 | n |
|---|---|---|---|
| QB | 0.2559 | 0.2515 | 2211 |
| RB | 0.4129 | 0.4106 | 3713 |
| TE | 0.3094 | 0.3070 | 3446 |
| WR | 0.3990 | 0.3948 | 5652 |

## Tuning (tune log loss, given offensive touchdowns)

| configuration | tune log loss |
|---|---|
| slot|x0.4|m0.25|cinf | 0.3265 **chosen** |
| slot|x1|m0.25|cinf | 0.3273 |
| none|x1|m0.5|cinf | 0.3317 |

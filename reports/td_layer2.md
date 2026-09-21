# Layer 2 and the end-to-end test

Tune [2022, 2023], test [2024, 2025]. Population: QB/RB/WR/TE on the game-day active list, 15022 player-games in test, 14.8% of whom scored. Active list covers 100.0% of snaps; 45.1% of actives hold a depth-chart slot. Five channels on raw counts; reallocation 'all'; kappa 5; moved-role weight 0.25. The engine gets the slot prior it has in production.

Chosen on tune: **slot|x0.4|m0.25|c40** (slot-prior scale x, Beta concentration c).

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
| + Beta share (chosen: slot|x0.4|m0.25|c40) | 0.3317 | fixed share | -0.0000 (-0.0001, +0.0001) not established |

Chosen vs engine directly: -0.0029 (-0.0053, -0.0007) better.

### Calibration given offensive touchdowns

| predicted P(score) | full slot, fixed share: predicted | chosen: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.019 | 0.016 | 0.025 | 5420 |
| (0.05, 0.1] | 0.079 | 0.073 | 0.068 | 2587 |
| (0.1, 0.2] | 0.146 | 0.144 | 0.142 | 3037 |
| (0.2, 0.3] | 0.249 | 0.246 | 0.253 | 1627 |
| (0.3, 0.45] | 0.371 | 0.367 | 0.376 | 1369 |
| (0.45, 0.6] | 0.517 | 0.511 | 0.489 | 595 |
| (0.6, 1.0] | 0.708 | 0.699 | 0.672 | 387 |

### No-history players

| model | mean predicted | actual rate | n |
|---|---|---|---|
| engine (full slot prior) | 0.089 | 0.035 | 572 |
| layer 2, full slot prior | 0.099 | 0.035 | 572 |
| layer 2, chosen | 0.044 | 0.035 | 572 |

## END TO END: what would be deployed (test)

Engine = implied points x league offensive TDs/point, linear, Poisson; per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. v1 = layer 1 frozen (Binomial(10), gamma 0.25) x layer 2 (slot|x0.4|m0.25|c40).

| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine (anytime_td_v0 structure) | 0.3608 | 0.1091 | 0.135 | baseline |
| v1 | 0.3576 | 0.1085 | 0.142 | -0.0032 (-0.0055, -0.0011) better |

Actual scoring rate 0.148.

Cross terms -- each layer alone, the other as the engine has it:

| model | log loss | mean predicted | vs engine |
|---|---|---|---|
| layer 1 frozen, engine allocation | 0.3605 | 0.138 | -0.0004 (-0.0006, -0.0001) better |
| engine count model, v1 allocation | 0.3580 | 0.139 | -0.0028 (-0.0050, -0.0007) better |

### Calibration, end to end

| predicted P(score) | engine: predicted | v1: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.029 | 0.022 | 0.032 | 4266 |
| (0.05, 0.1] | 0.073 | 0.074 | 0.071 | 2981 |
| (0.1, 0.2] | 0.132 | 0.144 | 0.149 | 3504 |
| (0.2, 0.3] | 0.234 | 0.246 | 0.261 | 2111 |
| (0.3, 0.45] | 0.338 | 0.363 | 0.367 | 1275 |
| (0.45, 0.6] | 0.471 | 0.516 | 0.502 | 566 |
| (0.6, 1.0] | 0.556 | 0.636 | 0.645 | 62 |

The 0.2-0.3 band is where most priced anytime lines sit.

| position | engine | v1 | n |
|---|---|---|---|
| QB | 0.2559 | 0.2511 | 2211 |
| RB | 0.4129 | 0.4104 | 3713 |
| TE | 0.3094 | 0.3073 | 3446 |
| WR | 0.3990 | 0.3952 | 5652 |

## Tuning (tune log loss, given offensive touchdowns)

| configuration | tune log loss |
|---|---|
| slot|x0.4|m0.25|c40 | 0.3264 **chosen** |
| slot|x0.4|m0.25|c80 | 0.3264 |
| slot|x0.4|m0.25|cinf | 0.3265 |
| slot|x0.4|m0.25|c20 | 0.3265 |
| slot|x0.6|m0.25|c40 | 0.3266 |
| slot|x0.6|m0.25|c80 | 0.3266 |
| slot|x0.6|m0.25|cinf | 0.3266 |
| slot|x0.6|m0.25|c20 | 0.3266 |
| slot|x0.4|m0.25|c10 | 0.3269 |
| slot|x0.6|m0.25|c10 | 0.3270 |
| slot|x1|m0.25|c40 | 0.3273 |
| slot|x1|m0.25|c80 | 0.3273 |
| slot|x1|m0.25|cinf | 0.3273 |
| slot|x1|m0.25|c20 | 0.3273 |
| slot|x1|m0.25|c10 | 0.3277 |
| slot|x0.4|m0.25|c5 | 0.3281 |
| slot|x0.6|m0.25|c5 | 0.3283 |
| slot|x1|m0.25|c5 | 0.3289 |
| none|x1|m0.5|cinf | 0.3317 |

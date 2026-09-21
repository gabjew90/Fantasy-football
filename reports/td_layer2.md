# Layer 2 and the end-to-end test

Tune [2022, 2023], test [2024, 2025]. Population: QB/RB/WR/TE on the game-day active list, 15022 player-games in test, 14.8% of whom scored. Active list covers 100.0% of snaps; 45.1% of actives hold a depth-chart slot. Reallocation 'all', kappa 5. The engine is given the slot prior it has in production, so neither side wins by the other lacking it.

## Allocation, given the team's offensive touchdowns (test)

| step | log loss | change vs row above (95% CI, game-clustered) |
|---|---|---|
| Engine today (pass/rush, inside-10, slot prior) | 0.3347 | baseline |
| five channels, raw counts, no prior (previous spec) | 0.3364 | vs engine: +0.0018 (-0.0018, +0.0056) not established |
| + slot prior for players with no history | 0.3333 | vs counts|none|0.5: -0.0031 (-0.0064, -0.0002) better |
|   alternative: + expected-touchdown weighting (on top of the slot prior) | 0.3359 | vs counts|slot|0.5: +0.0026 (+0.0005, +0.0047) worse |
| + moved-role weight tuned (chosen on tune: counts|slot|0.25) | 0.3331 | vs counts|slot|0.5: -0.0002 (-0.0005, +0.0000) not established |

Best on tune vs engine directly: -0.0016 (-0.0039, +0.0006) not established.

### The no-history players the review flagged

| model | mean predicted | actual rate | log loss | n |
|---|---|---|---|---|
| engine (slot prior) | 0.089 | 0.035 | 0.1587 | 572 |
| previous spec (no share) | 0.000 | 0.035 | 0.2425 | 572 |
| slot prior | 0.098 | 0.035 | 0.1634 | 572 |

### Calibration, best configuration, given offensive touchdowns

| predicted P(score) | previous spec: predicted | best: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.016 | 0.016 | 0.025 | 5168 |
| (0.05, 0.1] | 0.071 | 0.074 | 0.067 | 2616 |
| (0.1, 0.2] | 0.138 | 0.144 | 0.131 | 3186 |
| (0.2, 0.3] | 0.247 | 0.246 | 0.251 | 1664 |
| (0.3, 0.45] | 0.372 | 0.367 | 0.377 | 1373 |
| (0.45, 0.6] | 0.517 | 0.512 | 0.482 | 610 |
| (0.6, 1.0] | 0.711 | 0.704 | 0.662 | 405 |

## END TO END: what would be deployed (test)

Unconditional. Engine = implied points x league offensive TDs/point, linear, Poisson, per-TD share from pass/rush + inside-10 usage with the slot prior: the structure of anytime_td_v0. Rebuild = layer 1 frozen (Binomial(10), gamma 0.25) x layer 2 (counts|slot|0.25).

| model | log loss | Brier | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine (anytime_td_v0 structure) | 0.3608 | 0.1091 | 0.135 | baseline |
| Layer 1 frozen x previous layer 2 | 0.3620 | 0.1088 | 0.145 | +0.0012 (-0.0023, +0.0048) not established |
| Layer 1 frozen x best layer 2 | 0.3588 | 0.1086 | 0.145 | -0.0021 (-0.0043, +0.0000) not established |

Actual scoring rate 0.148.

### Where the end-to-end difference comes from

The two cross terms: each layer swapped in alone, the other left as the engine has it.

| model | log loss | mean predicted | vs engine (95% CI, game-clustered) |
|---|---|---|---|
| layer 1 frozen, ENGINE allocation | 0.3605 | 0.138 | -0.0004 (-0.0006, -0.0001) better |
| ENGINE count model, layer 2 allocation | 0.3591 | 0.143 | -0.0017 (-0.0039, +0.0004) not established |
| both (the rebuild) | 0.3588 | 0.145 | -0.0021 (-0.0043, +0.0000) not established |

| predicted P(score) | engine: predicted | engine: actual | rebuild: predicted | rebuild: actual |
|---|---|---|---|---|
| (0.0, 0.05] | 0.023 (4048) | 0.038 | 0.024 (3343) | 0.035 |
| (0.05, 0.1] | 0.075 (3109) | 0.078 | 0.075 (3259) | 0.065 |
| (0.1, 0.2] | 0.144 (3327) | 0.152 | 0.143 (3639) | 0.141 |
| (0.2, 0.3] | 0.245 (2007) | 0.276 | 0.246 (2143) | 0.256 |
| (0.3, 0.45] | 0.361 (1368) | 0.364 | 0.362 (1301) | 0.373 |
| (0.45, 0.6] | 0.507 (451) | 0.523 | 0.516 (571) | 0.496 |
| (0.6, 1.0] | 0.625 (18) | 0.833 | 0.636 (72) | 0.639 |

| position | engine | rebuild | n |
|---|---|---|---|
| QB | 0.2559 | 0.2526 | 2211 |
| RB | 0.4129 | 0.4123 | 3713 |
| TE | 0.3094 | 0.3082 | 3446 |
| WR | 0.3990 | 0.3959 | 5652 |

## Tuning (tune log loss, given offensive touchdowns)

| basis | no-history prior | moved-role weight | tune log loss |
|---|---|---|---|
| counts | slot | 0.25 | 0.3273 **chosen** |
| counts | slot | 0.5 | 0.3276 |
| counts | slot | 1 | 0.3283 |
| xtd | slot | 0.25 | 0.3302 |
| xtd | slot | 0.5 | 0.3305 |
| xtd | slot | 1 | 0.3311 |
| counts | none | 0.25 | 0.3314 |
| counts | none | 0.5 | 0.3317 |
| counts | none | 1 | 0.3323 |
| xtd | none | 0.25 | 0.3342 |
| xtd | none | 0.5 | 0.3345 |
| xtd | none | 1 | 0.3351 |

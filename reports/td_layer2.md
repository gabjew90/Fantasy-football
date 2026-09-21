# Layer 2: player allocation

Tune [2022, 2023], test [2024, 2025]. Population: every QB/RB/WR/TE on the GAME-DAY ACTIVE LIST (known before kickoff, not who took a snap), 15022 player-games in test, 14.8% of whom scored. The active list covers 100.0% of players who took an offensive snap. 48 snap rows had no GSIS id and were dropped from the history.

Both models are given the SAME information about the team's result, so the comparison is allocation and nothing else.

## Given the team's total offensive touchdowns

| model | log loss | Brier | mean predicted | vs engine today (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine today (kappa=5) | 0.3378 | 0.1015 | 0.140 | baseline |
| Layer 2, five channels (kappa=5) | 0.3375 | 0.1015 | 0.140 | -0.0003 (-0.0025, +0.0017) not established |

| position | engine today | layer 2 | n |
|---|---|---|---|
| QB | 0.2455 | 0.2435 | 2211 |
| RB | 0.3839 | 0.3861 | 3713 |
| TE | 0.2903 | 0.2901 | 3446 |
| WR | 0.3727 | 0.3712 | 5652 |

## Given the team's passing and rushing touchdowns (the engine's own granularity)

| model | log loss | Brier | mean predicted | vs engine today (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine today (kappa=5) | 0.3118 | 0.0937 | 0.140 | baseline |
| Layer 2, five channels (kappa=5) | 0.3114 | 0.0937 | 0.140 | -0.0004 (-0.0026, +0.0018) not established |

| position | engine today | layer 2 | n |
|---|---|---|---|
| QB | 0.2192 | 0.2153 | 2211 |
| RB | 0.3434 | 0.3474 | 3713 |
| TE | 0.2735 | 0.2726 | 3446 |
| WR | 0.3506 | 0.3489 | 5652 |

## Injury reallocation, where it can matter

In-season absences: team-games where a player who had played for the team in the last three weeks was inactive and had held at least 15% of a rushing or receiving channel.
519 team-games, 7097 player-games in test.

| reallocation | log loss | vs none (95% CI, game-clustered) |
|---|---|---|
| none: the share goes to other | 0.3331 | baseline |
| all: spread over every active teammate | 0.3312 | -0.0019 (-0.0035, -0.0004) better |
| position: to active teammates at his position | 0.3312 | -0.0019 (-0.0051, +0.0012) not established |

Weeks 1-3, all games: dominated by OFFSEASON departures -- last season's players who are no longer on the team, whose share has to go somewhere.
192 team-games, 2674 player-games in test.

| reallocation | log loss | vs none (95% CI, game-clustered) |
|---|---|---|
| none: the share goes to other | 0.3421 | baseline |
| all: spread over every active teammate | 0.3408 | -0.0013 (-0.0036, +0.0008) not established |
| position: to active teammates at his position | 0.3414 | -0.0007 (-0.0042, +0.0025) not established |


## Calibration, layer 2 given total touchdowns (test)

| predicted P(score) | mean predicted | actual rate | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.014 | 0.028 | 5679 |
| (0.05, 0.1] | 0.074 | 0.073 | 2492 |
| (0.1, 0.2] | 0.144 | 0.146 | 2997 |
| (0.2, 0.3] | 0.246 | 0.254 | 1619 |
| (0.3, 0.45] | 0.365 | 0.385 | 1312 |
| (0.45, 0.6] | 0.510 | 0.496 | 587 |
| (0.6, 1.0] | 0.700 | 0.690 | 336 |

## The artefact this replaced

The first version conditioned layer 2 on the team's actual touchdowns IN EACH CHANNEL while the engine got only pass and rush. Finer conditioning reveals more of the answer: one QB-rush touchdown means the starting quarterback scored.

| | log loss | QB log loss |
|---|---|---|
| engine, given pass/rush | 0.3118 | 0.2192 |
| layer 2, given each channel | 0.2961 | 0.0977 |

Not a comparison. Kept so the flattering number cannot be quoted without its reason.

## Tuning (tune log loss, no reallocation)

| kappa (games) | engine, total TDs | layer 2, total TDs | engine, pass/rush | layer 2, pass/rush |
|---|---|---|---|---|
| 0.5 | 0.3347 | 0.3345 | 0.3111 | 0.3112 |
| 2 | 0.3321 | 0.3323 | 0.3083 | 0.3086 |
| 5 | 0.3319 | 0.3321 | 0.3082 | 0.3084 |
| 15 | 0.3340 | 0.3339 | 0.3106 | 0.3104 |

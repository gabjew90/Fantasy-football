# Where an absent player's share goes: the Out path, tuned

Tune [2022, 2023], test [2024, 2025]. Rule: a fraction y of the absent player's share goes to eligible (priced) teammates at all, the rest to players outside that set; of the part that stays, x goes to every eligible teammate pro rata and 1 - x to eligible teammates at his position. The scorer shipped with x = 1, y = 1. Eligible = 5%+ share in the games he played.

## Targets

Tune: 122 absence events, 586 games. Test: 132 events, 695 games.

Test: the absent player held 0.217 of the team's targets. Players OUTSIDE the eligible set went from 0.127 with him to 0.367 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | **49.59** | 51.08 | 56.34 | 65.34 | 78.11 |
| 0.1 | 49.59 | 51.06 | 55.94 | 64.22 | 75.90 |
| 0.2 | 49.59 | 51.07 | 55.64 | 63.31 | 74.07 |
| 0.3 | 49.59 | 51.10 | 55.44 | 62.61 | 72.61 |
| 0.4 | 49.59 | 51.15 | 55.32 | 62.12 | 71.53 |
| 0.5 | 49.59 | 51.22 | 55.30 | 61.83 | 70.81 |
| 0.6 | 49.59 | 51.32 | 55.37 | 61.76 | 70.47 |
| 0.7 | 49.59 | 51.44 | 55.54 | 61.89 | 70.50 |
| 0.8 | 49.59 | 51.58 | 55.80 | 62.24 | 70.90 |
| 0.9 | 49.59 | 51.75 | 56.15 | 62.79 | 71.67 |
| 1 | 49.59 | 51.94 | 56.59 | 63.55 | 72.81 |

Test, chosen x = 0, y = 0 vs shipped x = 1, y = 1: loss 55.084 vs 86.395 (x 1e4); difference -31.311 (-42.055, -21.975), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.117 | 0.155 | 0.117 | 0.109 | -0.23 | nan |
| same position | 0.129 | 0.172 | 0.129 | 0.131 | 0.06 | nan |

## Carries

Tune: 113 absence events, 696 games. Test: 101 events, 566 games.

Test: the absent player held 0.362 of the team's carries. Players OUTSIDE the eligible set went from 0.065 with him to 0.359 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | 324.83 | **311.47** | 358.01 | 464.46 | 630.82 |
| 0.1 | 324.83 | 312.51 | 356.97 | 458.23 | 616.27 |
| 0.2 | 324.83 | 313.69 | 356.52 | 453.32 | 604.09 |
| 0.3 | 324.83 | 315.02 | 356.66 | 449.74 | 594.27 |
| 0.4 | 324.83 | 316.50 | 357.39 | 447.49 | 586.80 |
| 0.5 | 324.83 | 318.13 | 358.71 | 446.56 | 581.69 |
| 0.6 | 324.83 | 319.90 | 360.61 | 446.96 | 578.94 |
| 0.7 | 324.83 | 321.83 | 363.11 | 448.69 | 578.55 |
| 0.8 | 324.83 | 323.89 | 366.20 | 451.74 | 580.52 |
| 0.9 | 324.83 | 326.11 | 369.87 | 456.12 | 584.84 |
| 1 | 324.83 | 328.47 | 374.14 | 461.82 | 591.53 |

Test, chosen x = 0, y = 0.25 vs shipped x = 1, y = 1: loss 297.760 vs 454.604 (x 1e4); difference -156.844 (-228.784, -95.183), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.117 | 0.203 | 0.117 | 0.069 | -0.56 | nan |
| same position | 0.226 | 0.361 | 0.272 | 0.290 | 0.48 | 1.39 |

Chosen: targets x = 0, y = 0; carries x = 0, y = 0.25.


# Where an absent player's share goes: the Out path, tuned

Tune [2022, 2023], test [2024, 2025]. Rule: a fraction y of the absent player's share goes to eligible (priced) teammates at all, the rest to players outside that set; of the part that stays, x goes to every eligible teammate pro rata and 1 - x to eligible teammates at his position. The scorer shipped with x = 1, y = 1. Eligible = 5%+ share in the games he played.

## Targets

Tune: 115 absence events, 478 games. Test: 126 events, 585 games.

Test: the absent player held 0.215 of the team's targets. Players OUTSIDE the eligible set went from 0.112 with him to 0.267 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | 37.68 | 37.56 | 40.65 | 46.97 | 56.52 |
| 0.1 | 37.68 | 37.54 | 40.30 | 45.97 | 54.55 |
| 0.2 | 37.68 | **37.53** | 40.02 | 45.13 | 52.88 |
| 0.3 | 37.68 | 37.55 | 39.81 | 44.47 | 51.51 |
| 0.4 | 37.68 | 37.59 | 39.68 | 43.97 | 50.44 |
| 0.5 | 37.68 | 37.64 | 39.63 | 43.64 | 49.67 |
| 0.6 | 37.68 | 37.72 | 39.65 | 43.48 | 49.20 |
| 0.7 | 37.68 | 37.81 | 39.74 | 43.48 | 49.03 |
| 0.8 | 37.68 | 37.92 | 39.91 | 43.66 | 49.15 |
| 0.9 | 37.68 | 38.05 | 40.15 | 44.00 | 49.58 |
| 1 | 37.68 | 38.20 | 40.47 | 44.51 | 50.30 |

Test, chosen x = 0.2, y = 0.25 vs shipped x = 1, y = 1: loss 38.464 vs 53.351 (x 1e4); difference -14.887 (-21.510, -9.684), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.128 | 0.163 | 0.130 | 0.129 | 0.03 | 0.62 |
| same position | 0.133 | 0.171 | 0.152 | 0.157 | 0.63 | 1.24 |

## Carries

Tune: 105 absence events, 515 games. Test: 98 events, 494 games.

Test: the absent player held 0.368 of the team's carries. Players OUTSIDE the eligible set went from 0.057 with him to 0.220 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | 304.73 | **287.02** | 314.18 | 386.21 | 503.10 |
| 0.1 | 304.73 | 287.66 | 313.15 | 381.22 | 491.84 |
| 0.2 | 304.73 | 288.39 | 312.51 | 377.08 | 482.11 |
| 0.3 | 304.73 | 289.21 | 312.24 | 373.80 | 473.90 |
| 0.4 | 304.73 | 290.14 | 312.35 | 371.38 | 467.22 |
| 0.5 | 304.73 | 291.15 | 312.85 | 369.82 | 462.06 |
| 0.6 | 304.73 | 292.26 | 313.73 | 369.12 | 458.43 |
| 0.7 | 304.73 | 293.47 | 314.98 | 369.27 | 456.32 |
| 0.8 | 304.73 | 294.77 | 316.62 | 370.28 | 455.74 |
| 0.9 | 304.73 | 296.17 | 318.64 | 372.15 | 456.68 |
| 1 | 304.73 | 297.66 | 321.05 | 374.87 | 459.15 |

Test, chosen x = 0, y = 0.25 vs shipped x = 1, y = 1: loss 192.569 vs 289.026 (x 1e4); difference -96.456 (-136.114, -61.651), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.124 | 0.201 | 0.124 | 0.105 | -0.24 | nan |
| same position | 0.284 | 0.413 | 0.328 | 0.345 | 0.48 | 1.38 |

## I10_Targets

Tune: 105 absence events, 339 games. Test: 112 events, 412 games.

Test: the absent player held 0.210 of the team's i10_targets. Players OUTSIDE the eligible set went from 0.020 with him to 0.401 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | **385.40** | 399.31 | 421.89 | 453.15 | 493.08 |
| 0.1 | 385.40 | 399.32 | 421.17 | 450.93 | 488.63 |
| 0.2 | 385.40 | 399.38 | 420.64 | 449.17 | 484.97 |
| 0.3 | 385.40 | 399.50 | 420.31 | 447.85 | 482.10 |
| 0.4 | 385.40 | 399.66 | 420.18 | 446.97 | 480.02 |
| 0.5 | 385.40 | 399.87 | 420.25 | 446.54 | 478.73 |
| 0.6 | 385.40 | 400.13 | 420.51 | 446.55 | 478.23 |
| 0.7 | 385.40 | 400.44 | 420.98 | 447.00 | 478.53 |
| 0.8 | 385.40 | 400.80 | 421.64 | 447.91 | 479.61 |
| 0.9 | 385.40 | 401.21 | 422.49 | 449.25 | 481.49 |
| 1 | 385.40 | 401.67 | 423.55 | 451.04 | 484.15 |

Test, chosen x = 0, y = 0 vs shipped x = 1, y = 1: loss 411.412 vs 501.114 (x 1e4); difference -89.702 (-121.210, -62.258), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.177 | 0.221 | 0.177 | 0.123 | -1.21 | nan |
| same position | 0.198 | 0.245 | 0.198 | 0.168 | -0.65 | nan |

## I10_Carries

Tune: 95 absence events, 364 games. Test: 88 events, 363 games.

Test: the absent player held 0.344 of the team's i10_carries. Players OUTSIDE the eligible set went from 0.007 with him to 0.374 without him.

Tune loss (x 1e4), rows x, columns y:

| x | y=0 | y=0.25 | y=0.5 | y=0.75 | y=1 |
|---|---|---|---|---|---|
| 0 | 779.69 | **765.93** | 821.26 | 945.66 | 1139.14 |
| 0.1 | 779.69 | 770.19 | 825.36 | 945.17 | 1129.64 |
| 0.2 | 779.69 | 774.71 | 830.48 | 946.99 | 1124.23 |
| 0.3 | 779.69 | 779.49 | 836.63 | 951.11 | 1122.93 |
| 0.4 | 779.69 | 784.52 | 843.80 | 957.53 | 1125.72 |
| 0.5 | 779.69 | 789.80 | 851.99 | 966.26 | 1132.60 |
| 0.6 | 779.69 | 795.35 | 861.21 | 977.29 | 1143.58 |
| 0.7 | 779.69 | 801.14 | 871.46 | 990.63 | 1158.66 |
| 0.8 | 779.69 | 807.20 | 882.73 | 1006.27 | 1177.83 |
| 0.9 | 779.69 | 813.51 | 895.02 | 1024.22 | 1201.10 |
| 1 | 779.69 | 820.08 | 908.33 | 1044.47 | 1228.47 |

Test, chosen x = 0, y = 0.25 vs shipped x = 1, y = 1: loss 797.520 vs 1172.719 (x 1e4); difference -375.199 (-617.061, -206.225), better.

Test, actual gain / predicted gain by teammate group (1.00 = the rule is right):

| group | share with him | predicted, shipped | predicted, chosen | actual | ratio shipped | ratio chosen |
|---|---|---|---|---|---|---|
| other positions | 0.178 | 0.290 | 0.178 | 0.096 | -0.74 | nan |
| same position | 0.401 | 0.549 | 0.452 | 0.361 | -0.27 | -0.78 |

Chosen: targets x = 0.2, y = 0.25; carries x = 0, y = 0.25; i10_targets x = 0, y = 0; i10_carries x = 0, y = 0.25.


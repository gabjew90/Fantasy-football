# The end-zone split: red-zone targets and TDs separated into end-zone (pass_ez) and other (pass_rz)

Paired comparison, player by player: the shipped model from main (five channels) vs the same model with the split, identical players, game-clustered CIs (scripts/td_compare.py). No parameter was fitted, so every era is an evaluation. 2016-17 alone is below the harness's 95% active-list coverage guard and is not reported.

## 2022_2023

15040 player-games matched (15040 old, 15040 new rows); actual scoring rate 0.139.

| | old | new | new vs old (95% CI, game-clustered) |
|---|---|---|---|
| log loss, end to end | 0.3511 | 0.3508 | -0.0003 (-0.0012, +0.0007) not established |
| log loss, given the team's offensive TDs | 0.3241 | 0.3238 | -0.0003 (-0.0013, +0.0007) not established |
| mean predicted | 0.141 | 0.141 | |

- QB: old 0.2438, new 0.2438 (n 2214); mean predicted 0.083 -> 0.083 vs 0.087
- RB: old 0.4052, new 0.4031 (n 3819); mean predicted 0.215 -> 0.204 vs 0.186
- TE: old 0.2994, new 0.3008 (n 3362); mean predicted 0.097 -> 0.099 vs 0.098
- WR: old 0.3874, new 0.3873 (n 5645); mean predicted 0.140 -> 0.146 vs 0.154

Old, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.032 | 4591 |
| (0.05, 0.1] | 0.075 | 0.071 | 2470 |
| (0.1, 0.2] | 0.144 | 0.135 | 3711 |
| (0.2, 0.3] | 0.245 | 0.248 | 2153 |
| (0.3, 0.45] | 0.363 | 0.343 | 1397 |
| (0.45, 0.6] | 0.505 | 0.475 | 451 |
| (0.6, 1.0] | 0.633 | 0.609 | 64 |

New, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.033 | 4671 |
| (0.05, 0.1] | 0.075 | 0.074 | 2426 |
| (0.1, 0.2] | 0.145 | 0.132 | 3633 |
| (0.2, 0.3] | 0.247 | 0.246 | 2110 |
| (0.3, 0.45] | 0.363 | 0.346 | 1529 |
| (0.45, 0.6] | 0.507 | 0.468 | 434 |
| (0.6, 1.0] | 0.633 | 0.706 | 34 |

Top-q player realised / expected TDs: old 0.907, new 0.926.
New version, top-q player within channels: passing 0.81, rushing 1.00 (realised / share x team channel TDs).

## 2024_2025

15022 player-games matched (15022 old, 15022 new rows); actual scoring rate 0.148.

| | old | new | new vs old (95% CI, game-clustered) |
|---|---|---|---|
| log loss, end to end | 0.3562 | 0.3564 | +0.0002 (-0.0007, +0.0012) not established |
| log loss, given the team's offensive TDs | 0.3304 | 0.3307 | +0.0003 (-0.0008, +0.0013) not established |
| mean predicted | 0.144 | 0.145 | |

- QB: old 0.2439, new 0.2438 (n 2211); mean predicted 0.086 -> 0.086 vs 0.083
- RB: old 0.4103, new 0.4089 (n 3713); mean predicted 0.220 -> 0.208 vs 0.205
- TE: old 0.3073, new 0.3095 (n 3446); mean predicted 0.102 -> 0.102 vs 0.110
- WR: old 0.3943, new 0.3946 (n 5652); mean predicted 0.143 -> 0.151 vs 0.159

Old, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.031 | 4740 |
| (0.05, 0.1] | 0.074 | 0.075 | 2393 |
| (0.1, 0.2] | 0.144 | 0.146 | 3389 |
| (0.2, 0.3] | 0.246 | 0.245 | 2179 |
| (0.3, 0.45] | 0.362 | 0.365 | 1360 |
| (0.45, 0.6] | 0.514 | 0.493 | 619 |
| (0.6, 1.0] | 0.637 | 0.644 | 90 |

New, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.020 | 0.031 | 4841 |
| (0.05, 0.1] | 0.074 | 0.076 | 2317 |
| (0.1, 0.2] | 0.146 | 0.146 | 3282 |
| (0.2, 0.3] | 0.246 | 0.243 | 2142 |
| (0.3, 0.45] | 0.364 | 0.360 | 1529 |
| (0.45, 0.6] | 0.508 | 0.497 | 606 |
| (0.6, 1.0] | 0.630 | 0.717 | 53 |

Top-q player realised / expected TDs: old 0.914, new 0.937.
New version, top-q player within channels: passing 0.86, rushing 0.98 (realised / share x team channel TDs).

## 2018_2019

15227 player-games matched (15227 old, 15227 new rows); actual scoring rate 0.138.

| | old | new | new vs old (95% CI, game-clustered) |
|---|---|---|---|
| log loss, end to end | 0.3465 | 0.3465 | -0.0000 (-0.0009, +0.0008) not established |
| log loss, given the team's offensive TDs | 0.3229 | 0.3228 | -0.0001 (-0.0010, +0.0008) not established |
| mean predicted | 0.139 | 0.139 | |

- QB: old 0.1951, new 0.1951 (n 2359); mean predicted 0.061 -> 0.061 vs 0.061
- RB: old 0.3934, new 0.3907 (n 4063); mean predicted 0.204 -> 0.193 vs 0.177
- TE: old 0.3156, new 0.3169 (n 3197); mean predicted 0.101 -> 0.106 vs 0.109
- WR: old 0.3939, new 0.3950 (n 5608); mean predicted 0.145 -> 0.152 vs 0.158

Old, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.031 | 4893 |
| (0.05, 0.1] | 0.073 | 0.078 | 2595 |
| (0.1, 0.2] | 0.146 | 0.150 | 3375 |
| (0.2, 0.3] | 0.245 | 0.229 | 2167 |
| (0.3, 0.45] | 0.363 | 0.348 | 1426 |
| (0.45, 0.6] | 0.508 | 0.455 | 437 |
| (0.6, 1.0] | 0.655 | 0.523 | 86 |

New, end to end:

| predicted | mean predicted | actual | n |
|---|---|---|---|
| (-0.001, 0.05] | 0.021 | 0.031 | 4982 |
| (0.05, 0.1] | 0.073 | 0.083 | 2525 |
| (0.1, 0.2] | 0.147 | 0.148 | 3281 |
| (0.2, 0.3] | 0.246 | 0.225 | 2163 |
| (0.3, 0.45] | 0.363 | 0.345 | 1547 |
| (0.45, 0.6] | 0.505 | 0.463 | 423 |
| (0.6, 1.0] | 0.651 | 0.500 | 58 |

Top-q player realised / expected TDs: old 0.913, new 0.916.
New version, top-q player within channels: passing 0.81, rushing 1.01 (realised / share x team channel TDs).


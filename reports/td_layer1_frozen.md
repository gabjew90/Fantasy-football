# Layer 1, frozen spec scored as-is

Tuned once on [2022, 2023]: offensive touchdowns ~ Binomial(n=10) with mean = implied points x league offensive TDs-per-point x elasticity gamma=0.25; defence and special teams a flat 0.144 per team-game. Nothing below is re-tuned on the seasons it scores.

## Test: seasons 2024-2025, 1088 team-games

Offensive touchdowns (what an anytime prop settles on).

| model | CRPS | change vs row above (95% CI, game-clustered) |
|---|---|---|
| Engine today: league offensive ratio, linear, Poisson | 0.7234 | baseline |
| + binomial n=11 | 0.7156 | -0.0079 (-0.0105, -0.0052) better |
| + gamma=0.25, binomial n=10 (FROZEN) | 0.7090 | -0.0066 (-0.0101, -0.0032) better |

Log score: engine 1.6881, frozen 1.6528.

| quintile of implied | engine predicted | frozen predicted | actual offensive TDs | n |
|---|---|---|---|---|
| 1 | 1.789 | 1.682 | 1.735 | 219 |
| 2 | 2.136 | 2.098 | 2.049 | 245 |
| 3 | 2.377 | 2.398 | 2.516 | 217 |
| 4 | 2.588 | 2.664 | 2.657 | 210 |
| 5 | 2.884 | 3.050 | 3.325 | 197 |

All touchdowns: gamma applied to the TOTAL (previous spec) vs gamma on offensive touchdowns plus a flat D/ST term.

CRPS 0.7256 -> 0.7264: +0.0007 (-0.0003, +0.0018) not established.

| quintile of implied | gamma on total | offensive + flat D/ST | actual all TDs |
|---|---|---|---|
| 1 | 1.776 | 1.825 | 1.840 |
| 2 | 2.216 | 2.241 | 2.155 |
| 3 | 2.534 | 2.542 | 2.645 |
| 4 | 2.812 | 2.807 | 2.795 |
| 5 | 3.220 | 3.194 | 3.503 |

## Older seasons: seasons 2016-2019, 2048 team-games

Offensive touchdowns (what an anytime prop settles on).

| model | CRPS | change vs row above (95% CI, game-clustered) |
|---|---|---|
| Engine today: league offensive ratio, linear, Poisson | 0.7205 | baseline |
| + binomial n=11 | 0.7138 | -0.0067 (-0.0087, -0.0046) better |
| + gamma=0.25, binomial n=10 (FROZEN) | 0.7111 | -0.0027 (-0.0054, -0.0002) better |

Log score: engine 1.6831, frozen 1.6549.

| quintile of implied | engine predicted | frozen predicted | actual offensive TDs | n |
|---|---|---|---|---|
| 1 | 1.839 | 1.727 | 1.736 | 455 |
| 2 | 2.177 | 2.131 | 2.146 | 410 |
| 3 | 2.376 | 2.378 | 2.412 | 364 |
| 4 | 2.581 | 2.637 | 2.641 | 409 |
| 5 | 2.931 | 3.091 | 3.054 | 410 |

All touchdowns: gamma applied to the TOTAL (previous spec) vs gamma on offensive touchdowns plus a flat D/ST term.

CRPS 0.7370 -> 0.7378: +0.0008 (-0.0007, +0.0024) not established.

| quintile of implied | gamma on total | offensive + flat D/ST | actual all TDs |
|---|---|---|---|
| 1 | 1.858 | 1.871 | 1.881 |
| 2 | 2.295 | 2.275 | 2.300 |
| 3 | 2.561 | 2.521 | 2.580 |
| 4 | 2.840 | 2.781 | 2.824 |
| 5 | 3.328 | 3.235 | 3.273 |


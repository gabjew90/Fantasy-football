# Survival refit (plan B7, DECISIONS #26)

Rooms: 8. sims 200 (confirmation 1000), every 2 state(s), real seat, workers 7. Objective = mean over room types of the per-type log loss (equal weight per type; the one human room cannot be outvoted). Coordinate search on a coarse grid: the best point ON THE GRID, not identified parameters.

| room | type | league | picks | matched to board | adp |
|---|---|---|---|---|---|
| 1395566812157984768 | sleeper_human | omnibeta | 180 | 180 | adp_2026-08-19.json (230/294 board rows overridden) |
| 1396184666897145856 | sleeper_mock | keefamania | 150 | 148 | adp_2026-08-19.json (205/238 board rows overridden) |
| 1396191077534281728 | sleeper_mock | omnibeta | 46 | 46 | adp_2026-08-19.json (230/294 board rows overridden) |
| 1396194982775238656 | sleeper_mock | keefamania | 28 | 28 | adp_2026-08-19.json (205/238 board rows overridden) |
| 10502459 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) |
| 10503516 | yahoo_autopick | keefamania | 150 | 137 | board adp (Yahoo rank on this league's board) |
| 10504572 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) |
| 10505450 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) |

## Current knobs {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15}: objective 0.2132 sleeper_human 0.2366 sleeper_mock 0.2240 yahoo_autopick 0.1791 (n 40414, errors 0)

## Stage: sigma

| point | objective | sleeper_human | sleeper_mock | yahoo_autopick |
|---|---|---|---|---|
| {'sigma_early': 4.0, 'sigma_late': 15.0} | 0.2149 | 0.2537 | 0.2258 | 0.1652 |
| {'sigma_early': 4.0, 'sigma_late': 21.0} | 0.2114 | 0.2435 | 0.2210 | 0.1697 |
| {'sigma_early': 4.0, 'sigma_late': 27.0} | 0.2110 | 0.2370 | 0.2217 | 0.1745 |
| {'sigma_early': 4.0, 'sigma_late': 35.0} | 0.2148 | 0.2371 | 0.2250 | 0.1822 |
| {'sigma_early': 6.0, 'sigma_late': 15.0} | 0.2128 | 0.2463 | 0.2235 | 0.1686 |
| {'sigma_early': 6.0, 'sigma_late': 21.0} | 0.2120 | 0.2392 | 0.2222 | 0.1745 |
| {'sigma_early': 6.0, 'sigma_late': 27.0} | 0.2132 | 0.2366 | 0.2240 | 0.1791 |
| {'sigma_early': 6.0, 'sigma_late': 35.0} | 0.2168 | 0.2365 | 0.2274 | 0.1864 |
| {'sigma_early': 8.0, 'sigma_late': 15.0} | 0.2137 | 0.2434 | 0.2250 | 0.1728 |
| {'sigma_early': 8.0, 'sigma_late': 21.0} | 0.2136 | 0.2374 | 0.2249 | 0.1785 |
| {'sigma_early': 8.0, 'sigma_late': 27.0} | 0.2159 | 0.2362 | 0.2278 | 0.1835 |
| {'sigma_early': 8.0, 'sigma_late': 35.0} | 0.2200 | 0.2369 | 0.2324 | 0.1906 |
| {'sigma_early': 10.0, 'sigma_late': 15.0} | 0.2151 | 0.2400 | 0.2285 | 0.1769 |
| {'sigma_early': 10.0, 'sigma_late': 21.0} | 0.2165 | 0.2374 | 0.2294 | 0.1827 |
| {'sigma_early': 10.0, 'sigma_late': 27.0} | 0.2194 | 0.2375 | 0.2326 | 0.1881 |
| {'sigma_early': 10.0, 'sigma_late': 35.0} | 0.2239 | 0.2400 | 0.2375 | 0.1941 |

best after sigma: {'sigma_early': 4.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15} (objective 0.2110)

## Stage: reach

| point | objective | sleeper_human | sleeper_mock | yahoo_autopick |
|---|---|---|---|---|
| {'reach_prob': 0.0} | 0.2093 | 0.2405 | 0.2188 | 0.1687 |
| {'reach_prob': 0.1} | 0.2092 | 0.2361 | 0.2192 | 0.1722 |
| {'reach_prob': 0.15} | 0.2110 | 0.2370 | 0.2217 | 0.1745 |
| {'reach_prob': 0.25} | 0.2165 | 0.2420 | 0.2273 | 0.1801 |
| {'reach_prob': 0.35} | 0.2226 | 0.2466 | 0.2344 | 0.1867 |

best after reach: {'sigma_early': 4.0, 'sigma_late': 27.0, 'reach_prob': 0.1, 'need_damp': 0.15} (objective 0.2092)

## Stage: need

| point | objective | sleeper_human | sleeper_mock | yahoo_autopick |
|---|---|---|---|---|
| {'need_damp': 0.15} | 0.2092 | 0.2361 | 0.2192 | 0.1722 |
| {'need_damp': 0.3} | 0.2082 | 0.2360 | 0.2204 | 0.1682 |
| {'need_damp': 0.5} | 0.2082 | 0.2366 | 0.2213 | 0.1668 |

best after need: {'sigma_early': 4.0, 'sigma_late': 27.0, 'reach_prob': 0.1, 'need_damp': 0.3} (objective 0.2082)

## Confirmation at sims 1000

### current: {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15} -> objective 0.2114

pooled (n=40414)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 178 | 25% | 20% | 0.501 |
| 30-49% | 973 | 41% | 32% | 0.638 |
| 50-69% | 2239 | 61% | 65% | 0.640 |
| 70-89% | 6210 | 82% | 84% | 0.425 |
| 90-100% | 30814 | 97% | 98% | 0.103 |

sleeper_human (n=7519)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 57 | 25% | 30% | 0.603 |
| 30-49% | 224 | 40% | 46% | 0.687 |
| 50-69% | 497 | 61% | 68% | 0.630 |
| 70-89% | 1359 | 81% | 84% | 0.441 |
| 90-100% | 5382 | 97% | 97% | 0.123 |

sleeper_mock (n=7703)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 63 | 26% | 21% | 0.511 |
| 30-49% | 307 | 40% | 33% | 0.648 |
| 50-69% | 547 | 61% | 63% | 0.645 |
| 70-89% | 1348 | 81% | 84% | 0.434 |
| 90-100% | 5438 | 97% | 98% | 0.099 |

yahoo_autopick (n=25192)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 58 | 26% | 9% | 0.390 |
| 30-49% | 442 | 41% | 25% | 0.607 |
| 50-69% | 1195 | 61% | 64% | 0.642 |
| 70-89% | 3503 | 82% | 85% | 0.415 |
| 90-100% | 19994 | 97% | 98% | 0.098 |

### fitted: {'sigma_early': 4.0, 'sigma_late': 27.0, 'reach_prob': 0.1, 'need_damp': 0.3} -> objective 0.2060

pooled (n=40414)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 433 | 22% | 23% | 0.534 |
| 30-49% | 992 | 40% | 36% | 0.643 |
| 50-69% | 1778 | 61% | 62% | 0.654 |
| 70-89% | 6504 | 82% | 84% | 0.423 |
| 90-100% | 30707 | 97% | 98% | 0.093 |

sleeper_human (n=7519)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 122 | 21% | 34% | 0.689 |
| 30-49% | 218 | 40% | 52% | 0.701 |
| 50-69% | 382 | 60% | 66% | 0.644 |
| 70-89% | 1434 | 82% | 84% | 0.444 |
| 90-100% | 5363 | 97% | 97% | 0.119 |

sleeper_mock (n=7703)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 170 | 22% | 29% | 0.607 |
| 30-49% | 270 | 39% | 37% | 0.649 |
| 50-69% | 485 | 61% | 62% | 0.652 |
| 70-89% | 1269 | 82% | 83% | 0.447 |
| 90-100% | 5509 | 98% | 98% | 0.094 |

yahoo_autopick (n=25192)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 141 | 23% | 5% | 0.312 |
| 30-49% | 504 | 41% | 28% | 0.615 |
| 50-69% | 911 | 61% | 60% | 0.659 |
| 70-89% | 3801 | 83% | 85% | 0.407 |
| 90-100% | 19835 | 97% | 98% | 0.085 |

## Pre-registered calibration bar (within 8 points in every bucket with n >= 15)

pooled: PASS
human room: FAIL 0-29% (pred 21% obs 34%, n 122); 30-49% (pred 40% obs 52%, n 218)

## Empirical need damp (closed-slot take rate vs the ADP mass, one parameter, by room type)

| room type | picks | filled no open starter slot | implied damp | in use |
|---|---|---|---|---|
| sleeper_human | 180 | 61 | 0.44 | 0.3 |
| sleeper_mock | 224 | 60 | 0.31 | 0.3 |
| yahoo_autopick | 600 | 240 | 0.49 | 0.3 |

Wall time 726 s.

# Survival refit (plan B7, DECISIONS #26; autopick stage DECISIONS #35; rival stage DECISIONS #46)

Objective population: shown (the engine top-8 rows at each state).

Rooms: 41. sims 100 (confirmation 400), every 4 state(s), real seat, workers 6, stage rival_study. Objective = mean over room types of the per-type log loss (equal weight per type; the one human room cannot be outvoted). Coordinate search on a coarse grid: the best point ON THE GRID, not identified parameters. The autopick sub-stages run only on rooms whose sidecar gives a non-empty away set; the tracker at each state carries that pick's away set as `away_slots`.

| room | type | league | picks | matched to board | adp | yahoo_rank | away set |
|---|---|---|---|---|---|---|---|
| 1395566812157984768 | sleeper_human | omnibeta | 180 | 180 | adp_2026-08-19.json (230/294 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396184666897145856 | sleeper_mock | keefamania | 150 | 149 | adp_2026-08-19.json (206/225 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396191077534281728 | sleeper_mock | omnibeta | 46 | 46 | adp_2026-08-19.json (230/294 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396194982775238656 | sleeper_mock | keefamania | 28 | 28 | adp_2026-08-19.json (206/225 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10502459 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10503516 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10504572 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10505450 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10531886 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | sidecar: away set non-empty at 143/150 picks, slots seen [3, 4, 5, 7, 8, 9] |
| 10532940 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 5, 6, 7, 8, 9, 10] |
| 10534350 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: mock_players_10534350.json (225/225 board rows) | sidecar: away set non-empty at 139/150 picks, slots seen [1, 2, 3, 7, 8] |
| 10584427 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (225/225 board rows) | sidecar: away set non-empty at 146/150 picks, slots seen [2, 4, 5, 6, 10] |
| 10586715 | yahoo_autopick | keefamania | 150 | 141 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10586715.json (225/225 board rows) | sidecar: away set non-empty at 133/150 picks, slots seen [1, 2, 3, 4, 5, 9] |
| 10588125 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10588125.json (225/225 board rows) | sidecar: away set non-empty at 141/150 picks, slots seen [3, 4, 5, 7, 8, 10] |
| 10589182 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10589182.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 3, 4, 5, 6, 7, 10] |
| 10590238 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10590238.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 5, 6, 9, 10] |
| 10590944 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10590944.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [5, 6, 7, 8, 10] |
| 10597994 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10597994.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 4, 6, 7, 9] |
| 10598876 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10598876.json (225/225 board rows) | sidecar: away set non-empty at 139/150 picks, slots seen [2, 3, 10] |
| 10600461 | yahoo_autopick | keefamania | 150 | 141 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10600461.json (225/225 board rows) | sidecar: away set non-empty at 149/150 picks, slots seen [1, 2, 3, 4, 6, 8, 9, 10] |
| 10601343 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10601343.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 4, 6, 7, 10] |
| 10611562 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10611562.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 4, 5, 6, 8, 9] |
| 10612448 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10612448.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 7, 8] |
| 10616150 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10616150.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 3, 5, 6, 8, 9] |
| 10617211 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10617211.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 6, 8, 9] |
| 10618261 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10618261.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 6, 7, 8, 10] |
| 10619316 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10619316.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 3, 5, 7, 8, 10] |
| 10693315 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10693315.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 3, 4, 7, 8, 9] |
| 10694196 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | sidecar: away set non-empty at 148/150 picks, slots seen [1, 2, 4, 6, 7, 10] |
| 10703362 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10703362.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 5, 6, 8, 10] |
| 10704422 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10704422.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 6, 7, 9] |
| 10705481 | yahoo_autopick | keefamania | 150 | 141 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10705481.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 4, 6, 7, 9] |
| 10712781 | yahoo_autopick | keefamania | 210 | 187 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10712781.json (225/225 board rows) | sidecar: away set non-empty at 202/210 picks, slots seen [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 14] |
| 10713941 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10713941.json (225/225 board rows) | sidecar: away set non-empty at 143/150 picks, slots seen [2, 3, 4, 5, 6, 7, 9] |
| 10714820 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10714820.json (225/225 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 6, 7, 8, 10] |
| 10719939 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | sidecar: away set non-empty at 138/150 picks, slots seen [1, 2, 5, 6, 7, 9, 10] |
| email1a059ffa1d94f905 | yahoo_email | keefamania | 23 | 23 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a050324118c1 | yahoo_email | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a43675df6ac2 | yahoo_email | keefamania | 150 | 137 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a720ce261afe | yahoo_email | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05aae58012b315 | yahoo_email | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10719939.json (225/225 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |

## Current knobs {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.0, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'lottery'}: objective 0.7424 sleeper_human 0.2508 sleeper_mock 0.2170 yahoo_autopick 0.1805 yahoo_email 0.1861 (n 125205, errors 0)

## Stage: rival_x_sigma (41 room(s): 1395566812157984768, 1396184666897145856, 1396191077534281728, 1396194982775238656, 10502459, 10503516, 10504572, 10505450, 10531886, 10532940, 10534350, 10584427, 10586715, 10588125, 10589182, 10590238, 10590944, 10597994, 10598876, 10600461, 10601343, 10611562, 10612448, 10616150, 10617211, 10618261, 10619316, 10693315, 10694196, 10703362, 10704422, 10705481, 10712781, 10713941, 10714820, 10719939, email1a059ffa1d94f905, email1a05a050324118c1, email1a05a43675df6ac2, email1a05a720ce261afe, email1a05aae58012b315)

| point | objective | sleeper_human | sleeper_mock | yahoo_autopick | yahoo_email | pool / shown |
|---|---|---|---|---|---|---|
| {'rival_draw': 'lottery', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.7424 | 0.2508 | 0.2170 | 0.1805 | 0.1861 | pool 0.2086 shown 0.7424 (n 3364) |
| {'rival_draw': 'lottery', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.7987 | 0.2495 | 0.2341 | 0.1988 | 0.2115 | pool 0.2235 shown 0.7987 (n 3364) |
| {'rival_draw': 'lottery', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.8740 | 0.2608 | 0.2546 | 0.2159 | 0.2314 | pool 0.2407 shown 0.8740 (n 3364) |
| {'rival_draw': 'lottery', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.9208 | 0.2666 | 0.2693 | 0.2271 | 0.2412 | pool 0.2511 shown 0.9208 (n 3364) |
| {'rival_draw': 'floored', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.6708 | 0.2281 | 0.2039 | 0.1744 | 0.1824 | pool 0.1972 shown 0.6708 (n 3364) |
| {'rival_draw': 'floored', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.7722 | 0.2394 | 0.2285 | 0.1968 | 0.2101 | pool 0.2187 shown 0.7722 (n 3364) |
| {'rival_draw': 'floored', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.8488 | 0.2551 | 0.2524 | 0.2154 | 0.2302 | pool 0.2383 shown 0.8488 (n 3364) |
| {'rival_draw': 'floored', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.9114 | 0.2621 | 0.2674 | 0.2273 | 0.2406 | pool 0.2494 shown 0.9114 (n 3364) |
| {'rival_draw': 'order', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.6411 | 0.2757 | 0.1948 | 0.2172 | 0.1855 | pool 0.2183 shown 0.6411 (n 3376) |
| {'rival_draw': 'order', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.5955 | 0.2455 | 0.1956 | 0.2015 | 0.1858 | pool 0.2071 shown 0.5955 (n 3376) |
| {'rival_draw': 'order', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.6089 | 0.2365 | 0.2056 | 0.1994 | 0.1967 | pool 0.2096 shown 0.6089 (n 3376) |
| {'rival_draw': 'order', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.6405 | 0.2416 | 0.2188 | 0.2039 | 0.2068 | pool 0.2178 shown 0.6405 (n 3376) |

best after rival_x_sigma: {'sigma_early': 10.0, 'sigma_late': 45.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.0, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'order'} (objective 0.5955)

## Stage: autopick_list_prob (28 room(s): 10531886, 10532940, 10534350, 10584427, 10586715, 10588125, 10589182, 10590238, 10590944, 10597994, 10598876, 10600461, 10601343, 10611562, 10612448, 10616150, 10617211, 10618261, 10619316, 10693315, 10694196, 10703362, 10704422, 10705481, 10712781, 10713941, 10714820, 10719939)

| point | objective | yahoo_autopick | pool / shown |
|---|---|---|---|
| {'autopick_list_prob': 0.0} | 0.5354 | 0.2007 | pool 0.2007 shown 0.5354 (n 2412) |
| {'autopick_list_prob': 0.2} | 0.5208 | 0.1921 | pool 0.1921 shown 0.5208 (n 2412) |
| {'autopick_list_prob': 0.4} | 0.5306 | 0.1891 | pool 0.1891 shown 0.5306 (n 2412) |

best after autopick_list_prob: {'sigma_early': 10.0, 'sigma_late': 45.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.2, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'order'} (objective 0.5208)

## Confirmation at sims 400

### current: {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.0, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'lottery'} -> objective 0.6694 sleeper_human 0.2440 sleeper_mock 0.2136 yahoo_autopick 0.1762 yahoo_email 0.1828

pooled (n=125205)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 886 | 130 | 22% | 20% | -2% | [-5%, +2%] | 0.516 |
| 30-49% | 2572 | 270 | 40% | 33% | -7% | [-9%, -5%] | 0.642 |
| 50-69% | 5399 | 393 | 61% | 62% | +1% | [-1%, +3%] | 0.655 |
| 70-89% | 16409 | 507 | 82% | 85% | +3% | [+2%, +4%] | 0.424 |
| 90-100% | 99939 | 549 | 98% | 98% | +0% | [+0%, +0%] | 0.104 |

pooled SHOWN (engine top-8) (n=3376)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 65 | 35 | 24% | 17% | -7% | [-15%, +1%] | 0.446 |
| 30-49% | 365 | 133 | 41% | 20% | -21% | [-25%, -17%] | 0.593 |
| 50-69% | 563 | 237 | 60% | 34% | -26% | [-29%, -22%] | 0.785 |
| 70-89% | 928 | 375 | 81% | 58% | -23% | [-26%, -19%] | 0.807 |
| 90-100% | 1455 | 457 | 96% | 89% | -8% | [-9%, -6%] | 0.411 |

human (n=3942)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 23 | 3 | 25% | 35% | +9% | [+4%, +24%] | 0.637 |
| 30-49% | 91 | 5 | 40% | 43% | +3% | [-6%, +12%] | 0.681 |
| 50-69% | 214 | 7 | 61% | 68% | +7% | [-1%, +14%] | 0.642 |
| 70-89% | 665 | 8 | 82% | 83% | +2% | [-3%, +5%] | 0.451 |
| 90-100% | 2949 | 15 | 97% | 96% | -1% | [-2%, +0%] | 0.152 |

human SHOWN (engine top-8) (n=117)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 7 | 3 | 41% | 0% | -41% | [-43%, -41%] | 0.537 |
| 50-69% | 15 | 4 | 61% | 40% | -21% | [-36%, +5%] | 0.762 |
| 70-89% | 32 | 7 | 81% | 41% | -41% | [-57%, -19%] | 1.100 |
| 90-100% | 63 | 15 | 97% | 83% | -14% | [-26%, -3%] | 0.558 |

autopick (n=117329)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 840 | 122 | 22% | 20% | -2% | [-6%, +2%] | 0.512 |
| 30-49% | 2340 | 257 | 40% | 33% | -7% | [-10%, -5%] | 0.641 |
| 50-69% | 4936 | 375 | 61% | 62% | +1% | [-1%, +3%] | 0.657 |
| 70-89% | 15121 | 484 | 82% | 85% | +3% | [+2%, +4%] | 0.421 |
| 90-100% | 94092 | 512 | 98% | 98% | +0% | [+0%, +0%] | 0.103 |

autopick SHOWN (engine top-8) (n=3109)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 65 | 35 | 24% | 17% | -7% | [-15%, +1%] | 0.446 |
| 30-49% | 344 | 123 | 41% | 21% | -19% | [-23%, -15%] | 0.597 |
| 50-69% | 527 | 226 | 60% | 34% | -26% | [-31%, -22%] | 0.787 |
| 70-89% | 857 | 357 | 80% | 59% | -21% | [-24%, -18%] | 0.778 |
| 90-100% | 1316 | 420 | 96% | 89% | -7% | [-9%, -5%] | 0.395 |

sleeper_human (n=3942)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 23 | 3 | 25% | 35% | +9% | [+4%, +24%] | 0.637 |
| 30-49% | 91 | 5 | 40% | 43% | +3% | [-6%, +12%] | 0.681 |
| 50-69% | 214 | 7 | 61% | 68% | +7% | [-1%, +14%] | 0.642 |
| 70-89% | 665 | 8 | 82% | 83% | +2% | [-3%, +5%] | 0.451 |
| 90-100% | 2949 | 15 | 97% | 96% | -1% | [-2%, +0%] | 0.152 |

sleeper_human SHOWN (engine top-8) (n=117)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 7 | 3 | 41% | 0% | -41% | [-43%, -41%] | 0.537 |
| 50-69% | 15 | 4 | 61% | 40% | -21% | [-36%, +5%] | 0.762 |
| 70-89% | 32 | 7 | 81% | 41% | -41% | [-57%, -19%] | 1.100 |
| 90-100% | 63 | 15 | 97% | 83% | -14% | [-26%, -3%] | 0.558 |

sleeper_mock (n=3934)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 23 | 5 | 26% | 22% | -5% | [-28%, +2%] | 0.541 |
| 30-49% | 141 | 8 | 40% | 33% | -7% | [-14%, -3%] | 0.635 |
| 50-69% | 249 | 11 | 61% | 63% | +2% | [-3%, +7%] | 0.640 |
| 70-89% | 623 | 15 | 81% | 82% | +1% | [-0%, +3%] | 0.465 |
| 90-100% | 2898 | 22 | 98% | 98% | +0% | [-1%, +1%] | 0.100 |

sleeper_mock SHOWN (engine top-8) (n=150)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 14 | 7 | 41% | 0% | -41% | [-43%, -38%] | 0.526 |
| 50-69% | 21 | 7 | 60% | 38% | -22% | [-41%, -4%] | 0.751 |
| 70-89% | 39 | 11 | 81% | 36% | -45% | [-58%, -30%] | 1.203 |
| 90-100% | 76 | 22 | 96% | 83% | -13% | [-20%, -6%] | 0.559 |

yahoo_autopick (n=104193)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 779 | 114 | 22% | 21% | -1% | [-5%, +4%] | 0.526 |
| 30-49% | 2086 | 237 | 40% | 34% | -6% | [-8%, -4%] | 0.647 |
| 50-69% | 4362 | 338 | 61% | 62% | +1% | [-1%, +3%] | 0.656 |
| 70-89% | 13067 | 435 | 82% | 85% | +3% | [+2%, +4%] | 0.419 |
| 90-100% | 83899 | 457 | 98% | 98% | +0% | [-0%, +0%] | 0.104 |

yahoo_autopick SHOWN (engine top-8) (n=2753)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 65 | 35 | 24% | 17% | -7% | [-15%, +1%] | 0.446 |
| 30-49% | 314 | 111 | 41% | 22% | -19% | [-24%, -14%] | 0.601 |
| 50-69% | 457 | 201 | 60% | 33% | -27% | [-32%, -23%] | 0.791 |
| 70-89% | 737 | 316 | 80% | 60% | -20% | [-24%, -17%] | 0.764 |
| 90-100% | 1180 | 377 | 96% | 89% | -7% | [-9%, -5%] | 0.403 |

yahoo_email (n=13136)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 61 | 8 | 24% | 5% | -19% | [-25%, -16%] | 0.330 |
| 30-49% | 254 | 20 | 40% | 22% | -18% | [-23%, -13%] | 0.590 |
| 50-69% | 574 | 37 | 61% | 59% | -2% | [-8%, +5%] | 0.660 |
| 70-89% | 2054 | 49 | 82% | 84% | +2% | [-0%, +4%] | 0.433 |
| 90-100% | 10193 | 55 | 97% | 98% | +1% | [+1%, +1%] | 0.095 |

yahoo_email SHOWN (engine top-8) (n=356)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 30 | 12 | 40% | 13% | -27% | [-37%, -13%] | 0.562 |
| 50-69% | 70 | 25 | 61% | 40% | -21% | [-31%, -10%] | 0.760 |
| 70-89% | 120 | 41 | 81% | 54% | -27% | [-37%, -17%] | 0.865 |
| 90-100% | 136 | 43 | 95% | 90% | -5% | [-10%, -0%] | 0.328 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 125205 | FAIL 30-49% (obs-pred -7%, CI [-9%, -5%], n 2572, clusters 270); 70-89% (obs-pred +3%, CI [+2%, +4%], n 16409, clusters 507); 90-100% (obs-pred +0%, CI [+0%, +0%], n 99939, clusters 549) | PASS |
| human | 3942 | PASS | FAIL 0-29% (pred 25% obs 35%, n 23) |
| autopick | 117329 | FAIL 30-49% (obs-pred -7%, CI [-10%, -5%], n 2340, clusters 257); 70-89% (obs-pred +3%, CI [+2%, +4%], n 15121, clusters 484); 90-100% (obs-pred +0%, CI [+0%, +0%], n 94092, clusters 512) | PASS |

### fitted: {'sigma_early': 10.0, 'sigma_late': 45.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.2, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'order'} -> objective 0.5720 sleeper_human 0.2378 sleeper_mock 0.1922 yahoo_autopick 0.1890 yahoo_email 0.1815

pooled (n=125205)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 3174 | 382 | 13% | 34% | +21% | [+17%, +25%] | 1.069 |
| 30-49% | 2293 | 425 | 40% | 45% | +5% | [+3%, +8%] | 0.695 |
| 50-69% | 4144 | 469 | 61% | 62% | +2% | [-0%, +4%] | 0.655 |
| 70-89% | 12132 | 541 | 82% | 84% | +2% | [+1%, +3%] | 0.435 |
| 90-100% | 103462 | 549 | 98% | 98% | -1% | [-1%, -0%] | 0.129 |

pooled SHOWN (engine top-8) (n=3376)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 538 | 195 | 12% | 13% | +1% | [-2%, +4%] | 0.392 |
| 30-49% | 334 | 203 | 40% | 31% | -9% | [-14%, -5%] | 0.641 |
| 50-69% | 424 | 257 | 60% | 45% | -15% | [-20%, -11%] | 0.738 |
| 70-89% | 657 | 333 | 81% | 70% | -10% | [-14%, -7%] | 0.626 |
| 90-100% | 1423 | 453 | 97% | 90% | -7% | [-10%, -6%] | 0.564 |

human (n=3942)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 131 | 7 | 12% | 27% | +15% | [+7%, +26%] | 0.690 |
| 30-49% | 93 | 7 | 41% | 54% | +13% | [+7%, +20%] | 0.728 |
| 50-69% | 154 | 8 | 61% | 73% | +13% | [+7%, +18%] | 0.610 |
| 70-89% | 406 | 14 | 82% | 83% | +2% | [-3%, +6%] | 0.443 |
| 90-100% | 3158 | 15 | 98% | 96% | -2% | [-3%, -1%] | 0.197 |

human SHOWN (engine top-8) (n=117)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 19 | 4 | 13% | 32% | +19% | [+2%, +41%] | 0.748 |
| 30-49% | 12 | 6 | 40% | 8% | -32% | [-41%, -25%] | 0.564 |
| 50-69% | 12 | 6 | 59% | 50% | -9% | [-18%, +6%] | 0.743 |
| 70-89% | 16 | 9 | 81% | 81% | -0% | [-20%, +18%] | 0.445 |
| 90-100% | 58 | 15 | 97% | 78% | -20% | [-41%, +1%] | 0.807 |

autopick (n=117329)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 2923 | 364 | 13% | 35% | +22% | [+19%, +26%] | 1.117 |
| 30-49% | 2097 | 407 | 40% | 45% | +5% | [+2%, +8%] | 0.695 |
| 50-69% | 3798 | 450 | 61% | 62% | +1% | [-0%, +4%] | 0.656 |
| 70-89% | 11233 | 505 | 82% | 84% | +2% | [+1%, +3%] | 0.436 |
| 90-100% | 97278 | 512 | 98% | 98% | -0% | [-1%, -0%] | 0.127 |

autopick SHOWN (engine top-8) (n=3109)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 494 | 182 | 12% | 13% | +1% | [-3%, +5%] | 0.392 |
| 30-49% | 309 | 189 | 40% | 32% | -8% | [-13%, -3%] | 0.649 |
| 50-69% | 400 | 243 | 60% | 45% | -15% | [-19%, -10%] | 0.737 |
| 70-89% | 613 | 309 | 81% | 70% | -11% | [-15%, -7%] | 0.637 |
| 90-100% | 1293 | 418 | 97% | 91% | -6% | [-8%, -5%] | 0.539 |

sleeper_human (n=3942)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 131 | 7 | 12% | 27% | +15% | [+7%, +26%] | 0.690 |
| 30-49% | 93 | 7 | 41% | 54% | +13% | [+7%, +20%] | 0.728 |
| 50-69% | 154 | 8 | 61% | 73% | +13% | [+7%, +18%] | 0.610 |
| 70-89% | 406 | 14 | 82% | 83% | +2% | [-3%, +6%] | 0.443 |
| 90-100% | 3158 | 15 | 98% | 96% | -2% | [-3%, -1%] | 0.197 |

sleeper_human SHOWN (engine top-8) (n=117)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 19 | 4 | 13% | 32% | +19% | [+2%, +41%] | 0.748 |
| 30-49% | 12 | 6 | 40% | 8% | -32% | [-41%, -25%] | 0.564 |
| 50-69% | 12 | 6 | 59% | 50% | -9% | [-18%, +6%] | 0.743 |
| 70-89% | 16 | 9 | 81% | 81% | -0% | [-20%, +18%] | 0.445 |
| 90-100% | 58 | 15 | 97% | 78% | -20% | [-41%, +1%] | 0.807 |

sleeper_mock (n=3934)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 120 | 11 | 13% | 11% | -2% | [-9%, +6%] | 0.302 |
| 30-49% | 103 | 11 | 40% | 41% | +1% | [-6%, +9%] | 0.670 |
| 50-69% | 192 | 11 | 60% | 61% | +1% | [-7%, +9%] | 0.660 |
| 70-89% | 493 | 22 | 81% | 86% | +5% | [+3%, +7%] | 0.395 |
| 90-100% | 3026 | 22 | 98% | 98% | -1% | [-1%, +0%] | 0.125 |

sleeper_mock SHOWN (engine top-8) (n=150)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 25 | 9 | 9% | 0% | -9% | [-13%, -7%] | 0.103 |
| 30-49% | 13 | 8 | 38% | 15% | -23% | [-39%, -12%] | 0.527 |
| 50-69% | 12 | 8 | 59% | 33% | -25% | [-59%, +2%] | 0.764 |
| 70-89% | 28 | 15 | 83% | 79% | -5% | [-14%, +6%] | 0.482 |
| 90-100% | 72 | 20 | 97% | 79% | -18% | [-31%, -4%] | 0.814 |

yahoo_autopick (n=104193)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 2668 | 329 | 13% | 37% | +24% | [+20%, +28%] | 1.170 |
| 30-49% | 1835 | 365 | 40% | 46% | +6% | [+3%, +9%] | 0.696 |
| 50-69% | 3273 | 406 | 61% | 62% | +2% | [-0%, +4%] | 0.655 |
| 70-89% | 9607 | 453 | 82% | 83% | +2% | [+1%, +3%] | 0.439 |
| 90-100% | 86810 | 457 | 98% | 98% | -1% | [-1%, -0%] | 0.128 |

yahoo_autopick SHOWN (engine top-8) (n=2753)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 457 | 166 | 12% | 14% | +1% | [-2%, +6%] | 0.409 |
| 30-49% | 270 | 165 | 40% | 32% | -7% | [-13%, -2%] | 0.648 |
| 50-69% | 339 | 209 | 60% | 46% | -14% | [-19%, -9%] | 0.733 |
| 70-89% | 519 | 268 | 81% | 70% | -11% | [-15%, -7%] | 0.636 |
| 90-100% | 1168 | 376 | 97% | 91% | -7% | [-8%, -5%] | 0.567 |

yahoo_email (n=13136)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 255 | 35 | 15% | 23% | +7% | [-1%, +18%] | 0.559 |
| 30-49% | 262 | 42 | 40% | 40% | -0% | [-9%, +9%] | 0.684 |
| 50-69% | 525 | 44 | 61% | 60% | -0% | [-6%, +5%] | 0.661 |
| 70-89% | 1626 | 52 | 82% | 84% | +3% | [+0%, +5%] | 0.421 |
| 90-100% | 10468 | 55 | 98% | 98% | +0% | [-1%, +1%] | 0.111 |

yahoo_email SHOWN (engine top-8) (n=356)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 37 | 16 | 10% | 5% | -5% | [-10%, +2%] | 0.187 |
| 30-49% | 39 | 24 | 41% | 31% | -10% | [-24%, +5%] | 0.656 |
| 50-69% | 61 | 34 | 59% | 38% | -21% | [-32%, -11%] | 0.762 |
| 70-89% | 94 | 41 | 80% | 71% | -9% | [-19%, -1%] | 0.640 |
| 90-100% | 125 | 42 | 96% | 92% | -4% | [-9%, +0%] | 0.285 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 125205 | FAIL 0-29% (obs-pred +21%, CI [+17%, +25%], n 3174, clusters 382); 30-49% (obs-pred +5%, CI [+3%, +8%], n 2293, clusters 425); 70-89% (obs-pred +2%, CI [+1%, +3%], n 12132, clusters 541); 90-100% (obs-pred -1%, CI [-1%, -0%], n 103462, clusters 549) | FAIL 0-29% (pred 13% obs 34%, n 3174) |
| human | 3942 | PASS | FAIL 0-29% (pred 12% obs 27%, n 131); 30-49% (pred 41% obs 54%, n 93); 50-69% (pred 61% obs 73%, n 154) |
| autopick | 117329 | FAIL 0-29% (obs-pred +22%, CI [+19%, +26%], n 2923, clusters 364); 30-49% (obs-pred +5%, CI [+2%, +8%], n 2097, clusters 407); 70-89% (obs-pred +2%, CI [+1%, +3%], n 11233, clusters 505); 90-100% (obs-pred -0%, CI [-1%, -0%], n 97278, clusters 512) | FAIL 0-29% (pred 13% obs 35%, n 2923) |

## Empirical need damp (closed-slot take rate vs the ADP mass, one parameter, by room type)

| room type | picks | filled no open starter slot | implied damp | in use |
|---|---|---|---|---|
| sleeper_human | 180 | 61 | 0.48 | 0.15 |
| sleeper_mock | 224 | 60 | 0.43 | 0.15 |
| yahoo_autopick | 4860 | 1998 | 0.61 | 0.15 |
| yahoo_email | 623 | 240 | 0.55 | 0.15 |

Wall time 704 s.

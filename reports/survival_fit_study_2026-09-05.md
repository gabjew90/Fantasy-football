# Survival refit (plan B7, DECISIONS #26; autopick stage DECISIONS #35; rival stage DECISIONS #46)

Objective population: shown (the engine top-8 rows at each state).

Rooms: 11. sims 200 (confirmation 1000), every 2 state(s), real seat, workers 2, stage rival_study. Objective = mean over room types of the per-type log loss (equal weight per type; the one human room cannot be outvoted). Coordinate search on a coarse grid: the best point ON THE GRID, not identified parameters. The autopick sub-stages run only on rooms whose sidecar gives a non-empty away set; the tracker at each state carries that pick's away set as `away_slots`.

| room | type | league | picks | matched to board | adp | yahoo_rank | away set |
|---|---|---|---|---|---|---|---|
| 10726459 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10726459.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 4, 7, 8, 10] |
| 10727517 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10727517.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 8, 9] |
| 10728751 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10728751.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 5, 7, 10] |
| 10790713 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10790713.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 3, 4, 7, 9] |
| 10794762 | yahoo_autopick | keefamania | 150 | 141 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10794762.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 5, 6, 7, 8, 10] |
| 10795644 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10795644.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 4, 6, 8, 9] |
| 10796348 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10796348.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 3, 4, 5, 6, 10] |
| 10797402 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10797402.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 3, 4, 5, 7, 9, 10] |
| 10798461 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10798461.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 4, 5, 7] |
| 10799518 | yahoo_autopick | keefamania | 150 | 140 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10799518.json (226/226 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [1, 2, 3, 4, 6, 7, 8, 10] |
| 10800397 | yahoo_autopick | keefamania | 150 | 141 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10800397.json (226/226 board rows) | sidecar: away set non-empty at 98/150 picks, slots seen [1, 2, 5, 6, 7, 9, 10] |

## Current knobs {'sigma_early': 10.0, 'sigma_late': 45.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.2, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'order'}: objective 0.5781 yahoo_autopick 0.1880 (n 72180, errors 0)

## Stage: rival_x_sigma (11 room(s): 10726459, 10727517, 10728751, 10790713, 10794762, 10795644, 10796348, 10797402, 10798461, 10799518, 10800397)

| point | objective | yahoo_autopick | pool / shown |
|---|---|---|---|
| {'rival_draw': 'lottery', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.5490 | 0.1663 | pool 0.1663 shown 0.5490 (n 5518) |
| {'rival_draw': 'lottery', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.6005 | 0.1826 | pool 0.1826 shown 0.6005 (n 5520) |
| {'rival_draw': 'lottery', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.6316 | 0.1960 | pool 0.1960 shown 0.6316 (n 5522) |
| {'rival_draw': 'lottery', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.6534 | 0.2046 | pool 0.2046 shown 0.6534 (n 5521) |
| {'rival_draw': 'floored', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.5444 | 0.1644 | pool 0.1644 shown 0.5444 (n 5515) |
| {'rival_draw': 'floored', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.5983 | 0.1806 | pool 0.1806 shown 0.5983 (n 5516) |
| {'rival_draw': 'floored', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.6304 | 0.1952 | pool 0.1952 shown 0.6304 (n 5519) |
| {'rival_draw': 'floored', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.6541 | 0.2037 | pool 0.2037 shown 0.6541 (n 5518) |
| {'rival_draw': 'order', 'sigma_early': 6.0, 'sigma_late': 27.0} | 0.5835 | 0.2018 | pool 0.2018 shown 0.5835 (n 5514) |
| {'rival_draw': 'order', 'sigma_early': 10.0, 'sigma_late': 45.0} | 0.5781 | 0.1880 | pool 0.1880 shown 0.5781 (n 5514) |
| {'rival_draw': 'order', 'sigma_early': 15.0, 'sigma_late': 67.5} | 0.6032 | 0.1859 | pool 0.1859 shown 0.6032 (n 5515) |
| {'rival_draw': 'order', 'sigma_early': 20.0, 'sigma_late': 90.0} | 0.6248 | 0.1887 | pool 0.1887 shown 0.6248 (n 5515) |

best after rival_x_sigma: {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.2, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'floored'} (objective 0.5444)

## Stage: autopick_list_prob (11 room(s): 10726459, 10727517, 10728751, 10790713, 10794762, 10795644, 10796348, 10797402, 10798461, 10799518, 10800397)

| point | objective | yahoo_autopick | pool / shown |
|---|---|---|---|
| {'autopick_list_prob': 0.0} | 0.5590 | 0.1699 | pool 0.1699 shown 0.5590 (n 5514) |
| {'autopick_list_prob': 0.2} | 0.5444 | 0.1644 | pool 0.1644 shown 0.5444 (n 5515) |
| {'autopick_list_prob': 0.4} | 0.5291 | 0.1629 | pool 0.1629 shown 0.5291 (n 5516) |

best after autopick_list_prob: {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.4, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'floored'} (objective 0.5291)

## Confirmation at sims 1000

### current: {'sigma_early': 10.0, 'sigma_late': 45.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.2, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'order'} -> objective 0.5848 yahoo_autopick 0.1863

pooled (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1699 | 132 | 13% | 40% | +27% | [+20%, +34%] | 1.243 |
| 30-49% | 1278 | 145 | 40% | 43% | +3% | [-2%, +9%] | 0.692 |
| 50-69% | 2136 | 150 | 61% | 62% | +2% | [-2%, +5%] | 0.647 |
| 70-89% | 6279 | 151 | 82% | 83% | +1% | [-0%, +3%] | 0.447 |
| 90-100% | 60788 | 151 | 98% | 98% | -1% | [-1%, -0%] | 0.118 |

pooled SHOWN (engine top-8) (n=5516)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 612 | 88 | 14% | 17% | +3% | [-2%, +9%] | 0.424 |
| 30-49% | 473 | 113 | 40% | 28% | -12% | [-18%, -5%] | 0.630 |
| 50-69% | 625 | 128 | 60% | 42% | -17% | [-23%, -12%] | 0.730 |
| 70-89% | 1073 | 139 | 81% | 68% | -13% | [-17%, -9%] | 0.668 |
| 90-100% | 2733 | 149 | 97% | 89% | -9% | [-11%, -6%] | 0.661 |

human (n=0)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 0 | 0 | - | - | - | - | - |
| 50-69% | 0 | 0 | - | - | - | - | - |
| 70-89% | 0 | 0 | - | - | - | - | - |
| 90-100% | 0 | 0 | - | - | - | - | - |

human SHOWN (engine top-8) (n=0)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 0 | 0 | - | - | - | - | - |
| 50-69% | 0 | 0 | - | - | - | - | - |
| 70-89% | 0 | 0 | - | - | - | - | - |
| 90-100% | 0 | 0 | - | - | - | - | - |

autopick (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1699 | 132 | 13% | 40% | +27% | [+20%, +34%] | 1.243 |
| 30-49% | 1278 | 145 | 40% | 43% | +3% | [-2%, +9%] | 0.692 |
| 50-69% | 2136 | 150 | 61% | 62% | +2% | [-2%, +5%] | 0.647 |
| 70-89% | 6279 | 151 | 82% | 83% | +1% | [-0%, +3%] | 0.447 |
| 90-100% | 60788 | 151 | 98% | 98% | -1% | [-1%, -0%] | 0.118 |

autopick SHOWN (engine top-8) (n=5516)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 612 | 88 | 14% | 17% | +3% | [-2%, +9%] | 0.424 |
| 30-49% | 473 | 113 | 40% | 28% | -12% | [-18%, -5%] | 0.630 |
| 50-69% | 625 | 128 | 60% | 42% | -17% | [-23%, -12%] | 0.730 |
| 70-89% | 1073 | 139 | 81% | 68% | -13% | [-17%, -9%] | 0.668 |
| 90-100% | 2733 | 149 | 97% | 89% | -9% | [-11%, -6%] | 0.661 |

yahoo_autopick (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1699 | 132 | 13% | 40% | +27% | [+20%, +34%] | 1.243 |
| 30-49% | 1278 | 145 | 40% | 43% | +3% | [-2%, +9%] | 0.692 |
| 50-69% | 2136 | 150 | 61% | 62% | +2% | [-2%, +5%] | 0.647 |
| 70-89% | 6279 | 151 | 82% | 83% | +1% | [-0%, +3%] | 0.447 |
| 90-100% | 60788 | 151 | 98% | 98% | -1% | [-1%, -0%] | 0.118 |

yahoo_autopick SHOWN (engine top-8) (n=5516)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 612 | 88 | 14% | 17% | +3% | [-2%, +9%] | 0.424 |
| 30-49% | 473 | 113 | 40% | 28% | -12% | [-18%, -5%] | 0.630 |
| 50-69% | 625 | 128 | 60% | 42% | -17% | [-23%, -12%] | 0.730 |
| 70-89% | 1073 | 139 | 81% | 68% | -13% | [-17%, -9%] | 0.668 |
| 90-100% | 2733 | 149 | 97% | 89% | -9% | [-11%, -6%] | 0.661 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 72180 | FAIL 0-29% (obs-pred +27%, CI [+20%, +34%], n 1699, clusters 132); 90-100% (obs-pred -1%, CI [-1%, -0%], n 60788, clusters 151) | FAIL 0-29% (pred 13% obs 40%, n 1699) |
| human | 0 | PASS | PASS |
| autopick | 72180 | FAIL 0-29% (obs-pred +27%, CI [+20%, +34%], n 1699, clusters 132); 90-100% (obs-pred -1%, CI [-1%, -0%], n 60788, clusters 151) | FAIL 0-29% (pred 13% obs 40%, n 1699) |

### fitted: {'sigma_early': 6.0, 'sigma_late': 27.0, 'reach_prob': 0.15, 'need_damp': 0.15, 'autopick_list_prob': 0.4, 'autopick_sigma_scale': 0.5, 'autopick_need_damp': 0.02, 'rival_draw': 'floored'} -> objective 0.5252 yahoo_autopick 0.1609

pooled (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1049 | 123 | 16% | 20% | +4% | [-2%, +12%] | 0.547 |
| 30-49% | 1194 | 134 | 40% | 29% | -11% | [-15%, -6%] | 0.623 |
| 50-69% | 2168 | 145 | 61% | 59% | -2% | [-4%, +0%] | 0.663 |
| 70-89% | 8063 | 150 | 82% | 87% | +5% | [+3%, +6%] | 0.390 |
| 90-100% | 59706 | 151 | 98% | 98% | +0% | [-0%, +0%] | 0.097 |

pooled SHOWN (engine top-8) (n=5515)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 517 | 98 | 16% | 14% | -2% | [-7%, +3%] | 0.415 |
| 30-49% | 488 | 109 | 40% | 21% | -19% | [-23%, -14%] | 0.585 |
| 50-69% | 709 | 130 | 60% | 43% | -17% | [-21%, -12%] | 0.732 |
| 70-89% | 1236 | 135 | 81% | 73% | -8% | [-12%, -5%] | 0.583 |
| 90-100% | 2565 | 150 | 96% | 88% | -8% | [-11%, -5%] | 0.459 |

human (n=0)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 0 | 0 | - | - | - | - | - |
| 50-69% | 0 | 0 | - | - | - | - | - |
| 70-89% | 0 | 0 | - | - | - | - | - |
| 90-100% | 0 | 0 | - | - | - | - | - |

human SHOWN (engine top-8) (n=0)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 0 | 0 | - | - | - | - | - |
| 30-49% | 0 | 0 | - | - | - | - | - |
| 50-69% | 0 | 0 | - | - | - | - | - |
| 70-89% | 0 | 0 | - | - | - | - | - |
| 90-100% | 0 | 0 | - | - | - | - | - |

autopick (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1049 | 123 | 16% | 20% | +4% | [-2%, +12%] | 0.547 |
| 30-49% | 1194 | 134 | 40% | 29% | -11% | [-15%, -6%] | 0.623 |
| 50-69% | 2168 | 145 | 61% | 59% | -2% | [-4%, +0%] | 0.663 |
| 70-89% | 8063 | 150 | 82% | 87% | +5% | [+3%, +6%] | 0.390 |
| 90-100% | 59706 | 151 | 98% | 98% | +0% | [-0%, +0%] | 0.097 |

autopick SHOWN (engine top-8) (n=5515)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 517 | 98 | 16% | 14% | -2% | [-7%, +3%] | 0.415 |
| 30-49% | 488 | 109 | 40% | 21% | -19% | [-23%, -14%] | 0.585 |
| 50-69% | 709 | 130 | 60% | 43% | -17% | [-21%, -12%] | 0.732 |
| 70-89% | 1236 | 135 | 81% | 73% | -8% | [-12%, -5%] | 0.583 |
| 90-100% | 2565 | 150 | 96% | 88% | -8% | [-11%, -5%] | 0.459 |

yahoo_autopick (n=72180)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 1049 | 123 | 16% | 20% | +4% | [-2%, +12%] | 0.547 |
| 30-49% | 1194 | 134 | 40% | 29% | -11% | [-15%, -6%] | 0.623 |
| 50-69% | 2168 | 145 | 61% | 59% | -2% | [-4%, +0%] | 0.663 |
| 70-89% | 8063 | 150 | 82% | 87% | +5% | [+3%, +6%] | 0.390 |
| 90-100% | 59706 | 151 | 98% | 98% | +0% | [-0%, +0%] | 0.097 |

yahoo_autopick SHOWN (engine top-8) (n=5515)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 517 | 98 | 16% | 14% | -2% | [-7%, +3%] | 0.415 |
| 30-49% | 488 | 109 | 40% | 21% | -19% | [-23%, -14%] | 0.585 |
| 50-69% | 709 | 130 | 60% | 43% | -17% | [-21%, -12%] | 0.732 |
| 70-89% | 1236 | 135 | 81% | 73% | -8% | [-12%, -5%] | 0.583 |
| 90-100% | 2565 | 150 | 96% | 88% | -8% | [-11%, -5%] | 0.459 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 72180 | FAIL 30-49% (obs-pred -11%, CI [-15%, -6%], n 1194, clusters 134); 70-89% (obs-pred +5%, CI [+3%, +6%], n 8063, clusters 150) | FAIL 30-49% (pred 40% obs 29%, n 1194) |
| human | 0 | PASS | PASS |
| autopick | 72180 | FAIL 30-49% (obs-pred -11%, CI [-15%, -6%], n 1194, clusters 134); 70-89% (obs-pred +5%, CI [+3%, +6%], n 8063, clusters 150) | FAIL 30-49% (pred 40% obs 29%, n 1194) |

## Empirical need damp (closed-slot take rate vs the ADP mass, one parameter, by room type)

| room type | picks | filled no open starter slot | implied damp | in use |
|---|---|---|---|---|
| yahoo_autopick | 1650 | 667 | 0.53 | 0.15 |

Wall time 1159 s.

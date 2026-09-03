# Survival refit: leave-one-room-out (DECISIONS #35 G2)

Stage autopick; sims 200, every 2, real seat. For each room the stage fits on: coordinate fit on the OTHER rooms from CURRENT, then the held-out room's Bernoulli log-loss at that fitted point and at CURRENT. Held-out numbers are the only ones that count; the fitted point per fold is reported at grid precision.

| room | type | league | picks | matched to board | adp | yahoo_rank | away set |
|---|---|---|---|---|---|---|---|
| 1395566812157984768 | sleeper_human | omnibeta | 180 | 180 | adp_2026-08-19.json (230/294 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396184666897145856 | sleeper_mock | keefamania | 150 | 148 | adp_2026-08-19.json (205/238 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396191077534281728 | sleeper_mock | omnibeta | 46 | 46 | adp_2026-08-19.json (230/294 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 1396194982775238656 | sleeper_mock | keefamania | 28 | 28 | adp_2026-08-19.json (205/238 board rows overridden) | - | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10502459 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10503516 | yahoo_autopick | keefamania | 150 | 137 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10504572 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10505450 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| 10531886 | yahoo_autopick | keefamania | 150 | 138 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | sidecar: away set non-empty at 143/150 picks, slots seen [3, 4, 5, 7, 8, 9] |
| 10532940 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | sidecar: away set non-empty at 150/150 picks, slots seen [2, 5, 6, 7, 8, 9, 10] |
| 10534350 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: mock_players_10534350.json (238/238 board rows) | sidecar: away set non-empty at 139/150 picks, slots seen [1, 2, 3, 7, 8] |
| 10584427 | yahoo_autopick | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | sidecar: away set non-empty at 146/150 picks, slots seen [2, 4, 5, 6, 10] |
| email1a059ffa1d94f905 | yahoo_email | keefamania | 23 | 23 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a050324118c1 | yahoo_email | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a43675df6ac2 | yahoo_email | keefamania | 150 | 137 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05a720ce261afe | yahoo_email | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |
| email1a05aae58012b315 | yahoo_email | keefamania | 150 | 139 | board adp (Yahoo rank on this league's board) | yahoo_rank: players_10584427.json (238/238 board rows) | no sidecar: empty away set at every pick (autopick branch not exercised) |

| held-out room | type | n rows | fitted point (fold) | held-out at fitted | at CURRENT | delta |
|---|---|---|---|---|---|---|
| 10531886 | yahoo_autopick | 6521 | {'autopick_list_prob': 0.3, 'autopick_need_damp': 0.45} | 0.1520 | 0.1632 | -0.0111 |
| 10532940 | yahoo_autopick | 6254 | {'autopick_list_prob': 0.4, 'autopick_need_damp': 0.45} | 0.1688 | 0.1889 | -0.0201 |
| 10534350 | yahoo_autopick | 6432 | {'autopick_list_prob': 0.3, 'autopick_need_damp': 0.45} | 0.1481 | 0.1585 | -0.0104 |
| 10584427 | yahoo_autopick | 6563 | {'autopick_list_prob': 0.3, 'autopick_need_damp': 0.45} | 0.1641 | 0.1797 | -0.0155 |

Pooled mean over rooms (equal weight per room): fitted 0.1582  current 0.1726  delta -0.0143
Row-pooled held-out log-loss: fitted 0.1582  current 0.1724  delta -0.0143

## Held-out calibration (rows pooled across folds, each scored at its fold's fitted point)

### fitted (held-out)

pooled (n=25770)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 152 | 22 | 18% | 26% | +7% | [-9%, +23%] | 0.802 |
| 30-49% | 441 | 44 | 41% | 32% | -8% | [-14%, -1%] | 0.638 |
| 50-69% | 828 | 56 | 60% | 55% | -5% | [-8%, -2%] | 0.678 |
| 70-89% | 2809 | 59 | 82% | 84% | +2% | [+0%, +4%] | 0.424 |
| 90-100% | 21540 | 60 | 97% | 98% | +1% | [+0%, +1%] | 0.096 |

autopick (n=25770)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 152 | 22 | 18% | 26% | +7% | [-9%, +23%] | 0.802 |
| 30-49% | 441 | 44 | 41% | 32% | -8% | [-14%, -1%] | 0.638 |
| 50-69% | 828 | 56 | 60% | 55% | -5% | [-8%, -2%] | 0.678 |
| 70-89% | 2809 | 59 | 82% | 84% | +2% | [+0%, +4%] | 0.424 |
| 90-100% | 21540 | 60 | 97% | 98% | +1% | [+0%, +1%] | 0.096 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 25770 | FAIL 30-49% (obs-pred -8%, CI [-14%, -1%], n 441, clusters 44); 50-69% (obs-pred -5%, CI [-8%, -2%], n 828, clusters 56); 70-89% (obs-pred +2%, CI [+0%, +4%], n 2809, clusters 59); 90-100% (obs-pred +1%, CI [+0%, +1%], n 21540, clusters 60) | FAIL 30-49% (pred 41% obs 32%, n 441) |
| human | 0 | PASS | PASS |
| autopick | 25770 | FAIL 30-49% (obs-pred -8%, CI [-14%, -1%], n 441, clusters 44); 50-69% (obs-pred -5%, CI [-8%, -2%], n 828, clusters 56); 70-89% (obs-pred +2%, CI [+0%, +4%], n 2809, clusters 59); 90-100% (obs-pred +1%, CI [+0%, +1%], n 21540, clusters 60) | FAIL 30-49% (pred 41% obs 32%, n 441) |

### current

pooled (n=25770)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 95 | 11 | 20% | 39% | +19% | [-0%, +40%] | 0.795 |
| 30-49% | 420 | 29 | 41% | 41% | -0% | [-9%, +9%] | 0.678 |
| 50-69% | 1027 | 50 | 61% | 63% | +3% | [-3%, +8%] | 0.649 |
| 70-89% | 2926 | 59 | 81% | 83% | +2% | [-0%, +4%] | 0.441 |
| 90-100% | 21302 | 60 | 98% | 98% | +0% | [-0%, +1%] | 0.108 |

autopick (n=25770)

| predicted | n | clusters | predicted avg | observed | obs-pred | 90% CI (cluster bootstrap) | log loss |
|---|---|---|---|---|---|---|---|
| 0-29% | 95 | 11 | 20% | 39% | +19% | [-0%, +40%] | 0.795 |
| 30-49% | 420 | 29 | 41% | 41% | -0% | [-9%, +9%] | 0.678 |
| 50-69% | 1027 | 50 | 61% | 63% | +3% | [-3%, +8%] | 0.649 |
| 70-89% | 2926 | 59 | 81% | 83% | +2% | [-0%, +4%] | 0.441 |
| 90-100% | 21302 | 60 | 98% | 98% | +0% | [-0%, +1%] | 0.108 |

## Calibration bars (three views; CI bar = DECISIONS #35 G2: a bucket fails only when its cluster-bootstrap 90% CI of obs-pred excludes 0 with >= 30 clusters; 8-point bar = DECISIONS #26, n >= 15, for continuity)

| view | n | CI bar | 8-point bar |
|---|---|---|---|
| pooled | 25770 | PASS | FAIL 0-29% (pred 20% obs 39%, n 95) |
| human | 0 | PASS | PASS |
| autopick | 25770 | PASS | FAIL 0-29% (pred 20% obs 39%, n 95) |

Wall time 704 s.

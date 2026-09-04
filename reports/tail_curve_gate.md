# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`blend`) and `external` is the candidate (`blend_rank_lin`); rivals judged: `blend`.

Decision: **split** — accuracy pass, outcome FAIL. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 57.8 | 57.5 | 0.996 | 0.476 | 0.474 | -0.002 | yes |
| omnibeta | 301 | 63.0 | 62.9 | 0.998 | 0.467 | 0.470 | +0.003 | yes |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 68.6 | 68.5 | 0.561 | 0.546 |
| keefamania | 2023->2024 | RB | 44 | 56.0 | 54.8 | 0.597 | 0.599 |
| keefamania | 2023->2024 | TE | 16 | 36.8 | 37.1 | 0.556 | 0.556 |
| keefamania | 2023->2024 | WR | 55 | 50.9 | 51.1 | 0.481 | 0.483 |
| keefamania | 2024->2025 | QB | 19 | 77.2 | 76.7 | -0.082 | -0.082 |
| keefamania | 2024->2025 | RB | 37 | 68.2 | 68.6 | 0.634 | 0.641 |
| keefamania | 2024->2025 | TE | 13 | 37.3 | 37.2 | 0.110 | 0.071 |
| keefamania | 2024->2025 | WR | 50 | 59.6 | 59.0 | 0.493 | 0.490 |
| omnibeta | 2023->2024 | QB | 22 | 75.4 | 75.2 | 0.417 | 0.421 |
| omnibeta | 2023->2024 | RB | 48 | 59.3 | 58.2 | 0.614 | 0.609 |
| omnibeta | 2023->2024 | TE | 18 | 46.2 | 46.4 | 0.614 | 0.633 |
| omnibeta | 2023->2024 | WR | 58 | 60.2 | 61.0 | 0.470 | 0.472 |
| omnibeta | 2024->2025 | QB | 26 | 71.9 | 71.6 | 0.105 | 0.082 |
| omnibeta | 2024->2025 | RB | 44 | 70.6 | 70.6 | 0.637 | 0.657 |
| omnibeta | 2024->2025 | TE | 21 | 45.1 | 44.8 | 0.131 | 0.147 |
| omnibeta | 2024->2025 | WR | 64 | 65.8 | 65.6 | 0.471 | 0.471 |

## Test 2 — outcome (shared ADP-order rivals, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1554.5, external 1530.8 (Δ -23.7, -1.53%); external better in 25, worse in 18, tied 1. Pass: NO.

| league | pair | model mean | external mean | Δ |
|---|---|---|---|---|
| keefamania | 2023->2024 | 1464.4 | 1501.0 | +36.7 |
| keefamania | 2024->2025 | 1351.3 | 1283.2 | -68.2 |
| omnibeta | 2023->2024 | 1747.5 | 1636.6 | -110.9 |
| omnibeta | 2024->2025 | 1605.9 | 1656.1 | +50.2 |

### keefamania 2023->2024 — 10 teams, 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1362 | 1424 | +62 | 0/0 |
| 2 | 1451 | 1513 | +62 | 0/0 |
| 3 | 1451 | 1513 | +62 | 0/0 |
| 4 | 1383 | 1482 | +100 | 0/0 |
| 5 | 1449 | 1546 | +98 | 0/0 |
| 6 | 1610 | 1559 | -51 | 0/0 |
| 7 | 1650 | 1559 | -91 | 0/0 |
| 8 | 1515 | 1566 | +51 | 0/0 |
| 9 | 1387 | 1449 | +62 | 0/0 |
| 10 | 1387 | 1399 | +13 | 0/0 |

### keefamania 2024->2025 — 10 teams, 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1397 | 1470 | +73 | 0/0 |
| 2 | 1355 | 1159 | -196 | 0/0 |
| 3 | 1438 | 1439 | +2 | 0/0 |
| 4 | 1385 | 1287 | -98 | 0/0 |
| 5 | 1385 | 1224 | -161 | 0/0 |
| 6 | 1338 | 1224 | -114 | 0/0 |
| 7 | 1374 | 1480 | +106 | 0/0 |
| 8 | 1321 | 1197 | -124 | 0/0 |
| 9 | 1321 | 1197 | -124 | 0/0 |
| 10 | 1198 | 1152 | -46 | 0/0 |

### omnibeta 2023->2024 — 12 teams, 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1691 | 1732 | +41 | 0/0 |
| 2 | 1678 | 1697 | +19 | 0/0 |
| 3 | 1646 | 1700 | +54 | 0/0 |
| 4 | 1557 | 1527 | -30 | 0/0 |
| 5 | 1952 | 1600 | -351 | 0/0 |
| 6 | 1952 | 1600 | -351 | 0/0 |
| 7 | 1957 | 1600 | -357 | 0/0 |
| 8 | 1917 | 1647 | -270 | 0/0 |
| 9 | 1782 | 1472 | -310 | 0/0 |
| 10 | 1657 | 1657 | +0 | 0/0 |
| 11 | 1540 | 1713 | +172 | 0/0 |
| 12 | 1640 | 1694 | +54 | 0/0 |

### omnibeta 2024->2025 — 12 teams, 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1810 | 1842 | +32 | 0/0 |
| 2 | 1589 | 1658 | +69 | 0/0 |
| 3 | 1604 | 1658 | +54 | 0/0 |
| 4 | 1604 | 1507 | -97 | 0/0 |
| 5 | 1603 | 1572 | -31 | 0/0 |
| 6 | 1429 | 1572 | +144 | 0/0 |
| 7 | 1458 | 1572 | +114 | 0/0 |
| 8 | 1716 | 1831 | +116 | 0/0 |
| 9 | 1714 | 1831 | +117 | 0/0 |
| 10 | 1706 | 1780 | +74 | 0/0 |
| 11 | 1533 | 1499 | -34 | 0/0 |
| 12 | 1506 | 1549 | +43 | 0/0 |

Both arms face one rival list (the year's pool in ADP order), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ. Rivals never deviate from ADP, so runs and reaches are absent. K/DEF are absent from both arms. The history rows carry no team or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.


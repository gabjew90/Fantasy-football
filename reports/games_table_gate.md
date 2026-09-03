# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`blend`) and `external` is the candidate (`blend_gt`); rivals judged: `blend`.

Decision: **stay** — accuracy FAIL, outcome FAIL. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 57.8 | 59.1 | 1.023 | 0.476 | 0.479 | +0.004 | NO |
| omnibeta | 301 | 63.0 | 64.3 | 1.020 | 0.467 | 0.465 | -0.002 | yes |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 68.6 | 71.3 | 0.561 | 0.556 |
| keefamania | 2023->2024 | RB | 44 | 56.0 | 54.7 | 0.597 | 0.611 |
| keefamania | 2023->2024 | TE | 16 | 36.8 | 38.4 | 0.556 | 0.571 |
| keefamania | 2023->2024 | WR | 55 | 50.9 | 54.0 | 0.481 | 0.468 |
| keefamania | 2024->2025 | QB | 19 | 77.2 | 84.2 | -0.082 | -0.077 |
| keefamania | 2024->2025 | RB | 37 | 68.2 | 65.2 | 0.634 | 0.657 |
| keefamania | 2024->2025 | TE | 13 | 37.3 | 37.9 | 0.110 | 0.099 |
| keefamania | 2024->2025 | WR | 50 | 59.6 | 62.0 | 0.493 | 0.494 |
| omnibeta | 2023->2024 | QB | 22 | 75.4 | 76.4 | 0.417 | 0.495 |
| omnibeta | 2023->2024 | RB | 48 | 59.3 | 57.8 | 0.614 | 0.610 |
| omnibeta | 2023->2024 | TE | 18 | 46.2 | 49.1 | 0.614 | 0.626 |
| omnibeta | 2023->2024 | WR | 58 | 60.2 | 63.5 | 0.470 | 0.461 |
| omnibeta | 2024->2025 | QB | 26 | 71.9 | 75.1 | 0.105 | 0.063 |
| omnibeta | 2024->2025 | RB | 44 | 70.6 | 68.7 | 0.637 | 0.626 |
| omnibeta | 2024->2025 | TE | 21 | 45.1 | 46.7 | 0.131 | 0.112 |
| omnibeta | 2024->2025 | WR | 64 | 65.8 | 68.2 | 0.471 | 0.470 |

## Test 2 — outcome (shared ADP-order rivals, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1561.7, external 1544.1 (Δ -17.6, -1.13%); external better in 13, worse in 27, tied 4. Pass: NO.

| league | pair | model mean | external mean | Δ |
|---|---|---|---|---|
| keefamania | 2023->2024 | 1469.3 | 1482.5 | +13.1 |
| keefamania | 2024->2025 | 1351.9 | 1388.1 | +36.2 |
| omnibeta | 2023->2024 | 1769.5 | 1752.7 | -16.8 |
| omnibeta | 2024->2025 | 1605.8 | 1517.0 | -88.8 |

### keefamania 2023->2024 — 10 teams, 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1381 | 1362 | -19 | 0/0 |
| 2 | 1470 | 1513 | +43 | 0/0 |
| 3 | 1475 | 1517 | +43 | 0/0 |
| 4 | 1417 | 1398 | -19 | 0/0 |
| 5 | 1485 | 1449 | -36 | 0/0 |
| 6 | 1610 | 1562 | -48 | 0/0 |
| 7 | 1596 | 1562 | -34 | 0/0 |
| 8 | 1515 | 1557 | +42 | 0/0 |
| 9 | 1359 | 1453 | +94 | 0/0 |
| 10 | 1387 | 1453 | +66 | 0/0 |

### keefamania 2024->2025 — 10 teams, 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1397 | 1370 | -27 | 0/0 |
| 2 | 1361 | 1334 | -27 | 0/0 |
| 3 | 1438 | 1411 | -27 | 0/0 |
| 4 | 1385 | 1582 | +197 | 0/0 |
| 5 | 1385 | 1385 | +0 | 0/0 |
| 6 | 1338 | 1338 | +0 | 0/0 |
| 7 | 1374 | 1374 | +0 | 0/0 |
| 8 | 1321 | 1358 | +37 | 0/0 |
| 9 | 1321 | 1358 | +37 | 0/0 |
| 10 | 1198 | 1369 | +171 | 0/0 |

### omnibeta 2023->2024 — 12 teams, 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1691 | 1600 | -91 | 0/0 |
| 2 | 1678 | 1678 | +0 | 0/0 |
| 3 | 1646 | 1563 | -84 | 0/0 |
| 4 | 1557 | 1763 | +205 | 0/0 |
| 5 | 1952 | 1837 | -115 | 0/0 |
| 6 | 1952 | 1837 | -115 | 0/0 |
| 7 | 1957 | 1842 | -115 | 0/0 |
| 8 | 1895 | 1842 | -52 | 0/0 |
| 9 | 1860 | 1760 | -100 | 0/0 |
| 10 | 1670 | 1750 | +80 | 0/0 |
| 11 | 1736 | 1780 | +44 | 0/0 |
| 12 | 1640 | 1780 | +140 | 0/0 |

### omnibeta 2024->2025 — 12 teams, 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1810 | 1780 | -30 | 0/0 |
| 2 | 1589 | 1542 | -46 | 0/0 |
| 3 | 1604 | 1523 | -81 | 0/0 |
| 4 | 1604 | 1523 | -81 | 0/0 |
| 5 | 1603 | 1523 | -81 | 0/0 |
| 6 | 1429 | 1405 | -24 | 0/0 |
| 7 | 1458 | 1284 | -174 | 0/0 |
| 8 | 1714 | 1576 | -138 | 0/0 |
| 9 | 1714 | 1576 | -138 | 0/0 |
| 10 | 1706 | 1699 | -7 | 0/0 |
| 11 | 1533 | 1519 | -14 | 0/0 |
| 12 | 1506 | 1253 | -253 | 0/0 |

Both arms face one rival list (the year's pool in ADP order), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ. Rivals never deviate from ADP, so runs and reaches are absent. K/DEF are absent from both arms. The history rows carry no team or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.


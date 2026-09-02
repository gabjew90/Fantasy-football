# Projection-source gate (DECISIONS #23)

Decision: **stay** — accuracy FAIL, outcome FAIL. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 57.8 | 60.8 | 1.053 | 0.476 | 0.465 | -0.011 | NO |
| omnibeta | 301 | 63.0 | 66.0 | 1.047 | 0.467 | 0.464 | -0.003 | NO |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 68.6 | 78.5 | 0.561 | 0.586 |
| keefamania | 2023->2024 | RB | 44 | 56.0 | 54.9 | 0.597 | 0.613 |
| keefamania | 2023->2024 | TE | 16 | 36.8 | 45.1 | 0.556 | 0.515 |
| keefamania | 2023->2024 | WR | 55 | 50.9 | 51.9 | 0.481 | 0.457 |
| keefamania | 2024->2025 | QB | 19 | 77.2 | 88.0 | -0.082 | -0.253 |
| keefamania | 2024->2025 | RB | 37 | 68.2 | 66.5 | 0.634 | 0.654 |
| keefamania | 2024->2025 | TE | 13 | 37.3 | 40.9 | 0.110 | 0.225 |
| keefamania | 2024->2025 | WR | 50 | 59.6 | 64.6 | 0.493 | 0.474 |
| omnibeta | 2023->2024 | QB | 22 | 75.4 | 80.2 | 0.417 | 0.544 |
| omnibeta | 2023->2024 | RB | 48 | 59.3 | 58.9 | 0.614 | 0.626 |
| omnibeta | 2023->2024 | TE | 18 | 46.2 | 50.7 | 0.614 | 0.560 |
| omnibeta | 2023->2024 | WR | 58 | 60.2 | 62.2 | 0.470 | 0.471 |
| omnibeta | 2024->2025 | QB | 26 | 71.9 | 85.5 | 0.105 | -0.091 |
| omnibeta | 2024->2025 | RB | 44 | 70.6 | 67.3 | 0.637 | 0.660 |
| omnibeta | 2024->2025 | TE | 21 | 45.1 | 46.6 | 0.131 | 0.318 |
| omnibeta | 2024->2025 | WR | 64 | 65.8 | 71.7 | 0.471 | 0.420 |

## Test 2 — outcome (shared ADP-order rivals, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1558.2, external 1539.5 (Δ -18.8, -1.20%); external better in 20, worse in 24, tied 0. Pass: NO.

| league | pair | model mean | external mean | Δ |
|---|---|---|---|---|
| keefamania | 2023->2024 | 1471.9 | 1484.8 | +12.9 |
| keefamania | 2024->2025 | 1351.9 | 1449.8 | +97.9 |
| omnibeta | 2023->2024 | 1754.4 | 1636.3 | -118.1 |
| omnibeta | 2024->2025 | 1605.8 | 1562.8 | -43.0 |

### keefamania 2023->2024 — 10 teams, 13 rounds, rival pool 158, boards 152 / 145

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1381 | 1549 | +168 | 0/0 |
| 2 | 1470 | 1549 | +79 | 0/0 |
| 3 | 1475 | 1549 | +74 | 0/0 |
| 4 | 1443 | 1549 | +106 | 0/0 |
| 5 | 1485 | 1500 | +15 | 0/0 |
| 6 | 1610 | 1502 | -108 | 0/0 |
| 7 | 1596 | 1502 | -94 | 0/0 |
| 8 | 1515 | 1509 | -6 | 0/0 |
| 9 | 1359 | 1378 | +19 | 0/0 |
| 10 | 1387 | 1262 | -125 | 0/0 |

### keefamania 2024->2025 — 10 teams, 13 rounds, rival pool 144, boards 143 / 135

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1397 | 1592 | +194 | 0/0 |
| 2 | 1361 | 1592 | +231 | 0/0 |
| 3 | 1438 | 1421 | -17 | 0/0 |
| 4 | 1385 | 1377 | -8 | 0/0 |
| 5 | 1385 | 1421 | +36 | 0/0 |
| 6 | 1338 | 1421 | +82 | 0/0 |
| 7 | 1374 | 1421 | +47 | 0/0 |
| 8 | 1321 | 1421 | +100 | 0/0 |
| 9 | 1321 | 1437 | +116 | 0/0 |
| 10 | 1198 | 1397 | +199 | 0/0 |

### omnibeta 2023->2024 — 12 teams, 13 rounds, rival pool 177, boards 177 / 167

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1691 | 1545 | -146 | 0/0 |
| 2 | 1678 | 1545 | -134 | 0/0 |
| 3 | 1646 | 1619 | -28 | 0/0 |
| 4 | 1557 | 1686 | +129 | 0/0 |
| 5 | 1952 | 1621 | -330 | 0/0 |
| 6 | 1952 | 1699 | -252 | 0/0 |
| 7 | 1957 | 1773 | -184 | 0/0 |
| 8 | 1895 | 1773 | -122 | 0/0 |
| 9 | 1680 | 1672 | -8 | 0/0 |
| 10 | 1670 | 1554 | -116 | 0/0 |
| 11 | 1736 | 1554 | -182 | 0/0 |
| 12 | 1640 | 1596 | -44 | 0/0 |

### omnibeta 2024->2025 — 12 teams, 13 rounds, rival pool 205, boards 205 / 187

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1810 | 1622 | -188 | 0/0 |
| 2 | 1589 | 1405 | -184 | 0/0 |
| 3 | 1604 | 1405 | -199 | 0/0 |
| 4 | 1604 | 1502 | -102 | 0/0 |
| 5 | 1603 | 1502 | -101 | 0/0 |
| 6 | 1429 | 1528 | +99 | 0/0 |
| 7 | 1458 | 1647 | +189 | 0/0 |
| 8 | 1714 | 1754 | +40 | 0/0 |
| 9 | 1714 | 1665 | -49 | 0/0 |
| 10 | 1706 | 1528 | -178 | 0/0 |
| 11 | 1533 | 1626 | +93 | 0/0 |
| 12 | 1506 | 1570 | +64 | 0/0 |

Both arms face one rival list (the year's pool in ADP order), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ. Rivals never deviate from ADP, so runs and reaches are absent. K/DEF are absent from both arms. The history rows carry no team or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.


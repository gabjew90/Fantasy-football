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

## Test 2 — outcome (ADP-order rivals, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1563.2, external 1539.0 (Δ -24.2, -1.55%); external better in 19, worse in 25, tied 0. Pass: NO.

| league | pair | model mean | external mean | Δ |
|---|---|---|---|---|
| keefamania | 2023->2024 | 1471.5 | 1494.4 | +22.9 |
| keefamania | 2024->2025 | 1343.7 | 1427.0 | +83.3 |
| omnibeta | 2023->2024 | 1780.0 | 1653.3 | -126.7 |
| omnibeta | 2024->2025 | 1605.8 | 1555.1 | -50.7 |

### keefamania 2023->2024 — 10 teams, 13 rounds, boards 152 / 145

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1381 | 1572 | +192 | 0/0 |
| 2 | 1470 | 1549 | +79 | 0/0 |
| 3 | 1470 | 1549 | +79 | 0/0 |
| 4 | 1443 | 1522 | +79 | 0/0 |
| 5 | 1485 | 1477 | -8 | 0/0 |
| 6 | 1610 | 1573 | -37 | 0/0 |
| 7 | 1596 | 1580 | -15 | 0/0 |
| 8 | 1515 | 1451 | -64 | 0/0 |
| 9 | 1359 | 1335 | -24 | 0/0 |
| 10 | 1387 | 1335 | -51 | 0/0 |

### keefamania 2024->2025 — 10 teams, 12 rounds, boards 143 / 135

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1397 | 1592 | +194 | 0/0 |
| 2 | 1361 | 1592 | +231 | 0/0 |
| 3 | 1356 | 1377 | +21 | 0/0 |
| 4 | 1385 | 1377 | -8 | 0/0 |
| 5 | 1385 | 1365 | -20 | 0/0 |
| 6 | 1338 | 1365 | +26 | 0/0 |
| 7 | 1374 | 1365 | -9 | 0/0 |
| 8 | 1321 | 1365 | +44 | 0/0 |
| 9 | 1321 | 1437 | +116 | 0/0 |
| 10 | 1198 | 1437 | +239 | 0/0 |

### omnibeta 2023->2024 — 12 teams, 12 rounds, boards 177 / 167

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1691 | 1528 | -163 | 0/0 |
| 2 | 1678 | 1588 | -90 | 0/0 |
| 3 | 1646 | 1686 | +40 | 0/0 |
| 4 | 1557 | 1686 | +129 | 0/0 |
| 5 | 1952 | 1621 | -330 | 0/0 |
| 6 | 1952 | 1623 | -329 | 0/0 |
| 7 | 1957 | 1623 | -334 | 0/0 |
| 8 | 1950 | 1600 | -350 | 0/0 |
| 9 | 1860 | 1726 | -134 | 0/0 |
| 10 | 1670 | 1726 | +56 | 0/0 |
| 11 | 1736 | 1716 | -20 | 0/0 |
| 12 | 1711 | 1716 | +5 | 0/0 |

### omnibeta 2024->2025 — 12 teams, 13 rounds, boards 205 / 187

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1810 | 1622 | -188 | 0/0 |
| 2 | 1589 | 1509 | -79 | 0/0 |
| 3 | 1604 | 1509 | -94 | 0/0 |
| 4 | 1604 | 1404 | -200 | 0/0 |
| 5 | 1603 | 1470 | -133 | 0/0 |
| 6 | 1429 | 1496 | +67 | 0/0 |
| 7 | 1458 | 1647 | +189 | 0/0 |
| 8 | 1714 | 1754 | +40 | 0/0 |
| 9 | 1714 | 1665 | -49 | 0/0 |
| 10 | 1706 | 1528 | -178 | 0/0 |
| 11 | 1533 | 1528 | -5 | 0/0 |
| 12 | 1506 | 1528 | +22 | 0/0 |

Rivals never deviate from ADP here, so runs and reaches are absent; the comparison is between the two inputs under identical rivals, which is the question. K/DEF are absent from both arms.


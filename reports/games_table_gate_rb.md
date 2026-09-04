# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`blend`) and `external` is the candidate (`blend_gt_rb`); rivals judged: `blend`.

Decision: **flip** — accuracy pass, outcome pass. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 57.8 | 57.1 | 0.988 | 0.476 | 0.481 | +0.006 | yes |
| omnibeta | 301 | 63.0 | 62.5 | 0.992 | 0.467 | 0.465 | -0.002 | yes |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 68.6 | 68.6 | 0.561 | 0.561 |
| keefamania | 2023->2024 | RB | 44 | 56.0 | 54.7 | 0.597 | 0.611 |
| keefamania | 2023->2024 | TE | 16 | 36.8 | 36.8 | 0.556 | 0.556 |
| keefamania | 2023->2024 | WR | 55 | 50.9 | 50.9 | 0.481 | 0.481 |
| keefamania | 2024->2025 | QB | 19 | 77.2 | 77.2 | -0.082 | -0.082 |
| keefamania | 2024->2025 | RB | 37 | 68.2 | 65.2 | 0.634 | 0.657 |
| keefamania | 2024->2025 | TE | 13 | 37.3 | 37.3 | 0.110 | 0.110 |
| keefamania | 2024->2025 | WR | 50 | 59.6 | 59.6 | 0.493 | 0.493 |
| omnibeta | 2023->2024 | QB | 22 | 75.4 | 75.4 | 0.417 | 0.417 |
| omnibeta | 2023->2024 | RB | 48 | 59.3 | 57.8 | 0.614 | 0.610 |
| omnibeta | 2023->2024 | TE | 18 | 46.2 | 46.2 | 0.614 | 0.614 |
| omnibeta | 2023->2024 | WR | 58 | 60.2 | 60.2 | 0.470 | 0.470 |
| omnibeta | 2024->2025 | QB | 26 | 71.9 | 71.9 | 0.105 | 0.105 |
| omnibeta | 2024->2025 | RB | 44 | 70.6 | 68.7 | 0.637 | 0.626 |
| omnibeta | 2024->2025 | TE | 21 | 45.1 | 45.1 | 0.131 | 0.131 |
| omnibeta | 2024->2025 | WR | 64 | 65.8 | 65.8 | 0.471 | 0.471 |

## Test 2 — outcome (shared rival list, engine at every slot, lineups graded on actual points)

Over 220 slot-drafts: model 1572.0, external 1564.5 (Δ -7.5, -0.48%); external better in 99, worse in 110, tied 11. Pass: yes.

Engine errors (exception → best-available fallback): `blend_gt_rb` 0, `blend` 0. Our own picks the candidate changed: 1140 of 2860.

### Is the delta bigger than the noise?

With rivals pinned to exact consensus ADP, every replay of a pair makes the same rival picks, so its slot-drafts are one draft universe sampled at each seat rather than independent draws — and neighbouring seats see nearly the same board. Each seed below redraws the rival room (Gaussian noise of 6 picks on ADP, the same draw for every arm, so the per-slot comparison stays paired).

| seed | n | Δ mean | Δ % |
|---|---|---|---|
| exact ADP | 44 | +6.8 | +0.44% |
| 1 | 44 | +6.1 | +0.37% |
| 2 | 44 | -65.6 | -4.02% |
| 3 | 44 | +42.0 | +2.84% |
| 4 | 44 | -26.9 | -1.73% |

Observed Δ -0.48%, spread across seeds 6.87 points of percentage. **The delta is inside the seed spread, so this harness cannot resolve it** at 5 seeds. The pre-registered 1% threshold is unchanged; this line records how much of the measured delta is signal, and never moves the bar.

| league | pair | seed | model mean | external mean | Δ |
|---|---|---|---|---|---|
| keefamania | 2023->2024 | exact | 1464.4 | 1501.2 | +36.8 |
| keefamania | 2023->2024 | 1 | 1537.8 | 1546.8 | +9.0 |
| keefamania | 2023->2024 | 2 | 1482.4 | 1458.3 | -24.2 |
| keefamania | 2023->2024 | 3 | 1390.8 | 1448.3 | +57.5 |
| keefamania | 2023->2024 | 4 | 1403.6 | 1430.9 | +27.2 |
| keefamania | 2024->2025 | exact | 1351.3 | 1420.1 | +68.8 |
| keefamania | 2024->2025 | 1 | 1451.4 | 1455.0 | +3.6 |
| keefamania | 2024->2025 | 2 | 1432.0 | 1391.0 | -41.0 |
| keefamania | 2024->2025 | 3 | 1313.4 | 1417.0 | +103.6 |
| keefamania | 2024->2025 | 4 | 1400.6 | 1407.5 | +6.9 |
| omnibeta | 2023->2024 | exact | 1747.5 | 1704.5 | -43.0 |
| omnibeta | 2023->2024 | 1 | 1857.3 | 1804.1 | -53.2 |
| omnibeta | 2023->2024 | 2 | 1809.1 | 1664.6 | -144.5 |
| omnibeta | 2023->2024 | 3 | 1736.8 | 1730.2 | -6.6 |
| omnibeta | 2023->2024 | 4 | 1666.0 | 1639.6 | -26.4 |
| omnibeta | 2024->2025 | exact | 1605.9 | 1586.0 | -19.9 |
| omnibeta | 2024->2025 | 1 | 1684.8 | 1749.8 | +65.0 |
| omnibeta | 2024->2025 | 2 | 1737.5 | 1695.8 | -41.7 |
| omnibeta | 2024->2025 | 3 | 1425.3 | 1451.6 | +26.3 |
| omnibeta | 2024->2025 | 4 | 1693.3 | 1592.4 | -100.8 |

### keefamania 2023->2024 seed exact — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1362 | 1381 | +19 | 0/0 | 3/13 |
| 2 | 1451 | 1532 | +80 | 0/0 | 5/13 |
| 3 | 1451 | 1532 | +80 | 0/0 | 4/13 |
| 4 | 1383 | 1430 | +48 | 0/0 | 5/13 |
| 5 | 1449 | 1449 | +0 | 0/0 | 4/13 |
| 6 | 1610 | 1562 | -48 | 0/0 | 4/13 |
| 7 | 1650 | 1650 | +1 | 0/0 | 1/13 |
| 8 | 1515 | 1607 | +92 | 0/0 | 5/13 |
| 9 | 1387 | 1400 | +13 | 0/0 | 6/13 |
| 10 | 1387 | 1470 | +84 | 0/0 | 6/13 |

### keefamania 2023->2024 seed 1 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1430 | 1449 | +19 | 0/0 | 5/13 |
| 2 | 1526 | 1544 | +19 | 0/0 | 4/13 |
| 3 | 1526 | 1544 | +19 | 0/0 | 4/13 |
| 4 | 1511 | 1530 | +19 | 0/0 | 4/13 |
| 5 | 1513 | 1532 | +19 | 0/0 | 4/13 |
| 6 | 1533 | 1507 | -26 | 0/0 | 4/13 |
| 7 | 1587 | 1557 | -30 | 0/0 | 4/13 |
| 8 | 1502 | 1472 | -30 | 0/0 | 4/13 |
| 9 | 1625 | 1666 | +41 | 0/0 | 1/13 |
| 10 | 1625 | 1666 | +41 | 0/0 | 7/13 |

### keefamania 2023->2024 seed 2 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1430 | 1386 | -44 | 0/0 | 4/13 |
| 2 | 1482 | 1380 | -102 | 0/0 | 6/13 |
| 3 | 1491 | 1459 | -32 | 0/0 | 4/13 |
| 4 | 1452 | 1404 | -48 | 0/0 | 4/13 |
| 5 | 1533 | 1485 | -48 | 0/0 | 4/13 |
| 6 | 1533 | 1485 | -48 | 0/0 | 4/13 |
| 7 | 1533 | 1485 | -48 | 0/0 | 4/13 |
| 8 | 1502 | 1489 | -14 | 0/0 | 4/13 |
| 9 | 1434 | 1506 | +71 | 0/0 | 3/13 |
| 10 | 1434 | 1506 | +71 | 0/0 | 4/13 |

### keefamania 2023->2024 seed 3 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1314 | 1314 | +0 | 0/0 | 0/13 |
| 2 | 1489 | 1489 | +0 | 0/0 | 0/13 |
| 3 | 1356 | 1497 | +141 | 0/0 | 9/13 |
| 4 | 1381 | 1481 | +100 | 0/0 | 6/13 |
| 5 | 1412 | 1542 | +130 | 0/0 | 5/13 |
| 6 | 1412 | 1363 | -49 | 0/0 | 6/13 |
| 7 | 1381 | 1487 | +105 | 0/0 | 7/13 |
| 8 | 1397 | 1542 | +145 | 0/0 | 6/13 |
| 9 | 1376 | 1377 | +1 | 0/0 | 3/13 |
| 10 | 1391 | 1392 | +1 | 0/0 | 7/13 |

### keefamania 2023->2024 seed 4 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 152

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1382 | 1382 | +0 | 0/0 | 2/13 |
| 2 | 1388 | 1504 | +116 | 0/0 | 7/13 |
| 3 | 1388 | 1542 | +153 | 0/0 | 6/13 |
| 4 | 1512 | 1542 | +30 | 0/0 | 5/13 |
| 5 | 1512 | 1529 | +16 | 0/0 | 4/13 |
| 6 | 1489 | 1422 | -67 | 0/0 | 9/13 |
| 7 | 1469 | 1416 | -53 | 0/0 | 8/13 |
| 8 | 1469 | 1369 | -100 | 0/0 | 9/13 |
| 9 | 1223 | 1312 | +89 | 0/0 | 1/13 |
| 10 | 1202 | 1291 | +89 | 0/0 | 1/13 |

### keefamania 2024->2025 seed exact — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1397 | 1370 | -27 | 0/0 | 1/13 |
| 2 | 1355 | 1471 | +116 | 0/0 | 3/13 |
| 3 | 1438 | 1338 | -99 | 0/0 | 3/13 |
| 4 | 1385 | 1644 | +259 | 0/0 | 3/13 |
| 5 | 1385 | 1530 | +145 | 0/0 | 4/13 |
| 6 | 1338 | 1143 | -195 | 0/0 | 6/13 |
| 7 | 1374 | 1456 | +82 | 0/0 | 3/13 |
| 8 | 1321 | 1456 | +135 | 0/0 | 3/13 |
| 9 | 1321 | 1358 | +37 | 0/0 | 4/13 |
| 10 | 1198 | 1433 | +234 | 0/0 | 6/13 |

### keefamania 2024->2025 seed 1 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1473 | 1473 | +0 | 0/0 | 0/13 |
| 2 | 1385 | 1385 | +0 | 0/0 | 0/13 |
| 3 | 1516 | 1475 | -41 | 0/0 | 1/13 |
| 4 | 1614 | 1597 | -17 | 0/0 | 2/13 |
| 5 | 1550 | 1597 | +47 | 0/0 | 6/13 |
| 6 | 1550 | 1550 | +0 | 0/0 | 0/13 |
| 7 | 1323 | 1272 | -50 | 0/0 | 3/13 |
| 8 | 1354 | 1310 | -45 | 0/0 | 3/13 |
| 9 | 1457 | 1491 | +34 | 0/0 | 8/13 |
| 10 | 1292 | 1400 | +108 | 0/0 | 6/13 |

### keefamania 2024->2025 seed 2 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1475 | 1595 | +120 | 0/0 | 8/13 |
| 2 | 1475 | 1668 | +193 | 0/0 | 6/13 |
| 3 | 1361 | 1334 | -27 | 0/0 | 1/13 |
| 4 | 1458 | 1431 | -27 | 0/0 | 1/13 |
| 5 | 1458 | 1311 | -147 | 0/0 | 3/13 |
| 6 | 1396 | 1311 | -84 | 0/0 | 6/13 |
| 7 | 1488 | 1356 | -132 | 0/0 | 5/13 |
| 8 | 1488 | 1276 | -212 | 0/0 | 7/13 |
| 9 | 1488 | 1356 | -132 | 0/0 | 5/13 |
| 10 | 1234 | 1271 | +37 | 0/0 | 8/13 |

### keefamania 2024->2025 seed 3 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1319 | 1464 | +144 | 0/0 | 5/13 |
| 2 | 1484 | 1457 | -27 | 0/0 | 1/13 |
| 3 | 1338 | 1491 | +152 | 0/0 | 3/13 |
| 4 | 1338 | 1337 | -1 | 0/0 | 7/13 |
| 5 | 1338 | 1546 | +208 | 0/0 | 5/13 |
| 6 | 1194 | 1298 | +104 | 0/0 | 3/13 |
| 7 | 1150 | 1303 | +153 | 0/0 | 5/13 |
| 8 | 1303 | 1133 | -170 | 0/0 | 3/13 |
| 9 | 1314 | 1750 | +436 | 0/0 | 9/13 |
| 10 | 1353 | 1390 | +37 | 0/0 | 8/13 |

### keefamania 2024->2025 seed 4 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1541 | 1541 | +0 | 0/0 | 0/13 |
| 2 | 1477 | 1464 | -13 | 0/0 | 4/13 |
| 3 | 1312 | 1312 | +0 | 0/0 | 0/13 |
| 4 | 1312 | 1392 | +79 | 0/0 | 5/13 |
| 5 | 1317 | 1322 | +5 | 0/0 | 4/13 |
| 6 | 1390 | 1322 | -69 | 0/0 | 5/13 |
| 7 | 1410 | 1341 | -69 | 0/0 | 5/13 |
| 8 | 1442 | 1388 | -54 | 0/0 | 6/13 |
| 9 | 1442 | 1387 | -54 | 0/0 | 4/13 |
| 10 | 1363 | 1608 | +244 | 0/0 | 7/13 |

### omnibeta 2023->2024 seed exact — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1691 | 1600 | -91 | 0/0 | 7/13 |
| 2 | 1678 | 1512 | -167 | 0/0 | 5/13 |
| 3 | 1646 | 1519 | -128 | 0/0 | 4/13 |
| 4 | 1557 | 1732 | +175 | 0/0 | 7/13 |
| 5 | 1952 | 1733 | -219 | 0/0 | 6/13 |
| 6 | 1952 | 1733 | -219 | 0/0 | 6/13 |
| 7 | 1957 | 1935 | -22 | 0/0 | 6/13 |
| 8 | 1917 | 1931 | +14 | 0/0 | 6/13 |
| 9 | 1782 | 1860 | +78 | 0/0 | 4/13 |
| 10 | 1657 | 1665 | +8 | 0/0 | 3/13 |
| 11 | 1540 | 1617 | +77 | 0/0 | 5/13 |
| 12 | 1640 | 1617 | -22 | 0/0 | 7/13 |

### omnibeta 2023->2024 seed 1 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1781 | 1652 | -128 | 0/0 | 7/13 |
| 2 | 1781 | 1682 | -99 | 0/0 | 6/13 |
| 3 | 1797 | 1755 | -42 | 0/0 | 2/13 |
| 4 | 2019 | 1971 | -48 | 0/0 | 4/13 |
| 5 | 1976 | 1971 | -6 | 0/0 | 6/13 |
| 6 | 1976 | 1647 | -329 | 0/0 | 7/13 |
| 7 | 2019 | 1647 | -372 | 0/0 | 5/13 |
| 8 | 2030 | 2025 | -6 | 0/0 | 4/13 |
| 9 | 1550 | 1754 | +204 | 0/0 | 6/13 |
| 10 | 1776 | 1803 | +28 | 0/0 | 4/13 |
| 11 | 1776 | 1943 | +167 | 0/0 | 4/13 |
| 12 | 1806 | 1800 | -6 | 0/0 | 5/13 |

### omnibeta 2023->2024 seed 2 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1769 | 1334 | -436 | 0/0 | 7/13 |
| 2 | 1512 | 1375 | -137 | 0/0 | 5/13 |
| 3 | 1557 | 1403 | -154 | 0/0 | 4/13 |
| 4 | 1902 | 1549 | -354 | 0/0 | 11/13 |
| 5 | 1897 | 1816 | -80 | 0/0 | 5/13 |
| 6 | 1897 | 1816 | -80 | 0/0 | 7/13 |
| 7 | 1897 | 1858 | -39 | 0/0 | 7/13 |
| 8 | 1825 | 1651 | -175 | 0/0 | 8/13 |
| 9 | 1901 | 1900 | -1 | 0/0 | 5/13 |
| 10 | 1909 | 1900 | -9 | 0/0 | 5/13 |
| 11 | 1857 | 1786 | -71 | 0/0 | 4/13 |
| 12 | 1786 | 1588 | -198 | 0/0 | 7/13 |

### omnibeta 2023->2024 seed 3 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1871 | 1778 | -93 | 0/0 | 5/13 |
| 2 | 1871 | 1778 | -93 | 0/0 | 11/13 |
| 3 | 1858 | 1849 | -9 | 0/0 | 8/13 |
| 4 | 1909 | 1865 | -44 | 0/0 | 7/13 |
| 5 | 1603 | 1662 | +59 | 0/0 | 5/13 |
| 6 | 1626 | 1874 | +248 | 0/0 | 8/13 |
| 7 | 1618 | 1759 | +141 | 0/0 | 7/13 |
| 8 | 1548 | 1634 | +87 | 0/0 | 7/13 |
| 9 | 1783 | 1521 | -263 | 0/0 | 7/13 |
| 10 | 1694 | 1681 | -13 | 0/0 | 4/13 |
| 11 | 1725 | 1681 | -44 | 0/0 | 8/13 |
| 12 | 1735 | 1681 | -54 | 0/0 | 1/13 |

### omnibeta 2023->2024 seed 4 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1499 | 1554 | +55 | 0/0 | 5/13 |
| 2 | 1567 | 1408 | -159 | 0/0 | 8/13 |
| 3 | 1670 | 1374 | -297 | 0/0 | 11/13 |
| 4 | 1659 | 1678 | +19 | 0/0 | 9/13 |
| 5 | 1767 | 1599 | -168 | 0/0 | 8/13 |
| 6 | 1573 | 1554 | -18 | 0/0 | 6/13 |
| 7 | 1442 | 1609 | +167 | 0/0 | 9/13 |
| 8 | 1970 | 1757 | -214 | 0/0 | 5/13 |
| 9 | 1778 | 1860 | +81 | 0/0 | 8/13 |
| 10 | 1722 | 1860 | +138 | 0/0 | 8/13 |
| 11 | 1708 | 1787 | +78 | 0/0 | 4/13 |
| 12 | 1636 | 1636 | +0 | 0/0 | 2/13 |

### omnibeta 2024->2025 seed exact — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1810 | 1799 | -11 | 0/0 | 5/13 |
| 2 | 1589 | 1675 | +87 | 0/0 | 6/13 |
| 3 | 1604 | 1569 | -35 | 0/0 | 7/13 |
| 4 | 1604 | 1536 | -68 | 0/0 | 5/13 |
| 5 | 1603 | 1535 | -68 | 0/0 | 5/13 |
| 6 | 1429 | 1656 | +227 | 0/0 | 8/13 |
| 7 | 1458 | 1319 | -139 | 0/0 | 4/13 |
| 8 | 1716 | 1658 | -58 | 0/0 | 6/13 |
| 9 | 1714 | 1661 | -53 | 0/0 | 5/13 |
| 10 | 1706 | 1576 | -130 | 0/0 | 6/13 |
| 11 | 1533 | 1523 | -10 | 0/0 | 4/13 |
| 12 | 1506 | 1525 | +19 | 0/0 | 4/13 |

### omnibeta 2024->2025 seed 1 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1845 | 1723 | -122 | 0/0 | 6/13 |
| 2 | 1578 | 1742 | +165 | 0/0 | 7/13 |
| 3 | 1578 | 1775 | +197 | 0/0 | 7/13 |
| 4 | 1578 | 1775 | +197 | 0/0 | 7/13 |
| 5 | 1640 | 1670 | +31 | 0/0 | 6/13 |
| 6 | 1652 | 1652 | +0 | 0/0 | 2/13 |
| 7 | 1727 | 1774 | +47 | 0/0 | 7/13 |
| 8 | 1702 | 1745 | +43 | 0/0 | 9/13 |
| 9 | 1581 | 1716 | +134 | 0/0 | 6/13 |
| 10 | 1661 | 1729 | +69 | 0/0 | 5/13 |
| 11 | 1810 | 1821 | +11 | 0/0 | 4/13 |
| 12 | 1866 | 1875 | +8 | 0/0 | 2/13 |

### omnibeta 2024->2025 seed 2 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1701 | 1680 | -21 | 0/0 | 4/13 |
| 2 | 1701 | 1680 | -21 | 0/0 | 4/13 |
| 3 | 1535 | 1513 | -22 | 0/0 | 6/13 |
| 4 | 1651 | 1655 | +4 | 0/0 | 6/13 |
| 5 | 1651 | 1583 | -68 | 0/0 | 6/13 |
| 6 | 1802 | 1583 | -218 | 0/0 | 7/13 |
| 7 | 1709 | 1583 | -125 | 0/0 | 6/13 |
| 8 | 1709 | 1774 | +66 | 0/0 | 11/13 |
| 9 | 1817 | 1789 | -27 | 0/0 | 4/13 |
| 10 | 1852 | 1818 | -33 | 0/0 | 3/13 |
| 11 | 1878 | 1845 | -33 | 0/0 | 4/13 |
| 12 | 1845 | 1845 | +0 | 0/0 | 2/13 |

### omnibeta 2024->2025 seed 3 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1659 | 1680 | +22 | 0/0 | 5/13 |
| 2 | 1519 | 1433 | -86 | 0/0 | 4/13 |
| 3 | 1407 | 1435 | +28 | 0/0 | 6/13 |
| 4 | 1407 | 1435 | +28 | 0/0 | 6/13 |
| 5 | 1407 | 1435 | +28 | 0/0 | 6/13 |
| 6 | 1374 | 1365 | -9 | 0/0 | 7/13 |
| 7 | 1374 | 1391 | +17 | 0/0 | 6/13 |
| 8 | 1374 | 1396 | +22 | 0/0 | 6/13 |
| 9 | 1374 | 1396 | +22 | 0/0 | 6/13 |
| 10 | 1411 | 1435 | +24 | 0/0 | 6/13 |
| 11 | 1386 | 1483 | +97 | 0/0 | 5/13 |
| 12 | 1412 | 1535 | +123 | 0/0 | 4/13 |

### omnibeta 2024->2025 seed 4 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1712 | 1626 | -86 | 0/0 | 5/13 |
| 2 | 1767 | 1681 | -86 | 0/0 | 5/13 |
| 3 | 1767 | 1681 | -86 | 0/0 | 5/13 |
| 4 | 1767 | 1684 | -83 | 0/0 | 8/13 |
| 5 | 1655 | 1535 | -120 | 0/0 | 12/13 |
| 6 | 1657 | 1550 | -108 | 0/0 | 10/13 |
| 7 | 1657 | 1550 | -108 | 0/0 | 9/13 |
| 8 | 1626 | 1462 | -164 | 0/0 | 9/13 |
| 9 | 1637 | 1494 | -143 | 0/0 | 7/13 |
| 10 | 1826 | 1516 | -311 | 0/0 | 6/13 |
| 11 | 1566 | 1607 | +41 | 0/0 | 4/13 |
| 12 | 1683 | 1725 | +42 | 0/0 | 5/13 |

### What this harness does not test

- Both arms face one rival list per (pair, seed), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ.
- Rivals reach and fall independently around ADP. Position runs and tier cliffs, where rivals correlate with each other, are not modelled, so the seed spread bounds rival variance from below.
- K/DEF are absent from both arms.
- The history rows carry no team, depth-chart or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.
- `ecr` is null on these boards, so any board-side market-rank path is dead here. An arm that differs from its rival only through ECR would show up as inert above rather than as a pass; the picks-changed column is what distinguishes the two cases.


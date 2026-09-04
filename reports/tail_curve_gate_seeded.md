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

## Test 2 — outcome (shared rival list, engine at every slot, lineups graded on actual points)

Over 220 slot-drafts: model 1572.0, external 1554.2 (Δ -17.8, -1.13%); external better in 121, worse in 94, tied 5. Pass: NO.

Engine errors (exception → best-available fallback): `blend_rank_lin` 0, `blend` 0. Our own picks the candidate changed: 1317 of 2860.

### Is the delta bigger than the noise?

With rivals pinned to exact consensus ADP, every replay of a pair makes the same rival picks, so its slot-drafts are one draft universe sampled at each seat rather than independent draws — and neighbouring seats see nearly the same board. Each seed below redraws the rival room (Gaussian noise of 6 picks on ADP, the same draw for every arm, so the per-slot comparison stays paired).

| seed | n | Δ mean | Δ % |
|---|---|---|---|
| exact ADP | 44 | -23.7 | -1.53% |
| 1 | 44 | -35.2 | -2.14% |
| 2 | 44 | -72.2 | -4.43% |
| 3 | 44 | +16.1 | +1.09% |
| 4 | 44 | +26.2 | +1.69% |

Observed Δ -1.13%, spread across seeds 6.12 points of percentage. **The delta is inside the seed spread, so this harness cannot resolve it** at 5 seeds. The pre-registered 1% threshold is unchanged; this line records how much of the measured delta is signal, and never moves the bar.

| league | pair | seed | model mean | external mean | Δ |
|---|---|---|---|---|---|
| keefamania | 2023->2024 | exact | 1464.4 | 1501.0 | +36.7 |
| keefamania | 2023->2024 | 1 | 1537.8 | 1540.4 | +2.6 |
| keefamania | 2023->2024 | 2 | 1482.4 | 1493.3 | +10.8 |
| keefamania | 2023->2024 | 3 | 1390.8 | 1405.4 | +14.6 |
| keefamania | 2023->2024 | 4 | 1403.6 | 1498.6 | +95.0 |
| keefamania | 2024->2025 | exact | 1351.3 | 1283.2 | -68.2 |
| keefamania | 2024->2025 | 1 | 1451.4 | 1340.0 | -111.4 |
| keefamania | 2024->2025 | 2 | 1432.0 | 1331.8 | -100.2 |
| keefamania | 2024->2025 | 3 | 1313.4 | 1337.9 | +24.5 |
| keefamania | 2024->2025 | 4 | 1400.6 | 1369.0 | -31.6 |
| omnibeta | 2023->2024 | exact | 1747.5 | 1636.6 | -110.9 |
| omnibeta | 2023->2024 | 1 | 1857.3 | 1794.0 | -63.4 |
| omnibeta | 2023->2024 | 2 | 1809.1 | 1727.4 | -81.7 |
| omnibeta | 2023->2024 | 3 | 1736.8 | 1720.0 | -16.8 |
| omnibeta | 2023->2024 | 4 | 1666.0 | 1688.6 | +22.6 |
| omnibeta | 2024->2025 | exact | 1605.9 | 1656.1 | +50.2 |
| omnibeta | 2024->2025 | 1 | 1684.8 | 1709.8 | +25.0 |
| omnibeta | 2024->2025 | 2 | 1737.5 | 1628.8 | -108.6 |
| omnibeta | 2024->2025 | 3 | 1425.3 | 1468.7 | +43.4 |
| omnibeta | 2024->2025 | 4 | 1693.3 | 1714.0 | +20.7 |

### keefamania 2023->2024 seed exact — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1362 | 1424 | +62 | 0/0 | 6/13 |
| 2 | 1451 | 1513 | +62 | 0/0 | 3/13 |
| 3 | 1451 | 1513 | +62 | 0/0 | 3/13 |
| 4 | 1383 | 1482 | +100 | 0/0 | 5/13 |
| 5 | 1449 | 1546 | +98 | 0/0 | 5/13 |
| 6 | 1610 | 1559 | -51 | 0/0 | 5/13 |
| 7 | 1650 | 1559 | -91 | 0/0 | 9/13 |
| 8 | 1515 | 1566 | +51 | 0/0 | 5/13 |
| 9 | 1387 | 1449 | +62 | 0/0 | 3/13 |
| 10 | 1387 | 1399 | +13 | 0/0 | 7/13 |

### keefamania 2023->2024 seed 1 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1430 | 1538 | +108 | 0/0 | 7/13 |
| 2 | 1526 | 1538 | +12 | 0/0 | 4/13 |
| 3 | 1526 | 1539 | +13 | 0/0 | 4/13 |
| 4 | 1511 | 1524 | +13 | 0/0 | 6/13 |
| 5 | 1513 | 1526 | +13 | 0/0 | 4/13 |
| 6 | 1533 | 1494 | -39 | 0/0 | 6/13 |
| 7 | 1587 | 1600 | +13 | 0/0 | 4/13 |
| 8 | 1502 | 1560 | +58 | 0/0 | 2/13 |
| 9 | 1625 | 1459 | -166 | 0/0 | 5/13 |
| 10 | 1625 | 1625 | +0 | 0/0 | 5/13 |

### keefamania 2023->2024 seed 2 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1430 | 1543 | +114 | 0/0 | 10/13 |
| 2 | 1482 | 1482 | +0 | 0/0 | 4/13 |
| 3 | 1491 | 1534 | +43 | 0/0 | 4/13 |
| 4 | 1452 | 1469 | +17 | 0/0 | 4/13 |
| 5 | 1533 | 1550 | +17 | 0/0 | 4/13 |
| 6 | 1533 | 1550 | +17 | 0/0 | 4/13 |
| 7 | 1533 | 1550 | +17 | 0/0 | 4/13 |
| 8 | 1502 | 1481 | -22 | 0/0 | 5/13 |
| 9 | 1434 | 1387 | -47 | 0/0 | 8/13 |
| 10 | 1434 | 1387 | -47 | 0/0 | 9/13 |

### keefamania 2023->2024 seed 3 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1314 | 1427 | +113 | 0/0 | 8/13 |
| 2 | 1489 | 1532 | +43 | 0/0 | 3/13 |
| 3 | 1356 | 1417 | +62 | 0/0 | 3/13 |
| 4 | 1381 | 1448 | +67 | 0/0 | 5/13 |
| 5 | 1412 | 1463 | +51 | 0/0 | 6/13 |
| 6 | 1412 | 1463 | +51 | 0/0 | 6/13 |
| 7 | 1381 | 1397 | +15 | 0/0 | 2/13 |
| 8 | 1397 | 1397 | +0 | 0/0 | 0/13 |
| 9 | 1376 | 1288 | -88 | 0/0 | 3/13 |
| 10 | 1391 | 1223 | -168 | 0/0 | 6/13 |

### keefamania 2023->2024 seed 4 — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 151

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1382 | 1525 | +143 | 0/0 | 9/13 |
| 2 | 1388 | 1542 | +153 | 0/0 | 9/13 |
| 3 | 1388 | 1516 | +127 | 0/0 | 9/13 |
| 4 | 1512 | 1500 | -13 | 0/0 | 5/13 |
| 5 | 1512 | 1534 | +22 | 0/0 | 9/13 |
| 6 | 1489 | 1541 | +51 | 0/0 | 5/13 |
| 7 | 1469 | 1547 | +78 | 0/0 | 8/13 |
| 8 | 1469 | 1533 | +64 | 0/0 | 8/13 |
| 9 | 1223 | 1447 | +224 | 0/0 | 7/13 |
| 10 | 1202 | 1303 | +100 | 0/0 | 4/13 |

### keefamania 2024->2025 seed exact — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1397 | 1470 | +73 | 0/0 | 2/13 |
| 2 | 1355 | 1159 | -196 | 0/0 | 2/13 |
| 3 | 1438 | 1439 | +2 | 0/0 | 5/13 |
| 4 | 1385 | 1287 | -98 | 0/0 | 5/13 |
| 5 | 1385 | 1224 | -161 | 0/0 | 6/13 |
| 6 | 1338 | 1224 | -114 | 0/0 | 4/13 |
| 7 | 1374 | 1480 | +106 | 0/0 | 6/13 |
| 8 | 1321 | 1197 | -124 | 0/0 | 4/13 |
| 9 | 1321 | 1197 | -124 | 0/0 | 4/13 |
| 10 | 1198 | 1152 | -46 | 0/0 | 8/13 |

### keefamania 2024->2025 seed 1 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1473 | 1204 | -270 | 0/0 | 8/13 |
| 2 | 1385 | 1157 | -228 | 0/0 | 6/13 |
| 3 | 1516 | 1436 | -80 | 0/0 | 7/13 |
| 4 | 1614 | 1553 | -61 | 0/0 | 5/13 |
| 5 | 1550 | 1470 | -80 | 0/0 | 8/13 |
| 6 | 1550 | 1427 | -123 | 0/0 | 9/13 |
| 7 | 1323 | 1264 | -58 | 0/0 | 7/13 |
| 8 | 1354 | 1264 | -90 | 0/0 | 7/13 |
| 9 | 1457 | 1340 | -117 | 0/0 | 4/13 |
| 10 | 1292 | 1284 | -7 | 0/0 | 5/13 |

### keefamania 2024->2025 seed 2 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1475 | 1346 | -129 | 0/0 | 5/13 |
| 2 | 1475 | 1268 | -207 | 0/0 | 4/13 |
| 3 | 1361 | 1418 | +58 | 0/0 | 4/13 |
| 4 | 1458 | 1269 | -189 | 0/0 | 5/13 |
| 5 | 1458 | 1396 | -62 | 0/0 | 4/13 |
| 6 | 1396 | 1396 | +1 | 0/0 | 7/13 |
| 7 | 1488 | 1274 | -214 | 0/0 | 7/13 |
| 8 | 1488 | 1274 | -214 | 0/0 | 7/13 |
| 9 | 1488 | 1329 | -159 | 0/0 | 7/13 |
| 10 | 1234 | 1347 | +113 | 0/0 | 9/13 |

### keefamania 2024->2025 seed 3 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1319 | 1334 | +15 | 0/0 | 6/13 |
| 2 | 1484 | 1215 | -270 | 0/0 | 6/13 |
| 3 | 1338 | 1383 | +45 | 0/0 | 3/13 |
| 4 | 1338 | 1383 | +45 | 0/0 | 3/13 |
| 5 | 1338 | 1383 | +45 | 0/0 | 3/13 |
| 6 | 1194 | 1354 | +160 | 0/0 | 3/13 |
| 7 | 1150 | 1280 | +130 | 0/0 | 5/13 |
| 8 | 1303 | 1274 | -29 | 0/0 | 6/13 |
| 9 | 1314 | 1354 | +40 | 0/0 | 8/13 |
| 10 | 1353 | 1417 | +64 | 0/0 | 8/13 |

### keefamania 2024->2025 seed 4 — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1541 | 1305 | -236 | 0/0 | 6/13 |
| 2 | 1477 | 1349 | -127 | 0/0 | 6/13 |
| 3 | 1312 | 1385 | +73 | 0/0 | 5/13 |
| 4 | 1312 | 1203 | -109 | 0/0 | 6/13 |
| 5 | 1317 | 1363 | +45 | 0/0 | 4/13 |
| 6 | 1390 | 1363 | -28 | 0/0 | 5/13 |
| 7 | 1410 | 1341 | -69 | 0/0 | 6/13 |
| 8 | 1442 | 1387 | -54 | 0/0 | 5/13 |
| 9 | 1442 | 1387 | -54 | 0/0 | 5/13 |
| 10 | 1363 | 1608 | +245 | 0/0 | 7/13 |

### omnibeta 2023->2024 seed exact — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1691 | 1732 | +41 | 0/0 | 3/13 |
| 2 | 1678 | 1697 | +19 | 0/0 | 9/13 |
| 3 | 1646 | 1700 | +54 | 0/0 | 7/13 |
| 4 | 1557 | 1527 | -30 | 0/0 | 5/13 |
| 5 | 1952 | 1600 | -351 | 0/0 | 8/13 |
| 6 | 1952 | 1600 | -351 | 0/0 | 9/13 |
| 7 | 1957 | 1600 | -357 | 0/0 | 7/13 |
| 8 | 1917 | 1647 | -270 | 0/0 | 10/13 |
| 9 | 1782 | 1472 | -310 | 0/0 | 4/13 |
| 10 | 1657 | 1657 | +0 | 0/0 | 2/13 |
| 11 | 1540 | 1713 | +172 | 0/0 | 9/13 |
| 12 | 1640 | 1694 | +54 | 0/0 | 5/13 |

### omnibeta 2023->2024 seed 1 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1781 | 1785 | +4 | 0/0 | 3/13 |
| 2 | 1781 | 1804 | +22 | 0/0 | 9/13 |
| 3 | 1797 | 1824 | +28 | 0/0 | 6/13 |
| 4 | 2019 | 1985 | -34 | 0/0 | 7/13 |
| 5 | 1976 | 1985 | +9 | 0/0 | 5/13 |
| 6 | 1976 | 1767 | -210 | 0/0 | 6/13 |
| 7 | 2019 | 1768 | -251 | 0/0 | 8/13 |
| 8 | 2030 | 2039 | +9 | 0/0 | 3/13 |
| 9 | 1550 | 1791 | +241 | 0/0 | 7/13 |
| 10 | 1776 | 1581 | -194 | 0/0 | 2/13 |
| 11 | 1776 | 1581 | -194 | 0/0 | 3/13 |
| 12 | 1806 | 1618 | -189 | 0/0 | 5/13 |

### omnibeta 2023->2024 seed 2 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1769 | 1710 | -60 | 0/0 | 6/13 |
| 2 | 1512 | 1788 | +276 | 0/0 | 6/13 |
| 3 | 1557 | 1849 | +291 | 0/0 | 6/13 |
| 4 | 1902 | 1858 | -45 | 0/0 | 5/13 |
| 5 | 1897 | 1600 | -296 | 0/0 | 7/13 |
| 6 | 1897 | 1600 | -296 | 0/0 | 7/13 |
| 7 | 1897 | 1805 | -92 | 0/0 | 9/13 |
| 8 | 1825 | 1597 | -228 | 0/0 | 9/13 |
| 9 | 1901 | 1704 | -197 | 0/0 | 6/13 |
| 10 | 1909 | 1670 | -239 | 0/0 | 5/13 |
| 11 | 1857 | 1676 | -180 | 0/0 | 5/13 |
| 12 | 1786 | 1872 | +86 | 0/0 | 3/13 |

### omnibeta 2023->2024 seed 3 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1871 | 1873 | +2 | 0/0 | 7/13 |
| 2 | 1871 | 1873 | +2 | 0/0 | 6/13 |
| 3 | 1858 | 1873 | +15 | 0/0 | 7/13 |
| 4 | 1909 | 1817 | -92 | 0/0 | 9/13 |
| 5 | 1603 | 1621 | +18 | 0/0 | 5/13 |
| 6 | 1626 | 1586 | -40 | 0/0 | 4/13 |
| 7 | 1618 | 1761 | +142 | 0/0 | 8/13 |
| 8 | 1548 | 1616 | +68 | 0/0 | 5/13 |
| 9 | 1783 | 1637 | -146 | 0/0 | 8/13 |
| 10 | 1694 | 1699 | +5 | 0/0 | 9/13 |
| 11 | 1725 | 1636 | -89 | 0/0 | 6/13 |
| 12 | 1735 | 1651 | -84 | 0/0 | 6/13 |

### omnibeta 2023->2024 seed 4 — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 177

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1499 | 1599 | +100 | 0/0 | 6/13 |
| 2 | 1567 | 1599 | +31 | 0/0 | 7/13 |
| 3 | 1670 | 1680 | +10 | 0/0 | 11/13 |
| 4 | 1659 | 1657 | -2 | 0/0 | 7/13 |
| 5 | 1767 | 1717 | -49 | 0/0 | 8/13 |
| 6 | 1573 | 1679 | +107 | 0/0 | 5/13 |
| 7 | 1442 | 1764 | +322 | 0/0 | 7/13 |
| 8 | 1970 | 1811 | -160 | 0/0 | 5/13 |
| 9 | 1778 | 1682 | -96 | 0/0 | 6/13 |
| 10 | 1722 | 1751 | +30 | 0/0 | 8/13 |
| 11 | 1708 | 1708 | +0 | 0/0 | 0/13 |
| 12 | 1636 | 1616 | -20 | 0/0 | 2/13 |

### omnibeta 2024->2025 seed exact — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1810 | 1842 | +32 | 0/0 | 6/13 |
| 2 | 1589 | 1658 | +69 | 0/0 | 4/13 |
| 3 | 1604 | 1658 | +54 | 0/0 | 6/13 |
| 4 | 1604 | 1507 | -97 | 0/0 | 8/13 |
| 5 | 1603 | 1572 | -31 | 0/0 | 9/13 |
| 6 | 1429 | 1572 | +144 | 0/0 | 9/13 |
| 7 | 1458 | 1572 | +114 | 0/0 | 9/13 |
| 8 | 1716 | 1831 | +116 | 0/0 | 3/13 |
| 9 | 1714 | 1831 | +117 | 0/0 | 9/13 |
| 10 | 1706 | 1780 | +74 | 0/0 | 4/13 |
| 11 | 1533 | 1499 | -34 | 0/0 | 8/13 |
| 12 | 1506 | 1549 | +43 | 0/0 | 9/13 |

### omnibeta 2024->2025 seed 1 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1845 | 1775 | -70 | 0/0 | 4/13 |
| 2 | 1578 | 1663 | +86 | 0/0 | 4/13 |
| 3 | 1578 | 1650 | +73 | 0/0 | 4/13 |
| 4 | 1578 | 1650 | +73 | 0/0 | 4/13 |
| 5 | 1640 | 1699 | +60 | 0/0 | 8/13 |
| 6 | 1652 | 1725 | +73 | 0/0 | 7/13 |
| 7 | 1727 | 1699 | -28 | 0/0 | 8/13 |
| 8 | 1702 | 1699 | -2 | 0/0 | 1/13 |
| 9 | 1581 | 1699 | +118 | 0/0 | 5/13 |
| 10 | 1661 | 1810 | +149 | 0/0 | 5/13 |
| 11 | 1810 | 1822 | +11 | 0/0 | 3/13 |
| 12 | 1866 | 1624 | -243 | 0/0 | 7/13 |

### omnibeta 2024->2025 seed 2 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1701 | 1729 | +28 | 0/0 | 3/13 |
| 2 | 1701 | 1795 | +94 | 0/0 | 5/13 |
| 3 | 1535 | 1683 | +148 | 0/0 | 8/13 |
| 4 | 1651 | 1658 | +7 | 0/0 | 8/13 |
| 5 | 1651 | 1658 | +7 | 0/0 | 8/13 |
| 6 | 1802 | 1554 | -248 | 0/0 | 9/13 |
| 7 | 1709 | 1658 | -51 | 0/0 | 4/13 |
| 8 | 1709 | 1557 | -152 | 0/0 | 4/13 |
| 9 | 1817 | 1557 | -260 | 0/0 | 12/13 |
| 10 | 1852 | 1566 | -286 | 0/0 | 11/13 |
| 11 | 1878 | 1566 | -312 | 0/0 | 10/13 |
| 12 | 1845 | 1566 | -279 | 0/0 | 9/13 |

### omnibeta 2024->2025 seed 3 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1659 | 1746 | +88 | 0/0 | 7/13 |
| 2 | 1519 | 1648 | +129 | 0/0 | 7/13 |
| 3 | 1407 | 1486 | +79 | 0/0 | 5/13 |
| 4 | 1407 | 1486 | +79 | 0/0 | 5/13 |
| 5 | 1407 | 1417 | +10 | 0/0 | 5/13 |
| 6 | 1374 | 1403 | +28 | 0/0 | 11/13 |
| 7 | 1374 | 1403 | +28 | 0/0 | 11/13 |
| 8 | 1374 | 1403 | +28 | 0/0 | 11/13 |
| 9 | 1374 | 1402 | +28 | 0/0 | 11/13 |
| 10 | 1411 | 1402 | -9 | 0/0 | 11/13 |
| 11 | 1386 | 1402 | +16 | 0/0 | 6/13 |
| 12 | 1412 | 1427 | +16 | 0/0 | 6/13 |

### omnibeta 2024->2025 seed 4 — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 205

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1712 | 1820 | +108 | 0/0 | 6/13 |
| 2 | 1767 | 1820 | +54 | 0/0 | 6/13 |
| 3 | 1767 | 1809 | +42 | 0/0 | 7/13 |
| 4 | 1767 | 1809 | +42 | 0/0 | 7/13 |
| 5 | 1655 | 1696 | +42 | 0/0 | 7/13 |
| 6 | 1657 | 1664 | +6 | 0/0 | 6/13 |
| 7 | 1657 | 1854 | +197 | 0/0 | 5/13 |
| 8 | 1626 | 1588 | -38 | 0/0 | 5/13 |
| 9 | 1637 | 1588 | -49 | 0/0 | 9/13 |
| 10 | 1826 | 1774 | -52 | 0/0 | 6/13 |
| 11 | 1566 | 1557 | -9 | 0/0 | 4/13 |
| 12 | 1683 | 1590 | -93 | 0/0 | 4/13 |

### What this harness does not test

- Both arms face one rival list per (pair, seed), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ.
- Rivals reach and fall independently around ADP. Position runs and tier cliffs, where rivals correlate with each other, are not modelled, so the seed spread bounds rival variance from below.
- K/DEF are absent from both arms.
- The history rows carry no team, depth-chart or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.
- `ecr` is null on these boards, so any board-side market-rank path is dead here. An arm that differs from its rival only through ECR would show up as inert above rather than as a pass; the picks-changed column is what distinguishes the two cases.


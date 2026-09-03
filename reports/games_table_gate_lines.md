# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`lines`) and `external` is the candidate (`lines_gt`); rivals judged: `lines`.

Decision: **split** — accuracy FAIL, outcome pass. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 60.8 | 63.1 | 1.037 | 0.465 | 0.465 | +0.000 | NO |
| omnibeta | 301 | 66.0 | 68.1 | 1.031 | 0.464 | 0.467 | +0.003 | NO |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 78.5 | 84.7 | 0.586 | 0.550 |
| keefamania | 2023->2024 | RB | 44 | 54.9 | 54.5 | 0.613 | 0.611 |
| keefamania | 2023->2024 | TE | 16 | 45.1 | 47.2 | 0.515 | 0.515 |
| keefamania | 2023->2024 | WR | 55 | 51.9 | 55.6 | 0.457 | 0.450 |
| keefamania | 2024->2025 | QB | 19 | 88.0 | 96.7 | -0.253 | -0.218 |
| keefamania | 2024->2025 | RB | 37 | 66.5 | 64.1 | 0.654 | 0.658 |
| keefamania | 2024->2025 | TE | 13 | 40.9 | 41.3 | 0.225 | 0.264 |
| keefamania | 2024->2025 | WR | 50 | 64.6 | 67.6 | 0.474 | 0.473 |
| omnibeta | 2023->2024 | QB | 22 | 80.2 | 83.0 | 0.544 | 0.565 |
| omnibeta | 2023->2024 | RB | 48 | 58.9 | 58.7 | 0.626 | 0.626 |
| omnibeta | 2023->2024 | TE | 18 | 50.7 | 53.1 | 0.560 | 0.573 |
| omnibeta | 2023->2024 | WR | 58 | 62.2 | 66.5 | 0.471 | 0.461 |
| omnibeta | 2024->2025 | QB | 26 | 85.5 | 89.8 | -0.091 | -0.103 |
| omnibeta | 2024->2025 | RB | 44 | 67.3 | 65.8 | 0.660 | 0.673 |
| omnibeta | 2024->2025 | TE | 21 | 46.6 | 48.1 | 0.318 | 0.331 |
| omnibeta | 2024->2025 | WR | 64 | 71.7 | 74.9 | 0.420 | 0.422 |

## Test 2 — outcome (shared ADP-order rivals, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1536.6, external 1551.4 (Δ +14.7, +0.96%); external better in 23, worse in 17, tied 4. Pass: yes.

| league | pair | model mean | external mean | Δ |
|---|---|---|---|---|
| keefamania | 2023->2024 | 1479.2 | 1449.2 | -30.0 |
| keefamania | 2024->2025 | 1435.6 | 1442.0 | +6.4 |
| omnibeta | 2023->2024 | 1636.3 | 1705.2 | +68.9 |
| omnibeta | 2024->2025 | 1569.1 | 1573.8 | +4.7 |

### keefamania 2023->2024 — 10 teams, 13 rounds, rival pool 158, boards 145 / 145

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1549 | 1479 | -70 | 0/0 |
| 2 | 1549 | 1479 | -70 | 0/0 |
| 3 | 1549 | 1479 | -70 | 0/0 |
| 4 | 1493 | 1479 | -13 | 0/0 |
| 5 | 1500 | 1527 | +27 | 0/0 |
| 6 | 1502 | 1527 | +25 | 0/0 |
| 7 | 1502 | 1527 | +25 | 0/0 |
| 8 | 1509 | 1408 | -101 | 0/0 |
| 9 | 1378 | 1343 | -35 | 0/0 |
| 10 | 1262 | 1244 | -18 | 0/0 |

### keefamania 2024->2025 — 10 teams, 13 rounds, rival pool 144, boards 135 / 135

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1592 | 1464 | -127 | 0/0 |
| 2 | 1592 | 1564 | -28 | 0/0 |
| 3 | 1301 | 1288 | -13 | 0/0 |
| 4 | 1377 | 1542 | +165 | 0/0 |
| 5 | 1410 | 1410 | +0 | 0/0 |
| 6 | 1410 | 1421 | +11 | 0/0 |
| 7 | 1421 | 1421 | +0 | 0/0 |
| 8 | 1421 | 1437 | +16 | 0/0 |
| 9 | 1437 | 1437 | +0 | 0/0 |
| 10 | 1397 | 1437 | +40 | 0/0 |

### omnibeta 2023->2024 — 12 teams, 13 rounds, rival pool 177, boards 167 / 167

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1545 | 1629 | +84 | 0/0 |
| 2 | 1545 | 1629 | +84 | 0/0 |
| 3 | 1619 | 1651 | +32 | 0/0 |
| 4 | 1686 | 1632 | -54 | 0/0 |
| 5 | 1621 | 1751 | +130 | 0/0 |
| 6 | 1699 | 1901 | +201 | 0/0 |
| 7 | 1773 | 1848 | +76 | 0/0 |
| 8 | 1773 | 1848 | +76 | 0/0 |
| 9 | 1672 | 1672 | +0 | 0/0 |
| 10 | 1554 | 1619 | +66 | 0/0 |
| 11 | 1554 | 1619 | +66 | 0/0 |
| 12 | 1596 | 1662 | +66 | 0/0 |

### omnibeta 2024->2025 — 12 teams, 13 rounds, rival pool 205, boards 187 / 187

| slot | model | external | Δ | engine errors |
|---|---|---|---|---|
| 1 | 1622 | 1629 | +8 | 0/0 |
| 2 | 1405 | 1455 | +50 | 0/0 |
| 3 | 1405 | 1455 | +50 | 0/0 |
| 4 | 1531 | 1784 | +253 | 0/0 |
| 5 | 1502 | 1647 | +144 | 0/0 |
| 6 | 1528 | 1647 | +119 | 0/0 |
| 7 | 1754 | 1607 | -147 | 0/0 |
| 8 | 1754 | 1498 | -257 | 0/0 |
| 9 | 1658 | 1605 | -54 | 0/0 |
| 10 | 1528 | 1506 | -22 | 0/0 |
| 11 | 1570 | 1506 | -65 | 0/0 |
| 12 | 1570 | 1548 | -22 | 0/0 |

Both arms face one rival list (the year's pool in ADP order), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ. Rivals never deviate from ADP, so runs and reaches are absent. K/DEF are absent from both arms. The history rows carry no team or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.


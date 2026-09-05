# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`lines`) and `external` is the candidate (`lines_gt_rb`); rivals judged: `lines`.

Decision: **flip** — accuracy pass, outcome pass. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 60.8 | 60.4 | 0.993 | 0.465 | 0.465 | +0.000 | yes |
| omnibeta | 301 | 66.0 | 65.7 | 0.996 | 0.464 | 0.466 | +0.002 | yes |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 78.5 | 78.5 | 0.586 | 0.586 |
| keefamania | 2023->2024 | RB | 44 | 54.9 | 54.5 | 0.613 | 0.611 |
| keefamania | 2023->2024 | TE | 16 | 45.1 | 45.1 | 0.515 | 0.515 |
| keefamania | 2023->2024 | WR | 55 | 51.9 | 51.9 | 0.457 | 0.457 |
| keefamania | 2024->2025 | QB | 19 | 88.0 | 88.0 | -0.253 | -0.253 |
| keefamania | 2024->2025 | RB | 37 | 66.5 | 64.1 | 0.654 | 0.658 |
| keefamania | 2024->2025 | TE | 13 | 40.9 | 40.9 | 0.225 | 0.225 |
| keefamania | 2024->2025 | WR | 50 | 64.6 | 64.6 | 0.474 | 0.474 |
| omnibeta | 2023->2024 | QB | 22 | 80.2 | 80.2 | 0.544 | 0.544 |
| omnibeta | 2023->2024 | RB | 48 | 58.9 | 58.7 | 0.626 | 0.626 |
| omnibeta | 2023->2024 | TE | 18 | 50.7 | 50.7 | 0.560 | 0.560 |
| omnibeta | 2023->2024 | WR | 58 | 62.2 | 62.2 | 0.471 | 0.471 |
| omnibeta | 2024->2025 | QB | 26 | 85.5 | 85.5 | -0.091 | -0.091 |
| omnibeta | 2024->2025 | RB | 44 | 67.3 | 65.8 | 0.660 | 0.673 |
| omnibeta | 2024->2025 | TE | 21 | 46.6 | 46.6 | 0.318 | 0.318 |
| omnibeta | 2024->2025 | WR | 64 | 71.7 | 71.7 | 0.420 | 0.420 |

## Test 2 — outcome (shared rival list, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1523.1, external 1528.4 (Δ +5.3, +0.35%); external better in 15, worse in 9, tied 20. Pass: yes.

Engine errors (exception → best-available fallback): `lines_gt_rb` 0, `lines` 0. Our own picks the candidate changed: 123 of 572.

Rivals were pinned to exact consensus ADP (one seed), so the slot-drafts of a pair are one draft universe sampled at each seat, not independent draws. Re-run with `--seeds N` for an error bar.

| league | pair | seed | model mean | external mean | Δ |
|---|---|---|---|---|---|
| keefamania | 2023->2024 | exact | 1482.8 | 1499.4 | +16.6 |
| keefamania | 2024->2025 | exact | 1388.8 | 1388.8 | +0.0 |
| omnibeta | 2023->2024 | exact | 1636.3 | 1647.2 | +10.9 |
| omnibeta | 2024->2025 | exact | 1555.4 | 1550.0 | -5.4 |

### keefamania 2023->2024 seed exact — 10 teams, 13 of 13 rounds, rival pool 158, boards 145 / 145

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1549 | 1549 | +0 | 0/0 | 0/13 |
| 2 | 1549 | 1549 | +0 | 0/0 | 2/13 |
| 3 | 1526 | 1549 | +23 | 0/0 | 5/13 |
| 4 | 1552 | 1549 | -3 | 0/0 | 5/13 |
| 5 | 1500 | 1581 | +81 | 0/0 | 6/13 |
| 6 | 1502 | 1581 | +79 | 0/0 | 6/13 |
| 7 | 1502 | 1527 | +25 | 0/0 | 5/13 |
| 8 | 1509 | 1403 | -107 | 0/0 | 7/13 |
| 9 | 1378 | 1353 | -24 | 0/0 | 8/13 |
| 10 | 1262 | 1353 | +92 | 0/0 | 5/13 |

### keefamania 2024->2025 seed exact — 10 teams, 13 of 13 rounds, rival pool 144, boards 135 / 135

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1592 | 1592 | +0 | 0/0 | 0/13 |
| 2 | 1592 | 1592 | +0 | 0/0 | 0/13 |
| 3 | 1301 | 1301 | +0 | 0/0 | 0/13 |
| 4 | 1377 | 1377 | +0 | 0/0 | 0/13 |
| 5 | 1308 | 1308 | +0 | 0/0 | 0/13 |
| 6 | 1308 | 1308 | +0 | 0/0 | 0/13 |
| 7 | 1365 | 1365 | +0 | 0/0 | 2/13 |
| 8 | 1365 | 1365 | +0 | 0/0 | 2/13 |
| 9 | 1341 | 1341 | +0 | 0/0 | 0/13 |
| 10 | 1341 | 1341 | +0 | 0/0 | 3/13 |

### omnibeta 2023->2024 seed exact — 12 teams, 13 of 13 rounds, rival pool 177, boards 167 / 167

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1545 | 1417 | -128 | 0/0 | 1/13 |
| 2 | 1545 | 1545 | +0 | 0/0 | 2/13 |
| 3 | 1619 | 1619 | +0 | 0/0 | 2/13 |
| 4 | 1686 | 1717 | +30 | 0/0 | 3/13 |
| 5 | 1621 | 1652 | +30 | 0/0 | 3/13 |
| 6 | 1699 | 1699 | +0 | 0/0 | 0/13 |
| 7 | 1773 | 1773 | +0 | 0/0 | 0/13 |
| 8 | 1773 | 1773 | +0 | 0/0 | 0/13 |
| 9 | 1672 | 1672 | +0 | 0/0 | 0/13 |
| 10 | 1554 | 1619 | +66 | 0/0 | 1/13 |
| 11 | 1554 | 1619 | +66 | 0/0 | 1/13 |
| 12 | 1596 | 1662 | +66 | 0/0 | 1/13 |

### omnibeta 2024->2025 seed exact — 12 teams, 13 of 13 rounds, rival pool 205, boards 187 / 187

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1523 | 1624 | +100 | 0/0 | 5/13 |
| 2 | 1405 | 1465 | +61 | 0/0 | 6/13 |
| 3 | 1405 | 1470 | +66 | 0/0 | 7/13 |
| 4 | 1531 | 1652 | +121 | 0/0 | 1/13 |
| 5 | 1680 | 1680 | +0 | 0/0 | 0/13 |
| 6 | 1470 | 1680 | +210 | 0/0 | 4/13 |
| 7 | 1658 | 1580 | -78 | 0/0 | 3/13 |
| 8 | 1658 | 1658 | +0 | 0/0 | 2/13 |
| 9 | 1665 | 1539 | -126 | 0/0 | 5/13 |
| 10 | 1528 | 1403 | -126 | 0/0 | 5/13 |
| 11 | 1570 | 1403 | -168 | 0/0 | 6/13 |
| 12 | 1570 | 1445 | -126 | 0/0 | 9/13 |

### What this harness does not test

- Both arms face one rival list per (pair, seed), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ.
- Rivals reach and fall independently around ADP. Position runs and tier cliffs, where rivals correlate with each other, are not modelled, so the seed spread bounds rival variance from below.
- K/DEF are absent from both arms.
- The history rows carry no team, depth-chart or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.
- `ecr` is null on these boards, so any board-side market-rank path is dead here. An arm that differs from its rival only through ECR would show up as inert above rather than as a pass; the picks-changed column is what distinguishes the two cases.


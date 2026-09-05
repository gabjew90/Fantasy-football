# Projection-source gate (DECISIONS #23)

Arms: in every table below `model` is the first rival (`blend`) and `external` is the candidate (`fpros`); rivals judged: `blend`, `lines`.

Decision: **flip** — accuracy pass, outcome pass. Thresholds pre-registered: MAE within 2%, Spearman within 0.02, outcome within 1%.

`model` = usage + log-rank blend. `external` = outside stat lines; in history only Sleeper's week-1 lines exist and stand in for the 2026 sheet + Sleeper combination. The 2026 sheet itself cannot be judged until 2026 is played.

## Test 1 — accuracy (rows every arm projected, both pairs pooled)

| league | n | model MAE | external MAE | ratio | model ρ (weighted) | external ρ | Δρ | pass |
|---|---|---|---|---|---|---|---|---|
| keefamania | 254 | 57.8 | 57.6 | 0.997 | 0.476 | 0.476 | +0.000 | yes |
| omnibeta | 301 | 63.0 | 61.8 | 0.981 | 0.467 | 0.488 | +0.021 | yes |

Per cell (pair × position):

| league | pair | pos | n | model MAE | external MAE | model ρ | external ρ |
|---|---|---|---|---|---|---|---|
| keefamania | 2023->2024 | QB | 20 | 68.6 | 74.4 | 0.561 | 0.451 |
| keefamania | 2023->2024 | RB | 44 | 56.0 | 55.8 | 0.597 | 0.602 |
| keefamania | 2023->2024 | TE | 16 | 36.8 | 42.6 | 0.556 | 0.562 |
| keefamania | 2023->2024 | WR | 55 | 50.9 | 50.1 | 0.481 | 0.527 |
| keefamania | 2024->2025 | QB | 19 | 77.2 | 83.5 | -0.082 | -0.265 |
| keefamania | 2024->2025 | RB | 37 | 68.2 | 57.4 | 0.634 | 0.731 |
| keefamania | 2024->2025 | TE | 13 | 37.3 | 40.3 | 0.110 | 0.077 |
| keefamania | 2024->2025 | WR | 50 | 59.6 | 60.3 | 0.493 | 0.487 |
| omnibeta | 2023->2024 | QB | 22 | 75.4 | 75.0 | 0.417 | 0.433 |
| omnibeta | 2023->2024 | RB | 48 | 59.3 | 58.2 | 0.614 | 0.648 |
| omnibeta | 2023->2024 | TE | 18 | 46.2 | 46.6 | 0.614 | 0.577 |
| omnibeta | 2023->2024 | WR | 58 | 60.2 | 60.0 | 0.470 | 0.518 |
| omnibeta | 2024->2025 | QB | 26 | 71.9 | 77.9 | 0.105 | -0.031 |
| omnibeta | 2024->2025 | RB | 44 | 70.6 | 58.8 | 0.637 | 0.700 |
| omnibeta | 2024->2025 | TE | 21 | 45.1 | 43.4 | 0.131 | 0.338 |
| omnibeta | 2024->2025 | WR | 64 | 65.8 | 67.7 | 0.471 | 0.447 |

## Test 2 — outcome (shared rival list, engine at every slot, lineups graded on actual points)

Over 44 slot-drafts: model 1554.5, external 1700.5 (Δ +146.0, +9.39%); external better in 34, worse in 10, tied 0. Pass: yes.

Engine errors (exception → best-available fallback): `fpros` 0, `blend` 0, `lines` 0. Our own picks the candidate changed: 505 of 572.

Rivals were pinned to exact consensus ADP (one seed), so the slot-drafts of a pair are one draft universe sampled at each seat, not independent draws. Re-run with `--seeds N` for an error bar.

| league | pair | seed | model mean | external mean | Δ |
|---|---|---|---|---|---|
| keefamania | 2023->2024 | exact | 1464.4 | 1605.3 | +140.9 |
| keefamania | 2024->2025 | exact | 1351.3 | 1580.2 | +228.8 |
| omnibeta | 2023->2024 | exact | 1747.5 | 1766.6 | +19.2 |
| omnibeta | 2024->2025 | exact | 1605.9 | 1813.9 | +208.0 |

### keefamania 2023->2024 seed exact — 10 teams, 13 of 13 rounds, rival pool 158, boards 152 / 149

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1362 | 1445 | +83 | 0/0 | 12/13 |
| 2 | 1451 | 1653 | +202 | 0/0 | 11/13 |
| 3 | 1451 | 1653 | +202 | 0/0 | 11/13 |
| 4 | 1383 | 1576 | +194 | 0/0 | 13/13 |
| 5 | 1449 | 1596 | +147 | 0/0 | 12/13 |
| 6 | 1610 | 1616 | +5 | 0/0 | 11/13 |
| 7 | 1650 | 1616 | -34 | 0/0 | 11/13 |
| 8 | 1515 | 1616 | +101 | 0/0 | 12/13 |
| 9 | 1387 | 1582 | +195 | 0/0 | 11/13 |
| 10 | 1387 | 1700 | +313 | 0/0 | 11/13 |

### keefamania 2024->2025 seed exact — 10 teams, 13 of 13 rounds, rival pool 144, boards 143 / 143

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1397 | 1324 | -74 | 0/0 | 12/13 |
| 2 | 1355 | 1423 | +68 | 0/0 | 10/13 |
| 3 | 1438 | 1784 | +347 | 0/0 | 10/13 |
| 4 | 1385 | 1729 | +344 | 0/0 | 11/13 |
| 5 | 1385 | 1634 | +249 | 0/0 | 12/13 |
| 6 | 1338 | 1634 | +296 | 0/0 | 13/13 |
| 7 | 1374 | 1634 | +260 | 0/0 | 13/13 |
| 8 | 1321 | 1634 | +313 | 0/0 | 13/13 |
| 9 | 1321 | 1573 | +252 | 0/0 | 13/13 |
| 10 | 1198 | 1430 | +232 | 0/0 | 13/13 |

### omnibeta 2023->2024 seed exact — 12 teams, 13 of 13 rounds, rival pool 177, boards 177 / 176

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1691 | 1534 | -157 | 0/0 | 10/13 |
| 2 | 1678 | 1552 | -127 | 0/0 | 11/13 |
| 3 | 1646 | 1834 | +188 | 0/0 | 11/13 |
| 4 | 1557 | 1764 | +207 | 0/0 | 12/13 |
| 5 | 1952 | 1860 | -92 | 0/0 | 12/13 |
| 6 | 1952 | 1643 | -309 | 0/0 | 11/13 |
| 7 | 1957 | 1830 | -127 | 0/0 | 11/13 |
| 8 | 1917 | 1714 | -203 | 0/0 | 11/13 |
| 9 | 1782 | 1765 | -17 | 0/0 | 12/13 |
| 10 | 1657 | 1774 | +117 | 0/0 | 12/13 |
| 11 | 1540 | 1965 | +425 | 0/0 | 12/13 |
| 12 | 1640 | 1965 | +326 | 0/0 | 12/13 |

### omnibeta 2024->2025 seed exact — 12 teams, 13 of 13 rounds, rival pool 205, boards 205 / 204

| slot | model | external | Δ | engine errors | picks changed |
|---|---|---|---|---|---|
| 1 | 1810 | 1845 | +35 | 0/0 | 12/13 |
| 2 | 1589 | 1836 | +247 | 0/0 | 12/13 |
| 3 | 1604 | 1806 | +202 | 0/0 | 12/13 |
| 4 | 1604 | 1863 | +259 | 0/0 | 12/13 |
| 5 | 1603 | 1990 | +387 | 0/0 | 11/13 |
| 6 | 1429 | 1903 | +474 | 0/0 | 10/13 |
| 7 | 1458 | 1880 | +422 | 0/0 | 9/13 |
| 8 | 1716 | 1781 | +65 | 0/0 | 12/13 |
| 9 | 1714 | 1687 | -27 | 0/0 | 10/13 |
| 10 | 1706 | 1786 | +80 | 0/0 | 12/13 |
| 11 | 1533 | 1793 | +260 | 0/0 | 10/13 |
| 12 | 1506 | 1596 | +90 | 0/0 | 11/13 |

### What this harness does not test

- Both arms face one rival list per (pair, seed), so a player one arm never projected is still taken by the rivals at his ADP; only our own picks differ.
- Rivals reach and fall independently around ADP. Position runs and tier cliffs, where rivals correlate with each other, are not modelled, so the seed spread bounds rival variance from below.
- K/DEF are absent from both arms.
- The history rows carry no team, depth-chart or route data, so the handcuff and RB-receiving upside flags are inert on these boards for both arms; only the rookie upside path is live.
- `ecr` is null on these boards, so any board-side market-rank path is dead here. An arm that differs from its rival only through ECR would show up as inert above rather than as a pass; the picks-changed column is what distinguishes the two cases.


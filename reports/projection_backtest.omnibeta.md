# Projection backtest — omnibeta

Arms built as the pipeline would have built them before each target season's draft; scored against that season's actuals in league scoring, 17-game basis. Population = every player with a FantasyFootballCalculator ADP for the target year (an actual of 0 for anyone who never played: that is the projection's error, not a dropped row). Role gate off (no historical depth chart); no overrides or availability sweep. `lines` = Sleeper week-1 stat lines x 17, rows updated after the week-1 Tuesday dropped.

Configured alphas: {'model_alpha': 0.55, 'stable_veteran': 0.65, 'volatile': 0.4}

## 2023->2024

Pool 177 players; FFC names unmatched to Sleeper: 1; week-1 lines kept 1129, dropped as late updates 0, blank 8291.

| pos | arm | n | MAE | Spearman | n common | MAE common | Spearman common | MAE top36 | Spearman top36 |
|---|---|---|---|---|---|---|---|---|---|
| QB | usage | 22 | 73.8 | 0.339 | 22 | 73.8 | 0.339 | 73.8 | 0.339 |
| QB | curve | 26 | 73.6 | 0.335 | 22 | 79.2 | 0.473 | 73.6 | 0.335 |
| QB | blend | 26 | 70.4 | 0.313 | 22 | 75.4 | 0.417 | 70.4 | 0.313 |
| QB | lines | 26 | 77.0 | 0.367 | 22 | 80.2 | 0.544 | 77.0 | 0.367 |
| RB | usage | 51 | 69.0 | 0.522 | 48 | 62.6 | 0.570 | 73.7 | 0.389 |
| RB | curve | 60 | 74.0 | 0.552 | 48 | 61.2 | 0.644 | 73.9 | 0.532 |
| RB | blend | 60 | 72.1 | 0.547 | 48 | 59.3 | 0.614 | 72.5 | 0.519 |
| RB | lines | 53 | 61.5 | 0.584 | 48 | 58.9 | 0.626 | 58.9 | 0.632 |
| WR | usage | 60 | 68.4 | 0.365 | 58 | 69.5 | 0.392 | 66.4 | 0.371 |
| WR | curve | 71 | 58.7 | 0.498 | 58 | 58.6 | 0.479 | 56.3 | 0.494 |
| WR | blend | 71 | 60.1 | 0.471 | 58 | 60.2 | 0.470 | 57.3 | 0.500 |
| WR | lines | 69 | 62.6 | 0.480 | 58 | 62.2 | 0.471 | 64.8 | 0.347 |
| TE | usage | 19 | 51.1 | 0.388 | 18 | 46.7 | 0.560 | 51.1 | 0.388 |
| TE | curve | 20 | 50.5 | 0.511 | 18 | 46.2 | 0.628 | 50.5 | 0.511 |
| TE | blend | 20 | 52.7 | 0.385 | 18 | 46.2 | 0.614 | 52.7 | 0.385 |
| TE | lines | 19 | 54.0 | 0.456 | 18 | 50.7 | 0.560 | 54.0 | 0.456 |

Alpha grid (weight on the usage arm; the rest on the market term). Best by MAE / by Spearman:

| pos | vs curve: best MAE α (MAE) | best ρ α (ρ) | vs lines: best MAE α (MAE) | best ρ α (ρ) |
|---|---|---|---|---|
| QB | 1.0 (73.8) | 0.2 (0.477) | 1.0 (73.8) | 0.3 (0.588) |
| RB | 0.5 (65.6) | 0.2 (0.579) | 0.4 (57.6) | 0.3 (0.659) |
| WR | 0.0 (57.3) | 0.0 (0.470) | 0.0 (62.2) | 0.0 (0.471) |
| TE | 0.0 (47.1) | 0.0 (0.630) | 1.0 (46.7) | 0.3 (0.635) |

## 2024->2025

Pool 205 players; FFC names unmatched to Sleeper: 1; week-1 lines kept 835, dropped as late updates 0, blank 8584 — every row carried one bulk re-stamp date after week 1 (a touch, not a revision: the lines are still fractional projections), so all were kept.

| pos | arm | n | MAE | Spearman | n common | MAE common | Spearman common | MAE top36 | Spearman top36 |
|---|---|---|---|---|---|---|---|---|---|
| QB | usage | 26 | 73.0 | 0.031 | 26 | 73.0 | 0.031 | 73.0 | 0.031 |
| QB | curve | 29 | 71.6 | 0.082 | 26 | 72.6 | 0.070 | 71.6 | 0.082 |
| QB | blend | 29 | 71.0 | 0.128 | 26 | 71.9 | 0.105 | 71.0 | 0.128 |
| QB | lines | 29 | 91.2 | -0.002 | 26 | 85.5 | -0.091 | 91.2 | -0.002 |
| RB | usage | 50 | 74.0 | 0.551 | 44 | 73.5 | 0.572 | 82.6 | 0.333 |
| RB | curve | 64 | 70.7 | 0.627 | 44 | 70.9 | 0.662 | 66.1 | 0.665 |
| RB | blend | 64 | 69.1 | 0.622 | 44 | 70.6 | 0.637 | 71.8 | 0.543 |
| RB | lines | 56 | 65.9 | 0.618 | 44 | 67.3 | 0.660 | 68.6 | 0.586 |
| WR | usage | 72 | 72.1 | 0.458 | 64 | 66.7 | 0.475 | 76.3 | 0.248 |
| WR | curve | 86 | 70.0 | 0.540 | 64 | 66.1 | 0.464 | 72.2 | 0.219 |
| WR | blend | 86 | 70.2 | 0.529 | 64 | 65.8 | 0.471 | 72.6 | 0.234 |
| WR | lines | 78 | 67.1 | 0.517 | 64 | 71.7 | 0.420 | 84.9 | 0.182 |
| TE | usage | 22 | 48.7 | 0.170 | 21 | 47.6 | 0.119 | 48.7 | 0.170 |
| TE | curve | 26 | 45.8 | 0.411 | 21 | 45.9 | 0.291 | 45.8 | 0.411 |
| TE | blend | 26 | 45.0 | 0.221 | 21 | 45.1 | 0.131 | 45.0 | 0.221 |
| TE | lines | 24 | 43.4 | 0.346 | 21 | 46.6 | 0.318 | 43.4 | 0.346 |

Alpha grid (weight on the usage arm; the rest on the market term). Best by MAE / by Spearman:

| pos | vs curve: best MAE α (MAE) | best ρ α (ρ) | vs lines: best MAE α (MAE) | best ρ α (ρ) |
|---|---|---|---|---|
| QB | 0.1 (72.4) | 0.2 (0.092) | 1.0 (73.0) | 0.9 (0.035) |
| RB | 0.7 (73.6) | 0.1 (0.692) | 0.3 (65.7) | 0.2 (0.679) |
| WR | 0.0 (69.1) | 0.0 (0.508) | 0.9 (66.5) | 0.8 (0.487) |
| TE | 0.5 (46.8) | 0.0 (0.341) | 0.6 (45.9) | 0.2 (0.349) |


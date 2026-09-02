# Projection backtest — keefamania

Arms built as the pipeline would have built them before each target season's draft; scored against that season's actuals in league scoring, 17-game basis. Population = every player with a FantasyFootballCalculator ADP for the target year (an actual of 0 for anyone who never played: that is the projection's error, not a dropped row). Role gate off (no historical depth chart); no overrides or availability sweep. `lines` = Sleeper week-1 stat lines x 17, rows updated after the week-1 Tuesday dropped.

Configured alphas: {'model_alpha': 0.55, 'stable_veteran': 0.65, 'volatile': 0.4}

## 2023->2024

Pool 158 players; FFC names unmatched to Sleeper: 1; week-1 lines kept 1129, dropped as late updates 0, blank 8291.

| pos | arm | n | MAE | Spearman | n common | MAE common | Spearman common | MAE top36 | Spearman top36 |
|---|---|---|---|---|---|---|---|---|---|
| QB | usage | 20 | 66.6 | 0.501 | 20 | 66.6 | 0.501 | 66.6 | 0.501 |
| QB | curve | 23 | 67.6 | 0.456 | 20 | 72.3 | 0.517 | 67.6 | 0.456 |
| QB | blend | 23 | 64.4 | 0.431 | 20 | 68.6 | 0.561 | 64.4 | 0.431 |
| QB | lines | 23 | 74.1 | 0.484 | 20 | 78.5 | 0.586 | 74.1 | 0.484 |
| RB | usage | 46 | 64.0 | 0.463 | 44 | 58.5 | 0.539 | 68.7 | 0.388 |
| RB | curve | 53 | 67.7 | 0.533 | 44 | 56.7 | 0.626 | 67.3 | 0.522 |
| RB | blend | 53 | 67.1 | 0.528 | 44 | 56.0 | 0.597 | 67.0 | 0.525 |
| RB | lines | 48 | 56.2 | 0.602 | 44 | 54.9 | 0.613 | 55.1 | 0.627 |
| WR | usage | 56 | 57.3 | 0.383 | 55 | 57.7 | 0.403 | 56.3 | 0.338 |
| WR | curve | 64 | 49.9 | 0.454 | 55 | 50.3 | 0.503 | 48.0 | 0.440 |
| WR | blend | 64 | 50.5 | 0.435 | 55 | 50.9 | 0.481 | 48.8 | 0.441 |
| WR | lines | 63 | 51.5 | 0.429 | 55 | 51.9 | 0.457 | 53.7 | 0.309 |
| TE | usage | 17 | 41.2 | 0.384 | 16 | 37.1 | 0.541 | 41.2 | 0.384 |
| TE | curve | 18 | 40.0 | 0.486 | 16 | 36.3 | 0.582 | 40.0 | 0.486 |
| TE | blend | 18 | 42.3 | 0.378 | 16 | 36.8 | 0.556 | 42.3 | 0.378 |
| TE | lines | 17 | 47.4 | 0.363 | 16 | 45.1 | 0.515 | 47.4 | 0.363 |

Alpha grid (weight on the usage arm; the rest on the market term). Best by MAE / by Spearman:

| pos | vs curve: best MAE α (MAE) | best ρ α (ρ) | vs lines: best MAE α (MAE) | best ρ α (ρ) |
|---|---|---|---|---|
| QB | 1.0 (66.6) | 0.4 (0.588) | 1.0 (66.6) | 0.3 (0.644) |
| RB | 0.5 (60.7) | 0.5 (0.537) | 0.4 (54.1) | 0.3 (0.637) |
| WR | 0.0 (49.6) | 0.0 (0.503) | 0.0 (51.9) | 0.3 (0.479) |
| TE | 0.0 (37.5) | 0.0 (0.568) | 1.0 (37.1) | 0.2 (0.588) |

## 2024->2025

Pool 144 players; FFC names unmatched to Sleeper: 0; week-1 lines kept 835, dropped as late updates 0, blank 8584 — every row carried one bulk re-stamp date after week 1 (a touch, not a revision: the lines are still fractional projections), so all were kept.

| pos | arm | n | MAE | Spearman | n common | MAE common | Spearman common | MAE top36 | Spearman top36 |
|---|---|---|---|---|---|---|---|---|---|
| QB | usage | 19 | 77.4 | -0.095 | 19 | 77.4 | -0.095 | 77.4 | -0.095 |
| QB | curve | 20 | 80.8 | -0.079 | 19 | 78.5 | -0.120 | 80.8 | -0.079 |
| QB | blend | 20 | 79.6 | -0.051 | 19 | 77.2 | -0.082 | 79.6 | -0.051 |
| QB | lines | 20 | 90.5 | -0.135 | 19 | 88.0 | -0.253 | 90.5 | -0.135 |
| RB | usage | 39 | 76.4 | 0.430 | 37 | 71.2 | 0.508 | 69.6 | 0.375 |
| RB | curve | 48 | 66.8 | 0.702 | 37 | 67.1 | 0.707 | 58.7 | 0.545 |
| RB | blend | 48 | 68.4 | 0.583 | 37 | 68.2 | 0.634 | 62.8 | 0.503 |
| RB | lines | 45 | 64.9 | 0.654 | 37 | 66.5 | 0.654 | 62.9 | 0.545 |
| WR | usage | 55 | 63.5 | 0.465 | 50 | 59.9 | 0.475 | 64.3 | 0.234 |
| WR | curve | 61 | 60.0 | 0.534 | 50 | 60.0 | 0.496 | 63.3 | 0.217 |
| WR | blend | 61 | 60.1 | 0.521 | 50 | 59.6 | 0.493 | 63.2 | 0.219 |
| WR | lines | 56 | 62.8 | 0.493 | 50 | 64.6 | 0.474 | 72.9 | 0.223 |
| TE | usage | 13 | 35.3 | 0.159 | 13 | 35.3 | 0.159 | 35.3 | 0.159 |
| TE | curve | 15 | 39.0 | -0.046 | 13 | 40.0 | 0.016 | 39.0 | -0.046 |
| TE | blend | 15 | 36.7 | 0.093 | 13 | 37.3 | 0.110 | 36.7 | 0.093 |
| TE | lines | 15 | 38.6 | 0.121 | 13 | 40.9 | 0.225 | 38.6 | 0.121 |

Alpha grid (weight on the usage arm; the rest on the market term). Best by MAE / by Spearman:

| pos | vs curve: best MAE α (MAE) | best ρ α (ρ) | vs lines: best MAE α (MAE) | best ρ α (ρ) |
|---|---|---|---|---|
| QB | 1.0 (77.4) | 0.9 (-0.093) | 1.0 (77.4) | 0.9 (-0.079) |
| RB | 0.0 (70.3) | 0.0 (0.739) | 0.1 (66.2) | 0.2 (0.667) |
| WR | 0.1 (61.3) | 0.1 (0.560) | 1.0 (59.9) | 0.7 (0.498) |
| TE | 1.0 (35.3) | 0.9 (0.159) | 1.0 (35.3) | 0.1 (0.264) |


# Market volume fit: one season or three? (pre-registered 2026-10-06, before any fit)

## Why

The throws a team gets are 75% its own history and 25% a fitted line from the market:
plays and pass rate regressed on the team's spread and the game total
(build_priors.py, `market_env_fit`). The live fit uses one season, 544 team-games, and
the market explains only 2-4% of game-to-game volume. With that little signal, one
season's coefficients are noisy, and they were: the 2024 fit gives a pass-rate slope on
the spread of -0.0042 and on the total of +0.0008, while the 2025 fit gives -0.0022 and
+0.0038. The outside reviewer flagged that 544 is one season. Pooling three seasons
triples the sample, at the cost of older football.

## The arms

- **one** (shipped): fit on season S-1 only, used to predict season S.
- **pooled**: the same regression fit on seasons S-3, S-2 and S-1 together.

Same rows, same variables, same code (build_priors.py's fit, factored out so both arms
call it).

## The measure

Each team-game's market throws, plays x pass rate from the fit at that game's spread
and total, against the team's actual targets (the engine's "throws": passes with a
named receiver). The market fit is applied to throws only (DECISIONS #134), so throws
are what it has to get right. Mean squared error per team-game, regular season, every
game with a spread and total.

## The rule (fixed now)

The process rule: tune on 2022-24, confirm on 2025 once; 2026 is not read.

- **Selection, 2022-24:** pooled is selected if its mean squared error over the three
  seasons is lower than one's. A paired bootstrap of the difference (by team-game, 2,000
  draws) is reported either way.
- **Ship, 2025 read once:** the selected arm ships only if it is no worse than one on
  2025 (point estimate of the difference at or below zero).
- **What ships:** build_priors.py fits on the built season plus the two before it, so
  the live 2026 run uses 2023-25 and every backtest's priors pool the same way. If
  pooled loses, nothing changes and the round is null.

## Result

(Filled in after the runs, below this line, without editing anything above.)

**Run 2026-10-06** (`props/tools/market_fit_check.py`, archived at tag
`archive/market-refit-code`; the factored fit reproduces the shipped 2025 coefficients
exactly).

| Test season | Team-games | MSE one | MSE pooled | Pooled - one |
|---|---|---|---|---|
| 2022 | 542 | 68.79 | 69.43 | +0.64 |
| 2023 | 544 | 53.05 | 51.96 | -1.09 |
| 2024 | 544 | 60.44 | 61.46 | +1.02 |
| **2022-24** | **1,630** | **60.75** | **60.94** | **+0.19 (95% CI -0.29 to +0.67)** |

**Pooled is not selected.** Its error is slightly higher over 2022-24, and the
interval spans zero: the two are indistinguishable, with one season a hair ahead. Per
the rule, 2025 was not read and nothing changes; the one-season fit stays.

Reading: the extra sample does not help because older seasons carry their own league
pass-rate level, so pooling trades noise for drift. Either way the market line moves
throws by well under one per game at a 25% weight, against a typical miss of about
7.8 throws (the square root of 60.8): this knob cannot move the board.

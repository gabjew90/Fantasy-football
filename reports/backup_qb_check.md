# Backup quarterbacks: does the model miss receivers' and QBs' numbers? (pre-registered 2026-10-06, before any run)

## Why

The model blends a receiver's target share and efficiency from his own history and does
not know who is throwing. When a backup starts, the passing game may shrink and its
targets may move. Week 5 2026: Tampa Bay's receivers all sit in the model's Over zones
while the book prices the backup (148 yards in his one start). Before building any
adjustment, this checks whether the miss exists on 2022-25.

## Data

- The shipped engine's harness results, saved per player-game (`backtest.py --seasons
  2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025 --save-results`): projected mean
  catches and receiving yards per receiver, projected passing yards for the starting QB,
  and the actual numbers.
- nflverse play-by-play: who threw the most passes for each team in each game.

## The flag (fixed before looking)

A team-game is a **backup game** when the passer with the most attempts in that game is
not the team's **primary QB**: the passer with the most attempts for that team over its
earlier games of the same season, needing at least two earlier games in which he led the
team in attempts. Team-games without a primary QB yet (weeks 1-2, or no QB with two
starts) are left out of both groups.

## Read

Residual = actual - model mean, per player-game, as a share of the model mean
(sum of actual / sum of model, per group).

- **Receivers** (the receiving population): catches and receiving yards, backup games
  against all other team-games.
- **Quarterbacks** (the starting QB rows): passing yards, the same split.
- Diagnostics only, not part of the rule: WR1 vs other receivers; TE; RB.

**The miss earns an adjustment** if, for receiving yards, the backup-game actual / model
sits below the other games' in BOTH 2022-23 and 2024-25, and the 2024-25 difference has a
95% interval (resampling team-games) excluding zero. Then a pre-registered tuning round
builds the adjustment (a multiplier on the team's passing efficiency and/or volume when
the starter is not the primary QB) and judges it on CRPS like every other round.
Otherwise the board keeps flagging QB changes with no model change.

## Result

(Filled in after the run, below this line, without editing anything above.)

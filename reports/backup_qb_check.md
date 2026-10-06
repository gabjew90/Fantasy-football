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

### Result (2026-10-06): no receiver adjustment earned; the QB gap needs a cleaner split

Shipped engine, harness saved per player-game (props/tools/backup_qb_check.py):

| Period | Market | Backup team-games | actual / model, backup | actual / model, others | Difference (95% CI) |
|---|---|---|---|---|---|
| 2022-23 | receiving yards | 226 | 0.947 | 0.996 | -0.048 (-0.098, +0.001) |
| 2022-23 | catches | 226 | 0.966 | 0.996 | -0.030 (-0.074, +0.013) |
| 2022-23 | QB passing yards | 149 | 0.628 | 1.028 | -0.400 (-0.487, -0.316) |
| 2024-25 | receiving yards | 224 | 0.976 | 0.984 | -0.008 (-0.063, +0.049) |
| 2024-25 | catches | 224 | 0.995 | 0.977 | +0.018 (-0.027, +0.064) |
| 2024-25 | QB passing yards | 152 | 0.752 | 1.023 | -0.271 (-0.357, -0.184) |

- **The rule:** receiving yards run lower in backup games in both periods, but the 2024-25
  interval spans zero, so no receiver adjustment is earned.
- **QB passing yards** sit far below the model in backup games -- but the harness prices the
  depth chart's starter, and a "backup game" here includes games where the primary QB left
  injured or was benched mid-game, which nothing pregame can know. The gap mixes those with
  planned backup starts. Not acted on; the follow-up (pre-registered separately) splits
  planned starts (the backup listed QB1 before kickoff) from in-game exits.
- Diagnostic, not part of the rule: by slot, WR1s ran 0.889 of the model in backup games
  against 0.975 otherwise (WR2 0.939 / 0.976; WR3, TE1 unchanged) -- the shape of a backup
  spreading the ball away from the top target. A WR1-specific rule would need its own
  pre-registration and a fresh look, since this split was seen first here.

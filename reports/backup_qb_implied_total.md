# Backup quarterbacks: does the market's implied team total already carry the drop? (pre-registered 2026-10-06, before any run)

## Why

The backup-QB check (reports/backup_qb_check.md, PR #122) found receivers' yards about
5% under the model in backup games in 2022-23 and about 1% in 2024-25 (neither earned an
adjustment), and starting-QB passing yards 27-40% under. Two problems with reading those
numbers as they stand:

1. The flag was the in-game attempts leader, so a starter hurt in the first quarter made
   it a "backup game" -- that confounds the QB passing gap with in-game exits.
2. The market prices the backup. The book's spread and total move when a backup is named,
   and the engine already takes 25% of its throws and all of its touchdown level from the
   market. If the implied team total carries the drop, a separate backup adjustment would
   count it twice.

The outside reviewer's suggestion: one market-implied-total diagnostic for backup games.

## Data

The shipped engine's harness results per player-game, 2022-25 (the same saved results
PR #122 read); nflverse play-by-play; games.csv spread and total.

## Definitions (fixed now)

- **Planned start:** the team's starter is the passer of its first pass attempt of the
  game. A **backup start** is a game whose starter is not the team's primary QB (the
  passer who started the most of the team's earlier games that season, with at least two
  starts). Team-games without a primary yet are left out.
- **Implied team total:** (total + the team's own spread) / 2, from games.csv (spread
  positive = favoured). **Implied ratio:** this game's implied total over the team's mean
  implied total in its primary-QB starts that season before this game.
- **Team residual:** per team-game, sum of actual receiving yards over sum of the model's
  mean receiving yards for its receivers; for the starting QB, actual over model passing
  yards.

## The test

1. **How much team yardage tracks the implied total in normal games:** fit b on
   primary-QB team-games, 2022-23 only, in log(team residual) = a + b x log(implied
   ratio) (least squares, team-games weighted equally).
2. **Apply it to backup starts:** expected residual = exp(a + b x log(implied ratio)).
   Remaining gap = backup games' (actual / model) minus their expected residual,
   pooled sum-over-sum, 95% interval resampling team-games.

**Verdict, receivers' yards and QB passing yards separately, each in 2022-23 and
2024-25:**
- **"The implied total carries it"** if the remaining gap's interval includes zero in
  both periods AND the adjustment closes at least half of the raw gap in the period
  where the raw gap is largest.
- **"It does not"** if the remaining gap's interval excludes zero in either period on
  the same side as the raw gap. Then a backup adjustment is a candidate for a
  pre-registered tuning round.
- Otherwise **"unresolved"** (thin sample); the board keeps flagging QB changes.

Nothing ships from this diagnostic by itself.

## Result

(Filled in after the run, below this line, without editing anything above.)

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

### Run 2026-10-06 (props/tools/backup_implied_total.py, the shipped engine's 2022-25 harness results)

**Disclosed -- the pre-registered formula had a level bug, found on the first run.** The
level `a` came from a regression on logs; with real team-game noise a mean of logs sits
about 5% under the sum-over-sum ratio the gap is measured on, so "expected" ran ~5% low
and backups looked better than expected (receivers +2.1% / +4.7% after a raw -4.7% /
-1.9%). The slope b still comes from the log fit; the level is now set on the gap's own
scale (sum actual = sum model x exp(a) x ratio^b over the fit games). A test with
realistic noise fails on the old formula and passes on the new one. Both runs reported:

| Market | Period | Backup starts | Implied ratio | Raw gap | Remaining, pre-registered formula | Remaining, corrected (95% CI) |
|---|---|---|---|---|---|---|
| Receivers' yards | 2022-23 | 214 | 0.898 | -4.7% | +2.1% | -2.5% (-7.0, +2.3) |
| Receivers' yards | 2024-25 | 184 | 0.910 | -1.9% | +4.7% | +0.2% (-5.2, +6.2) |
| Starting QB passing | 2022-23 | 136 | 0.924 | -31.4% | -24.5% | -31.1% (-40.3, -21.9) |
| Starting QB passing | 2024-25 | 122 | 0.950 | -19.4% | -13.1% | -19.8% (-28.6, -10.8) |

Fits on 2022-23 primary-QB team-games: receivers b = +0.10 (673 games), QB passing
b = +0.23 (656). Verdicts as pre-registered (corrected formula): **receivers
"unresolved"** (both intervals include zero; the implied total closes 47% of the
2022-23 gap, just under the half required); **QB passing "it does not"**.

**The QB passing gap is not a model miss -- the harness graded the wrong quarterback.**
A check after the verdict (labelled post hoc): the harness grades its own pre-game
starter (the depth chart's), not the man who started. In 73 of 273 backup starts (27%)
those differ -- the depth chart still listed an active primary who did not start -- and
that QB threw 7% of his projection. Where the graded QB is the actual starter, backup
starts run at **0.995** of the model's passing yards (primary starts 1.020). The -20% to
-31% gap above, and the -27% / -40% in reports/backup_qb_check.md, are that grading
error. (The flagged starter threw almost all his team's passes: median share 100%.)

Consequences:
- No backup-QB adjustment is indicated for QB passing or receivers.
- backtest.py now grades the starting-QB markets only when the depth-chart starter
  actually started (DECISIONS #181), reporting how often it did not.
- The live engine picks its starter the same way, so a stale depth chart can price the
  wrong QB live. The report should flag it when the book prices another QB's passing.

# The scoreboard: how a change to the engine is judged (adopted 2026-10-06, before any score from it was read)

## What the engine is for

The user supplies the volume read (targets, carries); the engine turns it into a win chance
at one posted line, and the book's price is the hurdle that chance must clear. Whether the
engine alone knows more than the market is the label gate's question (blend.py), not this
board's. Whether the user's volume reads are good is answered by his logged bets.

So the engine is graded on the two links it owns, near-equally:

1. **Conversion** -- given the volume, are the catches and yards right AT THE LINE?
2. **Spread** -- given the average volume, is the game-to-game spread around it right? It
   moves the price most exactly where a bet is placed (a read well above or below the
   line's break-even): too much spread pulls every confident price toward 50%.

## The measures (props/tools/scoreboard.py, props/tools/conditional_calibration.py)

- **Population:** bettable player-games -- 3+ projected targets (receptions, receiving
  yards); 8+ projected carries for backs (rushing yards, rushing + receiving yards). Zero
  actual volume has no conditional chance and is left out.
- **Stand-in lines:** where a book hangs a line -- the engine's own pre-game median, at the
  half. props/tools/standin_check.py confirms they sit where Sleeper's 2026 lines sit (line
  positions only; no outcome read).
- **Conversion score (main):** with the player's ACTUAL targets / carries plugged into the
  pre-game rates, the Over chance at the stand-in line, scored by log loss (primary) and
  Brier against the outcome. backtest.py --conditional writes it (pc_*).
- **Own-volume score (secondary):** the same lines with the engine's own volume (pu_*) --
  the baseline a user's read departs from.
- **Spread:** real game-to-game spread of targets / carries around the projection in
  stable-role stretches (same team, same starting QB, projection within 20% of the
  stretch's mean, 4+ games) against the model's, by volume band. Real spread includes role
  drift: it is an upper bound, so a model spread above it is too wide for sure.
- **Calibration shape:** the PIT by tenths (10% each when calibrated) and within subgroups
  known before kickoff (favoured by 7+, underdog by 7+, backup QB started), beside the
  volume buckets.

## The rules (every pre-registration from now on cites these)

**Which score judges which change**
- **Conversion and efficiency-spread changes** (catch rate and its game swing, yards per
  catch and its shape, yards per carry and its swing): the conversion score.
- **Volume-spread changes** (share concentrations, team volume dispersion): the spread
  check -- the ratio moves toward 1 in the bands, not past it -- with the own-volume score
  as the guard.
- **Volume-mean changes** (team volume, market carries, the backs' pool): the own-volume
  score on the volume-driven markets, with the soft guards.

**Shipping a change**
- **Detectable:** log loss gain on the market(s) the change targets, 95% interval wholly
  above zero, on the tuning seasons.
- **Big enough to matter:** the change moves the Over chance at the stand-in lines by at
  least **1.0 point** on average (bettable population). A detectable change smaller than
  that is not worth a release split.
- **Confirmed:** on 2026's played weeks (read once), the target market's gain is not
  negative (point estimate).
- **Guards, in like units:** the markets the user bets (receptions, receiving yards,
  rushing yards, rushing + receiving yards, QB passing yards) may not get worse by more
  than 0.5% of their own log loss (point estimate); the others (QB rushing, rushing
  attempts, completions) block only when their interval is wholly worse.
- **Clustering:** intervals resample whole games for player-level changes and whole
  team-seasons for changes that act on a team all season (team volume, carry deductions,
  market terms).

**Multiple looks** (reports/comparisons_ledger_2026.md)
- Every comparison read on the confirmation data is logged in the ledger, by family.
  When k candidates in one family are read against the same confirmation weeks, their
  intervals are at 1 - 0.05 / k.
- No rule changes after a result is read; a changed rule applies to the next round only.

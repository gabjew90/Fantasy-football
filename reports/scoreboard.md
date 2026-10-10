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
- **Stand-in lines** (current definition in the amendments below: the pre-game expectation
  from inputs no setting moves, centred on Sleeper's lines by a fixed factor per market):
  where a book hangs a line -- first written as the engine's own pre-game median, at the
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

## Amendments

- **2026-10-06, after round 30 was registered, before any round read it:** QB rushing yards
  leave the board (DECISIONS #188) and the guards, from the next round on. Round 30's knobs
  do not touch them (the starting QB's yards-per-carry swing is eff_sd_qb, not in the grid).
- **2026-10-06, before any selection read:** the stand-in line is the half nearest below
  the pre-game EXPECTED value from inputs no width setting moves (expected targets x catch
  rate or yards per target; expected carries x yards per carry), not each setting's own
  median -- the median moved with the very knobs under test, so two settings were scored at
  different lines (caught in code review; the round 30 / 31 grids were stopped and rerun).
  Comparisons now refuse rows whose lines differ.

## Stand-in check (props/tools/standin_check.py, 2026 weeks 2-4; line positions only)

| Market | Lines matched | Median gap | Mean gap (stand-in minus posted) | Within |
|---|---|---|---|---|
| Catches | 154 | 0.0 | +0.1 | 97% within 1 |
| Receiving yards | 154 | 5.0 | +3.9 | 56% within 5 |
| Rushing yards | 54 | 6.0 | +3.9 | 44% within 5 |

The expected-value stand-ins sit about 4 yards above Sleeper's yards lines; the first
version (each setting's median) sat about 4 below. Books hang yards lines between the
median and the mean of a skewed distribution, and both versions measure within a few
yards of where real bets sit.
- **2026-10-06, from an outside review (applies from the next round on; no result already
  read is re-judged):**
  - **Decision-zone score:** every comparison also reports the score on cases where the
    reference chance is 25-75%, and log loss and Brier must agree in sign there for a ship.
    Measured on round 30 (already shipped under the old rule): all back-games +0.0074 log
    loss / +0.0018 Brier; decision zone (54% of games) +0.0025 / +0.0009, same sign, 99%
    interval (-0.0031, +0.0080) spanning zero; 4% of the gain came from cases outside 5-95%
    and the 49 games at the probability clip contributed +0.30 of +17.7. The gain sits in the
    5-25% and 75-95% zones -- confident reads -- and is positive, not detectable, at 25-75%.
  - **Resamples:** 10,000 for any interval above 95% (a 99.2% interval from 2,000 rests on
    about 8 values per tail).
  - **Spread check:** stability from role only -- same team, same starting QB, same depth slot
    -- not from the projections (which react to outcomes). Rerun on 2022-25: targets real /
    model 0.88 (0.85-0.91), 0.89 (0.86-0.93), 0.83 (0.77-0.90); carries 1.06, 1.01, 1.01, each
    spanning 1. The conclusion stands.
  - **Volume-ratio split (diagnostic):** in the conditional test, actual volume is an input,
    so splitting by actual / expected volume is legitimate and tests whether extra volume
    comes at lower efficiency.
  - **Stage-1 knobs** are judged on the spread check and the own-volume score only (round 33
    was registered that way).
- **2026-10-06, second outside review (before round 34 reads anything; nothing already read is
  re-judged):**
  - **The decision zone is 15-85%,** not the 25-75% written above: a bet needs about 56%+ at
    typical prices, so decisions sit at 55-85% and the mirror for Unders (the advice that
    widened it). scoreboard.py has used 15-85% since commit c252491; this records it here, where
    the rule lives. Round 30's 25-75% figures above stay as measured.
  - **Stand-in rounding:** the line is the half-point NEAREST the expected value (3.2 -> 3.5),
    not "the half nearest below" as written above -- the code has always done this
    (backtest.standin_half). Every comparison so far was scored at the code's lines, so no
    result changes; the question it measures is the Over at the nearest half.
  - **The frozen cohort:** a candidate is scored on exactly the reference's player-games (its
    own projections never re-select them), with equal outcomes and lines asserted.
  - **Guards are complete or blocked:** every bet market must be present, with 200+ player-games
    and a finite score; missing evidence blocks a ship (scoreboard.guard_verdict).
  - **Combined yards with a zero side:** a back with carries and no target (or targets and no
    carry) is scored on the combined line; only a game with neither is left out.
  - **"Upper bound":** real spread in role-stable stretches usually overstates the true spread
    (undetected drift), so a model spread well above it is likely too wide -- an assumption,
    not a guarantee.
- **2026-10-06, after the leave-one-season-out check (reports/loso_rounds_30_33.md):** every
  selection from round 34 on reports the out-of-fold gain of its rule
  (props/tools/loso_select.py) beside the in-sample gain. Detectability is still read on the
  registered seasons; an out-of-fold gain at or below zero is reported as a warning sign of
  selection, not a separate veto.
- **2026-10-09, before round 44 reads anything (DECISIONS #227):** a change to the SHAPE of a
  volume draw (round 44: an early-exit chance in the carries split) is judged on the own-volume
  score at the stand-in lines for its market and on the PIT tail it targets (moving toward 10%,
  not past), with the spread check as a guard (no band may become too wide for sure). The spread
  check measures variance in stable-role stretches and cannot see shape: for carries it already
  reads 1.01-1.06, so it would reject any added spread by construction, while the carries PIT's
  lower tail runs 3x thin (experiments/game_script_carries.py). Plain concentration changes stay
  judged on the spread check as before.

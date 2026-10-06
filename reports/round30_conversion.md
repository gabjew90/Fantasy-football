# Round 30: the conversion -- catches and yards given the volume (pre-registered 2026-10-06, before any run)

## Why

The scoreboard (reports/scoreboard.md) judges the engine first on conversion: given the
volume the user reads, is the chance at the line right? Tier 2 found the conversion off in
all three places, with the actual volume plugged in (2022-24, outside the 80% range; 20% is
calibrated): backs' rushing yards given carries 11% (far too wide), catches given targets
22% (too narrow), receiving yards given targets 19% (too wide, most at 10+ targets).

## The knobs (efficiency spread only; volume untouched)

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| eff_sd_rush | backs' game-wide yards-per-carry swing | 0.30 | 0, 0.075, 0.15, 0.30 |
| catch_conc | game-to-game catch-rate swing (Beta) | off | off, 200, 100, 50, 25 |
| catch_shape_mult | per-catch yards shape x this (larger = narrower) | 1 (off) | 1, 1.3, 1.6, 2.0 |

catch_conc and catch_shape_mult are crossed (both move receiving yards); eff_sd_rush alone.

## Selection (2022-25, weeks 2-18, corrected harness, `--conditional`)

On the conversion log loss at stand-in lines, bettable population (scoreboard.py), in order:

1. **eff_sd_rush** -- the value with the lowest rushing-yards conversion log loss (others
   shipped).
2. **catch_conc** -- the lowest receptions conversion log loss (shape 1).
3. **catch_shape_mult** -- the lowest receiving-yards conversion log loss, with catch_conc
   at its step-2 pick.

Ties within 0.0005 go to the shipped value. A pick that does not move the Over chance by
1.0 point on average (the scoreboard's minimum effect) stays at the shipped value.

## Ship test (the scoreboard's rule)

For each changed knob, against shipped (game-clustered):
- **Detectable** on its market on 2022-25: log loss gain, 95% interval above zero -- **99%
  for eff_sd_rush**, which belongs to the running-game family already read four times on
  2026 weeks 2-4 (reports/comparisons_ledger_2026.md).
- **Big enough:** moves the Over chance by 1.0+ point on average.
- **Confirmed** on 2026 weeks 2-4, read once: conversion log loss gain not negative on its
  market. (Disclosed: round 28b's whole-chain read on those weeks included eff_sd_rush
  0.075; the conversion score on them has not been read.)
- **Guards:** the other bet markets' conversion log loss no worse than -0.5% of their own
  (point estimate), rushing + receiving included; QB rushing, attempts, completions only if
  clearly worse.

Knobs ship separately: each passes or fails on its own; the passing ones then go in
together, and the combination must also pass the guards on 2022-25.

## Result

(Filled in after the runs, below this line, without editing anything above.)

### Selection, 2022-25 (props/tools/round30_select.py; stand-in lines from pre-game inputs, identical across settings)

Conversion log loss on the bettable population (lower is better):

| Knob | Values (log loss) | Pick |
|---|---|---|
| eff_sd_rush (rushing yards) | 0.30: 0.45588, 0: 0.45067, 0.075: 0.44921, **0.15: 0.44853** | 0.15 |
| catch_conc (receptions) | off: 0.34868, 200: 0.34867, 100: 0.34815, **50: 0.34785**, 25: 0.34858 | 50 |
| catch_shape_mult (receiving yards, catch_conc 50) | **1: 0.51581**, 1.3: 0.51597, 1.6: 0.51692, 2.0: 0.51980 | 1 (shipped) |

Ship checks against shipped (game-clustered):
- **eff_sd_rush 0.15:** rushing-yards conversion log loss +0.00735, **99%** interval
  (+0.00195, +0.01241) -- detectable; moves the Over chance 3.1 points; guards: rushing +
  receiving +1.0%, the rest unchanged.
- **catch_conc 50:** receptions +0.00083 (-0.00031, +0.00202) -- not detectable: stays off.
- **catch_shape_mult:** the narrower shapes score worse at the lines: stays 1.

### Confirmation, 2026 weeks 2-4 (read once)

eff_sd_rush 0.15 vs shipped: rushing-yards conversion log loss **+0.01565** (-0.00090,
+0.02954), 115 back-games, Over chances move 3.4 points; rushing + receiving +0.00170;
every other market identical. **Not negative: round 30 ships eff_sd_rush 0.15**
(resources/width_params.json). The only change: the backs' game-wide yards-per-carry swing
is halved, so a back's rushing yards for a given carry count spread less -- Tier 2 measured
11% of games outside the 80% range given the carries (20% calibrated).

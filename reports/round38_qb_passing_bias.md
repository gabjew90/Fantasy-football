# Round 38: the QB passing draw's level and shape (pre-registered 2026-10-06, before any run)

## Why

The expert review of round 36 (DECISIONS #196) found the shipped QB passing price biased at
the main line: on 2022-25 starters the Over at the stand-in line hit 52.7% while the engine
averaged 47.0% (+5.7 points, 95% +3.3 to +8.0). The diagnosis on the same frames (1,778
starts):

| | Actual | Engine |
|---|---|---|
| Mean passing yards | 228.0 | 223.3 |
| Median | 229.0 | 217.8 (the median of each game's draw, averaged) |
| Median / mean | ~1.00 | 0.975 |

The engine's draw is about 2% low on average, right-skewed where real games are nearly
symmetric, and too wide (14% of games outside the 80% range against a 17-23% bar; the
outcome deciles are hump-shaped and lean right). The median sits low on all three counts,
so an Over near the middle reads several points too low.

## The knobs (QB passing only; nothing else in the simulation moves)

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| pass_shrink | each game's full-game passing draw pulled toward its own simulated mean by this factor, BEFORE the starter-share draw (mean kept; an exit or benching keeps its full effect) | off | off, 0.85, 0.7, 0.55 |
| pass_scale | the passing draw times this (after the shrink) | 1.0 | 1.0, 1.02, 1.04 |

Crossed: 12 settings (backtest.py PASS_BIAS_GRID, `--tune-grid qbbias`). Receivers,
rushing and completions are untouched by construction (the knobs act after the receivers'
draws are summed), so their scores are identical across the grid -- checked, not assumed.

## Selection (2022-24) -- props/tools/round38_select.py

- **Score:** QB passing own-volume log loss at the stand-in line (the score that showed the
  bias), on one frozen cohort (the shipped setting's population).
- **Pick:** the lowest score; ties within 0.0005 go to the setting closest to shipped (fixed
  knob_distance: off sits beyond 0.85); a pick that moves the Over chance by under 1 point on
  average stays shipped.
- **Ship test:** the gain on 2022-24 detectable (95% game-clustered interval above zero),
  log loss and Brier both positive in the 15-85% decision zone, the leave-one-season-out
  gain reported beside it.
- **Width guard:** the pick's whole-chain passing width (share of games outside the 80%
  range) must not move further from the 17-23% bar than shipped's 14%.
- **CRPS guard:** paired CRPS on passing yards (props/tools/paired_crps.py) must not be
  worse (point estimate) -- the change moves the whole distribution, not just one line.

## Confirmation -- read once

2025 is NOT a clean confirmation season: the bias was measured on 2022-25 before this
pre-registration. The confirmation is **2026 weeks 2-4** (starters; a family not yet read on
those weeks): the own-volume log loss gain not negative (point estimate). About a hundred
starts cannot confirm or refute a gain this size; the rule is a sign check, stated as such.
2025 is reported for completeness, never as the confirmation.

## Not tested here

Scoring at lines one step either side of the centre (the expert's method point) needs the
draws, which the harness does not save; it is a follow-up for the scoreboard, not a reason
to hold this round.

## Result

(Filled in after the runs, below this line, without editing anything above.)

### Amendment before any result was read (2026-10-06, after the expert's audit of #99-#143)

The 12-setting run finished; **its results were not opened.** The expert's audit, reproduced
here on the round-36 frames (2022-25 starters, the Over at the stand-in line):

| Team implied points | Starts | Actual / engine yards | Over hit | Engine's Over | Engine's Over given actual targets |
|---|---|---|---|---|---|
| 18 or less | 219 | 0.894 | 38.8% | 46.9% | 41.8% |
| 18-21 | 419 | 0.995 | 49.6% | 47.2% | 46.4% |
| 21-24 | 547 | 1.041 | 53.6% | 46.8% | 47.9% |
| 24-27 | 419 | 1.049 | 56.6% | 47.0% | 47.5% |
| 27+ | 174 | 1.086 | 65.5% | 47.1% | 47.0% |

The same slope in 2022-23 and 2024-25. A level change alone cannot fix a bias that runs from
-8 to +18 points by game environment, so round 38 adds DECISIONS #137's implied-points scale
(code from tag archive/props-pass-implied), with the small exponents #137 never tried:

| Knob | Shipped | Grid |
|---|---|---|
| pass_implied_exp: the draw times (implied points / 22) ** this | 0 | 0, 0.1, 0.2, 0.3, 0.4 |
| pass_scale | 1.0 | 1.0, 1.02, 1.04 |
| pass_shrink (before the share draw) | off | off, 0.7 |

Crossed: 30 settings, one run (the unread 12-setting run is superseded). Selection, ship test,
width and CRPS guards and the 2026 weeks 2-4 confirmation as registered above, plus two guards:

- **Calibration by implied points:** the weighted mean gap |Over hit - engine's Over| over the
  five rows above must fall against shipped on 2022-24, and must not rise on 2026 weeks 2-4
  (point estimate; about a hundred starts, a sign check).
- **Conversion:** the passing log loss with actual targets plugged in must not be worse than
  shipped on 2022-24.

The exponent is gridded with an explicit 0 (off), so the tie rule's distance treats it as an
ordinary value. 2024-25 has now been read by the expert and here: a disclosed extra look; the
fresh evidence is 2026.

Disclosed before the run (code review): the backtest scales by nflverse's closing lines while
the live report scales by the line at run time, so the harness's environment is slightly
better informed; and if an exponent ships, a live run without a spread/total must say the
scale is off (to be added with the ship).

## Result (2026-10-06; props/tools/round38_select.py on the 30-setting grid, 2022-26)

**Pick (the registered rule): pass_implied_exp 0.2, pass_scale 1.04, pass_shrink off.** The
lowest own-volume log loss on 2022-24 was 0.3 / 1.04 / off (0.68901); 0.2 / 1.04 / off
(0.68937) sits inside the 0.0005 tie and closer to shipped.

| Check (pre-registered) | Pick | Shipped | Verdict |
|---|---|---|---|
| Own-volume log loss gain, 2022-24 | +0.0099 (95%: +0.0040, +0.0156) | -- | detectable: pass |
| Decision zone 15-85% (log loss and Brier) | both positive | -- | pass |
| Average move of the Over chance | 4.6 points | -- | pass (bar 1.0) |
| Calibration by implied points, 2022-24 (weighted mean gap) | 1.8 points | 6.3 points | falls: pass |
| Calibration by implied points, 2026 weeks 2-4 | 6.7 points | 11.2 points | does not rise: pass |
| Conversion (actual targets in), 2022-24 | +0.021 better | -- | pass |
| Paired CRPS, 2022-24 (lower is better) | 42.44 | 42.66 | not worse: pass |
| Width: games outside the 80% range, 2022-24 (bar 17-23%) | 11.9% | 13.8% | **further from the bar: FAIL** |
| Confirmation, 2026 weeks 2-4 (88 starts) | +0.026 (+0.003, +0.048) | -- | not negative: pass |
| Leave-one-season-out | +0.0086 (+0.0027, +0.0142); picks 0.2 / 0.3 / 0.2-scale | -- | every fold positive |

The Over rate minus the engine's chance by implied points, 2022-24 (points):

| Setting | 18 or less | 18-21 | 21-24 | 24-27 | 27+ |
|---|---|---|---|---|---|
| Shipped | -5.1 | +1.7 | +6.8 | +9.0 | +11.3 |
| Pick | -3.4 | -0.1 | +2.2 | +1.9 | +1.8 |

**Under the rule as written, round 38 does not ship: the width guard fails.** Why it fails is
mechanical: removing the bias brings more outcomes inside the 80% range (the shipped draw was
already too wide, and its bias hid part of that). The settings with the 0.7 narrowing overshoot
the other way (about 25% outside) and their scores sit outside the tie. Whether to override the
guard is the user's decision; this report does not make it.

### The user's decision (2026-10-06): ship, overriding the width guard

Asked after the result above, the user chose to ship the pick: the width guard read a move
of outcomes into the range (the bias removed) as a widening, which it was not designed to
catch. **Round 38 ships pass_implied_exp 0.2, pass_scale 1.04** (resources/width_params.json).
Calibration after the change, 2022-25 at the stand-in line (Over hit / engine):

| Team implied points | Before | After |
|---|---|---|
| 18 or less | 38.8% / 46.9% | 38.8% / 44.8% |
| 18-21 | 49.6% / 47.2% | 49.6% / 49.1% |
| 21-24 | 53.6% / 46.8% | 53.6% / 51.5% |
| 24-27 | 56.6% / 47.0% | 56.6% / 54.1% |
| 27+ | 65.5% / 47.1% | 65.5% / 56.8% |

The extremes keep part of the lean (27+: 8.7 points; 18 or less: 6.0, on 174 and 219 starts).
The draw stays too wide (11.9% outside the 80% range). A live run without a spread/total turns
the scale off and says so in the sources table.

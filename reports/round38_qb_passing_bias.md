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

# Leave-one-season-out: rounds 30-33's selection rules on seasons they never saw (2026-10-06; outside review finding 7)

Each round picked its setting on 2022-25 and reported an interval on the same seasons,
which ignores the choice. Here each round's registered rule (lowest mean log loss for its
market and score, on the shipped setting's cohort; ties within 0.0005 to the setting closer
to shipped; a pick that moves the Over chance by under 1.0 point stays shipped) picks on
three seasons and is scored against shipped on the fourth, rotating. The pooled
out-of-fold gain is what the PROCEDURE is worth; the in-sample gain is the round's own
number. Tool: props/tools/loso_select.py (reviewed, known-answer tests), on the rounds'
saved grids. Re-aggregation only: no new simulation, nothing changed.

| Round, knob (market, score) | Picks by held-out season (2022 / 23 / 24 / 25) | Out of fold (95%) | In sample (95%) |
|---|---|---|---|
| 30, eff_sd_rush (rushing, conversion) -- SHIPPED 0.15 | 0.15 / 0.15 / 0.15 / 0.15 | **+0.0074 (+0.0033, +0.0112)** | +0.0074 (+0.0035, +0.0112) |
| 30, catch_conc (receptions, conversion) -- not shipped | off / 50 / 50 / 50 | +0.0003 (-0.0008, +0.0013) | +0.0008 (-0.0003, +0.0020) |
| 32, catch_shape_exp (receiving yards, conversion) -- not shipped | shipped in every fold | 0 | 0 |
| 33, team_r_mult (QB passing, own volume) -- not shipped | 2.5 / 1.5 / 2.5 / 2.5 | +0.0003 (-0.0013, +0.0018) | +0.0012 (-0.0005, +0.0027) |

Round 32 here is its exponent at the shipped multiplier (the four settings with
catch_shape_mult off); round 31's rule selects on the spread check, not a log loss, and is
not re-aggregated (it was null).

## Reading

- **Round 30's ship survives the check that matters:** the same setting wins in every
  held-out season and its out-of-fold gain equals the in-sample one -- no winner's curse.
  (Its 2026 weeks 2-4 confirmation was a sign check on reused weeks; this is the stronger
  evidence.)
- **The two candidates that were not shipped shrink out of fold** (catch_conc to about a
  third of its in-sample gain, team_r_mult to a quarter), as the winner's curse predicts:
  their in-sample numbers were partly selection, and the rule was right to stop them.
- From round 34 on, a selection reports this out-of-fold number beside the in-sample one
  (scoreboard amendment below).

# Round 40: the receiving-yards level (pre-registered 2026-10-06, before any run)

## Why

DECISIONS #197 (#99 corrected) and #200: after round 41, the receiving-yards Over at the
stand-in line still hits 2.6 points more often than the engine says on 2022-25 (50.2% vs
47.6%); with actual targets plugged in about 1.2 points of it remains, so part of the miss is
the yards a catch, not the volume. Receptions are close (0.7). Raising receivers' yards also
raises QB passing (their sum), whose level round 38 just set, so passing's level is re-picked
in the same grid.

## The knobs

| Knob | Shipped | Grid |
|---|---|---|
| rec_ypc_mult: every receiver's yards a catch times this (the depth bucket's too) | 1 | 1, 1.02, 1.04, 1.06 |
| pass_scale (round 38's level) | 1.04 | 1, 1.02, 1.04 |

12 settings (`--tune-grid receivinglevel`); everything else as live (props-v1.49).

## Selection -- props/tools/round40_select.py

1. **Stage A:** rec_ypc_mult by the receiving-yards **conversion** log loss (actual targets in;
   the scoreboard's rule for a conversion setting), every receiver, pass_scale 1.04.
2. **Stage B:** pass_scale at stage A's result by QB passing **own-volume** log loss.

Each stage: lowest score, ties within 0.0005 to the value closest to shipped, a move of 1+
point, detectable on 2022-24 (interval above zero, log loss and Brier agreeing in the zone),
**confirmed on 2026 weeks 2-4** (not negative, point estimate), leave-one-season-out reported.
A failed stage keeps its shipped value.

## Guards on the combined setting (2022-24)

- Every market, both scores, no worse than -0.2%.
- The receiving-yards Over-minus-engine gap must shrink overall and not grow in any implied
  points row by more than 2 points; QB passing's weighted gap by implied points must not grow.
- Reported: receptions and the role rows.

## If it ships

The research reads' "we expect" yards a catch (catch_yards_read model_ypc, the QB read's model
yards a completion) take the same multiplier, so the reads match the price; the cards'
calibration rows are re-measured.

## Result

(Filled in after the runs, below this line, without editing anything above.)

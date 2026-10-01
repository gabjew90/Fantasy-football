# Round 14: last season's defense as the opponent shrinkage target -- a measured null

*2026-10-01. Code: branch `props/prior-defense` (commit 6c8db71, not merged). Harness:
`backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023 --test 2024,2025 --opp-prior-carry C`,
C in {0, 0.25, 0.5, 0.75, 1.0}, each season predicted from priors built from the season
before, the live scorer's settings, common random numbers per team-game, paired against
C = 0 by player-week with a 95% interval from resampling whole games.*

## The change tested

Today each defense's efficiency multiplier is shrunk toward league average (1.0) by plays
faced (k0 = 150). The alternative: shrink toward `1 + C x (last season's own shrunk
multiplier - 1)` -- the prior-season table `build_priors.py` already writes
(`priors_{S-1}_opponent.csv`) and the scorer never read. C = 0 is today's model, byte for
byte (unit-tested, and the C = 0 run reproduces `reports/yardage_harness.md` exactly).

## Decision rule, fixed before the results

Pick C on 2022-23 only; ship only if on 2024-25 it is no worse on catches, receiving yards
and rushing yards, at least one improvement has an interval excluding zero, and the four
width/calibration checks still pass. Otherwise C stays 0.

## Result: no setting clears it

Paired change in the model's CRPS, C = 0 minus this run (positive = this run better), with
the game-block 95% interval. No cell excludes zero.

| C | Seasons | Weeks | Receptions | Receiving yards | Rushing yards |
|---|---|---|---|---|---|
| 0.25 | tune 22-23 | 2-4 | +0.0004 [-0.0003, +0.0012] | +0.0023 [-0.0126, +0.0175] | +0.0121 [-0.0202, +0.0423] |
| 0.25 | tune 22-23 | 5-18 | -0.0001 [-0.0003, +0.0001] | -0.0013 [-0.0053, +0.0026] | -0.0008 [-0.0094, +0.0083] |
| 0.25 | test 24-25 | 2-4 | +0.0000 [-0.0009, +0.0010] | -0.0001 [-0.0151, +0.0150] | -0.0031 [-0.0376, +0.0343] |
| 0.25 | test 24-25 | 5-18 | +0.0000 [-0.0002, +0.0003] | +0.0019 [-0.0019, +0.0058] | +0.0034 [-0.0037, +0.0109] |
| 0.5 | tune 22-23 | 2-4 | +0.0009 [-0.0004, +0.0024] | +0.0106 [-0.0148, +0.0358] | +0.0190 [-0.0454, +0.0789] |
| 0.5 | tune 22-23 | 5-18 | -0.0002 [-0.0005, +0.0001] | -0.0001 [-0.0065, +0.0062] | -0.0031 [-0.0203, +0.0152] |
| 0.5 | test 24-25 | 2-4 | +0.0004 [-0.0013, +0.0023] | +0.0026 [-0.0226, +0.0297] | -0.0107 [-0.0802, +0.0639] |
| 0.5 | test 24-25 | 5-18 | +0.0000 [-0.0004, +0.0004] | +0.0018 [-0.0042, +0.0080] | +0.0055 [-0.0088, +0.0206] |
| 0.75 | tune 22-23 | 2-4 | +0.0011 [-0.0007, +0.0033] | +0.0216 [-0.0140, +0.0577] | +0.0203 [-0.0762, +0.1105] |
| 0.75 | tune 22-23 | 5-18 | -0.0002 [-0.0007, +0.0003] | -0.0003 [-0.0090, +0.0083] | -0.0068 [-0.0328, +0.0205] |
| 0.75 | test 24-25 | 2-4 | +0.0005 [-0.0020, +0.0033] | +0.0068 [-0.0278, +0.0455] | -0.0226 [-0.1274, +0.0888] |
| 0.75 | test 24-25 | 5-18 | +0.0000 [-0.0005, +0.0006] | +0.0016 [-0.0066, +0.0104] | +0.0063 [-0.0152, +0.0289] |
| 1.0 | tune 22-23 | 2-4 | +0.0016 [-0.0009, +0.0043] | +0.0208 [-0.0270, +0.0700] | +0.0161 [-0.1119, +0.1351] |
| 1.0 | tune 22-23 | 5-18 | -0.0002 [-0.0008, +0.0004] | -0.0010 [-0.0123, +0.0097] | -0.0121 [-0.0466, +0.0246] |
| 1.0 | test 24-25 | 2-4 | +0.0006 [-0.0029, +0.0043] | +0.0042 [-0.0396, +0.0530] | -0.0390 [-0.1782, +0.1092] |
| 1.0 | test 24-25 | 5-18 | -0.0001 [-0.0007, +0.0006] | +0.0008 [-0.0098, +0.0116] | +0.0059 [-0.0228, +0.0360] |

Reference CRPS (C = 0, all seasons): receptions 1.034, receiving yards 13.475, rushing
yards 16.262. The largest point estimate, +0.0216 on early-season receiving yards (tune),
is 0.16% of the score; early-season rushing on the test seasons leans the other way.

## Reading

Last season's defense adds nothing measurable on top of the current-season shrinkage. The
likely reason is upstream: the whole opponent adjustment is small (between-defense spread
about 8% SD in yards per target, about half of it kept), so moving its starting point moves
projections by a fraction of a yard. A defense effect large enough to matter would need a
richer signal (personnel, pass rush), not a different prior on the same team-level ratio.

## Side finding: the current harness verdicts

The C = 0 run reproduces the committed `reports/yardage_harness.md`: receptions, receiving
yards and QB rushing PASS; rushing yards does NOT (calibration, worst 60-90% bucket 0.034
against the 0.03 limit) and QB passing yards does NOT -- it beats baseline A clearly in 2025
(+1.30, interval excludes zero) but not in 2024 (+0.86, interval includes zero), and its
worst bucket (Under at 80-90%, -0.181) rests on 16 cases, the same bucket round 13 flagged.
Round 11's "all three pass" predates rounds 12-13.

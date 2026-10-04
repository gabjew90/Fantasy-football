# Round 23: target share reacts to last week's snap change (pre-registered 2026-10-03, before any run)

## The defect

reports/role_shift_check.md: on props-v1.28's 2022-25 harness results a
receiver whose snaps jumped 15+ points last week while his targets lagged
caught +0.51 (2022-23) / +0.28 (2024-25) more than projected the next week;
one whose snaps fell while his targets held caught about 0.55 fewer in both
periods. The share blend reacts to a role change late.

## The change (model.SNAP_REACT, off = byte for byte)

Blended target share x (last week's snap share / mean of his earlier weeks'
snap share) ** gamma, clipped to [0.6, 1.6]. Applies only when last week is the
week before this one and he has two earlier weeks with the same team (the same
LAST/BASE as the flag). Target share only: the rushing flag was not earned.
In the harness the snaps come from nflverse snap_counts mapped to gsis by
pfr_id; the scorer reads the same file (by name, as it already does).

## Grid (tune seasons 2022-23 only)

gamma in {0.25, 0.5, 1.0}, against props-v1.28 (`base`).

## Selection rule (written before running)

The gamma with the largest paired CRPS gain on receptions + receiving yards
summed over 2022-23, kept only if its gain is positive in BOTH 2022 and 2023
for both markets. Otherwise round 23 is dropped.

## Ship rule (written before running)

The chosen gamma runs ONCE on 2024-25 (held out). It ships only if, against
props-v1.28 on 2024-25:

1. no market (receiving yards, catches, rushing yards, QB passing, QB rushing)
   is worse with a paired 95% CI excluding zero;
2. receptions or receiving yards improves with a CI excluding zero.

2026 weeks 2-3 cannot test it (the rule needs three earlier weeks, so it first
acts in week 4); week 4 onward is the fresh check, read from the settled record.
If 2024-25 is flat, it does not ship and this report records a measured null.

## Result (2026-10-03): shipped at gamma 0.5

Tune seasons, paired CRPS change against props-v1.28 (positive = better,
95% interval from resampling team-weeks):

| Gamma | 2022 catches | 2022 rec yds | 2023 catches | 2023 rec yds |
|---|---|---|---|---|
| 0.25 | +0.0051 (+0.0010, +0.0092) | +0.0798 (+0.0380, +0.1221) | +0.0108 (+0.0070, +0.0144) | +0.0838 (+0.0425, +0.1276) |
| 0.5 | +0.0047 (-0.0020, +0.0114) | +0.0806 (+0.0118, +0.1513) | +0.0120 (+0.0055, +0.0183) | +0.1033 (+0.0336, +0.1723) |
| 1.0 | -0.0085 (-0.0195, +0.0021) | -0.0224 (-0.1289, +0.0879) | +0.0024 (-0.0077, +0.0125) | -0.0058 (-0.1192, +0.1095) |

By the rule, 0.5 (summed gain +0.2006 vs +0.1795 for 0.25; positive in both
seasons for both markets).

Held out, read once (2024-25, harness game-block intervals, pooled):

| Market | Change (95% CI) |
|---|---|
| receptions | +0.0089 (+0.0043, +0.0136) |
| receiving yards | +0.0437 (-0.0051, +0.0921) |
| rushing yards | 0 |
| QB rushing yards | 0 |
| QB passing yards | -0.0745 (-0.1765, +0.0256) |

Ship rule: (1) no market worse with an interval excluding zero -- yes;
(2) receptions improves with an interval excluding zero -- yes. **Ships.**

Disclosed beside it: by season (team-week resampling) QB passing is -0.177
(-0.319, -0.028) in 2024 and +0.029 (-0.099, +0.147) in 2025 -- the pooled
interval includes zero, but 2024 alone is worse. QB passing's worst
calibration band moved 0.055 -> 0.162, entirely the Under 80-90% band with
14 rows (9 hits against ~11.3 expected); every QB passing band with 150+
rows is within 0.03. Catches and receiving yards still pass the four-part
bar (receptions worst band 0.027 -> 0.018; receiving yards 0.025 -> 0.020).

Live check on pinned odds (DAL@HOU): 14 of 41 rows move, all receiving except
simulation noise (under 0.01); Dalton Schultz (snaps 54% last week vs 67%)
projects 6.3 targets instead of 7.1 and his catches Over goes 59% -> 50%.
2026 weeks 2-3 cannot test it (it first acts in week 4); the settled record
from week 4 is the fresh check.

## Round 25 (pre-registered 2026-10-03, before any run): a separate exponent for a snap increase

reports/role_shift_check.md's addendum found round 23 overshooting receivers
whose snaps jumped in 2024-25 (WR/TE role up: -0.38 catches, interval
excluding zero) while 2022-23 showed no overshoot. That slice was seen on the
held-out seasons, so the test is set on 2022-23 only and 2024-25 is read once.

Change: `model.SNAP_REACT_UP`, the exponent used when last week's snaps are
ABOVE his earlier weeks (decreases keep 0.5). Grid on 2022-23: SNAP_REACT_UP
in {0.5 (= round 23), 0.35, 0.25, 0.0}.

Selection: the value with the largest paired CRPS gain against round 23 on
receptions + receiving yards summed over 2022-23, kept only if positive in
both seasons for both markets; otherwise round 25 is dropped (round 23 stays
as shipped).

Ship rule (2024-25, read once): receptions or receiving yards better than
round 23 with an interval excluding zero, and no market worse with an
interval excluding zero.

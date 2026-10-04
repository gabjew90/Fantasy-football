# Role-shift flag: does it mean anything? (pre-registered 2026-10-03, before any run)

## Question

When a player's snap share moves while his target (or carry) share has not
caught up, does he beat or miss the shipped model's projection the next week?
If yes, the flag earns a place on the research board with that wording. If
not, the board shows the usage numbers without calling them a flag.

## Data

- Model: props-v1.28's harness results for 2022-25 (`final.pkl`, the run the
  release was read on): per player-week `mean_rec_model`, `mean_car_model` and
  actual receptions / carries.
- Usage: nflverse snap counts (offense_pct, pfr id mapped to gsis via
  players.csv) and play-by-play targets / carries over team totals, by week.
  Free 2026 data has snaps but no routes, so the flag uses snaps only, exactly
  as it could be computed live.

## The flag (fixed before looking)

For player-week W, using only weeks before W in the same season with the same
team: LAST = week W-1 (he must have played it); BASE = his earlier weeks (at
least 2) before W-1.

- **Role up (receiving):** snap share LAST - BASE >= +0.15 and target share
  LAST - BASE < +0.03.
- **Role down (receiving):** snap share LAST - BASE <= -0.15 and target share
  LAST - BASE > -0.03.
- **Role up / down (rushing):** the same with carry share, on rushing rows.

## Read

Residual = actual - model mean (receptions for the receiving flags, carries
for the rushing flags). Mean residual of flagged rows minus unflagged rows,
95% interval from resampling team-weeks. Read 2022-23 first (direction), then
2024-25 once.

- **Flag earns its wording** if the difference has the expected sign (role up
  beats the model, role down misses it) in BOTH periods and the 2024-25
  interval excludes zero.
- Otherwise the board shows "snaps x% (was y%), targets x% (was y%)" with no
  flag and no claim.

## Result (2026-10-03)

Shipped model: props-v1.28 harness results (`final.pkl`), 11,158 of 15,065
player-weeks joined to snap counts (weeks 4-18; a row needs three earlier
weeks with the same team, the last one being W-1).

| Period | Flag | Flagged rows | Flagged minus unflagged residual (95% CI) |
|---|---|---|---|
| 2022-23 | receiving, role up | 351 | +0.509 receptions (+0.335, +0.721) |
| 2022-23 | receiving, role down | 257 | -0.575 receptions (-0.767, -0.390) |
| 2022-23 | rushing, role up | 35 | +2.334 carries (+0.843, +3.918) |
| 2022-23 | rushing, role down | 15 | -2.300 carries (-4.265, -0.530) |
| 2024-25 | receiving, role up | 366 | +0.282 receptions (+0.090, +0.477) |
| 2024-25 | receiving, role down | 237 | -0.545 receptions (-0.745, -0.340) |
| 2024-25 | rushing, role up | 22 | +0.159 carries (-2.135, +2.725) |
| 2024-25 | rushing, role down | 9 | too few rows |

**Receiving flags: earned.** Both have the expected sign in both periods and
2024-25 intervals that exclude zero. A receiver whose snaps jumped last week
while his targets lagged caught about 0.3-0.5 more passes than the model
projected the next week; one whose snaps fell while his targets held caught
about 0.55 fewer. The model's share blend reacts to snaps late.

**Rushing flags: not earned.** Too few rows (a back's snap jump nearly always
comes with carries), and 2024-25 is flat. The board shows the snap and carry
numbers without a flag.

What this does not say: whether the BOOK also reacts late. The flag marks a
model blind spot worth researching; the journal decides whether it pays.

## Addendum (2026-10-03): by position, and against the round-23 model

The same flag and read, split into receivers/tight ends and backs, against
props-v1.28 and against round 23 (target share x (last/earlier snaps) ** 0.5,
reports/snap_react.md). Flagged minus unflagged catches residual (95% CI,
team-week resampling):

| Model | Period | Position | Flag | Rows | Difference |
|---|---|---|---|---|---|
| v1.28 | 2022-23 | WR/TE | role up | 200 | +0.547 (+0.281, +0.863) |
| v1.28 | 2022-23 | WR/TE | role down | 145 | -0.712 (-0.966, -0.442) |
| v1.28 | 2022-23 | RB | role up | 105 | +0.280 (-0.035, +0.589) |
| v1.28 | 2022-23 | RB | role down | 89 | -0.386 (-0.677, -0.035) |
| v1.28 | 2024-25 | WR/TE | role up | 210 | +0.076 (-0.182, +0.338) |
| v1.28 | 2024-25 | WR/TE | role down | 141 | -0.635 (-0.889, -0.332) |
| v1.28 | 2024-25 | RB | role up | 123 | +0.609 (+0.284, +0.930) |
| v1.28 | 2024-25 | RB | role down | 81 | -0.378 (-0.652, -0.048) |
| round 23 | 2022-23 | WR/TE | role up | 200 | +0.064 (-0.201, +0.343) |
| round 23 | 2022-23 | WR/TE | role down | 145 | -0.139 (-0.396, +0.123) |
| round 23 | 2022-23 | RB | role up | 105 | -0.150 (-0.436, +0.155) |
| round 23 | 2022-23 | RB | role down | 89 | +0.079 (-0.206, +0.412) |
| round 23 | 2024-25 | WR/TE | role up | 210 | -0.381 (-0.649, -0.103) |
| round 23 | 2024-25 | WR/TE | role down | 141 | -0.084 (-0.357, +0.206) |
| round 23 | 2024-25 | RB | role up | 123 | +0.153 (-0.185, +0.459) |
| round 23 | 2024-25 | RB | role down | 81 | +0.097 (-0.207, +0.383) |

- Under v1.28 the pattern holds for backs as well as receivers (the advice that
  "snaps are not routes" for backs did not show up in the catches residual).
- Round 23 absorbs it: every cell is within noise except WR/TE role up in
  2024-25, now -0.38 (an overshoot; 2022-23 shows none). That slice is
  post-hoc, so the rule is not changed on it; an asymmetric or position-aware
  exponent is the next test, pre-registered on 2022-23.
- The flag's wording changes accordingly: it marks a role change worth
  researching, and says the projection already moves his share for it. It no
  longer claims the model misses it.

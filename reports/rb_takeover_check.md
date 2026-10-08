# Running-back takeovers: does the model lag them? (pre-registered 2026-10-04, before any run)

## Why

The 2026-10-03 role-shift check (reports/role_shift_check.md) tested a back whose
SNAPS jumped while his carries lagged, and it found too few rows: a back's snaps and
carries usually move together. Week 4 showed the other pattern. Chuba Hubbard went
from about half of Carolina's carries to 83% (20 carries), and the model still
projected about 14; he ran for 122 on a 65.5 line. Tyler Allgeier went the other way
(42% to 7%). This checks whether a sharp change in carry share means the model's next
projection is off.

## Data

- Model: the 2026-10-03 harness run on the current engine (reports/yardage_harness.md,
  round-23 snap rule on): per back-week `mean_car_model` and actual carries, rushing
  population only.
- Carry share: nflverse play-by-play, his carries over his team's carries (kneel-downs
  out), by week.

## The flag (fixed before looking)

For back-week W, using only weeks before W in the same season with the same team:
LAST = week W-1 (he must have carried in it); BASE = his earlier weeks (at least two).

- **Takeover:** carry share LAST - BASE >= +0.20.
- **Demotion:** carry share LAST - BASE <= -0.20.

## Read

Residual = actual carries - model mean. Mean residual of flagged backs minus
unflagged, 95% interval from resampling team-weeks.

- **The flag earns a place** if the difference has the expected sign (a takeover beats
  the model, a demotion misses it) in BOTH 2022-23 and 2024-25, and the 2024-25 interval
  excludes zero. It would then join the board's role flags and point the
  "worth a look" mark for backs.
- Otherwise the board keeps showing the carry share and count with no flag and no claim.

## Result

(Filled in after the run, below this line, without editing anything above.)

### Result (2026-10-04): both flags earned

2,821 back-weeks joined (2022-25, weeks with a W-1 carry and two earlier weeks);
328 takeovers, 218 demotions.

| Period | Flag | Flagged backs | Flagged minus unflagged carries residual (95% CI) |
|---|---|---|---|
| 2022-23 | takeover | 163 | +2.57 carries (+1.62, +3.59) |
| 2022-23 | demotion | 109 | -2.29 carries (-3.21, -1.42) |
| 2024-25 | takeover | 165 | +2.00 carries (+1.10, +2.89) |
| 2024-25 | demotion | 109 | -1.95 carries (-2.87, -0.95) |

Expected sign in both periods, 2024-25 intervals clear of zero: a back whose carry
share jumped 20+ points last week got about two more carries than the model projected
the next week; one whose share fell 20+ points got about two fewer. The model's carry
share reacts to a backfield change late. The flags join the board as "carries up" /
"carries down" on rushing rows and point the "worth a look" mark (Over / Under).

What this does not say: whether the BOOK also lags (the journal decides), or how
the carry gap turns into yards. A model fix (moving carry share by the change, as round
23 does for receivers' target share) is a separate, pre-registered tuning round,
because it would move prices.

*Computed by props/tools/rb_takeover_check.py, deleted 2026-10-08 (DECISIONS #211); the code is in git history at 97a3173.*

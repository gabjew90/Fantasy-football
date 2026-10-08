# Round 27: yards per carry trusts a back's own number too fast? (pre-registered 2026-10-06, before any run)

## Why

An outside reviewer: with per-carry SD about 6 yards, k = 80 carries implies a true-talent
spread of about 0.67 yards per carry between backs (6 / sqrt(80)); published estimates are
0.25-0.4, which means k of roughly 200-600. Our own luck-free test (reports/robust_ypc_check.md)
agreed in direction: three games of a back's yards per carry predicted his later games worse
than the league average. The shipped value comes from the yearly priors fit (80 in the 2025
file), the fit already found unstable for the receiving constants.

## The knob

Yards per carry's shrinkage, `ypc` k, in carries. Grid: **80 (shipped), 200, 400, 600**.
Everything else at the shipped values (target share 80, catch rate 40, yards per target 80;
carry share from the priors fit).

Run: `backtest.py --seasons 2022,2023,2024,2025 --tune 2022,2023,2024 --test 2025
--k0 ypc=X,target_share=80,catch_rate=40,ypt=80` per arm (the --k0 option replaces the fixed
constants, so they are stated).

## The rule (fixed now)

The process rule from the reviewer: tune on 2022-24, confirm on 2025 once (2024 was read in
earlier rounds; the 2026 live log stays untouched as the only clean test).

- **Selection, 2022-24:** the k with the lowest rushing-yards CRPS over weeks 2-18; an arm is
  eligible only if QB rushing CRPS is no worse than the shipped value (the same constant
  covers a QB's yards per carry). Ties within 0.005 go to the smaller change.
- **Ship, 2025 read once:** the selected k ships only if 2025 rushing-yards CRPS (weeks 2-18)
  beats the shipped 80, QB rushing is no worse, and no calibration verdict worsens.
  Otherwise 80 stays and the round is null.

## Result

(Filled in after the runs, below this line, without editing anything above.)

**Run 2026-10-06** (four arms, each confirmed in its log: `ypc` 80 / 200 / 400 / 600 with
target share 80, catch rate 40, yards per target 80).

Selection window, 2022-24, weeks 2-18 (lower is better):

| ypc k | Rushing yards CRPS (n 3,032) | QB rushing CRPS (n 1,402) |
|---|---|---|
| **80 (shipped)** | **15.791** | **8.984** |
| 200 | 15.866 | 9.044 |
| 400 | 15.934 | 9.094 |
| 600 | 15.972 | 9.119 |

The shipped 80 is best, and every step toward more shrinkage is worse, for backs and
quarterbacks alike. It holds in each season (2022 16.749 vs 16.765 at 200; 2023 15.069
vs 15.146; 2024 15.546 vs 15.675) and in both windows (weeks 2-4 16.634 vs 16.686;
weeks 5-18 15.605 vs 15.684).

**Selected: 80, the shipped value. The round is null**; per the rule, 2025 was not read
and nothing changes.

Reading: the reviewer's 200-600 rests on published talent spreads that isolate the
runner. A back's yards per carry in our data also carries his line and scheme, which
persist from game to game, so his own number deserves more weight than the runner-only
estimate suggests. The luck-free test that pointed the other way
(reports/robust_ypc_check.md) used three games; this grid uses the engine's full
blend over three seasons.

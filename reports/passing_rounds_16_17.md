# Rounds 16-18: pass volume toward the market, and stable receiver shrinkage (props-v1.28)

*2026-10-01. Shipped with round 15 (the backs' carry shares, `reports/rush_lead.md`) in one
release so the prospective record splits once. Each round was tuned on 2022-23 and read once on
2024-25 against the same reference (round 15 alone); the combined release was then checked on all
four seasons and on 2026 weeks 2-3. DECISIONS #134 and #135.*

## Round 16: the market's fitted pass volume (model.MARKET_PASS_WEIGHT = 0.25)

The lead came from DECISIONS #106: the full market environment (plays and pass rate from a
regression on the team's spread and the total) helped QB passing yards 1.5% (interval excluding
zero) and hurt QB rushing. New design: the market moves the PASS volume only -- team targets blend
toward the fitted plays x pass rate; carries keep the team's history (`model.market_pass_volume`).

Tune seasons 2022-23 (paired against round 15 alone, game-block 95% intervals):

| Weight | Catches | Receiving yards | QB passing yards | Combined score |
|---|---|---|---|---|
| 0 | -- | -- | -- | 3.0000 |
| 0.25 | +0.0017 [+0.0001, +0.0033] | +0.0262 [+0.0074, +0.0440] | +0.539 [+0.294, +0.792] | 2.9855 |
| 0.5 | +0.0009 [-0.0019, +0.0038] | +0.0324 [+0.0027, +0.0619] | +0.727 [+0.263, +1.199] | 2.9819 |
| 0.75 | -0.0016 [-0.0058, +0.0025] | +0.0198 [-0.0242, +0.0635] | +0.671 [-0.028, +1.362] | 2.9864 |
| 1.0 | -0.0060 [-0.0116, -0.0006] | -0.0093 [-0.0666, +0.0480] | +0.264 [-0.643, +1.179] | 3.0011 |

**The selection rule changed after these results, and that is disclosed.** The rule fixed before the
runs (#106's: the smallest weight not measurably worse than the best on the combined score, 0
counting) picks 0, because the combined-score tie test is blunt (#106's review: it weights receiver
rows about 7 to 1). The user chose a per-market rule instead -- the smallest weight at which every
affected market is clearly better than no change, 0.25 -- with 2024-25 read exactly once.

Held out, 2024-25 at 0.25: QB passing **+0.298 [+0.085, +0.481]**, catches **+0.001 [+0.000,
+0.002]**, receiving yards +0.012 [-0.004, +0.028]; rushing and QB rushing exactly unchanged. 2026
weeks 2-3: every market positive, none clearly. Live check, NYJ@CHI: the underdog's projected catches
+0.08, the favourite's -0.12, carries unchanged.

## Round 17: fixed shrinkage for yards per target and catch rate (model.K0_FIXED)

Found while checking the receiver yardage shape (whose widths turned out right at every depth):
on 2022-23 the receivers least efficient so far this season ran 13% under their receiving-yards
projection and the most efficient 6% over -- the model pulled efficiency too hard toward the prior.
Cause: `build_priors.py` fits each rate's shrinkage constant on weeks 5-8 of ONE season over a
5-2560 grid, and the fit is unstable: yards per target 160 (for 2022), 640 (for 2023), 160 (2025's,
live now); catch rate 320 then 40. The season with the 640 had the worst error (0.823 -> 1.096
across efficiency quartiles).

Tune 2022-23, nine fixed settings against the yearly fit:

| Setting | Catches | Receiving yards | QB passing | Tie with best |
|---|---|---|---|---|
| yearly fit (today) | -- | -- | -- | **no (measurably worse)** |
| ypt 40, catch 40 (best) | +0.0023 [+0.0006, +0.0041] | +0.0774 [+0.0352, +0.1228] | +0.608 [+0.299, +0.920] | best |
| **ypt 80, catch 40 (chosen)** | +0.0023 [+0.0006, +0.0041] | +0.0754 [+0.0463, +0.1061] | +0.478 [+0.266, +0.698] | yes |

Rule fixed before: among settings tied with the best, the smallest change from today (the largest
constants) -- ypt 80, catch rate 40. Held out, 2024-25: receiving yards **+0.019 [+0.001, +0.036]**,
catches 0.000, QB passing +0.079 [-0.063, +0.226] (weeks 2-4 +0.360, clear); calibration better on
catches (0.028 -> 0.025) and receiving yards (0.030 -> 0.027). Smaller than on the tune seasons
because the yearly fit happened to land near sensible values for 2024-25 -- the fix is insurance
against the bad-fit years as much as a gain. 2026 weeks 2-3: receiving yards +0.010, QB passing
-0.104, both within noise. QB passing's worst calibration bucket (Under 80-90%) moved 0.181 -> 0.306
on 14 cases -- one or two games; the other seven buckets match.

## The combined release (rounds 15 + 16 + 17, the shipped settings)

Paired against props-v1.27 (what prices today), game-block 95% intervals:

| Seasons | Catches | Receiving yards | Rushing yards | QB rushing | QB passing |
|---|---|---|---|---|---|
| test 2024-25 | **+0.002 [+0.000, +0.004]** | **+0.032 [+0.009, +0.056]** | **+0.243 [+0.092, +0.392]** | -0.001 [-0.022, +0.020] | **+0.356 [+0.073, +0.601]** |
| 2026 weeks 2-3 | +0.001 | +0.067 | +0.219 | +0.022 | +0.380 |

The two passing changes add up (receiving yards +0.032 together against +0.012 and +0.019
alone; QB passing +0.356 against +0.298 and +0.079), so there is no bad interaction. Harness
verdicts on the shipped model: catches and receiving yards PASS (calibration 0.027 / 0.028);
QB passing now beats the naive baseline in BOTH test seasons (2024 +1.66, 2025 +1.41, each
clear -- props-v1.27 did not in 2024) but still misses calibration (Over 80-90%, -0.040 on 158
cases; the -0.092 bucket is 14 cases); rushing 0.032 and QB rushing 0.039 as in round 15.
`reports/yardage_harness.md` is re-rendered from this run.

## Round 18, added the same night: target share's shrinkage fixed at 80

A residual sweep of the round-15-17 model (2022-23 only, misses in the same direction in both
seasons) found receivers with the lowest target share so far running 11-15% above projection; the
per-season target-share fit was 20 and 40 for those seasons. Tune: 80 best, 40 / 160 / the fit
measurably worse. Held out 2024-25: catches +0.003 [+0.002, +0.004], receiving yards +0.025
[+0.012, +0.038]. 2026 weeks 2-3 identical to the decimal: this season's fit is already 80.

## The release as shipped (rounds 15-18), against props-v1.27

| Seasons | Catches | Receiving yards | Rushing yards | QB rushing | QB passing |
|---|---|---|---|---|---|
| test 2024-25 | **+0.005 [+0.003, +0.007]** | **+0.057 [+0.031, +0.082]** | **+0.243 [+0.092, +0.392]** | -0.001 [-0.022, +0.020] | **+0.393 [+0.110, +0.640]** |
| tune 2022-23 | +0.011 | +0.148 | +0.327 | -0.008 | +0.856 |

`reports/yardage_harness.md` is re-rendered from this run: catches and receiving yards PASS
(calibration 0.027 / 0.025); rushing (0.032), QB rushing (0.039) and QB passing (0.055) still miss
one calibration band each; QB passing beats the naive baseline in both test seasons.


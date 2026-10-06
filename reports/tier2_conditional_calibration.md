# Tier 2: calibration with the actual volume plugged in, then a two-stage width retune (pre-registered 2026-10-06, before any run)

## Why

The outside reviewer's main point: the engine is used to check lines under the user's
volume thesis, so what matters most is whether the second stage -- catches and yards
GIVEN the targets or carries -- is calibrated. Today's checks grade the whole chain at
once, so a too-wide volume stage can hide a too-narrow efficiency stage (or the reverse).
Our own audit already points that way: the simulated target spread for 8-9.5-target
receivers is 3.9 a game against about 3.3 observed.

## Part A: the diagnostic (no knob moves)

For every backtest player-game (the harness population, 2022-24, weeks 2-18, live
protocol, shipped settings):

1. **Stage 1, volume:** the model's simulated targets (receivers) and carries (backs, and
   the starting QB) against the actual count: PIT, share below p10 and above p90.
2. **Stage 2, efficiency given volume:** catches and receiving yards drawn GIVEN his actual
   targets; rushing yards GIVEN his actual carries (a QB's without kneel-downs). Every
   other input is the pre-game one the harness already uses (catch rate, yards per target,
   yards per carry, the league carry grid, the width settings) -- no in-game information
   besides the volume itself. Same PIT measures.

Buckets: volume (targets 1-3 / 4-6 / 7-9 / 10+; carries 1-9 / 10-14 / 15-19 / 20+; a
player with zero volume has no stage-2 outcome) and the team's final margin (lost by
9+, within 8, won by 9+). Every share is reported with a 95% interval from resampling
whole games.

**Reading:** a calibrated stage puts 10% below p10 and 10% above p90 (20% outside). A
stage is called too narrow / too wide only when the interval for "outside p10-p90"
excludes 20%. Part A changes nothing by itself; it decides which knobs Part B may touch.

Code: backtest.py `--conditional` (adds columns, off by default; the default run stays
byte-identical) and props/tools/conditional_calibration.py (reads the saved results).
The conditional draws use model.py's own per-player samplers, factored out of the joint
sampler so both run the same code, on a separate random stream.

## Part B: two-stage retune (only for stages Part A flags)

- **Stage 1 knobs:** share_conc_targets (now 40), share_conc_carries (now 20), and the team
  volume dispersion only if stage 1 is off for every share size.
- **Stage 2 knobs:** catch_conc (now off), eff_sd_rec (now 0), eff_sd_rush (now 0.30).
- **Selection, 2022-24:** for each flagged stage, the grid value whose stage's outside-
  p10-p90 share is closest to 20% (that stage's own diagnostic, not the whole chain).
  Grids: concentrations x0.5 / x0.75 / x1 / x1.5 / x2 of the current value; catch_conc
  off / 200 / 100 / 50; eff_sd_rec 0 / 0.1 / 0.2 / 0.3; eff_sd_rush 0.15 / 0.3 / 0.45.
- **Ship, 2025 read once:** the selected settings ship only if, on 2025 weeks 2-18, the
  whole-chain CRPS is no worse than shipped for every market they touch (point estimate)
  and no calibration verdict worsens. Otherwise the shipped widths stay and Part B is null.

## Result

(Filled in after the runs, below this line, without editing anything above.)

**Disclosed before any full run:** the smoke run (2023-24) showed stage 1 bucketed by
the ACTUAL volume, which selects on the outcome (a 10-target game sits above the model's
p90 by construction). Stage 1 is now bucketed by the PROJECTED volume (the simulation's
mean); stage 2 keeps the actual volume, its input. Final-margin buckets also select on
an outcome the player helped cause, so they are shown as descriptive, never judged.
Both rules have known-answer tests (props/tests/test_conditional_calibration.py), and
the harness itself passed an audit first (reports/harness_audit_2026-10-06.md).

### Part A, 2022-24, weeks 2-18 (shipped settings)

| Stage | Player-games | Outside p10-p90 (95% CI) | Verdict | Where it is worst |
|---|---|---|---|---|
| 1: targets | 9,978 | 18.0% (17.2-18.8) | too wide | projected 6.5+: 15% |
| 2: catches given targets | 8,625 | 22.4% (21.5-23.2) | too narrow | 7-9 targets: 25.2% |
| 2: receiving yards given targets | 8,625 | 18.6% (17.8-19.5) | too wide | 10+ targets: 13.9% |
| 1: carries, backs | 3,032 | 27.2% (25.5-28.9) | too narrow | projected under 9.5: 30.5% |
| 2: rushing yards given carries, backs | 2,795 | 11.3% (10.2-12.5) | too wide | 20+ carries: 6.9% |
| 1: carries, starting QB | 1,402 | 26.0% (23.7-28.2) | too narrow | -- |
| 2: QB rushing yards given carries | 1,149 | 20.0% (17.7-22.4) | ok | -- |

Reading: the reviewer's concern holds. For backs the two stages offset -- volume too
narrow, efficiency far too wide -- so the whole chain looked acceptable while each
stage is off. Flagged for Part B: every stage but QB rushing yards. The starting QB's
carries are flagged too, but no QB knob was pre-registered, so they cannot move in this
round (a later, separately registered round). Receiving yards given targets are too wide
while the only pre-registered yards knob (eff_sd_rec, now 0) can only widen them, so the
per-catch yards shape -- not in the grid -- is the likely lever, also for a later round.

### Part B, selection on 2022-24 (props/tools/conditional_calibration.py --grid)

| Stage | Knob | Shipped -> picked | Stage outside p10-p90, shipped -> picked |
|---|---|---|---|
| 1: targets | share_conc_targets | 40 -> 60 | 18.0% -> 20.6% (ok) |
| 1: carries, backs | share_conc_carries | 20 -> 10 (grid edge) | 27.9% -> 22.0% (still narrow) |
| 2: catches given targets | catch_conc | off -> 50 (grid edge) | 22.4% -> 20.6% (ok) |
| 2: receiving yards given targets | eff_sd_rec | 0 -> 0 | 18.6% (this knob can only widen) |
| 2: rushing yards given carries, backs | eff_sd_rush | 0.30 -> 0.15 (grid edge) | 11.3% -> 17.4% (still wide) |

### Part B, ship test on 2025 (read once; harness fixed to grade only the QB who started, DECISIONS #181)

Picked settings against shipped, paired, 2025 weeks 2-18 (positive = picked better):

| Market | Player-games | CRPS difference (95% CI) |
|---|---|---|
| Receptions | 3,189 | +0.0003 (-0.0014, +0.0019) |
| Receiving yards | 3,189 | -0.0042 (-0.0259, +0.0169) |
| Rushing yards | 997 | +0.0238 (-0.0319, +0.0804) |
| QB rushing yards | 461 | -0.0099 (-0.0447, +0.0237) |
| QB passing yards | 461 | -0.1309 (-0.2579, -0.0002) |
| Rushing attempts | 997 | -0.0004 (-0.0112, +0.0096) |
| QB completions | 461 | -0.0076 (-0.0157, +0.0002) |

Calibration verdicts: none worse; rushing attempts FAIL -> INSUFFICIENT DATA; widths
closer to 0.20 (receptions 0.181 -> 0.197, rushing attempts 0.250 -> 0.197).

**Part B is null: the shipped widths stay.** Five touched markets are worse on the
point estimate (QB passing clearly: wider catches widen passing more than they help).
The stage diagnostics did their job -- each stage moved toward calibration -- but the
whole chain's accuracy did not improve, and that is the ship test.

**Not acted on, a candidate for its own registration:** the running-game knobs alone
(share_conc_carries 10, eff_sd_rush 0.15) fixed the rushing-attempts FAIL and leaned
better on rushing yards. Choosing that subset now would be picked after reading 2025,
so it needs a fresh pre-registration judged on data not yet read (2026 as it settles),
and three picks sat at grid edges, so its grid would extend past them.

Note on the ship test's QB rows: it ran with the first-dropback starter rule; the code
review then widened it to the first three dropbacks, so a gadget first snap cannot
unseat the real starter (about 1% of team-games). Both arms graded the same rows, so the
null verdict does not depend on it.

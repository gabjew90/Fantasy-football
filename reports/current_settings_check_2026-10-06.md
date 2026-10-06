# The current settings, re-checked end to end (2026-10-06; outside review finding 6)

Round 30 (eff_sd_rush 0.30 -> 0.15) shipped on the conversion score -- actual carries
plugged in -- and its automated guards were conversion scores too. The outside review asked
for the whole chain (the engine's own volume) at the new setting, for all five markets, and
for the combined line checked directly inside game scripts. Code: backtest.py at 68ac50f
(the reviewed harness: frozen cohorts, zero-side combined yards, exact receptions chances;
no new-team cap -- that is step 7), `--seasons 2022,2023,2024,2025 --tune 2022,2023 --test
2024,2025 --conditional`, and props/tools/rr_dependence.py. No setting was changed by
anything below.

## Whole-chain width on the test seasons 2024-25 (share outside the model's 80% range; 20% is right, the bar 17-23%)

| Market | Before round 30 (reports/rush_rec_calibration.md) | Now | Verdict now |
|---|---|---|---|
| Receptions | -- | 18.4% (17.4-19.3) | width PASS, bias PASS |
| Receiving yards | 18.4% | 18.4% (17.4-19.3) | width PASS, bias PASS |
| Rushing yards (backs) | 19.8% (18.1-21.6) | **23.4% (21.5-25.2)** | width INSUFFICIENT DATA (leans narrow) |
| Rushing + receiving | 22.3% (20.5-24.0) | **24.9% (23.1-26.8)** | **width FAIL (too narrow)** |
| QB passing yards | 14.4% (12.2-16.8) | 14.4% (12.2-16.8) | width FAIL (too wide), unchanged |
| Rushing attempts (diagnostic) | -- | 26.4% (24.5-28.4) | width FAIL (too narrow) |

## Where bets are decided (round 30's own frames, 2022-25, at the stand-in lines; positive = 0.15 better than 0.30)

| | Conversion (actual volume) | Own volume (the board's numbers) |
|---|---|---|
| Rushing yards, log loss | +0.0074 (+0.0037, +0.0111) | +0.0001 (-0.0012, +0.0012) |
| Rushing + receiving, log loss | +0.0050 (+0.0019, +0.0080) | +0.0003 (-0.0006, +0.0012) |
| Same, decision zone 15-85% | +0.0050 / +0.0040, both intervals above 0 | +0.0003 / +0.0003, both spanning 0 |

Log loss and Brier agree in sign in every cell.

## The combined line inside game scripts (rr_dependence.py, 2022-25 backs, 4,029 back-games)

| Team's pregame spread | Rushing vs receiving residual r (95%) | Outside 80% range |
|---|---|---|
| Pooled | +0.044 (+0.010, +0.079) | 25.0% (23.7-26.4) |
| Favoured by 7+ | +0.078 (-0.006, +0.158) | 23.4% |
| Favoured by 3-7 | +0.052 (-0.011, +0.117) | 26.6% |
| Within 3 | -0.014 (-0.078, +0.055) | 24.8% |
| Underdog by 3-7 | +0.069 (-0.001, +0.140) | 24.5% |
| Underdog by 7+ | +0.075 (-0.011, +0.160) | 25.1% |

## Reading

1. **Round 30 holds where it was aimed and at the lines.** Given the volume (your read), the
   rushing chance is clearly better; with the engine's own volume, the chance at the line
   is unchanged. Nothing here argues for reverting it.
2. **The board's own rushing distributions are now too narrow in the tails.** Narrowing the
   yards-per-carry swing exposed the carries stage, which was already too narrow on the
   whole chain (26% outside). The spread check in role-stable stretches found the carries
   spread about right when the AVERAGE is right (real / model 1.06, 1.01, 1.01), so what is
   missing is the engine's uncertainty about a back's average workload. That matters for
   lines far from the median (alternate lines, long shots), not for the main line. It
   applies to the user's what-ifs too, less strongly: a workload read has error of its own,
   so a what-if priced at the user's number is somewhat overconfident for the same reason,
   mostly far from the middle (correction from the outside reviewer, 2026-10-06). No new
   modelling is needed for that: compare the read with the break-even volume the report
   already prints, and treat a small margin as thin.
3. **No hidden script dependence.** The correlation is small in every spread bucket, and the
   combined line's narrowness is the same in all of them (23-27%), so the cause is the
   shared one above, not a missing rushing/receiving dependence model.
4. **QB passing stays too wide**, unchanged (round 33's team-throws knob did not fix it).

## What follows

- The fix for point 2 is a pre-registered round on the board path only: an uncertainty
  draw on a back's projected carries share (the average), judged on whole-chain width and
  own-volume log loss, with the conversion score as a guard. It waits for the parity
  baseline (step 7) and the leave-one-season-out check (step 8).
- Until then the report wording stands as written on 2026-10-06 (rushing: re-check pending)
  and is updated to this result: rushing and combined distributions run narrow in the
  tails; the main-line chance is unaffected.

## Step 7: the same run with the scorer's new-team cap (harness parity, 779c2db / 68ac50f)

The harness now caps a carried-over prior for a player on a new team, as the scorer does.
Checked first that it does only that: the projected rush share moved for 2,794 of 2,819
new-team player-games and for no one else; team totals moved only on teams with a new-team
player; the 3,243 player-games on teams without one did not move at all. Test seasons
2024-25, share outside the 80% range:

| Market | Without the cap (step 6) | With it (step 7) |
|---|---|---|
| Receptions | 18.4% | 18.4% |
| Receiving yards | 18.4% | 19.0% |
| Rushing yards | 23.4% | 23.5% |
| Rushing + receiving | 24.9% (FAIL) | 25.2% (FAIL) |
| QB passing yards | 14.4% (FAIL) | 14.7% (12.5-17.1, INSUFFICIENT DATA -- a label change only: still too wide) |

Bias and baseline verdicts are unchanged. The capped run is the baseline every comparison
uses from here (compare() refuses to mix the two harnesses). Remaining parity gaps, still
disclosed in every harness report: weekly depth slots, the snap-share role scaling, and
pre-game injury regimes.

## Receiving and passing, stage by stage (the step 7 baseline, 2022-25; share outside the 80% range)

| Projected targets | Target spread real / model (role-stable) | Catches given targets | Rec yards given targets | Catches, whole chain | Rec yards, whole chain |
|---|---|---|---|---|---|
| 3-5 | 0.88 (0.85-0.91) | 21.9% (20.6-23.2) | 19.7% (18.4-20.9) | 19.2% | 20.2% |
| 5-8 | 0.89 (0.86-0.92) | 22.1% (20.7-23.6) | 16.2% (14.9-17.4) | 18.1% | 15.5% |
| 8-11 | 0.84 (0.77-0.91) | 22.5% (19.8-24.9) | 17.5% (15.1-19.9) | 16.8% | 14.0% |

The target spread is too wide in every band, while catches given targets already run at the
narrow edge (22%). Narrowing targets alone would help receiving yards (too wide at 5+
targets, whole chain 14-16%) and push catches past the bar -- so a target-spread change needs
the catch-rate swing widened with it (round 34's joint design), which is likely why round 31,
moving targets alone, came back null.

QB passing: 14.2% (12.6-15.8) outside on the whole chain, 17.9% (16.2-19.7) given every
receiver's actual targets (PIT mean 0.536: slightly low). The too-wide stage is the volume or
the starter-share draw, not the conversion; round 33 ruled out the team-throws dispersion, so
the starter-share draw (an injury or benching risk that applies to every start) is what is
left.

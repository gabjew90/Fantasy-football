# Round 33: the team's game-to-game throws, judged on QB passing (pre-registered 2026-10-06, before any run)

## Why

QB passing yards (a market the user bets) fail their width check: 14.1% of games outside
the model's 80% range on 2022-25, the middle tenths overfull. With every receiver's actual
targets plugged in, passing is close (18.0%), so most of the excess width comes from the
volume -- and for a QB, whose yards sum all his receivers, the share swings cancel and the
team's total throws are what is left. The team targets' dispersion (team_r_mult) was in
round 31's grid, judged there on receivers only.

## The knob

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| team_r_mult | the team targets' negative-binomial dispersion x this (larger = steadier team volume) | 1 (off) | 1, 1.5, 2.5, 4 |

Everything else shipped (round 30's eff_sd_rush 0.15 included).

## Selection (2022-25, weeks 2-18, `--conditional`)

The value with the lowest QB-passing own-volume log loss at the stand-in lines (the
engine's own volume -- this is a volume change), with team-season clustering. Eligible
only if the receivers' target spread stays at or below the real upper bound in every band
(scoreboard spread check: real / model at or below 1.00 in 3-5, 5-8, 8-11). Ties within
0.0005 go to the smaller multiplier. A pick that moves the passing Over chance by less
than 1.0 point stays shipped.

## Ship test

- **Detectable:** passing own-volume log loss gain, interval above zero, team-season
  clustered, at **97.5%** -- the volume-spread family's second candidate read on 2026 weeks
  2-4 (round 31 was the first; reports/comparisons_ledger_2026.md).
- **Big enough:** 1.0+ point average move on passing.
- **Confirmed** on 2026 weeks 2-4, read once: passing own-volume gain not negative.
- **Guards:** receptions and receiving yards own-volume log loss no worse than -0.5% of
  their own (point estimate); conversion scores untouched (they plug in actual volume).

## Result

(Filled in after the runs, below this line, without editing anything above.)

### Selection, 2022-25 (scoreboard; team-season clustered; 10,000 resamples)

| team_r_mult | QB passing own-volume log loss | Receivers' spread ratio (3-5 / 5-8 / 8-11) |
|---|---|---|
| 1 (shipped) | 0.69931 | 0.83 / 0.88 / 0.84 |
| 1.5 | 0.69895 | 0.84 / 0.89 / 0.86 |
| **2.5** | **0.69816** | 0.85 / 0.92 / 0.88 |
| 4 | 0.69905 | 0.85 / 0.91 / 0.90 |

Picked 2.5 (every setting keeps the receivers under the real upper bound). Against shipped:
QB passing own-volume log loss **+0.00115, 97.5% interval (-0.00051, +0.00284)** -- not
detectable; the Over chance moves 1.3 points. Guards: receptions -0.0001, receiving yards
-0.0002, rushing + receiving +0.0013 (relative), all within -0.5%.

**Round 33 is null at the detectability step; 2026 is not read for it.** The team's
throw variance is not where most of QB passing's excess width lives, or the effect is too
small for four seasons to pin; the conditional check (given the targets) runs slightly low,
the other open passing lead.

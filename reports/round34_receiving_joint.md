# Round 34: receiving's two links together -- target spread and catch-rate swing (pre-registered 2026-10-06, before any run)

## Why

The scoreboard's spread check finds the engine's target spread wider than real games in
every band (role-only stretches, 2022-25: real / model 0.88, 0.89, 0.83; an upper-bound
comparison). Narrowing it alone risks the other link: with the actual targets plugged in,
receptions are already too narrow (22.0% of bettable games outside the 80% range) while
receiving yards are slightly wide (18.0%). A narrower target spread would make whole-chain
receptions narrower still, so the share swing and the catch-rate swing move together
(the outside reviewer's point; round 31 moved the first alone).

## The knobs

| Knob | Shipped | Grid |
|---|---|---|
| share_conc_targets (how tightly a share holds game to game) | 40 | 40, 60, 80, 120 |
| catch_conc (game-to-game catch-rate swing; lower = more) | off | off, 100, 50, 25 |

Crossed: 16 settings; everything else shipped (round 30's eff_sd_rush 0.15 included).

## Data split (scoreboard amendment: fresh confirmation)

- **Selection: 2022-24 only.**
- **Confirmation: 2025, read once** -- this family (receiving volume spread + receiving
  conversion) has not been confirmed on 2025, and 2025 holds about four times the
  player-games of 2026 weeks 2-4. 2026 weeks 2-4 are not used (already read for this
  family by round 31).

## Selection rule (2022-24, centred stand-in lines)

Eligible settings: the target spread stays at or below the real upper bound in every band
(role-only stretches; real / model at most 1.00 in 3-5, 5-8, 8-11). Among them, the lowest
**receptions own-volume log loss** (both knobs move it; it is the whole chain your read
travels through). Ties within 0.0005 go to the setting closer to shipped.

## Ship test

- **Detectable on 2022-24:** receptions own-volume log loss gain, 95% interval above zero
  (game-clustered, 10,000 resamples).
- **Decision zone:** in cases whose reference chance is 15-85%, log loss and Brier agree in
  sign (positive).
- **Big enough:** the Over chance moves 1.0+ point on average.
- **Guards:** receiving yards own-volume and conversion log loss, and receptions conversion
  log loss, no worse than -0.5% of their own (point estimate); rushing + receiving and QB
  passing likewise.
- **Confirmed on 2025, read once:** receptions own-volume gain positive with its 95%
  interval above zero is NOT required (one season); the gain must be non-negative and the
  decision-zone signs must agree.

## Result

(Filled in after the runs, below this line, without editing anything above.)

**Amendment, 2026-10-06, before any run:** run on the current harness (priors over active
weeks, the new-team cap, exact receptions chances: DECISIONS #191-192), and scored by the
scoreboard as it now stands -- one frozen cohort, guards complete or BLOCKED
(scoreboard.guard_verdict), the 15-85% decision zone. Eligibility (target spread at or below
the real upper bound in every band) is read on 2022-24. The leave-one-season-out gain of the
rule (props/tools/loso_select.py, over the eligible settings) is reported beside the
in-sample gain. Tool: props/tools/round34_select.py.

### Result (2026-10-06; props/tools/round34_select.py on the 16-setting grid, 2022-25)

Eligible (target spread at or below real in every band, 2022-24): the 12 settings with
share_conc_targets 40-80; all four at 120 narrow the spread past real. Receptions own-volume
log loss on 2022-24 (lower is better): shipped 0.68665; the lowest 0.68515 (80, catch_conc 100);
within the 0.0005 tie, the setting closest to shipped is **share_conc_targets 60, catch_conc off
(0.68551)** -- picked by the registered tie rule.

| Check | Result |
|---|---|
| Gain on 2022-24 (receptions own volume) | +0.00114 (95%: +0.00022, +0.00207) -- detectable |
| Decision zone 15-85% | log loss and Brier both positive (every receptions case falls inside the zone) |
| Average move of the Over chance | 1.41 points (bar 1.0) |
| Guards (conversion and own volume, every market) | pass: receiving yards own volume +0.12%, rushing + receiving -0.02%, QB passing +0.06%; conversion unchanged |
| Confirmation, 2025 (read once) | +0.00028 (-0.00126, +0.00182), not negative; zone signs agree |
| Leave-one-season-out (2022-24) | +0.00083 (-0.00014, +0.00175); picks 60 / 60 / 80, every fold positive |

Widths, 2022-24: the target spread (real / model) 0.88 / 0.89 / 0.82 -> 0.94 / 0.95 / 0.86 --
closer to real; receptions 19.1% -> 21.2% outside the 80% range and receiving yards 17.3% ->
18.7%, both inside the bar. The catch-rate swing was not needed: narrowing targets alone did not
push catches past the bar.

**Round 34 ships share_conc_targets 60** (resources/width_params.json).

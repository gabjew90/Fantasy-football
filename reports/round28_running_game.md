# Round 28: the running game's two stages, retuned alone (pre-registered 2026-10-06, before any run)

## Why

Tier 2 (reports/tier2_conditional_calibration.md) found the backs' two stages off in
opposite directions -- carries too narrow (27% of games outside the model's p10-p90),
rushing yards given carries far too wide (11%) -- and the starting QB's carries too narrow
(26%). Its retune moved receiving and rushing knobs together; on 2025 the receiving side
(catch_conc) made QB passing worse while the running side leaned better on rushing yards
and fixed the rushing-attempts FAIL. Choosing the running side then would have been picked
after reading 2025, so it gets its own round, judged on data no round has tuned on.

## The knobs (nothing else moves)

| Knob | Shipped | Grid |
|---|---|---|
| share_conc_carries (backs' carry split) | 20 | 5, 7.5, 10, 15, 20 |
| eff_sd_rush (backs' game-wide yards-per-carry swing) | 0.30 | 0, 0.075, 0.15, 0.30 |
| share_conc_qb (starting QB's carry share) | 80 | 30, 50, 80 |

The grid runs past Tier 2's edges (10 and 0.15), where its picks sat.

## Selection (tuning data: 2022-25, weeks 2-18)

Corrected harness (starting-QB markets graded only on the QB who started, DECISIONS #181),
`--conditional`, each knob alone with the others shipped.

- Each knob: the value whose own stage's outside-p10-p90 share is closest to 20%
  (props/tools/conditional_calibration.py --grid): carries (backs) -> share_conc_carries;
  rushing yards given carries (backs) -> eff_sd_rush; carries (starting QB) ->
  share_conc_qb. Ties keep the shipped value.
- **Guard:** the three picks together, on 2022-25, must not make rushing yards, rushing
  attempts or QB rushing CRPS worse than shipped (point estimate). If they do, the round
  is null before any 2026 read.

## The ship test (2026 weeks 2-8, read once, after week 8 is graded)

The picked settings against shipped on 2026 weeks 2-8, the corrected harness:

- rushing yards, rushing attempts and QB rushing CRPS each no worse (point estimate),
- no calibration verdict worse in those three markets,
- receiving and passing markets identical (these knobs do not touch them; a difference
  means a bug, and the round stops).

All three hold: ship. Otherwise null, and the shipped widths stay. No look at 2026
weeks 2-8 for this family before the read.

## Result

(Filled in after the runs, below this line, without editing anything above.)

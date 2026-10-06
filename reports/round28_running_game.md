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

### Selection, 2022-25 (props/tools/conditional_calibration.py --grid; corrected harness)

| Stage | Knob | Shipped -> picked | Stage outside p10-p90, shipped -> picked |
|---|---|---|---|
| 1: carries, backs | share_conc_carries | 20 -> 10 | 27.3% -> 21.3% (ok) |
| 2: rushing yards given carries, backs | eff_sd_rush | 0.30 -> 0.075 | about 11% -> 20.0% (ok) |
| 1: carries, starting QB | share_conc_qb | 80 -> 30 | 24.2% -> 19.1% (ok) |

### Guard, 2022-25 (the three picks together vs shipped, paired)

Rushing yards +0.0304 (+0.0038, +0.0611); rushing attempts +0.0136 (+0.0081, +0.0192);
**QB rushing -0.0031 (-0.0269, +0.0203)**; receiving and passing identical.

**The guard fails** (QB rushing worse on the point estimate), so round 28 is null before
any 2026 read; 2026 weeks 2-8 stay unread for this family.

**Round 28b, registered now, after this guard and before its own (disclosed):** the two
BACKS' knobs only (share_conc_carries 10, eff_sd_rush 0.075), share_conc_qb stays 80. Same
guard on 2022-25 (rushing yards, rushing attempts, QB rushing no worse), then the same
2026 weeks 2-8 ship test, read once with round 29 under round 29's joint rule. The QB knob
is the one candidate cause the data names: the backs' knobs barely touch the QB's carries.

### Round 28b guard, 2022-25 (backs' knobs only: share_conc_carries 10, eff_sd_rush 0.075)

Rushing yards +0.0275 (+0.0000, +0.0586); rushing attempts +0.0125 (+0.0072, +0.0180);
QB rushing +0.0025 (-0.0142, +0.0188); receiving and passing identical. **The guard
passes.** Round 28b waits for the one read on 2026 weeks 2-8 (after week 8 is graded),
together with round 29 under its joint rule.

### Amendment, 2026-10-06, before any 2026 read (user: no waiting for midseason)

The ship test reads **2026 weeks 2-4** (every week played so far that a backtest can
score) instead of weeks 2-8, now, once. Same rule otherwise: rushing yards, rushing
attempts and QB rushing CRPS no worse (point estimate), no calibration verdict worse in
those markets, receiving and passing identical; rounds 28b and 29 each on their own test,
then jointly. Disclosed cost: about 550 back-games instead of about 1,300, so a no-worse
rule passes more easily by chance, and the result is reported with its intervals.

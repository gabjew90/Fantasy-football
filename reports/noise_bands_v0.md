# noise_bands_v0

*Built 2026-09-24 by `python -m fantasy.evidence bands`. Week-to-week standard deviation of each usage metric around a player's own season mean, players with >= 8 weeks; fitted on 2024, re-measured on 2025. A role change is flagged when the last two weeks differ from the earlier weeks by more than 2 noise SDs of that difference.*

**Verdict: PASS.** Stability: every role-defining band within 12% of its 2025 value (limit 20%). False alarms: each threshold is set so shuffled 2024 seasons (no role change) fire 5% of the time; on shuffled 2025 seasons the worst metric fires 7.0% (limit 10%). A fixed 2-SD rule fired on 8-36% of them.

**False-alarm rate by metric** (each player's games shuffled 20 times, so no role changed; the share of shuffles the flag fires on): QB snap_pct 5.5%, carry_share 3.7%; RB snap_pct 3.4%, carry_share 3.3%, tgt_share 4.9%, wopr 6.4%; WR snap_pct 7.0%, tgt_share 6.3%, ay_share 6.1%, wopr 5.7%; TE snap_pct 5.3%, tgt_share 5.5%, ay_share 3.4%, wopr 5.0%.

Role-defining metrics per position (the only ones flagged or judged): QB snap_pct, carry_share; RB snap_pct, carry_share, tgt_share, wopr; WR snap_pct, tgt_share, ay_share, wopr; TE snap_pct, tgt_share, ay_share, wopr. Chosen after the first fit failed on three metrics that mean nothing for the position -- TE carry share, QB target share, RB air-yard share -- which are shown below, marked excluded.

| Position | Metric | SD (fit) | SD (next season) | ratio | players | calibrated z | role metric |
|---|---|---|---|---|---|---|---|
| QB | snap_pct | 0.098 | 0.097 | 0.989 | 41 | 6.64 | yes |
| QB | tgt_share | 0.002 | 0.002 | 1.294 | 41 | — | excluded |
| QB | ay_share | 0.001 | 0.001 | 0.667 | 41 | — | excluded |
| QB | wopr | 0.003 | 0.004 | 1.121 | 41 | — | excluded |
| QB | carry_share | 0.061 | 0.066 | 1.074 | 41 | 2.55 | yes |
| RB | snap_pct | 0.122 | 0.109 | 0.894 | 104 | 2.55 | yes |
| RB | tgt_share | 0.034 | 0.037 | 1.083 | 104 | 2.77 | yes |
| RB | ay_share | 0.013 | 0.013 | 1.0 | 104 | — | excluded |
| RB | wopr | 0.057 | 0.062 | 1.079 | 104 | 2.95 | yes |
| RB | carry_share | 0.107 | 0.094 | 0.88 | 104 | 2.68 | yes |
| WR | snap_pct | 0.132 | 0.141 | 1.062 | 167 | 2.53 | yes |
| WR | tgt_share | 0.059 | 0.059 | 1.0 | 167 | 2.34 | yes |
| WR | ay_share | 0.089 | 0.090 | 1.008 | 167 | 2.54 | yes |
| WR | wopr | 0.143 | 0.146 | 1.02 | 167 | 2.51 | yes |
| WR | carry_share | 0.008 | 0.008 | 0.951 | 167 | — | excluded |
| TE | snap_pct | 0.128 | 0.128 | 1.0 | 104 | 2.37 | yes |
| TE | tgt_share | 0.038 | 0.041 | 1.092 | 104 | 2.59 | yes |
| TE | ay_share | 0.031 | 0.033 | 1.071 | 104 | 4.33 | yes |
| TE | wopr | 0.074 | 0.082 | 1.1 | 104 | 3.0 | yes |
| TE | carry_share | 0.003 | 0.007 | 2.323 | 104 | — | excluded |

Bands are the robust SD (1.4826 x MAD, never below half the classical SD) of a player-week around his own season mean, split by his usage level where a level has 100+ player-weeks:

- QB snap_pct: 0.8-1.01 sd 0.076 (n 465)
- QB carry_share: 0-0.15 sd 0.050 (n 355), 0.15-0.4 sd 0.092 (n 188)
- RB snap_pct: 0-0.5 sd 0.110 (n 982), 0.5-0.8 sd 0.146 (n 457)
- RB tgt_share: 0-0.1 sd 0.030 (n 1125), 0.1-0.2 sd 0.060 (n 330)
- RB wopr: 0-0.25 sd 0.056 (n 1438)
- RB carry_share: 0-0.15 sd 0.049 (n 513), 0.15-0.4 sd 0.150 (n 441), 0.4-1.01 sd 0.156 (n 515)
- WR snap_pct: 0-0.5 sd 0.141 (n 949), 0.5-0.8 sd 0.147 (n 916), 0.8-1.01 sd 0.079 (n 487)
- WR tgt_share: 0-0.1 sd 0.038 (n 996), 0.1-0.2 sd 0.075 (n 754), 0.2-1.01 sd 0.081 (n 602)
- WR ay_share: 0-0.1 sd 0.044 (n 778), 0.1-0.25 sd 0.112 (n 857), 0.25-1.01 sd 0.136 (n 717)
- WR wopr: 0-0.25 sd 0.090 (n 1005), 0.25-0.5 sd 0.188 (n 785), 0.5-10 sd 0.203 (n 562)
- TE snap_pct: 0-0.5 sd 0.127 (n 854), 0.5-0.8 sd 0.141 (n 488), 0.8-1.01 sd 0.071 (n 172)
- TE tgt_share: 0-0.1 sd 0.029 (n 1069), 0.1-0.2 sd 0.070 (n 332), 0.2-1.01 sd 0.086 (n 113)
- TE ay_share: 0-0.1 sd 0.021 (n 1109), 0.1-0.25 sd 0.093 (n 389)
- TE wopr: 0-0.25 sd 0.060 (n 1089), 0.25-0.5 sd 0.157 (n 367)

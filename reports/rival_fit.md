# Rival pick model fit (DECISIONS #35)

938 rival picks over 7 rooms from C:\Users\gabje\Desktop\fantasy-football\data\processed\rival_pools.jsonl. Multinomial likelihood over the candidate pool at each pick; grid from #35, values at grid precision; Wilks 90% intervals from 1-D profiles; selection by leave-one-room-out (LORO) log-likelihood per pick. `current` = the engine's model today.

## seat class `away` (n=102, rooms 3)

Exact list-hit share (lowest Yahoo rank among open-starter fits): 0.38. Current engine log-lik per pick: -4.865.

| form | best grid point | log-lik / pick (in-sample) | vs current |
|---|---|---|---|
| gauss_adp | sigma_early=4.0, sigma_late=35.0, need_damp=0.15, scale=0.75 | -3.908 | +0.957 |
| gauss_yrank | sigma_early=4.0, sigma_late=35.0, need_damp=0.15, scale=1.0 | -4.140 | +0.725 |
| mixture | sigma_early=4.0, sigma_late=27.0, need_damp=0.45, pi=0.3, scale=0.75 | -2.978 | +1.887 |

Mixture 90% intervals (grid): sigma_early in [4.0, 6.0]; sigma_late in [21.0, 27.0]; need_damp in [0.45, 0.45]; pi in [0.3, 0.4]; scale in [0.75, 1.0]

LORO held-out log-lik per pick (fit on the other rooms, scored on the held-out room):

| held-out room | n | mixture | gauss_yrank | gauss_adp | current |
|---|---|---|---|---|---|
| 10531886 | 14 | -2.552 | -6.154 | -3.406 | -4.090 |
| 10532940 | 54 | -3.057 | -4.212 | -3.918 | -4.930 |
| 10534350 | 34 | -3.107 | -3.294 | -4.098 | -5.082 |
| **pooled** | 102 | -3.005 | -4.172 | -3.908 | -4.865 |

## seat class `human` (n=300, rooms 3)

Exact list-hit share (lowest Yahoo rank among open-starter fits): 0.28. Current engine log-lik per pick: -3.940.

| form | best grid point | log-lik / pick (in-sample) | vs current |
|---|---|---|---|
| gauss_adp | sigma_early=4.0, sigma_late=27.0, need_damp=0.3 | -3.906 | +0.035 |
| gauss_yrank | sigma_early=4.0, sigma_late=35.0, need_damp=0.15 | -3.902 | +0.038 |
| mixture | sigma_early=4.0, sigma_late=27.0, need_damp=0.45, pi=0.2 | -3.309 | +0.632 |

Mixture 90% intervals (grid): sigma_early in [4.0, 4.0]; sigma_late in [27.0, 27.0]; need_damp in [0.45, 0.45]; pi in [0.2, 0.2]

LORO held-out log-lik per pick (fit on the other rooms, scored on the held-out room):

| held-out room | n | mixture | gauss_yrank | gauss_adp | current |
|---|---|---|---|---|---|
| 10531886 | 120 | -3.833 | -4.092 | -4.374 | -4.340 |
| 10532940 | 80 | -2.899 | -3.678 | -3.634 | -3.688 |
| 10534350 | 100 | -3.294 | -4.008 | -3.700 | -3.663 |
| **pooled** | 300 | -3.404 | -3.953 | -3.952 | -3.940 |

## seat class `unknown` (n=536, rooms 4)

Exact list-hit share (lowest Yahoo rank among open-starter fits): 0.33. Current engine log-lik per pick: -4.024.

| form | best grid point | log-lik / pick (in-sample) | vs current |
|---|---|---|---|
| gauss_adp | sigma_early=4.0, sigma_late=27.0, need_damp=0.3 | -4.008 | +0.017 |
| gauss_yrank | sigma_early=4.0, sigma_late=35.0, need_damp=0.15 | -3.945 | +0.079 |
| mixture | sigma_early=4.0, sigma_late=27.0, need_damp=0.45, pi=0.3 | -3.309 | +0.715 |

Mixture 90% intervals (grid): sigma_early in [4.0, 4.0]; sigma_late in [27.0, 27.0]; need_damp in [0.45, 0.45]; pi in [0.3, 0.3]

LORO held-out log-lik per pick (fit on the other rooms, scored on the held-out room):

| held-out room | n | mixture | gauss_yrank | gauss_adp | current |
|---|---|---|---|---|---|
| 10502459 | 134 | -3.197 | -3.946 | -4.030 | -4.046 |
| 10503516 | 134 | -3.837 | -4.155 | -4.204 | -4.200 |
| 10504572 | 134 | -3.232 | -3.911 | -3.943 | -3.951 |
| 10505450 | 134 | -3.125 | -3.767 | -3.876 | -3.900 |
| **pooled** | 536 | -3.348 | -3.945 | -4.013 | -4.024 |

## G1 (pre-registered)

LORO mixture log-lik per pick -3.005 vs current -4.865: better. pi_away 90% interval [0.3, 0.4]: excludes 0. **G1 PASS.**


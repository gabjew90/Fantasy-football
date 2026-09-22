# Layer 3: who scores together

Tune [2022, 2023], test [2024, 2025], second era [2018, 2019]. Legs = players priced 10%+ by anytime_td_v1 (slot|x0.4|m0.25|qs0.92|pull0.2|cap0.99|qb40|cinf) before kickoff. Exact joint model (td_joint.py).

## Channel-mix multipliers by the opponent's offensive TDs (estimated on tune)

| opponent TDs | qb_rush | rush_in5 | rush_far | pass_ez | pass_rz | pass_far |
|---|---|---|---|---|---|---|
| 0 (166 TDs) | 0.93 | 1.10 | 1.04 | 0.99 | 0.90 | 1.00 |
| 1 (482 TDs) | 1.04 | 1.00 | 1.12 | 0.86 | 1.08 | 1.05 |
| 2 (754 TDs) | 0.98 | 1.13 | 0.98 | 0.98 | 0.96 | 0.95 |
| 3 (556 TDs) | 1.09 | 0.92 | 0.90 | 1.06 | 1.02 | 0.99 |
| 4+ (503 TDs) | 0.92 | 0.86 | 0.99 | 1.10 | 1.01 | 1.02 |

Each bucket shrunk toward 1 by 200 touchdowns.

## The count correlation, and r (PROVISIONAL, not in the shadow model)

| seasons | games | residual correlation (95% CI) |
|---|---|---|
| tune | 543 | +0.208 (+0.133, +0.287) |
| test | 544 | +0.145 (+0.056, +0.228) |
| also | 512 | +0.173 (+0.089, +0.257) |

Pooled residual correlation +0.175; r = 0.432 matches it (moment matching over these games' means). Score-pair likelihood by r, for reference:

| r | tune | test | also |
|---|---|---|---|
| 0 | -3.2801 | -3.3056 | -3.3635 |
| 0.2 | -3.2732 | -3.3014 | -3.3579 |
| 0.3 | -3.2663 | -3.2978 | -3.3528 |
| 0.4 | -3.2598 | -3.2960 | -3.3492 |
| 0.5 | -3.2574 | -3.2998 | -3.3511 |
| 0.6 | -3.2658 | -3.3164 | -3.3661 |

## Tune [2022, 2023]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.1e-15; the copula moves single legs by up to 1.4e-03. Single-leg log loss with the mix shift 0.34625 vs v1 0.34629.

### Pairs, opponents: 28876 in 543 games; both scored 0.0529

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0512 | 0.19572 |  |  |
| joint | 0.0512 | 0.19572 | +0.00000 (-0.00000, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0512 | 0.19562 | -0.00010 (-0.00021, +0.00001) not established | -0.00006 (-0.00014, +0.00002) not established |
| joint + mix shift + copula (provisional) | 0.0535 | 0.19559 | -0.00012 (-0.00036, +0.00011) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.97, 1.03] | 28876 | 543 | 0.0512 | 0.0512 | 0.0529 | 1.034 (0.951, 1.120) | pass |

### Pairs, teammates: 26238 in 543 games; both scored 0.0458

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0515 | 0.17379 |  |  |
| joint | 0.0477 | 0.17346 | -0.00033 (-0.00065, -0.00000) better |  |
| joint + mix shift (SHADOW) | 0.0476 | 0.17346 | -0.00033 (-0.00067, +0.00002) not established | -0.00032 (-0.00065, +0.00000) not established |
| joint + mix shift + copula (provisional) | 0.0477 | 0.17346 | -0.00033 (-0.00067, +0.00001) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 26238 | 543 | 0.0515 | 0.0477 | 0.0458 | 0.961 (0.873, 1.037) | pass |

### Three legs, mixed: 190259 in 543 games; all scored 0.0111

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01142 | 0.05796 |  |
| joint + mix shift (SHADOW) | 0.01060 | 0.05793 | -0.00003 (-0.00015, +0.00010) not established |
| joint + mix shift + copula (provisional) | 0.01150 | 0.05792 | -0.00004 (-0.00010, +0.00002) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 190259 | 543 | 0.0114 | 0.0106 | 0.0111 | 1.053 (0.914, 1.201) | FAIL |

### Three legs, teammates: 51891 in 543 games; all scored 0.0085

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01147 | 0.04571 |  |
| joint + mix shift (SHADOW) | 0.00901 | 0.04527 | -0.00044 (-0.00080, -0.00000) better |
| joint + mix shift + copula (provisional) | 0.00902 | 0.04527 | -0.00044 (-0.00080, -0.00001) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 48131 | 543 | 0.0096 | 0.0075 | 0.0066 | 0.886 (0.712, 1.094) | FAIL |
| (0.8, 0.9] | 3760 | 408 | 0.0354 | 0.0288 | 0.0319 | 1.109 (0.801, 1.386) | FAIL |

## Test [2024, 2025]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.0e-15; the copula moves single legs by up to 1.5e-03. Single-leg log loss with the mix shift 0.35032 vs v1 0.35038.

### Pairs, opponents: 28393 in 544 games; both scored 0.0601

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0559 | 0.21348 |  |  |
| joint | 0.0559 | 0.21348 | -0.00000 (-0.00000, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0559 | 0.21339 | -0.00008 (-0.00020, +0.00004) not established | -0.00005 (-0.00013, +0.00003) not established |
| joint + mix shift + copula (provisional) | 0.0583 | 0.21327 | -0.00021 (-0.00047, +0.00006) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.97, 1.03] | 28393 | 544 | 0.0559 | 0.0559 | 0.0601 | 1.076 (0.992, 1.151) | FAIL |

### Pairs, teammates: 25834 in 544 games; both scored 0.0526

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0553 | 0.19207 |  |  |
| joint | 0.0514 | 0.19199 | -0.00008 (-0.00042, +0.00026) not established |  |
| joint + mix shift (SHADOW) | 0.0513 | 0.19196 | -0.00011 (-0.00046, +0.00024) not established | -0.00007 (-0.00042, +0.00027) not established |
| joint + mix shift + copula (provisional) | 0.0513 | 0.19196 | -0.00011 (-0.00046, +0.00023) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 25834 | 544 | 0.0553 | 0.0514 | 0.0526 | 1.024 (0.934, 1.095) | pass |

### Three legs, mixed: 184335 in 544 games; all scored 0.0132

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01286 | 0.06589 |  |
| joint + mix shift (SHADOW) | 0.01197 | 0.06591 | +0.00002 (-0.00011, +0.00015) not established |
| joint + mix shift + copula (provisional) | 0.01295 | 0.06585 | -0.00004 (-0.00011, +0.00003) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 184335 | 544 | 0.0129 | 0.0119 | 0.0132 | 1.107 (0.965, 1.234) | FAIL |

### Three legs, teammates: 50528 in 544 games; all scored 0.0096

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01251 | 0.05102 |  |
| joint + mix shift (SHADOW) | 0.00985 | 0.05063 | -0.00039 (-0.00076, -0.00002) better |
| joint + mix shift + copula (provisional) | 0.00988 | 0.05063 | -0.00039 (-0.00075, -0.00002) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 45354 | 544 | 0.0098 | 0.0077 | 0.0069 | 0.895 (0.730, 1.035) | FAIL |
| (0.8, 0.9] | 5174 | 459 | 0.0360 | 0.0293 | 0.0340 | 1.161 (0.930, 1.455) | FAIL |

## Also [2018, 2019]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.2e-15; the copula moves single legs by up to 1.5e-03. Single-leg log loss with the mix shift 0.34274 vs v1 0.34276.

### Pairs, opponents: 28493 in 512 games; both scored 0.0526

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0534 | 0.19584 |  |  |
| joint | 0.0534 | 0.19584 | +0.00000 (-0.00000, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0534 | 0.19579 | -0.00005 (-0.00017, +0.00007) not established | -0.00004 (-0.00012, +0.00004) not established |
| joint + mix shift + copula (provisional) | 0.0556 | 0.19589 | +0.00005 (-0.00021, +0.00030) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.97, 1.03] | 28493 | 512 | 0.0534 | 0.0534 | 0.0526 | 0.985 (0.909, 1.067) | pass |

### Pairs, teammates: 26135 in 512 games; both scored 0.0476

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0537 | 0.18257 |  |  |
| joint | 0.0498 | 0.18224 | -0.00033 (-0.00064, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0498 | 0.18224 | -0.00033 (-0.00064, +0.00000) not established | -0.00032 (-0.00063, +0.00001) not established |
| joint + mix shift + copula (provisional) | 0.0498 | 0.18222 | -0.00035 (-0.00065, -0.00002) better |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 26135 | 512 | 0.0537 | 0.0498 | 0.0476 | 0.956 (0.882, 1.036) | pass |

### Three legs, mixed: 193256 in 512 games; all scored 0.0109

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01211 | 0.05736 |  |
| joint + mix shift (SHADOW) | 0.01126 | 0.05725 | -0.00011 (-0.00021, +0.00001) not established |
| joint + mix shift + copula (provisional) | 0.01215 | 0.05732 | -0.00004 (-0.00010, +0.00002) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 193256 | 512 | 0.0121 | 0.0112 | 0.0109 | 0.971 (0.834, 1.112) | pass |

### Three legs, teammates: 53736 in 512 games; all scored 0.0084

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01219 | 0.04684 |  |
| joint + mix shift (SHADOW) | 0.00959 | 0.04625 | -0.00059 (-0.00091, -0.00024) better |
| joint + mix shift + copula (provisional) | 0.00961 | 0.04624 | -0.00060 (-0.00091, -0.00026) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 49048 | 512 | 0.0099 | 0.0077 | 0.0067 | 0.875 (0.731, 1.045) | FAIL |
| (0.8, 0.9] | 4688 | 387 | 0.0362 | 0.0294 | 0.0260 | 0.884 (0.649, 1.112) | FAIL |

## Choosing the shadow model on tune: worst |actual / predicted - 1| over large lift buckets

| candidate | tune | test | also |
|---|---|---|---|
| joint | 0.114 | 0.161 | 0.125 |
| joint + mix shift | 0.150 | 0.195 | 0.147 |
| joint + mix shift + copula | 0.371 | 0.227 | 0.198 |
| joint + copula | 0.114 | 0.184 | 0.519 |

Chosen on tune: **joint**. Gate (b) holds in an era when its worst bucket is within 5%.

| era | chosen model's worst bucket | gate (b) |
|---|---|---|
| test | 0.161 | FAIL |
| also | 0.125 | FAIL |

## Gate (b): every lift bucket with 1,000+ combinations within 5%, shadow model

| era | pairs opponents | pairs teammates | three legs mixed | three legs teammates |
|---|---|---|---|---|
| test | FAIL | pass | FAIL | FAIL |
| also | pass | pass | pass | FAIL |

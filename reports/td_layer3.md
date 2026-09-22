# Layer 3: who scores together

Tune [2022, 2023], test [2024, 2025], second era [2018, 2019]. Legs = players priced 10%+ by anytime_td_v1 (slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf) before kickoff. Exact joint model (td_joint.py).

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

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.3e-15; the copula moves single legs by up to 1.6e-03. Single-leg log loss with the mix shift 0.35290 vs v1 0.35296.

### Pairs, opponents: 27494 in 543 games; both scored 0.0539

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0561 | 0.19890 |  |  |
| joint | 0.0561 | 0.19890 | +0.00000 (-0.00000, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0561 | 0.19882 | -0.00008 (-0.00020, +0.00003) not established | -0.00004 (-0.00013, +0.00004) not established |
| joint + mix shift + copula (provisional) | 0.0585 | 0.19898 | +0.00008 (-0.00018, +0.00032) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.9, 0.97] | 3215 | 0.0733 | 0.0702 | 0.0607 | 0.864 | FAIL |
| (0.97, 1.03] | 19241 | 0.0551 | 0.0551 | 0.0538 | 0.976 | pass |
| (1.03, 1.1] | 5038 | 0.0489 | 0.0508 | 0.0498 | 0.980 | pass |

### Pairs, teammates: 24838 in 543 games; both scored 0.0467

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0559 | 0.17689 |  |  |
| joint | 0.0519 | 0.17630 | -0.00059 (-0.00090, -0.00026) better |  |
| joint + mix shift (SHADOW) | 0.0518 | 0.17629 | -0.00060 (-0.00094, -0.00025) better | -0.00059 (-0.00090, -0.00025) better |
| joint + mix shift + copula (provisional) | 0.0519 | 0.17629 | -0.00060 (-0.00093, -0.00025) better |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.8, 0.9] | 2119 | 0.0365 | 0.0325 | 0.0274 | 0.842 | FAIL |
| (0.9, 0.97] | 22519 | 0.0574 | 0.0534 | 0.0484 | 0.906 | FAIL |
| (0.97, 1.03] | 200 | 0.0854 | 0.0836 | 0.0650 | 0.778 | - |

### Three legs, mixed: 175905 in 543 games; all scored 0.0113

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01297 | 0.05883 |  |
| joint + mix shift (SHADOW) | 0.01206 | 0.05871 | -0.00012 (-0.00024, +0.00000) not established |
| joint + mix shift + copula (provisional) | 0.01308 | 0.05881 | -0.00002 (-0.00008, +0.00005) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 24 | 0.0100 | 0.0079 | 0.0000 | 0.000 | - |
| (0.8, 0.9] | 45923 | 0.0144 | 0.0126 | 0.0110 | 0.869 | FAIL |
| (0.9, 0.97] | 98637 | 0.0122 | 0.0114 | 0.0109 | 0.952 | pass |
| (0.97, 1.03] | 30739 | 0.0134 | 0.0133 | 0.0133 | 1.003 | pass |
| (1.03, 1.1] | 582 | 0.0115 | 0.0119 | 0.0120 | 1.010 | - |

### Three legs, teammates: 47410 in 543 games; all scored 0.0087

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01283 | 0.04698 |  |
| joint + mix shift (SHADOW) | 0.01012 | 0.04632 | -0.00067 (-0.00105, -0.00021) better |
| joint + mix shift + copula (provisional) | 0.01014 | 0.04632 | -0.00066 (-0.00105, -0.00020) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 41043 | 0.0103 | 0.0080 | 0.0065 | 0.812 | FAIL |
| (0.8, 0.9] | 6367 | 0.0291 | 0.0237 | 0.0228 | 0.961 | pass |

## Test [2024, 2025]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.1e-15; the copula moves single legs by up to 1.7e-03. Single-leg log loss with the mix shift 0.35845 vs v1 0.35853.

### Pairs, opponents: 26443 in 544 games; both scored 0.0632

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0617 | 0.22352 |  |  |
| joint | 0.0617 | 0.22352 | -0.00000 (-0.00000, +0.00000) not established |  |
| joint + mix shift (SHADOW) | 0.0618 | 0.22347 | -0.00005 (-0.00018, +0.00008) not established | -0.00002 (-0.00011, +0.00007) not established |
| joint + mix shift + copula (provisional) | 0.0643 | 0.22347 | -0.00005 (-0.00032, +0.00024) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.9, 0.97] | 3523 | 0.0810 | 0.0776 | 0.0735 | 0.948 | FAIL |
| (0.97, 1.03] | 17091 | 0.0607 | 0.0608 | 0.0651 | 1.071 | FAIL |
| (1.03, 1.1] | 5828 | 0.0530 | 0.0552 | 0.0515 | 0.932 | FAIL |
| (1.1, 1.2] | 1 | 0.0323 | 0.0357 | 0.0000 | 0.000 | - |

### Pairs, teammates: 23984 in 544 games; both scored 0.0547

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0606 | 0.19961 |  |  |
| joint | 0.0563 | 0.19931 | -0.00030 (-0.00064, +0.00006) not established |  |
| joint + mix shift (SHADOW) | 0.0562 | 0.19928 | -0.00033 (-0.00069, +0.00004) not established | -0.00029 (-0.00064, +0.00007) not established |
| joint + mix shift + copula (provisional) | 0.0563 | 0.19929 | -0.00032 (-0.00068, +0.00005) not established |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.8, 0.9] | 1815 | 0.0401 | 0.0357 | 0.0320 | 0.895 | FAIL |
| (0.9, 0.97] | 21975 | 0.0619 | 0.0576 | 0.0563 | 0.978 | pass |
| (0.97, 1.03] | 194 | 0.0937 | 0.0917 | 0.0825 | 0.899 | - |

### Three legs, mixed: 165442 in 544 games; all scored 0.0145

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01480 | 0.07182 |  |
| joint + mix shift (SHADOW) | 0.01380 | 0.07182 | -0.00000 (-0.00015, +0.00015) not established |
| joint + mix shift + copula (provisional) | 0.01491 | 0.07181 | -0.00001 (-0.00009, +0.00006) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 28 | 0.0106 | 0.0084 | 0.0000 | 0.000 | - |
| (0.8, 0.9] | 41554 | 0.0165 | 0.0145 | 0.0145 | 1.000 | pass |
| (0.9, 0.97] | 88022 | 0.0139 | 0.0130 | 0.0140 | 1.078 | FAIL |
| (0.97, 1.03] | 34977 | 0.0151 | 0.0149 | 0.0156 | 1.047 | pass |
| (1.03, 1.1] | 861 | 0.0133 | 0.0138 | 0.0058 | 0.420 | - |

### Three legs, teammates: 45033 in 544 games; all scored 0.0102

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01414 | 0.05411 |  |
| joint + mix shift (SHADOW) | 0.01119 | 0.05351 | -0.00060 (-0.00097, -0.00021) better |
| joint + mix shift + copula (provisional) | 0.01122 | 0.05351 | -0.00059 (-0.00096, -0.00020) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 37502 | 0.0108 | 0.0084 | 0.0072 | 0.857 | FAIL |
| (0.8, 0.9] | 7531 | 0.0307 | 0.0251 | 0.0251 | 1.001 | pass |

## Also [2018, 2019]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.2e-15; the copula moves single legs by up to 1.5e-03. Single-leg log loss with the mix shift 0.34751 vs v1 0.34753.

### Pairs, opponents: 27130 in 512 games; both scored 0.0530

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0589 | 0.19773 |  |  |
| joint | 0.0589 | 0.19773 | +0.00000 (+0.00000, +0.00000) worse |  |
| joint + mix shift (SHADOW) | 0.0590 | 0.19770 | -0.00003 (-0.00017, +0.00009) not established | -0.00002 (-0.00011, +0.00006) not established |
| joint + mix shift + copula (provisional) | 0.0614 | 0.19803 | +0.00029 (+0.00003, +0.00054) worse |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.8, 0.9] | 4 | 0.0570 | 0.0509 | 0.2500 | 4.913 | - |
| (0.9, 0.97] | 3919 | 0.0734 | 0.0701 | 0.0653 | 0.932 | FAIL |
| (0.97, 1.03] | 17327 | 0.0576 | 0.0577 | 0.0516 | 0.894 | FAIL |
| (1.03, 1.1] | 5877 | 0.0532 | 0.0554 | 0.0490 | 0.885 | FAIL |
| (1.1, 1.2] | 3 | 0.0280 | 0.0309 | 0.0000 | 0.000 | - |

### Pairs, teammates: 24811 in 512 games; both scored 0.0486

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0587 | 0.18639 |  |  |
| joint | 0.0546 | 0.18577 | -0.00063 (-0.00093, -0.00031) better |  |
| joint + mix shift (SHADOW) | 0.0545 | 0.18574 | -0.00065 (-0.00097, -0.00032) better | -0.00062 (-0.00093, -0.00031) better |
| joint + mix shift + copula (provisional) | 0.0545 | 0.18573 | -0.00066 (-0.00097, -0.00034) better |  |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.8, 0.9] | 1769 | 0.0400 | 0.0356 | 0.0288 | 0.809 | FAIL |
| (0.9, 0.97] | 22817 | 0.0599 | 0.0557 | 0.0497 | 0.892 | FAIL |
| (0.97, 1.03] | 225 | 0.0860 | 0.0842 | 0.0933 | 1.108 | - |

### Three legs, mixed: 179436 in 512 games; all scored 0.0111

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01392 | 0.05842 |  |
| joint + mix shift (SHADOW) | 0.01297 | 0.05820 | -0.00022 (-0.00032, -0.00010) better |
| joint + mix shift + copula (provisional) | 0.01397 | 0.05840 | -0.00002 (-0.00008, +0.00003) not established |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 135 | 0.0089 | 0.0071 | 0.0000 | 0.000 | - |
| (0.8, 0.9] | 46442 | 0.0148 | 0.0130 | 0.0102 | 0.783 | FAIL |
| (0.9, 0.97] | 98497 | 0.0132 | 0.0124 | 0.0107 | 0.867 | FAIL |
| (0.97, 1.03] | 33619 | 0.0149 | 0.0148 | 0.0131 | 0.885 | FAIL |
| (1.03, 1.1] | 743 | 0.0118 | 0.0122 | 0.0283 | 2.311 | - |

### Three legs, teammates: 49600 in 512 games; all scored 0.0087

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01374 | 0.04854 |  |
| joint + mix shift (SHADOW) | 0.01086 | 0.04769 | -0.00085 (-0.00116, -0.00051) better |
| joint + mix shift + copula (provisional) | 0.01088 | 0.04768 | -0.00086 (-0.00117, -0.00053) better |

Shadow model -- by the model's lift over the leg product:

| lift | n | mean leg product | mean model | actual | actual / model | gate |
|---|---|---|---|---|---|---|
| (0.0, 0.8] | 41949 | 0.0107 | 0.0083 | 0.0067 | 0.798 | FAIL |
| (0.8, 0.9] | 7651 | 0.0302 | 0.0247 | 0.0200 | 0.809 | FAIL |

## Gate (b): every lift bucket with 1,000+ combinations within 5%, shadow model

| era | pairs opponents | pairs teammates | three legs mixed | three legs teammates |
|---|---|---|---|---|
| test | FAIL | FAIL | FAIL | FAIL |
| also | FAIL | FAIL | FAIL | FAIL |

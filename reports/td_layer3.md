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

## Dirichlet concentration c, tuned on the three-teammate class (tune)

| c | three-teammate log loss (tune) | combinations | single-leg log loss (no-harm check) |
|---|---|---|---|
| fixed shares | 0.04526 | 51891 | 0.34629 |
| 100 | 0.04524 **chosen** | 51891 | 0.34626 |
| 50 | 0.04525 | 51891 | 0.34625 |
| 30 | 0.04527 | 51891 | 0.34624 |
| 20 | 0.04534 | 51891 | 0.34627 |
| 12 | 0.04555 | 51891 | 0.34640 |
| 8 | 0.04592 | 51891 | 0.34666 |

Applied to every candidate and era below.

## Tune [2022, 2023]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 5.3e-03; the copula moves single legs by up to 1.4e-03. Single-leg log loss with the mix shift 0.34622 vs v1 0.34629.

### Pairs, opponents: 28876 in 543 games; both scored 0.0529

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0512 | 0.19572 |  |  |
| joint | 0.0504 | 0.19575 | +0.00004 (-0.00004, +0.00011) not established |  |
| joint + mix shift | 0.0504 | 0.19566 | -0.00006 (-0.00019, +0.00006) not established | -0.00006 (-0.00014, +0.00001) not established |
| joint + mix shift + copula | 0.0526 | 0.19559 | -0.00012 (-0.00030, +0.00005) not established |  |
| joint + copula | 0.0526 | 0.19569 | -0.00002 (-0.00014, +0.00010) not established |  |

cross-team pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 771 | 149 | 0.0803 | 0.0770 | 0.0674 | 0.876 (nan, nan) | - |
| (0.97, 1.03] | 11147 | 526 | 0.0618 | 0.0620 | 0.0626 | 1.009 (0.917, 1.111) | pass |
| (1.03, 1.1] | 16933 | 543 | 0.0429 | 0.0453 | 0.0459 | 1.013 (0.895, 1.129) | pass |
| (1.1, 1.2] | 25 | 12 | 0.0295 | 0.0326 | 0.0400 | 1.226 (nan, nan) | - |

### Pairs, teammates: 26238 in 543 games; both scored 0.0458

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0515 | 0.17379 |  |  |
| joint | 0.0466 | 0.17344 | -0.00036 (-0.00078, +0.00007) not established |  |
| joint + mix shift | 0.0465 | 0.17344 | -0.00035 (-0.00079, +0.00009) not established | -0.00026 (-0.00061, +0.00009) not established |
| joint + mix shift + copula | 0.0466 | 0.17343 | -0.00036 (-0.00080, +0.00008) not established |  |
| joint + copula | 0.0466 | 0.17344 | -0.00036 (-0.00078, +0.00007) not established |  |

teammate pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.8, 0.9] | 12763 | 543 | 0.0374 | 0.0333 | 0.0299 | 0.899 (0.787, 1.038) | FAIL |
| (0.9, 0.97] | 13470 | 543 | 0.0647 | 0.0592 | 0.0609 | 1.029 (0.932, 1.118) | pass |
| (0.97, 1.03] | 5 | 3 | 0.0548 | 0.0535 | 0.0000 | 0.000 (nan, nan) | - |

### Three legs, mixed: 190259 in 543 games; all scored 0.0111

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01142 | 0.05796 |  |
| joint | 0.01026 | 0.05799 | +0.00003 (-0.00013, +0.00020) not established |
| joint + mix shift | 0.01027 | 0.05795 | -0.00001 (-0.00018, +0.00016) not established |
| joint + mix shift + copula | 0.01114 | 0.05792 | -0.00004 (-0.00011, +0.00003) not established |
| joint + copula | 0.01111 | 0.05795 | -0.00001 (-0.00006, +0.00005) not established |

mixed 3-leg, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 1 | 1 | 0.0103 | 0.0082 | 0.0000 | 0.000 (nan, nan) | - |
| (0.8, 0.9] | 7743 | 357 | 0.0142 | 0.0126 | 0.0136 | 1.080 (0.639, 1.610) | FAIL |
| (0.9, 0.97] | 66230 | 539 | 0.0135 | 0.0126 | 0.0118 | 0.933 (0.786, 1.096) | FAIL |
| (0.97, 1.03] | 81943 | 543 | 0.0105 | 0.0105 | 0.0109 | 1.035 (0.875, 1.209) | pass |
| (1.03, 1.1] | 34310 | 543 | 0.0090 | 0.0094 | 0.0099 | 1.059 (0.803, 1.310) | FAIL |
| (1.1, 1.2] | 32 | 13 | 0.0063 | 0.0070 | 0.0000 | 0.000 (nan, nan) | - |

### Three legs, teammates: 51891 in 543 games; all scored 0.0085

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01147 | 0.04571 |  |
| joint | 0.00862 | 0.04524 | -0.00046 (-0.00088, +0.00003) not established |
| joint + mix shift | 0.00860 | 0.04525 | -0.00045 (-0.00088, +0.00006) not established |
| joint + mix shift + copula | 0.00862 | 0.04525 | -0.00045 (-0.00088, +0.00006) not established |
| joint + copula | 0.00862 | 0.04524 | -0.00046 (-0.00088, +0.00003) not established |

three teammates, tune-chosen model (joint), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 51844 | 543 | 0.0114 | 0.0086 | 0.0084 | 0.979 (0.802, 1.175) | pass |
| (0.8, 0.9] | 47 | 23 | 0.0894 | 0.0722 | 0.0851 | 1.179 (nan, nan) | - |

## Test [2024, 2025]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 5.4e-03; the copula moves single legs by up to 1.5e-03. Single-leg log loss with the mix shift 0.35035 vs v1 0.35038.

### Pairs, opponents: 28393 in 544 games; both scored 0.0601

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0559 | 0.21348 |  |  |
| joint | 0.0550 | 0.21357 | +0.00009 (+0.00001, +0.00017) worse |  |
| joint + mix shift | 0.0550 | 0.21348 | +0.00000 (-0.00013, +0.00014) not established | -0.00005 (-0.00014, +0.00003) not established |
| joint + mix shift + copula | 0.0573 | 0.21331 | -0.00016 (-0.00036, +0.00005) not established |  |
| joint + copula | 0.0572 | 0.21341 | -0.00007 (-0.00020, +0.00006) not established |  |

cross-team pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.9, 0.97] | 957 | 235 | 0.0929 | 0.0889 | 0.1024 | 1.151 (nan, nan) | - |
| (0.97, 1.03] | 11141 | 540 | 0.0668 | 0.0670 | 0.0658 | 0.982 (0.896, 1.069) | pass |
| (1.03, 1.1] | 16276 | 544 | 0.0462 | 0.0488 | 0.0537 | 1.100 (0.985, 1.206) | FAIL |
| (1.1, 1.2] | 19 | 13 | 0.0281 | 0.0311 | 0.0526 | 1.694 (nan, nan) | - |

### Pairs, teammates: 25834 in 544 games; both scored 0.0526

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0553 | 0.19207 |  |  |
| joint | 0.0502 | 0.19204 | -0.00003 (-0.00048, +0.00042) not established |  |
| joint + mix shift | 0.0501 | 0.19201 | -0.00006 (-0.00051, +0.00040) not established | +0.00001 (-0.00035, +0.00038) not established |
| joint + mix shift + copula | 0.0502 | 0.19201 | -0.00006 (-0.00051, +0.00038) not established |  |
| joint + copula | 0.0502 | 0.19204 | -0.00003 (-0.00048, +0.00042) not established |  |

teammate pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.8, 0.9] | 12010 | 543 | 0.0391 | 0.0347 | 0.0338 | 0.973 (0.844, 1.107) | pass |
| (0.9, 0.97] | 13808 | 544 | 0.0694 | 0.0636 | 0.0689 | 1.084 (0.991, 1.166) | FAIL |
| (0.97, 1.03] | 16 | 14 | 0.0624 | 0.0609 | 0.0625 | 1.027 (nan, nan) | - |

### Three legs, mixed: 184335 in 544 games; all scored 0.0132

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01286 | 0.06589 |  |
| joint | 0.01157 | 0.06599 | +0.00010 (-0.00008, +0.00029) not established |
| joint + mix shift | 0.01160 | 0.06595 | +0.00007 (-0.00011, +0.00025) not established |
| joint + mix shift + copula | 0.01254 | 0.06587 | -0.00002 (-0.00009, +0.00006) not established |
| joint + copula | 0.01249 | 0.06590 | +0.00002 (-0.00004, +0.00008) not established |

mixed 3-leg, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 2 | 2 | 0.0066 | 0.0052 | 0.0000 | 0.000 (nan, nan) | - |
| (0.8, 0.9] | 8364 | 436 | 0.0168 | 0.0148 | 0.0152 | 1.026 (0.722, 1.355) | pass |
| (0.9, 0.97] | 62536 | 543 | 0.0152 | 0.0142 | 0.0141 | 0.994 (0.852, 1.145) | pass |
| (0.97, 1.03] | 77883 | 544 | 0.0119 | 0.0120 | 0.0132 | 1.102 (0.941, 1.263) | FAIL |
| (1.03, 1.1] | 35524 | 544 | 0.0099 | 0.0103 | 0.0112 | 1.088 (0.866, 1.337) | FAIL |
| (1.1, 1.2] | 26 | 16 | 0.0075 | 0.0083 | 0.0000 | 0.000 (nan, nan) | - |

### Three legs, teammates: 50528 in 544 games; all scored 0.0096

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01251 | 0.05102 |  |
| joint | 0.00944 | 0.05064 | -0.00039 (-0.00081, +0.00005) not established |
| joint + mix shift | 0.00942 | 0.05063 | -0.00039 (-0.00083, +0.00005) not established |
| joint + mix shift + copula | 0.00944 | 0.05063 | -0.00039 (-0.00082, +0.00005) not established |
| joint + copula | 0.00944 | 0.05064 | -0.00039 (-0.00081, +0.00005) not established |

three teammates, tune-chosen model (joint), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 50410 | 544 | 0.0123 | 0.0093 | 0.0093 | 1.005 (0.833, 1.156) | pass |
| (0.8, 0.9] | 118 | 55 | 0.0899 | 0.0726 | 0.1356 | 1.866 (nan, nan) | - |

## Also [2018, 2019]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 6.2e-03; the copula moves single legs by up to 1.4e-03. Single-leg log loss with the mix shift 0.34271 vs v1 0.34276.

### Pairs, opponents: 28493 in 512 games; both scored 0.0526

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0534 | 0.19584 |  |  |
| joint | 0.0525 | 0.19584 | +0.00000 (-0.00008, +0.00009) not established |  |
| joint + mix shift | 0.0525 | 0.19579 | -0.00005 (-0.00017, +0.00008) not established | -0.00004 (-0.00012, +0.00004) not established |
| joint + mix shift + copula | 0.0546 | 0.19585 | +0.00001 (-0.00018, +0.00019) not established |  |
| joint + copula | 0.0546 | 0.19590 | +0.00006 (-0.00004, +0.00016) not established |  |

cross-team pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.8, 0.9] | 1 | 1 | 0.0283 | 0.0254 | 0.0000 | 0.000 (nan, nan) | - |
| (0.9, 0.97] | 1274 | 242 | 0.0822 | 0.0786 | 0.0777 | 0.989 (0.784, 1.233) | pass |
| (0.97, 1.03] | 11570 | 510 | 0.0612 | 0.0614 | 0.0590 | 0.962 (0.873, 1.057) | pass |
| (1.03, 1.1] | 15638 | 512 | 0.0452 | 0.0477 | 0.0457 | 0.958 (0.857, 1.069) | pass |
| (1.1, 1.2] | 10 | 4 | 0.0388 | 0.0428 | 0.2000 | 4.668 (nan, nan) | - |

### Pairs, teammates: 26135 in 512 games; both scored 0.0476

| model | mean P(both) | log loss | vs leg product (95% CI) | dependence alone: vs its own marginals |
|---|---|---|---|---|
| leg by leg (v1 product) | 0.0537 | 0.18257 |  |  |
| joint | 0.0486 | 0.18220 | -0.00037 (-0.00077, +0.00006) not established |  |
| joint + mix shift | 0.0486 | 0.18220 | -0.00037 (-0.00078, +0.00006) not established | -0.00025 (-0.00059, +0.00010) not established |
| joint + mix shift + copula | 0.0486 | 0.18218 | -0.00039 (-0.00079, +0.00003) not established |  |
| joint + copula | 0.0486 | 0.18220 | -0.00037 (-0.00077, +0.00006) not established |  |

teammate pair, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.8, 0.9] | 13322 | 512 | 0.0401 | 0.0356 | 0.0362 | 1.015 (0.903, 1.135) | pass |
| (0.9, 0.97] | 12806 | 512 | 0.0679 | 0.0621 | 0.0595 | 0.958 (0.867, 1.056) | pass |
| (0.97, 1.03] | 7 | 6 | 0.0613 | 0.0597 | 0.1429 | 2.393 (nan, nan) | - |

### Three legs, mixed: 193256 in 512 games; all scored 0.0109

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01211 | 0.05736 |  |
| joint | 0.01087 | 0.05730 | -0.00006 (-0.00022, +0.00015) not established |
| joint + mix shift | 0.01090 | 0.05724 | -0.00011 (-0.00026, +0.00006) not established |
| joint + mix shift + copula | 0.01175 | 0.05729 | -0.00007 (-0.00012, -0.00001) better |
| joint + copula | 0.01171 | 0.05735 | -0.00001 (-0.00007, +0.00007) not established |

mixed 3-leg, tune-chosen model (joint + mix shift + copula), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 13 | 4 | 0.0106 | 0.0084 | 0.0000 | 0.000 (nan, nan) | - |
| (0.8, 0.9] | 11486 | 405 | 0.0149 | 0.0131 | 0.0124 | 0.951 (0.731, 1.220) | pass |
| (0.9, 0.97] | 70222 | 512 | 0.0136 | 0.0127 | 0.0113 | 0.890 (0.761, 1.033) | FAIL |
| (0.97, 1.03] | 85400 | 512 | 0.0113 | 0.0113 | 0.0107 | 0.948 (0.791, 1.113) | FAIL |
| (1.03, 1.1] | 26130 | 512 | 0.0096 | 0.0100 | 0.0096 | 0.964 (0.730, 1.273) | pass |
| (1.1, 1.2] | 5 | 4 | 0.0086 | 0.0095 | 0.2000 | 21.077 (nan, nan) | - |

### Three legs, teammates: 53736 in 512 games; all scored 0.0084

| model | mean P(all) | log loss | vs leg product (95% CI) |
|---|---|---|---|
| leg by leg (v1 product) | 0.01219 | 0.04684 |  |
| joint | 0.00917 | 0.04621 | -0.00063 (-0.00101, -0.00022) better |
| joint + mix shift | 0.00915 | 0.04620 | -0.00063 (-0.00102, -0.00022) better |
| joint + mix shift + copula | 0.00917 | 0.04619 | -0.00065 (-0.00102, -0.00024) better |
| joint + copula | 0.00917 | 0.04621 | -0.00063 (-0.00101, -0.00022) better |

three teammates, tune-chosen model (joint), descriptive -- by the model's lift over the leg product:

| lift | n | games | mean leg product | mean model | actual | actual / model (95% CI, game-clustered) | gate |
|---|---|---|---|---|---|---|---|
| (0.0, 0.8] | 53636 | 512 | 0.0121 | 0.0091 | 0.0084 | 0.921 (0.787, 1.074) | FAIL |
| (0.8, 0.9] | 100 | 37 | 0.0807 | 0.0652 | 0.0500 | 0.766 (nan, nan) | - |

## Shadow model per class, chosen on tune by pooled log loss

| class | joint | joint + mix shift | joint + mix shift + copula | joint + copula | chosen |
|---|---|---|---|---|---|
| cross-team pair | 0.19575 | 0.19566 | 0.19559 | 0.19569 | joint + mix shift + copula |
| mixed 3-leg | 0.05799 | 0.05795 | 0.05792 | 0.05795 | joint + mix shift + copula |
| teammate pair | 0.17344 | 0.17344 | 0.17343 | 0.17344 | joint + mix shift + copula |
| three teammates | 0.04524 | 0.04525 | 0.04525 | 0.04524 | joint |

## THE PARLAY GATE (computed by this script; DECISIONS #89)

(a') per era, the 0.45-0.6 single-leg bin: the 95% interval of actual minus predicted contains 0.

| era | rows | predicted | actual | gap (95% CI) | (a') |
|---|---|---|---|---|---|
| test | 503 | 0.504 | 0.529 | +0.024 (-0.019, +0.065) | pass |
| also | 319 | 0.504 | 0.517 | +0.013 (-0.044, +0.068) | pass |

(b') per class, pooled over the gate eras: OPEN if |ratio - 1| <= 5% and the 95% interval half-width < 10%; UNRESOLVED if the ratio is within 5% but the interval is wider; FAIL otherwise. Classes open individually, and only if (a') passes.

| class | model | combinations | games | pooled ratio (95% CI) | half-width | per era | status |
|---|---|---|---|---|---|---|---|
| cross-team pair | joint + mix shift + copula | 56886 | 1056 | 1.007 (0.955, 1.060) | 0.052 | test 1.049; also 0.963 | **OPEN** |
| mixed 3-leg | joint + mix shift + copula | 377591 | 1056 | 0.991 (0.902, 1.085) | 0.092 | test 1.054; also 0.927 | **OPEN** |
| teammate pair | joint + mix shift + copula | 51969 | 1056 | 1.014 (0.959, 1.074) | 0.057 | test 1.048; also 0.980 | **OPEN** |
| three teammates | joint | 104264 | 1056 | 0.969 (0.861, 1.084) | 0.112 | test 1.021; also 0.919 | **UNRESOLVED** |

Open classes: **cross-team pair, mixed 3-leg, teammate pair**.


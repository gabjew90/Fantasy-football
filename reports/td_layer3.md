# Layer 3: who scores together

Tune [2022, 2023], test [2024, 2025]. Pairs of players priced 10%+ by anytime_td_v1 (slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf) before kickoff; outcome = both scored. The joint model is exact (td_joint.py): teammates share their team's touchdown count; the teams are independent unless linked by the mix shift.

## Channel-mix multipliers by the opponent's offensive TDs (estimated on tune)

| opponent TDs | qb_rush | rush_in5 | rush_far | pass_rz | pass_far |
|---|---|---|---|---|---|
| 0 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| 1 | 1.06 | 1.01 | 1.17 | 0.91 | 1.08 |
| 2 | 0.97 | 1.16 | 0.98 | 0.97 | 0.94 |
| 3 | 1.13 | 0.89 | 0.86 | 1.06 | 0.99 |
| 4+ | 0.89 | 0.80 | 0.99 | 1.10 | 1.02 |

## Are the two teams' touchdown counts correlated beyond their implied totals?

| seasons | games | residual correlation (95% CI) |
|---|---|---|
| tune | 543 | +0.208 (+0.133, +0.287) |
| test | 544 | +0.145 (+0.056, +0.228) |

## The copula loading r, tuned on the likelihood of the actual score pairs

| r | latent correlation r^2 | tune: mean log P(pair) | test: mean log P(pair) |
|---|---|---|---|
| 0 | 0.00 | -3.2801 | -3.3056 |
| 0.2 | 0.04 | -3.2732 | -3.3014 |
| 0.3 | 0.09 | -3.2663 | -3.2978 |
| 0.4 | 0.16 | -3.2598 | -3.2960 |
| 0.5 | 0.25 | -3.2574 **chosen** | -3.2998 |
| 0.6 | 0.36 | -3.2658 | -3.3164 |

## Tune [2022, 2023]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.4e-15; the copula moves no single-leg price by more than 2.9e-03. With the mix shift, single-leg log loss 0.35309 vs v1 0.35322 on 15040 player-games.

### Opponents: 27783 pairs in 543 games; both scored 0.0542

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0551 | 0.20084 | 0.05020 |  |
| joint | 0.0551 | 0.20084 | 0.05020 | +0.00000 (-0.00000, +0.00000) not established |
| joint + mix shift | 0.0551 | 0.20060 | 0.05016 | -0.00024 (-0.00039, -0.00010) better |
| joint + mix shift + correlated counts | 0.0584 | 0.20073 | 0.05020 | -0.00011 (-0.00045, +0.00022) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.8, 0.9] | 1 | 0.0537 | 0.0481 | 0.0000 |
| (0.9, 0.97] | 328 | 0.0972 | 0.0929 | 0.0701 |
| (0.97, 1.03] | 4909 | 0.0825 | 0.0831 | 0.0689 |
| (1.03, 1.1] | 12653 | 0.0576 | 0.0613 | 0.0568 |
| (1.1, 1.2] | 9892 | 0.0370 | 0.0412 | 0.0432 |

### Teammates: 25020 pairs in 543 games; both scored 0.0467

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0551 | 0.17712 | 0.04325 |  |
| joint | 0.0512 | 0.17660 | 0.04319 | -0.00052 (-0.00084, -0.00019) better |
| joint + mix shift | 0.0511 | 0.17658 | 0.04319 | -0.00054 (-0.00088, -0.00020) better |
| joint + mix shift + correlated counts | 0.0512 | 0.17656 | 0.04319 | -0.00056 (-0.00089, -0.00022) better |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.0, 0.8] | 1 | 0.0351 | 0.0279 | 0.0000 |
| (0.8, 0.9] | 1950 | 0.0411 | 0.0364 | 0.0303 |
| (0.9, 0.97] | 22252 | 0.0568 | 0.0529 | 0.0486 |
| (0.97, 1.03] | 817 | 0.0418 | 0.0410 | 0.0330 |

## Test [2024, 2025]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.6e-15; the copula moves no single-leg price by more than 2.6e-03. With the mix shift, single-leg log loss 0.35816 vs v1 0.35828 on 15022 player-games.

### Opponents: 26550 pairs in 544 games; both scored 0.0626

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0608 | 0.22159 | 0.05694 |  |
| joint | 0.0608 | 0.22159 | 0.05694 | -0.00000 (-0.00000, +0.00000) not established |
| joint + mix shift | 0.0609 | 0.22135 | 0.05690 | -0.00025 (-0.00041, -0.00009) better |
| joint + mix shift + correlated counts | 0.0642 | 0.22133 | 0.05691 | -0.00026 (-0.00062, +0.00012) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.9, 0.97] | 391 | 0.1136 | 0.1088 | 0.0997 |
| (0.97, 1.03] | 5161 | 0.0894 | 0.0900 | 0.0789 |
| (1.03, 1.1] | 11503 | 0.0631 | 0.0671 | 0.0661 |
| (1.1, 1.2] | 9495 | 0.0404 | 0.0450 | 0.0480 |

### Teammates: 24162 pairs in 544 games; both scored 0.0543

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0594 | 0.19742 | 0.04956 |  |
| joint | 0.0553 | 0.19718 | 0.04953 | -0.00025 (-0.00060, +0.00011) not established |
| joint + mix shift | 0.0552 | 0.19713 | 0.04952 | -0.00029 (-0.00065, +0.00007) not established |
| joint + mix shift + correlated counts | 0.0553 | 0.19710 | 0.04952 | -0.00032 (-0.00067, +0.00003) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.0, 0.8] | 1 | 0.0419 | 0.0335 | 0.0000 |
| (0.8, 0.9] | 1986 | 0.0431 | 0.0381 | 0.0337 |
| (0.9, 0.97] | 21110 | 0.0615 | 0.0573 | 0.0563 |
| (0.97, 1.03] | 1063 | 0.0493 | 0.0483 | 0.0517 |
| (1.03, 1.1] | 2 | 0.0226 | 0.0234 | 0.0000 |


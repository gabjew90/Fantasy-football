# Layer 3: who scores together

Tune [2022, 2023], test [2024, 2025]. Pairs of players priced 10%+ by anytime_td_v1 (slot|x0.4|m0.25|qs0.92|cap0.99|qb40|cinf) before kickoff; outcome = both scored. The joint model is exact (td_joint.py): teammates share their team's touchdown count; the teams are independent unless linked by the mix shift.

## Channel-mix multipliers by the opponent's offensive TDs (estimated on tune)

| opponent TDs | qb_rush | rush_in5 | rush_far | pass_rz | pass_far |
|---|---|---|---|---|---|
| 0 (166 TDs) | 0.93 | 1.10 | 1.04 | 0.96 | 1.00 |
| 1 (482 TDs) | 1.04 | 1.00 | 1.12 | 0.93 | 1.05 |
| 2 (754 TDs) | 0.98 | 1.13 | 0.98 | 0.97 | 0.95 |
| 3 (556 TDs) | 1.09 | 0.92 | 0.90 | 1.05 | 0.99 |
| 4+ (503 TDs) | 0.92 | 0.86 | 0.99 | 1.07 | 1.02 |

Each bucket's raw multipliers are shrunk toward 1 by 200 touchdowns.


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

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.4e-15; the copula moves no single-leg price by more than 2.2e-03. With the mix shift, single-leg log loss 0.35317 vs v1 0.35322 on 15040 player-games.

### Opponents: 27783 pairs in 543 games; both scored 0.0542

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0551 | 0.20084 | 0.05020 |  |
| joint | 0.0551 | 0.20084 | 0.05020 | +0.00000 (-0.00000, +0.00000) not established |
| joint + mix shift | 0.0551 | 0.20067 | 0.05017 | -0.00017 (-0.00028, -0.00008) better |
| joint + mix shift + correlated counts | 0.0584 | 0.20081 | 0.05021 | -0.00003 (-0.00034, +0.00026) not established |

Dependence alone, against the product of each model's own marginals:

| model | vs its own marginals' product (95% CI) |
|---|---|
| joint + mix shift | -0.00012 (-0.00020, -0.00005) better |
| joint + mix shift + correlated counts | +0.00004 (-0.00024, +0.00032) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.9, 0.97] | 48 | 0.0973 | 0.0936 | 0.1042 |
| (0.97, 1.03] | 3591 | 0.0901 | 0.0912 | 0.0752 |
| (1.03, 1.1] | 19154 | 0.0557 | 0.0594 | 0.0565 |
| (1.1, 1.2] | 4990 | 0.0276 | 0.0305 | 0.0301 |

### Teammates: 25020 pairs in 543 games; both scored 0.0467

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0551 | 0.17712 | 0.04325 |  |
| joint | 0.0512 | 0.17660 | 0.04319 | -0.00052 (-0.00084, -0.00019) better |
| joint + mix shift | 0.0511 | 0.17661 | 0.04320 | -0.00051 (-0.00084, -0.00016) better |
| joint + mix shift + correlated counts | 0.0512 | 0.17659 | 0.04319 | -0.00053 (-0.00085, -0.00019) better |

Dependence alone, against the product of each model's own marginals:

| model | vs its own marginals' product (95% CI) |
|---|---|
| joint + mix shift | -0.00052 (-0.00084, -0.00019) better |
| joint + mix shift + correlated counts | -0.00053 (-0.00085, -0.00020) better |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.8, 0.9] | 1405 | 0.0363 | 0.0323 | 0.0292 |
| (0.9, 0.97] | 23430 | 0.0563 | 0.0523 | 0.0478 |
| (0.97, 1.03] | 185 | 0.0512 | 0.0500 | 0.0324 |

## Test [2024, 2025]

Consistency: the joint model's single-leg prices (no shift) equal anytime_td_v1's to 2.6e-15; the copula moves no single-leg price by more than 2.1e-03. With the mix shift, single-leg log loss 0.35821 vs v1 0.35828 on 15022 player-games.

### Opponents: 26550 pairs in 544 games; both scored 0.0626

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0608 | 0.22159 | 0.05694 |  |
| joint | 0.0608 | 0.22159 | 0.05694 | -0.00000 (-0.00000, +0.00000) not established |
| joint + mix shift | 0.0609 | 0.22142 | 0.05691 | -0.00018 (-0.00029, -0.00007) better |
| joint + mix shift + correlated counts | 0.0642 | 0.22140 | 0.05692 | -0.00019 (-0.00052, +0.00016) not established |

Dependence alone, against the product of each model's own marginals:

| model | vs its own marginals' product (95% CI) |
|---|---|
| joint + mix shift | -0.00012 (-0.00020, -0.00004) better |
| joint + mix shift + correlated counts | -0.00011 (-0.00043, +0.00023) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.9, 0.97] | 32 | 0.1312 | 0.1266 | 0.2188 |
| (0.97, 1.03] | 3964 | 0.0989 | 0.1001 | 0.0878 |
| (1.03, 1.1] | 18306 | 0.0600 | 0.0639 | 0.0637 |
| (1.1, 1.2] | 4248 | 0.0285 | 0.0315 | 0.0332 |

### Teammates: 24162 pairs in 544 games; both scored 0.0543

| model | mean P(both) | log loss | Brier | vs independent (95% CI, game-clustered) |
|---|---|---|---|---|
| independent (leg by leg) | 0.0594 | 0.19742 | 0.04956 |  |
| joint | 0.0553 | 0.19718 | 0.04953 | -0.00025 (-0.00060, +0.00011) not established |
| joint + mix shift | 0.0552 | 0.19715 | 0.04953 | -0.00027 (-0.00063, +0.00010) not established |
| joint + mix shift + correlated counts | 0.0553 | 0.19713 | 0.04952 | -0.00030 (-0.00065, +0.00006) not established |

Dependence alone, against the product of each model's own marginals:

| model | vs its own marginals' product (95% CI) |
|---|---|
| joint + mix shift | -0.00025 (-0.00060, +0.00011) not established |
| joint + mix shift + correlated counts | -0.00026 (-0.00062, +0.00009) not established |

Binned by the full model's lift over the product: does reality move with it?

| lift | pairs | mean independent | mean full model | actual both |
|---|---|---|---|---|
| (0.8, 0.9] | 1360 | 0.0378 | 0.0337 | 0.0287 |
| (0.9, 0.97] | 22643 | 0.0606 | 0.0565 | 0.0556 |
| (0.97, 1.03] | 159 | 0.0743 | 0.0725 | 0.0755 |


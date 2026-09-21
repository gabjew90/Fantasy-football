# Layer 1: team touchdown distributions

Tune seasons [2022, 2023], test seasons [2024, 2025] (never used for any choice). 2718 team-games with closing lines. Walk-forward: every game predicted from the prior season plus the earlier weeks of its own.

Data check: 0 team-games where 6 x TDs exceeds points scored (should be 0).

## Ablation ladder (test seasons)

Each row adds one component to the row above, using the value chosen on the tune seasons.

| step | CRPS | log score | bias | change vs row above (95% CI, game-clustered) |
|---|---|---|---|---|
| Engine today: league ratio, linear, Poisson (league, gamma=0, Poisson) | 0.7404 | 1.7128 | -0.089 | baseline |
| + team-specific ratio (team k=3000, gamma=0, Poisson) | 0.7391 | 1.7116 | -0.088 | -0.0012 (-0.0022, -0.0003) better |
| + fitted shape (team k=3000, gamma=0, Binomial n=11) | 0.7306 | 1.6825 | -0.088 | -0.0085 (-0.0112, -0.0056) better |
| + elasticity to implied total (team k=3000, gamma=0.25, Binomial n=11) | 0.7247 | 1.6761 | -0.068 | -0.0059 (-0.0097, -0.0023) better |

## Mean calibration by predicted-mean quintile (test)

| quintile | engine today: predicted | chosen: predicted | actual | actual variance | chosen shape's variance |
|---|---|---|---|---|---|
| 1 | 1.89 | 1.77 | 1.85 | 1.47 | 1.48 |
| 2 | 2.24 | 2.19 | 2.16 | 1.56 | 1.75 |
| 3 | 2.48 | 2.49 | 2.58 | 1.95 | 1.93 |
| 4 | 2.71 | 2.78 | 2.76 | 1.78 | 2.08 |
| 5 | 3.02 | 3.22 | 3.44 | 2.13 | 2.28 |

Actual variance is within-quintile, so it also contains the spread of means inside each quintile. That can only INFLATE it, which makes any shortfall against the Poisson variance conservative.

League TDs per point, test seasons: **0.1114** all touchdowns, **0.1057** offensive only. The engine's constant (0.1055) is the offensive figure, so it agrees.

## Full grid, top 12 by tune CRPS

| mean | gamma | shape | tune CRPS | test CRPS | test log score |
|---|---|---|---|---|---|
| team k=3000 | 0.25 | Binomial n=11 | 0.7203 | 0.7247 | 1.6761 | **chosen**
| league | 0.25 | Binomial n=11 | 0.7204 | 0.7256 | 1.6772 |
| team k=1000 | 0 | Binomial n=11 | 0.7204 | 0.7295 | 1.6812 |
| team k=300 | 0 | Binomial n=11 | 0.7205 | 0.7290 | 1.6804 |
| team k=1000 | 0.25 | Binomial n=11 | 0.7205 | 0.7242 | 1.6754 |
| team k=3000 | 0 | Binomial n=11 | 0.7208 | 0.7306 | 1.6825 |
| team k=100 | 0 | Binomial n=11 | 0.7211 | 0.7294 | 1.6807 |
| league | 0 | Binomial n=11 | 0.7214 | 0.7320 | 1.6841 |
| team k=300 | 0.25 | Binomial n=11 | 0.7215 | 0.7244 | 1.6756 |
| team k=100 | 0.25 | Binomial n=11 | 0.7228 | 0.7253 | 1.6764 |
| league | 0.5 | Binomial n=11 | 0.7236 | 0.7239 | 1.6757 |
| team k=3000 | 0.5 | Binomial n=11 | 0.7240 | 0.7235 | 1.6752 |

## Channel mix

Log loss of each touchdown's actual channel under the predicted mix (lower is better).

| mix | tune log loss | test log loss | TDs (tune) |
|---|---|---|---|
| league mix | 1.5906 | 1.5677 | 2617 |
| team, alpha=5 TDs | 1.6029 | 1.5814 | 2617 |
| team, alpha=20 TDs | 1.5881 | 1.5660 | 2617 |
| team, alpha=50 TDs | 1.5802 | 1.5580 | 2617 |
| team, alpha=100 TDs | 1.5785 | 1.5561 | 2617 | **chosen**
| team, alpha=200 TDs | 1.5803 | 1.5578 | 2617 |
| team, alpha=500 TDs | 1.5845 | 1.5617 | 2617 |
| team, alpha=1000 TDs | 1.5870 | 1.5642 | 2617 |

League channel mix, all seasons in the run:

| channel | share |
|---|---|
| qb_rush | 7.6% |
| rush_in5 | 17.7% |
| rush_far | 11.1% |
| pass_rz | 41.3% |
| pass_far | 16.8% |
| dst_other | 5.5% |

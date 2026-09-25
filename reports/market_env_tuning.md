# The Vegas-line environment (market_fit): tune seasons only

*Plan step 5 (docs/plans/2026-09-24-yardage-harness.md), 2026-09-25. Runs:
`backtest.py --seasons 2022,2023 --env market_fit --pace-weight W` for W in
0.25, 0.5, 0.75, 1.0, each paired player-week by player-week against the live
harness run (props-v1.24, `--env history`, the environment the scorer uses).
This run read the tune seasons only; nothing was chosen, so the test seasons
(2024-25) were not read.*

**What `market_fit` does.** Each team's plays and pass rate come from a blend
of its own history (the live environment) and a regression of plays and pass
rate on the team's own spread and the game total, fitted on the season
before (`market_env_fit` in the priors; plays R^2 ~0.02, pass rate ~0.04).
`W` is the weight on the market's prediction. Targets and carries follow;
every player's share, rate and the width settings are unchanged. The
harness uses nflverse's closing line; the scorer would use the line at the
time it runs.

**The rule, fixed before the 0.75 and 1.0 runs finished:** CRPS summed over
the five markets, each relative to the live model's; among weights not
measurably worse than the best, the smallest -- the live model counts as
weight 0. Computed by `props/tools/pick_market_env.py` from the runs'
`--save-results` pickles.

"Not measurably worse" two ways, 95% intervals resampling whole games. The
first run of the rule used only the second (the code review found it
weights a player-row by how many markets it is graded in, so the receiving
markets, about 7 rows in 8, dominate it); the first is the score itself, each
market weighing the same. They agree.

| W | Score (live = 5) | Score vs the best (markets equal) | Per-row composite vs the best | Not measurably worse |
|---|---|---|---|---|
| 0 (live) | 5.0000 | +0.0154 (-0.0020, +0.0322) | +0.0047 (-0.0008, +0.0101) | yes, both -- **chosen** |
| 0.25 | 4.9856 | +0.0010 (-0.0080, +0.0095) | +0.0002 (-0.0027, +0.0030) | yes, both |
| 0.5 | 4.9846 | best | best | -- |
| 0.75 | 4.9942 | +0.0096 (+0.0002, +0.0188) | +0.0037 (+0.0007, +0.0067) | no |
| 1.0 | 5.0197 | +0.0351 (+0.0177, +0.0530) | +0.0121 (+0.0066, +0.0179) | no |

**Result: the live environment stays.** The best weight is not measurably
better than no market at all, on either reading.

Per market, CRPS gain over live (positive = better), 95% interval resampling
whole games, 2022-23:

| W | Receptions | Receiving yards | Rushing yards | QB rushing yards | QB passing yards |
|---|---|---|---|---|---|
| 0.25 | +0.0018 (+0.0002, +0.0034) | +0.0171 (-0.0011, +0.0350) | +0.0600 (+0.0140, +0.1075) | -0.0284 (-0.0712, +0.0110) | +0.5384 (+0.2962, +0.7936) |
| 0.5 | +0.0007 (-0.0021, +0.0037) | +0.0334 (+0.0043, +0.0631) | +0.0483 (-0.0288, +0.1303) | -0.0517 (-0.1185, +0.0103) | +0.7445 (+0.2836, +1.2211) |
| 0.75 | -0.0015 (-0.0057, +0.0027) | +0.0187 (-0.0250, +0.0622) | +0.0406 (-0.0694, +0.1568) | -0.0868 (-0.1846, +0.0049) | +0.6518 (-0.0371, +1.3598) |
| 1.0 | -0.0060 (-0.0116, -0.0006) | -0.0093 (-0.0666, +0.0480) | -0.0100 (-0.1514, +0.1382) | -0.1588 (-0.2932, -0.0367) | +0.2644 (-0.6427, +1.1786) |

As a share of live CRPS at W = 0.5 (negative = better): receptions -0.07%,
receiving yards -0.25%, rushing yards -0.30%, QB rushing +0.59% (worse), QB
passing -1.52%.

**The lead, not acted on.** QB passing is the one market with a clear gain
(1.1-1.5% at W 0.25-0.5, intervals excluding 0); QB rushing moves the other
way, and together they cancel inside the noise. A pass-volume-only market
environment is a new design: it would be chosen on these tune seasons and
read once on 2024-25, like any other.

Known documentation error found on the way: `model.market_environment_fitted`'s
docstring says the team spread is "negative = favored"; `build_priors.py`
fits it and `backtest.py` passes it POSITIVE = favoured, consistently. Left
for the next engine change, so a docstring alone does not cut an engine
version.

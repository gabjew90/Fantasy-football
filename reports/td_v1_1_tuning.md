# anytime_td_v1.1: the share cap and the starter's QB-rush rate

Tune [2022, 2023], test [2024, 2025]. Everything else is anytime_td_v1 as shipped in props-v1.4 (slot x0.4, moved 0.25, fixed share, Binomial(10), gamma 0.25). Two settings, chosen together on tune log loss given the team's offensive touchdowns:

- **cap**: total share per channel after reallocation; the remainder is 'other'. v1 used 0.99; actives score 0.997 of offensive touchdowns.
- **QB rate**: the qb_rush weight in the channel mix. 'team mix' is v1 (the team's history); a number is the starter's QB-rush touchdowns over his teams' offensive touchdowns in his starts over the last 3 seasons, shrunk toward the league fraction by that many team touchdowns.

## Tune log loss, given offensive touchdowns

| cap | team mix | 10 | 20 | 40 | 80 |
|---|---|---|---|---|---|
| 0.99 | 0.32645 | 0.32634 | 0.32609 | **0.32604** | 0.32620 |
| 0.993 | 0.32646 | 0.32635 | 0.32611 | 0.32605 | 0.32621 |
| 0.995 | 0.32647 | 0.32636 | 0.32612 | 0.32606 | 0.32622 |
| 0.997 | 0.32649 | 0.32638 | 0.32613 | 0.32607 | 0.32623 |
| 0.999 | 0.32650 | 0.32639 | 0.32614 | 0.32608 | 0.32624 |

Chosen: **cap 0.99, QB rate 40**.

Starting quarterbacks only, tune log loss given offensive touchdowns:

| cap | team mix | 10 | 20 | 40 | 80 |
|---|---|---|---|---|---|
| 0.99 | 0.3790 | 0.3722 | 0.3707 | 0.3715 | 0.3747 |
| 0.993 | 0.3789 | 0.3721 | 0.3706 | 0.3713 | 0.3746 |
| 0.995 | 0.3788 | 0.3720 | 0.3705 | 0.3713 | 0.3745 |
| 0.997 | 0.3787 | 0.3719 | 0.3704 | 0.3712 | 0.3744 |
| 0.999 | 0.3786 | 0.3718 | 0.3704 | 0.3711 | 0.3744 |

## Test

15022 player-games, 0.148 scored.

| model | given offensive TDs | vs v1 | end to end | vs v1 | mean predicted, end to end |
|---|---|---|---|---|---|
| v1 (props-v1.4) | 0.3318 | | 0.3575 | | 0.145 |
| QB rate 40 only | 0.3308 | -0.0010 (-0.0016, -0.0003) better | 0.3566 | -0.0009 (-0.0016, -0.0003) better | 0.145 |
| chosen, both | 0.3308 | -0.0010 (-0.0016, -0.0003) better | 0.3566 | -0.0009 (-0.0016, -0.0003) better | 0.145 |

Summed share of actives per team-game: v1 0.990, chosen 0.990; actives actually scored 0.997 of offensive touchdowns.

### Calibration, end to end (binned by the chosen model)

| predicted P(score) | v1: predicted | chosen: predicted | actual rate | n |
|---|---|---|---|---|
| (-0.001, 0.05] | 0.025 | 0.023 | 0.031 | 4354 |
| (0.05, 0.1] | 0.078 | 0.074 | 0.073 | 2939 |
| (0.1, 0.2] | 0.143 | 0.144 | 0.147 | 3314 |
| (0.2, 0.3] | 0.244 | 0.246 | 0.247 | 2109 |
| (0.3, 0.45] | 0.358 | 0.362 | 0.368 | 1357 |
| (0.45, 0.6] | 0.511 | 0.515 | 0.492 | 602 |
| (0.6, 1.0] | 0.631 | 0.637 | 0.644 | 90 |

### Starting quarterbacks (test)

| population | n | actual rate | engine: predicted / log loss | v1: predicted / log loss | chosen: predicted / log loss |
|---|---|---|---|---|---|
| all starting QBs | 1088 | 0.148 | 0.096 / 0.4074 | 0.130 / 0.4000 | 0.123 / 0.3860 |
| QB new to his team as a starter | 67 | 0.104 | 0.041 / 0.3149 | 0.068 / 0.3480 | 0.068 / 0.3308 |

starting QBs, chosen vs v1 end to end: -0.0141 (-0.0214, -0.0064) better.

QBs new to their team as starter, chosen vs v1 end to end: -0.0171 (-0.0616, +0.0133) not established.

| position | v1 | chosen | n |
|---|---|---|---|
| QB | 0.2515 | 0.2464 | 2211 |
| RB | 0.4106 | 0.4104 | 3713 |
| TE | 0.3070 | 0.3073 | 3446 |
| WR | 0.3948 | 0.3943 | 5652 |

# anytime_td_v1: share by team touchdown count, and the starting-QB level

Model: slot|x0.4|m0.25|cap0.99|qb40|cinf (td_v1.V1 as shipped). Finding on [2022, 2023]; confirmation on [2024, 2025]. Team-games where the team scored at least one offensive touchdown.

## Finding: [2022, 2023]

### [2022, 2023]: realised touchdowns / expected (k x q), by rank of q within the team-game

1.00 means the player's share on a k-touchdown day is what the model assumes. A top-share ratio falling with k, and a backup ratio rising, is the blowout pattern.

| rank | k = 1 | k = 2 | k = 3 | k = 4+ |
|---|---|---|---|---|
| 1 (top q) | 0.86 (0.66-1.06) | 0.87 (0.74-1.00) | 0.93 (0.82-1.06) | 0.93 (0.80-1.06) |
| 2 | 1.04 (0.77-1.34) | 0.95 (0.78-1.12) | 0.91 (0.74-1.07) | 1.05 (0.89-1.21) |
| 3 | 0.83 (0.55-1.14) | 1.00 (0.81-1.23) | 1.05 (0.86-1.24) | 1.14 (0.95-1.33) |
| 4-6 | 1.26 (1.02-1.48) | 0.95 (0.82-1.09) | 1.07 (0.95-1.20) | 1.05 (0.93-1.18) |
| 7+ | 0.96 (0.72-1.19) | 1.32 (1.14-1.49) | 1.08 (0.91-1.24) | 0.95 (0.81-1.09) |

Same cells as realised share of team touchdowns vs mean q (n team-games):

| rank | k = 1 | k = 2 | k = 3 | k = 4+ |
|---|---|---|---|---|
| 1 (top q) | 0.214 vs 0.250 (n 203) | 0.217 vs 0.250 (n 280) | 0.232 vs 0.248 (n 222) | 0.230 vs 0.247 (n 160) |
| 2 | 0.168 vs 0.162 (n 203) | 0.156 vs 0.165 (n 280) | 0.148 vs 0.163 (n 222) | 0.173 vs 0.165 (n 160) |
| 3 | 0.105 vs 0.126 (n 203) | 0.127 vs 0.127 (n 280) | 0.133 vs 0.127 (n 222) | 0.147 vs 0.129 (n 160) |
| 4-6 | 0.105 vs 0.083 (n 203) | 0.079 vs 0.084 (n 280) | 0.090 vs 0.084 (n 222) | 0.087 vs 0.083 (n 160) |
| 7+ | 0.024 vs 0.025 (n 203) | 0.033 vs 0.025 (n 280) | 0.027 vs 0.025 (n 222) | 0.024 vs 0.025 (n 160) |

Mechanism check, top-q player, all k: realised / expected by pre-game spread and by the opponent's points (neither is moved by his own touchdowns).

| state | ratio (95% CI) | team-games |
|---|---|---|
| pre-game underdog by 3+ | 0.90 (0.79-1.01) | 345 |
| pre-game within 3 | 0.93 (0.80-1.06) | 264 |
| pre-game favourite by 3+ | 0.90 (0.80-1.00) | 386 |
| opponent scored 27+ | 0.86 (0.73-0.98) | 319 |
| opponent scored 14-26 | 0.96 (0.86-1.05) | 487 |
| opponent scored 13 or fewer | 0.88 (0.73-1.05) | 189 |

### [2022, 2023]: starting quarterbacks

| | team mix (v1) | starter rate (v1.1) | realised |
|---|---|---|---|
| qb_rush weight: mean, team-games with a TD | 0.0778 | 0.0775 | 0.0845 (QB-rush TDs / offensive TDs) |
| league fraction used as the shrinkage target | 0.0777 | 0.0777 | |
| starter per-TD share q | 0.0548 | 0.0549 | 0.0768 (his TDs / team offensive TDs) |
| starter P(score) given the team's TD count | 0.127 | 0.128 | 0.166 |

Within the channel: starter's implied share of QB-rush TDs (q / weight, capped at 1) 0.712; realised starter TDs / team QB-rush TDs 0.909 (a starter's TDs are almost all QB rushes).

### [2022, 2023]: the starter's share WITHIN the QB-rush channel

Predicted = his qb_rush share after blending and reallocation. Realised = his QB carries over the team's QB carries in that game.

| population | team-games | predicted share | realised carry share |
|---|---|---|---|
| all | 946 | 0.703 | 0.880 |
| weeks 1-4 | 222 | 0.730 | 0.937 |
| weeks 5+ | 724 | 0.695 | 0.862 |
| new to his team as starter | 56 | 0.519 | 0.624 |
| started for this team before | 890 | 0.714 | 0.896 |

### [2022, 2023]: where offensive TDs come from, by game state

The 'final' rows are produced partly BY these touchdowns (goal-line rushing while leading widens the margin), so only the pre-game rows say what a model could know.

| state | team-games | qb_rush | rush_in5 | rush_far | pass_rz | pass_far |
|---|---|---|---|---|---|---|
| final: trailing or tied | 545 | 0.095 | 0.158 | 0.094 | 0.466 | 0.186 |
| final: won by 1-16 | 417 | 0.082 | 0.198 | 0.122 | 0.414 | 0.185 |
| final: won by 17+ | 124 | 0.070 | 0.222 | 0.148 | 0.377 | 0.183 |
| pre-game: favourite by 3+ | 400 | 0.084 | 0.191 | 0.125 | 0.411 | 0.188 |
| pre-game: within 3 | 286 | 0.096 | 0.189 | 0.106 | 0.423 | 0.187 |
| pre-game: underdog by 3+ | 400 | 0.076 | 0.182 | 0.113 | 0.450 | 0.179 |

Sign check on spread: favourites by 3+ average 24.8 implied points vs 18.7 for underdogs by 3+.

## Confirmation: [2024, 2025]

### [2024, 2025]: realised touchdowns / expected (k x q), by rank of q within the team-game

1.00 means the player's share on a k-touchdown day is what the model assumes. A top-share ratio falling with k, and a backup ratio rising, is the blowout pattern.

| rank | k = 1 | k = 2 | k = 3 | k = 4+ |
|---|---|---|---|---|
| 1 (top q) | 1.00 (0.77-1.25) | 0.83 (0.71-0.95) | 0.94 (0.82-1.07) | 0.93 (0.83-1.03) |
| 2 | 0.67 (0.42-0.94) | 1.05 (0.87-1.23) | 0.98 (0.82-1.14) | 0.94 (0.81-1.07) |
| 3 | 0.94 (0.62-1.32) | 1.14 (0.94-1.35) | 1.16 (0.97-1.38) | 1.08 (0.93-1.25) |
| 4-6 | 1.12 (0.87-1.38) | 1.10 (0.97-1.25) | 0.94 (0.79-1.07) | 1.07 (0.96-1.19) |
| 7+ | 1.23 (0.91-1.57) | 0.99 (0.84-1.15) | 1.11 (0.96-1.28) | 1.04 (0.91-1.17) |

Same cells as realised share of team touchdowns vs mean q (n team-games):

| rank | k = 1 | k = 2 | k = 3 | k = 4+ |
|---|---|---|---|---|
| 1 (top q) | 0.262 vs 0.261 (n 176) | 0.218 vs 0.261 (n 279) | 0.242 vs 0.257 (n 211) | 0.246 vs 0.264 (n 204) |
| 2 | 0.113 vs 0.169 (n 176) | 0.175 vs 0.167 (n 279) | 0.168 vs 0.171 (n 211) | 0.157 vs 0.166 (n 204) |
| 3 | 0.123 vs 0.131 (n 176) | 0.149 vs 0.131 (n 279) | 0.155 vs 0.134 (n 211) | 0.142 vs 0.131 (n 204) |
| 4-6 | 0.092 vs 0.082 (n 176) | 0.090 vs 0.082 (n 279) | 0.077 vs 0.082 (n 211) | 0.088 vs 0.082 (n 204) |
| 7+ | 0.029 vs 0.023 (n 176) | 0.024 vs 0.024 (n 279) | 0.026 vs 0.023 (n 211) | 0.024 vs 0.023 (n 204) |

Mechanism check, top-q player, all k: realised / expected by pre-game spread and by the opponent's points (neither is moved by his own touchdowns).

| state | ratio (95% CI) | team-games |
|---|---|---|
| pre-game underdog by 3+ | 0.92 (0.81-1.03) | 363 |
| pre-game within 3 | 0.89 (0.75-1.02) | 245 |
| pre-game favourite by 3+ | 0.93 (0.83-1.03) | 397 |
| opponent scored 27+ | 0.81 (0.71-0.89) | 363 |
| opponent scored 14-26 | 0.97 (0.88-1.07) | 464 |
| opponent scored 13 or fewer | 0.99 (0.84-1.15) | 178 |

### [2024, 2025]: starting quarterbacks

| | team mix (v1) | starter rate (v1.1) | realised |
|---|---|---|---|
| qb_rush weight: mean, team-games with a TD | 0.0844 | 0.0807 | 0.0810 (QB-rush TDs / offensive TDs) |
| league fraction used as the shrinkage target | 0.0843 | 0.0843 | |
| starter per-TD share q | 0.0596 | 0.0569 | 0.0735 (his TDs / team offensive TDs) |
| starter P(score) given the team's TD count | 0.147 | 0.139 | 0.160 |

Within the channel: starter's implied share of QB-rush TDs (q / weight, capped at 1) 0.700; realised starter TDs / team QB-rush TDs 0.907 (a starter's TDs are almost all QB rushes).

### [2024, 2025]: the starter's share WITHIN the QB-rush channel

Predicted = his qb_rush share after blending and reallocation. Realised = his QB carries over the team's QB carries in that game.

| population | team-games | predicted share | realised carry share |
|---|---|---|---|
| all | 962 | 0.690 | 0.878 |
| weeks 1-4 | 228 | 0.680 | 0.941 |
| weeks 5+ | 734 | 0.693 | 0.857 |
| new to his team as starter | 62 | 0.453 | 0.522 |
| started for this team before | 900 | 0.706 | 0.906 |

### [2024, 2025]: where offensive TDs come from, by game state

The 'final' rows are produced partly BY these touchdowns (goal-line rushing while leading widens the margin), so only the pre-game rows say what a model could know.

| state | team-games | qb_rush | rush_in5 | rush_far | pass_rz | pass_far |
|---|---|---|---|---|---|---|
| final: trailing or tied | 545 | 0.080 | 0.176 | 0.090 | 0.472 | 0.182 |
| final: won by 1-16 | 390 | 0.091 | 0.189 | 0.129 | 0.418 | 0.173 |
| final: won by 17+ | 153 | 0.066 | 0.202 | 0.148 | 0.412 | 0.172 |
| pre-game: favourite by 3+ | 412 | 0.071 | 0.199 | 0.127 | 0.445 | 0.159 |
| pre-game: within 3 | 264 | 0.089 | 0.161 | 0.126 | 0.426 | 0.198 |
| pre-game: underdog by 3+ | 412 | 0.090 | 0.190 | 0.100 | 0.434 | 0.186 |

Sign check on spread: favourites by 3+ average 25.4 implied points vs 19.2 for underdogs by 3+.

### League QB-rush fraction of offensive touchdowns, by season

| season | QB-rush TDs | offensive TDs | fraction |
|---|---|---|---|
| 2021 | 94 | 1345 | 0.0699 |
| 2022 | 98 | 1237 | 0.0792 |
| 2023 | 110 | 1224 | 0.0899 |
| 2024 | 107 | 1320 | 0.0811 |
| 2025 | 107 | 1321 | 0.0810 |


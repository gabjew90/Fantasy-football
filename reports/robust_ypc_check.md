# Taking the luck out of yards a play (2026-10-05, rule set before each run)

## Question

The user asked whether removing long plays makes a yards line easier to judge
against the volume a player is expected to get. Which early-season figure best
predicts a player's yards a play for the rest of the season?

## Rule (fixed before running)

From weeks 1-3 of a season, compute each figure; target = his yards a play in
weeks 4-18 (regular season). Players with 20+ early carries and 50+ later carries
(runs, QB kneels out) or 8+ early catches and 20+ later catches. Error = mean absolute
difference, weighted by later volume. Caps are percentiles of all 2022-23 plays, so
2024-25 is out of sample. Winner = lowest 2024-25 error, checked against plain on
2022-23. The 99th-percentile cap was added on the user's request and run under the
same rule.

## Result

| Figure | Runs 2022-23 | Runs 2024-25 | Catches 2022-23 | Catches 2024-25 |
|---|---|---|---|---|
| plain average | 0.882 | 0.936 | 2.166 | 2.267 |
| drop the longest play | 0.938 | 0.986 | 2.604 | 2.540 |
| cap at 90th pct (runs 11, catches 23) | 0.864 | 1.034 | 2.207 | 2.167 |
| cap at 95th pct (runs 14, catches 30) | 0.794 | 0.939 | 2.113 | **2.066** |
| cap at 97.5th pct (runs 20, catches 38) | 0.771 | 0.865 | 2.098 | 2.075 |
| cap at 99th pct (runs 29, catches 50) | 0.793 | **0.851** | 2.136 | 2.151 |
| median play | 1.297 | 1.449 | 2.943 | 2.937 |
| league average alone | 0.581 | 0.565 | 2.250 | 2.239 |

82 / 76 runner seasons and 200 / 195 receiver seasons.

## Read

- Catches: cap each catch at 30 yards (95th percentile). Best in 2024-25, better
  than plain in both periods, and better than the league average.
- Runs: cap each run at 29 yards (99th percentile). Best in 2024-25 and better
  than plain in 2022-23 -- but every early figure lost to the league average, so
  three games of yards a carry are mostly noise and the read leans on the model's
  blended figure.
- Dropping the longest play was worse than the plain average every time: it always
  lowers a player's number, fluke or not.

These figures are report text only (research.catch_yards_read / carry_yards_read,
DECISIONS #166): no price, probability or record changes.

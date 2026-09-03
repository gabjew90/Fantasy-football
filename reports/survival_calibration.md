# Survival calibration (plan B1: horizon recomputed, structured where available)

Prediction = the engine's RAW survival to my next pick (structured field, or prose un-shrunk by the logged shrink; trails un-shrunk by 0.55 -- an assumption). Outcome = the player was still there at my next pick. Own takes inside the window and players gone before the window opened are excluded.

| room | type | teams | seat | picks | recs events | predictions | structured | prose |
|---|---|---|---|---|---|---|---|---|
| 1395566812157984768 | sleeper_human | 12 | 2 | 180 | 110 | 60 | 0 | 60 |
| 1396184666897145856 | sleeper_mock | 10 | 2 | 150 | 21 | 26 | 0 | 26 |
| 1396191077534281728 | sleeper_mock | 12 | 2 | 46 | 8 | 17 | 0 | 17 |
| 1396194982775238656 | sleeper_mock | 10 | 9 | 28 | 4 | 8 | 0 | 8 |
| 10502459 | yahoo_autopick | 10 | 9 | 150 | 14 | 1 | 0 | 1 |
| 10503516 | yahoo_autopick | 10 | 4 | 150 | 15 | 11 | 0 | 11 |
| 10504572 | yahoo_autopick | 10 | 9 | 150 | 15 | 9 | 0 | 9 |
| 10505450 | yahoo_autopick | 10 | 8 | 150 | 15 | 15 | 0 | 15 |

## pooled (n=147)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 6 | 25% | 0% | 0.290 |
| 30-49% | 14 | 37% | 29% | 0.605 |
| 50-69% | 20 | 59% | 30% | 0.799 |
| 70-89% | 33 | 80% | 42% | 1.043 |
| 90-100% | 74 | 96% | 86% | 0.466 |

## sleeper_human (n=60)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 3 | 25% | 0% | 0.284 |
| 30-49% | 2 | 39% | 0% | 0.494 |
| 50-69% | 5 | 59% | 0% | 0.904 |
| 70-89% | 10 | 82% | 30% | 1.368 |
| 90-100% | 40 | 97% | 82% | 0.584 |

## sleeper_mock (n=51)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 3 | 26% | 0% | 0.297 |
| 30-49% | 6 | 35% | 17% | 0.538 |
| 50-69% | 6 | 60% | 17% | 0.853 |
| 70-89% | 11 | 82% | 64% | 0.680 |
| 90-100% | 25 | 96% | 88% | 0.421 |

## yahoo_autopick (n=36)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 0 | - | - | - |
| 30-49% | 6 | 40% | 50% | 0.708 |
| 50-69% | 9 | 58% | 56% | 0.705 |
| 70-89% | 12 | 76% | 33% | 1.103 |
| 90-100% | 9 | 94% | 100% | 0.064 |

## The horizon defect, room 1395566812157984768 (the n the 0.55 shrink was fitted on)

| bucket | old horizon n | old observed | corrected n | corrected observed |
|---|---|---|---|---|
| 50-69% | 9 | 44% | 5 | 0% |
| 70-89% | 19 | 68% | 10 | 30% |
| 90-100% | 28 | 75% | 40 | 82% |

Old horizon: my_next_pick = the on-clock pick itself when I was on the clock, so every on-clock prediction graded as survived. Corrected: the window runs to my FOLLOWING turn.

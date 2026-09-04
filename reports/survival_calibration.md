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
| 10531886 | yahoo_autopick | 10 | 6 | 150 | 72 | 52 | 52 | 0 |
| 10532940 | yahoo_autopick | 10 | 3 | 150 | 62 | 46 | 46 | 0 |
| 10534350 | yahoo_autopick | 10 | 6 | 150 | 85 | 49 | 49 | 0 |
| 10584427 | yahoo_autopick | 10 | 8 | 150 | 90 | 58 | 58 | 0 |
| 10586715 | yahoo_autopick | 10 | 6 | 150 | 58 | 47 | 47 | 0 |
| 10588125 | yahoo_autopick | 10 | 1 | 150 | 53 | 38 | 38 | 0 |
| 10589182 | yahoo_autopick | 10 | 1 | 150 | 60 | 34 | 34 | 0 |
| 10590238 | yahoo_autopick | 10 | 7 | 150 | 58 | 52 | 52 | 0 |
| 10590944 | yahoo_autopick | 10 | 2 | 150 | 83 | 59 | 59 | 0 |
| 10597994 | yahoo_autopick | 10 | 5 | 150 | 72 | 53 | 53 | 0 |
| 10598876 | yahoo_autopick | 10 | 5 | 150 | 74 | 51 | 51 | 0 |
| 10600461 | yahoo_autopick | 10 | 5 | 150 | 53 | 56 | 56 | 0 |
| 10601343 | yahoo_autopick | 10 | 5 | 150 | 85 | 60 | 60 | 0 |
| 10611562 | yahoo_autopick | 10 | 3 | 150 | 63 | 54 | 54 | 0 |
| 10612448 | yahoo_autopick | 10 | 3 | 150 | 78 | 58 | 58 | 0 |
| 10616150 | yahoo_autopick | 10 | 7 | 150 | 87 | 57 | 57 | 0 |
| 10617211 | yahoo_autopick | 10 | 7 | 150 | 64 | 53 | 53 | 0 |
| 10618261 | yahoo_autopick | 10 | 9 | 150 | 65 | 51 | 51 | 0 |
| 10619316 | yahoo_autopick | 10 | 9 | 150 | 72 | 51 | 51 | 0 |
| 10693315 | yahoo_autopick | 10 | 5 | 150 | 55 | 50 | 50 | 0 |
| 10694196 | yahoo_autopick | 10 | 5 | 150 | 61 | 55 | 55 | 0 |
| 10703362 | yahoo_autopick | 10 | 4 | 150 | 68 | 55 | 55 | 0 |
| 10704422 | yahoo_autopick | 10 | 10 | 150 | 56 | 33 | 33 | 0 |
| 10705481 | yahoo_autopick | 10 | 2 | 150 | 72 | 62 | 62 | 0 |
| 10712781 | yahoo_autopick | 14 | 9 | 210 | 76 | 52 | 52 | 0 |
| 10713941 | yahoo_autopick | 10 | 8 | 150 | 73 | 41 | 41 | 0 |
| email1a059ffa1d94f905 | yahoo_email | 10 | 3 | 23 | 0 | 0 | 0 | 0 |
| email1a05a050324118c1 | yahoo_email | 10 | 1 | 150 | 0 | 0 | 0 | 0 |
| email1a05a43675df6ac2 | yahoo_email | 10 | 2 | 150 | 0 | 0 | 0 | 0 |
| email1a05a720ce261afe | yahoo_email | 10 | 4 | 150 | 0 | 0 | 0 | 0 |
| email1a05aae58012b315 | yahoo_email | 10 | 5 | 150 | 0 | 0 | 0 | 0 |

## pooled (n=1474)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 55 | 18% | 16% | 0.626 |
| 30-49% | 130 | 40% | 9% | 0.557 |
| 50-69% | 201 | 60% | 14% | 0.860 |
| 70-89% | 329 | 81% | 49% | 0.933 |
| 90-100% | 759 | 96% | 87% | 0.447 |

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

## yahoo_autopick (n=1363)

| predicted | n | predicted avg | observed | log loss |
|---|---|---|---|---|
| 0-29% | 49 | 18% | 18% | 0.667 |
| 30-49% | 122 | 40% | 9% | 0.559 |
| 50-69% | 190 | 60% | 14% | 0.859 |
| 70-89% | 308 | 81% | 49% | 0.927 |
| 90-100% | 694 | 96% | 87% | 0.440 |

## The horizon defect, room 1395566812157984768 (the n the 0.55 shrink was fitted on)

| bucket | old horizon n | old observed | corrected n | corrected observed |
|---|---|---|---|---|
| 50-69% | 9 | 44% | 5 | 0% |
| 70-89% | 19 | 68% | 10 | 30% |
| 90-100% | 28 | 75% | 40 | 82% |

Old horizon: my_next_pick = the on-clock pick itself when I was on the clock, so every on-clock prediction graded as survived. Corrected: the window runs to my FOLLOWING turn.

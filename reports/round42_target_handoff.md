# Round 42: the target handoff by absence age (pre-registered 2026-10-06, before any run)

## Why

The backtest never runs the injury logic (DECISIONS #198). The second expert audit measured
same-position teammates' targets, actual / projected: no key teammate out 0.98, first game
out 1.08 (1.03-1.12), continuing absence 1.04 (1.00-1.07). The live rule
(score_game.OUT_RULE["ts"] = x 0.2, y 0.25) hands on a quarter of the absent player's share
every week: about right the first game, about double later. Round 35 tested WHAT is handed
on (V2 for targets: positive every held-out season, not detectable; targets kept V0); this
round tests HOW MUCH, by absence age, keeping V0's share (the absent player's raw share last
season, as live).

## The grid

| | Shipped | Grid |
|---|---|---|
| y, first game out | 0.25 | 0.25, 0.35, 0.5 |
| y, continuing absence | 0.25 | 0.25, 0.15, 0.10, 0.05 |

x (the part spread over every teammate rather than his position) stays 0.2. 12 settings.

## Rule -- props/tools/round42_select.py (round 35's scoring)

- Each teammate-game: his season-to-date share plus the handoff, scored by squared error
  against his actual share; intervals resample whole team-seasons.
- **Selection 2022-24:** the lowest loss; within 0.5% of the best, the setting closest to
  shipped.
- **Ship:** the pick beats shipped with a 95% interval above zero on 2022-24; neither the
  first-game-out nor the continuing part worse by more than 5% of shipped's loss there; **not
  worse on 2026 weeks 2-4** (point estimate; 2025 is not read -- round 35 used it).
  Leave-one-season-out reported.
- Reported beside it: same-position teammates' actual / predicted share, first game out and
  continuing, shipped and pick.
- The live code's handoff is checked by known-answer tests if it ships (the harness does not
  reproduce the Out rule).

## Result

(Filled in after the run, below this line, without editing anything above.)

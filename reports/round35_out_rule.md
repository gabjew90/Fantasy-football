# Round 35: what the Out rule hands on, and for how long (pre-registered 2026-10-06, before any run)

## Why (second outside review, checked against the code)

The Out rule (score_game.apply_out_rule, OUT_RULE; reports/absence_tune.md) hands a quarter
of an absent player's share to the priced teammates. Two things differ from how it was tuned:

1. **Whose share.** It was tuned on the absent player's share THIS season, in the games he
   played (absence_tune.py `k_share`). The live scorer hands on his raw share from LAST
   season (`excl_rates`: priors target_share / rush_share).
2. **For how long.** It was tuned with teammates' shares measured over games WITH him. Live,
   a teammate's share is a season blend; after a few weeks out, it already contains the
   absence, and the rule adds the same quarter again every week.

Expected, not measured: the first game out is understated, a long absence overstated. This
is the spot where the user bets (an injury opens volume).

## What is compared (the absence games of 2022-25, every week a 15%+ target / 20%+ carry player is rostered but not active)

Each priced teammate's share in that game is predicted from his season-to-date share
before the game (the scorer's current-season evidence) plus the rule's handoff, and scored
against his actual share (squared error, per teammate-game; 95% intervals resampling whole
absence events). The shipped (x, y) per column stay fixed; only WHAT is handed on changes:

| Variant | The absent player's share handed on |
|---|---|
| V0 (shipped) | his raw share last season (his this-season share where no prior exists) |
| V1 | his share this season, in the games he played before this one |
| V2 | V1, times the fraction of the teammate's season-to-date games in which the absent player played (what is NOT yet in the teammate's share) |

## Rule

- **Selection on 2022-24:** the variant with the lowest loss, targets and carries scored
  separately; V0 kept within 0.5% of the best.
- **Ship test:** the pick beats V0 with a 95% interval above zero on 2022-24 AND is not
  worse on 2025 (read once; this family has not been read on 2025). Reported for all
  absence games and split by first game out / continuing.
- **Guards:** none needed beyond the split -- the rule only moves teammates of an absent
  player; the split must not show the pick worse by more than 5% of V0's loss in either
  part on 2022-24.
- **Leave-one-season-out** reported beside it (props/tools/loso_select.py convention).
- A pick that fails ships as a SHADOW line only if the user asks (DECISIONS #185 style).

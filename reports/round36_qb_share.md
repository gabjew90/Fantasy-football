# Round 36: the starter-share draw on QB passing (pre-registered 2026-10-06, before any run)

## Why

QB passing yards are too WIDE on the whole chain: 14% of games outside the model's 80% range
on 2022-25 (the bar is 17-23%), while given every receiver's actual targets they sit at 18%
-- so the excess width is in the volume or the starter's share, not the conversion. Round 33
ruled out the team's throw dispersion. What is left is the draw that multiplies every
simulated passing game by "the share of the team's passing yards the starter keeps" (prior
season's grid, mean 0.96, low tail 0.03): it prices injury exits and benchings into every
start, and a draw that is too spread out makes every passing distribution too wide.

## The knob

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| starter_share_shrink | the same share draw pulled toward the grid's own mean by this factor (keeps the passing average; 0 = always the mean) | off (= 1) | off, 0.75, 0.5, 0.25, 0 |

Everything else shipped. Only QB passing moves (the draw multiplies nothing else).

## Selection (2022-24, `--conditional`, scoreboard)

The setting with the lowest QB-passing own-volume log loss at the stand-in lines, game-clustered;
ties within 0.0005 go to the setting closer to shipped; a pick that moves the passing Over chance
by less than 1.0 point stays shipped.

## Ship test

- Detectable on 2022-24: passing own-volume log loss gain, 95% interval above zero (10,000
  resamples), decision-zone (15-85%) log loss and Brier agreeing in sign.
- Confirmed on 2025, read once (this family has never been read on 2025): gain not negative.
- Width reported beside it: the whole-chain passing share outside the 80% range should move
  toward 20%.
- Guards: none needed (no other market reads the draw); scoreboard.guard_verdict confirms every
  other market unchanged.
- Leave-one-season-out gain reported (loso_select.py). Tool: props/tools/round36_select.py.

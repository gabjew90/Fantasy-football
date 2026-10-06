# Round 32: receiving yards' spread as catches pile up (pre-registered 2026-10-06, before any run)

## Why

With the actual targets plugged in (scoreboard, 2022-25), receiving yards are off in
opposite directions by volume: too narrow with 1-3 targets (21.4% of games outside the
80% range), too wide with 4-6 (18.0%), 7-9 (17.0%) and 10+ (14.8%). The model sums
independent per-catch gamma draws, so its spread grows in proportion to catches; real
games' spread grows more slowly. Round 30's single shape multiplier moved every band the
same way and scored worse at the lines.

## The knobs (conversion only; the mean is unchanged)

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| catch_shape_exp | spread grows as catches^(2 - exp); 1 = today's linear growth | 1 (off) | 1, 1.15, 1.3, 1.5 |
| catch_shape_mult | per-catch shape x this (below 1 widens one-catch games) | 1 (off) | 1, 0.8 |

Crossed: 8 settings (catch_conc stays off; round 30).

## Selection (2022-25, weeks 2-18, `--conditional`, scoreboard lines)

The setting with the lowest receiving-yards conversion log loss on the bettable
population; ties within 0.0005 go to the setting closer to shipped. A pick that moves the
Over chance by less than 1.0 point on average stays shipped.

## Ship test (the scoreboard's rule)

- Detectable on 2022-25: receiving-yards conversion log loss gain, 95% interval above zero
  (game-clustered).
- Big enough: 1.0+ point average move at the stand-in lines.
- Confirmed on 2026 weeks 2-4, read once (the receiving-conversion family has not been read
  on those weeks): gain not negative.
- Guards: receptions unchanged by construction; rushing + receiving and QB passing
  conversion no worse than -0.5% of their own (point estimate).

## Result

(Filled in after the runs, below this line, without editing anything above.)

### Selection, 2022-25 (receiving-yards conversion log loss at the stand-in lines, bettable receivers)

| catch_shape_exp | mult 1 | mult 0.8 |
|---|---|---|
| 1 (shipped) | **0.51529** | 0.51679 |
| 1.15 | 0.51533 | 0.51543 |
| 1.3 | 0.51733 | 0.51626 |
| 1.5 | 0.52175 | 0.51945 |

**The shipped shape is the best: round 32 is null at selection**; 2026 is not read for it.
The by-volume pattern in the PIT (narrow at 1-3 targets, wide at 10+) sits in the tails;
at lines near the middle -- where bets are placed -- the shipped shape already scores best.
With round 30's catch-rate result, the receiving conversion is as good as these knobs make
it; the open receiving lever is the volume spread (round 31's finding).

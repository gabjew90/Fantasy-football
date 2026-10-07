# Round 41: tight ends and backs -- their own yards shape, tight ends' share (pre-registered 2026-10-06, before any run)

## Why

The second expert audit (DECISIONS #198), reproduced at round 34's setting on 2022-25:

| Group | Receptions: Over hit / engine | Receiving yards: Over hit / engine | Yards outside the 80% range, actual targets in |
|---|---|---|---|
| Tight ends | 49.0% / 44.1% (+4.9) | 54.0% / 47.4% (+6.6) | 14.4% (too wide) |
| Wide receivers | 45.1% / 44.3% | 50.1% / 47.6% | 17.5% |
| Backs | 43.0% / 43.9% | 46.7% / 46.2% | 24.8% (too narrow) |

One per-catch yards shape serves every role. Tight-end targets ran 5% above projection on the
bettable rows (the expert: 3%, 0.4-5.4%).

## The knobs (receiving only; explicit neutral values)

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| catch_shape_mult_te | tight ends' per-catch yards shape times this (larger = narrower) | 1 | 1, 1.5, 2 |
| catch_shape_mult_rb | backs' per-catch yards shape times this (smaller = wider) | 1 | 1, 0.75, 0.5 |
| te_share_mult | tight ends' target share times this; the depth bucket gives it up | 1 | 1, 1.03, 1.06 |

Crossed: 27 settings (`--tune-grid receivingroles`). Wide receivers keep the shared shape.

## Selection -- props/tools/round41_select.py, three stages, each on its own role's rows

1. **A1, tight-end shape:** tight ends' receiving-yards **conversion** log loss (actual targets
   in: the scoreboard's rule for a conversion setting), 2022-24.
2. **A2, back shape:** backs' receiving-yards conversion log loss, at A1's result.
3. **B, tight-end share:** tight ends' receptions **own-volume** log loss, at A1 and A2.

Each stage: the lowest score; ties within 0.0005 go to the value closest to shipped; a pick
must move the Over chance by at least 1 point on average; the gain detectable (95%
game-clustered interval above zero) with log loss and Brier agreeing in the 15-85% zone;
leave-one-season-out reported; **confirmed on 2026 weeks 2-4** (the gain not negative, point
estimate; about a hundred tight-end and back rows, a sign check). A stage that fails keeps
its knob at 1 and the next stage runs at 1.

## Guards on the combined setting (2022-24, every market, both scores)

- No market's conversion or own-volume log loss worse than shipped by more than **0.2%** (the
  expert's point: 0.5% near 50% allows a ~4-point shift), QB passing included (its yards are
  the receivers' sum).
- **Width:** each moved role's receiving-yards width with actual targets in must end closer to
  the 17-23% bar than shipped's (tight ends 14.4%, backs 24.8%), or inside it. (Measured
  with actual targets in, where the level bias cannot move outcomes across the range the way
  it did in round 38.)
- **Role calibration:** tight ends' Over-minus-engine gap must shrink on both markets.
- Reported beside it (the standing rule from #197): the Over rate against the engine by
  implied points, shipped and pick.

## If a role knob ships

- The live share multiplier is applied to the tight end's projection itself (his ts), so the
  report's projected targets, the 50/50 search and the card all show it; the search gets the
  role's shape (research.implied_targets, role=).
- The card's measured-calibration role rows are re-measured at the new setting.

## Result

(Filled in after the runs, below this line, without editing anything above.)

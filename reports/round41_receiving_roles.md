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

## Result (2026-10-06; props/tools/round41_select.py on the 27-setting grid, 2022-26)

| Stage | Pick | Gain on 2022-24 (95%) | 2026 weeks 2-4 | Leave-one-season-out | Verdict |
|---|---|---|---|---|---|
| A1 tight-end yards shape (conversion) | 1.5 | +0.0031 (-0.0020, +0.0080) | -0.0049 | +0.0031, every fold 1.5 | not detectable, 2026 negative: **stays 1** |
| A2 backs' yards shape (conversion) | 1 (shipped best) | -- | -- | -- | **stays 1** |
| B tight-end share (own volume) | **1.06** | **+0.0063 (+0.0016, +0.0112)** | +0.0012 (-0.016, +0.020) | +0.0063 (+0.0014, +0.0111), every fold 1.06 | **ships** |

Move of the Over chance 3.8 points (bar 1.0); log loss and Brier agree in the 15-85% zone.

**Guards on the combined setting (1 / 1 / 1.06), 2022-24, floor -0.2%:** conversion identical in
every market; own volume receptions +0.15%, receiving yards +0.27%, rushing + receiving -0.04%,
QB passing -0.10%, rushing identical -- **pass**. **Width:** the share knob cannot move the
conversion draws; on the frozen cohort tight ends' yards width is identical (14.37% both,
draws equal), so it does not move away from the bar (the unfrozen 14.4 -> 14.5 is rows entering
the bettable set). **Role calibration** (Over minus engine, points):

| | Tight-end receptions | Tight-end yards |
|---|---|---|
| Shipped, 2022-24 | +5.4 | +7.4 |
| Pick, 2022-24 | +1.9 | +4.7 |
| Shipped, 2026 weeks 2-4 | +0.5 | +5.9 |
| Pick, 2026 weeks 2-4 | -2.8 | +3.0 |

Shrinks on both: pass. By implied points (reported, the standing rule): receptions'
weighted gap falls in every row; receiving yards' too (24-27 still +6.0).

**Round 41 ships te_share_mult 1.06** (resources/width_params.json). Live it multiplies the
tight end's projected share (score_game, after the Out rule, before the share cap); the
simulation then runs without it, so it is applied once. The cards' receiving calibration rows
are re-measured at the new setting.

### Withdrawn on the seed check (2026-10-06, third expert review; DECISIONS #203)

The backtest's random noise is larger than some gains it approved (two runs of the same model
differ by up to 0.0015 in log loss and 1.7-1.8 points in the Over chance). Re-run under three
more seeds (`--tune-grid seedcheck41 --audit-seed-offset 1|2|3`), tight-end rows, receptions own
volume, 1.06 against 1.00:

| Seed | Gain 2022-24 (95%) | 2026 weeks 2-4 |
|---|---|---|
| 0 (the run it shipped on) | +0.0063 (+0.0013, +0.0112) | +0.0013 |
| 1 | +0.0032 (-0.0017, +0.0081) | -0.0050 |
| 2 | +0.0055 (+0.0009, +0.0105) | -0.0027 |
| 3 | +0.0051 (+0.0004, +0.0099) | +0.0004 |
| Average | +0.0050 | **-0.0015** |

The confirmation (2026 not negative) fails on the seed average and on two of four seeds, and the
live record at Sleeper's lines shows no tight-end lean (45.7% hit against an engine 46.3%, 199
lines). **te_share_mult goes back to 1** (the knob stays in the code, off). Seed noise between
two runs of the shipped model: Over moves of 1.7-1.8 points, log-loss differences up to 0.0018.

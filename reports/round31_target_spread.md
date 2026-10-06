# Round 31: the spread of a receiver's targets around his average (pre-registered 2026-10-06, before any run)

## Why

The scoreboard's spread check (2022-25, stable-role stretches; reports/scoreboard.md)
finds the model's game-to-game spread of targets wider than real games in every volume
band: real / model 0.83 (3-5 projected targets), 0.88 (5-8), 0.84 (8-11), each interval
below 1. Real spread there includes undetected role drift, so the model is too wide for
certain. Under the user's method (he sets the average, the engine spreads it), too much
spread pulls every confident receiving price toward 50% even when his read is right.
Carries are consistent in every band and are not touched.

## The knobs (volume spread only)

| Knob | What it does | Shipped | Grid |
|---|---|---|---|
| share_conc_targets | how tightly a player's share holds game to game | 40 | 40, 60, 80, 120 |
| team_r_mult | the team targets' dispersion x this (larger = steadier team volume) | 1 (off) | 1, 1.5, 2.5 |

Crossed: 12 settings.

## Selection (2022-25, weeks 2-18, corrected harness, `--conditional`)

The scoreboard's volume-spread rule -- the ratio moves toward 1 and not past it: among the
settings whose real / model ratio stays at or below 1.00 in all three bands (3-5, 5-8,
8-11), the one with the smallest largest gap to 1. Real spread is an upper bound, so the
engine is never narrowed past it. Ties (largest gap within 0.01) go to the setting closer
to shipped (fewer knobs moved, then smaller moves).

## Ship test

- **Guard (2022-25):** the own-volume log loss (the engine's own volume at the stand-in
  lines) for receptions and receiving yards no worse than -0.5% of its own (point
  estimate); the conversion score is untouched by these knobs (it plugs in the actual
  volume).
- **Confirmed** on 2026 weeks 2-4, read once (a family not yet read on those weeks): the
  own-volume log loss gain for receptions and receiving yards not negative (point
  estimate). Three weeks are too few for stable stretches, so the spread check itself is
  not repeated there.
- Team-level knob (team_r_mult): intervals cluster by team-season.

## Result

(Filled in after the runs, below this line, without editing anything above.)

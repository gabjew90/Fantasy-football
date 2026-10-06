# Round 29: the backs' carries take a share from the market (pre-registered 2026-10-06, before any run)

## Why

The implied team total test (reports/implied_total_test.md) found the backs' rushing yards
tracking the market's implied team total beyond the model, with the same slope in 2022-23
and 2024-25 (b = +0.60). Split on the same tuning data, most of it is carries (b = +0.46 /
+0.38, both clear) rather than yards per carry (+0.15 / +0.23): favoured teams run more,
and the backs' volume comes from history alone. Round 16 (DECISIONS #134) moved the throws
25% toward the market's fitted volume and left runs out because the full market environment
had hurt QB rushing (#106). This round moves the BACKS' carries only.

## The change

Team carries = (1 - w) x history + w x the market's fitted carries (plays x (1 - pass rate)
from `market_env_fit`, the fit #134 uses for throws), with the starting QB's expected
carries held where history put them (his carry share divided by the same factor), so only
the backs' and the depth pool's carries move. One function in model.py, called by the
scorer and the harness.

Grid: w = 0 (shipped), 0.25, 0.5, 0.75, 1.0.

## Selection (tuning data: 2022-25, weeks 2-18, corrected harness)

The w with the lowest rushing-yards CRPS; eligible only if QB rushing CRPS is no worse than
w = 0 (point estimate). Ties within 0.005 go to the smaller w.

## The ship test (2026 weeks 2-8, read once, after week 8 is graded -- with round 28)

Against shipped: rushing yards and rushing attempts CRPS no worse (point estimate), QB
rushing no worse, no calibration verdict worse in those three markets; receiving and
passing identical (these carries do not feed them; a difference stops the round).

**With round 28:** both are read once on the same weeks. Each ships only on its own test;
if both pass, the two together must also pass the same test before both ship (otherwise
the one with the larger rushing-yards gain ships alone).

## Result

(Filled in after the runs, below this line, without editing anything above.)

# Does the model under-use the market's implied team total? (pre-registered 2026-10-06, before any run)

## Why

The engine takes the market's spread and total for its touchdown level and for 25% of
its throws; everything else -- runs, shares, efficiency -- comes from history. If the
implied team total carries information the model does not, a team the market expects to
score more will beat our yardage projections, and one it expects to score less will fall
short. The outside reviewer put this test first among the market questions: if it passes,
the implied total already carries things like offensive-line injuries, and the separate
line test becomes redundant.

## Data

The shipped engine's harness results per player-game, 2022-25, from the corrected harness
(starting-QB markets graded only on the QB who started, DECISIONS #181); games.csv spread
and total.

## The measure

Per team-game: the team's receivers' summed actual receiving yards over their summed model
means; the same for its backs' rushing yards (the rushing population); the starting QB's
passing yards. The implied team total = (total + own spread) / 2, expressed against the
model's own expectation of the team: **implied ratio** = implied total / the team's mean
implied total over its earlier games that season (weeks with an earlier game only).

## The test (fixed now)

For each market, regress log(team actual / model) on log(implied ratio), team-games
weighted equally; the slope b. With the level set on the sum scale (DECISIONS: the
backup-QB diagnostic's correction -- the slope is what this test reads).

- **The implied total carries information the model lacks** for a market if b > 0 with a
  95% interval (resampling team-games) excluding zero in BOTH 2022-23 and 2024-25.
- **It does not** if the 2022-23 and 2024-25 intervals both include zero, or the two
  slopes have opposite signs.
- Otherwise **unresolved**.

A market that passes becomes a candidate for a pre-registered tuning round (an implied-
total term in that market's volume or efficiency), judged on CRPS like every other round.
Nothing ships from this test by itself. The offensive-line test is queued after this one.

## Result

(Filled in after the runs, below this line, without editing anything above.)

### Run 2026-10-06 (props/tools/implied_total_test.py; the corrected harness, 2022-25, shipped engine)

The corrected harness left out team-games where the depth chart's starter did not start:
30 / 24 / 31 / 7 of about 470 a season (2022-25).

| Market | 2022-23: team-games, b (95% CI) | 2024-25: team-games, b (95% CI) | Verdict |
|---|---|---|---|
| Backs' rushing yards | 1,017, +0.601 (+0.257, +0.971) | 1,018, +0.608 (+0.333, +0.889) | **the implied total carries information the model lacks** |
| Receivers' receiving yards | 1,021, +0.194 (-0.010, +0.394) | 1,023, +0.416 (+0.141, +0.719) | unresolved |
| Starting QB passing yards | 875, +0.180 (-0.047, +0.395) | 901, +0.478 (+0.142, +0.759) | unresolved |

**Reading.** The backs' running game takes nothing from the market (its volume is the
team's history; DECISIONS #106 found the full market environment hurt QB rushing, so runs
were left out of #134's market blend). Yet a team the market expects to score 10% above its
usual runs for about 6% more than our projection, with the same slope in both periods. The
receiving and passing slopes point the same way (clear in 2024-25, just short in 2022-23):
the throws already take 25% from the market, and the remainder looks smaller.

Next, per the rule: the backs' rushing becomes a candidate for a pre-registered tuning round
(an implied-total term in the backs' carries or yards per carry, leaving the QB's carries
alone). The offensive-line test was queued behind this one because a passing implied-total
term would already carry line injuries; for rushing it now likely does.

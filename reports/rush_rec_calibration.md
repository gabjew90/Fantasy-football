# Rushing + receiving yards: can the engine price the combined line? (pre-registered 2026-10-06, before any run)

## Why

DECISIONS #173 brought Sleeper's rushing + receiving line in as a read and held back our
own price: the simulation draws a team's runs and passes independently, so a back's
carries and targets never trade off with the game script, and summing his rushing and
receiving draws may misstate the spread. The user bets the combined line when it is the
better leg, so the check #173 promised runs now.

## Data

The corrected harness (starting-QB markets graded on the QB who started), 2022-25 weeks
2-18, shipped engine. Population: the rushing population (backs on the depth chart, or 20%+
of the team's carries over his last four games) who are also in the receiving population.
The combined draw is his receiving-yards draw plus his rushing-yards draw in the same
simulation index; the actual is his receiving plus rushing yards.

## The rule (fixed now)

The engine prices the combined line if its harness verdict parts are **not FAIL**:

- **width:** outcomes outside the model's p10-p90 -- the 95% interval must overlap
  0.17-0.23 (the bar every priced market uses);
- **bias:** actual / model mean within 5% -- the interval must overlap -5% to +5%;
- **calibration bands:** no 60-90% reliability band FAILS.

A FAIL on width or bias means summing independent draws misstates the combined line; then
pricing waits for the script-linked team volume model (Tier 3), and the board keeps reading
the line without a price.

Reported alongside, as diagnostics (no part of the rule): the actual correlation between a
back's rushing and receiving yards residuals, against the model's (zero by construction),
and the same parts for rushing yards and receiving yards alone on the same backs.

## Result

(Filled in after the run, below this line, without editing anything above.)

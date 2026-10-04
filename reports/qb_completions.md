# QB completions: can the engine price them? (pre-registered 2026-10-03, before any run)

## Why

Sleeper posts pass completions and pass attempts (30 QBs in the week-4 pull);
the research advice prefers workload props to yardage. The engine already
simulates every receiver's catches in the same game as the starting QB's
passing yards (model.simulate_qb_passing).

## The model (no new setting)

`model.simulate_qb_completions`: the tracked receivers' simulated catches,
plus the depth receivers' ('other' bucket) targets caught at the prior
season's depth catch rate, times the starter's share of the team's passing
(the same prior-season grid passing yards use), rounded to a whole catch. Its
own child random stream, drawn after passing yards, so no other number moves.
Attempts are not graded here: throwaways and spikes are not targets, so they
need a separate piece.

## The bar (written before running)

Completions are priced only if, on the test seasons 2024-25, they pass the
four-part `live` bar every priced market passed: beat baseline A on each test
season (interval excluding zero), unbiased (actual/model within 5%, PIT
0.47-0.53), width 0.20 +/- 0.03 outside p10-p90, and every 60-90% reliability
bucket within 0.03 (weeks 5-18). Every other market must stay identical.

## Result (2026-10-03): does not pass -- not priced

Test seasons 2024-25 (940 starting-QB games); every other market identical.

| Seasons | Gain over baseline A (95% CI) | Actual/model | PIT | Outside p10-p90 |
|---|---|---|---|---|
| 2024 all weeks | +0.028 (-0.037, +0.092) | 0.935 | 0.462 | 0.235 |
| 2025 all weeks | +0.073 (+0.014, +0.135) | 0.969 | 0.476 | 0.169 |
| test, weeks 5-18 | +0.020 (-0.021, +0.063) | 0.945 | 0.466 | 0.208 |

Verdict: beats baseline A each season **no**; unbiased **no** (the model runs
~5% high: actual/model 0.952); width 0.202 yes; calibration worst 0.058 **no**
(Overs 4-6 points too confident, Unders under-confident -- the bias, not the
width). Likely causes: the depth receivers' catch rate, targets thrown by
someone other than the starter, or the starter-share grid (built on yards)
applied to a count. The next step is a completions adjustment learned from the
prior season (live-faithful, from priors_{S-1}), pre-registered on 2022-23.
Pass attempts were not attempted: they need a throwaway/spike piece on top.

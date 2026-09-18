# nfl-prop-research: how the numbers are built
Version 1.0, 2026-09-17. Applies to model core `model.py` at registry entries receiving_hier_v2 (receptions, receiving yards), rush_yds_v0, anytime_td_v0. Running example: Dalton Kincaid, BUF TE1, DET@BUF 2026 week 2, Under 4.5 catches.

## 1. Data
- nflverse play-by-play, current season (weeks 1 to N-1): targets, catches, carries, yards, TDs, goal-line (inside-10) plays.
- nflverse prior season, pre-processed offseason by `build_priors.py` into `priors_{season}_*`: per-player shares and rates, per-slot league priors, per-team volumes, opponent efficiency allowed, dispersion fits, TD constants.
- Weekly rosters (ACT/INA), injury report, depth charts, snap counts for the target week.
- The Odds API: spreads, totals, allowlisted player props, all books returned.
- NWS hourly forecast at the stadium (Open-Meteo fallback).

Kincaid: 2025 = 15% target share over 14 games, catch rate 75%, 7.6 yards per target. 2026 wk 1 = 6 of 29 targets (21%). DK Under 4.5 at -167.

## 2. Team environment (how many chances exist)
Throws and runs per game: the team's prior-season mean blended with its current-season games (K0 = 4 games), times a league-wide drift ratio (recent 3 weeks / expanding, clipped 0.85 to 1.15, inactive before week 5). BUF: 29 throws, 29 runs.
Team offensive TDs: market-anchored. Implied points from the same-book spread and total, times the league TD-per-point constant, split pass/rush by the team's history. BUF: 30.0 implied points, 3.2 TDs. If the spread/total is unavailable the history blend is used and TD calls are capped at MODERATE.
Not conditioned on game script: the volume draw is centred on the blend regardless of whether the team is expected to be ahead or behind. `--env market_fit` shifts the centre by spread and total (fit on 2025, R2 0.02 to 0.04) and is not default. Within a team all players share one volume draw; across teams the draws are independent. Consequence: the whole pie shrinking together is simulated within a team, but the state that shrinks it (leading, trailing) is not, and cross-team script correlation is absent. Open registry gap.

## 3. Player share (how many of those chances are his)
Per rate (target share, catch rate, yards per target, rush share, yards per carry, goal-line shares):
1. Individual prior = his own prior-season rate, shrunk toward the slot prior by games played.
2. If he changed teams, the individual prior's weight is capped and the share is scaled by current/prior snap share.
3. Final = blend(current-season rate, current opportunities, individual prior, K0_rate) where weight on current = n / (n + K0_rate), n in opportunity units.
Kincaid target share: 0.15 prior, 0.21 current on 29 team targets, K0 = 80, weight on current 27%, final 0.16. Targets = 0.16 x 29 = 4.7.
Injuries: Out/Doubtful removed and share redistributed to the eligible set; Questionable projected as a normal/limited/out mixture (scale 0.86 conditional on playing).

## 4. Opponent adjustment
Team-level prior-season efficiency allowed (catch rate, yards per target, yards per carry), shrunk toward league with k0 = 150 plays, applied as a multiplier. DET defense: 0.954 on catches, 1.013 on yards per target. Kincaid catches: 4.7 x 0.75 x 0.954 = 3.37 expected.

## 5. Simulation
20,000 draws, seed fixed.
- Team volume: negative binomial around the environment (dispersion r = 33.7 targets, 28.5 carries).
- Split among players: multinomial by final share.
- Catches: binomial per target at the player's catch rate. Player-level count dispersion uses log r = a + b log mu (receptions a = 2.007, b = 0.830).
- Receiving yards: Gamma with league-wide per-catch shape 1.065 and player-specific scale (his yards per catch). Shape is not per player.
- Rushing yards: per-carry draws from the empirical 2025 residual quantile grid around the player's yards per carry.
- TDs: team pass and rush TDs allocated by goal-line share for the inside-10 fraction and by overall share for the rest; P(at least one) = 1 - exp(-lambda).
Kincaid: median 3 catches, P(<4.5) = 14,327 / 20,000 = 71.6%.

## 6. Book number
Both sides' American prices converted to implied probability, normalised to remove vig. DK -167 Under implies 62.5% raw, about 59% no-vig.

## 7. Edge rule and thresholds
Edge = model probability minus no-vig probability, in points. EV per $100 = 100 x (p x payout - (1 - p - push)). Kelly = (b p - q) / b. Thresholds ("Under if >= X") are the same draws read at each possible line, at -110.
Floors: 6 points for count and yardage props; 25% relative edge for TD props.

## 8. Tiers
- WEAK: new team, Questionable, current-season share more than 10 points from the prior (|cur - own_prior| > 0.10 where own_prior > 0.05), or gap over 15 points.
- STRONG: stable role, gap at or above the floor, and NOT prior-driven.
- Prior-driven test: if current-season share is more than 10% above the blended share and the call is Under (or more than 10% below and Over), the gap exists because the model trusts the prior more than the market does. Demoted to MODERATE and noted. Kincaid: current 0.21 vs blend 0.16 (+31%), call Under, so demoted.
- LEAN: stable but under the floor, no bet.
- TD calls: never STRONG if the team total is not market-anchored; annotated if history disagreed with market by more than 20%.

## 9. TD props are partly circular
The team TD total comes from the market's implied points. A TD gap therefore lives only in the allocation (goal-line share, overall share), not in the team's scoring expectation. Treat a TD gap as a share disagreement, not a game disagreement, and never as equivalent to a receptions gap.

## 10. Validation status
Walk-forward 2025 backtest of receptions and receiving yards (train weeks 5-8, test 9-18, N = 1,895 player-weeks):
- CRPS model 1.009 vs naive baseline 1.050 (receptions), 13.27 vs 13.94 (yards).
- Bias: PIT mean 0.498 / 0.503, actual/model mean 0.995 / 1.011.
- Distributional self-check (NOT calibration against a sportsbook): with lines placed at fixed offsets from the model's own median and bucketed by predicted probability, realized frequency lands within 2.6 points of stated in every 50-90% bucket for both markets and both sides. Worst bucket: 90%+ Under yards, realized 90.1% vs stated 94.4%. Table in `calibration_2025.csv`.
  - **The `n` column in that table is not a count of independent observations.** Each of the 1,895 player-weeks is reused at 8-10 offsets (4 for receptions, 5 for yards, each on both sides), so a bucket showing n=1,823 rests on far fewer than 1,823 independent games. It overstates the evidence by roughly an order of magnitude.
  - **It cannot speak to betting performance.** The lines are not book lines, and it covers every player-week symmetrically, whereas a call only occurs where the model and the book disagree. Selection is the whole mechanism, and this test removes it.

**Validated against posted sportsbook lines: nothing.** Not the pre-week-5 prior blend (this form was not in the backtest), not rushing yards, not anytime TD, not the edge rule against closing lines, not the prior-season team-volume blend in the live scorer, and not joint/parlay outcomes, which have never been compared against realised joint results at all. Every market is therefore ineligible under `scripts/eligibility.py`, and the record in `props/record` is being accumulated prospectively to answer the question. Second-season (2024) confirmation pending a residual 2.6% bias.

## 11. Parameter table (v1.0)
| Parameter | Value | Where |
|---|---|---|
| Team volume blend K0 | 4 games | priors_2025_params.json |
| K0 target share | 80 targets | k0_per_rate |
| K0 catch rate | 40 targets | k0_per_rate |
| K0 yards per target | 160 targets | k0_per_rate |
| K0 rush share | 40 carries | k0_per_rate |
| K0 yards per carry | 80 carries | k0_per_rate |
| K0 inside-10 target / carry share | 5 / 4 | k0_per_rate |
| Opponent shrinkage k0 | 150 plays | model.opponent_multiplier |
| Drift ratio window / clip | 3 weeks / [0.85, 1.15], off before week 5 | model.league_drift_ratio |
| Team targets / carries dispersion r | 33.7 / 28.5 | team_volume_dispersion |
| Receptions dispersion log r = a + b log mu | 2.007, 0.830 | receptions_dispersion |
| Carries dispersion | -0.652, 1.416 | carries_dispersion |
| Per-catch Gamma shape (league) | 1.065 | shape_ypc_per_catch |
| League pass rate / plays per game | 0.540 / 56.8 | params |
| League TD per point | 0.1055 | league_td_per_point |
| Questionable scale (conditional on playing) | 0.86 | score_game.py |
| New-team snap scaling | current / prior snap share | score_game.py |
| Role stability threshold | |cur - own_prior| > 0.10 | score_game.py stability() |
| Prior-driven gap threshold | (cur - blend) / blend > 0.10 | score_game.py |
| Edge floor | 6 pts; TD 25% relative | EDGE_FLOOR |
| Draws / seed | 20,000 / 20260917 | score_game.py |

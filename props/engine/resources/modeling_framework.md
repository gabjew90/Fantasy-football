# Opportunity-based prop modeling

Use this resource for distributions, fair odds, and entry thresholds. API-only tests do not need it. Verified historical seasons may supply priors for future outcomes. Keep current-season observations anchored to current-season games and honor any explicit user restriction on historical evidence.

## Generation process
Model the causes of the box score in linked stages. A candidate production model represents at least:

1. **Team environment:** possessions/plays, dropbacks and rush attempts, game-script regimes, and team scoring or touchdown opportunities, with uncertainty in each. Estimated from pre-game data only (see the pre-game information guard in `research_standard.md`). A same-book spread/total may inform a disclosed market-anchored scenario but cannot then serve as independent evidence of betting edge.
2. **Player opportunities:** allocate targets and carries among eligible teammates using role shares conditional on team volume; account for QB scrambles, goal-line allocation, red-zone targets, and changing teammates. Share draws obey team totals. The eligible set is the pre-game active roster. Update utilization parameters with verified current-season target/rush shares, high-value touches, and snap role. Snap share never substitutes for routes.
3. **Conditional production:** catches conditional on targets, yards conditional on attempts/catches, with depth, efficiency, zero outcomes, explosive tails, and uncertainty. Passing yards arise from team pass volume and passing efficiency, not a translated QB game-yard distribution. Preserve dependence among teammates, passers/receivers, rush/pass choices, and team script.
4. **Separate touchdown module:** project team offensive touchdowns or scoring chances, then allocate rush and receiving TD opportunities and conversions among competing scorers using inside-the-5 carries, inside-the-10/red-zone targets, QB rushing, and role/league conversion priors. Simulate correlated scorer events; multiple players may score. Match the bookmaker's anytime-TD settlement definition. Never use a player's historical scored-at-least-once frequency as the complete TD model.

These are design requirements, not a mandated distribution family. Negative-binomial team counts, hierarchical beta-binomial role shares, and conditional empirical gains are possible choices if diagnosed and calibrated. A direct mean shift of historical final box scores is a diagnostic baseline at most, never the promoted model.

## Hierarchical priors and changing roles
- Retrieve verified regular-season player/team/league data from prior seasons. Record stable IDs, game coverage, missing games, trades, injuries, teammates, and how zeros or inactive games are treated. Pool comparable positions, teams, or roles through an explicit hierarchy. Determine player-specific prior strength from effective opportunities and estimated between-player variation. Tune recency/continuity and hyperparameters on earlier training folds, never from favorable current prop prices. Do not hard-code exploratory season weights.
- Update current-season target share, rushing share, team volume, goal-line priority, and conditional efficiency separately. A single game produces broad role uncertainty, especially after a team switch, injury, or teammate absence. A structural break may warrant a separately estimated role regime.
- Separate uncertainty about expected role from conditional game variance and model misspecification. Draw role parameters before drawing game opportunities and efficiencies. Report which component most affects the quoted prop probability.
- Opponent rates and injury/weather adjustments must rest on identified samples with shrinkage to league baseline. Avoid double counting effects already absorbed by a market-anchored environment. With no support, use an explicitly neutral adjustment.
- For an unresolved injury or role, specify normal/limited/out regimes with probabilities grounded in cited evidence or clearly labeled assumptions with sensitivity bounds. If plausible regime weights change the decision, PASS; if participation cannot be bounded, DATA_INSUFFICIENT.

## Distribution validation
Freeze the model specification and produce chronological pre-game predictions under the pre-game information guard. Score:
- continuous yards/counts with CRPS (or a suitable log score), PIT/calibration diagnostics, and interval coverage/sharpness, split by market, position, and role-change regime
- TD Yes/No with Brier/log loss and reliability

**Scoring population.** Scores count only prop-eligible player-games. Primary definition: player-games with an archived line in the relevant market. Fallback proxy when no archive covers the period: among players on the team's active roster (`status = ACT` or `INA` on the pre-game weekly roster file) for the target week, pre-game QB1, RB1, RB2, WR1, WR2, WR3, TE1 by depth chart, plus any such player with at least 10% target share or 20% rush share over the prior four games in which they were `ACT`. Players on reserve, practice squad, or otherwise off the active roster for the target week are not in the scoring population for that week regardless of depth-chart history. Scoring a player who was never going to play penalizes the model for failing to predict a roster move that was already public before kickoff.

**Settlement for game-day inactives.** A player who is eligible pre-game but declared `INA` before kickoff is voided from scoring for that week, not scored as 0. Sportsbooks void props for scratched players; scoring them at 0 conflates "targeted zero times" with "did not suit up" and biases role-based models, because inactives are disproportionately players whose usage was already declining. Report the void rate alongside any validation result. Note the consequence: a score computed this way is conditional on the player having played, which mildly favors a model that over-predicts declining players. A score computed on the full roster is not a validation score; roster-tail zeros inflate baseline agreement and hide the error that matters.

Compare against player-history, rolling-utilization, and hierarchical baselines. Disclose sample counts, dependence among observations (player-games within a game are correlated), and the uncertainty of score differences via game-level block bootstrap. Tune on earlier folds; evaluate on a later untouched period. A result from a handful of player-games cannot establish sportsbook calibration.

## Betting validation
Requires the line archive. Replay candidate bets using only pre-game data and the archived bookmaker line/price at a stated decision time. Compare predicted win/push/loss at those lines with outcomes and no-vig same-market probabilities (correctly pairing complementary sides). Measure line-specific calibration, closing-line performance where closing rows exist, and net ROI after offered prices, pushes, and the selection rule. Benchmark against a flat strategy and no-vig consensus. Preserve all candidates and PASS decisions. If archived prices are absent, betting validation is unavailable; never treat an arbitrary historical median, a current quote replayed into the past, or current price alone as proof of edge. A model can pass distribution validation without demonstrating a betting edge.

## Model state
Model state is read from `model_registry.md`. It is never assigned at runtime. If the model being used has no registry entry, or its entry is `PROTOTYPE`, `REJECTED`, or `RETIRED`, the prop is `MODEL_UNVALIDATED`. Only a registry entry at `VALIDATED_DISTRIBUTION` or `VALIDATED_BETTING` can produce `MODEL_VALIDATED, ...` states, and only within the markets listed in that entry.

| State | Evidence | Output |
|---|---|---|
| `MODEL_UNVALIDATED` | No qualifying registry entry, or a required source/role input is missing. | Findings and optional clearly labeled diagnostic estimates; no fair odds or actionable threshold. `DATA_INSUFFICIENT` when even the distribution is indefensible. |
| `MODEL_VALIDATED, EDGE_INSUFFICIENT` | Registry entry at `VALIDATED_DISTRIBUTION` or better for this market; current edge below the edge rule or unstable under sensitivity. | Model probability, uncertainty, fair odds, observed quote, and PASS. If the entry is not `VALIDATED_BETTING`, say betting performance is unvalidated and do not assert +EV. |
| `MODEL_VALIDATED, EDGE_SUFFICIENT` | Registry entry at `VALIDATED_BETTING` for this market; fresh executable quote clears the edge rule and remains clear under plausible scenarios. | Fair odds, exact playable line and maximum juice, observed quote and timestamp, sensitivity, and the line/price at which it becomes PASS. |

Market availability and injury/role gates apply independently: a missing current price or unresolved material role prevents an actionable recommendation even for a validated model.

## Edge rule
Default thresholds, overridable by the user before the analysis starts (never after seeing the quote):
- `p_model` is the modeled probability of the bet winning; `p_novig` is the no-vig probability of the same side from the same bookmaker's complementary pair at the same snapshot (for anytime TD, where no complement is quoted, use the bookmaker's implied probability without vig removal and say so).
- Expected return per unit at the offered American price `A`: `ER = p_win × payout(A) − p_loss`, where `payout(A) = A/100` if `A > 0` else `100/|A|`, and `p_win + p_push + p_loss = 1`.
- A bet is `EDGE_SUFFICIENT` only if all three hold:
  1. `p_model − p_novig ≥ 0.03`
  2. `ER ≥ 0.03` at the offered price
  3. `ER ≥ 0` when `p_win` is replaced by the lower bound of its stated uncertainty interval
- The minimum acceptable price is the American price at which condition 2 binds, given `p_win` and `p_push`.

Recompute the outcome distribution at every alternative line; never move a fair price unchanged across lines. Fair decimal odds for O/U are `1 + p_loss/p_win` (`p_push = 0` for half-integer lines); TD Yes fair decimal odds are `1/p_yes`. Convert to American normally.

## Quote refresh
After a validated candidate clears preliminary gates, refresh its exact event, bookmaker, market, line, price, and `last_update` from the API as close as practical to valuation; record quota headers and archive the rows. A cached development snapshot can diagnose a model but cannot establish a current playable bet. If the refresh fails, preserve the model state, label the quote unavailable with its failure class, and PASS.

## Per-prop disclosure
Show the historical hierarchical baseline and effective sample, current utilization update, team/matchup/injury scenarios, distribution mean/median where meaningful, `p_win/p_push/p_loss` or TD Yes probability with uncertainty, registry entry ID and state, edge-rule arithmetic, and the quote with timestamp. Label VERIFIED DATA, CALCULATED METRIC, MODELING ASSUMPTION, and ANALYTICAL INFERENCE.

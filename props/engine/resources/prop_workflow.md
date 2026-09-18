# Prop Evaluation Workflow

## Required Output

### 1. Matchup Environment & Injury Context
Concise summary of: verified matchup and kickoff (local time and UTC), venue/roof/timezone, timestamped spread and total with bookmaker, derived team implied totals (same bookmaker and snapshot; state the spread sign convention), game-window weather or `closed roof`, roster status changes (INA, new ACT), official offensive-line and secondary concerns, other relevant availability, missing/unresolved inputs.

### 2. Primary Analytical Angles
Discuss only supported angles: opportunity concentration, target/rush competition, goal-line priority, inside-the-5 usage, explosive-play dependence, game-script sensitivity, distributional skew, current injury implications. Distinguish observed facts from inference.

### 3. Actionable Recommendation Table
Use exactly these columns:

| Player | Team | Prop Market | Model (registry ID, state) | Actionable Line & Price | Recommendation | Quant Thesis & Median Divergence |
|---|---|---|---|---|---|---|

Rules:
- `Recommendation` is `Over`, `Under`, `Yes`, or `PASS / DATA_INSUFFICIENT`.
- `Model` shows the registry entry ID and one of `MODEL_UNVALIDATED`, `MODEL_VALIDATED, EDGE_INSUFFICIENT`, `MODEL_VALIDATED, EDGE_SUFFICIENT`. With no registry entry write `none, MODEL_UNVALIDATED`.
- Do not force a minimum number of bets.
- Keep the observed quote separate from the actionable entry threshold.
- For `MODEL_UNVALIDATED`, omit a fair price and threshold; diagnostic estimates may appear labeled exploratory.
- For `EDGE_INSUFFICIENT`, fair odds with uncertainty may appear; the recommendation is PASS.
- Only `EDGE_SUFFICIENT` shows an actionable price, and only after the decision-snapshot refresh.

For each modeled prop include below the table: historical baseline and sample window; current-season opportunity and role update; matchup adjustment or `N/A`; model family, mean/median, uncertainty interval; proposed line; `p_win/p_push/p_loss` or `p_yes`; fair odds; edge-rule arithmetic (`p_model − p_novig`, ER at offered price, ER at lower bound) and the minimum acceptable price; observed quote with bookmaker and `last_update`; integer-line push treatment.

### 4. Evidence & Data Gaps
Source manifest:

| Source | Retrieval Time UTC | Source Update/Market Time | Coverage | Use | Gaps / Notes |
|---|---|---|---|---|---|

Include: calculation assumptions, modeling assumptions, simulation seed/count if used, missing route/charting data, unresolved injury information, missing sportsbook prices, weather uncertainty, quota remaining, archive rows written and where they were saved.

## Recommendation discipline
No recommendation is required. Prefer `PASS` when: line/price missing, unresolved injury materially changes opportunity, role is ambiguous, route-dependent thesis cannot be verified, one-game evidence cannot support a credible distribution, modeled edge is within uncertainty, or the model's registry status does not permit pricing.

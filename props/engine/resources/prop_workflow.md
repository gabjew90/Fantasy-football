# Prop Evaluation Workflow

## Required Output

### 1. Matchup Environment & Injury Context
Concise summary of: verified matchup and kickoff (local time and UTC), venue/roof/timezone, timestamped spread and total with bookmaker, derived team implied totals (same bookmaker and snapshot; state the spread sign convention), game-window weather or `closed roof`, roster status changes (INA, new ACT), official offensive-line and secondary concerns, other relevant availability, missing/unresolved inputs.

### 2. Primary Analytical Angles
Discuss only supported angles: opportunity concentration, target/rush competition, goal-line priority, inside-the-5 usage, explosive-play dependence, game-script sensitivity, distributional skew, current injury implications. Distinguish observed facts from inference.

### 3. Research Table
No recommendations (DECISIONS #142): the board is a research sheet until the settled
record shows the model earning weight beside the book. Use these columns:

| Player | Team | Prop Market | Line & Price (Over / Under) | Our projection (median, p10-p90) | Over: model / book | Line implies | Pays at this price if you expect | Last game | Flags |
|---|---|---|---|---|---|---|---|---|---|

Rules:
- No Over/Under/Yes/PASS call, no fair odds, no entry threshold, no EV, Kelly or stake.
- `Line implies` is the targets or carries per game at which the line is a fair 50/50.
- `Pays at this price if you expect` is the workload at which each side beats its own price
  (vig included), conditional on the model's numbers. It is how much role a view needs,
  not an entry threshold or a pick.
- Keep the observed quote (bookmaker, `last_update`) beside the model's numbers.
- For anytime TD give the model, the market and their blend; no fair odds.

For each line the user asks about include below the table: historical baseline and sample
window; current-season opportunity and role update (last game against earlier weeks, a
back's three jobs); matchup adjustment or `N/A`; model family, median and interval; the
role-shift or teammate flags and what they mean; integer-line push treatment.

### 4. Evidence & Data Gaps
Source manifest:

| Source | Retrieval Time UTC | Source Update/Market Time | Coverage | Use | Gaps / Notes |
|---|---|---|---|---|---|

Include: calculation assumptions, modeling assumptions, simulation seed/count if used, missing route/charting data, unresolved injury information, missing sportsbook prices, weather uncertainty, quota remaining, archive rows written and where they were saved.

## Research discipline
No recommendation is given. Say plainly when a thesis cannot be checked: line/price missing,
unresolved injury, ambiguous role, a route-dependent thesis (no route data), or one game of
evidence. The user's bets go in the journal with their four checklist answers.

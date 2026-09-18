# Research Standard

## 1. Verification and evidence rules

### Zero-hallucination
Do not fabricate or silently estimate: player statistics, route participation, injury status, depth-chart role, sportsbook lines, weather, market prices, probability estimates.

### Current-season anchor and historical priors
Describe observed player production and current role using verified current-season regular-season games played to date. For future game distributions, verified historical seasons may supply statistical priors, subject to `modeling_framework.md`. Label historical observations by season and distinguish them from current role evidence and modeled predictions. An explicit user current-season-only restriction overrides this permission.

### Evidence labels
- **VERIFIED DATA**: directly observed and sourced.
- **CALCULATED METRIC**: reproducibly derived from verified data.
- **MODELING ASSUMPTION**: an explicit model choice required for valuation.
- **ANALYTICAL INFERENCE**: a qualitative interpretation supported by evidence.
- **DATA_INSUFFICIENT**: data cannot support the requested conclusion.
- **PASS**: analysis is possible, but no actionable threshold is sufficiently supported.

## 2. Retrieval protocol
Retrieve data directly in the container. Search snippets, documentation, endpoint existence, or an HTTP success code alone are not proof of usable current data.

For each dataset verify: season, week, teams, game date, schema, coverage, update/retrieval time.

Freeze one input snapshot and record: retrieval time UTC, source URL without credentials, source update time when available, filters, missing fields, reconciliation discrepancies.

## 3. Failure classification
- `EXECUTION_INTERRUPTED`: tool execution ended without an API response or explicit denial
- `NETWORK_ENVIRONMENT_BLOCKED`: an explicit network-policy block (proxy `x-deny-reason: host_not_allowed` or equivalent)
- `DNS_FAILURE`
- `AUTH_FAILURE`: HTTP 401/403 from the API itself
- `QUOTA_EXHAUSTED`: HTTP 429 or `x-requests-remaining: 0`
- `HTTP_ERROR_<status>`
- `ASSET_NOT_FOUND`
- `EMPTY_RESPONSE`
- `SCHEMA_MISMATCH`
- `SOURCE_NOT_YET_PUBLISHED`: asset exists but does not yet contain the required week
- `DATA_INSUFFICIENT`

A failed request in one environment is not proof the source does not exist. Attempt an independent retrieval route where one exists and is permitted; never use another route to bypass a denial.

### Odds API execution recovery
- Use `scripts/odds_client.py` or standard-library `urllib.request` with a finite timeout. Preserve normal proxy, TLS, and permission controls.
- Distinguish an API HTTP response from a tool/execution error. A tool timeout or interrupted execution is `EXECUTION_INTERRUPTED`; it does not prove a bad key, missing subscription access, or unavailable markets. Record the redacted error and failed stage.
- For an execution interruption with no explicit denial, first check whether a complete successful response was already cached under `cache/`. Reuse it rather than re-requesting.
- If no complete response exists, retry the same authorized read-only request at most once. Keep the endpoint, credential, markets, and bookmakers unchanged. Stop if the retry fails.
- Never automatically retry an authentication rejection, permission denial, or quota exhaustion. Do not change network controls or use an alternate route to evade a restriction.
- Resume from successful stages: reuse a verified exact event ID from the current task and request only the failed markets. Revalidate the event if kickoff/team identity is stale or conflicting. Never present cached prices as newly retrieved current prices.
- Cache successful response bodies, retrieval time UTC, credential-free endpoint/parameters, market update times, and `x-requests-remaining`, `x-requests-used`, `x-requests-last`. Exclude credentials from caches, exceptions, logs, and reports. If a response was lost, mark that attempt's quota consumption unknown.
- Report stages separately. An authenticated events response proves event access, not successful odds retrieval. If recovery fails, return `TEST FAILED — <failure class>` and state completed stages, failed stage, attempts, and missing data.
- Do not recommend replacing a key, upgrading a subscription, or changing an allowlist solely because an execution was interrupted.

## 4. Core calculations

### aDOT
`target air yards / targets with recorded air yards`. Report denominator coverage if incomplete.

### Target share
`player eligible targets / team eligible targets`. Use the same eligibility rules in numerator and denominator.

### Rushing share
`player eligible carries / team eligible carries`. State treatment of scrambles and kneels. Default: exclude kneels, include designed QB runs, report scramble treatment explicitly.

### Air-yard share
`player target air yards / team target air yards`

### WOPR
`1.5 × target share + 0.7 × air-yard share`. WOPR is an opportunity-concentration proxy, not first-read share.

### Inside-the-10 / Inside-the-5
Eligible plays beginning at the opponent's 10/5-yard line or closer. Report carries and targets separately.

### Snap share
`player offensive snaps / team offensive snaps`

## 5. Route/charting rules
Snap counts do not establish routes run. If verified route data is unavailable:
- `Routes: N/A — VERIFIED CHARTING UNAVAILABLE`
- `Route Participation: N/A — VERIFIED CHARTING UNAVAILABLE`
- `TPRR: N/A — VERIFIED ROUTE DENOMINATOR UNAVAILABLE`

Never estimate routes as offensive snaps × team dropback rate. If verified play-level participation becomes available, `Pass Snap Share` may be calculated, but it must not be relabeled Route Participation.

## 6. Two-minute usage
PBP may be filtered where `half_seconds_remaining <= 120` to calculate two-minute targets, carries, target share, rush share, air yards, and red-zone opportunities. Do not claim two-minute snap participation without verified player-on-field participation.

## 7. Explosive-play dependence
Define thresholds before calculating. Default: explosive rush = 10+ yards, explosive reception/pass gain = 20+ yards. Report concentration, e.g. share of total yards from the largest 1 to 3 plays.

## 8. Modeling constraints
One game cannot establish a reliable future game-level distribution by itself.

Do not:
- call median per-target gain a future game median
- fit an unjustified precise distribution from one game
- pass a prior-season usage role through unchanged when current team, injury, or role evidence contradicts it
- promote a direct historical box-score mean shift or historical TD Yes frequency to a production opportunity/TD model

### Pre-game information guard
Every input to a prediction for game G must have been knowable before G's kickoff:
- team volume (plays, dropbacks, rush attempts) for G comes from a pre-game estimate built on prior games and the pre-game market, never from G's own play count
- the eligible player set for G comes from the weekly roster (`status = ACT`) and injury report as published before kickoff, never from who actually recorded a stat in G
- role shares for G come from games before G only
- prices for G are those archived at or before the stated decision time

A validation run that violates any of these is leaked and its scores are void.

For every modeled distribution disclose: model family, opportunity assumptions, explosive-play treatment, correlated opportunities, parameter uncertainty, game-script sensitivity, unverifiable assumptions, random seed and simulation count if simulation is used.

If the evidence cannot support a defensible probability estimate, return `DATA_INSUFFICIENT` or `PASS`. Apply `modeling_framework.md` to every modeled probability.

## 9. Pricing and fair-odds rules
For a supported prop provide: exact proposed line, modeled Over/Under probability with uncertainty, fair odds, minimum acceptable offered odds under the edge rule in `modeling_framework.md`, observed sportsbook quote, push treatment for integer lines. Never equate estimated positive edge with high confidence.

## 10. Touchdown props
Evaluate: verified inside-the-5 opportunities, goal-line/inside-the-10 priority, competing scorers, QB rushing, team implied total, offered implied probability.

Do not calculate anytime-TD market hold by summing probabilities across different players, because multiple players can score. A lone Yes quote does not establish market hold.

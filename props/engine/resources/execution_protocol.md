# Execution Protocol

Step order for a full prop evaluation in the Claude container. Replaces the ChatGPT Deep Research protocol; the same methodology now runs as code and tool calls here.

## 1. Resolve the task
Identify: season, week, exact matchup, prop candidates if provided, whether to discover candidates or evaluate supplied props, the user's edge thresholds if they override the defaults in `modeling_framework.md`, and whether this is API validation mode only.

## 2. Verify matchup before player research
Load games.csv, filter to the season/week/teams, confirm away/home, gameday, gametime, stadium, roof. Call Odds API `/events` and match on team names and `commence_time`. Resolve conflicts before proceeding.

## 3. Freeze a snapshot
Record actual retrieval time UTC, URLs retrieved (credential-free), source update timestamps, sportsbook `last_update` times, and weather forecast update/retrieval times. Do not mix later prices with earlier spreads/totals without saying so.

## 4. Retrieve current-season performance
Download PBP and snap counts for the season. For a Week N analysis, current opportunity evidence is Weeks 1 to N-1. Compute the metrics in `research_standard.md` section 4 for the relevant teams and players, with league-wide denominators where needed. Cross-check totals against Sleeper when retrievable; do not block on it.

## 5. Retrieve rosters, injuries, and depth charts independently
A PBP failure must not block roster, injury, depth chart, odds, or weather retrieval. Load roster_weekly for the target week (status ACT/INA), injuries for the target week (practice and report status with `date_modified`), and depth charts. Note the file's latest week; if the target week is absent, say so and treat prior-week rows as provisional.

## 6. Retrieve market data
Use `scripts/odds_client.py --key-file resources/credential.env` (or the env var / user-supplied key if present):
1. `events` (no quota cost); match the exact event ID.
2. Optionally `markets` (1 request) to learn what is open; skip if a cached inventory from this session exists.
3. `odds` for only the needed allowlisted markets, DraftKings and FanDuel, with `--archive`.
4. Record quota headers.
Apply the credential rules in `SKILL.md`. If authentication is unavailable, mark odds `N/A — AUTHENTICATED ODDS ACCESS UNAVAILABLE` and continue with the non-price analysis.

## 7. Weather
Skip for closed roofs. Otherwise verify stadium coordinates/timezone, retrieve the NWS hourly forecast; if it fails, use Open-Meteo. One provider per reported forecast. Apply the >15 mph sustained-wind screen exactly.

## 8. Modeling gate
Before modeling any prop, confirm:
- the player's role is verified enough
- the market price is available
- injury status is sufficiently resolved
- the model in use has a registry entry, and that entry's status permits the intended output
- the pre-game guard holds for every input
- the quote has been refreshed after preliminary candidate selection and archived as `decision`

If any fails, the prop is `PASS` or `DATA_INSUFFICIENT`. Do not manufacture probabilities to populate the table.

## 9. Output
Follow `prop_workflow.md`. End with a source manifest containing only sources actually retrieved. Present the archive file (or confirm the push) and any registry change as files.

## Order of operations for a bare API test
Steps 1, 2, 6 only. Report per `SKILL.md` API validation mode.

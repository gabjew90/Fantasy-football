# Data Source Matrix

All retrieval runs in the container. Download nflverse CSVs with `curl -sL` (GitHub release assets redirect) and load with pandas. Record retrieval time UTC for every asset.

## A. Schedule and matchup identity
Primary: nflverse games
`https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv`

Verify: season, game_type, week, gameday, away/home teams, gametime, stadium, roof, surface. Cross-check against the Sleeper `game_id` grouping (team codes) or, under `--source oddsapi`, The Odds API event listing (team names and `commence_time`). Never substitute a similarly named matchup from another season.

## B. Play-by-play
Primary: `https://github.com/nflverse/nflverse-data/releases/download/pbp/play_by_play_{season}.csv`

Filter: season, `game_type = REG`, games played to date, exact teams/weeks. Use league-wide data for denominators. If the asset exists but lacks the required week, classify `SOURCE_NOT_YET_PUBLISHED` (nflverse typically publishes within a day of the game).

## C. Snap counts
Primary: `https://github.com/nflverse/nflverse-data/releases/download/snap_counts/snap_counts_{season}.csv`

Snap counts support offensive snap totals and snap share only.

## D. Weekly rosters and inactives
Primary: `https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_{season}.csv`

Columns of interest: `season, week, team, position, full_name, gsis_id, status`. `status` values include `ACT` (active), `INA` (inactive), `RES` (reserve), `CUT`, `DEV`, `EXE`, `RET`. The upcoming week's row set is the pre-game eligible player universe. Treat a week's rows as provisional until the day of the game; final inactives are announced 90 minutes before kickoff and may post-date the file. Use `gsis_id` as the join key to PBP.

## E. Depth charts
Primary: `https://github.com/nflverse/nflverse-data/releases/download/depth_charts/depth_charts_{season}.csv`

Use for role ordering (RB1/RB2, WR1..WR3, TE1) and for the prop-eligibility proxy in `modeling_framework.md`. Depth charts are team-published and can lag; do not treat them as usage evidence.

## F. Official injuries
Primary: `https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_{season}.csv`

Separates `practice_status` (Did Not Participate / Limited / Full) from `report_status` (Out / Doubtful / Questionable), with `date_modified`. Record report date and whether participation is actual or estimated.

Cross-check against the official NFL injury page `https://www.nfl.com/injuries/` when the nflverse file lags or a status is ambiguous. ESPN `https://site.api.espn.com/apis/site/v2/sports/football/nfl/injuries` is discovery/cross-check only. Official reporting takes precedence over aggregators.

## G. Player identity
Primary crosswalk: `https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv`

Use `gsis_id` across nflverse assets. Use the crosswalk to map Odds API `description` (player display name) to `gsis_id`; resolve name collisions by team and position, never by name alone.

## H. Historical model priors
For future distributions, retrieve prior-season PBP and snap counts independently of current-season usage, normally the two prior seasons, from the same release paths with the season substituted.

Verify asset availability, game count, identity, team/role continuity, completeness, and postseason exclusion at retrieval. State whether opponent defensive rates, league conversion rates, and same-team/same-role comparables were actually retrieved. Do not treat unavailable data as zero or quietly reuse stale team roles.

For betting validation, use only the line archive defined in `line_archive.md`. If no archived prices cover the test period, label archived-market calibration, closing-line value, and realized ROI unavailable. Do not use player medians as substitutes for sportsbook-line validation.

## I. Box-score cross-check
Secondary: Sleeper `https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}` (also reachable via `api.sleeper.com/stats/nfl/{season}/{week}?season_type=regular`). Undocumented. Validate the response, do not treat missing keys as zero, report discrepancies, do not make Sleeper a blocking dependency.

## J. Sportsbook odds and props
Primary (since 2026-09-17): Sleeper Picks. `https://api.sleeper.app/lines/available?dynamic=true` returns the whole multi-sport board (~3,600 lines, ~0.3 s, no key, no quota); filter `sport == "nfl"`, `line_type == "normal"`, `game_status == "pre_game"`, `wager_type` in receptions / receiving_yards / rushing_yards / anytime_touchdowns (the allowlist; passing markets exist but are unmodeled). Players resolve by `subject_id` through `https://api.sleeper.app/v1/players/nfl` (12k rows, cache for a day; `gsis_id` is mostly missing, so join by full name via `norm_name` / `name_key_loose`). Team codes match nflverse except the Rams (`LAR`). Prices are payout multipliers on a pick'em product (2+ leg entries, ~12% overround per leg); convert to American (1.78 → -128). Anytime TD is two-sided (over = scores, under = does not), so de-vig it like an O/U line. Each option carries `subject_pos_rank` (Sleeper's WR1/TE2 rank), retained as a cross-check on the eligible set. Archive rows use bookmaker `sleeper` so closing-line value grades against a Sleeper close. Not a sportsbook: EV at Sleeper prices is lower than at DK/FD for the same line, and the numbers cannot be placed as a single straight bet there.

Fallback: The Odds API v4 (DK/FD plus consensus books), used automatically only when Sleeper has no lines for the event and `--no-oddsapi-fallback` is not set, or first under `--source oddsapi`. Base `https://api.the-odds-api.com/v4/sports/americanfootball_nfl`
- Events: `{base}/events` (no quota cost)
- Event markets: `{base}/events/{eventId}/markets?regions=us` (1 request)
- Event odds: `{base}/events/{eventId}/odds?regions=us&markets=...&oddsFormat=american&bookmakers=draftkings,fanduel` (cost = number of markets requested)

When `ODDS_API_PROXY_BASE_URL` is set, the same three stages are `{BASE}/events`, `{BASE}/markets?eventId=...`, `{BASE}/odds?eventId=...&markets=...`.

Credential lookup order is defined in `SKILL.md`; in production the bundled `resources/credential.env` is used via `odds_client.py --key-file`. Authenticated access must be proven by an actual successful request.

Request only the markets on the allowlist in `SKILL.md` unless the user expands it. Prefer DraftKings and FanDuel. Preserve bookmaker, market, player (`description`), outcome name, line (`point`), American price, and market `last_update`.

Capture on every response: `x-requests-remaining`, `x-requests-used`, `x-requests-last`. Free tier is 500 requests per month; a full allowlist pull for one event costs 8. Cache successful responses under `cache/` and avoid redundant inventory calls.

If safe authenticated access is not available: `N/A — AUTHENTICATED ODDS ACCESS UNAVAILABLE`.

## K. Weather
Primary: NWS `https://api.weather.gov/points/{latitude},{longitude}` then follow `forecastHourly`. Send a `User-Agent` header.

Fallback: Open-Meteo `https://api.open-meteo.com/v1/forecast` with verified stadium latitude/longitude, `hourly=temperature_2m,wind_speed_10m,wind_gusts_10m,precipitation_probability`, `temperature_unit=fahrenheit`, `wind_speed_unit=mph`, stadium-local `timezone`, and a horizon covering the game.

Report one provider's internally consistent game-window forecast: temperature, sustained wind, gusts if available, precipitation probability, retrieval time, forecast update time when exposed. Do not mix providers. Weather is a forecast, not certainty. Skip weather for closed-roof venues (games.csv `roof = closed` or `dome`) and say so.

Wind screen: apply passing-impact screening only when sustained wind exceeds 15 mph. Gusts alone do not satisfy the threshold. Do not invent a numerical passing downgrade.

## L. Persistence
The container resets between chats. GitHub (`api.github.com`) is on the allowlist and is the intended durable store for the line archive and registry when the user supplies a repository and token via `GITHUB_TOKEN`. Absent that, write outputs to `/mnt/user-data/outputs/` and present them so the user can save them. See `line_archive.md`.

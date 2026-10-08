# Line Archive

Betting validation is impossible without archived prices. Every price retrieval (Sleeper Picks or The Odds API) writes archive rows, with the bookmaker field naming the source. This is not optional and does not depend on whether the retrieval was for a test or a real evaluation.

## Record format
One row per outcome, JSON Lines, file `line_archive_nfl_{season}.jsonl`:

```
retrieved_at_utc, snapshot_type, season, week, event_id, commence_time, home_team, away_team,
bookmaker, market, player, outcome, point, price_american, last_update,
requests_remaining, requests_used, requests_last, source
```

- `snapshot_type`: the scheduled capture (`props/guard.py`) records three kinds -- `open` (the Thursday-evening sweep, once per week), `decision` (a capture inside 6 hours of a kickoff) and `close` (inside the final 60 minutes); each recorded call in `props/record/predictions/` carries its kind. Assign at write time; never relabel later. Known gap: the scorer stamps every row of its own archive JSONL `decision`, and `props/record_run.py` only fills a missing type, so the line record (`props/record/lines/`) currently reads `decision` on every row; the predictions rows hold the true kind. A direct `odds_client.py --archive` pull uses its own labels (`opening`, `decision`, `closing`, `interim`; default `interim`).
- `player` is the book's player name (the Odds API `description`, or Sleeper's player name; null for spreads/totals); `outcome` is `Over`/`Under`/`Yes`/team name.
- `source` is `sleeper_lines_available` for Sleeper Picks rows, `odds_api` or `proxy` for The Odds API.
- No key, no credential-bearing URL, in any row.

`score_game.py` writes these rows for every Sleeper pull; `scripts/odds_client.py` writes them when `--archive` is passed.

## Capture cadence
The scheduled props workflow (`.github/workflows/props.yml`, ticking every 15 minutes) captures every game: the Thursday `open` sweep, `decision` snapshots inside 6 hours of kickoff, and the `close` inside the final 60 minutes. Chat does not capture for the record. Actions cron can fire late, so a game may have no `close` row; then closing-line value for it is `unavailable`, not estimated.

Budget: Sleeper Picks is the primary price source and costs nothing (no key, no quota). The Odds API is a fallback only (8 requests for a full pull of one event on the 500/month free tier) and, for `--compare-books`, about 4 credits a game, never below 100 remaining. State remaining quota after any Odds API capture.

## Persistence
The scheduled workflow archives: it runs `props/record_run.py` on the capture's outputs and commits `props/record/` (lines, predictions, settled rows, the scorecard). Chat is read-only (CHAT.md): it never commits, pushes or passes `--record`, and a chat run's `line_archive_nfl_{season}.jsonl` in `/mnt/user-data/outputs/` is a reference copy, attached only when the user asks. `--prior-archive` still merges a previous file into a run, de-duplicating on `(event_id, bookmaker, market, player, outcome, point, last_update)`. `odds_client.py` still carries a `GITHUB_TOKEN` / `LINE_ARCHIVE_REPO` push; chat does not use it.

Never claim an archive row exists that the record does not hold.

## Use in validation
Only rows with `snapshot_type` in `{open, decision, close}` (direct Odds API pulls: `{opening, decision, closing}`) at or before the stated decision time are eligible for betting replay. `interim` rows may be used for line-movement description only.

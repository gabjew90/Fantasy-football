# Line Archive

Betting validation is impossible without archived prices. Every price retrieval (Sleeper Picks or The Odds API) writes archive rows, with the bookmaker field naming the source. This is not optional and does not depend on whether the retrieval was for a test or a real evaluation.

## Record format
One row per outcome, JSON Lines, file `line_archive_nfl_{season}.jsonl`:

```
retrieved_at_utc, snapshot_type, season, week, event_id, commence_time, home_team, away_team,
bookmaker, market, player, outcome, point, price_american, last_update,
requests_remaining, requests_used, requests_last, source
```

- `snapshot_type`: `opening` (first capture for the event), `decision` (capture at the time a recommendation is made), `closing` (capture within 60 minutes before `commence_time`), or `interim`. Assign at write time; never relabel later.
- `player` is the API `description` field (null for spreads/totals); `outcome` is `Over`/`Under`/`Yes`/team name.
- `source` is `odds_api` or `proxy`.
- No key, no credential-bearing URL, in any row.

`scripts/odds_client.py` writes these rows automatically when `--archive` is passed.

## Capture cadence
For any event under evaluation:
1. Opening: on first retrieval.
2. Decision: immediately before any recommendation table is finalized (this is the mandatory quote refresh).
3. Closing: the user must trigger a chat within the hour before kickoff, since the container cannot schedule itself. Prompt the user once per evaluated event about the closing capture time in local time. If no closing row exists, closing-line value for that event is `unavailable`, not estimated.

Budget: each capture of the eight allowlisted markets for one event costs 8 requests. On the 500/month free tier, three captures per event supports about 20 events per month. State remaining quota after every capture.

## Persistence
The container resets between chats, so the archive must leave the container every session:
- Preferred: when `GITHUB_TOKEN` and `LINE_ARCHIVE_REPO` (`owner/repo`) are set, `odds_client.py --archive` appends rows to the repo file via the Contents API (`api.github.com` is on the allowlist). At session start, pull the existing archive from the repo before appending.
- Fallback: write the session's rows to `/mnt/user-data/outputs/line_archive_nfl_{season}.jsonl` and present the file. The user re-uploads or merges it. When a prior archive is uploaded, load it first and de-duplicate on `(event_id, bookmaker, market, player, outcome, point, last_update)` before appending.

Never claim an archive exists that was not written and presented or pushed in that session.

## Use in validation
Only rows with `snapshot_type` in `{opening, decision, closing}` at or before the stated decision time are eligible for betting replay. `interim` rows may be used for line-movement description only.

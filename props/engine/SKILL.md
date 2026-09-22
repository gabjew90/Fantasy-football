---
name: nfl-prop-research
description: Quantitative NFL sportsbook player-prop research for the NFL Gambling Project. Use when the user asks to evaluate, price, or find edges on NFL player props (passing/rushing/receiving yards, receptions, passing TDs, anytime TD) or game spreads/totals, wants fair odds or line-and-price thresholds, asks to test The Odds API connection, or asks to archive lines or validate a prop model. Retrieves nflverse play-by-play, snaps, weekly rosters, injuries, depth charts, The Odds API prices, and NWS/Open-Meteo weather in the container. Not for fantasy football start/sit, waiver, trade, or draft decisions.
---

# NFL Prop Research

## Purpose
Evaluate NFL player props using verified evidence, reproducible calculations, and explicit uncertainty. Do not force bets. If the evidence cannot support a defensible probability or threshold, return `PASS` or `DATA_INSUFFICIENT`.

## Scope boundary
This skill owns sportsbook decisions only: prop market evaluation, Over/Under valuation, fair odds, line-and-price thresholds, TD-prop evaluation, line archiving, and model validation.

It does not own fantasy football decisions (start/sit, waivers, trades, draft). If a request is primarily a fantasy decision, do not apply this skill's betting framing to it. If a request contains both, answer the sportsbook portion with this skill and the fantasy portion separately, and keep the outputs distinct even when they share evidence. Do not replace fantasy roster logic with betting-market logic.

## Required resources
Always apply:
- `resources/research_standard.md` (evidence rules, failure classes, calculations)
- `resources/data_source_matrix.md` (sources, endpoints, credential lookup)
- `resources/execution_protocol.md` (step order for a full evaluation in this container)
- `resources/prop_workflow.md` (required output structure)
- `resources/methodology.md` (versioned reference for how the numbers are built; keep the parameter table current when any constant changes)

For any modeled probability, fair odds, or entry threshold, also apply:
- `resources/modeling_framework.md`
- `resources/model_registry.md` (the only source of model state)

For any sportsbook price retrieval, also apply:
- `resources/line_archive.md`

Helpers in `scripts/`:
- `score_game.py` — the main entry point for evaluating one upcoming game end to end.
  `python scripts/score_game.py --away DET --home BUF [--season Y] [--week N]
   [--prior-archive FILE] [--prior-log FILE] [--books all] [--no-odds]`
  It verifies the matchup against games.csv, fetches only the current season's
  play-by-play/rosters/injuries/depth charts/snaps, applies the bundled prior-season
  tables, pulls and archives a `decision` quote, and writes a report, an archive JSONL,
  a shadow log and a consensus-outlier CSV to `/mnt/user-data/outputs`.
- `score_week.py` — the entry point for any SLATE question ("all the week 2 games",
  "one pick per game", "what's on the board this week").
  `python scripts/score_week.py --season Y --week N [--games A@B,C@D] [--skip-started]`
  Runs `score_game.py` for every game off ONE shared workdir (nflverse files, the Sleeper
  lines pull, the Sleeper player table and the ESPN scoreboard are fetched once; ~2-3 s per
  game after the first), tolerates per-game failures, then writes `slate_summary_*.md`
  (the chat deliverable for slate questions; carries the runs table, the one-pick-per-game
  table, the slate-wide pick, the STRONG **and** MODERATE card, a computed per-game trust
  table and the calibration note, so the chat reply is a copy of the file and nothing is
  assembled by hand), `slate_survival_*.csv` (one must-win pick per game, rule below),
  `slate_card_*.csv` (every card row, sorted tier then backtested market then EV) and
  `slate_runs_*.csv`. A 16-game week takes about 45 s cold.
- `odds_client.py` — Odds API stages, header capture, caching, archive rows. Never prints
  the key. Prefer it over ad hoc curl.
- `build_priors.py` — OFFSEASON ONLY. Rebuilds `resources/priors_{season}_*` from a
  completed season, including the opponent efficiency table, team-volume dispersion,
  league pass rate/plays, and per-rate shrinkage constants (K0 tuned on a held-out fold).
  Do not run this during a normal evaluation; the tables are bundled.
- `model.py` — the shared model core (team environment incl. market-anchoring, opponent
  adjustment, per-rate shrinkage, TD allocation, joint-simulation primitives). Both
  `score_game.py` and `backtest.py` import this so the model that gets validated is the
  model that gets used. Never edit the model in `score_game.py` alone.
- `backtest.py` — OFFSEASON / VALIDATION ONLY. Walk-forward CRPS backtest of `model.py`
  against a completed season. Run this after any change to `model.py` before trusting the
  change; do not run it during a normal evaluation.

## Bundled prior-season tables
`resources/priors_{season}_players.csv`, `_slots.csv`, `_teams.csv`, `_roles.csv` and
`_params.json` hold prior-season per-player rates, per-slot league priors, per-team volumes,
dispersion fits, the per-catch Gamma shape, the empirical carry-yardage residual grid, and
the league TD-per-point constant. A live run reads these instead of reprocessing a ~100 MB
play-by-play file. They change once per offseason.

## Team environment and opponent adjustment (rounds 5-6, TD anchor round 10)
Team volume (throws, runs) comes from the team's own history blend by default. Team
TOUCHDOWN totals are anchored to the market by default: implied points from the same-book
spread/total times the league TD-per-point rate, keeping the history blend's pass/rush
split. Reason: at 20% week weight one blowout swings a history-blended TD total by a full
touchdown (CHI week 2: 2.76 avg, 8 TDs in week 1, blend 3.8 vs market-implied 2.74), and
that single number drives every player's anytime-TD probability. When the spread/total
cannot be fetched, TD totals fall back to history and TD calls are capped at MODERATE. A market-anchored
environment (`--env market`) exists but is OFF: a paired backtest on 2025 found no CRPS
difference versus history (the first version of this note claimed otherwise; that was a
misreading and is withdrawn). Opponent efficiency runs at the team level with fixed
shrinkage (k0=150 plays) and measurably improves reception-yards accuracy. An earlier
claim that it was harmful came from a yards-per-completion vs yards-per-target bug in the
league reference, now fixed; see `model_registry.md` round-7 correction. Position-group
level remains too thin to use. Shares are shrunk in opportunity units with per-rate constants.
Players on a team are simulated jointly (one team-volume draw, multinomial split), so
teammate outcomes are correlated; same-game-parlay numbers built from that are
unvalidated and parlay pricing is therefore gated off in the scorer. See
`model_registry.md`, `receiving_hier_v2`.

## Early-season prior extension
Before roughly week 5, current-season evidence is too thin to establish a role on its own.
In that regime the scorer uses each player's prior-season rate as an individual prior,
shrunk toward the slot prior by games played, then blends that toward current-season
observation with `K0`. Two guards apply: a player who changed teams has the weight of his
individual prior capped (his old role is weak evidence for his new one), and his projected
share is rescaled by the ratio of current to prior snap share when both are available.
**This blended form is not what the 2025 backtest validated.** It is an extension, and
output produced under it is exploratory even for `receiving_hier_v1`.

## Persistence between invocations
The container resets, so the archive and the decision log must leave each run and come back
to the next one. Either pass the previous files back in with `--prior-archive` and
`--prior-log` (the scorer de-duplicates and appends), or set `GITHUB_TOKEN` and
`LINE_ARCHIVE_REPO` so `odds_client.py` pushes archive rows to a repo. If neither is done,
each run's archive stands alone and closing-line value cannot be computed later.

If the returned archive is older than the current week, report `ARCHIVE_STALE` with the last
capture time rather than implying closing rows exist.

## Closing capture
The container cannot schedule itself. `score_game.py` prints how long until kickoff and, when
more than an hour remains, tells the user to open a chat inside the final 60 minutes and ask
for a closing capture. Without that row, closing-line value for the game is `unavailable` and
must not be estimated.

## Execution environment
This skill runs in the Claude container with `bash_tool` and Python. All retrieval and calculation happens there. Web search is a discovery aid only; it never substitutes for a direct retrieval, and it is never used to fetch prices.

Network allowlist known to work (verified 2026-09-17): github.com and raw.githubusercontent.com (nflverse, DynastyProcess), api.the-odds-api.com, api.weather.gov, api.open-meteo.com, www.nfl.com, site.api.espn.com, api.sleeper.app, api.sleeper.com, api.github.com. A `host_not_allowed` deny reason means the allowlist needs updating; report it as `NETWORK_ENVIRONMENT_BLOCKED` and tell the user, do not conclude the source is gone.

The container resets between chats. Anything that must persist (line archive, model registry updates, cached snapshots) must be written to `/mnt/user-data/outputs/` and presented, or pushed to the user's designated persistent store. See `resources/line_archive.md`.

## Default sportsbook market allowlist
Unless the user explicitly requests additional markets, restrict standard prop research to:
`spreads`, `totals`, `player_pass_yds`, `player_pass_tds`, `player_rush_yds`, `player_reception_yds`, `player_receptions`, `player_anytime_td`.

Do not silently expand into longest-play, first-TD, last-TD, alternate, or multi-TD markets.

## The Odds API credential
Lookup order:
1. Environment variable `ODDS_API_PROXY_BASE_URL` (read-only proxy; raw key stays server-side).
2. Environment variable `ODDS_API_KEY`.
3. A key the user supplies in the conversation (overrides the bundled key for that chat).
4. The bundled file `resources/credential.env` (`ODDS_API_KEY=...`). Pass its path to `scripts/odds_client.py --key-file`. This is the normal production path.
5. Otherwise: `N/A — AUTHENTICATED ODDS ACCESS UNAVAILABLE`.

Price-source order (automatic, default since 2026-09-17): **Sleeper Picks first**
(no key, no quota, ~0.3 s for the whole league's board) → The Odds API only as a fallback
when Sleeper has no lines for the event (spends 8 credits; `--no-oddsapi-fallback`
forbids it) → `--lines-file` (manual entry, explicit only). `--source oddsapi` restores the
old order (Odds API first, Sleeper as fallback) for a DK/FD closing capture when credits
are available. The source table in every report names which one was used. Spread/total:
ESPN scoreboard (carries the DK line; nflverse WAS/LA are mapped to ESPN WSH/LAR) → the
Odds API only under `--source oddsapi`. `--no-odds` disables all of them.

Sleeper specifics the scorer relies on: team codes match nflverse except the Rams
(`LA` → `LAR`, mapped; before the map the Rams' lines were silently dropped); anytime TD is
TWO-SIDED (a "won't score" multiplier is posted), so the TD no-vig strips the hold like an
O/U line instead of treating the Yes price as the market number; `subject_pos_rank`
(Sleeper's own WR1/TE2 rank) is cross-checked against the nflverse depth-chart slot and any
disagreement is logged and shown in the source table (the book's read on a role is the most
common early-season model failure; it is logged, never acted on); the lines pull is cached in the
workdir for `--sleeper-cache-ttl` seconds (default 600, env `SLEEPER_CACHE_TTL`) and the
player table for a day, so slate runs make one pull.

Quota (Odds API, fallback only): each full `--source oddsapi` run spends 8 credits (2 for
spread/total, 6 for the prop pull; a credit is one market-region). The free tier is
500/month, which is why Sleeper is primary. `x-requests-remaining`
is recorded on every call and printed in the source table. When the quota is gone:
- `ODDS_REUSE_CACHE_MAX_AGE=<seconds>` reuses the newest successful cached quote (events and
  odds) for the same event instead of spending a request; the source table says "reused
  cache, N s old". Only useful within one container session.
- `--lines-file lines.csv` (columns player,market,line,over_price,under_price,book; for
  anytime_td put the Yes price in over_price) prices manually entered lines through the
  identical join and card. No archive row is written and CLV cannot be computed for them;
  the card labels the source "manual lines file".
- Spread/total fall back to the ESPN scoreboard (site.api.espn.com, allowlisted, no key),
  which carries the DraftKings line; used for the TD anchor only, never for props.
- `--source sleeper` prices the card from Sleeper Picks (api.sleeper.app/lines/available,
  no key, no quota, allowlisted; verified 2026-09-17). Two-sided lines for receptions,
  receiving yards, rushing yards and anytime TD on most starters, with dynamic payout
  multipliers converted to American odds (1.78 -> -128). Sleeper is a pick'em product
  (2+ leg entries, ~12% overround per leg vs ~4.5% at DK/FD), so EV at Sleeper prices is
  lower for the same line; model % and no-vig % are comparable to a sportsbook's. Rows are
  archived with bookmaker "sleeper" so CLV can be graded against a Sleeper close. Player
  ids are joined by full name through /v1/players/nfl (gsis_id is missing for most rows).
- PrizePicks (api.prizepicks.com) is bot-blocked (DataDome captcha) and publishes lines
  without prices; not usable. ESPN and nfl.com publish no props. A quota failure degrades
  to "no prices this run" and never silently substitutes a scraped page.

The bundled key is a free-tier key the user has chosen to ship with the skill. The handling rules below still apply: it is read by the script, not by the model, and never appears in output.

Handling, regardless of how the key was obtained:
- pass it only as an environment variable or function argument inside the container
- never echo it in command output, cache files, archive rows, reports, citations, or logs
- never place it in a user-visible URL or a web search query
- never quote `resources/credential.env` or cite it as a source

Fetch `/events` first, match the exact event, request only required markets, cache successful responses, and record quota headers. In API validation mode, never substitute sportsbook pages for an API failure.

## API validation mode
When the user asks to test or verify The Odds API connection, market inventory, quota headers, or current authenticated pricing:
- The Odds API itself is the required source.
- Do not replace a failed API call with FanDuel/DraftKings webpage scraping or documentation.
- Before declaring a terminal failure, apply the bounded Odds API execution recovery in `resources/research_standard.md`; report completed and failed stages separately.
- If recovery fails, return `TEST FAILED` plus the precise failure classification.
- A successful test must include actual authenticated response data and quota headers.

## Core behavior
1. Verify the exact matchup, week, venue, kickoff, and timezone before player analysis.
2. Freeze one current input snapshot.
3. Retrieve current-season evidence directly from the defined source hierarchy, in the container.
4. Separate `VERIFIED DATA`, `CALCULATED METRIC`, `MODELING ASSUMPTION`, and `ANALYTICAL INFERENCE`.
5. Never infer source unavailability from a network failure in one execution environment.
6. Never manufacture missing route, injury, weather, or pricing data.
7. Use verified historical seasons as statistical priors for future outcomes when relevant; keep observed current-season utilization and historical priors separately identified. An explicit user restriction to current-season-only evidence overrides historical-prior permission.
8. Do not equate a positive estimated edge with high confidence.
9. Give an Over/Under recommendation only when the line, price, and probability estimate are sufficiently supported.
10. Model state is read from `resources/model_registry.md`, never assigned at runtime. A model with no registry entry, or a registry entry below `VALIDATED`, is `MODEL_UNVALIDATED` for pricing purposes. Only `MODEL_VALIDATED, EDGE_SUFFICIENT` can offer an actionable entry threshold, and only after a fresh quote.
11. Every odds retrieval appends to the line archive per `resources/line_archive.md`.

## Slate questions and the survival pick
When the user asks about more than one game ("evaluate all the week N games", "one pick per
game", "what's the best play this week"), run `score_week.py`, not 16 separate guides. The
chat reply is `slate_summary_*.md`, reproduced in full and in order: the runs table (spread,
total, lines, status), the one-pick-per-game table, the slate-wide single pick, the
STRONG/MODERATE slate card, the per-game trust table, and the calibration note. Every one of
those is computed by the scorer. Do not recompute, re-sort, re-filter or hand-assemble any of
them in the reply, and do not write trust notes from your own reading of the CSVs; if a
section looks wrong, fix `score_week.py` and re-run. Do not reproduce a full per-game guide
unless the user asks about one game.

Card sort is tier, then backtested market (receptions and receiving yards) ahead of rushing
and anytime TD, then EV. Sorting on EV alone floats the two markets with no backtest to the
top of the card, where they read as the best plays on the slate.

Tier filtering uses the BASE tier. Card tiers carry parenthetical annotations
("MODERATE (gap is prior-vs-market: ...)", "STRONG (note: history had this team at ...)"),
so an exact string match on "STRONG"/"MODERATE" silently drops rows.

"Do-or-die" / "must-win" / "if you could only have one bet" is a different objective from
the card and gets a different rule, implemented in `score_week.py` and quoted from
`slate_survival_*.csv`, never hand-picked: receptions and receiving yards only (the
backtested markets); players who changed teams or are Questionable excluded; the book must
agree (no-vig >= 0.55 on the same side); then the highest model probability. Fallbacks in
order: no-vig >= 0.50 calibrated; any market >= 0.50; calibrated with the book disagreeing
(flagged). If no unflagged line qualifies at any tier, the rule re-runs on the full frame and
the pick is marked "role-flagged fallback". The per-game picks and the slate-wide pick apply
the SAME exclusion, so the two scopes cannot disagree about who is eligible. A depth-role
player (RB2/WR3/proxy) can win either and the output names his slot, because excluding him
would be a different objective than "highest probability". Say plainly that
these maximise P(win) at a juiced price and are bad EV in isolation, that Sleeper needs 2+
legs per entry, and that alternate lines two units past the median beat any posted line for
this objective (quote the ladder). Note the 90%+ tail runs ~4 pts optimistic in the 2025
backtest.

## Fast path
For a narrow question, run only what it needs:
- **One game, specific markets:** `python scripts/score_game.py --away NYG --home LA --markets td`
  (markets: `receptions`, `rec_yds`, `rush_yds`, `td`, comma-separated). `--week` is optional and
  resolves to the next meeting; `LAR`, `WSH`, `JAC`, `LVR` are accepted. A `--markets` run prints a
  short summary (also saved as `summary_*.md`) instead of the full report, which is still written.
- **Today's games / one date:** `python scripts/score_week.py --today` or `--date YYYY-MM-DD`
  (`--markets` passes through).
- **Anytime TD:** every priced TD row is also in `td_board_*.csv` (the bet card leaves TD rows out).
  A TD-only run takes DraftKings prices from The Odds API when the cached quota shows 100+ credits,
  otherwise Sleeper; the sources table says which, and so must the reply.
- **Fantasy numbers:** `fantasy_points_*.csv` has median, p20 and p80 per player from the joint
  simulation (`--fantasy-scoring ppr|half|std|file.json|'rec=0.5,...'`). QB rows are rushing only:
  passing is not modelled.
- **Inside 60 minutes of kickoff** the report flags a candidate closing snapshot; say so in the reply.
  The scheduled capture records the official close.

## Output
Use the exact report structure in `resources/prop_workflow.md`.

Two rules for every reply:
- **State plainly when no row has positive expected value** at the posted prices. The report's first
  line says it; the reply says it in its opening lines, not buried under the tables.
- **Call `present_files` on the report** (`report_*.md`, plus `summary_*.md` for a `--markets` run) so
  the user can open it.

When `score_game.py` has been run, the CHAT REPLY is the deliverable, not the report file.
The archive JSONL and shadow-log CSV are still written (they feed closing-line value) but
need not be surfaced. Write the reply as a premium prop guide with this structure:

1. **Header** — matchup, kickoff, venue/roof. Then the game frame in one block: same-book
   spread and total with implied team totals, weather (temp, wind, rain, and whether the
   15 mph wind screen was hit), injury/inactive summary, and how much current-season data
   the model has. One sentence stating these are model opinions not yet validated
   against sportsbooks.
2. **How the game projects** — each team's projected throws, runs, and offensive TDs,
   and where those came from (history blend, market re-centre if used, league drift
   correction if active).
3. **The matchup** — each defense's efficiency allowed vs league (catch rate, yards per
   target, yards per carry, with sample size) and the multiplier applied to the opposing
   receivers/rushers. State plainly if the effect is small.
4. **Per team, starters in depth-chart order** (QB1, RB1, WR1, WR2, TE1, WR3; RB2/proxy
   only if they have a play). Each: a bold call block first, written as if-then rules
   ("UNDER 7.5 catches — Under from 7.5, Over from 6.5"; "TD YES at +100 — take Yes at
   -120 or longer"; "no play at 87.5 — Under from 90.5, Over from 82.5"). Then the
   rationale: last-season share and games, this season's count, blended median
   projection, the goal-line share behind any TD call, the opponent multiplier if it
   moved the number, and any Watch flag (new team, Questionable, snap scaling, or a
   book-far-from-us gap that means the book likely knows something).
   **Questionable players: give both cases, pick neither.** Every number in the run is
   priced as if a Questionable player PLAYS his normal role (no discount). The report's
   "If a Questionable player is out" section prices the same lines with him OUT and his
   share handed to his teammates. Show both numbers side by side for every line that
   moves, and state that his own props void if he sits. Do not weight the two cases by a
   guess at whether he plays and do not recommend one: the user decides.
5. **Bet card** — reproduce `bet_card_*.csv` as ONE table, sorted tier then EV: Tier,
   Player, Prop, Line, Book, Odds, Model %, No-vig %, Edge (pts), EV per $100, Kelly,
   Backtest hit rate for that probability bucket (receptions/rec yds only), Correlated with,
   Note. One row per (player, prop, side) at the best price across books; the best
   available line is in the CSV. Tiers: STRONG = stable role and edge at or above the floor
   (6 pts; TD props use relative edge >= 25% of the book's number); LEAN = stable but under
   the floor, no bet; WEAK = new team, Questionable, or gap over 15 pts, treat as the book
   knowing something. Do not hand-compute any of these numbers in the reply; quote the CSV.
   Write the no-vig as the probability of the SAME side as the call, never the other side.
   Then the exposure lines from `exposure_*.csv`: each team-volume thesis ("BUF throws low"),
   how many legs ride on it, and P(all bettable legs hit) from the joint sim vs the
   independent product. State that same-player props are one bet, not two.
   For anytime-TD calls, the model is `anytime_td_v1` (PROTOTYPE; see
   `resources/model_registry.md`). State each team's expected offensive touchdowns and
   the player's share of each, and say which model priced the row: the `td_model` column
   reads `anytime_td_v1`, or `anytime_td_v0` when v1 could not run (no market implied
   total). When the row is `anytime_td_v0`, say it is the fallback and that it runs about
   1.3 points low on average, so a gap in the book's favour is partly the model's. Most
   anytime markets are one-way (no "won't score" side except at Sleeper), so the book's
   number still carries its hold and is biased against the bet; say so with any TD gap.
   Give NO fair odds and NO "take Yes at +X" threshold for any anytime TD: v1 is
   outcome-backtested but untested against posted lines. Its known weak spot is a player
   in a NEW role -- a newly arrived starter, especially a running quarterback -- where one
   game of evidence and a backup's prior leave the book far better informed; say so when
   the gap is on such a player.
   Calibration: say plainly that NO market is validated against sportsbook lines.
   `resources/calibration_2025.csv` is a distributional self-check, not a track record:
   it places lines at fixed offsets from the model's own median, over every player-week
   rather than the ones worth betting, and reuses each player-week 8-10 times so its `n`
   column overstates the evidence by about an order of magnitude. Quote it only with that
   description attached. Rushing and TD have no backtest at all; say so.
   Ladder: `ladder_*.csv` holds P(stat <= k) per player for pricing alternate lines;
   surface it for the top two or three plays when the book's line sits inside the ladder.
6. **Parlays — DISABLED, do not price them.** `parlays_*.csv` is no longer written.
   The simulation does induce real within-team correlation, which is exactly why a
   parlay number built from it reads as authoritative, but the joint distribution has
   never been checked against realised joint outcomes: the backtest scores each market
   marginally and never looks at pairs. A correlation factor wrong in the second decimal
   turns a +450 fair price into a losing bet, and marginal CRPS cannot detect that. If
   asked for a parlay, say it is gated pending a joint-outcome holdout and give the
   single legs instead.
7. **Board summary** — plays count and Under/Over split, and the one-line note that the
   Under lean is unresolved until logged results settle it. Engineering notes (scorer
   changes, repackaging questions) never go in the report or the card; raise them in a
   separate paragraph after the guide, or not at all.

The shadow log carries a `tier` column so WEAK-tier calls are graded as their own bucket
at the week-8 review (do they hit at the model's rate or the book's?).

Prose and short bullet blocks are fine; no per-row PASS language; exploratory status is
stated once in the header, not repeated per line.
The scorer retrieves weather itself; do not fetch it separately unless the source table
shows it failed.
Do not collapse these into a shorter table or a bullet summary. The report is written for a
reader who watches football but does not follow betting math; keep its wording. The
technical appendix and the CSV files may be referred to rather than repeated.

## Final checks
Before finalizing:
- exact season/week/matchup verified against games.csv and the Odds API event
- latest weekly roster status (ACT/INA) and official injury report checked, with report date
- weather is a forecast and timestamped, one provider per reported forecast
- sustained-wind threshold applied correctly
- sportsbook quote has bookmaker, line, price, and update time
- same-book/snapshot spread and total used for team totals
- complementary outcomes used correctly for hold calculations
- no anytime-TD hold calculation by summing different players
- no missing route metric fabricated
- no unsupported future distribution invented from one game
- model state taken from the registry, not self-assigned
- edge rule from `modeling_framework.md` applied with the stated threshold
- any actionable quote refreshed immediately before valuation with source update time and quota headers
- archive rows written for every retrieved market and presented or pushed
- no API key present in output, cache, archive, or logs
- unresolved gaps explicitly disclosed

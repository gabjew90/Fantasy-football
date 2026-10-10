---
name: nfl-prop-research
description: Quantitative NFL sportsbook player-prop research for the NFL Gambling Project. Use when the user asks to evaluate, price, or find edges on NFL player props (receptions, receiving yards, non-QB rushing yards, rushing + receiving yards, passing yards) or game spreads/totals, wants fair odds or line-and-price thresholds, asks to test The Odds API connection, or asks to archive lines or validate a prop model. Retrieves nflverse play-by-play, snaps, weekly rosters, injuries, depth charts, The Odds API prices, and NWS/Open-Meteo weather in the container. Not for fantasy football start/sit, waiver, trade, or draft decisions.
---

# NFL Prop Research

## Purpose
Evaluate NFL player props using verified evidence, reproducible calculations, and explicit uncertainty. Do not force bets. If the evidence cannot support a defensible probability or threshold, return `PASS` or `DATA_INSUFFICIENT`.

## Scope boundary
This skill owns sportsbook decisions only: prop market evaluation, Over/Under valuation, fair odds, line-and-price thresholds, line archiving, and model validation.

**The engine's markets (user, 2026-10-06; DECISIONS #190):** receptions, receiving yards,
non-QB rushing yards, rushing + receiving yards and QB passing yards. **Deferred: QB rushing
yards and anytime touchdowns** -- neither is on the board, and you do not read, quote or
narrate them (the TD notes further down describe the deferred model and apply only if the
user explicitly asks for a TD price, which runs `--markets td`). QB rushing lines are not
priced or recorded at all; anytime TDs are still priced, logged and graded, so the record
keeps measuring them, but they are left off what the user reads. When a report or the user
mentions them, say they are deferred.

It does not own fantasy football decisions (start/sit, waivers, trades, draft). If a request is primarily a fantasy decision, do not apply this skill's betting framing to it. If a request contains both, answer the sportsbook portion with this skill and the fantasy portion separately, and keep the outputs distinct even when they share evidence. Do not replace fantasy roster logic with betting-market logic.

## Required resources
Always apply:
- `resources/research_standard.md` (evidence rules, failure classes, calculations)
- `resources/data_source_matrix.md` (sources, endpoints, credential lookup)
- `resources/execution_protocol.md` (step order for a full evaluation in this container)
- `resources/prop_workflow.md` (required output structure)
- `resources/team_matchup_guide.md` (the user's binding layout and voice for every single-game read's team section)
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
  (the chat deliverable for slate questions; carries the runs table, the research leads
  across the slate -- every receiving role-shift flag with what its line implies -- a
  computed per-game notes table and the calibration note, so the chat reply is a copy of
  the file and nothing is assembled by hand), `slate_research_*.csv` (every priced line's
  research row) and `slate_runs_*.csv`. `slate_card_*.csv` and `parlay_builder_*.csv` are
  still written for the record but are never shown: no picks (DECISIONS #142); the must-win
  pick's `slate_survival_*.csv` is no longer computed (DECISIONS #211). Timing, measured once at props-v1.26 (2026-09-27) and not re-timed since:
  a 15-game week took about 3 minutes on the Windows host (9 before it), about 5 s a game plus a
  full re-run per Questionable player for the 'if he's out' pricing.
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

## Team environment and opponent adjustment (rounds 5-6, TD anchor round 10; market volume rounds 16 and 39)
Team volume (throws, runs) starts from the team's own history blend, then moves part way
toward the market's fitted volume from the same-book spread and total: throws 25% of the way
(model.MARKET_PASS_WEIGHT, round 16, DECISIONS #134) and the backs' carries 50% of the way
(model.MARKET_RUSH_WEIGHT, round 39, DECISIONS #204; the starting QB's carries are held where
history put them). With no spread/total posted, volume stays on history alone. Team
TOUCHDOWN totals are anchored to the market by default: implied points from the same-book
spread/total times the league TD-per-point rate, keeping the history blend's pass/rush
split. Reason: at 20% week weight one blowout swings a history-blended TD total by a full
touchdown (CHI week 2: 2.76 avg, 8 TDs in week 1, blend 3.8 vs market-implied 2.74), and
that single number drives every player's anytime-TD probability. When the spread/total
cannot be fetched, TD totals fall back to history and TD calls are capped at MODERATE. The full
market-anchored environment (`--env market`, plays and pass rate re-centred together) exists but
is OFF: a paired backtest on 2025 found no CRPS difference versus history (the first version of
this note claimed otherwise; that was a misreading and is withdrawn). The partial pass and carry
blends above are what ships. Opponent efficiency runs at the team level with fixed
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
The two-stage blend and the new-team cap are what the 2022-25 harness runs (backtest.py
`--historical-blend` and `--new-team-cap`, both on by default), weeks 2-4 included: the second
expert audit found the early-season blend unbiased in weeks 2-4 and 14-16% better than the
naive baseline on receiving (DECISIONS #198). The snap-share rescaling, weekly depth slots and
pre-game injury handling are not in the harness (reports/current_settings_check_2026-10-06.md).
The live receiving model is `receiving_hier_v2`; its output is exploratory like every price here.

## Persistence between invocations
The record is kept by the scheduled props workflow (`.github/workflows/props.yml`), not by
chat: it scores every game near kickoff, writes the lines and calls to `props/record/` through
`props/record_run.py`, and commits them. Chat is read-only (CHAT.md, "Chat is read-only"): it
never passes `--record`, never commits or pushes, and writes nothing into the repository. A
chat run's archive JSONL and shadow log stay in the outputs folder as reference copies.
`--prior-archive` / `--prior-log` still merge a previous run's files into a new one (the
scorer de-duplicates and appends), and `odds_client.py` still carries a `GITHUB_TOKEN` /
`LINE_ARCHIVE_REPO` push; chat uses neither.

If the returned archive is older than the current week, report `ARCHIVE_STALE` with the last
capture time rather than implying closing rows exist.

## Closing capture
The scheduled capture takes it (`props/guard.py`, ticking every 15 minutes): a Thursday-evening
`open` sweep, `decision` snapshots inside 6 hours of a kickoff, and `close` inside the final 60
minutes. Each recorded call carries its snapshot type (`props/record/predictions/`). Actions
cron can fire late, so a game may have no `close` row; then closing-line value for it is
`unavailable` and must not be estimated. A chat run is never the close: `score_game.py` says how
long until kickoff and, inside 60 minutes, calls its own quote a reference copy.

## Execution environment
This skill runs in the Claude container with `bash_tool` and Python. All retrieval and calculation happens there. Web search is a discovery aid only; it never substitutes for a direct retrieval, and it is never used to fetch prices.

Network allowlist known to work (verified 2026-09-17): github.com and raw.githubusercontent.com (nflverse, DynastyProcess), api.the-odds-api.com, api.weather.gov, api.open-meteo.com, www.nfl.com, site.api.espn.com, api.sleeper.app, api.sleeper.com, api.github.com. A `host_not_allowed` deny reason means the allowlist needs updating; report it as `NETWORK_ENVIRONMENT_BLOCKED` and tell the user, do not conclude the source is gone.

The container resets between chats, and chat persists nothing: the record lives in the repo and only the scheduled workflow writes it (see "Persistence between invocations"). Files in `/mnt/user-data/outputs/` are reference copies; attach none unless the user asks. See `resources/line_archive.md`.

## Default sportsbook market allowlist
Unless the user explicitly requests additional markets, restrict standard prop research to the
engine's markets (DECISIONS #190): `spreads`, `totals`, `player_receptions`,
`player_reception_yds`, `player_rush_yds` (non-QB), `player_rush_reception_yds` (backs and
receivers) and `player_pass_yds` (the starting QB). `player_anytime_td` is deferred: priced,
logged and graded, shown only when the user asks (`--markets td`). `player_pass_tds` is not
priced (`odds_client.py`'s Odds API allowlist still lists it for a direct API pull).

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
  receiving yards, rushing yards, rushing + receiving yards, QB passing yards and anytime TD on most starters, with dynamic payout
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
9. Give no Over/Under recommendation, pick or bet label: the model has not shown it adds anything beside the book's price (DECISIONS #142); the report's first line quotes the current graded record and the label gate (DECISIONS #144). The board is a research sheet; labels return only at a fixed review (after weeks 8, 12 and 18) where the settled record shows, for the current engine version, the model earning weight beside the book AND its top-tier calls making money at Sleeper's recorded prices (DECISIONS #151).
10. Model state is read from `resources/model_registry.md`, never assigned at runtime. A model with no registry entry, or a registry entry below `VALIDATED`, is `MODEL_UNVALIDATED` for pricing purposes. Only `MODEL_VALIDATED, EDGE_SUFFICIENT` can offer an actionable entry threshold, and only after a fresh quote.
11. Every odds retrieval appends to the line archive per `resources/line_archive.md`.

## Slate questions
When the user asks about more than one game ("evaluate all the week N games", "what's on
the board this week"), run `score_week.py`, not 16 separate guides. The chat reply is
`slate_summary_*.md`, reproduced in full and in order: the runs table (spread, total, lines,
status), the research leads across the slate, the notes-by-game table, and the calibration
note. Every one of those is computed by the scorer. Do not recompute, re-sort, re-filter or
hand-assemble any of them in the reply; if a section looks wrong, fix `score_week.py` and
re-run. Do not reproduce a full per-game guide unless the user asks about one game.

"Best play", "one pick per game", "must-win", "if you could only have one bet": there is no
pick. Say why in one sentence (the model has not shown it adds anything beside the book's
price: over weeks 2-4 at Sleeper's real lines its log loss was 0.717 against the market's 0.692,
DECISIONS #202) and offer the research leads and the journal.

## Fast path
**The user never types a command (standing rule, 2026-10-06).** Every flag below is yours to
run from what the user says in plain words; never ask them to type one, and never end a reply
with a command for them to run. Turn their words into the flags yourself: "I think Kamara
gets 12 to 15 carries" is `--assume "Alvin Kamara: carries=12/13.5/15"`; "what if Bijan gets
more work" with no number is `carries=auto`; a report line **No priced replacement for ...**
or **The book's quarterback is not ours** means you rerun with the role what-if yourself and
present that run. What the engine can read for itself (injuries, who starts at QB) it now
decides on its own and says so in the report's first lines -- quote that.

For a narrow question, run only what it needs:
- **One game, specific markets:** `python scripts/score_game.py --away NYG --home LA --markets rec_yds,rush_rec`
  (markets: `receptions`, `rec_yds`, `rush_yds`, `rush_rec`, `pass_yds`; `td` is deferred, comma-separated). `--week` is optional and
  resolves to the next meeting; `LAR`, `WSH`, `JAC`, `LVR` are accepted. A `--markets` run prints a
  short summary (also saved as `summary_*.md`) instead of the full report, which is still written.
- **Your scenario (a what-if on workload):** add `--assume "PLAYER: carries=14"` (or `targets=8`,
  `catch=70%`, `ypt=9`, `ypc=4.5`; a team: `"HOU: pass=-3"`, `rush=+2`, `ypt=-5%`), repeatable. The
  board is priced as usual; the report adds **Your scenario (experimental)**: every line priced again
  with only those inputs changed (teammates give up what one player gains; the team total holds),
  judged against the win rate a Power Play leg needs (DECISIONS #225; a Sleeper pick's own price is
  not its break-even in a flat-payout entry, #208), with the engine's own chance as a reference.
  **Relative to the line** -- `--assume "PLAYER: carries=+2/+4/+6"` (or `targets=+1`) -- reads the
  user's view as more or fewer than the workload his line assumes: prefer it whenever the user
  compares with the line, because it keeps the engine's efficiency error out of the comparison.
  Reproduce that table in full, say the numbers are conditional on the user's assumptions (which are
  assumptions, not confidence intervals), and never call a line a play. Touchdowns are not adjusted.
  Never recorded (outputs in `scenarios/`).
  **A range** -- `--assume "PLAYER: carries=10/12/15"` (low / expected / high, smallest first; team
  changes too, `"NO: pass=-4/-2/+1"`) -- prices the board three times and adds the Over at each end,
  one chance per side averaged over the range (weights 1 : 4 : 1), and a verdict per side against
  the Power Play leg: *pays across your range*, *pays at your expected, not at your low/high*, *pays
  only at your low/high*, or *does not pay in your range*. Prefer a range whenever the user gives a
  rough number: a side that pays across the range does not rest on the exact figure. Narrate the
  verdict with its end named ("the Under needs him at your 15, not your 12"); a teammate's line runs
  the other way across the range.
  **No numbers? `carries=auto` / `targets=auto`** (a player's targets or carries only) builds the
  range itself: our projection plus or minus one standard error of his share over his last 10 games
  (last season's final games top up this season's; this season only after a team change or a
  backfield takeover; needs 3+ games). It measures how sure we are of his AVERAGE, not his
  game-to-game swing, which the price already holds. Quote the three numbers the report prints.
- **Role what-if (a replacement the depth chart has not promoted):** `--role "PLAYER=RB1"` (QB1, RB1,
  RB2, WR1, WR2, WR3, TE1; `"PLAYER (TEAM)=..."` when a name is on both teams), repeatable, with or
  without `--assume`. A full run -- research included -- that prices him with that slot's role average
  as his prior; nobody else moves; never recorded (outputs in `role/`). Run it yourself whenever the
  report says **No priced replacement for ...** (an Out starter whose team now prices fewer players
  at his position than it has slots) or **The book's quarterback is not ours** -- pick the man from
  the depth chart, the book's lines or the news, and say which. A starting QB who is out is handled
  automatically (the next quarterback is priced; DECISIONS #183), so this is for the rest.
- **Today's games / one date:** `python scripts/score_week.py --today` or `--date YYYY-MM-DD`
  (`--markets` passes through). `--kickoff 13:00` keeps one window (Eastern time: 13:00 is the
  10am PT games); `--sort total` orders the games by their total, highest first; `--overs-only`
  shows the Over side only. A slate run writes `slate_board_*.md` -- every game's full research
  table in one file, in that order -- and prints it: for "the props for these games", reproduce it
  in full (never trim rows), then a short read of what stands out per game. A **bold** prop is "worth a look"
  (DECISIONS #156): a role story plus last game's workload already past that side's break-even.
  **How the engine works, with the numbers:** resources/engine_overview.md -- read it when the user
  asks how a projection, share, weight or price is built, and quote its formulas.
  **Rushing + receiving yards is priced (DECISIONS #187):** a back's combined line now has the
  model's Over chance like any yardage line (the sum of his rushing and receiving draws; it
  passed its calibration check on 2022-25). Read it beside his separate rushing and receiving
  lines: the combined leg survives either script, and the report's air share says how much
  of it holds up if his team falls behind.
  **Market carries are live (round 39, DECISIONS #204):** a back's carries take half their
  volume from the market's script (favourites run more, underdogs less); the starting QB's carries
  are held. Each back's card also shows the Over **without** market carries (history alone) --
  graded beside the board for the week-8 reversal check, never the price. Receiving lines log the
  Over at the old target spread (40) the same way (round 34's check).
  **How a single-game read is written (user, 2026-10-06): follow `resources/team_matchup_guide.md`
  EXACTLY for the team section, then the "Player cards" rules for the players.** Read the guide
  before writing any single-game read; it is binding, not a suggestion (user: "just follow it
  exactly"). Written straight into the chat as markdown -- never a PDF or a file. In short:
  - **Order:** header and sources line -> opening thesis (two or three sentences, written after
    the sections) -> 1 the market -> 2 expected volume -> 3 unit performance (scores and tiers) ->
    4 who plays -> 5 production allowed by position -> 6 weather and venue -> 7 where the baseline
    could miss -> 8 expected game flow and what would change it -> the player cards.
  - **The report's "Team matchup" section prints sections 1-7 in that order**: copy every table
    as printed, in order, none skipped (home team first, one number per cell, ranks written
    "21.9 (13th most)"). Under each, one or two short paragraphs (two to four sentences each)
    following the guide's "Required narration" for that section.
  - **You write**: the opening thesis, every narration, and **section 8** -- its table (base
    case, a competitive alternative, the main failure branch, each with both teams'
    opportunities; chosen for THIS matchup, no probabilities) and the handoff to the players.
  - **Section 3**: the unit table and the user's tier caption, no ladder table; compare the
    scores, not just the letters (a C- and a D+ are neighbours).
  - **Voice** (the guide's voice section): observation -> matchup implication -> opportunity
    consequence -> condition that could change it. "The market expects", "Through four games",
    "The engine projects", "My base case". Interpret; never narrate table cells. No jargon, no
    broadcast adjectives ("stingiest", "explosive", "air it out", "feast"); plain "passes".
  - Run the guide's finished-report check before sending.
  - **Tie every player conclusion to his share, the line and the price**; a team read alone is
    never a player call. When the user gives a workload read, set it against the line's
    break-even volume and call a margin under 10% thin.
  **The full story** (user, 2026-10-05; DECISIONS #168) -- what each piece of data means. The
  LAYOUT of a single-game read is the team matchup guide followed by the player cards (above);
  this list is the reference for the content behind them:
  1. **The game.** The matchup and what each team has been, the weather (or roof), home and
     away, the Vegas lines (spread, total, implied points and the script they point to), the
     fantasy points each defence allows to RBs, WRs and TEs (the header's "Fantasy points
     allowed" line: PPR per game and rank -- a small sample this early, context only, never a
     reason on its own), each offence's EPA per play and points per drive gained and each
     defence's allowed (all plays, passes, runs), with their ranks (the header's "Offence" and
     "Defence" lines, 1st = most; read them against each other -- a top-5 passing offence into a
     bottom-5 pass defence; context, never a price input), and the injuries (who is out, questionable, back) -- plus any line
     moves since the morning. Include the **offensive line** (header line, DECISIONS #178): how
     many of each team's five regular linemen (most snaps this season) are out, and who. Context
     for the user to judge -- e.g. two starters out on a run-first team -- never a price change;
     say "status unknown" for an unmatched lineman, and say when no injury report is out yet.
  1b. **Team volume against the season** (the report's "Team volume" section, DECISIONS #172):
     each team's games this season -- score, how much of each game it spent ahead or behind by
     8+, pass attempts, sacks, designed carries, scrambles -- and whether our projected passes
     and runs fit them. Then the script: how teams under a line like this one spent their plays
     (ahead / close / behind), at this team's own pass share in each state, against our split.
     Say plainly when our volume or the script split sits outside every game it has played,
     and name the game whose script matches the Vegas line (a favourite's comfortable win).
  2. **Each player with a priced line**, team by team: his volume and share LAST SEASON, THIS
     SEASON so far, and last game against his earlier games (targets or carries, share and count).
     Then his **matchup** (his "Matchup." line, user 2026-10-06): the PPR points a game the
     defence he faces allows to his position and its rank -- "NYG give up the 10th most PPR
     points to tight ends (14.2 a game, league 13.6)". Say the games behind it while the sample
     is small; it is context, never the reason for a side on its own.
  3. **Teammates out or questionable** who move his work, and which way.
  4. **Expected volume and share, ours and the book's**: our projected targets or carries; the
     book's own volume where it posts it (catches / carries / completions lines, the side favoured,
     and the book's coin-flip number -- "a coin flip at about 19.2", its no-vig price turned into a
     volume with our simulation's game-to-game spread); what each
     yards line works out to ("line implies").
  5. **The lines themselves**: where our projection lands (zone), and the luckless check -- the
     card's "At his luck-capped rate" row (DECISIONS #206-#208): the volume the Over needs at his
     yards a play over his last 10 games with every play past his own 90th percentile capped, and
     the engine's chance of that volume, beside the book's own volume line where posted. For a QB
     the same row is in yards a completion and completions. Then **name the better line for each
     read, catches OR yards, and say why** -- never use the two interchangeably (user,
     2026-10-05). Yards is the better vehicle when the luck-capped row says the yards line takes
     fewer catches than the catches line asks (London, week 4: 82 yards took about 5.4 catches; the
     catches line asked 7); catches
     is better when the yards line takes more than his volume or rests on a long play, or when a
     plus-money catches price makes it the cheaper side. When neither fits, say so.
  6. **If-thens**, one per line of decision, with the losing branch, then **which legs don't mix**.
  A slate (several games) keeps the short per-game preview below; the full story is for one game
  or when the user asks for it.
  **Every game gets a short preview narrative**, in the board's order, BEFORE its bold lines:
  read the game, do not recite the table. Start from the context line under its heading --
  who is favoured and the implied points (the script: a big favourite runs late, an underdog
  throws; a low total with a backup QB plays conservative), and each team's "last week was a
  preview / differs" note. Then each side's situation, with the matchup rank for a player you
  name ("against the 3rd most PPR points to WRs"): the role changes that matter (who took
  over a backfield, whose target share jumped or collapsed, a returning star and who it takes
  from), where the model and the book disagree AND WHY (a stale prior on a new role, a game script
  the model does not price; when the model sits below most QB passing lines, say the gap is
  more likely the model's than the book's -- the backtest measured the engine's passing Over
  about 6 points too low at the main line (DECISIONS #196), round 38 removed most of that but
  not all at the extremes of implied points (DECISIONS #199), and at Sleeper's real lines over
  weeks 2-4, priced before round 38, passing Overs hit 57% against an engine 42% (DECISIONS #202)), and
  what to watch. A game with nothing to find says so in a sentence. Never call a line a bet.
  **Write for a reader without the table** (user, 2026-10-05). The narrative is read on its own,
  often on a phone after the table has scrolled away: every line it discusses names the player,
  the prop, the line, the side, and the number that decides it ("Kamara rushing yards, Over
  36.5: he needs about 14 carries; the model gives him 12"). Never point at the table ("see the
  row", "the zone above", "as the table shows"). That is not reciting the table: quote the one or
  two numbers the decision turns on, interpret the rest.
  **Spell out the if-then.** Every story ends in decisions the reader can act on, one per line,
  each in the form "If <a condition he can check or a belief he holds>, then <the leg that fits:
  player, prop, side, line> -- <what it needs>; if not, <skip it / the alternative>". Conditions
  are observable before entry (the inactives list, a confirmed starter, a line move) or plainly a
  belief ("if you think the Saints throw like they have all season"). Give the losing branch
  too, and say which conditions are the same game script so legs that need opposite scripts
  never share an entry. Close with **"Don't mix"**: list only the pairs of legs that conflict,
  each with its reason (two backs splitting one team's carries; one team running out the clock
  vs the same team throwing; a WR1's target spike vs the WR2 it came from), plus any pair that
  mixes only under a stated script; then one line saying everything else mixes (user,
  2026-10-05 -- a full mix matrix was noise; earlier, separate groups with no verdict read as
  "don't combine"). Say when how strongly two legs move together is
  judgment: the joint model is unchecked against real games and the what-if tool holds team
  totals fixed. These are conditional on the reader's view, never picks: no "take",
  "hammer", "best bet", and no ranking by expected profit.
  **Explore absences unprompted.** For every questionable or doubtful player with a role -- the
  rows' "<name> (<pos>) questionable" flags and the report's "Questionable, not priced here"
  line, which lists players the board does not price -- say who absorbs his work if he sits
  (his position first: a TE2 out nudges the TE1's targets; a back out nudges the other backs'
  carries), which lines that moves and in which direction, and that the inactives list (about
  90 minutes before kickoff) decides it. Quantify it with a what-if on the beneficiary
  (`--assume "<TE1>: targets=<his usual + about half the absent player's>"`) or, for a priced
  player, the report's "If a Questionable player is out" section. A leg that depends on the
  status is a leg to place only once the status is known.
  The research table's "A Power Play leg needs" cell (DECISIONS #225; it replaced the single-pick
  "pays at this price" cell, since in a Power Play the listed price does not apply) gives the
  workload above which the Over clears a leg's win rate -- about 56% for 4 picks at 10x, 55% for
  5 at 20x, whichever side, so a plus-money Under is no cheaper there than any other leg -- and at
  or below which the Under does; between them neither side is worth a leg. The cell says how far
  apart the two sit: about one pass or carry apart is finer than anyone can forecast, so build no
  leg on it (the engine's narrow ranges pull both toward the line for now). How it is found, when asked: the
  simulation moves his share until each side reaches the hurdle. It rests on the model's own
  catch rate and spread, so it guides how much role a view needs; it is not a guarantee.
  **The line-fit reads moved off the card (DECISIONS #208).** The old per-player reads --
  "Catches and yards" (DECISIONS #164), "Carries and yards" (#166), the QB's "Completions and
  yards" (#170), the rushing + receiving touches read (#173) and the achievability gauge that
  ended them -- are now columns in `research_*.csv` (`catch_yards`, `carry_yards`, `qb_yards`,
  `rush_rec`), not report text. On the card, the efficiency rows replace them: the volume the
  Over needs at his luck-capped rate, at his rate this season and at the engine's rate, each with
  the engine's chance of that volume; the efficiency the line needs at the engine's volume and
  his games this season that beat it; and "The book's other lines" (the catches line beside the
  yards line, the carries line and the side its prices favour, the longest-play lines). The
  rules those reads carried still apply when you narrate the card:
  - Lines move in half points, so each Over means the next whole number (3.5 catches = 4, 44.5
    yards = 45; a whole-number line pushes on itself).
  - The book's longest-play line says how much of the yards one play carries; it is the book's
    number only and is not priced here. Narrate the book's lines as its view of how he gets his
    yards, not as a model edge.
  - A back's season yards a carry is mostly noise this early (three games of yards a carry
    predicted later games worse than the league average in 2022-25; reports/robust_ypc_check.md):
    lean on the luck-capped and engine rows for runners. When the line asks about his usual yards
    a carry, his rushing-yards Over is a bet on the carries: say where the book's carries line and
    favoured side sit against the engine's volume (Bijan, week 4: 19.5, Under favoured, engine 17.5).
  - The luck-capped rate reads his last 10 games (crossing into last season while this one is
    short) with every play past his own 90th percentile counted at that value (a strict, luckless
    Over check: a back's cap is about 9 yards); under 10 plays in that window, his longest play
    in the window is left out instead. The card's notes name the games.
  - **Say whose volume each number is.** "The engine projects" is OUR volume, never the book's;
    the market's own volume line sits in its own row. A clear row on a 1-2 catch player is still
    close to a coin flip.
  - A back's combined line survives either script (the catches hold up when his team trails):
    name it when his rushing leg needs a different script from the rest of an entry. A combined
    what-if runs as a separate carry-and-catch scenario (carries, targets, catch rate and both
    yards rates kept apart).
  None of this changes a price.
  Then narrate the bold lines, analytically, in plain English -- interpret, do not recite the
  row's numbers back:
  1. **The story and its direction**: who is out or back, whose role moved, and why that points
     Over or Under for THIS player (a running back's real story is often a teammate in the
     backfield, not the receiver the flag names).
  2. **Does last week transfer?** Each mark ends with the team's note: "last week was a preview:
     same QB, same key absences" (the strongest evidence: last week already showed today's
     situation) or "last week differs: QB change / X newly out / X back" (last week's workload
     was earned in a different situation; say what changes and which way).
  3. **What the price demands**: how far past the break-even last week's workload sits, and
     whether his EARLIER role also clears it (if it does, the read survives even a reversion).
     A target spike without a snap increase is the least sticky kind; snaps and targets rising
     together is the most.
  4. **Which line suits the read**: catches vs yards by price (a −185 side needs 65%), and by
     the read itself (backup-QB volume suits catches over yards; one long play beats a yards Under).
  5. **How it fails**: game script, a teammate's health, efficiency vs volume.
  Close with a ranking of the bold lines by how well the read holds up (strongest / one real
  question / demanding or shaky), then the reminders: Sleeper entries need 2+ picks that each
  stand alone; log any bet in the journal with its angle.
- **Anytime TD:** every priced TD row is also in `td_board_*.csv` (the research table leaves TD rows out).
  A TD-only run takes DraftKings prices from The Odds API when the cached quota shows 100+ credits,
  otherwise Sleeper; the sources table says which, and so must the reply.
- **Fantasy numbers:** `fantasy_points_*.csv` has median, p20 and p80 per player from the joint
  simulation (`--fantasy-scoring ppr|half|std|file.json|'rec=0.5,...'`). QB rows are rushing only:
  passing yards are priced as a prop (below) but not yet scored as fantasy points.
- **Anytime-TD price to quote: the blend.** Every TD row carries `p_model` (anytime_td_v1),
  `p_market` (de-vigged: exact for Sleeper's two-sided prices, a provisional hold removed from one-way
  books) and `p_blend` (layer 4, their logit blend at the PROVISIONAL weight 0.5). Quote all three as
  information; no TD row is a pick. The settled record fits the real weight.
- **Parlays:** none are shown or priced (DECISIONS #142). If asked, say so and give the single legs'
  research rows instead.
- **Other books (opt-in):** `--compare-books` adds DraftKings and FanDuel player lines beside Sleeper's for
  that game (~4 Odds API credits; skipped below 100 credits or with no key, and the sources table says
  which). Their rows are labelled with the book, and "Where the books disagree" compares them. Use it on
  the games the user is researching, not the whole slate.
- **Inside 60 minutes of kickoff** the report flags a candidate closing snapshot; say so in the reply.
  The scheduled capture records the official close.

## Output
Use the exact report structure in `resources/prop_workflow.md`.

Two rules for every reply:
- **Say plainly, in the opening lines, that the board carries no bet labels and why** (the report's
  first line quotes the graded record and the label gate). Never call a
  line a play, a lean, an edge or a value, and quote no EV, Kelly or stake.
- **The reply is the answer; the report is not.** Do not attach or offer the report file
  (`present_files`) unless the user asks for it -- quote what matters from it in the reply.
- **Touchdown pairs:** quote only the report's "Touchdown pairs" section, which renders just the
  parlay classes the committed gate opened (cross-team and teammate pairs today). Both legs are
  PROTOTYPE, so give no fair odds; say how far the pair differs from multiplying its legs. Never
  present `joint_td_*.csv` (all four candidates, shadow) or a three-teammate combination.

When `score_game.py` has been run, the CHAT REPLY is the deliverable, not the report file.
The archive JSONL and shadow-log CSV are still written (reference copies; the record is the
scheduled workflow's) but need not be surfaced. A single-game read has ONE layout: the team
section follows `resources/team_matchup_guide.md` exactly (header and sources line, thesis,
sections 1-8 -- the market, expected volume, unit performance, who plays, production allowed,
weather and venue, where the baseline could miss, game flow; see "How a single-game read is
written" in the fast path), then the player cards. The parts below are the content rules for
the player cards and what follows them, not a second layout. State once, in the header, that
these are model opinions not tested against sportsbook lines.

1. **Per team, starters in depth-chart order** (QB1, RB1, WR1, WR2, TE1, WR3; RB2/proxy
   only if they have a line). Each: the report's player card, laid out and narrated as the
   "Player cards" rules below say. What its tables hold: the prop table (below); the role
   evidence (last game against his earlier games: shares, snaps, a back's three jobs, the
   quarterback); and any Watch flag (new team, Questionable, snap scaling, the
   receiving role-shift flag with its 2022-25 wording, a back's "carries up / down" flag when his
   carry share moved 20+ points last week (reports/rb_takeover_check.md: such backs beat or
   missed the model's carries by about two the next week), a teammate out or back).
   **Player cards (the report's per-player section; one table, user 2026-10-07).** The report
   prints one card per priced player: ONE prop table with a column per priced market (the first
   book's line; other books' lines in a small table under it), then his role evidence (a QB: his
   workload table), the historical baseline, the rate notes, the market-carries shadow for backs,
   Matchup and Watch. The live record and the backtest calibration print ONCE above the cards,
   not per player. The prop table is MARKET FIRST (DECISIONS #225), top to bottom: **the line
   assumes** (the workload the market's no-vig price implies at the engine's efficiency -- the
   line restated as volume: above the engine's volume, the market expects more work, or better
   efficiency, which one price cannot separate), **a Power Play leg needs** (the workload above
   which the Over clears a 4-pick leg's ~56%, and at or below which the Under does, and how far
   apart the two sit -- about one pass or carry apart is finer than anyone can forecast: say so
   and build no leg on it), the market's chance of the Over (the best available estimate of the
   chance), the price, what the Over needs, the engine's volume, its forecast (middle and 80%
   range), then **the volume
   chance** -- one row per efficiency (his luck-capped rate, his rate this season, the engine's),
   each "N [catches / carries / completions / targets] at [rate] -> [engine's chance of that
   volume]"; the market's own carries or completions line where posted; the efficiency the line
   needs at the engine's volume; how many of his games this season beat that; and last, the
   engine's own chance of the Over, a REFERENCE only (it has run high at real lines, #202: never
   present its gap to the market as information). Lead the read with the first two rows: "the
   line assumes N; the Over needs more than A for a leg, the Under B or fewer -- does he get more
   or less work than the line assumes, by enough, and why?" The engine owns
   the volume, the user judges the efficiency (user: "the engine just needs to predict when volume
   is more than X"): yards a catch for receivers (the engine's catches already hold his catch rate
   and its luck), yards a carry for backs, yards a completion for the starting QB; rushing +
   receiving uses both rates on the engine's carries and catches; receptions use targets and a
   catch rate. The notes under the table name each rate's games (luck-capped: his last 10 games,
   e.g. 7 from 2025 and 3 from 2026, plays past his own 90th percentile capped; this season:
   games and longest play) and the volume's calibration note (carries run narrow; big catch totals
   for top receivers and big completion totals run a little high). **Explain the data every time
   (user, 2026-10-07: "a lot of data, as long as there's sufficiently detailed explanation on how
   the data was produced and how to interpret the data").** Before the first card, copy the
   report's "How to read the player cards" table (each row: how it is produced, how to read it)
   and its "Using it" paragraph. Above the team matchup, say in a sentence or two how its tables
   were built (each section prints its window and method under its table). Never present a
   number without its source being explained somewhere in the answer. Copy the card's tables as
   printed -- every column and row, depth-chart order, never sorted by the gap. Then write the
   read around them, in plain words:
   - **The question** (bold, one line): what this player's prop turns on in THIS game ("Will
     Dallas's extra running belong to this back?").
   - **What his recent usage means**: name the change and why -- more snaps, a bigger share on
     the same snaps, or an absent teammate. A share rise with more snaps is stronger evidence
     than one busy game on unchanged snaps. Say whether last game had the same quarterback and
     the same teammates as this one (the card's quarterback row).
   - **What this matchup means**: the team-level script, then how much of it reaches this
     player through his share.
   - **Which prop fits the view**: receptions or yards, rushing or combined -- read across the
     table's columns. A line that needs only volume (receptions, or a yards line his capped and
     season rates both clear) suits a volume view; a line that needs an efficiency he has not
     shown this season needs a reason to expect it back. Say which efficiency row you believe and
     why. The volume chances are the engine's average-production thresholds, NOT the chance the
     prop wins: the market's chance is the best available estimate of that (an estimate, not a
     known probability). When two lines suit the same view (catches or yards), compare them on
     their market chances, not on the engine's -- a Power Play pays a flat multiple, so the leg
     with the better estimated chance is the better leg for that view.
   - **Where the read can fail**: the specific role, script or efficiency change.
   - **The closing condition** (bold): "If you expect [player] to [volume] at [efficiency] in
     this situation, [side, prop, line] fits that view. It stops fitting if [change]." Take the
     numbers from the table; call a margin under 10% thin. **Show the arithmetic of every
     volume x efficiency you state, and check it clears the line** ("22 completions x 8.5 = 187,
     clears 181"; "3 catches x 10.0 = 30, clears 29.5") -- expert review 2026-10-08 found
     "20+ completions at 8.5" for a 181 line (= 170) and "3-4 catches at about 9" for 29.5
     (= 27). Prefer the volume a table row already printed.
   - **Every usage claim comes from THAT player's own rows** -- never generalised from a
     teammate or a team story ("the backup QB doesn't throw to backs" was true of one back and
     false of the other). Say snaps rose or held from the numbers ("82% to 86%"), not by
     impression. Low team volume does not sink every line, and two receivers can both clear
     from the same throws: state such links only with the numbers that show them.
   - **Injuries:** when section 4 says the report is practice-only, say so and name the
     players who missed practice; never call a player's status known until game statuses
     post.
   After the cards: **"What changes for the remaining players"** (one short paragraph per
   group), and **"Reads that pull in different directions"** -- only conflicts the roles
   support (two backs cannot both gain share of one fixed workload; a receiver's target gain
   taken from a teammate pressures that teammate's Over), stated as assumptions, never as a
   joint probability. A workload scenario table appears only after the scenarios were run
   (`--assume`), never with estimated numbers. End with the card footnote on pick'em prices.
   A whole-number line can push: quote the engine's Over with the push beside it, as the card
   does.
   **Questionable players: give both cases, pick neither.** Every number in the run is
   priced as if a Questionable player PLAYS his normal role (no discount). The report's
   "If a Questionable player is out" section prices the same lines with him OUT and his
   share handed to his teammates. Show both numbers side by side for every line that
   moves, and state that his own props void if he sits. Do not weight the two cases by a
   guess at whether he plays and do not recommend one: the user decides.
2. **Research table** — reproduce the report's "Research table" (from `research_*.csv`) as ONE
   table, grouped by team: Player, Prop, Line, Price (Over / Under), Our projection, Over:
   model / book, Line implies, Pays at this price if you expect, Last game, Flags. Do not hand-compute any of these numbers
   and do not re-sort them by the model-book gap: ranking by gap ranked lines by how likely
   the model was missing something.
   For anytime-TD rows (deferred: only when the user asks for TDs, `--markets td`; DECISIONS
   #190), the model is `anytime_td_v1` (PROTOTYPE; see
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
   description attached. The backtest evidence is the 2022-25 harness at the current settings:
   `reports/current_settings_check_2026-10-06.md` in the repo (it supersedes
   `reports/yardage_harness.md` for width), with rounds 30-39 since (`reports/round30_conversion.md`,
   `reports/round34_receiving_joint.md`, `reports/round38_qb_passing_bias.md`,
   `reports/round29_market_runs.md` for round 39). **The live record at Sleeper's real lines comes first (DECISIONS
   #202):** over weeks 2-4 (1,536 graded lines) the engine's Over chance had no useful relationship
   to outcomes -- log loss 0.717 against the market's 0.692 (a coin flip is 0.693); passing Overs
   hit 57% against an engine 42%, rushing 40% against 47%. So read the market's no-vig chance as
   the best available estimate of the chance (not a known probability) and the engine for what it
   is built for: the workload a line needs, the role evidence and the what-ifs. A big engine-market
   gap can be news the market has, model error, stale inputs or different assumptions; never say
   which without evidence. Pooled backtest biases describe the engine on average; never apply one
   to a single player's chance. Any validation number names the engine version it graded. The live record prints once above the cards, beside the backtest rows; never
   present the engine's percentage as the better probability. The backtest evidence, with
   **measured biases at the main line (expert audit, DECISIONS #197)**:
   at the backtest's stand-in line on 2022-25 the receiving-yards Over hit 2.9 points more often
   than the engine said (receptions 1.4, rushing 1.8, combined 0.6), and every market leans by
   the team's implied points (backs on teams implied 27+: Over 58.7% against 48.5%, measured
   before round 39's market carries, which act on that lean; DECISIONS #204). The report
   prints, once above the cards, each team's row and the priced roles' rows ("Backtest
   calibration"; DECISIONS #198: tight ends' catches Over hit 4.9 points and yards 6.6 points more
   often than the engine said in the backtest -- not seen at real lines so far (live: 45.7% hit
   against 46.3%), and round 41's share change was withdrawn on the seed check (DECISIONS #203) --
   and with actual targets in, tight-end yards run too wide and backs' receiving yards too narrow);
   quote it with the price -- a measured
   record, never an adjustment you apply. Widths: receptions and receiving yards within the
   bar; rushing yards and rushing + receiving run too narrow in the tails (23-25% of games outside
   the 80% range on the re-check, reports/current_settings_check_2026-10-06.md): a line far
   from the projection -- an alternate line, a long shot -- reads more confident than it
   should; say so when quoting one. None is tested against posted lines yet; say that, not
   that the numbers are unvalidated guesses.
   QB passing yards (the starting QB only) are his receivers' yards in the same simulation
   times a starter's usual share, **scaled since round 38 by the team's implied points**
   ((implied / 22) ** 0.2, times 1.04; DECISIONS #199). Before it the Over at the harness's main
   line followed the implied points (38.8% hit at 18 or fewer, 65.5% at 27+, against an engine
   near 47% everywhere); after it the engine says 44.8% and 56.8% in those rows -- most of the
   lean is gone, the extremes keep some. The card prints the team's row beside every passing
   price; chat says it with any passing read. A run without a spread/total turns the scale off
   and says so in the sources table.
   Because the scale acts on the QB alone, his passing mean sits above his receivers' summed yards
   (about 4% at 22 implied points, 9.5% at 28.5): never compare a QB's line with his receivers' lines
   added up (fourth expert review). It is also too WIDE in the tails, still so after round 38 (11.9%
   of games outside the 80% range against a 17-23% bar, 2022-24; reports/round38_qb_passing_bias.md):
   its chances sit too close to 50%. Priced by the user's decision (DECISIONS #105), and round 38
   shipped over its width guard by the user's override (DECISIONS #199).
   Ladder: `ladder_*.csv` holds P(stat <= k) per player; quote it when the user asks about
   an alternate line.
3. **Parlays — DISABLED, do not price them.** `parlays_*.csv` is no longer written.
   The simulation does induce real within-team correlation, which is exactly why a
   parlay number built from it reads as authoritative, but the joint distribution has
   never been checked against realised joint outcomes: the backtest scores each market
   marginally and never looks at pairs. A correlation factor wrong in the second decimal
   turns a +450 fair price into a losing bet, and marginal CRPS cannot detect that. If
   asked for a parlay, say it is gated pending a joint-outcome holdout and give the
   single legs instead.
4. **Close** — the receiving role-shift flags on the board, if any, and one line on the
   journal: a bet the user makes is logged with its four checklist answers (the verified
   change, the workload the line implies, how it fails, the price) and its angle (injury,
   role, return or other, chosen when logged), and graded on Tuesday.
   Engineering notes never go in the guide; raise them in a separate paragraph after it.

The shadow log still carries the internal `tier` column so the scorecard can keep
measuring whether the model's confident calls beat the book. It is never shown.

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
- no pick, lean, edge, EV, Kelly or stake language in the reply
- any actionable quote refreshed immediately before valuation with source update time and quota headers
- archive rows written for every retrieved market (reference copies in the outputs folder; the record is the scheduled workflow's)
- no API key present in output, cache, archive, or logs
- unresolved gaps explicitly disclosed

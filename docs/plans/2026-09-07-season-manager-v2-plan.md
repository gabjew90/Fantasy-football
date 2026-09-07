# Plan: season manager v2 — multi-source decisions for trades, waivers and lineups

Verified against HEAD `3464921` (2026-09-07). Absorbs the prediction-ledger v3
plan rather than superseding it. Covers both leagues. Recommend-only. Daily
cron plus event alerts.

## What this is

`manager/` already works: twenty modules, a committed-state store, GitHub
Issues delivery, a Pacific-time trigger planner, and a 15-minute gate workflow
that gives at-least-once execution of scheduled checks. `waiver_brief` is 336
lines, `trade_radar` is 227 and already calls FantasyCalc, `usage` already
pulls nflverse snap share and target share.

So this is not a rebuild. It is three changes:

1. **One consensus number instead of one source.** Every decision module today
   reads a single projection. We now hold four independent reads plus a
   betting market, and they disagree by 20 to 65 points on the players that
   matter. Disagreement is signal, not noise, and nothing consumes it.
2. **Decisions priced marginally.** Every trade analysis this week was
   recomputed by hand as "what this costs my lineup versus what it gains
   theirs". That is the only framing that produced correct answers and it
   exists nowhere in the code.
3. **Every recommendation emitted as a graded row.** Absorbed from the ledger
   plan, with the corrections in the review of 2026-09-07.

## What is actually new since the manager was written

| Source | Status before today | Status now |
|---|---|---|
| The Odds API | `manager/vegas.py` written, no key, dead code | live, 496 calls/month left |
| ESPN projections | `draftkit/espn.py` exists, no manager consumer | verified, 423 skill players |
| FantasyPros ECR + dispersion | `draftkit/market.py` loads it, no manager consumer | verified, 5,850 rows with `sd`/`best`/`worst` |
| nflreadpy | `usage.py` uses the older `nfl_data_py` | 25 loaders incl. `load_pbp`, `load_ff_opportunity`, `load_nextgen_stats` |
| Yahoo | unreadable by the manager | scrape proven, 10 rosters in 6 page loads |
| FantasyCalc | already wired | already wired, but see D2 |

Route participation and YPRR remain unavailable. `usage.MISSING_NOTE` already
says so and that stays true; nflverse does not publish routes run.

## Defects to fix before anything is built on them

- **D1 `manager/vegas.py`** — the endpoint returns all 272 season games, and
  the loop assigns per event without a date filter, so every team ends up
  holding its Week 18 line. Add `commenceTimeFrom`/`commenceTimeTo`, or filter
  events to the current week before the loop. Test asserts the returned week.
- **D2 `manager/trade_radar.py:21`** — the FantasyCalc URL hardcodes
  `numTeams=12&ppr=1`. That is Omnibeta. Keefamania is 10-team half-PPR and
  gets silently wrong values. Build the URL from the league config. The same
  call also discards `trend30Day`, `maybeTradeFrequency`, `maybeRosterPercent`,
  `overallRank` and the moving standard deviation, which are the only fields
  that make buy-low and sell-high detectable.
- **D3 `manager/waiver_brief.py:278`** — regime hardcoded `"COMFORTABLE"`, so
  every per-dollar number is regime-blind. Carried over from the ledger plan;
  fix before the first graded row exists, since there is no baseline to
  contaminate yet.
- **D4 `manager/usage.py`** — migrate `nfl_data_py` to `nflreadpy`. The
  installed nflreadpy pins season validation at 2025 and 2026 release files
  are not published until after Week 1, so the loader must treat a missing
  2026 release as DATA MISSING, not an error, and the version needs a bump
  when the first week lands.

## Layer 1 — `manager/sources/`

One module per source. Each returns `(frame, note)` and never raises; a dead
source degrades to a DATA MISSING line, matching the existing pattern.

| module | gives | join key |
|---|---|---|
| `sleeper.py` | rosters, matchups, weekly stats, projections | sleeper_id |
| `espn.py` | season and weekly projections | sleeper_id via `draftkit.ids` |
| `sheet.py` | FantasyPros workbook lines | sleeper_id |
| `ecr.py` | expert consensus rank plus `sd`, `best`, `worst` | sleeper_id |
| `fantasycalc.py` | format-matched trade value, trend, trade frequency, roster% | sleeper_id (native) |
| `vegas.py` | implied team totals, spreads, win probability | team code |
| `nflverse.py` | snap %, target share, air yards share, red-zone carries | gsis → sleeper_id |
| `yahoo.py` | Keefamania rosters, lineups, transactions | name → sleeper_id |

Red-zone carry share is derived, not loaded: filter `load_pbp` on
`yardline_100 <= 20 and rush_attempt == 1`, group by rusher and team. Verified
today: 2,745 such plays in 2025.

## Layer 2 — `manager/consensus.py`

Promotes the method used in the 2026-09-06 analysis. For each player:

```
{mean, n_sources, spread, per_source: {sleeper, espn, sheet}, as_of}
```

Each source is scored in the league's own block, then rescaled onto a common
basis by the median over players all sources carry, then averaged. Scale
factors observed: ESPN 0.94, FantasyPros 1.00 against Sleeper.

`spread` is a first-class output, not a diagnostic. It is what separates a
confident call from a coin flip, and every bar below reads it.

## Layer 3 — the three decision modules

### Trades — `trade_radar.py` + new `manager/marginal.py`

`marginal.py` is the piece that does not exist and should. Three functions:

- `cost_to_lose(roster, player)` — lineup points lost if this player leaves,
  after the optimizer re-fills the slot. Not the player's projection.
- `gain_to_add(roster, player)` — lineup points gained if added.
- `price(my_roster, their_roster, give, get)` — both deltas for a package.

Everything useful this week came out of these three. A player with a 200-point
projection whose loss costs 0 is not a trade asset, and six of thirteen
Keefamania skill players are in exactly that state.

Radar output per opportunity: my delta, their delta, FantasyCalc value both
ways, `trend30Day` on both sides, and a flag when consensus `spread` on either
player exceeds 25, which marks a disagreement trade rather than a value trade.

Buy-low is `trend30Day` negative while consensus mean holds. Sell-high is the
inverse. Neither is computable today because the values call throws the fields
away.

### Waivers — `waiver_brief.py`

Keep the existing classify, bid-band and FAAB machinery. Add evidence columns
the free data now supports:

- snap-share delta week over week (already present)
- target share and air yards share delta (new, `load_player_stats`)
- red-zone carry share, last two weeks (new, derived from `load_pbp`)
- the player's team implied total over the next four weeks (new, Vegas)
- FantasyCalc `maybeRosterPercent` as the clock on how long he stays available

`rank_adds(ctx, store) -> (rows, meta)`; ledger keeps top 10, body renders 5.

### Start and sit — `lineup_opt.py`

Read the consensus mean rather than a single projection, and gate on
dispersion: recommend a swap only when the consensus gap exceeds
`max(1.5, 0.5 * combined spread)`. A 3-point edge between two players the
sources disagree about by 30 is not an edge.

Add the Vegas implied team total as a separate displayed column, never folded
silently into the projection.

## Layer 4 — ledger, absorbed

Per the ledger v3 plan with the corrections from the 2026-09-07 review:

- naive baselines use the historical base rate, not p = 1
- all six specs pre-registered before the first row
- trades and contingency scored on every emitted opportunity, not on executed
  events only
- provenance carries `proj_sources`, `n_sources`, `proj_spread`
- actuals cross-checked against `nflreadpy.load_player_stats`, which is
  independent of Sleeper
- new `ledger_source` ruler grading each source against weekly actuals, which
  settles the pre-registered gate in DECISIONS #23 and the `combine` knob
- `scripts/source_gate.py` and `scripts/clv_retro.py` are kept; script pruning
  is out of scope for this plan

## Layer 5 — delivery and event alerts

Scheduled jobs stay as they are. The 15-minute `gate.yml` workflow already
gives at-least-once execution, so event alerts need a watcher, not new
infrastructure. `manager/watch.py` compares the current pull to the last
committed state and fires when:

| trigger | threshold |
|---|---|
| starter injury status change | any change to Out, Doubtful or Questionable |
| snap share | −15 points week over week for a starter |
| Vegas implied total | ±3 points for a starter's team |
| FantasyCalc value | ±10% in 7 days for a rostered or watched player |
| opponent transaction | any add or drop by this week's opponent |

Each fires at most once per subject per week via the existing `first_time`
seen-set. Alerts carry the same provenance as ledger rows.

## Order, by dependency

1. D1 to D4, with tests.
2. `sources/` and `consensus.py`. Everything below reads them.
3. Ledger plus emission from every job. Only component whose value decays.
4. Pre-register all six specs.
5. `marginal.py`, then the three decision modules.
6. Yahoo reader behind `context.py:36`.
7. Actuals, harness, rulers.
8. `watch.py` and event triggers.
9. Survival shown-rows study, independent of the rest.

## Verification

- `pytest tests -q` green at every step. Current baseline is 802 passed, not
  the 699 the ledger plan cites.
- `python -m manager --dry-run --module all` leaves `state/` byte-identical,
  including `state/ledger/**`.
- `vegas.implied_totals` returns only the current week; a fixture with all 272
  games asserts no Week 18 line leaks in.
- FantasyCalc URL differs between the two league configs, asserted.
- `consensus` on a fixture reproduces the 2026-09-06 numbers: Etienne 199.1
  from 187.7 / 209.4 / 200.3, spread 21.7.
- A source outage in each of the eight source modules degrades to DATA MISSING
  with the run completing.
- Two identical `ab` arms under one seed produce byte-identical output.

## Risks

- **Source disagreement is large and real.** Jacksonville is second in the
  league on Rotowire and seventeenth on the betting market. A mean over
  disagreeing sources can be worse than picking the right one. The
  `ledger_source` ruler is the only thing that will settle it, and it needs a
  season of actuals. Until then `combine: first` stays and consensus is
  reported alongside, not substituted.
- **Yahoo scraping is fragile.** Page structure changes silently. The reader
  must assert row counts against the league's known roster size and fail loud.
- **Free-tier quotas.** The Odds API is 500 calls a month; the 6-hour cache
  puts normal use near 120. FantasyCalc and the ECR mirror are unmetered but
  uncontracted and can vanish without notice.

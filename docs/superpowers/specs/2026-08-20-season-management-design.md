# In-Season Management — waiver wire + weekly lineup (v1 design)

Date: 2026-08-20
Status: approved shape (two scheduled briefs + playoff regime); spec pending user review

## Goal

Outperform the league during the regular season with two set-and-forget weekly
briefs — a Tuesday waiver brief and a Sunday lineup brief — built on the same
chassis, philosophy, and edges as draft prep: humble market-grade baselines,
edge from usage recency, availability facts, and opponent modeling. The tool
recommends; the user taps in Sleeper (no public write API — same co-pilot
pattern as draft day).

## League facts (fetched from Sleeper, 2026-08-20)

- FAAB waivers (type 2), **$100 season budget**, weekly processing (not daily),
  waiver day 2 with 2 clear days → claims resolve Wednesday morning.
- Playoffs: **weeks 15–17, 6 of 12 teams**. Trade deadline: week 11.
- IR: 1 slot, accepts **OUT and DOUBTFUL** — effectively a free 16th roster
  spot most weeks; briefs must always propose filling it.
- **Keeper league: 1 keeper** (cost rules unknown — open question for the
  commissioner; keeper-aware valuation is v2 but the data model should carry a
  `keeper_appeal` note field from day one).
- Full K/DEF detailed scoring already in config; roster QB/2RB/2WR/TE/2FLEX/K/DEF/5BN.

## Design decisions (settled; revised after external review 2026-08-20)

1. **Weekly projections are not built from scratch, and the signals MODIFY the
   number (bounded), not annotate it.** Baseline = Sleeper's own weekly player
   projections. Adjustment layers, each capped:
   - **Matchup multiplier (±10% max):** nflverse fantasy points allowed per
     position per defense, shrunk hard toward league average before week 6
     (early defensive stats are noise). DOUBLE-COUNT GUARD: weeks 1–3, regress
     Sleeper's own weekly numbers against opponent quality; if their baseline
     is already matchup-aware, our multiplier applies at half weight (±5%
     tilt). This term is REQUIRED for v1 — without it the lineup engine fails
     the "all factors" bar.
   - **Usage-trend adjustment (±15% max, role-change cases only):** consensus
     projections lag role changes by ~a week; the window between "usage
     shifted" and "market repriced" is the lineup edge. Stable-role players
     get no usage adjustment.
   - **Availability:** hard gate (O/IR = 0), not a multiplier.
   Honest scope note, in the brief itself: for stable-role players the lineup
   brief is convenience; the durable edges are waivers, variance leans, and
   the role-change window.
   RISK: the projections endpoint is undocumented; verify in week 1 preseason.
   Fallback if absent: season-long proj ÷ 16, scaled by availability — degraded
   but functional.
2. **Three scheduled outputs, fully automated** (the ADP diff pattern):
   - Waiver brief, Tuesday 6 PM (nflverse data lands Tuesday AM; claims
     process Wednesday).
   - **Thursday check, Thursday 3 PM** — players lock at their OWN game's
     kickoff, so TNF starters lock three days before Sunday's brief. Scoped to
     that night's two teams only: start/sit for affected slots + inactive
     warnings. Same lineup engine, one filter.
   - Lineup brief, Sunday 9 AM (post-Saturday news, pre-lock; flags ordered by
     kickoff time — London 9:30 AM ET games first).
   Output: `reports/waiver_brief.md`, `reports/thursday_check.md`,
   `reports/lineup_brief.md`, all served by the dashboard (`/brief`).
3. **Playoff odds + regime in v1**, and the sim is **bye-aware**: weekly team
   strength is computed from each team's per-week startable roster (bye
   matrices from the schedule), never a season-constant sum — byes swing
   weekly strength by 15+ points in weeks 5–14, exactly when regime drives
   bid sizing.
4. **Rival remaining FAAB budgets are v1** (Sleeper rosters expose
   `waiver_budget_used` directly — a field read, not a model). Every claim
   shows "teams needing this position and their remaining budgets". Only bid
   *prediction* (sizes/habits) stays v2.
   Deferred to v2: rival bid modeling, keeper-aware valuation (needs cost
   rules), trade radar.

## Architecture (extends draftkit in place)

New modules, existing chassis (SleeperClient, Config, scheduled tasks, reports/):

- **season.py — weekly state refresh.** Pulls: current NFL week (`/state/nfl`),
  league rosters + owners, this week's matchups (my opponent), all transactions
  (for v2 FAAB history, logged from day one), Sleeper injury_status for all
  rostered + top free agents, weekly projections, nflverse weekly stats
  (usage deltas vs prior weeks). Persists `data/processed/season_week{N}.parquet`.
- **waivers.py — claims engine.** Free-agent pool → rest-of-season value vs
  positional replacement (in-season VORP, horizon-weighted by regime) → ranked
  claims with FAAB bands + drop pairing + IR housekeeping.
- **lineup.py — start/sit engine.** My roster vs my actual opponent: weekly
  baseline projection × availability × variance lean; flags inactive-risk
  starters; bye/lock sanity checks.
- **playoffs.py — regime model.** Monte Carlo the remaining schedule (existing
  sim machinery re-pointed): each team's weekly strength = sum of starters'
  weekly projections; H2H outcomes sampled with score variance; 1000 sims →
  playoff odds. Regimes: SAFE (>85%), COMFORTABLE (60–85%), BUBBLE (25–60%),
  LONGSHOT (<25%).
- **cli.py**: `season`, `waiverbrief`, `lineupbrief` commands; two new
  scheduled tasks + `SEASON BRIEFS.bat`.

## Waiver brief contents (Tuesday)

Header: record, playoff odds, regime banner ("BUBBLE — bids favor win-now").

Ranked claims, each with plain-English rationale (draft-style clauses):
1. **Contingency alerts first** — starter OUT/IR'd → his backup, cross-matched
   with the handcuff machinery. These are the league-winning claims.
2. **Usage-spike breakouts** — week-over-week deltas in snap %, routes, target
   share, red-zone touches (leading indicators, not points). Clause names the
   evidence: "route share 41% → 78% over two weeks".
3. **Streamers** — DEF/K (detailed scoring + opponent implied totals), with a
   weeks-15–17 lookahead column when regime is SAFE/COMFORTABLE.
4. Each claim: FAAB band (aggressive / fair / minimum), the drop it pairs
   with, and expected competition note (v1: positional need count across
   rivals; v2: modeled bids).

FAAB bands v1 (calibration constants in config, tuned weeks 1–3):
- **League-winning contingency tier is EXEMPT from calibration** — early-season
  RB injuries are historically when league-winners appear, i.e. exactly when
  bands are least calibrated. For this tier only, the aggressive number =
  (max remaining budget among rivals who need the position) + $5, capped by
  the asset's value to YOUR roster and by the 80%-of-remaining rule. Sealed-bid
  logic beats an untuned band at the highest-stakes moment.
- League-winning contingency (clear RB1 inheritance): 40–65% of remaining budget
- Strong breakout (multi-week usage trend + open role): 15–35%
- Speculative role change: 5–12%
- Streamer: 1–3%
- All scaled by regime (BUBBLE ×1.25 win-now / SAFE ×0.8 with stash preference)
  and weeks remaining. Never bid below $1; never recommend total commitment
  above 80% of remaining budget in one week.

Drop logic: lowest rest-of-season VORP among bench, protected classes: own-RB1
handcuffs, IR-slot occupants, players inside 2 weeks of bye-return… plus
"never drop to the team that needs him" note (rival rosters checked).

IR housekeeping, BOTH directions:
- Slot empty + any rostered player OUT/DOUBTFUL → brief's first line says to
  move him and claim with the freed spot.
- **Forced-exit check (the one that ruins a Sunday):** IR occupant upgraded
  past DOUBTFUL → Sleeper invalidates the roster until someone is cut. Both
  the Thursday check and the Sunday brief test IR eligibility of the occupant
  against current injury_status and, if violated, lead with the required move
  and a suggested drop.

## Lineup brief contents (Sunday)

- Optimal lineup vs my opponent's projected total, with per-slot deltas — only
  changes from current lineup are called out ("bench X, start Y: +3.2").
- **Variance lean**: if projected underdog by >8, prefer ceiling in close calls
  (start the boom/bust player); if favored by >8, prefer floor. Variance proxy:
  stddev of player's weekly scores to date, shrunk early season. Close call =
  projection gap < 2.5 pts; the lean only ever breaks close calls, never
  overrides a clear projection edge.
- Inactive-risk flags: any starter Q/D/O with kickoff time and backup-on-bench
  note ("if inactive, start Z").
- Bye/lock sanity: empty-slot and locked-player warnings at the top in red.

## Scheduling & ops

- `SEASON BRIEFS.bat` + two schtasks: Tue 18:00 (waiverbrief), Sun 09:00
  (lineupbrief). Same mkdir/exact-errorlevel patterns as the fixed launchers.
- Both briefs regenerate on demand via CLI; dashboard serves the latest at
  `/brief` (simple rendered markdown, same styling as /log).
- All Sleeper calls read-only; failures degrade to last-good data with a
  visible staleness banner in the brief header (ADP-diff pattern).
- Deep research passes (news verification on flagged names) remain ad hoc —
  the brief flags "worth a research pass: X, Y" and the user pings Claude.

## Error handling

- Missing weekly projections → fallback baseline + WARNING header in briefs.
- nflverse weekly data not yet published Tuesday → usage clauses omitted,
  claims still ranked by projection + contingency logic, header notes it.
- Empty transactions/rosters (API hiccup) → briefs still render from cache.
- Week boundary handling from `/state/nfl` only — never computed from dates.

## Testing

- Unit: FAAB band mapping, drop-protection rules, regime thresholds, variance
  lean tie-breaking, IR-housekeeping detection — all pure functions.
- Integration: brief generation against a recorded week of fixture JSON
  (rosters/matchups/projections) checked into tests/fixtures.
- Live: week 1 preseason dry run (endpoint verification), then calibration
  review of FAAB bands after weeks 1–3 actual results.

## V2 shelf (explicitly deferred)

Rival FAAB budget/bid modeling (transactions history accrues from week 1 via
season.py logging, so v2 has data waiting); keeper-aware pickup valuation
(blocked on commissioner cost rules); trade radar (weeks 6–11).

## Open questions

1. Keeper cost rules — user to ask commissioner (affects v2, logged here so it
   isn't lost).
2. Sleeper weekly projections endpoint shape/stability — verify week 1.
3. FAAB calibration constants — intentionally config knobs, tuned in season.

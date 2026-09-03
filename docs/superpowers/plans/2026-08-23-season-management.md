> Historical (superseded); see docs/draft-day-runbook.md and docs/plans/2026-09-02-final-form-and-survival-sim-plan.md

# Season Management Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** The in-season co-pilot from the revised spec: Tuesday waiver brief, early-games check, Sunday lineup brief, bye-aware playoff regime — fully automated, recommend-only.

**Architecture:** Five new modules on the draftkit chassis. `seasondata.py` fetches and persists weekly state (Sleeper league/projections/stats + nflverse schedules/usage + points-allowed). `weekly.py` is the pure projection composer (baseline × bounded matchup × bounded trend × availability gate). `playoffs.py` Monte-Carlos the remaining league schedule with byes. `waivers.py` and `lineup.py` turn state into brief models and render markdown to `reports/`. CLI commands + scheduled tasks + a dashboard `/brief` route deliver it.

**Tech Stack:** Python 3.10, polars, numpy, nflreadpy, stdlib http. No new deps.

**Spec:** `docs/superpowers/specs/2026-08-20-season-management-design.md` (revised after external review). Verified 2026-08-23: Sleeper weekly projections endpoint responds (placeholder-only until stat projections publish — detection required); nflverse 2026 schedules carry weekday/gametime/byes; **week 1 contains a Wednesday game**, so the spec's "Thursday check" generalizes to an early-games check driven by the schedule.

**Plan-format note:** tests are complete in every task; implementation steps carry complete code for all decision logic (composer, bands, regime, protections, renderers) and exact endpoint/field contracts for fetch plumbing. Executed inline immediately after writing, so plan and implementation share one source of truth.

**Config additions (`config.yaml`):**

```yaml
season:
  matchup_cap: 0.10          # ±cap on the opponent-defense multiplier
  matchup_shrink_weeks: 5    # ratio weight = weeks/(weeks+this); noise guard pre-week-6
  trend_cap: 0.15            # ±cap on the usage-trend adjustment (role changes only)
  trend_threshold: 0.07      # min abs target-share delta to count as a role change
  score_sigma: 28.0          # weekly team-score sd for win probability
  sims: 1000                 # playoff Monte Carlo iterations
  regime_safe: 0.85
  regime_comfortable: 0.60
  regime_bubble: 0.25
  faab:                      # fractions of REMAINING budget [fair_lo, aggressive_hi]
    league_winner: [0.40, 0.65]
    breakout: [0.15, 0.35]
    speculative: [0.05, 0.12]
    streamer: [0.01, 0.03]
    max_week_commit: 0.80    # never recommend committing more than this in one week
```

**File map:**
- Create: `draftkit/seasondata.py` — weekly state fetch/persist (network edge, thin)
- Create: `draftkit/weekly.py` — pure projection composer + matchup table math
- Create: `draftkit/playoffs.py` — bye-aware season sim + regime
- Create: `draftkit/waivers.py` — claims engine + waiver brief renderer
- Create: `draftkit/lineup.py` — lineup/early-check brief renderer
- Modify: `draftkit/cli.py` (4 commands), `draftkit/web.py` (/brief route), `config.yaml`
- Create: `scripts/SEASON BRIEFS.bat`, three schtasks
- Tests: `tests/test_weekly.py`, `tests/test_playoffs.py`, `tests/test_waivers.py`, `tests/test_lineup.py`, `tests/test_seasondata.py`

---

### Task 1: schedules, byes, kickoffs (`seasondata.py` part 1)

Contracts: `load_schedule(cfg, season) -> pl.DataFrame` — long format one row per team-game: `week:int, team:str, opp:str, gameday:str, weekday:str, gametime:str, is_home:bool`, teams in Sleeper codes (nflverse `LA`→`LAR`, `LV`→`LVR`... map: {"LA":"LAR","LV":"LVR","NO":"NOS","NE":"NEP","GB":"GBP","KC":"KCC","SF":"SFO","TB":"TBB","WSH":"WAS","JAX":"JAC"} applied via `_norm_team`). Cached to `data/processed/schedule_{season}.parquet`; network only on miss. `byes(schedule, week) -> set[str]` = all 32 minus teams appearing that week. `early_games(schedule, week) -> pl.DataFrame` = rows with weekday not in ("Saturday","Sunday","Monday") — Wednesday and Thursday both count. Tests build a 4-row fixture frame and never touch the network; `_norm_team` and `byes` and `early_games` are pure. Implementation fetches via `nflreadpy.load_schedules([season])`, filters `game_type=="REG"`, melts home/away into the long format.

- [ ] Test file `tests/test_seasondata.py`: `test_byes_are_missing_teams`, `test_early_games_include_wednesday`, `test_team_normalization` (LA→LAR, KC→KCC)
- [ ] Run to fail → implement → pass → commit `feat: season schedule/bye/kickoff data layer`

### Task 2: Sleeper weekly fetchers (`seasondata.py` part 2)

Contracts (all take `getter=get_json` injectable for tests):
- `nfl_state(getter) -> dict` — `/v1/state/nfl`, returns week/season/season_type.
- `weekly_projections(cfg, season, week, getter) -> dict[str, float] | None` — `/v1/projections/nfl/regular/{season}/{week}`; score each player's stat dict with the LEAGUE's live `scoring_settings` (fetched once via client.league, cached on cfg call site): `pts = sum(scoring[k]*v for k,v in stats.items() if k in scoring)`. **Placeholder detection:** if no player row contains any scoring-relevant key (all keys start with "adp_"), return `None` — callers fall back.
- `weekly_stats(season, week, getter) -> dict[str, dict]` — `/v1/stats/nfl/regular/{season}/{week}` raw (actuals for scoreboard/variance).
- `league_week_state(cfg, client) -> dict` — rosters (players, starters, owner, `settings.waiver_budget_used`), users (display names), matchups for current week (roster_id→matchup_id/points), season-to-date `transactions(leg)` appended to `data/processed/season/transactions.jsonl` dedup by transaction id.
- `injury_map(players_json) -> dict[str, str]` — sleeper_id → injury_status (Questionable/Doubtful/Out/IR...), empty string when none.
- `refresh(cfg) -> dict` — orchestrates all of the above + Task 3's points-allowed + usage deltas; persists under `data/processed/season/week{N:02d}/` (rosters.json, projections.json or FALLBACK marker, pa.parquet, usage_delta.parquet) and returns a summary dict; every fetch failure degrades to last-good with a `stale` list in the summary (ADP-diff pattern).

Tests monkeypatch the getter with recorded fixture dicts: `test_placeholder_projections_detected` (adp-only stats → None), `test_projection_scoring_uses_league_settings` (pass_td 4.0 → 2 TDs = 8 pts), `test_budget_read` (waiver_budget_used 37 → remaining 63).

- [ ] Tests → fail → implement → pass → commit `feat: sleeper weekly fetchers with placeholder detection`

### Task 3: points-allowed + usage deltas (`weekly.py` math, `seasondata.py` builders)

`points_allowed(week_stats_frames, scoring) -> pl.DataFrame(def_team, pos, pa_ratio)` — per defense per position, fantasy points allowed vs league average for that position (ratio 1.0 = average). Built from nflverse current-season weekly (`opponent_team` column) scored with `dataset.fantasy_points_expr`. `usage_deltas(current_weekly) -> pl.DataFrame(sleeper_id, pos, recent_share, season_share, delta)` — target share (WR/TE) or carry+target share (RB) over trailing 2 weeks vs season. Pure math in `weekly.py`:

```python
def shrunk_ratio(ratio: float, weeks: int, shrink_weeks: int) -> float:
    w = weeks / (weeks + shrink_weeks)
    return w * ratio + (1 - w) * 1.0

def matchup_mult(ratio: float | None, weeks: int, cap: float, shrink_weeks: int) -> float:
    if ratio is None: return 1.0
    return min(1 + cap, max(1 - cap, shrunk_ratio(ratio, weeks, shrink_weeks)))

def trend_adj(delta: float | None, cap: float, threshold: float) -> float:
    if delta is None or abs(delta) < threshold: return 0.0
    return min(cap, max(-cap, delta * 2.0))

def compose(base: float, mult: float, adj: float, status: str) -> float:
    if status in ("Out", "IR", "PUP", "Sus", "NA"): return 0.0
    return base * mult * (1 + adj)
```

Tests (`tests/test_weekly.py`): week-2 ratio 1.6 with shrink 5 → mult ≈ 1.10 capped; week-10 same ratio → capped at 1+cap; delta 0.05 under threshold → 0; delta 0.12 → +0.15 capped; status Out → 0 regardless.

- [ ] Tests → fail → implement → pass → commit `feat: bounded matchup and trend math`

### Task 4: playoff regime (`playoffs.py`)

`team_week_strength(roster_player_rows, week, byes, weekly_base) -> float` — best legal lineup (same slot logic as the draft grader) where a player whose team is on bye that week scores 0. `simulate_season(strengths_by_week, matchups_by_week, records, sims, sigma, rng) -> dict[roster_id, float]` — for each sim, each remaining matchup: win if `sA - sB + N(0, sigma*√2) > 0`; final standings by wins then total points; top-6 make playoffs; odds = fraction of sims in. `regime(odds, cfg) -> str` — SAFE/COMFORTABLE/BUBBLE/LONGSHOT per thresholds. Tests: bye week zeroes a starter and lowers that week's strength; a team with all wins already has odds 1.0; regime thresholds map exactly; deterministic under seeded rng.

- [ ] Tests → fail → implement → pass → commit `feat: bye-aware playoff odds and regime`

### Task 5: waivers engine + Tuesday brief (`waivers.py`)

Model: `build_waiver_model(ctx) -> dict` where ctx carries my roster, all rosters, FA pool (universe minus rostered, top ~150 by ROS value), weekly/ROS values, injury map, rival budgets/needs, regime, schedule.
- ROS value: `ros(player) = weekly_base(player) * remaining_weeks_scaled`, replacement = per-position median of FA ranks 5–15; claim value = ros − replacement.
- Claim classes in priority order: `contingency` (FA whose team's rostered starter at same pos is Out/IR — cross-checked against every roster, mine flagged separately), `spike` (usage delta ≥ threshold with evidence string), `streamer` (DEF/K best matchup_mult next week; weeks-15–17 note when regime SAFE/COMFORTABLE).
- FAAB bands: class → `[lo, hi] × remaining_budget`, regime multiplier (BUBBLE ×1.25 on win-now, SAFE ×0.8), min $1, week commit ≤ `max_week_commit`. **League-winner override:** aggressive = `max(budget of rivals needing that position) + 5`, capped by fair-band hi and by my remaining budget.
- Drops: lowest ROS among my bench, protected: handcuffs of my starters (backs_up column), IR occupants, players on bye next week whose return fills a starter. "Do-not-drop-to-rivals" note when a drop fills a hole for a team above BUBBLE.
- IR both directions: empty slot + rostered Out/Doubtful → lead action; occupant upgraded past Doubtful → RED lead action with suggested cut.
- `render_waiver_brief(model) -> str` markdown: regime banner, IR actions, claims table (name, class, evidence, bid band, drop pairing, rival budgets note), lens scoreboard footer (Task 7).

Tests: contingency detection from fixture rosters; sealed-bid = desperate rival max + 5 capped; drop protection keeps handcuff; IR forced-exit detected; commit cap enforced; renderer includes regime line.

- [ ] Tests → fail → implement → pass → commit `feat: waiver claims engine and Tuesday brief`

### Task 6: lineup + early-games briefs (`lineup.py`)

`build_lineup_model(ctx)`: my roster weekly values (Task 3 composer), current starters from Sleeper roster.starters, optimal lineup, delta list (only changes, each "+X.X pts"), opponent's projected total (their roster, same composer), variance lean — favorite/underdog margin > 8 → in close calls (gap < 2.5) prefer low/high stdev (weekly actual stddev from `weekly_stats`, shrunk ×min(1, weeks/4)); inactive-risk flags (starters Q/D/O) ordered by kickoff (schedule gametime); bye/empty-slot red warnings first. `build_early_model(ctx)`: same, filtered to teams in `early_games(schedule, week)`. Renderers → `reports/lineup_brief.md`, `reports/early_check.md`. Tests: optimal beats current fixture by exactly the benched-player delta; lean only flips sub-2.5 gaps; Wednesday team appears in early model; IR forced-exit shows in both.

- [ ] Tests → fail → implement → pass → commit `feat: lineup and early-games briefs`

### Task 7: three-lens scoreboard (`waivers.py` footer + `seasondata.py` accumulation)

Each refresh appends `{week, roster_id, actual_points}` from finalized matchups to `data/processed/season/actuals.jsonl`. Scoreboard table: cumulative actual points per team beside the three preseason orderings (our board 1989-table, league grader table, wizard grade order — constants in `draftkit/lenses.py` with source comments), plus each lens's rank-correlation (Spearman) with actual standings to date. Rendered as a footer section in the waiver brief. Test: correlation of identical orderings = 1.0; table renders 12 rows.

- [ ] Tests → fail → implement → pass → commit `feat: three-lens scoreboard`

### Task 8: CLI, web route, ops, integration smoke

- `cli.py`: `seasonrefresh` (runs seasondata.refresh, prints summary), `waiverbrief`, `lineupbrief`, `earlycheck` (each: refresh-if-stale then build+render, print path + headline).
- `web.py`: `GET /brief` serves the newest of the three briefs rendered like `/log` (reuse the markdown-ish renderer style; simple `<pre>`-free HTML: split lines, headings from `#`).
- `scripts/SEASON BRIEFS.bat` (arg %1 = command) + three schtasks: `draftkit waivers` Tue 18:00, `draftkit early check` Thu 15:00, `draftkit lineup` Sun 09:00 (exact-errorlevel + mkdir patterns from the fixed launchers). Retire note documented for the 9 AM ADP task (leave running until user confirms).
- README cadence section updated to the in-season rhythm.
- Integration smoke TODAY (preseason): `seasonrefresh` must run end-to-end with season_type="pre" → targets week 1 REG, projections placeholder → FALLBACK marker, byes/kickoffs real, briefs render with "PRESEASON — projections are fallback baselines" banner. Full suite green. Push.

- [ ] Smoke + suite → commit `feat: season CLI, /brief route, scheduled tasks` → push

**Self-review:** spec coverage — matchup term req (T3 ✓ with double-count knob `matchup_cap` halvable), signals-modify-with-caps (T3 composer ✓), three outputs incl. early check (T6/T8 ✓ generalized to Wednesday), rival budgets v1 (T5 ✓ field read), sealed-bid league-winner exempt from calibration (T5 ✓), bye-aware sim (T4 ✓), IR both directions (T5/T6 ✓), placeholder fallback + staleness banners (T2/T8 ✓), keeper_appeal field — carried as a note column in the FA pool table (T5, empty until commissioner rules land). Type consistency: `weekly.compose/matchup_mult/trend_adj` signatures used identically in T5/T6 ctx builders.

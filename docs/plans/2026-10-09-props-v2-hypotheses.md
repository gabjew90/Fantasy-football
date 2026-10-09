# Props engine v2: three hypotheses and the data behind them

Design note (the consolidation plan's first step for a methodology change: name the
hypothesis and the metric before writing code). Status: proposal, nothing built.

## How this fits the repo rules

CLAUDE.md says "no parallel engines" and "improve by replacing, not adding". A forked
`props/engine_v2/` would break both. The proposed shape:

- Each hypothesis is a study in `experiments/props_v2/` (outputs gitignored, 30-day expiry).
- A study that passes its test becomes a candidate inside `props/engine/` behind the existing
  interface, registered `shadow` in `core/registry.py`, and goes through a pre-registered round
  judged on `reports/scoreboard.md` with the four-seed rule (DECISIONS #188, #202).
- Data is read through `core.fetch` (participation is a new kind there; see below).

## What the current engine already does

The proposal describes several things the engine already has. The new work is narrower than it
looks.

| Proposal item | Current engine | Evidence |
|---|---|---|
| Project opportunity, shrink efficiency to position averages (H1) | Team volume blend (k=4) x player share x per-target / per-carry rates, each blended toward slot priors (`model.blended_rate`) | yardage harness, #198 |
| Full distribution, p10-p90 calibration | 20,000-sim distribution per player; width check (20% +/- 3 outside p10-p90) and 60-90% reliability buckets | `reports/yardage_harness.md` |
| Beat a naive trailing-average baseline on held-out weeks (H1 test) | Harness criterion 1: CRPS vs baseline A (player's own recent rates), walk-forward, tune 2022-23, test 2024-25 | every market in the harness passes (pooled 2024-25 interval above zero); width since superseded by `reports/current_settings_check_2026-10-06.md` |
| Volume predictable, efficiency not | Measured in #206: half-season stability yds/catch 0.57, catch rate 0.48, yds/target 0.31 | #206 |
| Injury reallocation from with/without splits (H2) | `OUT_RULE`, fitted on 2022-23 absence games, confirmed 2024-25 | `reports/absence_tune.md` |
| Line vs median, not mean (H3) | Prices P(X > line) from the simulated distribution, which uses the whole shape; harness records `above_med_*` | `backtest.py` |
| Condition on spread and total (H3) | Throws 25% toward market volume, backs' carries 50% (#134, #204); QB passing scaled by implied points (#199) | scoreboard |

## Data availability

Checked 2026-10-09 against the nflverse release URLs.

| Data | Seasons available | In `core.fetch` | Live in 2026 |
|---|---|---|---|
| Play-by-play | through 2026 | yes (`pbp`) | yes |
| Snap counts | through 2026 | yes (`snaps`) | yes |
| Weekly rosters (ACT/INA) | through 2026 | yes | yes |
| Injury reports | through 2026 | yes | yes |
| Depth charts | through 2026 | yes | yes |
| Schedule with spread and total | through 2026 | yes (`schedule`) | yes |
| **Participation** (11 on-field IDs per play, formation, personnel, targeted route) | 2016-2025 | **no** | **no** (2026 file 404 at week 5; published after the season) |
| FTN charting (play action, screen, catchable, drop) | 2022-2026 | no | yes, but no per-player route data |
| Routes run per player | none | -- | -- |
| **Prop lines** | **2026 weeks 2-5 only**, Sleeper, decision snapshots | `sleeper_lines` | being logged |
| Settled calls | 2026 weeks 2-4: 2,800 rows (rec yds 859, rec 817, rush 387, pass 99, TD 638) | -- | grows weekly |

Participation coverage, checked: 2022 has on-field players on 91.4% of plays, 2024 and 2025 on
100%. `route` is filled on about 40% of plays and is the targeted receiver's route only, so it
does not say who ran a route.

## H1: lines lag role changes

**What is new:** two things. (a) A route proxy: share of team dropbacks a player was on the
field for, from participation, as a better opportunity denominator than snap share. (b) A
recency term: a 3-week usage trend weighed against the season blend.

**Data verdict:**
- (a) is available for **backtesting only** (2016-2025). It cannot be a live input in 2026
  because participation is not published in season. It could inform priors (last season's
  dropback share) but not the weekly update. The on-field proxy also overcounts RBs and TEs who
  stay in to block. Snap counts remain the only live usage feed.
- (b) needs nothing new: pbp has targets and carries by week.
- The claim "lines lag" needs line history. There are four weeks of Sleeper lines. A trend
  signal fires on a small subset of rows, so a test on lines is badly underpowered this season.

**Test (forecast, no lines):** walk-forward 2022-25, tune 2022-23, judge 2024-25. Metric: CRPS
on targets, carries, receptions, receiving yards and rushing yards against the live engine (not
against baseline A, which the live engine already beats). Slice: player-weeks where 3-week share
differs from the season blend by more than a pre-set threshold. Pass: better on both test seasons
with the game-block bootstrap interval excluding zero, width and calibration unchanged.

**Test (market):** on the 2026 record, rows in the trend slice: model log loss vs the no-vig
market. Reported, not used to promote, until the slice has enough settled rows.

## H2: injury reallocation is learnable

**What is new:** replace the single pooled `OUT_RULE` (25% to priced teammates, 80/20 by
position, 75% to the depth pool) with a rule conditioned on the absent player's role (WR1, TE1,
RB1...) and on absence age. #198 already found the live rule is about right in the first game
and roughly double the observed gain in continuing absences, and that the backtest never runs
the injury logic.

**Data verdict: available.** Weekly rosters (INA/RES), injury reports, depth charts, snap counts
and pbp cover 2016-2025 for fitting and 2026 live. `absence_tune.py` already builds absence
events (241 target events, 203 carry events across 2022-25). Splitting by role and by absence
age divides those counts several ways, so the role cells will be thin; pooling across positions
with a role covariate is likely necessary. Earlier seasons (2016-21) can be added to raise N;
participation is not needed.

**Test:** predicted vs actual teammate share in held-out absence games (tune 2022-23, test
2024-25), loss as in `reports/absence_tune.md`, against the live `OUT_RULE`. Second check: run
the injury handoff inside the yardage harness, which today prices whoever was active.

## H3: yardage is right-skewed, unders are favoured

**What is new:** calibration of the tails sliced by spread bucket and position, and a test of
whether the under bias still exists at today's lines.

**Data verdict:**
- Skew and tail calibration by spread bucket: **available.** The harness already stores
  `abs_spread`, `team_spread` and the model median per row; the slice is a report change.
- Whether unders still win at the book: **only the 2026 record.** About 2,100 settled yardage and
  reception rows from three weeks, all at Sleeper (a pick'em product with ~12% overround per leg,
  not a sportsbook). That is enough to estimate the under rate by market with a wide interval,
  not by market x spread bucket. The 2017-22 figures in the proposal cannot be checked from the
  repo.

**Test:** (1) harness: PIT mean and outside-p10/p90 rates by position x spread bucket on
2024-25; a bucket fails if PIT mean is off 0.5 by more than 0.03. (2) record: Under hit rate by
market at Sleeper lines vs the no-vig price, refreshed weekly.

## Gaps that limit all three

1. **No historical prop lines.** CLV and ROI on past seasons are impossible; the only market test
   is the forward record. The archive has decision snapshots only, no open/close pairs, so CLV
   is not measurable yet either.
2. **No live route data.** Participation stops at the end of the prior season.
3. **One book.** Sleeper only, with DraftKings/FanDuel snapshots via `compare.py` when the Odds
   API key is present.

## Proposed order

1. H2 first: data is complete, the code base (`absence_tune.py`) exists, and #198 already
   measured a specific error in continuing absences.
2. H3 harness slice: a report change on existing data, informational.
3. H1 (b) recency term; H1 (a) only as a backtest study on whether dropback share beats snap
   share, since it cannot run live.

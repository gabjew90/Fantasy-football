# Auto-Manager build decisions

Judgment calls made during the one-pass build, per the spec's "make the call,
document it, keep going."

## Platform
- **Python 3.10, not 3.11+.** The existing repo venv is 3.10.10 and every library
  used supports it; nothing 3.11-only is needed. Rebuilding the venv mid-season
  risks the draft-era toolchain for zero functional gain. `tzdata` added for
  Windows zoneinfo.
- **Windows host, so no systemd.** The scheduler runs via `scripts/MANAGER.bat`
  under a Task Scheduler ONLOGON task (registration command in README). A
  `deploy/manager.service` systemd unit ships anyway for portability, as the spec
  asked for one in the README.
- **Same repo, new `manager/` package.** The spec says single repo; draftkit
  already owns Sleeper caching, the schedule parquet, league-scored weekly
  projections with placeholder fallback, lineup math, and ROS values (tiers.csv).
  Manager reuses those as a library and owns everything decision/delivery/scheduling.

## Delivery
- **Discord wiring is ON HOLD by user instruction (2026-08-25)**: delivery will
  ride GitHub Actions instead (details to come). `manager/deliver.py` keeps the
  webhook code path but the operative outputs are stdout + `reports/manager/*.md`
  — a clean handoff surface for an Actions workflow. Do not document or register
  anything Discord-specific until the user returns with the Actions design.
  Delivery remains post-or-edit keyed on a per-brief key in SQLite with a
  content hash, so unchanged re-runs are no-ops (idempotency requirement)
  regardless of backend.
- **Briefs are also written to `reports/manager/`** so the existing GitHub-push
  phone path keeps working alongside Discord. The old Tue/Thu/Sun scheduled
  tasks remain until Discord delivery is verified live, then should be retired
  (they are the fixed-cron failure mode this system replaces).

## Module 0
- **Slate** = a distinct kickoff datetime (PT) among games involving my rostered
  teams or my current opponent's rostered teams. Inactives = kickoff − 90 min;
  the per-slate check fires at inactives + 10 min.
- **Plan pass rule**: for each day with a relevant slate, one lineup plan pass at
  (earliest inactives that day − 60 min), floored at 4:00 AM PT. A normal Sunday
  (10:00 AM PT slate) lands exactly at the spec's ~7:30 AM PT; a 6:30 AM PT
  international kickoff pulls it to 4:00 AM PT; the Wednesday opener gets its own
  Wednesday pass. This generalizes "earlier on international weeks" to every
  schedule quirk.
- **Missing gametime** in the schedule feed defaults to 1:00 PM ET with a logged
  warning (has not occurred in the 2026 REG schedule).

## Module 1
- **FAAB budgets**: authoritative number is the roster's `waiver_budget_used`
  field; transaction-history reconstruction (summed winning waiver bids) runs as
  a cross-check and powers the per-rival spend detail. A mismatch is reported in
  the brief rather than silently resolved (field wins).
- **Carries inside the 10 / route participation / YPRR** are not in free nflverse
  weekly data. The brief uses snap %, target share, targets, carries, receiving
  yards week-over-week and prints `DATA MISSING: inside-10 carries, routes (not
  in free nflverse weekly data)` per the degrade-gracefully rule.
- **Add ranking** blends: contingency class (inherits an injured starter's role),
  Sleeper trending count (24 h), usage deltas, ROS value from tiers.csv, and my
  positional need over the next 3 bye weeks. Weights in `manager/waiver_brief.py`.

## Module 3
- **Vegas thresholds** per spec: implied team total ≥ 24 → ×1.05, < 18 → ×0.95
  (single 5% notch; anything larger would double-count what projections already
  price in). No `ODDS_API_KEY` → `DATA MISSING: Vegas lines` and no adjustment.

## Module 4
- **Weekly positional stdev assumptions** (points, full PPR): QB 7.0, RB 6.0,
  WR 6.5, TE 5.0, K 4.5, DEF 6.0. Win probability = P(margin > 0) under a normal
  with variance = sum of both lineups' player variances. These are conventional
  fantasy-variance figures, not fitted; revisit once 2026 actuals accumulate.
- Ceiling/floor mode: |projected margin| ≥ 10 flips coin-flip decisions
  (underdog → ceiling, favorite → floor); otherwise projection decides.

## Module 5
- **Veto-risk flag**: offer/ask FantasyCalc value ratio below 0.7 (either
  direction) → "may draw veto votes." Crude by design; the spec forbids building
  a valuation model.
- **Seller window**: after week 5, a team below .500 AND ≥ 2 games out of the
  6th seed.
- **Desperation event**: a rival's optimal-lineup starter freshly Out/IR where I
  roster a same-position player worth 60–140 % of the downed starter (the
  "replacement-shaped asset"), flagged 48 h urgency.
- **Playoff-schedule arbitrage** is qualitative in v1: each target lists his
  team's weeks 15–17 opponents in the rationale. A numeric strength adjustment
  needs a defense-quality model this repo doesn't have yet; faking one would be
  worse than naming the opponents.

## Scheduling
- APScheduler 3.x `BlockingScheduler` with `America/Los_Angeles` timezone; the
  Monday 6:00 AM planner recomputes and re-registers the week's jobs with
  deterministic ids (`wk{n}:{kind}:{iso}`, `replace_existing=True`) and drops
  stale ones, so a crashed-and-restarted process converges to the same schedule.
  On process start the planner runs immediately for the current week.

> Historical (superseded); see docs/draft-day-runbook.md and docs/plans/2026-09-02-final-form-and-survival-sim-plan.md

# Sleeper Auto-Manager ("must-win" edition) — build plan

Spec: uploads/0cd9a710-fantasymanagerbuildprompt.md (one-pass, no clarifying questions,
judgment calls -> DECISIONS.md). Notification-only; never writes to Sleeper.

## Tasks
1. Infra: `manager/` package — clock (PT/ET, DST-safe), SQLite store, Discord
   delivery (post/edit/idempotent-skip, dry-run), .env secrets, structured PT logging
2. Module 0 — schedule-driven trigger planner + lock-time tests (acceptance gate:
   Wednesday opener, 6:30 AM PT international, normal Sunday, Saturday slate)
3. Module 1 — waiver brief: trending + usage deltas (nflverse) + contingency claims +
   FAAB from transaction history (tested) + rival budgets + bye-aware scarcity + IR flags
4. Module 2 — inactives/injury monitor: twice-daily diff sweeps + per-slate checks
   with "Bench X, start Y" from Module 3's contingency table
5. Module 3 — lineup optimizer: Sleeper projections + Vegas implied totals (Odds API),
   FLEX/coin-flip focus, ceiling-floor mode from Module 4, contingency table
6. Module 4 — opponent scout: projected margin + win prob (documented variance)
7. Module 5 — trade radar (weeks 3-10): FantasyCalc values, structural fits, seller
   windows, desperation events, veto flag, repeat suppression
8. Scheduler: APScheduler (PT), Monday 6 AM planner registers the week dynamically,
   daily 8 AM healthcheck, week-plan message; Windows launcher + systemd unit; README
9. Definition of done: `python -m manager --dry-run --module all` end-to-end vs live
   league; all tests pass; scheduler registered (Discord post gated on webhook URL)

Reuse draftkit for: Sleeper client/caching, schedule parquet, weekly projections
with fallback, lineup math, waiver claim classes, tiers.csv ROS values.

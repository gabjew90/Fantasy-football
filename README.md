# draftkit — draft prep, live draft engine, in-season auto-manager

Multi-league since 2026-08-29: `config.yaml` holds globals, every league fact
lives in `leagues/<name>.yaml` (`--league <name>` / `DRAFTKIT_LEAGUE`).
Leagues on file: **Omnibeta Degens** (Sleeper, 12-team full PPR, 2 FLEX,
drafted 2026-08-23) and **Keefamania** (Yahoo, 10-team half PPR, 1 FLEX,
draft Sat 2026-09-05 — see `docs/draft-day-runbook.md`). Decisions and their
evidence live in `DECISIONS.md`; this README is the map, not the record.

> **The in-season auto-manager's cron stack is retired (2026-10-08, DECISIONS
> #212).** It had no schedule since 2026-09-25 (DECISIONS #109) and
> duplicated the fantasy commands: use `nfl fantasy ...` (lineup, waiver,
> trade, scenario), through chat or `python nfl.py fantasy --help`. Props
> capture and grading (`props.yml`) still run on their schedule. `manager/`
> keeps the Yahoo and consensus layer the fantasy commands import, the trade
> radar (pending the user's call on trade search), and two manual entrypoints:
> `yahoo-sync` (`scripts/YAHOO SYNC.bat`) and `trade-radar`.
>
> 5. Weekly projections auto-detect Sleeper publish state; until live they fall back to
>    season proj ÷ 16 with a visible banner. The matchup adjustment activates from
>    week 3 data (cap in config.yaml `inseason:`).

## Quickstart

```bash
pip install -r requirements.txt

python -m draftkit verify     # re-verify every league fact against the Sleeper API
python -m draftkit players    # cache the Sleeper player universe (daily TTL)
python -m draftkit market     # FantasyPros ECR + FFC ADP, matched to Sleeper IDs
python -m draftkit dataset    # nflverse 2025 data -> usage metrics (Phase 2)
python -m draftkit tiers      # projections + VORP + tiers.csv + board.md (Phase 3)
python -m draftkit board      # pretty-print the tier board in the terminal

python -m draftkit simulate --slot 6   # dry-run a full draft through the tracker
python -m draftkit track               # live tracker (Phase 4)
python -m draftkit track --draft-id <mock_draft_id> --slot 3   # vs. a Sleeper mock lobby
```

**Before draft day** (Sleeper leagues): `me.username` lives in the league's
yaml (`leagues/<name>.yaml -> me:`), not here; re-run `market` + `tiers` the
morning of the draft (pulls are cached 12–24h); a Sleeper mock lobby plus
`track --draft-id <id>` shows the tracker against a live picks feed. For the
Yahoo league the procedure is `docs/draft-day-runbook.md` (bridge server +
in-page driver; picks through Yahoo's own client action, store-verified).

## What the pipeline produces

- `tiers.csv` — player, sleeper_id, pos, proj_pts, vorp, tier, cliff_flag,
  ecr, adp, adp_delta, plus usage metrics (WOPR, TPRR/YPRR-proxy, high-value
  touches).
- `board.md` — printable tier board. ⛰ marks a **cliff**: last player before a
  drop bigger than one standard deviation of the position's VORP gaps.
- Live tracker: strikes drafted players, top-3 remaining per position,
  roster-need tracking against QB/2RB/2WR/TE/2FLEX/K/DEF/5BN, ADP-faller
  alerts (≥12 picks = one full round), and a cliff-vs-wait call computed from
  which specific rosters pick between your picks and what they still need.

## Verified league facts (2026-08-19, re-checkable via `verify`)

- Snake, 15 rounds, 60s timer, 12 teams, no third-round reversal, CPU
  autopick on timeout.
- Scoring: 1.0/rec, 0.04/pass yd, 4 pass TD, −1 INT, 0.1 rush/rec yd,
  6 rush/rec TD, −2 fumble lost. No TE premium.
- Roster: QB, 2RB, 2WR, TE, 2FLEX (RB/WR/TE), K, DEF, 5 BN.
- **Correction to the handoff doc: the league HAS 1 IR slot** (Out/Doubtful/
  Suspended/PUP eligible). A late-round stash of an injured starter is
  therefore playable — it doesn't burn a bench spot once the player is out.
- Draft order is finalized for 11/12 teams (roster 12 → slot 6 unclaimed).

## Design decisions & departures from the handoff plan

Where I deviated, and why:

1. **You don't need to upload a FantasyPros CSV to get started.**
   DynastyProcess mirrors FantasyPros redraft-PPR ECR (refreshed several times
   a week; the current pull is 4 days old) and FantasyFootballCalculator's
   public API supplies real 12-team PPR ADP from ~7k August drafts. Both are
   pulled automatically. A CSV at `data/external/fantasypros.csv` still
   overrides ECR if you want same-morning expert ranks.
2. **ID matching is map-first, fuzzy-second.** The DynastyProcess ID map links
   FantasyPros ↔ Sleeper ↔ nflverse (gsis/pfr) for ~4.7k players, so fuzzy
   name matching (Jr./III suffixes, D/ST naming) is only the fallback. Current
   unmatched count across 505 ECR rows: 2 (both irrelevant depth players).
3. **Projection = blend, with the model share configurable.** Pure
   2025-production projections can't see rookies, team changes, or injuries;
   pure market projections have no edge. The model share (alpha) is set by
   player type, not one number: 0.65 for stable veterans (12+ games, same
   team), 0.40 for new-team players and rookies, 0.55 otherwise, and WR is
   capped at 0.20 because two seasons of backtest made every step above zero
   worse there. The model half is 2025 league-scored PPG, shrunk by games
   played, adjusted by a within-position regression on WOPR + high-value
   touches, then role-gated (a depth-chart backup the market also ranks as a
   backup is scaled to his expected share of starting weeks). The market half
   is a per-position log-curve fit of projection vs. ECR. Players with no
   2025 data are 100% market-implied
   and labeled `proj_source=market_implied` in tiers.csv — treat those tiers
   as market consensus, not model insight. K/DEF are always market-implied by
   ECR rank with a deliberately flat spread (they're near-fungible; the small
   VORP keeps them out of recommendations until round 14, which is also hard-coded).
4. **TPRR/YPRR are proxy-derived and flagged.** nflverse route participation
   data ended after 2023, so routes ≈ offensive snaps × team dropback rate
   (`routes_proxy=true` in tiers.csv). If you get PFF/FantasyPoints exports,
   `data/external/overrides.csv` (sleeper_id, proj_pts) merges straight into
   the tier build.
5. **Recommendation engine has a hard roster-legality constraint.** Naive
   VORP-max never drafts a QB in a 1-QB league (bench WRs out-VORP QB12 all
   day). The tracker escalates unfilled dedicated-slot needs by round and
   switches to needs-only once remaining picks = open starter slots. The
   `simulate` command was added precisely because this class of bug only shows
   up over a full 15-round draft, not in unit tests.
6. **Replacement baselines are per league** (`leagues/<name>.yaml ->
   replacement_baselines`), derived from the league's format at onboarding
   and never copied between leagues (Omnibeta RB40/WR60/QB12/TE12;
   Keefamania settled by bake-off, DECISIONS 2026-09-01 #4).

## Strategy notes the numbers currently support

- 13 skill picks for 8 skill starters + 5 bench: startable depth > lottery
  tickets, but the IR slot (see above) makes exactly one injury stash free.
- TE and QB cliffs are steep this year: after the top-2 TEs the position falls
  off hard (tier 3 is a 40+ point drop), while QB tier 3 is deep — the model
  consistently waits on QB into rounds 7–9 and it costs almost nothing.
- The 60s clock + CPU autopick means the tracker's precomputed
  recommendations matter: everything renders instantly from tiers.csv; there
  are no network or model calls in the on-clock path.

## Testing

```bash
python -m pytest tests/          # snake math, needs, tiering, scoring, ID matching
python -m draftkit simulate --slot 6   # full-draft dry run through the real tracker code
```

## Operating notes

- Sleeper leagues launch draft day with `scripts/DRAFT DAY.bat`; Yahoo leagues follow `docs/draft-day-runbook.md` (bridge server + in-page driver).
- `git config core.hooksPath .githooks` is required once per clone: the pre-commit hook is the guard that keeps `state/*.json` commits and code commits apart.
- `scripts/SEASON BRIEFS.bat` and `scripts/ADP DIFF.bat` are run by Windows scheduled tasks on the laptop, not by the repo. SEASON BRIEFS (`python -m draftkit` briefs) overlaps the `nfl fantasy` commands and is a candidate for retirement — that decision is owed to the user; neither task has been touched. `scripts/YAHOO SYNC.bat` (also a scheduled task) keeps the committed Yahoo copy the fantasy commands read on a host without Yahoo credentials; `scripts/VEGAS REFRESH.bat` was deleted with the cron stack (DECISIONS #212), so its scheduled task, if still registered, has nothing to run.

Repo layout: `draftkit/` (pipeline + tracker modules), `manager/` (the Yahoo
and consensus layer under `fantasy/`, the trade radar, state in `state/`), `scripts/` (the Yahoo
draft rig — bridge server, in-page driver, pre-rank driver — and the
validation harness: replays, backtest, gates), `leagues/*.yaml` (league
facts), `config.yaml` (globals only), `tests/`, `data/raw` (API caches,
gitignored), `data/processed` (intermediates, gitignored), `tiers*.csv` +
`board*.md` (deliverables, committed), `reports/` (generated artifacts),
`DECISIONS.md` (the record).

## Auto-manager (retired 2026-10-08)

The in-season auto-manager's cron stack -- `weekly.yml` (planner, waiver
brief, scout, lineup backstop, healthcheck), `gate.yml` (the 15-minute check
gate) and the `python -m manager gate / cron / --module` entrypoints, with the
GitHub-Issue delivery behind them -- was retired on 2026-10-08 (DECISIONS
#212, the user's call). It had run only when dispatched by hand since
2026-09-25 (DECISIONS #109), and the fantasy commands answer the same
questions: use `nfl fantasy ...` (`lineup`, `waiver`, `trade`, `scenario`).
The last commit with the cron stack is b2341d3; git history is the undo.

What stays in `manager/` is what the fantasy commands import: the Yahoo API
client, sync and league source (`yahoo_api`, `yahoo_sync`, `yahoo_context`,
`yahoo`), the league context (`context`), the rest-of-season consensus and
FantasyPros feeds (`consensus`, `fantasypros`), the state store and the
decision ledger (`store`, `ledger`, `provenance`).

The trade radar (`trade_radar`, with `marginal`, `market`, `ecr`,
`waiver_brief`, `faab`, `usage`, `age_decay`) is kept pending the user's call
on trade search (repo sweep 2026-10-08): it searches the league for trades,
where `nfl fantasy trade` scores one named trade. Two manual entrypoints:

```
python -m manager --league keefamania yahoo-sync   # pull Yahoo into state/keefamania/yahoo/
python -m manager --league omnibeta trade-radar    # the trade search, printed; writes no state
```

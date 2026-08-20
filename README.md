# draftkit — Omnibeta Degens draft prep

Draft-prep pipeline + live draft tracker for Sleeper league **Omnibeta Degens**
(12-team, full PPR, 2 FLEX, 15-round snake, 120s clock).

> **Pre-draft cadence (settled 2026-08-19):**
> 1. **Daily, automated:** `draftkit adpdiff` runs at 9:00 AM via Windows Task Scheduler
>    ("draftkit ADP diff") — fresh FFC ADP snapshot, movers ≥15 picks in ≤4 days written
>    to `reports/adp_movers.md`. The diff is the news detector; no LLM involved.
> 2. **Night before (Saturday):** one deep research pass, fed by the movers list —
>    overrides only on dated, sourced facts (`reports/override_research.md` has the
>    format). Plus the full availability sweep (`data/external/availability.csv`).
> 3. **Morning of (Sunday):** re-check ONLY the compromised subset from the sweep —
>    preseason injury news breaks Fri/Sat and ADP is a trailing average, so
>    final-window recency is the whole edge. Then the DRAFT DAY icon at ~2:30 PM.
> 4. **Rounds 12–15 live:** ⛑ handcuff tags (backs up a ≤13-exp-game or
>    availability-flagged starter) are UI-only — the market blend already prices
>    handcuff option value, so they inform the human, never the engine.

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

**Before draft day** (in order):

1. Set `me.username` (or `me.user_id` / `me.draft_slot`) in `config.yaml`.
   Roster 12 / draft slot 6 is currently unclaimed and no Sleeper user
   "gabjew90" exists, so identity can't be auto-detected — see `verify` output.
2. Re-run `market` + `tiers` the morning of the draft (ECR/ADP move daily in
   August; every pull is cached ≤12–24h).
3. Optional: drop a fresh FantasyPros export at `data/external/fantasypros.csv`
   to override the auto-pulled ECR (see `data/external/README.md`).
4. Join a [Sleeper mock lobby](https://sleeper.com/draft) and run
   `track --draft-id <id>` once to see the tracker against a live picks feed.

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

- Snake, 15 rounds, 120s timer, 12 teams, no third-round reversal, CPU
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
   pure market projections have no edge. Default: 55% model (2025 league-scored
   PPG, shrunk by games played, adjusted by a within-position regression on
   WOPR + high-value touches) + 45% market-implied (per-position log-curve fit
   of projection vs. ECR). Players with no 2025 data are 100% market-implied
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
6. **Replacement baselines RB40/WR60/QB12/TE12** as specified (2-FLEX
   full-PPR skews flex toward WR); configurable in `config.yaml`.

## Strategy notes the numbers currently support

- 13 skill picks for 8 skill starters + 5 bench: startable depth > lottery
  tickets, but the IR slot (see above) makes exactly one injury stash free.
- TE and QB cliffs are steep this year: after the top-2 TEs the position falls
  off hard (tier 3 is a 40+ point drop), while QB tier 3 is deep — the model
  consistently waits on QB into rounds 7–9 and it costs almost nothing.
- The 120s clock + CPU autopick means the tracker's precomputed
  recommendations matter: everything renders instantly from tiers.csv; there
  are no network or model calls in the on-clock path.

## Testing

```bash
python -m pytest tests/          # snake math, needs, tiering, scoring, ID matching
python -m draftkit simulate --slot 6   # full-draft dry run through the real tracker code
```

Repo layout: `draftkit/` (pipeline + tracker modules), `tests/`, `config.yaml`
(all knobs), `data/raw` (API caches, gitignored), `data/processed`
(parquet intermediates, gitignored), `tiers.csv` + `board.md` (deliverables,
committed).

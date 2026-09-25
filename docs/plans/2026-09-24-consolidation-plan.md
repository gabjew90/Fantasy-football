# Consolidation plan: one data layer, four models, one CLI, one skill

Agreed 2026-09-24. Supersedes nothing; the props engine's own plans stay in force.

## Goal

Two use cases -- discretionary prop bets and discretionary fantasy decisions --
served by one repo, one CLI and one chat skill, with as few models as the
validation record justifies, and a structure where improving a model means
replacing a versioned component behind a fixed contract, never adding a
parallel engine.

Out of scope by the user's decision: FAAB and transaction-cost modelling.

## 1. Target structure

```
core/         the one data layer: nflverse fetch + cache (age-checked), Sleeper
              players, ID crosswalk (draftkit/ids.py promoted), schedule, ONE
              scoring function from the league yaml, lines (Sleeper Picks + Odds
              API), injuries, the snapshot manifest (what was fetched, when,
              coverage), the component registry
props/        the pricing engine as it stands, plus record / settle / scorecard
fantasy/      sources/   projection sources behind one protocol
              decision/  lineup, marginal value, waiver, trade, scenario
              evidence table, gate (computed from the manifest), ledger
draft/        draftkit's draft-only code, frozen
experiments/  one-off studies; outputs gitignored; 30-day shelf life
nfl.py        status | props game|slate | fantasy lineup|waiver|trade|scenario | draft
```

## 2. Models: from nine to four

Keep:
- `receiving_hier_v2` (receptions, receiving yards) -- props
- `rush_yds_v0` -- props
- the `anytime_td` stack, layers 1-4, as one model -- props
- one fantasy projection: a consensus of Sleeper, FantasyPros and ESPN, plus
  `market_points` (market-implied points from Sleeper Picks lines) where
  two-sided lines exist. No in-house fantasy model.

Delete (each in the PR that retires it, after its replacement has a week of use):
- draftkit `model_projection` and its role gate (retired; lost its own backtest).
  **Frozen until August draft prep** (user decision 2026-09-25, DECISIONS #108): still
  Omnibeta's draft source and the path the board byte-identity check runs; deleted when
  the draft switches to `fantasy/sources`.
- manager `xfp.py` (research only, no live consumer)
- the props fantasy export as a separate deliverable (it becomes the scoring step
  of `fantasy scenario`)
- the duplicate Sleeper-projection fetcher, the name-based ECR joiner, five of
  the six scoring functions, four of the five name normalizers

Freeze: the draft engine, under `draft/`, reading `fantasy/sources` in August.

## 3. The contract

- **Every projection is a distribution.** A source returns, per player-week,
  quantiles (p10, p25, p50, p75, p90) or joint samples (N draws, correlated
  within a team). Consumers accept either; a mean-only source is a narrow
  distribution. Adding dispersion or correlation is then a version bump, not a
  rewrite.
- **Uncertainty is reported in three parts:** source disagreement, model
  dispersion, role uncertainty. Templates keep them apart.
- **The ledger grades intervals, not only medians** (p20-p80 coverage), so a
  better dispersion model can win on the record.

## 4. Guardrails, enforced by tests and CI

1. Projection sources live only in `fantasy/sources/`, prop models only in
   `props/models/` (props adopts last; until then its scripts directory). A test
   fails on any module elsewhere that fetches play-by-play, emits projection
   columns or computes fantasy points.
2. A registry in code (`core/registry.py`): every source and model has a status
   (`live`, `shadow`, `retired`) and a validation artifact. Unregistered
   component: fail. Missing artifact: fail. A `retired` entry is deleted in the
   PR that retires it.
3. Knobs live in yaml; tuning is a config diff plus a harness report.
4. Promotion to `live` requires a measured harness delta. Props has its harness;
   fantasy gets a consensus-weight backtest and the graded ledger.
5. Byte-identity checks per model, so tuning one cannot move another.
6. `experiments/` with an age check.
7. `nfl data ...` is the labelled escape hatch: anything computed outside a
   registered command is `UNVALIDATED -- AD HOC`, never enters the ledger, and
   becomes a PR if it is asked for twice.
8. These rules are written into CLAUDE.md.

A methodology overhaul (not just a re-tune) follows the same path: a short
design note naming the hypothesis and the metric that would show it worked; the
new version in shadow, same directory, same protocol; head-to-head on the
harness; promote and delete, or delete.

## 5. One skill, harness only

The skill runs the bootstrap, holds the credentials (Odds API key, Yahoo
bundle), prints the engine disclosure line, asks one clarifying question when
the league or week is genuinely ambiguous, and writes prose from the report.
The routing table, report templates, evidence rules, labels, horizon weighting
and gate live in the repo and ship with the tag.

| The user asks | The skill runs |
|---|---|
| props for a game / the slate | `nfl status` then `nfl props game X@Y` or `nfl props slate` |
| waiver targets, or vs my bench | `nfl fantasy waiver --league L --pos RB [--vs-bench] [--horizon stream\|season]` |
| this week's start/sit | `nfl fantasy lineup --league L --week N` |
| player if teammate X is out | `nfl fantasy scenario --league L --player P --out X` |
| both a fantasy and a betting question | both commands, two labelled sections |

## 6. The user's decision framework, as components

### Start/sit -- pick the player with the better expected outcome for my situation this week

| Question | Component | State |
|---|---|---|
| 1. Opportunity | evidence table from play-by-play, by player ID | exists; air yards and inside-10 added from the props prior-builder |
| 2. Role stability vs normal noise | per-metric week-to-week noise bands | build |
| 3. Scoring environment | implied total and spread from `core` lines | exists |
| 4. Matchup, opponent-adjusted, weighted low | schedule-adjusted defense ratings | build (replaces unadjusted `defense.py`) |
| 5. Game-day validity | injuries, practice status, Questionable both ways | exists |
| Decision rule: likely win -> better floor, likely loss -> better ceiling | win probability (`scout`) + projection quantiles | skeleton exists; real once section 3 lands |

### Waiver / drop -- raise expected points over the relevant horizon

| Question | Component | State |
|---|---|---|
| Step zero: streamer or league-winner | `--horizon stream|season` argument first; a data rule only if it earns it | build |
| 1. Role vs output | usage deltas against box score | exists |
| 2. Role duration; P(role holds through the playoffs) | base-rate table by cause of role change, 2022-25 | build; ships in shadow |
| 3. Lineup improvement, counting only weeks either would start | `marginal.py` per matchup week / per playoff week | exists; per-week mode to add |
| Standing adjusts the weighting | one tilt from win probability and standings | build (after section 3) |
| Speculative adds discounted by P(role materializes) | from item 2 | build with item 2 |

### Teammate-out scenarios

The props engine's `--assume-out` path and its measured absence rule, scored
under the league's rules, beside observed history in the games the teammate
actually missed and the repriced market where lines have moved. The QB-out case
is provisional until a QB reallocation rule is validated; it is the first
tuning item.

## 7. Sequence -- one PR per step, tested and code-reviewed before push

0. Done (props-v1.17): capture inputs refresh; settle whenever the cron fires.
1. `core/`: age-checked fetch + cache, crosswalk, one scoring function, snapshot
   manifest, registry and guardrail tests. Existing callers of the duplicated
   scorers move onto `core.scoring`.
2. Done: distribution contract; `fantasy/sources/` with `sleeper_weekly` and
   `market_points` (migrated); the measured range model `dispersion_v0`.
   The rest-of-season consensus moves in with step 4, which first needs it.
3. Done: `nfl` CLI with `status`, `fantasy lineup` (existing optimizer,
   P(win)-maximising swaps), `fantasy scenario` (the engine's absence path);
   the gate reads the manifest; `--record` writes a ledger row (scheduled
   runs only; chat is read-only).
4. Done: the evidence table with calibrated role-change flags (4a), and
   `fantasy waiver` with the horizon as an argument, standing, the blocking
   rule and the role cause (4b). Still open from section 6: the opponent-
   adjusted matchup read (weighted low by design) and the role-DURATION
   probability (a base-rate study), both to be built behind the registry.
5. Done in code (nfl-v1.0): `skill/` (release spec, bootstrap, build) and `CHAT.md`;
   the user builds and installs the skill, then retires the two old ones. One skill; the two retired. The bootstrap fetches the whole repo at the tag (core/, fantasy/,
   draftkit/, manager/ and the props engine, not only props/engine), and passes the skill's Yahoo
   credentials through as this repo's env vars and token file, so Keefamania reads live from chat.
6. Props adopts `core` behind byte-identical checks; draft moves under
   `draft/`; retired paths deleted; Actions slimmed to props capture/settle,
   the Tuesday brief and ledger grading. **2026-09-25:** the props-only loader
   and xfp deleted; model_projection frozen until August (DECISIONS #108);
   the user asked for NO scheduled fantasy notifications, so the fantasy
   schedules are off entirely and the scheduled `nfl fantasy lineup
   --record` is dropped (DECISIONS #109) -- Actions runs props only.
   The engine stays self-contained (props glue adopts core: settle fetches
   through core.fetch); the draft move waits for August (DECISIONS #110).
   Step 6 is closed.
7. Replaced by docs/plans/2026-09-24-yardage-harness.md (the yardage props to the TD model's
   standard; the QB-out rule becomes one question inside it). Originally: first tuning items on
   the new rails: the QB-out reallocation rule, then
   whatever the ledger shows is weakest.

## 8. Risks

- Step 1 touches everything that fetches data. Props adopts last, behind
  byte-identity checks, for that reason.
- The fantasy harness does not exist yet; until it does, a fantasy methodology
  change is an argument, not a measurement.
- The role-duration model will be thin early. It ships as `shadow` with its
  base rates visible, never as a probability a drop is decided on.
- The guardrails catch structure, not judgment. "Promote or delete" for an
  interesting but unproven shadow component is a human call.

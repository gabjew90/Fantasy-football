# props/ — NFL sportsbook prop research and its historical record

This subtree is the sportsbook side of the repo. It is deliberately separate
from `draftkit/` and `manager/`, which own fantasy roster decisions. The two
answer different questions and must not share logic: a fantasy start/sit is a
roster allocation under league scoring, a prop call is a price comparison
against a book. `tests/test_boundary.py` fails the build if anything here
imports `draftkit` or `manager`.

## Why it exists

The model behind these calls has been backtested against 2025 outcomes for
receptions and receiving yards. It has **never** been tested against real
sportsbook prices. Nothing here is a validated betting edge, and a positive
estimated edge is not evidence of one. The only thing that can settle the
question is a record: every call, the price it was made at, where the line
closed, and what actually happened.

That record is what this subtree builds.

## Layout

```
props/
  engine/            the nfl-prop-research skill, vendored
    scripts/         score_game.py, score_week.py, model.py, odds_client.py, ...
    resources/       prior-season tables, model registry, calibration, methodology
    SKILL.md         the skill's own contract; the authority on how calls are made
  guard.py           stdlib-only window guard for the workflow
  record_run.py      files a scorer run's artifacts into the record
  settle.py          grades recorded calls against nflverse outcomes
  scorecard.py       calibration, tier validity and CLV rollups
  persist.py         append-and-dedupe record writer, three declared modes
  record/            the historical record (committed)
    predictions/<season>/wk<NN>.jsonl
    lines/<season>/line_archive_<season>.jsonl
    settled/<season>/settled_<season>.csv
    scorecard.md
  tests/             boundary and hygiene tests
```

`engine/resources/credential.env` is **not** vendored. This repo is public. The
workflow supplies `ODDS_API_KEY` from repo secrets; by default the engine
prices from Sleeper, which needs no key and has no quota.

## The record schema

A prediction row is one priced line at one moment. The fields exist so a call
can be re-derived later, not just scored:

| field | why it is kept |
|---|---|
| `season`, `week`, `event_id`, `game` | identity; the join key to outcomes |
| `book`, `market`, `player`, `team`, `slot` | what was priced, and the role the model assigned |
| `line`, `side`, `price` | the bet as it would have been placed |
| `p_model`, `p_novig`, `gap`, `ER` | the disagreement, and its size |
| `model_mean` | the projection behind the probability, for diagnosing a miss |
| `tier`, `decision`, `clears_edge_rule_if_validated` | what the rules said at the time |
| `new_team`, `questionable`, `flag` | the known weaknesses of that specific call |
| `engine_hash`, `engine_tag` | the build of `engine/` that made the call |
| `price_hash` | the part of that build that can change a price (since 2026-09-25) |
| `model_state` | the engine's own per-market label (`receiving_hier_v1`, …); it is hand-written and has been wrong, so it is not a version |
| `snapshot_type` | `decision`, `open` or `close` |
| `logged_at_utc`, `last_update` | when the call was made and when the book last moved |
| `commence_time`, `minutes_to_kickoff` | when the game starts, and how far out the call was made |

Rows are keyed on `(season, week, event_id, book, market, player, side, line,
snapshot_type, engine_hash)` and de-duplicated on write, so re-running a game
is safe — and a new engine never overwrites an older engine's calls. A line
archive row keeps the same key without `engine_hash`: a book quote is a market
fact, so the stamp on it says which build captured it, not which model
produced it.

### Which engine wrote a row

`engine_hash` is a sha256 over `engine/`: every file, line endings normalised
to LF, paths sorted bytewise, with `resources/credential.env` and build caches
excluded. That definition is what lets three copies of the same engine agree —
this repo's CRLF checkout, the LF tree on an Actions runner, and the installed
Claude skill, which carries the credential file the public repo must not.
Verified on all three: `911a3de4…`.

`engine_tag` is the release name from `engine.lock.json`, attached **only**
when the computed hash matches the lock. An edited engine still records rows;
they carry the real hash and no tag. The hash is never read from the lock — a
lock-sourced hash would keep claiming `props-v1.0` after the engine changed,
which is the one lie the stamp exists to prevent.

`price_hash` is the same formula over the part of `engine/` that can change a
price: `score_game.py`, `score_week.py` and every script they import or launch
(read from their source, so a new module is picked up by itself), plus every
data file under `resources/` but the prose (`*.md`). A docs, test or
offline-tool edit changes `engine_hash` and leaves `price_hash` alone. The
call rule and the scorecard group on the **pricing model**
(`engine_version.model_id`: the row's `price_hash`, else the one
`engine_prices.json` maps its `engine_hash` to, else the `engine_hash`
itself), so two releases that price identically are one record, and a
scorecard section names every release in it. `engine_prices.json` covers the
rows written before `price_hash` existed; each entry is computed from its
release tag's tree, and CI recomputes all of them.

```bash
python props/engine_version.py print                     # hash, tag, price hash, file count
python props/engine_version.py verify                    # IDENTICAL or DRIFT (names the files)
python props/engine_version.py write-lock --tag props-v1.1
python props/engine_version.py price-map [--check]       # engine_prices.json from the props-v* tags
```

### What counts as one call

The record keeps every priced line at every moment, which is right: a line
that moves is history worth having. A scorecard counts decisions, and those
are not the same thing. Week 2 holds 33 rows for a 32-line board because one
rush-yards Under was captured at 58.5 and then at 59.5 thirteen minutes
later.

So a **call** is the `decision` row with the latest `logged_at_utc` for one
(season, week, event, book, market, player, engine). `side` and `line` are
attributes of the call, not part of its identity. `open` and `close` rows are
never calls, so a game captured only inside the closing window has no call --
a price-only snapshot is not a decision. `props/calls.py` is the only place
that rule lives; `settle.py` and `scorecard.py` both import it.

`settle.py` grades every priced line and flags which one was the call
(`is_call`), because a superseded line beside the one that replaced it is what
makes the settled CSV self-explaining. `scorecard.py` counts only calls.

Settled rows add `actual`, `result`, `status`, `won`, `pnl_per_100`,
`is_call` and `join_method`. A player who did not play settles as `dnp`, not a loss, because
a book would have voided the prop; folding voids in as losses would bias every
hit rate downward. Rows whose name could not be joined are kept with status
`unjoined` and reported, never silently dropped.

They also add the fields that say WHY a call missed, which is the only reason
a record is worth keeping past the hit rate:

| field | question it answers |
| --- | --- |
| `miss` | actual minus `model_mean`: how far off, and in which direction |
| `targets`, `carries`, `target_share`, `air_yards_share`, `wopr` | was the ROLE the model assumed the role he got? |
| `opponent`, `team_points`, `opp_points`, `game_total` | or was the role right and the GAME the problem? |

Both come free: the usage columns are in the weekly stats file settle already
downloads, and the scores are in the schedule the guard already caches. A
diagnostic never gates a settle — a schedule that cannot be read costs the
context columns and nothing else.

## Running it

```bash
# score a game and file the result (chat container or laptop)
python props/engine/scripts/score_game.py --away MIA --home SF --season 2026 --week 2
python props/record_run.py --dir /mnt/user-data/outputs --snapshot-type decision

# grade a completed week once nflverse publishes (Tuesday morning ET)
python props/settle.py --season 2026 --week 2

# rebuild the rollups
python props/scorecard.py --season 2026
```

The scorecard groups by engine. With more than one version in the record it
prints a section each and **no** combined total: pooling two models' calls
produces one number that describes neither. `--pool` is the explicit override
for when you have decided the versions are comparable.

`persist.py` declares its mode on every write. `local` means the rows are on
disk but not committed; only `github` (inside the workflow) persists them.

## Releases, and how a model change reaches production

Three rules:

1. **The repo is the only engine.** `props/engine/` at a tagged release is the
   model. A chat session fetches it every session through the loader; the
   workflow exports it from the tag on every capture. Nothing runs an engine
   that is not in this repo.
2. **Chat is read-only; the workflow is the only writer.** Opening sweep
   Thursday, decision captures inside six hours of a kickoff, closing capture
   inside one hour, settle Tuesday, scorecard after. No chat run is logged,
   and none needs to be.
3. **Merging to `main` changes nothing that runs.** The engine switches when
   a tag is cut and `engine.lock.json` is bumped, which is a separate,
   one-line pull request.

`props-v1.1` is the worked example. Two engine defects: `backtest.py` used
the pandas 2.2 `include_groups` keyword, which is a `TypeError` on the 1.5.3
this repo pins, so the paired bootstrap crashed; and `score_game.py` stamped
`receiving_hier_v1` onto every row for a model the registry and the report
both call v2, so the record was mislabelled at the one field meant to scope a
later fix.

```bash
git switch -c props/v1.1 origin/main
# edit props/engine/... and the model_registry.md entry, citing the tag
venv\Scripts\python.exe -m pytest props/tests -q
python props/engine_version.py print          # the hash moved; the tag is now withheld
python props/engine_version.py write-lock --tag props-v1.1
python props/engine_version.py verify         # IDENTICAL (props-v1.1)
gh pr create                                  # props-ci runs the tests and the CRPS smoke
# merge, then cut the tag on the merge commit -- never on a branch commit a
# squash would orphan, and never move an existing tag:
git fetch origin && git tag -a props-v1.1 -m "..." origin/main && git push origin props-v1.1
```

Until that tag exists, `record_run.py` stamps the computed hash and leaves
`engine_tag` empty, and the capture workflow falls back to `main`'s engine
with `engine_source=main-fallback` on every row. Both are loud and neither
loses a capture.

Rebuild and reinstall the `.skill` only when `bootstrap.py` or the loader's
`SKILL.md` changed, or to refresh the vendored fallback:

```bash
python props/build_skill.py --credential "<path outside this repo>/credential.env" \
    --out dist/nfl-prop-research.skill
```

That file carries the API key. Treat it as a secret; `dist/` is gitignored
and a test fails the build if a credential is ever tracked here.

## The workflow

`.github/workflows/props.yml` runs on its own concurrency group
(`props-record`) and touches only `props/`, so it cannot collide with the
fantasy workflows on `manager-state`. A 15-minute tick hits `guard.py` first,
which installs nothing and exits in under a second unless there is work.

| Window | When | Snapshot |
|---|---|---|
| open | Thursday 22:00–24:00 UTC, once per ISO week | `open` |
| capture | a kickoff within six hours | `decision` |
| capture | a kickoff within 60 minutes | `close` |
| settle | Tuesday 14:00–16:00 UTC, once per ISO week | grades the week |

The windows are hours wide because GitHub fires these crons a median 128
minutes late (DECISIONS #70); a marker in the Actions cache is what stops the
other seven ticks inside a window from running again. The `close` snapshot is
what closing-line value is computed from, and it is the one thing a chat
session cannot reliably produce, since the container cannot schedule itself.
The `open` sweep is the other end of that measurement: by the time the
six-hour capture window opens, the board has already absorbed most of the
week's news.

## What the record is for

1. **Calibration.** When the model says 65%, does it hit 65%?
2. **Tier validity.** `WEAK` encodes the assumption that a large model/book gap
   means the book knows something. That is a prior, not a proof. The record
   grades WEAK calls as their own bucket so the assumption can be tested.
3. **Closing line value.** Whether the line moved toward the call. CLV is the
   earliest reliable signal because it does not require the bet to win.
4. **Diagnosing a bad run.** A hit rate says something is wrong; it never says
   what. Sorting losing calls by `miss` and reading `target_share` beside
   `game_total` separates the two failures that need different fixes — a role
   the model priced wrong, and a game script nothing could have priced. Lead
   time (`minutes_to_kickoff`) separates a third: calls that were stale rather
   than wrong.

Roughly 150 logged decisions with paired closing lines is the point at which
these questions start to have answers. Until then the scorecard is a log, not
a verdict.

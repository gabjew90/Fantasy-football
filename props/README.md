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
| `model_state` | the engine's own per-market label (`receiving_hier_v1`, …); it is hand-written and has been wrong, so it is not a version |
| `snapshot_type` | `decision`, `open` or `close` |
| `logged_at_utc`, `last_update` | when the call was made and when the book last moved |

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

```bash
python props/engine_version.py print                     # hash, tag, file count
python props/engine_version.py verify                    # IDENTICAL or DRIFT (names the files)
python props/engine_version.py write-lock --tag props-v1.1
```

Settled rows add `actual`, `result`, `status`, `won`, `pnl_per_100` and
`join_method`. A player who did not play settles as `dnp`, not a loss, because
a book would have voided the prop; folding voids in as losses would bias every
hit rate downward. Rows whose name could not be joined are kept with status
`unjoined` and reported, never silently dropped.

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

`persist.py` declares its mode on every write. `local` means the rows are on
disk but not committed; only `github` (inside the workflow) persists them.

## The workflow

`.github/workflows/props.yml` runs on its own concurrency group
(`props-record`) and touches only `props/`, so it cannot collide with the
fantasy workflows on `manager-state`. A 15-minute tick hits `guard.py` first,
which installs nothing and exits in under a second unless a kickoff is within
six hours. Inside 60 minutes of kickoff the capture is recorded as `close` —
that snapshot is what closing-line value is computed from, and it is the one
thing a chat session cannot reliably produce, since the container cannot
schedule itself.

## What the record is for

1. **Calibration.** When the model says 65%, does it hit 65%?
2. **Tier validity.** `WEAK` encodes the assumption that a large model/book gap
   means the book knows something. That is a prior, not a proof. The record
   grades WEAK calls as their own bucket so the assumption can be tested.
3. **Closing line value.** Whether the line moved toward the call. CLV is the
   earliest reliable signal because it does not require the bet to win.

Roughly 150 logged decisions with paired closing lines is the point at which
these questions start to have answers. Until then the scorecard is a log, not
a verdict.

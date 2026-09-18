---
name: nfl-prop-research
description: Quantitative NFL sportsbook player-prop research for the NFL Gambling Project. Fetches the released engine from the project repository and runs it, so a chat session, Claude Code and GitHub Actions all run byte-identical code. Use for prop valuation, fair odds, edges, tiers, closing-line capture and slate questions. Not for fantasy football start/sit, waiver, trade, or draft decisions -- those belong to nfl-fantasy-research.
---

# NFL Prop Research (loader)

This skill is a loader, not the engine. The engine lives in the project
repository at a tagged release, and this fetches it. That is deliberate: the
engine used to be edited here, in a chat session, with no history, no tests
and no way to tell which version produced which row of the betting record.
Now there is one engine, it is versioned, and every recorded call names the
build that made it.

## Step 0, every session: load the engine

```bash
python scripts/bootstrap.py
```

It prints, as its last lines:

```
ENGINE_DIR=/tmp/nfl-prop-engine/props-v1.0
ENGINE_TAG=props-v1.0
ENGINE_HASH=911a3de45e31...
ENGINE_SOURCE=fetched
```

Export `ENGINE_DIR` and use it for everything that follows. Do not run any
script from this skill's own directory except `bootstrap.py`.

## Then obey the engine's own contract

`$ENGINE_DIR/SKILL.md` is the authority on how calls are made -- markets,
tiers, the edge rule, the credential order, the report format, the survival
pick, every guardrail. Read it and follow it. This file does not restate it,
because a second copy of a 300-line contract is a second copy to drift.

Every path in it is relative to `$ENGINE_DIR`:

```bash
python "$ENGINE_DIR/scripts/score_game.py" --away MIA --home SF --season 2026 --week 2
python "$ENGINE_DIR/scripts/score_week.py" --season 2026 --week 2 --skip-started
```

Outputs still go to `/mnt/user-data/outputs` unless `NFL_OUT` says otherwise.

## Disclose which engine ran

**The first line of every reply names the engine**, because a number from an
unknown version is not a record:

> engine props-v1.0 (911a3de, fetched)

If `ENGINE_SOURCE=VENDORED_FALLBACK` the fetch failed and the bundled copy
ran instead. Say that, with the reason and the tag it could not reach:

> engine VENDORED FALLBACK (911a3de) -- could not reach props-v1.0:
> NETWORK_ENVIRONMENT_BLOCKED. This may not be the current model.

`bootstrap.py` prints that banner itself; do not suppress it. An old engine
is usable. An old engine passing as the current one is not.

## The credential

Unchanged from the engine's contract: proxy URL, then `ODDS_API_KEY`, then a
key given in the conversation, then the bundled `resources/credential.env`.
The bootstrap copies this skill's local credential file into the fetched
engine's `resources/` so the engine's own default finds it. It is never
printed, never quoted, never cited as a source, and it is not in the public
repository.

## This session writes nothing to the record

The betting record is written only by the project's scheduled workflow, which
captures opening, decision and closing snapshots on a clock a chat container
cannot keep. Produce the analysis and the report; do not try to file rows.

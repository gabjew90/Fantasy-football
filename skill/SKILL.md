---
name: nfl-research
description: NFL fantasy football and player props for the user's two leagues (Omnibeta on Sleeper, Keefamania on Yahoo). Use for ANY question about an NFL player, game or fantasy decision -- how a player looks this week, who to start (X or Y, what if I start X, set my lineup), waiver adds and drops at any position including defense and kicker, streaming, trades and injured players, how a player does if a teammate is out, rosters, records and standings; and player props -- a player's lines, the chance he clears any line, the best plays in a game or this week, a must-win pick, how a game projects. Runs the released engine from the project repository with live league data, so its numbers are the engine's.
---

# NFL research (harness)

This skill is a harness, not the engine. The engine, the routing table and
every output rule live in the project repository at a tagged release. This
fetches that release, puts the credentials beside it, and hands over.

## Step 0, every session

```bash
python scripts/bootstrap.py
```

Its last lines:

```
REPO_DIR=/tmp/nfl-release/<tag>
RELEASE_TAG=<tag named in nfl.lock.json on main>
RELEASE_HASH=<sha256 of the release>
RELEASE_SOURCE=fetched | cached | fetched-unverified | VENDORED_FALLBACK
DEPS=ok | installed: ... | missing: ...
YAHOO=live | absent ...
ODDS_KEY=present | absent ...
HARNESS=current | updated <id>    this loader updates itself: when the lock
                                  pins a newer harness, the pinned copy is
                                  fetched, verified and run (no reinstall)
FETCH_ROUTE=file by file (...)    only when the tarball host refused and the
                                  release came from raw.githubusercontent.com,
                                  still verified against the lock -- the
                                  current release, not a fallback
```

Then read `$REPO_DIR/CHAT.md` and obey it. It says which command answers
which question, how the reply is written, and what chat must never do. This
file does not restate it: a second copy of the rules is a second copy to
drift.

Do not run anything from this skill's own directory except `bootstrap.py`.

## Disclose which release ran

`$REPO_DIR/CHAT.md` decides how replies name the release: normally it is
recorded in the transcript and the log, not recited in every reply. The
exceptions are the ones that matter: `fetched-unverified` (a `--tag` other than
the lock's, nothing checked it) and `RELEASE_SOURCE=VENDORED_FALLBACK` (the
bootstrap printed a banner with the reason and the tag it could not reach) go
at the top of every reply. An old release is usable; an old release passing as
the current one is not.

## Credentials

`resources/credential.env` (the Odds API key -- optional: Sleeper is the
primary price source, the Odds API only its fallback -- and the FantasyPros
key, for practice reports and the probability of playing) and
`resources/Yahoo_Fantasy_Connection.json` stay in this skill. The bootstrap
copies them into the release directory, where the engine looks. Never read,
print, quote or cite them.

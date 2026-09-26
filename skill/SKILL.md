---
name: nfl-research
description: NFL player props and fantasy football decisions for the user's two leagues (Omnibeta on Sleeper, Keefamania on Yahoo). Use for prop prices, fair odds and edges on a game or the slate; start/sit and this week's matchup; waiver targets at RB/WR/TE or against the bench; and how a player projects if a teammate is out. Fetches the released engine from the project repository and runs it, so chat, Claude Code and GitHub Actions run byte-identical code. Replaces nfl-prop-research and nfl-fantasy-research.
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
primary price source, the Odds API only its fallback) and
`resources/Yahoo_Fantasy_Connection.json` stay in this skill. The bootstrap
copies them into the release directory, where the engine looks. Never read,
print, quote or cite them.

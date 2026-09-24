# How chat answers football questions

This is the contract the `nfl-research` chat skill obeys. It ships inside the
release (skill/release.py), so a change here reaches chat only when a new
`nfl-v*` tag is cut and `nfl.lock.json` names it. The installed skill is a
harness: it fetches this release, holds the credentials and reads this file.
Nothing about how a question is answered lives in the installed skill.

Every command below runs from `$REPO_DIR` (the bootstrap prints it):

```bash
cd "$REPO_DIR" && python nfl.py <command>
```

## The two leagues

| League | Platform | Name to pass |
|---|---|---|
| Omnibeta | Sleeper | `--league omnibeta` |
| Keefamania | Yahoo (live API when the bootstrap printed `YAHOO=live`) | `--league keefamania` |

A fantasy question that does not say which league, and whose context does not
settle it, gets ONE clarifying question. The week is never asked: every
command resolves the current week itself; pass `--week N` only when the user
names a week.

## Routing

| The user asks | Run |
|---|---|
| props for a game | `nfl.py status`, then follow **Props** below for that game |
| props for the slate / all games / today | `nfl.py status`, then **Props** with `score_week.py` |
| who to start / sit, this week's matchup | `nfl.py fantasy lineup --league L` |
| waiver targets at RB / WR / TE | `nfl.py fantasy waiver --league L --pos RB,WR --horizon H` |
| should I pick up X over someone on my bench | the same waiver run at X's position; find X in the candidate table and the cut it pairs with |
| how does X do if teammate Y is out | `nfl.py fantasy scenario --league L --player "X" --out "Y"` |
| is it too early / what is posted yet | `nfl.py status [--league L]` |
| a fantasy and a betting question together | both commands, two labelled sections, never mixed |

**Waiver horizon is step zero.** "Streamer", "this week", "bye fill" ->
`--horizon stream`. "Stash", "league winner", "rest of season", "playoffs" ->
`--horizon season`. Unsaid -> run both; lead with season and label which
horizon each recommendation serves.

**A named add outside the pool.** The waiver run scores a capped pool (the
best by consensus rate plus the biggest recent usage gains). When X is not
in its table, say X fell outside the evaluated pool and was not scored. Do
not estimate X's value in chat.

**Name resolution.** `scenario` exits 2 with `SCENARIO: ...` when a name
matches nobody, matches several players, names two teams, or the team is on
bye. Relay that message and ask; do not guess a player.

**No command covers it** (trades, draft, rest-of-season rankings, dynasty,
DFS): say the release does not model it. A further opinion is allowed only
labelled as outside the engine, and it cites no engine number it did not
print.

## Props

The props engine's own contract governs everything about a props answer --
markets, tiers, the edge rule, the credential order, the report format, the
survival pick:

```bash
export ENGINE_DIR="$REPO_DIR/props/engine"
```

Read `$ENGINE_DIR/SKILL.md` and follow it. Its paths are relative to
`$ENGINE_DIR` (`python "$ENGINE_DIR/scripts/score_game.py" --away MIA --home SF`).
`nfl.py props game MIA@SF` and `nfl.py props slate` run the same scripts.

Run `nfl.py status` first. When it says a game's lines are thin or the run is
early, say so before any price.

## Fantasy answers

1. **The gate line comes first**, verbatim: `LEAGUE DATA GATE: PASS`, or
   `LEAGUE DATA GATE: FAIL -- <what> -- the verdict below is CONDITIONAL`.
   After a FAIL, every recommendation is stated as conditional on the named
   failure, in the sentence that makes it.
2. **Answer the question in the opening lines** -- who starts, who to add and
   who to cut, how the player projects without the teammate -- then the
   reasons.
3. **Reasons follow the user's framework, in its order.** Start/sit:
   opportunity, role stability against normal noise, scoring environment,
   matchup (weighted low), game-day status; then the decision rule the report
   applied (likely to win -> better floor, likely to lose -> better ceiling).
   Waiver: the horizon, role vs output, how long the role lasts, lineup
   improvement counting only weeks either player starts, standing.
4. **Numbers come from the report.** Mean, floor (p10), ceiling (p90),
   P(win), season points added, evidence rows. Never compute a new projection
   in chat, never average in an outside ranking, never round a close call
   into a clear one.
5. **Carry the report's labels and caveats**: `INSUFFICIENT_SAMPLE`,
   `partial` market boards, range caveats by position, "not covered yet",
   "assumed" missed weeks, provisional components. A caveat the report prints
   is not dropped from the reply because it is inconvenient.
6. **No betting language in a fantasy answer**: no edge, EV, fair odds, Kelly,
   stake or tier. A props number that informs a fantasy answer (the scenario
   command uses the props engine) is quoted as fantasy points.
7. **Scenario answers show both sides**: the model's change with the teammate
   out, and what was observed in the games he actually missed, with the
   sample size. When they disagree, say so; do not pick one silently.

## Every reply

- **First line names the release**, because a number from an unknown version
  is not a record:
  > release nfl-v1.0 (3f2a9c1, fetched)

  On the fallback path:
  > release VENDORED FALLBACK (b18a684) -- could not reach nfl-v1.1:
  > <reason>. This may not be the current model.
- Call `present_files` on the report the command wrote (the path it prints
  after `report:`).
- `DEPS=missing: ...` from the bootstrap: say which command could not run and
  why; do not answer from memory instead.

## Chat is read-only

Chat never passes `--record`, never commits, pushes or opens issues, and never
writes into the repository. The graded ledger and the betting record are
written only by the scheduled workflows. Report files in the outputs folder
are reference copies for the conversation.

## Credentials

The bootstrap places them; chat never reads, prints, quotes or cites them. If
`YAHOO=absent`, Keefamania commands stop with `no Yahoo credentials and no
synced copy`; the reply says the installed skill carries no Yahoo bundle and
answers nothing about that league.

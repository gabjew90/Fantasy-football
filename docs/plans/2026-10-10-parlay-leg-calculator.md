# Parlay-leg calculator (props/calc/): design note

*2026-10-10. DECISIONS #231. Status: approved by the user on 2026-10-10; building. Order agreed
then: a working rushing and receptions card end to end at the prototype settings first, tuning
after; no scope additions until that card exists.*

## What it is, and why it is an exception

A small calculator for the user's Sleeper parlays. Given a posted line and its two prices, it
says how much work (carries, passes thrown to him, completions) a player needs for that leg to
win often enough, and how often he has had that much work before. The user judges whether that
is realistic. It never says a line is wrong, never gives its own chance of a result, and never
labels a bet.

CLAUDE.md says "no parallel engines". This is a deliberate, user-approved exception:

- The props engine's card already has a "workload a Power Play leg needs" row (CHAT.md,
  DECISIONS #225), computed at the engine's own volume and efficiency models. The calculator
  answers a similar question with a much smaller model the user can read end to end: eight
  settings, plain history rows, no volume projection.
- It lives in `props/calc/`, imports nothing from `props/engine/`, and a test enforces that.
  The engine, its workflow and its record are untouched and keep running.
- It is judged by its own tests below, not by the engine's scoreboard rounds (#188, #202),
  because it makes no forecast for the scoreboard to grade.

**Hypothesis.** A player's chance of clearing a line, given the work he gets, is captured well
enough by: work varying around a stated average, his blended per-play rates, and real per-play
outcomes for players like him. **Metric.** The conversion test and the spread test below,
with pass marks fixed here before any data is read.

## Data

| Source | Use |
|---|---|
| nflverse play-by-play, 2016 to now (2016-17 only feed the pools for 2018) | carries, targets, catches, completions, per-play yards, depth of target, starting QB |
| nflverse schedules (`games.csv`) | spread, total, final score, game dates (the leakage cut) |
| nflverse weekly rosters | position, team by week, gsis/pfr/sleeper IDs |
| nflverse snap counts | marks games a player left early, in his history rows |
| Sleeper `lines/available?dynamic=true` | live two-sided lines and payout multipliers |
| Sleeper `v1/players/nfl` | Sleeper player id to gsis id |
| `props/record/lines/` (read only) | saved line history, for the "line near kickoff" and back-dated tests |

**How it is fetched (decided: `core.fetch`).** The CI guardrail fails any new module whose
source fetches nflverse or Sleeper data outside `core.fetch`, and its allowlist may only shrink.
`core.fetch` fetches the raw files directly (urllib, no nflreadpy), caches them with an age
check, is one of the three core modules `props/` may use, and shares no code with
`props/engine/`.

**Play definitions (the known traps).**
- Carry: `rush_attempt == 1`, not a two-point try. Kneels are QB plays and do not touch RB rows.
- Target: a pass attempt with a named receiver. Sacks have no receiver and are neither targets
  nor attempts.
- Receiving yards: `receiving_yards` is NaN on incompletions, so it is filled with 0 before any
  per-target figure. Yards per catch uses catches only.
- Passing yards: the sum of yards on completions (box-score passing yards; sack yards are not
  subtracted from the passer). Scrambles are runs, not passes.
- Leakage: a week is priced only from games whose kickoff is before that week's first kickoff.
  The cut takes a date and is unit-tested.

**Player matching.** Sleeper lines carry a Sleeper player id where present; it maps to a gsis id
through Sleeper's player table, then to nflverse. Where only a name exists (older rows of the
line archive), the match is a normalised name (lowercase, accents, punctuation and suffixes
removed, a short nickname table such as Joshua/Josh) checked against team, then a first-initial
plus surname fallback ("C.McCaffrey") also checked against team. Every miss is written to a
log, never dropped silently. A name match without the team agreeing is a miss.

## The calculator

All draws use fixed random numbers (common random numbers), so the chance is a smooth,
increasing function of the workload W and the search is a plain bisection.

**Rushing yards.** Carries ~ negative binomial with mean W and spread setting `carry_r`. Each
carry gains his blended yards per carry plus a residual drawn from real RB carries in the two
seasons before the priced week, centred on zero. The game total is multiplied by one
good-day/bad-day factor, mean 1, sd `day_sd` (lognormal, so it cannot go negative).

**Receptions.** Targets ~ negative binomial (mean W, setting `target_r`); each target is caught
at his blended catch rate.

**Receiving yards.** As receptions; then each catch is given a depth bucket from his own mix of
catches by depth, and its yards are drawn from real catches by his position in that bucket,
scaled so the average equals his blended yards per catch. Bucket cut points are fixed
constants: short (air yards under 5), medium (5-14), deep (15+).

**Passing yards.** Completions ~ negative binomial (mean W,
setting `completion_r`). Each completion's yards are drawn from real completions by starting QBs
(the team's QB with the most dropbacks in that game) in the two prior seasons, by the QB's own mix of completions by depth (same buckets), scaled so the
average equals his blended yards per completion. The card gives yards per completion as much
space as volume: his blended and season figures, the yards per completion the line needs at his
usual completions, and how often he has reached it.

**His rates.** Each rate is a blend of his own recent games and a position baseline:
w = n / (n + k), where n is his opportunities (carries, targets, catches, completions) in his
last 16 games played before the week, and k is one setting per rate. The baseline is the
position average over the two prior seasons (for receivers, position and depth bucket). The card
also shows his plain season rate beside the blended one.

**Search.** For a market and line, find W where the Over's chance equals:
(a) the book's no-vig chance, 1/m_over divided by (1/m_over + 1/m_under): "book expects";
(b) the Over's break-even, 1/m_over;
(c) the Under's break-even, 1/m_under (as the W where the Over's chance is 1 minus that).
A user target win rate replaces (b) or (c) when given; the default is break-even.

**Rate needed at his usual workload.** The search turned around: hold W at his trailing
4-game average and find the rate at which the Over's chance equals its break-even (or the
user's target). Rushing yards: yards per carry. Receptions: catch rate. Receiving yards: yards
per catch (at his blended catch rate). Passing yards: yards per completion. Same settings, no
new ones. (There is no "good day" row; the user dropped it.)

## Settings (8, the hard cap)

**Tuned settings, by name, with the running count (kept current):**

1. `carry_r`
2. `day_sd`
3. `target_r`
4. `completion_r`
5. `k_ypc`
6. `k_catch`
7. `k_ypr`
8. `k_ypcomp`

Count: **8 of 8.** A new one requires removing one, and that is the user's call.

One file, `props/calc/settings.yaml`, each line with a plain-English comment.

| # | Setting | Start value | What it does |
|---|---|---|---|
| 1 | `carry_r` | 16 | How much his carries swing from game to game around his average (higher = steadier) |
| 2 | `day_sd` | 0.15 | How much a whole rushing day runs hot or cold |
| 3 | `target_r` | 8 | How much passes thrown to him swing from game to game |
| 4 | `completion_r` | 10 | How much a QB's completions swing from game to game |
| 5 | `k_ypc` | tuned | How many carries of his own count as much as the RB average |
| 6 | `k_catch` | tuned | Same, for catch rate, in targets |
| 7 | `k_ypr` | tuned | Same, for yards per catch, in catches |
| 8 | `k_ypcomp` | tuned | Same, for yards per completion, in completions |

**Fixed, not tuned.** Every fixed constant is listed in the same yaml file under a
`fixed (not tuned)` heading, each with a plain-English comment. They do not count toward the cap
of 8. None may change after any test result has been read: a test pins their values, so a change
fails CI until the test is edited, which a review sees. The list:

- rate window: his last 16 games played before the priced week, across seasons
- pool window: the two seasons before the priced week
- depth buckets: short under 5 air yards, medium 5-14, deep 15+
- simulations: 20,000, fixed seed
- range: 10th to 90th percentile (the "80% range" in the tests)
- result groups: won by 8+, within 7, lost by 8+
- usual workload and gap: trailing 4 games played
- tested players: at least 3 prior games; lead back = team carry leader, top 3 by targets
- matchup: garbage time = offense win probability under 10% or over 90%; "only N games" below 4
  games; tiers of 8 teams
- league-wide game-story figures: all completed seasons from 2018 before the current one

Passing yards has no completion-rate setting because its workload is completions, not attempts.
Receiving and passing yards have no day factor; if their ranges fail the conversion test, the
failure is reported as it is.

## Outputs

**1. Leg card** (illustrative numbers, not real data; fits a phone screen; receiving cards say "passes thrown to him"):

```
JAVONTE WILLIAMS - rushing yards - Over 64.5 at -125
To win often enough (56%): about 20 carries at his usual 3.7 a carry
At his usual 16 carries he needs 4.6 a carry (his season: 3.9)
Book expects: about 18 carries
How often he gets 20+: this season 2 of 5
  Won by 8+: 1 of 2 | Within 7: 1 of 2 | Lost by 8+: 0 of 1
  With Nix starting: 2 of 4 | With Stidham: 0 of 1
His last games: 18-71, 22-94, 14-48, 19-60, 12-39
Gap: 4 carries more than his last-4 average (16)
```

Prices are shown as American odds converted from Sleeper's multiplier, with the multiplier in
brackets. The gap is the needed workload minus his trailing 4-game average; "book expects" stays
its own row. The gap's
reading only restates that ("needs 4 more carries than his recent average"); it never says
whether to play the leg.

**1a. MATCHUP block** (added 2026-10-10, user). Display only: nothing in it changes any number
on the card or becomes a setting. It sits under the card's numbers. Every line carries its
sample size, and a figure built on fewer than 4 games says "only N games". Each line is worded
against the card's question (the workload or the yards per carry needed), never as a verdict.
Illustrative numbers:

```
MATCHUP (DEN at KC, week 6)
Game: KC -3.5, total 44.5; DEN 20.5, KC 24.0 implied points
  He needs 20 carries; in his games as an underdog: 15.0 a game (3 games)
Injuries: Sutton out. With him: 16.2 carries (5 games); without: 19.0 (only 2 games)
  QB: Nix starting, no change
KC defense: 4.6 a carry allowed to RBs (rank 27 of 32, 5 games)
  He needs 3.2 a carry at his usual 16 carries; KC allows 4.6
KC allows RBs 24.1 carries, 102 yards a game (5 games)
Tiers (EPA per play and success rate, garbage time out, 5 games):
  DEN offense: run 2 of 4, overall 3 of 4 | KC defense: run 4 of 4, overall 2 of 4
```

How each line is computed, in `props/calc/matchup.py`, from play-by-play, rosters, injuries and
schedules read through the same data layer as the rest of the tool (nothing from the engine):

- **Game.** Spread and total from the schedule (latest before the card is made). Implied points:
  favourite = total/2 + spread/2, underdog = total/2 - spread/2. The relating line uses his own
  workload history split by whether his team was favoured.
- **Injuries.** The week's report (nflverse injuries file; Sleeper's player status when it is
  newer, with the source and date shown). Listed: a QB change (this week's expected
  starter differs from last game's), and any teammate who is a lead back or top-3 by targets
  (same pre-game definition as the tests) ruled out or doubtful. For each, his workload in games
  with and without that player this season and last, "without" meaning the teammate played zero
  snaps (snap counts). Where no "without" games exist, the line says so.
- **Opposing defense.** Rushing cards: yards per carry allowed to RBs. Receiving cards: yards
  per target and catch rate allowed to his position (WR, TE or RB). Passing cards: yards per
  completion and completions allowed. Rank 1 = fewest allowed, out of 32, season to date before
  the priced week.
- **Volume allowed.** Carries and yards (or targets and yards, or completions and yards) allowed
  per game to his position.
- **Tiers.** Each team's EPA per play and success rate for and against, garbage time excluded,
  season to date. Teams are ranked on each, the two ranks averaged, and the average cut into
  four tiers of 8 (1 = best). The card shows the unit that matters (run for rushing cards, pass
  for receiving and passing) and overall.

Fixed display constants, not settings and not tuned: garbage time = plays with the offense's win
probability under 10% or over 90% (nflverse `wp`); the "only N games" threshold of 4; tiers of
8 teams. They change no calculated number and are listed under `fixed (not tuned)`.

Weeks with fewer than 4 games show "only N games" for ranks and tiers and nothing more; last
season's figures are not substituted. The block never re-runs the search at the defense's
allowed rate: a matchup never changes a calculated number. The matchup lines point at the
card's "rate needed at his usual workload" row.

**2. Entry check.** For each leg, the game story it needs: rushing Overs want his team ahead,
passing and receiving Overs want it behind or a shootout, Unders the reverse. Rushing legs show
team carries by result group, passing and receiving legs team pass attempts by result group, each
under a heading that reads "League-wide (all teams, 2018 to last season), not this team's
tendency". Conflicts are
listed when two legs in the same game need stories that cannot both happen (team A ahead and
team A behind; team A ahead and team B ahead). Cost: total payout P, the hit rate each of n legs
needs, (1/P)^(1/n), and the average loss per unit staked if every leg is a coin flip,
1 - P x 0.5^n.

**3. Log** (the user, 2026-10-10: reuse, not a second log). `python -m props.calc entry` builds
each leg's card and logs the entry through `props/journal.py` (`make_power_play`); each journal
leg row also carries the card's numbers (`calc_bar`, `calc_line_implies`, `calc_usual`,
`calc_gap`, both multipliers, the settings) and `volume_unit`. `journal.grade` grades the legs
with settle's stats and rules, saves his actual workload from `volume_unit`, and stamps the late
line from the line history. Calc has no settle of its own. Open: the journal has no "needed vs
actual, legs won vs break-even, by gap" table; the user decides whether to add one.

**Line capture.** `python -m props.calc capture` saves the current Sleeper lines into the props
record's line history (`props/record/lines/<season>/line_archive_<season>.jsonl`) through
`props/persist.py`, in the engine's row format with `snapshot_type: "calc"` plus the gsis id, the
nflverse game id and the exact multiplier. It is run by hand; no workflow is added or changed.
Unmatched lines are logged in `props/calc/log/name_misses.jsonl` and not saved.

Commands, all under `python -m props.calc`: `leg`, `entry`, `capture`.

## Testing

**Tuning and held-out split.** Settings are tuned on 2018-2023 only. 2024-25 is held out and
read once, at the end; the date and result of that read are recorded in this note and in
DECISIONS. Pass marks below are fixed now and are not changed after a result is seen.

**When a test fails (the user's rule, 2026-10-10).** No setting, adjustment or new constant is
added to fix it. The failure is reported, and the card states it in plain words (for example
"ranges for receiving yards tested too narrow"); then the user decides. One retune of the
existing settings on 2018-23 is allowed before asking. The held-out years are never used to
retune.

**Pre-registered tuning.**
- `carry_r`, `target_r`, `completion_r`: grid, chosen on the spread test (2018-23) as the value
  whose 80% range coverage is nearest 80%.
- `k_*` and `day_sd`: grid, chosen to minimise the log loss of the conversion test's Overs on
  2018-23.
- Grids are written into the tuning script before it runs, and the script goes through the
  code-review skill before its output is read (CLAUDE.md).

**Who is tested.** Lead backs (the team's carry leader over his games before that week) and the
team's top three by targets over the same games, each with at least 3 prior games. The group is
chosen from history before the game, never from the game's own result.

**Conversion test.** Plug in the workload he actually got (no workload variation; per-play and
day variation on) and price the Over at lines 0.8x, 1.0x and 1.2x of workload x blended rate,
rounded to the nearest half. Pass, for each market: stated versus actual Over rate within
3 points in every 10-point band from 20% to 80%, each band holding 200+ games; and the 80% range
(10th to 90th percentile) holds 77-83% of actual results. A band with fewer than 200 games is
reported as untested and the market does not pass.

**Spread test.** With W = his trailing 4-game average, the 80% workload range holds 77-83% of
actual workloads.

**Round trip.** The "book expects" workload fed back returns the no-vig chance within 1 point.

**Game-story rows.** League-average team carries in each result group (won by 8+, within 7, lost
by 8+), taken from 2018-23, are within about 1.5 carries of the 2024-25 averages; the same test,
same 1.5 mark, for team pass attempts. On the card both blocks are labelled league-wide.

**Unit tests.** Odds conversion (multiplier, American, break-even, no-vig), name matching
(including Joshua/Josh, "C.McCaffrey", a team mismatch), the leakage cut, and the boundary rule
(no `props.engine` import anywhere under `props/calc/`, same AST pattern as
`props/tests/test_boundary.py`). Matchup: implied points, the garbage-time cut, rank direction, the
"without" split from snap counts, and a display-only test that builds every card with the
matchup data present and with it absent and asserts every calculated number is identical; a
structural test that the calculator module never imports `matchup.py`.

**Sanity targets** (the throwaway prototype, `carry_r` 16, `day_sd` 0.15, `target_r` 8; within
about 1 before tuning, not required after):

| Input | Over | Under | Book |
|---|---|---|---|
| ypc 3.97, rush 64.5, -125/-132 | 19.1 | 16.2 | 17.6 |
| ypc 4.19, rush 54.5, -127/-130 | 15.6 | 13.1 | 14.3 |
| catch 0.74, rec 6.5, -128/-128 | 10.2 | 8.7 | 9.4 |

## Repo rules that apply

- Every script goes through the code-review skill before its output is used; a review of the
  branch diff after each major step.
- Tests run in `props/tests/` so the existing props CI job runs them; dependencies stay within
  `props/requirements.txt` (pandas, numpy, requests).
- Registry: register as `prop_model`, status `provisional` ("untested until the conversion
  and spread tests pass on 2024-25"), promoted to `live` with the held-out write-up as evidence.
- Verification (#215): a separate agent re-derives the test write-ups and the first few real
  cards. Routine cards are deterministic arithmetic covered by the tests.
- Not in the chat skill. Reaching chat would need a release tag and lock bump; out of scope
  unless you ask.

## Decisions (the user, 2026-10-10)

All sixteen open questions were answered: as recommended, except where noted.

1. 2016-17 play-by-play is fetched for the pools only; tuning stays 2018-23.
2. Data is read through `core.fetch`.
3. Rate window: last 16 games played, across seasons.
4. Fixed constants do not count toward the cap, but every one is listed in the yaml under
   `fixed (not tuned)`, and none may change after a test result has been read (user's change).
5. The "good day" row is dropped; its example had no rule. Replaced by the rate needed at his
   usual workload (user's change).
6. Passing workload is completions.
7. No day factor for receiving or passing yards; the conversion test decides, and a failure is
   reported plainly.
8. Passing pool: starters' completions only.
9. Gap = needed workload minus his trailing 4-game average; "book expects" stays a separate row
   (user's confirmation).
10. Game-story rows are league averages, labelled league-wide on the card so they are not read
    as the team's tendency (user's change).
11. Registered `provisional`; verification covers the write-ups and the first few real cards.
12. Matchup constants as proposed, under `fixed (not tuned)`.
13. Sleeper's player status is shown when newer than nflverse's injury file, with the source.
14. The rate-needed row is added (it also replaces the good-day row, item 5).
15. Early weeks show "only N games" and nothing else.
16. The search is never re-run at a defense's allowed rate.

## Progress log

- **2026-10-10, step 2 done:** settings, odds, names, data layer (through `core.fetch`), Sleeper
  capture, leg log. Per-game totals match nflverse's weekly stats on every non-QB row of 2019,
  2023 and 2025 except 3 lateral plays (QB carries differ only by the kneels this tool leaves
  out). The live Sleeper endpoint is blocked from the build container, so the capture is tested on
  fixtures shaped like the payload the repo already parses; it has not yet run against the live
  endpoint.
- **2026-10-10, first rushing and receptions cards** at the prototype settings. Sanity targets
  reproduced: 19.1 / 16.3 / 17.7, 15.5 / 13.2 / 14.3, 10.2 / 8.6 / 9.4 (all within 0.1).
  Code review (high) on the branch: 10 findings, 9 fixed (settlement timing, zero-work games,
  trades, relative-import guard, registry entry, two-sided line check, caching, constants read
  from the yaml); 1 left (re-reading the line archive per leg: a few legs a week, not worth the
  code). The first two real cards (Javonte Williams week 5, Puka Nacua week 4) were re-derived by
  a separate agent from the raw files: no mismatches.
- **2026-10-10, step A (reuse):** leg log switched to the journal; calc's own log, settle and
  summary deleted; capture writes through persist into the line history (calc's 362 earlier
  captures moved there); kickoff times from zoneinfo; ESPN spread and total read through
  `core.fetch` with core/status.py's parsing copied (props may not import core.status).

## Held-out read

Not yet done. The date and the result of the one read of 2024-25 go here.

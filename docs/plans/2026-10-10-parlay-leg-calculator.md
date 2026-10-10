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

## Card spec v1 (frozen)

Frozen 2026-10-10 (the user). From now on it changes only for (a) the user's answers to questions
Claude asks, or (b) a card that states something false or contradicts itself. Anything else,
the user's or Claude's, goes on "Later ideas" below. Built in `props/calc/card.py`
(`card.render`, `card.question`, `card.render_not_enough`).

### Leg card template

One card per leg, one side (the side asked about), plain text, about 40 characters wide (a
line may wrap). The same layout for all four bet types.

```
[Tested on 2018-25: ...]                <- the bet type's test line (see "Held-out read")
[Check first: ...]                      <- only when something affects the bar (below)
[PLAYER]
[Side] [line] [bet type] ([price])

Bar for this price  ~[N] [unit]         <- Unders: "~[N] [unit] or fewer"
Last 4: a, b, c, d  (avg [U])           <- oldest to newest; * on a marked game
[N]+ this season: [H] of [G]            <- Unders: "[N] or fewer this season: [H] of [G]"
[Short history: [G] season games.]      <- only with fewer than 4 season games
[Sleeper's [unit] line: [W]]            <- only when Sleeper posts one (step G)
[* Week N: ...]                         <- one line per marked game

AT [U] [UNIT]
Needed at this price: [E] [rate unit]   <- Unders: "... or less"
His recent rate ([n] games): [R]        <- the rate the bar assumes
This season: [S]                        <- below the minimum sample: "[S] ([n] [unit])"
[Opponent] allows: [x][ to POS] ([G] games)

MATCHUP
[TEAM] [run|pass] offense [grade] vs [OPP] [run|pass] defense [grade]
[Favorite] favored by [spread]. Total [total].
[Starting QB not confirmed.]            <- only when this game's starter is not settled (below)

[Closing question]

Line as of [Mon D, H:MM AM/PM] PT.
```

- Bet type words: "rushing yards", "catches", "receiving yards", "passing yards".
- Price: Sleeper's multiplier for that side as American odds.
- "Bar for this price": the average workload at which this side wins often enough at its price
  (break-even, a push void). Never "needs N to win". Out of range: "Bar for this price: any
  workload up to [max] [unit] clears it." / "... no workload up to [max] [unit] clears it."
- "Needed at this price": the rate that clears the price at his last-4 average workload, from
  the same calculator (not line divided by workload). Out of range: "any rate clears it" / "no
  rate clears it".
- "His recent rate ([n] games)": his blended rate over his last [n] games played (n = 16 when he
  has them), the rate the bar assumes. The blend toward the position average is explained in the
  "Calculation" follow-up, not on the card.
- "This season": his plain rate this season before the week; below the market's minimum own
  sample it is still shown, with its sample ("This season: 4.1 (15 targets)"), never replaced.
- Opponent row (display only): the opponent's defense this season before the week, in the
  needed rate's unit, win probability 10-90% only. Under 4 games: "[Opponent]: only [G] games."
  No plays to his position: "[Opponent] allows: no plays to [POS]s yet ([G] games)". Plays left
  out for a missing win chance or roster listing are counted on the row.
- MATCHUP (display only): grades from the engine's tier system (copied, `matchup.py`), as the
  engine grades them (tier_grade): a letter, S best to F worst, with + near the top of its band
  and - near the bottom (thirds; in a band of 4 whole points or fewer, halves) (the user,
  2026-10-10); a grade line too wide for the card breaks at "vs"; rushing cards run vs run, the other
  three pass vs pass; under 4 games
  "Only [G] games. No grades yet." Spread and total from ESPN; when ESPN has none, the nflverse
  schedule's line, labelled "(closing line)" after kickoff and "(schedule line)" before. An even
  spread: "No favorite (even spread)."; a missing spread: "No spread shown." An injury line
  appears only when it changes this player's role (not built yet).
- Today's quarterback (MATCHUP): "Starting QB not confirmed." when this game's starter is not
  settled: the week's official injury report (nflverse injuries) has no rows for his team yet; or
  his team's opening-day starter is listed Out, Doubtful or Questionable, or did not practise with
  no game status yet; or his team's most recent game was started by someone else (covers IR, which
  the weekly report leaves out, and a benching). Otherwise no line. No dependable source names the
  replacement before kickoff
  (ESPN's depth chart, in nflverse depth_charts, still listed Baker Mayfield as TB's QB1 before
  week 5 of 2026, two starts after he went out; Sleeper's depth chart is live-only and hand-kept),
  so the "[Name] starts at QB today." form is never shown: no guessed names.
- The test line, first on every card, one per bet type (the user's wording after the held-out
  read; see "Held-out read"); "Check first:" lines below it: a lookup note when newer saved quotes
  were skipped.
- Markers (rule 3): a game where his offensive snap share was under 0.5 times his average in his
  other games that season ("* Week N: played far fewer snaps than usual."), and a game his team's
  starting quarterback was not the team's opening-day starter, naming who started ("* Week 4:
  Jalon Daniels started at QB."). A game from last season says "[year] week N".
- Footer: one line, the saved quote's time in Pacific time; a typed line says "Line typed in."
- Not enough data (a rate or pool below its minimum sample): "Check first: not enough data, so no
  bar:", the reasons, "Last games: ..." and the markers; no bar, no rates.
- Not on the card: "Line implies ~N (our math)" (in the "Calculation" follow-up), any gap line,
  percentages, the other side, verdicts.

### Units (the same in the bar, the last 4, the season count, the three rate rows and the entry summary)

| Bet type | Workload | Rate | Opponent row |
|---|---|---|---|
| Rushing yards | carries | yards a carry | yards a carry allowed to RBs |
| Receptions | targets | catches per 10 targets | catches per 10 targets allowed to his position |
| Receiving yards | targets | yards a target (an incompletion is 0) | yards a target allowed to his position |
| Passing yards | completions | yards a completion | yards a completion allowed |

### Rounding

- Bar: whole number with "~" from 6 up; one decimal below 6 ("~3.2").
- Last-4 average and the AT header: one decimal ("avg 15.5", "AT 15.5 CARRIES").
- Rates: one decimal.
- Season count: from the bar as displayed. Over: games at or above it ("~17" -> "17+"; a shown
  3.2 counts games of 4 or more). Under: games at or below it ("~20 or fewer" -> "20 or fewer").
- Every displayed number rounds half up (26.25 shows as 26.3).
- Closing asks, both from the numbers as displayed, so the reader's subtraction matches: the
  workload ask is the bar as shown minus the last-4 average as shown, then to the nearest half
  (judged as shown, so one that rounds to 0 is even); the rate ask is the needed rate as shown
  minus the recent rate as shown.

### Closing question

Workload ask = bar minus last-4 average. Rate ask = needed rate at his average minus his recent
rate (the bar's). An Under turns both round, so a positive ask is what the bet needs ("fewer",
"less", "room for N more").

| Case | Over wording |
|---|---|
| Average meets the bar, fewer than 2 of the last 4 games reached it | "Average clears it, but only N of 4 games did." |
| Both asks positive | "About 1.5 more carries, or 0.5 more yards a carry?" |
| Workload ask 0 or less, rate ask positive | "Workload is there. 0.9 more yards a carry?" |
| Workload ask positive, rate ask 0 or less | "At his recent rate it clears. About 3 more carries?" |
| Workload ask 0, rate ask 0 or less | "Recent workload and rate both meet the bar." |
| Workload ask negative, rate ask 0 or less | "Room for about 2 fewer targets?" |
| No rate ask (no needed rate) | "About 1.5 more targets?" / "Workload is there." / "Room for about N fewer ..." |

### Entry summary (step F, not built yet)

```
YOUR $[stake] ENTRY · [n] LEGS
Return if all win: $[R]
Includes your $[stake] stake.

WHAT EACH NEEDS (biggest ask first)
[Player]: ~[bar] [unit], [gap] more than recent.

FIT CHECK
[Player]: more runs while [TEAM] is ahead.
[Player]: more throws while [TEAM] is behind.
These lean on opposite game stories.
Both can win. Check your case for each.

PRICE CHECK: EACH BET ON ITS OWN
[Player]: more than [H] wins in [G].

TO COVER THE ENTRY COST
All must win more than [H] in [G].

IF EACH LEG HITS 1 TIME IN 2
Also assume no shared game effects.
All [n] win: 1 entry in [2^n].
Average loss: $[L] per $[stake] entry.
```

- The payout is the total Sleeper shows, stake included; if computed from leg prices, say so.
- Legs sorted from the largest workload ask down (a sort, not a verdict; no "weakest" labels).
- FIT CHECK covers every pair on the same team or in the same game, one block per opposing pair;
  if none: "No opposing pairs found." Never "cannot both win". Each story names the player's team
  (fixed under rule (b), 2026-10-10: "Lamb: more throws from behind" beside "Irving: more throws
  from behind" read as the same story although one needs Dallas behind and the other Tampa Bay).
- Each leg's price check from its own price. The coin-flip figure is a stated hypothetical.
- After a batch: the grade legend "Grades: S best, F worst; + and - show where a team sits in its
  band." once, then the follow-up names:
  Workload, Calculation, Matchup, Fit, Entry cost.
- Season log (after step F): legs won out of legs played first; entries won second, with a note
  that entry results are too rare to judge alone. Built as a read-only calc command over the
  journal rows.

### Answered (2026-10-10)

1. Thin pool at a depth: when his position has fewer than 100 catches at a depth (RB deep: 69 in
   2024-25), every position's catches at that depth are used; said in the "Calculation"
   follow-up, not on the card. Only if those are thin too: not enough data.
2. No separate minimum for yards per catch; the blend handles a small sample.
3. The quarterback marker names who started (opening-day-starter rule for which games).

4. Passing yards' minimum samples: 40 of his own completions in his last 16 games, and 100
   starting quarterbacks' completions per depth in the pool (confirmed).
5. League yards per completion guard range 8.0-14.0 (confirmed).
6. The workload ask is taken from the bar and average as displayed; every displayed number rounds
   half up.
7. Grades carry the engine's + and - (tier_grade, copied unchanged with _band_mod).

## Later ideas

Not built; each needs the user's go-ahead (the frozen-spec rule).

- "Small workload" line: when the bar is under 6, one line under the bar block, "Small workload:
  one [target/carry] either way can decide this." (the user, 2026-10-10; not to be built now).
- The injury line in MATCHUP (spec rule 9) has no data source wired yet.
- Caching the opponent row and grades per run (a 5-card batch takes 7.5 s; not needed now).
- The closing question does not consider his this-season rate (the user, 2026-10-10).
- For live cards, an attributed line in MATCHUP: "Sleeper lists [Name] at QB." (the user,
  2026-10-10).
- day_sd, k_catch and k_ypr barely change the tuning scores (2018-23), so they may be removable
  (the user, 2026-10-10; not acted on).
- Show each unit's score beside its grade, as the engine's tables do (neighbouring grades can be
  a point apart); raised by the code review, 2026-10-10.

## Outputs

**Everything in this section below "Card spec v1 (frozen)" is superseded by it.**

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

**Line capture.** `python -m props.calc capture` saves the current Sleeper lines to
`props/calc/lines/<season>/line_archive_<season>.jsonl` with `props/persist.py`'s writer, in the
engine's row format (`snapshot_type: "calc"`, plus the gsis id, the nflverse game id and the exact
multiplier). Not into `props/record/`: only the props workflow commits there, and
`scripts/check_commit_hygiene.py` refuses a PR that mixes it with code. The card reads both files.
It is run by hand; no workflow is added or changed. Unmatched lines are logged in
`props/calc/log/name_misses.jsonl` and not saved.
When the engine workflow retires, the two stores merge: calc's file becomes the one line history
(the user, 2026-10-10).

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

## Known issues

- **Duplicated code (left as is, the user, 2026-10-10).** The catch-rate block (depth buckets, the
  thin-pool check, the baseline, the blend) is written twice in player.build, for receptions and
  receiving yards; the starting-QB lookup from the schedule is written twice (player._results and
  player.backup_qb). A fix to one copy must be made to the other.

- **The journal grades and stamps late lines by name, not by id** (the user, 2026-10-10: record
  it, do not change journal.py now). `journal.grade` finds the player in settle's weekly stats by
  normalised name and team, else by name alone when exactly one player has it; `journal.late_line`
  matches the line history by normalised name, market, side and week only. The gsis id calc puts
  on each leg row is not used. Triggers: (a) two players with the same normalised name have
  Sleeper lines in the same week and market, so the late line (and its CLV) can be the other
  player's; (b) a leg row whose team does not match the stats file (a midweek trade) and a
  namesake elsewhere in the league, so the leg stays open, or goes to "check"; (c) a name the book
  spells differently from nflverse (suffixes, nicknames), so the leg stays open as unjoined.
- **Repeat captures replace earlier ones at the same line.** persist's row key has no capture
  time, so a later calc capture of the same player, market, side and line replaces the earlier
  row's prices. The journal row keeps the prices its card used.
- **Engine rows after a flex.** The engine's name-joined rows must match the current kickoff
  exactly, so after a flexed game they are skipped and an older calc quote can be the newest
  found.

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
  summary deleted; capture writes with persist's writer in the line history's format (calc's 362 earlier
  captures moved there, then out again after review: calc's captures live in props/calc/lines in
  the same row format, because a PR may not touch props/record); kickoff times from zoneinfo; ESPN spread and total read through
  `core.fetch` with core/status.py's parsing copied (props may not import core.status).

## Tuning (2018-2023, 2026-10-10)

`python -m props.calc.harness` (props/calc/harness.py, reviewed before its output was read):
17,767 cases from 2018-23 (rushing 2,198, receptions and receiving yards 6,727 each, passing
2,115; 82 left out for not enough data). Pre-registered grids and order (module docstring).

| Setting | Was | Now | Chosen on (2018-23) |
|---|---|---|---|
| `carry_r` | 16 | 8 | spread coverage 80.0% |
| `target_r` | 8 | 10 | spread coverage 79.9% |
| `completion_r` | 10 | 25 | spread coverage 79.3% |
| `k_ypc` | 150 | 200 | rushing conversion log loss 0.6134 (with `day_sd`) |
| `day_sd` | 0.15 | 0.05 | same search; 0.00 and 0.10 within 0.0001 |
| `k_catch` | 60 | 10 | receptions log loss 0.5696; the grid's smallest value; the whole grid within 0.008 |
| `k_ypr` | 50 | 50 | receiving-yards log loss 0.6581; the whole grid within 0.0007 |
| `k_ypcomp` | 150 | 800 | passing log loss 0.5268; the grid's largest value |

**Tests on 2018-2023 at the tuned settings** (in sample):

| Bet type | Conversion bands | Conversion 80% range | Spread | Round trip |
|---|---|---|---|---|
| Rushing yards | fail: 50-60% off 9.6 (278 games); 30-40% 150 games (untested) | 79.1% pass | 80.0% pass | worst 0.005 pt pass |
| Receptions | fail: 30-40% off 5.7 | 78.1% pass | 79.9% pass | 0.005 pt pass |
| Receiving yards | fail: 70-80% off 5.8 (60-70% at the mark, 3.0) | 77.1% pass | 79.9% pass | 0.005 pt pass |
| Passing yards | fail: 30-40%, 50-60%, 60-70% under 200 games; 70-80% off 6.5 | 77.8% pass | 79.3% pass | 0.005 pt pass |

No retune: the conversion test plugs in the actual workload, so the three r settings do not
enter it, and the k settings and day_sd were already chosen on it.

## Held-out read

**Read once, 2026-10-10, 20:00:48-20:12:58 UTC**, at the tuned settings above. Record:
props/calc/heldout/heldout_read.json, with every case and priced line (cases_2024_2025.csv.gz,
lines_2024_2025.csv.gz, pools_2024_2025.npz). 6,098 cases (rushing 783, receptions and receiving
yards 2,267 each with a workload, passing 698).

| Bet type | Conversion bands (each 200+ games, within 3 points) | Conversion 80% range (77-83%) | Spread (77-83%) | Round trip (1 pt) | Result |
|---|---|---|---|---|---|
| Rushing yards | fail: 30-40% (40 games) and 50-60% (78) untested; the four bands with 200+ games within 2.3 | 77.4% pass | 82.3% pass | 0.005 pass | fail |
| Receptions | fail: 30-40% off 3.2, 40-50% off 4.3, 60-70% off 4.9 | 78.6% pass | 80.4% pass | 0.005 pass | fail |
| Receiving yards | fail: 30-40% off 3.7; 70-80% (138 games) untested | 77.0% pass | 80.4% pass | 0.005 pass | fail |
| Passing yards | fail: 40-50% off 4.5; 20-30%, 30-40%, 50-60%, 60-70%, 70-80% under 200 games | 80.5% pass | 76.9% fail | 0.005 pass | fail |

Game story (league-wide team carries and pass attempts by result group, 2018-23 against
2024-25, within 1.5): carries pass (largest gap 0.4); pass attempts fail (2024-25 teams threw
2.1, 2.0 and 1.7 fewer per game when behind 8+, within 7 and ahead 8+). Overall fail.

What the failures say (diagnosed, not fixed; the user's rule: no setting, adjustment or pass
mark is changed after a result):
- The conversion test's lines (0.8x, 1.0x, 1.2x of the actual workload x rate) put most stated
  chances near three values per bet type, so some 10-point bands rarely fill to 200 games. That
  is a property of the test as registered, and it is why rushing and passing fail on
  "untested" bands.
- Receptions' middle bands ran 3-5 points under the actual Over rate in 2024-25 (and the 30-40%
  band in 2018-23): the stated chances there are too low.
- Passing's workload range was slightly too narrow in 2024-25 (76.9%).
- Pass attempts per game fell league-wide in 2024-25; the game-story rows are not on the card.

**The band test leaves bands empty by design (the user, 2026-10-10).** Its lines sit at three
heights (0.8x, 1.0x and 1.2x of workload x rate) and each 10-point band needs 200 games, so the
stated chances bunch near three values per bet type and some bands cannot fill. This was the
user's specification, not a calculator fault. Accepted as reported: no retune, no grid changes,
no change to the band test.

**The card's test line (the user's wording, same day), first on every card, replacing "Check
first: workload bar untested."; the numbers above go in the "Calculation" follow-up:**
- Rushing yards: "Tested on 2018-25: held up where it could be checked."
- Receptions: "Tested on 2018-25: Overs hit a bit more often than this bar implies."
- Receiving yards: "Tested on 2018-25: roughly right, slightly strict on Overs."
- Passing yards: "Tested on 2018-25: the least reliable of the four. Treat the bar as rough."

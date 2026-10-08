# How the props engine works -- inputs to prices, with the actual numbers

*Settings as of props-v1.57 (2026-10-08; the prices unchanged since props-v1.53). The plain-language companion to methodology.md and
model_registry.md: every formula and setting the engine runs, where each came from, and
what is proven. Worked examples are from week 4 of 2026 (ATL at NO), computed at props-v1.40:
they predate round 34 (target spread 60), round 38 (QB passing scale) and round 39 (backs'
carries toward the market), so their numbers show the method, not today's output.*

## 0. What it is

- A **pricing model**: it simulates each game 20,000 times and reads how often each player
  clears each line.
- A **research layer** around it: readings that judge a line without changing its price.
- **Not proven to beat the book.** No bet labels until the record says otherwise
  (section 6).

## 1. Inputs (refreshed every run)

| Source | What it gives |
|---|---|
| nflverse play-by-play, this season through last week | targets, catches, yards, carries, scores, game states |
| Weekly rosters, injury report, depth charts, snap counts | who plays, roles, snap shares |
| Last season's priors (resources/priors_*) | each player's shares and rates, role averages (WR1, RB2...), team volume, variation settings, last season's plays game by game |
| Sleeper Picks (primary) / The Odds API (fallback) | lines and payouts; also lines read but not modelled (carries, completions, attempts, longest plays); rushing + receiving is priced since #187 |
| Vegas spread and total | game script and the touchdown anchor |
| NWS weather | matters only above 15 mph sustained wind |

## 2. Who plays, and absences

- Priced roles come from the latest published depth chart before kickoff (QB1, RB1-2,
  WR1-3, TE1), plus anyone with 10%+ of his team's targets or 20%+ of its carries this
  season.
- Out / Doubtful / reserve players are removed (a game-day inactive counts only for its own week:
  before this week's roster is published, last week's INA reads as active and the injury report decides). The engine does **not** re-rank the depth
  chart itself: a replacement is priced only if the published depth chart already lists him
  in a priced slot or his share passes the bar above. A lagging depth chart can leave the
  replacement unpriced -- the report then flags the absence with no priced replacement, and a
  role what-if (`--role "Player=RB1"`) prices him.
- **The Out rule** (score_game.OUT_RULE; tuned on 2022-23 absence games, confirmed on
  2024-25, reports/absence_tune.md):
  - targets: **25%** of the absent player's share goes to the priced teammates (80% of that
    to his position, 20% across everyone); **75%** to players outside the priced set;
  - carries: **25%** to the priced backs; **75%** to backs outside the set.
  The 75% is not given to any named player: it stays in the team's unpriced "depth" pool,
  simulated at depth players' rates. A promoted player who is priced gets his own blended
  share plus his part of the 25% -- counted once.
  Measured reason: when a player with ~21% of the targets sat, players outside the priced
  set went from 11% to 27% of the targets.
- Questionable players are priced as playing, with a separate "if he's out" section;
  teammates' rows carry the flag.
- **Known gap:** a backup quarterback does not change receivers' shares or efficiency (flagged
  by "QB change" notes only).

## 3. Team volume (throws aimed at a receiver, and runs, per game)

1. **History blend**, k = 4 games (backtested by the second expert audit: better than 2, tied
   with 8 and 16; DECISIONS #198):
   `volume = w x this season's average + (1 - w) x last season's average,  w = games / (games + 4)`
2. **Throws only: 25% toward the market** (fitted on 544 games; spread positive = favoured):
   - plays = 47.8 + 0.146 x spread + 0.20 x total
   - pass rate = 0.371 - 0.0022 x spread + 0.0038 x total
   - throws = 0.75 x history + 0.25 x (plays x pass rate)  (model.MARKET_PASS_WEIGHT, round 16, #134)
   The market explains only 2-4% of game-to-game volume, so the weight is small.
3. **Runs: the backs' carries 50% toward the market** (round 39, DECISIONS #204;
   model.MARKET_RUSH_WEIGHT): carries = 0.5 x history + 0.5 x (plays x (1 - pass rate)), from
   the same fit. The starting QB's carries are held where history put them (the full market
   version hurt QB rushing, #106). The without-change number (history carries) is logged
   beside the board as p_over_hist_carries for the week-8 reversal check, never the price.
4. **League drift correction** from week 5: a league-wide recent-volume ratio, capped at
   0.85-1.15.
5. **Touchdowns** are anchored to implied points (about 0.106 touchdowns per point).

*Example, Atlanta:* 74 targets and 102 runs in 3 games against 30.7 / 27.4 a game last season
-> w = 3/7 = 0.43 -> 28.1 throws and 30.2 runs; the market's 31.6 throws -> **29.0 throws,
30.2 runs** (at props-v1.40, before round 39 moved the runs toward the market too).

## 4. Player shares and rates: the two-stage blend (model.blended_rate)

Every rate: `blend = w x own + (1 - w) x prior,  w = n / (n + k)` -- read k as an imaginary
pile of k opportunities at the prior rate.

1. **Starting point:** last season's rate pulled toward his role's average (n = last season's
   opportunities).
2. **Final:** this season's rate pulled toward the starting point (n = this season's
   opportunities).

| Rate | k | n is counted in | Where k comes from |
|---|---|---|---|
| Target share | 80 | team targets | backtest (DECISIONS #136); reconfirmed by round 26 (#174) |
| Carry share | 40 | team carries | yearly priors fit; round 26: beats 20 / 10 / 5 (#174) |
| Catch rate | 40 | his targets | backtest (#135) |
| Yards per target | 80 | his targets | backtest (#135) |
| Yards per carry | 80 (2025 fit) | his carries | yearly priors fit |
| Goal-line target / carry share | 5 / 4 | goal-line chances | derived from the share k's |

The yearly fit (build_priors.py) tries k = 5 ... 2,560 on one season's weeks 7-8; it swung up
to 4x between years, which is why the receiving k's were fixed by backtest.

**Adjustments:**
- **Snap rule (target share only, round 23, #143):** x (last week's snaps / earlier
  snaps)^0.5, capped at x0.6-1.6. The power 0.5 won over 0.25 and 1.0; it is a fitted
  half-strength response, not a law: a 10% snap rise gives about a 5% share rise.
- **New team:** last season counts at most k (half weight); his new-team snap share scales
  the share.
- **Opponent (efficiency only):** a team-level multiplier on catch rate and yards per
  target / carry, k = 150 plays, about a +/-4% swing.
- **Shares over 100%:** after the Out rule and the snap rule, a team's priced target shares
  (and carry shares, and goal-line shares) are scaled down in proportion when they add to more
  than 100%, so the quoted projection and the simulation always agree.
- **Carry shares:** then moved
  halfway toward leaving 12% of carries for players outside the priced set (the QB's share
  untouched; round 15, #133).

*Example, Drake London:* starting point 0.82 x 30.5% + 0.18 x 22.3% = 29.1%; this season
0.48 x 25.7% + 0.52 x 29.1% = 27.4%; snaps 93% vs 80% -> x1.08 -> **29.6%**. 29 throws x
29.6% = **8.6 targets**; x 67% catch rate = **5.8 catches**.

*Example, Bijan Robinson:* 0.92 x 61.9% + 0.08 x 53.0% = 61.2%; 0.72 x 64.7% + 0.28 x
61.2% = 63.7%; team total 103% -> 61.9%; room for others -> about 58%. 30.2 runs x 58% =
**17.5 carries**.

## 5. The simulation (20,000 games per run)

| Piece | How it is drawn |
|---|---|
| Team throws / runs | negative binomial each (dispersion r about 34 / 28), **drawn independently** -- a team's passes and runs do not yet trade off with the game script |
| Split among players | random around each share; concentration 60 (targets, since round 34, DECISIONS #195), 20 (carries), 80 (QB carries) -- lower means bigger game-to-game swings |
| Catches | binomial(targets, catch rate) |
| Receiving yards | each catch drawn separately (gamma, shape 1.07), so any catch can go long |
| Rushing yards | carries x yards per carry plus per-carry draws from last season's real league run distribution; a game-wide efficiency swing (sd 0.15 since round 30, DECISIONS #189) |
| QB passing yards | his receivers' yards in the same game plus the depth receivers' (66% catch rate, 6.3 yards per target), x a draw of the share a starter keeps, x (implied points / 22)^0.2 x 1.04 since round 38 (DECISIONS #199; off when no spread/total is posted). Still too wide: 11.9% of games outside the 80% range |
| QB rushing | not on the board since DECISIONS #188 (the user does not bet it); his carries are still drawn, because they come out of the same team pool as the backs' |
| Rushing + receiving | a back's rushing and receiving draws summed in each simulation; priced since it passed its calibration check (#187) |
| Touchdowns | a separate prototype model (anytime_td_v1), blended with the market's price |

## 6. Price, record and the label gate

- **Model chance** = the share of the 20,000 simulated games that clear the line.
- **Book chance** = the payouts with the cut removed (1 / multiplier per side, scaled to
  sum to 100%).
- Every priced line is logged (the scheduled props workflow captures a Thursday open, decisions
  before kickoff and the close), settled Tuesday, graded on the scorecard. Chat never records.
- **The live record so far** (weeks 2-4, 1,536 lines at Sleeper's real lines, DECISIONS #202):
  the engine's log loss 0.717 against the market's 0.692 (a coin flip is 0.693). Read the
  market's chance as the best available estimate and the engine for volume and role.
- **Label gate:** labels return only at the week 8, 12 or 18 reviews, and only if both the
  model's weight beside the book and the profit of its strongest calls are wholly above zero.

## 7. The research layer (judges lines; never changes prices)

| Reading | Formula |
|---|---|
| Line implies | the targets or carries at which the line is a coin flip (a search in the simulation) |
| Pays if you expect / zone | the AVERAGE volume (his expected share; the game-to-game swings in volume stay in the price) at which each side reaches its break-even price; our projection falls in the Over, no-bet or Under zone. "Line implies" and the what-ifs are expected-volume numbers too |
| Whole numbers | each Over is read at the number that wins it: 3.5 means 4, 44.5 means 45 |
| Luck-capped yards a play | over his last 10 games, every play past his own 90th percentile is counted at that line; under 10 plays in that window, his longest there is dropped instead. Needs 8+ catches, 10+ carries or 20+ completions, else a dash |
| Volume chance (the card's efficiency rows, DECISIONS #206-#208) | volume needed = the Over / a rate (luck-capped, this season, the engine's), rounded up, and the engine's chance of reaching it in the simulation; plus the efficiency the line needs at the engine's volume and how many of his games beat it |
| Volume check (research CSV only since #208) | needed volume = yards needed / luck-capped rate, against ours ("comfortably more" at +15% or more, "fewer" at -15% or less) and the book's volume line. Arithmetic on realized volume, not the simulation; it leans against Overs by design. Kept in research_*.csv (catch_yards, carry_yards, qb_yards, rush_rec), off the card |
| Book's coin flip | line + game-to-game spread x the normal quantile of the book's no-vig chance |
| Team volume and script | each team's games this season; our projection against that range; teams under this kind of line split their snaps ahead / close / behind by 8+, times this team's pass share in each state, blended toward the league with 60 plays of weight |
| Rushing + receiving | the touches the line takes at his luck-capped rates; how much of his yards come from catches (research CSV `rush_rec`, beside the priced chance since #187, never a threshold) |
| Flags | role up/down; backfield takeover (carry share +/-20 points); teammates out, back or questionable; QB change; new team |
| Fantasy points allowed | PPR per game by position, context only |
| Offensive line | each team's five linemen with the most snaps this season; how many are out (report, reserve, off the roster) or questionable; context only, never a price input |
| What-ifs | separate runs with user assumptions, never recorded. A range (`carries=10/12/15`) prices low / expected / high and gives each side a verdict ("pays across your range" ... "does not pay in your range"); `--role "Player=RB1"` prices a replacement the depth chart has not promoted. `carries=auto` / `targets=auto`: our projection +/- one standard error of his share over his last 10 games x the team's projected volume (this season only after a team change or takeover; 3+ games) |
| No priced replacement | an Out starter whose team now prices fewer players at his position than it has slots; the report names him and suggests the role what-if |

## 8. Narration (SKILL.md)

A single-game read: the team section by resources/team_matchup_guide.md (sections 1-8), then
one card per player (one table; "How to read the player cards" copied before the first) ->
each player's volume and share, last season vs this season -> teammates out -> the engine's
volume vs the book's -> the card's efficiency rows, with catches or yards named per read ->
if-thens with the losing branch -> "Don't mix". Never picks.

**Publishing (DECISIONS #217).** Each run also writes `run_<slug>.json`, the cards and the brief as
data. A read written for others goes to scripts/publish.py as a reads file. publish.py first checks
it against the run: the leg is on the board, every volume x efficiency is recomputed, every cited
number matches, every number in the prose traces back, injuries match section 4, and no pick
language appears. Only then does it render the QA/QC version and the agent version
(resources/agent_guide.md). A failed check renders nothing.

## 9. Proven, unproven, next

- **Proven on past data:** beats a naive baseline; the Out rule; the snap rule; the
  takeover flag; the fixed k's; the team-volume k and the early-season blend (the expert
  audits, DECISIONS #197-#198).
- **Not shown, or measured against us:** an edge against the book (at Sleeper's real lines the
  engine has scored worse than the market, #202); the verdict labels at this sample size;
  carries too narrow (backs' rushing and rushing + receiving run narrow in the tails); QB
  passing too wide.
- **Owed or queued:** the week-8 review and its reversal rule for rounds 34 and 39 (#204),
  with the four-seed replay tool it needs; a pre-registered round on the uncertainty of a
  back's projected carries (reports/current_settings_check_2026-10-06.md); the backs' carry
  pool rebuilt as designed runs minus the QB's own rate (#188); the label gate's redesign
  (#202, the user's decision); a backup-QB adjustment.

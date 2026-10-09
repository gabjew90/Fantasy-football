# Round 43: efficiency from the player's own last 10 games, not the league average (pre-registered 2026-10-09, before any run)

## Why

Every efficiency rate the engine prices -- catch rate, yards per target, yards per carry -- is a
two-stage blend (model.blended_rate): last season's own rate pulled toward the league average
for his depth slot, then this season's rate pulled toward that. With the shipped constants
(K0_FIXED: yards per target 80 own targets, catch rate 40; yards per carry 80 carries from the
priors fit) a starter's yards per target is 26-59% league average and a backup's 80-95%
(TB-DAL, 2026 week 5, joined by ID).

- **The case (user, 2026-10-08):** Bucky Irving's receiving-yards Over was priced at 64-70% six
  times in 2026 (weeks 2-5) and lost all six. The engine's 7.6 yards a catch was 59% the RB1
  league average (5.88 a target), 26% his 2025 rate, 16% his 2026 rate (4.07 a target, 4.7 a
  catch on 13 catches). Backs' receiving-yards Overs priced 60%+ at lines of 20.5 or less hit
  8 of 19 in the settled 2026 record (engine 64.7%).
- **Our own evidence points the same way for catches and the other way for runs:**
  reports/robust_ypc_check.md -- after weeks 1-3, a player's own yards a catch capped at the
  95th percentile predicted weeks 4-18 better than the league average (2024-25 error 2.066 vs
  2.239); three games of yards a carry lost to the league average (0.565 vs 0.94). Round 27:
  the least shrinkage on yards per carry tried (k 80, the grid edge) scored best.
- **The user's design:** borrow from the player's own past, not other players -- his last 10
  games, his long plays capped at his own 90th percentile (the luck cap, DECISIONS #167/#207),
  which today prices nothing.

Hypothesis: a player's own capped last-10-games rate predicts his catches and yards given the
volume better than the league-anchored blend.

## What is compared

One change, three rates, each tested alone, plus all three together. `backtest.py --own-rates
<arm>` (new, default `off` = shipped, byte for byte):

| Arm | Catch rate | Yards per target | Yards per carry |
|---|---|---|---|
| off (shipped) | blend | blend | blend |
| catch_rate | **own** | blend | blend |
| ypt | blend | **own** | blend |
| ypc | blend | blend | **own** |
| all | **own** | **own** | **own** |

**"Own"**, for each player-game (week W of season S):
- **Window:** his last 10 regular-season games before W with at least one target (catch rate,
  yards per target) or one carry (yards per carry), drawn from season S-1 and season S weeks
  before W, with any team (the luck cap's window, research.luck_for; round 37 found rates
  travel with the player).
- **Catch rate:** catches / targets in the window.
- **Yards per target:** his catch yards in the window, each catch counted at most his own 90th
  percentile catch in the window (research.player_luck_line / luck_free_rate: 10+ catches, else
  his longest catch left out), divided by his targets in the window.
- **Yards per carry:** the same, on his runs (kneel-downs excluded, as the harness counts runs).
- **The long-play add-back (amended 2026-10-09, before any registered run):** the capped yards
  (catches and runs) are multiplied by his position's long-play factor -- over each player's
  final 10 games of LAST season (S-1) with such a play, for every player with 10+ plays there,
  plain yards over yards capped at each one's own 90th percentile of that window (the window's
  own definition), pooled by position (RB with fullbacks / WR / TE / QB, positions from last
  season's weekly rosters; `backtest.own_uplift`). A window with fewer than 10 catches (possible
  at 20+ targets) uses his plain yards a catch, with no trim and no add-back. Why: a smoke run on 2021 weeks 2-4 (outside this round's
  data; rates only, no outcome read) showed the capped average runs low for everyone --
  receivers 7.66 vs the blend's 8.80 yards a target, backs 3.68 vs 4.30 a carry -- because
  every player has real long plays. Priced raw, it would lower every Over for a reason unrelated
  to the hypothesis. With the add-back the levels match (receivers 8.38 vs 8.80, tight ends
  7.43 vs 7.58, backs 5.55 vs 5.63 a target and 4.42 vs 4.30 a carry; factors about 1.09 on
  catches, 1.2 on runs). The league enters only as the size of the luck share, never as a pull
  toward other players' rates.
- **Thin window:** under **20 targets** (catch rate, yards per target) or **40 carries** (yards
  per carry) in the window, the shipped blend is used instead. Picked, not measured: about two
  games of a starter's volume; a rookie's first weeks keep the shipped blend.
- **Unchanged:** the opponent adjustment on top (team level, k0 150), shares and volume, every
  width setting, the new-team cap on the blend (an own-window rate is his own plays, so no cap).

**The stand-in lines stay where the shipped engine puts them.** The conversion score's lines
come from the same rates this round replaces (backtest.add_conditional), and the scorer refuses
two runs at different lines. The lines now read the shipped rates (`cr_ship`, `ypt_ship`,
`ypc_ship`, computed in every arm); with `--own-rates off` the whole output equals today's
harness (checked by running main and this branch on 2026 weeks 2-4: all 107 columns identical on
669 player-games; a source test pins which rates the lines and the draws read), and scoreboard
.compare refuses any two arms whose lines differ, so every arm is scored at the same lines on
the same player-games.

## Which score judges each arm (reports/scoreboard.md)

Efficiency changes are judged on the **conversion** log loss (actual targets / carries plugged
in), bettable population:

| Arm | Judged on |
|---|---|
| catch_rate | receptions (pc_rec, exact) |
| ypt | receiving yards |
| ypc | rushing yards |
| all | reported on all three; ships only as described below |

## The rule (fixed now) -- props/tools/round43_select.py

- **Runs:** every arm on seeds 0-3 (`--audit-seed-offset 0..3`, the four-seed rule, #202), on
  2022-24 weeks 2-18 (selection) and 2026 weeks 2-4 (confirmation), `--conditional`, every
  other setting as shipped (props-v1.59 engine code). 2025 is not run.
- **Four seeds:** each arm's Over chances are averaged over the four seeds per player-game
  before scoring (selection and confirmation alike); the per-seed gains are reported, and a gain
  under 0.3% of the shipped log loss must be positive on every seed.
- **A single-rate arm ships if,** against shipped (props/tools/grid_select.run, two settings):
  - **detectable** on 2022-24: its market's conversion log-loss gain has a 95% game-clustered
    interval wholly above zero (10,000 resamples), with log loss and Brier agreeing in sign in
    the 15-85% decision zone;
  - **big enough:** it moves the Over chance at the stand-in lines on average by at least **1.8
    points** (receiving and rushing yards) or **1.0 point** (receptions). Amended before any read
    (code review): #202's 3.6 is twice the noise of ONE seed; the chances here are four-seed
    averages, which halve it (1/sqrt(4)), and receptions are scored exactly with no seed noise, so
    the scoreboard's original 1-point minimum applies there;
  - **guards pass:** every bet market (receptions, receiving yards, rushing yards, rushing +
    receiving, QB passing) no worse than -0.5% of its own log loss, on the conversion and the
    own-volume score, complete or blocked (scoreboard.guard_verdict);
  - **confirmed** on 2026 weeks 2-4: its market's gain not negative (point estimate), decision
    zone signs agreeing;
  - leave-one-season-out gain reported beside the in-sample one.
- **The final setting** is the set of rates whose single arms ship. With two or more, a run of
  exactly that set (four seeds) is checked against the guards on 2022-24 before it ships. The
  `all` arm is reported either way; it ships as such only if all three single arms ship.
- **No other rate, threshold or window is tried in this round.** A different window length,
  threshold or a recency weight is a later round.
- **Multiple looks:** family "efficiency source", 4 candidates read once on 2026 weeks 2-4 ->
  confirmation intervals reported at 1 - 0.05/4 = 98.75%; the ypc arm also belongs to the
  running-game family (already read four times on those weeks) and reports its interval at 99.2%.
  The confirmation rule itself stays the point estimate.

## Reported beside the verdict (no part of it)

- Gains by role (RB / WR / TE) for each arm, and how many player-games fell back to the blend.
- Irving 2026 weeks 2-4: the shipped and own rates and the Over chances at the stand-in lines.
- The Over-minus-engine gap by role, shipped and the final setting.

## If it ships

- The live scorer (score_game.rate) uses the same own-window rate for the shipped rates, from a
  resource of each player's last-season games built by build_play_yards.py (targets, catches,
  catch yards, runs per game), with this season's games from the current play-by-play; known-
  answer tests pin the live number to the harness's for the same player-week.
- The window length and the thin-window thresholds (10 games, 20 targets, 40 carries) move from
  backtest.py constants into the engine's resources config, read by the harness and the scorer
  alike (CLAUDE.md: knobs live in config).
- The blend code those rates no longer use for a full window stays only as the thin-window
  fallback; anything left unused is deleted in the promoting PR.
- The research reads' "we expect" yards a catch and the luck-free column then show the same
  number the price uses; registry entries (core/registry.py, model_registry.md) updated with
  this evidence.

## Result

(Filled in after the runs, below this line, without editing anything above.)

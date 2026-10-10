# Parlay-leg calculator (props/calc/): design note

*2026-10-10. DECISIONS #226. Status: awaiting the user's approval. No code is written until it is given.*

## What it is, and why it is an exception

The user places small Sleeper parlays for fun and wants a calculator, not a predictor. Given a
posted line and its price, the tool says what workload (carries, passes thrown to him,
completions) the player needs for the leg to win often enough, so the user can judge whether that
workload is realistic. It never says a line is wrong, never compares its own chance with the
book's, and never labels a bet.

CLAUDE.md says "no parallel engines". This tool is a deliberate exception the user approved on
2026-10-10, recorded in DECISIONS #226 and in one line of CLAUDE.md. Its scope is fixed by this
note. It shares no code with `props/engine/`, and a test fails if it imports from there. The
engine, its workflows and its record are not touched.

Overlap to be aware of: DECISIONS #225 (2026-10-09) made the engine's card restate a line as a
workload. The two tools answer a similar question in different ways. This one is deliberately
small: one workload number, a player's own rates, real per-play outcomes, no volume forecast.

**Hypothesis.** Given the workload a player actually got, the calculator's chance of clearing a
line matches how often he cleared it (conversion test), and its workload spread matches how much
workloads really vary (spread test). If both hold, "he needs about 20 carries" is a trustworthy
translation of the price.

**Metric.** The pass marks in the Testing section, fixed now, before any result is read.

## Layout

```
props/calc/
  settings.yaml      the 8 tunable settings, each with a plain-English comment
  data.py            loads nflverse pbp, schedules, weekly rosters, snap counts (see Q1)
  lines.py           Sleeper line capture (standalone), odds conversion, player matching
  rates.py           his rates: blended and plain season
  sim.py             the per-market chance-of-clearing functions
  search.py          finds the workload for a target chance
  card.py            leg card text
  matchup.py         the MATCHUP block (display only)
  entry.py           entry check (game story, conflicts, cost)
  log.py             jsonl log and season summary
  validate.py        conversion, spread, round-trip and game-story tests (writes reports)
  __main__.py        `python -m props.calc ...`
```

Only `props/calc/` and its tests are new. `props/record/lines/` is read, never written.

## Data

- nflverse play-by-play 2018 to present, schedules (spread, total, final score), weekly rosters,
  snap counts.
- Sleeper lines from `api.sleeper.app/lines/available?dynamic=true` (two-sided, payout
  multipliers) and players from `api.sleeper.app/v1/players/nfl`.
- `props/record/lines/` (saved line history), read only.
- **Leakage cut-off:** pricing week W of season S uses only games strictly before (S, W). One
  function owns the cut-off and every data read goes through it; a unit test checks it.
- **Known traps, handled in one place each:** receiving_yards is NaN on incompletions (filled with
  0 for yards per target; catches are filtered on `complete_pass == 1` before yards per catch);
  sacks are neither targets nor attempts (filtered on `sack == 0` and `pass_attempt` rules);
  spikes and kneels excluded from attempts and carries; two-point plays excluded.
- **Player matching.** Sleeper lines carry Sleeper's player id. Following CLAUDE.md ("joined by ID,
  never by name alone") and #224: Sleeper id -> gsis id through nflverse weekly rosters, which
  carry both. Where no id is available (older line-archive rows carry names only), a normalised
  name (lower case, punctuation and suffixes removed, a small nickname table such as
  joshua/josh) with a first-initial + surname fallback within the team. Every miss and every
  fallback match is logged. See Q2.

## Odds

- Sleeper gives each side a payout multiplier m. Break-even for that side = 1 / m.
- Shown as American odds for readability: m >= 2 -> +100(m-1); m < 2 -> -100/(m-1).
- No-vig chance ("book expects") for the Over = (1/m_over) / (1/m_over + 1/m_under).
- One-sided lines: break-even is shown; "book expects" is shown as "not available".

## His rates

One rate per market: yards per carry, catch rate, yards per catch, yards per completion.

- **Blended rate** = w x his rate over his recent games + (1 - w) x the position baseline,
  w = n / (n + k), where n is his volume in those games (carries, targets, catches, completions)
  and k is that rate's setting. "Recent games" = this season and last (see Q3).
- **Position baseline** = the position's pooled rate over the two seasons before the priced week,
  weighted by volume.
- **Plain season rate** is shown alongside, unblended, with its game count.

## The calculator

All four markets are Monte Carlo with a fixed seed per card, 20,000 draws, so the same inputs give
the same card. Workload W is the average; the realised workload varies around it.

**Rushing yards.** Carries ~ negative binomial with mean W and size `carry_spread`. Each carry =
his blended yards per carry + a residual drawn from real RB carries over the two seasons before the
priced week, with each residual centred on zero (carry yards minus that pool's mean). The game's
total is then multiplied by one good-day/bad-day multiplier, lognormal with mean 1 and sd
`good_day_sd`. Chance = share of draws over the line (a whole-number line that lands exactly is a
push and is reported separately).

**Receptions.** Targets ~ negative binomial with mean W and size `target_spread`. Each target is
caught with his blended catch rate.

**Receiving yards.** As receptions; then each catch's yards are drawn from real catches by his
position (WR / TE / RB) and depth-of-target bucket (behind the line, 0-9, 10-19, 20+ air yards),
with the bucket chosen by his own share of targets in each bucket (blended to the position mix with
the yards-per-catch k). The draws are scaled so their mean equals his blended yards per catch.
Whether a good-day multiplier applies here is Q4.

**Passing yards (proposal, open questions below).** Volume = completions, W = average completions.
Completions ~ negative binomial with mean W and size `completion_spread`. Each completion's yards
are drawn from real completions (all QBs, the two seasons before the priced week, by depth bucket
with his own depth mix), scaled to his blended yards per completion. The card gives yards per
completion as much space as volume: his blended rate, his season rate, his last games' rates, and
the completions needed at his usual rate and at a high and low rate.
Open questions for passing:
- P1. Completions or attempts x completion rate? Attempts separate volume from accuracy and read
  more naturally, but need a ninth setting (a k for completion rate), so one would have to go.
  Proposal: completions.
- P2. A game-level multiplier on yards per completion? Without one, the yards range is likely too
  narrow (a QB's yards per completion swings a lot game to game). Proposal: reuse `good_day_sd`
  for passing rather than add a setting, and let the conversion test say whether that is enough.
- P3. Sacks: excluded entirely (sack yards are not passing yards in the box score), which matches
  how books settle.
- P4. Which QBs: starters only (the QB with the most dropbacks in each game) for every rate and
  test.

**Search.** For a target chance p, find W such that chance(W) = p by bisection on W over [0.5, 60]
(passing: completions up to 45), with common random numbers across W so the chance rises
smoothly with W. Three searches per card: (a) the no-vig chance ("book expects"), (b) the Over's
break-even, (c) the Under's break-even (the W at which the Under wins at its break-even rate).
A user target win rate replaces the break-even when given; the default is the break-even.

## Outputs

**1. Leg card** (phone width, about 40 characters a line, no tables wider than that):

```
JAVONTE WILLIAMS - rushing yards
Over 64.5 at -125

To win often enough (56%):
  about 20 carries at his usual 3.7 a carry
  about 17 on a good day (4.5)
Book expects: about 18

How often he gets 20+ carries
  this season: 2 of 5
  won by 8+: 1 of 1
  within 7:  1 of 3
  lost by 8+: 0 of 1
  with QB X: 2 of 3 / with QB Y: 0 of 2

His last games (carries / yards)
  W4 17/61  W3 21/88  W2 12/40 ...

Gap: 2 carries above what the book expects.
  His usual workload is 17; he needs a bit more.
```

- "Good day" uses the 75th percentile of his game-level yards per carry this season and last
  (Q5: or the multiplier's +1 sd; the brief's example fits either).
- The QB split is shown only if the starting QB changed this season.
- Receiving cards say "passes thrown to him". Passing cards give yards per completion its own
  block of the same size as the volume block.
- The gap line is the needed workload minus "book expects", read in plain words by size
  (for example under 1: "about what the book expects"; 1 to 3: "a bit more"; over 3: "a lot more").
  The words are fixed text, not a judgement of the line.

**1b. MATCHUP block** (added by the user, 2026-10-10). Display only: nothing in it changes any
calculated number, feeds the search, or becomes a setting. A test checks that the card's numbers
are identical with the block on and off. Computed in `props/calc/matchup.py` from play-by-play,
weekly rosters, the nflverse injury file and schedules; nothing is imported from the engine.
Every line carries its sample size, and says "only N games" when there are fewer than 4 (M1).
Each line is worded against the card's question, as a fact beside the needed workload or rate,
never as a verdict.

- **Game:** spread, total and each team's implied points (implied = total / 2 +/- spread / 2,
  using the schedule's closing `spread_line` and `total_line`; nflverse's sign convention is
  checked against a known game before use). Example: "DEN favored by 3.5, total 41.5: DEN about
  22.5, MIA about 19. A rushing Over needs DEN ahead."
- **Key injuries:** a QB change, and any top-3 target or lead back of his team listed Out or
  Doubtful for the priced week (M2, M3). For each, his own workload in games with and without
  that player, this season and last. Example: "Sutton out. Williams with Sutton: 15.2 carries
  (9 games); without: 18.0 (only 2 games). He needs 20."
- **Opposing defense, his market:**
  - rushing: yards per carry allowed to RBs, with rank of 32. "MIA allows 4.6 a carry to RBs
    (27th, 5 games). He needs 3.2 a carry at 20 carries."
  - receiving: yards per target and catch rate allowed to his position (WR / TE / RB), with
    ranks.
  - passing: yards per completion and completion rate allowed (M4).
- **Volume allowed:** carries and yards (rushing) or targets and yards (receiving) allowed per
  game to his position, with rank. "MIA faces 24.1 RB carries a game (8th most, 5 games)."
- **Tiers:** each team's offense and defense placed in one of four tiers (ranks 1-8, 9-16, 17-24,
  25-32) by the average of its EPA-per-play rank and success-rate rank, garbage time excluded
  (M5). Shown as words ("top-8 run defense", "bottom-8 offense") with the games counted.

Scope: this season, games before the priced week (the same leakage cut-off as everything else).
Early in a season, when a team has fewer than 4 games, last season's figure is shown beside it,
labelled as last season (M6).

Open questions for the MATCHUP block:
- M1. "Thin" threshold: fewer than 4 games? (A display rule, fixed in code, not a setting.)
- M2. Whose injuries: his team only, or his team plus the opposing QB (which moves game story)?
  Proposal: both.
- M3. Source for the priced week's status. The nflverse injury file is the official report but
  can lag a day; Sleeper's player file has a live `injury_status`. Proposal: the official report
  when the week is present, else Sleeper's status labelled "Sleeper status, not the official
  report". "Out" = Out or Doubtful; Questionable is listed but not split.
- M4. Passing cards: the brief names rushing and receiving only. Proposal: yards per completion
  and completion rate allowed, plus sacks per dropback, so yards per completion gets its context.
- M5. Garbage time: proposal, plays with win probability outside 10-90% are excluded, for the
  tiers only. Should the per-carry and per-target allowed figures also exclude garbage time?
  Proposal: no, so they match how lines settle (all plays count).
- M6. Fall back to last season when under 4 games: yes, shown separately, never blended.

**2. Entry check.** For each leg, the game story it needs: rushing Overs want the team ahead;
passing and receiving Overs want it behind or a shootout; Unders the reverse. Conflicts are listed
(for example a rushing Over and the same team's passing Over; a rushing Over and the opponent's
receiving Over). Cost: the total payout (product of the leg multipliers, or the payout the user
types in), the hit rate each leg needs = (1 / payout)^(1 / legs), and the average loss per unit
staked if every leg is a coin flip = 1 - payout x 0.5^legs.

**3. Log** (`props/calc/log/legs.jsonl`, see Q6). At pricing: leg, line, both prices, book
expects, needed workload, his blended rate, timestamp. At settle: the actual workload, the result,
and the line near kickoff (from `props/record/lines/` when it has the player, else the calculator's
own last capture). The season summary groups legs by gap size and shows needed vs actual workload
and legs won vs break-even per group.

## The standalone line capture

`python -m props.calc capture` reads the Sleeper endpoint and appends a dated snapshot under
`props/calc/lines/`. It is run by hand; no workflow is added or changed (CLAUDE.md: props.yml is
the only scheduled workflow).

## The eight settings (settings.yaml)

| # | setting | meaning (plain English) | start |
|---|---|---|---|
| 1 | carry_spread | how much a back's carries swing from game to game; higher = steadier | 16 |
| 2 | target_spread | the same for passes thrown to a receiver | 8 |
| 3 | completion_spread | the same for a quarterback's completions | 12 |
| 4 | good_day_sd | how far a whole day's efficiency swings, good or bad | 0.15 |
| 5 | k_ypc | how many carries before his own yards per carry outweighs the position's | tuned |
| 6 | k_catch_rate | how many targets before his catch rate outweighs the position's | tuned |
| 7 | k_yards_per_catch | how many catches before his yards per catch outweighs the position's | tuned |
| 8 | k_yards_per_completion | how many completions before his yards per completion outweighs the position's | tuned |

Not counted as settings (fixed by this note, changing them is a design change): the 20,000 draws,
the depth buckets, the two-season pools, the recent-games window, the gap wording bands, file
paths. See Q7.

## Testing

Tuning uses 2018-2023 only. 2018 has no two prior seasons in the data (pbp starts at 2018), so
2018 feeds pools and rates but is not scored; scoring runs on 2019-2023 (Q8). Settings are tuned
by a small grid on the conversion and spread tests. **2024-25 is held out and read once, at the
end (step 7).** That read is recorded in this note with its date and every result, pass or fail.

Pass marks, fixed now:

- **Conversion test** (lead backs: most carries on his team that game; top-3 targets on his team
  that game). Plug in the workload he actually got, with no workload variation, and score the Over
  at lines of 0.8x, 1.0x and 1.2x of (workload x his blended rate), rounded to the half. Pass:
  stated chance vs actual result within 3 points in every 10-point band from 20% to 80% (each band
  needs 200+ games; a band below 200 is reported as "too few", not as a pass), and the 80% range
  of the stated outcome holds 77-83% of results. Run for rushing yards, receptions, receiving
  yards, passing yards (QB starters).
- **Spread test.** W = his trailing 4-game average; the central 80% workload range holds 77-83%
  of actual workloads. Per market.
- **Round trip.** The "book expects" workload fed back returns the no-vig chance within 1 point.
- **Game-story rows.** Team carries by result bucket (won by 8+, within 7, lost by 8+), from prior
  games, predict the actual bucket averages within about 1.5 carries on 2024-25 (read at the
  held-out step).
- **Unit tests:** the MATCHUP block leaves every card number unchanged; odds conversion; name matching (Joshua/Josh, "C.McCaffrey", suffixes); the
  leakage cut-off; the boundary rule (no import from `props.engine` or `props/engine/`, by AST,
  same pattern as `props/tests/test_boundary.py`).
- **Sanity targets** (from the user's prototype; within about 1 before tuning is expected):

  | inputs | Over | Under | book |
  |---|---|---|---|
  | ypc 3.97, line 64.5, -125/-132 | 19.1 | 16.2 | 17.6 |
  | ypc 4.19, line 54.5, -127/-130 | 15.6 | 13.1 | 14.3 |
  | catch 0.74, rec 6.5, -128/-128 | 10.2 | 8.7 | 9.4 |

A failed test is reported as failed. Pass marks are not changed after a result is read.

Process: per CLAUDE.md, every new script goes through the code-review skill before any test or
grid reads its output, and the branch gets a code review (high) before its PR merges.

## Open questions for the user

Each has a proposal; none is acted on until answered.

- **Q1. Data access.** The brief says "fetch raw files directly". CLAUDE.md's one-data-layer rule
  and the CI guardrail (`tests/test_core_guardrails.py`) fail any new module that reads nflverse
  or Sleeper URLs itself, and the allowlist may only shrink. `core.fetch` downloads the same raw
  files (age-checked cache, refuses truncated downloads) and is stdlib-only, and props is already
  allowed to use it. It is not part of the engine. Proposal: use `core.fetch`.
- **Q2. Matching.** Proposal: Sleeper id -> gsis id first (as #224), the brief's name rules as the
  fallback, every fallback and miss logged. `core.ids` is not used (props may not import it).
- **Q3. "Recent games" for the blend.** Proposal: this season and last, all games before the
  priced week. Alternative: a fixed number of recent games (would be a ninth setting unless fixed).
- **Q4. Good-day multiplier on receiving yards.** The brief gives it to rushing only. Proposal:
  none for receptions; for receiving yards, start without it and add it (reusing `good_day_sd`)
  only if the conversion test fails on spread.
- **Q5. "Good day" on the card.** Proposal: his 75th-percentile game-level rate this season and
  last. Alternative: blended rate x (1 + good_day_sd).
- **Q6. Log location.** Proposal: `props/calc/log/legs.jsonl`, committed (it is the user's record,
  small). Alternative: gitignored, local only.
- **Q7. What counts as a setting.** Proposal: only the 8 tuned numbers above; the fixed choices
  listed under them are design, changed only through this note.
- **Q8. 2018 as warm-up only.** Proposal: yes. Alternative: also fetch 2016-17 pbp for pools so
  2018 can be scored (outside the brief's "2018 to present").
- **Q9. Where the tests live.** `props.yml` runs `pytest props/tests` before every capture, so a
  calc test there could block the engine's capture. Proposal: unit tests in `tests/test_calc_*.py`
  (run by the repo's CI job, not the capture), and the boundary test there too. The data-heavy
  tests are scripts in `validate.py` writing to `reports/calc/`, not pytest.
- **Q10. Registry.** CLAUDE.md requires every model and projection source in `core/registry.py`.
  This is a calculator, not a projection, but it has tuned settings. Proposal: register it as
  `provisional` with the note "calculator; validated by the conversion and spread tests" and move
  it to `live` with the held-out report as evidence if it passes.
- **P1-P4** under Passing yards; **M1-M6** under the MATCHUP block.

## Order

1. This note and DECISIONS #226 (stop for approval). 2. Log and standalone Sleeper capture.
3. Rushing and receptions + conversion test. 4. Leg card, with the MATCHUP block. 5. Receiving yards, then passing yards.
6. Entry check. 7. Held-out read and write-up.

## Held-out read

Not yet done. Recorded here, once, at step 7.

# Round 44: an early-exit chance in the backs' carries draw (pre-registered 2026-10-09, before any run)

## Why

The diagnostic (experiments/game_script_carries.py, reviewed twice; shipped engine, 2022-24 and
2026 weeks 2-4, 1,630 team-games, 2,973 back-games) graded the carries draw's two stages alone:

| Stage | Outside the 80% range | Below p10 | Above p90 |
|---|---:|---:|---:|
| Team carries vs the engine's team mean | 17.5% | 9.1% | 8.4% |
| A back's carries given the team's actual total (touched the ball) | 26.7% | 11.9% | 14.9% |

The two recombined reproduce the harness's own carries PIT (26.8% vs 26.9%). Team carries
swing with the score (about -5 to +5 carries from blowout to blowout) but the engine's team
width already holds that. The miss is in the split, it is not game script (correlation with the
surprise margin 0.04), and its extreme low end is far too thin: games with 40% or less of the
carries his share of the team's total gives him happened **3.0x** as often as the engine's own
draw allows for RB1s (5.0% vs 1.7%, zero-touch scratches excluded; booms at 1.5x+ ran 1.5x).

Round 28b (a uniformly wider split) improved rushing yards and attempts on 2022-25 but lost
rushing attempts on 2026 weeks 2-4: a wider split spreads probability evenly and cannot make a
3x lower tail without overdoing the middle. Early exits (an injury in the game, a benching, a
committee flip) are a different shape: a small chance of a large cut.

**Hypothesis:** a mean-preserving early-exit chance in the share draw prices rushing yards at
the stand-in lines better than the shipped split, alone or with a slightly wider split.

## The option (built for this round; off = today's sampler, byte for byte)

`width_params.json` gains `carry_exit_rate` (0 = off) and `carry_exit_min_share` (0.15):

- Per simulation, each eligible non-QB rusher whose expected share is at least
  `carry_exit_min_share` (a real role) exits early with probability `carry_exit_rate`,
  independently. An exit multiplies his share in that simulation by U ~ Uniform(0, 0.4).
- The share he loses goes to his non-QB teammates on the board in proportion to their shares in
  that simulation (the backup gets the work). The starting QB and the 'other' bucket are left
  alone.
- **Mean-preserving:** before the draw the expected shares are adjusted (a fixed point, per
  team-game) so every player's average share equals the shipped one; a unit test holds every
  player's simulated mean carries within 1% of the off setting's.
- The thresholds 0.4 and 0.15 are fixed here, not tuned: 0.4 is the diagnostic's collapse
  line; 0.15 is the carry share that makes a player a key teammate (research.is_key_teammate).

## The grid (nothing else moves)

| Knob | Shipped | Grid |
|---|---|---|
| carry_exit_rate | 0 (off) | 0, 0.02, 0.03, 0.05 |
| share_conc_carries | 20 | 20, 15 |

Eight settings; the shipped one is (0, 20). The diagnostic's RB1 excess was about 3.3 points of
collapses, which the grid brackets.

## The rule (fixed now) -- props/tools/round44_select.py

**Runs:** `backtest.py --tune-width --tune-grid carryexit --conditional --save-results`, seeds 0-3
(`--audit-seed-offset`), every other setting as shipped. Selection: 2022-25 weeks 2-18.
Confirmation: 2026 weeks 2-5 (every week played), read once.

**Rule amendment (reports/scoreboard.md, made now, before any read; DECISIONS #227):** the
scoreboard judges volume-spread changes on the spread check (real / model spread in stable-role
stretches moving toward 1). That check measures variance in stable roles and cannot see shape;
for carries it already reads 1.01-1.06, so any added spread "moves past 1" by construction. A
change to the SHAPE of a volume draw is judged on the own-volume score at the stand-in lines
(the Over chance where bets sit, which rewards the right tails) and the PIT tail it targets,
with the spread check as a guard.

- **Four seeds (#202):** each setting's Over chances are averaged over the four seeds per
  player-game before scoring; per-seed gains are reported, and a gain under 0.3% of the shipped
  log loss must be positive on every seed.
- **Pick (on 2022-25):** props/tools/grid_select.run on the four-seed averages, market rushing
  yards, own-volume score (pu_rush), bettable backs (8+ projected carries); ties within 0.0005
  to the setting closest to shipped; a pick moving the Over chance under **1.8 points** on
  average stays shipped (the four-seed minimum, round 43).
- **Detectable:** the pick's rushing-yards own-volume log-loss gain over shipped has a 95%
  game-clustered interval wholly above zero (10,000 resamples), log loss and Brier agreeing in
  sign in the 15-85% decision zone.
- **The tail it targets:** on bettable backs, the share of carries outcomes below the model's
  10th percentile (pit_car) moves toward 10% and not past it: |pick - 10%| < |shipped - 10%|.
- **Guards:** the bet markets (receptions, receiving yards, rushing yards, rushing + receiving
  yards, QB passing yards) no worse than 0.5% of their own log loss, on conversion and own
  volume (point estimates); rushing attempts and completions block only when wholly worse.
  **Spread guard:** in no carries band (8-12, 12-16, 16-20, 20+) does the model become too wide
  for sure (real / model interval wholly below 1), role-only stable stretches, 2022-25.
- **Confirmed:** on 2026 weeks 2-5, the pick's rushing-yards own-volume gain over shipped is not
  negative (point estimate) and the decision-zone signs agree. The running-game family has been
  read six times on 2026 weeks (comparisons ledger; round 43's ypc arm included): this is the
  seventh, so its interval is reported at 1 - 0.05/7 (99.3%).
- **Ships** only if every line above holds; otherwise null, and the shipped split stays.
  Logged in reports/comparisons_ledger_2026.md either way.

**Disclosed:** the diagnostic that motivates this round read 2026 weeks 2-4 (carries PIT shape
only, no candidate). The confirmation weeks include those three; week 5 is unread by any
running-game candidate.

## Amendments, 2026-10-09, before any run (from the code review of the built option)

- **The handout:** an exiter's lost share goes to his non-QB teammates in proportion to their
  EXPECTED shares, not their shares in that simulation. With per-simulation shares the means could
  not be held: a tiny receiver (a receiver's 0.8 carries) ran 4.5% high. With expected shares the
  mean correction is exact (every combination of exiters enumerated) and the 1% test holds for
  every player, including a 0.01-share receiver.
- **The keep fraction is a knob:** `carry_exit_keep` (0.4) in width_params.json beside the other
  two, not a code constant; not gridded.
- **A named starting QB is required:** without one the option stays off for that team-game (a
  running QB is not a back).
- **The tail rule, written as meant:** "toward 10% and not past it" -- the pick's share below p10
  on the same side of 10% as shipped's and nearer; the formula alone allowed an overshoot.
- **The soft guards, made concrete:** rushing attempts (bettable backs) and completions (starting
  QBs) block when the paired CRPS difference, seed-averaged per player-game on 2022-25, has a 95%
  game-clustered interval wholly on the worse side. The scoreboard's log-loss guards cover only
  its five markets.
- **Run integrity:** the confirmation frames must hold 2026 weeks 2-5; the spread guard refuses to
  run without the starting QBs (it would treat a starter change as a stable stretch).
- **For the ship PR, if it ships:** exit eligibility (share >= 0.15) is decided after the workload
  search scales a share, so research.implied_carries would need the unscaled share.

## Result

(Filled in after the runs, below this line, without editing anything above.)

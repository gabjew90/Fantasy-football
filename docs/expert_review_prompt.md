# Expert review prompt — draft engine

Paste everything below the line to a fantasy-football statistics expert.
Written to be self-contained: it assumes no knowledge of this repo.

---

I've built an automated draft engine and I'd like you to poke holes in it.
Please be blunt — I'm more interested in what's wrong than in reassurance.

## The league

10-team, **half-PPR**, snake, 15 rounds, 1-minute clock. Starters:
QB, RB, RB, WR, WR, TE, **one** W/R/T flex, K, DEF, plus 6 bench and 2 IR
(IR not filled during the draft). Passing TD 4pt, 25 yd/pt, plus a league
quirk: **+2 bonus on 40+ yard passing TDs** (recorded but not modelled —
my weekly data lacks TD distance).

## How it values players

**Projections** blend a usage-based statistical model with market consensus
(FantasyPros ECR/ADP). The blend weight varies by player type: 0.65 toward
the model for stable veterans, 0.40 for players who changed teams, 0.55
default. A small number of manual overrides are allowed for hard facts only
(transactions, injuries, depth chart, coaching changes) — never hype — capped
at 8 overrides, none moving a projection more than 40%. Players who are out
(suspension, exempt list) are zeroed.

**VORP** = projected points − points of the "replacement" player, where
replacement is a rank I set per position. Currently:

| pos | baseline | replacement is | elite VORP |
|---|---|---|---|
| QB | QB5 | ~QB5 (274.8 pts) | best QB +20.6 |
| TE | TE8 | ~TE8 (127.4) | best TE +62.8 |
| RB | RB24 | RB24 (160.2) | best RB +122.8 |
| WR | WR24 | WR24 (147.0) | best WR +68.9 |

RB/WR are format-derived (10 teams × starters, flex demand split
45/45/10). **QB and TE are not** — see the open questions.

**Standing tilts**, each capped at 10%: fade mid-tier TEs, fade non-rushing
QBs, boost rushing QBs late, small boost to elite TEs, and a 10% regression
haircut on last season's positional top 5.

## How it decides on the clock

1. **Survival simulation.** Monte Carlo over every rival pick between now and
   my next turn (1000 sims). Rivals sample from a rolling ADP window around
   the current pick, weighted by an ADP Gaussian whose sigma grows from 6
   picks in round 1 to 27 by round 15, damped by the roster slots they've
   already filled, and tilted by their own historical positional tendencies.
   Includes a fat-tail mixture: 15% of the time a rival's noise is scaled 3×,
   one-directionally (rivals reach early, they don't reach late), plus
   positional-run escalation when 2+ picks of one position land in a 5-pick
   window.

2. **Calibration.** Raw survival probabilities are shrunk toward 0.5:
   `calibrated = 0.5 + (raw − 0.5) × 0.55`. Fitted to my own completed draft
   (n=67): raw 96% → actual 75%, 82% → 68%, 45% → 50%.

3. **Urgency** per position = VORP(best available now) − E[VORP(best
   available at my next turn)].

4. **Candidates**: one per position — the top 3 there after guardrails, with
   near-ties (within 2 VORP) broken by who's fallen furthest past ADP. From
   round 8 onward the position is first re-sorted on an upside-boosted proxy
   (×1.15 for flagged high-variance players) before truncation, on the theory
   that bench picks win on 90th percentiles rather than medians.

5. **Two-pick joint planner.** Rank by
   `pair = need-weighted VORP(now) + best expected partner at my next turn`,
   where a same-position partner is capped at the second-best currently on
   the board. This exists because greedy per-position urgency "won the pick
   and lost the round" twice in a real draft.

**Hard guardrails**: never a 3rd QB or TE; no QB2 before round 10; a 2nd TE
only if a top-6 TE has fallen 12+ picks past his ADP; K/DEF only in the final
two picks; at most one zero-role stash; and once remaining picks ≤ open
starter slots, starters only.

## Where I know I'm on thin ice — please attack these

1. **I fitted the QB and TE baselines to ADP.** Format math gives QB10/TE11;
   I swept values and picked the ones minimising mean |board rank − ADP rank|
   over each position's top 10, landing on QB5/TE8. Three problems: n=10, the
   optimum is flat (QB4–QB7 are all within ~2), and it's fitted to market
   rather than validated on outcomes. Is calibrating a *structural*
   assumption to market defensible while leaving projections independent, or
   is it circular? Is there a better way to set replacement level in a
   10-team league?

2. **My TE projections may be the real issue.** The board has TE1 at 190 and
   TE2 at 189, then TE3 at 147 and TE4–TE8 within 4 points of each other. So
   elite TEs carry +62 VORP and keep surfacing in the first two rounds. Is a
   ~43-point gap between TE2 and TE3 plausible, or is that a modelling
   artifact? No choice of baseline changes this — it's the projections.

3. **Two elite TEs, both starting** (one at TE, one in the flex). The engine
   will do this when they're the two best players available. In a 10-team
   half-PPR with a single flex, is that a real strategy or a trap?

4. **QB2 not before round 10.** With a QB5 replacement level the engine
   already wants QBs late. Is a hard round gate the right instrument, or
   should QB2 just be allowed to compete on value?

5. **Survival shrink 0.55** was fitted to 67 observations from one draft.
   Does that magnitude of overconfidence match your experience of how often
   "he'll last another round" is wrong?

6. **What's structurally missing?** Things I do not model at all: bye-week
   stacking (warned but never scored), handcuffing (display only), playoff
   schedule strength, positional runs beyond the 5-pick window, and any
   opponent-specific reads beyond historical positional tendency.

What would you change first?

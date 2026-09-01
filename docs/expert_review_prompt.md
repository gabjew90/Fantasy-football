# Expert review prompt — draft engine

Paste everything below the line to a fantasy-football statistics expert.
Self-contained: assumes no knowledge of this repo.

The framing matters. This engine is meant to be **league-agnostic** — you
point it at a league and it derives that league's parameters from format.
So the interesting question is not "are these numbers right for my league"
but "is the derivation right for any league". Two leagues run on it today
(12-team full-PPR Sleeper, 10-team half-PPR Yahoo) and more are expected.

---

I've built a draft engine that is supposed to adapt to any league you point
it at. I'd like you to attack the **derivation logic**, not tune numbers for
me. Please be blunt.

## What is fixed vs derived

A league is described by facts only — team count, roster slots, scoring,
rounds. Everything positional is then derived:

- **Replacement baseline** per position = `round(teams × starter demand)`,
  where a flex slot contributes demand split **RB 0.45 / WR 0.45 / TE 0.10**,
  and a superflex contributes QB 0.8 / RB 0.1 / WR 0.1.
  - 12-team, 1 QB, 2 flex → QB12, RB40, WR60, TE12
  - 10-team, 1 QB, 1 flex → QB10, RB24, WR24, TE11
- **VORP** = projected points − the points of the player at that rank.
- Projections blend a usage model with market consensus, weighted 0.65 toward
  the model for stable veterans, 0.40 for players who changed teams.
- Scoring (half vs full PPR, TD values, bonuses) feeds the projections.

## What decides the pick

Monte Carlo over every rival pick before my next turn (1000 sims). Rivals
sample from a rolling ADP window, with ADP noise sigma growing from 6 picks
in round 1 to 27 by round 15, damped by the roster slots they've already
filled, tilted by their historical positional tendencies, plus a fat-tail
mixture (15% of the time noise ×3, one-directional — rivals reach early, not
late) and escalation when 2+ picks of one position land in a 5-pick window.

Raw survival probabilities are then shrunk toward 0.5:
`calibrated = 0.5 + (raw − 0.5) × 0.55`.

Urgency per position = VORP(best available now) − E[VORP(best available at my
next turn)]. Final ranking is a two-pick joint plan:
`need-weighted VORP(now) + best expected partner at my next turn`, with a
same-position partner capped at the second-best currently on the board.

## The core problem I want your help with

**The format-derived baseline appears to be wrong for streamable positions,
and I patched the symptom instead of the derivation.**

In the 10-team league, `teams × demand` gives QB10. That says: if I skip
quarterbacks, I end up with roughly the 10th-best QB. But the market behaves
as though it's about QB5 — and empirically, in a mock, the QB my board ranked
5th was still on the board at pick 98. My board consequently reached **35
picks past ADP on QBs** while RB (+2) and WR (+2) were well calibrated.

I "fixed" it by hand-fitting QB5/TE8 for that one league, minimising
`mean |board rank − ADP rank|`. That is bad on three counts: n=10, the
optimum is flat (QB4–QB7 all within ~2), and **it does not generalise** —
the next league onboarded gets the same broken QB10 derivation.

So, the questions:

1. **What is the right derivation for replacement level at streamable
   positions?** Starter demand clearly overstates scarcity for QB/TE/K/DEF,
   because the waiver pool stays startable all season in a way it doesn't for
   RB. Should replacement be derived from the *shape of the projection curve*
   (e.g. how many players sit within X% of the positional best) rather than
   from team count? From expected number rostered? Something else?

2. **Should the flex split vary with scoring?** I use RB 0.45 / WR 0.45 /
   TE 0.10 everywhere. In full PPR, pass-catching backs and slot receivers
   gain a lot relative to half. Does flex composition actually shift enough
   to matter, or is the split second-order?

3. **Which of my constants should be league-derived rather than universal?**
   Currently identical for every league regardless of size or scoring:
   - "no second QB before round 10"
   - "a second TE only if a top-6 TE has fallen 12+ picks past ADP"
   - survival calibration shrink 0.55 (fitted to a *single* 12-team draft,
     n=67, then applied to a 10-team league)
   - K/DEF confined to the final two picks

   Intuitively the QB2 gate should be later in a 10-team league than a
   14-team one, and TE rules should depend on scoring. But I'd rather hear
   which of these genuinely need to scale and which are fine as constants.

4. **Is the projection curve itself the real problem?** In the 10-team board,
   TE1 projects 190 and TE2 189, then TE3 147 and TE4–TE8 within 4 points of
   each other. Elite TEs therefore carry +62 VORP and keep surfacing in the
   first two rounds. No choice of baseline changes that — it is the
   projections. Is a ~43-point gap between TE2 and TE3 plausible, or does
   that pattern indicate a modelling artifact?

5. **Two elite TEs, both starting** — one at TE, one in the single flex. The
   engine will do this when they are the two best available. Real strategy or
   trap, in a 10-team half-PPR?

6. **What is structurally missing?** Not modelled at all: bye-week stacking
   (warned, never scored), handcuffing (display only), playoff schedule
   strength, and any opponent read beyond historical positional tendency.

What would you change first — and is there a principled way to make
replacement level adapt to a league without fitting it to that league's ADP?

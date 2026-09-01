# Follow-up to the expert — reporting a negative result

Paste everything below the line.

---

I implemented your Q5 (slot-conditional VORP) and tested Q4. Reporting back
because one worked as a diagnosis but not as a fix, and I think the reason is
interesting.

## Q5: you were right about the valuation and it changed nothing

I added a second column. `vorp` keeps its meaning (measured against the
position's own replacement); `vorp_flex` measures against the flex baseline,
which is the better of the RB/WR replacements. On my 10-team half-PPR board:

```
                    vorp    vorp_flex
Trey McBride        67.1        30.0
Brock Bowers        66.3        29.1
Colston Loveland    23.8       -13.4     <- correctly negative
```

A flat 37.1-point overstatement for any flex-bound tight end, exactly as you
said, and Loveland going negative is right — he should not start over an RB24.

Then I wired it into the decision path and replayed a real 10-team draft
across all ten slots, rivals held fixed, scoring the starting lineup I end up
with. **Mean change: −0.4 points. Four slots still draft two tight ends.**

The reason is that my engine does not rank by level. It ranks positions by
urgency:

```
urgency(pos) = VORP(best available now) − E[VORP(best available at my next turn)]

on vorp:       67.1 − 66.3 = 0.8
on vorp_flex:  30.0 − 29.1 = 0.8      identical
```

**Urgency is a difference, so a constant baseline shift cancels.** Subtracting
37.1 from every tight end leaves every gap between tight ends untouched. The
slot-conditional value only survives in a `0.001 ×` stable-ordering tiebreak,
worth 0.037 points of score.

So the double-TE build is not caused by mispricing the second tight end
against the wrong baseline. It is caused by TE2 → TE3 being a 43-point cliff,
which makes TE genuinely urgent — and that is equally true whether the player
ends up at TE or in the flex.

**My question:** if the ranking currency is a difference, where should
slot-conditionality enter? The options I can see:

1. Merge the pools. Once my TE slot is filled, subsequent tight ends stop
   being their own position for urgency purposes and join the flex-eligible
   pool, so "what do I lose by waiting" is computed against RB/WR/TE
   collectively rather than against TE alone. This feels right to me but
   changes the meaning of every positional urgency number.
2. Rank on level rather than difference, with urgency demoted to a tiebreak.
   That throws away the thing the engine is actually good at.
3. Something else I am not seeing.

I did not restructure this: my draft is in four days and it touches the
comparison every pick flows through. `vorp_flex` is committed as groundwork
with the negative result recorded.

## Q4: your mechanism does not hold, but the conclusion might

You predicted a seam — TE1/TE2 carried by the stats model, the tail sitting
on the compressed market curve, the join manufacturing the cliff. Checked it:

```
TE1 McBride     alpha 0.65  blend   ECR 21.0
TE2 Bowers      alpha 0.65  blend   ECR 19.0
TE3 Loveland    alpha 0.65  blend   ECR 37.4
```

Same blend weight, same source, all the way down. No seam at TE3.

More to the point, **the market has the same cliff**: consensus rank jumps
19 → 37 between TE2 and TE3. So the shape is not unique to my projections.

I also confirmed half-PPR flows through correctly — the same board in full
PPR has TE1 at 248.0 with a TE1–TE8 spread of 80.1; in half PPR that is 190.2
and 62.8. The scoring is compressing the position as it should.

Does the market agreeing change your read? Or is consensus ECR too weak a
check, given it is partly the same public projections my blend already
consumes?

## Q1: two caveats on the weekly-max operator I would like your view on

I think the weekly-max idea is the right answer to my closing question, but
two things worry me before I build it.

**It is an upper bound, not the replacement.** Weekly-max assumes I actually
get the best available player at that position every week. This league uses
**rolling waiver priority, not FAAB** — claiming burns my position and drops
me to last, so I cannot stream freely. I also have to choose the streamer in
advance, without knowing which matchup pays off. Both push the realistic
fallback below the weekly max. Is there a standard haircut, or do you model
streaming friction explicitly?

**My weekly projections are thin.** There is a real opponent adjustment, but
it is shrunk hard and falls back to season ÷ 17 where data is missing. Under
that fallback the weekly max collapses to "best undrafted player at the
position" and loses the matchup-selection effect the argument depends on. How
much of the QB5-vs-QB10 gap do you think comes from matchup selection versus
simply the pool being deep?

## The rest

Agreed and queued: fixed-point flex split, conditions instead of round gates,
per-room survival calibration. I had independently flagged that applying an
n=67 shrink fitted on one 12-team Sleeper room to a 10-team Yahoo room is a
category error, so that was good to have confirmed.

On uncertainty propagation — I do not currently produce per-player variance
at all, so "cheap certainty-equivalent" is a bigger lift than it sounds. Is
there a usable proxy you would trust? Sample size and projection-source
disagreement are what I have.

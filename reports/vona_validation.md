# VONA vs VORP — draft-day ranking validation (2026-08-31)

## Why

Mock 8 reached an average of **9.4 picks past market**, worst of all on
Mahomes: taken at 42 against an ADP of 102, to gain **0.72 pts/game** over
Purdy — who was still on the board at 99. The cost landed on the bench: four
WRs at or below replacement, because a mid-round pick went to a position
where waiting was nearly free.

VORP cannot see this. It scores against a fixed replacement, so it is blind to
how *flat* a position is:

| pos | top-10 spread | per game |
|---|---:|---:|
| RB | 82.3 | 4.84 |
| TE | 67.5 | 3.97 |
| QB | 35.0 | 2.06 |
| WR | 33.6 | 1.98 |

VONA asks the draft-day question instead: how much better is this player than
whoever I could still get **at my next turn**? Flat positions self-discount;
scarce ones do not. Within a position VORP differences *are* projection
differences (shared baseline), so VONA is the gap to the best expected
survivor.

## Method

`scripts/vona_replay.py` replays a completed draft with the rivals' picks held
FIXED and only our own re-decided, under each ranking. Scored two ways:

- **CLV** (closing ADP − pick slot) — the repo's standing out-of-sample grade.
- **Starting-lineup VORP** — the decision-relevant outcome. CLV alone is
  biased *against* VONA, because taking a scarce-position player early reads
  as a reach even when it is correct.

## Result — 22 slot replays across 2 real drafts

| Metric | mean | median | VONA better |
|---|---:|---:|---:|
| CLV delta | +0.34 | −0.12 | 10/22 |
| Lineup VORP delta | **+10.3** | **+11.6** | **16/22** (2 worse, 4 tied) |

stdev 23.2 · worst case −63.9

**VONA builds better lineups at no cost in market discipline.**

## Limitations, stated plainly

- Within a draft the slots share one opponent pick sequence, so the replays
  are **correlated, not independent**. Effective sample is nearer 2 drafts
  than 22; no p-value is claimed.
- Two replays lost badly (−29.4, −63.9). VONA concentrates value into scarce
  positions — right on average, higher variance.
- The counterfactual assumes rivals pick identically regardless of what we
  take, which is false at the margin.

Shipped on the consistency (16 of 18 non-tied) plus the mechanical rationale,
not on a significance test.

## Known failure mode — found at slot 9

VONA underestimates urgency when a position holds **two** elite players and
the roster can start two of them (TE + FLEX).

Slot 9, 10-team replay:

| pick | VORP took | VONA took |
|---:|---|---|
| 9 | **McBride (TE)** | Cook III (RB) |
| 12 | **Bowers (TE)** | McBride (TE) |
| 29 | Cook III (RB) | Kyren Williams (RB) |

VONA's reasoning at pick 9 was locally correct: Bowers survives to pick 12,
so McBride's urgency is only 67.1 − 66.3 = **0.8**, and there is no rush at
TE. It was right — McBride *was* still there at 12.

But it took only ONE of the pair. VORP took both at 9 and 12, and Cook
survived to 29 anyway, so VORP captured all three. Final lineup VORP 375.7
against VONA's 346.3.

The gap: VONA computes the fallback as "best survivor at this position",
which assumes we fill **one** slot there. With TE + FLEX we can start two,
and the fallback for the *second* TE is the third-best TE, who is far worse.

Not fixed, deliberately, four days from the draft: it costs a slot-dependent
amount, VONA is still ahead at 8 of 10 slots (mean +12.5, median +10.4), and
a depth-aware fallback is a bigger change than the evidence justifies right
now. Revisit in the offseason.

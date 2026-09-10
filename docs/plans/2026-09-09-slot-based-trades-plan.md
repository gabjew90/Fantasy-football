# Plan: trades are read in slots -- one currency per side

Verified against HEAD `d732ee0` (2026-09-09). Retires the gate-1 counterparty
test and the market-mode prototype (scratchpad only, never shipped). Covers
both leagues.

## What this is

Today's trade gate asks the counterparty the wrong question in the wrong
currency. `verdict()` requires `their_delta >= 0` -- the other manager's
lineup, in MY point projections. Measured this session: that surfaces
packages worth +0.6 a season to him, which nobody accepts, and the only thing
that passed it was a dead-weight sweetener. Deebo Samuel scores surplus 0.0
against every roster in isolation and carried the entire +7.2 of the best
package on the board -- and to the manager receiving him he is clutter.

The market-mode prototype swung the other way: "he says yes if his FantasyCalc
gain is >= 110%." Roster-blind. It recommended Caleb Williams + Derrick Henry
for Amon-Ra St. Brown as a +13% market win for cbarone -- who has Jalen Hurts
and would start Caleb never. Counting only what he could use, the deal was 80%.
A no. Caleb starts for exactly one team in the league, by 4.4 points.

Neither is how a person reads an offer. A manager thinks in **slots**. For
each player he would receive: does this upgrade a starter? Does it give me
depth I actually need? Otherwise it is nothing, whatever the market says.
Same three questions for each player he gives up.

The design (user, 2026-09-09):

- **Counterparty**: modelled on *perception*. He accepts if a player I send
  is a POSITIONAL rank upgrade for him AND the market value of his resulting
  starters, backfill included, does not drop. Both. (User, 2026-09-09.)
- **Me**: modelled on *points* -- the joint re-solve `price()` already does,
  plus `depth_risk`. The per-source range is REPORTED, never gated: mean and
  range in pts/wk on every row, and whether to send is the user's decision.
- **Dead weight** counts for nothing on either side. That is what retires the
  sweetener.

## The classification

After the joint re-solve (`slot_moves`), every player in a package lands in
exactly one class on the roster that RECEIVES him:

| class | test | counts toward |
|---|---|---|
| STARTS | in the starting lineup after -- the post-backfill lineup `price()` returns, not raw `slot_moves` | both acceptance tests |
| USABLE_DEPTH | not starting; best non-starter at his position; better than the best wire body at that position | display only |
| DEAD_WEIGHT | neither | nothing |

A class is a SLOT FACT about one player on one roster, not a verdict, and
STARTS is not the same as UPGRADE. Deebo Samuel STARTS for ayatollahabdullah
after Wilson leaves -- he fills the emptied flex -- and is a downgrade at WR
against every receiver they had (overall 141 against a worst starter at 30).
He is tagged FILLER. The verdict is the two acceptance tests below, applied
to the whole starting set. The first draft called this class STARTER_UPGRADE
and the name was wrong twice over: it read as a verdict on the trade, and it
conflated starting with upgrading.

And on the roster that GIVES him:

| class | test | counts toward |
|---|---|---|
| STARTED | was starting before | starters-market test |
| DEPTH_LOST | was best backup at position and better than wire | display only |
| FREE | neither | nothing |

"Better than the wire" is the test that made Caleb worthless to everyone at
once: six QBs at 253-275 sit on the Omnibeta wire. Depth a manager could
claim tomorrow is not depth.

## Acceptance: does it look like a win to him

Two tests. He accepts only if BOTH pass.

**Test 1 -- a positional rank upgrade from me.** A player I send is an
upgrade if he beats the WORST INCUMBENT STARTER AT HIS OWN POSITION before
the trade, on overall ECR, counting a flex-starter at that position as a
starter. At least one sent player must be an upgrade.

POSITIONAL, and LABEL-FREE. Position is a fact about the player. The slot
name -- RB1, RB2, FLEX -- is an artefact of the optimiser's fill order and
must never be compared across the trade: a team's best RB can sit in the
flex label, and a bench RB gets the RB2 label the moment someone better
leaves. Three earlier drafts of this test each failed on that:

  * a slot-label test (RB2 before vs RB2 after) is fragile to relabelling;
  * a whole-set test (everyone who left vs everyone who entered, matched by
    rank) is net rank in disguise and rejects Javonte -> Wilson, because it
    treats an RB and a WR as interchangeable seats;
  * the position test sees what a manager sees: Javonte (RB, overall 43)
    against their worst starting RB Monangai (120) is an upgrade, and
    Monangai sliding to the flex label does not undo it.

It also separates starting from upgrading. Deebo STARTS for
ayatollahabdullah and is tagged FILLER: WR overall 141 against a worst
starting WR of 30.

**Test 2 -- the market value of his resulting starters must not drop.**
`sum(FantasyCalc over his starters after, backfill included) >=
sum(over his starters before)`. A roster-state test, not a transaction
test: it does not care what he "received", only what his starting lineup is
worth as a set of assets. Dead weight never enters it (a non-starter is not
a starter); the body he must DROP in a 2-for-1 never enters it either.

**Reported, not gated -- net overall rank of his starters.** `sum(overall
ECR before) - sum(after)`. This is the rankings-reader's view of the same
trade, and it disagrees with Test 1 exactly where the expert board and the
trade market disagree: Javonte -> Wilson is a positional upgrade AND net
-13, because the panel has Wilson at 30 and Javonte at 43 while the market
values Javonte more (4,860 against 3,774 -- the RB premium). A manager who
reads FantasyPros refuses; one who reads his trade calculator accepts. No
rule can say which he is; the ledger can. So the flag is printed on every
row -- "rankings-reader would refuse, net -44" -- and the ledger decides
whether it is promoted to a gate.

Measured on the known cases, Test 1 + Test 2:

| package | Test 1 | Test 2 | his net rank | his side |
|---|---|---|---|---|
| Caleb + Henry -> St. Brown (cbarone) | Henry over Warren | -1,717 | -32 | reject |
| Javonte -> Wilson (ayatollahabdullah) | Javonte over Monangai | +1,086 | -13 | accept |
| Javonte + Deebo -> Wilson | Javonte; Deebo FILLER | +1,003 | -20 | accept |
| RJ Harvey -> Bo Nix (rybryethguy) | Harvey does not start | 0 | 0 | reject |
| Henry + Fannin -> McMillan + Smith | Henry over Warren, Fannin over Goedert | +288 | -44 | accept |

The net ranks in that table were measured on the DynastyProcess mirror
(`ro` board, 2026-09-04). The live FantasyPros ALL board (2026-09-10, panel
181) reproduces every verdict and every tag, with net ranks of -27, -12,
-31, 0 and -42 respectively. The first live cut read `position=OP` -- the
SUPERFLEX board, quarterbacks stacked on top, Caleb Williams at overall 8 --
and was caught because positional rank tracked the mirror exactly while
overall did not. `rank_panel()` now chooses the board from the league shape
and every row says which list it came from.

The last row is the deal this whole design was built on rejecting, and his
side now ACCEPTS it. That is correct: "accept" is a prediction that a
position-by-position manager plausibly clicks yes -- RB up, TE up, value
even -- not a claim the deal is good for him. What the old standard got
wrong was ME recommending it as good for both. Under this design my side
shows +18.2 on the blend with a range of -20.4 to +50.0 across sources, and
the user decides. That deal is the reason the range is reported and not
gated.

Rank source: FantasyPros consensus OVERALL rank, positional carried for
display, from the largest panel available -- `type=draft` (~149 experts)
while it is fresh; `type=ros` is a three-expert panel and every row must
carry its panel size so a 0.00 sd is never read as agreement.

## My side: what am I getting, and how sure is that

`my_delta > 0` on the blend filters the list -- a package the best estimate
says loses points is not worth a row. Everything else is REPORTED, and the
decision to send is the user's:

- **mean pts/wk** -- `my_delta / weeks_left` on the blended consensus;
- **range pts/wk** -- the same package priced on each source alone
  (Sleeper, ESPN, FantasyPros), min to max, over `weeks_left`;
- `depth_risk` at every position the package touches; `newly_thin`;
  `confident()`.

THE RANGE IS NOT A GATE. User decision, 2026-09-09: "that last gate is my
discretionary decision to reject or approve, you just tell me the mean and
the range I'm getting on points/wk." The earlier draft vetoed any package a
single source priced below -5 for me. On Henry + Fannin -> McMillan + Smith
that veto fired (FantasyPros alone says -20.4) and hid a package his side
accepts and the blend prices at +1.07/wk with a range of -1.2 to +2.9. The
range is MY uncertainty about MY gain; whether to act on it is judgement,
not arithmetic, and the tool's job is to make it legible, not to decide.

The market ceiling stays advisory (decision 2026-09-09).

## Step 1: the chip finder (revise `tradeable`)

A chip is a player who is **cheap for me to sell AND has a buyer**. Both.
Caleb is cheap (18.7 points with Jordan Love backfilled) and has no buyer.
Henry costs 88 and upgrades RB2 for cbarone (over Warren, 171) and for
ayatollahabdullah (over Monangai, 145) -- a rank jump either can see.

For each of my players:

- `true_cost` = lineup drop with **position-aware** waiver backfill (D1).
- `buyers` = teams where he is a POSITIONAL rank upgrade (Test 1) -- assessed
  in the buyer's currency, overall ECR, not in my points. Caleb has no buyer
  on points (`gain_to_add` is 0 for ten of eleven teams) and several on rank
  (Lord2Pale, Tulchh, DihtrickCohones all start QBs the panel ranks below
  him). A buyer has to be found in the currency the buyer uses.
- Rank chips by `true_cost` ascending among those with a buyer; unbought
  players last regardless of cost.

## Step 2: the package search

For each buyer, packages from chips (plus optionally one more piece), through
`price()`: my side passes; his side accepts; sort by my pts/wk; and print
both sides' slot classifications on every row so the reader sees WHY --
"Henry -> his RB2 seat over Warren (RB28 -> RB12)"; "Caleb -> dead weight
behind Hurts".

## Defects to fix before anything is built on them

- **D1 `marginal.backfill()` is position-blind.** It takes the top *n* of the
  wire by raw points. Harmless on my roster today (Deebo covers any flex hole)
  and coincidentally right for Caleb (the wire's best body is a QB). Give
  Henry in a 2-for-1 on a roster with no flex-eligible bench and it hands
  over a QB who cannot play flex, pricing the seat as empty. Feeds `price`,
  `depth_risk`, `thin_after`, and Step 1's `true_cost`. Fix: choose the body
  that maximises the resulting lineup, candidates = top 3 per position
  (about 18 solves, ~0.2 ms; the naive version over the whole wire is ~4 ms
  per package and too slow for the frontier).
- **D2 (known gap, NOT fixed by this plan): the receiver of a 2-for-1 must
  drop someone.** cbarone receives two and gives one; his roster grows by a
  body he has to cut, and the model charges him nothing for it. It is the
  mirror of the waiver backfill the GIVER earns, and it is unmodelled on the
  receiving side. Cheap once `classify()` exists -- the drop is whichever of
  his rows is FREE and lowest -- but it is a separate change and this plan
  does not claim it.
- **D3 (known gap, NOT fixed by this plan): a backfill can be credited for an
  upgrade the trade did not create.** The position-aware fill takes the wire
  body that raises the lineup most. When nothing on the wire fills the seat
  the trade emptied, that body can be an unrelated upgrade elsewhere -- one
  the roster could make any Tuesday by dropping its worst bench body. Caught
  live on 2026-09-09: a wire DEF that beat mine was picked as the backfill
  for a 2-for-1 touching no DEF seat, moving the package from +2.4 to +13.4.
  K and DEF are now excluded outright (streamed, never traded, single-source
  projections). The general case -- a wire WR who beats a current starter --
  is still credited to the trade. The honest cap is "what this spot is worth
  over dropping the worst bench body for the same add", and it is a separate
  change.

## What is retired

- `verdict()`'s `their_delta >= 0` as the counterparty test. Kept behind
  `mode="points"`; the default becomes `mode="slots"`.
- The market-mode prototype (scratchpad; never shipped).
- Gate 2's band as the acceptance test. The floor's job -- "will he refuse"
  -- is now answered by the classification. The advisory ceiling stays.
- The per-source range as a gate on my side (`MY_WORST = -5`). It is a
  report now -- mean and range in pts/wk on every row -- and the send
  decision is the user's. User decision, 2026-09-09.

## Knobs

```
POSITIONAL_TEST  = "worst_incumbent"  # Test 1: sent player beats worst starter at HIS position, overall ECR
STARTERS_MARKET  = "no_drop"          # Test 2: sum(market of his starters after) >= before, backfill in
NET_RANK_FLAG    = True               # printed on every row, never gated; the ledger decides
BACKFILL_TOP_K   = 3                  # per position, for D1
# RETIRED AS GATES, 2026-09-09: ACCEPT_RULE ("rank_or_market") and MY_WORST
# (the -5 per-source range veto). The range is a report: mean and range in
# pts/wk on every row, and the send decision is the user's.
```

## Measurement

The acceptance model predicts a human decision. The only true validation is
whether offers get accepted, which needs the ledger (season-manager v2, step
3, still owed): record every offer with its predicted classification and the
outcome, and grade the model on what came back.

Until then, regression fences for the cases that motivated this:

1. Caleb + Henry -> St. Brown (cbarone): his side REJECTS. Henry passes
   Test 1 (over Warren, 74); Test 2 fails, starters-market -1,717. Caleb does
   not start behind Hurts -- by the wire rule he classifies USABLE_DEPTH, a
   QB2 nineteen points over Jordan Love, not DEAD_WEIGHT -- and either way he
   never enters either test: not a positional upgrade, not a starter.
2. Javonte -> Garrett Wilson (ayatollahabdullah), straight: his side ACCEPTS.
   Test 1: Javonte (RB, 43) over Monangai (120). Test 2: +1,086. Net-rank
   flag -13. Appears with no sweetener attached.
3. Javonte + Deebo -> Wilson: Deebo STARTS and is tagged FILLER (WR 141
   against a worst starting WR of 30). The row must say so; the package is
   accepted on Javonte alone.
4. RJ Harvey -> Bo Nix (rybryethguy): his side REJECTS -- Harvey does not
   start for them, so Test 1 has nobody to test. Killed by acceptance, not
   by the range or `confident()`.
5. Position-aware backfill: a roster with no flex-eligible bench giving an RB
   in a 2-for-1 is backfilled with the best wire RB/flex body, not the best
   wire QB.
6. Henry + Fannin -> McMillan + Smith (cbarone) is LISTED, not dropped: his
   side accepts (Henry over Warren, Fannin over Goedert, +288), net-rank
   flag -44, my side +1.07/wk with range -1.2 to +2.9. The earlier range
   veto removed this row; it must now appear with those three numbers on it,
   because the decision it represents is the user's.
7. Henry + Warren -> Egbuka + A.J. Brown (Tulchh), UAT 2026-09-10: Brown was
   Out (ankle) on Sleeper and the radar priced him as a healthy WR11 at
   +1.16/wk from a day-old player file, because the trade path never read
   injury_status. Now: the player file is refetched after three hours in
   season; every roster and the wire go through `injury_discount()` before
   pricing (Out/Doubtful one week, IR/PUP four or FantasyPros `ir_weeks`,
   ros_season untouched so the range inherits the discount); and every
   injured piece prints `⚠ INJURED: name (pos) is Out -- priced at X ROS, Y
   healthy (n wk out)` ahead of the other warnings. Advisory, never a gate.
   Measured: the same package re-prices at +0.31/wk with Brown at 232/247.
   Sleeper's Out carries no duration, so a multi-week Out is under-discounted
   until it becomes IR; the line says the assumption out loud.

## Order

Status 2026-09-10: steps 1-7 landed -- D1 a043fd2, classify adba7b7, rank
plumbing e339933 (with the superflex-board fix), accepts 3a8adbe, verdict
modes 9f743c2, chips 39f4639 (with the K/DEF fix), radar bffc1d5. Three
live checks caught what fixtures could not: a wire DEF credited to a trade
as backfill (D3), the superflex overall board read as the one-QB board, and
a DEF and a K at the top of the chip list. Step 8, the review, found three
more (DECISIONS 69): the per-source range priced on the season scale inside
a prorated roster; an unranked incumbent setting the Test 1 floor at 300
(live on the mirror, where IDP namesakes overwrote offensive rows);
DEPTH_LOST judged against the post-fill wire. All fixed; 1,097 tests.

1. D1 -- position-aware `backfill()`, with fence 5.
2. `classify()` -- the slot classification per side, from `slot_moves` plus
   the wire. Fences 1-3 on fixtures.
3. Rank plumbing -- positional ECR per sleeper_id with panel size, from the
   FantasyPros feed already fetched.
4. `accepts()` -- Test 1 (positional upgrade, worst incumbent at his
   position), Test 2 (starters-market, backfill in), per-player tags
   (UPGRADE / FILLER / does not start), and the net-rank flag.
5. `verdict(mode="slots")` -- wired, reading `Deal.acceptance` that
   `price(ranks=)` attaches. SHIPPED WITH `MODE = "points"` STILL THE
   DEFAULT: the radar passes no rank panel to `price()` until step 7, and a
   slots default before that would reject every production package with
   "acceptance: not computed". The flip is one token and lands in step 7.
6. `tradeable()` -- chips with buyers.
7. `trade_radar` -- the Step 2 search and the per-row classification print.
8. DECISIONS cross-reference; code review.

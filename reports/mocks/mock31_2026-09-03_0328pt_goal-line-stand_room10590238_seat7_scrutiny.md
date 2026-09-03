# Scrutiny: Mock 31 -- Goal Line Stand (room 10590238) -- Thursday 2026-09-03 03:28 PT -- 10 teams, our seat 7

Captured 2026-09-03 03:38:53 PT. Times below are Pacific. 10 teams, our team id 7, draft slot 7. 150 picks in the trail, 67 bridge plan calls, 58 recs events in the room log.

## How the engine thinks, in plain English

1. **Projections first.** Every player has a season points projection for this league's
   scoring. On its own that number ranks quarterbacks at the top of every list, which is why it
   is never used on its own.
2. **Value over what is freely available.** The engine subtracts, per position, the points of the
   player you could get for nothing at that position (the replacement level, derived from how
   many starters this league's format demands). That difference is the value column, VORP. A
   player who can only start in the flex is valued against the flex replacement instead.
3. **Markets, not positions.** It only shops in slots you have not filled. Once your tight end
   slot is full there is no tight end market any more; remaining tight ends compete inside the
   flex against running backs and receivers.
4. **Survival: who will still be there at your next turn.** It simulates the picks between now
   and your next turn a thousand times. Each rival takes players near their average draft
   position, prefers positions they still need, and an autopick seat follows Yahoo's default
   list more tightly than a human would. The share of simulations in which a player is still
   on the board at your next pick is the survival percentage. It never ranks anyone by itself.
5. **Cost of waiting is what ranks.** For each market: the best value available now, minus the
   best value it expects to still be there at your next turn. That is the "waiting likely costs
   about N points" line. A big player with low survival makes waiting expensive; a deep position
   makes waiting nearly free. When every cost is near zero, the most valuable player who fills a
   slot wins the tie.
6. **Two picks at once.** It checks the pair: this pick plus the best partner it expects at the
   next turn, so it does not win this pick and lose the round.
7. **Hard rules override everything.** No second quarterback before round 10, no second tight
   end unless a top-6 one has fallen far past his ADP, kicker and defense only in the last two
   picks, and never leave a starting slot unfillable.
8. **Late rounds are insurance, not points.** Once the lineup is full, a bench player is priced
   by how many weeks you will need him (position injury rates plus the bye) times his weekly
   edge over the waiver wire; a handcuff to your own starter is worth more.
9. **The driver executes and verifies.** The page asks the engine at the turn, makes the pick
   through Yahoo's own action, and confirms it in Yahoo's data before recording it. If its
   readings disagree it does nothing and the queue it keeps catches the pick.

## The run in numbers

- Our picks: 15; by the driver 15 (action 15, click 0), by Yahoo from the queue / autopick 0.
- Action latency to store confirmation: median 477 ms, min 338, max 906.
- Heartbeats 9; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (1): dropped 1 feed entries numbered >= header pick 71.
- Away seats over the room (each change): {} -> {5,6} -> {1,5,6,9} -> {1,5,6,9,10} -> {1,2,5,6,9,10} -> {1,2,5,6,9} -> {1,2,5,6,9,10} -> {1,2,5,6,9}.
- Managers away at the end: 1 Michael, 2 jamesjones24, 3 Beau Spangler, 4 cherrio, 5 Greg, 6 Gilbert, 9 Rav.

## Our picks, one block each

### Pick 7 (round 1): Jaxon Smith-Njigba (WR)

- In plain English: Took Jaxon Smith-Njigba (WR) because waiting would likely cost about 8 points at WR, with a 60% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 445 ms, ranker engine, plan call 211, plan age 770 ms, at 03:28:31 PT.
- Engine's reason: waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 60% chance he's still there at your next pick · fills your open WR slot · TAKE-NOW ZONE: only 2 left before the WR value drops, and 6 teams 
- Top projection available: Josh Allen -> took it: False.
- Passed on: De'Von Achane (RB, s=0.621, e=68.5); Trey McBride (TE, s=0.977, e=77.3); Josh Allen (QB, s=0.869, e=44.9).
- Plan call 211 @pick 7: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6], state store with 6 drafted / 0 mine.
- Engine's first choice was **Jaxon Smith-Njigba** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaxon Smith-Njigba | WR | 89.4 | 0.60 | 0.60 | 81.8 | 89.4 | waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 60% chance |
| De'Von Achane | RB | 73.4 | 0.62 | 0.62 | 68.5 | 73.4 | waiting likely costs ~5 pts at RB (best option now 73, ~69 by your next turn) · 62% chance |
| Trey McBride | TE | 77.9 | 0.98 | 0.98 | 77.3 | 77.9 | safe to wait on TE · 98% chance he's still there at your next pick · fills your open TE sl |
| Josh Allen | QB | 47.0 | 0.87 | 0.87 | 44.9 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 87% chance |
| Amon-Ra St. Brown | WR | 81.8 | - | - | - | - | depth fallback (engine list exhausted) |
| James Cook III | RB | 63.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.9 | 2.1 | 7 |
| RB | 73.4 | 68.5 | 4.9 | 23 |
| WR | 89.4 | 81.8 | 7.6 | 25 |
| TE | 77.9 | 77.3 | 0.6 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 71.6 | 1.8 | 54 |

### Pick 14 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 29 points at RB, with a 10% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 499 ms, ranker engine, plan call 214, plan age 811 ms, at 03:28:50 PT.
- Engine's reason: waiting likely costs ~29 pts at RB (best option now 73, ~44 by your next turn) · 10% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 12 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Justin Jefferson (WR, s=0.062, e=44.6); Trey McBride (TE, s=0.513, e=57.8); Josh Allen (QB, s=0.464, e=38.4).
- Plan call 214 @pick 14: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 9], state store with 13 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.10 | 0.10 | 44.2 | 73.4 | waiting likely costs ~29 pts at RB (best option now 73, ~44 by your next turn) · 10% chanc |
| Justin Jefferson | WR | 53.9 | 0.06 | 0.06 | 44.6 | 53.9 | waiting likely costs ~9 pts at WR (best option now 54, ~45 by your next turn) · 6% chance  |
| Trey McBride | TE | 77.9 | 0.51 | 0.51 | 57.8 | 77.9 | waiting likely costs ~20 pts at TE (best option now 78, ~58 by your next turn) · 51% chanc |
| Josh Allen | QB | 47.0 | 0.46 | 0.46 | 38.4 | 47.0 | waiting likely costs ~9 pts at QB (best option now 47, ~38 by your next turn) · 46% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake London | WR | 51.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.4 | 8.6 | 9 |
| RB | 73.4 | 44.2 | 29.2 | 19 |
| WR | 53.9 | 44.6 | 9.3 | 24 |
| TE | 77.9 | 57.8 | 20.1 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 45.1 | 28.3 | 51 |

### Pick 27 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 17 points at TE, with a 68% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 570 ms, ranker engine, plan call 219, plan age 899 ms, at 03:29:36 PT.
- Engine's reason: waiting likely costs ~17 pts at TE (best option now 78, ~61 by your next turn) · 68% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 6 teams
- Top projection available: Josh Allen -> took it: False.
- Passed on: Rashee Rice (WR, s=0.594, e=29.9); Javonte Williams (RB, s=0.643, e=33.1); Josh Allen (QB, s=0.871, e=44.9).
- Plan call 219 @pick 27: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 9], state store with 26 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.69 | 0.69 | 60.8 | 77.9 | waiting likely costs ~17 pts at TE (best option now 78, ~61 by your next turn) · 68% chanc |
| Rashee Rice | WR | 34.1 | 0.59 | 0.59 | 29.9 | 34.1 | waiting likely costs ~4 pts at WR (best option now 34, ~30 by your next turn) · 59% chance |
| Javonte Williams | RB | 36.9 | 0.64 | 0.64 | 33.1 | 36.9 | waiting likely costs ~4 pts at RB (best option now 37, ~33 by your next turn) · 64% chance |
| Josh Allen | QB | 47.0 | 0.87 | 0.87 | 44.9 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 87% chance |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.9 | 2.1 | 10 |
| RB | 36.9 | 33.1 | 3.8 | 17 |
| WR | 34.1 | 29.9 | 4.2 | 22 |
| TE | 77.9 | 60.8 | 17.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 39.985766857976785 | 38.1 | 1.9 | 47 |

### Pick 34 (round 4): Josh Allen (QB)

- In plain English: Took Josh Allen (QB) because waiting would likely cost about 16 points at QB, with a 29% chance he would still be there next turn.
- Driver: via **action**, verified store, 373 ms, ranker engine, plan call 223, plan age 694 ms, at 03:30:12 PT.
- Engine's reason: waiting likely costs ~16 pts at QB (best option now 47, ~31 by your next turn) · 29% chance he's still there at your next pick · fills your open QB slot · 12 teams picking before you still need a QB · bargain: still here
- Top projection available: Josh Allen -> took it: True.
- Passed on: Garrett Wilson (WR, s=0.543, e=19.3); Travis Etienne Jr. (RB, s=0.421, e=22.7); Drake Maye (QB, s=None, e=None).
- Plan call 223 @pick 34: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 9], state store with 33 drafted / 3 mine.
- Engine's first choice was **Josh Allen** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Josh Allen | QB | 47.0 | 0.29 | 0.29 | 31.5 | 47.0 | waiting likely costs ~16 pts at QB (best option now 47, ~31 by your next turn) · 29% chanc |
| Garrett Wilson | WR | 23.9 | 0.54 | 0.54 | 19.3 | 23.9 | waiting likely costs ~5 pts at WR (best option now 24, ~19 by your next turn) · 54% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.42 | 0.42 | 22.7 | 26.3 | waiting likely costs ~4 pts at RB (best option now 26, ~23 by your next turn) · 42% chance |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 31.5 | 15.5 | 11 |
| RB | 26.3 | 22.7 | 3.6 | 17 |
| WR | 23.9 | 19.3 | 4.6 | 19 |
| TE | 23.8 | 22.5 | 1.3 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 22.8 | 3.6 | 43 |

### Pick 47 (round 5): Davante Adams (WR)

- In plain English: Took Davante Adams (WR) because waiting would likely cost about 3 points at WR, with a 76% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 477 ms, ranker engine, plan call 228, plan age 803 ms, at 03:31:01 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 76% chance he's still there at your next pick · fills your open WR slot · 6 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.979, e=9.3); Rhamondre Stevenson (RB, s=None, e=None); Quinshon Judkins (RB, s=None, e=None).
- Plan call 228 @pick 47: needs {'QB': 0, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 9], state store with 46 drafted / 4 mine.
- Engine's first choice was **Davante Adams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Davante Adams | WR | 13.1 | 0.76 | 0.76 | 10.4 | 13.1 | waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 76% chance |
| Jaylen Warren | RB | 9.3 | 0.98 | 0.98 | 9.3 | 9.3 | safe to wait on RB · 98% chance he's still there at your next pick · fills your open RB sl |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quinshon Judkins | RB | 3.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Terry McLaurin | WR | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.0 | 5.1 | 14 |
| RB | 9.3 | 9.3 | 0.0 | 16 |
| WR | 13.1 | 10.4 | 2.7 | 18 |
| TE | 21.1 | 21.0 | 0.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 42 |

### Pick 54 (round 6): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (82% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 458 ms, ranker engine, plan call 232, plan age 775 ms, at 03:31:37 PT.
- Engine's reason: safe to wait on RB · 82% chance he's still there at your next pick · fills your open RB slot · 6 teams picking before you still need a RB
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); Quinshon Judkins (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None).
- Plan call 232 @pick 54: needs {'QB': 0, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 9, 10], state store with 53 drafted / 5 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.82 | 0.82 | 8.8 | 9.3 | safe to wait on RB · 82% chance he's still there at your next pick · fills your open RB sl |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quinshon Judkins | RB | 3.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 15.9 | 2.1 | 14 |
| RB | 9.3 | 8.8 | 0.5 | 18 |
| WR | 0.0 | -0.4 | 0.4 | 18 |
| TE | 21.1 | 20.3 | 0.8 | 10 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.8 | 0.5 | 46 |

### Pick 67 (round 7): TreVeyon Henderson (RB)

- In plain English: Took TreVeyon Henderson (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 82% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 453 ms, ranker engine, plan call 239, plan age 776 ms, at 03:32:49 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) · 82% chance he's still there at your next pick · fills a FLEX slot ⛑ backs up Rhamondre Stevenson (13g)
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jameson Williams (WR, s=None, e=None); Christian Watson (WR, s=None, e=None); Mike Evans (WR, s=None, e=None).
- Plan call 239 @pick 67: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9], state store with 66 drafted / 6 mine.
- Engine's first choice was **TreVeyon Henderson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| TreVeyon Henderson | RB | 2.9 | 0.82 | 0.82 | 1.4 | 2.9 | waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) ·  |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.0 | 0.7 | 19 |
| RB | 2.9 | 1.4 | 1.5 | 23 |
| WR | 0.0 | -0.5 | 0.5 | 31 |
| TE | 21.1 | 18.6 | 2.5 | 17 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 2.872545684015563 | 1.4 | 1.5 | 71 |

### Pick 74 (round 8): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 88 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 394 ms, ranker engine, plan call 245, plan age 722 ms, at 03:33:49 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 88 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Christian Watson (WR, s=0.03, e=-8.2); Mike Evans (WR, s=None, e=None); Parker Washington (WR, s=None, e=None).
- Plan call 245 @pick 74: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9], state store with 73 drafted / 7 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.95 | 0.95 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs |
| Christian Watson | WR | -0.8 | 0.03 | 0.03 | -8.2 | -0.8 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.3/wk over the wire (Rashod Bate |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.9 | 1.8 | 19 |
| RB | -5.4 | -5.4 | 0.0 | 31 |
| WR | -0.8 | -8.2 | 7.4 | 41 |
| TE | 19.8 | 16.3 | 3.5 | 20 |
| K | 13.5 | 13.4 | 0.1 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 7 |

### Pick 87 (round 9): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 23 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 574 ms, ranker engine, plan call 249, plan age 907 ms, at 03:34:21 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Wan'Dale Robinson (WR, s=0.991, e=-10.6); Courtland Sutton (WR, s=None, e=None); Michael Pittman Jr. (WR, s=None, e=None).
- Plan call 249 @pick 87: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9], state store with 86 drafted / 8 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.97 | 0.97 | -6.7 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1 |
| Wan'Dale Robinson | WR | -10.6 | 0.99 | 0.99 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Wilson | WR | -14.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.1 | 0.7 | 18 |
| RB | -6.2 | -6.7 | 0.5 | 27 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 19.8 | 18.3 | 1.5 | 20 |
| K | 13.5 | 13.5 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 11 |

### Pick 94 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 536 ms, ranker engine, plan call 253, plan age 862 ms, at 03:34:58 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.735, e=10.8); Aaron Jones Sr. (RB, s=0.96, e=-26); Matthew Stafford (QB, s=None, e=None).
- Plan call 253 @pick 94: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9], state store with 93 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.96 | 0.96 | -10.7 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.73 | 0.73 | 10.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Aaron Jones Sr. | RB | -25.9 | 0.96 | 0.96 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.8 | 2.0 | 18 |
| RB | -25.9 | -26.0 | 0.1 | 25 |
| WR | -10.6 | -10.7 | 0.1 | 35 |
| TE | 19.8 | 9.7 | 10.1 | 19 |
| K | 13.5 | 13.5 | 0.0 | 14 |
| DEF | 18.0 | 18.0 | 0.0 | 11 |

### Pick 107 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 382 ms, ranker engine, plan call 258, plan age 709 ms, at 03:35:49 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Michael Pittman Jr. (WR, s=0.941, e=-13.8); Aaron Jones Sr. (RB, s=0.944, e=-26.1); Matthew Stafford (QB, s=None, e=None).
- Plan call 258 @pick 107: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9, 10], state store with 106 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.93 | 0.93 | 12.3 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Michael Pittman Jr. | WR | -13.3 | 0.94 | 0.94 | -13.8 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.94 | 0.94 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyler Murray | QB | -14.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.3 | 0.5 | 15 |
| RB | -25.9 | -26.1 | 0.2 | 22 |
| WR | -13.3 | -13.8 | 0.5 | 30 |
| TE | 10.9 | 10.5 | 0.4 | 17 |
| K | 13.5 | 13.3 | 0.2 | 15 |
| DEF | 18.0 | 16.9 | 1.1 | 14 |

### Pick 114 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 906 ms, ranker engine, plan call 261, plan age 1238 ms, at 03:36:26 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.931, e=-26.1); Jakobi Meyers (WR, s=None, e=None); Makai Lemon (WR, s=None, e=None).
- Plan call 261 @pick 114: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9, 10], state store with 113 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.91 | 0.91 | -14.0 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.93 | 0.93 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jayden Reed | WR | -28.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 12 |
| RB | -25.9 | -26.1 | 0.2 | 22 |
| WR | -13.3 | -14.0 | 0.7 | 28 |
| TE | 0.5 | 0.2 | 0.3 | 16 |
| K | 13.5 | 11.3 | 2.2 | 16 |
| DEF | 16.0 | 14.2 | 1.8 | 13 |

### Pick 127 (round 13): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +7.9 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 695 ms, ranker engine, plan call 266, plan age 1024 ms, at 03:37:14 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.957, e=-21.8); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 266 @pick 127: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9, 10], state store with 126 drafted / 12 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.96 | 0.96 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | 0.96 | 0.96 | -21.8 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +2. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Woody Marks | RB | -30.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 10 |
| RB | -25.9 | -26.1 | 0.2 | 20 |
| WR | -21.5 | -21.8 | 0.3 | 23 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 12.0 | 11.5 | 0.5 | 17 |
| DEF | 16.0 | 15.5 | 0.5 | 13 |

### Pick 134 (round 14): Seahawks (DEF)

- In plain English: Took Seattle Seahawks (DEF) because waiting would likely cost about 6 points at DEF, with a 9% chance he would still be there next turn. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 501 ms, ranker engine, plan call 269, plan age 826 ms, at 03:37:38 PT.
- Engine's reason: waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 9% chance he's still there at your next pick · fills your open DEF slot · TAKE-NOW ZONE: only 12 left before the DEF value drops, and 12 tea
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Cam Little (K, s=0.787, e=9.2); Cameron Dicker (K, s=None, e=None); Philadelphia Eagles (DEF, s=None, e=None).
- Plan call 269 @pick 134: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 5, 6, 9, 10], state store with 133 drafted / 13 mine.
- Engine's first choice was **Seattle Seahawks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Seattle Seahawks | DEF | 14.0 | 0.09 | 0.09 | 8.4 | 14.0 | waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 9% chance  |
| Cam Little | K | 9.0 | 0.79 | 0.79 | 9.2 | 10.5 | waiting likely costs ~1 pts at K (best option now 10, ~9 by your next turn) · 79% chance h |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Philadelphia Eagles | DEF | 10.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -17.2 | 0.7 | 9 |
| RB | -30.3 | -30.6 | 0.3 | 18 |
| WR | -21.5 | -22.0 | 0.5 | 23 |
| TE | -2.4 | -2.7 | 0.3 | 12 |
| K | 10.5 | 9.2 | 1.3 | 16 |
| DEF | 14.0 | 8.4 | 5.6 | 11 |

### Pick 147 (round 15): Cairo Santos (K)

- In plain English: Took Cairo Santos (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 338 ms, ranker engine, plan call 274, plan age 667 ms, at 03:38:22 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Jake Bates (K, s=None, e=None); Andy Borregales (K, s=None, e=None).
- Plan call 274 @pick 147: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 5, 6, 9], state store with 146 drafted / 14 mine.
- Engine's first choice was **Cairo Santos** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cairo Santos | K | 1.5 | - | - | - | - | fills your open K slot |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Harrison Mevis | K | -4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 10 | 15% | 0% |
| 30-50% | 8 | 43% | 38% |
| 50-70% | 22 | 61% | 23% |
| 70-90% | 30 | 82% | 63% |
| 90-100% | 60 | 96% | 82% |

130 predictions over 57 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    03:28:00  plan #208 for pick 1: Christian McCaffrey RB 49% “waiting likely costs ~19 pts at RB (best opt” · Ja'Marr Chase WR 52% “waiting likely costs ~11 pts at WR (best opt” · Trey McBride TE 99% “safe to wait on TE”
    03:28:01  driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    03:28:10  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    03:28:10  pick 2  Bijan Robinson (RB) taken by seat 2 in 0 s — a target is gone
    03:28:11  pick 3  Ja'Marr Chase (WR) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone (was 52% to survive)
    03:28:13  pick 4  Jonathan Taylor (RB) taken by seat 4 in 3 s — a target is gone
    03:28:14  plan #210 for pick 5: Christian McCaffrey RB 73% “waiting likely costs ~22 pts at RB (best opt” · Puka Nacua WR 82% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 100% “safe to wait on TE”
    03:28:14  pick 5  Puka Nacua (WR) taken by seat 5 in 0 s INSTANTLY (autopick) — a target is gone (was 82% to survive)
    03:28:17  pick 6  Christian McCaffrey (RB) taken by seat 6 in 4 s — a target is gone (was 73% to survive)
    03:28:30  plan #211 for pick 7: Jaxon Smith-Njigba WR 60% “waiting likely costs ~8 pts at WR (best opti” · De'Von Achane RB 62% “waiting likely costs ~5 pts at RB (best opti” · Trey McBride TE 98% “safe to wait on TE”
    03:28:30  ON THE CLOCK, pick 7 · plan #211 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    03:28:31  PICKED Jaxon Smith-Njigba (WR) via action, confirmed in 445 ms — chose Jaxon Smith-Njigba (WR): waiting would likely cost about 8 points at WR, 60% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:28:33  plan #212 for pick 8: Amon-Ra St. Brown WR 54% “waiting likely costs ~13 pts at WR (best opt” · De'Von Achane RB 57% “waiting likely costs ~6 pts at RB (best opti” · Trey McBride TE 96% “safe to wait on TE”
    03:28:39  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 8 s — a target is gone (was 54% to survive)
    03:28:39  pick 9  James Cook III (RB) taken by seat 9 in 0 s — a target is gone
    03:28:39  pick 10  Saquon Barkley (RB) taken by seat 10 in 0 s
    03:28:39  pick 11  CeeDee Lamb (WR) taken by seat 10 in 0 s — a target is gone
    03:28:40  pick 12  Kenneth Walker III (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    03:28:45  plan #213 for pick 13: De'Von Achane RB 90% “waiting likely costs ~1 pts at RB (best opti” · Justin Jefferson WR 89% “safe to wait on WR” · Trey McBride TE 98% “safe to wait on TE”
    03:28:48  pick 13  Chase Brown (RB) taken by seat 8 in 9 s — a target is gone
    03:28:49  plan #214 for pick 14: De'Von Achane RB 10% “waiting likely costs ~29 pts at RB (best opt” · Justin Jefferson WR 6% “waiting likely costs ~9 pts at WR (best opti” · Trey McBride TE 51% “waiting likely costs ~20 pts at TE (best opt
    03:28:49  ON THE CLOCK, pick 14 · plan #214 (0.0 s old) · lineup needs QB RBx2 WR TE FLEX K DEF
    03:28:50  PICKED De'Von Achane (RB) via action, confirmed in 499 ms — chose De'Von Achane (RB): waiting would likely cost about 29 points at RB, 10% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:28:52  pick 15  Justin Jefferson (WR) taken by seat 6 in 2 s — a target is gone (was 6% to survive)
    03:28:52  pick 16  Omarion Hampton (RB) taken by seat 5 in 0 s
    03:28:53  plan #215 for pick 17: Trey McBride TE 49% “waiting likely costs ~24 pts at TE (best opt” · Drake London WR 24% “waiting likely costs ~8 pts at WR (best opti” · Derrick Henry RB 10% “waiting likely costs ~11 pts at RB (best opt”
    03:28:55  pick 17  Derrick Henry (RB) taken by seat 4 in 3 s — a target is gone (was 10% to survive)
    03:28:58  pick 18  Brock Bowers (TE) taken by seat 3 in 3 s — a target is gone
    03:29:01  pick 19  Nico Collins (WR) taken by seat 2 in 3 s — a target is gone
    03:29:01  heartbeat sent (Yahoo told we are not idle)
    03:29:02  pick 20  Drake London (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone (was 24% to survive)
    03:29:03  pick 21  Ashton Jeanty (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    03:29:05  plan #216 for pick 22: Trey McBride TE 67% “waiting likely costs ~18 pts at TE (best opt” · A.J. Brown WR 41% “waiting likely costs ~3 pts at WR (best opti” · Kyren Williams RB 63% “waiting likely costs ~2 pts at RB (best opti”
    03:29:25  pick 22  George Pickens (WR) taken by seat 2 in 22 s — a target is gone
    03:29:27  pick 23  A.J. Brown (WR) taken by seat 3 in 2 s INSTANTLY (autopick) — a target is gone (was 41% to survive)
    03:29:29  plan #218 for pick 24: Trey McBride TE 71% “waiting likely costs ~16 pts at TE (best opt” · Chris Olave WR 69% “waiting likely costs ~2 pts at WR (best opti” · Kyren Williams RB 73% “waiting likely costs ~1 pts at RB (best opti”
    03:29:33  pick 24  Kyren Williams (RB) taken by seat 4 in 6 s — a target is gone (was 73% to survive)
    03:29:34  pick 25  Malik Nabers (WR) taken by seat 5 in 1 s INSTANTLY (autopick)
    03:29:35  pick 26  Chris Olave (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone (was 69% to survive)
    03:29:35  plan #219 for pick 27: Trey McBride TE 69% “waiting likely costs ~17 pts at TE (best opt” · Rashee Rice WR 59% “waiting likely costs ~4 pts at WR (best opti” · Javonte Williams RB 64% “waiting likely costs ~4 pts at RB (best opti”
    03:29:35  ON THE CLOCK, pick 27 · plan #219 (0.0 s old) · lineup needs QB RB WR TE FLEX K DEF
    03:29:36  PICKED Trey McBride (TE) via action, confirmed in 570 ms — chose Trey McBride (TE): waiting would likely cost about 17 points at TE, 69% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:29:39  plan #220 for pick 28: Rashee Rice WR 55% “waiting likely costs ~5 pts at WR (best opti” · Javonte Williams RB 63% “waiting likely costs ~4 pts at your FLEX spo” · Josh Allen QB 84% “waiting likely costs ~3 pts at QB (best opti”
    03:29:45  pick 28  Javonte Williams (RB) taken by seat 8 in 8 s — a target is gone (was 63% to survive)
    03:29:45  pick 29  DeVonta Smith (WR) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone
    03:29:51  plan #221 for pick 30: Rashee Rice WR 67% “waiting likely costs ~3 pts at WR (best opti” · Josh Allen QB 92% “waiting likely costs ~1 pts at QB (best opti” · Travis Etienne Jr. RB 87% “safe to wait on RB”
    03:30:00  pick 30  Breece Hall (RB) taken by seat 10 in 16 s
    03:30:01  heartbeat sent (Yahoo told we are not idle)
    03:30:03  plan #222 for pick 31: Rashee Rice WR 76% “waiting likely costs ~2 pts at WR (best opti” · Josh Allen QB 94% “safe to wait on QB” · Travis Etienne Jr. RB 88% “safe to wait on RB”
    03:30:06  pick 31  Rashee Rice (WR) taken by seat 10 in 6 s — a target is gone (was 76% to survive)
    03:30:07  pick 32  Jeremiyah Love (RB) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    03:30:11  pick 33  Zay Flowers (WR) taken by seat 8 in 4 s — a target is gone
    03:30:11  plan #223 for pick 34: Josh Allen QB 29% “waiting likely costs ~16 pts at QB (best opt” · Garrett Wilson WR 54% “waiting likely costs ~5 pts at WR (best opti” · Travis Etienne Jr. RB 42% “waiting likely costs ~4 pts at RB (best op
    03:30:11  ON THE CLOCK, pick 34 · plan #223 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    03:30:12  PICKED Josh Allen (QB) via action, confirmed in 373 ms — chose Josh Allen (QB): waiting would likely cost about 16 points at QB, 29% to still be there next turn
    03:30:14  pick 35  Tee Higgins (WR) taken by seat 6 in 2 s
    03:30:14  pick 36  Jaylen Waddle (WR) taken by seat 5 in 0 s
    03:30:15  plan #224 for pick 37: Garrett Wilson WR 46% “waiting likely costs ~6 pts at WR (best opti” · Travis Etienne Jr. RB 27% “waiting likely costs ~5 pts at your FLEX spo” · Cam Skattebo RB “depth fallback (engine list exhausted)”
    03:30:20  pick 37  Tetairoa McMillan (WR) taken by seat 4 in 6 s — a target is gone
    03:30:27  pick 38  Garrett Wilson (WR) taken by seat 3 in 7 s — a target is gone (was 46% to survive)
    03:30:27  plan #225 for pick 39: Travis Etienne Jr. RB 29% “waiting likely costs ~5 pts at your FLEX spo” · Davante Adams WR 88% “safe to wait on WR” · Cam Skattebo RB “depth fallback (engine list exhausted)”
    03:30:44  pick 39  D'Andre Swift (RB) taken by seat 2 in 17 s — a target is gone
    03:30:44  pick 40  Colston Loveland (TE) taken by seat 1 in 0 s INSTANTLY (autopick)
    03:30:45  pick 41  Ladd McConkey (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    03:30:52  plan #227 for pick 42: Travis Etienne Jr. RB 31% “waiting likely costs ~6 pts at your FLEX spo” · Davante Adams WR 88% “safe to wait on WR” · Cam Skattebo RB “depth fallback (engine list exhausted)”
    03:30:56  pick 42  DJ Moore (WR) taken by seat 2 in 11 s
    03:30:56  pick 43  Travis Etienne Jr. (RB) taken by seat 3 in 0 s — a target is gone (was 31% to survive)
    03:30:58  pick 44  Emeka Egbuka (WR) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone
    03:30:59  pick 45  Cam Skattebo (RB) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    03:31:00  pick 46  Tyler Warren (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    03:31:00  plan #228 for pick 47: Davante Adams WR 76% “waiting likely costs ~3 pts at WR (best opti” · Jaylen Warren RB 98% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    03:31:00  ON THE CLOCK, pick 47 · plan #228 (0.0 s old) · lineup needs RB WR FLEX K DEF
    03:31:01  PICKED Davante Adams (WR) via action, confirmed in 477 ms — chose Davante Adams (WR): waiting would likely cost about 3 points at WR, 76% to still be there next turn; top projection left was Drake Maye, passed on purpose
    03:31:03  heartbeat sent (Yahoo told we are not idle)
    03:31:04  plan #229 for pick 48: Jaylen Warren RB 97% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    03:31:09  pick 48  Lamar Jackson (QB) taken by seat 8 in 8 s
    03:31:09  pick 49  Luther Burden III (WR) taken by seat 9 in 0 s
    03:31:11  pick 50  Terry McLaurin (WR) taken by seat 10 in 2 s INSTANTLY (autopick) — a target is gone
    03:31:16  plan #230 for pick 51: Jaylen Warren RB 98% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    03:31:24  pick 51  David Montgomery (RB) taken by seat 10 in 13 s
    03:31:25  pick 52  Drake Maye (QB) taken by seat 9 in 1 s INSTANTLY (autopick)
    03:31:28  plan #231 for pick 53: Jaylen Warren RB 98% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    03:31:34  pick 53  Bucky Irving (RB) taken by seat 8 in 9 s — a target is gone
    03:31:36  plan #232 for pick 54: Jaylen Warren RB 82% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    03:31:36  ON THE CLOCK, pick 54 · plan #232 (0.0 s old) · lineup needs RB FLEX K DEF
    03:31:37  PICKED Jaylen Warren (RB) via action, confirmed in 458 ms — chose Jaylen Warren (RB): nothing urgent, the most valuable player who fills a slot (82% to survive, nobody better worth waiting for); top projection left was Jalen Hurts
    03:31:39  pick 55  Bhayshul Tuten (RB) taken by seat 6 in 2 s
    03:31:39  pick 56  Joe Burrow (QB) taken by seat 5 in 0 s
    03:31:39  plan #233 for pick 57: Rhamondre Stevenson RB 84% “safe to wait on your FLEX spot” · Quinshon Judkins RB “depth fallback (engine list exhausted)” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    03:31:50  pick 57  Quinshon Judkins (RB) taken by seat 4 in 12 s — a target is gone
    03:31:52  plan #234 for pick 58: Rhamondre Stevenson RB 88% “safe to wait on your FLEX spot” · TreVeyon Henderson RB “depth fallback (engine list exhausted)” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:31:54  pick 58  Jadarian Price (RB) taken by seat 3 in 4 s
    03:32:03  heartbeat sent (Yahoo told we are not idle)
    03:32:04  plan #235 for pick 59: Rhamondre Stevenson RB 94% “safe to wait on your FLEX spot” · TreVeyon Henderson RB “depth fallback (engine list exhausted)” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:32:24  pick 59  Jayden Daniels (QB) taken by seat 2 in 29 s
    03:32:24  pick 60  Rhamondre Stevenson (RB) taken by seat 1 in 0 s INSTANTLY (autopick) — a target is gone (was 94% to survive)
    03:32:24  pick 61  Jalen Hurts (QB) taken by seat 1 in 1 s INSTANTLY (autopick)
    03:32:26  pick 62  Tucker Kraft (TE) taken by seat 2 in 1 s INSTANTLY (autopick)
    03:32:29  plan #237 for pick 63: TreVeyon Henderson RB 84% “waiting likely costs ~1 pts at your FLEX spo” · Jameson Williams WR “depth fallback (engine list exhausted)” · Rome Odunze WR “depth fallback (engine list exhausted)”
    03:32:44  pick 63  Caleb Williams (QB) taken by seat 3 in 19 s
    03:32:47  pick 64  Rome Odunze (WR) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone
    03:32:47  pick 65  Sam LaPorta (TE) taken by seat 5 in 0 s INSTANTLY (autopick)
    03:32:48  pick 66  Justin Herbert (QB) taken by seat 6 in 1 s INSTANTLY (autopick)
    03:32:49  plan #239 for pick 67: TreVeyon Henderson RB 82% “waiting likely costs ~2 pts at your FLEX spo” · Jameson Williams WR “depth fallback (engine list exhausted)” · Christian Watson WR “depth fallback (engine list exhausted)”
    03:32:49  ON THE CLOCK, pick 67 · plan #239 (0.0 s old) · lineup needs FLEX K DEF
    03:32:49  PICKED TreVeyon Henderson (RB) via action, confirmed in 453 ms — chose TreVeyon Henderson (RB): waiting would likely cost about 2 points at your FLEX spot, 82% to still be there next turn; top projection left was Trevor Lawrence, 
    03:32:52  plan #240 for pick 68: Rico Dowdle RB 92% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 58% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    03:33:04  heartbeat sent (Yahoo told we are not idle)
    03:33:04  pick 68  Kyle Pitts Sr. (TE) taken by seat 8 in 15 s
    03:33:06  pick 69  Harold Fannin Jr. (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    03:33:17  plan #242 for pick 70: Rico Dowdle RB 93% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 58% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    03:33:29  pick 70  Dak Prescott (QB) taken by seat 10 in 24 s
    03:33:30  plan #243 for pick 71: Rico Dowdle RB 93% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 59% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    03:33:42  pick 71  Rico Dowdle (RB) taken by seat 10 in 13 s — a target is gone (was 93% to survive)
    03:33:42  bridge warning: dropped 1 feed entries numbered >= header pick 71
    03:33:45  pick 72  Jameson Williams (WR) taken by seat 9 in 3 s — a target is gone (was 59% to survive)
    03:33:47  pick 73  MarShawn Lloyd (RB) taken by seat 8 in 3 s
    03:33:48  plan #245 for pick 74: RJ Harvey RB 95% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 3% “bench insurance: covers 2 WR starters ~6.5 w” · Mike Evans WR “depth fallback (engine list exhausted)”
    03:33:48  ON THE CLOCK, pick 74 · plan #245 (0.0 s old) · lineup needs K DEF
    03:33:49  PICKED RJ Harvey (RB) via action, confirmed in 394 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +9.1 a week over the wire, about 88 points; top projection left was Trevor Law
    03:33:51  pick 75  Christian Watson (WR) taken by seat 6 in 2 s — a target is gone (was 3% to survive)
    03:33:51  pick 76  Parker Washington (WR) taken by seat 5 in 0 s — a target is gone
    03:33:52  plan #246 for pick 77: Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Mike Evans WR 8% “bench insurance: covers 2 WR starters ~6.5 w” · DK Metcalf WR “depth fallback (engine list exhausted)”
    03:33:58  pick 77  Mike Evans (WR) taken by seat 4 in 6 s — a target is gone (was 8% to survive)
    03:33:58  pick 78  Marvin Harrison Jr. (WR) taken by seat 3 in 0 s — a target is gone
    03:33:58  pick 79  Brian Thomas Jr. (WR) taken by seat 2 in 0 s
    03:33:58  pick 80  Carnell Tate (WR) taken by seat 1 in 0 s — a target is gone
    03:33:59  pick 81  Jonathon Brooks (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    03:34:00  pick 82  DK Metcalf (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    03:34:04  heartbeat sent (Yahoo told we are not idle)
    03:34:05  plan #247 for pick 83: Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Courtland Sutton WR “depth fallback (engine list exhausted)”
    03:34:11  pick 83  Blake Corum (RB) taken by seat 3 in 12 s
    03:34:17  pick 84  Trevor Lawrence (QB) taken by seat 4 in 6 s
    03:34:17  plan #248 for pick 85: Kenny Gainwell RB 100% “bench insurance: covers 3 RB starters behind” · Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Courtland Sutton WR “depth fallback (engine list exhausted)”
    03:34:20  pick 85  Tony Pollard (RB) taken by seat 5 in 3 s
    03:34:20  pick 86  Chris Godwin Jr. (WR) taken by seat 6 in 0 s — a target is gone
    03:34:20  plan #249 for pick 87: Kenny Gainwell RB 97% “bench insurance: covers 3 RB starters behind” · Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Courtland Sutton WR “depth fallback (engine list exhausted)”
    03:34:20  ON THE CLOCK, pick 87 · plan #249 (0.0 s old) · lineup needs K DEF
    03:34:21  PICKED Kenny Gainwell (RB) via action, confirmed in 574 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +9.1 a week over the wire, about 23 points; top projection left was 
    03:34:24  plan #250 for pick 88: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · J.K. Dobbins RB 35% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR “depth fallback (engine list exhausted)”
    03:34:33  pick 88  Courtland Sutton (WR) taken by seat 8 in 11 s — a target is gone
    03:34:33  pick 89  J.K. Dobbins (RB) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone (was 35% to survive)
    03:34:36  plan #251 for pick 90: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Aaron Jones Sr. RB 98% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted
    03:34:36  pick 90  Dallas Goedert (TE) taken by seat 10 in 3 s
    03:34:48  plan #252 for pick 91: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 94% “bench insurance: covers 1 QB starter ~3.6 wk” · Aaron Jones Sr. RB 98% “bench insurance: covers 3 RB start
    03:34:52  pick 91  Jordan Mason (RB) taken by seat 10 in 16 s
    03:34:52  pick 92  Michael Wilson (WR) taken by seat 9 in 0 s
    03:34:56  pick 93  Alec Pierce (WR) taken by seat 8 in 5 s
    03:34:57  plan #253 for pick 94: Wan'Dale Robinson WR 96% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 74% “bench insurance: covers 1 QB starter ~3.6 wk” · Aaron Jones Sr. RB 96% “bench insurance: covers 3 RB start
    03:34:57  ON THE CLOCK, pick 94 · plan #253 (0.0 s old) · lineup needs K DEF
    03:34:58  PICKED Wan'Dale Robinson (WR) via action, confirmed in 536 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    03:35:00  pick 95  George Kittle (TE) taken by seat 6 in 2 s
    03:35:00  pick 96  Josh Downs (WR) taken by seat 5 in 0 s
    03:35:01  plan #254 for pick 97: Patrick Mahomes II QB 77% “bench insurance: covers 1 QB starter ~3.6 wk” · Michael Pittman Jr. WR 91% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 94% “bench insurance: covers 3 RB sta
    03:35:05  heartbeat sent (Yahoo told we are not idle)
    03:35:22  pick 97  Quentin Johnston (WR) taken by seat 4 in 21 s
    03:35:25  pick 98  Brock Purdy (QB) taken by seat 3 in 4 s — a target is gone
    03:35:26  plan #256 for pick 99: Patrick Mahomes II QB 76% “bench insurance: covers 1 QB starter ~3.6 wk” · Michael Pittman Jr. WR 95% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 96% “bench insurance: covers 3 RB sta
    03:35:26  pick 99  Chuba Hubbard (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    03:35:30  pick 100  Stefon Diggs (WR) taken by seat 1 in 4 s
    03:35:30  pick 101  Bo Nix (QB) taken by seat 1 in 0 s — a target is gone
    03:35:30  pick 102  Jaxson Dart (QB) taken by seat 2 in 0 s — a target is gone
    03:35:39  plan #257 for pick 103: Patrick Mahomes II QB 88% “bench insurance: covers 1 QB starter ~3.6 wk” · Michael Pittman Jr. WR 96% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 97% “bench insurance: covers 3 RB st
    03:35:45  pick 103  KC Concepcion (WR) taken by seat 3 in 15 s
    03:35:47  pick 104  Josh Jacobs (RB) taken by seat 4 in 2 s INSTANTLY (autopick)
    03:35:47  pick 105  Dalton Kincaid (TE) taken by seat 5 in 0 s INSTANTLY (autopick)
    03:35:48  pick 106  Jacory Croskey-Merritt (RB) taken by seat 6 in 1 s INSTANTLY (autopick)
    03:35:48  plan #258 for pick 107: Patrick Mahomes II QB 93% “bench insurance: covers 1 QB starter ~3.6 wk” · Michael Pittman Jr. WR 94% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 94% “bench insurance: covers 3 RB st
    03:35:48  ON THE CLOCK, pick 107 · plan #258 (0.0 s old) · lineup needs K DEF
    03:35:49  PICKED Patrick Mahomes II (QB) via action, confirmed in 382 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    03:35:52  plan #259 for pick 108: Michael Pittman Jr. WR 93% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 95% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    03:36:01  pick 108  De'Zhaun Stribling (WR) taken by seat 8 in 12 s
    03:36:01  pick 109  Matthew Stafford (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    03:36:02  pick 110  Jordan Addison (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    03:36:03  pick 111  Kyler Murray (QB) taken by seat 10 in 1 s INSTANTLY (autopick)
    03:36:04  pick 112  Travis Kelce (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    03:36:04  plan #260 for pick 113: Michael Pittman Jr. WR 99% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 99% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    03:36:15  pick 113  Texans (DEF) taken by seat 8 in 11 s
    03:36:24  heartbeat sent (Yahoo told we are not idle)
    03:36:25  plan #261 for pick 114: Michael Pittman Jr. WR 91% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 93% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    03:36:25  ON THE CLOCK, pick 114 · plan #261 (0.0 s old) · lineup needs K DEF
    03:36:26  pick 115  Jared Goff (QB) taken by seat 6 in 0 s INSTANTLY (autopick)
    03:36:26  PICKED Michael Pittman Jr. (WR) via action, confirmed in 906 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.5 a week over the wire, about 2 points; top projection 
    03:36:28  pick 116  Jordan Love (QB) taken by seat 5 in 2 s
    03:36:29  plan #262 for pick 117: Aaron Jones Sr. RB 94% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 94% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    03:36:46  pick 117  Isaiah Likely (TE) taken by seat 4 in 17 s
    03:36:53  pick 118  Chris Rodriguez Jr. (RB) taken by seat 3 in 7 s
    03:36:53  pick 119  Mark Andrews (TE) taken by seat 2 in 0 s INSTANTLY (autopick)
    03:36:54  plan #264 for pick 120: Aaron Jones Sr. RB 96% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 96% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    03:36:54  pick 120  Juwan Johnson (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    03:36:56  pick 121  Jayden Reed (WR) taken by seat 1 in 2 s INSTANTLY (autopick) — a target is gone
    03:36:56  pick 122  Matthew Golden (WR) taken by seat 2 in 0 s INSTANTLY (autopick)
    03:37:06  plan #265 for pick 123: Aaron Jones Sr. RB 99% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 96% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    03:37:08  pick 123  Brandon Aubrey (K) taken by seat 3 in 12 s
    03:37:11  pick 124  Rashid Shaheed (WR) taken by seat 4 in 3 s
    03:37:12  pick 125  Makai Lemon (WR) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    03:37:13  pick 126  Kyle Monangai (RB) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    03:37:13  plan #266 for pick 127: Aaron Jones Sr. RB 96% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 96% “bench insurance: covers 2 WR starters behind” · Romeo Doubs WR “depth fallback (engine list exhausted)”
    03:37:13  ON THE CLOCK, pick 127 · plan #266 (0.0 s old) · lineup needs K DEF
    03:37:14  PICKED Aaron Jones Sr. (RB) via action, confirmed in 695 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +7.9 a week over the wire, about 2 points; top projection left was
    03:37:17  plan #267 for pick 128: Denver Broncos DEF 74% “safe to wait on DEF” · Cameron Dicker K 90% “safe to wait on K” · Seattle Seahawks DEF “depth fallback (engine list exhausted)”
    03:37:24  heartbeat sent (Yahoo told we are not idle)
    03:37:27  pick 128  Ka'imi Fairbairn (K) taken by seat 8 in 13 s — a target is gone
    03:37:27  pick 129  Rachaad White (RB) taken by seat 9 in 0 s INSTANTLY (autopick)
    03:37:28  pick 130  Jake Ferguson (TE) taken by seat 10 in 1 s INSTANTLY (autopick)
    03:37:29  pick 131  Rams (DEF) taken by seat 10 in 1 s INSTANTLY (autopick)
    03:37:29  plan #268 for pick 132: Denver Broncos DEF 70% “safe to wait on DEF” · Cam Little K 98% “safe to wait on K” · Seattle Seahawks DEF “depth fallback (engine list exhausted)”
    03:37:30  pick 132  Broncos (DEF) taken by seat 9 in 1 s INSTANTLY (autopick)
    03:37:37  pick 133  Baker Mayfield (QB) taken by seat 8 in 7 s
    03:37:38  plan #269 for pick 134: Seattle Seahawks DEF 9% “waiting likely costs ~6 pts at DEF (best opt” · Cam Little K 79% “waiting likely costs ~1 pts at K (best optio” · Cameron Dicker K “depth fallback (engine list exhausted)”
    03:37:38  ON THE CLOCK, pick 134 · plan #269 (0.0 s old) · lineup needs K DEF
    03:37:38  PICKED Seattle Seahawks (DEF) via action, confirmed in 501 ms — chose Seattle Seahawks (DEF): waiting would likely cost about 6 points at DEF, 9% to still be there next turn; top projection left was Daniel Jones, passed on purpose
    03:37:41  pick 135  Eagles (DEF) taken by seat 6 in 2 s
    03:37:41  pick 136  Cameron Dicker (K) taken by seat 5 in 0 s — a target is gone
    03:37:41  plan #270 for pick 137: Cam Little K 57% “waiting likely costs ~1 pts at K (best optio” · Jason Myers K “depth fallback (engine list exhausted)” · Eddy Pineiro K “depth fallback (engine list exhausted)”
    03:37:46  pick 137  Patriots (DEF) taken by seat 4 in 5 s
    03:37:53  pick 138  Jonah Coleman (RB) taken by seat 3 in 7 s
    03:37:54  plan #271 for pick 139: Cam Little K 64% “waiting likely costs ~1 pts at K (best optio” · Jason Myers K “depth fallback (engine list exhausted)” · Eddy Pineiro K “depth fallback (engine list exhausted)”
    03:37:54  pick 139  Jason Myers (K) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    03:37:55  pick 140  Vikings (DEF) taken by seat 1 in 1 s INSTANTLY (autopick)
    03:37:56  pick 141  Cam Little (K) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone (was 64% to survive)
    03:37:57  pick 142  Jaguars (DEF) taken by seat 2 in 1 s INSTANTLY (autopick)
    03:38:06  plan #272 for pick 143: Eddy Pineiro K 89% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    03:38:15  pick 143  Lions (DEF) taken by seat 3 in 18 s
    03:38:19  plan #273 for pick 144: Eddy Pineiro K 92% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    03:38:19  pick 144  Eddy Pineiro (K) taken by seat 4 in 4 s — a target is gone (was 92% to survive)
    03:38:21  pick 145  Steelers (DEF) taken by seat 5 in 2 s
    03:38:21  pick 146  Tyler Loop (K) taken by seat 6 in 0 s — a target is gone
    03:38:21  plan #274 for pick 147: Cairo Santos K “fills your open K slot” · Evan McPherson K “depth fallback (engine list exhausted)” · Jake Bates K “depth fallback (engine list exhausted)”
    03:38:21  ON THE CLOCK, pick 147 · plan #274 (0.0 s old) · lineup needs K
    03:38:22  PICKED Cairo Santos (K) via action, confirmed in 338 ms — chose Cairo Santos (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Daniel Jones, passed on purpose
    03:38:24  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    03:28:01 PT preflight: ok=true pick_path=action my_team=7 plan=plan 25 deep @pick 1 via store call#208
    03:28:01 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    03:28:01 PT NARR info driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    03:28:31 PT ON CLOCK -> {"drafted":"Jaxon Smith-Njigba","pos":"WR","vorp":89.4,"proj":231.5,"why":"waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 60% chance he's still there at your next pick · fills your op
    03:28:50 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~29 pts at RB (best option now 73, ~44 by your next turn) · 10% chance he's still there at your next pick · fills your open R
    03:29:01 PT heartbeat: setAwayStatus(false)
    03:29:01 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:29:36 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~17 pts at TE (best option now 78, ~61 by your next turn) · 68% chance he's still there at your next pick · fills your open TE
    03:30:01 PT heartbeat: setAwayStatus(false)
    03:30:01 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:30:12 PT ON CLOCK -> {"drafted":"Josh Allen","pos":"QB","vorp":47,"proj":320.6,"why":"waiting likely costs ~16 pts at QB (best option now 47, ~31 by your next turn) · 29% chance he's still there at your next pick · fills your open QB slo
    03:31:01 PT ON CLOCK -> {"drafted":"Davante Adams","pos":"WR","vorp":13.1,"proj":155.2,"why":"waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 76% chance he's still there at your next pick · fills your open WR
    03:31:03 PT heartbeat: setAwayStatus(false)
    03:31:03 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:31:37 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on RB · 82% chance he's still there at your next pick · fills your open RB slot · 6 teams picking before you still need a RB","s":0.82
    03:32:03 PT heartbeat: setAwayStatus(false)
    03:32:03 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:32:49 PT ON CLOCK -> {"drafted":"TreVeyon Henderson","pos":"RB","vorp":2.9,"proj":163.1,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) · 82% chance he's still there at your next pick · fill
    03:33:04 PT heartbeat: setAwayStatus(false)
    03:33:04 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:33:42 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 71
    03:33:49 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 88 pts","s":0.954,"sr":0.954,"e":-5.4,"top_proj_availabl
    03:34:04 PT heartbeat: setAwayStatus(false)
    03:34:04 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:34:21 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts","s":0.97,"sr":0
    03:34:58 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.962,"sr":0.962,"e":-10.7,"top_
    03:35:05 PT heartbeat: setAwayStatus(false)
    03:35:05 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:35:49 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.925,"sr":0.925,"e":12.3,"top_pr
    03:36:24 PT heartbeat: setAwayStatus(false)
    03:36:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:36:26 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    03:37:14 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.9
    03:37:24 PT heartbeat: setAwayStatus(false)
    03:37:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:37:39 PT ON CLOCK -> {"drafted":"Seattle Seahawks","pos":"DEF","vorp":14,"proj":131,"why":"waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 9% chance he's still there at your next pick · fills your open DEF
    03:38:22 PT ON CLOCK -> {"drafted":"Cairo Santos","pos":"K","vorp":1.5,"proj":138,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection":
    03:38:24 PT roster full
    03:38:24 PT NARR info roster full — driver done; posting the trail when the room finishes
    03:38:24 PT driver stop


# Scrutiny: Mock 40 -- Third and Long (room 10617211) -- Thursday 2026-09-03 16:12 PT -- 10 teams, our seat 7

Captured 2026-09-03 16:26:22 PT. Times below are Pacific. 10 teams, our team id 7, draft slot 7. 150 picks in the trail, 83 bridge plan calls, 64 recs events in the room log.

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
- Action latency to store confirmation: median 398 ms, min 272, max 566.
- Heartbeats 13; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (2): 1 drafted entries matched no board player: 144 Will Reichard; dropped 1 feed entries numbered >= header pick 26.
- Away seats over the room (each change): {} -> {1,2} -> {1,2,6} -> {1,2} -> {1,2,4,8} -> {1,2,4} -> {1,2,4,8} -> {1,2,4,8,9} -> {1,2,4,5,8,9}.
- Managers away at the end: 1 Jacob, 2 Steve, 4 Keith, 5 Eric, 8 Christian, 9 Andre.

## Our picks, one block each

### Pick 7 (round 1): Jonathan Taylor (RB)

- In plain English: Took Jonathan Taylor (RB) because waiting would likely cost about 15 points at RB, with a 59% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 527 ms, ranker engine, plan call 8, plan age 853 ms, at 16:13:29 PT.
- Engine's reason: waiting likely costs ~15 pts at RB (best option now 104, ~89 by your next turn) · 59% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 6 team
- Top projection available: Josh Allen -> took it: False.
- Passed on: Jaxon Smith-Njigba (WR, s=0.569, e=81.6); Trey McBride (TE, s=0.975, e=77.3); Josh Allen (QB, s=0.87, e=44.9).
- Plan call 8 @pick 7: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 6 drafted / 0 mine.
- Engine's first choice was **Jonathan Taylor** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jonathan Taylor | RB | 104.3 | 0.59 | 0.59 | 89.3 | 104.3 | waiting likely costs ~15 pts at RB (best option now 104, ~89 by your next turn) · 59% chan |
| Jaxon Smith-Njigba | WR | 89.4 | 0.57 | 0.57 | 81.6 | 89.4 | waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 57% chance |
| Trey McBride | TE | 77.9 | 0.97 | 0.97 | 77.3 | 77.9 | safe to wait on TE · 98% chance he's still there at your next pick · fills your open TE sl |
| Josh Allen | QB | 47.0 | 0.87 | 0.87 | 44.9 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 87% chance |
| Amon-Ra St. Brown | WR | 81.8 | - | - | - | - | depth fallback (engine list exhausted) |
| De'Von Achane | RB | 73.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.9 | 2.1 | 7 |
| RB | 104.3 | 89.3 | 15.0 | 23 |
| WR | 89.4 | 81.6 | 7.8 | 25 |
| TE | 77.9 | 77.3 | 0.6 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 104.29215856190694 | 91.1 | 13.2 | 54 |

### Pick 14 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 19 points at RB, with a 40% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 445 ms, ranker engine, plan call 13, plan age 764 ms, at 16:14:22 PT.
- Engine's reason: waiting likely costs ~19 pts at RB (best option now 73, ~54 by your next turn) · 40% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 12 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: CeeDee Lamb (WR, s=0.674, e=54.4); Trey McBride (TE, s=0.502, e=56.1); Josh Allen (QB, s=0.255, e=34.9).
- Plan call 13 @pick 14: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 13 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.40 | 0.40 | 54.1 | 73.4 | waiting likely costs ~19 pts at RB (best option now 73, ~54 by your next turn) · 40% chanc |
| CeeDee Lamb | WR | 56.8 | 0.67 | 0.67 | 54.4 | 56.8 | waiting likely costs ~2 pts at WR (best option now 57, ~54 by your next turn) · 67% chance |
| Trey McBride | TE | 77.9 | 0.50 | 0.50 | 56.1 | 77.9 | waiting likely costs ~22 pts at TE (best option now 78, ~56 by your next turn) · 50% chanc |
| Josh Allen | QB | 47.0 | 0.26 | 0.26 | 34.9 | 47.0 | waiting likely costs ~12 pts at QB (best option now 47, ~35 by your next turn) · 26% chanc |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Justin Jefferson | WR | 53.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 34.9 | 12.1 | 9 |
| RB | 73.4 | 54.1 | 19.3 | 18 |
| WR | 56.8 | 54.4 | 2.4 | 25 |
| TE | 77.9 | 56.1 | 21.8 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 55.0 | 18.4 | 51 |

### Pick 27 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 14 points at TE, with a 75% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 566 ms, ranker engine, plan call 22, plan age 888 ms, at 16:16:04 PT.
- Engine's reason: waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 75% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 6 teams
- Top projection available: Josh Allen -> took it: False.
- Passed on: Chris Olave (WR, s=0.579, e=36); Josh Allen (QB, s=0.831, e=44.2); Rashee Rice (WR, s=None, e=None).
- Plan call 22 @pick 27: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 26 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.75 | 0.75 | 64.1 | 77.9 | waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 75% chanc |
| Chris Olave | WR | 40.1 | 0.58 | 0.58 | 36.0 | 40.1 | waiting likely costs ~4 pts at WR (best option now 40, ~36 by your next turn) · 58% chance |
| Josh Allen | QB | 47.0 | 0.83 | 0.83 | 44.2 | 47.0 | waiting likely costs ~3 pts at QB (best option now 47, ~44 by your next turn) · 83% chance |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.2 | 2.8 | 10 |
| RB | 26.3 | 26.1 | 0.2 | 16 |
| WR | 40.1 | 36.0 | 4.1 | 23 |
| TE | 77.9 | 64.1 | 13.8 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 39.985766857976785 | 36.5 | 3.5 | 47 |

### Pick 34 (round 4): Rashee Rice (WR)

- In plain English: Took Rashee Rice (WR) because waiting would likely cost about 6 points at WR, with a 44% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 423 ms, ranker engine, plan call 27, plan age 749 ms, at 16:16:53 PT.
- Engine's reason: waiting likely costs ~6 pts at WR (best option now 34, ~28 by your next turn) · 44% chance he's still there at your next pick · fills your open WR slot · 10 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.358, e=22.1); Drake Maye (QB, s=0.501, e=24.4); Cam Skattebo (RB, s=None, e=None).
- Plan call 27 @pick 34: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 33 drafted / 3 mine.
- Engine's first choice was **Rashee Rice** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rashee Rice | WR | 34.1 | 0.44 | 0.44 | 27.8 | 34.1 | waiting likely costs ~6 pts at WR (best option now 34, ~28 by your next turn) · 44% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.36 | 0.36 | 22.1 | 26.3 | waiting likely costs ~4 pts at your FLEX spot (best option now 26, ~22 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.50 | 0.50 | 24.4 | 31.1 | waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 50% chance |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| DeVonta Smith | WR | 23.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 24.4 | 6.7 | 10 |
| RB | 26.3 | 21.4 | 4.9 | 18 |
| WR | 34.1 | 27.8 | 6.3 | 20 |
| TE | 23.8 | 22.4 | 1.4 | 6 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 22.1 | 4.3 | 44 |

### Pick 47 (round 5): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 4 points at WR, with a 72% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 469 ms, ranker engine, plan call 33, plan age 791 ms, at 16:17:47 PT.
- Engine's reason: waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 72% chance he's still there at your next pick · fills your open WR slot · 6 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.949, e=9.2); Jalen Hurts (QB, s=0.768, e=17.5); Trevor Lawrence (QB, s=None, e=None).
- Plan call 33 @pick 47: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 46 drafted / 4 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.72 | 0.72 | 20.2 | 23.9 | waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 72% chance |
| Jaylen Warren | RB | 9.3 | 0.95 | 0.95 | 9.2 | 9.3 | safe to wait on your FLEX spot · 95% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | 0.77 | 0.77 | 17.5 | 18.0 | safe to wait on QB · 77% chance he's still there at your next pick · fills your open QB sl |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.5 | 0.5 | 12 |
| RB | 9.3 | 9.2 | 0.1 | 16 |
| WR | 23.9 | 20.2 | 3.7 | 19 |
| TE | 23.8 | 23.0 | 0.8 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 44 |

### Pick 54 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB) because waiting would likely cost about 2 points at QB, with a 12% chance he would still be there next turn.
- Driver: via **action**, verified store, 342 ms, ranker engine, plan call 39, plan age 672 ms, at 16:18:51 PT.
- Engine's reason: waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 12% chance he's still there at your next pick · fills your open QB slot · 8 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.853, e=8.9); Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None).
- Plan call 39 @pick 54: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 8], state store with 53 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.12 | 0.12 | 15.8 | 18.0 | waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 12% chance |
| Jaylen Warren | RB | 9.3 | 0.85 | 0.85 | 8.9 | 9.3 | safe to wait on your FLEX spot · 85% chance he's still there at your next pick · fills a F |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Justin Herbert | QB | 7.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 15.8 | 2.2 | 13 |
| RB | 9.3 | 8.9 | 0.4 | 19 |
| WR | 0.0 | -0.2 | 0.2 | 17 |
| TE | 23.8 | 21.7 | 2.1 | 11 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.9 | 0.4 | 47 |

### Pick 67 (round 7): Rhamondre Stevenson (RB)

- In plain English: Took Rhamondre Stevenson (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 74% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 448 ms, ranker engine, plan call 45, plan age 768 ms, at 16:19:55 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 7, ~5 by your next turn) · 74% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: TreVeyon Henderson (RB, s=None, e=None); Rome Odunze (WR, s=None, e=None); Christian Watson (WR, s=None, e=None).
- Plan call 45 @pick 67: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 8], state store with 66 drafted / 6 mine.
- Engine's first choice was **Rhamondre Stevenson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rhamondre Stevenson | RB | 7.2 | 0.74 | 0.74 | 5.5 | 7.2 | waiting likely costs ~2 pts at your FLEX spot (best option now 7, ~5 by your next turn) ·  |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.1 | 0.6 | 19 |
| RB | 7.2 | 5.5 | 1.7 | 24 |
| WR | -0.7 | -1.0 | 0.3 | 30 |
| TE | 21.1 | 19.5 | 1.6 | 17 |
| K | 13.5 | 13.4 | 0.1 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 7.2333043142844815 | 5.5 | 1.7 | 71 |

### Pick 74 (round 8): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +1.9 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 18 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 379 ms, ranker engine, plan call 49, plan age 705 ms, at 16:20:31 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 18 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Mike Evans (WR, s=0.6, e=-5.3); Kenny Gainwell (RB, s=None, e=None); DK Metcalf (WR, s=None, e=None).
- Plan call 49 @pick 74: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 8], state store with 73 drafted / 7 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.94 | 0.94 | -5.5 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodri |
| Mike Evans | WR | -2.4 | 0.60 | 0.60 | -5.3 | -2.4 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.5/wk over the wire (Romeo Doubs |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.9 | 1.8 | 19 |
| RB | -5.4 | -5.5 | 0.1 | 33 |
| WR | -2.4 | -5.3 | 2.9 | 38 |
| TE | 19.8 | 16.2 | 3.6 | 21 |
| K | 13.5 | 12.9 | 0.6 | 11 |
| DEF | 18.0 | 17.8 | 0.2 | 7 |

### Pick 87 (round 9): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +1.0 points a week over the waiver wire (Romeo Doubs), worth about 7 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 398 ms, ranker engine, plan call 54, plan age 729 ms, at 16:21:23 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.982, e=-6.3); Rico Dowdle (RB, s=None, e=None); Courtland Sutton (WR, s=None, e=None).
- Plan call 54 @pick 87: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 8], state store with 86 drafted / 8 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.99 | 0.99 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs |
| Kenny Gainwell | RB | -6.2 | 0.98 | 0.98 | -6.3 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Rico Dowdle | RB | -11.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Wilson | WR | -14.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.8 | 0.9 | 18 |
| RB | -6.2 | -6.3 | 0.1 | 30 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 13.8 | 12.6 | 1.2 | 19 |
| K | 12.0 | 12.0 | 0.0 | 12 |
| DEF | 18.0 | 17.8 | 0.2 | 10 |

### Pick 94 (round 10): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Tyler Shough), worth about 8 points.
- Driver: via **action**, verified store, 389 ms, ranker engine, plan call 59, plan age 717 ms, at 16:22:11 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Kenny Gainwell (RB, s=0.877, e=-8.2); Courtland Sutton (WR, s=0.71, e=-11.8); Matthew Stafford (QB, s=None, e=None).
- Plan call 59 @pick 94: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 8, 9], state store with 93 drafted / 9 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.71 | 0.71 | 10.7 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough |
| Kenny Gainwell | RB | -6.2 | 0.88 | 0.88 | -8.2 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Courtland Sutton | WR | -11.1 | 0.71 | 0.71 | -11.8 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.7 | 2.1 | 17 |
| RB | -6.2 | -8.2 | 2.0 | 29 |
| WR | -11.1 | -11.8 | 0.7 | 36 |
| TE | 13.8 | 11.7 | 2.1 | 18 |
| K | 12.0 | 11.9 | 0.1 | 13 |
| DEF | 16.0 | 15.6 | 0.4 | 9 |

### Pick 107 (round 11): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +1.8 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 5 points. The top raw projection available was Matthew Stafford; the engine passed on him on purpose.
- Driver: via **action**, verified store, 352 ms, ranker engine, plan call 66, plan age 688 ms, at 16:23:23 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts
- Top projection available: Matthew Stafford -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.929, e=-11.3); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 66 @pick 107: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 8, 9], state store with 106 drafted / 10 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.96 | 0.96 | -6.9 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Courtland Sutton | WR | -11.1 | 0.93 | 0.93 | -11.3 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 6.6 | 4.0 | 2.6 | 14 |
| RB | -6.2 | -6.9 | 0.7 | 27 |
| WR | -11.1 | -11.3 | 0.2 | 29 |
| TE | 13.8 | 13.6 | 0.2 | 18 |
| K | 12.0 | 11.4 | 0.6 | 14 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 114 (round 12): Courtland Sutton (WR)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +1.0 points a week over the waiver wire (Deebo Samuel Sr.), worth about 1 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 370 ms, ranker engine, plan call 69, plan age 696 ms, at 16:23:44 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.946, e=-26.1); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 69 @pick 114: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 8, 9], state store with 113 drafted / 11 mine.
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.97 | 0.97 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Aaron Jones Sr. | RB | -25.9 | 0.95 | 0.95 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -11.9 | 0.1 | 13 |
| RB | -25.9 | -26.1 | 0.2 | 24 |
| WR | -11.1 | -11.2 | 0.1 | 28 |
| TE | 10.9 | 10.6 | 0.3 | 17 |
| K | 10.5 | 9.2 | 1.3 | 14 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 127 (round 13): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +0.7 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 0 points. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 451 ms, ranker engine, plan call 75, plan age 781 ms, at 16:24:48 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.7/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.975, e=-21.7); Deebo Samuel Sr. (WR, s=None, e=None); Kyle Monangai (RB, s=None, e=None).
- Plan call 75 @pick 127: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 8, 9], state store with 126 drafted / 12 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.98 | 0.98 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Jakobi Meyers | WR | -21.5 | 0.97 | 0.97 | -21.7 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyle Monangai | RB | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Woody Marks | RB | -30.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.7 | 0.2 | 10 |
| RB | -25.9 | -26.0 | 0.1 | 22 |
| WR | -21.5 | -21.7 | 0.2 | 23 |
| TE | 0.5 | 0.4 | 0.1 | 14 |
| K | 10.5 | 10.2 | 0.3 | 16 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 134 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (35% to survive, but nobody better was worth waiting for). The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 364 ms, ranker engine, plan call 79, plan age 697 ms, at 16:25:26 PT.
- Engine's reason: safe to wait on DEF · 35% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · two-pick plan: pair with the ~29-pt RB expected at your next turn
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Cam Little (K, s=0.584, e=8.2); Minnesota Vikings (DEF, s=None, e=None); Jason Myers (K, s=None, e=None).
- Plan call 79 @pick 134: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 8, 9], state store with 133 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.35 | 0.35 | 7.9 | 8.0 | safe to wait on DEF · 35% chance he's still there at your next pick · fills your open DEF  |
| Cam Little | K | 9.0 | 0.58 | 0.58 | 8.2 | 9.0 | safe to wait on K · 58% chance he's still there at your next pick · fills your open K slot |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -17.0 | 0.5 | 9 |
| RB | -30.3 | -30.4 | 0.1 | 20 |
| WR | -21.5 | -21.8 | 0.3 | 23 |
| TE | -2.4 | -2.6 | 0.2 | 13 |
| K | 9.0 | 8.2 | 0.8 | 15 |
| DEF | 8.0 | 7.9 | 0.1 | 9 |

### Pick 147 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 272 ms, ranker engine, plan call 83, plan age 627 ms, at 16:26:06 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 83 @pick 147: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 4, 5, 8, 9], state store with 146 drafted / 14 mine, warnings ['1 drafted entries matched no board player: 144 Will Reichard'].
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | - | - | - | - | fills your open K slot |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 6 | 22% | 50% |
| 30-50% | 11 | 39% | 27% |
| 50-70% | 30 | 59% | 33% |
| 70-90% | 43 | 81% | 72% |
| 90-100% | 66 | 96% | 82% |

156 predictions over 63 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T16:15:52   WARNING plan #21: dropped 1 feed entries numbered >= header pick 26
    2026-09-03T16:26:05   WARNING plan #83: 1 drafted entries matched no board player: 144 Will Reichard

## Narration (what the panel showed live, Pacific time)

    16:12:17  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 19 · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next) · 49% survives to our turn
  • Ja'Marr Chase WR · wait costs 11 · pick costs 24.2 · 52% survives to our tur
    16:12:18  driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    16:13:05  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    16:13:06  pick 2  Bijan Robinson (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    16:13:08  plan #6 for pick 3
  • Christian McCaffrey RB · wait costs 28 · pick costs 0, best pair 279.8 (159.6 now + ~120.2 WR next) · 54% survives to our turn
  • Ja'Marr Chase WR · wait costs 6 · pick costs 22.6 · 70% survives to our turn
    16:13:11  pick 3  Puka Nacua (WR) taken by seat 3 in 4 s — a target is gone
    16:13:19  heartbeat sent (Yahoo told we are not idle)
    16:13:20  pick 4  Ja'Marr Chase (WR) taken by seat 4 in 9 s — a target is gone (was 70% to survive)
    16:13:21  plan #7 for pick 5
  • Christian McCaffrey RB · wait costs 12 · pick costs 0, best pair 269.3 (159.6 now + ~109.7 RB next) · 78% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 2 · pick costs 21.9 · 79% survives to our
    16:13:26  pick 5  James Cook III (RB) taken by seat 5 in 6 s — a target is gone
    16:13:28  pick 6  Christian McCaffrey (RB) taken by seat 6 in 2 s INSTANTLY (autopick) — a target is gone (was 78% to survive)
    16:13:28  plan #8 for pick 7
  • Jonathan Taylor RB · wait costs 15 · pick costs 0, best pair 202 (109.7 now + ~92.3 WR next) · 59% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 8 · pick costs 7.2 · 57% survives to our turn
  
    16:13:28  ON THE CLOCK, pick 7 · plan #8 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    16:13:29  PICKED Jonathan Taylor (RB) via action, confirmed in 527 ms — chose Jonathan Taylor (RB): waiting would likely cost about 15 points at RB, 59% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    16:13:32  plan #9 for pick 8
  • Jaxon Smith-Njigba WR · wait costs 8 · pick costs 0, best pair 192.2 (100 now + ~92.2 WR next) · 59% survives to our turn
  • De'Von Achane RB · wait costs 8 · pick costs 21.2 · 52% survives to our turn
  • 
    16:13:50  pick 8  Jaxon Smith-Njigba (WR) taken by seat 8 in 21 s — a target is gone (was 59% to survive)
    16:13:54  pick 9  Saquon Barkley (RB) taken by seat 9 in 4 s
    16:13:57  plan #11 for pick 10
  • Amon-Ra St. Brown WR · wait costs 8 · pick costs 0, best pair 165.1 (92.4 now + ~72.7 RB next) · 69% survives to our turn
  • De'Von Achane RB · wait costs 6 · pick costs 2 · 64% survives to our turn
  • T
    16:14:01  pick 10  Amon-Ra St. Brown (WR) taken by seat 10 in 7 s — a target is gone (was 69% to survive)
    16:14:05  pick 11  Kenneth Walker III (RB) taken by seat 10 in 5 s
    16:14:09  pick 12  Chase Brown (RB) taken by seat 9 in 4 s — a target is gone
    16:14:09  plan #12 for pick 13
  • De'Von Achane RB · wait costs 2 · pick costs 0, best pair 146 (78.8 now + ~67.2 WR next) · 90% survives to our turn
  • CeeDee Lamb WR · safe to wait · pick costs 2.1 · 90% survives to our turn
  • Trey Mc
    16:14:20  pick 13  Omarion Hampton (RB) taken by seat 8 in 11 s
    16:14:20  heartbeat sent (Yahoo told we are not idle)
    16:14:21  plan #13 for pick 14
  • De'Von Achane RB · wait costs 19 · pick costs 0, best pair 143.9 (78.8 now + ~65.1 WR next) · 40% survives to our turn
  • CeeDee Lamb WR · wait costs 2 · pick costs 12 · 67% survives to our turn
  • Trey 
    16:14:21  ON THE CLOCK, pick 14 · plan #13 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    16:14:22  PICKED De'Von Achane (RB) via action, confirmed in 445 ms — chose De'Von Achane (RB): waiting would likely cost about 19 points at RB, 40% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    16:14:25  plan #14 for pick 15
  • CeeDee Lamb WR · wait costs 3 · pick costs 0, best pair 131.9 (67.4 now + ~64.5 WR next) · 64% survives to our turn
  • Trey McBride TE · wait costs 25 · pick costs 2.9 · 46% survives to our turn
  • Derri
    16:14:30  pick 15  CeeDee Lamb (WR) taken by seat 6 in 8 s — a target is gone (was 64% to survive)
    16:14:32  pick 16  Derrick Henry (RB) taken by seat 5 in 2 s INSTANTLY (autopick) — a target is gone (was 21% to survive)
    16:14:38  plan #15 for pick 17
  • Justin Jefferson WR · wait costs 5 · pick costs 0, best pair 123.9 (64.5 now + ~59.4 WR next) · 55% survives to our turn
  • Trey McBride TE · wait costs 21 · pick costs 0.3 · 53% survives to our turn
  • 
    16:14:41  pick 17  Justin Jefferson (WR) taken by seat 4 in 9 s — a target is gone (was 55% to survive)
    16:14:50  plan #16 for pick 18
  • Trey McBride TE · wait costs 18 · pick costs 0, best pair 117.5 (64.2 now + ~53.3 WR next) · 56% survives to our turn
  • Drake London WR · wait costs 8 · pick costs 2.6 · 21% survives to our turn
  • Josh
    16:15:00  pick 18  A.J. Brown (WR) taken by seat 3 in 19 s — a target is gone
    16:15:00  pick 19  Nico Collins (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    16:15:01  pick 20  Brock Bowers (TE) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    16:15:02  pick 21  Drake London (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone (was 21% to survive)
    16:15:02  plan #17 for pick 22
  • Trey McBride TE · wait costs 18 · pick costs 0, best pair 113.4 (64.2 now + ~49.2 WR next) · 67% survives to our turn
  • Chris Olave WR · wait costs 2 · pick costs 15.8 · 72% survives to our turn
  • Josh
    16:15:06  pick 22  Ashton Jeanty (RB) taken by seat 2 in 4 s — a target is gone
    16:15:15  plan #18 for pick 23
  • Trey McBride TE · wait costs 14 · pick costs 0, best pair 113.7 (64.2 now + ~49.5 WR next) · 74% survives to our turn
  • Chris Olave WR · wait costs 1 · pick costs 13.2 · 74% survives to our turn
  • Josh
    16:15:20  heartbeat sent (Yahoo told we are not idle)
    16:15:26  pick 23  Kyren Williams (RB) taken by seat 3 in 20 s — a target is gone
    16:15:27  plan #19 for pick 24
  • Trey McBride TE · wait costs 10 · pick costs 0, best pair 114.2 (64.2 now + ~50 WR next) · 82% survives to our turn
  • Chris Olave WR · safe to wait · pick costs 8.9 · 81% survives to our turn
  • Josh Al
    16:15:34  pick 24  Malik Nabers (WR) taken by seat 4 in 8 s
    16:15:39  plan #20 for pick 25
  • Trey McBride TE · wait costs 7 · pick costs 0, best pair 114.4 (64.2 now + ~50.2 WR next) · 88% survives to our turn
  • Chris Olave WR · safe to wait · pick costs 6.3 · 85% survives to our turn
  • Josh A
    16:15:50  pick 25  George Pickens (WR) taken by seat 5 in 16 s — a target is gone
    16:15:52  pick 26  Javonte Williams (RB) taken by seat 6 in 2 s INSTANTLY (autopick) — a target is gone
    16:15:52  plan #21 for pick 26
  • Trey McBride TE · wait costs 3 · pick costs 0, best pair 114.5 (64.2 now + ~50.3 WR next) · 95% survives to our turn
  • Chris Olave WR · safe to wait · pick costs 2.4 · 93% survives to our turn
  • Josh A
    16:15:52  bridge warning: dropped 1 feed entries numbered >= header pick 26
    16:16:03  plan #22 for pick 27
  • Trey McBride TE · wait costs 14 · pick costs 0, best pair 110.9 (64.2 now + ~46.7 WR next) · 75% survives to our turn
  • Chris Olave WR · wait costs 4 · pick costs 9.8 · 58% survives to our turn
  • Josh 
    16:16:03  ON THE CLOCK, pick 27 · plan #22 (0.0 s old) · lineup needs QB WRx2 TE FLEX K DEF
    16:16:04  PICKED Trey McBride (TE) via action, confirmed in 566 ms — chose Trey McBride (TE): waiting would likely cost about 14 points at TE, 75% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    16:16:06  plan #23 for pick 28
  • Chris Olave WR · wait costs 4 · pick costs 0, best pair 95.5 (50.7 now + ~44.8 WR next) · 57% survives to our turn
  • Josh Allen QB · wait costs 3 · pick costs 14.9 · 82% survives to our turn
  • Travis E
    16:16:21  pick 28  Jeremiyah Love (RB) taken by seat 8 in 18 s
    16:16:21  heartbeat sent (Yahoo told we are not idle)
    16:16:30  pick 29  Chris Olave (WR) taken by seat 9 in 8 s — a target is gone (was 57% to survive)
    16:16:31  plan #25 for pick 30
  • Rashee Rice WR · wait costs 3 · pick costs 0, best pair 79.3 (44.8 now + ~34.5 WR next) · 72% survives to our turn
  • Josh Allen QB · wait costs 2 · pick costs 3.2 · 89% survives to our turn
  • Travis Et
    16:16:37  pick 30  Josh Allen (QB) taken by seat 10 in 8 s — a target is gone (was 89% to survive)
    16:16:39  pick 31  Jaylen Waddle (WR) taken by seat 10 in 2 s INSTANTLY (autopick)
    16:16:43  pick 32  Ladd McConkey (WR) taken by seat 9 in 4 s
    16:16:43  plan #26 for pick 33
  • Rashee Rice WR · safe to wait · pick costs 0, best pair 79.3 (44.8 now + ~34.5 WR next) · 91% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · pick costs 3.8 · 96% survives to our turn
  • D
    16:16:51  pick 33  Colston Loveland (TE) taken by seat 8 in 8 s
    16:16:52  plan #27 for pick 34
  • Rashee Rice WR · wait costs 6 · pick costs 0, best pair 79.3 (44.8 now + ~34.5 WR next) · 44% survives to our turn
  • Travis Etienne Jr. RB · wait costs 4 · pick costs 9.1 · 36% survives to our turn
  • D
    16:16:52  ON THE CLOCK, pick 34 · plan #27 (0.0 s old) · lineup needs QB WRx2 FLEX K DEF
    16:16:53  PICKED Rashee Rice (WR) via action, confirmed in 423 ms — chose Rashee Rice (WR): waiting would likely cost about 6 points at WR, 44% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    16:16:56  plan #28 for pick 35
  • Garrett Wilson WR · wait costs 1 · pick costs 0, best pair 68.1 (34.5 now + ~33.6 WR next) · 55% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 2.9 · 32% survives to our turn
  
    16:17:06  pick 35  Luther Burden III (WR) taken by seat 6 in 13 s
    16:17:09  plan #29 for pick 36
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 68.1 (34.5 now + ~33.6 WR next) · 61% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 2.6 · 34% survives to our turn
  
    16:17:12  pick 36  Tetairoa McMillan (WR) taken by seat 5 in 6 s
    16:17:19  pick 37  D'Andre Swift (RB) taken by seat 4 in 7 s — a target is gone
    16:17:21  plan #30 for pick 38
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 68.1 (34.5 now + ~33.6 WR next) · 62% survives to our turn
  • Travis Etienne Jr. RB · wait costs 6 · pick costs 2.4 · 36% survives to our turn
  
    16:17:21  pick 38  DeVonta Smith (WR) taken by seat 3 in 2 s INSTANTLY (autopick) — a target is gone
    16:17:21  pick 39  Tee Higgins (WR) taken by seat 2 in 0 s INSTANTLY (autopick)
    16:17:25  pick 40  Breece Hall (RB) taken by seat 1 in 4 s
    16:17:25  pick 41  Zay Flowers (WR) taken by seat 1 in 0 s — a target is gone
    16:17:25  pick 42  Travis Etienne Jr. (RB) taken by seat 2 in 0 s — a target is gone (was 36% to survive)
    16:17:25  heartbeat sent (Yahoo told we are not idle)
    16:17:26  pick 43  Drake Maye (QB) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone (was 56% to survive)
    16:17:28  pick 44  Cam Skattebo (RB) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone
    16:17:30  pick 45  Emeka Egbuka (WR) taken by seat 5 in 2 s INSTANTLY (autopick)
    16:17:33  plan #31 for pick 46
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 58.2 (34.5 now + ~23.7 WR next) · 92% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 9.7 · 100% survives to our turn
  • Ja
    16:17:46  pick 46  Jayden Daniels (QB) taken by seat 6 in 16 s
    16:17:47  plan #33 for pick 47
  • Garrett Wilson WR · wait costs 4 · pick costs 0, best pair 58.2 (34.5 now + ~23.7 WR next) · 72% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 12.6 · 95% survives to our turn
  • Ja
    16:17:47  ON THE CLOCK, pick 47 · plan #33 (0.0 s old) · lineup needs QB WR FLEX K DEF
    16:17:47  PICKED Garrett Wilson (WR) via action, confirmed in 469 ms — chose Garrett Wilson (WR): waiting would likely cost about 4 points at WR, 72% to still be there next turn
  • top projection left was Jalen Hurts, passed on purpose
    16:17:50  pick 48  Lamar Jackson (QB) taken by seat 8 in 2 s
    16:17:50  plan #34 for pick 49
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 43.1 (5.2 now + ~37.9 WR next) · 85% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 15.9 · 96% survives to our turn
  • Trevor
    16:18:16  pick 49  Parker Washington (WR) taken by seat 9 in 26 s
    16:18:26  heartbeat sent (Yahoo told we are not idle)
    16:18:28  plan #37 for pick 50
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 43.1 (5.2 now + ~37.9 WR next) · 88% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 16 · 98% survives to our turn
  • Trevor L
    16:18:37  pick 50  Terry McLaurin (WR) taken by seat 10 in 22 s
    16:18:40  plan #38 for pick 51
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 43.1 (5.2 now + ~37.9 WR next) · 89% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 15.7 · 99% survives to our turn
  • Trevor
    16:18:41  pick 51  Bucky Irving (RB) taken by seat 10 in 4 s
    16:18:49  pick 52  Davante Adams (WR) taken by seat 9 in 8 s — a target is gone
    16:18:49  pick 53  DJ Moore (WR) taken by seat 8 in 0 s INSTANTLY (autopick)
    16:18:50  plan #39 for pick 54
  • Jalen Hurts QB · wait costs 2 · pick costs 0, best pair 42.8 (5.2 now + ~37.6 WR next) · 12% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 20.5 · 85% survives to our turn
  • Trevor
    16:18:50  ON THE CLOCK, pick 54 · plan #39 (0.0 s old) · lineup needs QB FLEX K DEF
    16:18:51  PICKED Jalen Hurts (QB) via action, confirmed in 342 ms — chose Jalen Hurts (QB): waiting would likely cost about 2 points at QB, 12% to still be there next turn
    16:18:53  pick 55  Tyler Warren (TE) taken by seat 6 in 2 s
    16:18:54  plan #40 for pick 56
  • Jaylen Warren RB · safe to wait · 82% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • Quinshon Judkins RB · depth fallback, engine list done
    16:19:08  pick 56  Jameson Williams (WR) taken by seat 5 in 15 s — a target is gone
    16:19:09  pick 57  Joe Burrow (QB) taken by seat 4 in 1 s INSTANTLY (autopick)
    16:19:16  pick 58  David Montgomery (RB) taken by seat 3 in 7 s
    16:19:17  pick 59  Tucker Kraft (TE) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:19:19  pick 60  Bhayshul Tuten (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:19:20  plan #42 for pick 61
  • Jaylen Warren RB · safe to wait · 90% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • Quinshon Judkins RB · depth fallback, engine list done
    16:19:20  pick 61  Caleb Williams (QB) taken by seat 1 in 2 s INSTANTLY (autopick)
    16:19:20  pick 62  Justin Herbert (QB) taken by seat 2 in 0 s INSTANTLY (autopick)
    16:19:23  pick 63  Jadarian Price (RB) taken by seat 3 in 2 s
    16:19:23  pick 64  Sam LaPorta (TE) taken by seat 4 in 0 s
    16:19:26  heartbeat sent (Yahoo told we are not idle)
    16:19:32  plan #43 for pick 65
  • Jaylen Warren RB · safe to wait · 93% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • Quinshon Judkins RB · depth fallback, engine list done
    16:19:47  pick 65  Quinshon Judkins (RB) taken by seat 5 in 24 s — a target is gone
    16:19:53  pick 66  Jaylen Warren (RB) taken by seat 6 in 6 s — a target is gone (was 93% to survive)
    16:19:54  plan #45 for pick 67
  • Rhamondre Stevenson RB · wait costs 2 · 74% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
  • Rome Odunze WR · depth fallback, engine list done
    16:19:54  ON THE CLOCK, pick 67 · plan #45 (0.0 s old) · lineup needs FLEX K DEF
    16:19:55  PICKED Rhamondre Stevenson (RB) via action, confirmed in 448 ms — chose Rhamondre Stevenson (RB): waiting would likely cost about 2 points at your FLEX spot, 74% to still be there next turn
  • top projection left was Trevor Lawre
    16:19:57  pick 68  TreVeyon Henderson (RB) taken by seat 8 in 2 s — a target is gone
    16:19:57  plan #46 for pick 69
  • RJ Harvey RB · insurance worth ~18 · 99% survives to our turn
  • Rome Odunze WR · insurance worth ~10 · 80% survives to our turn
  • Christian Watson WR · depth fallback, engine list done
    16:20:17  pick 69  Kyle Pitts Sr. (TE) taken by seat 9 in 20 s
    16:20:20  pick 70  Rome Odunze (WR) taken by seat 10 in 3 s — a target is gone (was 80% to survive)
    16:20:22  plan #48 for pick 71
  • RJ Harvey RB · insurance worth ~18 · 99% survives to our turn
  • Christian Watson WR · insurance worth ~10 · 84% survives to our turn
  • Mike Evans WR · depth fallback, engine list done
    16:20:27  pick 71  Dak Prescott (QB) taken by seat 10 in 7 s
    16:20:27  heartbeat sent (Yahoo told we are not idle)
    16:20:28  pick 72  Chris Godwin Jr. (WR) taken by seat 9 in 2 s INSTANTLY (autopick)
    16:20:29  pick 73  Christian Watson (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 84% to survive)
    16:20:30  plan #49 for pick 74
  • RJ Harvey RB · insurance worth ~18 · 94% survives to our turn
  • Mike Evans WR · insurance worth ~10 · 60% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:20:30  ON THE CLOCK, pick 74 · plan #49 (0.0 s old) · lineup needs K DEF
    16:20:31  PICKED RJ Harvey (RB) via action, confirmed in 379 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +1.9 a week over the wire, about 18 points
  • top projection left was Trevor 
    16:20:33  pick 75  Brandon Aubrey (K) taken by seat 6 in 2 s
    16:20:34  plan #50 for pick 76
  • Mike Evans WR · insurance worth ~10 · 66% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • DK Metcalf WR · depth fallback, engine list done
    16:20:39  pick 76  Mike Evans (WR) taken by seat 5 in 6 s — a target is gone (was 66% to survive)
    16:20:40  pick 77  Marvin Harrison Jr. (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    16:20:46  plan #51 for pick 78
  • DK Metcalf WR · insurance worth ~7 · 52% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • Carnell Tate WR · depth fallback, engine list done
    16:20:54  pick 78  MarShawn Lloyd (RB) taken by seat 3 in 14 s
    16:20:55  pick 79  Brian Thomas Jr. (WR) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:20:56  pick 80  Carnell Tate (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    16:20:57  pick 81  Jonathon Brooks (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:20:58  pick 82  DK Metcalf (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 52% to survive)
    16:20:59  plan #52 for pick 83
  • Wan'Dale Robinson WR · insurance worth ~7 · 100% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Rico Dowdle RB · depth fallback, engine list done
    16:21:08  pick 83  George Kittle (TE) taken by seat 3 in 10 s
    16:21:09  pick 84  Harold Fannin Jr. (TE) taken by seat 4 in 1 s INSTANTLY (autopick)
    16:21:11  plan #53 for pick 85
  • Wan'Dale Robinson WR · insurance worth ~7 · 100% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 100% survives to our turn
  • Rico Dowdle RB · depth fallback, engine list done
    16:21:16  pick 85  Jaxson Dart (QB) taken by seat 5 in 7 s
    16:21:22  pick 86  Rams (DEF) taken by seat 6 in 6 s
    16:21:23  plan #54 for pick 87
  • Wan'Dale Robinson WR · insurance worth ~7 · 99% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • Rico Dowdle RB · depth fallback, engine list done
    16:21:23  ON THE CLOCK, pick 87 · plan #54 (0.0 s old) · lineup needs K DEF
    16:21:23  PICKED Wan'Dale Robinson (WR) via action, confirmed in 398 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +1.0 a week over the wire, about 7 points
  • top projection l
    16:21:26  pick 88  Trevor Lawrence (QB) taken by seat 8 in 2 s
    16:21:26  plan #55 for pick 89
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 92% survives to our turn
  • Rico Dowdle RB · depth fallback, engine list done
    16:21:28  heartbeat sent (Yahoo told we are not idle)
    16:21:54  pick 89  De'Zhaun Stribling (WR) taken by seat 9 in 28 s
    16:21:56  pick 90  Texans (DEF) taken by seat 10 in 2 s INSTANTLY (autopick)
    16:22:04  plan #58 for pick 91
  • Patrick Mahomes II QB · insurance worth ~8 · 78% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 96% survives to ou
    16:22:08  pick 91  Dalton Kincaid (TE) taken by seat 10 in 12 s
    16:22:08  pick 92  Rico Dowdle (RB) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone
    16:22:09  pick 93  Tony Pollard (RB) taken by seat 8 in 1 s INSTANTLY (autopick)
    16:22:10  plan #59 for pick 94
  • Patrick Mahomes II QB · insurance worth ~8 · 71% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 88% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 71% survives to ou
    16:22:10  ON THE CLOCK, pick 94 · plan #59 (0.0 s old) · lineup needs K DEF
    16:22:11  PICKED Patrick Mahomes II (QB) via action, confirmed in 389 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    16:22:14  plan #60 for pick 95
  • Kenny Gainwell RB · insurance worth ~5 · 88% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 70% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:22:23  pick 95  Alec Pierce (WR) taken by seat 6 in 12 s — a target is gone
    16:22:24  pick 96  Michael Wilson (WR) taken by seat 5 in 2 s INSTANTLY (autopick) — a target is gone
    16:22:25  pick 97  J.K. Dobbins (RB) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    16:22:26  plan #61 for pick 98
  • Kenny Gainwell RB · insurance worth ~5 · 90% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 72% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:22:29  heartbeat sent (Yahoo told we are not idle)
    16:22:45  pick 98  Stefon Diggs (WR) taken by seat 3 in 20 s — a target is gone
    16:22:46  pick 99  Chuba Hubbard (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:22:47  pick 100  Josh Downs (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    16:22:48  pick 101  Brock Purdy (QB) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:22:49  pick 102  Bo Nix (QB) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:22:50  plan #63 for pick 103
  • Kenny Gainwell RB · insurance worth ~5 · 97% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 92% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:11  pick 103  Broncos (DEF) taken by seat 3 in 22 s
    16:23:12  pick 104  Quentin Johnston (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    16:23:13  pick 105  Makai Lemon (WR) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    16:23:15  plan #65 for pick 106
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 98% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:21  pick 106  Jayden Reed (WR) taken by seat 6 in 8 s — a target is gone
    16:23:22  plan #66 for pick 107
  • Kenny Gainwell RB · insurance worth ~5 · 96% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 93% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:22  ON THE CLOCK, pick 107 · plan #66 (0.0 s old) · lineup needs K DEF
    16:23:23  PICKED Kenny Gainwell (RB) via action, confirmed in 352 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +1.8 a week over the wire, about 5 points
  • top projection left wa
    16:23:25  pick 108  Jordan Addison (WR) taken by seat 8 in 2 s — a target is gone
    16:23:25  pick 109  Matthew Stafford (QB) taken by seat 9 in 0 s
    16:23:25  plan #67 for pick 110
  • Courtland Sutton WR · insurance worth ~1 · 96% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:28  pick 110  Ka'imi Fairbairn (K) taken by seat 10 in 4 s
    16:23:29  heartbeat sent (Yahoo told we are not idle)
    16:23:38  plan #68 for pick 111
  • Courtland Sutton WR · insurance worth ~1 · 98% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:40  pick 111  Blake Corum (RB) taken by seat 10 in 12 s
    16:23:41  pick 112  Jacory Croskey-Merritt (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    16:23:42  pick 113  Dallas Goedert (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    16:23:43  plan #69 for pick 114
  • Courtland Sutton WR · insurance worth ~1 · 97% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 95% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:23:43  ON THE CLOCK, pick 114 · plan #69 (0.0 s old) · lineup needs K DEF
    16:23:44  PICKED Courtland Sutton (WR) via action, confirmed in 370 ms — lineup full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +1.0 a week over the wire, about 1 points
  • top projection lef
    16:23:47  plan #70 for pick 115
  • Aaron Jones Sr. RB · insurance worth ~0 · 93% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:23:52  pick 115  Jordan Mason (RB) taken by seat 6 in 8 s
    16:23:52  pick 116  Travis Kelce (TE) taken by seat 5 in 0 s INSTANTLY (autopick)
    16:23:53  pick 117  Kyler Murray (QB) taken by seat 4 in 1 s INSTANTLY (autopick)
    16:23:59  plan #71 for pick 118
  • Aaron Jones Sr. RB · insurance worth ~0 · 97% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 96% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:24:19  pick 118  Baker Mayfield (QB) taken by seat 3 in 26 s
    16:24:20  pick 119  Isaiah Likely (TE) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:24:21  pick 120  Mark Andrews (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:24:21  pick 121  KC Concepcion (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    16:24:22  pick 122  Matthew Golden (WR) taken by seat 2 in 1 s INSTANTLY (autopick)
    16:24:24  plan #73 for pick 123
  • Aaron Jones Sr. RB · insurance worth ~0 · 99% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 97% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:24:30  heartbeat sent (Yahoo told we are not idle)
    16:24:43  pick 123  Romeo Doubs (WR) taken by seat 3 in 20 s — a target is gone
    16:24:43  pick 124  Michael Pittman Jr. (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 97% to survive)
    16:24:44  pick 125  Josh Jacobs (RB) taken by seat 5 in 1 s INSTANTLY (autopick)
    16:24:46  pick 126  Jared Goff (QB) taken by seat 6 in 2 s INSTANTLY (autopick)
    16:24:47  plan #75 for pick 127
  • Aaron Jones Sr. RB · insurance worth ~0 · 98% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 98% survives to our turn
  • Deebo Samuel Sr. WR · depth fallback, engine list done
    16:24:47  ON THE CLOCK, pick 127 · plan #75 (0.0 s old) · lineup needs K DEF
    16:24:48  PICKED Aaron Jones Sr. (RB) via action, confirmed in 451 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +0.7 a week over the wire, about 0 points
  • top projection left 
    16:24:50  pick 128  Kyle Monangai (RB) taken by seat 8 in 2 s — a target is gone
    16:24:50  pick 129  Jordan Love (QB) taken by seat 9 in 0 s
    16:24:50  plan #76 for pick 130
  • Seattle Seahawks DEF · safe to wait · pick costs 0, best pair 41.5 (12 now + ~29.5 RB next) · 100% survives to our turn
  • Cam Little K · safe to wait · pick costs 9 · 87% survives to our turn
  • Camero
    16:24:56  pick 130  Jake Ferguson (TE) taken by seat 10 in 7 s
    16:25:02  plan #77 for pick 131
  • Seattle Seahawks DEF · safe to wait · pick costs 0, best pair 41.6 (12 now + ~29.6 RB next) · 100% survives to our turn
  • Cam Little K · safe to wait · pick costs 9 · 89% survives to our turn
  • Camero
    16:25:23  pick 131  Seahawks (DEF) taken by seat 10 in 26 s
    16:25:23  pick 132  Eagles (DEF) taken by seat 9 in 0 s INSTANTLY (autopick)
    16:25:24  pick 133  Cameron Dicker (K) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    16:25:25  plan #79 for pick 134
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 33.5 (4 now + ~29.5 RB next) · 35% survives to our turn
  • Cam Little K · safe to wait · pick costs 1 · 58% survives to our turn
  • Minne
    16:25:25  ON THE CLOCK, pick 134 · plan #79 (0.0 s old) · lineup needs K DEF
    16:25:26  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 364 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (35% to survive, nobody better worth waiting for)
  • top projection lef
    16:25:29  plan #80 for pick 135
  • Cam Little K · safe to wait · 60% survives to our turn
  • Jason Myers K · depth fallback, engine list done
  • Eddy Pineiro K · depth fallback, engine list done
    16:25:31  heartbeat sent (Yahoo told we are not idle)
    16:25:32  pick 135  Rachaad White (RB) taken by seat 6 in 7 s
    16:25:33  pick 136  Jason Myers (K) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    16:25:34  pick 137  Vikings (DEF) taken by seat 4 in 1 s INSTANTLY (autopick)
    16:25:38  pick 138  Juwan Johnson (TE) taken by seat 3 in 4 s
    16:25:39  pick 139  Cam Little (K) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 60% to survive)
    16:25:40  pick 140  Jaguars (DEF) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:25:40  plan #81 for pick 141
  • Eddy Pineiro K · safe to wait · 81% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    16:25:43  pick 141  Tyler Loop (K) taken by seat 1 in 3 s — a target is gone
    16:25:43  pick 142  Patriots (DEF) taken by seat 2 in 0 s
    16:25:52  plan #82 for pick 143
  • Eddy Pineiro K · safe to wait · 85% survives to our turn
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    16:26:01  pick 143  Harrison Mevis (K) taken by seat 3 in 18 s — a target is gone
    16:26:01  pick 144  Will Reichard (K) taken by seat 4 in 0 s INSTANTLY (autopick)
    16:26:02  pick 145  Ravens (DEF) taken by seat 5 in 1 s INSTANTLY (autopick)
    16:26:05  pick 146  Jakobi Meyers (WR) taken by seat 6 in 3 s
    16:26:05  plan #83 for pick 147
  • Eddy Pineiro K
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    16:26:05  bridge warning: 1 drafted entries matched no board player: 144 Will Reichard
    16:26:05  ON THE CLOCK, pick 147 · plan #83 (0.0 s old) · lineup needs K
    16:26:06  PICKED Eddy Pineiro (K) via action, confirmed in 272 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Daniel Jones, passed on purpose
    16:26:08  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    16:12:18 PT preflight: ok=true pick_path=action my_team=7 plan=plan 25 deep @pick 1 via store call#1
    16:12:18 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    16:12:18 PT NARR info driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    16:13:19 PT heartbeat: setAwayStatus(false)
    16:13:19 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:13:29 PT ON CLOCK -> {"drafted":"Jonathan Taylor","pos":"RB","vorp":104.3,"proj":264.5,"why":"waiting likely costs ~15 pts at RB (best option now 104, ~89 by your next turn) · 59% chance he's still there at your next pick · fills your op
    16:14:20 PT heartbeat: setAwayStatus(false)
    16:14:20 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:14:22 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~19 pts at RB (best option now 73, ~54 by your next turn) · 40% chance he's still there at your next pick · fills your open R
    16:15:20 PT heartbeat: setAwayStatus(false)
    16:15:20 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:15:52 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 26
    16:16:04 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 75% chance he's still there at your next pick · fills your open TE
    16:16:21 PT heartbeat: setAwayStatus(false)
    16:16:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:16:53 PT ON CLOCK -> {"drafted":"Rashee Rice","pos":"WR","vorp":34.1,"proj":176.3,"why":"waiting likely costs ~6 pts at WR (best option now 34, ~28 by your next turn) · 44% chance he's still there at your next pick · fills your open WR s
    16:17:25 PT heartbeat: setAwayStatus(false)
    16:17:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:17:47 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 72% chance he's still there at your next pick · fills your open WR 
    16:18:26 PT heartbeat: setAwayStatus(false)
    16:18:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:18:51 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 12% chance he's still there at your next pick · fills your open QB slo
    16:19:26 PT heartbeat: setAwayStatus(false)
    16:19:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:19:55 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 7, ~5 by your next turn) · 74% chance he's still there at your next pick · fil
    16:20:27 PT heartbeat: setAwayStatus(false)
    16:20:27 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:20:31 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 18 pts","s":0.943,"sr":0.943,"e":-5.5,"top_proj_
    16:21:24 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts","s":0.994,"sr":0.994,"e":-10.6,"top_proj
    16:21:28 PT heartbeat: setAwayStatus(false)
    16:21:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:22:11 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts","s":0.708,"sr":0.708,"e":10.7,"top_proj_
    16:22:29 PT heartbeat: setAwayStatus(false)
    16:22:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:23:23 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts","s":0.96
    16:23:29 PT heartbeat: setAwayStatus(false)
    16:23:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:23:44 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts","s":0.
    16:24:30 PT heartbeat: setAwayStatus(false)
    16:24:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:24:48 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.7/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts","s"
    16:25:26 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 35% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · t
    16:25:31 PT heartbeat: setAwayStatus(false)
    16:25:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:26:05 PT BRIDGE WARNING: 1 drafted entries matched no board player: 144 Will Reichard
    16:26:06 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection":
    16:26:08 PT roster full
    16:26:08 PT NARR info roster full — driver done; posting the trail when the room finishes
    16:26:08 PT driver stop


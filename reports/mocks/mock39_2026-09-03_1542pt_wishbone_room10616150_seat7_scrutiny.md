# Scrutiny: Mock 39 -- Wishbone (room 10616150) -- Thursday 2026-09-03 15:42 PT -- 10 teams, our seat 7

Captured 2026-09-03 16:04:35 PT. Times below are Pacific. 10 teams, our team id 7, draft slot 7. 150 picks in the trail, 118 bridge plan calls, 87 recs events in the room log.

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
- Action latency to store confirmation: median 429 ms, min 313, max 2400.
- Heartbeats 20; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 1.
- Bridge warnings (0): none.
- Away seats over the room (each change): {} -> {6} -> {1,6} -> {1,6,9} -> {6,9} -> {6,8,9} -> {6,9} -> {9} -> {6,9} -> {1,6,9} -> {6,9} -> {6} -> {6,8} -> {5,6,8} -> {1,5,6,8} -> {1,3,5,6,8} -> {1,5,6,8} -> {1,5,6,8,9} -> {1,5,6,8} -> {1,5,6,8,9} -> {1,5,6,8}.
- Managers away at the end: 1 Evan, 4 Ashtynn, 5 Seatown, 6 Jared, 8 Nick, 9 Adam.

## Our picks, one block each

### Pick 7 (round 1): Jaxon Smith-Njigba (WR)

- In plain English: Took Jaxon Smith-Njigba (WR) because waiting would likely cost about 8 points at WR, with a 60% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 710 ms, ranker engine, plan call 105, plan age 1048 ms, at 15:43:59 PT.
- Engine's reason: waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 60% chance he's still there at your next pick · fills your open WR slot · TAKE-NOW ZONE: only 2 left before the WR value drops, and 6 teams 
- Top projection available: Josh Allen -> took it: False.
- Passed on: De'Von Achane (RB, s=0.621, e=68.5); Trey McBride (TE, s=0.977, e=77.3); Josh Allen (QB, s=0.869, e=44.9).
- Plan call 105 @pick 7: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6], state store with 6 drafted / 0 mine.
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

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 19 points at RB, with a 32% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 2400 ms, ranker engine, plan call 113, plan age 2775 ms, at 15:45:27 PT.
- Engine's reason: waiting likely costs ~19 pts at RB (best option now 73, ~55 by your next turn) · 32% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 12 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.515, e=59); Drake London (WR, s=0.382, e=44.6); Josh Allen (QB, s=0.464, e=38.4).
- Plan call 113 @pick 14: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6, 8, 9], state store with 13 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.32 | 0.32 | 54.6 | 73.4 | waiting likely costs ~19 pts at RB (best option now 73, ~55 by your next turn) · 32% chanc |
| Trey McBride | TE | 77.9 | 0.52 | 0.52 | 59.0 | 77.9 | waiting likely costs ~19 pts at TE (best option now 78, ~59 by your next turn) · 52% chanc |
| Drake London | WR | 51.0 | 0.38 | 0.38 | 44.6 | 51.0 | waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 38% chance |
| Josh Allen | QB | 47.0 | 0.46 | 0.46 | 38.4 | 47.0 | waiting likely costs ~9 pts at QB (best option now 47, ~38 by your next turn) · 46% chance |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.4 | 8.6 | 9 |
| RB | 73.4 | 54.6 | 18.8 | 20 |
| WR | 51.0 | 44.6 | 6.4 | 23 |
| TE | 77.9 | 59.0 | 18.9 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 55.1 | 18.3 | 51 |

### Pick 27 (round 3): Chris Olave (WR)

- In plain English: Took Chris Olave (WR) because waiting would likely cost about 7 points at WR, with a 23% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1155 ms, ranker engine, plan call 6, plan age 1489 ms, at 15:48:06 PT.
- Engine's reason: waiting likely costs ~7 pts at WR (best option now 40, ~33 by your next turn) · 23% chance he's still there at your next pick · fills your open WR slot · 6 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Josh Allen -> took it: False.
- Passed on: Kyren Williams (RB, s=0.551, e=34.1); Josh Allen (QB, s=0.865, e=44.8); Tyler Warren (TE, s=0.949, e=23.7).
- Plan call 6 @pick 27: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6, 9], state store with 26 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.23 | 0.23 | 32.7 | 40.1 | waiting likely costs ~7 pts at WR (best option now 40, ~33 by your next turn) · 23% chance |
| Kyren Williams | RB | 40.5 | 0.55 | 0.55 | 34.1 | 40.5 | waiting likely costs ~6 pts at your FLEX spot (best option now 41, ~34 by your next turn)  |
| Josh Allen | QB | 47.0 | 0.86 | 0.86 | 44.8 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 86% chance |
| Tyler Warren | TE | 23.8 | 0.95 | 0.95 | 23.7 | 23.8 | safe to wait on TE · 95% chance he's still there at your next pick · fills your open TE sl |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.8 | 2.2 | 10 |
| RB | 40.5 | 34.1 | 6.4 | 17 |
| WR | 40.1 | 32.7 | 7.4 | 23 |
| TE | 23.8 | 23.7 | 0.1 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 34.1 | 6.4 | 47 |

### Pick 34 (round 4): Travis Etienne Jr. (RB)

- In plain English: Took Travis Etienne Jr. (RB) because waiting would likely cost about 3 points at RB, with a 45% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1277 ms, ranker engine, plan call 13, plan age 1610 ms, at 15:49:26 PT.
- Engine's reason: waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 45% chance he's still there at your next pick · fills your open RB slot · only 3 RBs left at this level · 12 teams picking before you still 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.603, e=25.7); Tyler Warren (TE, s=0.572, e=22.6); Rashee Rice (WR, s=None, e=None).
- Plan call 13 @pick 34: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 6, 9], state store with 33 drafted / 3 mine.
- Engine's first choice was **Travis Etienne Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Travis Etienne Jr. | RB | 26.3 | 0.45 | 0.45 | 23.1 | 26.3 | waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 45% chance |
| Drake Maye | QB | 31.1 | 0.60 | 0.60 | 25.7 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 60% chance |
| Tyler Warren | TE | 23.8 | 0.57 | 0.57 | 22.6 | 23.8 | waiting likely costs ~1 pts at TE (best option now 24, ~23 by your next turn) · 57% chance |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.7 | 5.4 | 10 |
| RB | 26.3 | 23.1 | 3.2 | 18 |
| WR | 34.1 | 24.4 | 9.7 | 19 |
| TE | 23.8 | 22.6 | 1.2 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 23.5 | 2.8 | 44 |

### Pick 47 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 6 points at QB, with a 56% chance he would still be there next turn.
- Driver: via **action**, verified store, 418 ms, ranker engine, plan call 24, plan age 745 ms, at 15:51:34 PT.
- Engine's reason: waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 56% chance he's still there at your next pick · fills your open QB slot · 4 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: True.
- Passed on: George Kittle (TE, s=0.983, e=21); Jaylen Warren (RB, s=0.961, e=9.2); Kyle Pitts Sr. (TE, s=None, e=None).
- Plan call 24 @pick 47: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6, 9], state store with 46 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.56 | 0.56 | 25.1 | 31.1 | waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 56% chance |
| George Kittle | TE | 19.8 | 0.98 | 0.98 | 21.0 | 21.1 | safe to wait on TE · 98% chance he's still there at your next pick · fills your open TE sl |
| Jaylen Warren | RB | 9.3 | 0.96 | 0.96 | 9.2 | 9.3 | safe to wait on your FLEX spot · 96% chance he's still there at your next pick · fills a F |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.1 | 6.0 | 12 |
| RB | 9.3 | 9.2 | 0.1 | 14 |
| WR | 15.4 | 14.8 | 0.6 | 22 |
| TE | 21.1 | 21.0 | 0.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 44 |

### Pick 54 (round 6): George Kittle (TE)

- In plain English: Took George Kittle (TE): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (85% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 813 ms, ranker engine, plan call 29, plan age 1148 ms, at 15:52:26 PT.
- Engine's reason: safe to wait on TE · 85% chance he's still there at your next pick · fills your open TE slot · 12 teams picking before you still need a TE · two-pick plan: pair with the ~37-pt WR expected at your next turn
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.79, e=8.7); Kyle Pitts Sr. (TE, s=None, e=None); Harold Fannin Jr. (TE, s=None, e=None).
- Plan call 29 @pick 54: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6, 9], state store with 53 drafted / 5 mine.
- Engine's first choice was **George Kittle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| George Kittle | TE | 19.8 | 0.85 | 0.85 | 20.3 | 21.1 | safe to wait on TE · 85% chance he's still there at your next pick · fills your open TE sl |
| Jaylen Warren | RB | 9.3 | 0.79 | 0.79 | 8.7 | 9.3 | safe to wait on your FLEX spot · 79% chance he's still there at your next pick · fills a F |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Tucker Kraft | TE | 16.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Dallas Goedert | TE | 13.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.0 | 0.7 | 11 |
| RB | 9.3 | 8.7 | 0.6 | 17 |
| WR | 13.1 | 7.4 | 5.7 | 22 |
| TE | 21.1 | 20.3 | 0.8 | 10 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.7 | 0.6 | 49 |

### Pick 67 (round 7): Rhamondre Stevenson (RB)

- In plain English: Took Rhamondre Stevenson (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (84% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1388 ms, ranker engine, plan call 41, plan age 1729 ms, at 15:54:50 PT.
- Engine's reason: safe to wait on your FLEX spot · 84% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Davante Adams (WR, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 41 @pick 67: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 6, 8], state store with 66 drafted / 6 mine.
- Engine's first choice was **Rhamondre Stevenson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rhamondre Stevenson | RB | 7.2 | 0.83 | 0.83 | 6.2 | 7.2 | safe to wait on your FLEX spot · 84% chance he's still there at your next pick · fills a F |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.5 | 0.2 | 17 |
| RB | 7.2 | 6.2 | 1.0 | 24 |
| WR | 13.1 | 11.6 | 1.5 | 33 |
| TE | 21.1 | 17.2 | 3.9 | 17 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 7.2333043142844815 | 6.2 | 1.0 | 74 |

### Pick 74 (round 8): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +1.9 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 18 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 585 ms, ranker engine, plan call 47, plan age 910 ms, at 15:55:50 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 18 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jameson Williams (WR, s=0.079, e=-6.7); Mike Evans (WR, s=None, e=None); Parker Washington (WR, s=None, e=None).
- Plan call 47 @pick 74: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8, 9], state store with 73 drafted / 7 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.93 | 0.93 | -5.5 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodri |
| Jameson Williams | WR | 0.0 | 0.08 | 0.08 | -6.7 | 0.0 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.6/wk over the wire (Romeo Doubs |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.7 | 1.0 | 18 |
| RB | -5.4 | -5.5 | 0.1 | 33 |
| WR | 0.0 | -6.7 | 6.7 | 41 |
| TE | 21.1 | 17.0 | 4.1 | 20 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 6 |

### Pick 87 (round 9): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +1.0 points a week over the waiver wire (Romeo Doubs), worth about 7 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 420 ms, ranker engine, plan call 56, plan age 750 ms, at 15:57:31 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.972, e=-6.6); Courtland Sutton (WR, s=None, e=None); Michael Pittman Jr. (WR, s=None, e=None).
- Plan call 56 @pick 87: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 86 drafted / 8 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.99 | 0.99 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs |
| Kenny Gainwell | RB | -6.2 | 0.97 | 0.97 | -6.6 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Wilson | WR | -14.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.0 | 0.8 | 17 |
| RB | -6.2 | -6.6 | 0.4 | 30 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 13.8 | 12.9 | 0.9 | 19 |
| K | 13.5 | 13.5 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 10 |

### Pick 94 (round 10): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Tyler Shough), worth about 8 points.
- Driver: via **action**, verified store, 427 ms, ranker engine, plan call 63, plan age 759 ms, at 15:58:48 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Kenny Gainwell (RB, s=0.882, e=-8.6); Courtland Sutton (WR, s=0.692, e=-11.9); Matthew Stafford (QB, s=None, e=None).
- Plan call 63 @pick 94: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 93 drafted / 9 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.72 | 0.72 | 10.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough |
| Kenny Gainwell | RB | -6.2 | 0.88 | 0.88 | -8.6 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Courtland Sutton | WR | -11.1 | 0.69 | 0.69 | -11.9 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.5 | 2.3 | 17 |
| RB | -6.2 | -8.6 | 2.4 | 27 |
| WR | -11.1 | -11.9 | 0.8 | 35 |
| TE | 13.8 | 12.4 | 1.4 | 19 |
| K | 13.5 | 13.5 | 0.0 | 14 |
| DEF | 18.0 | 18.0 | 0.0 | 10 |

### Pick 107 (round 11): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +0.7 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 2 points. The top raw projection available was Jaxson Dart; the engine passed on him on purpose.
- Driver: via **action**, verified store, 400 ms, ranker engine, plan call 72, plan age 731 ms, at 16:00:31 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +0.7/wk over the wire (Chris Rodriguez Jr.) ≈ 2 pts
- Top projection available: Jaxson Dart -> took it: False.
- Passed on: Michael Pittman Jr. (WR, s=0.948, e=-13.7); Jakobi Meyers (WR, s=None, e=None); Jordan Addison (WR, s=None, e=None).
- Plan call 72 @pick 107: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 106 drafted / 10 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.96 | 0.96 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +0.7 |
| Michael Pittman Jr. | WR | -13.3 | 0.95 | 0.95 | -13.7 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.9 |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -10.9 | -10.9 | 0.0 | 14 |
| RB | -25.9 | -26.0 | 0.1 | 23 |
| WR | -13.3 | -13.7 | 0.4 | 30 |
| TE | 13.8 | 13.4 | 0.4 | 18 |
| K | 13.5 | 13.4 | 0.1 | 15 |
| DEF | 18.0 | 17.3 | 0.7 | 13 |

### Pick 114 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +0.9 points a week over the waiver wire (Deebo Samuel Sr.), worth about 1 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 429 ms, ranker engine, plan call 77, plan age 759 ms, at 16:01:17 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.9/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Woody Marks (RB, s=0.945, e=-30.5); Jakobi Meyers (WR, s=None, e=None); Makai Lemon (WR, s=None, e=None).
- Plan call 77 @pick 114: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 113 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.92 | 0.92 | -14.0 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.9 |
| Woody Marks | RB | -30.3 | 0.94 | 0.94 | -30.5 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 13 |
| RB | -30.3 | -30.5 | 0.2 | 21 |
| WR | -13.3 | -14.0 | 0.7 | 29 |
| TE | 0.5 | 0.2 | 0.3 | 15 |
| K | 13.5 | 11.9 | 1.6 | 16 |
| DEF | 18.0 | 15.9 | 2.1 | 13 |

### Pick 127 (round 13): Woody Marks (RB)

- In plain English: Lineup already full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +0.4 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 0 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 378 ms, ranker engine, plan call 83, plan age 730 ms, at 16:02:13 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.4/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.96, e=-21.8); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 83 @pick 127: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 126 drafted / 12 mine.
- Engine's first choice was **Woody Marks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Woody Marks | RB | -30.3 | 0.97 | 0.97 | -30.4 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Jakobi Meyers | WR | -21.5 | 0.96 | 0.96 | -21.8 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyrone Tracy Jr. | RB | -33.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -11.9 | 0.1 | 12 |
| RB | -30.3 | -30.4 | 0.1 | 20 |
| WR | -21.5 | -21.8 | 0.3 | 23 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 12.0 | 11.6 | 0.4 | 16 |
| DEF | 16.0 | 15.0 | 1.0 | 12 |

### Pick 134 (round 14): Eagles (DEF)

- In plain English: Took Philadelphia Eagles (DEF) because waiting would likely cost about 2 points at DEF, with a 20% chance he would still be there next turn. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 313 ms, ranker engine, plan call 86, plan age 641 ms, at 16:02:37 PT.
- Engine's reason: waiting likely costs ~2 pts at DEF (best option now 10, ~8 by your next turn) · 20% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · two-pick plan: pair
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cam Little (K, s=0.639, e=8.4); Cameron Dicker (K, s=None, e=None); Minnesota Vikings (DEF, s=None, e=None).
- Plan call 86 @pick 134: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8], state store with 133 drafted / 13 mine.
- Engine's first choice was **Philadelphia Eagles** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Philadelphia Eagles | DEF | 10.0 | 0.20 | 0.20 | 7.9 | 10.0 | waiting likely costs ~2 pts at DEF (best option now 10, ~8 by your next turn) · 20% chance |
| Cam Little | K | 9.0 | 0.64 | 0.64 | 8.4 | 10.5 | waiting likely costs ~2 pts at K (best option now 10, ~8 by your next turn) · 64% chance h |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Pittsburgh Steelers | DEF | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.1 | 0.2 | 11 |
| RB | -33.0 | -33.5 | 0.5 | 17 |
| WR | -21.5 | -22.1 | 0.6 | 23 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 10.5 | 8.4 | 2.1 | 15 |
| DEF | 10.0 | 7.9 | 2.1 | 10 |

### Pick 147 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 383 ms, ranker engine, plan call 93, plan age 741 ms, at 16:03:43 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 93 @pick 147: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 5, 6, 8], state store with 146 drafted / 14 mine.
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
| 0-30% | 8 | 20% | 12% |
| 30-50% | 19 | 43% | 21% |
| 50-70% | 44 | 58% | 36% |
| 70-90% | 45 | 81% | 53% |
| 90-100% | 98 | 96% | 87% |

214 predictions over 86 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    15:42:17  plan #96 for pick 1
  • Christian McCaffrey RB · wait costs 19 · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next) · 49% survives to our turn
  • Ja'Marr Chase WR · wait costs 11 · pick costs 24.2 · 52% survives to our tu
    15:42:18  driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    15:43:06  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    15:43:09  plan #101 for pick 2
  • Christian McCaffrey RB · wait costs 22 · pick costs 0, best pair 284.8 (159.6 now + ~125.2 RB next) · 52% survives to our turn
  • Ja'Marr Chase WR · wait costs 9 · pick costs 20.8 · 59% survives to our tu
    15:43:17  pick 2  Bijan Robinson (RB) taken by seat 2 in 11 s — a target is gone
    15:43:18  heartbeat sent (Yahoo told we are not idle)
    15:43:23  plan #102 for pick 3
  • Christian McCaffrey RB · wait costs 28 · pick costs 0, best pair 279.8 (159.6 now + ~120.2 WR next) · 54% survives to our turn
  • Ja'Marr Chase WR · wait costs 6 · pick costs 22.6 · 70% survives to our tu
    15:43:33  pick 3  Ja'Marr Chase (WR) taken by seat 3 in 16 s — a target is gone (was 70% to survive)
    15:43:34  plan #103 for pick 4
  • Christian McCaffrey RB · wait costs 20 · pick costs 0, best pair 269.3 (159.6 now + ~109.7 RB next) · 67% survives to our turn
  • Puka Nacua WR · wait costs 4 · pick costs 19.1 · 71% survives to our turn

    15:43:42  pick 4  Jonathan Taylor (RB) taken by seat 4 in 9 s — a target is gone
    15:43:47  plan #104 for pick 5
  • Christian McCaffrey RB · wait costs 22 · pick costs 0, best pair 268.1 (159.6 now + ~108.5 WR next) · 73% survives to our turn
  • Puka Nacua WR · wait costs 2 · pick costs 19.8 · 82% survives to our turn

    15:43:56  pick 5  Puka Nacua (WR) taken by seat 5 in 14 s — a target is gone (was 82% to survive)
    15:43:57  pick 6  Christian McCaffrey (RB) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone (was 73% to survive)
    15:43:58  plan #105 for pick 7
  • Jaxon Smith-Njigba WR · wait costs 8 · pick costs 0, best pair 192.4 (100 now + ~92.4 WR next) · 60% survives to our turn
  • De'Von Achane RB · wait costs 5 · pick costs 21.1 · 62% survives to our turn
  
    15:43:58  ON THE CLOCK, pick 7 · plan #105 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    15:43:59  PICKED Jaxon Smith-Njigba (WR) via action, confirmed in 710 ms — chose Jaxon Smith-Njigba (WR): waiting would likely cost about 8 points at WR, 60% to still be there next turn
  • top projection left was Josh Allen, passed on purp
    15:44:03  plan #106 for pick 8
  • Amon-Ra St. Brown WR · wait costs 13 · pick costs 0, best pair 165.6 (92.4 now + ~73.2 RB next) · 54% survives to our turn
  • De'Von Achane RB · wait costs 6 · pick costs 6.8 · 57% survives to our turn
  
    15:44:07  pick 8  James Cook III (RB) taken by seat 8 in 8 s — a target is gone
    15:44:15  plan #107 for pick 9
  • Amon-Ra St. Brown WR · wait costs 11 · pick costs 0, best pair 164.5 (92.4 now + ~72.1 RB next) · 60% survives to our turn
  • De'Von Achane RB · wait costs 7 · pick costs 3.8 · 59% survives to our turn
  
    15:44:19  heartbeat sent (Yahoo told we are not idle)
    15:44:36  pick 9  Amon-Ra St. Brown (WR) taken by seat 9 in 28 s — a target is gone (was 60% to survive)
    15:44:39  plan #109 for pick 10
  • De'Von Achane RB · wait costs 6 · pick costs 0, best pair 144.7 (78.8 now + ~65.9 RB next) · 64% survives to our turn
  • CeeDee Lamb WR · wait costs 2 · pick costs 4.1 · 52% survives to our turn
  • Trey
    15:44:39  pick 10  Saquon Barkley (RB) taken by seat 10 in 4 s
    15:44:52  pick 11  CeeDee Lamb (WR) taken by seat 10 in 12 s — a target is gone (was 52% to survive)
    15:44:52  pick 12  Kenneth Walker III (RB) taken by seat 9 in 0 s
    15:44:52  plan #110 for pick 13
  • De'Von Achane RB · wait costs 1 · pick costs 0, best pair 144.7 (78.8 now + ~65.9 RB next) · 90% survives to our turn
  • Justin Jefferson WR · safe to wait · pick costs 2.7 · 89% survives to our turn
  •
    15:45:21  pick 13  Justin Jefferson (WR) taken by seat 8 in 30 s — a target is gone (was 89% to survive)
    15:45:21  heartbeat sent (Yahoo told we are not idle)
    15:45:24  plan #113 for pick 14
  • De'Von Achane RB · wait costs 19 · pick costs 0, best pair 138.8 (78.8 now + ~60 RB next) · 32% survives to our turn
  • Trey McBride TE · wait costs 19 · pick costs 14.6 · 52% survives to our turn
  • Dr
    15:45:24  ON THE CLOCK, pick 14 · plan #113 (0.0 s old) · lineup needs QB RBx2 WR TE FLEX K DEF
    15:45:27  pick 15  Chase Brown (RB) taken by seat 6 in 0 s — a target is gone
    15:45:27  PICKED De'Von Achane (RB) via action, confirmed in 2400 ms — chose De'Von Achane (RB): waiting would likely cost about 19 points at RB, 32% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    15:45:34  plan #114 for pick 16
  • Trey McBride TE · wait costs 20 · pick costs 0, best pair 119.3 (64.2 now + ~55.1 WR next) · 50% survives to our turn
  • Drake London WR · wait costs 7 · pick costs 3.4 · 36% survives to our turn
  • Der
    15:45:52  pick 16  Derrick Henry (RB) taken by seat 5 in 25 s — a target is gone (was 28% to survive)
    15:45:57  plan #116 for pick 17
  • Trey McBride TE · wait costs 18 · pick costs 0, best pair 119.5 (64.2 now + ~55.3 WR next) · 53% survives to our turn
  • Drake London WR · wait costs 6 · pick costs 3.6 · 37% survives to our turn
  • Kyr
    15:46:08  pick 17  Javonte Williams (RB) taken by seat 4 in 16 s
    15:46:09  plan #117 for pick 18
  • Trey McBride TE · wait costs 18 · pick costs 0, best pair 120.9 (64.2 now + ~56.7 WR next) · 52% survives to our turn
  • Drake London WR · wait costs 5 · pick costs 5 · 48% survives to our turn
  • Kyren
    15:46:17  pick 18  Brock Bowers (TE) taken by seat 3 in 9 s — a target is gone
    15:46:21  plan #118 for pick 19
  • Trey McBride TE · wait costs 26 · pick costs 0, best pair 121.2 (64.2 now + ~57 WR next) · 52% survives to our turn
  • Drake London WR · wait costs 5 · pick costs 5.3 · 49% survives to our turn
  • Kyren
    15:46:22  heartbeat sent (Yahoo told we are not idle)
    15:46:25  pick 19  Omarion Hampton (RB) taken by seat 2 in 8 s — a target is gone
    15:46:34  plan #119 for pick 20
  • Trey McBride TE · wait costs 21 · pick costs 0, best pair 121.7 (64.2 now + ~57.5 WR next) · 61% survives to our turn
  • Drake London WR · wait costs 4 · pick costs 5.8 · 53% survives to our turn
  • Kyr
    15:46:47  pick 20  Drake London (WR) taken by seat 1 in 22 s — a target is gone (was 47% to survive)
    15:46:52  pick 21  Trey McBride (TE) taken by seat 1 in 5 s — a target is gone (was 57% to survive)
    15:47:00  engine bridge unreachable (TypeError: Failed to fetch) — using the last plan; the queue is the safety net
    15:47:06  pick 22  Nico Collins (WR) taken by seat 2 in 15 s — a target is gone
    15:47:11  plan #1 for pick 23
  • A.J. Brown WR · wait costs 2 · pick costs 0, best pair 105 (54.3 now + ~50.7 WR next) · 65% survives to our turn
  • Kyren Williams RB · wait costs 3 · pick costs 6.4 · 74% survives to our turn
  • Josh All
    15:47:21  pick 23  Ashton Jeanty (RB) taken by seat 3 in 15 s — a target is gone
    15:47:23  heartbeat sent (Yahoo told we are not idle)
    15:47:24  plan #2 for pick 24
  • A.J. Brown WR · wait costs 1 · pick costs 0, best pair 105 (54.3 now + ~50.7 WR next) · 67% survives to our turn
  • Kyren Williams RB · wait costs 3 · pick costs 6.2 · 76% survives to our turn
  • Josh All
    15:47:33  pick 24  George Pickens (WR) taken by seat 4 in 12 s — a target is gone
    15:47:37  plan #3 for pick 25
  • A.J. Brown WR · wait costs 2 · pick costs 0, best pair 105 (54.3 now + ~50.7 WR next) · 49% survives to our turn
  • Kyren Williams RB · wait costs 2 · pick costs 6.8 · 83% survives to our turn
  • Josh All
    15:48:02  pick 25  A.J. Brown (WR) taken by seat 5 in 29 s — a target is gone (was 49% to survive)
    15:48:02  plan #5 for pick 26
  • Kyren Williams RB · wait costs 2 · pick costs 0, best pair 96.2 (45.9 now + ~50.3 WR next) · 88% survives to our turn
  • Chris Olave WR · safe to wait · pick costs 0.7 · 93% survives to our turn
  • Josh A
    15:48:03  pick 26  Malik Nabers (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    15:48:04  plan #6 for pick 27
  • Chris Olave WR · wait costs 7 · pick costs 0, best pair 95.5 (50.7 now + ~44.8 WR next) · 23% survives to our turn
  • Kyren Williams RB · wait costs 6 · pick costs 6.2 · 55% survives to our turn
  • Josh A
    15:48:04  ON THE CLOCK, pick 27 · plan #6 (0.0 s old) · lineup needs QB RB WR TE FLEX K DEF
    15:48:06  PICKED Chris Olave (WR) via action, confirmed in 1155 ms — chose Chris Olave (WR): waiting would likely cost about 7 points at WR, 23% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    15:48:09  plan #7 for pick 28
  • Kyren Williams RB · wait costs 8 · pick costs 0, best pair 107.4 (45.9 now + ~61.5 WR next) · 47% survives to our turn
  • Josh Allen QB · wait costs 2 · pick costs 11.7 · 86% survives to our turn
  • Tyler
    15:48:20  pick 28  Kyren Williams (RB) taken by seat 8 in 14 s — a target is gone (was 47% to survive)
    15:48:21  pick 29  DeVonta Smith (WR) taken by seat 9 in 1 s INSTANTLY (autopick)
    15:48:21  plan #8 for pick 30
  • Josh Allen QB · wait costs 1 · pick costs 0, best pair 89.1 (34.2 now + ~54.9 WR next) · 92% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · pick costs 2.5 · 87% survives to our turn
  • Tyl
    15:48:25  heartbeat sent (Yahoo told we are not idle)
    15:48:41  pick 30  Josh Allen (QB) taken by seat 10 in 21 s — a target is gone (was 92% to survive)
    15:48:47  plan #10 for pick 31
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 86.6 (31.7 now + ~54.9 WR next) · 90% survives to our turn
  • Drake Maye QB · safe to wait · pick costs 13.4 · 98% survives to our turn
  • T
    15:49:10  pick 31  Jeremiyah Love (RB) taken by seat 10 in 28 s — a target is gone
    15:49:10  pick 32  Tee Higgins (WR) taken by seat 9 in 0 s INSTANTLY (autopick)
    15:49:11  plan #12 for pick 33
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 86.7 (31.7 now + ~55 WR next) · 95% survives to our turn
  • Drake Maye QB · safe to wait · pick costs 13.4 · 97% survives to our turn
  • Tyl
    15:49:12  pick 33  Jaylen Waddle (WR) taken by seat 8 in 2 s INSTANTLY (autopick)
    15:49:24  plan #13 for pick 34
  • Travis Etienne Jr. RB · wait costs 3 · pick costs 0, best pair 83.9 (31.7 now + ~52.2 WR next) · 45% survives to our turn
  • Drake Maye QB · wait costs 5 · pick costs 13.4 · 60% survives to our turn
  • T
    15:49:24  ON THE CLOCK, pick 34 · plan #13 (0.0 s old) · lineup needs QB RB TE FLEX K DEF
    15:49:26  pick 35  Breece Hall (RB) taken by seat 6 in 0 s INSTANTLY (autopick)
    15:49:26  PICKED Travis Etienne Jr. (RB) via action, confirmed in 1277 ms — chose Travis Etienne Jr. (RB): waiting would likely cost about 3 points at RB, 45% to still be there next turn
  • top projection left was Drake Maye, passed on pur
    15:49:28  heartbeat sent (Yahoo told we are not idle)
    15:49:31  plan #14 for pick 36
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 68 (18.3 now + ~49.7 WR next) · 56% survives to our turn
  • Tyler Warren TE · wait costs 1 · pick costs 8.3 · 56% survives to our turn
  • Cam Skatte
    15:49:40  pick 36  Cam Skattebo (RB) taken by seat 5 in 14 s — a target is gone (was 46% to survive)
    15:49:43  plan #15 for pick 37
  • Drake Maye QB · wait costs 5 · pick costs 0, best pair 63.9 (18.3 now + ~45.6 WR next) · 61% survives to our turn
  • Tyler Warren TE · wait costs 1 · pick costs 8.3 · 57% survives to our turn
  • D'Andre 
    15:49:43  pick 37  Zay Flowers (WR) taken by seat 4 in 3 s — a target is gone
    15:49:55  plan #16 for pick 38
  • Drake Maye QB · wait costs 5 · pick costs 0, best pair 64.3 (18.3 now + ~46 WR next) · 62% survives to our turn
  • Tyler Warren TE · wait costs 1 · pick costs 8.3 · 61% survives to our turn
  • D'Andre Sw
    15:49:56  pick 38  D'Andre Swift (RB) taken by seat 3 in 14 s — a target is gone (was 57% to survive)
    15:50:08  plan #17 for pick 39
  • Rashee Rice WR · wait costs 4 · pick costs 0, best pair 65.5 (44.8 now + ~20.7 WR next) · 43% survives to our turn
  • Drake Maye QB · wait costs 5 · pick costs 6.3 · 61% survives to our turn
  • Tyler War
    15:50:08  pick 39  Colston Loveland (TE) taken by seat 2 in 11 s — a target is gone
    15:50:11  pick 40  Rashee Rice (WR) taken by seat 1 in 3 s — a target is gone (was 43% to survive)
    15:50:20  plan #18 for pick 41
  • Drake Maye QB · wait costs 4 · pick costs 0, best pair 56.2 (18.3 now + ~37.9 WR next) · 70% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 8.3 · 71% survives to our turn
  • Jaylen W
    15:50:28  heartbeat sent (Yahoo told we are not idle)
    15:50:37  pick 41  Bucky Irving (RB) taken by seat 1 in 27 s
    15:50:45  plan #20 for pick 42
  • Drake Maye QB · wait costs 3 · pick costs 0, best pair 56.2 (18.3 now + ~37.9 WR next) · 75% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 8.3 · 75% survives to our turn
  • Jaylen W
    15:50:55  pick 42  Lamar Jackson (QB) taken by seat 2 in 17 s
    15:50:57  plan #21 for pick 43
  • Drake Maye QB · wait costs 3 · pick costs 0, best pair 56.2 (18.3 now + ~37.9 WR next) · 77% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 8.3 · 77% survives to our turn
  • Jaylen W
    15:51:05  pick 43  Joe Burrow (QB) taken by seat 3 in 10 s
    15:51:09  plan #22 for pick 44
  • Drake Maye QB · wait costs 3 · pick costs 0, best pair 56.3 (18.3 now + ~38 WR next) · 76% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 8.3 · 82% survives to our turn
  • Jaylen War
    15:51:10  pick 44  David Montgomery (RB) taken by seat 4 in 6 s
    15:51:22  plan #23 for pick 45
  • Drake Maye QB · wait costs 3 · pick costs 0, best pair 56.3 (18.3 now + ~38 WR next) · 80% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 8.3 · 87% survives to our turn
  • Jaylen War
    15:51:29  heartbeat sent (Yahoo told we are not idle)
    15:51:32  pick 45  Tyler Warren (TE) taken by seat 5 in 21 s — a target is gone (was 87% to survive)
    15:51:33  pick 46  Garrett Wilson (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    15:51:34  plan #24 for pick 47
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 56.2 (18.3 now + ~37.9 WR next) · 56% survives to our turn
  • George Kittle TE · safe to wait · pick costs 12.3 · 98% survives to our turn
  • Jaylen
    15:51:34  ON THE CLOCK, pick 47 · plan #24 (0.0 s old) · lineup needs QB TE FLEX K DEF
    15:51:34  PICKED Drake Maye (QB) via action, confirmed in 418 ms — chose Drake Maye (QB): waiting would likely cost about 6 points at QB, 56% to still be there next turn
    15:51:37  plan #25 for pick 48
  • George Kittle TE · safe to wait · pick costs 0, best pair 43.9 (6 now + ~37.9 WR next) · 98% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 13.9 · 97% survives to our turn
  • Kyle P
    15:51:46  pick 48  Tetairoa McMillan (WR) taken by seat 8 in 11 s — a target is gone
    15:51:47  pick 49  Bhayshul Tuten (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    15:51:49  plan #26 for pick 50
  • George Kittle TE · safe to wait · pick costs 0, best pair 43.9 (6 now + ~37.9 WR next) · 98% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 15.4 · 98% survives to our turn
  • Kyle P
    15:52:06  pick 50  Ladd McConkey (WR) taken by seat 10 in 19 s
    15:52:12  pick 51  Emeka Egbuka (WR) taken by seat 10 in 6 s
    15:52:12  pick 52  Jayden Daniels (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    15:52:14  plan #28 for pick 53
  • George Kittle TE · safe to wait · pick costs 0, best pair 44 (6 now + ~38 WR next) · 98% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 15.1 · 99% survives to our turn
  • Kyle Pitts
    15:52:22  pick 53  Jalen Hurts (QB) taken by seat 8 in 11 s
    15:52:25  plan #29 for pick 54
  • George Kittle TE · safe to wait · pick costs 0, best pair 43.3 (6 now + ~37.3 WR next) · 85% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 17.8 · 79% survives to our turn
  • Kyle P
    15:52:25  ON THE CLOCK, pick 54 · plan #29 (0.0 s old) · lineup needs TE FLEX K DEF
    15:52:26  PICKED George Kittle (TE) via action, confirmed in 813 ms — chose George Kittle (TE): nothing urgent, the most valuable player who fills a slot (85% to survive, nobody better worth waiting for)
  • top projection left was Trevor L
    15:52:29  pick 55  Tucker Kraft (TE) taken by seat 6 in 2 s — a target is gone
    15:52:31  plan #30 for pick 56
  • Jaylen Warren RB · safe to wait · 81% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    15:52:34  heartbeat sent (Yahoo told we are not idle)
    15:52:36  pick 56  Quinshon Judkins (RB) taken by seat 5 in 7 s — a target is gone
    15:52:43  plan #31 for pick 57
  • Jaylen Warren RB · safe to wait · 77% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    15:52:57  pick 57  Jaylen Warren (RB) taken by seat 4 in 21 s — a target is gone (was 77% to survive)
    15:53:10  plan #33 for pick 58
  • Rhamondre Stevenson RB · wait costs 1 · 81% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Terry McLaurin WR · depth fallback, engine list done
    15:53:10  pick 58  DJ Moore (WR) taken by seat 3 in 13 s
    15:53:22  plan #34 for pick 59
  • Rhamondre Stevenson RB · wait costs 1 · 84% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Terry McLaurin WR · depth fallback, engine list done
    15:53:24  pick 59  Terry McLaurin (WR) taken by seat 2 in 14 s — a target is gone
    15:53:34  plan #35 for pick 60
  • Rhamondre Stevenson RB · safe to wait · 86% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    15:53:37  heartbeat sent (Yahoo told we are not idle)
    15:53:40  pick 60  Dak Prescott (QB) taken by seat 1 in 16 s
    15:53:46  plan #36 for pick 61
  • Rhamondre Stevenson RB · safe to wait · 86% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    15:53:58  pick 61  Rams (DEF) taken by seat 1 in 17 s
    15:53:59  plan #37 for pick 62
  • Rhamondre Stevenson RB · safe to wait · 90% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    15:54:12  pick 62  Christian Watson (WR) taken by seat 2 in 14 s — a target is gone
    15:54:24  plan #39 for pick 63
  • Rhamondre Stevenson RB · safe to wait · 94% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    15:54:39  heartbeat sent (Yahoo told we are not idle)
    15:54:41  pick 63  Jadarian Price (RB) taken by seat 3 in 28 s
    15:54:45  pick 64  Bo Nix (QB) taken by seat 4 in 5 s
    15:54:47  pick 65  Caleb Williams (QB) taken by seat 5 in 1 s INSTANTLY (autopick)
    15:54:47  pick 66  Justin Herbert (QB) taken by seat 6 in 0 s INSTANTLY (autopick)
    15:54:48  plan #41 for pick 67
  • Rhamondre Stevenson RB · safe to wait · 84% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    15:54:48  ON THE CLOCK, pick 67 · plan #41 (0.0 s old) · lineup needs FLEX K DEF
    15:54:50  pick 68  TreVeyon Henderson (RB) taken by seat 8 in 0 s INSTANTLY (autopick) — a target is gone
    15:54:50  PICKED Rhamondre Stevenson (RB) via action, confirmed in 1388 ms — chose Rhamondre Stevenson (RB): nothing urgent, the most valuable player who fills a slot (84% to survive, nobody better worth waiting for)
  • top projection left
    15:54:54  plan #42 for pick 69
  • RJ Harvey RB · insurance worth ~18 · 99% survives to our turn
  • Davante Adams WR · insurance worth ~16 · 90% survives to our turn
  • Jameson Williams WR · depth fallback, engine list done
    15:55:19  pick 69  Sam LaPorta (TE) taken by seat 9 in 29 s
    15:55:29  plan #45 for pick 70
  • RJ Harvey RB · insurance worth ~18 · 100% survives to our turn
  • Davante Adams WR · insurance worth ~16 · 95% survives to our turn
  • Jameson Williams WR · depth fallback, engine list done
    15:55:35  pick 70  Luther Burden III (WR) taken by seat 10 in 15 s — a target is gone
    15:55:39  heartbeat sent (Yahoo told we are not idle)
    15:55:41  plan #46 for pick 71
  • RJ Harvey RB · insurance worth ~18 · 100% survives to our turn
  • Davante Adams WR · insurance worth ~16 · 95% survives to our turn
  • Jameson Williams WR · depth fallback, engine list done
    15:55:46  pick 71  Davante Adams (WR) taken by seat 10 in 12 s — a target is gone (was 95% to survive)
    15:55:46  pick 72  Rome Odunze (WR) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone
    15:55:47  pick 73  Harold Fannin Jr. (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    15:55:49  plan #47 for pick 74
  • RJ Harvey RB · insurance worth ~18 · 93% survives to our turn
  • Jameson Williams WR · insurance worth ~11 · 8% survives to our turn
  • Mike Evans WR · depth fallback, engine list done
    15:55:49  ON THE CLOCK, pick 74 · plan #47 (0.0 s old) · lineup needs K DEF
    15:55:50  PICKED RJ Harvey (RB) via action, confirmed in 585 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +1.9 a week over the wire, about 18 points
  • top projection left was Trevor 
    15:55:52  pick 75  Jameson Williams (WR) taken by seat 6 in 2 s — a target is gone (was 8% to survive)
    15:55:52  pick 76  Parker Washington (WR) taken by seat 5 in 0 s — a target is gone
    15:55:53  plan #48 for pick 77
  • Mike Evans WR · insurance worth ~10 · 16% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 97% survives to our turn
  • DK Metcalf WR · depth fallback, engine list done
    15:56:00  pick 77  Kyle Pitts Sr. (TE) taken by seat 4 in 8 s
    15:56:06  plan #49 for pick 78
  • Mike Evans WR · insurance worth ~10 · 16% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • DK Metcalf WR · depth fallback, engine list done
    15:56:10  pick 78  Jonathon Brooks (RB) taken by seat 3 in 10 s
    15:56:18  plan #50 for pick 79
  • Mike Evans WR · insurance worth ~10 · 17% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 97% survives to our turn
  • DK Metcalf WR · depth fallback, engine list done
    15:56:21  pick 79  Mike Evans (WR) taken by seat 2 in 11 s — a target is gone (was 17% to survive)
    15:56:21  pick 80  Marvin Harrison Jr. (WR) taken by seat 1 in 0 s — a target is gone
    15:56:22  pick 81  Brian Thomas Jr. (WR) taken by seat 1 in 1 s INSTANTLY (autopick)
    15:56:30  plan #51 for pick 82
  • DK Metcalf WR · insurance worth ~7 · 58% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 98% survives to our turn
  • Carnell Tate WR · depth fallback, engine list done
    15:56:39  heartbeat sent (Yahoo told we are not idle)
    15:56:49  pick 82  DK Metcalf (WR) taken by seat 2 in 28 s — a target is gone (was 58% to survive)
    15:56:55  plan #53 for pick 83
  • Carnell Tate WR · insurance worth ~7 · 36% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Wan'Dale Robinson WR · depth fallback, engine list done
    15:57:09  pick 83  Rico Dowdle (RB) taken by seat 3 in 20 s — a target is gone
    15:57:20  plan #55 for pick 84
  • Carnell Tate WR · insurance worth ~7 · 33% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 100% survives to our turn
  • Wan'Dale Robinson WR · depth fallback, engine list done
    15:57:29  pick 84  Jayden Reed (WR) taken by seat 4 in 20 s
    15:57:29  pick 85  Carnell Tate (WR) taken by seat 5 in 0 s INSTANTLY (autopick) — a target is gone (was 33% to survive)
    15:57:29  pick 86  Trevor Lawrence (QB) taken by seat 6 in 1 s INSTANTLY (autopick)
    15:57:30  plan #56 for pick 87
  • Wan'Dale Robinson WR · insurance worth ~7 · 99% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 97% survives to our turn
  • Courtland Sutton WR · depth fallback, engine list done
    15:57:30  ON THE CLOCK, pick 87 · plan #56 (0.0 s old) · lineup needs K DEF
    15:57:31  PICKED Wan'Dale Robinson (WR) via action, confirmed in 420 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +1.0 a week over the wire, about 7 points
  • top projection l
    15:57:33  pick 88  Tony Pollard (RB) taken by seat 8 in 2 s
    15:57:34  plan #57 for pick 89
  • Kenny Gainwell RB · insurance worth ~5 · 96% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 90% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    15:57:40  heartbeat sent (Yahoo told we are not idle)
    15:58:02  pick 89  Chris Godwin Jr. (WR) taken by seat 9 in 28 s — a target is gone
    15:58:11  plan #60 for pick 90
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 92% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    15:58:17  pick 90  Chuba Hubbard (RB) taken by seat 10 in 15 s
    15:58:23  plan #61 for pick 91
  • Patrick Mahomes II QB · insurance worth ~8 · 96% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 94% survives to ou
    15:58:41  heartbeat sent (Yahoo told we are not idle)
    15:58:45  pick 91  MarShawn Lloyd (RB) taken by seat 10 in 28 s
    15:58:46  pick 92  J.K. Dobbins (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    15:58:46  pick 93  Michael Wilson (WR) taken by seat 8 in 0 s INSTANTLY (autopick)
    15:58:47  plan #63 for pick 94
  • Patrick Mahomes II QB · insurance worth ~8 · 72% survives to our turn
  • Kenny Gainwell RB · insurance worth ~5 · 88% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 69% survives to ou
    15:58:47  ON THE CLOCK, pick 94 · plan #63 (0.0 s old) · lineup needs K DEF
    15:58:48  PICKED Patrick Mahomes II (QB) via action, confirmed in 427 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    15:58:50  pick 95  Josh Downs (WR) taken by seat 6 in 2 s
    15:58:50  pick 96  Jacory Croskey-Merritt (RB) taken by seat 5 in 0 s
    15:58:51  plan #64 for pick 97
  • Kenny Gainwell RB · insurance worth ~5 · 90% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 73% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    15:59:10  pick 97  Alec Pierce (WR) taken by seat 4 in 20 s — a target is gone
    15:59:17  plan #66 for pick 98
  • Kenny Gainwell RB · insurance worth ~5 · 91% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 75% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    15:59:32  pick 98  Quentin Johnston (WR) taken by seat 3 in 21 s — a target is gone
    15:59:38  pick 99  Courtland Sutton (WR) taken by seat 2 in 6 s — a target is gone (was 75% to survive)
    15:59:39  pick 100  Stefon Diggs (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    15:59:40  pick 101  Blake Corum (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    15:59:41  plan #68 for pick 102
  • Kenny Gainwell RB · insurance worth ~5 · 94% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~1 · 92% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    15:59:45  pick 102  Jordan Mason (RB) taken by seat 2 in 5 s
    15:59:45  heartbeat sent (Yahoo told we are not idle)
    15:59:54  plan #69 for pick 103
  • Kenny Gainwell RB · insurance worth ~5 · 93% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~1 · 94% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:00:05  pick 103  Matthew Stafford (QB) taken by seat 3 in 20 s
    16:00:06  plan #70 for pick 104
  • Kenny Gainwell RB · insurance worth ~5 · 95% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~1 · 96% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:00:27  pick 104  Kenny Gainwell (RB) taken by seat 4 in 22 s — a target is gone (was 95% to survive)
    16:00:28  pick 105  Brock Purdy (QB) taken by seat 5 in 1 s INSTANTLY (autopick)
    16:00:29  pick 106  Dalton Kincaid (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    16:00:30  plan #72 for pick 107
  • Aaron Jones Sr. RB · insurance worth ~2 · 96% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~1 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:00:30  ON THE CLOCK, pick 107 · plan #72 (0.0 s old) · lineup needs K DEF
    16:00:31  PICKED Aaron Jones Sr. (RB) via action, confirmed in 400 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +0.7 a week over the wire, about 2 points
  • top projection left 
    16:00:33  pick 108  Jaxson Dart (QB) taken by seat 8 in 2 s
    16:00:33  pick 109  Kyle Monangai (RB) taken by seat 9 in 0 s — a target is gone
    16:00:33  plan #73 for pick 110
  • Michael Pittman Jr. WR · insurance worth ~1 · 98% survives to our turn
  • Woody Marks RB · insurance worth ~0 · 98% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:00:46  heartbeat sent (Yahoo told we are not idle)
    16:01:01  pick 110  Travis Kelce (TE) taken by seat 10 in 28 s
    16:01:10  plan #76 for pick 111
  • Michael Pittman Jr. WR · insurance worth ~1 · 97% survives to our turn
  • Woody Marks RB · insurance worth ~0 · 99% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:01:14  pick 111  Mark Andrews (TE) taken by seat 10 in 13 s
    16:01:15  pick 112  Jordan Addison (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    16:01:15  pick 113  Dallas Goedert (TE) taken by seat 8 in 0 s INSTANTLY (autopick)
    16:01:16  plan #77 for pick 114
  • Michael Pittman Jr. WR · insurance worth ~1 · 92% survives to our turn
  • Woody Marks RB · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:01:16  ON THE CLOCK, pick 114 · plan #77 (0.0 s old) · lineup needs K DEF
    16:01:17  PICKED Michael Pittman Jr. (WR) via action, confirmed in 429 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +0.9 a week over the wire, about 1 points
  • top projecti
    16:01:19  pick 115  Josh Jacobs (RB) taken by seat 6 in 2 s
    16:01:19  pick 116  Isaiah Likely (TE) taken by seat 5 in 0 s
    16:01:20  plan #78 for pick 117
  • Woody Marks RB · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 94% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    16:01:35  pick 117  Xavier Worthy (WR) taken by seat 4 in 16 s
    16:01:41  pick 118  Brandon Aubrey (K) taken by seat 3 in 6 s
    16:01:45  plan #80 for pick 119
  • Woody Marks RB · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 95% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    16:01:46  pick 119  Matthew Golden (WR) taken by seat 2 in 5 s
    16:01:46  pick 120  Kyler Murray (QB) taken by seat 1 in 0 s INSTANTLY (autopick)
    16:01:47  pick 121  Juwan Johnson (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    16:01:47  heartbeat sent (Yahoo told we are not idle)
    16:01:50  pick 122  Makai Lemon (WR) taken by seat 2 in 4 s — a target is gone
    16:01:56  plan #81 for pick 123
  • Woody Marks RB · insurance worth ~0 · 97% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 96% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    16:02:04  pick 123  Texans (DEF) taken by seat 3 in 13 s
    16:02:09  plan #82 for pick 124
  • Woody Marks RB · insurance worth ~0 · 99% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 97% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    16:02:10  pick 124  Jason Myers (K) taken by seat 4 in 6 s
    16:02:11  pick 125  De'Zhaun Stribling (WR) taken by seat 5 in 1 s INSTANTLY (autopick)
    16:02:12  pick 126  KC Concepcion (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    16:02:12  plan #83 for pick 127
  • Woody Marks RB · insurance worth ~0 · 97% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 96% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    16:02:12  ON THE CLOCK, pick 127 · plan #83 (0.0 s old) · lineup needs K DEF
    16:02:13  PICKED Woody Marks (RB) via action, confirmed in 378 ms — lineup full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +0.4 a week over the wire, about 0 points
  • top projection left was Jare
    16:02:15  pick 128  Chris Rodriguez Jr. (RB) taken by seat 8 in 2 s
    16:02:15  pick 129  Ka'imi Fairbairn (K) taken by seat 9 in 0 s
    16:02:16  plan #84 for pick 130
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 41.9 (14 now + ~27.9 RB next) · 70% survives to our turn
  • Cam Little K · safe to wait · pick costs 11 · 93% survives to our turn
  • Seattle 
    16:02:21  pick 130  Jared Goff (QB) taken by seat 10 in 5 s
    16:02:28  plan #85 for pick 131
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 41.9 (14 now + ~27.9 RB next) · 68% survives to our turn
  • Cam Little K · safe to wait · pick costs 11 · 95% survives to our turn
  • Seattle 
    16:02:34  pick 131  Broncos (DEF) taken by seat 10 in 14 s
    16:02:34  pick 132  Keaton Mitchell (RB) taken by seat 9 in 0 s INSTANTLY (autopick)
    16:02:35  pick 133  Seahawks (DEF) taken by seat 8 in 1 s INSTANTLY (autopick)
    16:02:36  plan #86 for pick 134
  • Philadelphia Eagles DEF · wait costs 2 · pick costs 0, best pair 35.7 (8 now + ~27.7 RB next) · 20% survives to our turn
  • Cam Little K · wait costs 2 · pick costs 5 · 64% survives to our turn
  • Camer
    16:02:36  ON THE CLOCK, pick 134 · plan #86 (0.0 s old) · lineup needs K DEF
    16:02:37  PICKED Philadelphia Eagles (DEF) via action, confirmed in 313 ms — chose Philadelphia Eagles (DEF): waiting would likely cost about 2 points at DEF, 20% to still be there next turn
  • top projection left was Baker Mayfield, passe
    16:02:39  pick 135  Cameron Dicker (K) taken by seat 6 in 2 s — a target is gone
    16:02:39  pick 136  Vikings (DEF) taken by seat 5 in 0 s
    16:02:40  plan #87 for pick 137
  • Cam Little K · wait costs 2 · 31% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    16:02:45  pick 137  Dalton Schultz (TE) taken by seat 4 in 6 s
    16:02:47  heartbeat sent (Yahoo told we are not idle)
    16:02:53  plan #88 for pick 138
  • Cam Little K · wait costs 2 · 29% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    16:03:09  pick 138  Rachaad White (RB) taken by seat 3 in 24 s
    16:03:11  pick 139  Patriots (DEF) taken by seat 2 in 2 s INSTANTLY (autopick)
    16:03:11  pick 140  Jalen Coker (WR) taken by seat 1 in 0 s INSTANTLY (autopick)
    16:03:12  pick 141  Cam Little (K) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone (was 29% to survive)
    16:03:16  plan #90 for pick 142
  • Eddy Pineiro K · safe to wait · 88% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    16:03:16  pick 142  Trey Smack (K) taken by seat 2 in 4 s
    16:03:28  plan #91 for pick 143
  • Eddy Pineiro K · safe to wait · 90% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    16:03:37  pick 143  Jake Ferguson (TE) taken by seat 3 in 21 s
    16:03:40  pick 144  Ravens (DEF) taken by seat 4 in 3 s
    16:03:41  pick 145  Tyler Loop (K) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    16:03:41  plan #92 for pick 146
  • Eddy Pineiro K · safe to wait · 98% survives to our turn
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    16:03:42  pick 146  Jaguars (DEF) taken by seat 6 in 1 s INSTANTLY (autopick)
    16:03:42  plan #93 for pick 147
  • Eddy Pineiro K
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    16:03:42  ON THE CLOCK, pick 147 · plan #93 (0.0 s old) · lineup needs K
    16:03:43  PICKED Eddy Pineiro (K) via action, confirmed in 383 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Baker Mayfield, passed on purpose
    16:03:46  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    15:42:18 PT preflight: ok=true pick_path=action my_team=7 plan=plan 25 deep @pick 1 via store call#96
    15:42:18 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    15:42:18 PT NARR info driver started — seat 7, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    15:43:18 PT heartbeat: setAwayStatus(false)
    15:43:18 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:43:59 PT ON CLOCK -> {"drafted":"Jaxon Smith-Njigba","pos":"WR","vorp":89.4,"proj":231.5,"why":"waiting likely costs ~8 pts at WR (best option now 89, ~82 by your next turn) · 60% chance he's still there at your next pick · fills your op
    15:44:19 PT heartbeat: setAwayStatus(false)
    15:44:19 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:45:21 PT heartbeat: setAwayStatus(false)
    15:45:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:45:27 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~19 pts at RB (best option now 73, ~55 by your next turn) · 32% chance he's still there at your next pick · fills your open R
    15:46:22 PT heartbeat: setAwayStatus(false)
    15:46:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:47:00 PT PLAN bridge unreachable: TypeError: Failed to fetch
    15:47:23 PT heartbeat: setAwayStatus(false)
    15:47:23 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:48:06 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~7 pts at WR (best option now 40, ~33 by your next turn) · 23% chance he's still there at your next pick · fills your open WR s
    15:48:25 PT heartbeat: setAwayStatus(false)
    15:48:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:49:26 PT ON CLOCK -> {"drafted":"Travis Etienne Jr.","pos":"RB","vorp":26.3,"proj":186.5,"why":"waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 45% chance he's still there at your next pick · fills your op
    15:49:28 PT heartbeat: setAwayStatus(false)
    15:49:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:50:28 PT heartbeat: setAwayStatus(false)
    15:50:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:51:29 PT heartbeat: setAwayStatus(false)
    15:51:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:51:34 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 56% chance he's still there at your next pick · fills your open QB sl
    15:52:26 PT ON CLOCK -> {"drafted":"George Kittle","pos":"TE","vorp":19.8,"proj":142,"why":"safe to wait on TE · 85% chance he's still there at your next pick · fills your open TE slot · 12 teams picking before you still need a TE · two-pic
    15:52:34 PT heartbeat: setAwayStatus(false)
    15:52:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:53:37 PT heartbeat: setAwayStatus(false)
    15:53:37 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:54:39 PT heartbeat: setAwayStatus(false)
    15:54:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:54:50 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"safe to wait on your FLEX spot · 84% chance he's still there at your next pick · fills a FLEX slot","s":0.835,"sr":0.835,"e":6.2,"top_proj_av
    15:55:39 PT heartbeat: setAwayStatus(false)
    15:55:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:55:50 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 18 pts","s":0.932,"sr":0.932,"e":-5.5,"top_proj_
    15:56:39 PT heartbeat: setAwayStatus(false)
    15:56:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:57:31 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts","s":0.987,"sr":0.987,"e":-10.6,"top_proj
    15:57:40 PT heartbeat: setAwayStatus(false)
    15:57:40 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:58:41 PT heartbeat: setAwayStatus(false)
    15:58:41 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    15:58:48 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts","s":0.72,"sr":0.72,"e":10.5,"top_proj_av
    15:59:45 PT heartbeat: setAwayStatus(false)
    15:59:45 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:00:31 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +0.7/wk over the wire (Chris Rodriguez Jr.) ≈ 2 pts","s":
    16:00:46 PT heartbeat: setAwayStatus(false)
    16:00:46 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:01:17 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.9/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts","s"
    16:01:47 PT heartbeat: setAwayStatus(false)
    16:01:47 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:02:13 PT ON CLOCK -> {"drafted":"Woody Marks","pos":"RB","vorp":-30.3,"proj":129.9,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.4/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts","s":0.9
    16:02:37 PT ON CLOCK -> {"drafted":"Philadelphia Eagles","pos":"DEF","vorp":10,"proj":127,"why":"waiting likely costs ~2 pts at DEF (best option now 10, ~8 by your next turn) · 20% chance he's still there at your next pick · fills your open
    16:02:47 PT heartbeat: setAwayStatus(false)
    16:02:47 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:03:43 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    16:03:46 PT roster full
    16:03:46 PT NARR info roster full — driver done; posting the trail when the room finishes
    16:03:46 PT driver stop


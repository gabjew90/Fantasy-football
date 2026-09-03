# Scrutiny: Mock 41 -- Pump Fake II (room 10618261) -- Thursday 2026-09-03 16:42 PT -- 10 teams, our seat 9

Captured 2026-09-03 16:56:35 PT. Times below are Pacific. 10 teams, our team id 9, draft slot 9. 150 picks in the trail, 82 bridge plan calls, 65 recs events in the room log.

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
- Action latency to store confirmation: median 438 ms, min 312, max 761.
- Heartbeats 13; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (1): 1 drafted entries matched no board player: 148 Will Reichard.
- Away seats over the room (each change): {} -> {5,6} -> {5} -> {5,6,10} -> {5,10} -> {5,6,10} -> {2,5,6,10} -> {5,6,10} -> {2,5,6,10} -> {5,6,10} -> {2,5,6,10} -> {5,6,10} -> {5,6,8,10} -> {1,5,6,8,10} -> {1,4,5,6,8,10} -> {1,4,5,6,7,8,10} -> {1,2,4,5,6,7,8,10}.
- Managers away at the end: 1 tim, 2 Humza Usman, 4 joe, 5 Brenna, 6 Buford Brown, 7 Matthew, 8 Cameron, 10 Brent.

## Our picks, one block each

### Pick 9 (round 1): Jaxon Smith-Njigba (WR)

- In plain English: Took Jaxon Smith-Njigba (WR) because waiting would likely cost about 6 points at WR, with a 82% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 408 ms, ranker engine, plan call 10, plan age 898 ms, at 16:43:58 PT.
- Engine's reason: waiting likely costs ~6 pts at WR (best option now 89, ~84 by your next turn) · 82% chance he's still there at your next pick · fills your open WR slot · last WR at this level — big drop after him · 2 teams picking befor
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: De'Von Achane (RB, s=0.832, e=71.1); Trey McBride (TE, s=0.993, e=77.8); Josh Allen (QB, s=0.937, e=46).
- Plan call 10 @pick 9: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 8 drafted / 0 mine.
- Engine's first choice was **Jaxon Smith-Njigba** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaxon Smith-Njigba | WR | 89.4 | 0.82 | 0.82 | 83.6 | 89.4 | waiting likely costs ~6 pts at WR (best option now 89, ~84 by your next turn) · 82% chance |
| De'Von Achane | RB | 73.4 | 0.83 | 0.83 | 71.1 | 73.4 | waiting likely costs ~2 pts at RB (best option now 73, ~71 by your next turn) · 83% chance |
| Trey McBride | TE | 77.9 | 0.99 | 0.99 | 77.8 | 77.9 | safe to wait on TE · 99% chance he's still there at your next pick · fills your open TE sl |
| Josh Allen | QB | 47.0 | 0.94 | 0.94 | 46.0 | 47.0 | waiting likely costs ~1 pts at QB (best option now 47, ~46 by your next turn) · 94% chance |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 46.0 | 1.0 | 7 |
| RB | 73.4 | 71.1 | 2.3 | 22 |
| WR | 89.4 | 83.6 | 5.8 | 25 |
| TE | 77.9 | 77.8 | 0.1 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 72.9 | 0.5 | 53 |

### Pick 12 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 22 points at RB, with a 25% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 588 ms, ranker engine, plan call 11, plan age 1077 ms, at 16:44:02 PT.
- Engine's reason: waiting likely costs ~22 pts at RB (best option now 73, ~52 by your next turn) · 25% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 16 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.413, e=53.2); Justin Jefferson (WR, s=0.185, e=45.2); Josh Allen (QB, s=0.427, e=37.6).
- Plan call 11 @pick 12: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 10], state store with 11 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.25 | 0.25 | 51.7 | 73.4 | waiting likely costs ~22 pts at RB (best option now 73, ~52 by your next turn) · 25% chanc |
| Trey McBride | TE | 77.9 | 0.41 | 0.41 | 53.2 | 77.9 | waiting likely costs ~25 pts at TE (best option now 78, ~53 by your next turn) · 41% chanc |
| Justin Jefferson | WR | 53.9 | 0.18 | 0.18 | 45.2 | 53.9 | waiting likely costs ~9 pts at WR (best option now 54, ~45 by your next turn) · 18% chance |
| Josh Allen | QB | 47.0 | 0.43 | 0.43 | 37.6 | 47.0 | waiting likely costs ~9 pts at QB (best option now 47, ~38 by your next turn) · 43% chance |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 37.6 | 9.4 | 8 |
| RB | 73.4 | 51.7 | 21.7 | 21 |
| WR | 53.9 | 45.2 | 8.7 | 24 |
| TE | 77.9 | 53.2 | 24.7 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 52.4 | 21.0 | 52 |

### Pick 29 (round 3): Chris Olave (WR)

- In plain English: Took Chris Olave (WR) because waiting would likely cost about 5 points at WR, with a 34% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 388 ms, ranker engine, plan call 21, plan age 882 ms, at 16:45:57 PT.
- Engine's reason: waiting likely costs ~5 pts at WR (best option now 40, ~35 by your next turn) · 34% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Javonte Williams (RB, s=0.868, e=35.5); Drake Maye (QB, s=1, e=31.1); Tyler Warren (TE, s=1, e=23.8).
- Plan call 21 @pick 29: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 10], state store with 28 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.34 | 0.34 | 35.5 | 40.1 | waiting likely costs ~5 pts at WR (best option now 40, ~35 by your next turn) · 34% chance |
| Javonte Williams | RB | 36.9 | 0.87 | 0.87 | 35.5 | 36.9 | waiting likely costs ~1 pts at your FLEX spot (best option now 37, ~36 by your next turn)  |
| Drake Maye | QB | 31.1 | 1.00 | 1.00 | 31.1 | 31.1 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Tyler Warren | TE | 23.8 | 1.00 | 1.00 | 23.8 | 23.8 | safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE s |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 31.1 | 0.0 | 9 |
| RB | 36.9 | 35.5 | 1.4 | 18 |
| WR | 40.1 | 35.5 | 4.6 | 22 |
| TE | 23.8 | 23.8 | 0.0 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 35.5 | 1.4 | 47 |

### Pick 32 (round 4): Javonte Williams (RB)

- In plain English: Took Javonte Williams (RB) because waiting would likely cost about 11 points at RB, with a 31% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 438 ms, ranker engine, plan call 22, plan age 901 ms, at 16:46:01 PT.
- Engine's reason: waiting likely costs ~11 pts at RB (best option now 37, ~26 by your next turn) · 31% chance he's still there at your next pick · fills your open RB slot · 16 teams picking before you still need a RB · two-pick plan: pair
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.516, e=24.6); Tyler Warren (TE, s=0.497, e=22.4); Rashee Rice (WR, s=None, e=None).
- Plan call 22 @pick 32: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 10], state store with 31 drafted / 3 mine.
- Engine's first choice was **Javonte Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Javonte Williams | RB | 36.9 | 0.31 | 0.31 | 26.2 | 36.9 | waiting likely costs ~11 pts at RB (best option now 37, ~26 by your next turn) · 31% chanc |
| Drake Maye | QB | 31.1 | 0.52 | 0.52 | 24.6 | 31.1 | waiting likely costs ~7 pts at QB (best option now 31, ~25 by your next turn) · 52% chance |
| Tyler Warren | TE | 23.8 | 0.50 | 0.50 | 22.4 | 23.8 | waiting likely costs ~1 pts at TE (best option now 24, ~22 by your next turn) · 50% chance |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 24.6 | 6.5 | 10 |
| RB | 36.9 | 26.2 | 10.7 | 18 |
| WR | 34.1 | 24.3 | 9.8 | 20 |
| TE | 23.8 | 22.4 | 1.4 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 26.7 | 10.2 | 45 |

### Pick 49 (round 5): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (89% to survive, but nobody better was worth waiting for).
- Driver: via **action**, verified store, 365 ms, ranker engine, plan call 35, plan age 854 ms, at 16:48:31 PT.
- Engine's reason: safe to wait on QB · 89% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair with the ~43-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: George Kittle (TE, s=1, e=21.1); Jaylen Warren (RB, s=1, e=9.3); Kyle Pitts Sr. (TE, s=None, e=None).
- Plan call 35 @pick 49: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 10], state store with 48 drafted / 4 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.89 | 0.89 | 17.7 | 18.0 | safe to wait on QB · 89% chance he's still there at your next pick · fills your open QB sl |
| George Kittle | TE | 19.8 | 1.00 | 1.00 | 21.1 | 21.1 | safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE s |
| Jaylen Warren | RB | 9.3 | 1.00 | 1.00 | 9.3 | 9.3 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills a  |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Tucker Kraft | TE | 16.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.7 | 0.3 | 12 |
| RB | 9.3 | 9.3 | -0.0 | 18 |
| WR | 15.4 | 14.3 | 1.1 | 20 |
| TE | 21.1 | 21.1 | 0.0 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 46 |

### Pick 52 (round 6): George Kittle (TE)

- In plain English: Took George Kittle (TE) because waiting would likely cost about 2 points at TE, with a 72% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 396 ms, ranker engine, plan call 36, plan age 910 ms, at 16:48:35 PT.
- Engine's reason: waiting likely costs ~2 pts at TE (best option now 21, ~19 by your next turn) · 72% chance he's still there at your next pick · fills your open TE slot · 16 teams picking before you still need a TE · two-pick plan: pair 
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.676, e=8.2); Kyle Pitts Sr. (TE, s=None, e=None); Harold Fannin Jr. (TE, s=None, e=None).
- Plan call 36 @pick 52: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 10], state store with 51 drafted / 5 mine.
- Engine's first choice was **George Kittle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| George Kittle | TE | 19.8 | 0.72 | 0.72 | 19.4 | 21.1 | waiting likely costs ~2 pts at TE (best option now 21, ~19 by your next turn) · 72% chance |
| Jaylen Warren | RB | 9.3 | 0.68 | 0.68 | 8.2 | 9.3 | waiting likely costs ~1 pts at your FLEX spot (best option now 9, ~8 by your next turn) ·  |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Tucker Kraft | TE | 16.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Tetairoa McMillan | WR | 15.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.0 | 0.7 | 10 |
| RB | 9.3 | 8.1 | 1.2 | 17 |
| WR | 15.4 | 13.4 | 2.0 | 22 |
| TE | 21.1 | 19.4 | 1.7 | 9 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.2 | 1.2 | 48 |

### Pick 69 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (87% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 542 ms, ranker engine, plan call 46, plan age 1147 ms, at 16:50:26 PT.
- Engine's reason: safe to wait on your FLEX spot · 87% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 46 @pick 69: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 8, 10], state store with 68 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.87 | 0.87 | 9.0 | 9.3 | safe to wait on your FLEX spot · 87% chance he's still there at your next pick · fills a F |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.5 | 0.2 | 18 |
| RB | 9.3 | 9.0 | 0.3 | 27 |
| WR | 0.0 | -0.3 | 0.3 | 33 |
| TE | 21.1 | 15.7 | 5.4 | 17 |
| K | 13.5 | 13.5 | 0.0 | 6 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.0 | 0.3 | 77 |

### Pick 72 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +2.7 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 26 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 463 ms, ranker engine, plan call 47, plan age 1013 ms, at 16:50:31 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodriguez Jr.) ≈ 26 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Christian Watson (WR, s=0.119, e=-8.1); Rhamondre Stevenson (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None).
- Plan call 47 @pick 72: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 8, 10], state store with 71 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.46 | 0.46 | 0.3 | 7.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodri |
| Christian Watson | WR | -0.8 | 0.12 | 0.12 | -8.1 | -0.8 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.6/wk over the wire (Romeo Doubs |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.9 | 1.8 | 19 |
| RB | 7.2 | 0.3 | 6.9 | 34 |
| WR | -0.8 | -8.1 | 7.3 | 39 |
| TE | 13.8 | 12.7 | 1.1 | 19 |
| K | 13.5 | 13.4 | 0.1 | 9 |
| DEF | 18.0 | 17.9 | 0.1 | 7 |

### Pick 89 (round 9): DK Metcalf (WR)

- In plain English: Lineup already full, so DK Metcalf (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +1.1 points a week over the waiver wire (Romeo Doubs), worth about 7 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 471 ms, ranker engine, plan call 57, plan age 972 ms, at 16:52:17 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +1.1/wk over the wire (Romeo Doubs) ≈ 7 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: RJ Harvey (RB, s=0.977, e=-5.4); Kenny Gainwell (RB, s=None, e=None); Wan'Dale Robinson (WR, s=None, e=None).
- Plan call 57 @pick 89: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 8, 10], state store with 88 drafted / 8 mine.
- Engine's first choice was **DK Metcalf** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| DK Metcalf | WR | -9.2 | 0.40 | 0.40 | -10.0 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.1/wk over the wire (Romeo Doubs |
| RJ Harvey | RB | -5.4 | 0.98 | 0.98 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.2 | 0.5 | 18 |
| RB | -5.4 | -5.4 | 0.0 | 28 |
| WR | -9.2 | -10.0 | 0.8 | 38 |
| TE | 13.8 | 13.7 | 0.1 | 19 |
| K | 13.5 | 13.5 | 0.0 | 13 |
| DEF | 16.0 | 16.0 | 0.0 | 10 |

### Pick 92 (round 10): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Tyler Shough), worth about 8 points.
- Driver: via **action**, verified store, 405 ms, ranker engine, plan call 58, plan age 957 ms, at 16:52:22 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.743, e=-6.5); Wan'Dale Robinson (WR, s=0.931, e=-10.7); Matthew Stafford (QB, s=None, e=None).
- Plan call 58 @pick 92: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 8, 10], state store with 91 drafted / 9 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.64 | 0.64 | 9.4 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough |
| RJ Harvey | RB | -5.4 | 0.74 | 0.74 | -6.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9 |
| Wan'Dale Robinson | WR | -10.6 | 0.93 | 0.93 | -10.7 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 9.4 | 3.4 | 17 |
| RB | -5.4 | -6.5 | 1.1 | 28 |
| WR | -10.6 | -10.7 | 0.1 | 36 |
| TE | 13.8 | 11.5 | 2.3 | 19 |
| K | 13.5 | 13.5 | 0.0 | 14 |
| DEF | 16.0 | 15.9 | 0.1 | 10 |

### Pick 109 (round 11): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +1.9 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 5 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 426 ms, ranker engine, plan call 67, plan age 953 ms, at 16:54:04 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Wan'Dale Robinson (WR, s=0.998, e=-10.6); Kenny Gainwell (RB, s=None, e=None); Courtland Sutton (WR, s=None, e=None).
- Plan call 67 @pick 109: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8, 10], state store with 108 drafted / 10 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.96 | 0.96 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9 |
| Wan'Dale Robinson | WR | -10.6 | 1.00 | 1.00 | -10.6 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Alec Pierce | WR | -17.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 11 |
| RB | -5.4 | -5.4 | 0.0 | 23 |
| WR | -10.6 | -10.6 | 0.0 | 32 |
| TE | 13.8 | 13.7 | 0.1 | 18 |
| K | 12.0 | 12.0 | 0.0 | 14 |
| DEF | 16.0 | 16.0 | 0.0 | 13 |

### Pick 112 (round 12): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +1.0 points a week over the waiver wire (Romeo Doubs), worth about 1 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 761 ms, ranker engine, plan call 68, plan age 1295 ms, at 16:54:08 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 1 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.856, e=-9.1); Courtland Sutton (WR, s=None, e=None); Michael Pittman Jr. (WR, s=None, e=None).
- Plan call 68 @pick 112: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 6, 8, 10], state store with 111 drafted / 11 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.90 | 0.90 | -10.7 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Kenny Gainwell | RB | -6.2 | 0.86 | 0.86 | -9.1 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2. |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Alec Pierce | WR | -17.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.1 | 0.2 | 11 |
| RB | -6.2 | -9.1 | 2.9 | 21 |
| WR | -10.6 | -10.7 | 0.1 | 32 |
| TE | 10.9 | 10.6 | 0.3 | 17 |
| K | 12.0 | 10.4 | 1.6 | 15 |
| DEF | 16.0 | 12.6 | 3.4 | 13 |

### Pick 129 (round 13): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +1.0 points a week over the waiver wire (Tyjae Spears), worth about 0 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 561 ms, ranker engine, plan call 75, plan age 1244 ms, at 16:55:27 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1.0/wk over the wire (Tyjae Spears) ≈ 0 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.977, e=-21.6); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 75 @pick 129: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 4, 5, 6, 8, 10], state store with 128 drafted / 12 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.99 | 0.99 | -25.9 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |
| Jakobi Meyers | WR | -21.5 | 0.98 | 0.98 | -21.6 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Woody Marks | RB | -30.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 10 |
| RB | -25.9 | -25.9 | 0.0 | 19 |
| WR | -21.5 | -21.6 | 0.1 | 22 |
| TE | 0.5 | 0.5 | 0.0 | 13 |
| K | 12.0 | 11.8 | 0.2 | 17 |
| DEF | 16.0 | 16.0 | 0.0 | 13 |

### Pick 132 (round 14): Broncos (DEF)

- In plain English: Took Denver Broncos (DEF) because waiting would likely cost about 6 points at DEF, with a 4% chance he would still be there next turn. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 668 ms, ranker engine, plan call 76, plan age 1354 ms, at 16:55:31 PT.
- Engine's reason: waiting likely costs ~6 pts at DEF (best option now 16, ~10 by your next turn) · 4% chance he's still there at your next pick · fills your open DEF slot · TAKE-NOW ZONE: only 13 left before the DEF value drops, and 14 te
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cameron Dicker (K, s=0.579, e=10.2); Seattle Seahawks (DEF, s=None, e=None); Ka'imi Fairbairn (K, s=None, e=None).
- Plan call 76 @pick 132: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 4, 5, 6, 8, 10], state store with 131 drafted / 13 mine.
- Engine's first choice was **Denver Broncos** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Denver Broncos | DEF | 16.0 | 0.04 | 0.04 | 9.7 | 16.0 | waiting likely costs ~6 pts at DEF (best option now 16, ~10 by your next turn) · 4% chance |
| Cameron Dicker | K | 10.5 | 0.58 | 0.58 | 10.2 | 12.0 | waiting likely costs ~2 pts at K (best option now 12, ~10 by your next turn) · 58% chance  |
| Seattle Seahawks | DEF | 14.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Ka'imi Fairbairn | K | 12.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Philadelphia Eagles | DEF | 10.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Little | K | 9.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.1 | 0.2 | 10 |
| RB | -30.3 | -30.8 | 0.5 | 18 |
| WR | -21.5 | -22.4 | 0.9 | 21 |
| TE | 0.5 | 0.3 | 0.2 | 13 |
| K | 12.0 | 10.2 | 1.8 | 17 |
| DEF | 16.0 | 9.7 | 6.3 | 12 |

### Pick 149 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 312 ms, ranker engine, plan call 82, plan age 966 ms, at 16:56:33 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 82 @pick 149: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 4, 5, 6, 7, 8, 10], state store with 148 drafted / 14 mine, warnings ['1 drafted entries matched no board player: 148 Will Reichard'].
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
| 0-30% | 13 | 19% | 8% |
| 30-50% | 35 | 41% | 3% |
| 50-70% | 26 | 58% | 15% |
| 70-90% | 34 | 82% | 74% |
| 90-100% | 52 | 97% | 87% |

160 predictions over 64 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T16:56:32   WARNING plan #82: 1 drafted entries matched no board player: 148 Will Reichard

## Narration (what the panel showed live, Pacific time)

    16:42:21  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 25 · pick costs 0, best pair 320.5 (174.6 now + ~145.9 RB next) · 39% survives to our turn
  • Ja'Marr Chase WR · wait costs 16 · pick costs 39.7 · 44% survives to our tur
    16:42:22  driver started — seat 9, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    16:43:09  pick 1  Jahmyr Gibbs (RB) taken by tim (seat 1) — a target is gone
    16:43:11  pick 2  Bijan Robinson (RB) taken by Humza Usman (seat 2) in 2 s INSTANTLY (autopick) — a target is gone
    16:43:11  plan #6 for pick 2
  • Christian McCaffrey RB · wait costs 29 · pick costs 0, best pair 314.8 (174.6 now + ~140.2 RB next) · 43% survives to our turn
  • Ja'Marr Chase WR · wait costs 13 · pick costs 37.9 · 50% survives to our tur
    16:43:18  pick 3  Ja'Marr Chase (WR) taken by Judy (seat 3) in 7 s — a target is gone (was 50% to survive)
    16:43:22  heartbeat sent (Yahoo told we are not idle)
    16:43:23  plan #7 for pick 4
  • Christian McCaffrey RB · wait costs 30 · pick costs 0, best pair 299.3 (174.6 now + ~124.7 RB next) · 54% survives to our turn
  • Puka Nacua WR · wait costs 7 · pick costs 38.8 · 60% survives to our turn
  
    16:43:26  pick 4  Christian McCaffrey (RB) taken by joe (seat 4) in 7 s — a target is gone (was 54% to survive)
    16:43:27  pick 5  Puka Nacua (WR) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone (was 60% to survive)
    16:43:28  pick 6  Jonathan Taylor (RB) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick) — a target is gone
    16:43:33  pick 7  Amon-Ra St. Brown (WR) taken by Matthew (seat 7) in 5 s — a target is gone
    16:43:36  plan #8 for pick 8
  • Jaxon Smith-Njigba WR · wait costs 4 · pick costs 0, best pair 198.6 (105.5 now + ~93.1 RB next) · 87% survives to our turn
  • De'Von Achane RB · safe to wait · pick costs 3.6 · 93% survives to our turn
  •
    16:43:56  pick 8  James Cook III (RB) taken by Cameron (seat 8) in 24 s — a target is gone
    16:43:57  plan #10 for pick 9
  • Jaxon Smith-Njigba WR · wait costs 6 · pick costs 0, best pair 197 (105.5 now + ~91.5 RB next) · 82% survives to our turn
  • De'Von Achane RB · wait costs 2 · pick costs 3.4 · 83% survives to our turn
  • 
    16:43:57  ON THE CLOCK, pick 9 · plan #10 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    16:43:58  PICKED Jaxon Smith-Njigba (WR) via action, confirmed in 408 ms — chose Jaxon Smith-Njigba (WR): waiting would likely cost about 6 points at WR, 82% to still be there next turn
  • top projection left was Josh Allen, passed on purp
    16:44:00  pick 10  Saquon Barkley (RB) taken by Brent (seat 10) in 2 s
    16:44:00  pick 11  CeeDee Lamb (WR) taken by Brent (seat 10) in 0 s — a target is gone
    16:44:01  plan #11 for pick 12
  • De'Von Achane RB · wait costs 22 · pick costs 0, best pair 165.9 (93.8 now + ~72.1 RB next) · 25% survives to our turn
  • Trey McBride TE · wait costs 25 · pick costs 18.7 · 41% survives to our turn
  • J
    16:44:01  ON THE CLOCK, pick 12 · plan #11 (0.0 s old) · lineup needs QB RBx2 WR TE FLEX K DEF
    16:44:02  PICKED De'Von Achane (RB) via action, confirmed in 588 ms — chose De'Von Achane (RB): waiting would likely cost about 22 points at RB, 25% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    16:44:05  plan #12 for pick 13
  • Chase Brown RB · wait costs 18 · pick costs 0, best pair 145.4 (80.9 now + ~64.5 RB next) · 17% survives to our turn
  • Trey McBride TE · wait costs 27 · pick costs 7 · 38% survives to our turn
  • Justin
    16:44:17  pick 13  Chase Brown (RB) taken by Cameron (seat 8) in 15 s — a target is gone (was 17% to survive)
    16:44:20  plan #13 for pick 14
  • Justin Jefferson WR · wait costs 9 · pick costs 0, best pair 137.1 (70 now + ~67.1 WR next) · 19% survives to our turn
  • Trey McBride TE · wait costs 27 · pick costs 1.1 · 38% survives to our turn
  • De
    16:44:22  pick 14  Justin Jefferson (WR) taken by Matthew (seat 7) in 5 s — a target is gone (was 19% to survive)
    16:44:22  pick 15  Kenneth Walker III (RB) taken by Buford Brown (seat 6) in 0 s
    16:44:22  heartbeat sent (Yahoo told we are not idle)
    16:44:23  pick 16  Omarion Hampton (RB) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:44:28  pick 17  Derrick Henry (RB) taken by joe (seat 4) in 5 s — a target is gone (was 20% to survive)
    16:44:30  plan #14 for pick 18
  • Trey McBride TE · wait costs 25 · pick costs 0, best pair 135.2 (75.1 now + ~60.1 WR next) · 42% survives to our turn
  • Drake London WR · wait costs 7 · pick costs 8.3 · 36% survives to our turn
  • Kyre
    16:44:31  pick 18  Ashton Jeanty (RB) taken by Judy (seat 3) in 4 s
    16:44:38  pick 19  Brock Bowers (TE) taken by Humza Usman (seat 2) in 7 s — a target is gone
    16:44:42  plan #15 for pick 20
  • Trey McBride TE · wait costs 31 · pick costs 0, best pair 135.2 (75.1 now + ~60.1 WR next) · 43% survives to our turn
  • Drake London WR · wait costs 7 · pick costs 8.4 · 35% survives to our turn
  • Kyre
    16:44:51  pick 20  Nico Collins (WR) taken by tim (seat 1) in 12 s — a target is gone
    16:44:55  plan #16 for pick 21
  • Trey McBride TE · wait costs 25 · pick costs 0, best pair 134.1 (75.1 now + ~59.1 WR next) · 54% survives to our turn
  • Drake London WR · wait costs 8 · pick costs 7.3 · 26% survives to our turn
  • Kyre
    16:44:57  pick 21  A.J. Brown (WR) taken by tim (seat 1) in 7 s — a target is gone
    16:44:59  pick 22  Drake London (WR) taken by Humza Usman (seat 2) in 2 s INSTANTLY (autopick) — a target is gone (was 26% to survive)
    16:45:07  plan #17 for pick 23
  • Trey McBride TE · wait costs 23 · pick costs 0, best pair 133.7 (75.1 now + ~58.6 RB next) · 57% survives to our turn
  • Kyren Williams RB · wait costs 2 · pick costs 15.5 · 61% survives to our turn
  • C
    16:45:22  pick 23  Kyren Williams (RB) taken by Judy (seat 3) in 23 s — a target is gone (was 61% to survive)
    16:45:22  heartbeat sent (Yahoo told we are not idle)
    16:45:30  pick 24  Josh Allen (QB) taken by joe (seat 4) in 7 s — a target is gone (was 70% to survive)
    16:45:31  pick 25  George Pickens (WR) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone
    16:45:32  pick 26  Malik Nabers (WR) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick)
    16:45:32  plan #19 for pick 27
  • Trey McBride TE · wait costs 7 · pick costs 0, best pair 131.3 (75.1 now + ~56.2 RB next) · 87% survives to our turn
  • Javonte Williams RB · wait costs 1 · pick costs 6.2 · 89% survives to our turn
  • C
    16:45:35  pick 27  Trey McBride (TE) taken by Matthew (seat 7) in 4 s — a target is gone (was 87% to survive)
    16:45:44  plan #20 for pick 28
  • Chris Olave WR · safe to wait · pick costs 0, best pair 112.9 (56.2 now + ~56.7 RB next) · 90% survives to our turn
  • Javonte Williams RB · safe to wait · pick costs 0, best pair 113 (57.3 now + ~55.7 WR
    16:45:56  pick 28  DeVonta Smith (WR) taken by Cameron (seat 8) in 21 s
    16:45:56  plan #21 for pick 29
  • Chris Olave WR · wait costs 5 · pick costs 0, best pair 112.1 (56.2 now + ~55.9 RB next) · 34% survives to our turn
  • Javonte Williams RB · wait costs 1 · pick costs 3.1 · 87% survives to our turn
  • Dr
    16:45:56  ON THE CLOCK, pick 29 · plan #21 (0.0 s old) · lineup needs QB RB WR TE FLEX K DEF
    16:45:57  PICKED Chris Olave (WR) via action, confirmed in 388 ms — chose Chris Olave (WR): waiting would likely cost about 5 points at WR, 34% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    16:45:59  pick 30  Jeremiyah Love (RB) taken by Brent (seat 10) in 2 s
    16:45:59  pick 31  Tee Higgins (WR) taken by Brent (seat 10) in 0 s
    16:46:00  plan #22 for pick 32
  • Javonte Williams RB · wait costs 11 · pick costs 0, best pair 118.1 (57.3 now + ~60.8 WR next) · 31% survives to our turn
  • Drake Maye QB · wait costs 7 · pick costs 17 · 52% survives to our turn
  • Tyl
    16:46:00  ON THE CLOCK, pick 32 · plan #22 (0.0 s old) · lineup needs QB RB TE FLEX K DEF
    16:46:01  PICKED Javonte Williams (RB) via action, confirmed in 438 ms — chose Javonte Williams (RB): waiting would likely cost about 11 points at RB, 31% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    16:46:05  plan #23 for pick 33
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 95.6 (40.3 now + ~55.3 WR next) · 53% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 15 · 32% survives to our turn
  • Tyl
    16:46:23  heartbeat sent (Yahoo told we are not idle)
    16:46:28  pick 33  Rashee Rice (WR) taken by Cameron (seat 8) in 27 s — a target is gone
    16:46:30  plan #25 for pick 34
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 95.2 (40.3 now + ~54.9 WR next) · 54% survives to our turn
  • Travis Etienne Jr. RB · wait costs 6 · pick costs 14.5 · 34% survives to our turn
  • T
    16:46:45  pick 34  Breece Hall (RB) taken by Matthew (seat 7) in 17 s
    16:46:45  pick 35  Zay Flowers (WR) taken by Buford Brown (seat 6) in 0 s — a target is gone
    16:46:46  pick 36  Jaylen Waddle (WR) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:46:55  plan #27 for pick 37
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 96.2 (40.3 now + ~55.9 WR next) · 55% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 15.3 · 37% survives to our turn
  • T
    16:47:02  pick 37  Colston Loveland (TE) taken by joe (seat 4) in 16 s
    16:47:07  plan #28 for pick 38
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 95.7 (40.3 now + ~55.4 WR next) · 56% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 14.7 · 28% survives to our turn
  • T
    16:47:12  pick 38  Garrett Wilson (WR) taken by Judy (seat 3) in 10 s — a target is gone
    16:47:15  pick 39  Travis Etienne Jr. (RB) taken by Humza Usman (seat 2) in 4 s — a target is gone (was 28% to survive)
    16:47:20  plan #29 for pick 40
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 92.7 (40.3 now + ~52.5 WR next) · 58% survives to our turn
  • Cam Skattebo RB · wait costs 8 · pick costs 11.9 · 45% survives to our turn
  • Tyler W
    16:47:23  heartbeat sent (Yahoo told we are not idle)
    16:47:31  pick 40  David Montgomery (RB) taken by tim (seat 1) in 16 s
    16:47:32  plan #30 for pick 41
  • Drake Maye QB · wait costs 4 · pick costs 0, best pair 93.9 (40.3 now + ~53.6 WR next) · 69% survives to our turn
  • Cam Skattebo RB · wait costs 6 · pick costs 11.6 · 50% survives to our turn
  • Tyler W
    16:47:38  pick 41  Drake Maye (QB) taken by tim (seat 1) in 6 s — a target is gone (was 69% to survive)
    16:47:41  pick 42  Ladd McConkey (WR) taken by Humza Usman (seat 2) in 4 s
    16:47:44  plan #31 for pick 43
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 82.5 (27.2 now + ~55.3 WR next) · 86% survives to our turn
  • Tyler Warren TE · safe to wait · pick costs 6.3 · 71% survives to our turn
  • Cam Ska
    16:47:44  pick 43  Tyler Warren (TE) taken by Judy (seat 3) in 3 s — a target is gone (was 71% to survive)
    16:47:57  plan #32 for pick 44
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 83.1 (27.2 now + ~55.9 WR next) · 86% survives to our turn
  • Cam Skattebo RB · wait costs 4 · pick costs 10.1 · 65% survives to our turn
  • George
    16:48:03  pick 44  DJ Moore (WR) taken by joe (seat 4) in 18 s
    16:48:04  pick 45  D'Andre Swift (RB) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone
    16:48:05  pick 46  Cam Skattebo (RB) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick) — a target is gone (was 65% to survive)
    16:48:09  plan #33 for pick 47
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 70.6 (27.2 now + ~43.4 WR next) · 94% survives to our turn
  • George Kittle TE · safe to wait · pick costs 10.3 · 100% survives to our turn
  • Jayl
    16:48:09  pick 47  Lamar Jackson (QB) taken by Matthew (seat 7) in 5 s
    16:48:22  plan #34 for pick 48
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 70.6 (27.2 now + ~43.4 WR next) · 96% survives to our turn
  • George Kittle TE · safe to wait · pick costs 10.3 · 100% survives to our turn
  • Jayl
    16:48:24  heartbeat sent (Yahoo told we are not idle)
    16:48:29  pick 48  Emeka Egbuka (WR) taken by Cameron (seat 8) in 20 s
    16:48:30  plan #35 for pick 49
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 70.6 (27.2 now + ~43.4 WR next) · 89% survives to our turn
  • George Kittle TE · safe to wait · pick costs 10.3 · 100% survives to our turn
  • Jayl
    16:48:30  ON THE CLOCK, pick 49 · plan #35 (0.0 s old) · lineup needs QB TE FLEX K DEF
    16:48:31  PICKED Jalen Hurts (QB) via action, confirmed in 365 ms — chose Jalen Hurts (QB): nothing urgent, the most valuable player who fills a slot (89% to survive, nobody better worth waiting for)
    16:48:33  pick 50  Bucky Irving (RB) taken by Brent (seat 10) in 2 s
    16:48:33  pick 51  Joe Burrow (QB) taken by Brent (seat 10) in 0 s
    16:48:34  plan #36 for pick 52
  • George Kittle TE · wait costs 2 · pick costs 0, best pair 59.2 (16.9 now + ~42.3 WR next) · 72% survives to our turn
  • Jaylen Warren RB · wait costs 1 · pick costs 11.7 · 68% survives to our turn
  • Kyl
    16:48:34  ON THE CLOCK, pick 52 · plan #36 (0.0 s old) · lineup needs TE FLEX K DEF
    16:48:35  PICKED George Kittle (TE) via action, confirmed in 396 ms — chose George Kittle (TE): waiting would likely cost about 2 points at TE, 72% to still be there next turn
  • top projection left was Trevor Lawrence, passed on purpose
    16:48:39  plan #37 for pick 53
  • Jaylen Warren RB · wait costs 1 · 70% survives to our turn
  • Tetairoa McMillan WR · depth fallback, engine list done
  • Davante Adams WR · depth fallback, engine list done
    16:48:59  pick 53  Terry McLaurin (WR) taken by Cameron (seat 8) in 23 s — a target is gone
    16:49:03  plan #39 for pick 54
  • Jaylen Warren RB · wait costs 1 · 71% survives to our turn
  • Tetairoa McMillan WR · depth fallback, engine list done
  • Davante Adams WR · depth fallback, engine list done
    16:49:10  pick 54  Bhayshul Tuten (RB) taken by Matthew (seat 7) in 11 s
    16:49:10  pick 55  Jayden Daniels (QB) taken by Buford Brown (seat 6) in 0 s INSTANTLY (autopick)
    16:49:12  pick 56  Tucker Kraft (TE) taken by Brenna (seat 5) in 2 s INSTANTLY (autopick)
    16:49:15  plan #40 for pick 57
  • Jaylen Warren RB · safe to wait · 71% survives to our turn
  • Tetairoa McMillan WR · depth fallback, engine list done
  • Davante Adams WR · depth fallback, engine list done
    16:49:16  pick 57  Tetairoa McMillan (WR) taken by joe (seat 4) in 5 s — a target is gone
    16:49:23  pick 58  Caleb Williams (QB) taken by Judy (seat 3) in 6 s
    16:49:25  heartbeat sent (Yahoo told we are not idle)
    16:49:29  plan #41 for pick 59
  • Jaylen Warren RB · safe to wait · 75% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    16:49:29  pick 59  Quinshon Judkins (RB) taken by Humza Usman (seat 2) in 6 s — a target is gone
    16:49:41  plan #42 for pick 60
  • Jaylen Warren RB · safe to wait · 77% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    16:49:42  pick 60  Harold Fannin Jr. (TE) taken by tim (seat 1) in 14 s
    16:49:53  plan #43 for pick 61
  • Jaylen Warren RB · safe to wait · 77% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    16:49:54  pick 61  Rome Odunze (WR) taken by tim (seat 1) in 12 s — a target is gone
    16:49:58  pick 62  Davante Adams (WR) taken by Humza Usman (seat 2) in 4 s — a target is gone
    16:50:04  pick 63  Luther Burden III (WR) taken by Judy (seat 3) in 6 s
    16:50:06  plan #44 for pick 64
  • Jaylen Warren RB · safe to wait · 86% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    16:50:20  pick 64  Mike Evans (WR) taken by joe (seat 4) in 16 s — a target is gone
    16:50:21  pick 65  Justin Herbert (QB) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:50:22  pick 66  Sam LaPorta (TE) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick)
    16:50:24  pick 67  Jadarian Price (RB) taken by Matthew (seat 7) in 2 s INSTANTLY (autopick)
    16:50:24  pick 68  Dak Prescott (QB) taken by Cameron (seat 8) in 0 s INSTANTLY (autopick)
    16:50:25  plan #46 for pick 69
  • Jaylen Warren RB · safe to wait · 87% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    16:50:25  ON THE CLOCK, pick 69 · plan #46 (0.0 s old) · lineup needs FLEX K DEF
    16:50:26  PICKED Jaylen Warren (RB) via action, confirmed in 542 ms — chose Jaylen Warren (RB): nothing urgent, the most valuable player who fills a slot (87% to survive, nobody better worth waiting for)
  • top projection left was Trevor L
    16:50:28  pick 70  Kyle Pitts Sr. (TE) taken by Brent (seat 10) in 2 s
    16:50:28  pick 71  Jameson Williams (WR) taken by Brent (seat 10) in 0 s — a target is gone
    16:50:28  heartbeat sent (Yahoo told we are not idle)
    16:50:30  plan #47 for pick 72
  • Rico Dowdle RB · insurance worth ~26 · 46% survives to our turn
  • Christian Watson WR · insurance worth ~10 · 12% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
    16:50:30  ON THE CLOCK, pick 72 · plan #47 (0.0 s old) · lineup needs K DEF
    16:50:31  PICKED Rico Dowdle (RB) via action, confirmed in 463 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +2.7 a week over the wire, about 26 points
  • he also backs up one of our
    16:50:34  pick 73  Bo Nix (QB) taken by Cameron (seat 8) in 2 s
    16:50:36  plan #48 for pick 74
  • Christian Watson WR · insurance worth ~10 · 14% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 32% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    16:50:54  pick 74  Brian Thomas Jr. (WR) taken by Matthew (seat 7) in 20 s
    16:50:55  pick 75  Christian Watson (WR) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick) — a target is gone (was 14% to survive)
    16:50:55  pick 76  Parker Washington (WR) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone
    16:50:59  plan #50 for pick 77
  • DK Metcalf WR · insurance worth ~7 · 46% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 27% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    16:51:11  pick 77  Marvin Harrison Jr. (WR) taken by joe (seat 4) in 16 s — a target is gone
    16:51:23  plan #52 for pick 78
  • DK Metcalf WR · insurance worth ~7 · 52% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 26% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    16:51:24  pick 78  Rhamondre Stevenson (RB) taken by Judy (seat 3) in 13 s — a target is gone (was 26% to survive)
    16:51:27  pick 79  TreVeyon Henderson (RB) taken by Humza Usman (seat 2) in 3 s — a target is gone
    16:51:29  heartbeat sent (Yahoo told we are not idle)
    16:51:35  plan #53 for pick 80
  • DK Metcalf WR · insurance worth ~7 · 53% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 88% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:51:40  pick 80  Tony Pollard (RB) taken by tim (seat 1) in 13 s
    16:51:42  pick 81  MarShawn Lloyd (RB) taken by tim (seat 1) in 2 s INSTANTLY (autopick)
    16:51:44  pick 82  Michael Wilson (WR) taken by Humza Usman (seat 2) in 3 s — a target is gone
    16:51:47  pick 83  Texans (DEF) taken by Judy (seat 3) in 3 s
    16:51:48  plan #54 for pick 84
  • DK Metcalf WR · insurance worth ~7 · 75% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 95% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:52:01  pick 84  De'Zhaun Stribling (WR) taken by joe (seat 4) in 14 s
    16:52:01  pick 85  Carnell Tate (WR) taken by Brenna (seat 5) in 0 s INSTANTLY (autopick) — a target is gone
    16:52:02  pick 86  Jonathon Brooks (RB) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick)
    16:52:12  plan #56 for pick 87
  • DK Metcalf WR · insurance worth ~7 · 88% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 98% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:52:15  pick 87  Blake Corum (RB) taken by Matthew (seat 7) in 13 s
    16:52:16  pick 88  J.K. Dobbins (RB) taken by Cameron (seat 8) in 1 s INSTANTLY (autopick)
    16:52:16  plan #57 for pick 89
  • DK Metcalf WR · insurance worth ~7 · 40% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 98% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:52:16  ON THE CLOCK, pick 89 · plan #57 (0.0 s old) · lineup needs K DEF
    16:52:17  PICKED DK Metcalf (WR) via action, confirmed in 471 ms — lineup full, so DK Metcalf (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +1.1 a week over the wire, about 7 points
  • top projection left was Trevor
    16:52:19  pick 90  Trevor Lawrence (QB) taken by Brent (seat 10) in 2 s
    16:52:19  pick 91  Chris Godwin Jr. (WR) taken by Brent (seat 10) in 0 s — a target is gone
    16:52:21  plan #58 for pick 92
  • Patrick Mahomes II QB · insurance worth ~8 · 64% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 74% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 93% survives to our tu
    16:52:21  ON THE CLOCK, pick 92 · plan #58 (0.0 s old) · lineup needs K DEF
    16:52:22  PICKED Patrick Mahomes II (QB) via action, confirmed in 405 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    16:52:24  pick 93  Dalton Kincaid (TE) taken by Cameron (seat 8) in 2 s
    16:52:25  plan #59 for pick 94
  • RJ Harvey RB · insurance worth ~5 · 75% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 93% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:52:30  heartbeat sent (Yahoo told we are not idle)
    16:52:31  pick 94  Jared Goff (QB) taken by Matthew (seat 7) in 7 s
    16:52:32  pick 95  Josh Downs (WR) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick)
    16:52:32  pick 96  Chuba Hubbard (RB) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:52:38  plan #60 for pick 97
  • RJ Harvey RB · insurance worth ~5 · 79% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 93% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:52:59  pick 97  Quentin Johnston (WR) taken by joe (seat 4) in 27 s — a target is gone
    16:53:02  plan #62 for pick 98
  • RJ Harvey RB · insurance worth ~5 · 79% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 94% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:53:04  pick 98  Jacory Croskey-Merritt (RB) taken by Judy (seat 3) in 5 s
    16:53:06  pick 99  Jordan Mason (RB) taken by Humza Usman (seat 2) in 2 s INSTANTLY (autopick)
    16:53:15  plan #63 for pick 100
  • RJ Harvey RB · insurance worth ~5 · 79% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 94% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:53:15  pick 100  Stefon Diggs (WR) taken by tim (seat 1) in 9 s — a target is gone
    16:53:24  pick 101  Matthew Stafford (QB) taken by tim (seat 1) in 9 s
    16:53:26  pick 102  Jaxson Dart (QB) taken by Humza Usman (seat 2) in 2 s INSTANTLY (autopick)
    16:53:27  plan #64 for pick 103
  • RJ Harvey RB · insurance worth ~5 · 86% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 97% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:53:28  pick 103  Brandon Aubrey (K) taken by Judy (seat 3) in 2 s INSTANTLY (autopick)
    16:53:30  heartbeat sent (Yahoo told we are not idle)
    16:53:39  plan #65 for pick 104
  • RJ Harvey RB · insurance worth ~5 · 90% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 97% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:53:51  pick 104  Jordan Addison (WR) taken by joe (seat 4) in 23 s — a target is gone
    16:53:51  pick 105  Brock Purdy (QB) taken by Brenna (seat 5) in 0 s INSTANTLY (autopick)
    16:53:52  plan #66 for pick 106
  • RJ Harvey RB · insurance worth ~5 · 94% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 99% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:53:53  pick 106  Kyler Murray (QB) taken by Buford Brown (seat 6) in 2 s INSTANTLY (autopick)
    16:54:02  pick 107  Josh Jacobs (RB) taken by Matthew (seat 7) in 9 s
    16:54:03  pick 108  Kyle Monangai (RB) taken by Cameron (seat 8) in 1 s INSTANTLY (autopick)
    16:54:03  plan #67 for pick 109
  • RJ Harvey RB · insurance worth ~5 · 96% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~1 · 100% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    16:54:03  ON THE CLOCK, pick 109 · plan #67 (0.0 s old) · lineup needs K DEF
    16:54:04  PICKED RJ Harvey (RB) via action, confirmed in 426 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +1.9 a week over the wire, about 5 points
  • top projection left was Baker Ma
    16:54:04  pick 110  Chris Rodriguez Jr. (RB) taken by Brent (seat 10) in 1 s INSTANTLY (autopick)
    16:54:06  pick 111  Dallas Goedert (TE) taken by Brent (seat 10) in 2 s INSTANTLY (autopick)
    16:54:07  plan #68 for pick 112
  • Wan'Dale Robinson WR · insurance worth ~1 · 90% survives to our turn
  • Kenny Gainwell RB · insurance worth ~1 · 86% survives to our turn
  • Courtland Sutton WR · depth fallback, engine list done
    16:54:07  ON THE CLOCK, pick 112 · plan #68 (0.0 s old) · lineup needs K DEF
    16:54:08  pick 113  Travis Kelce (TE) taken by Cameron (seat 8) in 0 s INSTANTLY (autopick)
    16:54:08  PICKED Wan'Dale Robinson (WR) via action, confirmed in 761 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +1.0 a week over the wire, about 1 points
  • top projection l
    16:54:12  plan #69 for pick 114
  • Kenny Gainwell RB · insurance worth ~1 · 89% survives to our turn
  • Courtland Sutton WR · insurance worth ~0 · 94% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:54:14  pick 114  Kenny Gainwell (RB) taken by Matthew (seat 7) in 6 s — a target is gone (was 89% to survive)
    16:54:14  pick 115  Isaiah Likely (TE) taken by Buford Brown (seat 6) in 0 s INSTANTLY (autopick)
    16:54:15  pick 116  Mark Andrews (TE) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:54:20  pick 117  Alec Pierce (WR) taken by joe (seat 4) in 4 s — a target is gone
    16:54:24  plan #70 for pick 118
  • Aaron Jones Sr. RB · insurance worth ~0 · 92% survives to our turn
  • Courtland Sutton WR · insurance worth ~0 · 96% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:54:31  heartbeat sent (Yahoo told we are not idle)
    16:54:32  pick 118  Jayden Reed (WR) taken by Judy (seat 3) in 13 s — a target is gone
    16:54:35  pick 119  KC Concepcion (WR) taken by Humza Usman (seat 2) in 3 s
    16:54:36  pick 120  Juwan Johnson (TE) taken by tim (seat 1) in 1 s INSTANTLY (autopick)
    16:54:37  plan #71 for pick 121
  • Aaron Jones Sr. RB · insurance worth ~0 · 96% survives to our turn
  • Courtland Sutton WR · insurance worth ~0 · 97% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    16:54:38  pick 121  Courtland Sutton (WR) taken by tim (seat 1) in 2 s INSTANTLY (autopick) — a target is gone (was 97% to survive)
    16:54:41  pick 122  Matthew Golden (WR) taken by Humza Usman (seat 2) in 4 s
    16:54:49  plan #72 for pick 123
  • Aaron Jones Sr. RB · insurance worth ~0 · 96% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:54:51  pick 123  Makai Lemon (WR) taken by Judy (seat 3) in 10 s — a target is gone
    16:55:01  plan #73 for pick 124
  • Aaron Jones Sr. RB · insurance worth ~0 · 97% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 97% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    16:55:22  pick 124  Rachaad White (RB) taken by joe (seat 4) in 30 s
    16:55:22  pick 125  Michael Pittman Jr. (WR) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone (was 97% to survive)
    16:55:23  pick 126  Jalen Coker (WR) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick)
    16:55:25  pick 127  Rashid Shaheed (WR) taken by Matthew (seat 7) in 2 s INSTANTLY (autopick)
    16:55:25  pick 128  Jordan Love (QB) taken by Cameron (seat 8) in 0 s INSTANTLY (autopick)
    16:55:25  plan #75 for pick 129
  • Aaron Jones Sr. RB · insurance worth ~0 · 99% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 98% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    16:55:25  ON THE CLOCK, pick 129 · plan #75 (0.0 s old) · lineup needs K DEF
    16:55:27  PICKED Aaron Jones Sr. (RB) via action, confirmed in 561 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +1.0 a week over the wire, about 0 points
  • top projection left 
    16:55:29  pick 130  Romeo Doubs (WR) taken by Brent (seat 10) in 2 s — a target is gone
    16:55:29  pick 131  Rams (DEF) taken by Brent (seat 10) in 0 s
    16:55:30  plan #76 for pick 132
  • Denver Broncos DEF · wait costs 6 · pick costs 0, best pair 91.7 (14 now + ~77.7 RB next) · 4% survives to our turn
  • Cameron Dicker K · wait costs 2 · pick costs 9.5 · 58% survives to our turn
  • Seat
    16:55:30  ON THE CLOCK, pick 132 · plan #76 (0.0 s old) · lineup needs K DEF
    16:55:31  pick 133  Seahawks (DEF) taken by Cameron (seat 8) in 0 s INSTANTLY (autopick)
    16:55:31  PICKED Denver Broncos (DEF) via action, confirmed in 668 ms — chose Denver Broncos (DEF): waiting would likely cost about 6 points at DEF, 4% to still be there next turn
  • top projection left was Baker Mayfield, passed on purpos
    16:55:34  heartbeat sent (Yahoo told we are not idle)
    16:55:35  plan #77 for pick 134
  • Cameron Dicker K · wait costs 3 · 34% survives to our turn
  • Ka'imi Fairbairn K · depth fallback, engine list done
  • Cam Little K · depth fallback, engine list done
    16:56:01  pick 134  Ka'imi Fairbairn (K) taken by Matthew (seat 7) in 30 s — a target is gone
    16:56:03  pick 135  Eagles (DEF) taken by Buford Brown (seat 6) in 2 s INSTANTLY (autopick)
    16:56:04  pick 136  Cameron Dicker (K) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick) — a target is gone (was 34% to survive)
    16:56:05  pick 137  Jason Myers (K) taken by joe (seat 4) in 1 s INSTANTLY (autopick) — a target is gone
    16:56:08  pick 138  Jakobi Meyers (WR) taken by Judy (seat 3) in 4 s
    16:56:12  plan #80 for pick 139
  • Cam Little K · wait costs 2 · 33% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    16:56:12  pick 139  Harrison Mevis (K) taken by Humza Usman (seat 2) in 4 s
    16:56:15  pick 140  Vikings (DEF) taken by tim (seat 1) in 3 s
    16:56:15  pick 141  Cam Little (K) taken by tim (seat 1) in 0 s — a target is gone (was 33% to survive)
    16:56:15  pick 142  Patriots (DEF) taken by Humza Usman (seat 2) in 1 s INSTANTLY (autopick)
    16:56:24  plan #81 for pick 143
  • Eddy Pineiro K · safe to wait · 88% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    16:56:27  pick 143  Keaton Mitchell (RB) taken by Judy (seat 3) in 12 s
    16:56:27  pick 144  Jaguars (DEF) taken by joe (seat 4) in 0 s
    16:56:28  pick 145  Steelers (DEF) taken by Brenna (seat 5) in 1 s INSTANTLY (autopick)
    16:56:29  pick 146  Tyler Loop (K) taken by Buford Brown (seat 6) in 1 s INSTANTLY (autopick) — a target is gone
    16:56:31  pick 147  Ravens (DEF) taken by Matthew (seat 7) in 2 s INSTANTLY (autopick)
    16:56:32  pick 148  Will Reichard (K) taken by Cameron (seat 8) in 1 s INSTANTLY (autopick)
    16:56:32  plan #82 for pick 149
  • Eddy Pineiro K
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    16:56:32  bridge warning: 1 drafted entries matched no board player: 148 Will Reichard
    16:56:32  ON THE CLOCK, pick 149 · plan #82 (0.0 s old) · lineup needs K
    16:56:33  PICKED Eddy Pineiro (K) via action, confirmed in 312 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Baker Mayfield, passed on purpose
    16:56:35  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    16:42:22 PT preflight: ok=true pick_path=action my_team=9 plan=plan 25 deep @pick 1 via store call#1
    16:42:22 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    16:42:22 PT NARR info driver started — seat 9, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    16:43:22 PT heartbeat: setAwayStatus(false)
    16:43:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:43:58 PT ON CLOCK -> {"drafted":"Jaxon Smith-Njigba","pos":"WR","vorp":89.4,"proj":231.5,"why":"waiting likely costs ~6 pts at WR (best option now 89, ~84 by your next turn) · 82% chance he's still there at your next pick · fills your op
    16:44:02 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~22 pts at RB (best option now 73, ~52 by your next turn) · 25% chance he's still there at your next pick · fills your open R
    16:44:22 PT heartbeat: setAwayStatus(false)
    16:44:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:45:22 PT heartbeat: setAwayStatus(false)
    16:45:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:45:57 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~5 pts at WR (best option now 40, ~35 by your next turn) · 34% chance he's still there at your next pick · fills your open WR s
    16:46:01 PT ON CLOCK -> {"drafted":"Javonte Williams","pos":"RB","vorp":36.9,"proj":197.1,"why":"waiting likely costs ~11 pts at RB (best option now 37, ~26 by your next turn) · 31% chance he's still there at your next pick · fills your ope
    16:46:23 PT heartbeat: setAwayStatus(false)
    16:46:23 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:47:23 PT heartbeat: setAwayStatus(false)
    16:47:23 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:48:24 PT heartbeat: setAwayStatus(false)
    16:48:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:48:31 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 89% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick p
    16:48:35 PT ON CLOCK -> {"drafted":"George Kittle","pos":"TE","vorp":19.8,"proj":142,"why":"waiting likely costs ~2 pts at TE (best option now 21, ~19 by your next turn) · 72% chance he's still there at your next pick · fills your open TE s
    16:49:25 PT heartbeat: setAwayStatus(false)
    16:49:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:50:26 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on your FLEX spot · 87% chance he's still there at your next pick · fills a FLEX slot","s":0.873,"sr":0.873,"e":9,"top_proj_available"
    16:50:28 PT heartbeat: setAwayStatus(false)
    16:50:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:50:31 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodriguez Jr.) ≈ 26 pts · HANDCUFF: backs up your Jaylen Warren"
    16:51:29 PT heartbeat: setAwayStatus(false)
    16:51:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:52:17 PT ON CLOCK -> {"drafted":"DK Metcalf","pos":"WR","vorp":-9.2,"proj":132.9,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +1.1/wk over the wire (Romeo Doubs) ≈ 7 pts","s":0.395,"sr":0.395,"e":-10,"top_proj_available
    16:52:22 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts","s":0.638,"sr":0.638,"e":9.4,"top_proj_a
    16:52:30 PT heartbeat: setAwayStatus(false)
    16:52:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:53:30 PT heartbeat: setAwayStatus(false)
    16:53:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:54:04 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts","s":0.959,"
    16:54:08 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 1 pts","s":0.895,
    16:54:31 PT heartbeat: setAwayStatus(false)
    16:54:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:55:27 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1.0/wk over the wire (Tyjae Spears) ≈ 0 pts","s":0.991,
    16:55:31 PT ON CLOCK -> {"drafted":"Denver Broncos","pos":"DEF","vorp":16,"proj":133,"why":"waiting likely costs ~6 pts at DEF (best option now 16, ~10 by your next turn) · 4% chance he's still there at your next pick · fills your open DEF 
    16:55:34 PT heartbeat: setAwayStatus(false)
    16:55:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    16:56:32 PT BRIDGE WARNING: 1 drafted entries matched no board player: 148 Will Reichard
    16:56:33 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    16:56:35 PT roster full
    16:56:35 PT NARR info roster full — driver done; posting the trail when the room finishes
    16:56:35 PT driver stop


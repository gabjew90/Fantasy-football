# Scrutiny: Mock 26 -- First and Ten (room 10534350) -- Wednesday 2026-09-02 23:18 PT -- 10 teams, our seat 6

Captured 2026-09-02 23:38:27 PT. Times below are Pacific. 10 teams, our team id 6, draft slot 6. 150 picks in the trail, 110 bridge plan calls, 85 recs events in the room log.

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
- Action latency to store confirmation: median 451 ms, min 346, max 1156.
- Heartbeats 5; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {1} -> {} -> {7} -> {1,7} -> {7} -> {} -> {7} -> {} -> {1,2} -> {1} -> {7} -> {1,7} -> {7} -> {1,7} -> {7} -> {1,7} -> {7} -> {1,7} -> {1,2,7} -> {7} -> {2,7} -> {7} -> {7,8} -> {1,2,7,8} -> {1,2,3,7,8} -> {1,3,7,8} -> {1,2,3,7,8} -> {1,3,7,8} -> {3,7,8} -> {2,3,7,8} -> {3,7,8} -> {1,3,7,8} -> {3,7,8} -> {1,3,7,8} -> {1,3,7} -> {1,2,3,7} -> {1,3,7} -> {1,3,7,8}.
- Managers away at the end: 1 Preston, 3 Timothy, 7 kxsarai, 8 Danimal.

## Our picks, one block each

### Pick 6 (round 1): Puka Nacua (WR)

- In plain English: Took Puka Nacua (WR) because waiting would likely cost about 8 points at WR, with a 59% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 422 ms, ranker engine, plan call 27, plan age 733 ms, at 23:18:29 PT.
- Engine's reason: waiting likely costs ~8 pts at WR (best option now 100, ~92 by your next turn) · 59% chance he's still there at your next pick · fills your open WR slot · TAKE-NOW ZONE: only 3 left before the WR value drops, and 8 teams
- Top projection available: Josh Allen -> took it: False.
- Passed on: De'Von Achane (RB, s=0.475, e=65.5); Trey McBride (TE, s=0.952, e=76.6); Josh Allen (QB, s=0.786, e=43.6).
- Plan call 27 @pick 6: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 5 drafted / 0 mine.
- Engine's first choice was **Puka Nacua** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Puka Nacua | WR | 99.9 | 0.59 | 0.59 | 91.9 | 99.9 | waiting likely costs ~8 pts at WR (best option now 100, ~92 by your next turn) · 59% chanc |
| De'Von Achane | RB | 73.4 | 0.47 | 0.47 | 65.5 | 73.4 | waiting likely costs ~8 pts at RB (best option now 73, ~66 by your next turn) · 48% chance |
| Trey McBride | TE | 77.9 | 0.95 | 0.95 | 76.6 | 77.9 | waiting likely costs ~1 pts at TE (best option now 78, ~77 by your next turn) · 95% chance |
| Josh Allen | QB | 47.0 | 0.79 | 0.79 | 43.6 | 47.0 | waiting likely costs ~3 pts at QB (best option now 47, ~44 by your next turn) · 79% chance |
| Jaxon Smith-Njigba | WR | 89.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Amon-Ra St. Brown | WR | 81.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.6 | 3.4 | 6 |
| RB | 73.4 | 65.5 | 7.9 | 22 |
| WR | 99.9 | 91.9 | 8.0 | 25 |
| TE | 77.9 | 76.6 | 1.3 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 81.79575968181507 | 77.3 | 4.4 | 53 |

### Pick 15 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 15 points at TE, with a 58% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 397 ms, ranker engine, plan call 36, plan age 724 ms, at 23:20:09 PT.
- Engine's reason: waiting likely costs ~15 pts at TE (best option now 78, ~63 by your next turn) · 58% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 10 team
- Top projection available: Drake Maye -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Chase Brown (RB, s=0.492, e=52.2); Drake London (WR, s=0.414, e=45.4); Drake Maye (QB, s=0.964, e=30.6).
- Plan call 36 @pick 15: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 14 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.58 | 0.58 | 63.2 | 77.9 | waiting likely costs ~15 pts at TE (best option now 78, ~63 by your next turn) · 58% chanc |
| Chase Brown | RB | 60.5 | 0.49 | 0.49 | 52.2 | 60.5 | waiting likely costs ~8 pts at RB (best option now 60, ~52 by your next turn) · 49% chance |
| Drake London | WR | 51.0 | 0.41 | 0.41 | 45.4 | 51.0 | waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 41% chance |
| Drake Maye | QB | 31.1 | 0.96 | 0.96 | 30.6 | 31.1 | safe to wait on QB · 96% chance he's still there at your next pick · fills your open QB sl |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Derrick Henry | RB | 50.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 30.6 | 0.5 | 8 |
| RB | 60.5 | 52.2 | 8.3 | 20 |
| WR | 51.0 | 45.4 | 5.6 | 23 |
| TE | 77.9 | 63.2 | 14.7 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 60.53180861379445 | 52.4 | 8.1 | 51 |

### Pick 26 (round 3): Chris Olave (WR)

- In plain English: Took Chris Olave (WR) because waiting would likely cost about 3 points at WR, with a 53% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 555 ms, ranker engine, plan call 44, plan age 871 ms, at 23:21:38 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 40, ~37 by your next turn) · 53% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Javonte Williams (RB, s=0.596, e=32.5); Drake Maye (QB, s=0.918, e=30); George Pickens (WR, s=None, e=None).
- Plan call 44 @pick 26: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1], state store with 25 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.53 | 0.53 | 37.5 | 40.1 | waiting likely costs ~3 pts at WR (best option now 40, ~37 by your next turn) · 53% chance |
| Javonte Williams | RB | 36.9 | 0.60 | 0.60 | 32.5 | 36.9 | waiting likely costs ~4 pts at RB (best option now 37, ~32 by your next turn) · 60% chance |
| Drake Maye | QB | 31.1 | 0.92 | 0.92 | 30.0 | 31.1 | waiting likely costs ~1 pts at QB (best option now 31, ~30 by your next turn) · 92% chance |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 30.0 | 1.1 | 9 |
| RB | 36.9 | 32.5 | 4.4 | 16 |
| WR | 40.1 | 37.5 | 2.6 | 24 |
| TE | 23.8 | 23.5 | 0.3 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 32.5 | 4.4 | 47 |

### Pick 35 (round 4): Travis Etienne Jr. (RB)

- In plain English: Took Travis Etienne Jr. (RB) because waiting would likely cost about 3 points at RB, with a 61% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 437 ms, ranker engine, plan call 55, plan age 751 ms, at 23:23:39 PT.
- Engine's reason: waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 61% chance he's still there at your next pick · fills your open RB slot · only 2 RBs left at this level · 10 teams picking before you still 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.649, e=26.3); Rashee Rice (WR, s=None, e=None); Cam Skattebo (RB, s=None, e=None).
- Plan call 55 @pick 35: needs {'QB': 1, 'RB': 2, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 34 drafted / 3 mine.
- Engine's first choice was **Travis Etienne Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Travis Etienne Jr. | RB | 26.3 | 0.61 | 0.61 | 23.5 | 26.3 | waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 61% chance |
| Drake Maye | QB | 31.1 | 0.65 | 0.65 | 26.3 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 65% chance |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.3 | 4.8 | 10 |
| RB | 26.3 | 23.5 | 2.8 | 16 |
| WR | 34.1 | 28.3 | 5.8 | 20 |
| TE | 23.8 | 22.8 | 1.0 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 24.2 | 2.1 | 44 |

### Pick 46 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 6 points at QB, with a 58% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 695 ms, ranker engine, plan call 67, plan age 1041 ms, at 23:26:10 PT.
- Engine's reason: waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 58% chance he's still there at your next pick · fills your open QB slot · 6 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.95, e=9.2); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 67 @pick 46: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 45 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.58 | 0.58 | 25.3 | 31.1 | waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 58% chance |
| Jaylen Warren | RB | 9.3 | 0.95 | 0.95 | 9.2 | 9.3 | safe to wait on RB · 95% chance he's still there at your next pick · fills your open RB sl |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.3 | 5.8 | 13 |
| RB | 9.3 | 9.2 | 0.1 | 15 |
| WR | 13.1 | 10.8 | 2.3 | 20 |
| TE | 23.8 | 22.4 | 1.4 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 44 |

### Pick 55 (round 6): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (84% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 465 ms, ranker engine, plan call 76, plan age 780 ms, at 23:28:05 PT.
- Engine's reason: safe to wait on RB · 84% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Emeka Egbuka (WR, s=None, e=None); Rhamondre Stevenson (RB, s=None, e=None); Terry McLaurin (WR, s=None, e=None).
- Plan call 76 @pick 55: needs {'QB': 0, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7, 8], state store with 54 drafted / 5 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.84 | 0.84 | 8.9 | 9.3 | safe to wait on RB · 84% chance he's still there at your next pick · fills your open RB sl |
| Emeka Egbuka | WR | 8.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Terry McLaurin | WR | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.6 | 1.4 | 14 |
| RB | 9.3 | 8.9 | 0.4 | 16 |
| WR | 8.2 | 6.7 | 1.5 | 21 |
| TE | 21.1 | 19.7 | 1.4 | 8 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.9 | 0.4 | 45 |

### Pick 66 (round 7): Rhamondre Stevenson (RB)

- In plain English: Took Rhamondre Stevenson (RB) because waiting would likely cost about 4 points at your FLEX spot, with a 72% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 386 ms, ranker engine, plan call 85, plan age 704 ms, at 23:29:44 PT.
- Engine's reason: waiting likely costs ~4 pts at your FLEX spot (best option now 7, ~4 by your next turn) · 72% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jameson Williams (WR, s=None, e=None); Mike Evans (WR, s=None, e=None); RJ Harvey (RB, s=None, e=None).
- Plan call 85 @pick 66: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 7, 8], state store with 65 drafted / 6 mine.
- Engine's first choice was **Rhamondre Stevenson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rhamondre Stevenson | RB | 7.2 | 0.72 | 0.72 | 3.7 | 7.2 | waiting likely costs ~4 pts at your FLEX spot (best option now 7, ~4 by your next turn) ·  |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.4 | 1.3 | 20 |
| RB | 7.2 | 3.7 | 3.5 | 22 |
| WR | 0.0 | -1.4 | 1.4 | 27 |
| TE | 21.1 | 19.8 | 1.3 | 13 |
| K | 13.5 | 13.4 | 0.1 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 7.2333043142844815 | 3.7 | 3.5 | 62 |

### Pick 75 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 96 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 445 ms, ranker engine, plan call 89, plan age 759 ms, at 23:30:26 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: DK Metcalf (WR, s=0.677, e=-9.4); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 89 @pick 75: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 7, 8], state store with 74 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.75 | 0.75 | -5.5 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacob |
| DK Metcalf | WR | -9.2 | 0.68 | 0.68 | -9.4 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.0 | 0.8 | 19 |
| RB | -5.4 | -5.5 | 0.1 | 33 |
| WR | -9.2 | -9.4 | 0.2 | 38 |
| TE | 16.4 | 12.3 | 4.1 | 20 |
| K | 13.5 | 13.3 | 0.2 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 8 |

### Pick 86 (round 9): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 23 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 458 ms, ranker engine, plan call 99, plan age 775 ms, at 23:32:37 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Wan'Dale Robinson (WR, s=0.978, e=-10.6); Kenny Gainwell (RB, s=None, e=None); Courtland Sutton (WR, s=None, e=None).
- Plan call 99 @pick 86: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 7, 8], state store with 85 drafted / 8 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.88 | 0.88 | -5.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1 |
| Wan'Dale Robinson | WR | -10.6 | 0.98 | 0.98 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Wilson | WR | -14.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.7 | 1.1 | 18 |
| RB | -5.4 | -5.5 | 0.1 | 29 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 13.8 | 13.1 | 0.7 | 19 |
| K | 13.5 | 13.2 | 0.3 | 13 |
| DEF | 18.0 | 17.6 | 0.4 | 11 |

### Pick 95 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 361 ms, ranker engine, plan call 103, plan age 673 ms, at 23:33:14 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.672, e=10.5); Kenny Gainwell (RB, s=0.91, e=-8); Matthew Stafford (QB, s=None, e=None).
- Plan call 103 @pick 95: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 7, 8], state store with 94 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.96 | 0.96 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.67 | 0.67 | 10.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Kenny Gainwell | RB | -6.2 | 0.91 | 0.91 | -8.0 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.5 | 2.3 | 18 |
| RB | -6.2 | -8.0 | 1.8 | 25 |
| WR | -10.6 | -10.6 | 0.0 | 34 |
| TE | 13.8 | 11.5 | 2.3 | 19 |
| K | 13.5 | 13.4 | 0.1 | 14 |
| DEF | 18.0 | 17.8 | 0.2 | 11 |

### Pick 106 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 451 ms, ranker engine, plan call 108, plan age 769 ms, at 23:34:09 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.918, e=-7.8); Courtland Sutton (WR, s=0.865, e=-11.4); Jared Goff (QB, s=None, e=None).
- Plan call 108 @pick 106: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 7, 8], state store with 105 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.92 | 0.92 | 10.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Kenny Gainwell | RB | -6.2 | 0.92 | 0.92 | -7.8 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.86 | 0.86 | -11.4 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyler Murray | QB | -14.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.8 | 2.0 | 14 |
| RB | -6.2 | -7.8 | 1.6 | 23 |
| WR | -11.1 | -11.4 | 0.3 | 30 |
| TE | 13.8 | 13.5 | 0.3 | 18 |
| K | 13.5 | 13.4 | 0.1 | 15 |
| DEF | 18.0 | 17.7 | 0.3 | 13 |

### Pick 115 (round 12): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +9.1 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 488 ms, ranker engine, plan call 114, plan age 810 ms, at 23:35:09 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.974, e=-11.2); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 114 @pick 115: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 7, 8], state store with 114 drafted / 11 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.97 | 0.97 | -6.9 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.97 | 0.97 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 10 |
| RB | -6.2 | -6.9 | 0.7 | 22 |
| WR | -11.1 | -11.2 | 0.1 | 28 |
| TE | 0.5 | 0.2 | 0.3 | 16 |
| K | 13.5 | 13.4 | 0.1 | 16 |
| DEF | 18.0 | 17.7 | 0.3 | 14 |

### Pick 126 (round 13): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1156 ms, ranker engine, plan call 121, plan age 1481 ms, at 23:36:18 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Woody Marks (RB, s=0.968, e=-30.4); Jakobi Meyers (WR, s=None, e=None); Romeo Doubs (WR, s=None, e=None).
- Plan call 121 @pick 126: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 7], state store with 125 drafted / 12 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.96 | 0.96 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Woody Marks | RB | -30.3 | 0.97 | 0.97 | -30.4 | -30.3 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.8 | 0.3 | 8 |
| RB | -30.3 | -30.4 | 0.1 | 20 |
| WR | -13.3 | -13.6 | 0.3 | 25 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 13.5 | 13.5 | 0.0 | 17 |
| DEF | 16.0 | 15.9 | 0.1 | 13 |

### Pick 135 (round 14): Eagles (DEF)

- In plain English: Took Philadelphia Eagles (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (60% to survive, but nobody better was worth waiting for). The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 346 ms, ranker engine, plan call 126, plan age 658 ms, at 23:37:08 PT.
- Engine's reason: safe to wait on DEF · 60% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · two-pick plan: pair with the ~30-pt RB expected at your next turn
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Cam Little (K, s=0.656, e=10); Cameron Dicker (K, s=None, e=None); Minnesota Vikings (DEF, s=None, e=None).
- Plan call 126 @pick 135: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 7, 8], state store with 134 drafted / 13 mine.
- Engine's first choice was **Philadelphia Eagles** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Philadelphia Eagles | DEF | 10.0 | 0.59 | 0.59 | 9.1 | 10.0 | safe to wait on DEF · 60% chance he's still there at your next pick · fills your open DEF  |
| Cam Little | K | 9.0 | 0.66 | 0.66 | 10.0 | 10.5 | safe to wait on K · 66% chance he's still there at your next pick · fills your open K slot |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.8 | 0.3 | 8 |
| RB | -30.3 | -30.4 | 0.1 | 18 |
| WR | -21.5 | -21.8 | 0.3 | 24 |
| TE | 0.5 | 0.4 | 0.1 | 12 |
| K | 10.5 | 10.0 | 0.5 | 16 |
| DEF | 10.0 | 9.1 | 0.9 | 10 |

### Pick 146 (round 15): Evan McPherson (K)

- In plain English: Took Evan McPherson (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 543 ms, ranker engine, plan call 133, plan age 856 ms, at 23:38:16 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 133 @pick 146: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 3, 7, 8], state store with 145 drafted / 14 mine.
- Engine's first choice was **Evan McPherson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Evan McPherson | K | 3.0 | - | - | - | - | fills your open K slot |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 30-50% | 11 | 46% | 0% |
| 50-70% | 37 | 63% | 22% |
| 70-90% | 43 | 81% | 40% |
| 90-100% | 96 | 96% | 81% |

187 predictions over 84 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Driver log (the lines that matter, Pacific time)

    23:18:10 PT preflight: ok=true pick_path=action my_team=6 plan=plan 25 deep @pick 3 via store call#24
    23:18:10 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    23:18:29 PT ON CLOCK -> {"drafted":"Puka Nacua","pos":"WR","vorp":99.9,"proj":242,"why":"waiting likely costs ~8 pts at WR (best option now 100, ~92 by your next turn) · 59% chance he's still there at your next pick · fills your open WR slo
    23:20:09 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~15 pts at TE (best option now 78, ~63 by your next turn) · 58% chance he's still there at your next pick · fills your open TE
    23:21:38 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~3 pts at WR (best option now 40, ~37 by your next turn) · 53% chance he's still there at your next pick · fills your open WR s
    23:22:10 PT heartbeat: setAwayStatus(false)
    23:23:39 PT ON CLOCK -> {"drafted":"Travis Etienne Jr.","pos":"RB","vorp":26.3,"proj":186.5,"why":"waiting likely costs ~3 pts at RB (best option now 26, ~23 by your next turn) · 61% chance he's still there at your next pick · fills your op
    23:26:10 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 58% chance he's still there at your next pick · fills your open QB sl
    23:26:12 PT heartbeat: setAwayStatus(false)
    23:28:05 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on RB · 84% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB","s":0.84
    23:29:44 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"waiting likely costs ~4 pts at your FLEX spot (best option now 7, ~4 by your next turn) · 72% chance he's still there at your next pick · fil
    23:30:12 PT heartbeat: setAwayStatus(false)
    23:30:26 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren","s":0.
    23:32:37 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts","s":0.881,"sr":0.8
    23:33:14 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.965,"sr":0.965,"e":-10.6,"top_
    23:34:09 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.92,"sr":0.92,"e":10.8,"top_proj
    23:34:12 PT heartbeat: setAwayStatus(false)
    23:35:09 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.966,"
    23:36:18 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    23:37:08 PT ON CLOCK -> {"drafted":"Philadelphia Eagles","pos":"DEF","vorp":10,"proj":127,"why":"safe to wait on DEF · 60% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · 
    23:38:13 PT heartbeat: setAwayStatus(false)
    23:38:16 PT ON CLOCK -> {"drafted":"Evan McPherson","pos":"K","vorp":3,"proj":139.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection
    23:38:18 PT roster full
    23:38:18 PT driver stop


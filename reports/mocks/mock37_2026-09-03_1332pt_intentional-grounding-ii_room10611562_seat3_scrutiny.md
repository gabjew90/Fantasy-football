# Scrutiny: Mock 37 -- Intentional Grounding II (room 10611562) -- Thursday 2026-09-03 13:32 PT -- 10 teams, our seat 3

Captured 2026-09-03 13:49:39 PT. Times below are Pacific. 10 teams, our team id 3, draft slot 3. 150 picks in the trail, 97 bridge plan calls, 63 recs events in the room log.

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
- Action latency to store confirmation: median 435 ms, min 269, max 1495.
- Heartbeats 16; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (3): 1 drafted entries matched no board player: 94 Will Reichard; 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader; dropped 1 feed entries numbered >= header pick 142.
- Away seats over the room (each change): {} -> {4} -> {4,6,8,9} -> {6,8,9} -> {4,6,8,9} -> {4,5,6,8,9} -> {4,6,8,9} -> {6,8,9} -> {4,6,8,9} -> {1,4,6,8,9} -> {1,4,5,6,8,9}.
- Managers away at the end: 1 Joe R, 4 Jason, 5 STRYKER, 6 matt, 8 red22, 9 Marcel Sarkisian.

## Our picks, one block each

### Pick 3 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 56 points at RB, with a 31% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 435 ms, ranker engine, plan call 8, plan age 746 ms, at 13:33:35 PT.
- Engine's reason: waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 14 tea
- Top projection available: Josh Allen -> took it: False.
- Passed on: Ja'Marr Chase (WR, s=0.529, e=100.8); Trey McBride (TE, s=0.864, e=73.8); Josh Allen (QB, s=0.638, e=41.2).
- Plan call 8 @pick 3: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 2 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.31 | 0.31 | 98.5 | 154.2 | waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chan |
| Ja'Marr Chase | WR | 115.3 | 0.53 | 0.53 | 100.8 | 115.3 | waiting likely costs ~15 pts at WR (best option now 115, ~101 by your next turn) · 53% cha |
| Trey McBride | TE | 77.9 | 0.86 | 0.86 | 73.8 | 77.9 | waiting likely costs ~4 pts at TE (best option now 78, ~74 by your next turn) · 86% chance |
| Josh Allen | QB | 47.0 | 0.64 | 0.64 | 41.2 | 47.0 | waiting likely costs ~6 pts at QB (best option now 47, ~41 by your next turn) · 64% chance |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Puka Nacua | WR | 99.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 41.2 | 5.8 | 6 |
| RB | 154.2 | 98.5 | 55.7 | 23 |
| WR | 115.3 | 100.8 | 14.5 | 25 |
| TE | 77.9 | 73.8 | 4.1 | 5 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 111.5 | 42.7 | 53 |

### Pick 18 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 5 points at TE, with a 81% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 411 ms, ranker engine, plan call 17, plan age 726 ms, at 13:35:10 PT.
- Engine's reason: waiting likely costs ~5 pts at TE (best option now 78, ~73 by your next turn) · 81% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 4 teams 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=0.67, e=48.2); Derrick Henry (RB, s=0.707, e=47.2); Josh Allen (QB, s=0.739, e=42.8).
- Plan call 17 @pick 18: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 17 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.81 | 0.81 | 72.9 | 77.9 | waiting likely costs ~5 pts at TE (best option now 78, ~73 by your next turn) · 81% chance |
| Drake London | WR | 51.0 | 0.67 | 0.67 | 48.2 | 51.0 | waiting likely costs ~3 pts at WR (best option now 51, ~48 by your next turn) · 67% chance |
| Derrick Henry | RB | 50.4 | 0.71 | 0.71 | 47.2 | 50.4 | waiting likely costs ~3 pts at RB (best option now 50, ~47 by your next turn) · 71% chance |
| Josh Allen | QB | 47.0 | 0.74 | 0.74 | 42.8 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 74% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.8 | 4.2 | 9 |
| RB | 50.4 | 47.2 | 3.2 | 18 |
| WR | 51.0 | 48.2 | 2.8 | 22 |
| TE | 77.9 | 72.9 | 5.0 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 50.44274023536681 | 47.5 | 3.0 | 48 |

### Pick 23 (round 3): Chris Olave (WR)

- In plain English: Took Chris Olave (WR) because waiting would likely cost about 8 points at WR, with a 20% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 420 ms, ranker engine, plan call 22, plan age 741 ms, at 13:35:59 PT.
- Engine's reason: waiting likely costs ~8 pts at WR (best option now 40, ~32 by your next turn) · 20% chance he's still there at your next pick · fills your open WR slot · 14 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Josh Allen -> took it: False.
- Passed on: Kyren Williams (RB, s=0.21, e=34.2); Josh Allen (QB, s=0.632, e=40.7); Javonte Williams (RB, s=None, e=None).
- Plan call 22 @pick 23: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 22 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.20 | 0.20 | 31.9 | 40.1 | waiting likely costs ~8 pts at WR (best option now 40, ~32 by your next turn) · 20% chance |
| Kyren Williams | RB | 40.5 | 0.21 | 0.21 | 34.2 | 40.5 | waiting likely costs ~6 pts at your FLEX spot (best option now 41, ~34 by your next turn)  |
| Josh Allen | QB | 47.0 | 0.63 | 0.63 | 40.7 | 47.0 | waiting likely costs ~6 pts at QB (best option now 47, ~41 by your next turn) · 63% chance |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 40.7 | 6.3 | 9 |
| RB | 40.5 | 34.2 | 6.3 | 18 |
| WR | 40.1 | 31.9 | 8.2 | 23 |
| TE | 23.8 | 23.5 | 0.3 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 34.2 | 6.4 | 47 |

### Pick 38 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (83% to survive, but nobody better was worth waiting for). The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 461 ms, ranker engine, plan call 30, plan age 783 ms, at 13:37:26 PT.
- Engine's reason: safe to wait on WR · 83% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pick plan: pair with the ~31-pt WR expected at your next turn
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.722, e=25.4); Drake Maye (QB, s=0.848, e=29.1); Cam Skattebo (RB, s=None, e=None).
- Plan call 30 @pick 38: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [6, 8, 9], state store with 37 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.83 | 0.83 | 23.3 | 23.9 | safe to wait on WR · 83% chance he's still there at your next pick · fills your open WR sl |
| Travis Etienne Jr. | RB | 26.3 | 0.72 | 0.72 | 25.4 | 26.3 | safe to wait on RB · 72% chance he's still there at your next pick · fills your open RB sl |
| Drake Maye | QB | 31.1 | 0.85 | 0.85 | 29.1 | 31.1 | waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 85% chance |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 29.1 | 2.0 | 9 |
| RB | 26.3 | 25.4 | 0.9 | 17 |
| WR | 23.9 | 23.3 | 0.6 | 21 |
| TE | 23.8 | 23.3 | 0.5 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 26.331806855987054 | 25.4 | 0.9 | 46 |

### Pick 43 (round 5): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB) because waiting would likely cost about 8 points at your FLEX spot, with a 53% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 445 ms, ranker engine, plan call 37, plan age 770 ms, at 13:38:39 PT.
- Engine's reason: waiting likely costs ~8 pts at your FLEX spot (best option now 26, ~18 by your next turn) · 53% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 10 teams 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.28, e=20.5); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 37 @pick 43: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 42 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.53 | 0.53 | 18.1 | 25.8 | waiting likely costs ~8 pts at your FLEX spot (best option now 26, ~18 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.28 | 0.28 | 20.5 | 31.1 | waiting likely costs ~11 pts at QB (best option now 31, ~21 by your next turn) · 28% chanc |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Tetairoa McMillan | WR | 15.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaylen Waddle | WR | 14.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 20.5 | 10.6 | 13 |
| RB | 25.8 | 18.1 | 7.7 | 17 |
| WR | 15.4 | 13.8 | 1.6 | 19 |
| TE | 23.8 | 21.5 | 2.3 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 18.1 | 7.8 | 44 |

### Pick 58 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (67% to survive, but nobody better was worth waiting for).
- Driver: via **action**, verified store, 470 ms, ranker engine, plan call 45, plan age 865 ms, at 13:40:05 PT.
- Engine's reason: safe to wait on QB · 67% chance he's still there at your next pick · fills your open QB slot · 4 teams picking before you still need a QB · two-pick plan: pair with the ~36-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.934, e=9.2); Trevor Lawrence (QB, s=None, e=None); Davante Adams (WR, s=None, e=None).
- Plan call 45 @pick 58: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 57 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.67 | 0.67 | 17.2 | 18.0 | safe to wait on QB · 67% chance he's still there at your next pick · fills your open QB sl |
| Jaylen Warren | RB | 9.3 | 0.93 | 0.93 | 9.2 | 9.3 | safe to wait on your FLEX spot · 93% chance he's still there at your next pick · fills a F |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.2 | 0.8 | 14 |
| RB | 9.3 | 9.2 | 0.1 | 16 |
| WR | 13.1 | 11.7 | 1.4 | 21 |
| TE | 21.1 | 20.9 | 0.2 | 11 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 48 |

### Pick 63 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 5 points at your FLEX spot, with a 51% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 465 ms, ranker engine, plan call 51, plan age 791 ms, at 13:41:11 PT.
- Engine's reason: waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 51% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Davante Adams (WR, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 51 @pick 63: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 62 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.51 | 0.51 | 4.6 | 9.3 | waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) ·  |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.5 | 1.2 | 16 |
| RB | 9.3 | 4.5 | 4.8 | 17 |
| WR | 13.1 | 10.4 | 2.7 | 22 |
| TE | 21.1 | 15.9 | 5.2 | 11 |
| K | 13.5 | 13.2 | 0.3 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 4.6 | 4.7 | 50 |

### Pick 78 (round 8): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +8.3 points a week over the waiver wire (Ollie Gordon II), worth about 80 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 334 ms, ranker engine, plan call 61, plan age 668 ms, at 13:42:59 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.9, e=-9.3); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 61 @pick 78: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6, 8, 9], state store with 77 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 0.99 | 0.99 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordo |
| DK Metcalf | WR | -9.2 | 0.90 | 0.90 | -9.3 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.8 | 0.9 | 20 |
| RB | -5.4 | -5.4 | 0.0 | 32 |
| WR | -9.2 | -9.3 | 0.1 | 39 |
| TE | 19.8 | 18.4 | 1.4 | 19 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 8 |

### Pick 83 (round 9): DK Metcalf (WR)

- In plain English: Lineup already full, so DK Metcalf (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.8 points a week over the waiver wire (Rashod Bateman), worth about 18 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 405 ms, ranker engine, plan call 65, plan age 733 ms, at 13:43:37 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bateman) ≈ 18 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: RJ Harvey (RB, s=0.784, e=-5.7); Kenny Gainwell (RB, s=None, e=None); Carnell Tate (WR, s=None, e=None).
- Plan call 65 @pick 83: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6, 8, 9], state store with 82 drafted / 8 mine.
- Engine's first choice was **DK Metcalf** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| DK Metcalf | WR | -9.2 | 0.45 | 0.45 | -9.9 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | 0.78 | 0.78 | -5.7 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.6 | 2.2 | 19 |
| RB | -5.4 | -5.7 | 0.3 | 30 |
| WR | -9.2 | -9.9 | 0.7 | 38 |
| TE | 19.8 | 16.7 | 3.1 | 19 |
| K | 13.5 | 12.9 | 0.6 | 12 |
| DEF | 18.0 | 16.8 | 1.2 | 10 |

### Pick 98 (round 10): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +6.5 points a week over the waiver wire (Ollie Gordon II), worth about 16 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1495 ms, ranker engine, plan call 69, plan age 1895 ms, at 13:44:19 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5/wk over the wire (Ollie Gordon II) ≈ 16 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.886, e=12.1); Wan'Dale Robinson (WR, s=0.969, e=-10.6); Matthew Stafford (QB, s=None, e=None).
- Plan call 69 @pick 98: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 97 drafted / 9 mine, warnings ['1 drafted entries matched no board player: 94 Will Reichard'].
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.96 | 0.96 | -5.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5 |
| Patrick Mahomes II | QB | 12.8 | 0.89 | 0.89 | 12.1 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Wan'Dale Robinson | WR | -10.6 | 0.97 | 0.97 | -10.6 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.1 | 0.7 | 18 |
| RB | -5.4 | -5.5 | 0.1 | 26 |
| WR | -10.6 | -10.6 | 0.0 | 34 |
| TE | 13.8 | 13.4 | 0.4 | 18 |
| K | 13.5 | 13.5 | 0.0 | 14 |
| DEF | 18.0 | 18.0 | 0.0 | 9 |

### Pick 103 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 509 ms, ranker engine, plan call 74, plan age 837 ms, at 13:45:07 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Wan'Dale Robinson (WR, s=0.953, e=-10.6); Kenny Gainwell (RB, s=0.889, e=-8.4); Matthew Stafford (QB, s=None, e=None).
- Plan call 74 @pick 103: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 102 drafted / 10 mine, warnings ['1 drafted entries matched no board player: 94 Will Reichard'].
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.79 | 0.79 | 11.4 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Wan'Dale Robinson | WR | -10.6 | 0.95 | 0.95 | -10.6 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | 0.89 | 0.89 | -8.4 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.4 | 1.4 | 16 |
| RB | -6.2 | -8.4 | 2.2 | 24 |
| WR | -10.6 | -10.6 | 0.0 | 33 |
| TE | 13.8 | 13.1 | 0.7 | 18 |
| K | 13.5 | 13.3 | 0.2 | 15 |
| DEF | 18.0 | 17.4 | 0.6 | 10 |

### Pick 118 (round 12): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 597 ms, ranker engine, plan call 80, plan age 929 ms, at 13:46:11 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.972, e=-26); Michael Pittman Jr. (WR, s=None, e=None); Stefon Diggs (WR, s=None, e=None).
- Plan call 80 @pick 118: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 117 drafted / 11 mine, warnings ['1 drafted entries matched no board player: 94 Will Reichard'].
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.98 | 0.98 | -10.6 | -10.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.97 | 0.97 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Stefon Diggs | WR | -18.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -25.9 | -26.0 | 0.1 | 21 |
| WR | -10.6 | -10.6 | 0.0 | 29 |
| TE | 0.5 | 0.4 | 0.1 | 15 |
| K | 12.0 | 11.8 | 0.2 | 15 |
| DEF | 18.0 | 17.9 | 0.1 | 12 |

### Pick 123 (round 13): Woody Marks (RB)

- In plain English: Lineup already full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +5.0 points a week over the waiver wire (Ollie Gordon II), worth about 1 points. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 382 ms, ranker engine, plan call 83, plan age 744 ms, at 13:46:38 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5.0/wk over the wire (Ollie Gordon II) ≈ 1 pts
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Michael Pittman Jr. (WR, s=0.938, e=-13.6); Stefon Diggs (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 83 @pick 123: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 8, 9], state store with 122 drafted / 12 mine, warnings ['1 drafted entries matched no board player: 94 Will Reichard'].
- Engine's first choice was **Woody Marks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Woody Marks | RB | -30.3 | 0.94 | 0.94 | -30.7 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5. |
| Michael Pittman Jr. | WR | -13.3 | 0.94 | 0.94 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +2. |
| Stefon Diggs | WR | -18.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -30.3 | -30.7 | 0.4 | 19 |
| WR | -13.3 | -13.6 | 0.3 | 28 |
| TE | 0.5 | 0.4 | 0.1 | 14 |
| K | 12.0 | 11.1 | 0.9 | 15 |
| DEF | 16.0 | 15.9 | 0.1 | 11 |

### Pick 138 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (77% to survive, but nobody better was worth waiting for). The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 346 ms, ranker engine, plan call 92, plan age 689 ms, at 13:48:16 PT.
- Engine's reason: safe to wait on DEF · 77% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · two-pick plan: pair with the ~25-pt RB expected at your next turn
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cam Little (K, s=0.823, e=8.7); Minnesota Vikings (DEF, s=None, e=None); Jason Myers (K, s=None, e=None).
- Plan call 92 @pick 138: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 4, 5, 6, 8, 9], state store with 137 drafted / 13 mine, warnings ['1 drafted entries matched no board player: 94 Will Reichard'].
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.77 | 0.77 | 8.0 | 8.0 | safe to wait on DEF · 77% chance he's still there at your next pick · fills your open DEF  |
| Cam Little | K | 9.0 | 0.82 | 0.82 | 8.7 | 9.0 | safe to wait on K · 82% chance he's still there at your next pick · fills your open K slot |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 10 |
| RB | -37.5 | -37.6 | 0.1 | 16 |
| WR | -21.5 | -21.7 | 0.2 | 23 |
| TE | 0.5 | 0.5 | 0.0 | 14 |
| K | 9.0 | 8.7 | 0.3 | 15 |
| DEF | 8.0 | 8.0 | 0.0 | 8 |

### Pick 143 (round 15): Cam Little (K)

- In plain English: Took Cam Little (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 269 ms, ranker engine, plan call 97, plan age 597 ms, at 13:48:58 PT.
- Engine's reason: fills your open K slot · bargain: still here 14 picks after he's usually drafted
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Eddy Pineiro (K, s=None, e=None); Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None).
- Plan call 97 @pick 143: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 4, 5, 6, 8, 9], state store with 142 drafted / 14 mine, warnings ['2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader'].
- Engine's first choice was **Cam Little** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Little | K | 9.0 | - | - | - | - | fills your open K slot · bargain: still here 14 picks after he's usually drafted |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 6 | 24% | 0% |
| 30-50% | 14 | 39% | 7% |
| 50-70% | 17 | 61% | 24% |
| 70-90% | 47 | 81% | 64% |
| 90-100% | 61 | 96% | 82% |

145 predictions over 62 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T13:44:17   WARNING plan #69: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:44:22   WARNING plan #70: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:44:34   WARNING plan #71: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:44:47   WARNING plan #72: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:44:59   WARNING plan #73: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:45:06   WARNING plan #74: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:45:10   WARNING plan #75: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:45:22   WARNING plan #76: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:45:34   WARNING plan #77: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:45:47   WARNING plan #78: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:00   WARNING plan #79: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:10   WARNING plan #80: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:13   WARNING plan #81: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:26   WARNING plan #82: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:38   WARNING plan #83: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:41   WARNING plan #84: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:46:54   WARNING plan #85: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:47:06   WARNING plan #86: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:47:19   WARNING plan #87: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:47:31   WARNING plan #88: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:47:44   WARNING plan #89: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:47:57   WARNING plan #90: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:48:09   WARNING plan #91: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:48:15   WARNING plan #92: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:48:19   WARNING plan #93: 1 drafted entries matched no board player: 94 Will Reichard
    2026-09-03T13:48:31   WARNING plan #94: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    2026-09-03T13:48:44   WARNING plan #95: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    2026-09-03T13:48:57   WARNING plan #96: dropped 1 feed entries numbered >= header pick 142
    2026-09-03T13:48:57   WARNING plan #96: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    2026-09-03T13:48:58   WARNING plan #97: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader

## Narration (what the panel showed live, Pacific time)

    13:32:23  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 5 · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next) · 83% survives to our turn
  • Ja'Marr Chase WR · wait costs 4 · pick costs 11.3 · 77% survives to our turn

    13:32:24  driver started — seat 3, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    13:33:24  heartbeat sent (Yahoo told we are not idle)
    13:33:30  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    13:33:34  pick 2  Bijan Robinson (RB) taken by seat 2 in 4 s — a target is gone
    13:33:35  plan #8 for pick 3
  • Christian McCaffrey RB · wait costs 56 · pick costs 0, best pair 269.7 (159.6 now + ~110.1 WR next) · 31% survives to our turn
  • Ja'Marr Chase WR · wait costs 15 · pick costs 36 · 53% survives to our turn

    13:33:35  ON THE CLOCK, pick 3 · plan #8 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    13:33:35  PICKED Christian McCaffrey (RB) via action, confirmed in 435 ms — chose Christian McCaffrey (RB): waiting would likely cost about 56 points at RB, 31% to still be there next turn
  • top projection left was Josh Allen, passed on p
    13:33:37  pick 4  Ja'Marr Chase (WR) taken by seat 4 in 2 s — a target is gone (was 53% to survive)
    13:33:38  plan #9 for pick 5
  • Jonathan Taylor RB · wait costs 30 · pick costs 0, best pair 201.8 (109.7 now + ~92.1 WR next) · 34% survives to our turn
  • Puka Nacua WR · wait costs 17 · pick costs 0.6 · 42% survives to our turn
  • Tre
    13:33:40  pick 5  Jaxon Smith-Njigba (WR) taken by seat 5 in 3 s — a target is gone
    13:33:40  pick 6  Puka Nacua (WR) taken by seat 6 in 0 s INSTANTLY (autopick) — a target is gone (was 42% to survive)
    13:33:45  pick 7  Jonathan Taylor (RB) taken by seat 7 in 5 s — a target is gone (was 34% to survive)
    13:33:45  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 0 s — a target is gone
    13:33:46  pick 9  James Cook III (RB) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    13:33:50  plan #10 for pick 10
  • De'Von Achane RB · wait costs 17 · pick costs 0, best pair 140.8 (78.8 now + ~62 WR next) · 27% survives to our turn
  • CeeDee Lamb WR · wait costs 4 · pick costs 12.8 · 39% survives to our turn
  • Trey 
    13:34:09  pick 10  Kenneth Walker III (RB) taken by seat 10 in 23 s
    13:34:15  plan #12 for pick 11
  • De'Von Achane RB · wait costs 15 · pick costs 0, best pair 142.9 (78.8 now + ~64.1 RB next) · 33% survives to our turn
  • CeeDee Lamb WR · wait costs 3 · pick costs 12.8 · 51% survives to our turn
  • Tre
    13:34:24  heartbeat sent (Yahoo told we are not idle)
    13:34:32  pick 11  De'Von Achane (RB) taken by seat 10 in 23 s — a target is gone (was 33% to survive)
    13:34:33  pick 12  Saquon Barkley (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:34:34  pick 13  CeeDee Lamb (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 51% to survive)
    13:34:39  plan #14 for pick 14
  • Chase Brown RB · wait costs 8 · pick costs 0, best pair 127.4 (65.9 now + ~61.5 WR next) · 46% survives to our turn
  • Justin Jefferson WR · wait costs 2 · pick costs 4.1 · 65% survives to our turn
  • Tr
    13:34:42  pick 14  Chase Brown (RB) taken by seat 7 in 8 s — a target is gone (was 46% to survive)
    13:34:42  pick 15  Justin Jefferson (WR) taken by seat 6 in 0 s — a target is gone (was 65% to survive)
    13:34:52  plan #15 for pick 16
  • Drake London WR · wait costs 2 · pick costs 0, best pair 117.6 (60.2 now + ~57.4 TE next) · 79% survives to our turn
  • Trey McBride TE · safe to wait · pick costs 0.7 · 97% survives to our turn
  • Derri
    13:35:09  pick 16  Nico Collins (WR) taken by seat 5 in 27 s — a target is gone
    13:35:09  pick 17  Omarion Hampton (RB) taken by seat 4 in 0 s INSTANTLY (autopick)
    13:35:09  plan #17 for pick 18
  • Trey McBride TE · wait costs 5 · pick costs 0, best pair 115.7 (58.2 now + ~57.5 WR next) · 81% survives to our turn
  • Drake London WR · wait costs 3 · pick costs 2.3 · 67% survives to our turn
  • Derri
    13:35:09  ON THE CLOCK, pick 18 · plan #17 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    13:35:10  PICKED Trey McBride (TE) via action, confirmed in 411 ms — chose Trey McBride (TE): waiting would likely cost about 5 points at TE, 81% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    13:35:13  plan #18 for pick 19
  • Derrick Henry RB · wait costs 3 · pick costs 0, best pair 113.1 (55.8 now + ~57.3 WR next) · 68% survives to our turn
  • Drake London WR · wait costs 3 · pick costs 0, best pair 113.1 (60.2 now + ~52.9 WR
    13:35:17  pick 19  Derrick Henry (RB) taken by seat 2 in 7 s — a target is gone (was 68% to survive)
    13:35:24  heartbeat sent (Yahoo told we are not idle)
    13:35:25  plan #19 for pick 20
  • Drake London WR · wait costs 2 · pick costs 0, best pair 113.1 (60.2 now + ~52.9 WR next) · 72% survives to our turn
  • Kyren Williams RB · safe to wait · pick costs 9.2 · 79% survives to our turn
  • Jos
    13:35:40  pick 20  A.J. Brown (WR) taken by seat 1 in 23 s — a target is gone
    13:35:49  plan #21 for pick 21
  • Drake London WR · wait costs 2 · pick costs 0, best pair 109.5 (60.2 now + ~49.3 WR next) · 86% survives to our turn
  • Kyren Williams RB · safe to wait · pick costs 4.9 · 85% survives to our turn
  • Jos
    13:35:56  pick 21  Brock Bowers (TE) taken by seat 1 in 16 s
    13:35:57  pick 22  Drake London (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 86% to survive)
    13:35:58  plan #22 for pick 23
  • Chris Olave WR · wait costs 8 · pick costs 0, best pair 90.5 (49.3 now + ~41.2 WR next) · 20% survives to our turn
  • Kyren Williams RB · wait costs 6 · pick costs 3.4 · 21% survives to our turn
  • Josh 
    13:35:58  ON THE CLOCK, pick 23 · plan #22 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    13:35:59  PICKED Chris Olave (WR) via action, confirmed in 420 ms — chose Chris Olave (WR): waiting would likely cost about 8 points at WR, 20% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    13:36:01  pick 24  Ashton Jeanty (RB) taken by seat 4 in 2 s — a target is gone
    13:36:02  plan #23 for pick 25
  • George Pickens WR · wait costs 5 · pick costs 0, best pair 88.9 (45.5 now + ~43.4 WR next) · 45% survives to our turn
  • Kyren Williams RB · wait costs 10 · pick costs 2.3 · 23% survives to our turn
  • J
    13:36:14  pick 25  Colston Loveland (TE) taken by seat 5 in 14 s
    13:36:16  pick 26  George Pickens (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone (was 45% to survive)
    13:36:23  pick 27  DeVonta Smith (WR) taken by seat 7 in 7 s
    13:36:23  pick 28  Malik Nabers (WR) taken by seat 8 in 0 s INSTANTLY (autopick) — a target is gone
    13:36:24  pick 29  Kyren Williams (RB) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone (was 23% to survive)
    13:36:25  heartbeat sent (Yahoo told we are not idle)
    13:36:26  plan #25 for pick 30
  • Javonte Williams RB · wait costs 8 · pick costs 0, best pair 78.9 (42.3 now + ~36.6 WR next) · 30% survives to our turn
  • Rashee Rice WR · wait costs 7 · pick costs 1 · 37% survives to our turn
  • Josh 
    13:36:48  pick 30  Josh Allen (QB) taken by seat 10 in 24 s — a target is gone (was 90% to survive)
    13:36:51  plan #27 for pick 31
  • Javonte Williams RB · wait costs 7 · pick costs 0, best pair 80.4 (42.3 now + ~38.1 WR next) · 40% survives to our turn
  • Rashee Rice WR · wait costs 5 · pick costs 1.5 · 51% survives to our turn
  • Dra
    13:37:10  pick 31  Rashee Rice (WR) taken by seat 10 in 22 s — a target is gone (was 51% to survive)
    13:37:10  pick 32  Tee Higgins (WR) taken by seat 9 in 0 s INSTANTLY (autopick)
    13:37:11  pick 33  Jeremiyah Love (RB) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    13:37:13  pick 34  Lamar Jackson (QB) taken by seat 7 in 2 s INSTANTLY (autopick)
    13:37:13  pick 35  Breece Hall (RB) taken by seat 6 in 0 s INSTANTLY (autopick)
    13:37:16  plan #29 for pick 36
  • Javonte Williams RB · wait costs 2 · pick costs 0, best pair 75.4 (42.3 now + ~33.1 WR next) · 85% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 1.6 · 93% survives to our turn
  • 
    13:37:19  pick 36  D'Andre Swift (RB) taken by seat 5 in 6 s — a target is gone
    13:37:25  pick 37  Javonte Williams (RB) taken by seat 4 in 5 s — a target is gone (was 85% to survive)
    13:37:25  heartbeat sent (Yahoo told we are not idle)
    13:37:25  plan #30 for pick 38
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 64.3 (33.1 now + ~31.2 WR next) · 83% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 64.3 (31.7 now + ~32
    13:37:25  ON THE CLOCK, pick 38 · plan #30 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    13:37:26  PICKED Garrett Wilson (WR) via action, confirmed in 461 ms — chose Garrett Wilson (WR): nothing urgent, the most valuable player who fills a slot (83% to survive, nobody better worth waiting for)
  • top projection left was Drake 
    13:37:29  plan #31 for pick 39
  • Travis Etienne Jr. RB · wait costs 1 · pick costs 0, best pair 84.1 (31.7 now + ~52.4 WR next) · 73% survives to our turn
  • Drake Maye QB · wait costs 2 · pick costs 16.3 · 83% survives to our turn
  • C
    13:37:56  pick 39  Zay Flowers (WR) taken by seat 2 in 30 s — a target is gone
    13:38:06  pick 40  Travis Etienne Jr. (RB) taken by seat 1 in 10 s — a target is gone (was 73% to survive)
    13:38:06  plan #34 for pick 41
  • Cam Skattebo RB · wait costs 2 · pick costs 0, best pair 82 (31.2 now + ~50.8 WR next) · 86% survives to our turn
  • Drake Maye QB · safe to wait · pick costs 15.8 · 93% survives to our turn
  • Jalen Hur
    13:38:12  pick 41  DJ Moore (WR) taken by seat 1 in 6 s
    13:38:19  plan #35 for pick 42
  • Cam Skattebo RB · safe to wait · pick costs 0, best pair 83.3 (31.2 now + ~52.1 WR next) · 94% survives to our turn
  • Drake Maye QB · safe to wait · pick costs 15.8 · 95% survives to our turn
  • Jalen H
    13:38:25  heartbeat sent (Yahoo told we are not idle)
    13:38:37  pick 42  Ladd McConkey (WR) taken by seat 2 in 25 s
    13:38:38  plan #37 for pick 43
  • Cam Skattebo RB · wait costs 8 · pick costs 0, best pair 76.5 (31.2 now + ~45.3 WR next) · 53% survives to our turn
  • Drake Maye QB · wait costs 11 · pick costs 15.8 · 28% survives to our turn
  • Jalen 
    13:38:38  ON THE CLOCK, pick 43 · plan #37 (0.0 s old) · lineup needs QB RB FLEX K DEF
    13:38:39  PICKED Cam Skattebo (RB) via action, confirmed in 445 ms — chose Cam Skattebo (RB): waiting would likely cost about 8 points at your FLEX spot, 53% to still be there next turn
  • top projection left was Drake Maye, passed on purp
    13:38:41  pick 44  Jaylen Waddle (WR) taken by seat 4 in 2 s — a target is gone
    13:38:42  plan #38 for pick 45
  • Drake Maye QB · wait costs 11 · pick costs 0, best pair 51.8 (15.4 now + ~36.4 WR next) · 28% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 23.7 · 93% survives to our turn
  • Jalen
    13:39:09  pick 45  Tetairoa McMillan (WR) taken by seat 5 in 28 s — a target is gone
    13:39:10  pick 46  Tyler Warren (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    13:39:20  plan #41 for pick 47
  • Drake Maye QB · wait costs 9 · pick costs 0, best pair 51.8 (15.4 now + ~36.4 WR next) · 39% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 26.1 · 94% survives to our turn
  • Jalen 
    13:39:26  heartbeat sent (Yahoo told we are not idle)
    13:39:29  pick 47  Terry McLaurin (WR) taken by seat 7 in 18 s
    13:39:29  pick 48  Bucky Irving (RB) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:39:30  pick 49  Emeka Egbuka (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    13:39:32  plan #42 for pick 50
  • Drake Maye QB · wait costs 7 · pick costs 0, best pair 51.9 (15.4 now + ~36.5 WR next) · 50% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 26.2 · 96% survives to our turn
  • Jalen 
    13:39:38  pick 50  David Montgomery (RB) taken by seat 10 in 8 s
    13:39:43  pick 51  Christian Watson (WR) taken by seat 10 in 5 s
    13:39:43  pick 52  Drake Maye (QB) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone (was 50% to survive)
    13:39:44  plan #43 for pick 53
  • Jalen Hurts QB · wait costs 1 · pick costs 0, best pair 38.8 (2.3 now + ~36.5 WR next) · 36% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 11.8 · 95% survives to our turn
  • Trevor
    13:39:44  pick 53  Joe Burrow (QB) taken by seat 8 in 0 s INSTANTLY (autopick)
    13:39:50  pick 54  Rome Odunze (WR) taken by seat 7 in 6 s
    13:39:50  pick 55  Bhayshul Tuten (RB) taken by seat 6 in 0 s INSTANTLY (autopick)
    13:39:56  plan #44 for pick 56
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 38.8 (2.3 now + ~36.5 WR next) · 64% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 10.9 · 98% survives to our turn
  • Trevor
    13:40:03  pick 56  Rico Dowdle (RB) taken by seat 5 in 13 s
    13:40:04  pick 57  Jayden Daniels (QB) taken by seat 4 in 1 s INSTANTLY (autopick)
    13:40:04  plan #45 for pick 58
  • Jalen Hurts QB · safe to wait · pick costs 0, best pair 38.7 (2.3 now + ~36.4 WR next) · 67% survives to our turn
  • Jaylen Warren RB · safe to wait · pick costs 11.4 · 93% survives to our turn
  • Trevor
    13:40:04  ON THE CLOCK, pick 58 · plan #45 (0.0 s old) · lineup needs QB FLEX K DEF
    13:40:05  PICKED Jalen Hurts (QB) via action, confirmed in 470 ms — chose Jalen Hurts (QB): nothing urgent, the most valuable player who fills a slot (67% to survive, nobody better worth waiting for)
    13:40:08  plan #46 for pick 59
  • Jaylen Warren RB · safe to wait · 93% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    13:40:25  pick 59  Jadarian Price (RB) taken by seat 2 in 20 s
    13:40:26  heartbeat sent (Yahoo told we are not idle)
    13:40:33  plan #48 for pick 60
  • Jaylen Warren RB · safe to wait · 93% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    13:40:53  pick 60  Parker Washington (WR) taken by seat 1 in 27 s
    13:40:57  plan #50 for pick 61
  • Jaylen Warren RB · safe to wait · 97% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • Rhamondre Stevenson RB · depth fallback, engine list done
    13:41:03  pick 61  Rhamondre Stevenson (RB) taken by seat 1 in 10 s — a target is gone
    13:41:09  pick 62  Quinshon Judkins (RB) taken by seat 2 in 6 s — a target is gone
    13:41:10  plan #51 for pick 63
  • Jaylen Warren RB · wait costs 5 · 51% survives to our turn
  • Davante Adams WR · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    13:41:10  ON THE CLOCK, pick 63 · plan #51 (0.0 s old) · lineup needs FLEX K DEF
    13:41:11  PICKED Jaylen Warren (RB) via action, confirmed in 465 ms — chose Jaylen Warren (RB): waiting would likely cost about 5 points at your FLEX spot, 51% to still be there next turn
  • top projection left was Trevor Lawrence, passed 
    13:41:13  pick 64  Tucker Kraft (TE) taken by seat 4 in 2 s
    13:41:14  plan #52 for pick 65
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Davante Adams WR · insurance worth ~26 · 83% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    13:41:29  heartbeat sent (Yahoo told we are not idle)
    13:41:30  pick 65  Caleb Williams (QB) taken by seat 5 in 17 s
    13:41:31  pick 66  Justin Herbert (QB) taken by seat 6 in 1 s INSTANTLY (autopick)
    13:41:33  pick 67  Harold Fannin Jr. (TE) taken by seat 7 in 2 s INSTANTLY (autopick)
    13:41:33  pick 68  Sam LaPorta (TE) taken by seat 8 in 0 s INSTANTLY (autopick)
    13:41:34  pick 69  Kyle Pitts Sr. (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:41:38  plan #54 for pick 70
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Davante Adams WR · insurance worth ~26 · 84% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    13:41:59  pick 70  Isaiah Likely (TE) taken by seat 10 in 25 s
    13:42:02  plan #56 for pick 71
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • Davante Adams WR · insurance worth ~26 · 85% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    13:42:21  pick 71  Rams (DEF) taken by seat 10 in 22 s
    13:42:22  pick 72  Luther Burden III (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    13:42:23  pick 73  Jameson Williams (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    13:42:26  pick 74  Davante Adams (WR) taken by seat 7 in 3 s — a target is gone (was 85% to survive)
    13:42:26  pick 75  Mike Evans (WR) taken by seat 6 in 0 s INSTANTLY (autopick) — a target is gone
    13:42:26  plan #58 for pick 76
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 85% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    13:42:32  heartbeat sent (Yahoo told we are not idle)
    13:42:57  pick 76  TreVeyon Henderson (RB) taken by seat 5 in 30 s — a target is gone
    13:42:57  pick 77  Marvin Harrison Jr. (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    13:42:58  plan #61 for pick 78
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 90% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    13:42:58  ON THE CLOCK, pick 78 · plan #61 (0.0 s old) · lineup needs K DEF
    13:42:59  PICKED Tyrone Tracy Jr. (RB) via action, confirmed in 334 ms — lineup full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +8.3 a week over the wire, about 80 points
  • he also backs up 
    13:43:01  plan #62 for pick 79
  • DK Metcalf WR · insurance worth ~18 · 91% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 97% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:43:07  pick 79  Brian Thomas Jr. (WR) taken by seat 2 in 8 s
    13:43:13  plan #63 for pick 80
  • DK Metcalf WR · insurance worth ~18 · 91% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 97% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:43:24  pick 80  MarShawn Lloyd (RB) taken by seat 1 in 17 s
    13:43:26  plan #64 for pick 81
  • DK Metcalf WR · insurance worth ~18 · 97% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 99% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:43:27  pick 81  Chris Godwin Jr. (WR) taken by seat 1 in 3 s
    13:43:32  heartbeat sent (Yahoo told we are not idle)
    13:43:35  pick 82  Trevor Lawrence (QB) taken by seat 2 in 8 s
    13:43:36  plan #65 for pick 83
  • DK Metcalf WR · insurance worth ~18 · 45% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 78% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:43:36  ON THE CLOCK, pick 83 · plan #65 (0.0 s old) · lineup needs K DEF
    13:43:37  PICKED DK Metcalf (WR) via action, confirmed in 405 ms — lineup full, so DK Metcalf (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.8 a week over the wire, about 18 points
  • top projection left was Patri
    13:43:39  pick 84  Carnell Tate (WR) taken by seat 4 in 2 s — a target is gone
    13:43:39  pick 85  Jonathon Brooks (RB) taken by seat 5 in 0 s
    13:43:39  pick 86  Dak Prescott (QB) taken by seat 6 in 0 s
    13:43:40  plan #66 for pick 87
  • RJ Harvey RB · insurance worth ~16 · 79% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 98% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:43:42  pick 87  Chargers (DEF) taken by seat 7 in 3 s
    13:43:42  pick 88  Tony Pollard (RB) taken by seat 8 in 0 s
    13:43:43  pick 89  J.K. Dobbins (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:43:52  plan #67 for pick 90
  • RJ Harvey RB · insurance worth ~16 · 81% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 99% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    13:44:00  pick 90  Blake Corum (RB) taken by seat 10 in 17 s
    13:44:01  pick 91  De'Zhaun Stribling (WR) taken by seat 10 in 1 s INSTANTLY (autopick)
    13:44:02  pick 92  Michael Wilson (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    13:44:03  pick 93  Josh Downs (WR) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:44:05  plan #68 for pick 94
  • RJ Harvey RB · insurance worth ~16 · 90% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 89% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 99% survives to our t
    13:44:09  pick 94  Will Reichard (K) taken by seat 7 in 6 s
    13:44:10  pick 95  George Kittle (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    13:44:17  pick 96  Matthew Golden (WR) taken by seat 5 in 6 s
    13:44:17  pick 97  Chuba Hubbard (RB) taken by seat 4 in 0 s INSTANTLY (autopick)
    13:44:17  plan #69 for pick 98
  • RJ Harvey RB · insurance worth ~16 · 96% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 89% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 97% survives to our t
    13:44:17  bridge warning: 1 drafted entries matched no board player: 94 Will Reichard
    13:44:17  ON THE CLOCK, pick 98 · plan #69 (0.0 s old) · lineup needs K DEF
    13:44:19  PICKED RJ Harvey (RB) via action, confirmed in 1495 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +6.5 a week over the wire, about 16 points
  • top projection left was Patric
    13:44:22  plan #70 for pick 99
  • Patrick Mahomes II QB · insurance worth ~8 · 90% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 99% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 96% survives to o
    13:44:33  heartbeat sent (Yahoo told we are not idle)
    13:44:45  pick 99  Jacory Croskey-Merritt (RB) taken by seat 2 in 26 s
    13:44:47  plan #72 for pick 100
  • Patrick Mahomes II QB · insurance worth ~8 · 93% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 99% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 97% survives to 
    13:45:01  pick 100  Brock Purdy (QB) taken by seat 1 in 16 s — a target is gone
    13:45:03  pick 101  Jared Goff (QB) taken by seat 1 in 2 s INSTANTLY (autopick)
    13:45:05  pick 102  Alec Pierce (WR) taken by seat 2 in 2 s INSTANTLY (autopick)
    13:45:06  plan #74 for pick 103
  • Patrick Mahomes II QB · insurance worth ~8 · 79% survives to our turn
  • Wan'Dale Robinson WR · insurance worth ~2 · 95% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 89% survives to 
    13:45:06  ON THE CLOCK, pick 103 · plan #74 (0.0 s old) · lineup needs K DEF
    13:45:07  PICKED Patrick Mahomes II (QB) via action, confirmed in 509 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    13:45:09  pick 104  Bo Nix (QB) taken by seat 4 in 2 s — a target is gone
    13:45:10  plan #75 for pick 105
  • Wan'Dale Robinson WR · insurance worth ~2 · 93% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 88% survives to our turn
  • Courtland Sutton WR · depth fallback, engine list done
    13:45:16  pick 105  Makai Lemon (WR) taken by seat 5 in 6 s
    13:45:17  pick 106  Quentin Johnston (WR) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    13:45:19  pick 107  KC Concepcion (WR) taken by seat 7 in 3 s
    13:45:20  pick 108  Jaxson Dart (QB) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:45:21  pick 109  Dalton Kincaid (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:45:22  plan #76 for pick 110
  • Wan'Dale Robinson WR · insurance worth ~2 · 96% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 96% survives to our turn
  • Courtland Sutton WR · depth fallback, engine list done
    13:45:33  heartbeat sent (Yahoo told we are not idle)
    13:45:50  pick 110  Kyle Monangai (RB) taken by seat 10 in 29 s
    13:46:00  plan #79 for pick 111
  • Wan'Dale Robinson WR · insurance worth ~2 · 98% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 98% survives to our turn
  • Courtland Sutton WR · depth fallback, engine list done
    13:46:01  pick 111  Brandon Aubrey (K) taken by seat 10 in 11 s
    13:46:01  pick 112  Matthew Stafford (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    13:46:02  pick 113  Dallas Goedert (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:46:06  pick 114  Courtland Sutton (WR) taken by seat 7 in 5 s — a target is gone
    13:46:07  pick 115  Jordan Mason (RB) taken by seat 6 in 0 s INSTANTLY (autopick)
    13:46:08  pick 116  Kenny Gainwell (RB) taken by seat 5 in 2 s INSTANTLY (autopick) — a target is gone (was 98% to survive)
    13:46:09  pick 117  Travis Kelce (TE) taken by seat 4 in 1 s INSTANTLY (autopick)
    13:46:10  plan #80 for pick 118
  • Wan'Dale Robinson WR · insurance worth ~2 · 98% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 97% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    13:46:10  ON THE CLOCK, pick 118 · plan #80 (0.0 s old) · lineup needs K DEF
    13:46:11  PICKED Wan'Dale Robinson (WR) via action, confirmed in 597 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.7 a week over the wire, about 2 points
  • top projection l
    13:46:13  plan #81 for pick 119
  • Aaron Jones Sr. RB · insurance worth ~1 · 98% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 98% survives to our turn
  • Stefon Diggs WR · depth fallback, engine list done
    13:46:16  pick 119  Juwan Johnson (TE) taken by seat 2 in 5 s
    13:46:26  plan #82 for pick 120
  • Aaron Jones Sr. RB · insurance worth ~1 · 97% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 98% survives to our turn
  • Stefon Diggs WR · depth fallback, engine list done
    13:46:33  pick 120  Mike Washington Jr. (RB) taken by seat 1 in 17 s
    13:46:34  heartbeat sent (Yahoo told we are not idle)
    13:46:35  pick 121  Aaron Jones Sr. (RB) taken by seat 1 in 2 s INSTANTLY (autopick) — a target is gone (was 97% to survive)
    13:46:37  pick 122  Texans (DEF) taken by seat 2 in 2 s INSTANTLY (autopick)
    13:46:38  plan #83 for pick 123
  • Woody Marks RB · insurance worth ~1 · 94% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 94% survives to our turn
  • Stefon Diggs WR · depth fallback, engine list done
    13:46:38  ON THE CLOCK, pick 123 · plan #83 (0.0 s old) · lineup needs K DEF
    13:46:38  PICKED Woody Marks (RB) via action, confirmed in 382 ms — lineup full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +5.0 a week over the wire, about 1 points
  • top projection left was Kyle
    13:46:41  pick 124  Stefon Diggs (WR) taken by seat 4 in 2 s — a target is gone
    13:46:41  plan #84 for pick 125
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 39.3 (14 now + ~25.3 RB next) · 95% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 9.5 · 61% survives to our turn
  • Sea
    13:47:09  pick 125  Kyler Murray (QB) taken by seat 5 in 29 s
    13:47:10  pick 126  Jordan Addison (WR) taken by seat 6 in 1 s INSTANTLY (autopick)
    13:47:13  pick 127  Jayden Reed (WR) taken by seat 7 in 3 s
    13:47:14  pick 128  Michael Pittman Jr. (WR) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:47:15  pick 129  Josh Jacobs (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:47:19  plan #87 for pick 130
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 39.3 (14 now + ~25.3 RB next) · 99% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 9.5 · 78% survives to our turn
  • Sea
    13:47:34  heartbeat sent (Yahoo told we are not idle)
    13:47:38  pick 130  Romeo Doubs (WR) taken by seat 10 in 23 s
    13:47:44  plan #89 for pick 131
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 39.3 (14 now + ~25.3 RB next) · 99% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 9.5 · 74% survives to our turn
  • Sea
    13:48:07  pick 131  Sam Darnold (QB) taken by seat 10 in 29 s
    13:48:08  pick 132  Broncos (DEF) taken by seat 9 in 1 s INSTANTLY (autopick)
    13:48:09  pick 133  Seahawks (DEF) taken by seat 8 in 1 s INSTANTLY (autopick)
    13:48:09  plan #91 for pick 134
  • Philadelphia Eagles DEF · safe to wait · pick costs 0, best pair 33.3 (8 now + ~25.3 RB next) · 77% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 3.5 · 85% survives to our turn
  •
    13:48:12  pick 134  Chris Rodriguez Jr. (RB) taken by seat 7 in 3 s
    13:48:13  pick 135  Ka'imi Fairbairn (K) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    13:48:14  pick 136  Eagles (DEF) taken by seat 5 in 1 s INSTANTLY (autopick)
    13:48:15  pick 137  Cameron Dicker (K) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 85% to survive)
    13:48:15  plan #92 for pick 138
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 29.2 (4 now + ~25.2 RB next) · 77% survives to our turn
  • Cam Little K · safe to wait · pick costs 1 · 82% survives to our turn
  • Minne
    13:48:15  ON THE CLOCK, pick 138 · plan #92 (0.0 s old) · lineup needs K DEF
    13:48:16  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 346 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (77% to survive, nobody better worth waiting for)
  • top projection lef
    13:48:19  plan #93 for pick 139
  • Cam Little K · safe to wait · 86% survives to our turn
  • Jason Myers K · depth fallback, engine list done
  • Eddy Pineiro K · depth fallback, engine list done
    13:48:30  pick 139  Spencer Shrader (K) taken by seat 2 in 14 s
    13:48:30  pick 140  Jason Myers (K) taken by seat 1 in 0 s INSTANTLY (autopick) — a target is gone
    13:48:31  pick 141  Vikings (DEF) taken by seat 1 in 1 s INSTANTLY (autopick)
    13:48:31  plan #94 for pick 142
  • Cam Little K · safe to wait · 96% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    13:48:31  bridge warning: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    13:48:34  heartbeat sent (Yahoo told we are not idle)
    13:48:56  pick 142  Rachaad White (RB) taken by seat 2 in 25 s
    13:48:57  plan #96 for pick 141
  • Cam Little K · safe to wait · 95% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    13:48:57  bridge warning: dropped 1 feed entries numbered >= header pick 142
    13:48:57  bridge warning: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    13:48:58  plan #97 for pick 143
  • Cam Little K
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    13:48:58  ON THE CLOCK, pick 143 · plan #97 (0.0 s old) · lineup needs K
    13:48:58  PICKED Cam Little (K) via action, confirmed in 269 ms — chose Cam Little (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Baker Mayfield, passed on purpose
    13:49:01  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    13:32:24 PT preflight: ok=true pick_path=action my_team=3 plan=plan 25 deep @pick 1 via store call#1
    13:32:24 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    13:32:24 PT NARR info driver started — seat 3, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    13:33:24 PT heartbeat: setAwayStatus(false)
    13:33:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:33:35 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills you
    13:34:24 PT heartbeat: setAwayStatus(false)
    13:34:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:35:10 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~5 pts at TE (best option now 78, ~73 by your next turn) · 81% chance he's still there at your next pick · fills your open TE 
    13:35:24 PT heartbeat: setAwayStatus(false)
    13:35:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:35:59 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~8 pts at WR (best option now 40, ~32 by your next turn) · 20% chance he's still there at your next pick · fills your open WR s
    13:36:25 PT heartbeat: setAwayStatus(false)
    13:36:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:37:25 PT heartbeat: setAwayStatus(false)
    13:37:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:37:26 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"safe to wait on WR · 83% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pic
    13:38:25 PT heartbeat: setAwayStatus(false)
    13:38:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:38:39 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~8 pts at your FLEX spot (best option now 26, ~18 by your next turn) · 53% chance he's still there at your next pick · fills you
    13:39:26 PT heartbeat: setAwayStatus(false)
    13:39:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:40:05 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 67% chance he's still there at your next pick · fills your open QB slot · 4 teams picking before you still need a QB · two-pick p
    13:40:26 PT heartbeat: setAwayStatus(false)
    13:40:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:41:11 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 51% chance he's still there at your next pick · fills a F
    13:41:29 PT heartbeat: setAwayStatus(false)
    13:41:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:42:32 PT heartbeat: setAwayStatus(false)
    13:42:32 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:42:59 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo"
    13:43:32 PT heartbeat: setAwayStatus(false)
    13:43:32 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:43:37 PT ON CLOCK -> {"drafted":"DK Metcalf","pos":"WR","vorp":-9.2,"proj":132.9,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bateman) ≈ 18 pts","s":0.45,"sr":0.45,"e":-9.9,"top_proj_availa
    13:44:17 PT BRIDGE WARNING: 1 drafted entries matched no board player: 94 Will Reichard
    13:44:19 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5/wk over the wire (Ollie Gordon II) ≈ 16 pts","s":0.959,"sr"
    13:44:33 PT heartbeat: setAwayStatus(false)
    13:44:33 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:45:07 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.793,"sr":0.793,"e":11.4,"top_pr
    13:45:33 PT heartbeat: setAwayStatus(false)
    13:45:33 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:46:11 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.9
    13:46:34 PT heartbeat: setAwayStatus(false)
    13:46:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:46:38 PT ON CLOCK -> {"drafted":"Woody Marks","pos":"RB","vorp":-30.3,"proj":129.9,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5.0/wk over the wire (Ollie Gordon II) ≈ 1 pts","s":0.941,"
    13:47:34 PT heartbeat: setAwayStatus(false)
    13:47:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:48:16 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 77% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · t
    13:48:31 PT BRIDGE WARNING: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    13:48:34 PT heartbeat: setAwayStatus(false)
    13:48:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:48:57 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 142
    13:48:57 PT BRIDGE WARNING: 2 drafted entries matched no board player: 94 Will Reichard, 139 Spencer Shrader
    13:48:58 PT ON CLOCK -> {"drafted":"Cam Little","pos":"K","vorp":9,"proj":145.5,"why":"fills your open K slot · bargain: still here 14 picks after he's usually drafted","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield",
    13:49:01 PT roster full
    13:49:01 PT NARR info roster full — driver done; posting the trail when the room finishes
    13:49:01 PT driver stop


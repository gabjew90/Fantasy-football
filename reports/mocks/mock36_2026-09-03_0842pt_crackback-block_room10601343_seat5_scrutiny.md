# Scrutiny: Mock 36 -- Crackback Block (room 10601343) -- Thursday 2026-09-03 08:42 PT -- 10 teams, our seat 5

Captured 2026-09-03 09:03:49 PT. Times below are Pacific. 10 teams, our team id 5, draft slot 5. 150 picks in the trail, 118 bridge plan calls, 85 recs events in the room log.

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
- Action latency to store confirmation: median 402 ms, min 276, max 547.
- Heartbeats 20; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (1): 1 drafted entries matched no board player: 143 Will Reichard.
- Away seats over the room (each change): {} -> {1,2} -> {1} -> {1,2} -> {1,2,3} -> {1,2} -> {1,2,6} -> {1,2,3} -> {1,2} -> {1,2,7} -> {1,2} -> {1,2,7} -> {1,2} -> {1,2,7} -> {1,2,4,7} -> {1,2,7} -> {1,2,3,7}.
- Managers away at the end: 1 Troy, 2 Kelvin, 3 Bert, 7 Aj, 8 Richard.

## Our picks, one block each

### Pick 5 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 36 points at RB, with a 48% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 402 ms, ranker engine, plan call 10, plan age 726 ms, at 08:44:07 PT.
- Engine's reason: waiting likely costs ~36 pts at RB (best option now 154, ~118 by your next turn) · 48% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 10 te
- Top projection available: Josh Allen -> took it: False.
- Passed on: Jaxon Smith-Njigba (WR, s=0.4, e=74.5); Trey McBride (TE, s=0.935, e=76.2); Josh Allen (QB, s=0.731, e=42.7).
- Plan call 10 @pick 5: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1], state store with 4 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.48 | 0.48 | 117.9 | 154.2 | waiting likely costs ~36 pts at RB (best option now 154, ~118 by your next turn) · 48% cha |
| Jaxon Smith-Njigba | WR | 89.4 | 0.40 | 0.40 | 74.5 | 89.4 | waiting likely costs ~15 pts at WR (best option now 89, ~74 by your next turn) · 40% chanc |
| Trey McBride | TE | 77.9 | 0.94 | 0.94 | 76.2 | 77.9 | waiting likely costs ~2 pts at TE (best option now 78, ~76 by your next turn) · 94% chance |
| Josh Allen | QB | 47.0 | 0.73 | 0.73 | 42.7 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 73% chance |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Amon-Ra St. Brown | WR | 81.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.7 | 4.3 | 6 |
| RB | 154.2 | 117.9 | 36.3 | 23 |
| WR | 89.4 | 74.5 | 14.9 | 23 |
| TE | 77.9 | 76.2 | 1.7 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 119.2 | 35.1 | 52 |

### Pick 16 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 25 points at RB, with a 26% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 439 ms, ranker engine, plan call 19, plan age 755 ms, at 08:45:40 PT.
- Engine's reason: waiting likely costs ~25 pts at RB (best option now 73, ~48 by your next turn) · 26% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 8 teams picking befo
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.702, e=67.6); Drake London (WR, s=0.433, e=45.8); Josh Allen (QB, s=0.556, e=39.8).
- Plan call 19 @pick 16: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1], state store with 15 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.26 | 0.26 | 48.2 | 73.4 | waiting likely costs ~25 pts at RB (best option now 73, ~48 by your next turn) · 26% chanc |
| Trey McBride | TE | 77.9 | 0.70 | 0.70 | 67.6 | 77.9 | waiting likely costs ~10 pts at TE (best option now 78, ~68 by your next turn) · 70% chanc |
| Drake London | WR | 51.0 | 0.43 | 0.43 | 45.8 | 51.0 | waiting likely costs ~5 pts at WR (best option now 51, ~46 by your next turn) · 43% chance |
| Josh Allen | QB | 47.0 | 0.56 | 0.56 | 39.8 | 47.0 | waiting likely costs ~7 pts at QB (best option now 47, ~40 by your next turn) · 56% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 39.8 | 7.2 | 9 |
| RB | 73.4 | 48.2 | 25.2 | 18 |
| WR | 51.0 | 45.8 | 5.2 | 23 |
| TE | 77.9 | 67.6 | 10.3 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 48.7 | 24.7 | 49 |

### Pick 25 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 22 points at TE, with a 59% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 432 ms, ranker engine, plan call 24, plan age 758 ms, at 08:46:30 PT.
- Engine's reason: waiting likely costs ~22 pts at TE (best option now 78, ~56 by your next turn) · 59% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 10 team
- Top projection available: Josh Allen -> took it: False.
- Passed on: Rashee Rice (WR, s=0.479, e=29.1); Josh Allen (QB, s=0.754, e=42.7); Kyren Williams (RB, s=None, e=None).
- Plan call 24 @pick 25: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 24 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.59 | 0.59 | 55.7 | 77.9 | waiting likely costs ~22 pts at TE (best option now 78, ~56 by your next turn) · 59% chanc |
| Rashee Rice | WR | 34.1 | 0.48 | 0.48 | 29.1 | 34.1 | waiting likely costs ~5 pts at WR (best option now 34, ~29 by your next turn) · 48% chance |
| Josh Allen | QB | 47.0 | 0.75 | 0.75 | 42.7 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 75% chance |
| Kyren Williams | RB | 40.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.7 | 4.3 | 10 |
| RB | 40.5 | 36.3 | 4.2 | 17 |
| WR | 34.1 | 29.1 | 5.0 | 22 |
| TE | 77.9 | 55.7 | 22.2 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 38.9 | 1.7 | 47 |

### Pick 36 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 3 points at WR, with a 70% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 420 ms, ranker engine, plan call 36, plan age 744 ms, at 08:48:41 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 26, ~22 by your next turn) · 70% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.489, e=24.2); Drake Maye (QB, s=0.69, e=27); Malik Nabers (WR, s=None, e=None).
- Plan call 36 @pick 36: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 35 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.70 | 0.70 | 22.5 | 25.9 | waiting likely costs ~3 pts at WR (best option now 26, ~22 by your next turn) · 70% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.49 | 0.49 | 24.2 | 26.3 | waiting likely costs ~2 pts at your FLEX spot (best option now 26, ~24 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.69 | 0.69 | 27.0 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 69% chance |
| Malik Nabers | WR | 25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 27.0 | 4.1 | 10 |
| RB | 26.3 | 24.2 | 2.1 | 19 |
| WR | 25.9 | 22.5 | 3.4 | 18 |
| TE | 23.8 | 23.0 | 0.8 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 24.2 | 2.1 | 44 |

### Pick 45 (round 5): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB) because waiting would likely cost about 6 points at your FLEX spot, with a 64% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 483 ms, ranker engine, plan call 43, plan age 808 ms, at 08:49:53 PT.
- Engine's reason: waiting likely costs ~6 pts at your FLEX spot (best option now 26, ~20 by your next turn) · 64% chance he's still there at your next pick · fills a FLEX slot · last RB at this level — big drop after him · 10 teams pickin
- Top projection available: Drake Maye -> took it: False.
- Passed on: Davante Adams (WR, s=0.632, e=9); Drake Maye (QB, s=0.604, e=25.5); Jalen Hurts (QB, s=None, e=None).
- Plan call 43 @pick 45: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 44 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.64 | 0.64 | 19.9 | 25.8 | waiting likely costs ~6 pts at your FLEX spot (best option now 26, ~20 by your next turn)  |
| Davante Adams | WR | 13.1 | 0.63 | 0.63 | 9.0 | 13.1 | waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 63% chance  |
| Drake Maye | QB | 31.1 | 0.60 | 0.60 | 25.5 | 31.1 | waiting likely costs ~6 pts at QB (best option now 31, ~26 by your next turn) · 60% chance |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.5 | 5.6 | 13 |
| RB | 25.8 | 19.8 | 6.0 | 17 |
| WR | 13.1 | 9.0 | 4.1 | 18 |
| TE | 23.8 | 22.5 | 1.3 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 19.9 | 6.0 | 43 |

### Pick 56 (round 6): Jameson Williams (WR)

- In plain English: Took Jameson Williams (WR): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (70% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 388 ms, ranker engine, plan call 56, plan age 708 ms, at 08:52:17 PT.
- Engine's reason: safe to wait on WR · 70% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · two-pick plan: pair with the ~9-pt RB expected at your next turn
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jalen Hurts (QB, s=0.558, e=16.9); Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None).
- Plan call 56 @pick 56: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 55 drafted / 5 mine.
- Engine's first choice was **Jameson Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jameson Williams | WR | 0.0 | 0.70 | 0.70 | -0.2 | 0.0 | safe to wait on WR · 70% chance he's still there at your next pick · fills your open WR sl |
| Jalen Hurts | QB | 18.0 | 0.56 | 0.56 | 16.9 | 18.0 | waiting likely costs ~1 pts at QB (best option now 18, ~17 by your next turn) · 56% chance |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaylen Warren | RB | 9.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.9 | 1.1 | 14 |
| RB | 9.3 | 8.9 | 0.4 | 17 |
| WR | 0.0 | -0.2 | 0.2 | 20 |
| TE | 21.1 | 20.6 | 0.5 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 65 (round 7): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB) because waiting would likely cost about 1 points at QB, with a 67% chance he would still be there next turn.
- Driver: via **action**, verified store, 398 ms, ranker engine, plan call 60, plan age 725 ms, at 08:52:49 PT.
- Engine's reason: waiting likely costs ~1 pts at QB (best option now 18, ~17 by your next turn) · 67% chance he's still there at your next pick · fills your open QB slot · 6 teams picking before you still need a QB · 9 picks past his usua
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None); Caleb Williams (QB, s=None, e=None).
- Plan call 60 @pick 65: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 64 drafted / 6 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.67 | 0.67 | 16.9 | 18.0 | waiting likely costs ~1 pts at QB (best option now 18, ~17 by your next turn) · 67% chance |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaylen Warren | RB | 9.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Justin Herbert | QB | 7.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.9 | 1.1 | 20 |
| RB | 9.3 | 6.5 | 2.8 | 20 |
| WR | -0.8 | -1.7 | 0.9 | 24 |
| TE | 21.1 | 18.5 | 2.6 | 12 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 76 (round 8): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +8.3 points a week over the waiver wire (Ollie Gordon II), worth about 80 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 366 ms, ranker engine, plan call 72, plan age 685 ms, at 08:55:05 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.578, e=-9.7); Kenny Gainwell (RB, s=None, e=None); Marvin Harrison Jr. (WR, s=None, e=None).
- Plan call 72 @pick 76: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 75 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 0.99 | 0.99 | -6.3 | -6.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordo |
| DK Metcalf | WR | -9.2 | 0.58 | 0.58 | -9.7 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Rico Dowdle | RB | -11.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.5 | 1.2 | 21 |
| RB | -6.2 | -6.3 | 0.1 | 32 |
| WR | -9.2 | -9.7 | 0.5 | 38 |
| TE | 21.1 | 18.5 | 2.6 | 20 |
| K | 13.5 | 13.4 | 0.1 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 7 |

### Pick 85 (round 9): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 380 ms, ranker engine, plan call 76, plan age 731 ms, at 08:55:47 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.92, e=-6.7); Kyle Pitts Sr. (TE, s=0.837, e=19.7); Dallas Goedert (TE, s=None, e=None).
- Plan call 76 @pick 85: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2], state store with 84 drafted / 8 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.96 | 0.96 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Kenny Gainwell | RB | -6.2 | 0.92 | 0.92 | -6.7 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.4 |
| Kyle Pitts Sr. | TE | 21.1 | 0.84 | 0.84 | 19.7 | 21.1 | bench insurance: covers 1 TE starter ~3.9 wks/season · +2.9/wk over the wire (Cade Otton)  |
| Dallas Goedert | TE | 13.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Kelce | TE | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Ferguson | TE | 0.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.9 | 1.9 | 18 |
| RB | -6.2 | -6.7 | 0.5 | 29 |
| WR | -10.6 | -10.6 | 0.0 | 38 |
| TE | 21.1 | 19.7 | 1.4 | 20 |
| K | 13.5 | 13.5 | 0.0 | 12 |
| DEF | 18.0 | 17.9 | 0.1 | 10 |

### Pick 96 (round 10): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +6.4 points a week over the waiver wire (Ollie Gordon II), worth about 16 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 512 ms, ranker engine, plan call 88, plan age 841 ms, at 08:57:58 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.4/wk over the wire (Ollie Gordon II) ≈ 16 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.82, e=11.2); Courtland Sutton (WR, s=0.785, e=-11.6); Bo Nix (QB, s=None, e=None).
- Plan call 88 @pick 96: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 7], state store with 95 drafted / 9 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.94 | 0.94 | -7.4 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.4 |
| Patrick Mahomes II | QB | 12.8 | 0.82 | 0.82 | 11.2 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Courtland Sutton | WR | -11.1 | 0.79 | 0.79 | -11.6 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.2 | 1.6 | 17 |
| RB | -6.2 | -7.4 | 1.2 | 27 |
| WR | -11.1 | -11.6 | 0.5 | 34 |
| TE | 13.8 | 12.9 | 0.9 | 19 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 10 |

### Pick 105 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 375 ms, ranker engine, plan call 93, plan age 713 ms, at 08:58:47 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Courtland Sutton (WR, s=0.889, e=-11.5); Aaron Jones Sr. (RB, s=0.917, e=-26.2); Bo Nix (QB, s=None, e=None).
- Plan call 93 @pick 105: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 7], state store with 104 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.90 | 0.90 | 11.9 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Courtland Sutton | WR | -11.1 | 0.89 | 0.89 | -11.5 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.92 | 0.92 | -26.2 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5. |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.9 | 0.9 | 17 |
| RB | -25.9 | -26.2 | 0.3 | 22 |
| WR | -11.1 | -11.5 | 0.4 | 30 |
| TE | 13.8 | 13.4 | 0.4 | 19 |
| K | 12.0 | 11.8 | 0.2 | 14 |
| DEF | 18.0 | 17.4 | 0.6 | 12 |

### Pick 116 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Jaxson Dart; the engine passed on him on purpose.
- Driver: via **action**, verified store, 500 ms, ranker engine, plan call 101, plan age 861 ms, at 09:00:11 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Jaxson Dart -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.946, e=-26.1); Jakobi Meyers (WR, s=None, e=None); Makai Lemon (WR, s=None, e=None).
- Plan call 101 @pick 116: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 7], state store with 115 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.94 | 0.94 | -13.8 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.95 | 0.95 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -10.9 | -10.9 | 0.0 | 14 |
| RB | -25.9 | -26.1 | 0.2 | 21 |
| WR | -13.3 | -13.8 | 0.5 | 27 |
| TE | 13.8 | 12.9 | 0.9 | 18 |
| K | 10.5 | 9.9 | 0.6 | 14 |
| DEF | 16.0 | 10.8 | 5.2 | 11 |

### Pick 125 (round 13): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +5.2 points a week over the waiver wire (Ollie Gordon II), worth about 1 points. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 547 ms, ranker engine, plan call 107, plan age 880 ms, at 09:01:14 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5.2/wk over the wire (Ollie Gordon II) ≈ 1 pts
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.897, e=-22.2); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 107 @pick 125: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 7], state store with 124 drafted / 12 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.93 | 0.93 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5. |
| Jakobi Meyers | WR | -21.5 | 0.90 | 0.90 | -22.2 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +2. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyle Monangai | RB | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -25.9 | -26.1 | 0.2 | 21 |
| WR | -21.5 | -22.2 | 0.7 | 24 |
| TE | 0.5 | 0.3 | 0.2 | 14 |
| K | 10.5 | 10.0 | 0.5 | 15 |
| DEF | 16.0 | 12.7 | 3.3 | 11 |

### Pick 136 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF) because waiting would likely cost about 1 points at DEF, with a 81% chance he would still be there next turn. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 346 ms, ranker engine, plan call 114, plan age 680 ms, at 09:02:33 PT.
- Engine's reason: waiting likely costs ~1 pts at DEF (best option now 8, ~7 by your next turn) · 81% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · two-pick plan: pair 
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Cam Little (K, s=0.668, e=8.2); Cameron Dicker (K, s=None, e=None); Minnesota Vikings (DEF, s=None, e=None).
- Plan call 114 @pick 136: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 7], state store with 135 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.81 | 0.81 | 6.5 | 8.0 | waiting likely costs ~1 pts at DEF (best option now 8, ~7 by your next turn) · 81% chance  |
| Cam Little | K | 9.0 | 0.67 | 0.67 | 8.2 | 10.5 | waiting likely costs ~2 pts at K (best option now 10, ~8 by your next turn) · 67% chance h |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 10 |
| RB | -28.8 | -28.8 | 0.0 | 16 |
| WR | -21.5 | -21.9 | 0.4 | 24 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 10.5 | 8.2 | 2.3 | 15 |
| DEF | 8.0 | 6.5 | 1.5 | 9 |

### Pick 145 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 276 ms, ranker engine, plan call 118, plan age 647 ms, at 09:03:05 PT.
- Engine's reason: fills your open K slot
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 118 @pick 145: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 3, 7], state store with 144 drafted / 14 mine, warnings ['1 drafted entries matched no board player: 143 Will Reichard'].
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
| 0-30% | 3 | 23% | 0% |
| 30-50% | 17 | 44% | 12% |
| 50-70% | 38 | 62% | 39% |
| 70-90% | 67 | 82% | 67% |
| 90-100% | 85 | 95% | 86% |

210 predictions over 84 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T09:03:00   WARNING plan #117: 1 drafted entries matched no board player: 143 Will Reichard
    2026-09-03T09:03:04   WARNING plan #118: 1 drafted entries matched no board player: 143 Will Reichard

## Narration (what the panel showed live, Pacific time)

    08:42:22  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 11 · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next) · 65% survives to our turn
  • Ja'Marr Chase WR · wait costs 7 · pick costs 17.7 · 64% survives to our turn
    08:42:24  driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    08:43:07  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    08:43:08  pick 2  Bijan Robinson (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:43:13  plan #6 for pick 3
  • Christian McCaffrey RB · wait costs 14 · pick costs 0, best pair 281.2 (159.6 now + ~121.6 WR next) · 74% survives to our turn
  • Ja'Marr Chase WR · wait costs 3 · pick costs 11.1 · 82% survives to our turn
    08:43:24  heartbeat sent (Yahoo told we are not idle)
    08:43:38  pick 3  Ja'Marr Chase (WR) taken by seat 3 in 30 s — a target is gone (was 82% to survive)
    08:43:49  plan #9 for pick 4
  • Christian McCaffrey RB · wait costs 7 · pick costs 0, best pair 269.3 (159.6 now + ~109.7 RB next) · 85% survives to our turn
  • Puka Nacua WR · wait costs 1 · pick costs 7.9 · 90% survives to our turn
  • 
    08:43:50  pick 4  Puka Nacua (WR) taken by seat 4 in 12 s — a target is gone (was 90% to survive)
    08:44:06  plan #10 for pick 5
  • Christian McCaffrey RB · wait costs 36 · pick costs 0, best pair 269.3 (159.6 now + ~109.7 RB next) · 48% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 15 · pick costs 47.4 · 40% survives to o
    08:44:06  ON THE CLOCK, pick 5 · plan #10 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    08:44:07  PICKED Christian McCaffrey (RB) via action, confirmed in 402 ms — chose Christian McCaffrey (RB): waiting would likely cost about 36 points at RB, 48% to still be there next turn
  • top projection left was Josh Allen, passed on p
    08:44:10  plan #11 for pick 6
  • Jonathan Taylor RB · wait costs 25 · pick costs 0, best pair 193.3 (109.7 now + ~83.6 WR next) · 40% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 15 · pick costs 9.7 · 40% survives to our tur
    08:44:15  pick 6  Jonathan Taylor (RB) taken by seat 6 in 8 s — a target is gone (was 40% to survive)
    08:44:22  plan #12 for pick 7
  • Jaxon Smith-Njigba WR · wait costs 13 · pick costs 0, best pair 184.7 (98.6 now + ~86.1 WR next) · 45% survives to our turn
  • De'Von Achane RB · wait costs 10 · pick costs 19.8 · 40% survives to our turn

    08:44:27  pick 7  Jaxon Smith-Njigba (WR) taken by seat 7 in 12 s — a target is gone (was 45% to survive)
    08:44:27  heartbeat sent (Yahoo told we are not idle)
    08:44:29  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 2 s INSTANTLY (autopick) — a target is gone
    08:44:34  plan #13 for pick 9
  • De'Von Achane RB · wait costs 8 · pick costs 0, best pair 147.9 (78.8 now + ~69.1 RB next) · 46% survives to our turn
  • CeeDee Lamb WR · wait costs 3 · pick costs 11 · 46% survives to our turn
  • Trey Mc
    08:44:38  pick 9  Saquon Barkley (RB) taken by seat 9 in 9 s
    08:44:44  pick 10  James Cook III (RB) taken by seat 10 in 7 s — a target is gone
    08:44:46  plan #14 for pick 11
  • De'Von Achane RB · wait costs 7 · pick costs 0, best pair 144.7 (78.8 now + ~65.9 RB next) · 58% survives to our turn
  • CeeDee Lamb WR · wait costs 2 · pick costs 7.1 · 64% survives to our turn
  • Trey 
    08:44:48  pick 11  CeeDee Lamb (WR) taken by seat 10 in 3 s — a target is gone (was 64% to survive)
    08:44:59  pick 12  Derrick Henry (RB) taken by seat 9 in 11 s
    08:44:59  plan #15 for pick 13
  • De'Von Achane RB · wait costs 5 · pick costs 0, best pair 144.7 (78.8 now + ~65.9 RB next) · 71% survives to our turn
  • Trey McBride TE · wait costs 1 · pick costs 6.6 · 94% survives to our turn
  • Just
    08:45:07  pick 13  Chase Brown (RB) taken by seat 8 in 8 s — a target is gone
    08:45:11  plan #16 for pick 14
  • De'Von Achane RB · wait costs 7 · pick costs 0, best pair 141.8 (78.8 now + ~63 TE next) · 78% survives to our turn
  • Trey McBride TE · wait costs 1 · pick costs 6.1 · 94% survives to our turn
  • Justin
    08:45:28  heartbeat sent (Yahoo told we are not idle)
    08:45:33  pick 14  Justin Jefferson (WR) taken by seat 7 in 27 s — a target is gone (was 84% to survive)
    08:45:36  plan #18 for pick 15
  • De'Von Achane RB · wait costs 3 · pick costs 0, best pair 142.6 (78.8 now + ~63.8 TE next) · 90% survives to our turn
  • Trey McBride TE · safe to wait · pick costs 3.1 · 98% survives to our turn
  • Drak
    08:45:38  pick 15  Kenneth Walker III (RB) taken by seat 6 in 5 s
    08:45:39  plan #19 for pick 16
  • De'Von Achane RB · wait costs 25 · pick costs 0, best pair 133.9 (78.8 now + ~55.1 WR next) · 26% survives to our turn
  • Trey McBride TE · wait costs 10 · pick costs 14.6 · 70% survives to our turn
  • D
    08:45:39  ON THE CLOCK, pick 16 · plan #19 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    08:45:40  PICKED De'Von Achane (RB) via action, confirmed in 439 ms — chose De'Von Achane (RB): waiting would likely cost about 25 points at RB, 26% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    08:45:42  plan #20 for pick 17
  • Trey McBride TE · wait costs 12 · pick costs 0, best pair 118.9 (64.2 now + ~54.7 WR next) · 67% survives to our turn
  • Drake London WR · wait costs 6 · pick costs 5.8 · 41% survives to our turn
  • Josh
    08:45:42  pick 17  Omarion Hampton (RB) taken by seat 4 in 3 s
    08:45:45  pick 18  Brock Bowers (TE) taken by seat 3 in 2 s — a target is gone
    08:45:54  plan #21 for pick 19
  • Trey McBride TE · wait costs 16 · pick costs 0, best pair 119.1 (64.2 now + ~54.9 WR next) · 70% survives to our turn
  • Drake London WR · wait costs 5 · pick costs 6 · 39% survives to our turn
  • Josh A
    08:46:13  pick 19  Nico Collins (WR) taken by seat 2 in 29 s — a target is gone
    08:46:14  pick 20  Drake London (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone (was 39% to survive)
    08:46:15  pick 21  Ashton Jeanty (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:46:16  pick 22  George Pickens (WR) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:46:19  plan #23 for pick 23
  • Trey McBride TE · wait costs 6 · pick costs 0, best pair 116.3 (64.2 now + ~52.1 WR next) · 89% survives to our turn
  • A.J. Brown WR · safe to wait · pick costs 5.2 · 81% survives to our turn
  • Josh Al
    08:46:23  pick 23  A.J. Brown (WR) taken by seat 3 in 6 s — a target is gone (was 81% to survive)
    08:46:27  pick 24  Chris Olave (WR) taken by seat 4 in 5 s — a target is gone
    08:46:28  heartbeat sent (Yahoo told we are not idle)
    08:46:29  plan #24 for pick 25
  • Trey McBride TE · wait costs 22 · pick costs 0, best pair 108.4 (64.2 now + ~44.2 RB next) · 59% survives to our turn
  • Rashee Rice WR · wait costs 5 · pick costs 20.8 · 48% survives to our turn
  • Josh
    08:46:29  ON THE CLOCK, pick 25 · plan #24 (0.0 s old) · lineup needs QB WRx2 TE FLEX K DEF
    08:46:30  PICKED Trey McBride (TE) via action, confirmed in 432 ms — chose Trey McBride (TE): waiting would likely cost about 22 points at TE, 59% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    08:46:32  plan #25 for pick 26
  • Rashee Rice WR · wait costs 5 · pick costs 0, best pair 84.7 (43.4 now + ~41.3 RB next) · 45% survives to our turn
  • Kyren Williams RB · wait costs 5 · pick costs 0.6 · 50% survives to our turn
  • Josh 
    08:46:37  pick 26  Josh Allen (QB) taken by seat 6 in 7 s — a target is gone (was 72% to survive)
    08:46:45  plan #26 for pick 27
  • Rashee Rice WR · wait costs 5 · pick costs 0, best pair 85.4 (43.4 now + ~42 RB next) · 50% survives to our turn
  • Kyren Williams RB · wait costs 4 · pick costs 0.8 · 55% survives to our turn
  • Drake M
    08:46:53  pick 27  Kyren Williams (RB) taken by seat 7 in 16 s — a target is gone (was 55% to survive)
    08:46:57  plan #27 for pick 28
  • Rashee Rice WR · wait costs 5 · pick costs 0, best pair 80.9 (43.4 now + ~37.5 RB next) · 48% survives to our turn
  • Javonte Williams RB · wait costs 5 · pick costs 0.1 · 57% survives to our turn
  • Dra
    08:46:57  pick 28  Javonte Williams (RB) taken by seat 8 in 4 s — a target is gone (was 57% to survive)
    08:47:10  plan #28 for pick 29
  • Rashee Rice WR · wait costs 4 · pick costs 0, best pair 78.6 (43.4 now + ~35.2 WR next) · 58% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · pick costs 7.3 · 73% survives to our turn
  • D
    08:47:21  pick 29  Rashee Rice (WR) taken by seat 9 in 24 s — a target is gone (was 58% to survive)
    08:47:22  plan #29 for pick 30
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 66.2 (33.1 now + ~33.1 WR next) · 88% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · pick costs 0.1 · 72% survives to our turn
  
    08:47:29  heartbeat sent (Yahoo told we are not idle)
    08:47:44  pick 30  Jeremiyah Love (RB) taken by seat 10 in 22 s — a target is gone
    08:47:44  pick 31  DeVonta Smith (WR) taken by seat 10 in 0 s INSTANTLY (autopick) — a target is gone
    08:47:46  plan #31 for pick 32
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 66.4 (31.7 now + ~34.7 WR next) · 80% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 0.2 · 90% survives to our turn
  
    08:48:06  pick 32  Emeka Egbuka (WR) taken by seat 9 in 22 s
    08:48:09  pick 33  Zay Flowers (WR) taken by seat 8 in 4 s — a target is gone
    08:48:11  plan #33 for pick 34
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 66.5 (31.7 now + ~34.8 WR next) · 90% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 0.3 · 92% survives to our turn
  
    08:48:29  heartbeat sent (Yahoo told we are not idle)
    08:48:39  pick 34  Ladd McConkey (WR) taken by seat 7 in 30 s
    08:48:40  pick 35  Colston Loveland (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    08:48:41  plan #36 for pick 36
  • Garrett Wilson WR · wait costs 3 · pick costs 0, best pair 64.9 (33.1 now + ~31.8 WR next) · 71% survives to our turn
  • Travis Etienne Jr. RB · wait costs 2 · pick costs 1.4 · 49% survives to our turn
  
    08:48:41  ON THE CLOCK, pick 36 · plan #36 (0.0 s old) · lineup needs QB WRx2 FLEX K DEF
    08:48:41  PICKED Garrett Wilson (WR) via action, confirmed in 420 ms — chose Garrett Wilson (WR): waiting would likely cost about 3 points at WR, 71% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    08:48:44  plan #37 for pick 37
  • Malik Nabers WR · wait costs 9 · pick costs 0, best pair 64.5 (35.2 now + ~29.3 RB next) · 21% survives to our turn
  • Travis Etienne Jr. RB · wait costs 2 · pick costs 6.5 · 48% survives to our turn
  • 
    08:49:01  pick 37  Malik Nabers (WR) taken by seat 4 in 19 s — a target is gone (was 21% to survive)
    08:49:04  pick 38  Travis Etienne Jr. (RB) taken by seat 3 in 4 s — a target is gone (was 48% to survive)
    08:49:04  pick 39  Tee Higgins (WR) taken by seat 2 in 0 s INSTANTLY (autopick)
    08:49:05  pick 40  Breece Hall (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:49:06  pick 41  Jaylen Waddle (WR) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:49:07  pick 42  D'Andre Swift (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:49:08  plan #39 for pick 43
  • Cam Skattebo RB · wait costs 3 · pick costs 0, best pair 55.7 (31.2 now + ~24.5 WR next) · 85% survives to our turn
  • Tetairoa McMillan WR · safe to wait · pick costs 2.4 · 92% survives to our turn
  • D
    08:49:30  heartbeat sent (Yahoo told we are not idle)
    08:49:34  pick 43  Lamar Jackson (QB) taken by seat 3 in 27 s
    08:49:45  plan #42 for pick 44
  • Cam Skattebo RB · wait costs 1 · pick costs 0, best pair 55.9 (31.2 now + ~24.7 WR next) · 91% survives to our turn
  • Tetairoa McMillan WR · safe to wait · pick costs 1.6 · 99% survives to our turn
  • D
    08:49:52  pick 44  Tetairoa McMillan (WR) taken by seat 4 in 18 s — a target is gone (was 99% to survive)
    08:49:53  plan #43 for pick 45
  • Cam Skattebo RB · wait costs 6 · pick costs 0, best pair 49.5 (31.2 now + ~18.3 WR next) · 64% survives to our turn
  • Davante Adams WR · wait costs 4 · pick costs 1.9 · 63% survives to our turn
  • Drake
    08:49:53  ON THE CLOCK, pick 45 · plan #43 (0.0 s old) · lineup needs QB WR FLEX K DEF
    08:49:53  PICKED Cam Skattebo (RB) via action, confirmed in 483 ms — chose Cam Skattebo (RB): waiting would likely cost about 6 points at your FLEX spot, 64% to still be there next turn
  • top projection left was Drake Maye, passed on purp
    08:49:56  plan #44 for pick 46
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 36.2 (18.3 now + ~17.9 WR next) · 58% survives to our turn
  • Davante Adams WR · wait costs 4 · pick costs 1.5 · 60% survives to our turn
  • Jalen H
    08:50:00  pick 46  Terry McLaurin (WR) taken by seat 6 in 6 s
    08:50:05  pick 47  Bucky Irving (RB) taken by seat 7 in 5 s
    08:50:08  pick 48  Tyler Warren (TE) taken by seat 8 in 3 s
    08:50:09  plan #45 for pick 49
  • Drake Maye QB · wait costs 4 · pick costs 0, best pair 36.8 (18.3 now + ~18.5 WR next) · 68% survives to our turn
  • Davante Adams WR · wait costs 4 · pick costs 0.6 · 70% survives to our turn
  • Jalen H
    08:50:30  heartbeat sent (Yahoo told we are not idle)
    08:50:32  pick 49  David Montgomery (RB) taken by seat 9 in 24 s
    08:50:33  plan #47 for pick 50
  • Drake Maye QB · wait costs 5 · pick costs 0, best pair 37.7 (18.3 now + ~19.4 WR next) · 64% survives to our turn
  • Davante Adams WR · wait costs 3 · pick costs 2.1 · 77% survives to our turn
  • Jalen H
    08:50:51  pick 50  DJ Moore (WR) taken by seat 10 in 19 s
    08:50:58  plan #49 for pick 51
  • Drake Maye QB · wait costs 4 · pick costs 0, best pair 38.4 (18.3 now + ~20.1 WR next) · 69% survives to our turn
  • Davante Adams WR · wait costs 2 · pick costs 2.1 · 83% survives to our turn
  • Jalen H
    08:51:09  pick 51  Drake Maye (QB) taken by seat 10 in 18 s — a target is gone (was 69% to survive)
    08:51:11  plan #50 for pick 52
  • Davante Adams WR · wait costs 2 · pick costs 0, best pair 31.1 (22.3 now + ~8.8 RB next) · 86% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 5.3 · 71% survives to our turn
  • Trevor 
    08:51:31  heartbeat sent (Yahoo told we are not idle)
    08:51:33  pick 52  Davante Adams (WR) taken by seat 9 in 24 s — a target is gone (was 86% to survive)
    08:51:36  plan #52 for pick 53
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 18 (9.2 now + ~8.8 RB next) · 88% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 3.6 · 85% survives to our turn
  • Trevor 
    08:51:41  pick 53  Jadarian Price (RB) taken by seat 8 in 8 s
    08:51:49  plan #53 for pick 54
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 18 (9.2 now + ~8.8 RB next) · 92% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 3.5 · 90% survives to our turn
  • Trevor 
    08:52:02  pick 54  Tucker Kraft (TE) taken by seat 7 in 21 s
    08:52:13  plan #55 for pick 55
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 18 (9.2 now + ~8.8 RB next) · 93% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 3.5 · 100% survives to our turn
  • Trevor
    08:52:16  pick 55  Luther Burden III (WR) taken by seat 6 in 13 s
    08:52:16  plan #56 for pick 56
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 17.8 (9.2 now + ~8.6 RB next) · 70% survives to our turn
  • Jalen Hurts QB · wait costs 1 · pick costs 3.5 · 56% survives to our turn
  • Trevo
    08:52:16  ON THE CLOCK, pick 56 · plan #56 (0.0 s old) · lineup needs QB WR K DEF
    08:52:17  PICKED Jameson Williams (WR) via action, confirmed in 388 ms — chose Jameson Williams (WR): nothing urgent, the most valuable player who fills a slot (70% to survive, nobody better worth waiting for)
  • top projection left was Ja
    08:52:20  plan #57 for pick 57
  • Jalen Hurts QB · wait costs 1 · 54% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    08:52:22  pick 57  Bhayshul Tuten (RB) taken by seat 4 in 5 s
    08:52:28  pick 58  Rhamondre Stevenson (RB) taken by seat 3 in 5 s — a target is gone
    08:52:29  pick 59  Joe Burrow (QB) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:52:30  pick 60  Jayden Daniels (QB) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:52:31  pick 61  Sam LaPorta (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:52:31  pick 62  Harold Fannin Jr. (TE) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:52:31  heartbeat sent (Yahoo told we are not idle)
    08:52:32  plan #58 for pick 63
  • Jalen Hurts QB · safe to wait · 90% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    08:52:36  pick 63  Quinshon Judkins (RB) taken by seat 3 in 5 s
    08:52:44  plan #59 for pick 64
  • Jalen Hurts QB · safe to wait · 88% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    08:52:48  pick 64  Rome Odunze (WR) taken by seat 4 in 12 s
    08:52:49  plan #60 for pick 65
  • Jalen Hurts QB · wait costs 1 · 67% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    08:52:49  ON THE CLOCK, pick 65 · plan #60 (0.0 s old) · lineup needs QB K DEF
    08:52:49  PICKED Jalen Hurts (QB) via action, confirmed in 398 ms — chose Jalen Hurts (QB): waiting would likely cost about 1 points at QB, 67% to still be there next turn
    08:52:52  plan #61 for pick 66
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Christian Watson WR · insurance worth ~21 · 67% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    08:52:53  pick 66  Christian Watson (WR) taken by seat 6 in 3 s — a target is gone (was 67% to survive)
    08:53:04  plan #62 for pick 67
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Mike Evans WR · insurance worth ~20 · 70% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    08:53:20  pick 67  Jaylen Warren (RB) taken by seat 7 in 28 s — a target is gone
    08:53:24  pick 68  Dak Prescott (QB) taken by seat 8 in 4 s
    08:53:29  plan #64 for pick 69
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Mike Evans WR · insurance worth ~20 · 76% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:53:33  heartbeat sent (Yahoo told we are not idle)
    08:53:51  pick 69  RJ Harvey (RB) taken by seat 9 in 27 s — a target is gone
    08:53:53  plan #66 for pick 70
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Mike Evans WR · insurance worth ~20 · 82% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:54:06  pick 70  Parker Washington (WR) taken by seat 10 in 15 s — a target is gone
    08:54:09  pick 71  TreVeyon Henderson (RB) taken by seat 10 in 3 s — a target is gone
    08:54:19  plan #68 for pick 72
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 99% survives to our turn
  • Mike Evans WR · insurance worth ~20 · 88% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:54:29  pick 72  George Kittle (TE) taken by seat 9 in 20 s
    08:54:31  plan #69 for pick 73
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • Mike Evans WR · insurance worth ~20 · 86% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:54:34  pick 73  Mike Evans (WR) taken by seat 8 in 5 s — a target is gone (was 86% to survive)
    08:54:34  heartbeat sent (Yahoo told we are not idle)
    08:54:43  plan #70 for pick 74
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 93% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:55:00  pick 74  Carnell Tate (WR) taken by seat 7 in 25 s — a target is gone
    08:55:04  pick 75  Rams (DEF) taken by seat 6 in 5 s
    08:55:05  plan #72 for pick 76
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 58% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:55:05  ON THE CLOCK, pick 76 · plan #72 (0.0 s old) · lineup needs K DEF
    08:55:05  PICKED Tyrone Tracy Jr. (RB) via action, confirmed in 366 ms — lineup full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +8.3 a week over the wire, about 80 points
  • he also backs up 
    08:55:08  plan #73 for pick 77
  • DK Metcalf WR · insurance worth ~18 · 60% survives to our turn
  • Kenny Gainwell RB · insurance worth ~16 · 99% survives to our turn
  • Marvin Harrison Jr. WR · depth fallback, engine list done
    08:55:24  pick 77  Jonathon Brooks (RB) taken by seat 4 in 19 s
    08:55:28  pick 78  Marvin Harrison Jr. (WR) taken by seat 3 in 4 s — a target is gone
    08:55:29  pick 79  Caleb Williams (QB) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:55:30  pick 80  Brian Thomas Jr. (WR) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:55:32  pick 81  Justin Herbert (QB) taken by seat 1 in 2 s INSTANTLY (autopick)
    08:55:32  pick 82  DK Metcalf (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone (was 60% to survive)
    08:55:33  plan #75 for pick 83
  • Wan'Dale Robinson WR · insurance worth ~17 · 100% survives to our turn
  • Kenny Gainwell RB · insurance worth ~16 · 99% survives to our turn
  • Rico Dowdle RB · depth fallback, engine list done
    08:55:34  pick 83  MarShawn Lloyd (RB) taken by seat 3 in 1 s INSTANTLY (autopick)
    08:55:37  heartbeat sent (Yahoo told we are not idle)
    08:55:45  pick 84  Trevor Lawrence (QB) taken by seat 4 in 12 s
    08:55:46  plan #76 for pick 85
  • Wan'Dale Robinson WR · insurance worth ~17 · 96% survives to our turn
  • Kenny Gainwell RB · insurance worth ~16 · 92% survives to our turn
  • Kyle Pitts Sr. TE · insurance worth ~11 · 84% survives to ou
    08:55:46  ON THE CLOCK, pick 85 · plan #76 (0.0 s old) · lineup needs K DEF
    08:55:47  PICKED Wan'Dale Robinson (WR) via action, confirmed in 380 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points
  • top projection 
    08:55:49  pick 86  Brandon Aubrey (K) taken by seat 6 in 2 s
    08:55:50  plan #77 for pick 87
  • Kenny Gainwell RB · insurance worth ~16 · 95% survives to our turn
  • Kyle Pitts Sr. TE · insurance worth ~11 · 82% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 86% survives to our 
    08:56:12  pick 87  Tony Pollard (RB) taken by seat 7 in 23 s
    08:56:15  plan #79 for pick 88
  • Kenny Gainwell RB · insurance worth ~16 · 95% survives to our turn
  • Kyle Pitts Sr. TE · insurance worth ~11 · 87% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 88% survives to our 
    08:56:26  pick 88  Alec Pierce (WR) taken by seat 8 in 14 s
    08:56:27  plan #80 for pick 89
  • Kenny Gainwell RB · insurance worth ~16 · 95% survives to our turn
  • Kyle Pitts Sr. TE · insurance worth ~11 · 89% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 90% survives to our 
    08:56:38  heartbeat sent (Yahoo told we are not idle)
    08:56:51  pick 89  Matthew Stafford (QB) taken by seat 9 in 25 s
    08:56:51  plan #82 for pick 90
  • Kenny Gainwell RB · insurance worth ~16 · 96% survives to our turn
  • Kyle Pitts Sr. TE · insurance worth ~11 · 89% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 88% survives to our 
    08:56:54  pick 90  Kyle Pitts Sr. (TE) taken by seat 10 in 3 s — a target is gone (was 89% to survive)
    08:56:59  pick 91  Rico Dowdle (RB) taken by seat 10 in 5 s
    08:57:04  plan #83 for pick 92
  • Kenny Gainwell RB · insurance worth ~16 · 96% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 89% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 94% survives to o
    08:57:15  pick 92  Jordan Addison (WR) taken by seat 9 in 17 s
    08:57:16  plan #84 for pick 93
  • Kenny Gainwell RB · insurance worth ~16 · 98% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 90% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 95% survives to o
    08:57:21  pick 93  Jordan Mason (RB) taken by seat 8 in 6 s
    08:57:29  plan #85 for pick 94
  • Kenny Gainwell RB · insurance worth ~16 · 99% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 94% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 97% survives to o
    08:57:38  heartbeat sent (Yahoo told we are not idle)
    08:57:50  pick 94  Michael Wilson (WR) taken by seat 7 in 29 s
    08:57:54  plan #87 for pick 95
  • Kenny Gainwell RB · insurance worth ~16 · 98% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 98% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 98% survives to o
    08:57:57  pick 95  Chris Godwin Jr. (WR) taken by seat 6 in 6 s
    08:57:57  plan #88 for pick 96
  • Kenny Gainwell RB · insurance worth ~16 · 94% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 82% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 79% survives to o
    08:57:57  ON THE CLOCK, pick 96 · plan #88 (0.0 s old) · lineup needs K DEF
    08:57:58  PICKED Kenny Gainwell (RB) via action, confirmed in 512 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +6.4 a week over the wire, about 16 points
  • top projection left w
    08:58:01  plan #89 for pick 97
  • Patrick Mahomes II QB · insurance worth ~8 · 82% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 80% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 21% survives to our 
    08:58:07  pick 97  J.K. Dobbins (RB) taken by seat 4 in 9 s — a target is gone (was 21% to survive)
    08:58:13  pick 98  De'Zhaun Stribling (WR) taken by seat 3 in 5 s
    08:58:13  plan #90 for pick 99
  • Patrick Mahomes II QB · insurance worth ~8 · 85% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 82% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 98% survives to o
    08:58:13  pick 99  Josh Downs (WR) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:58:16  pick 100  Chuba Hubbard (RB) taken by seat 1 in 2 s
    08:58:16  pick 101  Quentin Johnston (WR) taken by seat 1 in 0 s
    08:58:17  pick 102  Jacory Croskey-Merritt (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:58:25  plan #91 for pick 103
  • Patrick Mahomes II QB · insurance worth ~8 · 98% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 97% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 98% survives to 
    08:58:40  pick 103  Stefon Diggs (WR) taken by seat 3 in 23 s
    08:58:40  heartbeat sent (Yahoo told we are not idle)
    08:58:45  pick 104  Blake Corum (RB) taken by seat 4 in 5 s
    08:58:46  plan #93 for pick 105
  • Patrick Mahomes II QB · insurance worth ~8 · 90% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 89% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 92% survives to 
    08:58:46  ON THE CLOCK, pick 105 · plan #93 (0.0 s old) · lineup needs K DEF
    08:58:47  PICKED Patrick Mahomes II (QB) via action, confirmed in 375 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    08:58:50  plan #94 for pick 106
  • Courtland Sutton WR · insurance worth ~2 · 89% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 91% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:58:52  pick 106  KC Concepcion (WR) taken by seat 6 in 5 s
    08:58:52  pick 107  Brock Purdy (QB) taken by seat 7 in 0 s
    08:58:53  pick 108  Ka'imi Fairbairn (K) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:59:02  plan #95 for pick 109
  • Courtland Sutton WR · insurance worth ~2 · 94% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 94% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:59:19  pick 109  Travis Kelce (TE) taken by seat 9 in 26 s
    08:59:22  pick 110  Jayden Reed (WR) taken by seat 10 in 4 s — a target is gone
    08:59:27  plan #97 for pick 111
  • Courtland Sutton WR · insurance worth ~2 · 96% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 96% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:59:34  pick 111  Texans (DEF) taken by seat 10 in 12 s
    08:59:39  plan #98 for pick 112
  • Courtland Sutton WR · insurance worth ~2 · 97% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 97% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:59:41  heartbeat sent (Yahoo told we are not idle)
    09:00:00  pick 112  Brian Robinson (RB) taken by seat 9 in 26 s
    09:00:02  pick 113  Seahawks (DEF) taken by seat 8 in 2 s INSTANTLY (autopick)
    09:00:02  pick 114  Bo Nix (QB) taken by seat 7 in 0 s INSTANTLY (autopick)
    09:00:03  plan #100 for pick 115
  • Courtland Sutton WR · insurance worth ~2 · 99% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    09:00:10  pick 115  Courtland Sutton (WR) taken by seat 6 in 7 s — a target is gone (was 99% to survive)
    09:00:10  plan #101 for pick 116
  • Michael Pittman Jr. WR · insurance worth ~2 · 94% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~1 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    09:00:10  ON THE CLOCK, pick 116 · plan #101 (0.0 s old) · lineup needs K DEF
    09:00:11  PICKED Michael Pittman Jr. (WR) via action, confirmed in 500 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.5 a week over the wire, about 2 points
  • top projecti
    09:00:14  plan #102 for pick 117
  • Aaron Jones Sr. RB · insurance worth ~1 · 94% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 94% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    09:00:23  pick 117  Dalton Kincaid (TE) taken by seat 4 in 12 s
    09:00:26  plan #103 for pick 118
  • Aaron Jones Sr. RB · insurance worth ~1 · 95% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 95% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    09:00:41  heartbeat sent (Yahoo told we are not idle)
    09:00:53  pick 118  Jaxson Dart (QB) taken by seat 3 in 31 s
    09:00:53  pick 119  Dallas Goedert (TE) taken by seat 2 in 0 s
    09:00:54  pick 120  Isaiah Likely (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    09:00:55  pick 121  Matthew Golden (WR) taken by seat 1 in 1 s INSTANTLY (autopick)
    09:00:56  pick 122  Makai Lemon (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    09:00:57  pick 123  Mark Andrews (TE) taken by seat 3 in 1 s INSTANTLY (autopick)
    09:01:03  plan #106 for pick 124
  • Aaron Jones Sr. RB · insurance worth ~1 · 100% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 99% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    09:01:13  pick 124  Jared Goff (QB) taken by seat 4 in 16 s
    09:01:14  plan #107 for pick 125
  • Aaron Jones Sr. RB · insurance worth ~1 · 93% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 90% survives to our turn
  • Romeo Doubs WR · depth fallback, engine list done
    09:01:14  ON THE CLOCK, pick 125 · plan #107 (0.0 s old) · lineup needs K DEF
    09:01:14  PICKED Aaron Jones Sr. (RB) via action, confirmed in 547 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +5.2 a week over the wire, about 1 points
  • top projection left 
    09:01:17  plan #108 for pick 126
  • Denver Broncos DEF · wait costs 3 · pick costs 0, best pair 44.4 (14 now + ~30.4 RB next) · 50% survives to our turn
  • Cam Little K · safe to wait · pick costs 11 · 79% survives to our turn
  • Cameron
    09:01:30  pick 126  Tyler Allgeier (RB) taken by seat 6 in 16 s
    09:01:33  pick 127  Juwan Johnson (TE) taken by seat 7 in 2 s
    09:01:37  pick 128  Jordan Love (QB) taken by seat 8 in 4 s
    09:01:41  heartbeat sent (Yahoo told we are not idle)
    09:01:42  plan #110 for pick 129
  • Denver Broncos DEF · wait costs 2 · pick costs 0, best pair 44.4 (14 now + ~30.4 RB next) · 68% survives to our turn
  • Cam Little K · safe to wait · pick costs 11 · 85% survives to our turn
  • Cameron
    09:01:50  pick 129  Broncos (DEF) taken by seat 9 in 14 s
    09:01:54  plan #111 for pick 130
  • Philadelphia Eagles DEF · safe to wait · pick costs 0, best pair 38.4 (8 now + ~30.4 RB next) · 66% survives to our turn
  • Cam Little K · safe to wait · pick costs 5 · 87% survives to our turn
  • Came
    09:02:06  pick 130  Chris Rodriguez Jr. (RB) taken by seat 10 in 16 s
    09:02:06  plan #112 for pick 131
  • Philadelphia Eagles DEF · safe to wait · pick costs 0, best pair 38.4 (8 now + ~30.4 RB next) · 65% survives to our turn
  • Cam Little K · safe to wait · pick costs 5 · 89% survives to our turn
  • Came
    09:02:14  pick 131  Jason Myers (K) taken by seat 10 in 8 s — a target is gone
    09:02:19  plan #113 for pick 132
  • Philadelphia Eagles DEF · safe to wait · pick costs 0, best pair 38.5 (8 now + ~30.5 RB next) · 67% survives to our turn
  • Cam Little K · safe to wait · pick costs 5 · 92% survives to our turn
  • Came
    09:02:23  pick 132  Baker Mayfield (QB) taken by seat 9 in 9 s
    09:02:25  pick 133  Tank Bigsby (RB) taken by seat 8 in 2 s INSTANTLY (autopick)
    09:02:26  pick 134  Eagles (DEF) taken by seat 7 in 1 s INSTANTLY (autopick)
    09:02:31  pick 135  Mike Washington Jr. (RB) taken by seat 6 in 5 s
    09:02:32  plan #114 for pick 136
  • Pittsburgh Steelers DEF · wait costs 1 · pick costs 0, best pair 34.5 (4 now + ~30.5 RB next) · 81% survives to our turn
  • Cam Little K · wait costs 2 · pick costs 1 · 67% survives to our turn
  • Came
    09:02:32  ON THE CLOCK, pick 136 · plan #114 (0.0 s old) · lineup needs K DEF
    09:02:33  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 346 ms — chose Pittsburgh Steelers (DEF): waiting would likely cost about 1 points at DEF, 81% to still be there next turn
  • top projection left was Kyler Murray, passed 
    09:02:36  plan #115 for pick 137
  • Cam Little K · wait costs 2 · 66% survives to our turn
  • Cameron Dicker K · depth fallback, engine list done
  • Eddy Pineiro K · depth fallback, engine list done
    09:02:41  heartbeat sent (Yahoo told we are not idle)
    09:02:43  pick 137  Cameron Dicker (K) taken by seat 4 in 10 s — a target is gone
    09:02:43  pick 138  Vikings (DEF) taken by seat 3 in 0 s INSTANTLY (autopick)
    09:02:44  pick 139  Cam Little (K) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 66% to survive)
    09:02:45  pick 140  Jaguars (DEF) taken by seat 1 in 1 s INSTANTLY (autopick)
    09:02:46  pick 141  Tyler Loop (K) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    09:02:47  pick 142  Patriots (DEF) taken by seat 2 in 1 s INSTANTLY (autopick)
    09:02:48  plan #116 for pick 143
  • Eddy Pineiro K · safe to wait · 98% survives to our turn
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    09:02:50  pick 143  Will Reichard (K) taken by seat 3 in 3 s
    09:03:00  plan #117 for pick 144
  • Eddy Pineiro K · safe to wait · 98% survives to our turn
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    09:03:00  bridge warning: 1 drafted entries matched no board player: 143 Will Reichard
    09:03:04  pick 144  Chargers (DEF) taken by seat 4 in 14 s
    09:03:04  plan #118 for pick 145
  • Eddy Pineiro K
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    09:03:05  ON THE CLOCK, pick 145 · plan #118 (0.0 s old) · lineup needs K
    09:03:05  PICKED Eddy Pineiro (K) via action, confirmed in 276 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Kyler Murray, passed on purpose
    09:03:07  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    08:42:24 PT preflight: ok=true pick_path=action my_team=5 plan=plan 25 deep @pick 1 via store call#1
    08:42:24 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    08:42:24 PT NARR info driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    08:43:24 PT heartbeat: setAwayStatus(false)
    08:43:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:44:07 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~36 pts at RB (best option now 154, ~118 by your next turn) · 48% chance he's still there at your next pick · fills yo
    08:44:27 PT heartbeat: setAwayStatus(false)
    08:44:27 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:45:28 PT heartbeat: setAwayStatus(false)
    08:45:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:45:40 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~25 pts at RB (best option now 73, ~48 by your next turn) · 26% chance he's still there at your next pick · fills your open R
    08:46:28 PT heartbeat: setAwayStatus(false)
    08:46:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:46:30 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~22 pts at TE (best option now 78, ~56 by your next turn) · 59% chance he's still there at your next pick · fills your open TE
    08:47:29 PT heartbeat: setAwayStatus(false)
    08:47:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:48:29 PT heartbeat: setAwayStatus(false)
    08:48:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:48:41 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~3 pts at WR (best option now 26, ~22 by your next turn) · 70% chance he's still there at your next pick · fills your open WR 
    08:49:30 PT heartbeat: setAwayStatus(false)
    08:49:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:49:53 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~6 pts at your FLEX spot (best option now 26, ~20 by your next turn) · 64% chance he's still there at your next pick · fills a F
    08:50:30 PT heartbeat: setAwayStatus(false)
    08:50:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:51:31 PT heartbeat: setAwayStatus(false)
    08:51:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:52:17 PT ON CLOCK -> {"drafted":"Jameson Williams","pos":"WR","vorp":0,"proj":142.1,"why":"safe to wait on WR · 70% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · two-pi
    08:52:31 PT heartbeat: setAwayStatus(false)
    08:52:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:52:49 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"waiting likely costs ~1 pts at QB (best option now 18, ~17 by your next turn) · 67% chance he's still there at your next pick · fills your open QB slo
    08:53:33 PT heartbeat: setAwayStatus(false)
    08:53:33 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:54:34 PT heartbeat: setAwayStatus(false)
    08:54:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:55:06 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo"
    08:55:37 PT heartbeat: setAwayStatus(false)
    08:55:37 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:55:47 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.964,"sr":0.964,"e":-10.6,"top_
    08:56:38 PT heartbeat: setAwayStatus(false)
    08:56:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:57:38 PT heartbeat: setAwayStatus(false)
    08:57:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:57:58 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.4/wk over the wire (Ollie Gordon II) ≈ 16 pts","s":0.935,"
    08:58:40 PT heartbeat: setAwayStatus(false)
    08:58:40 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:58:47 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.896,"sr":0.896,"e":11.9,"top_pr
    08:59:41 PT heartbeat: setAwayStatus(false)
    08:59:41 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    09:00:11 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    09:00:41 PT heartbeat: setAwayStatus(false)
    09:00:41 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    09:01:15 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +5.2/wk over the wire (Ollie Gordon II) ≈ 1 pts","s":0.9
    09:01:41 PT heartbeat: setAwayStatus(false)
    09:01:41 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    09:02:33 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"waiting likely costs ~1 pts at DEF (best option now 8, ~7 by your next turn) · 81% chance he's still there at your next pick · fills your open D
    09:02:41 PT heartbeat: setAwayStatus(false)
    09:02:41 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    09:03:00 PT BRIDGE WARNING: 1 drafted entries matched no board player: 143 Will Reichard
    09:03:05 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":258.9,"vorp":-14.7},"took_top_projection":
    09:03:07 PT roster full
    09:03:07 PT NARR info roster full — driver done; posting the trail when the room finishes
    09:03:07 PT driver stop


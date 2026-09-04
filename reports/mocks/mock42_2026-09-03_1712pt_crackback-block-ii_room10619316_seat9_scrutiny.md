# Scrutiny: Mock 42 -- Crackback Block II (room 10619316) -- Thursday 2026-09-03 17:12 PT -- 10 teams, our seat 9

Captured 2026-09-03 17:29:13 PT. Times below are Pacific. 10 teams, our team id 9, draft slot 9. 150 picks in the trail, 97 bridge plan calls, 72 recs events in the room log.

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
- Action latency to store confirmation: median 431 ms, min 344, max 1051.
- Heartbeats 16; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (4): 1 drafted entries matched no board player: 106 Bills; 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas; 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell; dropped 1 feed entries numbered >= header pick 76.
- Away seats over the room (each change): {} -> {5} -> {5,10} -> {1,5,10} -> {5,10} -> {1,5,10} -> {1,3,5,10} -> {1,3,5,8,10} -> {1,3,5,10} -> {1,3,5,7,10}.
- Managers away at the end: 1 craig, 3 Travis, 5 Kari, 7 Kasey, 10 Christopher.

## Our picks, one block each

### Pick 9 (round 1): Jaxon Smith-Njigba (WR)

- In plain English: Took Jaxon Smith-Njigba (WR) because waiting would likely cost about 5 points at WR, with a 85% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 431 ms, ranker engine, plan call 11, plan age 952 ms, at 17:14:03 PT.
- Engine's reason: waiting likely costs ~5 pts at WR (best option now 89, ~84 by your next turn) · 85% chance he's still there at your next pick · fills your open WR slot · last WR at this level — big drop after him · 2 teams picking befor
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: De'Von Achane (RB, s=0.837, e=71.1); Trey McBride (TE, s=0.992, e=77.7); Josh Allen (QB, s=0.939, e=46).
- Plan call 11 @pick 9: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 8 drafted / 0 mine.
- Engine's first choice was **Jaxon Smith-Njigba** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaxon Smith-Njigba | WR | 89.4 | 0.85 | 0.85 | 84.4 | 89.4 | waiting likely costs ~5 pts at WR (best option now 89, ~84 by your next turn) · 85% chance |
| De'Von Achane | RB | 73.4 | 0.84 | 0.84 | 71.1 | 73.4 | waiting likely costs ~2 pts at RB (best option now 73, ~71 by your next turn) · 84% chance |
| Trey McBride | TE | 77.9 | 0.99 | 0.99 | 77.7 | 77.9 | safe to wait on TE · 99% chance he's still there at your next pick · fills your open TE sl |
| Josh Allen | QB | 47.0 | 0.94 | 0.94 | 46.0 | 47.0 | safe to wait on QB · 94% chance he's still there at your next pick · fills your open QB sl |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 46.0 | 1.0 | 7 |
| RB | 73.4 | 71.1 | 2.3 | 22 |
| WR | 89.4 | 84.4 | 5.0 | 25 |
| TE | 77.9 | 77.7 | 0.2 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 73.0 | 0.4 | 53 |

### Pick 12 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 17 points at RB, with a 34% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 429 ms, ranker engine, plan call 15, plan age 919 ms, at 17:14:37 PT.
- Engine's reason: waiting likely costs ~17 pts at RB (best option now 73, ~56 by your next turn) · 34% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 16 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.37, e=51); Justin Jefferson (WR, s=0.404, e=47); Josh Allen (QB, s=0.373, e=36.5).
- Plan call 15 @pick 12: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 10], state store with 11 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.34 | 0.34 | 56.5 | 73.4 | waiting likely costs ~17 pts at RB (best option now 73, ~56 by your next turn) · 34% chanc |
| Trey McBride | TE | 77.9 | 0.37 | 0.37 | 51.0 | 77.9 | waiting likely costs ~27 pts at TE (best option now 78, ~51 by your next turn) · 37% chanc |
| Justin Jefferson | WR | 53.9 | 0.40 | 0.40 | 47.0 | 53.9 | waiting likely costs ~7 pts at WR (best option now 54, ~47 by your next turn) · 40% chance |
| Josh Allen | QB | 47.0 | 0.37 | 0.37 | 36.5 | 47.0 | waiting likely costs ~10 pts at QB (best option now 47, ~37 by your next turn) · 37% chanc |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 36.5 | 10.5 | 8 |
| RB | 73.4 | 56.5 | 16.9 | 21 |
| WR | 53.9 | 47.0 | 6.9 | 24 |
| TE | 77.9 | 51.0 | 26.9 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 57.0 | 16.4 | 52 |

### Pick 29 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 11 points at TE, with a 80% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 402 ms, ranker engine, plan call 28, plan age 880 ms, at 17:17:01 PT.
- Engine's reason: waiting likely costs ~11 pts at TE (best option now 78, ~67 by your next turn) · 80% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 2 teams
- Top projection available: Drake Maye -> took it: False.
- Passed on: Javonte Williams (RB, s=0.778, e=34.5); Rashee Rice (WR, s=0.771, e=31.8); Drake Maye (QB, s=0.999, e=31.1).
- Plan call 28 @pick 29: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 10], state store with 28 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.80 | 0.80 | 66.9 | 77.9 | waiting likely costs ~11 pts at TE (best option now 78, ~67 by your next turn) · 80% chanc |
| Javonte Williams | RB | 36.9 | 0.78 | 0.78 | 34.5 | 36.9 | waiting likely costs ~2 pts at RB (best option now 37, ~35 by your next turn) · 78% chance |
| Rashee Rice | WR | 34.1 | 0.77 | 0.77 | 31.8 | 34.1 | waiting likely costs ~2 pts at WR (best option now 34, ~32 by your next turn) · 77% chance |
| Drake Maye | QB | 31.1 | 1.00 | 1.00 | 31.1 | 31.1 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 31.1 | 0.0 | 9 |
| RB | 36.9 | 34.5 | 2.4 | 18 |
| WR | 34.1 | 31.8 | 2.3 | 21 |
| TE | 77.9 | 66.9 | 11.0 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 39.985766857976785 | 39.1 | 0.9 | 47 |

### Pick 32 (round 4): Javonte Williams (RB)

- In plain English: Took Javonte Williams (RB) because waiting would likely cost about 9 points at RB, with a 41% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 370 ms, ranker engine, plan call 29, plan age 869 ms, at 17:17:05 PT.
- Engine's reason: waiting likely costs ~9 pts at RB (best option now 37, ~28 by your next turn) · 41% chance he's still there at your next pick · fills your open RB slot · 16 teams picking before you still need a RB · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Rashee Rice (WR, s=0.396, e=25.7); Drake Maye (QB, s=0.498, e=24.3); Travis Etienne Jr. (RB, s=None, e=None).
- Plan call 29 @pick 32: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 10], state store with 31 drafted / 3 mine.
- Engine's first choice was **Javonte Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Javonte Williams | RB | 36.9 | 0.41 | 0.41 | 28.0 | 36.9 | waiting likely costs ~9 pts at RB (best option now 37, ~28 by your next turn) · 41% chance |
| Rashee Rice | WR | 34.1 | 0.40 | 0.40 | 25.7 | 34.1 | waiting likely costs ~8 pts at WR (best option now 34, ~26 by your next turn) · 40% chance |
| Drake Maye | QB | 31.1 | 0.50 | 0.50 | 24.3 | 31.1 | waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 50% chance |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 24.3 | 6.8 | 10 |
| RB | 36.9 | 28.0 | 8.9 | 18 |
| WR | 34.1 | 25.7 | 8.4 | 20 |
| TE | 23.8 | 22.2 | 1.6 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 28.5 | 8.5 | 45 |

### Pick 49 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 3 points at QB, with a 81% chance he would still be there next turn.
- Driver: via **action**, verified store, 1051 ms, ranker engine, plan call 41, plan age 2274 ms, at 17:19:20 PT.
- Engine's reason: waiting likely costs ~3 pts at QB (best option now 31, ~29 by your next turn) · 81% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: True.
- Passed on: Davante Adams (WR, s=0.862, e=11.3); Jaylen Warren (RB, s=1, e=9.3); Jalen Hurts (QB, s=None, e=None).
- Plan call 41 @pick 49: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 10], state store with 48 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.81 | 0.81 | 28.6 | 31.1 | waiting likely costs ~3 pts at QB (best option now 31, ~29 by your next turn) · 81% chance |
| Davante Adams | WR | 13.1 | 0.86 | 0.86 | 11.3 | 13.1 | waiting likely costs ~2 pts at WR (best option now 13, ~11 by your next turn) · 86% chance |
| Jaylen Warren | RB | 9.3 | 1.00 | 1.00 | 9.3 | 9.3 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills a  |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 28.6 | 2.5 | 13 |
| RB | 9.3 | 9.3 | -0.0 | 18 |
| WR | 13.1 | 11.3 | 1.8 | 18 |
| TE | 23.8 | 23.2 | 0.6 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 45 |

### Pick 52 (round 6): Davante Adams (WR)

- In plain English: Took Davante Adams (WR) because waiting would likely cost about 4 points at WR, with a 70% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 451 ms, ranker engine, plan call 42, plan age 974 ms, at 17:19:24 PT.
- Engine's reason: waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 70% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pick plan: pair wi
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.689, e=8.3); Rhamondre Stevenson (RB, s=None, e=None); Quinshon Judkins (RB, s=None, e=None).
- Plan call 42 @pick 52: needs {'QB': 0, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 10], state store with 51 drafted / 5 mine.
- Engine's first choice was **Davante Adams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Davante Adams | WR | 13.1 | 0.70 | 0.70 | 9.1 | 13.1 | waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 70% chance  |
| Jaylen Warren | RB | 9.3 | 0.69 | 0.69 | 8.3 | 9.3 | waiting likely costs ~1 pts at your FLEX spot (best option now 9, ~8 by your next turn) ·  |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quinshon Judkins | RB | 3.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 15.3 | 2.7 | 12 |
| RB | 9.3 | 8.2 | 1.1 | 17 |
| WR | 13.1 | 9.1 | 4.0 | 20 |
| TE | 21.1 | 18.2 | 2.9 | 9 |
| K | 13.5 | 13.3 | 0.2 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.3 | 1.1 | 46 |

### Pick 69 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (90% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 468 ms, ranker engine, plan call 56, plan age 962 ms, at 17:22:00 PT.
- Engine's reason: safe to wait on your FLEX spot · 90% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); Mike Evans (WR, s=None, e=None); RJ Harvey (RB, s=None, e=None).
- Plan call 56 @pick 69: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 10], state store with 68 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.90 | 0.90 | 9.1 | 9.3 | safe to wait on your FLEX spot · 90% chance he's still there at your next pick · fills a F |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Luther Burden III | WR | -7.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.4 | 0.3 | 20 |
| RB | 9.3 | 9.1 | 0.2 | 25 |
| WR | -2.4 | -3.0 | 0.6 | 32 |
| TE | 21.1 | 20.9 | 0.2 | 18 |
| K | 13.5 | 13.5 | 0.0 | 6 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 75 |

### Pick 72 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +2.7 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 26 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 622 ms, ranker engine, plan call 57, plan age 1180 ms, at 17:22:04 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodriguez Jr.) ≈ 26 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Mike Evans (WR, s=0.581, e=-5.4); Rhamondre Stevenson (RB, s=None, e=None); RJ Harvey (RB, s=None, e=None).
- Plan call 57 @pick 72: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 5, 10], state store with 71 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.52 | 0.52 | 0.4 | 7.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodri |
| Mike Evans | WR | -2.4 | 0.58 | 0.58 | -5.4 | -2.4 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.5/wk over the wire (Romeo Doubs |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.6 | 2.1 | 20 |
| RB | 7.2 | 0.4 | 6.8 | 32 |
| WR | -2.4 | -5.4 | 3.0 | 38 |
| TE | 21.1 | 16.8 | 4.3 | 21 |
| K | 13.5 | 13.1 | 0.4 | 9 |
| DEF | 18.0 | 17.8 | 0.2 | 7 |

### Pick 89 (round 9): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +1.0 points a week over the waiver wire (Romeo Doubs), worth about 7 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 468 ms, ranker engine, plan call 68, plan age 1163 ms, at 17:24:09 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: RJ Harvey (RB, s=0.975, e=-5.4); Kenny Gainwell (RB, s=None, e=None); Courtland Sutton (WR, s=None, e=None).
- Plan call 68 @pick 89: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 88 drafted / 8 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 1.00 | 1.00 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs |
| RJ Harvey | RB | -5.4 | 0.97 | 0.97 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.5 | 0.3 | 18 |
| RB | -5.4 | -5.4 | 0.0 | 28 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 13.8 | 13.7 | 0.1 | 19 |
| K | 13.5 | 13.4 | 0.1 | 13 |
| DEF | 18.0 | 17.8 | 0.2 | 11 |

### Pick 92 (round 10): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Tyler Shough), worth about 8 points.
- Driver: via **action**, verified store, 404 ms, ranker engine, plan call 69, plan age 885 ms, at 17:24:13 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.672, e=-6.7); Courtland Sutton (WR, s=0.636, e=-12.1); Matthew Stafford (QB, s=None, e=None).
- Plan call 69 @pick 92: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 91 drafted / 9 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.62 | 0.62 | 9.9 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough |
| RJ Harvey | RB | -5.4 | 0.67 | 0.67 | -6.7 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.9 |
| Courtland Sutton | WR | -11.1 | 0.64 | 0.64 | -12.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 9.9 | 2.9 | 18 |
| RB | -5.4 | -6.7 | 1.3 | 27 |
| WR | -11.1 | -12.1 | 1.0 | 35 |
| TE | 13.8 | 11.3 | 2.5 | 19 |
| K | 13.5 | 13.3 | 0.2 | 14 |
| DEF | 18.0 | 17.5 | 0.5 | 11 |

### Pick 109 (round 11): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +1.8 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 5 points. The top raw projection available was Matthew Stafford; the engine passed on him on purpose.
- Driver: via **action**, verified store, 477 ms, ranker engine, plan call 79, plan age 1189 ms, at 17:26:07 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts
- Top projection available: Matthew Stafford -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.968, e=-11.2); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 79 @pick 109: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 108 drafted / 10 mine, warnings ['1 drafted entries matched no board player: 106 Bills'].
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.99 | 0.99 | -6.5 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8 |
| Courtland Sutton | WR | -11.1 | 0.97 | 0.97 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 6.6 | 6.3 | 0.3 | 14 |
| RB | -6.2 | -6.5 | 0.3 | 23 |
| WR | -11.1 | -11.2 | 0.1 | 31 |
| TE | 13.8 | 13.7 | 0.1 | 18 |
| K | 12.0 | 11.8 | 0.2 | 14 |
| DEF | 16.0 | 15.9 | 0.1 | 12 |

### Pick 112 (round 12): Courtland Sutton (WR)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +1.0 points a week over the waiver wire (Deebo Samuel Sr.), worth about 1 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 595 ms, ranker engine, plan call 80, plan age 1153 ms, at 17:26:12 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.916, e=-26.3); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 80 @pick 112: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 111 drafted / 11 mine, warnings ['1 drafted entries matched no board player: 106 Bills'].
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.94 | 0.94 | -11.3 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0 |
| Aaron Jones Sr. | RB | -25.9 | 0.92 | 0.92 | -26.3 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 13 |
| RB | -25.9 | -26.3 | 0.4 | 22 |
| WR | -11.1 | -11.3 | 0.2 | 31 |
| TE | 10.9 | 10.6 | 0.3 | 17 |
| K | 12.0 | 10.4 | 1.6 | 15 |
| DEF | 16.0 | 15.6 | 0.4 | 12 |

### Pick 129 (round 13): Woody Marks (RB)

- In plain English: Lineup already full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +0.4 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 0 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 394 ms, ranker engine, plan call 89, plan age 898 ms, at 17:27:49 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.4/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.997, e=-21.5); Makai Lemon (WR, s=None, e=None); Romeo Doubs (WR, s=None, e=None).
- Plan call 89 @pick 129: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 128 drafted / 12 mine, warnings ['2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas'].
- Engine's first choice was **Woody Marks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Woody Marks | RB | -30.3 | 1.00 | 1.00 | -30.3 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0. |
| Jakobi Meyers | WR | -21.5 | 1.00 | 1.00 | -21.5 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| KC Concepcion | WR | -30.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -11.8 | -0.0 | 11 |
| RB | -30.3 | -30.3 | 0.0 | 20 |
| WR | -21.5 | -21.5 | 0.0 | 25 |
| TE | 0.5 | 0.5 | 0.0 | 13 |
| K | 12.0 | 11.9 | 0.1 | 16 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 132 (round 14): Eagles (DEF)

- In plain English: Took Philadelphia Eagles (DEF) because waiting would likely cost about 1 points at DEF, with a 43% chance he would still be there next turn. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 344 ms, ranker engine, plan call 90, plan age 834 ms, at 17:27:54 PT.
- Engine's reason: waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 43% chance he's still there at your next pick · fills your open DEF slot · 10 teams picking before you still need a DEF · two-pick plan: pai
- Top projection available: Jared Goff -> took it: False.
- Passed on: Cameron Dicker (K, s=0.682, e=11.5); Ka'imi Fairbairn (K, s=None, e=None); Cam Little (K, s=None, e=None).
- Plan call 90 @pick 132: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 3, 5, 10], state store with 131 drafted / 13 mine, warnings ['2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas'].
- Engine's first choice was **Philadelphia Eagles** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Philadelphia Eagles | DEF | 10.0 | 0.43 | 0.43 | 8.7 | 10.0 | waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 43% chance |
| Cameron Dicker | K | 10.5 | 0.68 | 0.68 | 11.5 | 12.0 | safe to wait on K · 68% chance he's still there at your next pick · fills your open K slot |
| Ka'imi Fairbairn | K | 12.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Little | K | 9.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 11 |
| RB | -33.0 | -33.4 | 0.4 | 19 |
| WR | -21.5 | -22.0 | 0.5 | 24 |
| TE | 0.5 | 0.3 | 0.2 | 13 |
| K | 12.0 | 11.5 | 0.5 | 16 |
| DEF | 10.0 | 8.7 | 1.3 | 10 |

### Pick 149 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 386 ms, ranker engine, plan call 97, plan age 986 ms, at 17:29:11 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None).
- Plan call 97 @pick 149: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 3, 5, 7, 10], state store with 148 drafted / 14 mine, warnings ['3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell'].
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | - | - | - | - | fills your open K slot |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 4 | 27% | 0% |
| 30-50% | 33 | 40% | 27% |
| 50-70% | 40 | 61% | 32% |
| 70-90% | 38 | 80% | 61% |
| 90-100% | 57 | 96% | 81% |

172 predictions over 71 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T17:22:20   WARNING plan #59: dropped 1 feed entries numbered >= header pick 76
    2026-09-03T17:25:55   WARNING plan #78: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:06   WARNING plan #79: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:11   WARNING plan #80: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:15   WARNING plan #81: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:28   WARNING plan #82: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:40   WARNING plan #83: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:26:53   WARNING plan #84: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:27:05   WARNING plan #85: 1 drafted entries matched no board player: 106 Bills
    2026-09-03T17:27:18   WARNING plan #86: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:27:30   WARNING plan #87: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:27:42   WARNING plan #88: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:27:48   WARNING plan #89: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:27:53   WARNING plan #90: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:27:57   WARNING plan #91: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:28:09   WARNING plan #92: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    2026-09-03T17:28:21   WARNING plan #93: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    2026-09-03T17:28:34   WARNING plan #94: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    2026-09-03T17:28:47   WARNING plan #95: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    2026-09-03T17:28:59   WARNING plan #96: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    2026-09-03T17:29:10   WARNING plan #97: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell

## Narration (what the panel showed live, Pacific time)

    17:12:18  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 25 · pick costs 0, best pair 320.5 (174.6 now + ~145.9 RB next) · 39% survives to our turn
  • Ja'Marr Chase WR · wait costs 16 · pick costs 39.7 · 44% survives to our tur
    17:12:19  driver started — seat 9, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    17:13:14  pick 1  Jahmyr Gibbs (RB) (seat 1) — a target is gone
    17:13:17  pick 2  Bijan Robinson (RB) (seat 2) in 3 s — a target is gone
    17:13:20  heartbeat sent (Yahoo told we are not idle)
    17:13:21  pick 3  Ja'Marr Chase (WR) (seat 3) in 4 s — a target is gone (was 44% to survive)
    17:13:21  plan #7 for pick 4
  • Christian McCaffrey RB · wait costs 30 · pick costs 0, best pair 299.3 (174.6 now + ~124.7 RB next) · 54% survives to our turn
  • Puka Nacua WR · wait costs 7 · pick costs 38.8 · 60% survives to our turn
  
    17:13:25  pick 4  Puka Nacua (WR) (seat 4) in 4 s — a target is gone (was 60% to survive)
    17:13:25  pick 5  Jonathan Taylor (RB) (seat 5) in 0 s — a target is gone
    17:13:33  plan #8 for pick 6
  • Christian McCaffrey RB · wait costs 24 · pick costs 0, best pair 275.6 (174.6 now + ~101 WR next) · 70% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 5 · pick costs 19.8 · 68% survives to our t
    17:13:38  pick 6  Amon-Ra St. Brown (WR) (seat 6) in 14 s — a target is gone
    17:13:43  pick 7  James Cook III (RB) (seat 7) in 5 s — a target is gone
    17:13:46  plan #9 for pick 8
  • Christian McCaffrey RB · wait costs 8 · pick costs 0, best pair 276.6 (174.6 now + ~102 WR next) · 90% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 4 · pick costs 4.7 · 89% survives to our tur
    17:14:02  pick 8  Christian McCaffrey (RB) (seat 8) in 19 s — a target is gone (was 90% to survive)
    17:14:02  plan #11 for pick 9
  • Jaxon Smith-Njigba WR · wait costs 5 · pick costs 0, best pair 197 (105.5 now + ~91.5 RB next) · 85% survives to our turn
  • De'Von Achane RB · wait costs 2 · pick costs 2.7 · 84% survives to our turn
  • 
    17:14:02  ON THE CLOCK, pick 9 · plan #11 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    17:14:03  PICKED Jaxon Smith-Njigba (WR) via action, confirmed in 431 ms — chose Jaxon Smith-Njigba (WR): waiting would likely cost about 5 points at WR, 85% to still be there next turn
  • top projection left was Josh Allen, passed on purp
    17:14:05  plan #12 for pick 10
  • De'Von Achane RB · wait costs 2 · pick costs 0, best pair 174.7 (93.8 now + ~80.9 RB next) · 81% survives to our turn
  • Trey McBride TE · safe to wait · pick costs 8.3 · 99% survives to our turn
  • CeeD
    17:14:20  heartbeat sent (Yahoo told we are not idle)
    17:14:32  pick 10  Saquon Barkley (RB) (seat 10) in 29 s
    17:14:34  pick 11  CeeDee Lamb (WR) (seat 10) in 2 s INSTANTLY (autopick) — a target is gone (was 79% to survive)
    17:14:36  plan #15 for pick 12
  • De'Von Achane RB · wait costs 17 · pick costs 0, best pair 170.7 (93.8 now + ~76.9 RB next) · 34% survives to our turn
  • Trey McBride TE · wait costs 27 · pick costs 18.7 · 37% survives to our turn
  • J
    17:14:36  ON THE CLOCK, pick 12 · plan #15 (0.0 s old) · lineup needs QB RBx2 WR TE FLEX K DEF
    17:14:37  PICKED De'Von Achane (RB) via action, confirmed in 429 ms — chose De'Von Achane (RB): waiting would likely cost about 17 points at RB, 34% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    17:14:40  plan #16 for pick 13
  • Chase Brown RB · wait costs 15 · pick costs 0, best pair 147.5 (80.9 now + ~66.6 RB next) · 24% survives to our turn
  • Trey McBride TE · wait costs 28 · pick costs 6.9 · 37% survives to our turn
  • Just
    17:14:48  pick 13  Justin Jefferson (WR) (seat 8) in 11 s — a target is gone (was 36% to survive)
    17:14:53  plan #17 for pick 14
  • Chase Brown RB · wait costs 14 · pick costs 0, best pair 148.9 (80.9 now + ~68 RB next) · 29% survives to our turn
  • Trey McBride TE · wait costs 28 · pick costs 6.5 · 35% survives to our turn
  • Drake 
    17:14:55  pick 14  Kenneth Walker III (RB) (seat 7) in 7 s
    17:15:03  pick 15  Chase Brown (RB) (seat 6) in 8 s — a target is gone (was 29% to survive)
    17:15:04  pick 16  Omarion Hampton (RB) (seat 5) in 1 s INSTANTLY (autopick)
    17:15:05  plan #18 for pick 17
  • Trey McBride TE · wait costs 25 · pick costs 0, best pair 137.3 (75.1 now + ~62.2 RB next) · 39% survives to our turn
  • Derrick Henry RB · wait costs 9 · pick costs 5.6 · 38% survives to our turn
  • Dra
    17:15:10  pick 17  Derrick Henry (RB) (seat 4) in 6 s — a target is gone (was 38% to survive)
    17:15:17  plan #19 for pick 18
  • Trey McBride TE · wait costs 23 · pick costs 0, best pair 135.4 (75.1 now + ~60.3 WR next) · 42% survives to our turn
  • Drake London WR · wait costs 7 · pick costs 8.5 · 37% survives to our turn
  • Kyre
    17:15:20  heartbeat sent (Yahoo told we are not idle)
    17:15:30  pick 18  Ashton Jeanty (RB) (seat 3) in 20 s
    17:15:32  pick 19  A.J. Brown (WR) (seat 2) in 2 s INSTANTLY (autopick) — a target is gone
    17:15:42  plan #21 for pick 20
  • Trey McBride TE · wait costs 19 · pick costs 0, best pair 135.3 (75.1 now + ~60.2 WR next) · 47% survives to our turn
  • Drake London WR · wait costs 7 · pick costs 10.7 · 43% survives to our turn
  • Kyr
    17:16:02  pick 20  Nico Collins (WR) (seat 1) in 29 s — a target is gone
    17:16:02  pick 21  Brock Bowers (TE) (seat 1) in 1 s INSTANTLY (autopick) — a target is gone
    17:16:06  plan #23 for pick 22
  • Trey McBride TE · wait costs 23 · pick costs 0, best pair 136.7 (75.1 now + ~61.6 WR next) · 57% survives to our turn
  • Drake London WR · wait costs 6 · pick costs 11.5 · 57% survives to our turn
  • Kyr
    17:16:13  pick 22  Malik Nabers (WR) (seat 2) in 10 s
    17:16:19  plan #24 for pick 23
  • Trey McBride TE · wait costs 22 · pick costs 0, best pair 136.6 (75.1 now + ~61.5 WR next) · 59% survives to our turn
  • Drake London WR · wait costs 6 · pick costs 10.8 · 56% survives to our turn
  • Kyr
    17:16:21  heartbeat sent (Yahoo told we are not idle)
    17:16:28  pick 23  Drake London (WR) (seat 3) in 15 s — a target is gone (was 56% to survive)
    17:16:31  plan #25 for pick 24
  • Trey McBride TE · wait costs 20 · pick costs 0, best pair 134.2 (75.1 now + ~59.1 RB next) · 62% survives to our turn
  • Kyren Williams RB · wait costs 2 · pick costs 16 · 67% survives to our turn
  • Chr
    17:16:33  pick 24  George Pickens (WR) (seat 4) in 6 s — a target is gone
    17:16:34  pick 25  Chris Olave (WR) (seat 5) in 1 s INSTANTLY (autopick) — a target is gone (was 65% to survive)
    17:16:41  pick 26  Kyren Williams (RB) (seat 6) in 7 s — a target is gone (was 67% to survive)
    17:16:43  plan #26 for pick 27
  • Trey McBride TE · wait costs 8 · pick costs 0, best pair 131.1 (75.1 now + ~56.1 RB next) · 86% survives to our turn
  • Javonte Williams RB · wait costs 1 · pick costs 6.4 · 88% survives to our turn
  • J
    17:16:48  pick 27  Josh Allen (QB) (seat 7) in 6 s — a target is gone (was 92% to survive)
    17:16:55  plan #27 for pick 28
  • Trey McBride TE · wait costs 3 · pick costs 0, best pair 131.9 (75.1 now + ~56.8 RB next) · 94% survives to our turn
  • Javonte Williams RB · safe to wait · pick costs 2.6 · 96% survives to our turn
  • R
    17:17:00  pick 28  DeVonta Smith (WR) (seat 8) in 12 s
    17:17:00  plan #28 for pick 29
  • Trey McBride TE · wait costs 11 · pick costs 0, best pair 130 (75.1 now + ~55 RB next) · 80% survives to our turn
  • Javonte Williams RB · wait costs 2 · pick costs 8.6 · 78% survives to our turn
  • Rash
    17:17:00  ON THE CLOCK, pick 29 · plan #28 (0.0 s old) · lineup needs QB RB WR TE FLEX K DEF
    17:17:01  PICKED Trey McBride (TE) via action, confirmed in 402 ms — chose Trey McBride (TE): waiting would likely cost about 11 points at TE, 80% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    17:17:03  pick 30  Jeremiyah Love (RB) (seat 10) in 2 s
    17:17:03  pick 31  Tee Higgins (WR) (seat 10) in 0 s
    17:17:04  plan #29 for pick 32
  • Javonte Williams RB · wait costs 9 · pick costs 0, best pair 104 (57.3 now + ~46.7 RB next) · 41% survives to our turn
  • Rashee Rice WR · wait costs 8 · pick costs 5.3 · 40% survives to our turn
  • Drak
    17:17:04  ON THE CLOCK, pick 32 · plan #29 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    17:17:05  PICKED Javonte Williams (RB) via action, confirmed in 370 ms — chose Javonte Williams (RB): waiting would likely cost about 9 points at RB, 41% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    17:17:08  plan #30 for pick 33
  • Rashee Rice WR · wait costs 9 · pick costs 0, best pair 91.5 (50.3 now + ~41.3 RB next) · 39% survives to our turn
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 3.2 · 28% survives to our turn
  • D
    17:17:23  pick 33  Zay Flowers (WR) (seat 8) in 18 s — a target is gone
    17:17:23  heartbeat sent (Yahoo told we are not idle)
    17:17:25  pick 34  Jaylen Waddle (WR) (seat 7) in 2 s INSTANTLY (autopick)
    17:17:29  pick 35  Rashee Rice (WR) (seat 6) in 4 s — a target is gone (was 39% to survive)
    17:17:29  pick 36  Breece Hall (RB) (seat 5) in 0 s INSTANTLY (autopick)
    17:17:33  plan #32 for pick 37
  • Travis Etienne Jr. RB · wait costs 5 · pick costs 0, best pair 81.3 (46.7 now + ~34.6 WR next) · 33% survives to our turn
  • Garrett Wilson WR · wait costs 6 · pick costs 0, best pair 81.3 (40 now + ~41.3
    17:17:48  pick 37  Tetairoa McMillan (WR) (seat 4) in 19 s — a target is gone
    17:17:57  plan #34 for pick 38
  • Drake Maye QB · wait costs 7 · pick costs 0, best pair 82.6 (40.3 now + ~42.3 RB next) · 47% survives to our turn
  • Garrett Wilson WR · wait costs 6 · pick costs 0.3 · 52% survives to our turn
  • Travis
    17:17:59  pick 38  Cam Skattebo (RB) (seat 3) in 11 s — a target is gone
    17:18:02  pick 39  Colston Loveland (TE) (seat 2) in 3 s
    17:18:03  pick 40  Garrett Wilson (WR) (seat 1) in 1 s INSTANTLY (autopick) — a target is gone (was 52% to survive)
    17:18:04  pick 41  Ladd McConkey (WR) (seat 1) in 1 s INSTANTLY (autopick)
    17:18:10  plan #35 for pick 42
  • Drake Maye QB · wait costs 5 · pick costs 0, best pair 83.9 (40.3 now + ~43.6 RB next) · 62% survives to our turn
  • Travis Etienne Jr. RB · wait costs 3 · pick costs 2.1 · 66% survives to our turn
  • Da
    17:18:22  pick 42  Lamar Jackson (QB) (seat 2) in 18 s
    17:18:25  heartbeat sent (Yahoo told we are not idle)
    17:18:34  plan #37 for pick 43
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 84.7 (40.3 now + ~44.4 RB next) · 57% survives to our turn
  • Travis Etienne Jr. RB · wait costs 2 · pick costs 3.5 · 73% survives to our turn
  • Da
    17:18:38  pick 43  Travis Etienne Jr. (RB) (seat 3) in 15 s — a target is gone (was 73% to survive)
    17:18:44  pick 44  D'Andre Swift (RB) (seat 4) in 6 s — a target is gone
    17:18:44  pick 45  Emeka Egbuka (WR) (seat 5) in 0 s INSTANTLY (autopick)
    17:18:46  plan #38 for pick 46
  • Drake Maye QB · wait costs 2 · pick costs 0, best pair 69.9 (40.3 now + ~29.6 RB next) · 88% survives to our turn
  • Davante Adams WR · wait costs 1 · pick costs 2 · 89% survives to our turn
  • Jaylen Wa
    17:18:54  pick 46  DJ Moore (WR) (seat 6) in 10 s
    17:18:57  pick 47  Terry McLaurin (WR) (seat 7) in 3 s
    17:18:58  plan #39 for pick 48
  • Drake Maye QB · safe to wait · pick costs 0, best pair 69.9 (40.3 now + ~29.7 RB next) · 94% survives to our turn
  • Davante Adams WR · safe to wait · pick costs 1.2 · 99% survives to our turn
  • Jaylen 
    17:19:17  pick 48  Bucky Irving (RB) (seat 8) in 20 s
    17:19:17  plan #41 for pick 49
  • Drake Maye QB · wait costs 3 · pick costs 0, best pair 69.9 (40.3 now + ~29.7 RB next) · 81% survives to our turn
  • Davante Adams WR · wait costs 2 · pick costs 3 · 86% survives to our turn
  • Jaylen Wa
    17:19:17  ON THE CLOCK, pick 49 · plan #41 (0.0 s old) · lineup needs QB WR FLEX K DEF
    17:19:20  PICKED Drake Maye (QB) via action, confirmed in 1051 ms — chose Drake Maye (QB): waiting would likely cost about 3 points at QB, 81% to still be there next turn
    17:19:22  pick 50  Tyler Warren (TE) (seat 10) in 2 s
    17:19:22  pick 51  Bhayshul Tuten (RB) (seat 10) in 0 s
    17:19:23  plan #42 for pick 52
  • Davante Adams WR · wait costs 4 · pick costs 0, best pair 57.8 (29.2 now + ~28.6 RB next) · 70% survives to our turn
  • Jaylen Warren RB · wait costs 1 · pick costs 2.8 · 69% survives to our turn
  • Rham
    17:19:23  ON THE CLOCK, pick 52 · plan #42 (0.0 s old) · lineup needs WR FLEX K DEF
    17:19:24  PICKED Davante Adams (WR) via action, confirmed in 451 ms — chose Davante Adams (WR): waiting would likely cost about 4 points at WR, 70% to still be there next turn
  • top projection left was Jalen Hurts, passed on purpose
    17:19:26  heartbeat sent (Yahoo told we are not idle)
    17:19:27  plan #43 for pick 53
  • Jaylen Warren RB · safe to wait · 72% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • Quinshon Judkins RB · depth fallback, engine list done
    17:19:46  pick 53  Joe Burrow (QB) (seat 8) in 22 s
    17:19:49  pick 54  Quinshon Judkins (RB) (seat 7) in 3 s — a target is gone
    17:19:52  plan #45 for pick 55
  • Jaylen Warren RB · wait costs 1 · 73% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:20:01  pick 55  Jalen Hurts (QB) (seat 6) in 12 s
    17:20:02  pick 56  Jayden Daniels (QB) (seat 5) in 1 s INSTANTLY (autopick)
    17:20:04  plan #46 for pick 57
  • Jaylen Warren RB · wait costs 1 · 74% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:20:17  pick 57  Christian Watson (WR) (seat 4) in 15 s — a target is gone
    17:20:26  heartbeat sent (Yahoo told we are not idle)
    17:20:29  plan #48 for pick 58
  • Jaylen Warren RB · safe to wait · 78% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:20:34  pick 58  David Montgomery (RB) (seat 3) in 16 s — a target is gone
    17:20:41  plan #49 for pick 59
  • Jaylen Warren RB · safe to wait · 76% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:20:49  pick 59  Rome Odunze (WR) (seat 2) in 16 s — a target is gone
    17:20:49  pick 60  Jadarian Price (RB) (seat 1) in 0 s INSTANTLY (autopick)
    17:20:50  pick 61  Caleb Williams (QB) (seat 1) in 1 s INSTANTLY (autopick)
    17:20:54  plan #50 for pick 62
  • Jaylen Warren RB · safe to wait · 80% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:21:09  pick 62  Blake Corum (RB) (seat 2) in 19 s
    17:21:19  plan #52 for pick 63
  • Jaylen Warren RB · safe to wait · 91% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:21:27  heartbeat sent (Yahoo told we are not idle)
    17:21:28  pick 63  Tucker Kraft (TE) (seat 3) in 19 s
    17:21:31  plan #53 for pick 64
  • Jaylen Warren RB · safe to wait · 90% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:21:31  pick 64  Parker Washington (WR) (seat 4) in 3 s — a target is gone
    17:21:31  pick 65  Sam LaPorta (TE) (seat 5) in 0 s INSTANTLY (autopick)
    17:21:40  pick 66  Harold Fannin Jr. (TE) (seat 6) in 9 s
    17:21:43  plan #54 for pick 67
  • Jaylen Warren RB · safe to wait · 95% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:21:48  pick 67  Jameson Williams (WR) (seat 7) in 8 s — a target is gone
    17:21:55  plan #55 for pick 68
  • Jaylen Warren RB · safe to wait · 98% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    17:21:59  pick 68  TreVeyon Henderson (RB) (seat 8) in 11 s — a target is gone
    17:21:59  plan #56 for pick 69
  • Jaylen Warren RB · safe to wait · 90% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • Mike Evans WR · depth fallback, engine list done
    17:21:59  ON THE CLOCK, pick 69 · plan #56 (0.0 s old) · lineup needs FLEX K DEF
    17:22:00  PICKED Jaylen Warren (RB) via action, confirmed in 468 ms — chose Jaylen Warren (RB): nothing urgent, the most valuable player who fills a slot (90% to survive, nobody better worth waiting for)
  • top projection left was Trevor L
    17:22:02  pick 70  Justin Herbert (QB) (seat 10) in 2 s
    17:22:02  pick 71  Luther Burden III (WR) (seat 10) in 0 s — a target is gone
    17:22:03  plan #57 for pick 72
  • Rico Dowdle RB · insurance worth ~26 · 52% survives to our turn
  • Mike Evans WR · insurance worth ~10 · 58% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
    17:22:03  ON THE CLOCK, pick 72 · plan #57 (0.0 s old) · lineup needs K DEF
    17:22:04  PICKED Rico Dowdle (RB) via action, confirmed in 622 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +2.7 a week over the wire, about 26 points
  • he also backs up one of our
    17:22:08  plan #58 for pick 73
  • Mike Evans WR · insurance worth ~10 · 61% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 45% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    17:22:14  pick 73  Jonathon Brooks (RB) (seat 8) in 10 s
    17:22:17  pick 74  Kyle Pitts Sr. (TE) (seat 7) in 3 s
    17:22:19  pick 75  Marvin Harrison Jr. (WR) (seat 6) in 2 s INSTANTLY (autopick) — a target is gone
    17:22:19  pick 76  Mike Evans (WR) (seat 5) in 0 s INSTANTLY (autopick) — a target is gone (was 61% to survive)
    17:22:20  plan #59 for pick 76
  • Mike Evans WR · insurance worth ~10 · 61% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 50% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    17:22:20  bridge warning: dropped 1 feed entries numbered >= header pick 76
    17:22:23  pick 77  Dak Prescott (QB) (seat 4) in 4 s
    17:22:27  heartbeat sent (Yahoo told we are not idle)
    17:22:32  plan #60 for pick 78
  • DK Metcalf WR · insurance worth ~7 · 53% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 62% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    17:22:51  pick 78  Alec Pierce (WR) (seat 3) in 28 s
    17:22:57  plan #62 for pick 79
  • DK Metcalf WR · insurance worth ~7 · 56% survives to our turn
  • Rhamondre Stevenson RB · insurance worth ~7 · 62% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    17:22:57  pick 79  Kyle Monangai (RB) (seat 2) in 6 s
    17:22:58  pick 80  Rhamondre Stevenson (RB) (seat 1) in 1 s INSTANTLY (autopick) — a target is gone (was 62% to survive)
    17:22:59  pick 81  Brian Thomas Jr. (WR) (seat 1) in 1 s INSTANTLY (autopick)
    17:23:00  pick 82  Carnell Tate (WR) (seat 2) in 1 s INSTANTLY (autopick) — a target is gone
    17:23:09  plan #63 for pick 83
  • DK Metcalf WR · insurance worth ~7 · 76% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 92% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:23:28  heartbeat sent (Yahoo told we are not idle)
    17:23:31  pick 83  Trevor Lawrence (QB) (seat 3) in 31 s
    17:23:32  pick 84  MarShawn Lloyd (RB) (seat 4) in 1 s INSTANTLY (autopick)
    17:23:32  pick 85  DK Metcalf (WR) (seat 5) in 0 s INSTANTLY (autopick) — a target is gone (was 76% to survive)
    17:23:34  plan #65 for pick 86
  • Wan'Dale Robinson WR · insurance worth ~7 · 99% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 96% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:23:36  pick 86  Tony Pollard (RB) (seat 6) in 5 s
    17:23:46  plan #66 for pick 87
  • Wan'Dale Robinson WR · insurance worth ~7 · 99% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 96% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:23:58  pick 87  Michael Wilson (WR) (seat 7) in 22 s — a target is gone
    17:23:58  plan #67 for pick 88
  • Wan'Dale Robinson WR · insurance worth ~7 · 100% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 99% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:24:07  pick 88  George Kittle (TE) (seat 8) in 9 s
    17:24:08  plan #68 for pick 89
  • Wan'Dale Robinson WR · insurance worth ~7 · 100% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 98% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:24:08  ON THE CLOCK, pick 89 · plan #68 (0.0 s old) · lineup needs K DEF
    17:24:09  PICKED Wan'Dale Robinson (WR) via action, confirmed in 468 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +1.0 a week over the wire, about 7 points
  • top projection l
    17:24:11  pick 90  Chris Godwin Jr. (WR) (seat 10) in 3 s — a target is gone
    17:24:11  pick 91  J.K. Dobbins (RB) (seat 10) in 0 s
    17:24:12  plan #69 for pick 92
  • Patrick Mahomes II QB · insurance worth ~8 · 63% survives to our turn
  • RJ Harvey RB · insurance worth ~5 · 67% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 64% survives to our tur
    17:24:12  ON THE CLOCK, pick 92 · plan #69 (0.0 s old) · lineup needs K DEF
    17:24:13  PICKED Patrick Mahomes II (QB) via action, confirmed in 404 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    17:24:17  plan #70 for pick 93
  • RJ Harvey RB · insurance worth ~5 · 69% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 64% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:24:28  heartbeat sent (Yahoo told we are not idle)
    17:24:45  pick 93  Josh Downs (WR) (seat 8) in 31 s — a target is gone
    17:24:51  pick 94  Rams (DEF) (seat 7) in 6 s
    17:24:53  plan #73 for pick 95
  • RJ Harvey RB · insurance worth ~5 · 71% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 61% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:25:07  pick 95  Quentin Johnston (WR) (seat 6) in 16 s — a target is gone
    17:25:07  pick 96  Chuba Hubbard (RB) (seat 5) in 0 s INSTANTLY (autopick)
    17:25:18  plan #75 for pick 97
  • RJ Harvey RB · insurance worth ~5 · 71% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 70% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:25:28  pick 97  Jacory Croskey-Merritt (RB) (seat 4) in 21 s
    17:25:28  pick 98  Stefon Diggs (WR) (seat 3) in 0 s INSTANTLY (autopick) — a target is gone
    17:25:28  heartbeat sent (Yahoo told we are not idle)
    17:25:30  plan #76 for pick 99
  • RJ Harvey RB · insurance worth ~5 · 73% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 72% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:25:34  pick 99  Texans (DEF) (seat 2) in 6 s
    17:25:35  pick 100  Brock Purdy (QB) (seat 1) in 1 s INSTANTLY (autopick)
    17:25:37  pick 101  Jordan Mason (RB) (seat 1) in 1 s INSTANTLY (autopick)
    17:25:43  plan #77 for pick 102
  • RJ Harvey RB · insurance worth ~5 · 83% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 87% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:25:47  pick 102  Ja'Kobi Lane (WR) (seat 2) in 11 s
    17:25:48  pick 103  Bo Nix (QB) (seat 3) in 1 s INSTANTLY (autopick)
    17:25:50  pick 104  Dalton Kincaid (TE) (seat 4) in 2 s INSTANTLY (autopick)
    17:25:50  pick 105  Jaxson Dart (QB) (seat 5) in 0 s INSTANTLY (autopick)
    17:25:53  pick 106  Bills (DEF) (seat 6) in 2 s INSTANTLY (autopick)
    17:25:55  plan #78 for pick 107
  • RJ Harvey RB · insurance worth ~5 · 97% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 98% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    17:25:55  bridge warning: 1 drafted entries matched no board player: 106 Bills
    17:25:59  pick 107  RJ Harvey (RB) (seat 7) in 6 s — a target is gone (was 97% to survive)
    17:26:06  pick 108  Brandon Aubrey (K) (seat 8) in 7 s
    17:26:06  plan #79 for pick 109
  • Kenny Gainwell RB · insurance worth ~5 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 97% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    17:26:06  ON THE CLOCK, pick 109 · plan #79 (0.1 s old) · lineup needs K DEF
    17:26:07  PICKED Kenny Gainwell (RB) via action, confirmed in 477 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +1.8 a week over the wire, about 5 points
  • top projection left wa
    17:26:10  pick 110  Matthew Stafford (QB) (seat 10) in 2 s
    17:26:10  pick 111  Dallas Goedert (TE) (seat 10) in 0 s
    17:26:11  plan #80 for pick 112
  • Courtland Sutton WR · insurance worth ~1 · 94% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 92% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    17:26:11  ON THE CLOCK, pick 112 · plan #80 (0.0 s old) · lineup needs K DEF
    17:26:12  PICKED Courtland Sutton (WR) via action, confirmed in 595 ms — lineup full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +1.0 a week over the wire, about 1 points
  • top projection lef
    17:26:15  plan #81 for pick 113
  • Aaron Jones Sr. RB · insurance worth ~0 · 91% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 92% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    17:26:24  pick 113  Isaiah Likely (TE) (seat 8) in 12 s
    17:26:27  pick 114  Aaron Jones Sr. (RB) (seat 7) in 3 s — a target is gone (was 91% to survive)
    17:26:28  plan #82 for pick 115
  • Woody Marks RB · insurance worth ~0 · 94% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 94% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    17:26:30  heartbeat sent (Yahoo told we are not idle)
    17:26:46  pick 115  Baker Mayfield (QB) (seat 6) in 19 s
    17:26:46  pick 116  Travis Kelce (TE) (seat 5) in 0 s INSTANTLY (autopick)
    17:26:53  plan #84 for pick 117
  • Woody Marks RB · insurance worth ~0 · 94% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 95% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    17:26:57  pick 117  Michael Pittman Jr. (WR) (seat 4) in 11 s — a target is gone (was 95% to survive)
    17:26:59  pick 118  Mark Andrews (TE) (seat 3) in 2 s INSTANTLY (autopick)
    17:27:05  plan #85 for pick 119
  • Woody Marks RB · insurance worth ~0 · 96% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 96% survives to our turn
  • Jordan Addison WR · depth fallback, engine list done
    17:27:08  pick 119  Josh Jacobs (RB) (seat 2) in 9 s
    17:27:08  pick 120  Juwan Johnson (TE) (seat 1) in 0 s INSTANTLY (autopick)
    17:27:10  pick 121  De'Zhaun Stribling (WR) (seat 1) in 2 s INSTANTLY (autopick)
    17:27:12  pick 122  Caleb Douglas (WR) (seat 2) in 2 s INSTANTLY (autopick)
    17:27:12  pick 123  Jordan Addison (WR) (seat 3) in 1 s INSTANTLY (autopick) — a target is gone
    17:27:18  plan #86 for pick 124
  • Woody Marks RB · insurance worth ~0 · 97% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 97% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    17:27:18  bridge warning: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    17:27:31  heartbeat sent (Yahoo told we are not idle)
    17:27:33  pick 124  Broncos (DEF) (seat 4) in 21 s
    17:27:33  pick 125  Jayden Reed (WR) (seat 5) in 0 s INSTANTLY (autopick) — a target is gone
    17:27:36  pick 126  Keenan Allen (WR) (seat 6) in 3 s
    17:27:40  pick 127  Trey Smack (K) (seat 7) in 4 s
    17:27:42  plan #88 for pick 128
  • Woody Marks RB · insurance worth ~0 · 99% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 99% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    17:27:47  pick 128  Kyler Murray (QB) (seat 8) in 7 s
    17:27:48  plan #89 for pick 129
  • Woody Marks RB · insurance worth ~0 · 100% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 100% survives to our turn
  • Makai Lemon WR · depth fallback, engine list done
    17:27:49  ON THE CLOCK, pick 129 · plan #89 (0.0 s old) · lineup needs K DEF
    17:27:49  PICKED Woody Marks (RB) via action, confirmed in 394 ms — lineup full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +0.4 a week over the wire, about 0 points
  • top projection left was Jare
    17:27:52  pick 130  KC Concepcion (WR) (seat 10) in 2 s — a target is gone
    17:27:52  pick 131  Seahawks (DEF) (seat 10) in 0 s
    17:27:53  plan #90 for pick 132
  • Philadelphia Eagles DEF · wait costs 1 · pick costs 0, best pair 84.1 (8 now + ~76.1 RB next) · 43% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 3.5 · 68% survives to our turn
  •
    17:27:53  ON THE CLOCK, pick 132 · plan #90 (0.0 s old) · lineup needs K DEF
    17:27:54  PICKED Philadelphia Eagles (DEF) via action, confirmed in 344 ms — chose Philadelphia Eagles (DEF): waiting would likely cost about 1 points at DEF, 43% to still be there next turn
  • top projection left was Jared Goff, passed on
    17:27:57  plan #91 for pick 133
  • Cameron Dicker K · safe to wait · 70% survives to our turn
  • Ka'imi Fairbairn K · depth fallback, engine list done
  • Cam Little K · depth fallback, engine list done
    17:28:12  pick 133  Matthew Golden (WR) (seat 8) in 18 s
    17:28:13  pick 134  Sam Darnold (QB) (seat 7) in 1 s INSTANTLY (autopick)
    17:28:15  pick 135  Chris Boswell (K) (seat 6) in 2 s INSTANTLY (autopick)
    17:28:15  pick 136  Ka'imi Fairbairn (K) (seat 5) in 0 s INSTANTLY (autopick) — a target is gone
    17:28:18  pick 137  Jason Myers (K) (seat 4) in 3 s — a target is gone
    17:28:18  pick 138  Cameron Dicker (K) (seat 3) in 0 s INSTANTLY (autopick) — a target is gone (was 70% to survive)
    17:28:21  plan #93 for pick 139
  • Cam Little K · safe to wait · 80% survives to our turn
  • Eddy Pineiro K · depth fallback, engine list done
  • Tyler Loop K · depth fallback, engine list done
    17:28:21  bridge warning: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    17:28:24  pick 139  Jordan Love (QB) (seat 2) in 6 s
    17:28:24  pick 140  Vikings (DEF) (seat 1) in 0 s
    17:28:24  pick 141  Cam Little (K) (seat 1) in 0 s — a target is gone (was 80% to survive)
    17:28:31  heartbeat sent (Yahoo told we are not idle)
    17:28:34  plan #94 for pick 142
  • Eddy Pineiro K · safe to wait · 84% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    17:28:45  pick 142  Makai Lemon (WR) (seat 2) in 21 s
    17:28:46  pick 143  Jaguars (DEF) (seat 3) in 1 s INSTANTLY (autopick)
    17:28:47  plan #95 for pick 144
  • Eddy Pineiro K · safe to wait · 90% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    17:28:59  pick 144  Jared Goff (QB) (seat 4) in 12 s
    17:28:59  plan #96 for pick 145
  • Eddy Pineiro K · safe to wait · 91% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    17:28:59  pick 145  Patriots (DEF) (seat 5) in 1 s INSTANTLY (autopick)
    17:29:07  pick 146  Chris Rodriguez Jr. (RB) (seat 6) in 7 s
    17:29:08  pick 147  Jake Ferguson (TE) (seat 7) in 1 s INSTANTLY (autopick)
    17:29:10  pick 148  Ravens (DEF) (seat 8) in 2 s INSTANTLY (autopick)
    17:29:10  plan #97 for pick 149
  • Eddy Pineiro K
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    17:29:10  ON THE CLOCK, pick 149 · plan #97 (0.0 s old) · lineup needs K
    17:29:11  PICKED Eddy Pineiro (K) via action, confirmed in 386 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Daniel Jones, passed on purpose
    17:29:13  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    17:12:19 PT preflight: ok=true pick_path=action my_team=9 plan=plan 25 deep @pick 1 via store call#1
    17:12:19 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    17:12:19 PT NARR info driver started — seat 9, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    17:13:20 PT heartbeat: setAwayStatus(false)
    17:13:20 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:14:03 PT ON CLOCK -> {"drafted":"Jaxon Smith-Njigba","pos":"WR","vorp":89.4,"proj":231.5,"why":"waiting likely costs ~5 pts at WR (best option now 89, ~84 by your next turn) · 85% chance he's still there at your next pick · fills your op
    17:14:20 PT heartbeat: setAwayStatus(false)
    17:14:20 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:14:37 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~17 pts at RB (best option now 73, ~56 by your next turn) · 34% chance he's still there at your next pick · fills your open R
    17:15:20 PT heartbeat: setAwayStatus(false)
    17:15:20 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:16:21 PT heartbeat: setAwayStatus(false)
    17:16:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:17:01 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~11 pts at TE (best option now 78, ~67 by your next turn) · 80% chance he's still there at your next pick · fills your open TE
    17:17:05 PT ON CLOCK -> {"drafted":"Javonte Williams","pos":"RB","vorp":36.9,"proj":197.1,"why":"waiting likely costs ~9 pts at RB (best option now 37, ~28 by your next turn) · 41% chance he's still there at your next pick · fills your open
    17:17:23 PT heartbeat: setAwayStatus(false)
    17:17:23 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:18:25 PT heartbeat: setAwayStatus(false)
    17:18:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:19:20 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~3 pts at QB (best option now 31, ~29 by your next turn) · 81% chance he's still there at your next pick · fills your open QB sl
    17:19:24 PT ON CLOCK -> {"drafted":"Davante Adams","pos":"WR","vorp":13.1,"proj":155.2,"why":"waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 70% chance he's still there at your next pick · fills your open WR 
    17:19:26 PT heartbeat: setAwayStatus(false)
    17:19:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:20:26 PT heartbeat: setAwayStatus(false)
    17:20:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:21:27 PT heartbeat: setAwayStatus(false)
    17:21:27 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:22:00 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on your FLEX spot · 90% chance he's still there at your next pick · fills a FLEX slot","s":0.898,"sr":0.898,"e":9.1,"top_proj_availabl
    17:22:04 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +2.7/wk over the wire (Chris Rodriguez Jr.) ≈ 26 pts · HANDCUFF: backs up your Jaylen Warren"
    17:22:20 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 76
    17:22:27 PT heartbeat: setAwayStatus(false)
    17:22:27 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:23:28 PT heartbeat: setAwayStatus(false)
    17:23:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:24:09 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +1.0/wk over the wire (Romeo Doubs) ≈ 7 pts","s":1,"sr":1,"e":-10.6,"top_proj_availab
    17:24:13 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Tyler Shough) ≈ 8 pts","s":0.625,"sr":0.625,"e":9.9,"top_proj_a
    17:24:28 PT heartbeat: setAwayStatus(false)
    17:24:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:25:28 PT heartbeat: setAwayStatus(false)
    17:25:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:25:55 PT BRIDGE WARNING: 1 drafted entries matched no board player: 106 Bills
    17:26:07 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +1.8/wk over the wire (Chris Rodriguez Jr.) ≈ 5 pts","s":0.98
    17:26:12 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +1.0/wk over the wire (Deebo Samuel Sr.) ≈ 1 pts","s":0.
    17:26:30 PT heartbeat: setAwayStatus(false)
    17:26:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:27:18 PT BRIDGE WARNING: 2 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas
    17:27:31 PT heartbeat: setAwayStatus(false)
    17:27:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:27:49 PT ON CLOCK -> {"drafted":"Woody Marks","pos":"RB","vorp":-30.3,"proj":129.9,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +0.4/wk over the wire (Chris Rodriguez Jr.) ≈ 0 pts","s":0.9
    17:27:54 PT ON CLOCK -> {"drafted":"Philadelphia Eagles","pos":"DEF","vorp":10,"proj":127,"why":"waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 43% chance he's still there at your next pick · fills your open
    17:28:21 PT BRIDGE WARNING: 3 drafted entries matched no board player: 106 Bills, 122 Caleb Douglas, 135 Chris Boswell
    17:28:31 PT heartbeat: setAwayStatus(false)
    17:28:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    17:29:11 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection":
    17:29:13 PT roster full
    17:29:13 PT NARR info roster full — driver done; posting the trail when the room finishes
    17:29:13 PT driver stop


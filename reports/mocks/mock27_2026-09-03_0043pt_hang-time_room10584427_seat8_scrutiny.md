# Scrutiny: Mock 27 -- Hang Time (room 10584427) -- Thursday 2026-09-03 00:43 PT -- 10 teams, our seat 8

Captured 2026-09-03 01:05:23 PT. Times below are Pacific. 10 teams, our team id 8, draft slot 8. 150 picks in the trail, 114 bridge plan calls, 90 recs events in the room log.

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
- Action latency to store confirmation: median 436 ms, min 353, max 603.
- Heartbeats 5; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (2): 1 drafted entries matched no board player: 127 Kaleb Johnson; 2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard.
- Away seats over the room (each change): {} -> {5} -> {4,5} -> {5} -> {5,6} -> {4,5,6} -> {2,4,5,6} -> {4,5,6} -> {4,5,6,10} -> {4,5,6} -> {4,5,6,10}.
- Managers away at the end: 4 Raymond, 5 Sergio, 6 Luke, 10 Dylan.

## Our picks, one block each

### Pick 8 (round 1): Jaxon Smith-Njigba (WR)

- In plain English: Took Jaxon Smith-Njigba (WR) because waiting would likely cost about 12 points at WR, with a 65% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 402 ms, ranker engine, plan call 10, plan age 718 ms, at 00:44:52 PT.
- Engine's reason: waiting likely costs ~12 pts at WR (best option now 89, ~78 by your next turn) · 65% chance he's still there at your next pick · fills your open WR slot · last WR at this level — big drop after him · 4 teams picking befo
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: De'Von Achane (RB, s=0.721, e=70.4); Trey McBride (TE, s=0.969, e=77.3); Josh Allen (QB, s=0.903, e=45.5).
- Plan call 10 @pick 8: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 7 drafted / 0 mine.
- Engine's first choice was **Jaxon Smith-Njigba** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaxon Smith-Njigba | WR | 89.4 | 0.65 | 0.65 | 77.5 | 89.4 | waiting likely costs ~12 pts at WR (best option now 89, ~78 by your next turn) · 65% chanc |
| De'Von Achane | RB | 73.4 | 0.72 | 0.72 | 70.4 | 73.4 | waiting likely costs ~3 pts at RB (best option now 73, ~70 by your next turn) · 72% chance |
| Trey McBride | TE | 77.9 | 0.97 | 0.97 | 77.3 | 77.9 | safe to wait on TE · 97% chance he's still there at your next pick · fills your open TE sl |
| Josh Allen | QB | 47.0 | 0.90 | 0.90 | 45.5 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 90% chance |
| James Cook III | RB | 63.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase Brown | RB | 60.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 45.5 | 1.5 | 7 |
| RB | 73.4 | 70.4 | 3.0 | 23 |
| WR | 89.4 | 77.5 | 11.9 | 25 |
| TE | 77.9 | 77.3 | 0.6 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 72.2 | 1.2 | 54 |

### Pick 13 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 20 points at RB, with a 36% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 420 ms, ranker engine, plan call 13, plan age 731 ms, at 00:45:24 PT.
- Engine's reason: waiting likely costs ~20 pts at RB (best option now 73, ~53 by your next turn) · 36% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 14 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Justin Jefferson (WR, s=0.474, e=48.4); Trey McBride (TE, s=0.44, e=55.3); Josh Allen (QB, s=0.41, e=37.4).
- Plan call 13 @pick 13: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 12 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.36 | 0.36 | 53.4 | 73.4 | waiting likely costs ~20 pts at RB (best option now 73, ~53 by your next turn) · 36% chanc |
| Justin Jefferson | WR | 53.9 | 0.47 | 0.47 | 48.4 | 53.9 | waiting likely costs ~6 pts at WR (best option now 54, ~48 by your next turn) · 47% chance |
| Trey McBride | TE | 77.9 | 0.44 | 0.44 | 55.3 | 77.9 | waiting likely costs ~23 pts at TE (best option now 78, ~55 by your next turn) · 44% chanc |
| Josh Allen | QB | 47.0 | 0.41 | 0.41 | 37.4 | 47.0 | waiting likely costs ~10 pts at QB (best option now 47, ~37 by your next turn) · 41% chanc |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake London | WR | 51.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 37.4 | 9.6 | 8 |
| RB | 73.4 | 53.4 | 20.0 | 20 |
| WR | 53.9 | 48.4 | 5.5 | 24 |
| TE | 77.9 | 55.3 | 22.6 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 53.9 | 19.5 | 52 |

### Pick 28 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 10 points at TE, with a 82% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 436 ms, ranker engine, plan call 29, plan age 749 ms, at 00:48:42 PT.
- Engine's reason: waiting likely costs ~10 pts at TE (best option now 78, ~68 by your next turn) · 82% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 4 teams
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Josh Allen (QB, s=0.89, e=45.2); Travis Etienne Jr. (RB, s=0.866, e=25.5); Chris Olave (WR, s=None, e=None).
- Plan call 29 @pick 28: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 27 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.82 | 0.82 | 68.0 | 77.9 | waiting likely costs ~10 pts at TE (best option now 78, ~68 by your next turn) · 82% chanc |
| A.J. Brown | WR | 43.6 | 0.77 | 0.77 | 42.4 | 43.6 | waiting likely costs ~1 pts at WR (best option now 44, ~42 by your next turn) · 77% chance |
| Josh Allen | QB | 47.0 | 0.89 | 0.89 | 45.2 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 89% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.87 | 0.87 | 25.5 | 26.3 | safe to wait on RB · 87% chance he's still there at your next pick · fills your open RB sl |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 45.2 | 1.8 | 10 |
| RB | 26.3 | 25.5 | 0.8 | 15 |
| WR | 43.6 | 42.4 | 1.2 | 24 |
| TE | 77.9 | 68.0 | 9.9 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 39.985766857976785 | 37.5 | 2.5 | 47 |

### Pick 33 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 2 points at WR, with a 46% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 431 ms, ranker engine, plan call 32, plan age 744 ms, at 00:49:11 PT.
- Engine's reason: waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 46% chance he's still there at your next pick · fills your open WR slot · 14 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.462, e=20.5); Drake Maye (QB, s=0.461, e=23.7); DeVonta Smith (WR, s=None, e=None).
- Plan call 32 @pick 33: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 32 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.46 | 0.46 | 22.1 | 23.9 | waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 46% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.46 | 0.46 | 20.5 | 26.3 | waiting likely costs ~6 pts at RB (best option now 26, ~21 by your next turn) · 46% chance |
| Drake Maye | QB | 31.1 | 0.46 | 0.46 | 23.7 | 31.1 | waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 46% chance |
| DeVonta Smith | WR | 23.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 23.7 | 7.4 | 10 |
| RB | 26.3 | 20.5 | 5.8 | 16 |
| WR | 23.9 | 22.1 | 1.8 | 21 |
| TE | 23.8 | 22.3 | 1.5 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 26.331806855987054 | 20.6 | 5.8 | 44 |

### Pick 48 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 2 points at QB, with a 88% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 463 ms, ranker engine, plan call 42, plan age 774 ms, at 00:51:18 PT.
- Engine's reason: waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 88% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.951, e=9.2); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 42 @pick 48: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 47 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.88 | 0.88 | 29.5 | 31.1 | waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 88% chance |
| Jaylen Warren | RB | 9.3 | 0.95 | 0.95 | 9.2 | 9.3 | safe to wait on RB · 95% chance he's still there at your next pick · fills your open RB sl |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 29.5 | 1.6 | 14 |
| RB | 9.3 | 9.2 | 0.1 | 17 |
| WR | 13.1 | 12.3 | 0.8 | 20 |
| TE | 21.1 | 21.0 | 0.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 45 |

### Pick 53 (round 6): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (83% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 441 ms, ranker engine, plan call 46, plan age 787 ms, at 00:51:54 PT.
- Engine's reason: safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Davante Adams (WR, s=None, e=None); Rhamondre Stevenson (RB, s=None, e=None); Quinshon Judkins (RB, s=None, e=None).
- Plan call 46 @pick 53: needs {'QB': 0, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6], state store with 52 drafted / 5 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.83 | 0.83 | 8.9 | 9.3 | safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB sl |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quinshon Judkins | RB | 3.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Terry McLaurin | WR | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 15.2 | 2.8 | 14 |
| RB | 9.3 | 8.9 | 0.4 | 16 |
| WR | 13.1 | 9.5 | 3.6 | 19 |
| TE | 21.1 | 19.6 | 1.5 | 10 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.9 | 0.4 | 45 |

### Pick 68 (round 7): Rhamondre Stevenson (RB)

- In plain English: Took Rhamondre Stevenson (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (82% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 603 ms, ranker engine, plan call 58, plan age 918 ms, at 00:54:36 PT.
- Engine's reason: safe to wait on your FLEX spot · 82% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: TreVeyon Henderson (RB, s=None, e=None); Rome Odunze (WR, s=None, e=None); Mike Evans (WR, s=None, e=None).
- Plan call 58 @pick 68: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 67 drafted / 6 mine.
- Engine's first choice was **Rhamondre Stevenson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rhamondre Stevenson | RB | 7.2 | 0.82 | 0.82 | 6.3 | 7.2 | safe to wait on your FLEX spot · 82% chance he's still there at your next pick · fills a F |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.2 | 0.5 | 19 |
| RB | 7.2 | 6.3 | 0.9 | 23 |
| WR | -0.7 | -0.8 | 0.1 | 29 |
| TE | 21.1 | 20.4 | 0.7 | 19 |
| K | 13.5 | 13.5 | 0.0 | 6 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 7.2333043142844815 | 6.3 | 0.9 | 71 |

### Pick 73 (round 8): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 87 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 374 ms, ranker engine, plan call 62, plan age 698 ms, at 00:55:07 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 87 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rome Odunze (WR, s=0.722, e=-1.8); Mike Evans (WR, s=None, e=None); DK Metcalf (WR, s=None, e=None).
- Plan call 62 @pick 73: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 72 drafted / 7 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.98 | 0.98 | -6.5 | -6.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs |
| Rome Odunze | WR | -0.7 | 0.72 | 0.72 | -1.8 | -0.7 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.3/wk over the wire (Rashod Bate |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.0 | 1.7 | 20 |
| RB | -6.2 | -6.5 | 0.3 | 30 |
| WR | -0.7 | -1.8 | 1.1 | 39 |
| TE | 21.1 | 17.0 | 4.1 | 22 |
| K | 13.5 | 13.0 | 0.5 | 10 |
| DEF | 18.0 | 17.7 | 0.3 | 7 |

### Pick 88 (round 9): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +7.9 points a week over the waiver wire (Josh Jacobs), worth about 20 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 470 ms, ranker engine, plan call 73, plan age 829 ms, at 00:57:14 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +7.9/wk over the wire (Josh Jacobs) ≈ 20 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Wan'Dale Robinson (WR, s=0.988, e=-10.6); Courtland Sutton (WR, s=None, e=None); Michael Pittman Jr. (WR, s=None, e=None).
- Plan call 73 @pick 88: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 87 drafted / 8 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.99 | 0.99 | -25.9 | -25.9 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +7.9 |
| Wan'Dale Robinson | WR | -10.6 | 0.99 | 0.99 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Wilson | WR | -14.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.3 | 0.4 | 20 |
| RB | -25.9 | -25.9 | 0.0 | 25 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 19.8 | 18.9 | 0.9 | 20 |
| K | 13.5 | 13.5 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 10 |

### Pick 93 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 508 ms, ranker engine, plan call 77, plan age 831 ms, at 00:57:57 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.618, e=10); Kyle Monangai (RB, s=0.762, e=-29.2); Matthew Stafford (QB, s=None, e=None).
- Plan call 77 @pick 93: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 92 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.95 | 0.95 | -10.7 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.62 | 0.62 | 10.0 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Kyle Monangai | RB | -28.8 | 0.76 | 0.76 | -29.2 | -28.8 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.0 | 2.8 | 19 |
| RB | -28.8 | -29.2 | 0.4 | 24 |
| WR | -10.6 | -10.7 | 0.1 | 37 |
| TE | 13.8 | 12.0 | 1.8 | 19 |
| K | 13.5 | 13.3 | 0.2 | 14 |
| DEF | 18.0 | 17.5 | 0.5 | 10 |

### Pick 108 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 528 ms, ranker engine, plan call 85, plan age 842 ms, at 00:59:34 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Michael Pittman Jr. (WR, s=0.966, e=-13.4); Woody Marks (RB, s=0.983, e=-30.3); Jared Goff (QB, s=None, e=None).
- Plan call 85 @pick 108: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 107 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.96 | 0.96 | 11.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Michael Pittman Jr. | WR | -13.3 | 0.97 | 0.97 | -13.4 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Woody Marks | RB | -30.3 | 0.98 | 0.98 | -30.3 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyler Murray | QB | -14.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Baker Mayfield | QB | -14.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.8 | 1.0 | 14 |
| RB | -30.3 | -30.3 | 0.0 | 21 |
| WR | -13.3 | -13.4 | 0.1 | 33 |
| TE | 10.9 | 10.7 | 0.2 | 17 |
| K | 13.5 | 13.5 | 0.0 | 15 |
| DEF | 16.0 | 15.9 | 0.1 | 12 |

### Pick 113 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 416 ms, ranker engine, plan call 91, plan age 746 ms, at 01:00:40 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Woody Marks (RB, s=0.942, e=-30.5); Alec Pierce (WR, s=None, e=None); Stefon Diggs (WR, s=None, e=None).
- Plan call 91 @pick 113: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 5, 6], state store with 112 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.92 | 0.92 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Woody Marks | RB | -30.3 | 0.94 | 0.94 | -30.5 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Alec Pierce | WR | -17.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Stefon Diggs | WR | -18.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -30.3 | -30.5 | 0.2 | 20 |
| WR | -13.3 | -13.6 | 0.3 | 31 |
| TE | 10.9 | 10.7 | 0.2 | 17 |
| K | 13.5 | 13.2 | 0.3 | 16 |
| DEF | 16.0 | 15.7 | 0.3 | 12 |

### Pick 128 (round 13): Woody Marks (RB)

- In plain English: Lineup already full, so Woody Marks (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +7.6 points a week over the waiver wire (Josh Jacobs), worth about 2 points. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 494 ms, ranker engine, plan call 99, plan age 826 ms, at 01:02:32 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.6/wk over the wire (Josh Jacobs) ≈ 2 pts
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Makai Lemon (WR, s=0.98, e=-27.4); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 99 @pick 128: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5, 6], state store with 127 drafted / 12 mine, warnings ['1 drafted entries matched no board player: 127 Kaleb Johnson'].
- Engine's first choice was **Woody Marks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Woody Marks | RB | -30.3 | 0.98 | 0.98 | -30.3 | -30.3 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Makai Lemon | WR | -27.4 | 0.98 | 0.98 | -27.4 | -27.4 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +1. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyrone Tracy Jr. | RB | -33.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.6 | 0.1 | 10 |
| RB | -30.3 | -30.3 | 0.0 | 19 |
| WR | -27.4 | -27.4 | 0.0 | 24 |
| TE | 0.5 | 0.5 | 0.0 | 14 |
| K | 13.5 | 13.5 | 0.0 | 18 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 133 (round 14): Eagles (DEF)

- In plain English: Took Philadelphia Eagles (DEF) because waiting would likely cost about 1 points at DEF, with a 48% chance he would still be there next turn. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 353 ms, ranker engine, plan call 104, plan age 680 ms, at 01:03:16 PT.
- Engine's reason: waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 48% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · two-pick plan: pair
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Ka'imi Fairbairn (K, s=0.753, e=13.5); Brandon Aubrey (K, s=None, e=None); Cameron Dicker (K, s=None, e=None).
- Plan call 104 @pick 133: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5, 6], state store with 132 drafted / 13 mine, warnings ['1 drafted entries matched no board player: 127 Kaleb Johnson'].
- Engine's first choice was **Philadelphia Eagles** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Philadelphia Eagles | DEF | 10.0 | 0.48 | 0.48 | 8.9 | 10.0 | waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 48% chance |
| Ka'imi Fairbairn | K | 12.0 | 0.75 | 0.75 | 13.5 | 13.5 | safe to wait on K · 75% chance he's still there at your next pick · fills your open K slot |
| Brandon Aubrey | K | 13.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Little | K | 9.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.6 | 0.1 | 10 |
| RB | -33.0 | -33.2 | 0.2 | 18 |
| WR | -27.9 | -28.0 | 0.1 | 23 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 13.5 | 13.5 | 0.0 | 17 |
| DEF | 10.0 | 8.9 | 1.1 | 10 |

### Pick 148 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 383 ms, ranker engine, plan call 114, plan age 714 ms, at 01:05:15 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Jake Bates (K, s=None, e=None); Andy Borregales (K, s=None, e=None).
- Plan call 114 @pick 148: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [4, 5, 6, 10], state store with 147 drafted / 14 mine, warnings ['2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard'].
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | - | - | - | - | fills your open K slot |
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
| 0-30% | 1 | 27% | 0% |
| 30-50% | 33 | 43% | 52% |
| 50-70% | 27 | 60% | 33% |
| 70-90% | 46 | 80% | 37% |
| 90-100% | 97 | 96% | 79% |

204 predictions over 89 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T01:02:31   WARNING plan #99: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:02:34   WARNING plan #100: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:02:47   WARNING plan #101: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:02:59   WARNING plan #102: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:11   WARNING plan #103: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:15   WARNING plan #104: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:19   WARNING plan #105: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:31   WARNING plan #106: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:44   WARNING plan #107: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:03:59   WARNING plan #108: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:04:12   WARNING plan #109: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:04:25   WARNING plan #110: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:04:37   WARNING plan #111: 1 drafted entries matched no board player: 127 Kaleb Johnson
    2026-09-03T01:04:49   WARNING plan #112: 2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard
    2026-09-03T01:05:02   WARNING plan #113: 2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard
    2026-09-03T01:05:14   WARNING plan #114: 2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard

## Driver log (the lines that matter, Pacific time)

    00:43:15 PT preflight: ok=true pick_path=action my_team=8 plan=plan 25 deep @pick 3 via store call#1
    00:43:15 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    00:44:52 PT ON CLOCK -> {"drafted":"Jaxon Smith-Njigba","pos":"WR","vorp":89.4,"proj":231.5,"why":"waiting likely costs ~12 pts at WR (best option now 89, ~78 by your next turn) · 65% chance he's still there at your next pick · fills your o
    00:45:24 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~20 pts at RB (best option now 73, ~53 by your next turn) · 36% chance he's still there at your next pick · fills your open R
    00:47:16 PT heartbeat: setAwayStatus(false)
    00:48:42 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~10 pts at TE (best option now 78, ~68 by your next turn) · 82% chance he's still there at your next pick · fills your open TE
    00:49:11 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 46% chance he's still there at your next pick · fills your open WR 
    00:51:17 PT heartbeat: setAwayStatus(false)
    00:51:18 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 88% chance he's still there at your next pick · fills your open QB sl
    00:51:54 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB","s":0.83
    00:54:36 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"safe to wait on your FLEX spot · 82% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a 
    00:55:07 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 87 pts","s":0.978,"sr":0.978,"e":-6.5,"top_proj_avail
    00:55:17 PT heartbeat: setAwayStatus(false)
    00:57:14 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +7.9/wk over the wire (Josh Jacobs) ≈ 20 pts","s":0.99,"s
    00:57:57 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.951,"sr":0.951,"e":-10.7,"top_
    00:59:18 PT heartbeat: setAwayStatus(false)
    00:59:34 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.959,"sr":0.959,"e":11.8,"top_pr
    01:00:40 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    01:02:31 PT BRIDGE WARNING: 1 drafted entries matched no board player: 127 Kaleb Johnson
    01:02:32 PT ON CLOCK -> {"drafted":"Woody Marks","pos":"RB","vorp":-30.3,"proj":129.9,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.6/wk over the wire (Josh Jacobs) ≈ 2 pts","s":0.983,"sr":
    01:03:16 PT ON CLOCK -> {"drafted":"Philadelphia Eagles","pos":"DEF","vorp":10,"proj":127,"why":"waiting likely costs ~1 pts at DEF (best option now 10, ~9 by your next turn) · 48% chance he's still there at your next pick · fills your open
    01:03:20 PT heartbeat: setAwayStatus(false)
    01:04:49 PT BRIDGE WARNING: 2 drafted entries matched no board player: 127 Kaleb Johnson, 142 Will Reichard
    01:05:15 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection":
    01:05:17 PT roster full
    01:05:17 PT driver stop


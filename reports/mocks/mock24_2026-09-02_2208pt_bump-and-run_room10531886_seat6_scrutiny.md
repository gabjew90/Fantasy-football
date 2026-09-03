# Scrutiny: Mock 24 -- Bump and Run (room 10531886) -- Wednesday 2026-09-02 22:08 PT -- 10 teams, our seat 6

Captured 2026-09-02 22:27:58 PT. Times below are Pacific. 10 teams, our team id 6, draft slot 6. 150 picks in the trail, 85 bridge plan calls, 72 recs events in the room log.

Injected: mock 24: faults at 66 (makePick no-op), 71 (forced away), 78-86 (bridge killed)

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

- Our picks: 15; by the driver 13 (action 12, click 1), by Yahoo from the queue / autopick 2: 86 RJ Harvey, 126 Michael Pittman Jr..
- Action latency to store confirmation: median 501 ms, min 250, max 1455.
- Heartbeats 4; away flags detected and cleared 3; gate failures 4; local-ranker fallbacks 1; plan refresh failures 9.
- Bridge warnings (2): 1 drafted entries matched no board player: 139 Will Reichard; dropped 1 feed entries numbered >= header pick 138.
- Away seats over the room (each change): {} -> {5} -> {7} -> {} -> {4} -> {4,8} -> {4} -> {4,8} -> {4} -> {4,9} -> {3,4,9} -> {3,4,5,9} -> {3,4,5,7,9}.
- Managers away at the end: 3 Jonathan, 4 Matt, 5 Nicholas, 7 Elias, 8 vincent, 9 Burro, 10 Kyle.

## Our picks, one block each

### Pick 6 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 30 points at RB, with a 56% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 934 ms, ranker engine, plan call 4, plan age 1271 ms, at 22:09:00 PT.
- Engine's reason: waiting likely costs ~30 pts at RB (best option now 154, ~125 by your next turn) · 56% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 8 tea
- Top projection available: Josh Allen -> took it: False.
- Passed on: Amon-Ra St. Brown (WR, s=0.481, e=67.1); Trey McBride (TE, s=0.947, e=76.6); Josh Allen (QB, s=0.805, e=43.9).
- Plan call 4 @pick 6: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 5 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.56 | 0.56 | 124.7 | 154.2 | waiting likely costs ~30 pts at RB (best option now 154, ~125 by your next turn) · 56% cha |
| Amon-Ra St. Brown | WR | 81.8 | 0.48 | 0.48 | 67.1 | 81.8 | waiting likely costs ~15 pts at WR (best option now 82, ~67 by your next turn) · 48% chanc |
| Trey McBride | TE | 77.9 | 0.95 | 0.95 | 76.6 | 77.9 | waiting likely costs ~1 pts at TE (best option now 78, ~77 by your next turn) · 95% chance |
| Josh Allen | QB | 47.0 | 0.81 | 0.81 | 43.9 | 47.0 | waiting likely costs ~3 pts at QB (best option now 47, ~44 by your next turn) · 80% chance |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |
| De'Von Achane | RB | 73.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.9 | 3.1 | 6 |
| RB | 154.2 | 124.7 | 29.5 | 24 |
| WR | 81.8 | 67.1 | 14.7 | 23 |
| TE | 77.9 | 76.6 | 1.3 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 124.9 | 29.4 | 53 |

### Pick 15 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 18 points at RB, with a 47% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 853 ms, ranker engine, plan call 8, plan age 1186 ms, at 22:09:42 PT.
- Engine's reason: waiting likely costs ~18 pts at RB (best option now 73, ~55 by your next turn) · 47% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 10 teams picking bef
- Top projection available: Josh Allen -> took it: False.
- Passed on: Trey McBride (TE, s=0.575, e=62.5); Justin Jefferson (WR, s=0.585, e=50.4); Josh Allen (QB, s=0.474, e=38.4).
- Plan call 8 @pick 15: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 14 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.47 | 0.47 | 55.1 | 73.4 | waiting likely costs ~18 pts at RB (best option now 73, ~55 by your next turn) · 47% chanc |
| Trey McBride | TE | 77.9 | 0.57 | 0.57 | 62.5 | 77.9 | waiting likely costs ~15 pts at TE (best option now 78, ~62 by your next turn) · 57% chanc |
| Justin Jefferson | WR | 53.9 | 0.58 | 0.58 | 50.4 | 53.9 | waiting likely costs ~3 pts at WR (best option now 54, ~50 by your next turn) · 58% chance |
| Josh Allen | QB | 47.0 | 0.47 | 0.47 | 38.4 | 47.0 | waiting likely costs ~9 pts at QB (best option now 47, ~38 by your next turn) · 47% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake London | WR | 51.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.4 | 8.6 | 9 |
| RB | 73.4 | 55.1 | 18.3 | 18 |
| WR | 53.9 | 50.4 | 3.5 | 24 |
| TE | 77.9 | 62.5 | 15.4 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 55.6 | 17.8 | 50 |

### Pick 26 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 20 points at TE, with a 63% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 419 ms, ranker engine, plan call 17, plan age 731 ms, at 22:11:22 PT.
- Engine's reason: waiting likely costs ~20 pts at TE (best option now 78, ~58 by your next turn) · 63% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 8 teams
- Top projection available: Josh Allen -> took it: False.
- Passed on: Chris Olave (WR, s=0.512, e=37.3); Josh Allen (QB, s=0.778, e=43.2); Kyren Williams (RB, s=None, e=None).
- Plan call 17 @pick 26: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 25 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.63 | 0.63 | 57.6 | 77.9 | waiting likely costs ~20 pts at TE (best option now 78, ~58 by your next turn) · 63% chanc |
| Chris Olave | WR | 40.1 | 0.51 | 0.51 | 37.3 | 40.1 | waiting likely costs ~3 pts at WR (best option now 40, ~37 by your next turn) · 51% chance |
| Josh Allen | QB | 47.0 | 0.78 | 0.78 | 43.2 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 78% chance |
| Kyren Williams | RB | 40.5 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.2 | 3.8 | 10 |
| RB | 40.5 | 33.3 | 7.2 | 14 |
| WR | 40.1 | 37.3 | 2.8 | 24 |
| TE | 77.9 | 57.6 | 20.3 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 37.9 | 2.7 | 46 |

### Pick 35 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 2 points at WR, with a 61% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1303 ms, ranker engine, plan call 24, plan age 1633 ms, at 22:12:34 PT.
- Engine's reason: waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 61% chance he's still there at your next pick · fills your open WR slot · 10 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Cam Skattebo (RB, s=0.458, e=17.2); Drake Maye (QB, s=0.613, e=25.9); Zay Flowers (WR, s=None, e=None).
- Plan call 24 @pick 35: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 34 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.61 | 0.61 | 21.9 | 23.9 | waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 61% chance |
| Cam Skattebo | RB | 25.8 | 0.46 | 0.46 | 17.2 | 25.8 | waiting likely costs ~9 pts at your FLEX spot (best option now 26, ~17 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.61 | 0.61 | 25.9 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 61% chance |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.9 | 5.2 | 10 |
| RB | 25.8 | 17.1 | 8.7 | 16 |
| WR | 23.9 | 21.9 | 2.0 | 20 |
| TE | 23.8 | 22.6 | 1.2 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 25.84223678225652 | 17.2 | 8.7 | 44 |

### Pick 46 (round 5): Davante Adams (WR)

- In plain English: Took Davante Adams (WR) because waiting would likely cost about 4 points at WR, with a 62% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1455 ms, ranker engine, plan call 29, plan age 4470 ms, at 22:13:30 PT.
- Engine's reason: waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 62% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair wi
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.685, e=26.8); Jaylen Warren (RB, s=0.952, e=9.2); Jalen Hurts (QB, s=None, e=None).
- Plan call 29 @pick 46: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 45 drafted / 4 mine.
- Engine's first choice was **Davante Adams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Davante Adams | WR | 13.1 | 0.62 | 0.62 | 8.8 | 13.1 | waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 62% chance  |
| Drake Maye | QB | 31.1 | 0.69 | 0.69 | 26.8 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 68% chance |
| Jaylen Warren | RB | 9.3 | 0.95 | 0.95 | 9.2 | 9.3 | safe to wait on your FLEX spot · 95% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.8 | 4.3 | 13 |
| RB | 9.3 | 9.2 | 0.1 | 15 |
| WR | 13.1 | 8.8 | 4.3 | 19 |
| TE | 23.8 | 22.6 | 1.2 | 10 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 44 |

### Pick 55 (round 6): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 5 points at QB, with a 63% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 385 ms, ranker engine, plan call 37, plan age 701 ms, at 22:15:09 PT.
- Engine's reason: waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance he's still there at your next pick · fills your open QB slot · 8 teams picking before you still need a QB · 8 picks past his usua
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.801, e=8.8); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 37 @pick 55: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 54 drafted / 5 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.63 | 0.63 | 25.7 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance |
| Jaylen Warren | RB | 9.3 | 0.80 | 0.80 | 8.8 | 9.3 | safe to wait on your FLEX spot · 80% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.7 | 5.4 | 14 |
| RB | 9.3 | 8.8 | 0.5 | 17 |
| WR | 0.0 | -0.2 | 0.2 | 18 |
| TE | 21.1 | 19.9 | 1.2 | 10 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.8 | 0.5 | 45 |

### Pick 66 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 3 points at your FLEX spot, with a 67% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose. Before this landed the driver skipped: Jaylen Warren:action-timeout.
- Driver: via **click**, verified store, - ms, ranker engine, plan call 45, plan age 6774 ms, at 22:16:45 PT.
- Engine's reason: waiting likely costs ~3 pts at your FLEX spot (best option now 9, ~6 by your next turn) · 67% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Skipped before this landed: Jaylen Warren:action-timeout.
- Passed on: TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None); Rome Odunze (WR, s=None, e=None).
- Plan call 45 @pick 66: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 8], state store with 65 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.67 | 0.67 | 6.5 | 9.3 | waiting likely costs ~3 pts at your FLEX spot (best option now 9, ~6 by your next turn) ·  |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.6 | 1.1 | 20 |
| RB | 9.3 | 6.5 | 2.8 | 23 |
| WR | 0.0 | -0.5 | 0.5 | 26 |
| TE | 21.1 | 19.8 | 1.3 | 13 |
| K | 13.5 | 13.4 | 0.1 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 6.5 | 2.9 | 62 |

### Pick 75 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 96 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 703 ms, ranker engine, plan call 51, plan age 1028 ms, at 22:18:00 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Rome Odunze (WR, s=0.756, e=-2.9); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 51 @pick 75: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 74 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.68 | 0.68 | -5.5 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacob |
| Rome Odunze | WR | -0.7 | 0.76 | 0.76 | -2.9 | -0.7 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.3/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.8 | 1.0 | 19 |
| RB | -5.4 | -5.5 | 0.1 | 33 |
| WR | -0.7 | -2.9 | 2.2 | 38 |
| TE | 19.8 | 15.6 | 4.2 | 20 |
| K | 13.5 | 13.3 | 0.2 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 8 |

### Pick 86 (round 9): RJ Harvey (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    22:18:46 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:03 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:14 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:14 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (46s)
    22:19:17 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:17 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (49s)
    22:19:20 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:20 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (52s)
    22:19:20 PT LOCAL ranking: plan gate failed 3x (plan is for pick 80, header says 86; plan stale (52s)) -> dropping the plan for this turn
    22:19:39 PT ON CLOCK retry -> {"err":"no-verified-pick","attempted":["Bijan Robinson:action-timeout","Bijan Robinson:norow->gone","Jaxon Smith-Njigba:action-timeout","Jaxon Smith-Njigba:norow->gone"]}
    22:19:43 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:43 PT GATE FAILED -> not clicking: no plan
- No plan call at this pick; the last plan before it was call 54 @pick 80:
- Plan call 54 @pick 80: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 79 drafted / 8 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.93 | 0.93 | -5.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1 |
| DK Metcalf | WR | -9.2 | 0.74 | 0.74 | -9.5 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.6 | 0.2 | 17 |
| RB | -5.4 | -5.5 | 0.1 | 31 |
| WR | -9.2 | -9.5 | 0.3 | 39 |
| TE | 19.8 | 16.9 | 2.9 | 20 |
| K | 13.5 | 13.3 | 0.2 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 9 |

### Pick 95 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 550 ms, ranker engine, plan call 4, plan age 879 ms, at 22:20:59 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.811, e=11.5); Kenny Gainwell (RB, s=0.916, e=-7.9); Matthew Stafford (QB, s=None, e=None).
- Plan call 4 @pick 6: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 5 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.56 | 0.56 | 124.7 | 154.2 | waiting likely costs ~30 pts at RB (best option now 154, ~125 by your next turn) · 56% cha |
| Amon-Ra St. Brown | WR | 81.8 | 0.48 | 0.48 | 67.1 | 81.8 | waiting likely costs ~15 pts at WR (best option now 82, ~67 by your next turn) · 48% chanc |
| Trey McBride | TE | 77.9 | 0.95 | 0.95 | 76.6 | 77.9 | waiting likely costs ~1 pts at TE (best option now 78, ~77 by your next turn) · 95% chance |
| Josh Allen | QB | 47.0 | 0.81 | 0.81 | 43.9 | 47.0 | waiting likely costs ~3 pts at QB (best option now 47, ~44 by your next turn) · 80% chance |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |
| De'Von Achane | RB | 73.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.9 | 3.1 | 6 |
| RB | 154.2 | 124.7 | 29.5 | 24 |
| WR | 81.8 | 67.1 | 14.7 | 23 |
| TE | 77.9 | 76.6 | 1.3 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 124.9 | 29.4 | 53 |

### Pick 106 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points. The top raw projection available was Matthew Stafford; the engine passed on him on purpose.
- Driver: via **action**, verified store, 398 ms, ranker engine, plan call 9, plan age 714 ms, at 22:21:57 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Matthew Stafford -> took it: False.
- Plan rows the page dropped: Michael Pittman Jr. (gone).
- Passed on: Kenny Gainwell (RB, s=0.921, e=-7.8); Matthew Stafford (QB, s=None, e=None).
- Plan call 9 @pick 16: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 15 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.54 | 0.54 | 60.2 | 77.9 | waiting likely costs ~18 pts at TE (best option now 78, ~60 by your next turn) · 54% chanc |
| Justin Jefferson | WR | 53.9 | 0.55 | 0.55 | 49.9 | 53.9 | waiting likely costs ~4 pts at WR (best option now 54, ~50 by your next turn) · 55% chance |
| Josh Allen | QB | 47.0 | 0.49 | 0.49 | 38.6 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 49% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake London | WR | 51.0 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.6 | 8.4 | 9 |
| RB | 40.5 | 38.6 | 1.9 | 17 |
| WR | 53.9 | 49.9 | 4.0 | 24 |
| TE | 77.9 | 60.2 | 17.7 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 39.8 | 0.8 | 49 |

### Pick 115 (round 12): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 2 points. The top raw projection available was Matthew Stafford; the engine passed on him on purpose.
- Driver: via **action**, verified store, 444 ms, ranker engine, plan call 14, plan age 776 ms, at 22:23:01 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 2 pts
- Top projection available: Matthew Stafford -> took it: False.
- Plan rows the page dropped: Michael Pittman Jr. (gone).
- Plan call 14 @pick 24: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 23 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.89 | 0.89 | 71.7 | 77.9 | waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 88% chance |
| Chris Olave | WR | 40.1 | 0.88 | 0.88 | 39.6 | 40.1 | safe to wait on WR · 88% chance he's still there at your next pick · fills your open WR sl |
| Josh Allen | QB | 47.0 | 0.91 | 0.91 | 45.5 | 47.0 | waiting likely costs ~1 pts at QB (best option now 47, ~46 by your next turn) · 91% chance |
| Kyren Williams | RB | 40.5 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 45.5 | 1.5 | 10 |
| RB | 40.5 | 39.3 | 1.2 | 16 |
| WR | 40.1 | 39.6 | 0.5 | 23 |
| TE | 77.9 | 71.7 | 6.2 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 40.4 | 0.1 | 47 |

### Pick 126 (round 13): Michael Pittman Jr. (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    22:24:40 PT ON CLOCK retry -> {"err":"no-verified-pick","attempted":["Breece Hall:action-timeout","Breece Hall:norow->gone","Courtland Sutton:action-timeout","Courtland Sutton:norow->gone"]}
    22:24:49 PT ON CLOCK -> turn ended: {"err":"pick-made-by-other-means","attempted":["Bucky Irving:action-timeout","Bucky Irving:norow->gone","Marvin Harrison Jr.:notours(Michael Pittman Jr.)"],"landed":"Michael Pittman Jr."}
    22:24:52 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    22:25:41 PT ON CLOCK -> {"drafted":"Cam Little","pos":"K","vorp":9,"proj":145.5,"why":"safe to wait on K · 71% chance he's still there at your next pick · fills your open K slot · 8 teams picking before you still need a K · 6 picks past his usual draft spot · 
    22:26:26 PT ON CLOCK -> {"drafted":"Kansas City Chiefs","pos":"DEF","vorp":-6,"proj":111,"why":"depth fallback (engine list exhausted)","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projectio
- Plan call 21 @pick 126: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 9], state store with 125 drafted / 12 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.96 | 0.96 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.96 | 0.96 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +7. |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 11 |
| RB | -25.9 | -26.1 | 0.2 | 20 |
| WR | -13.3 | -13.6 | 0.3 | 27 |
| TE | 0.5 | 0.4 | 0.1 | 14 |
| K | 10.5 | 10.1 | 0.4 | 15 |
| DEF | 10.0 | 9.4 | 0.6 | 9 |

### Pick 135 (round 14): Cam Little (K)

- In plain English: Took Cam Little (K): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (71% to survive, but nobody better was worth waiting for). The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 452 ms, ranker engine, plan call 26, plan age 794 ms, at 22:25:41 PT.
- Engine's reason: safe to wait on K · 71% chance he's still there at your next pick · fills your open K slot · 8 teams picking before you still need a K · 6 picks past his usual draft spot · two-pick plan: pair with the ~32-pt RB expected
- Top projection available: Daniel Jones -> took it: False.
- Plan rows the page dropped: Pittsburgh Steelers (gone).
- Passed on: Eddy Pineiro (K, s=None, e=None); Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None).
- Plan call 26 @pick 39: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 38 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.56 | 0.56 | 18.5 | 25.8 | waiting likely costs ~7 pts at your FLEX spot (best option now 26, ~18 by your next turn)  |
| Zay Flowers | WR | 22.0 | 0.69 | 0.69 | 19.7 | 22.0 | waiting likely costs ~2 pts at WR (best option now 22, ~20 by your next turn) · 70% chance |
| Drake Maye | QB | 31.1 | 0.68 | 0.68 | 26.8 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 68% chance |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Tetairoa McMillan | WR | 15.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.8 | 4.3 | 12 |
| RB | 25.8 | 18.5 | 7.3 | 15 |
| WR | 22.0 | 19.7 | 2.3 | 21 |
| TE | 23.8 | 22.9 | 0.9 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 18.5 | 7.3 | 45 |

### Pick 146 (round 15): Chiefs (DEF)

- In plain English: Took Kansas City Chiefs (DEF) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 250 ms, ranker engine, plan call 31, plan age 570 ms, at 22:26:26 PT.
- Engine's reason: depth fallback (engine list exhausted)
- Top projection available: Daniel Jones -> took it: False.
- Plan rows the page dropped: Baltimore Ravens (gone), Green Bay Packers (gone).
- Passed on: Cleveland Browns (DEF, s=None, e=None); Detroit Lions (DEF, s=None, e=None); Dallas Cowboys (DEF, s=None, e=None).
- Plan call 31 @pick 49: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4], state store with 48 drafted / 5 mine.
- Engine's first choice was **Drake Maye** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.76 | 0.76 | 27.8 | 31.1 | waiting likely costs ~3 pts at QB (best option now 31, ~28 by your next turn) · 76% chance |
| Jaylen Warren | RB | 9.3 | 0.95 | 0.95 | 9.2 | 9.3 | safe to wait on your FLEX spot · 95% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 27.8 | 3.3 | 13 |
| RB | 9.3 | 9.2 | 0.1 | 18 |
| WR | 3.0 | 2.0 | 1.0 | 18 |
| TE | 23.8 | 22.6 | 1.2 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 4 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 45 |

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 30-50% | 7 | 47% | 57% |
| 50-70% | 34 | 60% | 32% |
| 70-90% | 55 | 80% | 73% |
| 90-100% | 70 | 95% | 94% |

166 predictions over 71 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-02T22:25:44   WARNING plan #27: dropped 1 feed entries numbered >= header pick 138
    2026-09-02T22:25:56   WARNING plan #28: 1 drafted entries matched no board player: 139 Will Reichard
    2026-09-02T22:26:08   WARNING plan #29: 1 drafted entries matched no board player: 139 Will Reichard
    2026-09-02T22:26:20   WARNING plan #30: 1 drafted entries matched no board player: 139 Will Reichard
    2026-09-02T22:26:26   WARNING plan #31: 1 drafted entries matched no board player: 139 Will Reichard

## Driver log (the lines that matter, Pacific time)

    22:08:33 PT preflight: ok=true pick_path=action my_team=6 plan=plan 25 deep @pick 5 via store call#1
    22:08:34 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    22:09:00 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~30 pts at RB (best option now 154, ~125 by your next turn) · 56% chance he's still there at your next pick · fills yo
    22:09:42 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~18 pts at RB (best option now 73, ~55 by your next turn) · 47% chance he's still there at your next pick · fills your open R
    22:11:22 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~20 pts at TE (best option now 78, ~58 by your next turn) · 63% chance he's still there at your next pick · fills your open TE
    22:12:34 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 61% chance he's still there at your next pick · fills your open WR 
    22:12:36 PT heartbeat: setAwayStatus(false)
    22:13:30 PT ON CLOCK -> {"drafted":"Davante Adams","pos":"WR","vorp":13.1,"proj":155.2,"why":"waiting likely costs ~4 pts at WR (best option now 13, ~9 by your next turn) · 62% chance he's still there at your next pick · fills your open WR 
    22:15:09 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance he's still there at your next pick · fills your open QB sl
    22:16:37 PT heartbeat: setAwayStatus(false)
    22:16:45 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~3 pts at your FLEX spot (best option now 9, ~6 by your next turn) · 67% chance he's still there at your next pick · fills a F
    22:17:22 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    22:18:00 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren","s":0.
    22:18:46 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:03 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:14 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:14 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (46s)
    22:19:17 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:17 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (49s)
    22:19:20 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:20 PT GATE FAILED -> not clicking: plan is for pick 80, header says 86; plan stale (52s)
    22:19:20 PT LOCAL ranking: plan gate failed 3x (plan is for pick 80, header says 86; plan stale (52s)) -> dropping the plan for this turn
    22:19:39 PT ON CLOCK retry -> {"err":"no-verified-pick","attempted":["Bijan Robinson:action-timeout","Bijan Robinson:norow->gone","Jaxon Smith-Njigba:action-timeout","Jaxon Smith-Njigba:norow->gone"]}
    22:19:43 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:43 PT GATE FAILED -> not clicking: no plan
    22:19:45 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    22:19:47 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:19:59 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:20:11 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:20:37 PT heartbeat: setAwayStatus(false)
    22:20:59 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.945,"sr":0.945,"e":-10.8,"top_
    22:21:57 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.927,"sr":0.927,"e":12.2,"top_pr
    22:23:01 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 2 pts","s":0.925,"sr":
    22:24:40 PT ON CLOCK retry -> {"err":"no-verified-pick","attempted":["Breece Hall:action-timeout","Breece Hall:norow->gone","Courtland Sutton:action-timeout","Courtland Sutton:norow->gone"]}
    22:24:42 PT heartbeat: setAwayStatus(false)
    22:24:49 PT ON CLOCK -> turn ended: {"err":"pick-made-by-other-means","attempted":["Bucky Irving:action-timeout","Bucky Irving:norow->gone","Marvin Harrison Jr.:notours(Michael Pittman Jr.)"],"landed":"Michael Pittman Jr."}
    22:24:52 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    22:25:41 PT ON CLOCK -> {"drafted":"Cam Little","pos":"K","vorp":9,"proj":145.5,"why":"safe to wait on K · 71% chance he's still there at your next pick · fills your open K slot · 8 teams picking before you still need a K · 6 picks past his
    22:25:44 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 138
    22:25:56 PT BRIDGE WARNING: 1 drafted entries matched no board player: 139 Will Reichard
    22:26:26 PT ON CLOCK -> {"drafted":"Kansas City Chiefs","pos":"DEF","vorp":-6,"proj":111,"why":"depth fallback (engine list exhausted)","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5}
    22:26:29 PT roster full
    22:26:29 PT driver stop
    22:26:29 PT trail: 147 picks, 13 records -> C:\Users\gabje\Desktop\fantasy-football\data\logs\mocks\10531886.json


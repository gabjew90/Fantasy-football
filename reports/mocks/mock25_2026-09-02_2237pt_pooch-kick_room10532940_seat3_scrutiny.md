# Scrutiny: Mock 25 -- Pooch Kick (room 10532940) -- Wednesday 2026-09-02 22:37 PT -- 10 teams, our seat 3

Captured 2026-09-02 22:53:03 PT. Times below are Pacific. 10 teams, our team id 3, draft slot 3. 150 picks in the trail, 76 bridge plan calls, 62 recs events in the room log.

The page was reloaded mid-draft at 2026-09-02 22:42:20 PT; records from before it are merged in.

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

- Our picks: 15; by the driver 14 (action 13, click 1), by Yahoo from the queue / autopick 3: 78 Kenny Gainwell, 83 RJ Harvey, 123 Courtland Sutton.
- Action latency to store confirmation: median 430 ms, min 391, max 2436.
- Heartbeats 3; away flags detected and cleared 0; gate failures 6; local-ranker fallbacks 2; plan refresh failures 13.
- Bridge warnings (0): none.
- Away seats over the room (each change): {} -> {8} -> {8,10} -> {8} -> {2,8} -> {8} -> {5,8} -> {8} -> {2,8} -> {2,6,8} -> {2,5,6,8} -> {2,5,6,8,10} -> {2,5,6,7,8,9,10}.
- Managers away at the end: 2 Kirk, 5 micke, 6 Nick, 7 Lucas, 8 Tremayn, 9 NoKaOi, 10 Xay.

## Our picks, one block each

### Pick 3 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 56 points at RB, with a 31% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 399 ms, ranker engine, plan call 6, plan age 719 ms, at 22:38:19 PT.
- Engine's reason: waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 14 tea
- Top projection available: Josh Allen -> took it: False.
- Passed on: Ja'Marr Chase (WR, s=0.529, e=100.8); Trey McBride (TE, s=0.864, e=73.8); Josh Allen (QB, s=0.638, e=41.2).
- Plan call 6 @pick 3: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 2 drafted / 0 mine.
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

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 6 points at TE, with a 79% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 396 ms, ranker engine, plan call 17, plan age 712 ms, at 22:40:42 PT.
- Engine's reason: waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 79% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 4 teams 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=0.673, e=48.4); Kyren Williams (RB, s=0.765, e=39.5); Josh Allen (QB, s=0.734, e=42.8).
- Plan call 17 @pick 18: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8], state store with 17 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.79 | 0.79 | 72.1 | 77.9 | waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 79% chance |
| Drake London | WR | 51.0 | 0.67 | 0.67 | 48.4 | 51.0 | waiting likely costs ~3 pts at WR (best option now 51, ~48 by your next turn) · 67% chance |
| Kyren Williams | RB | 40.5 | 0.77 | 0.77 | 39.5 | 40.5 | safe to wait on RB · 76% chance he's still there at your next pick · fills your open RB sl |
| Josh Allen | QB | 47.0 | 0.73 | 0.73 | 42.8 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 73% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.8 | 4.2 | 9 |
| RB | 40.5 | 39.5 | 1.0 | 17 |
| WR | 51.0 | 48.4 | 2.6 | 23 |
| TE | 77.9 | 72.1 | 5.8 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 40.2 | 0.3 | 48 |

### Pick 23 (round 3): Chris Olave (WR)

- In plain English: Took Chris Olave (WR) because waiting would likely cost about 4 points at WR, with a 29% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 458 ms, ranker engine, plan call 23, plan age 770 ms, at 22:41:39 PT.
- Engine's reason: waiting likely costs ~4 pts at WR (best option now 41, ~38 by your next turn) · 29% chance he's still there at your next pick · fills your open WR slot · 14 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Kyren Williams (RB, s=0.362, e=33.3); Drake Maye (QB, s=0.817, e=28.7); Nico Collins (WR, s=None, e=None).
- Plan call 23 @pick 23: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8], state store with 22 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.29 | 0.29 | 37.6 | 41.4 | waiting likely costs ~4 pts at WR (best option now 41, ~38 by your next turn) · 29% chance |
| Kyren Williams | RB | 40.5 | 0.36 | 0.36 | 33.3 | 40.5 | waiting likely costs ~7 pts at RB (best option now 40, ~33 by your next turn) · 36% chance |
| Drake Maye | QB | 31.1 | 0.82 | 0.82 | 28.7 | 31.1 | waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 82% chance |
| Nico Collins | WR | 41.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 28.7 | 2.4 | 8 |
| RB | 40.5 | 33.3 | 7.2 | 17 |
| WR | 41.4 | 37.6 | 3.8 | 24 |
| TE | 58.1 | 45.5 | 12.6 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 33.5 | 7.0 | 48 |

### Pick 38 (round 4): Rashee Rice (WR)

- In plain English: Took Rashee Rice (WR) because waiting would likely cost about 3 points at WR, with a 74% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 456 ms, ranker engine, plan call 35, plan age 769 ms, at 22:43:39 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 34, ~31 by your next turn) · 74% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Cam Skattebo (RB, s=0.737, e=24); Drake Maye (QB, s=0.912, e=29.9); Garrett Wilson (WR, s=None, e=None).
- Plan call 35 @pick 38: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 8], state store with 37 drafted / 3 mine.
- Engine's first choice was **Rashee Rice** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rashee Rice | WR | 34.1 | 0.74 | 0.74 | 31.3 | 34.1 | waiting likely costs ~3 pts at WR (best option now 34, ~31 by your next turn) · 74% chance |
| Cam Skattebo | RB | 25.8 | 0.74 | 0.74 | 24.0 | 25.8 | waiting likely costs ~2 pts at RB (best option now 26, ~24 by your next turn) · 74% chance |
| Drake Maye | QB | 31.1 | 0.91 | 0.91 | 29.9 | 31.1 | waiting likely costs ~1 pts at QB (best option now 31, ~30 by your next turn) · 91% chance |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 29.9 | 1.2 | 10 |
| RB | 25.8 | 24.0 | 1.8 | 17 |
| WR | 34.1 | 31.3 | 2.8 | 20 |
| TE | 23.8 | 23.3 | 0.5 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 24.3 | 1.5 | 45 |

### Pick 43 (round 5): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB) because waiting would likely cost about 5 points at your FLEX spot, with a 56% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 442 ms, ranker engine, plan call 39, plan age 754 ms, at 22:44:38 PT.
- Engine's reason: waiting likely costs ~5 pts at your FLEX spot (best option now 26, ~21 by your next turn) · 56% chance he's still there at your next pick · fills your open RB slot · only 2 RBs left at this level · 14 teams picking befor
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.36, e=21.8); Garrett Wilson (WR, s=None, e=None); D'Andre Swift (RB, s=None, e=None).
- Plan call 39 @pick 43: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8], state store with 42 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.56 | 0.56 | 21.0 | 25.8 | waiting likely costs ~5 pts at your FLEX spot (best option now 26, ~21 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.36 | 0.36 | 21.8 | 31.1 | waiting likely costs ~9 pts at QB (best option now 31, ~22 by your next turn) · 36% chance |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 21.8 | 9.3 | 14 |
| RB | 25.8 | 21.0 | 4.8 | 18 |
| WR | 23.9 | 16.2 | 7.7 | 18 |
| TE | 21.1 | 20.8 | 0.3 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 21.1 | 4.8 | 43 |

### Pick 58 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (86% to survive, but nobody better was worth waiting for). The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 412 ms, ranker engine, plan call 47, plan age 728 ms, at 22:46:17 PT.
- Engine's reason: safe to wait on QB · 86% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair with the ~36-pt WR expected at your next turn
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.925, e=9.1); Trevor Lawrence (QB, s=None, e=None); Davante Adams (WR, s=None, e=None).
- Plan call 47 @pick 58: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 8, 10], state store with 57 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.86 | 0.86 | 17.7 | 18.0 | safe to wait on QB · 86% chance he's still there at your next pick · fills your open QB sl |
| Jaylen Warren | RB | 9.3 | 0.93 | 0.93 | 9.1 | 9.3 | safe to wait on your FLEX spot · 92% chance he's still there at your next pick · fills a F |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.7 | 0.3 | 16 |
| RB | 9.3 | 9.1 | 0.2 | 16 |
| WR | 13.1 | 9.4 | 3.7 | 20 |
| TE | 21.1 | 20.8 | 0.3 | 10 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 46 |

### Pick 63 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 62% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 430 ms, ranker engine, plan call 50, plan age 749 ms, at 22:46:39 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 62% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Christian Watson (WR, s=None, e=None).
- Plan call 50 @pick 63: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 8, 10], state store with 62 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.62 | 0.62 | 7.5 | 9.3 | waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) ·  |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.3 | 2.4 | 17 |
| RB | 9.3 | 7.5 | 1.8 | 19 |
| WR | -0.8 | -3.1 | 2.3 | 20 |
| TE | 21.1 | 15.5 | 5.6 | 10 |
| K | 13.5 | 13.3 | 0.2 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 7.5 | 1.8 | 49 |

### Pick 78 (round 8): Kenny Gainwell (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    22:47:21 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:34 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:47 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:59 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:10 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:10 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (63s)
    22:48:14 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:14 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (66s)
    22:48:17 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:17 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (70s)
    22:48:17 PT LOCAL ranking: plan gate failed 3x (plan is for pick 67, header says 78; plan stale (70s)) -> dropping the plan for this turn
    22:48:22 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"","s":0,"sr":null,"e":null,"top_proj_available":{"n":"Trevor Lawrence","p":"QB","proj":289.3,"vorp":15.7},"took_top_projection":false,"passed_on":[{"n":"Jaxon Smith-Nj
- No plan call at this pick; the last plan before it was call 53 @pick 67:
- Plan call 53 @pick 67: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 8, 10], state store with 66 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | - | - | 4.9 | 7.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacob |
| Christian Watson | WR | -0.8 | 0.66 | 0.66 | -3.7 | -0.8 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.3/wk over the wire (Rashod Bate |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.8 | 1.9 | 20 |
| RB | 7.2 | 4.9 | 2.3 | 24 |
| WR | -0.8 | -3.7 | 2.9 | 28 |
| TE | 21.1 | 15.4 | 5.7 | 18 |
| K | 13.5 | 13.3 | 0.2 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 83 (round 9): RJ Harvey (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    22:38:19 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills your open RB slot · TAK
    22:40:42 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 79% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE
    22:41:39 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~4 pts at WR (best option now 41, ~38 by your next turn) · 29% chance he's still there at your next pick · fills your open WR slot · 14 teams picki
    22:43:39 PT ON CLOCK -> {"drafted":"Rashee Rice","pos":"WR","vorp":34.1,"proj":176.3,"why":"waiting likely costs ~3 pts at WR (best option now 34, ~31 by your next turn) · 74% chance he's still there at your next pick · fills your open WR slot · 4 teams pickin
    22:44:38 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 26, ~21 by your next turn) · 56% chance he's still there at your next pick · fills your open RB slot · onl
    22:46:17 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 86% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair with the ~
    22:46:39 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 62% chance he's still there at your next pick · fills a FLEX slot","s":0.617,
    22:47:21 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:34 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:47 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:59 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:10 PT PLAN bridge unreachable: TypeError: Failed to fetch
- No plan call at this pick; the last plan before it was call 53 @pick 67:
- Plan call 53 @pick 67: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 8, 10], state store with 66 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | - | - | 4.9 | 7.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacob |
| Christian Watson | WR | -0.8 | 0.66 | 0.66 | -3.7 | -0.8 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.3/wk over the wire (Rashod Bate |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.8 | 1.9 | 20 |
| RB | 7.2 | 4.9 | 2.3 | 24 |
| WR | -0.8 | -3.7 | 2.9 | 28 |
| TE | 21.1 | 15.4 | 5.7 | 18 |
| K | 13.5 | 13.3 | 0.2 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 98 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 448 ms, ranker engine, plan call 5, plan age 769 ms, at 22:50:02 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.893, e=11.6); Tyrone Tracy Jr. (RB, s=0.985, e=-26); Brock Purdy (QB, s=None, e=None).
- Plan call 5 @pick 2: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 1 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.88 | 0.88 | 150.1 | 154.2 | waiting likely costs ~4 pts at your FLEX spot (best option now 154, ~150 by your next turn |
| Ja'Marr Chase | WR | 115.3 | 0.89 | 0.89 | 113.6 | 115.3 | waiting likely costs ~2 pts at WR (best option now 115, ~114 by your next turn) · 89% chan |
| Trey McBride | TE | 77.9 | 1.00 | 1.00 | 77.9 | 77.9 | safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE s |
| Josh Allen | QB | 47.0 | 0.99 | 0.99 | 46.9 | 47.0 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Bijan Robinson | RB | 119.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 46.9 | 0.1 | 6 |
| RB | 154.2 | 150.1 | 4.1 | 23 |
| WR | 115.3 | 113.6 | 1.7 | 25 |
| TE | 77.9 | 77.9 | 0.0 | 5 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 150.1 | 4.1 | 53 |

### Pick 103 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points. The top raw projection available was Jaxson Dart; the engine passed on him on purpose.
- Driver: via **action**, verified store, 415 ms, ranker engine, plan call 8, plan age 733 ms, at 22:50:22 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Jaxson Dart -> took it: False.
- Passed on: Tyrone Tracy Jr. (RB, s=0.953, e=-26.2); Courtland Sutton (WR, s=0.828, e=-11.6); Jaxson Dart (QB, s=None, e=None).
- Plan call 8 @pick 4: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 3 drafted / 1 mine.
- Engine's first choice was **Ja'Marr Chase** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Ja'Marr Chase | WR | 115.3 | 0.47 | 0.47 | 97.3 | 115.3 | waiting likely costs ~18 pts at WR (best option now 115, ~97 by your next turn) · 47% chan |
| Jonathan Taylor | RB | 104.3 | 0.25 | 0.25 | 70.2 | 104.3 | waiting likely costs ~34 pts at RB (best option now 104, ~70 by your next turn) · 25% chan |
| Trey McBride | TE | 77.9 | 0.86 | 0.86 | 73.5 | 77.9 | waiting likely costs ~4 pts at TE (best option now 78, ~74 by your next turn) · 86% chance |
| Josh Allen | QB | 47.0 | 0.59 | 0.59 | 40.4 | 47.0 | waiting likely costs ~7 pts at QB (best option now 47, ~40 by your next turn) · 59% chance |
| Puka Nacua | WR | 99.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxon Smith-Njigba | WR | 89.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 40.4 | 6.6 | 6 |
| RB | 104.3 | 70.2 | 34.1 | 22 |
| WR | 115.3 | 97.3 | 18.0 | 25 |
| TE | 77.9 | 73.5 | 4.4 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 104.29215856190694 | 89.8 | 14.5 | 53 |

### Pick 118 (round 12): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose. Before this landed the driver skipped: Tyrone Tracy Jr.:action-timeout, Tyrone Tracy Jr.:norow->gone, Courtland Sutton:action-timeout.
- Driver: via **click**, verified roster-count, - ms, ranker engine, plan call 16, plan age 10829 ms, at 22:51:53 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Skipped before this landed: Tyrone Tracy Jr.:action-timeout, Tyrone Tracy Jr.:norow->gone, Courtland Sutton:action-timeout.
- Passed on: Tyrone Tracy Jr. (RB, s=0.988, e=-25.9); Jakobi Meyers (WR, s=None, e=None); Aaron Jones Sr. (RB, s=None, e=None).
- Plan call 16 @pick 17: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8], state store with 16 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.96 | 0.96 | 77.2 | 77.9 | safe to wait on TE · 96% chance he's still there at your next pick · fills your open TE sl |
| Drake London | WR | 51.0 | 0.93 | 0.93 | 50.5 | 51.0 | safe to wait on WR · 93% chance he's still there at your next pick · fills your open WR sl |
| Derrick Henry | RB | 50.4 | 0.87 | 0.87 | 49.1 | 50.4 | waiting likely costs ~1 pts at your FLEX spot (best option now 50, ~49 by your next turn)  |
| Josh Allen | QB | 47.0 | 0.91 | 0.91 | 45.5 | 47.0 | waiting likely costs ~1 pts at QB (best option now 47, ~46 by your next turn) · 91% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 45.5 | 1.5 | 9 |
| RB | 50.4 | 49.1 | 1.3 | 18 |
| WR | 51.0 | 50.5 | 0.5 | 23 |
| TE | 77.9 | 77.2 | 0.7 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 50.44274023536681 | 49.1 | 1.3 | 49 |

### Pick 123 (round 13): Courtland Sutton (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    22:52:24 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 81% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · two-pick plan: pair w
    22:52:53 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection":false,"passed_on":
- No plan call at this pick; the last plan before it was call 16 @pick 118:
- Plan call 16 @pick 118: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5, 6, 7, 8, 9, 10], state store+dom-roster with 117 drafted / 11 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 0.99 | 0.99 | -25.9 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10 |
| Courtland Sutton | WR | -11.1 | 0.99 | 0.99 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 11 |
| RB | -25.9 | -25.9 | 0.0 | 22 |
| WR | -11.1 | -11.2 | 0.1 | 27 |
| TE | -2.4 | -2.5 | 0.1 | 13 |
| K | 13.5 | 13.5 | 0.0 | 16 |
| DEF | 18.0 | 17.9 | 0.1 | 14 |

### Pick 138 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (81% to survive, but nobody better was worth waiting for). The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 2436 ms, ranker engine, plan call 19, plan age 2754 ms, at 22:52:24 PT.
- Engine's reason: safe to wait on DEF · 81% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · two-pick plan: pair with the ~32-pt RB expected at your next turn
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Eddy Pineiro (K, s=0.932, e=7.4); Minnesota Vikings (DEF, s=None, e=None); Jason Myers (K, s=None, e=None).
- Plan call 19 @pick 19: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8, 10], state store with 18 drafted / 2 mine.
- Engine's first choice was **Drake London** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake London | WR | 51.0 | 0.70 | 0.70 | 48.6 | 51.0 | waiting likely costs ~2 pts at WR (best option now 51, ~49 by your next turn) · 70% chance |
| Kyren Williams | RB | 40.5 | 0.70 | 0.70 | 39.3 | 40.5 | waiting likely costs ~1 pts at RB (best option now 40, ~39 by your next turn) · 70% chance |
| Josh Allen | QB | 47.0 | 0.69 | 0.69 | 42.0 | 47.0 | waiting likely costs ~5 pts at QB (best option now 47, ~42 by your next turn) · 69% chance |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Nico Collins | WR | 41.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.0 | 5.0 | 9 |
| RB | 40.5 | 39.3 | 1.2 | 18 |
| WR | 51.0 | 48.6 | 2.4 | 25 |
| TE | 58.1 | 49.0 | 9.1 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 39.4 | 1.2 | 50 |

### Pick 143 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 392 ms, ranker engine, plan call 23, plan age 717 ms, at 22:52:53 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None).
- Plan call 23 @pick 23: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [8], state store with 22 drafted / 2 mine.
- Engine's first choice was **Chris Olave** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Chris Olave | WR | 40.1 | 0.29 | 0.29 | 37.6 | 41.4 | waiting likely costs ~4 pts at WR (best option now 41, ~38 by your next turn) · 29% chance |
| Kyren Williams | RB | 40.5 | 0.36 | 0.36 | 33.3 | 40.5 | waiting likely costs ~7 pts at RB (best option now 40, ~33 by your next turn) · 36% chance |
| Drake Maye | QB | 31.1 | 0.82 | 0.82 | 28.7 | 31.1 | waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 82% chance |
| Nico Collins | WR | 41.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 28.7 | 2.4 | 8 |
| RB | 40.5 | 33.3 | 7.2 | 17 |
| WR | 41.4 | 37.6 | 3.8 | 24 |
| TE | 58.1 | 45.5 | 12.6 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 33.5 | 7.0 | 48 |

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 2 | 27% | 0% |
| 30-50% | 22 | 41% | 0% |
| 50-70% | 28 | 61% | 32% |
| 70-90% | 47 | 82% | 77% |
| 90-100% | 57 | 96% | 93% |

156 predictions over 61 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Driver log (the lines that matter, Pacific time)

    22:37:33 PT preflight: ok=true pick_path=action my_team=3 plan=plan 25 deep @pick 1 via store call#1
    22:37:34 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    22:38:19 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills you
    22:40:42 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 79% chance he's still there at your next pick · fills your open TE 
    22:41:34 PT heartbeat: setAwayStatus(false)
    22:41:39 PT ON CLOCK -> {"drafted":"Chris Olave","pos":"WR","vorp":40.1,"proj":182.2,"why":"waiting likely costs ~4 pts at WR (best option now 41, ~38 by your next turn) · 29% chance he's still there at your next pick · fills your open WR s
    22:42:32 PT preflight: ok=true pick_path=action my_team=3 plan=plan 25 deep @pick 31 via store call#28
    22:42:32 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    22:43:39 PT ON CLOCK -> {"drafted":"Rashee Rice","pos":"WR","vorp":34.1,"proj":176.3,"why":"waiting likely costs ~3 pts at WR (best option now 34, ~31 by your next turn) · 74% chance he's still there at your next pick · fills your open WR s
    22:44:38 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 26, ~21 by your next turn) · 56% chance he's still there at your next pick · fills you
    22:46:17 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 86% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick p
    22:46:33 PT heartbeat: setAwayStatus(false)
    22:46:39 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 62% chance he's still there at your next pick · fills a F
    22:47:21 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:34 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:47 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:47:59 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:10 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:10 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (63s)
    22:48:14 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:14 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (66s)
    22:48:17 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:17 PT GATE FAILED -> not clicking: plan is for pick 67, header says 78; plan stale (70s)
    22:48:17 PT LOCAL ranking: plan gate failed 3x (plan is for pick 67, header says 78; plan stale (70s)) -> dropping the plan for this turn
    22:48:22 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"","s":0,"sr":null,"e":null,"top_proj_available":{"n":"Trevor Lawrence","p":"QB","proj":289.3,"vorp":15.7},"took_top_projection":false,"passed_on":[
    22:48:26 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:39 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:46 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:46 PT GATE FAILED -> not clicking: no plan
    22:48:49 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:49 PT GATE FAILED -> not clicking: no plan
    22:48:52 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:48:52 PT GATE FAILED -> not clicking: no plan
    22:48:52 PT LOCAL ranking: plan gate failed 3x (no plan) -> dropping the plan for this turn
    22:48:53 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"","s":3,"sr":null,"e":null,"top_proj_available":{"n":"Trevor Lawrence","p":"QB","proj":289.3,"vorp":15.7},"took_top_projection":false,"passed_on":[{"n
    22:48:57 PT PLAN bridge unreachable: TypeError: Failed to fetch
    22:50:02 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.981,"sr":0.981,"e":-10.6,"top_
    22:50:22 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.812,"sr":0.812,"e":8.3,"top_pro
    22:50:34 PT heartbeat: setAwayStatus(false)
    22:51:53 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.98
    22:52:24 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 81% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · t
    22:52:53 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    22:52:55 PT roster full
    22:52:55 PT driver stop


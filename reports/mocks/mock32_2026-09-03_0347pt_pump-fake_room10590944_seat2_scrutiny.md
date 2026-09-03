# Scrutiny: Mock 32 -- Pump Fake (room 10590944) -- Thursday 2026-09-03 03:47 PT -- 10 teams, our seat 2

Captured 2026-09-03 04:06:09 PT. Times below are Pacific. 10 teams, our team id 2, draft slot 2. 150 picks in the trail, 105 bridge plan calls, 83 recs events in the room log.

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
- Action latency to store confirmation: median 436 ms, min 323, max 621.
- Heartbeats 17; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (1): dropped 1 feed entries numbered >= header pick 137.
- Away seats over the room (each change): {} -> {5} -> {5,10} -> {5,7,10} -> {5,7,8,10} -> {5,6,7,8,10}.
- Managers away at the end: 5 Chuck, 6 Keegan, 7 Jerrico One, 8 Nando, 10 Jose.

## Our picks, one block each

### Pick 2 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 43 points at RB, with a 29% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 370 ms, ranker engine, plan call 278, plan age 687 ms, at 03:48:06 PT.
- Engine's reason: waiting likely costs ~43 pts at RB (best option now 154, ~111 by your next turn) · 29% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 16 te
- Top projection available: Josh Allen -> took it: False.
- Passed on: Ja'Marr Chase (WR, s=0.453, e=96.4); Trey McBride (TE, s=0.816, e=71.7); Josh Allen (QB, s=0.502, e=39).
- Plan call 278 @pick 2: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 1 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.29 | 0.29 | 111.1 | 154.2 | waiting likely costs ~43 pts at RB (best option now 154, ~111 by your next turn) · 29% cha |
| Ja'Marr Chase | WR | 115.3 | 0.45 | 0.45 | 96.4 | 115.3 | waiting likely costs ~19 pts at WR (best option now 115, ~96 by your next turn) · 45% chan |
| Trey McBride | TE | 77.9 | 0.82 | 0.82 | 71.7 | 77.9 | waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 82% chance |
| Josh Allen | QB | 47.0 | 0.50 | 0.50 | 39.0 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 50% chance |
| Bijan Robinson | RB | 119.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 39.0 | 8.0 | 6 |
| RB | 154.2 | 111.1 | 43.1 | 23 |
| WR | 115.3 | 96.4 | 18.9 | 25 |
| TE | 77.9 | 71.7 | 6.2 | 5 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 118.8 | 35.4 | 53 |

### Pick 19 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 6 points at TE, with a 89% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 415 ms, ranker engine, plan call 289, plan age 737 ms, at 03:50:04 PT.
- Engine's reason: waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 89% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 2 teams 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=0.823, e=49.7); Kyren Williams (RB, s=0.886, e=40.1); Josh Allen (QB, s=0.864, e=44.8).
- Plan call 289 @pick 19: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 18 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.89 | 0.89 | 72.1 | 77.9 | waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 89% chance |
| Drake London | WR | 51.0 | 0.82 | 0.82 | 49.7 | 51.0 | waiting likely costs ~1 pts at WR (best option now 51, ~50 by your next turn) · 82% chance |
| Kyren Williams | RB | 40.5 | 0.89 | 0.89 | 40.1 | 40.5 | safe to wait on RB · 89% chance he's still there at your next pick · fills your open RB sl |
| Josh Allen | QB | 47.0 | 0.86 | 0.86 | 44.8 | 47.0 | waiting likely costs ~2 pts at QB (best option now 47, ~45 by your next turn) · 86% chance |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Nico Collins | WR | 41.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 44.8 | 2.2 | 9 |
| RB | 40.5 | 40.1 | 0.4 | 18 |
| WR | 51.0 | 49.7 | 1.3 | 25 |
| TE | 77.9 | 72.1 | 5.8 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 40.5 | 0.1 | 50 |

### Pick 22 (round 3): Drake London (WR)

- In plain English: Took Drake London (WR) because waiting would likely cost about 6 points at WR, with a 48% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 496 ms, ranker engine, plan call 291, plan age 836 ms, at 03:50:14 PT.
- Engine's reason: waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 48% chance he's still there at your next pick · fills your open WR slot · 16 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Javonte Williams (RB, s=0.357, e=29.4); Josh Allen (QB, s=0.582, e=39.2); Nico Collins (WR, s=None, e=None).
- Plan call 291 @pick 22: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 21 drafted / 2 mine.
- Engine's first choice was **Drake London** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake London | WR | 51.0 | 0.48 | 0.48 | 44.8 | 51.0 | waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 48% chance |
| Javonte Williams | RB | 36.9 | 0.36 | 0.36 | 29.4 | 36.9 | waiting likely costs ~8 pts at RB (best option now 37, ~29 by your next turn) · 36% chance |
| Josh Allen | QB | 47.0 | 0.58 | 0.58 | 39.2 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 58% chance |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Nico Collins | WR | 41.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 39.2 | 7.8 | 9 |
| RB | 36.9 | 29.4 | 7.5 | 16 |
| WR | 51.0 | 44.8 | 6.2 | 26 |
| TE | 23.8 | 23.1 | 0.7 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 32.1 | 4.8 | 48 |

### Pick 39 (round 4): Rashee Rice (WR)

- In plain English: Took Rashee Rice (WR) because waiting would likely cost about 2 points at WR, with a 82% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 425 ms, ranker engine, plan call 307, plan age 757 ms, at 03:53:22 PT.
- Engine's reason: waiting likely costs ~2 pts at WR (best option now 34, ~32 by your next turn) · 82% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · 4 picks past his usua
- Top projection available: Drake Maye -> took it: False.
- Passed on: Cam Skattebo (RB, s=0.971, e=25.3); Drake Maye (QB, s=0.902, e=29.8); Garrett Wilson (WR, s=None, e=None).
- Plan call 307 @pick 39: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 38 drafted / 3 mine.
- Engine's first choice was **Rashee Rice** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rashee Rice | WR | 34.1 | 0.82 | 0.82 | 32.2 | 34.1 | waiting likely costs ~2 pts at WR (best option now 34, ~32 by your next turn) · 82% chance |
| Cam Skattebo | RB | 25.8 | 0.97 | 0.97 | 25.3 | 25.8 | safe to wait on RB · 97% chance he's still there at your next pick · fills your open RB sl |
| Drake Maye | QB | 31.1 | 0.90 | 0.90 | 29.8 | 31.1 | waiting likely costs ~1 pts at QB (best option now 31, ~30 by your next turn) · 90% chance |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 29.8 | 1.3 | 12 |
| RB | 25.8 | 25.3 | 0.5 | 16 |
| WR | 34.1 | 32.2 | 1.9 | 21 |
| TE | 23.8 | 23.5 | 0.3 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 25.5 | 0.3 | 45 |

### Pick 42 (round 5): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB) because waiting would likely cost about 12 points at your FLEX spot, with a 27% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 530 ms, ranker engine, plan call 310, plan age 848 ms, at 03:53:43 PT.
- Engine's reason: waiting likely costs ~12 pts at your FLEX spot (best option now 26, ~14 by your next turn) · 27% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 10 teams
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.37, e=21.8); Garrett Wilson (WR, s=None, e=None); Jalen Hurts (QB, s=None, e=None).
- Plan call 310 @pick 42: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5], state store with 41 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.27 | 0.27 | 13.6 | 25.8 | waiting likely costs ~12 pts at your FLEX spot (best option now 26, ~14 by your next turn) |
| Drake Maye | QB | 31.1 | 0.37 | 0.37 | 21.8 | 31.1 | waiting likely costs ~9 pts at QB (best option now 31, ~22 by your next turn) · 37% chance |
| Garrett Wilson | WR | 23.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 21.8 | 9.3 | 13 |
| RB | 25.8 | 13.6 | 12.2 | 17 |
| WR | 23.9 | 15.9 | 8.0 | 20 |
| TE | 21.1 | 20.6 | 0.5 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 13.6 | 12.2 | 44 |

### Pick 59 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (84% to survive, but nobody better was worth waiting for).
- Driver: via **action**, verified store, 477 ms, ranker engine, plan call 327, plan age 810 ms, at 03:56:59 PT.
- Engine's reason: safe to wait on QB · 84% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick plan: pair with the ~36-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.97, e=9.1); Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None).
- Plan call 327 @pick 59: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7, 10], state store with 58 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.84 | 0.84 | 17.6 | 18.0 | safe to wait on QB · 84% chance he's still there at your next pick · fills your open QB sl |
| Jaylen Warren | RB | 9.3 | 0.97 | 0.97 | 9.1 | 9.3 | safe to wait on your FLEX spot · 97% chance he's still there at your next pick · fills a F |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Emeka Egbuka | WR | 8.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.6 | 0.4 | 15 |
| RB | 9.3 | 9.1 | 0.2 | 15 |
| WR | 8.2 | 7.8 | 0.4 | 22 |
| TE | 21.1 | 21.1 | 0.0 | 10 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 47 |

### Pick 62 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 10 points at your FLEX spot, with a 26% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 488 ms, ranker engine, plan call 330, plan age 826 ms, at 03:57:18 PT.
- Engine's reason: waiting likely costs ~10 pts at your FLEX spot (best option now 9, ~-1 by your next turn) · 26% chance he's still there at your next pick · fills a FLEX slot · 6 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Emeka Egbuka (WR, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 330 @pick 62: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7, 10], state store with 61 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.26 | 0.26 | -1.0 | 9.3 | waiting likely costs ~10 pts at your FLEX spot (best option now 9, ~-1 by your next turn)  |
| Emeka Egbuka | WR | 8.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.2 | 1.5 | 15 |
| RB | 9.3 | -1.0 | 10.3 | 17 |
| WR | 8.2 | 3.8 | 4.4 | 23 |
| TE | 21.1 | 17.5 | 3.6 | 10 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | -1.0 | 10.4 | 50 |

### Pick 79 (round 8): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.9 points a week over the waiver wire (Josh Jacobs), worth about 105 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 415 ms, ranker engine, plan call 343, plan age 754 ms, at 03:59:50 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacobs) ≈ 105 pts · HANDCUFF: backs up your Cam Skattebo
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.879, e=-9.3); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 343 @pick 79: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7, 8, 10], state store with 78 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacob |
| DK Metcalf | WR | -9.2 | 0.88 | 0.88 | -9.3 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.6 | 0.1 | 19 |
| RB | -5.4 | -5.4 | 0.0 | 31 |
| WR | -9.2 | -9.3 | 0.1 | 37 |
| TE | 21.1 | 21.0 | 0.1 | 22 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 8 |

### Pick 82 (round 9): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 25 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 509 ms, ranker engine, plan call 346, plan age 838 ms, at 04:00:19 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.151, e=-10.4); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 346 @pick 82: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7, 8, 10], state store with 81 drafted / 8 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.49 | 0.49 | -5.6 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10. |
| DK Metcalf | WR | -9.2 | 0.15 | 0.15 | -10.4 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 11.8 | 3.9 | 19 |
| RB | -5.4 | -5.6 | 0.2 | 29 |
| WR | -9.2 | -10.4 | 1.2 | 37 |
| TE | 21.1 | 18.2 | 2.9 | 22 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 9 |

### Pick 99 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 436 ms, ranker engine, plan call 358, plan age 781 ms, at 04:02:32 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.96, e=12.5); RJ Harvey (RB, s=0.965, e=-5.4); Matthew Stafford (QB, s=None, e=None).
- Plan call 358 @pick 99: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 98 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.99 | 0.99 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.96 | 0.96 | 12.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.96 | 0.96 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.5 | 0.3 | 16 |
| RB | -5.4 | -5.4 | 0.0 | 24 |
| WR | -10.6 | -10.6 | 0.0 | 35 |
| TE | 13.8 | 13.7 | 0.1 | 19 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 10 |

### Pick 102 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 323 ms, ranker engine, plan call 361, plan age 651 ms, at 04:02:50 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.826, e=-6); Courtland Sutton (WR, s=0.774, e=-11.8); Matthew Stafford (QB, s=None, e=None).
- Plan call 361 @pick 102: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 101 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.85 | 0.85 | 11.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.83 | 0.83 | -6.0 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.77 | 0.77 | -11.8 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.5 | 1.3 | 16 |
| RB | -5.4 | -6.0 | 0.6 | 24 |
| WR | -11.1 | -11.8 | 0.7 | 32 |
| TE | 13.8 | 12.4 | 1.4 | 19 |
| K | 12.0 | 11.2 | 0.8 | 13 |
| DEF | 18.0 | 15.2 | 2.8 | 11 |

### Pick 119 (round 12): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +9.1 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 535 ms, ranker engine, plan call 367, plan age 871 ms, at 04:03:52 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.991, e=-11.1); Kenny Gainwell (RB, s=None, e=None); Michael Pittman Jr. (WR, s=None, e=None).
- Plan call 367 @pick 119: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 118 drafted / 11 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.99 | 0.99 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.99 | 0.99 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 11 |
| RB | -5.4 | -5.4 | 0.0 | 21 |
| WR | -11.1 | -11.1 | 0.0 | 28 |
| TE | 10.9 | 10.8 | 0.1 | 16 |
| K | 12.0 | 11.9 | 0.1 | 15 |
| DEF | 14.0 | 13.9 | 0.1 | 11 |

### Pick 122 (round 13): Courtland Sutton (WR)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 325 ms, ranker engine, plan call 370, plan age 658 ms, at 04:04:17 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.933, e=-7.6); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 370 @pick 122: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 121 drafted / 12 mine.
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.96 | 0.96 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | 0.93 | 0.93 | -7.6 | -6.2 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +9. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.1 | 0.2 | 10 |
| RB | -6.2 | -7.6 | 1.4 | 20 |
| WR | -11.1 | -11.2 | 0.1 | 28 |
| TE | 10.9 | 10.4 | 0.5 | 15 |
| K | 12.0 | 9.5 | 2.5 | 15 |
| DEF | 14.0 | 8.8 | 5.2 | 11 |

### Pick 139 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (93% to survive, but nobody better was worth waiting for). The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 337 ms, ranker engine, plan call 377, plan age 685 ms, at 04:05:32 PT.
- Engine's reason: safe to wait on DEF · 93% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · two-pick plan: pair with the ~32-pt RB expected at your next turn
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cam Little (K, s=0.947, e=8.8); Eddy Pineiro (K, s=None, e=None); Tyler Loop (K, s=None, e=None).
- Plan call 377 @pick 139: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 138 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.93 | 0.93 | 5.9 | 6.0 | safe to wait on DEF · 93% chance he's still there at your next pick · fills your open DEF  |
| Cam Little | K | 9.0 | 0.95 | 0.95 | 8.8 | 9.0 | safe to wait on K · 95% chance he's still there at your next pick · fills your open K slot |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| New England Patriots | DEF | 4.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 9 |
| RB | -25.9 | -25.9 | 0.0 | 18 |
| WR | -21.5 | -21.6 | 0.1 | 22 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 9.0 | 8.8 | 0.2 | 14 |
| DEF | 6.0 | 5.9 | 0.1 | 8 |

### Pick 142 (round 15): Cam Little (K)

- In plain English: Took Cam Little (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 621 ms, ranker engine, plan call 379, plan age 947 ms, at 04:05:43 PT.
- Engine's reason: fills your open K slot · bargain: still here 13 picks after he's usually drafted
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Eddy Pineiro (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None).
- Plan call 379 @pick 142: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [5, 6, 7, 8, 10], state store with 141 drafted / 14 mine.
- Engine's first choice was **Cam Little** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Little | K | 9.0 | - | - | - | - | fills your open K slot · bargain: still here 13 picks after he's usually drafted |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 12 | 21% | 8% |
| 30-50% | 29 | 39% | 0% |
| 50-70% | 32 | 59% | 41% |
| 70-90% | 50 | 83% | 82% |
| 90-100% | 74 | 96% | 92% |

197 predictions over 82 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    03:47:41  plan #275 for pick 1: Christian McCaffrey RB 93% “waiting likely costs ~2 pts at your FLEX spo” · Ja'Marr Chase WR 88% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 100% “safe to wait on TE”
    03:47:42  driver started — seat 2, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    03:48:04  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    03:48:05  plan #278 for pick 2: Christian McCaffrey RB 29% “waiting likely costs ~43 pts at RB (best opt” · Ja'Marr Chase WR 45% “waiting likely costs ~19 pts at WR (best opt” · Trey McBride TE 82% “waiting likely costs ~6 pts at TE (best o
    03:48:05  ON THE CLOCK, pick 2 · plan #278 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    03:48:06  PICKED Christian McCaffrey (RB) via action, confirmed in 370 ms — chose Christian McCaffrey (RB): waiting would likely cost about 43 points at RB, 29% to still be there next turn; top projection left was Josh Allen, passed on purp
    03:48:09  plan #279 for pick 3: Bijan Robinson RB 41% “waiting likely costs ~31 pts at RB (best opt” · Ja'Marr Chase WR 43% “waiting likely costs ~21 pts at WR (best opt” · Trey McBride TE 82% “waiting likely costs ~6 pts at TE (best opti”
    03:48:19  pick 3  Bijan Robinson (RB) taken by seat 3 in 13 s — a target is gone (was 41% to survive)
    03:48:20  pick 4  Jonathan Taylor (RB) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone
    03:48:21  plan #280 for pick 5: Ja'Marr Chase WR 49% “waiting likely costs ~17 pts at WR (best opt” · De'Von Achane RB 26% “waiting likely costs ~16 pts at RB (best opt” · Trey McBride TE 82% “waiting likely costs ~6 pts at TE (best opti”
    03:48:21  pick 5  Ja'Marr Chase (WR) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone (was 49% to survive)
    03:48:31  pick 6  Jaxon Smith-Njigba (WR) taken by seat 6 in 10 s — a target is gone
    03:48:34  plan #281 for pick 7: Puka Nacua WR 36% “waiting likely costs ~25 pts at WR (best opt” · De'Von Achane RB 27% “waiting likely costs ~14 pts at RB (best opt” · Trey McBride TE 85% “waiting likely costs ~5 pts at TE (best opti”
    03:48:42  heartbeat sent (Yahoo told we are not idle)
    03:48:52  pick 7  Puka Nacua (WR) taken by seat 7 in 20 s — a target is gone (was 36% to survive)
    03:48:58  plan #283 for pick 8: Amon-Ra St. Brown WR 26% “waiting likely costs ~22 pts at WR (best opt” · De'Von Achane RB 31% “waiting likely costs ~13 pts at RB (best opt” · Trey McBride TE 86% “waiting likely costs ~4 pts at TE (best opt
    03:49:01  pick 8  James Cook III (RB) taken by seat 8 in 9 s — a target is gone
    03:49:06  pick 9  Saquon Barkley (RB) taken by seat 9 in 5 s
    03:49:07  pick 10  Amon-Ra St. Brown (WR) taken by seat 10 in 2 s INSTANTLY (autopick) — a target is gone (was 26% to survive)
    03:49:10  plan #284 for pick 11: De'Von Achane RB 44% “waiting likely costs ~12 pts at RB (best opt” · CeeDee Lamb WR 38% “waiting likely costs ~4 pts at WR (best opti” · Trey McBride TE 85% “waiting likely costs ~4 pts at TE (best opti”
    03:49:12  pick 11  Brock Bowers (TE) taken by seat 10 in 4 s — a target is gone
    03:49:16  pick 12  Omarion Hampton (RB) taken by seat 9 in 4 s
    03:49:20  pick 13  Kenneth Walker III (RB) taken by seat 8 in 5 s
    03:49:22  plan #285 for pick 14: De'Von Achane RB 54% “waiting likely costs ~9 pts at RB (best opti” · CeeDee Lamb WR 50% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 90% “waiting likely costs ~6 pts at TE (best opti”
    03:49:36  pick 14  De'Von Achane (RB) taken by seat 7 in 16 s — a target is gone (was 54% to survive)
    03:49:43  heartbeat sent (Yahoo told we are not idle)
    03:49:47  plan #287 for pick 15: Chase Brown RB 55% “waiting likely costs ~6 pts at RB (best opti” · CeeDee Lamb WR 56% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 90% “waiting likely costs ~6 pts at TE (best opti”
    03:49:49  pick 15  Chase Brown (RB) taken by seat 6 in 13 s — a target is gone (was 55% to survive)
    03:49:49  pick 16  CeeDee Lamb (WR) taken by seat 5 in 0 s — a target is gone (was 56% to survive)
    03:49:57  pick 17  Derrick Henry (RB) taken by seat 4 in 8 s — a target is gone
    03:49:59  plan #288 for pick 18: Justin Jefferson WR 92% “safe to wait on WR” · Trey McBride TE 96% “waiting likely costs ~2 pts at TE (best opti” · Kyren Williams RB 93% “safe to wait on RB”
    03:50:03  pick 18  Justin Jefferson (WR) taken by seat 3 in 5 s — a target is gone (was 92% to survive)
    03:50:03  plan #289 for pick 19: Trey McBride TE 89% “waiting likely costs ~6 pts at TE (best opti” · Drake London WR 82% “waiting likely costs ~1 pts at WR (best opti” · Kyren Williams RB 89% “safe to wait on RB”
    03:50:03  ON THE CLOCK, pick 19 · plan #289 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    03:50:04  PICKED Trey McBride (TE) via action, confirmed in 415 ms — chose Trey McBride (TE): waiting would likely cost about 6 points at TE, 89% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:50:06  plan #290 for pick 20: Drake London WR 79% “waiting likely costs ~2 pts at WR (best opti” · Kyren Williams RB 88% “safe to wait on RB” · Josh Allen QB 88% “waiting likely costs ~2 pts at QB (best opti”
    03:50:11  pick 20  Ashton Jeanty (RB) taken by seat 1 in 7 s
    03:50:12  pick 21  Kyren Williams (RB) taken by seat 1 in 2 s INSTANTLY (autopick) — a target is gone (was 88% to survive)
    03:50:14  plan #291 for pick 22: Drake London WR 48% “waiting likely costs ~6 pts at WR (best opti” · Javonte Williams RB 36% “waiting likely costs ~8 pts at RB (best opti” · Josh Allen QB 58% “waiting likely costs ~8 pts at QB (best opti”
    03:50:14  ON THE CLOCK, pick 22 · plan #291 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    03:50:14  PICKED Drake London (WR) via action, confirmed in 496 ms — chose Drake London (WR): waiting would likely cost about 6 points at WR, 48% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:50:18  plan #292 for pick 23: A.J. Brown WR 31% “waiting likely costs ~6 pts at WR (best opti” · Javonte Williams RB 33% “waiting likely costs ~8 pts at RB (best opti” · Josh Allen QB 53% “waiting likely costs ~9 pts at QB (best opti”
    03:50:22  pick 23  Nico Collins (WR) taken by seat 3 in 8 s — a target is gone
    03:50:24  pick 24  George Pickens (WR) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone
    03:50:25  pick 25  A.J. Brown (WR) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone (was 31% to survive)
    03:50:30  plan #293 for pick 26: Chris Olave WR 31% “waiting likely costs ~9 pts at WR (best opti” · Javonte Williams RB 42% “waiting likely costs ~7 pts at RB (best opti” · Josh Allen QB 65% “waiting likely costs ~6 pts at QB (best opti”
    03:50:46  heartbeat sent (Yahoo told we are not idle)
    03:50:53  pick 26  Jeremiyah Love (RB) taken by seat 6 in 28 s
    03:50:55  plan #295 for pick 27: Chris Olave WR 37% “waiting likely costs ~8 pts at WR (best opti” · Javonte Williams RB 37% “waiting likely costs ~8 pts at RB (best opti” · Josh Allen QB 65% “waiting likely costs ~7 pts at QB (best opti”
    03:51:02  pick 27  Javonte Williams (RB) taken by seat 7 in 10 s — a target is gone (was 37% to survive)
    03:51:08  plan #296 for pick 28: Chris Olave WR 41% “waiting likely costs ~7 pts at WR (best opti” · Travis Etienne Jr. RB 58% “waiting likely costs ~2 pts at RB (best opti” · Josh Allen QB 66% “waiting likely costs ~6 pts at QB (best opti”
    03:51:30  pick 28  Tee Higgins (WR) taken by seat 8 in 27 s
    03:51:32  plan #298 for pick 29: Chris Olave WR 39% “waiting likely costs ~7 pts at WR (best opti” · Travis Etienne Jr. RB 60% “waiting likely costs ~2 pts at RB (best opti” · Josh Allen QB 71% “waiting likely costs ~5 pts at QB (best opti”
    03:51:37  pick 29  Josh Allen (QB) taken by seat 9 in 7 s — a target is gone (was 71% to survive)
    03:51:41  pick 30  Chris Olave (WR) taken by seat 10 in 5 s — a target is gone (was 39% to survive)
    03:51:44  plan #299 for pick 31: Rashee Rice WR 54% “waiting likely costs ~4 pts at WR (best opti” · Travis Etienne Jr. RB 64% “waiting likely costs ~1 pts at RB (best opti” · Drake Maye QB 80% “waiting likely costs ~3 pts at QB (best opti”
    03:51:49  heartbeat sent (Yahoo told we are not idle)
    03:52:11  pick 31  DeVonta Smith (WR) taken by seat 10 in 30 s — a target is gone
    03:52:19  pick 32  Zay Flowers (WR) taken by seat 9 in 7 s — a target is gone
    03:52:21  plan #302 for pick 33: Rashee Rice WR 60% “waiting likely costs ~4 pts at WR (best opti” · Travis Etienne Jr. RB 73% “safe to wait on RB” · Drake Maye QB 82% “waiting likely costs ~2 pts at QB (best opti”
    03:52:23  pick 33  Breece Hall (RB) taken by seat 8 in 5 s
    03:52:34  plan #303 for pick 34: Rashee Rice WR 67% “waiting likely costs ~3 pts at WR (best opti” · Travis Etienne Jr. RB 73% “safe to wait on RB” · Drake Maye QB 86% “waiting likely costs ~2 pts at QB (best opti”
    03:52:49  pick 34  Travis Etienne Jr. (RB) taken by seat 7 in 26 s — a target is gone (was 73% to survive)
    03:52:49  heartbeat sent (Yahoo told we are not idle)
    03:52:59  plan #305 for pick 35: Rashee Rice WR 76% “waiting likely costs ~2 pts at WR (best opti” · Cam Skattebo RB 73% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 89% “waiting likely costs ~1 pts at QB (best opti”
    03:53:11  pick 35  D'Andre Swift (RB) taken by seat 6 in 22 s — a target is gone
    03:53:12  pick 36  Colston Loveland (TE) taken by seat 5 in 1 s INSTANTLY (autopick)
    03:53:12  plan #306 for pick 37: Rashee Rice WR 86% “waiting likely costs ~1 pts at WR (best opti” · Cam Skattebo RB 85% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 93% “safe to wait on QB”
    03:53:16  pick 37  Malik Nabers (WR) taken by seat 4 in 4 s — a target is gone
    03:53:21  pick 38  Jaylen Waddle (WR) taken by seat 3 in 5 s
    03:53:22  plan #307 for pick 39: Rashee Rice WR 82% “waiting likely costs ~2 pts at WR (best opti” · Cam Skattebo RB 97% “safe to wait on RB” · Drake Maye QB 90% “waiting likely costs ~1 pts at QB (best opti”
    03:53:22  ON THE CLOCK, pick 39 · plan #307 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    03:53:22  PICKED Rashee Rice (WR) via action, confirmed in 425 ms — chose Rashee Rice (WR): waiting would likely cost about 2 points at WR, 82% to still be there next turn; top projection left was Drake Maye, passed on purpose
    03:53:25  plan #308 for pick 40: Cam Skattebo RB 97% “safe to wait on your FLEX spot” · Drake Maye QB 89% “waiting likely costs ~1 pts at QB (best opti” · Garrett Wilson WR “depth fallback (engine list exhausted)”
    03:53:33  pick 40  Tetairoa McMillan (WR) taken by seat 1 in 11 s — a target is gone
    03:53:37  plan #309 for pick 41: Cam Skattebo RB 99% “safe to wait on your FLEX spot” · Drake Maye QB 94% “safe to wait on QB” · Garrett Wilson WR “depth fallback (engine list exhausted)”
    03:53:41  pick 41  Tyler Warren (TE) taken by seat 1 in 8 s
    03:53:43  plan #310 for pick 42: Cam Skattebo RB 27% “waiting likely costs ~12 pts at your FLEX sp” · Drake Maye QB 37% “waiting likely costs ~9 pts at QB (best opti” · Garrett Wilson WR “depth fallback (engine list exhausted)”
    03:53:43  ON THE CLOCK, pick 42 · plan #310 (0.0 s old) · lineup needs QB RB FLEX K DEF
    03:53:43  PICKED Cam Skattebo (RB) via action, confirmed in 530 ms — chose Cam Skattebo (RB): waiting would likely cost about 12 points at your FLEX spot, 27% to still be there next turn; top projection left was Drake Maye, passed on purpos
    03:53:46  plan #311 for pick 43: Drake Maye QB 34% “waiting likely costs ~10 pts at QB (best opt” · Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Garrett Wilson WR “depth fallback (engine list exhausted)”
    03:53:50  heartbeat sent (Yahoo told we are not idle)
    03:53:55  pick 43  Garrett Wilson (WR) taken by seat 3 in 12 s — a target is gone
    03:53:59  plan #312 for pick 44: Drake Maye QB 38% “waiting likely costs ~9 pts at QB (best opti” · Jaylen Warren RB 89% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:54:17  pick 44  DJ Moore (WR) taken by seat 4 in 22 s
    03:54:17  pick 45  Lamar Jackson (QB) taken by seat 5 in 0 s INSTANTLY (autopick)
    03:54:24  plan #314 for pick 46: Drake Maye QB 45% “waiting likely costs ~8 pts at QB (best opti” · Jaylen Warren RB 92% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:54:33  pick 46  Jadarian Price (RB) taken by seat 6 in 16 s
    03:54:36  plan #315 for pick 47: Drake Maye QB 52% “waiting likely costs ~7 pts at QB (best opti” · Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:54:51  heartbeat sent (Yahoo told we are not idle)
    03:54:52  pick 47  Ladd McConkey (WR) taken by seat 7 in 19 s — a target is gone
    03:55:00  plan #317 for pick 48: Drake Maye QB 53% “waiting likely costs ~7 pts at QB (best opti” · Jaylen Warren RB 91% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:55:07  pick 48  Davante Adams (WR) taken by seat 8 in 15 s — a target is gone
    03:55:12  plan #318 for pick 49: Drake Maye QB 57% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:55:17  pick 49  Bhayshul Tuten (RB) taken by seat 9 in 10 s
    03:55:24  plan #319 for pick 50: Drake Maye QB 58% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:55:32  pick 50  Bucky Irving (RB) taken by seat 10 in 14 s
    03:55:34  pick 51  Drake Maye (QB) taken by seat 10 in 3 s — a target is gone (was 58% to survive)
    03:55:37  plan #320 for pick 52: Jalen Hurts QB 54% “waiting likely costs ~1 pts at QB (best opti” · Jaylen Warren RB 94% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:55:44  pick 52  Rome Odunze (WR) taken by seat 9 in 9 s
    03:55:46  pick 53  Joe Burrow (QB) taken by seat 8 in 2 s INSTANTLY (autopick)
    03:55:49  plan #321 for pick 54: Jalen Hurts QB 57% “waiting likely costs ~1 pts at QB (best opti” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:55:51  heartbeat sent (Yahoo told we are not idle)
    03:56:15  pick 54  Sam LaPorta (TE) taken by seat 7 in 29 s
    03:56:26  plan #324 for pick 55: Jalen Hurts QB 65% “safe to wait on QB” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:56:29  pick 55  Quinshon Judkins (RB) taken by seat 6 in 14 s
    03:56:30  pick 56  David Montgomery (RB) taken by seat 5 in 1 s INSTANTLY (autopick)
    03:56:38  plan #325 for pick 57: Jalen Hurts QB 83% “safe to wait on QB” · Jaylen Warren RB 96% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:56:46  pick 57  Rhamondre Stevenson (RB) taken by seat 4 in 16 s — a target is gone
    03:56:51  plan #326 for pick 58: Jalen Hurts QB 94% “safe to wait on QB” · Jaylen Warren RB 96% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:56:53  heartbeat sent (Yahoo told we are not idle)
    03:56:58  pick 58  Luther Burden III (WR) taken by seat 3 in 12 s
    03:56:58  plan #327 for pick 59: Jalen Hurts QB 84% “safe to wait on QB” · Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:56:58  ON THE CLOCK, pick 59 · plan #327 (0.0 s old) · lineup needs QB FLEX K DEF
    03:56:59  PICKED Jalen Hurts (QB) via action, confirmed in 477 ms — chose Jalen Hurts (QB): nothing urgent, the most valuable player who fills a slot (84% to survive, nobody better worth waiting for)
    03:57:01  plan #328 for pick 60: Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Emeka Egbuka WR “depth fallback (engine list exhausted)” · Terry McLaurin WR “depth fallback (engine list exhausted)”
    03:57:07  pick 60  Jayden Daniels (QB) taken by seat 1 in 8 s
    03:57:14  plan #329 for pick 61: Jaylen Warren RB 98% “safe to wait on your FLEX spot” · Emeka Egbuka WR “depth fallback (engine list exhausted)” · Terry McLaurin WR “depth fallback (engine list exhausted)”
    03:57:16  pick 61  Terry McLaurin (WR) taken by seat 1 in 9 s — a target is gone
    03:57:17  plan #330 for pick 62: Jaylen Warren RB 26% “waiting likely costs ~10 pts at your FLEX sp” · Emeka Egbuka WR “depth fallback (engine list exhausted)” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    03:57:17  ON THE CLOCK, pick 62 · plan #330 (0.0 s old) · lineup needs FLEX K DEF
    03:57:18  PICKED Jaylen Warren (RB) via action, confirmed in 488 ms — chose Jaylen Warren (RB): waiting would likely cost about 10 points at your FLEX spot, 26% to still be there next turn; top projection left was Trevor Lawrence, passed on
    03:57:21  plan #331 for pick 63: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Emeka Egbuka WR 60% “bench insurance: covers 2 WR starters ~6.5 w” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    03:57:32  pick 63  TreVeyon Henderson (RB) taken by seat 3 in 15 s — a target is gone
    03:57:33  plan #332 for pick 64: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Emeka Egbuka WR 58% “bench insurance: covers 2 WR starters ~6.5 w” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:57:42  pick 64  Emeka Egbuka (WR) taken by seat 4 in 9 s — a target is gone (was 58% to survive)
    03:57:42  pick 65  Jonathon Brooks (RB) taken by seat 5 in 0 s INSTANTLY (autopick)
    03:57:46  plan #333 for pick 66: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 25% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    03:57:53  heartbeat sent (Yahoo told we are not idle)
    03:58:09  pick 66  Christian Watson (WR) taken by seat 6 in 28 s — a target is gone
    03:58:09  pick 67  Carnell Tate (WR) taken by seat 7 in 0 s INSTANTLY (autopick)
    03:58:11  plan #335 for pick 68: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 39% “bench insurance: covers 2 WR starters ~6.5 w” · Mike Evans WR “depth fallback (engine list exhausted)”
    03:58:35  pick 68  Tucker Kraft (TE) taken by seat 8 in 26 s
    03:58:37  plan #337 for pick 69: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 38% “bench insurance: covers 2 WR starters ~6.5 w” · Mike Evans WR “depth fallback (engine list exhausted)”
    03:58:46  pick 69  Brian Thomas Jr. (WR) taken by seat 9 in 11 s
    03:58:46  pick 70  Dak Prescott (QB) taken by seat 10 in 0 s INSTANTLY (autopick)
    03:58:47  pick 71  MarShawn Lloyd (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    03:58:49  plan #338 for pick 72: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 56% “bench insurance: covers 2 WR starters ~6.5 w” · Mike Evans WR “depth fallback (engine list exhausted)”
    03:58:54  heartbeat sent (Yahoo told we are not idle)
    03:58:57  pick 72  Jameson Williams (WR) taken by seat 9 in 10 s — a target is gone (was 56% to survive)
    03:58:59  pick 73  Parker Washington (WR) taken by seat 8 in 2 s INSTANTLY (autopick) — a target is gone
    03:58:59  pick 74  Rams (DEF) taken by seat 7 in 0 s INSTANTLY (autopick)
    03:59:01  plan #339 for pick 75: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 61% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:59:24  pick 75  Chris Godwin Jr. (WR) taken by seat 6 in 25 s
    03:59:25  pick 76  Mike Evans (WR) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone (was 61% to survive)
    03:59:25  plan #341 for pick 77: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:59:29  pick 77  Caleb Williams (QB) taken by seat 4 in 4 s
    03:59:37  plan #342 for pick 78: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:59:49  pick 78  Justin Herbert (QB) taken by seat 3 in 20 s
    03:59:50  plan #343 for pick 79: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 88% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:59:50  ON THE CLOCK, pick 79 · plan #343 (0.0 s old) · lineup needs K DEF
    03:59:50  PICKED Tyrone Tracy Jr. (RB) via action, confirmed in 415 ms — lineup full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +10.9 a week over the wire, about 105 points; he also backs up o
    03:59:53  plan #344 for pick 80: Rico Dowdle RB 93% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 90% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:59:57  heartbeat sent (Yahoo told we are not idle)
    04:00:07  pick 80  Blake Corum (RB) taken by seat 1 in 17 s
    04:00:17  pick 81  Alec Pierce (WR) taken by seat 1 in 9 s
    04:00:18  plan #346 for pick 82: Rico Dowdle RB 49% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 15% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    04:00:18  ON THE CLOCK, pick 82 · plan #346 (0.0 s old) · lineup needs K DEF
    04:00:19  PICKED Rico Dowdle (RB) via action, confirmed in 509 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +10.0 a week over the wire, about 25 points; he also backs up one of our s
    04:00:22  plan #347 for pick 83: DK Metcalf WR 16% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 82% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:00:32  pick 83  Trevor Lawrence (QB) taken by seat 3 in 14 s
    04:00:34  plan #348 for pick 84: DK Metcalf WR 17% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:00:37  pick 84  Marvin Harrison Jr. (WR) taken by seat 4 in 4 s — a target is gone
    04:00:37  pick 85  DK Metcalf (WR) taken by seat 5 in 0 s — a target is gone (was 17% to survive)
    04:00:46  plan #349 for pick 86: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 31% “bench insurance: covers 1 TE starter ~3.9 wk” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters behind
    04:00:57  heartbeat sent (Yahoo told we are not idle)
    04:01:01  pick 86  Harold Fannin Jr. (TE) taken by seat 6 in 24 s — a target is gone
    04:01:01  pick 87  Brock Purdy (QB) taken by seat 7 in 0 s INSTANTLY (autopick)
    04:01:02  pick 88  Kyle Pitts Sr. (TE) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 31% to survive)
    04:01:11  plan #351 for pick 89: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 86% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:01:16  pick 89  Jacory Croskey-Merritt (RB) taken by seat 9 in 14 s
    04:01:17  pick 90  J.K. Dobbins (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    04:01:18  pick 91  Jordan Mason (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    04:01:24  plan #352 for pick 92: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 83% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters be
    04:01:31  pick 92  De'Zhaun Stribling (WR) taken by seat 9 in 14 s
    04:01:31  pick 93  Tony Pollard (RB) taken by seat 8 in 0 s INSTANTLY (autopick)
    04:01:32  pick 94  Michael Wilson (WR) taken by seat 7 in 1 s INSTANTLY (autopick)
    04:01:36  plan #353 for pick 95: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 90% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 95% “bench insurance: covers 3 RB starters be
    04:01:58  heartbeat sent (Yahoo told we are not idle)
    04:02:03  pick 95  Bo Nix (QB) taken by seat 6 in 30 s — a target is gone
    04:02:04  pick 96  George Kittle (TE) taken by seat 5 in 1 s INSTANTLY (autopick)
    04:02:08  pick 97  Brandon Aubrey (K) taken by seat 4 in 5 s
    04:02:14  plan #356 for pick 98: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 99% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 99% “bench insurance: covers 3 RB starters b
    04:02:30  pick 98  Chuba Hubbard (RB) taken by seat 3 in 22 s
    04:02:31  plan #358 for pick 99: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 96% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 97% “bench insurance: covers 3 RB starters be
    04:02:31  ON THE CLOCK, pick 99 · plan #358 (0.0 s old) · lineup needs K DEF
    04:02:32  PICKED Wan'Dale Robinson (WR) via action, confirmed in 436 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    04:02:34  plan #359 for pick 100: Patrick Mahomes II QB 96% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 96% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 97% “bench insurance: covers 2 WR starters be
    04:02:39  pick 100  Josh Downs (WR) taken by seat 1 in 7 s
    04:02:46  plan #360 for pick 101: Patrick Mahomes II QB 99% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 97% “bench insurance: covers 2 WR starters be
    04:02:47  pick 101  Jordan Addison (WR) taken by seat 1 in 9 s
    04:02:49  plan #361 for pick 102: Patrick Mahomes II QB 85% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 83% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 77% “bench insurance: covers 2 WR starters be
    04:02:49  ON THE CLOCK, pick 102 · plan #361 (0.0 s old) · lineup needs K DEF
    04:02:50  PICKED Patrick Mahomes II (QB) via action, confirmed in 323 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    04:02:53  plan #362 for pick 103: RJ Harvey RB 81% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 78% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:02:58  heartbeat sent (Yahoo told we are not idle)
    04:02:59  pick 103  Isaiah Likely (TE) taken by seat 3 in 9 s
    04:03:05  plan #363 for pick 104: RJ Harvey RB 82% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 79% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:03:10  pick 104  Chris Rodriguez Jr. (RB) taken by seat 4 in 11 s
    04:03:11  pick 105  Jaxson Dart (QB) taken by seat 5 in 1 s INSTANTLY (autopick)
    04:03:12  pick 106  Dalton Kincaid (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    04:03:13  pick 107  Josh Jacobs (RB) taken by seat 7 in 1 s INSTANTLY (autopick)
    04:03:14  pick 108  Quentin Johnston (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    04:03:17  plan #364 for pick 109: RJ Harvey RB 90% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 91% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:03:21  pick 109  KC Concepcion (WR) taken by seat 9 in 7 s
    04:03:21  pick 110  Stefon Diggs (WR) taken by seat 10 in 0 s INSTANTLY (autopick) — a target is gone
    04:03:22  pick 111  Dallas Goedert (TE) taken by seat 10 in 1 s INSTANTLY (autopick)
    04:03:29  pick 112  Matthew Golden (WR) taken by seat 9 in 7 s
    04:03:29  pick 113  Matthew Stafford (QB) taken by seat 8 in 0 s INSTANTLY (autopick)
    04:03:30  pick 114  Kyler Murray (QB) taken by seat 7 in 1 s INSTANTLY (autopick)
    04:03:30  plan #365 for pick 115: RJ Harvey RB 98% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 98% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:03:31  pick 115  Jared Goff (QB) taken by seat 6 in 2 s INSTANTLY (autopick)
    04:03:31  pick 116  Kyle Monangai (RB) taken by seat 5 in 0 s INSTANTLY (autopick)
    04:03:43  plan #366 for pick 117: RJ Harvey RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:03:44  pick 117  Texans (DEF) taken by seat 4 in 12 s
    04:03:51  pick 118  Broncos (DEF) taken by seat 3 in 7 s
    04:03:51  plan #367 for pick 119: RJ Harvey RB 100% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    04:03:51  ON THE CLOCK, pick 119 · plan #367 (0.0 s old) · lineup needs K DEF
    04:03:52  PICKED RJ Harvey (RB) via action, confirmed in 535 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +9.1 a week over the wire, about 2 points; top projection left was Baker Mayfi
    04:03:55  plan #368 for pick 120: Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted)
    04:03:59  pick 120  Hunter Henry (TE) taken by seat 1 in 6 s
    04:03:59  heartbeat sent (Yahoo told we are not idle)
    04:04:07  plan #369 for pick 121: Courtland Sutton WR 100% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted
    04:04:15  pick 121  Malik Willis (QB) taken by seat 1 in 17 s
    04:04:17  plan #370 for pick 122: Courtland Sutton WR 97% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 93% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted)
    04:04:17  ON THE CLOCK, pick 122 · plan #370 (0.0 s old) · lineup needs K DEF
    04:04:17  PICKED Courtland Sutton (WR) via action, confirmed in 325 ms — lineup full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.7 a week over the wire, about 2 points; top projection left w
    04:04:21  plan #371 for pick 123: Seattle Seahawks DEF 5% “waiting likely costs ~5 pts at DEF (best opt” · Cameron Dicker K 41% “waiting likely costs ~3 pts at K (best optio” · Ka'imi Fairbairn K “depth fallback (engine list exhausted)”
    04:04:28  pick 123  Seahawks (DEF) taken by seat 3 in 11 s
    04:04:33  plan #372 for pick 124: Philadelphia Eagles DEF 16% “waiting likely costs ~3 pts at DEF (best opt” · Cameron Dicker K 30% “waiting likely costs ~3 pts at K (best optio” · Ka'imi Fairbairn K “depth fallback (engine list exhausted)”
    04:04:36  pick 124  Kenny Gainwell (RB) taken by seat 4 in 8 s
    04:04:36  pick 125  Jayden Reed (WR) taken by seat 5 in 0 s INSTANTLY (autopick)
    04:04:38  pick 126  Michael Pittman Jr. (WR) taken by seat 6 in 1 s INSTANTLY (autopick)
    04:04:38  pick 127  Travis Kelce (TE) taken by seat 7 in 1 s INSTANTLY (autopick)
    04:04:39  pick 128  Makai Lemon (WR) taken by seat 8 in 1 s INSTANTLY (autopick)
    04:04:44  pick 129  Eagles (DEF) taken by seat 9 in 4 s
    04:04:44  pick 130  Rachaad White (RB) taken by seat 10 in 0 s INSTANTLY (autopick)
    04:04:45  plan #373 for pick 131: Cameron Dicker K 45% “waiting likely costs ~2 pts at K (best optio” · Pittsburgh Steelers DEF 90% “safe to wait on DEF” · Ka'imi Fairbairn K “depth fallback (engine list exhausted)”
    04:04:45  pick 131  Ka'imi Fairbairn (K) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    04:04:53  pick 132  Dalton Schultz (TE) taken by seat 9 in 9 s
    04:04:54  pick 133  Cameron Dicker (K) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 45% to survive)
    04:04:55  pick 134  Jalen Coker (WR) taken by seat 7 in 1 s INSTANTLY (autopick)
    04:04:56  pick 135  Jason Myers (K) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    04:04:57  plan #374 for pick 136: Pittsburgh Steelers DEF 97% “safe to wait on DEF” · Cam Little K 93% “safe to wait on K” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    04:04:58  pick 136  Vikings (DEF) taken by seat 5 in 1 s INSTANTLY (autopick)
    04:05:01  heartbeat sent (Yahoo told we are not idle)
    04:05:10  plan #375 for pick 137: Pittsburgh Steelers DEF 98% “safe to wait on DEF” · Cam Little K 94% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)”
    04:05:22  pick 137  Romeo Doubs (WR) taken by seat 4 in 24 s
    04:05:22  bridge warning: dropped 1 feed entries numbered >= header pick 137
    04:05:31  pick 138  Jordan Love (QB) taken by seat 3 in 9 s
    04:05:31  plan #377 for pick 139: Pittsburgh Steelers DEF 93% “safe to wait on DEF” · Cam Little K 95% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)”
    04:05:31  ON THE CLOCK, pick 139 · plan #377 (0.0 s old) · lineup needs K DEF
    04:05:32  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 337 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (93% to survive, nobody better worth waiting for); top projection left w
    04:05:34  plan #378 for pick 140: Cam Little K 94% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Tyler Loop K “depth fallback (engine list exhausted)”
    04:05:36  pick 140  Patriots (DEF) taken by seat 1 in 4 s
    04:05:42  pick 141  Tyler Loop (K) taken by seat 1 in 6 s — a target is gone
    04:05:42  plan #379 for pick 142: Cam Little K “fills your open K slot” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    04:05:42  ON THE CLOCK, pick 142 · plan #379 (0.0 s old) · lineup needs K
    04:05:43  PICKED Cam Little (K) via action, confirmed in 621 ms — chose Cam Little (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Baker Mayfield, passed on purpose
    04:05:45  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    03:47:42 PT preflight: ok=true pick_path=action my_team=2 plan=plan 25 deep @pick 1 via store call#275
    03:47:42 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    03:47:42 PT NARR info driver started — seat 2, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    03:48:06 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~43 pts at RB (best option now 154, ~111 by your next turn) · 29% chance he's still there at your next pick · fills yo
    03:48:42 PT heartbeat: setAwayStatus(false)
    03:48:42 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:49:43 PT heartbeat: setAwayStatus(false)
    03:49:43 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:50:04 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~6 pts at TE (best option now 78, ~72 by your next turn) · 89% chance he's still there at your next pick · fills your open TE 
    03:50:15 PT ON CLOCK -> {"drafted":"Drake London","pos":"WR","vorp":51,"proj":193.1,"why":"waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 48% chance he's still there at your next pick · fills your open WR sl
    03:50:46 PT heartbeat: setAwayStatus(false)
    03:50:46 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:51:49 PT heartbeat: setAwayStatus(false)
    03:51:49 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:52:49 PT heartbeat: setAwayStatus(false)
    03:52:49 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:53:22 PT ON CLOCK -> {"drafted":"Rashee Rice","pos":"WR","vorp":34.1,"proj":176.3,"why":"waiting likely costs ~2 pts at WR (best option now 34, ~32 by your next turn) · 82% chance he's still there at your next pick · fills your open WR s
    03:53:43 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~12 pts at your FLEX spot (best option now 26, ~14 by your next turn) · 27% chance he's still there at your next pick · fills yo
    03:53:50 PT heartbeat: setAwayStatus(false)
    03:53:50 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:54:51 PT heartbeat: setAwayStatus(false)
    03:54:51 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:55:51 PT heartbeat: setAwayStatus(false)
    03:55:51 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:56:53 PT heartbeat: setAwayStatus(false)
    03:56:53 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:56:59 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 84% chance he's still there at your next pick · fills your open QB slot · 2 teams picking before you still need a QB · two-pick p
    03:57:18 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~10 pts at your FLEX spot (best option now 9, ~-1 by your next turn) · 26% chance he's still there at your next pick · fills a
    03:57:53 PT heartbeat: setAwayStatus(false)
    03:57:53 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:58:54 PT heartbeat: setAwayStatus(false)
    03:58:54 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:59:50 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacobs) ≈ 105 pts · HANDCUFF: backs up your Cam Skattebo","
    03:59:57 PT heartbeat: setAwayStatus(false)
    03:59:57 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:00:19 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs
    04:00:57 PT heartbeat: setAwayStatus(false)
    04:00:57 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:01:58 PT heartbeat: setAwayStatus(false)
    04:01:58 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:02:32 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.987,"sr":0.987,"e":-10.6,"top_
    04:02:50 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.848,"sr":0.848,"e":11.5,"top_pr
    04:02:58 PT heartbeat: setAwayStatus(false)
    04:02:58 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:03:52 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.995,"sr"
    04:03:59 PT heartbeat: setAwayStatus(false)
    04:03:59 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:04:17 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.96
    04:05:01 PT heartbeat: setAwayStatus(false)
    04:05:01 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    04:05:22 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 137
    04:05:32 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 93% chance he's still there at your next pick · fills your open DEF slot · 2 teams picking before you still need a DEF · t
    04:05:43 PT ON CLOCK -> {"drafted":"Cam Little","pos":"K","vorp":9,"proj":145.5,"why":"fills your open K slot · bargain: still here 13 picks after he's usually drafted","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield",
    04:05:45 PT roster full
    04:05:45 PT NARR info roster full — driver done; posting the trail when the room finishes
    04:05:45 PT driver stop


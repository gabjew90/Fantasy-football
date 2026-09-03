# Scrutiny: Mock 30 -- First and Ten (room 10589182) -- Thursday 2026-09-03 02:57 PT -- 10 teams, our seat 1

Captured 2026-09-03 03:15:43 PT. Times below are Pacific. 10 teams, our team id 1, draft slot 1. 150 picks in the trail, 66 bridge plan calls, 60 recs events in the room log.

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

- Our picks: 15; by the driver 13 (action 13, click 0), by Yahoo from the queue / autopick 2: 120 Courtland Sutton, 121 Dallas Goedert.
- Action latency to store confirmation: median 984 ms, min 920, max 1007.
- Heartbeats 4; away flags detected and cleared 1; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {} -> {3,4,7} -> {2,3,4,7} -> {2,3,4,6,7} -> {2,3,4,6,7,10}.
- Managers away at the end: 2 Rene, 3 Kevin, 4 Jabari, 6 Luke, 7 Component B, 10 Neil.

## Our picks, one block each

### Pick 1 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 34 points at RB, with a 27% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1007 ms, ranker engine, plan call 146, plan age 1926 ms, at 02:58:06 PT.
- Engine's reason: waiting likely costs ~34 pts at RB (best option now 154, ~120 by your next turn) · 27% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 18 te
- Top projection available: Josh Allen -> took it: False.
- Passed on: Ja'Marr Chase (WR, s=0.357, e=91.6); Trey McBride (TE, s=0.793, e=70.5); Josh Allen (QB, s=0.48, e=38.7).
- Plan call 146 @pick 1: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 0 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.27 | 0.27 | 120.2 | 154.2 | waiting likely costs ~34 pts at RB (best option now 154, ~120 by your next turn) · 27% cha |
| Ja'Marr Chase | WR | 115.3 | 0.36 | 0.36 | 91.6 | 115.3 | waiting likely costs ~24 pts at WR (best option now 115, ~92 by your next turn) · 36% chan |
| Trey McBride | TE | 77.9 | 0.79 | 0.79 | 70.5 | 77.9 | waiting likely costs ~7 pts at TE (best option now 78, ~71 by your next turn) · 79% chance |
| Josh Allen | QB | 47.0 | 0.48 | 0.48 | 38.7 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 48% chance |
| Jahmyr Gibbs | RB | 125.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Bijan Robinson | RB | 119.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.7 | 8.3 | 6 |
| RB | 154.2 | 120.2 | 34.0 | 24 |
| WR | 115.3 | 91.6 | 23.7 | 25 |
| TE | 77.9 | 70.5 | 7.4 | 5 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 124.2 | 30.0 | 54 |

### Pick 20 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 991 ms, ranker engine, plan call 152, plan age 1938 ms, at 02:59:52 PT.
- Engine's reason: safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pick plan: pair with the ~60-pt WR expected at your next turn
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=1, e=51); Javonte Williams (RB, s=1, e=36.9); Josh Allen (QB, s=1, e=47).
- Plan call 152 @pick 20: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 19 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 1.00 | 1.00 | 77.9 | 77.9 | safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE s |
| Drake London | WR | 51.0 | 1.00 | 1.00 | 51.0 | 51.0 | safe to wait on WR · 100% chance he's still there at your next pick · fills your open WR s |
| Javonte Williams | RB | 36.9 | 1.00 | 1.00 | 36.9 | 36.9 | safe to wait on RB · 100% chance he's still there at your next pick · fills your open RB s |
| Josh Allen | QB | 47.0 | 1.00 | 1.00 | 47.0 | 47.0 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 47.0 | 0.0 | 9 |
| RB | 36.9 | 36.9 | 0.0 | 17 |
| WR | 51.0 | 51.0 | 0.0 | 24 |
| TE | 77.9 | 77.9 | 0.0 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 39.985766857976785 | 40.0 | 0.0 | 49 |

### Pick 21 (round 3): Drake London (WR)

- In plain English: Took Drake London (WR) because waiting would likely cost about 14 points at WR, with a 14% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 966 ms, ranker engine, plan call 153, plan age 1889 ms, at 02:59:58 PT.
- Engine's reason: waiting likely costs ~14 pts at WR (best option now 51, ~37 by your next turn) · 14% chance he's still there at your next pick · fills your open WR slot · 18 teams picking before you still need a WR · two-pick plan: pair
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Javonte Williams (RB, s=0.325, e=30.5); Josh Allen (QB, s=0.54, e=38.7); Chris Olave (WR, s=None, e=None).
- Plan call 153 @pick 21: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 20 drafted / 2 mine.
- Engine's first choice was **Drake London** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake London | WR | 51.0 | 0.14 | 0.14 | 36.9 | 51.0 | waiting likely costs ~14 pts at WR (best option now 51, ~37 by your next turn) · 14% chanc |
| Javonte Williams | RB | 36.9 | 0.33 | 0.33 | 30.5 | 36.9 | waiting likely costs ~6 pts at RB (best option now 37, ~31 by your next turn) · 32% chance |
| Josh Allen | QB | 47.0 | 0.54 | 0.54 | 38.7 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 54% chance |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.7 | 8.3 | 9 |
| RB | 36.9 | 30.5 | 6.4 | 17 |
| WR | 51.0 | 36.9 | 14.1 | 24 |
| TE | 58.1 | 25.3 | 32.8 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 36.93446478175926 | 31.2 | 5.8 | 48 |

### Pick 40 (round 4): D'Andre Swift (RB)

- In plain English: Took D'Andre Swift (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 920 ms, ranker engine, plan call 160, plan age 1948 ms, at 03:02:10 PT.
- Engine's reason: safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · two-pick plan: pair with the ~33-pt WR expected at your next turn
- Top projection available: Drake Maye -> took it: False.
- Passed on: Garrett Wilson (WR, s=1, e=23.9); Drake Maye (QB, s=1, e=31.1); Jalen Hurts (QB, s=None, e=None).
- Plan call 160 @pick 40: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 39 drafted / 3 mine.
- Engine's first choice was **D'Andre Swift** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| D'Andre Swift | RB | 21.0 | 1.00 | 1.00 | 21.0 | 21.0 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills yo |
| Garrett Wilson | WR | 23.9 | 1.00 | 1.00 | 23.9 | 23.9 | safe to wait on WR · 100% chance he's still there at your next pick · fills your open WR s |
| Drake Maye | QB | 31.1 | 1.00 | 1.00 | 31.1 | 31.1 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Tetairoa McMillan | WR | 15.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 31.1 | 0.0 | 13 |
| RB | 21.0 | 21.0 | 0.0 | 17 |
| WR | 23.9 | 23.9 | 0.0 | 20 |
| TE | 23.8 | 23.8 | 0.0 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 21.042528197063064 | 21.0 | 0.0 | 45 |

### Pick 41 (round 5): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 11 points at WR, with a 11% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 958 ms, ranker engine, plan call 161, plan age 1702 ms, at 03:02:16 PT.
- Engine's reason: waiting likely costs ~11 pts at WR (best option now 24, ~13 by your next turn) · 11% chance he's still there at your next pick · fills your open WR slot · 14 teams picking before you still need a WR · two-pick plan: pair
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.298, e=20.6); Jaylen Warren (RB, s=0.917, e=9.1); Jalen Hurts (QB, s=None, e=None).
- Plan call 161 @pick 41: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 40 drafted / 4 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.11 | 0.11 | 12.6 | 23.9 | waiting likely costs ~11 pts at WR (best option now 24, ~13 by your next turn) · 11% chanc |
| Drake Maye | QB | 31.1 | 0.30 | 0.30 | 20.6 | 31.1 | waiting likely costs ~10 pts at QB (best option now 31, ~21 by your next turn) · 30% chanc |
| Jaylen Warren | RB | 9.3 | 0.92 | 0.92 | 9.1 | 9.3 | safe to wait on your FLEX spot · 92% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Tetairoa McMillan | WR | 15.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 20.6 | 10.5 | 13 |
| RB | 9.3 | 9.1 | 0.2 | 16 |
| WR | 23.9 | 12.6 | 11.3 | 20 |
| TE | 23.8 | 21.1 | 2.7 | 8 |
| K | 13.5 | 13.4 | 0.1 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 44 |

### Pick 60 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for).
- Driver: via **action**, verified store, 990 ms, ranker engine, plan call 169, plan age 1854 ms, at 03:04:56 PT.
- Engine's reason: safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pair with the ~37-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Jaylen Warren (RB, s=1, e=9.3); Trevor Lawrence (QB, s=None, e=None); Davante Adams (WR, s=None, e=None).
- Plan call 169 @pick 60: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 59 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 1.00 | 1.00 | 18.0 | 18.0 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Jaylen Warren | RB | 9.3 | 1.00 | 1.00 | 9.3 | 9.3 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills a  |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 18.0 | 0.0 | 14 |
| RB | 9.3 | 9.3 | 0.0 | 15 |
| WR | 13.1 | 13.1 | 0.0 | 22 |
| TE | 21.1 | 21.1 | 0.0 | 11 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 48 |

### Pick 61 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 7 points at your FLEX spot, with a 52% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 953 ms, ranker engine, plan call 170, plan age 1866 ms, at 03:05:02 PT.
- Engine's reason: waiting likely costs ~7 pts at your FLEX spot (best option now 9, ~2 by your next turn) · 52% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Davante Adams (WR, s=None, e=None); Jameson Williams (WR, s=None, e=None); Rome Odunze (WR, s=None, e=None).
- Plan call 170 @pick 61: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 60 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.52 | 0.52 | 2.3 | 9.3 | waiting likely costs ~7 pts at your FLEX spot (best option now 9, ~2 by your next turn) ·  |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.6 | 2.1 | 13 |
| RB | 9.3 | 2.2 | 7.1 | 16 |
| WR | 13.1 | 7.1 | 6.0 | 24 |
| TE | 21.1 | 15.9 | 5.2 | 11 |
| K | 13.5 | 13.4 | 0.1 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 2.3 | 7.0 | 51 |

### Pick 80 (round 8): Kyle Monangai (RB)

- In plain English: Lineup already full, so Kyle Monangai (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.7 points a week over the waiver wire (Josh Jacobs), worth about 103 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 988 ms, ranker engine, plan call 180, plan age 1859 ms, at 03:07:33 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.7/wk over the wire (Josh Jacobs) ≈ 103 pts · HANDCUFF: backs up your D'Andre Swift
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Carnell Tate (WR, s=1, e=-10.2); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 180 @pick 80: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 79 drafted / 7 mine.
- Engine's first choice was **Kyle Monangai** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kyle Monangai | RB | -28.8 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.7/wk over the wire (Josh Jacob |
| Carnell Tate | WR | -10.2 | 1.00 | 1.00 | -10.2 | -10.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Rico Dowdle | RB | -11.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.7 | 0.0 | 19 |
| RB | -5.4 | -5.4 | 0.0 | 32 |
| WR | -10.2 | -10.2 | 0.0 | 36 |
| TE | 19.8 | 19.8 | 0.0 | 21 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 8 |

### Pick 81 (round 9): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 25 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 924 ms, ranker engine, plan call 181, plan age 1847 ms, at 03:07:39 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Carnell Tate (WR, s=0.059, e=-10.6); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 181 @pick 81: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 80 drafted / 8 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.40 | 0.40 | -5.9 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10. |
| Carnell Tate | WR | -10.2 | 0.06 | 0.06 | -10.6 | -10.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 12.2 | 3.5 | 19 |
| RB | -5.4 | -5.9 | 0.5 | 31 |
| WR | -10.2 | -10.6 | 0.4 | 37 |
| TE | 19.8 | 15.2 | 4.6 | 21 |
| K | 13.5 | 13.4 | 0.1 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 9 |

### Pick 100 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 990 ms, ranker engine, plan call 192, plan age 1852 ms, at 03:10:37 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=1, e=12.8); RJ Harvey (RB, s=1, e=-5.4); Matthew Stafford (QB, s=None, e=None).
- Plan call 192 @pick 100: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 99 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 1.00 | 1.00 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 1.00 | 1.00 | 12.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.8 | 0.0 | 17 |
| RB | -5.4 | -5.4 | 0.0 | 23 |
| WR | -10.6 | -10.6 | 0.0 | 36 |
| TE | 13.8 | 13.8 | 0.0 | 18 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 16.0 | 16.0 | 0.0 | 9 |

### Pick 101 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 959 ms, ranker engine, plan call 193, plan age 1791 ms, at 03:10:43 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.82, e=-6); Courtland Sutton (WR, s=0.83, e=-11.5); Matthew Stafford (QB, s=None, e=None).
- Plan call 193 @pick 101: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 7], state store with 100 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.78 | 0.78 | 11.3 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.82 | 0.82 | -6.0 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.83 | 0.83 | -11.5 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.3 | 1.5 | 17 |
| RB | -5.4 | -6.0 | 0.6 | 23 |
| WR | -11.1 | -11.5 | 0.4 | 35 |
| TE | 13.8 | 12.7 | 1.1 | 18 |
| K | 12.0 | 11.4 | 0.6 | 13 |
| DEF | 16.0 | 14.2 | 1.8 | 10 |

### Pick 120 (round 12): Courtland Sutton (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    03:10:43 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.784,"sr":0.784,"e":11.3,"top_proj_available":{"n":"
    03:13:30 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    03:13:30 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    03:15:00 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"safe to wait on K · 100% chance he's still there at your next pick · fills your open K slot · two-pick plan: pair with the ~32-pt RB expected at your next turn","s":1,"sr"
    03:15:05 PT ON CLOCK -> {"drafted":"Baltimore Ravens","pos":"DEF","vorp":-2,"proj":115,"why":"fills your open DEF slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection":false,"pass
- No plan call at this pick; the last plan before it was call 199 @pick 118:
- Plan call 199 @pick 118: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 3, 4, 7], state store with 117 drafted / 11 mine.
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.99 | 0.99 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.98 | 0.98 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -25.9 | -26.0 | 0.1 | 21 |
| WR | -11.1 | -11.1 | 0.0 | 30 |
| TE | 13.8 | 13.8 | 0.0 | 18 |
| K | 12.0 | 10.3 | 1.7 | 13 |
| DEF | 8.0 | 7.8 | 0.2 | 9 |

### Pick 121 (round 13): Dallas Goedert (TE)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    02:58:06 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~34 pts at RB (best option now 154, ~120 by your next turn) · 27% chance he's still there at your next pick · fills your open RB slot · TA
    02:59:52 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pick plan: pair with t
    02:59:58 PT ON CLOCK -> {"drafted":"Drake London","pos":"WR","vorp":51,"proj":193.1,"why":"waiting likely costs ~14 pts at WR (best option now 51, ~37 by your next turn) · 14% chance he's still there at your next pick · fills your open WR slot · 18 teams picki
    03:02:10 PT ON CLOCK -> {"drafted":"D'Andre Swift","pos":"RB","vorp":21,"proj":181.2,"why":"safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · two-pick plan: 
    03:02:16 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~11 pts at WR (best option now 24, ~13 by your next turn) · 11% chance he's still there at your next pick · fills your open WR slot · 14 teams pic
    03:04:56 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pair with the ~37-pt WR
    03:05:02 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~7 pts at your FLEX spot (best option now 9, ~2 by your next turn) · 52% chance he's still there at your next pick · fills a FLEX slot · 2 teams p
    03:07:33 PT ON CLOCK -> {"drafted":"Kyle Monangai","pos":"RB","vorp":-28.8,"proj":131.3,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.7/wk over the wire (Josh Jacobs) ≈ 103 pts · HANDCUFF: backs up your D'Andre Swift","s":1,"sr":1,"e":-5.4
    03:07:39 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Jaylen Warr
    03:10:37 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":1,"sr":1,"e":-10.6,"top_proj_available":{"n":"Patric
    03:10:43 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.784,"sr":0.784,"e":11.3,"top_proj_available":{"n":"
    03:13:30 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
- No plan call at this pick; the last plan before it was call 199 @pick 118:
- Plan call 199 @pick 118: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 3, 4, 7], state store with 117 drafted / 11 mine.
- Engine's first choice was **Courtland Sutton** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.99 | 0.99 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.98 | 0.98 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 12 |
| RB | -25.9 | -26.0 | 0.1 | 21 |
| WR | -11.1 | -11.1 | 0.0 | 30 |
| TE | 13.8 | 13.8 | 0.0 | 18 |
| K | 12.0 | 10.3 | 1.7 | 13 |
| DEF | 8.0 | 7.8 | 0.2 | 9 |

### Pick 140 (round 14): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 991 ms, ranker engine, plan call 206, plan age 1726 ms, at 03:15:00 PT.
- Engine's reason: safe to wait on K · 100% chance he's still there at your next pick · fills your open K slot · two-pick plan: pair with the ~32-pt RB expected at your next turn
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Baltimore Ravens (DEF, s=1, e=0); Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None).
- Plan call 206 @pick 140: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 3, 4, 6, 7, 10], state store with 139 drafted / 13 mine.
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | 1.00 | 1.00 | 6.0 | 6.0 | safe to wait on K · 100% chance he's still there at your next pick · fills your open K slo |
| Baltimore Ravens | DEF | -2.0 | 1.00 | 1.00 | 0.0 | 0.0 | safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 10 |
| RB | -25.9 | -25.9 | 0.0 | 21 |
| WR | -27.9 | -27.9 | 0.0 | 22 |
| TE | -2.4 | -2.4 | 0.0 | 12 |
| K | 6.0 | 6.0 | 0.0 | 13 |
| DEF | 0.0 | 0.0 | 0.0 | 5 |

### Pick 141 (round 15): Ravens (DEF)

- In plain English: Took Baltimore Ravens (DEF) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 984 ms, ranker engine, plan call 207, plan age 1944 ms, at 03:15:05 PT.
- Engine's reason: fills your open DEF slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Los Angeles Chargers (DEF, s=None, e=None); Green Bay Packers (DEF, s=None, e=None); Kansas City Chiefs (DEF, s=None, e=None).
- Plan call 207 @pick 141: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 0, 'DEF': 1, 'BN': 6}, away seats [2, 3, 4, 6, 7, 10], state store with 140 drafted / 14 mine.
- Engine's first choice was **Baltimore Ravens** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Baltimore Ravens | DEF | -2.0 | - | - | - | - | fills your open DEF slot |
| Los Angeles Chargers | DEF | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Green Bay Packers | DEF | -4.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Kansas City Chiefs | DEF | -6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cleveland Browns | DEF | -8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Detroit Lions | DEF | -10.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 18 | 22% | 0% |
| 30-50% | 16 | 39% | 12% |
| 50-70% | 18 | 59% | 11% |
| 70-90% | 40 | 81% | 78% |
| 90-100% | 54 | 97% | 83% |

146 predictions over 59 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    02:57:26  plan #142 for pick 1: Christian McCaffrey RB 27% “waiting likely costs ~34 pts at RB (best opt” · Ja'Marr Chase WR 36% “waiting likely costs ~24 pts at WR (best opt” · Trey McBride TE 79% “waiting likely costs ~7 pts at TE (best o
    02:57:28  driver started — seat 1, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    02:58:04  ON THE CLOCK, pick 1 · plan #146 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    02:58:06  PICKED Christian McCaffrey (RB) via action, confirmed in 1007 ms — chose Christian McCaffrey (RB): waiting would likely cost about 34 points at RB, 27% to still be there next turn; top projection left was Josh Allen, passed on pur
    02:58:10  plan #147 for pick 2: Jahmyr Gibbs RB 42% “waiting likely costs ~23 pts at RB (best opt” · Ja'Marr Chase WR 35% “waiting likely costs ~26 pts at WR (best opt” · Trey McBride TE 78% “waiting likely costs ~8 pts at TE (best opti”
    02:58:15  pick 2  Jahmyr Gibbs (RB) taken by seat 2 in 9 s — a target is gone (was 42% to survive)
    02:58:15  pick 3  Bijan Robinson (RB) taken by seat 3 in 0 s — a target is gone
    02:58:15  pick 4  Ja'Marr Chase (WR) taken by seat 4 in 0 s — a target is gone (was 35% to survive)
    02:58:15  pick 5  Puka Nacua (WR) taken by seat 5 in 0 s — a target is gone
    02:58:40  pick 6  Jonathan Taylor (RB) taken by seat 6 in 25 s — a target is gone
    02:58:40  pick 7  Jaxon Smith-Njigba (WR) taken by seat 7 in 0 s — a target is gone
    02:58:41  plan #148 for pick 8: Amon-Ra St. Brown WR 15% “waiting likely costs ~27 pts at WR (best opt” · De'Von Achane RB 22% “waiting likely costs ~17 pts at RB (best opt” · Trey McBride TE 88% “waiting likely costs ~4 pts at TE (best opt
    02:58:50  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 10 s — a target is gone (was 15% to survive)
    02:58:50  pick 9  James Cook III (RB) taken by seat 9 in 0 s — a target is gone
    02:59:00  pick 10  CeeDee Lamb (WR) taken by seat 10 in 10 s — a target is gone
    02:59:00  plan #149 for pick 11: De'Von Achane RB 32% “waiting likely costs ~16 pts at RB (best opt” · Justin Jefferson WR 33% “waiting likely costs ~5 pts at WR (best opti” · Trey McBride TE 86% “waiting likely costs ~4 pts at TE (best opt
    02:59:05  pick 11  Kenneth Walker III (RB) taken by seat 10 in 5 s
    02:59:05  pick 12  Saquon Barkley (RB) taken by seat 9 in 0 s
    02:59:07  pick 13  De'Von Achane (RB) taken by seat 8 in 2 s INSTANTLY (autopick) — a target is gone (was 32% to survive)
    02:59:08  pick 14  Chase Brown (RB) taken by seat 7 in 1 s INSTANTLY (autopick) — a target is gone
    02:59:13  pick 15  Justin Jefferson (WR) taken by seat 6 in 5 s — a target is gone (was 33% to survive)
    02:59:13  plan #150 for pick 16: Trey McBride TE 89% “waiting likely costs ~3 pts at TE (best opti” · Drake London WR 70% “waiting likely costs ~2 pts at WR (best opti” · Derrick Henry RB 42% “waiting likely costs ~6 pts at RB (best opti”
    02:59:26  pick 16  Derrick Henry (RB) taken by seat 5 in 13 s — a target is gone (was 42% to survive)
    02:59:26  pick 17  Omarion Hampton (RB) taken by seat 4 in 0 s
    02:59:26  plan #151 for pick 18: Drake London WR 78% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 94% “waiting likely costs ~2 pts at TE (best opti” · Kyren Williams RB 94% “safe to wait on RB”
    02:59:29  pick 18  Nico Collins (WR) taken by seat 3 in 3 s — a target is gone
    02:59:50  pick 19  Kyren Williams (RB) taken by seat 2 in 21 s — a target is gone (was 94% to survive)
    02:59:50  plan #152 for pick 20: Trey McBride TE 100% “safe to wait on TE” · Drake London WR 100% “safe to wait on WR” · Javonte Williams RB 100% “safe to wait on RB”
    02:59:50  ON THE CLOCK, pick 20 · plan #152 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    02:59:52  PICKED Trey McBride (TE) via action, confirmed in 991 ms — chose Trey McBride (TE): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left was Josh Allen, 
    02:59:56  plan #153 for pick 21: Drake London WR 14% “waiting likely costs ~14 pts at WR (best opt” · Javonte Williams RB 33% “waiting likely costs ~6 pts at RB (best opti” · Josh Allen QB 54% “waiting likely costs ~8 pts at QB (best opti”
    02:59:56  ON THE CLOCK, pick 21 · plan #153 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    02:59:58  PICKED Drake London (WR) via action, confirmed in 966 ms — chose Drake London (WR): waiting would likely cost about 14 points at WR, 14% to still be there next turn; top projection left was Josh Allen, passed on purpose
    03:00:02  plan #154 for pick 22: A.J. Brown WR 14% “waiting likely costs ~12 pts at WR (best opt” · Javonte Williams RB 31% “waiting likely costs ~7 pts at RB (best opti” · Josh Allen QB 51% “waiting likely costs ~9 pts at QB (best opti”
    03:00:02  pick 22  Brock Bowers (TE) taken by seat 2 in 4 s
    03:00:06  pick 23  Ashton Jeanty (RB) taken by seat 3 in 4 s — a target is gone
    03:00:06  pick 24  George Pickens (WR) taken by seat 4 in 0 s — a target is gone
    03:00:31  pick 25  A.J. Brown (WR) taken by seat 5 in 25 s — a target is gone (was 14% to survive)
    03:00:31  pick 26  Chris Olave (WR) taken by seat 6 in 0 s — a target is gone
    03:00:31  pick 27  Josh Allen (QB) taken by seat 7 in 0 s — a target is gone (was 51% to survive)
    03:00:32  plan #155 for pick 28: Rashee Rice WR 33% “waiting likely costs ~7 pts at WR (best opti” · Javonte Williams RB 41% “waiting likely costs ~7 pts at RB (best opti” · Drake Maye QB 79% “waiting likely costs ~3 pts at QB (best opti”
    03:00:41  pick 28  Javonte Williams (RB) taken by seat 8 in 10 s — a target is gone (was 41% to survive)
    03:00:41  pick 29  DeVonta Smith (WR) taken by seat 9 in 0 s — a target is gone
    03:00:56  pick 30  Colston Loveland (TE) taken by seat 10 in 15 s
    03:00:56  plan #156 for pick 31: Rashee Rice WR 45% “waiting likely costs ~6 pts at WR (best opti” · Travis Etienne Jr. RB 65% “safe to wait on RB” · Drake Maye QB 83% “waiting likely costs ~2 pts at QB (best opti”
    03:01:04  pick 31  Jeremiyah Love (RB) taken by seat 10 in 8 s — a target is gone
    03:01:14  plan #157 for pick 32: Rashee Rice WR 54% “waiting likely costs ~5 pts at WR (best opti” · Travis Etienne Jr. RB 63% “waiting likely costs ~1 pts at RB (best opti” · Drake Maye QB 83% “waiting likely costs ~2 pts at QB (best opti”
    03:01:19  pick 32  Jaylen Waddle (WR) taken by seat 9 in 15 s
    03:01:22  pick 33  Cam Skattebo (RB) taken by seat 8 in 3 s — a target is gone
    03:01:22  pick 34  Malik Nabers (WR) taken by seat 7 in 0 s INSTANTLY (autopick) — a target is gone
    03:01:31  pick 35  Breece Hall (RB) taken by seat 6 in 9 s
    03:01:31  heartbeat sent (Yahoo told we are not idle)
    03:01:31  plan #158 for pick 36: Rashee Rice WR 67% “waiting likely costs ~3 pts at WR (best opti” · Travis Etienne Jr. RB 78% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 92% “waiting likely costs ~1 pts at QB (best opti”
    03:01:53  pick 36  Tee Higgins (WR) taken by seat 5 in 22 s
    03:01:53  pick 37  Zay Flowers (WR) taken by seat 4 in 0 s — a target is gone
    03:01:53  plan #159 for pick 38: Rashee Rice WR 54% “waiting likely costs ~5 pts at WR (best opti” · Travis Etienne Jr. RB 88% “safe to wait on RB” · Drake Maye QB 94% “safe to wait on QB”
    03:02:00  pick 38  Rashee Rice (WR) taken by seat 3 in 7 s — a target is gone (was 54% to survive)
    03:02:08  pick 39  Travis Etienne Jr. (RB) taken by seat 2 in 8 s — a target is gone (was 88% to survive)
    03:02:08  plan #160 for pick 40: D'Andre Swift RB 100% “safe to wait on your FLEX spot” · Garrett Wilson WR 100% “safe to wait on WR” · Drake Maye QB 100% “safe to wait on QB”
    03:02:08  ON THE CLOCK, pick 40 · plan #160 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    03:02:10  PICKED D'Andre Swift (RB) via action, confirmed in 920 ms — chose D'Andre Swift (RB): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left was Drake Maye
    03:02:14  plan #161 for pick 41: Garrett Wilson WR 11% “waiting likely costs ~11 pts at WR (best opt” · Drake Maye QB 30% “waiting likely costs ~10 pts at QB (best opt” · Jaylen Warren RB 92% “safe to wait on your FLEX spot”
    03:02:14  ON THE CLOCK, pick 41 · plan #161 (0.0 s old) · lineup needs QB WR FLEX K DEF
    03:02:16  PICKED Garrett Wilson (WR) via action, confirmed in 958 ms — chose Garrett Wilson (WR): waiting would likely cost about 11 points at WR, 11% to still be there next turn; top projection left was Drake Maye, passed on purpose
    03:02:20  plan #162 for pick 42: Drake Maye QB 27% “waiting likely costs ~11 pts at QB (best opt” · Jaylen Warren RB 94% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:02:30  pick 42  Tetairoa McMillan (WR) taken by seat 2 in 14 s — a target is gone
    03:02:30  pick 43  Tyler Warren (TE) taken by seat 3 in 0 s
    03:02:30  pick 44  Lamar Jackson (QB) taken by seat 4 in 0 s
    03:02:46  pick 45  Ladd McConkey (WR) taken by seat 5 in 16 s
    03:02:47  plan #163 for pick 46: Drake Maye QB 50% “waiting likely costs ~7 pts at QB (best opti” · Jaylen Warren RB 93% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:02:51  pick 46  Emeka Egbuka (WR) taken by seat 6 in 5 s — a target is gone
    03:02:51  pick 47  DJ Moore (WR) taken by seat 7 in 0 s
    03:02:55  pick 48  Terry McLaurin (WR) taken by seat 8 in 4 s
    03:03:09  pick 49  David Montgomery (RB) taken by seat 9 in 14 s
    03:03:09  plan #164 for pick 50: Drake Maye QB 53% “waiting likely costs ~7 pts at QB (best opti” · Jaylen Warren RB 93% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:03:30  pick 50  Parker Washington (WR) taken by seat 10 in 21 s
    03:03:30  plan #165 for pick 51: Drake Maye QB 59% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:03:56  pick 51  Bhayshul Tuten (RB) taken by seat 10 in 26 s
    03:03:56  plan #166 for pick 52: Drake Maye QB 65% “waiting likely costs ~5 pts at QB (best opti” · Jaylen Warren RB 94% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    03:04:01  pick 52  Jadarian Price (RB) taken by seat 9 in 5 s
    03:04:03  pick 53  Drake Maye (QB) taken by seat 8 in 2 s INSTANTLY (autopick) — a target is gone (was 65% to survive)
    03:04:04  pick 54  Bucky Irving (RB) taken by seat 7 in 1 s INSTANTLY (autopick)
    03:04:12  pick 55  Quinshon Judkins (RB) taken by seat 6 in 8 s
    03:04:12  plan #167 for pick 56: Jalen Hurts QB 75% “safe to wait on QB” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:04:37  pick 56  Rhamondre Stevenson (RB) taken by seat 5 in 25 s — a target is gone
    03:04:38  plan #168 for pick 57: Jalen Hurts QB 83% “safe to wait on QB” · Jaylen Warren RB 99% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:04:38  pick 57  TreVeyon Henderson (RB) taken by seat 4 in 1 s INSTANTLY (autopick)
    03:04:42  pick 58  Joe Burrow (QB) taken by seat 3 in 4 s
    03:04:54  pick 59  Jayden Daniels (QB) taken by seat 2 in 12 s
    03:04:54  plan #169 for pick 60: Jalen Hurts QB 100% “safe to wait on QB” · Jaylen Warren RB 100% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    03:04:54  ON THE CLOCK, pick 60 · plan #169 (0.0 s old) · lineup needs QB FLEX K DEF
    03:04:56  PICKED Jalen Hurts (QB) via action, confirmed in 990 ms — chose Jalen Hurts (QB): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for)
    03:05:00  plan #170 for pick 61: Jaylen Warren RB 52% “waiting likely costs ~7 pts at your FLEX spo” · Davante Adams WR “depth fallback (engine list exhausted)” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:05:00  ON THE CLOCK, pick 61 · plan #170 (0.0 s old) · lineup needs FLEX K DEF
    03:05:02  PICKED Jaylen Warren (RB) via action, confirmed in 953 ms — chose Jaylen Warren (RB): waiting would likely cost about 7 points at your FLEX spot, 52% to still be there next turn; top projection left was Trevor Lawrence, passed on 
    03:05:06  plan #171 for pick 62: Kyle Monangai RB 97% “bench insurance: covers 3 RB starters ~9.6 w” · Davante Adams WR 61% “bench insurance: covers 2 WR starters ~6.5 w” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:05:16  pick 62  Luther Burden III (WR) taken by seat 2 in 14 s
    03:05:16  pick 63  Jonathon Brooks (RB) taken by seat 3 in 0 s
    03:05:16  pick 64  Tucker Kraft (TE) taken by seat 4 in 0 s
    03:05:18  plan #172 for pick 65: Kyle Monangai RB 96% “bench insurance: covers 3 RB starters ~9.6 w” · Davante Adams WR 75% “bench insurance: covers 2 WR starters ~6.5 w” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:05:38  pick 65  Christian Watson (WR) taken by seat 5 in 22 s — a target is gone
    03:05:38  heartbeat sent (Yahoo told we are not idle)
    03:05:39  plan #173 for pick 66: Kyle Monangai RB 97% “bench insurance: covers 3 RB starters ~9.6 w” · Davante Adams WR 70% “bench insurance: covers 2 WR starters ~6.5 w” · Jameson Williams WR “depth fallback (engine list exhausted)”
    03:05:48  pick 66  Davante Adams (WR) taken by seat 6 in 10 s — a target is gone (was 70% to survive)
    03:05:49  pick 67  Sam LaPorta (TE) taken by seat 7 in 1 s INSTANTLY (autopick)
    03:05:52  plan #174 for pick 68: Kyle Monangai RB 98% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 42% “bench insurance: covers 2 WR starters ~6.5 w” · Rome Odunze WR “depth fallback (engine list exhausted)”
    03:05:56  pick 68  Kyle Pitts Sr. (TE) taken by seat 8 in 7 s
    03:06:06  pick 69  Rome Odunze (WR) taken by seat 9 in 10 s — a target is gone
    03:06:07  plan #175 for pick 70: Kyle Monangai RB 97% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 23% “bench insurance: covers 2 WR starters ~6.5 w” · Mike Evans WR “depth fallback (engine list exhausted)”
    03:06:19  pick 70  Mike Evans (WR) taken by seat 10 in 13 s — a target is gone
    03:06:19  plan #176 for pick 71: Kyle Monangai RB 97% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 22% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:06:39  pick 71  Dak Prescott (QB) taken by seat 10 in 20 s
    03:06:39  plan #177 for pick 72: Kyle Monangai RB 97% “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 21% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:06:44  pick 72  Justin Herbert (QB) taken by seat 9 in 5 s
    03:06:47  pick 73  Alec Pierce (WR) taken by seat 8 in 3 s
    03:06:48  pick 74  Rams (DEF) taken by seat 7 in 1 s INSTANTLY (autopick)
    03:06:55  pick 75  Jameson Williams (WR) taken by seat 6 in 7 s — a target is gone (was 21% to survive)
    03:06:55  plan #178 for pick 76: Kyle Monangai RB 99% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 81% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:07:19  pick 76  Caleb Williams (QB) taken by seat 5 in 24 s
    03:07:19  pick 77  Marvin Harrison Jr. (WR) taken by seat 4 in 0 s — a target is gone
    03:07:19  pick 78  Brian Thomas Jr. (WR) taken by seat 3 in 0 s
    03:07:31  pick 79  DK Metcalf (WR) taken by seat 2 in 12 s — a target is gone (was 81% to survive)
    03:07:31  plan #180 for pick 80: Kyle Monangai RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · Carnell Tate WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:07:31  ON THE CLOCK, pick 80 · plan #180 (0.0 s old) · lineup needs K DEF
    03:07:33  PICKED Kyle Monangai (RB) via action, confirmed in 988 ms — lineup full, so Kyle Monangai (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +10.7 a week over the wire, about 103 points; he also backs up one of 
    03:07:37  plan #181 for pick 81: Rico Dowdle RB 40% “bench insurance: covers 3 RB starters behind” · Carnell Tate WR 6% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    03:07:37  ON THE CLOCK, pick 81 · plan #181 (0.0 s old) · lineup needs K DEF
    03:07:39  PICKED Rico Dowdle (RB) via action, confirmed in 924 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +10.0 a week over the wire, about 25 points; he also backs up one of our s
    03:07:43  plan #182 for pick 82: Carnell Tate WR 6% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 73% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:07:55  pick 82  George Kittle (TE) taken by seat 2 in 16 s
    03:07:55  pick 83  Carnell Tate (WR) taken by seat 3 in 0 s — a target is gone (was 6% to survive)
    03:07:56  plan #183 for pick 84: Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 78% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:07:56  pick 84  Harold Fannin Jr. (TE) taken by seat 4 in 1 s INSTANTLY (autopick)
    03:08:06  pick 85  MarShawn Lloyd (RB) taken by seat 5 in 10 s
    03:08:08  plan #184 for pick 86: Wan'Dale Robinson WR 96% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 80% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:08:26  pick 86  Josh Jacobs (RB) taken by seat 6 in 20 s
    03:08:28  plan #185 for pick 87: Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 80% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:08:28  pick 87  Brandon Aubrey (K) taken by seat 7 in 3 s
    03:08:30  pick 88  Tony Pollard (RB) taken by seat 8 in 1 s INSTANTLY (autopick)
    03:08:38  pick 89  Chris Godwin Jr. (WR) taken by seat 9 in 8 s — a target is gone
    03:08:38  plan #186 for pick 90: Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 83% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:09:06  pick 90  Jacory Croskey-Merritt (RB) taken by seat 10 in 28 s
    03:09:06  plan #187 for pick 91: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Trevor Lawrence QB 30% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters behin
    03:09:24  pick 91  De'Zhaun Stribling (WR) taken by seat 10 in 18 s
    03:09:24  plan #188 for pick 92: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Trevor Lawrence QB 28% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 87% “bench insurance: covers 3 RB starters behin
    03:09:33  pick 92  Isaiah Likely (TE) taken by seat 9 in 9 s
    03:09:36  pick 93  Jaxson Dart (QB) taken by seat 8 in 3 s
    03:09:36  plan #189 for pick 94: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Trevor Lawrence QB 28% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 90% “bench insurance: covers 3 RB starters behin
    03:09:36  pick 94  Texans (DEF) taken by seat 7 in 1 s INSTANTLY (autopick)
    03:09:38  heartbeat sent (Yahoo told we are not idle)
    03:09:52  pick 95  Chuba Hubbard (RB) taken by seat 6 in 15 s
    03:09:52  plan #190 for pick 96: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Trevor Lawrence QB 45% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 93% “bench insurance: covers 3 RB starters behi
    03:10:12  pick 96  J.K. Dobbins (RB) taken by seat 5 in 20 s
    03:10:12  pick 97  Trevor Lawrence (QB) taken by seat 4 in 0 s — a target is gone (was 45% to survive)
    03:10:12  plan #191 for pick 98: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 93% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 95% “bench insurance: covers 3 RB starters b
    03:10:14  pick 98  Blake Corum (RB) taken by seat 3 in 2 s INSTANTLY (autopick)
    03:10:35  pick 99  Jordan Mason (RB) taken by seat 2 in 21 s
    03:10:35  plan #192 for pick 100: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 100% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 100% “bench insurance: covers 3 RB starter
    03:10:35  ON THE CLOCK, pick 100 · plan #192 (0.0 s old) · lineup needs K DEF
    03:10:37  PICKED Wan'Dale Robinson (WR) via action, confirmed in 990 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    03:10:41  plan #193 for pick 101: Patrick Mahomes II QB 78% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 82% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 83% “bench insurance: covers 2 WR starters be
    03:10:41  ON THE CLOCK, pick 101 · plan #193 (0.0 s old) · lineup needs K DEF
    03:10:43  PICKED Patrick Mahomes II (QB) via action, confirmed in 959 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    03:10:47  plan #194 for pick 102: RJ Harvey RB 82% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 80% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:10:51  pick 102  Michael Wilson (WR) taken by seat 2 in 8 s — a target is gone
    03:10:52  pick 103  Brock Purdy (QB) taken by seat 3 in 1 s INSTANTLY (autopick)
    03:10:53  pick 104  Josh Downs (WR) taken by seat 4 in 1 s INSTANTLY (autopick)
    03:11:15  plan #195 for pick 105: RJ Harvey RB 89% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 87% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    03:11:15  pick 105  Stefon Diggs (WR) taken by seat 5 in 22 s — a target is gone
    03:11:18  pick 106  Matthew Stafford (QB) taken by seat 6 in 3 s
    03:11:18  pick 107  Jared Goff (QB) taken by seat 7 in 0 s INSTANTLY (autopick)
    03:11:21  pick 108  Seahawks (DEF) taken by seat 8 in 3 s
    03:11:24  pick 109  Eagles (DEF) taken by seat 9 in 3 s
    03:11:47  pick 110  Kenny Gainwell (RB) taken by seat 10 in 23 s — a target is gone
    03:11:47  plan #196 for pick 111: RJ Harvey RB 95% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 95% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted)”
    03:12:15  pick 111  Bo Nix (QB) taken by seat 10 in 28 s
    03:12:18  pick 112  Broncos (DEF) taken by seat 9 in 3 s
    03:12:21  pick 113  Jason Myers (K) taken by seat 8 in 3 s
    03:12:21  pick 114  Cameron Dicker (K) taken by seat 7 in 0 s INSTANTLY (autopick)
    03:12:35  pick 115  Makai Lemon (WR) taken by seat 6 in 14 s — a target is gone
    03:12:35  plan #198 for pick 116: RJ Harvey RB 98% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 98% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted)”
    03:12:53  pick 116  KC Concepcion (WR) taken by seat 5 in 18 s
    03:12:53  pick 117  RJ Harvey (RB) taken by seat 4 in 0 s — a target is gone (was 98% to survive)
    03:12:53  plan #199 for pick 118: Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 98% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted
    03:13:09  pick 118  Dalton Kincaid (TE) taken by seat 3 in 16 s
    03:13:09  pick 119  Kyler Murray (QB) taken by seat 2 in 0 s
    03:13:29  pick 122  Quentin Johnston (WR) taken by seat 2 in 0 s — a target is gone
    03:13:29  pick 123  Jordan Addison (WR) taken by seat 3 in 0 s — a target is gone
    03:13:29  pick 124  Jayden Reed (WR) taken by seat 4 in 0 s — a target is gone
    03:13:30  Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    03:13:31  plan #200 for pick 125: Ka'imi Fairbairn K 28% “waiting likely costs ~3 pts at K (best optio” · Pittsburgh Steelers DEF 71% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    03:13:38  pick 125  Travis Kelce (TE) taken by seat 5 in 9 s
    03:13:39  heartbeat sent (Yahoo told we are not idle)
    03:13:45  pick 126  Jordan Love (QB) taken by seat 6 in 7 s
    03:13:45  pick 127  Jake Ferguson (TE) taken by seat 7 in 0 s
    03:13:46  plan #201 for pick 128: Ka'imi Fairbairn K 27% “waiting likely costs ~3 pts at K (best optio” · Pittsburgh Steelers DEF 76% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    03:14:00  pick 128  Michael Pittman Jr. (WR) taken by seat 8 in 15 s
    03:14:01  plan #202 for pick 129: Ka'imi Fairbairn K 28% “waiting likely costs ~3 pts at K (best optio” · Pittsburgh Steelers DEF 78% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    03:14:02  pick 129  Ka'imi Fairbairn (K) taken by seat 9 in 2 s INSTANTLY (autopick) — a target is gone (was 28% to survive)
    03:14:08  pick 130  Patriots (DEF) taken by seat 10 in 6 s
    03:14:15  plan #203 for pick 131: Pittsburgh Steelers DEF 84% “waiting likely costs ~2 pts at DEF (best opt” · Cam Little K 64% “waiting likely costs ~1 pts at K (best optio” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    03:14:36  pick 131  Mark Andrews (TE) taken by seat 10 in 28 s
    03:14:37  plan #204 for pick 132: Pittsburgh Steelers DEF 84% “waiting likely costs ~2 pts at DEF (best opt” · Cam Little K 66% “waiting likely costs ~1 pts at K (best optio” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    03:14:47  pick 132  Matthew Golden (WR) taken by seat 9 in 11 s
    03:14:50  plan #205 for pick 133: Pittsburgh Steelers DEF 85% “waiting likely costs ~2 pts at DEF (best opt” · Cam Little K 66% “waiting likely costs ~1 pts at K (best optio” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    03:14:50  pick 133  Jakobi Meyers (WR) taken by seat 8 in 3 s
    03:14:50  pick 134  Travis Hunter (WR) taken by seat 7 in 0 s INSTANTLY (autopick)
    03:14:51  pick 135  Juwan Johnson (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    03:14:55  pick 136  Vikings (DEF) taken by seat 5 in 4 s
    03:14:56  pick 137  Cam Little (K) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 66% to survive)
    03:14:57  pick 138  Jaguars (DEF) taken by seat 3 in 1 s INSTANTLY (autopick)
    03:14:58  pick 139  Steelers (DEF) taken by seat 2 in 1 s INSTANTLY (autopick)
    03:14:58  plan #206 for pick 140: Eddy Pineiro K 100% “safe to wait on K” · Baltimore Ravens DEF 100% “safe to wait on DEF” · Tyler Loop K “depth fallback (engine list exhausted)”
    03:14:58  ON THE CLOCK, pick 140 · plan #206 (0.0 s old) · lineup needs K DEF
    03:15:00  PICKED Eddy Pineiro (K) via action, confirmed in 991 ms — chose Eddy Pineiro (K): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left was Baker Mayfield
    03:15:03  plan #207 for pick 141: Baltimore Ravens DEF “fills your open DEF slot” · Los Angeles Chargers DEF “depth fallback (engine list exhausted)” · Green Bay Packers DEF “depth fallback (engine list exhausted)”
    03:15:03  ON THE CLOCK, pick 141 · plan #207 (0.0 s old) · lineup needs DEF
    03:15:05  pick 142  Tyler Loop (K) taken by seat 2 in 0 s INSTANTLY (autopick)
    03:15:05  PICKED Baltimore Ravens (DEF) via action, confirmed in 984 ms — chose Baltimore Ravens (DEF) to fill a mandatory slot; nothing the engine named was left; top projection left was Baker Mayfield, passed on purpose
    03:15:08  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    02:57:28 PT preflight: ok=true pick_path=action my_team=1 plan=plan 25 deep @pick 1 via store call#142
    02:57:28 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    02:57:28 PT NARR info driver started — seat 1, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    02:58:06 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~34 pts at RB (best option now 154, ~120 by your next turn) · 27% chance he's still there at your next pick · fills yo
    02:59:52 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pi
    02:59:58 PT ON CLOCK -> {"drafted":"Drake London","pos":"WR","vorp":51,"proj":193.1,"why":"waiting likely costs ~14 pts at WR (best option now 51, ~37 by your next turn) · 14% chance he's still there at your next pick · fills your open WR s
    03:01:31 PT heartbeat: setAwayStatus(false)
    03:01:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:02:10 PT ON CLOCK -> {"drafted":"D'Andre Swift","pos":"RB","vorp":21,"proj":181.2,"why":"safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after h
    03:02:16 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~11 pts at WR (best option now 24, ~13 by your next turn) · 11% chance he's still there at your next pick · fills your open WR
    03:04:56 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pai
    03:05:02 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~7 pts at your FLEX spot (best option now 9, ~2 by your next turn) · 52% chance he's still there at your next pick · fills a F
    03:05:38 PT heartbeat: setAwayStatus(false)
    03:05:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:07:33 PT ON CLOCK -> {"drafted":"Kyle Monangai","pos":"RB","vorp":-28.8,"proj":131.3,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.7/wk over the wire (Josh Jacobs) ≈ 103 pts · HANDCUFF: backs up your D'Andre Swift","
    03:07:39 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs
    03:09:38 PT heartbeat: setAwayStatus(false)
    03:09:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:10:37 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":1,"sr":1,"e":-10.6,"top_proj_ava
    03:10:43 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.784,"sr":0.784,"e":11.3,"top_pr
    03:13:30 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    03:13:30 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    03:13:39 PT heartbeat: setAwayStatus(false)
    03:13:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    03:15:00 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"safe to wait on K · 100% chance he's still there at your next pick · fills your open K slot · two-pick plan: pair with the ~32-pt RB expected at your n
    03:15:05 PT ON CLOCK -> {"drafted":"Baltimore Ravens","pos":"DEF","vorp":-2,"proj":115,"why":"fills your open DEF slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_pro
    03:15:08 PT roster full
    03:15:08 PT NARR info roster full — driver done; posting the trail when the room finishes
    03:15:08 PT driver stop


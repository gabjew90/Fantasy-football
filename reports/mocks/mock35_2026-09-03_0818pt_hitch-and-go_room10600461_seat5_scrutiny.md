# Scrutiny: Mock 35 -- Hitch and Go (room 10600461) -- Thursday 2026-09-03 08:18 PT -- 10 teams, our seat 5

Captured 2026-09-03 08:28:10 PT. Times below are Pacific. 10 teams, our team id 5, draft slot 5. 150 picks in the trail, 66 bridge plan calls, 53 recs events in the room log.

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
- Action latency to store confirmation: median 441 ms, min 296, max 537.
- Heartbeats 9; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (2): dropped 1 feed entries numbered >= header pick 32; dropped 1 feed entries numbered >= header pick 98.
- Away seats over the room (each change): {} -> {2} -> {2,4} -> {2,4,6} -> {2,4,6,10} -> {2,4,6,9,10} -> {2,4,6,8,9,10} -> {1,2,4,6,8,9,10} -> {1,2,3,4,6,8,9,10}.
- Managers away at the end: 1 Chris, 2 michael, 3 Kasey, 4 Hunter, 6 Derrick W, 8 Ron Berlin, 9 Lee, 10 Larry.

## Our picks, one block each

### Pick 5 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 36 points at RB, with a 48% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 517 ms, ranker engine, plan call 175, plan age 842 ms, at 08:18:42 PT.
- Engine's reason: waiting likely costs ~36 pts at RB (best option now 154, ~118 by your next turn) · 48% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 10 te
- Top projection available: Josh Allen -> took it: False.
- Passed on: Jaxon Smith-Njigba (WR, s=0.4, e=74.5); Trey McBride (TE, s=0.935, e=76.2); Josh Allen (QB, s=0.731, e=42.7).
- Plan call 175 @pick 5: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4], state store with 4 drafted / 0 mine.
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

### Pick 16 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 16 points at TE, with a 60% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 340 ms, ranker engine, plan call 182, plan age 669 ms, at 08:19:50 PT.
- Engine's reason: waiting likely costs ~16 pts at TE (best option now 78, ~62 by your next turn) · 60% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 8 teams
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=0.36, e=44.6); Derrick Henry (RB, s=0.39, e=43.7); Josh Allen (QB, s=0.427, e=37.9).
- Plan call 182 @pick 16: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 10], state store with 15 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.59 | 0.59 | 62.2 | 77.9 | waiting likely costs ~16 pts at TE (best option now 78, ~62 by your next turn) · 60% chanc |
| Drake London | WR | 51.0 | 0.36 | 0.36 | 44.6 | 51.0 | waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 36% chance |
| Derrick Henry | RB | 50.4 | 0.39 | 0.39 | 43.7 | 50.4 | waiting likely costs ~7 pts at RB (best option now 50, ~44 by your next turn) · 39% chance |
| Josh Allen | QB | 47.0 | 0.43 | 0.43 | 37.9 | 47.0 | waiting likely costs ~9 pts at QB (best option now 47, ~38 by your next turn) · 43% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 37.9 | 9.1 | 9 |
| RB | 50.4 | 43.7 | 6.7 | 19 |
| WR | 51.0 | 44.6 | 6.4 | 22 |
| TE | 77.9 | 62.2 | 15.7 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 50.44274023536681 | 44.1 | 6.3 | 49 |

### Pick 25 (round 3): Kyren Williams (RB)

- In plain English: Took Kyren Williams (RB) because waiting would likely cost about 9 points at RB, with a 39% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 411 ms, ranker engine, plan call 186, plan age 727 ms, at 08:20:30 PT.
- Engine's reason: waiting likely costs ~9 pts at RB (best option now 40, ~32 by your next turn) · 39% chance he's still there at your next pick · fills your open RB slot · 10 teams picking before you still need a RB · two-pick plan: pair 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Josh Allen (QB, s=0.783, e=43.3); Chris Olave (WR, s=None, e=None); Rashee Rice (WR, s=None, e=None).
- Plan call 186 @pick 25: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 10], state store with 24 drafted / 2 mine.
- Engine's first choice was **A.J. Brown** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| A.J. Brown | WR | 43.6 | 0.49 | 0.49 | 38.2 | 43.6 | waiting likely costs ~5 pts at WR (best option now 44, ~38 by your next turn) · 49% chance |
| Kyren Williams | RB | 40.5 | 0.39 | 0.39 | 31.5 | 40.5 | waiting likely costs ~9 pts at RB (best option now 40, ~32 by your next turn) · 39% chance |
| Josh Allen | QB | 47.0 | 0.78 | 0.78 | 43.3 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 78% chance |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake Maye | QB | 31.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.3 | 3.7 | 10 |
| RB | 40.5 | 31.5 | 9.0 | 16 |
| WR | 43.6 | 38.2 | 5.4 | 24 |
| TE | 23.8 | 23.5 | 0.3 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 31.7 | 8.9 | 47 |

### Pick 36 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 2 points at WR, with a 65% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 410 ms, ranker engine, plan call 194, plan age 725 ms, at 08:21:58 PT.
- Engine's reason: waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 65% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Cam Skattebo (RB, s=0.508, e=21.4); Drake Maye (QB, s=0.657, e=26.6); Zay Flowers (WR, s=None, e=None).
- Plan call 194 @pick 36: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 8, 9, 10], state store with 35 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.65 | 0.65 | 22.0 | 23.9 | waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 65% chance |
| Cam Skattebo | RB | 25.8 | 0.51 | 0.51 | 21.4 | 25.8 | waiting likely costs ~4 pts at your FLEX spot (best option now 26, ~21 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.66 | 0.66 | 26.6 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~27 by your next turn) · 66% chance |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.6 | 4.5 | 10 |
| RB | 25.8 | 21.3 | 4.5 | 17 |
| WR | 23.9 | 22.0 | 1.9 | 19 |
| TE | 23.8 | 22.8 | 1.0 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 25.84223678225652 | 21.4 | 4.5 | 44 |

### Pick 45 (round 5): Davante Adams (WR)

- In plain English: Took Davante Adams (WR) because waiting would likely cost about 2 points at WR, with a 55% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 502 ms, ranker engine, plan call 199, plan age 818 ms, at 08:22:45 PT.
- Engine's reason: waiting likely costs ~2 pts at WR (best option now 13, ~11 by your next turn) · 55% chance he's still there at your next pick · fills your open WR slot · 6 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.336, e=21.6); Jaylen Warren (RB, s=0.977, e=9.3); Jalen Hurts (QB, s=None, e=None).
- Plan call 199 @pick 45: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 8, 9, 10], state store with 44 drafted / 4 mine.
- Engine's first choice was **Davante Adams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Davante Adams | WR | 13.1 | 0.55 | 0.55 | 10.8 | 13.1 | waiting likely costs ~2 pts at WR (best option now 13, ~11 by your next turn) · 55% chance |
| Drake Maye | QB | 31.1 | 0.34 | 0.34 | 21.6 | 31.1 | waiting likely costs ~9 pts at QB (best option now 31, ~22 by your next turn) · 34% chance |
| Jaylen Warren | RB | 9.3 | 0.98 | 0.98 | 9.3 | 9.3 | safe to wait on your FLEX spot · 98% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 21.6 | 9.5 | 14 |
| RB | 9.3 | 9.3 | 0.0 | 15 |
| WR | 13.1 | 10.8 | 2.3 | 19 |
| TE | 23.8 | 21.7 | 2.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 42 |

### Pick 56 (round 6): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 5 points at QB, with a 63% chance he would still be there next turn.
- Driver: via **action**, verified store, 439 ms, ranker engine, plan call 203, plan age 756 ms, at 08:23:24 PT.
- Engine's reason: waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance he's still there at your next pick · fills your open QB slot · 8 teams picking before you still need a QB · 9 picks past his usua
- Top projection available: Drake Maye -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.958, e=9.2); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 203 @pick 56: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 8, 9, 10], state store with 55 drafted / 5 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.63 | 0.63 | 25.6 | 31.1 | waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance |
| Jaylen Warren | RB | 9.3 | 0.96 | 0.96 | 9.2 | 9.3 | safe to wait on your FLEX spot · 96% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 25.6 | 5.5 | 14 |
| RB | 9.3 | 9.2 | 0.1 | 15 |
| WR | 0.0 | -0.2 | 0.2 | 22 |
| TE | 21.1 | 20.4 | 0.7 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 46 |

### Pick 65 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 4 points at your FLEX spot, with a 60% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 537 ms, ranker engine, plan call 208, plan age 855 ms, at 08:24:12 PT.
- Engine's reason: waiting likely costs ~4 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 60% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None); Rome Odunze (WR, s=None, e=None).
- Plan call 208 @pick 65: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 6, 8, 9, 10], state store with 64 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.59 | 0.59 | 5.3 | 9.3 | waiting likely costs ~4 pts at your FLEX spot (best option now 9, ~5 by your next turn) ·  |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.4 | 2.3 | 17 |
| RB | 9.3 | 5.3 | 4.0 | 20 |
| WR | 0.0 | -0.5 | 0.5 | 27 |
| TE | 21.1 | 14.2 | 6.9 | 12 |
| K | 13.5 | 13.3 | 0.2 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 5.3 | 4.0 | 59 |

### Pick 76 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 96 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 494 ms, ranker engine, plan call 212, plan age 811 ms, at 08:24:52 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Mike Evans (WR, s=0.616, e=-5.2); TreVeyon Henderson (RB, s=None, e=None); RJ Harvey (RB, s=None, e=None).
- Plan call 212 @pick 76: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 6, 8, 9, 10], state store with 75 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.56 | 0.56 | 1.1 | 2.9 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacob |
| Mike Evans | WR | -2.4 | 0.62 | 0.62 | -5.2 | -2.4 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.2/wk over the wire (Rashod Bate |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.6 | 0.2 | 18 |
| RB | 2.9 | 1.1 | 1.8 | 34 |
| WR | -2.4 | -5.2 | 2.8 | 40 |
| TE | 13.8 | 13.6 | 0.2 | 18 |
| K | 13.5 | 12.9 | 0.6 | 11 |
| DEF | 18.0 | 17.8 | 0.2 | 8 |

### Pick 85 (round 9): Blake Corum (RB)

- In plain English: Lineup already full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.8 points a week over the waiver wire (Josh Jacobs), worth about 25 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 386 ms, ranker engine, plan call 215, plan age 709 ms, at 08:25:12 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Kyren Williams
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: DK Metcalf (WR, s=0.513, e=-9.9); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 215 @pick 85: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 6, 8, 9, 10], state store with 84 drafted / 8 mine.
- Engine's first choice was **Blake Corum** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Blake Corum | RB | -46.1 | 0.62 | 0.62 | -5.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8 |
| DK Metcalf | WR | -9.2 | 0.51 | 0.51 | -9.9 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.1 | 1.7 | 18 |
| RB | -5.4 | -5.5 | 0.1 | 29 |
| WR | -9.2 | -9.9 | 0.7 | 39 |
| TE | 13.8 | 12.7 | 1.1 | 18 |
| K | 13.5 | 12.9 | 0.6 | 12 |
| DEF | 18.0 | 16.9 | 1.1 | 11 |

### Pick 96 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 492 ms, ranker engine, plan call 219, plan age 823 ms, at 08:25:47 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.643, e=4.2); RJ Harvey (RB, s=0.741, e=-6); Kenny Gainwell (RB, s=None, e=None).
- Plan call 219 @pick 96: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 6, 8, 9, 10], state store with 95 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.98 | 0.98 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.64 | 0.64 | 4.2 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.74 | 0.74 | -6.0 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 4.2 | 8.6 | 15 |
| RB | -5.4 | -6.0 | 0.6 | 26 |
| WR | -10.6 | -10.6 | 0.0 | 36 |
| TE | 13.8 | 12.6 | 1.2 | 18 |
| K | 13.5 | 13.3 | 0.2 | 14 |
| DEF | 18.0 | 17.4 | 0.6 | 11 |

### Pick 105 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 296 ms, ranker engine, plan call 221, plan age 616 ms, at 08:25:56 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.865, e=-5.7); Courtland Sutton (WR, s=0.858, e=-11.5); Kenny Gainwell (RB, s=None, e=None).
- Plan call 221 @pick 105: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 6, 8, 9, 10], state store with 104 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.85 | 0.85 | 8.7 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.86 | 0.86 | -5.7 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.86 | 0.86 | -11.5 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Baker Mayfield | QB | -14.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 8.7 | 4.1 | 12 |
| RB | -5.4 | -5.7 | 0.3 | 24 |
| WR | -11.1 | -11.5 | 0.4 | 33 |
| TE | 10.9 | 10.2 | 0.7 | 17 |
| K | 13.5 | 13.4 | 0.1 | 15 |
| DEF | 18.0 | 17.4 | 0.6 | 13 |

### Pick 116 (round 12): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +9.1 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 441 ms, ranker engine, plan call 227, plan age 764 ms, at 08:26:56 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.993, e=-11.1); Michael Pittman Jr. (WR, s=None, e=None); Alec Pierce (WR, s=None, e=None).
- Plan call 227 @pick 116: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 6, 8, 9, 10], state store with 115 drafted / 11 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.98 | 0.98 | -6.6 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.99 | 0.99 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Alec Pierce | WR | -17.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 9 |
| RB | -6.2 | -6.6 | 0.4 | 22 |
| WR | -11.1 | -11.1 | 0.0 | 32 |
| TE | -2.4 | -2.5 | 0.1 | 12 |
| K | 13.5 | 13.5 | 0.0 | 16 |
| DEF | 18.0 | 17.8 | 0.2 | 14 |

### Pick 125 (round 13): Courtland Sutton (WR)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 466 ms, ranker engine, plan call 229, plan age 790 ms, at 08:27:06 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.982, e=-26); Michael Pittman Jr. (WR, s=None, e=None); Jakobi Meyers (WR, s=None, e=None).
- Plan call 229 @pick 125: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 6, 8, 9, 10], state store with 124 drafted / 12 mine.
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 1.00 | 1.00 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.98 | 0.98 | -26.0 | -25.9 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +7. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.6 | 0.1 | 8 |
| RB | -25.9 | -26.0 | 0.1 | 21 |
| WR | -11.1 | -11.1 | 0.0 | 28 |
| TE | -2.4 | -2.7 | 0.3 | 9 |
| K | 13.5 | 13.5 | 0.0 | 17 |
| DEF | 18.0 | 17.9 | 0.1 | 14 |

### Pick 136 (round 14): Seahawks (DEF)

- In plain English: Took Seattle Seahawks (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 456 ms, ranker engine, plan call 234, plan age 792 ms, at 08:27:55 PT.
- Engine's reason: safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · bargain: still here 56 picks after he's usually drafted · two-pick plan: pai
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Cameron Dicker (K, s=0.828, e=11.8); Ka'imi Fairbairn (K, s=None, e=None); Philadelphia Eagles (DEF, s=None, e=None).
- Plan call 234 @pick 136: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 6, 8, 9, 10], state store with 135 drafted / 13 mine.
- Engine's first choice was **Seattle Seahawks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Seattle Seahawks | DEF | 14.0 | 1.00 | 1.00 | 14.0 | 14.0 | safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF |
| Cameron Dicker | K | 10.5 | 0.83 | 0.83 | 11.8 | 12.0 | safe to wait on K · 83% chance he's still there at your next pick · fills your open K slot |
| Ka'imi Fairbairn | K | 12.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Philadelphia Eagles | DEF | 10.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Little | K | 9.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.5 | -16.6 | 0.1 | 8 |
| RB | -25.9 | -25.9 | 0.0 | 18 |
| WR | -21.5 | -21.6 | 0.1 | 24 |
| TE | -2.4 | -2.5 | 0.1 | 9 |
| K | 12.0 | 11.8 | 0.2 | 17 |
| DEF | 14.0 | 14.0 | 0.0 | 11 |

### Pick 145 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Daniel Jones; the engine passed on him on purpose.
- Driver: via **action**, verified store, 325 ms, ranker engine, plan call 236, plan age 676 ms, at 08:28:04 PT.
- Engine's reason: fills your open K slot
- Top projection available: Daniel Jones -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None).
- Plan call 236 @pick 145: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 3, 4, 6, 8, 9, 10], state store with 144 drafted / 14 mine.
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
| 30-50% | 22 | 41% | 23% |
| 50-70% | 27 | 61% | 37% |
| 70-90% | 39 | 80% | 54% |
| 90-100% | 44 | 97% | 91% |

132 predictions over 52 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    08:18:12  plan #171 for pick 2
  • Christian McCaffrey RB · wait costs 13 · 68% survives to our turn
  • Ja'Marr Chase WR · wait costs 5 · 72% survives to our turn
  • Trey McBride TE · safe to wait · 99% survives to our turn
    08:18:13  driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    08:18:34  pick 2  Bijan Robinson (RB) taken by seat 2 in 23 s — a target is gone
    08:18:38  plan #174 for pick 3
  • Christian McCaffrey RB · wait costs 14 · 74% survives to our turn
  • Ja'Marr Chase WR · wait costs 3 · 82% survives to our turn
  • Trey McBride TE · safe to wait · 100% survives to our turn
    08:18:39  pick 3  Ja'Marr Chase (WR) taken by seat 3 in 5 s — a target is gone (was 82% to survive)
    08:18:40  pick 4  Puka Nacua (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    08:18:41  plan #175 for pick 5
  • Christian McCaffrey RB · wait costs 36 · 48% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 15 · 40% survives to our turn
  • Trey McBride TE · wait costs 2 · 94% survives to our turn
    08:18:41  ON THE CLOCK, pick 5 · plan #175 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    08:18:42  PICKED Christian McCaffrey (RB) via action, confirmed in 517 ms — chose Christian McCaffrey (RB): waiting would likely cost about 36 points at RB, 48% to still be there next turn
  • top projection left was Josh Allen, passed on p
    08:18:44  pick 6  Jonathan Taylor (RB) taken by seat 6 in 2 s — a target is gone
    08:18:44  plan #176 for pick 7
  • Jaxon Smith-Njigba WR · wait costs 12 · 47% survives to our turn
  • De'Von Achane RB · wait costs 11 · 35% survives to our turn
  • Trey McBride TE · wait costs 1 · 95% survives to our turn
    08:18:52  pick 7  Jaxon Smith-Njigba (WR) taken by seat 7 in 8 s — a target is gone (was 47% to survive)
    08:18:56  plan #177 for pick 8
  • Amon-Ra St. Brown WR · wait costs 14 · 49% survives to our turn
  • De'Von Achane RB · wait costs 10 · 36% survives to our turn
  • Trey McBride TE · wait costs 1 · 94% survives to our turn
    08:18:56  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 4 s — a target is gone (was 49% to survive)
    08:19:08  plan #178 for pick 9
  • De'Von Achane RB · wait costs 9 · 40% survives to our turn
  • CeeDee Lamb WR · wait costs 3 · 46% survives to our turn
  • Trey McBride TE · safe to wait · 97% survives to our turn
    08:19:14  heartbeat sent (Yahoo told we are not idle)
    08:19:15  pick 9  CeeDee Lamb (WR) taken by seat 9 in 19 s — a target is gone (was 46% to survive)
    08:19:15  pick 10  James Cook III (RB) taken by seat 10 in 0 s INSTANTLY (autopick) — a target is gone
    08:19:16  pick 11  Chase Brown (RB) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    08:19:18  pick 12  De'Von Achane (RB) taken by seat 9 in 2 s INSTANTLY (autopick) — a target is gone (was 40% to survive)
    08:19:21  plan #179 for pick 13
  • Trey McBride TE · wait costs 1 · 96% survives to our turn
  • Justin Jefferson WR · wait costs 1 · 71% survives to our turn
  • Derrick Henry RB · wait costs 2 · 69% survives to our turn
    08:19:25  pick 13  Justin Jefferson (WR) taken by seat 8 in 7 s — a target is gone (was 71% to survive)
    08:19:33  plan #180 for pick 14
  • Drake London WR · wait costs 1 · 84% survives to our turn
  • Trey McBride TE · safe to wait · 98% survives to our turn
  • Derrick Henry RB · wait costs 1 · 75% survives to our turn
    08:19:49  pick 14  Nico Collins (WR) taken by seat 7 in 24 s — a target is gone
    08:19:49  pick 15  Saquon Barkley (RB) taken by seat 6 in 0 s INSTANTLY (autopick) — a target is gone
    08:19:50  plan #182 for pick 16
  • Trey McBride TE · wait costs 16 · 60% survives to our turn
  • Drake London WR · wait costs 6 · 36% survives to our turn
  • Derrick Henry RB · wait costs 7 · 39% survives to our turn
    08:19:50  ON THE CLOCK, pick 16 · plan #182 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    08:19:50  PICKED Trey McBride (TE) via action, confirmed in 340 ms — chose Trey McBride (TE): waiting would likely cost about 16 points at TE, 60% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    08:19:52  pick 17  Kenneth Walker III (RB) taken by seat 4 in 2 s
    08:19:53  plan #183 for pick 18
  • Drake London WR · wait costs 6 · 38% survives to our turn
  • Derrick Henry RB · wait costs 6 · 44% survives to our turn
  • Josh Allen QB · wait costs 9 · 46% survives to our turn
    08:20:05  pick 18  Omarion Hampton (RB) taken by seat 3 in 13 s — a target is gone
    08:20:06  pick 19  Derrick Henry (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 44% to survive)
    08:20:15  pick 20  Brock Bowers (TE) taken by seat 1 in 8 s
    08:20:15  heartbeat sent (Yahoo told we are not idle)
    08:20:18  plan #185 for pick 21
  • Drake London WR · wait costs 3 · 62% survives to our turn
  • Kyren Williams RB · wait costs 2 · 63% survives to our turn
  • Josh Allen QB · wait costs 6 · 63% survives to our turn
    08:20:21  pick 21  Javonte Williams (RB) taken by seat 1 in 6 s — a target is gone
    08:20:21  pick 22  Drake London (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone (was 62% to survive)
    08:20:29  pick 23  Ashton Jeanty (RB) taken by seat 3 in 8 s
    08:20:29  pick 24  George Pickens (WR) taken by seat 4 in 0 s INSTANTLY (autopick) — a target is gone
    08:20:30  plan #186 for pick 25
  • A.J. Brown WR · wait costs 5 · 49% survives to our turn
  • Kyren Williams RB · wait costs 9 · 39% survives to our turn
  • Josh Allen QB · wait costs 4 · 78% survives to our turn
    08:20:30  ON THE CLOCK, pick 25 · plan #186 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    08:20:30  PICKED Kyren Williams (RB) via action, confirmed in 411 ms — chose Kyren Williams (RB): waiting would likely cost about 9 points at RB, 39% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    08:20:32  pick 26  A.J. Brown (WR) taken by seat 6 in 2 s — a target is gone (was 49% to survive)
    08:20:33  plan #187 for pick 27
  • Chris Olave WR · wait costs 7 · 35% survives to our turn
  • Josh Allen QB · wait costs 3 · 80% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · 72% survives to our turn
    08:20:43  pick 27  Jeremiyah Love (RB) taken by seat 7 in 10 s
    08:20:45  plan #188 for pick 28
  • Chris Olave WR · wait costs 7 · 36% survives to our turn
  • Josh Allen QB · wait costs 3 · 84% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · 75% survives to our turn
    08:20:50  pick 28  Josh Allen (QB) taken by seat 8 in 7 s — a target is gone (was 84% to survive)
    08:20:57  plan #189 for pick 29
  • Chris Olave WR · wait costs 7 · 38% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · 82% survives to our turn
  • Drake Maye QB · safe to wait · 95% survives to our turn
    08:21:16  heartbeat sent (Yahoo told we are not idle)
    08:21:19  pick 29  Malik Nabers (WR) taken by seat 9 in 29 s — a target is gone
    08:21:20  pick 30  Chris Olave (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone (was 38% to survive)
    08:21:21  pick 31  Breece Hall (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:21:22  pick 32  DeVonta Smith (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    08:21:23  plan #191 for pick 32
  • Rashee Rice WR · wait costs 4 · 59% survives to our turn
  • Travis Etienne Jr. RB · safe to wait · 86% survives to our turn
  • Drake Maye QB · safe to wait · 97% survives to our turn
    08:21:23  bridge warning: dropped 1 feed entries numbered >= header pick 32
    08:21:29  pick 33  Travis Etienne Jr. (RB) taken by seat 8 in 7 s — a target is gone (was 86% to survive)
    08:21:35  plan #192 for pick 34
  • Rashee Rice WR · wait costs 2 · 77% survives to our turn
  • Cam Skattebo RB · safe to wait · 87% survives to our turn
  • Drake Maye QB · safe to wait · 98% survives to our turn
    08:21:56  pick 34  Rashee Rice (WR) taken by seat 7 in 27 s — a target is gone (was 77% to survive)
    08:21:56  pick 35  Tee Higgins (WR) taken by seat 6 in 0 s INSTANTLY (autopick)
    08:21:57  plan #194 for pick 36
  • Garrett Wilson WR · wait costs 2 · 65% survives to our turn
  • Cam Skattebo RB · wait costs 4 · 51% survives to our turn
  • Drake Maye QB · wait costs 5 · 66% survives to our turn
    08:21:57  ON THE CLOCK, pick 36 · plan #194 (0.0 s old) · lineup needs QB WRx2 FLEX K DEF
    08:21:58  PICKED Garrett Wilson (WR) via action, confirmed in 410 ms — chose Garrett Wilson (WR): waiting would likely cost about 2 points at WR, 65% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    08:22:00  pick 37  Zay Flowers (WR) taken by seat 4 in 2 s — a target is gone
    08:22:00  plan #195 for pick 38
  • Cam Skattebo RB · wait costs 4 · 54% survives to our turn
  • Tetairoa McMillan WR · wait costs 1 · 48% survives to our turn
  • Drake Maye QB · wait costs 6 · 58% survives to our turn
    08:22:10  pick 38  Jaylen Waddle (WR) taken by seat 3 in 10 s — a target is gone
    08:22:10  pick 39  Colston Loveland (TE) taken by seat 2 in 0 s INSTANTLY (autopick)
    08:22:13  plan #196 for pick 40
  • Cam Skattebo RB · wait costs 3 · 59% survives to our turn
  • Tetairoa McMillan WR · safe to wait · 63% survives to our turn
  • Drake Maye QB · wait costs 4 · 67% survives to our turn
    08:22:17  heartbeat sent (Yahoo told we are not idle)
    08:22:22  pick 40  David Montgomery (RB) taken by seat 1 in 13 s
    08:22:25  plan #197 for pick 41
  • Cam Skattebo RB · wait costs 3 · 67% survives to our turn
  • Tetairoa McMillan WR · safe to wait · 73% survives to our turn
  • Drake Maye QB · wait costs 4 · 69% survives to our turn
    08:22:40  pick 41  Terry McLaurin (WR) taken by seat 1 in 18 s
    08:22:40  pick 42  Tetairoa McMillan (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone (was 73% to survive)
    08:22:43  pick 43  D'Andre Swift (RB) taken by seat 3 in 3 s — a target is gone
    08:22:44  pick 44  Cam Skattebo (RB) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 67% to survive)
    08:22:44  plan #199 for pick 45
  • Davante Adams WR · wait costs 2 · 55% survives to our turn
  • Drake Maye QB · wait costs 9 · 34% survives to our turn
  • Jaylen Warren RB · safe to wait · 98% survives to our turn
    08:22:44  ON THE CLOCK, pick 45 · plan #199 (0.0 s old) · lineup needs QB WR FLEX K DEF
    08:22:45  PICKED Davante Adams (WR) via action, confirmed in 502 ms — chose Davante Adams (WR): waiting would likely cost about 2 points at WR, 55% to still be there next turn
  • top projection left was Drake Maye, passed on purpose
    08:22:47  pick 46  Tyler Warren (TE) taken by seat 6 in 2 s
    08:22:48  plan #200 for pick 47
  • Drake Maye QB · wait costs 9 · 38% survives to our turn
  • Jaylen Warren RB · safe to wait · 98% survives to our turn
  • Jalen Hurts QB · depth fallback, engine list done
    08:23:03  pick 47  Bucky Irving (RB) taken by seat 7 in 15 s
    08:23:04  pick 48  Ladd McConkey (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    08:23:04  pick 49  Lamar Jackson (QB) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:23:05  pick 50  Emeka Egbuka (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    08:23:06  pick 51  Tucker Kraft (TE) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:23:07  pick 52  Bhayshul Tuten (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:23:08  pick 53  Quinshon Judkins (RB) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:23:13  plan #202 for pick 54
  • Drake Maye QB · wait costs 2 · 85% survives to our turn
  • Jaylen Warren RB · safe to wait · 99% survives to our turn
  • Jalen Hurts QB · depth fallback, engine list done
    08:23:17  heartbeat sent (Yahoo told we are not idle)
    08:23:22  pick 54  Joe Burrow (QB) taken by seat 7 in 14 s
    08:23:22  pick 55  Jadarian Price (RB) taken by seat 6 in 0 s INSTANTLY (autopick)
    08:23:23  plan #203 for pick 56
  • Drake Maye QB · wait costs 5 · 63% survives to our turn
  • Jaylen Warren RB · safe to wait · 96% survives to our turn
  • Jalen Hurts QB · depth fallback, engine list done
    08:23:23  ON THE CLOCK, pick 56 · plan #203 (0.0 s old) · lineup needs QB FLEX K DEF
    08:23:24  PICKED Drake Maye (QB) via action, confirmed in 439 ms — chose Drake Maye (QB): waiting would likely cost about 5 points at QB, 63% to still be there next turn
    08:23:26  pick 57  Jayden Daniels (QB) taken by seat 4 in 2 s
    08:23:26  plan #204 for pick 58
  • Jaylen Warren RB · safe to wait · 95% survives to our turn
  • Rhamondre Stevenson RB · depth fallback, engine list done
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:23:33  pick 58  Jalen Hurts (QB) taken by seat 3 in 7 s
    08:23:33  pick 59  Rhamondre Stevenson (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:23:38  plan #205 for pick 60
  • Jaylen Warren RB · safe to wait · 95% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
  • Jameson Williams WR · depth fallback, engine list done
    08:23:48  pick 60  Justin Herbert (QB) taken by seat 1 in 14 s
    08:23:51  plan #206 for pick 61
  • Jaylen Warren RB · safe to wait · 97% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
  • Jameson Williams WR · depth fallback, engine list done
    08:24:03  pick 61  Luther Burden III (WR) taken by seat 1 in 15 s
    08:24:03  plan #207 for pick 62
  • Jaylen Warren RB · safe to wait · 98% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
  • Jameson Williams WR · depth fallback, engine list done
    08:24:03  pick 62  Caleb Williams (QB) taken by seat 2 in 0 s INSTANTLY (autopick)
    08:24:11  pick 63  Sam LaPorta (TE) taken by seat 3 in 8 s
    08:24:11  pick 64  Harold Fannin Jr. (TE) taken by seat 4 in 0 s INSTANTLY (autopick)
    08:24:11  plan #208 for pick 65
  • Jaylen Warren RB · wait costs 4 · 60% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
  • Jameson Williams WR · depth fallback, engine list done
    08:24:11  ON THE CLOCK, pick 65 · plan #208 (0.0 s old) · lineup needs FLEX K DEF
    08:24:12  PICKED Jaylen Warren (RB) via action, confirmed in 537 ms — chose Jaylen Warren (RB): waiting would likely cost about 4 points at your FLEX spot, 60% to still be there next turn
  • top projection left was Trevor Lawrence, passed 
    08:24:14  pick 66  Dak Prescott (QB) taken by seat 6 in 2 s
    08:24:15  plan #209 for pick 67
  • Rico Dowdle RB · insurance worth ~96 · 87% survives to our turn
  • Jameson Williams WR · insurance worth ~21 · 53% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:24:17  heartbeat sent (Yahoo told we are not idle)
    08:24:35  pick 67  DJ Moore (WR) taken by seat 7 in 20 s — a target is gone
    08:24:36  pick 68  Kyle Pitts Sr. (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:24:37  pick 69  George Kittle (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:24:37  pick 70  Trevor Lawrence (QB) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:24:38  pick 71  Rome Odunze (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    08:24:39  pick 72  Jameson Williams (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone (was 53% to survive)
    08:24:40  plan #211 for pick 73
  • Rico Dowdle RB · insurance worth ~96 · 92% survives to our turn
  • Christian Watson WR · insurance worth ~21 · 75% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:24:44  pick 73  Christian Watson (WR) taken by seat 8 in 4 s — a target is gone (was 75% to survive)
    08:24:50  pick 74  Dalton Kincaid (TE) taken by seat 7 in 7 s
    08:24:50  pick 75  Parker Washington (WR) taken by seat 6 in 0 s INSTANTLY (autopick) — a target is gone
    08:24:51  plan #212 for pick 76
  • Rico Dowdle RB · insurance worth ~96 · 56% survives to our turn
  • Mike Evans WR · insurance worth ~20 · 62% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:24:51  ON THE CLOCK, pick 76 · plan #212 (0.0 s old) · lineup needs K DEF
    08:24:52  PICKED Rico Dowdle (RB) via action, confirmed in 494 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +10.0 a week over the wire, about 96 points
  • he also backs up one of ou
    08:24:54  pick 77  Mike Evans (WR) taken by seat 4 in 2 s — a target is gone (was 62% to survive)
    08:24:55  plan #213 for pick 78
  • Blake Corum RB · insurance worth ~25 · 91% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 49% survives to our turn
  • TreVeyon Henderson RB · depth fallback, engine list done
    08:25:04  pick 78  Carnell Tate (WR) taken by seat 3 in 10 s — a target is gone
    08:25:05  pick 79  TreVeyon Henderson (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:06  pick 80  MarShawn Lloyd (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:25:07  pick 81  Marvin Harrison Jr. (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:07  plan #214 for pick 82
  • Blake Corum RB · insurance worth ~25 · 92% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 74% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    08:25:10  pick 82  Brian Thomas Jr. (WR) taken by seat 2 in 3 s
    08:25:10  pick 83  Tony Pollard (RB) taken by seat 3 in 0 s
    08:25:10  pick 84  Jonathon Brooks (RB) taken by seat 4 in 0 s
    08:25:11  plan #215 for pick 85
  • Blake Corum RB · insurance worth ~25 · 62% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 51% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    08:25:11  ON THE CLOCK, pick 85 · plan #215 (0.0 s old) · lineup needs K DEF
    08:25:12  PICKED Blake Corum (RB) via action, confirmed in 386 ms — lineup full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +9.8 a week over the wire, about 25 points
  • he also backs up one of our
    08:25:14  pick 86  DK Metcalf (WR) taken by seat 6 in 2 s — a target is gone (was 51% to survive)
    08:25:15  plan #216 for pick 87
  • Wan'Dale Robinson WR · insurance worth ~17 · 99% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 83% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:25:18  heartbeat sent (Yahoo told we are not idle)
    08:25:26  pick 87  J.K. Dobbins (RB) taken by seat 7 in 12 s
    08:25:26  pick 88  Chris Godwin Jr. (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:27  plan #217 for pick 89
  • Wan'Dale Robinson WR · insurance worth ~17 · 100% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 88% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:25:27  pick 89  Michael Wilson (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:28  pick 90  Josh Downs (WR) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:25:29  pick 91  Chuba Hubbard (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:25:30  pick 92  Jacory Croskey-Merritt (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:25:31  pick 93  Brock Purdy (QB) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:25:39  plan #218 for pick 94
  • Wan'Dale Robinson WR · insurance worth ~17 · 100% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 94% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 94% survives to our
    08:25:45  pick 94  Matthew Stafford (QB) taken by seat 7 in 14 s — a target is gone
    08:25:46  pick 95  Bo Nix (QB) taken by seat 6 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:46  plan #219 for pick 96
  • Wan'Dale Robinson WR · insurance worth ~17 · 98% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 64% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 74% survives to our 
    08:25:46  ON THE CLOCK, pick 96 · plan #219 (0.0 s old) · lineup needs K DEF
    08:25:47  PICKED Wan'Dale Robinson (WR) via action, confirmed in 492 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points
  • top projection 
    08:25:49  pick 97  Quentin Johnston (WR) taken by seat 4 in 2 s
    08:25:49  pick 98  Stefon Diggs (WR) taken by seat 3 in 0 s
    08:25:50  plan #220 for pick 98
  • Patrick Mahomes II QB · insurance worth ~8 · 74% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 81% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 70% survives to our tu
    08:25:50  bridge warning: dropped 1 feed entries numbered >= header pick 98
    08:25:50  pick 99  Jordan Mason (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:25:51  pick 100  Jaxson Dart (QB) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:52  pick 101  Josh Jacobs (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    08:25:53  pick 102  Kyler Murray (QB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:54  pick 103  Jared Goff (QB) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone
    08:25:55  pick 104  Dallas Goedert (TE) taken by seat 4 in 1 s INSTANTLY (autopick)
    08:25:56  plan #221 for pick 105
  • Patrick Mahomes II QB · insurance worth ~8 · 85% survives to our turn
  • RJ Harvey RB · insurance worth ~2 · 87% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 86% survives to our t
    08:25:56  ON THE CLOCK, pick 105 · plan #221 (0.0 s old) · lineup needs K DEF
    08:25:56  PICKED Patrick Mahomes II (QB) via action, confirmed in 296 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    08:25:58  pick 106  Kyle Monangai (RB) taken by seat 6 in 2 s
    08:25:59  plan #222 for pick 107
  • RJ Harvey RB · insurance worth ~2 · 87% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 89% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    08:26:19  heartbeat sent (Yahoo told we are not idle)
    08:26:20  pick 107  KC Concepcion (WR) taken by seat 7 in 22 s
    08:26:21  pick 108  RJ Harvey (RB) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 87% to survive)
    08:26:22  pick 109  Travis Kelce (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:26:23  pick 110  Jordan Love (QB) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:26:24  plan #224 for pick 111
  • Kenny Gainwell RB · insurance worth ~2 · 98% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:26:25  pick 111  Isaiah Likely (TE) taken by seat 10 in 2 s INSTANTLY (autopick)
    08:26:25  pick 112  Malik Willis (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    08:26:26  pick 113  Mark Andrews (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:26:36  plan #225 for pick 114
  • Kenny Gainwell RB · insurance worth ~2 · 99% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 100% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:26:53  pick 114  Juwan Johnson (TE) taken by seat 7 in 28 s
    08:26:54  pick 115  Jake Ferguson (TE) taken by seat 6 in 1 s INSTANTLY (autopick)
    08:26:55  plan #227 for pick 116
  • Kenny Gainwell RB · insurance worth ~2 · 98% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:26:55  ON THE CLOCK, pick 116 · plan #227 (0.0 s old) · lineup needs K DEF
    08:26:56  PICKED Kenny Gainwell (RB) via action, confirmed in 441 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +9.1 a week over the wire, about 2 points
  • top projection left wa
    08:26:58  pick 117  Baker Mayfield (QB) taken by seat 4 in 2 s
    08:26:58  pick 118  Dalton Schultz (TE) taken by seat 3 in 0 s
    08:26:58  pick 119  Chig Okonkwo (TE) taken by seat 2 in 0 s
    08:26:59  plan #228 for pick 120
  • Courtland Sutton WR · insurance worth ~2 · 100% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 99% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:27:00  pick 120  Terrance Ferguson (TE) taken by seat 1 in 2 s INSTANTLY (autopick)
    08:27:00  pick 121  De'Zhaun Stribling (WR) taken by seat 1 in 0 s INSTANTLY (autopick)
    08:27:01  pick 122  Jordan Addison (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:27:02  pick 123  Jayden Reed (WR) taken by seat 3 in 1 s INSTANTLY (autopick)
    08:27:03  pick 124  Alec Pierce (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    08:27:05  plan #229 for pick 125
  • Courtland Sutton WR · insurance worth ~2 · 100% survives to our turn
  • Aaron Jones Sr. RB · insurance worth ~0 · 98% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    08:27:05  ON THE CLOCK, pick 125 · plan #229 (0.0 s old) · lineup needs K DEF
    08:27:06  PICKED Courtland Sutton (WR) via action, confirmed in 466 ms — lineup full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.7 a week over the wire, about 2 points
  • top projection lef
    08:27:08  pick 126  Matthew Golden (WR) taken by seat 6 in 2 s
    08:27:08  plan #230 for pick 127
  • Houston Texans DEF · safe to wait · 97% survives to our turn
  • Ka'imi Fairbairn K · safe to wait · 76% survives to our turn
  • Denver Broncos DEF · depth fallback, engine list done
    08:27:19  heartbeat sent (Yahoo told we are not idle)
    08:27:27  pick 127  Chris Rodriguez Jr. (RB) taken by seat 7 in 19 s
    08:27:28  pick 128  Michael Pittman Jr. (WR) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:27:28  pick 129  Makai Lemon (WR) taken by seat 9 in 1 s INSTANTLY (autopick)
    08:27:29  pick 130  Rachaad White (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:27:30  pick 131  Texans (DEF) taken by seat 10 in 1 s INSTANTLY (autopick)
    08:27:31  pick 132  Brandon Aubrey (K) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    08:27:32  pick 133  Rams (DEF) taken by seat 8 in 1 s INSTANTLY (autopick)
    08:27:32  plan #232 for pick 134
  • Denver Broncos DEF · safe to wait · 99% survives to our turn
  • Cameron Dicker K · safe to wait · 94% survives to our turn
  • Seattle Seahawks DEF · depth fallback, engine list done
    08:27:53  pick 134  Mike Washington Jr. (RB) taken by seat 7 in 21 s
    08:27:54  pick 135  Broncos (DEF) taken by seat 6 in 1 s INSTANTLY (autopick)
    08:27:54  plan #234 for pick 136
  • Seattle Seahawks DEF · safe to wait · 100% survives to our turn
  • Cameron Dicker K · safe to wait · 83% survives to our turn
  • Ka'imi Fairbairn K · depth fallback, engine list done
    08:27:54  ON THE CLOCK, pick 136 · plan #234 (0.0 s old) · lineup needs K DEF
    08:27:55  PICKED Seattle Seahawks (DEF) via action, confirmed in 456 ms — chose Seattle Seahawks (DEF): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for)
  • top projection left was
    08:27:57  pick 137  Ka'imi Fairbairn (K) taken by seat 4 in 2 s — a target is gone
    08:27:57  pick 138  Eagles (DEF) taken by seat 3 in 0 s
    08:27:58  plan #235 for pick 139
  • Cam Little K · safe to wait · 77% survives to our turn
  • Cameron Dicker K · depth fallback, engine list done
  • Jason Myers K · depth fallback, engine list done
    08:27:58  pick 139  Cameron Dicker (K) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    08:28:00  pick 140  Jason Myers (K) taken by seat 1 in 2 s — a target is gone
    08:28:00  pick 141  Vikings (DEF) taken by seat 1 in 0 s
    08:28:01  pick 142  Jaguars (DEF) taken by seat 2 in 1 s INSTANTLY (autopick)
    08:28:02  pick 143  Cam Little (K) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone (was 77% to survive)
    08:28:03  pick 144  Patriots (DEF) taken by seat 4 in 1 s INSTANTLY (autopick)
    08:28:03  plan #236 for pick 145
  • Eddy Pineiro K
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    08:28:03  ON THE CLOCK, pick 145 · plan #236 (0.0 s old) · lineup needs K
    08:28:04  PICKED Eddy Pineiro (K) via action, confirmed in 325 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Daniel Jones, passed on purpose
    08:28:06  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    08:18:13 PT preflight: ok=true pick_path=action my_team=5 plan=plan 25 deep @pick 2 via store call#171
    08:18:13 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    08:18:13 PT NARR info driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    08:18:42 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~36 pts at RB (best option now 154, ~118 by your next turn) · 48% chance he's still there at your next pick · fills yo
    08:19:14 PT heartbeat: setAwayStatus(false)
    08:19:14 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:19:50 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~16 pts at TE (best option now 78, ~62 by your next turn) · 60% chance he's still there at your next pick · fills your open TE
    08:20:15 PT heartbeat: setAwayStatus(false)
    08:20:15 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:20:30 PT ON CLOCK -> {"drafted":"Kyren Williams","pos":"RB","vorp":40.5,"proj":200.7,"why":"waiting likely costs ~9 pts at RB (best option now 40, ~32 by your next turn) · 39% chance he's still there at your next pick · fills your open R
    08:21:16 PT heartbeat: setAwayStatus(false)
    08:21:16 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:21:23 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 32
    08:21:58 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~2 pts at WR (best option now 24, ~22 by your next turn) · 65% chance he's still there at your next pick · fills your open WR 
    08:22:17 PT heartbeat: setAwayStatus(false)
    08:22:17 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:22:45 PT ON CLOCK -> {"drafted":"Davante Adams","pos":"WR","vorp":13.1,"proj":155.2,"why":"waiting likely costs ~2 pts at WR (best option now 13, ~11 by your next turn) · 55% chance he's still there at your next pick · fills your open WR
    08:23:17 PT heartbeat: setAwayStatus(false)
    08:23:17 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:23:24 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~5 pts at QB (best option now 31, ~26 by your next turn) · 63% chance he's still there at your next pick · fills your open QB sl
    08:24:12 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~4 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 60% chance he's still there at your next pick · fills a F
    08:24:17 PT heartbeat: setAwayStatus(false)
    08:24:17 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:24:52 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren","s":0.
    08:25:12 PT ON CLOCK -> {"drafted":"Blake Corum","pos":"RB","vorp":-46.1,"proj":114.1,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: back
    08:25:18 PT heartbeat: setAwayStatus(false)
    08:25:18 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:25:47 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.984,"sr":0.984,"e":-10.6,"top_
    08:25:50 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 98
    08:25:56 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.854,"sr":0.854,"e":8.7,"top_pro
    08:26:19 PT heartbeat: setAwayStatus(false)
    08:26:19 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:26:56 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.982,"
    08:27:06 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.99
    08:27:19 PT heartbeat: setAwayStatus(false)
    08:27:19 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    08:27:55 PT ON CLOCK -> {"drafted":"Seattle Seahawks","pos":"DEF","vorp":14,"proj":131,"why":"safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF slot · 8 teams picking before you still need a DEF · ba
    08:28:04 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Daniel Jones","p":"QB","proj":257.1,"vorp":-16.5},"took_top_projection":
    08:28:06 PT roster full
    08:28:06 PT NARR info roster full — driver done; posting the trail when the room finishes
    08:28:06 PT driver stop


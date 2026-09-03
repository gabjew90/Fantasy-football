# Scrutiny: Mock 33 -- Intentional Grounding (room 10597994) -- Thursday 2026-09-03 07:07 PT -- 10 teams, our seat 5

Captured 2026-09-03 07:23:17 PT. Times below are Pacific. 10 teams, our team id 5, draft slot 5. 150 picks in the trail, 90 bridge plan calls, 72 recs events in the room log.

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
- Action latency to store confirmation: median 404 ms, min 320, max 517.
- Heartbeats 14; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (2): 1 drafted entries matched no board player: 126 Kayshon Boutte; 2 drafted entries matched no board player: 126 Kayshon Boutte, 144 Will Reichard.
- Away seats over the room (each change): {} -> {2} -> {2,6} -> {2,9} -> {2,4,9} -> {2,4,7,9} -> {2,4,9}.
- Managers away at the end: 2 Bryson Teixeira, 3 stupak, 4 Ben, 9 Calvin.

## Our picks, one block each

### Pick 5 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 38 points at RB, with a 46% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 413 ms, ranker engine, plan call 8, plan age 740 ms, at 07:08:24 PT.
- Engine's reason: waiting likely costs ~38 pts at RB (best option now 154, ~116 by your next turn) · 46% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 10 te
- Top projection available: Josh Allen -> took it: False.
- Passed on: Jaxon Smith-Njigba (WR, s=0.421, e=75.5); Trey McBride (TE, s=0.933, e=76); Josh Allen (QB, s=0.75, e=43).
- Plan call 8 @pick 5: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2], state store with 4 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Christian McCaffrey | RB | 154.2 | 0.46 | 0.46 | 116.1 | 154.2 | waiting likely costs ~38 pts at RB (best option now 154, ~116 by your next turn) · 46% cha |
| Jaxon Smith-Njigba | WR | 89.4 | 0.42 | 0.42 | 75.5 | 89.4 | waiting likely costs ~14 pts at WR (best option now 89, ~76 by your next turn) · 42% chanc |
| Trey McBride | TE | 77.9 | 0.93 | 0.93 | 76.0 | 77.9 | waiting likely costs ~2 pts at TE (best option now 78, ~76 by your next turn) · 93% chance |
| Josh Allen | QB | 47.0 | 0.75 | 0.75 | 43.0 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 75% chance |
| Jonathan Taylor | RB | 104.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Amon-Ra St. Brown | WR | 81.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.0 | 4.0 | 6 |
| RB | 154.2 | 116.1 | 38.1 | 23 |
| WR | 89.4 | 75.5 | 13.9 | 23 |
| TE | 77.9 | 76.0 | 1.9 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 154.24360475819503 | 117.2 | 37.0 | 52 |

### Pick 16 (round 2): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 14 points at TE, with a 63% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 426 ms, ranker engine, plan call 14, plan age 754 ms, at 07:09:29 PT.
- Engine's reason: waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 63% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 8 teams
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Justin Jefferson (WR, s=0.669, e=51.2); Kyren Williams (RB, s=0.642, e=39.3); Josh Allen (QB, s=0.475, e=38.6).
- Plan call 14 @pick 16: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 9], state store with 15 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.63 | 0.63 | 64.3 | 77.9 | waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 63% chanc |
| Justin Jefferson | WR | 53.9 | 0.67 | 0.67 | 51.2 | 53.9 | waiting likely costs ~3 pts at WR (best option now 54, ~51 by your next turn) · 67% chance |
| Kyren Williams | RB | 40.5 | 0.64 | 0.64 | 39.3 | 40.5 | waiting likely costs ~1 pts at RB (best option now 40, ~39 by your next turn) · 64% chance |
| Josh Allen | QB | 47.0 | 0.47 | 0.47 | 38.6 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 48% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Drake London | WR | 51.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.6 | 8.4 | 9 |
| RB | 40.5 | 39.3 | 1.2 | 17 |
| WR | 53.9 | 51.2 | 2.7 | 24 |
| TE | 77.9 | 64.3 | 13.6 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 40.1 | 0.5 | 49 |

### Pick 25 (round 3): Kyren Williams (RB)

- In plain English: Took Kyren Williams (RB) because waiting would likely cost about 5 points at RB, with a 45% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 517 ms, ranker engine, plan call 19, plan age 844 ms, at 07:10:23 PT.
- Engine's reason: waiting likely costs ~5 pts at RB (best option now 40, ~35 by your next turn) · 45% chance he's still there at your next pick · fills your open RB slot · 10 teams picking before you still need a RB · two-pick plan: pair 
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Josh Allen (QB, s=0.766, e=43); Chris Olave (WR, s=None, e=None); Javonte Williams (RB, s=None, e=None).
- Plan call 19 @pick 25: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 9], state store with 24 drafted / 2 mine.
- Engine's first choice was **A.J. Brown** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| A.J. Brown | WR | 43.6 | 0.50 | 0.50 | 38.5 | 43.6 | waiting likely costs ~5 pts at WR (best option now 44, ~39 by your next turn) · 50% chance |
| Kyren Williams | RB | 40.5 | 0.45 | 0.45 | 35.5 | 40.5 | waiting likely costs ~5 pts at RB (best option now 40, ~35 by your next turn) · 45% chance |
| Josh Allen | QB | 47.0 | 0.77 | 0.77 | 43.0 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 77% chance |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.0 | 4.0 | 10 |
| RB | 40.5 | 35.5 | 5.0 | 16 |
| WR | 43.6 | 38.5 | 5.1 | 24 |
| TE | 23.8 | 23.5 | 0.3 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 35.6 | 5.0 | 47 |

### Pick 36 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 1 points at WR, with a 70% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 474 ms, ranker engine, plan call 25, plan age 794 ms, at 07:11:25 PT.
- Engine's reason: waiting likely costs ~1 pts at WR (best option now 24, ~23 by your next turn) · 70% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.551, e=23.3); Drake Maye (QB, s=0.671, e=26.7); Cam Skattebo (RB, s=None, e=None).
- Plan call 25 @pick 36: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 9], state store with 35 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.70 | 0.70 | 22.6 | 23.9 | waiting likely costs ~1 pts at WR (best option now 24, ~23 by your next turn) · 70% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.55 | 0.55 | 23.3 | 26.3 | waiting likely costs ~3 pts at your FLEX spot (best option now 26, ~23 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.67 | 0.67 | 26.7 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 67% chance |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.7 | 4.4 | 9 |
| RB | 26.3 | 23.2 | 3.1 | 18 |
| WR | 23.9 | 22.6 | 1.3 | 19 |
| TE | 23.8 | 22.9 | 0.9 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 23.3 | 3.1 | 45 |

### Pick 45 (round 5): Davante Adams (WR)

- In plain English: Took Davante Adams (WR) because waiting would likely cost about 3 points at WR, with a 61% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 384 ms, ranker engine, plan call 32, plan age 707 ms, at 07:12:35 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 61% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.547, e=24.8); Jaylen Warren (RB, s=0.929, e=9.1); Jalen Hurts (QB, s=None, e=None).
- Plan call 32 @pick 45: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 44 drafted / 4 mine.
- Engine's first choice was **Davante Adams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Davante Adams | WR | 13.1 | 0.61 | 0.61 | 10.3 | 13.1 | waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 61% chance |
| Drake Maye | QB | 31.1 | 0.55 | 0.55 | 24.8 | 31.1 | waiting likely costs ~6 pts at QB (best option now 31, ~25 by your next turn) · 55% chance |
| Jaylen Warren | RB | 9.3 | 0.93 | 0.93 | 9.1 | 9.3 | safe to wait on your FLEX spot · 93% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 24.8 | 6.3 | 13 |
| RB | 9.3 | 9.1 | 0.2 | 16 |
| WR | 13.1 | 10.3 | 2.8 | 19 |
| TE | 23.8 | 22.0 | 1.8 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 43 |

### Pick 56 (round 6): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 4 points at QB, with a 70% chance he would still be there next turn.
- Driver: via **action**, verified store, 320 ms, ranker engine, plan call 39, plan age 641 ms, at 07:13:52 PT.
- Engine's reason: waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 70% chance he's still there at your next pick · fills your open QB slot · 8 teams picking before you still need a QB · 9 picks past his usua
- Top projection available: Drake Maye -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.936, e=9.2); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 39 @pick 56: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 55 drafted / 5 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.69 | 0.69 | 26.6 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 70% chance |
| Jaylen Warren | RB | 9.3 | 0.94 | 0.94 | 9.2 | 9.3 | safe to wait on your FLEX spot · 94% chance he's still there at your next pick · fills a F |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.6 | 4.5 | 14 |
| RB | 9.3 | 9.2 | 0.1 | 19 |
| WR | 3.0 | 2.5 | 0.5 | 20 |
| TE | 21.1 | 20.6 | 0.5 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.2 | 0.1 | 48 |

### Pick 65 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 54% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 413 ms, ranker engine, plan call 46, plan age 730 ms, at 07:15:01 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~7 by your next turn) · 54% chance he's still there at your next pick · fills a FLEX slot · 4 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); Quinshon Judkins (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None).
- Plan call 46 @pick 65: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 64 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.54 | 0.54 | 7.5 | 9.3 | waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~7 by your next turn) ·  |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quinshon Judkins | RB | 3.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Mike Evans | WR | -2.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.7 | 1.0 | 18 |
| RB | 9.3 | 7.5 | 1.8 | 23 |
| WR | -0.8 | -1.6 | 0.8 | 24 |
| TE | 21.1 | 19.0 | 2.1 | 13 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 7.5 | 1.8 | 60 |

### Pick 76 (round 8): Rico Dowdle (RB)

- In plain English: Lineup already full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +10.0 points a week over the waiver wire (Josh Jacobs), worth about 96 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 404 ms, ranker engine, plan call 54, plan age 723 ms, at 07:16:26 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Mike Evans (WR, s=0.776, e=-4); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 54 @pick 76: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 7, 9], state store with 75 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -11.0 | 0.67 | 0.67 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacob |
| Mike Evans | WR | -2.4 | 0.78 | 0.78 | -4.0 | -2.4 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.2/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.5 | 1.2 | 21 |
| RB | -5.4 | -5.4 | 0.0 | 32 |
| WR | -2.4 | -4.0 | 1.6 | 38 |
| TE | 21.1 | 19.7 | 1.4 | 21 |
| K | 13.5 | 13.1 | 0.4 | 11 |
| DEF | 16.0 | 15.7 | 0.3 | 7 |

### Pick 85 (round 9): Blake Corum (RB)

- In plain English: Lineup already full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.8 points a week over the waiver wire (Josh Jacobs), worth about 25 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 453 ms, ranker engine, plan call 58, plan age 774 ms, at 07:17:04 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Kyren Williams
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.736, e=-9.6); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 58 @pick 85: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 7, 9], state store with 84 drafted / 8 mine.
- Engine's first choice was **Blake Corum** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Blake Corum | RB | -46.1 | 0.80 | 0.80 | -5.5 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8 |
| DK Metcalf | WR | -9.2 | 0.74 | 0.74 | -9.6 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.6 | 2.1 | 19 |
| RB | -5.4 | -5.5 | 0.1 | 29 |
| WR | -9.2 | -9.6 | 0.4 | 38 |
| TE | 19.8 | 17.7 | 2.1 | 20 |
| K | 13.5 | 13.2 | 0.3 | 12 |
| DEF | 16.0 | 15.6 | 0.4 | 10 |

### Pick 96 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 385 ms, ranker engine, plan call 63, plan age 709 ms, at 07:17:55 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.748, e=10.5); RJ Harvey (RB, s=0.8, e=-5.9); Bo Nix (QB, s=None, e=None).
- Plan call 63 @pick 96: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 7, 9], state store with 95 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.97 | 0.97 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.75 | 0.75 | 10.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.80 | 0.80 | -5.9 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.5 | 2.3 | 17 |
| RB | -5.4 | -5.9 | 0.5 | 28 |
| WR | -10.6 | -10.6 | 0.0 | 34 |
| TE | 13.8 | 12.8 | 1.0 | 18 |
| K | 13.5 | 13.4 | 0.1 | 14 |
| DEF | 16.0 | 15.7 | 0.3 | 10 |

### Pick 105 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 492 ms, ranker engine, plan call 70, plan age 834 ms, at 07:19:04 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: RJ Harvey (RB, s=0.867, e=-5.9); Courtland Sutton (WR, s=0.894, e=-11.4); Bo Nix (QB, s=None, e=None).
- Plan call 70 @pick 105: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 7, 9], state store with 104 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.89 | 0.89 | 11.7 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| RJ Harvey | RB | -5.4 | 0.87 | 0.87 | -5.9 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.89 | 0.89 | -11.4 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.7 | 1.1 | 15 |
| RB | -5.4 | -5.9 | 0.5 | 25 |
| WR | -11.1 | -11.4 | 0.3 | 32 |
| TE | 0.5 | 0.2 | 0.3 | 16 |
| K | 13.5 | 13.4 | 0.1 | 15 |
| DEF | 16.0 | 15.7 | 0.3 | 12 |

### Pick 116 (round 12): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +9.1 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 364 ms, ranker engine, plan call 76, plan age 693 ms, at 07:20:06 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Courtland Sutton (WR, s=0.982, e=-11.2); Kenny Gainwell (RB, s=None, e=None); Quentin Johnston (WR, s=None, e=None).
- Plan call 76 @pick 116: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 115 drafted / 11 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.97 | 0.97 | -5.4 | -5.4 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.98 | 0.98 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Quentin Johnston | WR | -15.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -11.9 | 0.1 | 11 |
| RB | -5.4 | -5.4 | 0.0 | 23 |
| WR | -11.1 | -11.2 | 0.1 | 31 |
| TE | 0.5 | 0.4 | 0.1 | 15 |
| K | 13.5 | 13.4 | 0.1 | 15 |
| DEF | 14.0 | 13.8 | 0.2 | 11 |

### Pick 125 (round 13): Jakobi Meyers (WR)

- In plain English: Lineup already full, so Jakobi Meyers (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.1 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 394 ms, ranker engine, plan call 80, plan age 728 ms, at 07:20:47 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.951, e=-7.2); Jordan Addison (WR, s=None, e=None); Aaron Jones Sr. (RB, s=None, e=None).
- Plan call 80 @pick 125: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 124 drafted / 12 mine.
- Engine's first choice was **Jakobi Meyers** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jakobi Meyers | WR | -21.5 | 0.92 | 0.92 | -21.7 | -21.5 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1 |
| Kenny Gainwell | RB | -6.2 | 0.95 | 0.95 | -7.2 | -6.2 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +9. |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Jayden Reed | WR | -28.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 11 |
| RB | -6.2 | -7.2 | 1.0 | 22 |
| WR | -21.5 | -21.7 | 0.2 | 28 |
| TE | 0.5 | 0.4 | 0.1 | 13 |
| K | 13.5 | 13.3 | 0.2 | 15 |
| DEF | 8.0 | 7.8 | 0.2 | 9 |

### Pick 136 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (64% to survive, but nobody better was worth waiting for). The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 358 ms, ranker engine, plan call 86, plan age 711 ms, at 07:21:53 PT.
- Engine's reason: safe to wait on DEF · 64% chance he's still there at your next pick · fills your open DEF slot · 4 teams picking before you still need a DEF · two-pick plan: pair with the ~44-pt RB expected at your next turn
- Top projection available: Jared Goff -> took it: False.
- Passed on: Eddy Pineiro (K, s=0.784, e=5.6); Tyler Loop (K, s=None, e=None); New England Patriots (DEF, s=None, e=None).
- Plan call 86 @pick 136: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 135 drafted / 13 mine, warnings ['1 drafted entries matched no board player: 126 Kayshon Boutte'].
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.64 | 0.64 | 5.1 | 6.0 | safe to wait on DEF · 64% chance he's still there at your next pick · fills your open DEF  |
| Eddy Pineiro | K | 6.0 | 0.78 | 0.78 | 5.6 | 6.0 | safe to wait on K · 78% chance he's still there at your next pick · fills your open K slot |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| New England Patriots | DEF | 4.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jacksonville Jaguars | DEF | 2.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -11.9 | 0.1 | 11 |
| RB | -6.2 | -6.9 | 0.7 | 21 |
| WR | -27.4 | -27.4 | 0.0 | 24 |
| TE | 0.5 | 0.3 | 0.2 | 12 |
| K | 6.0 | 5.6 | 0.4 | 13 |
| DEF | 6.0 | 5.1 | 0.9 | 8 |

### Pick 145 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 396 ms, ranker engine, plan call 90, plan age 752 ms, at 07:22:24 PT.
- Engine's reason: fills your open K slot
- Top projection available: Jared Goff -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Andy Borregales (K, s=None, e=None).
- Plan call 90 @pick 145: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [2, 4, 9], state store with 144 drafted / 14 mine, warnings ['2 drafted entries matched no board player: 126 Kayshon Boutte, 144 Will Reichard'].
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | - | - | - | - | fills your open K slot |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Cairo Santos | K | 1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Harrison Mevis | K | -4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 30-50% | 11 | 44% | 27% |
| 50-70% | 30 | 62% | 47% |
| 70-90% | 59 | 81% | 76% |
| 90-100% | 67 | 96% | 84% |

167 predictions over 71 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T07:21:02   WARNING plan #82: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:21:15   WARNING plan #83: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:21:27   WARNING plan #84: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:21:40   WARNING plan #85: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:21:53   WARNING plan #86: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:21:56   WARNING plan #87: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:22:08   WARNING plan #88: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:22:21   WARNING plan #89: 1 drafted entries matched no board player: 126 Kayshon Boutte
    2026-09-03T07:22:23   WARNING plan #90: 2 drafted entries matched no board player: 126 Kayshon Boutte, 144 Will Reichard

## Narration (what the panel showed live, Pacific time)

    07:07:16  plan #1 for pick 1: Christian McCaffrey RB 65% “waiting likely costs ~11 pts at RB (best opt” · Ja'Marr Chase WR 64% “waiting likely costs ~7 pts at WR (best opti” · Trey McBride TE 99% “safe to wait on TE”
    07:07:17  driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    07:08:07  pick 1  Bijan Robinson (RB) taken by seat 1 — a target is gone
    07:08:07  plan #6 for pick 2: Christian McCaffrey RB 68% “waiting likely costs ~11 pts at RB (best opt” · Ja'Marr Chase WR 70% “waiting likely costs ~6 pts at WR (best opti” · Trey McBride TE 99% “safe to wait on TE”
    07:08:08  pick 2  Jahmyr Gibbs (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    07:08:14  pick 3  Puka Nacua (WR) taken by seat 3 in 6 s — a target is gone
    07:08:18  heartbeat sent (Yahoo told we are not idle)
    07:08:19  plan #7 for pick 4: Christian McCaffrey RB 87% “waiting likely costs ~7 pts at your FLEX spo” · Ja'Marr Chase WR 91% “waiting likely costs ~2 pts at WR (best opti” · Trey McBride TE 99% “safe to wait on TE”
    07:08:22  pick 4  Ja'Marr Chase (WR) taken by seat 4 in 8 s — a target is gone (was 91% to survive)
    07:08:23  plan #8 for pick 5: Christian McCaffrey RB 46% “waiting likely costs ~38 pts at RB (best opt” · Jaxon Smith-Njigba WR 42% “waiting likely costs ~14 pts at WR (best opt” · Trey McBride TE 93% “waiting likely costs ~2 pts at TE (bes
    07:08:23  ON THE CLOCK, pick 5 · plan #8 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    07:08:24  PICKED Christian McCaffrey (RB) via action, confirmed in 413 ms — chose Christian McCaffrey (RB): waiting would likely cost about 38 points at RB, 46% to still be there next turn; top projection left was Josh Allen, passed on purp
    07:08:27  plan #9 for pick 6: Jonathan Taylor RB 40% “waiting likely costs ~25 pts at RB (best opt” · Jaxon Smith-Njigba WR 40% “waiting likely costs ~15 pts at WR (best opt” · Trey McBride TE 92% “waiting likely costs ~2 pts at TE (best op
    07:08:27  pick 6  Amon-Ra St. Brown (WR) taken by seat 6 in 3 s — a target is gone
    07:08:31  pick 7  James Cook III (RB) taken by seat 7 in 4 s — a target is gone
    07:08:35  pick 8  Jonathan Taylor (RB) taken by seat 8 in 4 s — a target is gone (was 40% to survive)
    07:08:39  plan #10 for pick 9: Jaxon Smith-Njigba WR 56% “waiting likely costs ~16 pts at WR (best opt” · De'Von Achane RB 46% “waiting likely costs ~10 pts at RB (best opt” · Trey McBride TE 94% “waiting likely costs ~2 pts at TE (best opt
    07:09:04  pick 9  Jaxon Smith-Njigba (WR) taken by seat 9 in 30 s — a target is gone (was 58% to survive)
    07:09:08  pick 10  Kenneth Walker III (RB) taken by seat 10 in 4 s
    07:09:13  pick 11  De'Von Achane (RB) taken by seat 10 in 4 s — a target is gone (was 41% to survive)
    07:09:13  pick 12  Saquon Barkley (RB) taken by seat 9 in 0 s INSTANTLY (autopick)
    07:09:15  pick 13  CeeDee Lamb (WR) taken by seat 8 in 3 s — a target is gone
    07:09:17  plan #13 for pick 14: Chase Brown RB 77% “waiting likely costs ~3 pts at RB (best opti” · Trey McBride TE 95% “safe to wait on TE” · Justin Jefferson WR 82% “safe to wait on WR”
    07:09:21  heartbeat sent (Yahoo told we are not idle)
    07:09:22  pick 14  Chase Brown (RB) taken by seat 7 in 7 s — a target is gone (was 77% to survive)
    07:09:28  pick 15  Derrick Henry (RB) taken by seat 6 in 5 s — a target is gone
    07:09:28  plan #14 for pick 16: Trey McBride TE 63% “waiting likely costs ~14 pts at TE (best opt” · Justin Jefferson WR 67% “waiting likely costs ~3 pts at WR (best opti” · Kyren Williams RB 64% “waiting likely costs ~1 pts at RB (best opt
    07:09:28  ON THE CLOCK, pick 16 · plan #14 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    07:09:29  PICKED Trey McBride (TE) via action, confirmed in 426 ms — chose Trey McBride (TE): waiting would likely cost about 14 points at TE, 63% to still be there next turn; top projection left was Josh Allen, passed on purpose
    07:09:32  plan #15 for pick 17: Justin Jefferson WR 65% “waiting likely costs ~3 pts at WR (best opti” · Kyren Williams RB 63% “waiting likely costs ~1 pts at RB (best opti” · Josh Allen QB 44% “waiting likely costs ~9 pts at QB (best opti”
    07:09:42  pick 17  Justin Jefferson (WR) taken by seat 4 in 13 s — a target is gone (was 65% to survive)
    07:09:44  plan #16 for pick 18: Drake London WR 40% “waiting likely costs ~6 pts at WR (best opti” · Kyren Williams RB 69% “safe to wait on RB” · Josh Allen QB 48% “waiting likely costs ~8 pts at QB (best opti”
    07:09:51  pick 18  Omarion Hampton (RB) taken by seat 3 in 10 s — a target is gone
    07:09:51  pick 19  Nico Collins (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    07:09:56  pick 20  Drake London (WR) taken by seat 1 in 5 s — a target is gone (was 40% to survive)
    07:09:56  plan #17 for pick 21: A.J. Brown WR 56% “waiting likely costs ~2 pts at WR (best opti” · Kyren Williams RB 78% “safe to wait on your FLEX spot” · Josh Allen QB 68% “waiting likely costs ~5 pts at QB (best opti”
    07:10:00  pick 21  Ashton Jeanty (RB) taken by seat 1 in 4 s — a target is gone
    07:10:00  pick 22  Brock Bowers (TE) taken by seat 2 in 0 s
    07:10:09  plan #18 for pick 23: A.J. Brown WR 81% “safe to wait on WR” · Kyren Williams RB 85% “safe to wait on your FLEX spot” · Josh Allen QB 88% “waiting likely costs ~2 pts at QB (best opti”
    07:10:10  pick 23  George Pickens (WR) taken by seat 3 in 10 s — a target is gone
    07:10:21  pick 24  Jeremiyah Love (RB) taken by seat 4 in 11 s
    07:10:21  heartbeat sent (Yahoo told we are not idle)
    07:10:22  plan #19 for pick 25: A.J. Brown WR 50% “waiting likely costs ~5 pts at WR (best opti” · Kyren Williams RB 45% “waiting likely costs ~5 pts at RB (best opti” · Josh Allen QB 77% “waiting likely costs ~4 pts at QB (best opti”
    07:10:22  ON THE CLOCK, pick 25 · plan #19 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    07:10:23  PICKED Kyren Williams (RB) via action, confirmed in 517 ms — chose Kyren Williams (RB): waiting would likely cost about 5 points at RB, 45% to still be there next turn; top projection left was Josh Allen, passed on purpose
    07:10:25  pick 26  Javonte Williams (RB) taken by seat 6 in 2 s — a target is gone
    07:10:26  plan #20 for pick 27: A.J. Brown WR 54% “waiting likely costs ~5 pts at WR (best opti” · Josh Allen QB 77% “waiting likely costs ~4 pts at QB (best opti” · Travis Etienne Jr. RB 74% “safe to wait on your FLEX spot”
    07:10:33  pick 27  Chris Olave (WR) taken by seat 7 in 8 s — a target is gone
    07:10:37  pick 28  D'Andre Swift (RB) taken by seat 8 in 4 s
    07:10:38  pick 29  A.J. Brown (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone (was 54% to survive)
    07:10:38  plan #21 for pick 30: Rashee Rice WR 52% “waiting likely costs ~4 pts at WR (best opti” · Josh Allen QB 90% “waiting likely costs ~2 pts at QB (best opti” · Travis Etienne Jr. RB 79% “safe to wait on your FLEX spot”
    07:10:44  pick 30  Josh Allen (QB) taken by seat 10 in 6 s — a target is gone (was 90% to survive)
    07:10:44  pick 31  Jaylen Waddle (WR) taken by seat 10 in 1 s INSTANTLY (autopick)
    07:10:45  pick 32  Malik Nabers (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    07:10:50  plan #22 for pick 33: Rashee Rice WR 78% “waiting likely costs ~2 pts at WR (best opti” · Travis Etienne Jr. RB 89% “safe to wait on your FLEX spot” · Drake Maye QB 93% “safe to wait on QB”
    07:11:12  pick 33  DeVonta Smith (WR) taken by seat 8 in 27 s — a target is gone
    07:11:14  plan #24 for pick 34: Rashee Rice WR 83% “waiting likely costs ~2 pts at WR (best opti” · Travis Etienne Jr. RB 93% “safe to wait on your FLEX spot” · Drake Maye QB 96% “safe to wait on QB”
    07:11:21  pick 34  Joe Burrow (QB) taken by seat 7 in 9 s
    07:11:21  heartbeat sent (Yahoo told we are not idle)
    07:11:23  pick 35  Rashee Rice (WR) taken by seat 6 in 2 s INSTANTLY (autopick) — a target is gone (was 83% to survive)
    07:11:24  plan #25 for pick 36: Garrett Wilson WR 71% “waiting likely costs ~1 pts at WR (best opti” · Travis Etienne Jr. RB 55% “waiting likely costs ~3 pts at your FLEX spo” · Drake Maye QB 67% “waiting likely costs ~4 pts at QB (best opt
    07:11:24  ON THE CLOCK, pick 36 · plan #25 (0.0 s old) · lineup needs QB WRx2 FLEX K DEF
    07:11:25  PICKED Garrett Wilson (WR) via action, confirmed in 474 ms — chose Garrett Wilson (WR): waiting would likely cost about 1 points at WR, 71% to still be there next turn; top projection left was Drake Maye, passed on purpose
    07:11:27  plan #26 for pick 37: Travis Etienne Jr. RB 55% “waiting likely costs ~3 pts at your FLEX spo” · Zay Flowers WR 54% “waiting likely costs ~3 pts at WR (best opti” · Drake Maye QB 64% “waiting likely costs ~5 pts at QB (best opti”
    07:11:55  pick 37  Tee Higgins (WR) taken by seat 4 in 30 s — a target is gone
    07:12:04  pick 38  Travis Etienne Jr. (RB) taken by seat 3 in 9 s — a target is gone (was 55% to survive)
    07:12:04  plan #29 for pick 39: Cam Skattebo RB 49% “waiting likely costs ~8 pts at your FLEX spo” · Zay Flowers WR 65% “waiting likely costs ~3 pts at WR (best opti” · Drake Maye QB 64% “waiting likely costs ~5 pts at QB (best opti”
    07:12:04  pick 39  Breece Hall (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    07:12:09  pick 40  Zay Flowers (WR) taken by seat 1 in 4 s — a target is gone (was 65% to survive)
    07:12:13  pick 41  Tetairoa McMillan (WR) taken by seat 1 in 5 s — a target is gone
    07:12:13  pick 42  Ladd McConkey (WR) taken by seat 2 in 0 s INSTANTLY (autopick)
    07:12:16  plan #30 for pick 43: Cam Skattebo RB 74% “waiting likely costs ~4 pts at your FLEX spo” · Davante Adams WR 95% “safe to wait on WR” · Drake Maye QB 80% “waiting likely costs ~3 pts at QB (best opti”
    07:12:21  heartbeat sent (Yahoo told we are not idle)
    07:12:33  pick 43  Cam Skattebo (RB) taken by seat 3 in 20 s — a target is gone (was 74% to survive)
    07:12:34  pick 44  Colston Loveland (TE) taken by seat 4 in 1 s INSTANTLY (autopick)
    07:12:34  plan #32 for pick 45: Davante Adams WR 61% “waiting likely costs ~3 pts at WR (best opti” · Drake Maye QB 55% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 93% “safe to wait on your FLEX spot”
    07:12:34  ON THE CLOCK, pick 45 · plan #32 (0.0 s old) · lineup needs QB WR FLEX K DEF
    07:12:35  PICKED Davante Adams (WR) via action, confirmed in 384 ms — chose Davante Adams (WR): waiting would likely cost about 3 points at WR, 61% to still be there next turn; top projection left was Drake Maye, passed on purpose
    07:12:38  plan #33 for pick 46: Drake Maye QB 57% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 92% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:12:44  pick 46  DJ Moore (WR) taken by seat 6 in 9 s
    07:12:51  plan #34 for pick 47: Drake Maye QB 55% “waiting likely costs ~6 pts at QB (best opti” · Jaylen Warren RB 94% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:13:05  pick 47  Romeo Doubs (WR) taken by seat 7 in 21 s
    07:13:12  pick 48  Emeka Egbuka (WR) taken by seat 8 in 6 s — a target is gone
    07:13:12  pick 49  Tyler Warren (TE) taken by seat 9 in 0 s INSTANTLY (autopick)
    07:13:16  plan #36 for pick 50: Drake Maye QB 73% “waiting likely costs ~4 pts at QB (best opti” · Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:13:20  pick 50  Luther Burden III (WR) taken by seat 10 in 8 s
    07:13:22  heartbeat sent (Yahoo told we are not idle)
    07:13:29  plan #37 for pick 51: Drake Maye QB 75% “waiting likely costs ~3 pts at QB (best opti” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:13:32  pick 51  David Montgomery (RB) taken by seat 10 in 12 s
    07:13:33  pick 52  Lamar Jackson (QB) taken by seat 9 in 1 s INSTANTLY (autopick)
    07:13:36  pick 53  Tucker Kraft (TE) taken by seat 8 in 4 s
    07:13:41  plan #38 for pick 54: Drake Maye QB 92% “waiting likely costs ~1 pts at QB (best opti” · Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:13:44  pick 54  Colby Parkinson (TE) taken by seat 7 in 8 s
    07:13:50  pick 55  Rome Odunze (WR) taken by seat 6 in 6 s
    07:13:52  plan #39 for pick 56: Drake Maye QB 70% “waiting likely costs ~4 pts at QB (best opti” · Jaylen Warren RB 94% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:13:52  ON THE CLOCK, pick 56 · plan #39 (0.0 s old) · lineup needs QB FLEX K DEF
    07:13:52  PICKED Drake Maye (QB) via action, confirmed in 320 ms — chose Drake Maye (QB): waiting would likely cost about 4 points at QB, 70% to still be there next turn
    07:13:54  pick 57  Bucky Irving (RB) taken by seat 4 in 2 s
    07:13:55  plan #40 for pick 58: Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    07:14:09  pick 58  Terry McLaurin (WR) taken by seat 3 in 14 s — a target is gone
    07:14:10  pick 59  Bhayshul Tuten (RB) taken by seat 2 in 1 s INSTANTLY (autopick)
    07:14:20  plan #42 for pick 60: Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    07:14:22  heartbeat sent (Yahoo told we are not idle)
    07:14:26  pick 60  Caleb Williams (QB) taken by seat 1 in 16 s
    07:14:32  plan #43 for pick 61: Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    07:14:35  pick 61  Jameson Williams (WR) taken by seat 1 in 9 s — a target is gone
    07:14:35  pick 62  Jayden Daniels (QB) taken by seat 2 in 0 s INSTANTLY (autopick)
    07:14:45  plan #44 for pick 63: Jaylen Warren RB 99% “safe to wait on your FLEX spot” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    07:14:58  pick 63  Harold Fannin Jr. (TE) taken by seat 3 in 23 s
    07:14:59  pick 64  Jalen Hurts (QB) taken by seat 4 in 1 s INSTANTLY (autopick)
    07:15:00  plan #46 for pick 65: Jaylen Warren RB 54% “waiting likely costs ~2 pts at your FLEX spo” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · Quinshon Judkins RB “depth fallback (engine list exhausted)”
    07:15:00  ON THE CLOCK, pick 65 · plan #46 (0.0 s old) · lineup needs FLEX K DEF
    07:15:01  PICKED Jaylen Warren (RB) via action, confirmed in 413 ms — chose Jaylen Warren (RB): waiting would likely cost about 2 points at your FLEX spot, 54% to still be there next turn; top projection left was Trevor Lawrence, passed on 
    07:15:04  plan #47 for pick 66: Rico Dowdle RB 79% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 68% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:15:11  pick 66  Jadarian Price (RB) taken by seat 6 in 11 s
    07:15:16  plan #48 for pick 67: Rico Dowdle RB 79% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 69% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:15:23  heartbeat sent (Yahoo told we are not idle)
    07:15:26  pick 67  Texans (DEF) taken by seat 7 in 14 s
    07:15:28  pick 68  Christian Watson (WR) taken by seat 8 in 2 s INSTANTLY (autopick) — a target is gone (was 69% to survive)
    07:15:28  plan #49 for pick 69: Rico Dowdle RB 82% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 74% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:15:28  pick 69  Quinshon Judkins (RB) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    07:15:38  pick 70  Sam LaPorta (TE) taken by seat 10 in 9 s
    07:15:39  pick 71  Jonathon Brooks (RB) taken by seat 10 in 2 s INSTANTLY (autopick)
    07:15:39  pick 72  Parker Washington (WR) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone
    07:15:41  plan #50 for pick 73: Rico Dowdle RB 92% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 91% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:15:43  pick 73  Rhamondre Stevenson (RB) taken by seat 8 in 3 s — a target is gone
    07:15:54  plan #51 for pick 74: Rico Dowdle RB 93% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 95% “bench insurance: covers 2 WR starters ~6.5 w” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    07:16:12  pick 74  TreVeyon Henderson (RB) taken by seat 7 in 30 s — a target is gone
    07:16:18  plan #53 for pick 75: Rico Dowdle RB 99% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:16:24  heartbeat sent (Yahoo told we are not idle)
    07:16:25  pick 75  Brian Thomas Jr. (WR) taken by seat 6 in 13 s
    07:16:26  plan #54 for pick 76: Rico Dowdle RB 67% “bench insurance: covers 3 RB starters ~9.6 w” · Mike Evans WR 78% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:16:26  ON THE CLOCK, pick 76 · plan #54 (0.0 s old) · lineup needs K DEF
    07:16:26  PICKED Rico Dowdle (RB) via action, confirmed in 404 ms — lineup full, so Rico Dowdle (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +10.0 a week over the wire, about 96 points; he also backs up one of our s
    07:16:28  pick 77  Mike Evans (WR) taken by seat 4 in 2 s — a target is gone (was 78% to survive)
    07:16:29  plan #55 for pick 78: Blake Corum RB 91% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 68% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:16:46  pick 78  Tony Pollard (RB) taken by seat 3 in 17 s
    07:16:46  pick 79  Marvin Harrison Jr. (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    07:16:48  pick 80  Kyle Pitts Sr. (TE) taken by seat 1 in 2 s INSTANTLY (autopick)
    07:16:53  plan #57 for pick 81: Blake Corum RB 93% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 77% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:16:56  pick 81  MarShawn Lloyd (RB) taken by seat 1 in 9 s
    07:16:56  pick 82  Carnell Tate (WR) taken by seat 2 in 0 s — a target is gone
    07:17:01  pick 83  Dak Prescott (QB) taken by seat 3 in 5 s
    07:17:02  pick 84  Justin Herbert (QB) taken by seat 4 in 1 s INSTANTLY (autopick)
    07:17:03  plan #58 for pick 85: Blake Corum RB 80% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 74% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:17:03  ON THE CLOCK, pick 85 · plan #58 (0.0 s old) · lineup needs K DEF
    07:17:04  PICKED Blake Corum (RB) via action, confirmed in 453 ms — lineup full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +9.8 a week over the wire, about 25 points; he also backs up one of our st
    07:17:07  plan #59 for pick 86: DK Metcalf WR 72% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 88% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:17:17  pick 86  George Kittle (TE) taken by seat 6 in 13 s
    07:17:17  pick 87  DK Metcalf (WR) taken by seat 7 in 0 s INSTANTLY (autopick) — a target is gone (was 72% to survive)
    07:17:20  plan #60 for pick 88: Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 90% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:17:24  heartbeat sent (Yahoo told we are not idle)
    07:17:26  pick 88  Trevor Lawrence (QB) taken by seat 8 in 9 s
    07:17:27  pick 89  Chris Godwin Jr. (WR) taken by seat 9 in 1 s INSTANTLY (autopick) — a target is gone
    07:17:32  plan #61 for pick 90: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 90% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:17:38  pick 90  Stefon Diggs (WR) taken by seat 10 in 11 s
    07:17:44  plan #62 for pick 91: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 82% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 93% “bench insurance: covers 3 RB starters beh
    07:17:47  pick 91  Alec Pierce (WR) taken by seat 10 in 10 s
    07:17:47  pick 92  J.K. Dobbins (RB) taken by seat 9 in 0 s INSTANTLY (autopick)
    07:17:50  pick 93  Dalton Kincaid (TE) taken by seat 8 in 3 s
    07:17:50  pick 94  Michael Wilson (WR) taken by seat 7 in 0 s INSTANTLY (autopick)
    07:17:54  pick 95  Matthew Stafford (QB) taken by seat 6 in 4 s — a target is gone
    07:17:55  plan #63 for pick 96: Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 75% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 80% “bench insurance: covers 3 RB starters beh
    07:17:55  ON THE CLOCK, pick 96 · plan #63 (0.0 s old) · lineup needs K DEF
    07:17:55  PICKED Wan'Dale Robinson (WR) via action, confirmed in 385 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    07:17:58  pick 97  Josh Downs (WR) taken by seat 4 in 2 s
    07:17:58  plan #64 for pick 98: Patrick Mahomes II QB 79% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 82% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 79% “bench insurance: covers 2 WR starters behi
    07:18:23  pick 98  Travis Kelce (TE) taken by seat 3 in 26 s
    07:18:23  pick 99  Chuba Hubbard (RB) taken by seat 2 in 0 s INSTANTLY (autopick)
    07:18:24  plan #66 for pick 100: Patrick Mahomes II QB 87% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 88% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 84% “bench insurance: covers 2 WR starters beh
    07:18:25  heartbeat sent (Yahoo told we are not idle)
    07:18:36  pick 100  Jacory Croskey-Merritt (RB) taken by seat 1 in 13 s
    07:18:36  plan #67 for pick 101: Patrick Mahomes II QB 90% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 89% “bench insurance: covers 2 WR starters beh
    07:18:46  pick 101  Dallas Goedert (TE) taken by seat 1 in 10 s
    07:18:46  pick 102  Brock Purdy (QB) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    07:18:49  plan #68 for pick 103: Patrick Mahomes II QB 95% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 92% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 96% “bench insurance: covers 2 WR starters beh
    07:19:02  pick 103  Jaxson Dart (QB) taken by seat 3 in 16 s — a target is gone
    07:19:02  pick 104  Jordan Mason (RB) taken by seat 4 in 0 s INSTANTLY (autopick)
    07:19:03  plan #70 for pick 105: Patrick Mahomes II QB 89% “bench insurance: covers 1 QB starter ~3.6 wk” · RJ Harvey RB 87% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 89% “bench insurance: covers 2 WR starters beh
    07:19:03  ON THE CLOCK, pick 105 · plan #70 (0.0 s old) · lineup needs K DEF
    07:19:04  PICKED Patrick Mahomes II (QB) via action, confirmed in 492 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    07:19:07  plan #71 for pick 106: RJ Harvey RB 87% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 90% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:19:14  pick 106  Ka'imi Fairbairn (K) taken by seat 6 in 11 s
    07:19:14  pick 107  Bo Nix (QB) taken by seat 7 in 0 s INSTANTLY (autopick)
    07:19:19  plan #72 for pick 108: RJ Harvey RB 91% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 94% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:19:25  heartbeat sent (Yahoo told we are not idle)
    07:19:28  pick 108  Baker Mayfield (QB) taken by seat 8 in 13 s
    07:19:28  pick 109  Kyler Murray (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    07:19:31  plan #73 for pick 110: RJ Harvey RB 98% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 97% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:19:41  pick 110  Michael Pittman Jr. (WR) taken by seat 10 in 14 s — a target is gone
    07:19:43  pick 111  Rams (DEF) taken by seat 10 in 2 s INSTANTLY (autopick)
    07:19:43  plan #74 for pick 112: RJ Harvey RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 98% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:19:44  pick 112  Isaiah Likely (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    07:19:49  pick 113  Josh Jacobs (RB) taken by seat 8 in 6 s
    07:19:50  pick 114  Kyle Monangai (RB) taken by seat 7 in 1 s INSTANTLY (autopick)
    07:19:56  plan #75 for pick 115: RJ Harvey RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:20:04  pick 115  Broncos (DEF) taken by seat 6 in 14 s
    07:20:05  plan #76 for pick 116: RJ Harvey RB 97% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 98% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:20:05  ON THE CLOCK, pick 116 · plan #76 (0.0 s old) · lineup needs K DEF
    07:20:06  PICKED RJ Harvey (RB) via action, confirmed in 364 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +9.1 a week over the wire, about 2 points; top projection left was Jared Goff,
    07:20:08  pick 117  Mark Andrews (TE) taken by seat 4 in 2 s
    07:20:09  plan #77 for pick 118: Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 97% “bench insurance: covers 3 RB starters behind” · Quentin Johnston WR “depth fallback (engine list exhausted)”
    07:20:26  heartbeat sent (Yahoo told we are not idle)
    07:20:27  pick 118  Courtland Sutton (WR) taken by seat 3 in 19 s — a target is gone (was 99% to survive)
    07:20:27  pick 119  Juwan Johnson (TE) taken by seat 2 in 0 s INSTANTLY (autopick)
    07:20:31  pick 120  Eagles (DEF) taken by seat 1 in 4 s
    07:20:34  plan #79 for pick 121: Quentin Johnston WR 99% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    07:20:43  pick 121  Cameron Dicker (K) taken by seat 1 in 13 s
    07:20:44  pick 122  Quentin Johnston (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone (was 99% to survive)
    07:20:45  pick 123  Seahawks (DEF) taken by seat 3 in 1 s INSTANTLY (autopick)
    07:20:46  pick 124  De'Zhaun Stribling (WR) taken by seat 4 in 1 s INSTANTLY (autopick)
    07:20:47  plan #80 for pick 125: Jakobi Meyers WR 92% “bench insurance: covers 2 WR starters behind” · Kenny Gainwell RB 95% “bench insurance: covers 3 RB starters behind” · Jordan Addison WR “depth fallback (engine list exhausted)”
    07:20:47  ON THE CLOCK, pick 125 · plan #80 (0.0 s old) · lineup needs K DEF
    07:20:47  PICKED Jakobi Meyers (WR) via action, confirmed in 394 ms — lineup full, so Jakobi Meyers (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.1 a week over the wire, about 2 points; top projection left was Jar
    07:20:50  plan #81 for pick 126: Brandon Aubrey K 95% “safe to wait on K” · Pittsburgh Steelers DEF 72% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    07:20:55  pick 126  Kayshon Boutte (WR) taken by seat 6 in 8 s
    07:21:01  pick 127  Jason Myers (K) taken by seat 7 in 6 s — a target is gone
    07:21:02  plan #82 for pick 128: Brandon Aubrey K 97% “safe to wait on K” · Pittsburgh Steelers DEF 72% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    07:21:02  bridge warning: 1 drafted entries matched no board player: 126 Kayshon Boutte
    07:21:06  pick 128  Jordan Addison (WR) taken by seat 8 in 4 s
    07:21:07  pick 129  Jayden Reed (WR) taken by seat 9 in 1 s INSTANTLY (autopick)
    07:21:15  plan #83 for pick 130: Brandon Aubrey K 98% “safe to wait on K” · Pittsburgh Steelers DEF 87% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    07:21:20  pick 130  Hunter Henry (TE) taken by seat 10 in 14 s
    07:21:27  heartbeat sent (Yahoo told we are not idle)
    07:21:27  plan #84 for pick 131: Brandon Aubrey K 98% “safe to wait on K” · Pittsburgh Steelers DEF 87% “safe to wait on DEF” · Cam Little K “depth fallback (engine list exhausted)”
    07:21:30  pick 131  Brandon Aubrey (K) taken by seat 10 in 10 s — a target is gone (was 98% to survive)
    07:21:30  pick 132  Vikings (DEF) taken by seat 9 in 0 s
    07:21:34  pick 133  Cam Little (K) taken by seat 8 in 4 s — a target is gone
    07:21:36  pick 134  Matthew Golden (WR) taken by seat 7 in 2 s INSTANTLY (autopick)
    07:21:40  plan #85 for pick 135: Pittsburgh Steelers DEF 98% “safe to wait on DEF” · Eddy Pineiro K 98% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)”
    07:21:52  pick 135  Aaron Jones Sr. (RB) taken by seat 6 in 16 s
    07:21:53  plan #86 for pick 136: Pittsburgh Steelers DEF 64% “safe to wait on DEF” · Eddy Pineiro K 78% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)”
    07:21:53  ON THE CLOCK, pick 136 · plan #86 (0.0 s old) · lineup needs K DEF
    07:21:53  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 358 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (64% to survive, nobody better worth waiting for); top projection left w
    07:21:56  pick 137  Jaguars (DEF) taken by seat 4 in 2 s
    07:21:56  plan #87 for pick 138: Eddy Pineiro K 82% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    07:21:57  pick 138  Mike Washington Jr. (RB) taken by seat 3 in 2 s INSTANTLY (autopick)
    07:21:57  pick 139  Patriots (DEF) taken by seat 2 in 0 s INSTANTLY (autopick)
    07:22:05  pick 140  C.J. Stroud (QB) taken by seat 1 in 8 s
    07:22:08  plan #88 for pick 141: Eddy Pineiro K 83% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    07:22:18  pick 141  Keaton Mitchell (RB) taken by seat 1 in 12 s
    07:22:19  pick 142  Tyler Loop (K) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    07:22:21  plan #89 for pick 143: Eddy Pineiro K 88% “safe to wait on K” · Evan McPherson K “depth fallback (engine list exhausted)” · Cairo Santos K “depth fallback (engine list exhausted)”
    07:22:22  pick 143  Jake Bates (K) taken by seat 3 in 3 s — a target is gone
    07:22:23  pick 144  Will Reichard (K) taken by seat 4 in 1 s INSTANTLY (autopick)
    07:22:23  plan #90 for pick 145: Eddy Pineiro K “fills your open K slot” · Evan McPherson K “depth fallback (engine list exhausted)” · Cairo Santos K “depth fallback (engine list exhausted)”
    07:22:23  bridge warning: 2 drafted entries matched no board player: 126 Kayshon Boutte, 144 Will Reichard
    07:22:23  ON THE CLOCK, pick 145 · plan #90 (0.0 s old) · lineup needs K
    07:22:24  PICKED Eddy Pineiro (K) via action, confirmed in 396 ms — chose Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Jared Goff, passed on purpose
    07:22:26  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    07:07:17 PT preflight: ok=true pick_path=action my_team=5 plan=plan 25 deep @pick 1 via store call#1
    07:07:17 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    07:07:17 PT NARR info driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    07:08:18 PT heartbeat: setAwayStatus(false)
    07:08:18 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:08:24 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~38 pts at RB (best option now 154, ~116 by your next turn) · 46% chance he's still there at your next pick · fills yo
    07:09:21 PT heartbeat: setAwayStatus(false)
    07:09:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:09:29 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~14 pts at TE (best option now 78, ~64 by your next turn) · 63% chance he's still there at your next pick · fills your open TE
    07:10:21 PT heartbeat: setAwayStatus(false)
    07:10:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:10:23 PT ON CLOCK -> {"drafted":"Kyren Williams","pos":"RB","vorp":40.5,"proj":200.7,"why":"waiting likely costs ~5 pts at RB (best option now 40, ~35 by your next turn) · 45% chance he's still there at your next pick · fills your open R
    07:11:21 PT heartbeat: setAwayStatus(false)
    07:11:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:11:25 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~1 pts at WR (best option now 24, ~23 by your next turn) · 70% chance he's still there at your next pick · fills your open WR 
    07:12:21 PT heartbeat: setAwayStatus(false)
    07:12:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:12:35 PT ON CLOCK -> {"drafted":"Davante Adams","pos":"WR","vorp":13.1,"proj":155.2,"why":"waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 61% chance he's still there at your next pick · fills your open WR
    07:13:22 PT heartbeat: setAwayStatus(false)
    07:13:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:13:52 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 70% chance he's still there at your next pick · fills your open QB sl
    07:14:22 PT heartbeat: setAwayStatus(false)
    07:14:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:15:01 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~7 by your next turn) · 54% chance he's still there at your next pick · fills a F
    07:15:23 PT heartbeat: setAwayStatus(false)
    07:15:23 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:16:24 PT heartbeat: setAwayStatus(false)
    07:16:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:16:26 PT ON CLOCK -> {"drafted":"Rico Dowdle","pos":"RB","vorp":-11,"proj":149.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +10.0/wk over the wire (Josh Jacobs) ≈ 96 pts · HANDCUFF: backs up your Jaylen Warren","s":0.
    07:17:04 PT ON CLOCK -> {"drafted":"Blake Corum","pos":"RB","vorp":-46.1,"proj":114.1,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: back
    07:17:24 PT heartbeat: setAwayStatus(false)
    07:17:24 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:17:55 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.968,"sr":0.968,"e":-10.6,"top_
    07:18:25 PT heartbeat: setAwayStatus(false)
    07:18:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:19:04 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.887,"sr":0.887,"e":11.7,"top_pr
    07:19:25 PT heartbeat: setAwayStatus(false)
    07:19:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:20:06 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9.1/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.973,"sr"
    07:20:26 PT heartbeat: setAwayStatus(false)
    07:20:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:20:47 PT ON CLOCK -> {"drafted":"Jakobi Meyers","pos":"WR","vorp":-21.5,"proj":120.7,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.921,"
    07:21:02 PT BRIDGE WARNING: 1 drafted entries matched no board player: 126 Kayshon Boutte
    07:21:27 PT heartbeat: setAwayStatus(false)
    07:21:27 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:21:53 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 64% chance he's still there at your next pick · fills your open DEF slot · 4 teams picking before you still need a DEF · t
    07:22:23 PT BRIDGE WARNING: 2 drafted entries matched no board player: 126 Kayshon Boutte, 144 Will Reichard
    07:22:24 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Jared Goff","p":"QB","proj":261.8,"vorp":-11.8},"took_top_projection":fa
    07:22:26 PT roster full
    07:22:26 PT NARR info roster full — driver done; posting the trail when the room finishes
    07:22:26 PT driver stop


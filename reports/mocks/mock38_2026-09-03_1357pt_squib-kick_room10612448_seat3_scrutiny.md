# Scrutiny: Mock 38 -- Squib Kick (room 10612448) -- Thursday 2026-09-03 13:57 PT -- 10 teams, our seat 3

Captured 2026-09-03 14:15:53 PT. Times below are Pacific. 10 teams, our team id 3, draft slot 3. 150 picks in the trail, 95 bridge plan calls, 78 recs events in the room log.

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
- Action latency to store confirmation: median 573 ms, min 326, max 2411.
- Heartbeats 17; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (3): dropped 1 feed entries numbered >= header pick 24; dropped 1 feed entries numbered >= header pick 26; dropped 1 feed entries numbered >= header pick 53.
- Away seats over the room (each change): {} -> {2} -> {2,5} -> {2,4,5} -> {1,2,4,5} -> {1,2,4,5,7,8} -> {1,2,4,5,7}.
- Managers away at the end: 1 Tyler, 2 Brandon, 4 jonathan, 5, 7 R, 9 Andrew.

## Our picks, one block each

### Pick 3 (round 1): Christian McCaffrey (RB)

- In plain English: Took Christian McCaffrey (RB) because waiting would likely cost about 56 points at RB, with a 31% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 539 ms, ranker engine, plan call 7, plan age 861 ms, at 13:58:27 PT.
- Engine's reason: waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills your open RB slot · TAKE-NOW ZONE: only 1 left before the RB value drops, and 14 tea
- Top projection available: Josh Allen -> took it: False.
- Passed on: Ja'Marr Chase (WR, s=0.529, e=100.8); Trey McBride (TE, s=0.864, e=73.8); Josh Allen (QB, s=0.638, e=41.2).
- Plan call 7 @pick 3: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2], state store with 2 drafted / 0 mine.
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

### Pick 18 (round 2): Derrick Henry (RB)

- In plain English: Took Derrick Henry (RB) because waiting would likely cost about 5 points at RB, with a 56% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1352 ms, ranker engine, plan call 18, plan age 1693 ms, at 14:00:35 PT.
- Engine's reason: waiting likely costs ~5 pts at RB (best option now 50, ~46 by your next turn) · 56% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB · two-pick plan: pair w
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.848, e=73.6); Josh Allen (QB, s=0.706, e=42.3); Brock Bowers (TE, s=None, e=None).
- Plan call 18 @pick 18: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5], state store with 17 drafted / 1 mine.
- Engine's first choice was **Derrick Henry** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Derrick Henry | RB | 50.4 | 0.56 | 0.56 | 45.9 | 50.4 | waiting likely costs ~5 pts at RB (best option now 50, ~46 by your next turn) · 56% chance |
| Trey McBride | TE | 77.9 | 0.85 | 0.85 | 73.6 | 77.9 | waiting likely costs ~4 pts at TE (best option now 78, ~74 by your next turn) · 85% chance |
| A.J. Brown | WR | 43.6 | 0.61 | 0.61 | 42.1 | 43.6 | waiting likely costs ~1 pts at WR (best option now 44, ~42 by your next turn) · 61% chance |
| Josh Allen | QB | 47.0 | 0.71 | 0.71 | 42.3 | 47.0 | waiting likely costs ~5 pts at QB (best option now 47, ~42 by your next turn) · 71% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyren Williams | RB | 40.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.3 | 4.7 | 9 |
| RB | 50.4 | 45.9 | 4.5 | 19 |
| WR | 43.6 | 42.1 | 1.5 | 21 |
| TE | 77.9 | 73.6 | 4.3 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 50.44274023536681 | 46.1 | 4.4 | 48 |

### Pick 23 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 31 points at TE, with a 44% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 2411 ms, ranker engine, plan call 21, plan age 2773 ms, at 14:01:00 PT.
- Engine's reason: waiting likely costs ~31 pts at TE (best option now 78, ~47 by your next turn) · 44% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 14 team
- Top projection available: Josh Allen -> took it: False.
- Passed on: Chris Olave (WR, s=0.344, e=33.6); Josh Allen (QB, s=0.637, e=40.5); Kyren Williams (RB, s=None, e=None).
- Plan call 21 @pick 23: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 5], state store with 22 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.44 | 0.44 | 47.1 | 77.9 | waiting likely costs ~31 pts at TE (best option now 78, ~47 by your next turn) · 44% chanc |
| Chris Olave | WR | 40.1 | 0.34 | 0.34 | 33.6 | 40.1 | waiting likely costs ~7 pts at WR (best option now 40, ~34 by your next turn) · 34% chance |
| Josh Allen | QB | 47.0 | 0.64 | 0.64 | 40.5 | 47.0 | waiting likely costs ~7 pts at QB (best option now 47, ~40 by your next turn) · 64% chance |
| Kyren Williams | RB | 40.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 40.5 | 6.5 | 9 |
| RB | 40.5 | 32.9 | 7.6 | 17 |
| WR | 40.1 | 33.6 | 6.5 | 23 |
| TE | 77.9 | 47.1 | 30.8 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 36.3 | 4.3 | 47 |

### Pick 38 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (85% to survive, but nobody better was worth waiting for). The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 433 ms, ranker engine, plan call 33, plan age 765 ms, at 14:03:25 PT.
- Engine's reason: safe to wait on WR · 85% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pick plan: pair with the ~31-pt WR expected at your next turn
- Top projection available: Drake Maye -> took it: False.
- Passed on: Cam Skattebo (RB, s=0.752, e=24.1); Drake Maye (QB, s=0.842, e=29); Zay Flowers (WR, s=None, e=None).
- Plan call 33 @pick 38: needs {'QB': 1, 'RB': 0, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5], state store with 37 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.85 | 0.85 | 23.0 | 23.9 | safe to wait on WR · 85% chance he's still there at your next pick · fills your open WR sl |
| Cam Skattebo | RB | 25.8 | 0.75 | 0.75 | 24.1 | 25.8 | waiting likely costs ~2 pts at your FLEX spot (best option now 26, ~24 by your next turn)  |
| Drake Maye | QB | 31.1 | 0.84 | 0.84 | 29.0 | 31.1 | waiting likely costs ~2 pts at QB (best option now 31, ~29 by your next turn) · 84% chance |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 29.0 | 2.1 | 10 |
| RB | 25.8 | 24.1 | 1.7 | 16 |
| WR | 23.9 | 23.0 | 0.9 | 21 |
| TE | 23.8 | 23.4 | 0.4 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 24.1 | 1.7 | 45 |

### Pick 43 (round 5): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB) because waiting would likely cost about 14 points at your FLEX spot, with a 14% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 475 ms, ranker engine, plan call 36, plan age 801 ms, at 14:03:51 PT.
- Engine's reason: waiting likely costs ~14 pts at your FLEX spot (best option now 26, ~11 by your next turn) · 14% chance he's still there at your next pick · fills a FLEX slot · last RB at this level — big drop after him · 10 teams picki
- Top projection available: Drake Maye -> took it: False.
- Passed on: Davante Adams (WR, s=0.478, e=10.3); Drake Maye (QB, s=0.418, e=22.7); Jalen Hurts (QB, s=None, e=None).
- Plan call 36 @pick 43: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5], state store with 42 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 0.14 | 0.14 | 11.4 | 25.8 | waiting likely costs ~14 pts at your FLEX spot (best option now 26, ~11 by your next turn) |
| Davante Adams | WR | 13.1 | 0.48 | 0.48 | 10.3 | 13.1 | waiting likely costs ~3 pts at WR (best option now 13, ~10 by your next turn) · 48% chance |
| Drake Maye | QB | 31.1 | 0.42 | 0.42 | 22.7 | 31.1 | waiting likely costs ~8 pts at QB (best option now 31, ~23 by your next turn) · 42% chance |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 22.7 | 8.4 | 14 |
| RB | 25.8 | 11.4 | 14.4 | 16 |
| WR | 13.1 | 10.3 | 2.8 | 19 |
| TE | 23.8 | 21.7 | 2.1 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 11.4 | 14.4 | 43 |

### Pick 58 (round 6): Jameson Williams (WR)

- In plain English: Took Jameson Williams (WR): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (88% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 893 ms, ranker engine, plan call 45, plan age 1254 ms, at 14:05:32 PT.
- Engine's reason: safe to wait on WR · 88% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · two-pick plan: pair with the ~9-pt RB expected at your next turn
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jalen Hurts (QB, s=0.662, e=17.2); Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None).
- Plan call 45 @pick 58: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5], state store with 57 drafted / 5 mine.
- Engine's first choice was **Jameson Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jameson Williams | WR | 0.0 | 0.89 | 0.89 | -0.1 | 0.0 | safe to wait on WR · 88% chance he's still there at your next pick · fills your open WR sl |
| Jalen Hurts | QB | 18.0 | 0.66 | 0.66 | 17.2 | 18.0 | safe to wait on QB · 66% chance he's still there at your next pick · fills your open QB sl |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaylen Warren | RB | 9.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 17.2 | 0.8 | 15 |
| RB | 9.3 | 8.8 | 0.5 | 14 |
| WR | 0.0 | -0.1 | 0.1 | 23 |
| TE | 21.1 | 21.0 | 0.1 | 10 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 63 (round 7): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB) because waiting would likely cost about 2 points at QB, with a 33% chance he would still be there next turn.
- Driver: via **action**, verified store, 682 ms, ranker engine, plan call 48, plan age 1191 ms, at 14:05:57 PT.
- Engine's reason: waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 33% chance he's still there at your next pick · fills your open QB slot · 6 teams picking before you still need a QB · 7 picks past his usua
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None); Jaylen Warren (RB, s=None, e=None).
- Plan call 48 @pick 63: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5], state store with 62 drafted / 6 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 0.33 | 0.33 | 15.6 | 18.0 | waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 33% chance |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaylen Warren | RB | 9.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Justin Herbert | QB | 7.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 15.6 | 2.4 | 16 |
| RB | 9.3 | 3.0 | 6.3 | 18 |
| WR | -0.7 | -1.7 | 1.0 | 23 |
| TE | 21.1 | 16.6 | 4.5 | 9 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 78 (round 8): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +8.3 points a week over the waiver wire (Ollie Gordon II), worth about 80 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 427 ms, ranker engine, plan call 60, plan age 753 ms, at 14:08:12 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: DK Metcalf (WR, s=0.339, e=-10.1); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 60 @pick 78: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5], state store with 77 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordo |
| DK Metcalf | WR | -9.2 | 0.34 | 0.34 | -10.1 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Rico Dowdle | RB | -11.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.7 | 1.0 | 18 |
| RB | -5.4 | -5.4 | 0.0 | 33 |
| WR | -9.2 | -10.1 | 0.9 | 37 |
| TE | 19.8 | 18.5 | 1.3 | 21 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 9 |

### Pick 83 (round 9): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 491 ms, ranker engine, plan call 62, plan age 890 ms, at 14:08:35 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: RJ Harvey (RB, s=0.803, e=-5.9); Kenny Gainwell (RB, s=None, e=None); Rico Dowdle (RB, s=None, e=None).
- Plan call 62 @pick 83: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5], state store with 82 drafted / 8 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.96 | 0.96 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | 0.80 | 0.80 | -5.9 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5 |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Rico Dowdle | RB | -11.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.6 | 1.2 | 17 |
| RB | -5.4 | -5.9 | 0.5 | 31 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 19.8 | 14.8 | 5.0 | 20 |
| K | 13.5 | 13.5 | 0.0 | 12 |
| DEF | 18.0 | 17.9 | 0.1 | 11 |

### Pick 98 (round 10): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +6.5 points a week over the waiver wire (Ollie Gordon II), worth about 16 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 593 ms, ranker engine, plan call 72, plan age 1028 ms, at 14:10:27 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5/wk over the wire (Ollie Gordon II) ≈ 16 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.851, e=11.5); Courtland Sutton (WR, s=0.832, e=-11.5); Bo Nix (QB, s=None, e=None).
- Plan call 72 @pick 98: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5], state store with 97 drafted / 9 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.86 | 0.86 | -5.6 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5 |
| Patrick Mahomes II | QB | 12.8 | 0.85 | 0.85 | 11.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Courtland Sutton | WR | -11.1 | 0.83 | 0.83 | -11.5 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Brock Purdy | QB | 2.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.5 | 1.3 | 16 |
| RB | -5.4 | -5.6 | 0.2 | 26 |
| WR | -11.1 | -11.5 | 0.4 | 34 |
| TE | 10.9 | 9.7 | 1.2 | 17 |
| K | 13.5 | 13.5 | 0.0 | 14 |
| DEF | 18.0 | 18.0 | 0.0 | 11 |

### Pick 103 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 764 ms, ranker engine, plan call 73, plan age 1134 ms, at 14:10:36 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Courtland Sutton (WR, s=0.808, e=-11.7); Kenny Gainwell (RB, s=0.874, e=-8.7); Bo Nix (QB, s=None, e=None).
- Plan call 73 @pick 103: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5], state store with 102 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.87 | 0.87 | 11.4 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Courtland Sutton | WR | -11.1 | 0.81 | 0.81 | -11.7 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Kenny Gainwell | RB | -6.2 | 0.87 | 0.87 | -8.7 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6. |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.4 | 1.4 | 15 |
| RB | -6.2 | -8.7 | 2.5 | 24 |
| WR | -11.1 | -11.7 | 0.6 | 32 |
| TE | 10.9 | 9.8 | 1.1 | 17 |
| K | 13.5 | 13.2 | 0.3 | 15 |
| DEF | 18.0 | 16.7 | 1.3 | 12 |

### Pick 118 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1480 ms, ranker engine, plan call 85, plan age 1870 ms, at 14:13:11 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Kenny Gainwell (RB, s=0.969, e=-6.8); Jakobi Meyers (WR, s=None, e=None); Jordan Addison (WR, s=None, e=None).
- Plan call 85 @pick 118: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 7], state store with 117 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.97 | 0.97 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Kenny Gainwell | RB | -6.2 | 0.97 | 0.97 | -6.8 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 11 |
| RB | -6.2 | -6.8 | 0.6 | 22 |
| WR | -13.3 | -13.6 | 0.3 | 30 |
| TE | -2.4 | -2.6 | 0.2 | 12 |
| K | 13.5 | 12.3 | 1.2 | 16 |
| DEF | 16.0 | 14.8 | 1.2 | 12 |

### Pick 123 (round 13): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +6.4 points a week over the waiver wire (Ollie Gordon II), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 573 ms, ranker engine, plan call 86, plan age 946 ms, at 14:13:19 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6.4/wk over the wire (Ollie Gordon II) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.906, e=-22.1); Aaron Jones Sr. (RB, s=None, e=None); Makai Lemon (WR, s=None, e=None).
- Plan call 86 @pick 123: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 7], state store with 122 drafted / 12 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.94 | 0.94 | -7.4 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6. |
| Jakobi Meyers | WR | -21.5 | 0.91 | 0.91 | -22.1 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +2. |
| Aaron Jones Sr. | RB | -25.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 11 |
| RB | -6.2 | -7.4 | 1.2 | 21 |
| WR | -21.5 | -22.1 | 0.6 | 27 |
| TE | -2.4 | -3.3 | 0.9 | 11 |
| K | 13.5 | 11.6 | 1.9 | 16 |
| DEF | 16.0 | 13.7 | 2.3 | 12 |

### Pick 138 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF) because waiting would likely cost about 2 points at DEF, with a 91% chance he would still be there next turn. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 326 ms, ranker engine, plan call 93, plan age 658 ms, at 14:14:34 PT.
- Engine's reason: waiting likely costs ~2 pts at DEF (best option now 8, ~6 by your next turn) · 91% chance he's still there at your next pick · fills your open DEF slot · 4 teams picking before you still need a DEF · two-pick plan: pair 
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cam Little (K, s=0.595, e=7.8); Minnesota Vikings (DEF, s=None, e=None); Eddy Pineiro (K, s=None, e=None).
- Plan call 93 @pick 138: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 5, 7], state store with 137 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.91 | 0.91 | 6.5 | 8.0 | waiting likely costs ~2 pts at DEF (best option now 8, ~6 by your next turn) · 91% chance  |
| Cam Little | K | 9.0 | 0.59 | 0.59 | 7.8 | 9.0 | waiting likely costs ~1 pts at K (best option now 9, ~8 by your next turn) · 60% chance he |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| New England Patriots | DEF | 4.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 11 |
| RB | -25.9 | -26.0 | 0.1 | 18 |
| WR | -21.5 | -21.7 | 0.2 | 23 |
| TE | -2.4 | -2.7 | 0.3 | 10 |
| K | 9.0 | 7.8 | 1.2 | 14 |
| DEF | 8.0 | 6.5 | 1.5 | 9 |

### Pick 143 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 370 ms, ranker engine, plan call 95, plan age 761 ms, at 14:14:51 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 95 @pick 143: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 4, 5, 7], state store with 142 drafted / 14 mine.
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
| 0-30% | 5 | 25% | 0% |
| 30-50% | 34 | 39% | 6% |
| 50-70% | 28 | 61% | 29% |
| 70-90% | 68 | 83% | 75% |
| 90-100% | 53 | 95% | 83% |

188 predictions over 77 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Bridge log: warnings and errors

    2026-09-03T14:01:10   WARNING plan #22: dropped 1 feed entries numbered >= header pick 24
    2026-09-03T14:01:22   WARNING plan #23: dropped 1 feed entries numbered >= header pick 26
    2026-09-03T14:05:13   WARNING plan #43: dropped 1 feed entries numbered >= header pick 53

## Narration (what the panel showed live, Pacific time)

    13:57:19  plan #1 for pick 1
  • Christian McCaffrey RB · wait costs 5 · pick costs 0, best pair 290.5 (159.6 now + ~130.9 RB next) · 83% survives to our turn
  • Ja'Marr Chase WR · wait costs 4 · pick costs 11.3 · 77% survives to our turn

    13:57:20  driver started — seat 3, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    13:58:09  pick 1  Jahmyr Gibbs (RB) taken by seat 1 — a target is gone
    13:58:10  plan #6 for pick 2
  • Christian McCaffrey RB · wait costs 4 · pick costs 0, best pair 284.8 (159.6 now + ~125.2 RB next) · 88% survives to our turn
  • Ja'Marr Chase WR · wait costs 2 · pick costs 4.7 · 89% survives to our turn
 
    13:58:10  pick 2  Bijan Robinson (RB) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    13:58:25  heartbeat sent (Yahoo told we are not idle)
    13:58:26  plan #7 for pick 3
  • Christian McCaffrey RB · wait costs 56 · pick costs 0, best pair 269.7 (159.6 now + ~110.1 WR next) · 31% survives to our turn
  • Ja'Marr Chase WR · wait costs 15 · pick costs 36 · 53% survives to our turn

    13:58:26  ON THE CLOCK, pick 3 · plan #7 (0.0 s old) · lineup needs QB RBx2 WRx2 TE FLEX K DEF
    13:58:27  PICKED Christian McCaffrey (RB) via action, confirmed in 539 ms — chose Christian McCaffrey (RB): waiting would likely cost about 56 points at RB, 31% to still be there next turn
  • top projection left was Josh Allen, passed on p
    13:58:31  plan #8 for pick 4
  • Ja'Marr Chase WR · wait costs 18 · pick costs 0, best pair 231.2 (124.6 now + ~106.6 WR next) · 47% survives to our turn
  • Jonathan Taylor RB · wait costs 34 · pick costs 14.9 · 25% survives to our turn
  
    13:58:41  pick 4  Ja'Marr Chase (WR) taken by seat 4 in 14 s — a target is gone (was 47% to survive)
    13:58:41  pick 5  Puka Nacua (WR) taken by seat 5 in 0 s — a target is gone
    13:58:44  plan #9 for pick 6
  • Jonathan Taylor RB · wait costs 31 · pick costs 0, best pair 188.7 (109.7 now + ~79 WR next) · 29% survives to our turn
  • Jaxon Smith-Njigba WR · wait costs 20 · pick costs 11.1 · 35% survives to our turn

    13:58:51  pick 6  Jonathan Taylor (RB) taken by seat 6 in 10 s — a target is gone (was 29% to survive)
    13:58:56  plan #10 for pick 7
  • Jaxon Smith-Njigba WR · wait costs 19 · pick costs 0, best pair 178 (98.6 now + ~79.4 WR next) · 35% survives to our turn
  • De'Von Achane RB · wait costs 13 · pick costs 19.8 · 31% survives to our turn
  
    13:59:03  pick 7  Jaxon Smith-Njigba (WR) taken by seat 7 in 12 s — a target is gone (was 35% to survive)
    13:59:08  plan #11 for pick 8
  • Amon-Ra St. Brown WR · wait costs 20 · pick costs 0, best pair 158 (91 now + ~67 RB next) · 33% survives to our turn
  • De'Von Achane RB · wait costs 12 · pick costs 8 · 33% survives to our turn
  • Trey M
    13:59:13  pick 8  Amon-Ra St. Brown (WR) taken by seat 8 in 10 s — a target is gone (was 33% to survive)
    13:59:24  plan #12 for pick 9
  • De'Von Achane RB · wait costs 12 · pick costs 0, best pair 145.7 (78.8 now + ~66.9 RB next) · 32% survives to our turn
  • CeeDee Lamb WR · wait costs 4 · pick costs 12.8 · 34% survives to our turn
  • Trey
    13:59:24  pick 9  Saquon Barkley (RB) taken by seat 9 in 12 s
    13:59:24  pick 10  James Cook III (RB) taken by seat 10 in 0 s — a target is gone
    13:59:26  pick 11  CeeDee Lamb (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone (was 34% to survive)
    13:59:28  heartbeat sent (Yahoo told we are not idle)
    13:59:31  pick 12  Kenneth Walker III (RB) taken by seat 9 in 6 s
    13:59:33  plan #13 for pick 13
  • De'Von Achane RB · wait costs 8 · pick costs 0, best pair 144.7 (78.8 now + ~65.9 RB next) · 55% survives to our turn
  • Justin Jefferson WR · wait costs 3 · pick costs 11.3 · 43% survives to our turn
  •
    13:59:59  pick 13  Chase Brown (RB) taken by seat 8 in 27 s — a target is gone
    14:00:00  plan #15 for pick 14
  • De'Von Achane RB · wait costs 11 · pick costs 0, best pair 139.5 (78.8 now + ~60.7 WR next) · 57% survives to our turn
  • Justin Jefferson WR · wait costs 2 · pick costs 8.9 · 45% survives to our turn
  •
    14:00:04  pick 14  De'Von Achane (RB) taken by seat 7 in 5 s — a target is gone (was 57% to survive)
    14:00:10  pick 15  Nico Collins (WR) taken by seat 6 in 6 s
    14:00:10  pick 16  Justin Jefferson (WR) taken by seat 5 in 0 s INSTANTLY (autopick) — a target is gone (was 45% to survive)
    14:00:12  plan #16 for pick 17
  • Drake London WR · safe to wait · pick costs 0, best pair 118 (60.2 now + ~57.8 TE next) · 89% survives to our turn
  • Trey McBride TE · safe to wait · pick costs 0.3 · 98% survives to our turn
  • Derrick
    14:00:29  heartbeat sent (Yahoo told we are not idle)
    14:00:32  pick 17  Drake London (WR) taken by seat 4 in 21 s — a target is gone (was 89% to survive)
    14:00:33  plan #18 for pick 18
  • Derrick Henry RB · wait costs 5 · pick costs 0, best pair 109.7 (55.8 now + ~53.9 TE next) · 56% survives to our turn
  • Trey McBride TE · wait costs 4 · pick costs 0.1 · 85% survives to our turn
  • A.J.
    14:00:33  ON THE CLOCK, pick 18 · plan #18 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    14:00:35  PICKED Derrick Henry (RB) via action, confirmed in 1352 ms — chose Derrick Henry (RB): waiting would likely cost about 5 points at RB, 56% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    14:00:36  pick 19  Omarion Hampton (RB) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    14:00:38  plan #19 for pick 20
  • Trey McBride TE · wait costs 5 · pick costs 0, best pair 109.8 (58.2 now + ~51.6 WR next) · 83% survives to our turn
  • A.J. Brown WR · wait costs 1 · pick costs 3.8 · 67% survives to our turn
  • Josh Al
    14:00:43  pick 20  Brock Bowers (TE) taken by seat 1 in 7 s — a target is gone
    14:00:53  plan #20 for pick 21
  • Trey McBride TE · wait costs 7 · pick costs 0, best pair 110.4 (58.2 now + ~52.2 WR next) · 87% survives to our turn
  • A.J. Brown WR · safe to wait · pick costs 6.2 · 80% survives to our turn
  • Josh Al
    14:00:53  pick 21  A.J. Brown (WR) taken by seat 1 in 10 s — a target is gone (was 80% to survive)
    14:00:53  pick 22  Ashton Jeanty (RB) taken by seat 2 in 0 s
    14:00:57  plan #21 for pick 23
  • Trey McBride TE · wait costs 31 · pick costs 0, best pair 101.1 (58.2 now + ~42.9 WR next) · 44% survives to our turn
  • Chris Olave WR · wait costs 7 · pick costs 8.9 · 34% survives to our turn
  • Josh 
    14:00:57  ON THE CLOCK, pick 23 · plan #21 (0.0 s old) · lineup needs QB WRx2 TE FLEX K DEF
    14:01:00  PICKED Trey McBride (TE) via action, confirmed in 2411 ms — chose Trey McBride (TE): waiting would likely cost about 31 points at TE, 44% to still be there next turn
  • top projection left was Josh Allen, passed on purpose
    14:01:07  pick 24  George Pickens (WR) taken by seat 4 in 6 s — a target is gone
    14:01:10  plan #22 for pick 24
  • Chris Olave WR · wait costs 7 · pick costs 0, best pair 92 (49.3 now + ~42.7 WR next) · 34% survives to our turn
  • Kyren Williams RB · wait costs 8 · pick costs 3.4 · 27% survives to our turn
  • Josh Al
    14:01:10  bridge warning: dropped 1 feed entries numbered >= header pick 24
    14:01:11  pick 25  Malik Nabers (WR) taken by seat 5 in 4 s
    14:01:20  pick 26  Chris Olave (WR) taken by seat 6 in 9 s — a target is gone (was 34% to survive)
    14:01:23  plan #23 for pick 26
  • Chris Olave WR · wait costs 8 · pick costs 0, best pair 90.6 (49.3 now + ~41.3 WR next) · 35% survives to our turn
  • Kyren Williams RB · wait costs 7 · pick costs 3.4 · 30% survives to our turn
  • Josh 
    14:01:23  bridge warning: dropped 1 feed entries numbered >= header pick 26
    14:01:28  pick 27  Kyren Williams (RB) taken by seat 7 in 9 s — a target is gone (was 30% to survive)
    14:01:29  heartbeat sent (Yahoo told we are not idle)
    14:01:33  plan #24 for pick 28
  • Javonte Williams RB · wait costs 7 · pick costs 0, best pair 79.8 (42.3 now + ~37.5 WR next) · 41% survives to our turn
  • Rashee Rice WR · wait costs 6 · pick costs 0.8 · 44% survives to our turn
  • Jos
    14:01:43  pick 28  DeVonta Smith (WR) taken by seat 8 in 15 s — a target is gone
    14:01:46  plan #25 for pick 29
  • Javonte Williams RB · wait costs 6 · pick costs 0, best pair 79.8 (42.3 now + ~37.5 WR next) · 46% survives to our turn
  • Rashee Rice WR · wait costs 6 · pick costs 0.3 · 47% survives to our turn
  • Jos
    14:01:56  pick 29  David Montgomery (RB) taken by seat 9 in 13 s
    14:01:58  plan #26 for pick 30
  • Javonte Williams RB · wait costs 6 · pick costs 0, best pair 80.8 (42.3 now + ~38.5 WR next) · 50% survives to our turn
  • Rashee Rice WR · wait costs 5 · pick costs 0.7 · 55% survives to our turn
  • Jos
    14:02:04  pick 30  Tee Higgins (WR) taken by seat 10 in 8 s
    14:02:07  pick 31  Josh Allen (QB) taken by seat 10 in 3 s — a target is gone (was 81% to survive)
    14:02:10  plan #27 for pick 32
  • Javonte Williams RB · wait costs 4 · pick costs 0, best pair 82 (42.3 now + ~39.7 WR next) · 64% survives to our turn
  • Rashee Rice WR · wait costs 4 · pick costs 0.3 · 65% survives to our turn
  • Drake
    14:02:21  pick 32  Rashee Rice (WR) taken by seat 9 in 14 s — a target is gone (was 65% to survive)
    14:02:23  plan #28 for pick 33
  • Javonte Williams RB · wait costs 3 · pick costs 0, best pair 75.1 (42.3 now + ~32.8 WR next) · 69% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 3.1 · 89% survives to our turn
  • 
    14:02:23  pick 33  Javonte Williams (RB) taken by seat 8 in 3 s — a target is gone (was 69% to survive)
    14:02:30  heartbeat sent (Yahoo told we are not idle)
    14:02:34  pick 34  Breece Hall (RB) taken by seat 7 in 10 s
    14:02:36  plan #29 for pick 35
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 64.8 (31.7 now + ~33.1 WR next) · 79% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 0.3 · 96% survives to our turn
  
    14:02:44  pick 35  Jeremiyah Love (RB) taken by seat 6 in 10 s — a target is gone
    14:02:45  pick 36  Colston Loveland (TE) taken by seat 5 in 1 s INSTANTLY (autopick)
    14:02:48  plan #30 for pick 37
  • Travis Etienne Jr. RB · safe to wait · pick costs 0, best pair 64.9 (31.7 now + ~33.2 WR next) · 89% survives to our turn
  • Garrett Wilson WR · safe to wait · pick costs 0.2 · 99% survives to our turn
  
    14:03:24  pick 37  Travis Etienne Jr. (RB) taken by seat 4 in 39 s — a target is gone (was 89% to survive)
    14:03:24  plan #33 for pick 38
  • Garrett Wilson WR · safe to wait · pick costs 0, best pair 64.3 (33.1 now + ~31.2 WR next) · 85% survives to our turn
  • Cam Skattebo RB · wait costs 2 · pick costs 0.8 · 75% survives to our turn
  • Drak
    14:03:24  ON THE CLOCK, pick 38 · plan #33 (0.0 s old) · lineup needs QB WRx2 FLEX K DEF
    14:03:25  PICKED Garrett Wilson (WR) via action, confirmed in 433 ms — chose Garrett Wilson (WR): nothing urgent, the most valuable player who fills a slot (85% to survive, nobody better worth waiting for)
  • top projection left was Drake 
    14:03:27  pick 39  Zay Flowers (WR) taken by seat 2 in 2 s — a target is gone
    14:03:27  plan #34 for pick 40
  • Cam Skattebo RB · wait costs 1 · pick costs 0, best pair 55.4 (31.2 now + ~24.2 WR next) · 83% survives to our turn
  • Tetairoa McMillan WR · safe to wait · pick costs 0.7 · 72% survives to our turn
  • D
    14:03:32  pick 40  Jaylen Waddle (WR) taken by seat 1 in 5 s — a target is gone
    14:03:32  heartbeat sent (Yahoo told we are not idle)
    14:03:41  plan #35 for pick 41
  • Tetairoa McMillan WR · wait costs 1 · pick costs 0, best pair 55.2 (24.6 now + ~30.6 RB next) · 50% survives to our turn
  • Cam Skattebo RB · safe to wait · pick costs 0.5 · 90% survives to our turn
  • D
    14:03:41  pick 41  D'Andre Swift (RB) taken by seat 1 in 8 s — a target is gone
    14:03:41  pick 42  Tetairoa McMillan (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone (was 50% to survive)
    14:03:51  plan #36 for pick 43
  • Cam Skattebo RB · wait costs 14 · pick costs 0, best pair 50.8 (31.2 now + ~19.6 WR next) · 14% survives to our turn
  • Davante Adams WR · wait costs 3 · pick costs 8.9 · 48% survives to our turn
  • Drak
    14:03:51  ON THE CLOCK, pick 43 · plan #36 (0.0 s old) · lineup needs QB WR FLEX K DEF
    14:03:51  PICKED Cam Skattebo (RB) via action, confirmed in 475 ms — chose Cam Skattebo (RB): waiting would likely cost about 14 points at your FLEX spot, 14% to still be there next turn
  • top projection left was Drake Maye, passed on pur
    14:03:54  pick 44  Tyler Warren (TE) taken by seat 4 in 2 s
    14:03:54  pick 45  Lamar Jackson (QB) taken by seat 5 in 0 s
    14:03:55  plan #37 for pick 46
  • Drake Maye QB · wait costs 7 · pick costs 0, best pair 35.5 (15.4 now + ~20.1 WR next) · 49% survives to our turn
  • Davante Adams WR · wait costs 2 · pick costs 1.4 · 49% survives to our turn
  • Jalen H
    14:04:00  pick 46  Ladd McConkey (WR) taken by seat 6 in 7 s — a target is gone
    14:04:07  plan #38 for pick 47
  • Drake Maye QB · wait costs 7 · pick costs 0, best pair 34.1 (15.4 now + ~18.7 WR next) · 53% survives to our turn
  • Davante Adams WR · wait costs 4 · pick costs 1.3 · 51% survives to our turn
  • Jalen H
    14:04:19  pick 47  Terry McLaurin (WR) taken by seat 7 in 18 s
    14:04:21  plan #39 for pick 48
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 34.2 (15.4 now + ~18.8 WR next) · 59% survives to our turn
  • Davante Adams WR · wait costs 4 · pick costs 1.4 · 55% survives to our turn
  • Jalen H
    14:04:33  heartbeat sent (Yahoo told we are not idle)
    14:04:35  pick 48  Emeka Egbuka (WR) taken by seat 8 in 17 s — a target is gone
    14:04:45  plan #41 for pick 49
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 32.2 (15.4 now + ~16.8 WR next) · 61% survives to our turn
  • Davante Adams WR · wait costs 6 · pick costs 0.1 · 58% survives to our turn
  • Jalen H
    14:04:50  pick 49  Davante Adams (WR) taken by seat 9 in 15 s — a target is gone (was 58% to survive)
    14:04:58  plan #42 for pick 50
  • Drake Maye QB · wait costs 6 · pick costs 0, best pair 24.6 (15.4 now + ~9.2 WR next) · 60% survives to our turn
  • Jameson Williams WR · safe to wait · pick costs 5.8 · 85% survives to our turn
  • Jalen
    14:04:58  pick 50  Bucky Irving (RB) taken by seat 10 in 8 s
    14:05:04  pick 51  Tucker Kraft (TE) taken by seat 10 in 6 s
    14:05:07  pick 52  Bhayshul Tuten (RB) taken by seat 9 in 2 s INSTANTLY (autopick)
    14:05:11  pick 53  Drake Maye (QB) taken by seat 8 in 5 s — a target is gone (was 60% to survive)
    14:05:13  plan #43 for pick 53
  • Drake Maye QB · wait costs 5 · pick costs 0, best pair 24.6 (15.4 now + ~9.2 WR next) · 66% survives to our turn
  • Jameson Williams WR · safe to wait · pick costs 4.8 · 92% survives to our turn
  • Jalen
    14:05:13  bridge warning: dropped 1 feed entries numbered >= header pick 53
    14:05:18  pick 54  Jadarian Price (RB) taken by seat 7 in 7 s
    14:05:25  plan #44 for pick 55
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 18 (9.2 now + ~8.8 RB next) · 95% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 6.4 · 76% survives to our turn
  • Trevor 
    14:05:26  pick 55  Joe Burrow (QB) taken by seat 6 in 8 s
    14:05:27  pick 56  Quinshon Judkins (RB) taken by seat 5 in 1 s INSTANTLY (autopick)
    14:05:30  pick 57  Rhamondre Stevenson (RB) taken by seat 4 in 2 s — a target is gone
    14:05:31  plan #45 for pick 58
  • Jameson Williams WR · safe to wait · pick costs 0, best pair 17.7 (9.2 now + ~8.5 RB next) · 89% survives to our turn
  • Jalen Hurts QB · safe to wait · pick costs 6.2 · 66% survives to our turn
  • Trevo
    14:05:31  ON THE CLOCK, pick 58 · plan #45 (0.0 s old) · lineup needs QB WR K DEF
    14:05:32  PICKED Jameson Williams (WR) via action, confirmed in 893 ms — chose Jameson Williams (WR): nothing urgent, the most valuable player who fills a slot (89% to survive, nobody better worth waiting for)
  • top projection left was Ja
    14:05:35  pick 59  Jayden Daniels (QB) taken by seat 2 in 3 s
    14:05:35  heartbeat sent (Yahoo told we are not idle)
    14:05:37  plan #46 for pick 60
  • Jalen Hurts QB · safe to wait · 79% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    14:05:43  pick 60  DJ Moore (WR) taken by seat 1 in 8 s
    14:05:49  plan #47 for pick 61
  • Jalen Hurts QB · safe to wait · 84% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    14:05:51  pick 61  Caleb Williams (QB) taken by seat 1 in 9 s — a target is gone
    14:05:51  pick 62  Sam LaPorta (TE) taken by seat 2 in 0 s INSTANTLY (autopick)
    14:05:56  plan #48 for pick 63
  • Jalen Hurts QB · wait costs 2 · 33% survives to our turn
  • Trevor Lawrence QB · depth fallback, engine list done
  • Patrick Mahomes II QB · depth fallback, engine list done
    14:05:56  ON THE CLOCK, pick 63 · plan #48 (0.0 s old) · lineup needs QB K DEF
    14:05:57  PICKED Jalen Hurts (QB) via action, confirmed in 682 ms — chose Jalen Hurts (QB): waiting would likely cost about 2 points at QB, 33% to still be there next turn
    14:06:00  pick 64  Justin Herbert (QB) taken by seat 4 in 3 s — a target is gone
    14:06:00  pick 65  TreVeyon Henderson (RB) taken by seat 5 in 0 s — a target is gone
    14:06:03  plan #49 for pick 66
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Rome Odunze WR · insurance worth ~21 · 49% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    14:06:11  pick 66  Luther Burden III (WR) taken by seat 6 in 11 s
    14:06:16  plan #50 for pick 67
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Rome Odunze WR · insurance worth ~21 · 30% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    14:06:26  pick 67  Parker Washington (WR) taken by seat 7 in 15 s — a target is gone
    14:06:29  plan #51 for pick 68
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Rome Odunze WR · insurance worth ~21 · 33% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    14:06:36  heartbeat sent (Yahoo told we are not idle)
    14:06:52  pick 68  Christian Watson (WR) taken by seat 8 in 26 s — a target is gone
    14:06:54  plan #53 for pick 69
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Rome Odunze WR · insurance worth ~21 · 34% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    14:07:02  pick 69  Mike Evans (WR) taken by seat 9 in 10 s — a target is gone
    14:07:06  plan #54 for pick 70
  • Tyrone Tracy Jr. RB · insurance worth ~80
  • Rome Odunze WR · insurance worth ~21 · 33% survives to our turn
  • Jaylen Warren RB · depth fallback, engine list done
    14:07:07  pick 70  Rome Odunze (WR) taken by seat 10 in 5 s — a target is gone (was 33% to survive)
    14:07:13  pick 71  Jaylen Warren (RB) taken by seat 10 in 7 s — a target is gone
    14:07:19  plan #55 for pick 72
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 83% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    14:07:36  heartbeat sent (Yahoo told we are not idle)
    14:07:37  pick 72  Jaxson Dart (QB) taken by seat 9 in 24 s
    14:07:42  pick 73  Kyle Pitts Sr. (TE) taken by seat 8 in 5 s
    14:07:42  plan #57 for pick 74
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 87% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    14:07:47  pick 74  Dak Prescott (QB) taken by seat 7 in 6 s
    14:07:54  plan #58 for pick 75
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 89% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    14:08:11  pick 75  Marvin Harrison Jr. (WR) taken by seat 6 in 23 s — a target is gone
    14:08:11  pick 76  Brian Thomas Jr. (WR) taken by seat 5 in 0 s
    14:08:11  pick 77  Carnell Tate (WR) taken by seat 4 in 0 s — a target is gone
    14:08:11  plan #60 for pick 78
  • Tyrone Tracy Jr. RB · insurance worth ~80 · 100% survives to our turn
  • DK Metcalf WR · insurance worth ~18 · 34% survives to our turn
  • RJ Harvey RB · depth fallback, engine list done
    14:08:11  ON THE CLOCK, pick 78 · plan #60 (0.0 s old) · lineup needs K DEF
    14:08:12  PICKED Tyrone Tracy Jr. (RB) via action, confirmed in 427 ms — lineup full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +8.3 a week over the wire, about 80 points
  • he also backs up 
    14:08:14  pick 79  Jonathon Brooks (RB) taken by seat 2 in 2 s
    14:08:14  pick 80  DK Metcalf (WR) taken by seat 1 in 0 s — a target is gone (was 34% to survive)
    14:08:14  plan #61 for pick 81
  • Wan'Dale Robinson WR · insurance worth ~17 · 100% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 100% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:08:15  pick 81  Harold Fannin Jr. (TE) taken by seat 1 in 0 s INSTANTLY (autopick)
    14:08:33  pick 82  Trevor Lawrence (QB) taken by seat 2 in 18 s
    14:08:34  plan #62 for pick 83
  • Wan'Dale Robinson WR · insurance worth ~17 · 96% survives to our turn
  • RJ Harvey RB · insurance worth ~16 · 80% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:08:34  ON THE CLOCK, pick 83 · plan #62 (0.1 s old) · lineup needs K DEF
    14:08:35  PICKED Wan'Dale Robinson (WR) via action, confirmed in 491 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points
  • top projection 
    14:08:37  pick 84  Rico Dowdle (RB) taken by seat 4 in 2 s — a target is gone
    14:08:37  pick 85  Tony Pollard (RB) taken by seat 5 in 0 s
    14:08:37  heartbeat sent (Yahoo told we are not idle)
    14:08:38  plan #63 for pick 86
  • RJ Harvey RB · insurance worth ~16 · 80% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 78% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:08:46  pick 86  George Kittle (TE) taken by seat 6 in 9 s
    14:08:51  plan #64 for pick 87
  • RJ Harvey RB · insurance worth ~16 · 81% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 79% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:08:53  pick 87  MarShawn Lloyd (RB) taken by seat 7 in 8 s
    14:09:00  pick 88  J.K. Dobbins (RB) taken by seat 8 in 7 s
    14:09:04  plan #65 for pick 89
  • RJ Harvey RB · insurance worth ~16 · 83% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 83% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:09:17  pick 89  Dalton Kincaid (TE) taken by seat 9 in 17 s
    14:09:29  plan #67 for pick 90
  • RJ Harvey RB · insurance worth ~16 · 82% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 86% survives to our turn
  • Kenny Gainwell RB · depth fallback, engine list done
    14:09:33  pick 90  Jacory Croskey-Merritt (RB) taken by seat 10 in 16 s
    14:09:37  heartbeat sent (Yahoo told we are not idle)
    14:09:39  pick 91  De'Zhaun Stribling (WR) taken by seat 10 in 6 s
    14:09:42  plan #68 for pick 92
  • RJ Harvey RB · insurance worth ~16 · 88% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 86% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 87% survives to our tu
    14:09:49  pick 92  Matthew Stafford (QB) taken by seat 9 in 10 s — a target is gone
    14:09:54  plan #69 for pick 93
  • RJ Harvey RB · insurance worth ~16 · 90% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 88% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 88% survives to our tu
    14:09:56  pick 93  Chris Godwin Jr. (WR) taken by seat 8 in 7 s
    14:10:07  plan #70 for pick 94
  • RJ Harvey RB · insurance worth ~16 · 93% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 91% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 89% survives to our tu
    14:10:08  pick 94  Dallas Goedert (TE) taken by seat 7 in 12 s
    14:10:18  plan #71 for pick 95
  • RJ Harvey RB · insurance worth ~16 · 94% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 91% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 91% survives to our tu
    14:10:22  pick 95  Blake Corum (RB) taken by seat 6 in 14 s
    14:10:24  pick 96  Michael Wilson (WR) taken by seat 5 in 2 s INSTANTLY (autopick)
    14:10:24  pick 97  Josh Downs (WR) taken by seat 4 in 0 s INSTANTLY (autopick)
    14:10:26  plan #72 for pick 98
  • RJ Harvey RB · insurance worth ~16 · 87% survives to our turn
  • Patrick Mahomes II QB · insurance worth ~8 · 85% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 83% survives to our tu
    14:10:26  ON THE CLOCK, pick 98 · plan #72 (0.1 s old) · lineup needs K DEF
    14:10:27  PICKED RJ Harvey (RB) via action, confirmed in 593 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +6.5 a week over the wire, about 16 points
  • top projection left was Patrick
    14:10:32  pick 99  Chuba Hubbard (RB) taken by seat 2 in 4 s
    14:10:32  pick 100  Quentin Johnston (WR) taken by seat 1 in 0 s
    14:10:32  pick 101  Brock Purdy (QB) taken by seat 1 in 0 s — a target is gone
    14:10:32  pick 102  Stefon Diggs (WR) taken by seat 2 in 0 s
    14:10:34  plan #73 for pick 103
  • Patrick Mahomes II QB · insurance worth ~8 · 87% survives to our turn
  • Courtland Sutton WR · insurance worth ~2 · 81% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 87% survives to o
    14:10:35  ON THE CLOCK, pick 103 · plan #73 (0.0 s old) · lineup needs K DEF
    14:10:36  PICKED Patrick Mahomes II (QB) via action, confirmed in 764 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    14:10:38  pick 104  Bo Nix (QB) taken by seat 4 in 2 s — a target is gone
    14:10:38  pick 105  Kyler Murray (QB) taken by seat 5 in 0 s — a target is gone
    14:10:38  heartbeat sent (Yahoo told we are not idle)
    14:10:41  plan #74 for pick 106
  • Courtland Sutton WR · insurance worth ~2 · 89% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 89% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:10:45  pick 106  Jordan Mason (RB) taken by seat 6 in 7 s
    14:10:51  pick 107  Jared Goff (QB) taken by seat 7 in 5 s
    14:10:53  plan #75 for pick 108
  • Courtland Sutton WR · insurance worth ~2 · 93% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 91% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:11:21  pick 108  Travis Kelce (TE) taken by seat 8 in 30 s
    14:11:30  plan #78 for pick 109
  • Courtland Sutton WR · insurance worth ~2 · 93% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 90% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:11:35  pick 109  Josh Jacobs (RB) taken by seat 9 in 14 s
    14:11:37  pick 110  Alec Pierce (WR) taken by seat 10 in 3 s — a target is gone
    14:11:38  heartbeat sent (Yahoo told we are not idle)
    14:11:42  plan #79 for pick 111
  • Courtland Sutton WR · insurance worth ~2 · 96% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 95% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:11:47  pick 111  Texans (DEF) taken by seat 10 in 9 s
    14:11:54  plan #80 for pick 112
  • Courtland Sutton WR · insurance worth ~2 · 97% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 96% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:12:07  pick 112  Isaiah Likely (TE) taken by seat 9 in 20 s
    14:12:08  plan #81 for pick 113
  • Courtland Sutton WR · insurance worth ~2 · 98% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 97% survives to our turn
  • Michael Pittman Jr. WR · depth fallback, engine list done
    14:12:28  pick 113  Courtland Sutton (WR) taken by seat 8 in 22 s — a target is gone (was 98% to survive)
    14:12:29  pick 114  Mark Andrews (TE) taken by seat 7 in 1 s INSTANTLY (autopick)
    14:12:32  plan #83 for pick 115
  • Michael Pittman Jr. WR · insurance worth ~2 · 98% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 99% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    14:12:39  heartbeat sent (Yahoo told we are not idle)
    14:12:42  pick 115  Rams (DEF) taken by seat 6 in 13 s
    14:12:43  pick 116  Juwan Johnson (TE) taken by seat 5 in 1 s INSTANTLY (autopick)
    14:12:45  plan #84 for pick 117
  • Michael Pittman Jr. WR · insurance worth ~2 · 99% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 99% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    14:12:45  pick 117  Jake Ferguson (TE) taken by seat 4 in 2 s INSTANTLY (autopick)
    14:13:09  plan #85 for pick 118
  • Michael Pittman Jr. WR · insurance worth ~2 · 97% survives to our turn
  • Kenny Gainwell RB · insurance worth ~2 · 97% survives to our turn
  • Jakobi Meyers WR · depth fallback, engine list done
    14:13:09  ON THE CLOCK, pick 118 · plan #85 (0.0 s old) · lineup needs K DEF
    14:13:11  PICKED Michael Pittman Jr. (WR) via action, confirmed in 1480 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.5 a week over the wire, about 2 points
  • top project
    14:13:15  pick 119  Dalton Schultz (TE) taken by seat 2 in 4 s
    14:13:15  pick 120  Kyle Monangai (RB) taken by seat 1 in 0 s
    14:13:15  pick 121  Jordan Addison (WR) taken by seat 1 in 0 s — a target is gone
    14:13:15  pick 122  Jayden Reed (WR) taken by seat 2 in 0 s — a target is gone
    14:13:18  plan #86 for pick 123
  • Kenny Gainwell RB · insurance worth ~2 · 94% survives to our turn
  • Jakobi Meyers WR · insurance worth ~0 · 91% survives to our turn
  • Aaron Jones Sr. RB · depth fallback, engine list done
    14:13:18  ON THE CLOCK, pick 123 · plan #86 (0.0 s old) · lineup needs K DEF
    14:13:19  PICKED Kenny Gainwell (RB) via action, confirmed in 573 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +6.4 a week over the wire, about 2 points
  • top projection left wa
    14:13:21  pick 124  KC Concepcion (WR) taken by seat 4 in 2 s — a target is gone
    14:13:21  pick 125  Matthew Golden (WR) taken by seat 5 in 0 s
    14:13:23  plan #87 for pick 126
  • Denver Broncos DEF · wait costs 1 · pick costs 0, best pair 46.1 (14 now + ~32.1 RB next) · 63% survives to our turn
  • Ka'imi Fairbairn K · wait costs 1 · pick costs 8 · 77% survives to our turn
  • Sea
    14:13:40  heartbeat sent (Yahoo told we are not idle)
    14:13:43  pick 126  Makai Lemon (WR) taken by seat 6 in 22 s
    14:13:43  pick 127  Chris Rodriguez Jr. (RB) taken by seat 7 in 0 s INSTANTLY (autopick)
    14:13:48  plan #89 for pick 128
  • Denver Broncos DEF · safe to wait · pick costs 0, best pair 46 (14 now + ~32 RB next) · 74% survives to our turn
  • Ka'imi Fairbairn K · wait costs 1 · pick costs 8 · 82% survives to our turn
  • Seattle
    14:13:48  pick 128  Jordyn Tyson (WR) taken by seat 8 in 5 s
    14:13:53  pick 129  Brandon Aubrey (K) taken by seat 9 in 4 s — a target is gone
    14:14:00  plan #90 for pick 130
  • Denver Broncos DEF · wait costs 2 · pick costs 0, best pair 46.1 (14 now + ~32.1 RB next) · 32% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 9.5 · 84% survives to our turn
  • Sea
    14:14:05  pick 130  Chig Okonkwo (TE) taken by seat 10 in 12 s
    14:14:12  plan #91 for pick 131
  • Denver Broncos DEF · wait costs 2 · pick costs 0, best pair 46.1 (14 now + ~32.1 RB next) · 32% survives to our turn
  • Cameron Dicker K · safe to wait · pick costs 9.5 · 86% survives to our turn
  • Sea
    14:14:17  pick 131  Ka'imi Fairbairn (K) taken by seat 10 in 12 s — a target is gone
    14:14:17  pick 132  Eagles (DEF) taken by seat 9 in 0 s
    14:14:21  pick 133  Broncos (DEF) taken by seat 8 in 4 s
    14:14:21  pick 134  Seahawks (DEF) taken by seat 7 in 0 s INSTANTLY (autopick)
    14:14:24  plan #92 for pick 135
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 36.2 (4 now + ~32.2 RB next) · 95% survives to our turn
  • Cam Little K · safe to wait · pick costs 1 · 93% survives to our turn
  • Camer
    14:14:32  pick 135  Rachaad White (RB) taken by seat 6 in 11 s
    14:14:32  pick 136  Cameron Dicker (K) taken by seat 5 in 0 s INSTANTLY (autopick) — a target is gone
    14:14:33  pick 137  Jason Myers (K) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    14:14:34  plan #93 for pick 138
  • Pittsburgh Steelers DEF · wait costs 2 · pick costs 0, best pair 36.2 (4 now + ~32.2 RB next) · 91% survives to our turn
  • Cam Little K · wait costs 1 · pick costs 1 · 60% survives to our turn
  • Minne
    14:14:34  ON THE CLOCK, pick 138 · plan #93 (0.0 s old) · lineup needs K DEF
    14:14:34  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 326 ms — chose Pittsburgh Steelers (DEF): waiting would likely cost about 2 points at DEF, 91% to still be there next turn
  • top projection left was Baker Mayfield, passe
    14:14:37  pick 139  Vikings (DEF) taken by seat 2 in 2 s
    14:14:37  pick 140  Cam Little (K) taken by seat 1 in 0 s — a target is gone (was 60% to survive)
    14:14:37  pick 141  Jaguars (DEF) taken by seat 1 in 0 s
    14:14:37  plan #94 for pick 142
  • Eddy Pineiro K · safe to wait · 99% survives to our turn
  • Tyler Loop K · depth fallback, engine list done
  • Evan McPherson K · depth fallback, engine list done
    14:14:50  pick 142  Tyler Loop (K) taken by seat 2 in 13 s — a target is gone
    14:14:50  heartbeat sent (Yahoo told we are not idle)
    14:14:50  plan #95 for pick 143
  • Eddy Pineiro K
  • Evan McPherson K · depth fallback, engine list done
  • Cairo Santos K · depth fallback, engine list done
    14:14:50  ON THE CLOCK, pick 143 · plan #95 (0.0 s old) · lineup needs K
    14:14:51  PICKED Eddy Pineiro (K) via action, confirmed in 370 ms — chose Eddy Pineiro (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Baker Mayfield, passed on purpose
    14:14:53  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    13:57:20 PT preflight: ok=true pick_path=action my_team=3 plan=plan 25 deep @pick 1 via store call#1
    13:57:20 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    13:57:20 PT NARR info driver started — seat 3, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    13:58:25 PT heartbeat: setAwayStatus(false)
    13:58:25 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    13:58:27 PT ON CLOCK -> {"drafted":"Christian McCaffrey","pos":"RB","vorp":154.2,"proj":314.4,"why":"waiting likely costs ~56 pts at RB (best option now 154, ~99 by your next turn) · 31% chance he's still there at your next pick · fills you
    13:59:28 PT heartbeat: setAwayStatus(false)
    13:59:28 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:00:29 PT heartbeat: setAwayStatus(false)
    14:00:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:00:35 PT ON CLOCK -> {"drafted":"Derrick Henry","pos":"RB","vorp":50.4,"proj":210.6,"why":"waiting likely costs ~5 pts at RB (best option now 50, ~46 by your next turn) · 56% chance he's still there at your next pick · fills your open RB
    14:01:00 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~31 pts at TE (best option now 78, ~47 by your next turn) · 44% chance he's still there at your next pick · fills your open TE
    14:01:10 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 24
    14:01:23 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 26
    14:01:29 PT heartbeat: setAwayStatus(false)
    14:01:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:02:30 PT heartbeat: setAwayStatus(false)
    14:02:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:03:25 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"safe to wait on WR · 85% chance he's still there at your next pick · fills your open WR slot · 4 teams picking before you still need a WR · two-pic
    14:03:32 PT heartbeat: setAwayStatus(false)
    14:03:32 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:03:52 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"waiting likely costs ~14 pts at your FLEX spot (best option now 26, ~11 by your next turn) · 14% chance he's still there at your next pick · fills a 
    14:04:33 PT heartbeat: setAwayStatus(false)
    14:04:33 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:05:13 PT BRIDGE WARNING: dropped 1 feed entries numbered >= header pick 53
    14:05:32 PT ON CLOCK -> {"drafted":"Jameson Williams","pos":"WR","vorp":0,"proj":142.1,"why":"safe to wait on WR · 88% chance he's still there at your next pick · fills your open WR slot · 2 teams picking before you still need a WR · two-pi
    14:05:35 PT heartbeat: setAwayStatus(false)
    14:05:35 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:05:57 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"waiting likely costs ~2 pts at QB (best option now 18, ~16 by your next turn) · 33% chance he's still there at your next pick · fills your open QB slo
    14:06:36 PT heartbeat: setAwayStatus(false)
    14:06:36 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:07:36 PT heartbeat: setAwayStatus(false)
    14:07:36 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:08:12 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +8.3/wk over the wire (Ollie Gordon II) ≈ 80 pts · HANDCUFF: backs up your Cam Skattebo"
    14:08:35 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.964,"sr":0.964,"e":-10.6,"top_
    14:08:37 PT heartbeat: setAwayStatus(false)
    14:08:37 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:09:37 PT heartbeat: setAwayStatus(false)
    14:09:37 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:10:27 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +6.5/wk over the wire (Ollie Gordon II) ≈ 16 pts","s":0.865,"sr"
    14:10:36 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.867,"sr":0.867,"e":11.4,"top_pr
    14:10:38 PT heartbeat: setAwayStatus(false)
    14:10:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:11:38 PT heartbeat: setAwayStatus(false)
    14:11:38 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:12:39 PT heartbeat: setAwayStatus(false)
    14:12:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:13:11 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    14:13:19 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +6.4/wk over the wire (Ollie Gordon II) ≈ 2 pts","s":0.941,"
    14:13:40 PT heartbeat: setAwayStatus(false)
    14:13:40 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:14:34 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"waiting likely costs ~2 pts at DEF (best option now 8, ~6 by your next turn) · 91% chance he's still there at your next pick · fills your open D
    14:14:50 PT heartbeat: setAwayStatus(false)
    14:14:50 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    14:14:51 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    14:14:53 PT roster full
    14:14:53 PT NARR info roster full — driver done; posting the trail when the room finishes
    14:14:53 PT driver stop


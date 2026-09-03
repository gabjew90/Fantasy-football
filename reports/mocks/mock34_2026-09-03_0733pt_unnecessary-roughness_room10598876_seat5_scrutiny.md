# Scrutiny: Mock 34 -- Unnecessary Roughness (room 10598876) -- Thursday 2026-09-03 07:33 PT -- 10 teams, our seat 5

Captured 2026-09-03 07:47:30 PT. Times below are Pacific. 10 teams, our team id 5, draft slot 5. 150 picks in the trail, 80 bridge plan calls, 74 recs events in the room log.

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

- Our picks: 15; by the driver 14 (action 14, click 0), by Yahoo from the queue / autopick 1: 5 Puka Nacua.
- Action latency to store confirmation: median 402 ms, min 298, max 430.
- Heartbeats 13; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {3,10} -> {2,3,10}.
- Managers away at the end: 2 P.J., 3 Mike, 10 Dennis.

## Our picks, one block each

### Pick 5 (round 1): Puka Nacua (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    07:34:27 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~16 pts at RB (best option now 73, ~58 by your next turn) · 54% chance he's still there at your next pick · fills your open RB slot · last RB at 
    07:34:53 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~30 pts at TE (best option now 78, ~48 by your next turn) · 45% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZON
    07:36:03 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~3 pts at WR (best option now 24, ~21 by your next turn) · 69% chance he's still there at your next pick · fills your open WR slot · 8 teams picki
    07:36:43 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 48% chance he's still there at your next pick · fills your open QB slot · 8 teams picking
    07:37:58 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB","s":0.829,"sr":0.829,"e":8.9
    07:38:30 PT ON CLOCK -> {"drafted":"TreVeyon Henderson","pos":"RB","vorp":2.9,"proj":163.1,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) · 74% chance he's still there at your next pick · fills a FLEX slot ⛑ back
- No plan call recorded at this pick (bridge down?).

### Pick 16 (round 2): De'Von Achane (RB)

- In plain English: Took De'Von Achane (RB) because waiting would likely cost about 16 points at RB, with a 54% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 412 ms, ranker engine, plan call 95, plan age 727 ms, at 07:34:27 PT.
- Engine's reason: waiting likely costs ~16 pts at RB (best option now 73, ~58 by your next turn) · 54% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · 8 teams picking befo
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Trey McBride (TE, s=0.636, e=65.2); Drake London (WR, s=0.388, e=45.2); Josh Allen (QB, s=0.49, e=38.9).
- Plan call 95 @pick 16: needs {'QB': 1, 'RB': 2, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 15 drafted / 1 mine.
- Engine's first choice was **De'Von Achane** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| De'Von Achane | RB | 73.4 | 0.54 | 0.54 | 57.6 | 73.4 | waiting likely costs ~16 pts at RB (best option now 73, ~58 by your next turn) · 54% chanc |
| Trey McBride | TE | 77.9 | 0.64 | 0.64 | 65.2 | 77.9 | waiting likely costs ~13 pts at TE (best option now 78, ~65 by your next turn) · 64% chanc |
| Drake London | WR | 51.0 | 0.39 | 0.39 | 45.2 | 51.0 | waiting likely costs ~6 pts at WR (best option now 51, ~45 by your next turn) · 39% chance |
| Josh Allen | QB | 47.0 | 0.49 | 0.49 | 38.9 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 49% chance |
| Brock Bowers | TE | 58.1 | - | - | - | - | depth fallback (engine list exhausted) |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.9 | 8.1 | 9 |
| RB | 73.4 | 57.6 | 15.8 | 18 |
| WR | 51.0 | 45.2 | 5.8 | 23 |
| TE | 77.9 | 65.2 | 12.7 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 73.40147081424419 | 57.9 | 15.5 | 49 |

### Pick 25 (round 3): Trey McBride (TE)

- In plain English: Took Trey McBride (TE) because waiting would likely cost about 30 points at TE, with a 45% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 400 ms, ranker engine, plan call 98, plan age 715 ms, at 07:34:52 PT.
- Engine's reason: waiting likely costs ~30 pts at TE (best option now 78, ~48 by your next turn) · 45% chance he's still there at your next pick · fills your open TE slot · TAKE-NOW ZONE: only 1 left before the TE value drops, and 10 team
- Top projection available: Josh Allen -> took it: False.
- Passed on: Chris Olave (WR, s=0.331, e=32.1); Javonte Williams (RB, s=0.486, e=34.2); Josh Allen (QB, s=0.744, e=42.5).
- Plan call 98 @pick 25: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 24 drafted / 2 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 0.45 | 0.45 | 47.9 | 77.9 | waiting likely costs ~30 pts at TE (best option now 78, ~48 by your next turn) · 45% chanc |
| Chris Olave | WR | 40.1 | 0.33 | 0.33 | 32.1 | 40.1 | waiting likely costs ~8 pts at WR (best option now 40, ~32 by your next turn) · 33% chance |
| Javonte Williams | RB | 36.9 | 0.49 | 0.49 | 34.2 | 36.9 | waiting likely costs ~3 pts at RB (best option now 37, ~34 by your next turn) · 49% chance |
| Josh Allen | QB | 47.0 | 0.74 | 0.74 | 42.5 | 47.0 | waiting likely costs ~4 pts at QB (best option now 47, ~43 by your next turn) · 74% chance |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Ashton Jeanty | RB | 32.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 42.5 | 4.5 | 10 |
| RB | 36.9 | 34.2 | 2.7 | 17 |
| WR | 40.1 | 32.1 | 8.0 | 22 |
| TE | 77.9 | 47.9 | 30.0 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 39.985766857976785 | 37.1 | 2.9 | 47 |

### Pick 36 (round 4): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 3 points at WR, with a 69% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 414 ms, ranker engine, plan call 105, plan age 727 ms, at 07:36:03 PT.
- Engine's reason: waiting likely costs ~3 pts at WR (best option now 24, ~21 by your next turn) · 69% chance he's still there at your next pick · fills your open WR slot · 8 teams picking before you still need a WR · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Travis Etienne Jr. (RB, s=0.511, e=24.1); Drake Maye (QB, s=0.674, e=26.8); Cam Skattebo (RB, s=None, e=None).
- Plan call 105 @pick 36: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 35 drafted / 3 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.69 | 0.69 | 21.0 | 23.9 | waiting likely costs ~3 pts at WR (best option now 24, ~21 by your next turn) · 69% chance |
| Travis Etienne Jr. | RB | 26.3 | 0.51 | 0.51 | 24.1 | 26.3 | waiting likely costs ~2 pts at RB (best option now 26, ~24 by your next turn) · 51% chance |
| Drake Maye | QB | 31.1 | 0.67 | 0.67 | 26.8 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 67% chance |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |
| D'Andre Swift | RB | 21.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.8 | 4.3 | 10 |
| RB | 26.3 | 24.1 | 2.2 | 19 |
| WR | 23.9 | 21.0 | 2.9 | 18 |
| TE | 23.8 | 22.9 | 0.9 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 26.331806855987054 | 24.1 | 2.2 | 44 |

### Pick 45 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 7 points at QB, with a 48% chance he would still be there next turn.
- Driver: via **action**, verified store, 409 ms, ranker engine, plan call 109, plan age 732 ms, at 07:36:43 PT.
- Engine's reason: waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 48% chance he's still there at your next pick · fills your open QB slot · 8 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: True.
- Passed on: Jaylen Warren (RB, s=0.913, e=9.1); Jalen Hurts (QB, s=None, e=None); Trevor Lawrence (QB, s=None, e=None).
- Plan call 109 @pick 45: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 44 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.48 | 0.48 | 23.8 | 31.1 | waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 48% chance |
| Jaylen Warren | RB | 9.3 | 0.91 | 0.91 | 9.1 | 9.3 | safe to wait on RB · 91% chance he's still there at your next pick · fills your open RB sl |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 23.8 | 7.3 | 14 |
| RB | 9.3 | 9.1 | 0.2 | 16 |
| WR | 13.1 | 9.3 | 3.8 | 19 |
| TE | 21.1 | 20.9 | 0.2 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.1 | 0.2 | 42 |

### Pick 56 (round 6): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (83% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 421 ms, ranker engine, plan call 116, plan age 738 ms, at 07:37:58 PT.
- Engine's reason: safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 116 @pick 56: needs {'QB': 0, 'RB': 1, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 55 drafted / 5 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.83 | 0.83 | 8.9 | 9.3 | safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB sl |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Rome Odunze | WR | -0.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.5 | 1.5 | 14 |
| RB | 9.3 | 8.9 | 0.4 | 15 |
| WR | 0.0 | -0.1 | 0.1 | 21 |
| TE | 21.1 | 20.5 | 0.6 | 10 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.9 | 0.4 | 46 |

### Pick 65 (round 7): TreVeyon Henderson (RB)

- In plain English: Took TreVeyon Henderson (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 74% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 422 ms, ranker engine, plan call 120, plan age 740 ms, at 07:38:30 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) · 74% chance he's still there at your next pick · fills a FLEX slot ⛑ backs up Rhamondre Stevenson (13g)
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Christian Watson (WR, s=None, e=None); RJ Harvey (RB, s=None, e=None); Parker Washington (WR, s=None, e=None).
- Plan call 120 @pick 65: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 64 drafted / 6 mine.
- Engine's first choice was **TreVeyon Henderson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| TreVeyon Henderson | RB | 2.9 | 0.74 | 0.74 | 0.7 | 2.9 | waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) ·  |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 14.4 | 1.3 | 19 |
| RB | 2.9 | 0.7 | 2.2 | 19 |
| WR | -0.8 | -2.3 | 1.5 | 23 |
| TE | 21.1 | 18.3 | 2.8 | 15 |
| K | 13.5 | 13.4 | 0.1 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 2.872545684015563 | 0.7 | 2.2 | 57 |

### Pick 76 (round 8): RJ Harvey (RB)

- In plain English: Lineup already full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 88 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 298 ms, ranker engine, plan call 127, plan age 634 ms, at 07:39:49 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 88 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: DK Metcalf (WR, s=0.691, e=-9.5); Kenny Gainwell (RB, s=None, e=None); Carnell Tate (WR, s=None, e=None).
- Plan call 127 @pick 76: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 75 drafted / 7 mine.
- Engine's first choice was **RJ Harvey** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| RJ Harvey | RB | -5.4 | 0.93 | 0.93 | -5.5 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs |
| DK Metcalf | WR | -9.2 | 0.69 | 0.69 | -9.5 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.6 | 0.2 | 19 |
| RB | -5.4 | -5.5 | 0.1 | 32 |
| WR | -9.2 | -9.5 | 0.3 | 38 |
| TE | 21.1 | 19.4 | 1.7 | 21 |
| K | 13.5 | 13.2 | 0.3 | 11 |
| DEF | 18.0 | 17.9 | 0.1 | 8 |

### Pick 85 (round 9): Kenny Gainwell (RB)

- In plain English: Lineup already full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.1 points a week over the waiver wire (Josh Jacobs), worth about 23 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 302 ms, ranker engine, plan call 133, plan age 625 ms, at 07:40:50 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: DK Metcalf (WR, s=0.716, e=-9.6); Kyle Pitts Sr. (TE, s=0.838, e=20.7); George Kittle (TE, s=None, e=None).
- Plan call 133 @pick 85: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 84 drafted / 8 mine.
- Engine's first choice was **Kenny Gainwell** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kenny Gainwell | RB | -6.2 | 0.93 | 0.93 | -7.2 | -6.2 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1 |
| DK Metcalf | WR | -9.2 | 0.72 | 0.72 | -9.6 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| Kyle Pitts Sr. | TE | 21.1 | 0.84 | 0.84 | 20.7 | 21.1 | bench insurance: covers 1 TE starter ~3.9 wks/season · +2.9/wk over the wire (Cade Otton)  |
| George Kittle | TE | 19.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Dallas Goedert | TE | 13.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.3 | 1.5 | 18 |
| RB | -6.2 | -7.2 | 1.0 | 29 |
| WR | -9.2 | -9.6 | 0.4 | 37 |
| TE | 21.1 | 20.7 | 0.4 | 21 |
| K | 13.5 | 13.3 | 0.2 | 12 |
| DEF | 16.0 | 15.8 | 0.2 | 10 |

### Pick 96 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 363 ms, ranker engine, plan call 142, plan age 725 ms, at 07:42:25 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: George Kittle (TE, s=0.846, e=18.7); Patrick Mahomes II (QB, s=0.816, e=11.5); J.K. Dobbins (RB, s=0.861, e=-21.4).
- Plan call 142 @pick 96: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 95 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.97 | 0.97 | -10.7 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| George Kittle | TE | 19.8 | 0.85 | 0.85 | 18.7 | 19.8 | bench insurance: covers 1 TE starter ~3.9 wks/season · +2.8/wk over the wire (Cade Otton)  |
| Patrick Mahomes II | QB | 12.8 | 0.82 | 0.82 | 11.5 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| J.K. Dobbins | RB | -20.6 | 0.86 | 0.86 | -21.4 | -20.6 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +8. |
| Dallas Goedert | TE | 13.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Kelce | TE | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.5 | 1.3 | 17 |
| RB | -20.6 | -21.4 | 0.8 | 27 |
| WR | -10.6 | -10.7 | 0.1 | 36 |
| TE | 19.8 | 18.7 | 1.1 | 19 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 14.0 | 13.9 | 0.1 | 8 |

### Pick 105 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 390 ms, ranker engine, plan call 146, plan age 723 ms, at 07:43:01 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Michael Pittman Jr. (WR, s=0.904, e=-13.6); Aaron Jones Sr. (RB, s=0.901, e=-26.2); Matthew Stafford (QB, s=None, e=None).
- Plan call 146 @pick 105: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 104 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.91 | 0.91 | 12.1 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Michael Pittman Jr. | WR | -13.3 | 0.90 | 0.90 | -13.6 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.90 | 0.90 | -26.2 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.1 | 0.7 | 16 |
| RB | -25.9 | -26.2 | 0.3 | 25 |
| WR | -13.3 | -13.6 | 0.3 | 32 |
| TE | 10.9 | 10.1 | 0.8 | 17 |
| K | 12.0 | 11.4 | 0.6 | 14 |
| DEF | 14.0 | 13.9 | 0.1 | 10 |

### Pick 116 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.5 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 403 ms, ranker engine, plan call 153, plan age 735 ms, at 07:44:20 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.942, e=-26.2); Jakobi Meyers (WR, s=None, e=None); Makai Lemon (WR, s=None, e=None).
- Plan call 153 @pick 116: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 115 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -13.3 | 0.97 | 0.97 | -13.5 | -13.3 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5 |
| Aaron Jones Sr. | RB | -25.9 | 0.94 | 0.94 | -26.2 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jayden Reed | WR | -28.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 13 |
| RB | -25.9 | -26.2 | 0.3 | 21 |
| WR | -13.3 | -13.5 | 0.2 | 29 |
| TE | 10.9 | 10.7 | 0.2 | 16 |
| K | 12.0 | 11.5 | 0.5 | 15 |
| DEF | 14.0 | 13.9 | 0.1 | 11 |

### Pick 125 (round 13): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +7.9 points a week over the waiver wire (Zach Charbonnet), worth about 2 points. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 319 ms, ranker engine, plan call 159, plan age 651 ms, at 07:45:16 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Zach Charbonnet) ≈ 2 pts
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.938, e=-21.9); Makai Lemon (WR, s=None, e=None); Romeo Doubs (WR, s=None, e=None).
- Plan call 159 @pick 125: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 124 drafted / 12 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.94 | 0.94 | -26.2 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | 0.94 | 0.94 | -21.9 | -21.5 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +2. |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jayden Reed | WR | -28.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 11 |
| RB | -25.9 | -26.2 | 0.3 | 21 |
| WR | -21.5 | -21.9 | 0.4 | 26 |
| TE | 0.5 | 0.4 | 0.1 | 14 |
| K | 9.0 | 8.3 | 0.7 | 14 |
| DEF | 14.0 | 13.9 | 0.1 | 11 |

### Pick 136 (round 14): Eagles (DEF)

- In plain English: Took Philadelphia Eagles (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (69% to survive, but nobody better was worth waiting for). The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 430 ms, ranker engine, plan call 165, plan age 764 ms, at 07:46:19 PT.
- Engine's reason: safe to wait on DEF · 69% chance he's still there at your next pick · fills your open DEF slot · 6 teams picking before you still need a DEF · two-pick plan: pair with the ~29-pt RB expected at your next turn
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Cam Little (K, s=0.825, e=8.4); Minnesota Vikings (DEF, s=None, e=None); Eddy Pineiro (K, s=None, e=None).
- Plan call 165 @pick 136: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 10], state store with 135 drafted / 13 mine.
- Engine's first choice was **Philadelphia Eagles** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Philadelphia Eagles | DEF | 10.0 | 0.69 | 0.69 | 9.3 | 10.0 | safe to wait on DEF · 69% chance he's still there at your next pick · fills your open DEF  |
| Cam Little | K | 9.0 | 0.82 | 0.82 | 8.4 | 9.0 | safe to wait on K · 82% chance he's still there at your next pick · fills your open K slot |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Eddy Pineiro | K | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Pittsburgh Steelers | DEF | 6.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.7 | -14.7 | 0.0 | 10 |
| RB | -30.3 | -30.4 | 0.1 | 20 |
| WR | -21.5 | -21.9 | 0.4 | 23 |
| TE | -6.3 | -6.3 | 0.0 | 11 |
| K | 9.0 | 8.4 | 0.6 | 14 |
| DEF | 10.0 | 9.3 | 0.7 | 9 |

### Pick 145 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 302 ms, ranker engine, plan call 170, plan age 657 ms, at 07:47:10 PT.
- Engine's reason: fills your open K slot
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 170 @pick 145: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [2, 3, 10], state store with 144 drafted / 14 mine.
- Engine's first choice was **Eddy Pineiro** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Eddy Pineiro | K | 6.0 | - | - | - | - | fills your open K slot |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 30-50% | 13 | 43% | 8% |
| 50-70% | 19 | 64% | 53% |
| 70-90% | 53 | 80% | 40% |
| 90-100% | 82 | 95% | 84% |

167 predictions over 73 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    07:33:45  plan #91 for pick 12: De'Von Achane RB 65% “waiting likely costs ~9 pts at RB (best opti” · CeeDee Lamb WR 71% “waiting likely costs ~1 pts at WR (best opti” · Trey McBride TE 91% “waiting likely costs ~2 pts at TE (best opti”
    07:33:46  driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    07:33:55  pick 12  Derrick Henry (RB) taken by seat 9 in 10 s — a target is gone
    07:33:59  plan #93 for pick 13: De'Von Achane RB 72% “waiting likely costs ~9 pts at RB (best opti” · CeeDee Lamb WR 79% “safe to wait on WR” · Trey McBride TE 94% “waiting likely costs ~1 pts at TE (best opti”
    07:34:08  pick 13  Justin Jefferson (WR) taken by seat 8 in 13 s — a target is gone
    07:34:10  pick 14  CeeDee Lamb (WR) taken by seat 7 in 3 s — a target is gone (was 79% to survive)
    07:34:11  plan #94 for pick 15: De'Von Achane RB 89% “waiting likely costs ~4 pts at RB (best opti” · Trey McBride TE 98% “safe to wait on TE” · Drake London WR 91% “safe to wait on WR”
    07:34:22  pick 15  Kenneth Walker III (RB) taken by seat 6 in 12 s
    07:34:27  plan #95 for pick 16: De'Von Achane RB 54% “waiting likely costs ~16 pts at RB (best opt” · Trey McBride TE 64% “waiting likely costs ~13 pts at TE (best opt” · Drake London WR 39% “waiting likely costs ~6 pts at WR (best opti”
    07:34:27  ON THE CLOCK, pick 16 · plan #95 (0.0 s old) · lineup needs QB RBx2 WR TE FLEX K DEF
    07:34:27  PICKED De'Von Achane (RB) via action, confirmed in 412 ms — chose De'Von Achane (RB): waiting would likely cost about 16 points at RB, 54% to still be there next turn; top projection left was Josh Allen, passed on purpose
    07:34:30  pick 17  Omarion Hampton (RB) taken by seat 4 in 2 s
    07:34:30  pick 18  Nico Collins (WR) taken by seat 3 in 0 s — a target is gone
    07:34:30  plan #96 for pick 19: Trey McBride TE 63% “waiting likely costs ~13 pts at TE (best opt” · Drake London WR 46% “waiting likely costs ~5 pts at WR (best opti” · Kyren Williams RB 65% “waiting likely costs ~2 pts at RB (best opti”
    07:34:31  pick 19  Drake London (WR) taken by seat 2 in 2 s INSTANTLY (autopick) — a target is gone (was 46% to survive)
    07:34:34  pick 20  George Pickens (WR) taken by seat 1 in 3 s
    07:34:37  pick 21  Kyren Williams (RB) taken by seat 1 in 3 s — a target is gone (was 65% to survive)
    07:34:42  plan #97 for pick 22: Trey McBride TE 76% “waiting likely costs ~6 pts at TE (best opti” · A.J. Brown WR 61% “waiting likely costs ~2 pts at WR (best opti” · Javonte Williams RB 91% “safe to wait on RB”
    07:34:47  heartbeat sent (Yahoo told we are not idle)
    07:34:47  pick 22  A.J. Brown (WR) taken by seat 2 in 10 s — a target is gone (was 61% to survive)
    07:34:48  pick 23  Brock Bowers (TE) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone
    07:34:51  pick 24  Malik Nabers (WR) taken by seat 4 in 3 s
    07:34:52  plan #98 for pick 25: Trey McBride TE 45% “waiting likely costs ~30 pts at TE (best opt” · Chris Olave WR 33% “waiting likely costs ~8 pts at WR (best opti” · Javonte Williams RB 49% “waiting likely costs ~3 pts at RB (best opti”
    07:34:52  ON THE CLOCK, pick 25 · plan #98 (0.0 s old) · lineup needs QB RB WR TE FLEX K DEF
    07:34:52  PICKED Trey McBride (TE) via action, confirmed in 400 ms — chose Trey McBride (TE): waiting would likely cost about 30 points at TE, 45% to still be there next turn; top projection left was Josh Allen, passed on purpose
    07:34:55  plan #99 for pick 26: Chris Olave WR 31% “waiting likely costs ~9 pts at WR (best opti” · Javonte Williams RB 39% “waiting likely costs ~3 pts at your FLEX spo” · Josh Allen QB 72% “waiting likely costs ~5 pts at QB (best opti”
    07:34:59  pick 26  Josh Allen (QB) taken by seat 6 in 7 s — a target is gone (was 72% to survive)
    07:35:02  pick 27  Chris Olave (WR) taken by seat 7 in 3 s — a target is gone (was 31% to survive)
    07:35:07  plan #100 for pick 28: Rashee Rice WR 47% “waiting likely costs ~6 pts at WR (best opti” · Javonte Williams RB 45% “waiting likely costs ~3 pts at your FLEX spo” · Drake Maye QB 89% “waiting likely costs ~1 pts at QB (best opti”
    07:35:11  pick 28  DeVonta Smith (WR) taken by seat 8 in 8 s — a target is gone
    07:35:20  plan #101 for pick 29: Rashee Rice WR 43% “waiting likely costs ~6 pts at WR (best opti” · Javonte Williams RB 50% “waiting likely costs ~2 pts at your FLEX spo” · Drake Maye QB 91% “waiting likely costs ~1 pts at QB (best opti”
    07:35:23  pick 29  Tee Higgins (WR) taken by seat 9 in 12 s
    07:35:24  pick 30  Ashton Jeanty (RB) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    07:35:25  pick 31  Jeremiyah Love (RB) taken by seat 10 in 1 s INSTANTLY (autopick)
    07:35:32  plan #102 for pick 32: Javonte Williams RB 66% “waiting likely costs ~4 pts at your FLEX spo” · Rashee Rice WR 78% “waiting likely costs ~2 pts at WR (best opti” · Drake Maye QB 92% “waiting likely costs ~1 pts at QB (best opti”
    07:35:44  pick 32  Rashee Rice (WR) taken by seat 9 in 19 s — a target is gone (was 78% to survive)
    07:35:44  plan #103 for pick 33: Javonte Williams RB 75% “waiting likely costs ~3 pts at your FLEX spo” · Garrett Wilson WR 92% “safe to wait on WR” · Drake Maye QB 94% “safe to wait on QB”
    07:35:49  heartbeat sent (Yahoo told we are not idle)
    07:35:51  pick 33  Colston Loveland (TE) taken by seat 8 in 7 s
    07:35:58  plan #104 for pick 34: Javonte Williams RB 81% “waiting likely costs ~2 pts at your FLEX spo” · Garrett Wilson WR 97% “safe to wait on WR” · Drake Maye QB 96% “safe to wait on QB”
    07:35:58  pick 34  Javonte Williams (RB) taken by seat 7 in 6 s — a target is gone (was 81% to survive)
    07:36:02  pick 35  Zay Flowers (WR) taken by seat 6 in 4 s — a target is gone
    07:36:03  plan #105 for pick 36: Garrett Wilson WR 69% “waiting likely costs ~3 pts at WR (best opti” · Travis Etienne Jr. RB 51% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 67% “waiting likely costs ~4 pts at QB (best op
    07:36:03  ON THE CLOCK, pick 36 · plan #105 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    07:36:03  PICKED Garrett Wilson (WR) via action, confirmed in 414 ms — chose Garrett Wilson (WR): waiting would likely cost about 3 points at WR, 69% to still be there next turn; top projection left was Drake Maye, passed on purpose
    07:36:06  pick 37  Jaylen Waddle (WR) taken by seat 4 in 2 s
    07:36:06  plan #106 for pick 38: Travis Etienne Jr. RB 54% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 69% “waiting likely costs ~4 pts at QB (best opti” · Cam Skattebo RB “depth fallback (engine list exhausted)”
    07:36:11  pick 38  Breece Hall (RB) taken by seat 3 in 5 s
    07:36:11  pick 39  Travis Etienne Jr. (RB) taken by seat 2 in 0 s — a target is gone (was 54% to survive)
    07:36:19  plan #107 for pick 40: Cam Skattebo RB 63% “waiting likely costs ~3 pts at your FLEX spo” · Drake Maye QB 73% “waiting likely costs ~4 pts at QB (best opti” · D'Andre Swift RB “depth fallback (engine list exhausted)”
    07:36:21  pick 40  Tetairoa McMillan (WR) taken by seat 1 in 10 s — a target is gone
    07:36:26  pick 41  Cam Skattebo (RB) taken by seat 1 in 5 s — a target is gone (was 63% to survive)
    07:36:31  plan #108 for pick 42: D'Andre Swift RB 73% “waiting likely costs ~3 pts at your FLEX spo” · Drake Maye QB 83% “waiting likely costs ~2 pts at QB (best opti” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:36:40  pick 42  D'Andre Swift (RB) taken by seat 2 in 13 s — a target is gone (was 73% to survive)
    07:36:40  pick 43  Ladd McConkey (WR) taken by seat 3 in 0 s INSTANTLY (autopick) — a target is gone
    07:36:41  pick 44  Tyler Warren (TE) taken by seat 4 in 2 s INSTANTLY (autopick)
    07:36:42  plan #109 for pick 45: Drake Maye QB 48% “waiting likely costs ~7 pts at QB (best opti” · Jaylen Warren RB 91% “safe to wait on RB” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    07:36:42  ON THE CLOCK, pick 45 · plan #109 (0.0 s old) · lineup needs QB RB FLEX K DEF
    07:36:43  PICKED Drake Maye (QB) via action, confirmed in 409 ms — chose Drake Maye (QB): waiting would likely cost about 7 points at QB, 48% to still be there next turn
    07:36:46  plan #110 for pick 46: Jaylen Warren RB 95% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Emeka Egbuka WR “depth fallback (engine list exhausted)”
    07:36:53  pick 46  Bucky Irving (RB) taken by seat 6 in 10 s — a target is gone
    07:36:53  heartbeat sent (Yahoo told we are not idle)
    07:36:58  plan #111 for pick 47: Jaylen Warren RB 93% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Emeka Egbuka WR “depth fallback (engine list exhausted)”
    07:37:01  pick 47  Bhayshul Tuten (RB) taken by seat 7 in 8 s
    07:37:11  plan #112 for pick 48: Jaylen Warren RB 94% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Emeka Egbuka WR “depth fallback (engine list exhausted)”
    07:37:23  pick 48  Luther Burden III (WR) taken by seat 8 in 22 s
    07:37:24  plan #113 for pick 49: Jaylen Warren RB 96% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Emeka Egbuka WR “depth fallback (engine list exhausted)”
    07:37:26  pick 49  David Montgomery (RB) taken by seat 9 in 2 s INSTANTLY (autopick)
    07:37:26  pick 50  Emeka Egbuka (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    07:37:27  pick 51  Lamar Jackson (QB) taken by seat 10 in 1 s INSTANTLY (autopick)
    07:37:33  pick 52  Terry McLaurin (WR) taken by seat 9 in 6 s — a target is gone
    07:37:36  plan #114 for pick 53: Jaylen Warren RB 98% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:37:40  pick 53  Jadarian Price (RB) taken by seat 8 in 7 s
    07:37:48  plan #115 for pick 54: Jaylen Warren RB 99% “safe to wait on RB” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    07:37:51  pick 54  Quinshon Judkins (RB) taken by seat 7 in 11 s — a target is gone
    07:37:53  heartbeat sent (Yahoo told we are not idle)
    07:37:57  pick 55  Davante Adams (WR) taken by seat 6 in 5 s — a target is gone
    07:37:57  plan #116 for pick 56: Jaylen Warren RB 83% “safe to wait on RB” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    07:37:57  ON THE CLOCK, pick 56 · plan #116 (0.0 s old) · lineup needs RB FLEX K DEF
    07:37:58  PICKED Jaylen Warren (RB) via action, confirmed in 421 ms — chose Jaylen Warren (RB): nothing urgent, the most valuable player who fills a slot (83% to survive, nobody better worth waiting for); top projection left was Jalen Hurts
    07:38:01  plan #117 for pick 57: Rhamondre Stevenson RB 88% “waiting likely costs ~1 pts at your FLEX spo” · TreVeyon Henderson RB “depth fallback (engine list exhausted)” · Jameson Williams WR “depth fallback (engine list exhausted)”
    07:38:06  pick 57  Rome Odunze (WR) taken by seat 4 in 8 s — a target is gone
    07:38:06  pick 58  Rhamondre Stevenson (RB) taken by seat 3 in 0 s — a target is gone (was 88% to survive)
    07:38:10  pick 59  DJ Moore (WR) taken by seat 2 in 4 s — a target is gone
    07:38:13  plan #118 for pick 60: TreVeyon Henderson RB 90% “safe to wait on your FLEX spot” · Jameson Williams WR “depth fallback (engine list exhausted)” · Christian Watson WR “depth fallback (engine list exhausted)”
    07:38:16  pick 60  Jameson Williams (WR) taken by seat 1 in 7 s — a target is gone
    07:38:18  pick 61  Dak Prescott (QB) taken by seat 1 in 2 s INSTANTLY (autopick)
    07:38:21  pick 62  Mike Evans (WR) taken by seat 2 in 3 s — a target is gone
    07:38:22  pick 63  Joe Burrow (QB) taken by seat 3 in 1 s INSTANTLY (autopick)
    07:38:25  plan #119 for pick 64: TreVeyon Henderson RB 98% “safe to wait on your FLEX spot” · Christian Watson WR “depth fallback (engine list exhausted)” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:38:28  pick 64  Jalen Hurts (QB) taken by seat 4 in 6 s
    07:38:29  plan #120 for pick 65: TreVeyon Henderson RB 74% “waiting likely costs ~2 pts at your FLEX spo” · Christian Watson WR “depth fallback (engine list exhausted)” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:38:29  ON THE CLOCK, pick 65 · plan #120 (0.0 s old) · lineup needs FLEX K DEF
    07:38:30  PICKED TreVeyon Henderson (RB) via action, confirmed in 422 ms — chose TreVeyon Henderson (RB): waiting would likely cost about 2 points at your FLEX spot, 74% to still be there next turn; top projection left was Trevor Lawrence, 
    07:38:33  plan #121 for pick 66: Rico Dowdle RB 87% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 70% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:38:38  pick 66  Tucker Kraft (TE) taken by seat 6 in 8 s
    07:38:40  pick 67  Justin Herbert (QB) taken by seat 7 in 2 s INSTANTLY (autopick)
    07:38:45  plan #122 for pick 68: Rico Dowdle RB 85% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 72% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:38:54  heartbeat sent (Yahoo told we are not idle)
    07:38:56  pick 68  Parker Washington (WR) taken by seat 8 in 16 s — a target is gone
    07:38:58  plan #123 for pick 69: Rico Dowdle RB 90% “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 75% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:39:00  pick 69  Christian Watson (WR) taken by seat 9 in 4 s — a target is gone (was 75% to survive)
    07:39:00  pick 70  Sam LaPorta (TE) taken by seat 10 in 0 s
    07:39:00  pick 71  Jayden Daniels (QB) taken by seat 10 in 0 s
    07:39:09  pick 72  Trevor Lawrence (QB) taken by seat 9 in 9 s
    07:39:10  plan #124 for pick 73: Rico Dowdle RB 92% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 93% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    07:39:26  pick 73  Rico Dowdle (RB) taken by seat 8 in 16 s — a target is gone (was 92% to survive)
    07:39:35  plan #126 for pick 74: RJ Harvey RB 99% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 95% “bench insurance: covers 2 WR starters ~6.5 w” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:39:42  pick 74  Isaiah Likely (TE) taken by seat 7 in 16 s
    07:39:48  pick 75  Marvin Harrison Jr. (WR) taken by seat 6 in 6 s — a target is gone
    07:39:48  plan #127 for pick 76: RJ Harvey RB 93% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 69% “bench insurance: covers 2 WR starters ~6.5 w” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    07:39:48  ON THE CLOCK, pick 76 · plan #127 (0.0 s old) · lineup needs K DEF
    07:39:49  PICKED RJ Harvey (RB) via action, confirmed in 298 ms — lineup full, so RJ Harvey (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +9.1 a week over the wire, about 88 points; top projection left was Patrick Ma
    07:39:52  plan #128 for pick 77: Kenny Gainwell RB 98% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 67% “bench insurance: covers 2 WR starters ~6.5 w” · Carnell Tate WR “depth fallback (engine list exhausted)”
    07:39:56  pick 77  Caleb Williams (QB) taken by seat 4 in 7 s
    07:39:56  pick 78  Brian Thomas Jr. (WR) taken by seat 3 in 0 s — a target is gone
    07:39:56  heartbeat sent (Yahoo told we are not idle)
    07:40:04  plan #129 for pick 79: Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 79% “bench insurance: covers 2 WR starters ~6.5 w” · Carnell Tate WR “depth fallback (engine list exhausted)”
    07:40:17  pick 79  Chris Godwin Jr. (WR) taken by seat 2 in 21 s
    07:40:29  plan #131 for pick 80: Kenny Gainwell RB 100% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 76% “bench insurance: covers 2 WR starters ~6.5 w” · Carnell Tate WR “depth fallback (engine list exhausted)”
    07:40:37  pick 80  Carnell Tate (WR) taken by seat 1 in 20 s — a target is gone
    07:40:41  plan #132 for pick 81: Kenny Gainwell RB 100% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 80% “bench insurance: covers 2 WR starters ~6.5 w” · Wan'Dale Robinson WR “depth fallback (engine list exhausted)”
    07:40:45  pick 81  MarShawn Lloyd (RB) taken by seat 1 in 8 s
    07:40:47  pick 82  Courtland Sutton (WR) taken by seat 2 in 2 s INSTANTLY (autopick) — a target is gone
    07:40:47  pick 83  Jonathon Brooks (RB) taken by seat 3 in 0 s INSTANTLY (autopick)
    07:40:48  pick 84  Texans (DEF) taken by seat 4 in 2 s INSTANTLY (autopick)
    07:40:49  plan #133 for pick 85: Kenny Gainwell RB 93% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 72% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 84% “bench insurance: covers 1 TE starter ~3.9 wk”
    07:40:49  ON THE CLOCK, pick 85 · plan #133 (0.0 s old) · lineup needs K DEF
    07:40:50  PICKED Kenny Gainwell (RB) via action, confirmed in 302 ms — lineup full, so Kenny Gainwell (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +9.1 a week over the wire, about 23 points; top projection left was 
    07:40:53  plan #134 for pick 86: DK Metcalf WR 73% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 81% “bench insurance: covers 1 TE starter ~3.9 wk” · Tony Pollard RB 70% “bench insurance: covers 3 RB starters behind”
    07:40:57  pick 86  Brandon Aubrey (K) taken by seat 6 in 7 s
    07:40:57  heartbeat sent (Yahoo told we are not idle)
    07:41:00  pick 87  Tony Pollard (RB) taken by seat 7 in 3 s — a target is gone (was 70% to survive)
    07:41:05  plan #135 for pick 88: DK Metcalf WR 80% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 86% “bench insurance: covers 1 TE starter ~3.9 wk” · J.K. Dobbins RB 74% “bench insurance: covers 3 RB starters behind”
    07:41:07  pick 88  Brock Purdy (QB) taken by seat 8 in 8 s
    07:41:18  plan #136 for pick 89: DK Metcalf WR 78% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 87% “bench insurance: covers 1 TE starter ~3.9 wk” · J.K. Dobbins RB 77% “bench insurance: covers 3 RB starters behind”
    07:41:23  pick 89  Kyle Pitts Sr. (TE) taken by seat 9 in 16 s — a target is gone (was 87% to survive)
    07:41:24  pick 90  DK Metcalf (WR) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone (was 78% to survive)
    07:41:25  pick 91  Harold Fannin Jr. (TE) taken by seat 10 in 1 s INSTANTLY (autopick) — a target is gone
    07:41:30  plan #137 for pick 92: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 93% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 91% “bench insurance: covers 3 RB starters
    07:41:51  pick 92  KC Concepcion (WR) taken by seat 9 in 26 s
    07:41:55  plan #139 for pick 93: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 95% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 94% “bench insurance: covers 3 RB starters
    07:41:57  heartbeat sent (Yahoo told we are not idle)
    07:42:01  pick 93  Blake Corum (RB) taken by seat 8 in 10 s
    07:42:08  plan #140 for pick 94: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 97% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 95% “bench insurance: covers 3 RB starters
    07:42:10  pick 94  Rams (DEF) taken by seat 7 in 9 s
    07:42:20  plan #141 for pick 95: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 98% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 97% “bench insurance: covers 3 RB starter
    07:42:24  pick 95  Broncos (DEF) taken by seat 6 in 14 s
    07:42:25  plan #142 for pick 96: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · George Kittle TE 85% “bench insurance: covers 1 TE starter ~3.9 wk” · Patrick Mahomes II QB 82% “bench insurance: covers 1 QB starter
    07:42:25  ON THE CLOCK, pick 96 · plan #142 (0.0 s old) · lineup needs K DEF
    07:42:25  PICKED Wan'Dale Robinson (WR) via action, confirmed in 363 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    07:42:28  plan #143 for pick 97: George Kittle TE 87% “bench insurance: covers 1 TE starter ~3.9 wk” · Patrick Mahomes II QB 79% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 86% “bench insurance: covers 3 RB starters beh
    07:42:28  pick 97  Josh Downs (WR) taken by seat 4 in 3 s
    07:42:30  pick 98  Michael Wilson (WR) taken by seat 3 in 1 s INSTANTLY (autopick)
    07:42:40  plan #144 for pick 99: George Kittle TE 89% “bench insurance: covers 1 TE starter ~3.9 wk” · Patrick Mahomes II QB 85% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 93% “bench insurance: covers 3 RB starters beh
    07:42:41  pick 99  Dallas Goedert (TE) taken by seat 2 in 11 s — a target is gone
    07:42:49  pick 100  George Kittle (TE) taken by seat 1 in 8 s — a target is gone (was 89% to survive)
    07:42:49  pick 101  Jacory Croskey-Merritt (RB) taken by seat 1 in 1 s INSTANTLY (autopick)
    07:42:52  plan #145 for pick 102: Patrick Mahomes II QB 91% “bench insurance: covers 1 QB starter ~3.6 wk” · J.K. Dobbins RB 96% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR 97% “bench insurance: covers 2 WR start
    07:42:57  pick 102  Stefon Diggs (WR) taken by seat 2 in 7 s
    07:42:58  pick 103  Bo Nix (QB) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone
    07:42:58  heartbeat sent (Yahoo told we are not idle)
    07:43:00  pick 104  J.K. Dobbins (RB) taken by seat 4 in 2 s INSTANTLY (autopick) — a target is gone (was 96% to survive)
    07:43:01  plan #146 for pick 105: Patrick Mahomes II QB 91% “bench insurance: covers 1 QB starter ~3.6 wk” · Michael Pittman Jr. WR 90% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 90% “bench insurance: covers 3 RB st
    07:43:01  ON THE CLOCK, pick 105 · plan #146 (0.0 s old) · lineup needs K DEF
    07:43:01  PICKED Patrick Mahomes II (QB) via action, confirmed in 390 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    07:43:04  plan #147 for pick 106: Michael Pittman Jr. WR 91% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 91% “bench insurance: covers 3 RB starters behind” · Quentin Johnston WR “depth fallback (engine list exhausted
    07:43:04  pick 106  Alec Pierce (WR) taken by seat 6 in 3 s — a target is gone
    07:43:17  plan #148 for pick 107: Michael Pittman Jr. WR 88% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 93% “bench insurance: covers 3 RB starters behind” · Quentin Johnston WR “depth fallback (engine list exhausted
    07:43:21  pick 107  Jordan Addison (WR) taken by seat 7 in 16 s — a target is gone
    07:43:27  pick 108  Jaxson Dart (QB) taken by seat 8 in 6 s
    07:43:29  plan #149 for pick 109: Michael Pittman Jr. WR 94% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 95% “bench insurance: covers 3 RB starters behind” · Quentin Johnston WR “depth fallback (engine list exhausted
    07:43:33  pick 109  Chuba Hubbard (RB) taken by seat 9 in 6 s
    07:43:33  pick 110  Quentin Johnston (WR) taken by seat 10 in 0 s — a target is gone
    07:43:33  pick 111  Jordan Mason (RB) taken by seat 10 in 0 s
    07:43:40  pick 112  Matthew Stafford (QB) taken by seat 9 in 7 s
    07:43:41  plan #150 for pick 113: Michael Pittman Jr. WR 98% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 97% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    07:43:46  pick 113  Dalton Kincaid (TE) taken by seat 8 in 6 s
    07:43:54  plan #151 for pick 114: Michael Pittman Jr. WR 99% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 98% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    07:43:58  heartbeat sent (Yahoo told we are not idle)
    07:44:10  pick 114  Josh Jacobs (RB) taken by seat 7 in 24 s
    07:44:18  pick 115  Kyle Monangai (RB) taken by seat 6 in 8 s — a target is gone
    07:44:19  plan #153 for pick 116: Michael Pittman Jr. WR 97% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 94% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    07:44:19  ON THE CLOCK, pick 116 · plan #153 (0.0 s old) · lineup needs K DEF
    07:44:20  PICKED Michael Pittman Jr. (WR) via action, confirmed in 403 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.5 a week over the wire, about 2 points; top projection 
    07:44:22  plan #154 for pick 117: Aaron Jones Sr. RB 95% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 96% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    07:44:35  pick 117  Mark Andrews (TE) taken by seat 4 in 15 s
    07:44:37  pick 118  Travis Kelce (TE) taken by seat 3 in 2 s INSTANTLY (autopick)
    07:44:45  pick 119  Jared Goff (QB) taken by seat 2 in 8 s
    07:44:47  plan #156 for pick 120: Aaron Jones Sr. RB 98% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 97% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    07:44:49  pick 120  Jalen Coker (WR) taken by seat 1 in 5 s
    07:44:50  pick 121  Jordan Love (QB) taken by seat 1 in 1 s INSTANTLY (autopick)
    07:44:59  heartbeat sent (Yahoo told we are not idle)
    07:44:59  plan #157 for pick 122: Aaron Jones Sr. RB 99% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 99% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    07:45:10  pick 122  Cameron Dicker (K) taken by seat 2 in 20 s
    07:45:10  pick 123  De'Zhaun Stribling (WR) taken by seat 3 in 0 s INSTANTLY (autopick)
    07:45:11  plan #158 for pick 124: Aaron Jones Sr. RB 100% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 98% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    07:45:15  pick 124  Ka'imi Fairbairn (K) taken by seat 4 in 5 s
    07:45:15  plan #159 for pick 125: Aaron Jones Sr. RB 94% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 94% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    07:45:16  ON THE CLOCK, pick 125 · plan #159 (0.0 s old) · lineup needs K DEF
    07:45:16  PICKED Aaron Jones Sr. (RB) via action, confirmed in 319 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +7.9 a week over the wire, about 2 points; top projection left was
    07:45:19  plan #160 for pick 126: Seattle Seahawks DEF 99% “safe to wait on DEF” · Cam Little K 67% “safe to wait on K” · Philadelphia Eagles DEF “depth fallback (engine list exhausted)”
    07:45:19  pick 126  Jake Ferguson (TE) taken by seat 6 in 3 s
    07:45:26  pick 127  Tyler Shough (QB) taken by seat 7 in 7 s
    07:45:31  plan #161 for pick 128: Seattle Seahawks DEF 98% “safe to wait on DEF” · Cam Little K 72% “safe to wait on K” · Philadelphia Eagles DEF “depth fallback (engine list exhausted)”
    07:45:42  pick 128  Jason Myers (K) taken by seat 8 in 16 s — a target is gone
    07:45:43  plan #162 for pick 129: Seattle Seahawks DEF 99% “safe to wait on DEF” · Cam Little K 79% “safe to wait on K” · Philadelphia Eagles DEF “depth fallback (engine list exhausted)”
    07:45:50  pick 129  Hunter Henry (TE) taken by seat 9 in 8 s
    07:45:50  pick 130  Jayden Reed (WR) taken by seat 10 in 0 s INSTANTLY (autopick)
    07:45:51  pick 131  Seahawks (DEF) taken by seat 10 in 1 s INSTANTLY (autopick)
    07:45:56  plan #163 for pick 132: Philadelphia Eagles DEF 88% “safe to wait on DEF” · Cam Little K 92% “safe to wait on K” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    07:45:58  pick 132  Patriots (DEF) taken by seat 9 in 7 s
    07:45:59  heartbeat sent (Yahoo told we are not idle)
    07:46:08  plan #164 for pick 133: Philadelphia Eagles DEF 91% “safe to wait on DEF” · Cam Little K 93% “safe to wait on K” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    07:46:12  pick 133  Matthew Golden (WR) taken by seat 8 in 14 s
    07:46:15  pick 134  Chig Okonkwo (TE) taken by seat 7 in 3 s
    07:46:18  pick 135  Makai Lemon (WR) taken by seat 6 in 3 s
    07:46:19  plan #165 for pick 136: Philadelphia Eagles DEF 69% “safe to wait on DEF” · Cam Little K 83% “safe to wait on K” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    07:46:19  ON THE CLOCK, pick 136 · plan #165 (0.0 s old) · lineup needs K DEF
    07:46:19  PICKED Philadelphia Eagles (DEF) via action, confirmed in 430 ms — chose Philadelphia Eagles (DEF): nothing urgent, the most valuable player who fills a slot (69% to survive, nobody better worth waiting for); top projection left w
    07:46:22  plan #166 for pick 137: Cam Little K 82% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Tyler Loop K “depth fallback (engine list exhausted)”
    07:46:30  pick 137  Xavier Worthy (WR) taken by seat 4 in 11 s
    07:46:31  pick 138  Vikings (DEF) taken by seat 3 in 1 s INSTANTLY (autopick)
    07:46:34  plan #167 for pick 139: Cam Little K 85% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Tyler Loop K “depth fallback (engine list exhausted)”
    07:46:43  pick 139  Ravens (DEF) taken by seat 2 in 12 s
    07:46:46  pick 140  Cairo Santos (K) taken by seat 1 in 4 s — a target is gone
    07:46:47  plan #168 for pick 141: Cam Little K 92% “safe to wait on K” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Tyler Loop K “depth fallback (engine list exhausted)”
    07:46:53  pick 141  Steelers (DEF) taken by seat 1 in 6 s
    07:46:54  pick 142  Deebo Samuel Sr. (WR) taken by seat 2 in 2 s INSTANTLY (autopick)
    07:46:54  pick 143  Cam Little (K) taken by seat 3 in 0 s INSTANTLY (autopick) — a target is gone (was 92% to survive)
    07:46:59  plan #169 for pick 144: Eddy Pineiro K 98% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    07:47:02  heartbeat sent (Yahoo told we are not idle)
    07:47:09  pick 144  Mike Washington Jr. (RB) taken by seat 4 in 14 s
    07:47:09  plan #170 for pick 145: Eddy Pineiro K “fills your open K slot” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    07:47:09  ON THE CLOCK, pick 145 · plan #170 (0.0 s old) · lineup needs K
    07:47:10  PICKED Eddy Pineiro (K) via action, confirmed in 302 ms — chose Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Kyler Murray, passed on purpose
    07:47:12  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    07:33:46 PT preflight: ok=true pick_path=action my_team=5 plan=plan 25 deep @pick 12 via store call#91
    07:33:46 PT driver start — sleep via worker — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    07:33:46 PT NARR info driver started — seat 5, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    07:34:27 PT ON CLOCK -> {"drafted":"De'Von Achane","pos":"RB","vorp":73.4,"proj":233.6,"why":"waiting likely costs ~16 pts at RB (best option now 73, ~58 by your next turn) · 54% chance he's still there at your next pick · fills your open R
    07:34:47 PT heartbeat: setAwayStatus(false)
    07:34:47 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:34:53 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"waiting likely costs ~30 pts at TE (best option now 78, ~48 by your next turn) · 45% chance he's still there at your next pick · fills your open TE
    07:35:49 PT heartbeat: setAwayStatus(false)
    07:35:49 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:36:03 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~3 pts at WR (best option now 24, ~21 by your next turn) · 69% chance he's still there at your next pick · fills your open WR 
    07:36:43 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~7 pts at QB (best option now 31, ~24 by your next turn) · 48% chance he's still there at your next pick · fills your open QB sl
    07:36:53 PT heartbeat: setAwayStatus(false)
    07:36:53 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:37:53 PT heartbeat: setAwayStatus(false)
    07:37:53 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:37:58 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"safe to wait on RB · 83% chance he's still there at your next pick · fills your open RB slot · 4 teams picking before you still need a RB","s":0.82
    07:38:30 PT ON CLOCK -> {"drafted":"TreVeyon Henderson","pos":"RB","vorp":2.9,"proj":163.1,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 3, ~1 by your next turn) · 74% chance he's still there at your next pick · fill
    07:38:54 PT heartbeat: setAwayStatus(false)
    07:38:54 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:39:49 PT ON CLOCK -> {"drafted":"RJ Harvey","pos":"RB","vorp":-5.4,"proj":154.8,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 88 pts","s":0.933,"sr":0.933,"e":-5.5,"top_proj_availabl
    07:39:56 PT heartbeat: setAwayStatus(false)
    07:39:56 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:40:50 PT ON CLOCK -> {"drafted":"Kenny Gainwell","pos":"RB","vorp":-6.2,"proj":154,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.1/wk over the wire (Josh Jacobs) ≈ 23 pts","s":0.932,"sr":
    07:40:57 PT heartbeat: setAwayStatus(false)
    07:40:57 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:41:57 PT heartbeat: setAwayStatus(false)
    07:41:57 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:42:25 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.975,"sr":0.975,"e":-10.7,"top_
    07:42:58 PT heartbeat: setAwayStatus(false)
    07:42:58 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:43:01 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.91,"sr":0.91,"e":12.1,"top_proj
    07:43:58 PT heartbeat: setAwayStatus(false)
    07:43:58 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:44:20 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-13.3,"proj":128.8,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.5/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0
    07:44:59 PT heartbeat: setAwayStatus(false)
    07:44:59 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:45:16 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Zach Charbonnet) ≈ 2 pts","s":0.9
    07:45:59 PT heartbeat: setAwayStatus(false)
    07:45:59 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:46:19 PT ON CLOCK -> {"drafted":"Philadelphia Eagles","pos":"DEF","vorp":10,"proj":127,"why":"safe to wait on DEF · 69% chance he's still there at your next pick · fills your open DEF slot · 6 teams picking before you still need a DEF · 
    07:47:02 PT heartbeat: setAwayStatus(false)
    07:47:02 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    07:47:10 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":258.9,"vorp":-14.7},"took_top_projection":
    07:47:12 PT roster full
    07:47:12 PT NARR info roster full — driver done; posting the trail when the room finishes
    07:47:12 PT driver stop


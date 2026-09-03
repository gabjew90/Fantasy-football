# Scrutiny: Mock 29 -- Hurry-Up Offense (room 10588125) -- Thursday 2026-09-03 02:28 PT -- 10 teams, our seat 1

Captured 2026-09-03 02:42:10 PT. Times below are Pacific. 10 teams, our team id 1, draft slot 1. 150 picks in the trail, 62 bridge plan calls, 53 recs events in the room log.

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

- Our picks: 15; by the driver 12 (action 12, click 0), by Yahoo from the queue / autopick 3: 1 Jahmyr Gibbs, 80 RJ Harvey, 81 Kenny Gainwell.
- Action latency to store confirmation: median 992 ms, min 902, max 1010.
- Heartbeats 3; away flags detected and cleared 1; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {} -> {7} -> {5,7} -> {7} -> {5,7} -> {7} -> {5,7,8} -> {7,8} -> {5,7,8} -> {5,8} -> {3,5,8} -> {3,5,7,8} -> {3,5,8} -> {3,4,5,8} -> {3,4,5,7,8,10}.
- Managers away at the end: 3 Neesh, 4 James, 5 victor, 7 raul, 8 Clean, 10 ac2fly.

## Our picks, one block each

### Pick 1 (round 1): Jahmyr Gibbs (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    02:29:56 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pick plan: pair with t
- Plan call 86 @pick 1: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 0 drafted / 0 mine.
- Engine's first choice was **Christian McCaffrey** -> NOT taken.

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
- Driver: via **action**, verified store, 993 ms, ranker engine, plan call 93, plan age 1949 ms, at 02:29:56 PT.
- Engine's reason: safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pick plan: pair with the ~60-pt WR expected at your next turn
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Drake London (WR, s=1, e=51); Kyren Williams (RB, s=1, e=40.5); Josh Allen (QB, s=1, e=47).
- Plan call 93 @pick 20: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7], state store with 19 drafted / 1 mine.
- Engine's first choice was **Trey McBride** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Trey McBride | TE | 77.9 | 1.00 | 1.00 | 77.9 | 77.9 | safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE s |
| Drake London | WR | 51.0 | 1.00 | 1.00 | 51.0 | 51.0 | safe to wait on WR · 100% chance he's still there at your next pick · fills your open WR s |
| Kyren Williams | RB | 40.5 | 1.00 | 1.00 | 40.5 | 40.5 | safe to wait on RB · 100% chance he's still there at your next pick · fills your open RB s |
| Josh Allen | QB | 47.0 | 1.00 | 1.00 | 47.0 | 47.0 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 47.0 | 0.0 | 9 |
| RB | 40.5 | 40.5 | 0.0 | 18 |
| WR | 51.0 | 51.0 | 0.0 | 24 |
| TE | 77.9 | 77.9 | 0.0 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 40.538716071469565 | 40.5 | 0.0 | 49 |

### Pick 21 (round 3): Drake London (WR)

- In plain English: Took Drake London (WR) because waiting would likely cost about 13 points at WR, with a 13% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1010 ms, ranker engine, plan call 94, plan age 2900 ms, at 02:30:03 PT.
- Engine's reason: waiting likely costs ~13 pts at WR (best option now 51, ~38 by your next turn) · 13% chance he's still there at your next pick · fills your open WR slot · 18 teams picking before you still need a WR · two-pick plan: pair
- Top projection available: Josh Allen -> took it: False.
- Plan rows the page dropped: A.J. Brown (drafted).
- Passed on: Kyren Williams (RB, s=0.261, e=33); Josh Allen (QB, s=0.562, e=38.8); Chris Olave (WR, s=None, e=None).
- Plan call 94 @pick 21: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [5, 7], state store with 20 drafted / 2 mine.
- Engine's first choice was **Drake London** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake London | WR | 51.0 | 0.13 | 0.13 | 37.5 | 51.0 | waiting likely costs ~13 pts at WR (best option now 51, ~38 by your next turn) · 13% chanc |
| Kyren Williams | RB | 40.5 | 0.26 | 0.26 | 33.0 | 40.5 | waiting likely costs ~7 pts at RB (best option now 40, ~33 by your next turn) · 26% chance |
| Josh Allen | QB | 47.0 | 0.56 | 0.56 | 38.8 | 47.0 | waiting likely costs ~8 pts at QB (best option now 47, ~39 by your next turn) · 56% chance |
| A.J. Brown | WR | 43.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 38.8 | 8.2 | 9 |
| RB | 40.5 | 33.0 | 7.5 | 18 |
| WR | 51.0 | 37.5 | 13.5 | 24 |
| TE | 23.8 | 23.1 | 0.7 | 6 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 33.6 | 7.0 | 48 |

### Pick 40 (round 4): Cam Skattebo (RB)

- In plain English: Took Cam Skattebo (RB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 914 ms, ranker engine, plan call 101, plan age 1943 ms, at 02:31:42 PT.
- Engine's reason: safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · two-pick plan: pair with the ~33-pt WR expected at your next turn
- Top projection available: Drake Maye -> took it: False.
- Passed on: Garrett Wilson (WR, s=1, e=23.9); Drake Maye (QB, s=1, e=31.1); Zay Flowers (WR, s=None, e=None).
- Plan call 101 @pick 40: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 39 drafted / 3 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 25.8 | 1.00 | 1.00 | 25.8 | 25.8 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills yo |
| Garrett Wilson | WR | 23.9 | 1.00 | 1.00 | 23.9 | 23.9 | safe to wait on WR · 100% chance he's still there at your next pick · fills your open WR s |
| Drake Maye | QB | 31.1 | 1.00 | 1.00 | 31.1 | 31.1 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 31.1 | 0.0 | 12 |
| RB | 25.8 | 25.8 | 0.0 | 16 |
| WR | 23.9 | 23.9 | 0.0 | 21 |
| TE | 23.8 | 23.8 | 0.0 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 25.8 | 0.0 | 46 |

### Pick 41 (round 5): Garrett Wilson (WR)

- In plain English: Took Garrett Wilson (WR) because waiting would likely cost about 4 points at WR, with a 35% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 1004 ms, ranker engine, plan call 102, plan age 1622 ms, at 02:31:49 PT.
- Engine's reason: waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 35% chance he's still there at your next pick · fills your open WR slot · 16 teams picking before you still need a WR · two-pick plan: pair 
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.422, e=22.6); Jaylen Warren (RB, s=0.856, e=9); Zay Flowers (WR, s=None, e=None).
- Plan call 102 @pick 41: needs {'QB': 1, 'RB': 0, 'WR': 1, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [7], state store with 40 drafted / 4 mine.
- Engine's first choice was **Garrett Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Garrett Wilson | WR | 23.9 | 0.35 | 0.35 | 20.4 | 23.9 | waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 35% chance |
| Drake Maye | QB | 31.1 | 0.42 | 0.42 | 22.6 | 31.1 | waiting likely costs ~9 pts at QB (best option now 31, ~23 by your next turn) · 42% chance |
| Jaylen Warren | RB | 9.3 | 0.86 | 0.86 | 9.0 | 9.3 | safe to wait on your FLEX spot · 86% chance he's still there at your next pick · fills a F |
| Zay Flowers | WR | 22.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 22.6 | 8.5 | 12 |
| RB | 9.3 | 8.9 | 0.4 | 15 |
| WR | 23.9 | 20.4 | 3.5 | 21 |
| TE | 23.8 | 21.6 | 2.2 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 9.307117353117064 | 9.0 | 0.3 | 45 |

### Pick 60 (round 6): Jalen Hurts (QB)

- In plain English: Took Jalen Hurts (QB): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for).
- Driver: via **action**, verified store, 981 ms, ranker engine, plan call 111, plan age 1809 ms, at 02:34:18 PT.
- Engine's reason: safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pair with the ~37-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: True.
- Passed on: Jaylen Warren (RB, s=1, e=9.3); Trevor Lawrence (QB, s=None, e=None); Patrick Mahomes II (QB, s=None, e=None).
- Plan call 111 @pick 60: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 5, 8], state store with 59 drafted / 5 mine.
- Engine's first choice was **Jalen Hurts** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jalen Hurts | QB | 18.0 | 1.00 | 1.00 | 18.0 | 18.0 | safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB s |
| Jaylen Warren | RB | 9.3 | 1.00 | 1.00 | 9.3 | 9.3 | safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills a  |
| Trevor Lawrence | QB | 15.7 | - | - | - | - | depth fallback (engine list exhausted) |
| Patrick Mahomes II | QB | 12.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Caleb Williams | QB | 10.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Justin Herbert | QB | 7.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 18.0 | 0.0 | 16 |
| RB | 9.3 | 9.3 | 0.0 | 17 |
| WR | 0.0 | 0.0 | 0.0 | 19 |
| TE | 21.1 | 21.1 | 0.0 | 10 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 9.3 | 0.0 | 46 |

### Pick 61 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 5 points at your FLEX spot, with a 47% chance he would still be there next turn. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 994 ms, ranker engine, plan call 112, plan age 2762 ms, at 02:34:25 PT.
- Engine's reason: waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 47% chance he's still there at your next pick · fills a FLEX slot · 2 teams picking before you still need a RB
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Rhamondre Stevenson (RB, s=None, e=None); TreVeyon Henderson (RB, s=None, e=None); Jameson Williams (WR, s=None, e=None).
- Plan call 112 @pick 61: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 5, 7, 8], state store with 60 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.47 | 0.47 | 4.8 | 9.3 | waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) ·  |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| TreVeyon Henderson | RB | 2.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jameson Williams | WR | 0.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Christian Watson | WR | -0.8 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.9 | 1.8 | 15 |
| RB | 9.3 | 4.8 | 4.5 | 18 |
| WR | 0.0 | -4.4 | 4.4 | 21 |
| TE | 21.1 | 16.1 | 5.0 | 10 |
| K | 13.5 | 13.4 | 0.1 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 4.8 | 4.5 | 49 |

### Pick 80 (round 8): RJ Harvey (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    02:34:25 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 47% chance he's still there at your next pick · fills a FLEX slot · 2 teams p
    02:37:54 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    02:37:54 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    02:38:56 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":1,"sr":1,"e":-10.6,"top_proj_available":{"n":"Patric
    02:39:02 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.798,"sr":0.798,"e":11.3,"top_proj_available":{"n":"
    02:39:54 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10.9/wk over the wire (Zach Charbonnet) ≈ 3 pts · HANDCUFF: backs up your Ca
    02:40:01 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.951,"sr":0.951,"e":-11
    02:41:16 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF slot · 3 picks past his usual draft spot · two-pick plan: pair with the ~
    02:41:21 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection":false,"passed_on":
- No plan call at this pick; the last plan before it was call 122 @pick 79:
- Plan call 122 @pick 79: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 8], state store with 78 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacob |
| DK Metcalf | WR | -9.2 | 0.97 | 0.97 | -9.2 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.3 | 0.4 | 19 |
| RB | -5.4 | -5.4 | 0.0 | 31 |
| WR | -9.2 | -9.2 | 0.0 | 37 |
| TE | 21.1 | 21.0 | 0.1 | 21 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 9 |

### Pick 81 (round 9): Kenny Gainwell (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    02:29:56 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pick plan: pair with t
    02:30:03 PT ON CLOCK -> {"drafted":"Drake London","pos":"WR","vorp":51,"proj":193.1,"why":"waiting likely costs ~13 pts at WR (best option now 51, ~38 by your next turn) · 13% chance he's still there at your next pick · fills your open WR slot · 18 teams picki
    02:31:42 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after him · two-pick plan: p
    02:31:49 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 35% chance he's still there at your next pick · fills your open WR slot · 16 teams pick
    02:34:18 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pair with the ~37-pt WR
    02:34:25 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 47% chance he's still there at your next pick · fills a FLEX slot · 2 teams p
    02:37:54 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    02:37:54 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    02:38:56 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":1,"sr":1,"e":-10.6,"top_proj_available":{"n":"Patric
    02:39:02 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.798,"sr":0.798,"e":11.3,"top_proj_available":{"n":"
    02:39:54 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10.9/wk over the wire (Zach Charbonnet) ≈ 3 pts · HANDCUFF: backs up your Ca
    02:40:01 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.951,"sr":0.951,"e":-11
- No plan call at this pick; the last plan before it was call 122 @pick 79:
- Plan call 122 @pick 79: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 8], state store with 78 drafted / 7 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -5.4 | -5.4 | bench insurance: covers 3 RB starters ~9.6 wks/season · +10.9/wk over the wire (Josh Jacob |
| DK Metcalf | WR | -9.2 | 0.97 | 0.97 | -9.2 | -9.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.8/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Carnell Tate | WR | -10.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Wan'Dale Robinson | WR | -10.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 15.3 | 0.4 | 19 |
| RB | -5.4 | -5.4 | 0.0 | 31 |
| WR | -9.2 | -9.2 | 0.0 | 37 |
| TE | 21.1 | 21.0 | 0.1 | 21 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 9 |

### Pick 100 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 992 ms, ranker engine, plan call 127, plan age 1887 ms, at 02:38:56 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=1, e=12.8); Tyrone Tracy Jr. (RB, s=1, e=-25.9); Matthew Stafford (QB, s=None, e=None).
- Plan call 127 @pick 100: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 99 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 1.00 | 1.00 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 1.00 | 1.00 | 12.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -25.9 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 12.8 | 0.0 | 17 |
| RB | -25.9 | -25.9 | 0.0 | 24 |
| WR | -10.6 | -10.6 | 0.0 | 35 |
| TE | 13.8 | 13.8 | 0.0 | 18 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 9 |

### Pick 101 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 902 ms, ranker engine, plan call 128, plan age 1413 ms, at 02:39:02 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Tyrone Tracy Jr. (RB, s=0.94, e=-26.2); Courtland Sutton (WR, s=0.741, e=-12.1); Matthew Stafford (QB, s=None, e=None).
- Plan call 128 @pick 101: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 100 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.80 | 0.80 | 11.3 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Tyrone Tracy Jr. | RB | -33.0 | 0.94 | 0.94 | -26.2 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10 |
| Courtland Sutton | WR | -11.1 | 0.74 | 0.74 | -12.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 11.3 | 1.5 | 17 |
| RB | -25.9 | -26.2 | 0.3 | 24 |
| WR | -11.1 | -12.1 | 1.0 | 34 |
| TE | 13.8 | 12.6 | 1.2 | 18 |
| K | 12.0 | 11.4 | 0.6 | 13 |
| DEF | 18.0 | 13.1 | 4.9 | 10 |

### Pick 120 (round 12): Tyrone Tracy Jr. (RB)

- In plain English: Lineup already full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +10.9 points a week over the waiver wire (Zach Charbonnet), worth about 3 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 988 ms, ranker engine, plan call 133, plan age 1782 ms, at 02:39:54 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10.9/wk over the wire (Zach Charbonnet) ≈ 3 pts · HANDCUFF: backs up your Cam Skattebo
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Courtland Sutton (WR, s=1, e=-11.1); Michael Pittman Jr. (WR, s=None, e=None); Stefon Diggs (WR, s=None, e=None).
- Plan call 133 @pick 120: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 119 drafted / 11 mine.
- Engine's first choice was **Tyrone Tracy Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyrone Tracy Jr. | RB | -33.0 | 1.00 | 1.00 | -25.9 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10 |
| Courtland Sutton | WR | -11.1 | 1.00 | 1.00 | -11.1 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Stefon Diggs | WR | -18.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 10 |
| RB | -25.9 | -25.9 | 0.0 | 22 |
| WR | -11.1 | -11.1 | 0.0 | 33 |
| TE | -2.4 | -2.4 | 0.0 | 11 |
| K | 12.0 | 12.0 | 0.0 | 14 |
| DEF | 16.0 | 16.0 | 0.0 | 11 |

### Pick 121 (round 13): Courtland Sutton (WR)

- In plain English: Lineup already full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 993 ms, ranker engine, plan call 134, plan age 1795 ms, at 02:40:01 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Aaron Jones Sr. (RB, s=0.848, e=-26.4); Michael Pittman Jr. (WR, s=None, e=None); Stefon Diggs (WR, s=None, e=None).
- Plan call 134 @pick 121: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 120 drafted / 12 mine.
- Engine's first choice was **Courtland Sutton** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Courtland Sutton | WR | -11.1 | 0.95 | 0.95 | -11.2 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Aaron Jones Sr. | RB | -25.9 | 0.85 | 0.85 | -26.4 | -25.9 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +7. |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Stefon Diggs | WR | -18.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jakobi Meyers | WR | -21.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jordan Addison | WR | -23.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.3 | 0.4 | 10 |
| RB | -25.9 | -26.4 | 0.5 | 21 |
| WR | -11.1 | -11.2 | 0.1 | 33 |
| TE | -2.4 | -4.1 | 1.7 | 11 |
| K | 12.0 | 8.9 | 3.1 | 14 |
| DEF | 16.0 | 7.5 | 8.5 | 11 |

### Pick 140 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (100% to survive, but nobody better was worth waiting for). The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 990 ms, ranker engine, plan call 140, plan age 1753 ms, at 02:41:16 PT.
- Engine's reason: safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF slot · 3 picks past his usual draft spot · two-pick plan: pair with the ~30-pt RB expected at your next turn
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Eddy Pineiro (K, s=1, e=6); Tyler Loop (K, s=None, e=None); New England Patriots (DEF, s=None, e=None).
- Plan call 140 @pick 140: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 139 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 1.00 | 1.00 | 6.0 | 6.0 | safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF |
| Eddy Pineiro | K | 6.0 | 1.00 | 1.00 | 6.0 | 6.0 | safe to wait on K · 100% chance he's still there at your next pick · fills your open K slo |
| Tyler Loop | K | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| New England Patriots | DEF | 4.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Evan McPherson | K | 3.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jacksonville Jaguars | DEF | 2.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -14.9 | 0.0 | 9 |
| RB | -28.8 | -28.8 | 0.0 | 19 |
| WR | -27.9 | -27.9 | 0.0 | 23 |
| TE | -2.4 | -2.4 | 0.0 | 11 |
| K | 6.0 | 6.0 | 0.0 | 13 |
| DEF | 6.0 | 6.0 | 0.0 | 8 |

### Pick 141 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 993 ms, ranker engine, plan call 141, plan age 1973 ms, at 02:41:21 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Tyler Loop (K, s=None, e=None); Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None).
- Plan call 141 @pick 141: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [3, 4, 5, 7, 8, 10], state store with 140 drafted / 14 mine.
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
| 0-30% | 16 | 16% | 19% |
| 30-50% | 21 | 38% | 5% |
| 50-70% | 13 | 61% | 31% |
| 70-90% | 30 | 82% | 80% |
| 90-100% | 44 | 98% | 86% |

124 predictions over 52 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    02:28:31  plan #87 for pick 10: Amon-Ra St. Brown WR 39% “waiting likely costs ~18 pts at WR (best opt” · De'Von Achane RB 31% “waiting likely costs ~17 pts at RB (best opt” · Trey McBride TE 81% “waiting likely costs ~6 pts at TE (best opt
    02:28:32  driver started — seat 1, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    02:28:49  pick 10  CeeDee Lamb (WR) taken by seat 10 in 19 s — a target is gone
    02:28:56  pick 11  Justin Jefferson (WR) taken by seat 10 in 7 s — a target is gone
    02:29:00  pick 12  Chase Brown (RB) taken by seat 9 in 4 s — a target is gone
    02:29:01  plan #90 for pick 13: Amon-Ra St. Brown WR 44% “waiting likely costs ~19 pts at WR (best opt” · De'Von Achane RB 46% “waiting likely costs ~15 pts at RB (best opt” · Trey McBride TE 83% “waiting likely costs ~5 pts at TE (best opt
    02:29:10  pick 13  De'Von Achane (RB) taken by seat 8 in 10 s — a target is gone (was 46% to survive)
    02:29:10  pick 14  Amon-Ra St. Brown (WR) taken by seat 7 in 0 s INSTANTLY (autopick) — a target is gone (was 44% to survive)
    02:29:14  plan #91 for pick 15: Trey McBride TE 85% “waiting likely costs ~4 pts at TE (best opti” · Drake London WR 62% “waiting likely costs ~3 pts at WR (best opti” · Derrick Henry RB 59% “waiting likely costs ~4 pts at RB (best opti”
    02:29:19  pick 15  Kenneth Walker III (RB) taken by seat 6 in 9 s
    02:29:19  pick 16  Omarion Hampton (RB) taken by seat 5 in 0 s
    02:29:23  pick 17  Derrick Henry (RB) taken by seat 4 in 4 s — a target is gone (was 59% to survive)
    02:29:30  pick 18  Brock Bowers (TE) taken by seat 3 in 7 s — a target is gone
    02:29:30  plan #92 for pick 19: Trey McBride TE 94% “waiting likely costs ~3 pts at TE (best opti” · Drake London WR 90% “safe to wait on WR” · Kyren Williams RB 94% “safe to wait on RB”
    02:29:54  pick 19  Nico Collins (WR) taken by seat 2 in 24 s — a target is gone
    02:29:54  plan #93 for pick 20: Trey McBride TE 100% “safe to wait on TE” · Drake London WR 100% “safe to wait on WR” · Kyren Williams RB 100% “safe to wait on RB”
    02:29:54  ON THE CLOCK, pick 20 · plan #93 (0.0 s old) · lineup needs QB RB WRx2 TE FLEX K DEF
    02:29:56  PICKED Trey McBride (TE) via action, confirmed in 993 ms — chose Trey McBride (TE): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left was Josh Allen, 
    02:30:00  plan #94 for pick 21: Drake London WR 13% “waiting likely costs ~13 pts at WR (best opt” · Kyren Williams RB 26% “waiting likely costs ~7 pts at RB (best opti” · Josh Allen QB 56% “waiting likely costs ~8 pts at QB (best opti”
    02:30:00  ON THE CLOCK, pick 21 · plan #94 (0.0 s old) · lineup needs QB RB WRx2 FLEX K DEF
    02:30:03  PICKED Drake London (WR) via action, confirmed in 1010 ms — chose Drake London (WR): waiting would likely cost about 13 points at WR, 13% to still be there next turn; top projection left was Josh Allen, passed on purpose
    02:30:07  plan #95 for pick 22: A.J. Brown WR 20% “waiting likely costs ~11 pts at WR (best opt” · Kyren Williams RB 23% “waiting likely costs ~8 pts at RB (best opti” · Josh Allen QB 52% “waiting likely costs ~9 pts at QB (best opti”
    02:30:07  pick 22  A.J. Brown (WR) taken by seat 2 in 4 s — a target is gone (was 20% to survive)
    02:30:18  pick 23  Ashton Jeanty (RB) taken by seat 3 in 11 s — a target is gone
    02:30:18  pick 24  George Pickens (WR) taken by seat 4 in 0 s — a target is gone
    02:30:20  pick 25  Malik Nabers (WR) taken by seat 5 in 2 s
    02:30:21  plan #96 for pick 26: Chris Olave WR 15% “waiting likely costs ~12 pts at WR (best opt” · Kyren Williams RB 27% “waiting likely costs ~9 pts at RB (best opti” · Josh Allen QB 70% “waiting likely costs ~6 pts at QB (best opti”
    02:30:25  pick 26  Kyren Williams (RB) taken by seat 6 in 5 s — a target is gone (was 27% to survive)
    02:30:25  pick 27  Chris Olave (WR) taken by seat 7 in 0 s — a target is gone (was 15% to survive)
    02:30:32  pick 28  DeVonta Smith (WR) taken by seat 8 in 7 s
    02:30:33  plan #97 for pick 29: Rashee Rice WR 36% “waiting likely costs ~8 pts at WR (best opti” · Javonte Williams RB 38% “waiting likely costs ~7 pts at RB (best opti” · Josh Allen QB 77% “waiting likely costs ~4 pts at QB (best opti”
    02:30:40  pick 29  Josh Allen (QB) taken by seat 9 in 8 s — a target is gone (was 77% to survive)
    02:30:47  pick 30  Javonte Williams (RB) taken by seat 10 in 7 s — a target is gone (was 38% to survive)
    02:30:47  plan #98 for pick 31: Rashee Rice WR 48% “waiting likely costs ~6 pts at WR (best opti” · Travis Etienne Jr. RB 64% “safe to wait on RB” · Drake Maye QB 80% “waiting likely costs ~3 pts at QB (best opti”
    02:30:57  pick 31  D'Andre Swift (RB) taken by seat 10 in 10 s — a target is gone
    02:30:59  pick 32  Jeremiyah Love (RB) taken by seat 9 in 2 s INSTANTLY (autopick) — a target is gone
    02:30:59  plan #99 for pick 33: Rashee Rice WR 63% “waiting likely costs ~4 pts at WR (best opti” · Travis Etienne Jr. RB 65% “waiting likely costs ~2 pts at RB (best opti” · Drake Maye QB 79% “waiting likely costs ~3 pts at QB (best opti”
    02:31:09  pick 33  Travis Etienne Jr. (RB) taken by seat 8 in 10 s — a target is gone (was 65% to survive)
    02:31:09  pick 34  Breece Hall (RB) taken by seat 7 in 0 s INSTANTLY (autopick)
    02:31:14  plan #100 for pick 35: Rashee Rice WR 69% “waiting likely costs ~3 pts at WR (best opti” · Cam Skattebo RB 71% “waiting likely costs ~5 pts at RB (best opti” · Drake Maye QB 82% “waiting likely costs ~2 pts at QB (best opti”
    02:31:14  pick 35  Tee Higgins (WR) taken by seat 6 in 6 s
    02:31:19  pick 36  Rashee Rice (WR) taken by seat 5 in 4 s — a target is gone (was 69% to survive)
    02:31:19  pick 37  Lamar Jackson (QB) taken by seat 4 in 0 s
    02:31:23  pick 38  Jaylen Waddle (WR) taken by seat 3 in 4 s
    02:31:40  pick 39  Bhayshul Tuten (RB) taken by seat 2 in 17 s
    02:31:40  plan #101 for pick 40: Cam Skattebo RB 100% “safe to wait on your FLEX spot” · Garrett Wilson WR 100% “safe to wait on WR” · Drake Maye QB 100% “safe to wait on QB”
    02:31:40  ON THE CLOCK, pick 40 · plan #101 (0.0 s old) · lineup needs QB RB WR FLEX K DEF
    02:31:42  PICKED Cam Skattebo (RB) via action, confirmed in 914 ms — chose Cam Skattebo (RB): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left was Drake Maye, 
    02:31:47  plan #102 for pick 41: Garrett Wilson WR 35% “waiting likely costs ~4 pts at WR (best opti” · Drake Maye QB 42% “waiting likely costs ~9 pts at QB (best opti” · Jaylen Warren RB 86% “safe to wait on your FLEX spot”
    02:31:47  ON THE CLOCK, pick 41 · plan #102 (0.0 s old) · lineup needs QB WR FLEX K DEF
    02:31:49  PICKED Garrett Wilson (WR) via action, confirmed in 1004 ms — chose Garrett Wilson (WR): waiting would likely cost about 4 points at WR, 35% to still be there next turn; top projection left was Drake Maye, passed on purpose
    02:31:52  pick 42  Tyler Warren (TE) taken by seat 2 in 3 s
    02:31:53  plan #103 for pick 43: Drake Maye QB 38% “waiting likely costs ~9 pts at QB (best opti” · Jaylen Warren RB 87% “safe to wait on your FLEX spot” · Zay Flowers WR “depth fallback (engine list exhausted)”
    02:32:04  pick 43  Ladd McConkey (WR) taken by seat 3 in 12 s
    02:32:04  pick 44  Zay Flowers (WR) taken by seat 4 in 0 s — a target is gone
    02:32:06  plan #104 for pick 45: Drake Maye QB 43% “waiting likely costs ~8 pts at QB (best opti” · Jaylen Warren RB 85% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    02:32:06  pick 45  Emeka Egbuka (WR) taken by seat 5 in 2 s INSTANTLY (autopick)
    02:32:15  pick 46  DJ Moore (WR) taken by seat 6 in 9 s
    02:32:15  pick 47  Colston Loveland (TE) taken by seat 7 in 0 s INSTANTLY (autopick)
    02:32:44  pick 48  Tetairoa McMillan (WR) taken by seat 8 in 29 s — a target is gone
    02:32:44  heartbeat sent (Yahoo told we are not idle)
    02:32:45  plan #105 for pick 49: Drake Maye QB 27% “waiting likely costs ~10 pts at QB (best opt” · Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    02:32:49  pick 49  Tucker Kraft (TE) taken by seat 9 in 5 s
    02:32:59  pick 50  David Montgomery (RB) taken by seat 10 in 10 s
    02:32:59  plan #106 for pick 51: Drake Maye QB 37% “waiting likely costs ~9 pts at QB (best opti” · Jaylen Warren RB 87% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    02:33:02  pick 51  Davante Adams (WR) taken by seat 10 in 3 s — a target is gone
    02:33:15  plan #107 for pick 52: Drake Maye QB 31% “waiting likely costs ~10 pts at QB (best opt” · Jaylen Warren RB 87% “safe to wait on your FLEX spot” · Jalen Hurts QB “depth fallback (engine list exhausted)”
    02:33:23  pick 52  Bucky Irving (RB) taken by seat 9 in 21 s
    02:33:23  pick 53  Drake Maye (QB) taken by seat 8 in 0 s INSTANTLY (autopick) — a target is gone (was 31% to survive)
    02:33:27  pick 54  Luther Burden III (WR) taken by seat 7 in 4 s
    02:33:28  plan #108 for pick 55: Jalen Hurts QB 67% “safe to wait on QB” · Jaylen Warren RB 89% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    02:33:33  pick 55  Jadarian Price (RB) taken by seat 6 in 6 s
    02:33:33  pick 56  Mike Evans (WR) taken by seat 5 in 0 s
    02:33:40  pick 57  Terry McLaurin (WR) taken by seat 4 in 7 s
    02:33:40  plan #109 for pick 58: Jalen Hurts QB 87% “safe to wait on QB” · Jaylen Warren RB 93% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    02:34:09  pick 58  Quinshon Judkins (RB) taken by seat 3 in 29 s
    02:34:09  plan #110 for pick 59: Jalen Hurts QB 96% “safe to wait on QB” · Jaylen Warren RB 97% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    02:34:16  pick 59  Rome Odunze (WR) taken by seat 2 in 7 s
    02:34:16  plan #111 for pick 60: Jalen Hurts QB 100% “safe to wait on QB” · Jaylen Warren RB 100% “safe to wait on your FLEX spot” · Trevor Lawrence QB “depth fallback (engine list exhausted)”
    02:34:16  ON THE CLOCK, pick 60 · plan #111 (0.0 s old) · lineup needs QB FLEX K DEF
    02:34:18  PICKED Jalen Hurts (QB) via action, confirmed in 981 ms — chose Jalen Hurts (QB): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for)
    02:34:22  plan #112 for pick 61: Jaylen Warren RB 47% “waiting likely costs ~5 pts at your FLEX spo” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)” · TreVeyon Henderson RB “depth fallback (engine list exhausted)”
    02:34:22  ON THE CLOCK, pick 61 · plan #112 (0.0 s old) · lineup needs FLEX K DEF
    02:34:25  PICKED Jaylen Warren (RB) via action, confirmed in 994 ms — chose Jaylen Warren (RB): waiting would likely cost about 5 points at your FLEX spot, 47% to still be there next turn; top projection left was Trevor Lawrence, passed on 
    02:34:29  plan #113 for pick 62: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 24% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    02:34:50  pick 62  TreVeyon Henderson (RB) taken by seat 2 in 25 s — a target is gone
    02:34:50  pick 63  Joe Burrow (QB) taken by seat 3 in 0 s
    02:34:50  pick 64  MarShawn Lloyd (RB) taken by seat 4 in 0 s
    02:34:51  plan #114 for pick 65: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 31% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    02:34:51  pick 65  Rhamondre Stevenson (RB) taken by seat 5 in 1 s INSTANTLY (autopick) — a target is gone
    02:35:02  pick 66  Dak Prescott (QB) taken by seat 6 in 11 s
    02:35:04  plan #115 for pick 67: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 32% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    02:35:24  pick 67  Jayden Daniels (QB) taken by seat 7 in 22 s
    02:35:25  plan #116 for pick 68: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Jameson Williams WR 33% “bench insurance: covers 2 WR starters ~6.5 w” · Christian Watson WR “depth fallback (engine list exhausted)”
    02:35:25  pick 68  Sam LaPorta (TE) taken by seat 8 in 1 s INSTANTLY (autopick)
    02:35:44  pick 69  Jameson Williams (WR) taken by seat 9 in 19 s — a target is gone (was 33% to survive)
    02:35:44  plan #117 for pick 70: Tyrone Tracy Jr. RB “bench insurance: covers 3 RB starters ~9.6 w” · Christian Watson WR 31% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    02:35:54  pick 70  Christian Watson (WR) taken by seat 10 in 10 s — a target is gone (was 31% to survive)
    02:35:56  plan #118 for pick 71: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · Parker Washington WR 28% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    02:36:19  pick 71  Caleb Williams (QB) taken by seat 10 in 25 s
    02:36:19  pick 72  Rico Dowdle (RB) taken by seat 9 in 0 s
    02:36:19  pick 73  Parker Washington (WR) taken by seat 8 in 0 s — a target is gone (was 28% to survive)
    02:36:28  pick 74  Marvin Harrison Jr. (WR) taken by seat 7 in 9 s — a target is gone
    02:36:28  plan #120 for pick 75: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 81% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    02:36:53  pick 75  Chris Godwin Jr. (WR) taken by seat 6 in 25 s
    02:36:53  pick 76  Justin Herbert (QB) taken by seat 5 in 0 s
    02:36:53  heartbeat sent (Yahoo told we are not idle)
    02:36:53  plan #121 for pick 77: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 85% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    02:36:58  pick 77  George Kittle (TE) taken by seat 4 in 5 s
    02:36:58  pick 78  Brian Thomas Jr. (WR) taken by seat 3 in 0 s
    02:37:14  plan #122 for pick 79: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters ~9.6 w” · DK Metcalf WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    02:37:29  pick 79  Trevor Lawrence (QB) taken by seat 2 in 31 s
    02:37:52  pick 82  Jonathon Brooks (RB) taken by seat 2 in 0 s
    02:37:52  pick 83  Carnell Tate (WR) taken by seat 3 in 0 s — a target is gone
    02:37:52  pick 84  Isaiah Likely (TE) taken by seat 4 in 0 s
    02:37:54  pick 85  Harold Fannin Jr. (TE) taken by seat 5 in 2 s INSTANTLY (autopick)
    02:37:54  Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    02:37:55  plan #123 for pick 86: DK Metcalf WR 6% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 13% “bench insurance: covers 1 TE starter ~3.9 wk” · Tyrone Tracy Jr. RB 97% “bench insurance: covers 3 RB starters behind”
    02:38:09  pick 86  Rams (DEF) taken by seat 6 in 15 s
    02:38:09  pick 87  Tony Pollard (RB) taken by seat 7 in 0 s
    02:38:10  plan #124 for pick 88: DK Metcalf WR 6% “bench insurance: covers 2 WR starters ~6.5 w” · Kyle Pitts Sr. TE 15% “bench insurance: covers 1 TE starter ~3.9 wk” · Tyrone Tracy Jr. RB 98% “bench insurance: covers 3 RB starters behind”
    02:38:10  pick 88  DK Metcalf (WR) taken by seat 8 in 1 s INSTANTLY (autopick) — a target is gone (was 6% to survive)
    02:38:22  pick 89  Alec Pierce (WR) taken by seat 9 in 12 s
    02:38:22  pick 90  Kyle Pitts Sr. (TE) taken by seat 10 in 0 s — a target is gone (was 15% to survive)
    02:38:23  plan #125 for pick 91: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 74% “bench insurance: covers 1 QB starter ~3.6 wk” · Tyrone Tracy Jr. RB 98% “bench insurance: covers 3 RB star
    02:38:32  pick 91  J.K. Dobbins (RB) taken by seat 10 in 10 s
    02:38:43  pick 92  Quentin Johnston (WR) taken by seat 9 in 11 s
    02:38:43  pick 93  Chuba Hubbard (RB) taken by seat 8 in 0 s
    02:38:43  plan #126 for pick 94: Wan'Dale Robinson WR 99% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 85% “bench insurance: covers 1 QB starter ~3.6 wk” · Tyrone Tracy Jr. RB 99% “bench insurance: covers 3 RB star
    02:38:49  pick 94  Jacory Croskey-Merritt (RB) taken by seat 7 in 6 s
    02:38:49  pick 95  Eagles (DEF) taken by seat 6 in 0 s
    02:38:49  pick 96  Blake Corum (RB) taken by seat 5 in 0 s
    02:38:49  pick 97  Michael Wilson (WR) taken by seat 4 in 0 s
    02:38:49  pick 98  Brock Purdy (QB) taken by seat 3 in 0 s — a target is gone
    02:38:54  pick 99  Brandon Aubrey (K) taken by seat 2 in 5 s
    02:38:54  plan #127 for pick 100: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 100% “bench insurance: covers 1 QB starter ~3.6 wk” · Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB 
    02:38:54  ON THE CLOCK, pick 100 · plan #127 (0.0 s old) · lineup needs K DEF
    02:38:56  PICKED Wan'Dale Robinson (WR) via action, confirmed in 992 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    02:39:00  plan #128 for pick 101: Patrick Mahomes II QB 80% “bench insurance: covers 1 QB starter ~3.6 wk” · Tyrone Tracy Jr. RB 94% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 74% “bench insurance: covers 2 WR star
    02:39:00  ON THE CLOCK, pick 101 · plan #128 (0.0 s old) · lineup needs K DEF
    02:39:02  PICKED Patrick Mahomes II (QB) via action, confirmed in 902 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    02:39:07  pick 102  Texans (DEF) taken by seat 2 in 5 s
    02:39:07  pick 103  Jordan Mason (RB) taken by seat 3 in 0 s
    02:39:07  pick 104  Bo Nix (QB) taken by seat 4 in 0 s — a target is gone
    02:39:07  pick 105  Jaxson Dart (QB) taken by seat 5 in 0 s — a target is gone
    02:39:08  plan #129 for pick 106: Tyrone Tracy Jr. RB 94% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 85% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhauste
    02:39:08  pick 106  Jason Myers (K) taken by seat 6 in 1 s INSTANTLY (autopick)
    02:39:08  pick 107  Dalton Kincaid (TE) taken by seat 7 in 0 s INSTANTLY (autopick)
    02:39:13  pick 108  Matthew Stafford (QB) taken by seat 8 in 5 s
    02:39:19  pick 109  Jordan Love (QB) taken by seat 9 in 6 s
    02:39:19  pick 110  Kyler Murray (QB) taken by seat 10 in 0 s INSTANTLY (autopick)
    02:39:19  pick 111  Dallas Goedert (TE) taken by seat 10 in 0 s INSTANTLY (autopick)
    02:39:20  plan #130 for pick 112: Tyrone Tracy Jr. RB 97% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 94% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhauste
    02:39:32  pick 112  Travis Kelce (TE) taken by seat 9 in 13 s
    02:39:32  pick 113  Mark Andrews (TE) taken by seat 8 in 0 s
    02:39:32  pick 114  Jared Goff (QB) taken by seat 7 in 0 s
    02:39:32  plan #131 for pick 115: Tyrone Tracy Jr. RB 97% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 98% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhauste
    02:39:41  pick 115  Jake Ferguson (TE) taken by seat 6 in 9 s
    02:39:41  pick 116  Juwan Johnson (TE) taken by seat 5 in 0 s INSTANTLY (autopick)
    02:39:42  pick 117  Josh Jacobs (RB) taken by seat 4 in 1 s INSTANTLY (autopick)
    02:39:43  pick 118  Dalton Schultz (TE) taken by seat 3 in 1 s INSTANTLY (autopick)
    02:39:44  plan #132 for pick 119: Tyrone Tracy Jr. RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 99% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhauste
    02:39:52  pick 119  Josh Downs (WR) taken by seat 2 in 9 s — a target is gone
    02:39:52  plan #133 for pick 120: Tyrone Tracy Jr. RB 100% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 100% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhaus
    02:39:52  ON THE CLOCK, pick 120 · plan #133 (0.0 s old) · lineup needs K DEF
    02:39:54  PICKED Tyrone Tracy Jr. (RB) via action, confirmed in 988 ms — lineup full, so Tyrone Tracy Jr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +10.9 a week over the wire, about 3 points; he also backs up one
    02:39:59  plan #134 for pick 121: Courtland Sutton WR 95% “bench insurance: covers 2 WR starters behind” · Aaron Jones Sr. RB 85% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted
    02:39:59  ON THE CLOCK, pick 121 · plan #134 (0.0 s old) · lineup needs K DEF
    02:40:01  PICKED Courtland Sutton (WR) via action, confirmed in 993 ms — lineup full, so Courtland Sutton (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.7 a week over the wire, about 2 points; top projection left w
    02:40:05  plan #135 for pick 122: Denver Broncos DEF 1% “waiting likely costs ~8 pts at DEF (best opt” · Cameron Dicker K 37% “waiting likely costs ~3 pts at K (best optio” · Seattle Seahawks DEF “depth fallback (engine list exhausted)”
    02:40:14  pick 122  KC Concepcion (WR) taken by seat 2 in 13 s
    02:40:14  pick 123  Stefon Diggs (WR) taken by seat 3 in 0 s
    02:40:15  pick 124  De'Zhaun Stribling (WR) taken by seat 4 in 1 s INSTANTLY (autopick)
    02:40:16  pick 125  Jordan Addison (WR) taken by seat 5 in 1 s INSTANTLY (autopick)
    02:40:17  plan #136 for pick 126: Denver Broncos DEF 4% “waiting likely costs ~7 pts at DEF (best opt” · Cameron Dicker K 55% “waiting likely costs ~2 pts at K (best optio” · Seattle Seahawks DEF “depth fallback (engine list exhausted)”
    02:40:26  pick 126  Matthew Golden (WR) taken by seat 6 in 10 s
    02:40:26  pick 127  Jayden Reed (WR) taken by seat 7 in 0 s
    02:40:27  pick 128  Michael Pittman Jr. (WR) taken by seat 8 in 1 s INSTANTLY (autopick)
    02:40:29  plan #137 for pick 129: Denver Broncos DEF 7% “waiting likely costs ~6 pts at DEF (best opt” · Cameron Dicker K 75% “waiting likely costs ~1 pts at K (best optio” · Seattle Seahawks DEF “depth fallback (engine list exhausted)”
    02:40:30  pick 129  Zach Charbonnet (RB) taken by seat 9 in 3 s
    02:40:30  pick 130  Makai Lemon (WR) taken by seat 10 in 0 s INSTANTLY (autopick)
    02:40:34  pick 131  Broncos (DEF) taken by seat 10 in 4 s
    02:40:50  pick 132  Jakobi Meyers (WR) taken by seat 9 in 16 s
    02:40:50  pick 133  Seahawks (DEF) taken by seat 8 in 0 s
    02:40:50  plan #138 for pick 134: Cameron Dicker K 61% “waiting likely costs ~2 pts at K (best optio” · Pittsburgh Steelers DEF 86% “safe to wait on DEF” · Ka'imi Fairbairn K “depth fallback (engine list exhausted)”
    02:40:58  pick 134  Ka'imi Fairbairn (K) taken by seat 7 in 8 s — a target is gone
    02:40:58  heartbeat sent (Yahoo told we are not idle)
    02:41:05  pick 135  Aaron Jones Sr. (RB) taken by seat 6 in 7 s
    02:41:05  pick 136  Cameron Dicker (K) taken by seat 5 in 0 s — a target is gone (was 61% to survive)
    02:41:05  plan #139 for pick 137: Pittsburgh Steelers DEF 95% “waiting likely costs ~1 pts at DEF (best opt” · Cam Little K 85% “safe to wait on K” · Minnesota Vikings DEF “depth fallback (engine list exhausted)”
    02:41:07  pick 137  Vikings (DEF) taken by seat 4 in 2 s INSTANTLY (autopick)
    02:41:07  pick 138  Cam Little (K) taken by seat 3 in 0 s INSTANTLY (autopick) — a target is gone (was 85% to survive)
    02:41:14  pick 139  Daniel Jones (QB) taken by seat 2 in 7 s
    02:41:14  plan #140 for pick 140: Pittsburgh Steelers DEF 100% “safe to wait on DEF” · Eddy Pineiro K 100% “safe to wait on K” · Tyler Loop K “depth fallback (engine list exhausted)”
    02:41:14  ON THE CLOCK, pick 140 · plan #140 (0.0 s old) · lineup needs K DEF
    02:41:16  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 990 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (100% to survive, nobody better worth waiting for); top projection left 
    02:41:19  plan #141 for pick 141: Eddy Pineiro K “fills your open K slot” · Tyler Loop K “depth fallback (engine list exhausted)” · Evan McPherson K “depth fallback (engine list exhausted)”
    02:41:19  ON THE CLOCK, pick 141 · plan #141 (0.0 s old) · lineup needs K
    02:41:21  PICKED Eddy Pineiro (K) via action, confirmed in 993 ms — chose Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Baker Mayfield, passed on purpose
    02:41:24  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    02:28:32 PT preflight: ok=false pick_path=action my_team=1 plan=plan 25 deep @pick 10 via store call#87
    02:28:32 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    02:28:32 PT NARR info driver started — seat 1, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    02:29:56 PT ON CLOCK -> {"drafted":"Trey McBride","pos":"TE","vorp":77.9,"proj":200.2,"why":"safe to wait on TE · 100% chance he's still there at your next pick · fills your open TE slot · last TE at this level — big drop after him · two-pi
    02:30:03 PT ON CLOCK -> {"drafted":"Drake London","pos":"WR","vorp":51,"proj":193.1,"why":"waiting likely costs ~13 pts at WR (best option now 51, ~38 by your next turn) · 13% chance he's still there at your next pick · fills your open WR s
    02:31:42 PT ON CLOCK -> {"drafted":"Cam Skattebo","pos":"RB","vorp":25.8,"proj":186,"why":"safe to wait on your FLEX spot · 100% chance he's still there at your next pick · fills your open RB slot · last RB at this level — big drop after hi
    02:31:49 PT ON CLOCK -> {"drafted":"Garrett Wilson","pos":"WR","vorp":23.9,"proj":166,"why":"waiting likely costs ~4 pts at WR (best option now 24, ~20 by your next turn) · 35% chance he's still there at your next pick · fills your open WR 
    02:32:44 PT heartbeat: setAwayStatus(false)
    02:32:44 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    02:34:18 PT ON CLOCK -> {"drafted":"Jalen Hurts","pos":"QB","vorp":18,"proj":291.6,"why":"safe to wait on QB · 100% chance he's still there at your next pick · fills your open QB slot · 4 picks past his usual draft spot · two-pick plan: pai
    02:34:25 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~5 pts at your FLEX spot (best option now 9, ~5 by your next turn) · 47% chance he's still there at your next pick · fills a F
    02:36:53 PT heartbeat: setAwayStatus(false)
    02:36:53 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    02:37:54 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    02:37:54 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    02:38:56 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":1,"sr":1,"e":-10.6,"top_proj_ava
    02:39:02 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.798,"sr":0.798,"e":11.3,"top_pr
    02:39:54 PT ON CLOCK -> {"drafted":"Tyrone Tracy Jr.","pos":"RB","vorp":-33,"proj":127.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +10.9/wk over the wire (Zach Charbonnet) ≈ 3 pts · HANDCU
    02:40:01 PT ON CLOCK -> {"drafted":"Courtland Sutton","pos":"WR","vorp":-11.1,"proj":131.1,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.95
    02:40:58 PT heartbeat: setAwayStatus(false)
    02:40:58 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    02:41:16 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 100% chance he's still there at your next pick · fills your open DEF slot · 3 picks past his usual draft spot · two-pick p
    02:41:21 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    02:41:24 PT roster full
    02:41:24 PT NARR info roster full — driver done; posting the trail when the room finishes
    02:41:24 PT driver stop


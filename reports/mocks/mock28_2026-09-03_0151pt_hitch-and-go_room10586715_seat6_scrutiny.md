# Scrutiny: Mock 28 -- Hitch and Go (room 10586715) -- Thursday 2026-09-03 01:51 PT -- 10 teams, our seat 6

Captured 2026-09-03 02:06:10 PT. Times below are Pacific. 10 teams, our team id 6, draft slot 6. 150 picks in the trail, 79 bridge plan calls, 58 recs events in the room log.

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

- Our picks: 15; by the driver 13 (action 13, click 0), by Yahoo from the queue / autopick 2: 6 Puka Nacua, 15 Justin Jefferson.
- Action latency to store confirmation: median 438 ms, min 356, max 519.
- Heartbeats 3; away flags detected and cleared 1; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {2,4,6} -> {2,4} -> {2} -> {2,4} -> {2,4,5} -> {2,4} -> {2,4,9} -> {1,2,9} -> {1,2,4,9} -> {1,2,3,4,9} -> {1,2,3,4,5,9} -> {1,2,3,4,9}.
- Managers away at the end: 1 Michael, 2 Hector, 3 Rodney, 4 Jarrod Donald-lutey, 9 Yoni.

## Our picks, one block each

### Pick 6 (round 1): Puka Nacua (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    01:51:12 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    01:51:12 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    01:52:18 PT ON CLOCK -> {"drafted":"Kyren Williams","pos":"RB","vorp":40.5,"proj":200.7,"why":"waiting likely costs ~3 pts at RB (best option now 40, ~37 by your next turn) · 63% chance he's still there at your next pick · fills your open RB slot · 8 teams pic
    01:54:01 PT ON CLOCK -> {"drafted":"Javonte Williams","pos":"RB","vorp":36.9,"proj":197.1,"why":"waiting likely costs ~5 pts at RB (best option now 37, ~32 by your next turn) · 59% chance he's still there at your next pick · fills your open RB slot · 8 teams p
    01:55:00 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 71% chance he's still there at your next pick · fills your open QB slot · 6 teams picking
    01:56:30 PT ON CLOCK -> {"drafted":"George Kittle","pos":"TE","vorp":19.8,"proj":142,"why":"safe to wait on TE · 87% chance he's still there at your next pick · fills your open TE slot · 8 teams picking before you still need a TE · two-pick plan: pair with the
    01:57:38 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 68% chance he's still there at your next pick · fills a FLEX slot","s":0.681,
    01:58:40 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 95 pts","s":0.273,"sr":0.273,"e":-2,"top_proj_available":{"n":"Trev
- No plan call recorded at this pick (bridge down?).

### Pick 15 (round 2): Justin Jefferson (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    01:51:12 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    01:51:12 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    01:52:18 PT ON CLOCK -> {"drafted":"Kyren Williams","pos":"RB","vorp":40.5,"proj":200.7,"why":"waiting likely costs ~3 pts at RB (best option now 40, ~37 by your next turn) · 63% chance he's still there at your next pick · fills your open RB slot · 8 teams pic
    01:54:01 PT ON CLOCK -> {"drafted":"Javonte Williams","pos":"RB","vorp":36.9,"proj":197.1,"why":"waiting likely costs ~5 pts at RB (best option now 37, ~32 by your next turn) · 59% chance he's still there at your next pick · fills your open RB slot · 8 teams p
    01:55:00 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 71% chance he's still there at your next pick · fills your open QB slot · 6 teams picking
    01:56:30 PT ON CLOCK -> {"drafted":"George Kittle","pos":"TE","vorp":19.8,"proj":142,"why":"safe to wait on TE · 87% chance he's still there at your next pick · fills your open TE slot · 8 teams picking before you still need a TE · two-pick plan: pair with the
    01:57:38 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 68% chance he's still there at your next pick · fills a FLEX slot","s":0.681,
    01:58:40 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 95 pts","s":0.273,"sr":0.273,"e":-2,"top_proj_available":{"n":"Trev
    01:59:50 PT ON CLOCK -> {"drafted":"Blake Corum","pos":"RB","vorp":-46.1,"proj":114.1,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Kyren Will
    02:00:51 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.98,"sr":0.98,"e":-10.6,"top_proj_available":{"n":"
    02:02:00 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.897,"sr":0.897,"e":10.2,"top_proj_available":{"n":"
    02:02:54 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Josh Jacobs) ≈ 2 pts","s":0.932,"sr":0.932,"e":-26.1,
- No plan call recorded at this pick (bridge down?).

### Pick 26 (round 3): Kyren Williams (RB)

- In plain English: Took Kyren Williams (RB) because waiting would likely cost about 3 points at RB, with a 63% chance he would still be there next turn. The top raw projection available was Josh Allen; the engine passed on him on purpose.
- Driver: via **action**, verified store, 437 ms, ranker engine, plan call 7, plan age 765 ms, at 01:52:18 PT.
- Engine's reason: waiting likely costs ~3 pts at RB (best option now 40, ~37 by your next turn) · 63% chance he's still there at your next pick · fills your open RB slot · 8 teams picking before you still need a RB · two-pick plan: pair w
- Top projection available: Josh Allen -> took it: False.
- Passed on: Josh Allen (QB, s=0.8, e=43.6); Tyler Warren (TE, s=0.883, e=23.5); Chris Olave (WR, s=None, e=None).
- Plan call 7 @pick 26: needs {'QB': 1, 'RB': 2, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4], state store with 25 drafted / 2 mine.
- Engine's first choice was **Kyren Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Kyren Williams | RB | 40.5 | 0.63 | 0.63 | 37.4 | 40.5 | waiting likely costs ~3 pts at RB (best option now 40, ~37 by your next turn) · 63% chance |
| Josh Allen | QB | 47.0 | 0.80 | 0.80 | 43.6 | 47.0 | waiting likely costs ~3 pts at QB (best option now 47, ~44 by your next turn) · 80% chance |
| Tyler Warren | TE | 23.8 | 0.88 | 0.88 | 23.5 | 23.8 | safe to wait on TE · 88% chance he's still there at your next pick · fills your open TE sl |
| Chris Olave | WR | 40.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Javonte Williams | RB | 36.9 | - | - | - | - | depth fallback (engine list exhausted) |
| George Pickens | WR | 36.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 47.0 | 43.6 | 3.4 | 10 |
| RB | 40.5 | 37.4 | 3.1 | 16 |
| WR | 40.1 | 36.6 | 3.5 | 23 |
| TE | 23.8 | 23.5 | 0.3 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 14.0 | 14.0 | 0.0 | 1 |
| FLEX | 40.538716071469565 | 37.5 | 3.0 | 46 |

### Pick 35 (round 4): Javonte Williams (RB)

- In plain English: Took Javonte Williams (RB) because waiting would likely cost about 5 points at RB, with a 59% chance he would still be there next turn. The top raw projection available was Drake Maye; the engine passed on him on purpose.
- Driver: via **action**, verified store, 441 ms, ranker engine, plan call 16, plan age 760 ms, at 01:54:01 PT.
- Engine's reason: waiting likely costs ~5 pts at RB (best option now 37, ~32 by your next turn) · 59% chance he's still there at your next pick · fills your open RB slot · 8 teams picking before you still need a RB · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: False.
- Passed on: Drake Maye (QB, s=0.671, e=26.7); Tyler Warren (TE, s=0.648, e=22.8); Rashee Rice (WR, s=None, e=None).
- Plan call 16 @pick 35: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2], state store with 34 drafted / 3 mine.
- Engine's first choice was **Javonte Williams** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Javonte Williams | RB | 36.9 | 0.59 | 0.59 | 31.7 | 36.9 | waiting likely costs ~5 pts at RB (best option now 37, ~32 by your next turn) · 59% chance |
| Drake Maye | QB | 31.1 | 0.67 | 0.67 | 26.7 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 67% chance |
| Tyler Warren | TE | 23.8 | 0.65 | 0.65 | 22.8 | 23.8 | safe to wait on TE · 65% chance he's still there at your next pick · fills your open TE sl |
| Rashee Rice | WR | 34.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Travis Etienne Jr. | RB | 26.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Cam Skattebo | RB | 25.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 26.7 | 4.4 | 10 |
| RB | 36.9 | 31.7 | 5.2 | 18 |
| WR | 34.1 | 27.9 | 6.2 | 19 |
| TE | 23.8 | 22.8 | 1.0 | 7 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 16.0 | 16.0 | 0.0 | 2 |
| FLEX | 36.93446478175926 | 31.9 | 5.0 | 44 |

### Pick 46 (round 5): Drake Maye (QB)

- In plain English: Took Drake Maye (QB) because waiting would likely cost about 4 points at QB, with a 71% chance he would still be there next turn.
- Driver: via **action**, verified store, 427 ms, ranker engine, plan call 22, plan age 742 ms, at 01:55:00 PT.
- Engine's reason: waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 71% chance he's still there at your next pick · fills your open QB slot · 6 teams picking before you still need a QB · two-pick plan: pair w
- Top projection available: Drake Maye -> took it: True.
- Passed on: Tyler Warren (TE, s=0.677, e=22.9); Cam Skattebo (RB, s=0.677, e=20.5); Kyle Pitts Sr. (TE, s=None, e=None).
- Plan call 22 @pick 46: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 5], state store with 45 drafted / 4 mine.
- Engine's first choice was **Drake Maye** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake Maye | QB | 31.1 | 0.71 | 0.71 | 27.2 | 31.1 | waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 71% chance |
| Tyler Warren | TE | 23.8 | 0.68 | 0.68 | 22.9 | 23.8 | safe to wait on TE · 68% chance he's still there at your next pick · fills your open TE sl |
| Cam Skattebo | RB | 25.8 | 0.68 | 0.68 | 20.5 | 25.8 | waiting likely costs ~5 pts at your FLEX spot (best option now 26, ~20 by your next turn)  |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| George Kittle | TE | 19.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Jalen Hurts | QB | 18.0 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 31.1 | 27.2 | 3.9 | 14 |
| RB | 25.8 | 20.4 | 5.4 | 17 |
| WR | 13.1 | 8.5 | 4.6 | 18 |
| TE | 23.8 | 22.9 | 0.9 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 25.84223678225652 | 20.5 | 5.4 | 43 |

### Pick 55 (round 6): George Kittle (TE)

- In plain English: Took George Kittle (TE): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (87% to survive, but nobody better was worth waiting for). The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 377 ms, ranker engine, plan call 29, plan age 694 ms, at 01:56:30 PT.
- Engine's reason: safe to wait on TE · 87% chance he's still there at your next pick · fills your open TE slot · 8 teams picking before you still need a TE · two-pick plan: pair with the ~36-pt WR expected at your next turn
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Jaylen Warren (RB, s=0.83, e=8.8); Kyle Pitts Sr. (TE, s=None, e=None); Harold Fannin Jr. (TE, s=None, e=None).
- Plan call 29 @pick 55: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [2, 4, 9], state store with 54 drafted / 5 mine.
- Engine's first choice was **George Kittle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| George Kittle | TE | 19.8 | 0.87 | 0.87 | 20.5 | 21.1 | safe to wait on TE · 87% chance he's still there at your next pick · fills your open TE sl |
| Jaylen Warren | RB | 9.3 | 0.83 | 0.83 | 8.8 | 9.3 | safe to wait on your FLEX spot · 83% chance he's still there at your next pick · fills a F |
| Kyle Pitts Sr. | TE | 21.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Harold Fannin Jr. | TE | 16.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Dallas Goedert | TE | 13.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.4 | 1.6 | 15 |
| RB | 9.3 | 8.8 | 0.5 | 19 |
| WR | 13.1 | 8.9 | 4.2 | 16 |
| TE | 21.1 | 20.5 | 0.6 | 9 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 8.8 | 0.5 | 44 |

### Pick 66 (round 7): Jaylen Warren (RB)

- In plain English: Took Jaylen Warren (RB) because waiting would likely cost about 2 points at your FLEX spot, with a 68% chance he would still be there next turn. The top raw projection available was Jalen Hurts; the engine passed on him on purpose.
- Driver: via **action**, verified store, 460 ms, ranker engine, plan call 35, plan age 779 ms, at 01:57:38 PT.
- Engine's reason: waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 68% chance he's still there at your next pick · fills a FLEX slot
- Top projection available: Jalen Hurts -> took it: False.
- Passed on: Davante Adams (WR, s=None, e=None); Rhamondre Stevenson (RB, s=None, e=None); RJ Harvey (RB, s=None, e=None).
- Plan call 35 @pick 66: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 9], state store with 65 drafted / 6 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | 9.3 | 0.68 | 0.68 | 7.7 | 9.3 | waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) ·  |
| Davante Adams | WR | 13.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Rhamondre Stevenson | RB | 7.2 | - | - | - | - | depth fallback (engine list exhausted) |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Parker Washington | WR | -5.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 18.0 | 16.9 | 1.1 | 21 |
| RB | 9.3 | 7.7 | 1.6 | 23 |
| WR | 13.1 | 9.8 | 3.3 | 26 |
| TE | 16.4 | 14.8 | 1.6 | 12 |
| K | 13.5 | 13.5 | 0.0 | 4 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |
| FLEX | 9.307117353117064 | 7.7 | 1.6 | 61 |

### Pick 75 (round 8): Rhamondre Stevenson (RB)

- In plain English: Lineup already full, so Rhamondre Stevenson (RB) is insurance: covers 3 RB starter(s) for about 9.6 weeks a season at +9.8 points a week over the waiver wire (Josh Jacobs), worth about 95 points. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 426 ms, ranker engine, plan call 41, plan age 750 ms, at 01:58:39 PT.
- Engine's reason: bench insurance: covers 3 RB starters ~9.6 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 95 pts
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Parker Washington (WR, s=0.115, e=-9.1); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 41 @pick 75: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 9], state store with 74 drafted / 7 mine.
- Engine's first choice was **Rhamondre Stevenson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rhamondre Stevenson | RB | 7.2 | 0.27 | 0.27 | -2.0 | 7.2 | bench insurance: covers 3 RB starters ~9.6 wks/season · +9.8/wk over the wire (Josh Jacobs |
| Parker Washington | WR | -5.5 | 0.12 | 0.12 | -9.1 | -5.5 | bench insurance: covers 2 WR starters ~6.5 wks/season · +3.0/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| DK Metcalf | WR | -9.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Marvin Harrison Jr. | WR | -9.6 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.9 | 1.8 | 20 |
| RB | 7.2 | -2.0 | 9.2 | 32 |
| WR | -5.5 | -9.1 | 3.6 | 39 |
| TE | 16.4 | 14.0 | 2.4 | 19 |
| K | 13.5 | 13.5 | 0.0 | 11 |
| DEF | 18.0 | 18.0 | 0.0 | 8 |

### Pick 86 (round 9): Blake Corum (RB)

- In plain English: Lineup already full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) for about 2.5 weeks a season at +9.8 points a week over the waiver wire (Josh Jacobs), worth about 25 points. He also backs up one of our own starters, which raises that value. The top raw projection available was Trevor Lawrence; the engine passed on him on purpose.
- Driver: via **action**, verified store, 519 ms, ranker engine, plan call 48, plan age 842 ms, at 01:59:50 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: backs up your Kyren Williams
- Top projection available: Trevor Lawrence -> took it: False.
- Passed on: Wan'Dale Robinson (WR, s=0.972, e=-10.6); RJ Harvey (RB, s=None, e=None); Kenny Gainwell (RB, s=None, e=None).
- Plan call 48 @pick 86: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 4, 9], state store with 85 drafted / 8 mine.
- Engine's first choice was **Blake Corum** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Blake Corum | RB | -46.1 | 0.79 | 0.79 | -5.6 | -5.4 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8 |
| Wan'Dale Robinson | WR | -10.6 | 0.97 | 0.97 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| RJ Harvey | RB | -5.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Kenny Gainwell | RB | -6.2 | - | - | - | - | depth fallback (engine list exhausted) |
| Courtland Sutton | WR | -11.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.7 | 13.6 | 2.1 | 19 |
| RB | -5.4 | -5.6 | 0.2 | 31 |
| WR | -10.6 | -10.6 | 0.0 | 37 |
| TE | 13.8 | 12.1 | 1.7 | 17 |
| K | 12.0 | 12.0 | 0.0 | 12 |
| DEF | 18.0 | 17.9 | 0.1 | 11 |

### Pick 95 (round 10): Wan'Dale Robinson (WR)

- In plain English: Lineup already full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +2.7 points a week over the waiver wire (Rashod Bateman), worth about 17 points. The top raw projection available was Patrick Mahomes II; the engine passed on him on purpose.
- Driver: via **action**, verified store, 481 ms, ranker engine, plan call 53, plan age 808 ms, at 02:00:51 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts
- Top projection available: Patrick Mahomes II -> took it: False.
- Passed on: Patrick Mahomes II (QB, s=0.667, e=9.8); Kenny Gainwell (RB, s=0.915, e=-7.9); Matthew Stafford (QB, s=None, e=None).
- Plan call 53 @pick 95: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 9], state store with 94 drafted / 9 mine.
- Engine's first choice was **Wan'Dale Robinson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Wan'Dale Robinson | WR | -10.6 | 0.98 | 0.98 | -10.6 | -10.6 | bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bate |
| Patrick Mahomes II | QB | 12.8 | 0.67 | 0.67 | 9.8 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Kenny Gainwell | RB | -6.2 | 0.92 | 0.92 | -7.9 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Matthew Stafford | QB | 6.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Bo Nix | QB | 4.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Jaxson Dart | QB | -10.9 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 9.8 | 3.0 | 17 |
| RB | -6.2 | -7.9 | 1.7 | 28 |
| WR | -10.6 | -10.6 | 0.0 | 35 |
| TE | 13.8 | 10.3 | 3.5 | 17 |
| K | 12.0 | 12.0 | 0.0 | 13 |
| DEF | 18.0 | 18.0 | 0.0 | 11 |

### Pick 106 (round 11): Patrick Mahomes (QB)

- In plain English: Lineup already full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) for about 3.6 weeks a season at +2.3 points a week over the waiver wire (Jacoby Brissett), worth about 8 points.
- Driver: via **action**, verified store, 493 ms, ranker engine, plan call 58, plan age 819 ms, at 02:02:00 PT.
- Engine's reason: bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts
- Top projection available: Patrick Mahomes II -> took it: True.
- Passed on: Kenny Gainwell (RB, s=0.925, e=-7.7); Courtland Sutton (WR, s=0.928, e=-11.3); Jared Goff (QB, s=None, e=None).
- Plan call 58 @pick 106: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 5, 9], state store with 105 drafted / 10 mine.
- Engine's first choice was **Patrick Mahomes II** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Patrick Mahomes II | QB | 12.8 | 0.90 | 0.90 | 10.2 | 12.8 | bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Briss |
| Kenny Gainwell | RB | -6.2 | 0.93 | 0.93 | -7.7 | -6.2 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +9. |
| Courtland Sutton | WR | -11.1 | 0.93 | 0.93 | -11.3 | -11.1 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.7 |
| Jared Goff | QB | -11.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Michael Pittman Jr. | WR | -13.3 | - | - | - | - | depth fallback (engine list exhausted) |
| Kyler Murray | QB | -14.7 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 12.8 | 10.2 | 2.6 | 14 |
| RB | -6.2 | -7.7 | 1.5 | 24 |
| WR | -11.1 | -11.3 | 0.2 | 32 |
| TE | 13.8 | 12.6 | 1.2 | 16 |
| K | 12.0 | 11.8 | 0.2 | 14 |
| DEF | 18.0 | 17.2 | 0.8 | 13 |

### Pick 115 (round 12): Aaron Jones Sr. (RB)

- In plain English: Lineup already full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +7.9 points a week over the waiver wire (Josh Jacobs), worth about 2 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 455 ms, ranker engine, plan call 63, plan age 778 ms, at 02:02:54 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Josh Jacobs) ≈ 2 pts
- Top projection available: Jared Goff -> took it: False.
- Passed on: Jakobi Meyers (WR, s=0.929, e=-21.9); Makai Lemon (WR, s=None, e=None); Romeo Doubs (WR, s=None, e=None).
- Plan call 63 @pick 115: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 9], state store with 114 drafted / 11 mine.
- Engine's first choice was **Aaron Jones Sr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Aaron Jones Sr. | RB | -25.9 | 0.93 | 0.93 | -26.1 | -25.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7. |
| Jakobi Meyers | WR | -21.5 | 0.93 | 0.93 | -21.9 | -21.5 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1 |
| Makai Lemon | WR | -27.4 | - | - | - | - | depth fallback (engine list exhausted) |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Jayden Reed | WR | -28.6 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -11.8 | -12.0 | 0.2 | 13 |
| RB | -25.9 | -26.1 | 0.2 | 23 |
| WR | -21.5 | -21.9 | 0.4 | 27 |
| TE | 0.5 | 0.3 | 0.2 | 15 |
| K | 12.0 | 11.1 | 0.9 | 15 |
| DEF | 18.0 | 13.3 | 4.7 | 13 |

### Pick 126 (round 13): Jakobi Meyers (WR)

- In plain English: Lineup already full, so Jakobi Meyers (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +2.1 points a week over the waiver wire (Rashod Bateman), worth about 2 points. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 417 ms, ranker engine, plan call 67, plan age 739 ms, at 02:03:55 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1/wk over the wire (Rashod Bateman) ≈ 2 pts
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Kyle Monangai (RB, s=0.974, e=-28.8); Romeo Doubs (WR, s=None, e=None); Deebo Samuel Sr. (WR, s=None, e=None).
- Plan call 67 @pick 126: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 9], state store with 125 drafted / 12 mine.
- Engine's first choice was **Jakobi Meyers** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jakobi Meyers | WR | -21.5 | 0.95 | 0.95 | -21.8 | -21.5 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1 |
| Kyle Monangai | RB | -28.8 | 0.97 | 0.97 | -28.8 | -28.8 | bench insurance: covers 3 RB starters behind 3 reserves already held ~0.0 wks/season · +7. |
| Romeo Doubs | WR | -27.9 | - | - | - | - | depth fallback (engine list exhausted) |
| Deebo Samuel Sr. | WR | -28.8 | - | - | - | - | depth fallback (engine list exhausted) |
| Khalil Shakir | WR | -30.1 | - | - | - | - | depth fallback (engine list exhausted) |
| Woody Marks | RB | -30.3 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 11 |
| RB | -28.8 | -28.8 | 0.0 | 20 |
| WR | -21.5 | -21.8 | 0.3 | 24 |
| TE | -2.4 | -2.6 | 0.2 | 12 |
| K | 12.0 | 11.6 | 0.4 | 16 |
| DEF | 18.0 | 17.0 | 1.0 | 13 |

### Pick 135 (round 14): Seahawks (DEF)

- In plain English: Took Seattle Seahawks (DEF) because waiting would likely cost about 6 points at DEF, with a 7% chance he would still be there next turn. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 356 ms, ranker engine, plan call 75, plan age 698 ms, at 02:05:25 PT.
- Engine's reason: waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 7% chance he's still there at your next pick · fills your open DEF slot · 10 teams picking before you still need a DEF · bargain: still here
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Cam Little (K, s=0.809, e=9.5); Cameron Dicker (K, s=None, e=None); Philadelphia Eagles (DEF, s=None, e=None).
- Plan call 75 @pick 135: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [1, 2, 3, 4, 9], state store with 134 drafted / 13 mine.
- Engine's first choice was **Seattle Seahawks** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Seattle Seahawks | DEF | 14.0 | 0.07 | 0.07 | 8.0 | 14.0 | waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 7% chance  |
| Cam Little | K | 9.0 | 0.81 | 0.81 | 9.5 | 10.5 | safe to wait on K · 81% chance he's still there at your next pick · fills your open K slot |
| Cameron Dicker | K | 10.5 | - | - | - | - | depth fallback (engine list exhausted) |
| Philadelphia Eagles | DEF | 10.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Minnesota Vikings | DEF | 8.0 | - | - | - | - | depth fallback (engine list exhausted) |
| Jason Myers | K | 7.5 | - | - | - | - | depth fallback (engine list exhausted) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -14.9 | -15.0 | 0.1 | 10 |
| RB | -30.3 | -30.6 | 0.3 | 18 |
| WR | -27.9 | -28.0 | 0.1 | 22 |
| TE | -2.4 | -2.7 | 0.3 | 12 |
| K | 10.5 | 9.5 | 1.0 | 16 |
| DEF | 14.0 | 8.0 | 6.0 | 10 |

### Pick 146 (round 15): Eddy Pineiro (K)

- In plain English: Took Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Baker Mayfield; the engine passed on him on purpose.
- Driver: via **action**, verified store, 438 ms, ranker engine, plan call 79, plan age 763 ms, at 02:05:55 PT.
- Engine's reason: fills your open K slot
- Top projection available: Baker Mayfield -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 79 @pick 146: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [1, 2, 3, 4, 9], state store with 145 drafted / 14 mine.
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
| 0-30% | 4 | 14% | 0% |
| 30-50% | 7 | 46% | 29% |
| 50-70% | 30 | 63% | 63% |
| 70-90% | 30 | 83% | 53% |
| 90-100% | 57 | 96% | 84% |

128 predictions over 57 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    01:51:10  plan #1 for pick 18: Kyren Williams RB 60% “waiting likely costs ~2 pts at RB (best opti” · Brock Bowers TE 37% “waiting likely costs ~22 pts at TE (best opt” · Josh Allen QB 55% “waiting likely costs ~7 pts at QB (best opti”
    01:51:11  driver started — seat 6, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    01:51:12  Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    01:51:20  pick 18  Omarion Hampton (RB) taken by seat 3 in 11 s — a target is gone
    01:51:20  pick 19  Ashton Jeanty (RB) taken by seat 2 in 0 s INSTANTLY (autopick)
    01:51:25  plan #3 for pick 20: Kyren Williams RB 60% “waiting likely costs ~2 pts at RB (best opti” · Brock Bowers TE 41% “waiting likely costs ~20 pts at TE (best opt” · Josh Allen QB 59% “waiting likely costs ~7 pts at QB (best opti”
    01:51:36  pick 20  A.J. Brown (WR) taken by seat 1 in 15 s — a target is gone
    01:51:38  plan #4 for pick 21: Kyren Williams RB 65% “waiting likely costs ~2 pts at RB (best opti” · Brock Bowers TE 50% “waiting likely costs ~17 pts at TE (best opt” · Josh Allen QB 69% “waiting likely costs ~5 pts at QB (best opti”
    01:52:00  pick 21  Nico Collins (WR) taken by seat 1 in 25 s — a target is gone
    01:52:00  pick 22  Jeremiyah Love (RB) taken by seat 2 in 0 s INSTANTLY (autopick)
    01:52:00  plan #5 for pick 23: Kyren Williams RB 78% “waiting likely costs ~1 pts at RB (best opti” · Brock Bowers TE 54% “waiting likely costs ~16 pts at TE (best opt” · Josh Allen QB 81% “waiting likely costs ~3 pts at QB (best opti”
    01:52:04  pick 23  Drake London (WR) taken by seat 3 in 4 s — a target is gone
    01:52:05  pick 24  Brock Bowers (TE) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 54% to survive)
    01:52:13  plan #6 for pick 25: Kyren Williams RB 93% “safe to wait on your FLEX spot” · Josh Allen QB 94% “safe to wait on QB” · Tyler Warren TE 100% “safe to wait on TE”
    01:52:16  pick 25  Malik Nabers (WR) taken by seat 5 in 11 s
    01:52:17  plan #7 for pick 26: Kyren Williams RB 63% “waiting likely costs ~3 pts at RB (best opti” · Josh Allen QB 80% “waiting likely costs ~3 pts at QB (best opti” · Tyler Warren TE 88% “safe to wait on TE”
    01:52:17  ON THE CLOCK, pick 26 · plan #7 (0.0 s old) · lineup needs QB RBx2 TE FLEX K DEF
    01:52:18  PICKED Kyren Williams (RB) via action, confirmed in 437 ms — chose Kyren Williams (RB): waiting would likely cost about 3 points at RB, 63% to still be there next turn; top projection left was Josh Allen, passed on purpose
    01:52:20  plan #8 for pick 27: Javonte Williams RB 56% “waiting likely costs ~5 pts at RB (best opti” · Josh Allen QB 79% “waiting likely costs ~4 pts at QB (best opti” · Tyler Warren TE 87% “safe to wait on TE”
    01:52:41  pick 27  Josh Allen (QB) taken by seat 7 in 24 s — a target is gone (was 79% to survive)
    01:52:45  plan #10 for pick 28: Javonte Williams RB 58% “waiting likely costs ~5 pts at RB (best opti” · Drake Maye QB 90% “waiting likely costs ~1 pts at QB (best opti” · Tyler Warren TE 90% “safe to wait on TE”
    01:52:47  pick 28  George Pickens (WR) taken by seat 8 in 6 s — a target is gone
    01:52:51  pick 29  Chris Olave (WR) taken by seat 9 in 4 s — a target is gone
    01:52:58  plan #11 for pick 30: Javonte Williams RB 71% “waiting likely costs ~3 pts at your FLEX spo” · Drake Maye QB 94% “safe to wait on QB” · Tyler Warren TE 92% “safe to wait on TE”
    01:53:14  pick 30  Tetairoa McMillan (WR) taken by seat 10 in 23 s
    01:53:17  pick 31  Tucker Kraft (TE) taken by seat 10 in 3 s
    01:53:19  pick 32  DeVonta Smith (WR) taken by seat 9 in 3 s — a target is gone
    01:53:22  plan #13 for pick 33: Javonte Williams RB 88% “waiting likely costs ~1 pts at your FLEX spo” · Drake Maye QB 97% “safe to wait on QB” · Tyler Warren TE 93% “safe to wait on TE”
    01:53:37  pick 33  Tee Higgins (WR) taken by seat 8 in 18 s
    01:53:47  plan #15 for pick 34: Javonte Williams RB 94% “safe to wait on your FLEX spot” · Drake Maye QB 100% “safe to wait on QB” · Tyler Warren TE 97% “safe to wait on TE”
    01:54:00  pick 34  Breece Hall (RB) taken by seat 7 in 23 s
    01:54:01  plan #16 for pick 35: Javonte Williams RB 59% “waiting likely costs ~5 pts at RB (best opti” · Drake Maye QB 67% “waiting likely costs ~4 pts at QB (best opti” · Tyler Warren TE 65% “safe to wait on TE”
    01:54:01  ON THE CLOCK, pick 35 · plan #16 (0.0 s old) · lineup needs QB RB TE FLEX K DEF
    01:54:01  PICKED Javonte Williams (RB) via action, confirmed in 441 ms — chose Javonte Williams (RB): waiting would likely cost about 5 points at RB, 59% to still be there next turn; top projection left was Drake Maye, passed on purpose
    01:54:04  plan #17 for pick 36: Drake Maye QB 68% “waiting likely costs ~4 pts at QB (best opti” · Tyler Warren TE 64% “safe to wait on TE” · Travis Etienne Jr. RB 48% “waiting likely costs ~3 pts at your FLEX spo”
    01:54:04  pick 36  Jaylen Waddle (WR) taken by seat 5 in 3 s
    01:54:08  pick 37  Zay Flowers (WR) taken by seat 4 in 3 s — a target is gone
    01:54:14  pick 38  Rashee Rice (WR) taken by seat 3 in 6 s — a target is gone
    01:54:14  pick 39  Garrett Wilson (WR) taken by seat 2 in 0 s INSTANTLY (autopick) — a target is gone
    01:54:16  plan #18 for pick 40: Drake Maye QB 68% “waiting likely costs ~4 pts at QB (best opti” · Tyler Warren TE 68% “safe to wait on TE” · Travis Etienne Jr. RB 61% “waiting likely costs ~1 pts at your FLEX spo”
    01:54:21  pick 40  Ladd McConkey (WR) taken by seat 1 in 7 s
    01:54:24  pick 41  Emeka Egbuka (WR) taken by seat 1 in 4 s
    01:54:25  pick 42  Terry McLaurin (WR) taken by seat 2 in 1 s INSTANTLY (autopick)
    01:54:28  pick 43  Travis Etienne Jr. (RB) taken by seat 3 in 3 s — a target is gone (was 61% to survive)
    01:54:28  pick 44  D'Andre Swift (RB) taken by seat 4 in 0 s INSTANTLY (autopick) — a target is gone
    01:54:28  plan #19 for pick 45: Drake Maye QB 93% “safe to wait on QB” · Tyler Warren TE 94% “safe to wait on TE” · Cam Skattebo RB 91% “waiting likely costs ~2 pts at your FLEX spo”
    01:54:58  pick 45  Colston Loveland (TE) taken by seat 5 in 30 s — a target is gone
    01:54:59  plan #22 for pick 46: Drake Maye QB 71% “waiting likely costs ~4 pts at QB (best opti” · Tyler Warren TE 68% “safe to wait on TE” · Cam Skattebo RB 68% “waiting likely costs ~5 pts at your FLEX spo”
    01:54:59  ON THE CLOCK, pick 46 · plan #22 (0.0 s old) · lineup needs QB TE FLEX K DEF
    01:55:00  PICKED Drake Maye (QB) via action, confirmed in 427 ms — chose Drake Maye (QB): waiting would likely cost about 4 points at QB, 71% to still be there next turn
    01:55:03  plan #23 for pick 47: Tyler Warren TE 64% “waiting likely costs ~1 pts at TE (best opti” · Cam Skattebo RB 65% “waiting likely costs ~6 pts at your FLEX spo” · Kyle Pitts Sr. TE “depth fallback (engine list exhausted)”
    01:55:08  pick 47  DJ Moore (WR) taken by seat 7 in 8 s
    01:55:12  heartbeat sent (Yahoo told we are not idle)
    01:55:12  pick 48  Tyler Warren (TE) taken by seat 8 in 5 s — a target is gone (was 64% to survive)
    01:55:15  plan #24 for pick 49: George Kittle TE 97% “safe to wait on TE” · Cam Skattebo RB 79% “waiting likely costs ~3 pts at your FLEX spo” · Kyle Pitts Sr. TE “depth fallback (engine list exhausted)”
    01:55:29  pick 49  Cam Skattebo (RB) taken by seat 9 in 16 s — a target is gone (was 79% to survive)
    01:55:32  pick 50  TreVeyon Henderson (RB) taken by seat 10 in 4 s
    01:55:35  pick 51  Luther Burden III (WR) taken by seat 10 in 3 s
    01:55:39  plan #26 for pick 52: George Kittle TE 97% “safe to wait on TE” · Jaylen Warren RB 95% “safe to wait on your FLEX spot” · Kyle Pitts Sr. TE “depth fallback (engine list exhausted)”
    01:55:53  pick 52  Rome Odunze (WR) taken by seat 9 in 18 s
    01:56:03  pick 53  Christian Watson (WR) taken by seat 8 in 9 s
    01:56:04  plan #28 for pick 54: George Kittle TE 99% “safe to wait on TE” · Jaylen Warren RB 98% “safe to wait on your FLEX spot” · Kyle Pitts Sr. TE “depth fallback (engine list exhausted)”
    01:56:29  pick 54  Mike Evans (WR) taken by seat 7 in 26 s
    01:56:30  plan #29 for pick 55: George Kittle TE 87% “safe to wait on TE” · Jaylen Warren RB 83% “safe to wait on your FLEX spot” · Kyle Pitts Sr. TE “depth fallback (engine list exhausted)”
    01:56:30  ON THE CLOCK, pick 55 · plan #29 (0.0 s old) · lineup needs TE FLEX K DEF
    01:56:30  PICKED George Kittle (TE) via action, confirmed in 377 ms — chose George Kittle (TE): nothing urgent, the most valuable player who fills a slot (87% to survive, nobody better worth waiting for); top projection left was Jalen Hurts
    01:56:33  plan #30 for pick 56: Jaylen Warren RB 78% “safe to wait on your FLEX spot” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:56:43  pick 56  Bucky Irving (RB) taken by seat 5 in 13 s — a target is gone
    01:56:45  plan #31 for pick 57: Jaylen Warren RB 88% “safe to wait on your FLEX spot” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:56:49  pick 57  Lamar Jackson (QB) taken by seat 4 in 6 s
    01:56:58  plan #32 for pick 58: Jaylen Warren RB 90% “safe to wait on your FLEX spot” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:57:11  pick 58  David Montgomery (RB) taken by seat 3 in 22 s — a target is gone
    01:57:12  pick 59  Kyle Pitts Sr. (TE) taken by seat 2 in 1 s INSTANTLY (autopick)
    01:57:12  pick 60  Bhayshul Tuten (RB) taken by seat 1 in 0 s INSTANTLY (autopick)
    01:57:13  pick 61  Joe Burrow (QB) taken by seat 1 in 1 s INSTANTLY (autopick)
    01:57:14  pick 62  Dak Prescott (QB) taken by seat 2 in 1 s INSTANTLY (autopick)
    01:57:30  pick 63  Jadarian Price (RB) taken by seat 3 in 16 s
    01:57:30  pick 64  Jameson Williams (WR) taken by seat 4 in 0 s — a target is gone
    01:57:30  plan #34 for pick 65: Jaylen Warren RB 98% “safe to wait on your FLEX spot” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:57:37  pick 65  Quinshon Judkins (RB) taken by seat 5 in 7 s — a target is gone
    01:57:38  plan #35 for pick 66: Jaylen Warren RB 68% “waiting likely costs ~2 pts at your FLEX spo” · Davante Adams WR “depth fallback (engine list exhausted)” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:57:38  ON THE CLOCK, pick 66 · plan #35 (0.0 s old) · lineup needs FLEX K DEF
    01:57:38  PICKED Jaylen Warren (RB) via action, confirmed in 460 ms — chose Jaylen Warren (RB): waiting would likely cost about 2 points at your FLEX spot, 68% to still be there next turn; top projection left was Jalen Hurts, passed on purp
    01:57:41  plan #36 for pick 67: Rico Dowdle RB 83% “bench insurance: covers 3 RB starters ~9.6 w” · Davante Adams WR 84% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:57:58  pick 67  Davante Adams (WR) taken by seat 7 in 20 s — a target is gone (was 84% to survive)
    01:58:06  plan #38 for pick 68: Rico Dowdle RB 87% “bench insurance: covers 3 RB starters ~9.6 w” · Parker Washington WR 75% “bench insurance: covers 2 WR starters ~6.5 w” · Rhamondre Stevenson RB “depth fallback (engine list exhausted)”
    01:58:08  pick 68  Jayden Daniels (QB) taken by seat 8 in 10 s
    01:58:08  pick 69  Jalen Hurts (QB) taken by seat 9 in 0 s
    01:58:10  pick 70  Rico Dowdle (RB) taken by seat 10 in 2 s INSTANTLY (autopick) — a target is gone (was 87% to survive)
    01:58:18  plan #39 for pick 71: Rhamondre Stevenson RB 86% “bench insurance: covers 3 RB starters ~9.6 w” · Parker Washington WR 86% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:58:20  pick 71  Caleb Williams (QB) taken by seat 10 in 10 s
    01:58:21  pick 72  Sam LaPorta (TE) taken by seat 9 in 1 s INSTANTLY (autopick)
    01:58:30  plan #40 for pick 73: Rhamondre Stevenson RB 91% “bench insurance: covers 3 RB starters ~9.6 w” · Parker Washington WR 92% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:58:34  pick 73  Jonathon Brooks (RB) taken by seat 8 in 13 s
    01:58:38  pick 74  Isaiah Likely (TE) taken by seat 7 in 4 s
    01:58:39  plan #41 for pick 75: Rhamondre Stevenson RB 27% “bench insurance: covers 3 RB starters ~9.6 w” · Parker Washington WR 12% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:58:39  ON THE CLOCK, pick 75 · plan #41 (0.0 s old) · lineup needs K DEF
    01:58:39  PICKED Rhamondre Stevenson (RB) via action, confirmed in 426 ms — lineup full, so Rhamondre Stevenson (RB) is insurance: covers 3 RB starter(s) about 9.6 weeks a season at +9.8 a week over the wire, about 95 points; top projection
    01:58:42  plan #42 for pick 76: Blake Corum RB 90% “bench insurance: covers 3 RB starters behind” · Parker Washington WR 9% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:58:57  pick 76  Parker Washington (WR) taken by seat 5 in 18 s — a target is gone (was 9% to survive)
    01:58:58  pick 77  Marvin Harrison Jr. (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    01:59:07  plan #44 for pick 78: Blake Corum RB 93% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 49% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:59:12  heartbeat sent (Yahoo told we are not idle)
    01:59:15  pick 78  Justin Herbert (QB) taken by seat 3 in 17 s
    01:59:15  pick 79  Brandon Aubrey (K) taken by seat 2 in 0 s INSTANTLY (autopick)
    01:59:16  pick 80  Harold Fannin Jr. (TE) taken by seat 1 in 1 s INSTANTLY (autopick)
    01:59:17  pick 81  Brian Thomas Jr. (WR) taken by seat 1 in 1 s INSTANTLY (autopick)
    01:59:18  pick 82  Carnell Tate (WR) taken by seat 2 in 1 s INSTANTLY (autopick) — a target is gone
    01:59:19  plan #45 for pick 83: Blake Corum RB 97% “bench insurance: covers 3 RB starters behind” · DK Metcalf WR 58% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:59:23  pick 83  Travis Kelce (TE) taken by seat 3 in 6 s
    01:59:24  pick 84  DK Metcalf (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone (was 58% to survive)
    01:59:32  plan #46 for pick 85: Blake Corum RB 99% “bench insurance: covers 3 RB starters behind” · Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:59:48  pick 85  Josh Downs (WR) taken by seat 5 in 24 s
    01:59:49  plan #48 for pick 86: Blake Corum RB 79% “bench insurance: covers 3 RB starters behind” · Wan'Dale Robinson WR 97% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB “depth fallback (engine list exhausted)”
    01:59:49  ON THE CLOCK, pick 86 · plan #48 (0.0 s old) · lineup needs K DEF
    01:59:50  PICKED Blake Corum (RB) via action, confirmed in 519 ms — lineup full, so Blake Corum (RB) is insurance: covers 3 RB starter(s) about 2.5 weeks a season at +9.8 a week over the wire, about 25 points; he also backs up one of our st
    01:59:53  plan #49 for pick 87: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 86% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    01:59:55  pick 87  MarShawn Lloyd (RB) taken by seat 7 in 6 s
    02:00:05  plan #50 for pick 88: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · RJ Harvey RB 85% “bench insurance: covers 3 RB starters behind” · Kenny Gainwell RB “depth fallback (engine list exhausted)”
    02:00:19  pick 88  Chris Godwin Jr. (WR) taken by seat 8 in 24 s — a target is gone
    02:00:19  pick 89  Trevor Lawrence (QB) taken by seat 9 in 0 s INSTANTLY (autopick)
    02:00:23  pick 90  Alec Pierce (WR) taken by seat 10 in 4 s
    02:00:25  pick 91  RJ Harvey (RB) taken by seat 10 in 2 s INSTANTLY (autopick) — a target is gone (was 85% to survive)
    02:00:26  pick 92  Tony Pollard (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    02:00:46  pick 93  Brock Purdy (QB) taken by seat 8 in 20 s
    02:00:46  plan #52 for pick 94: Wan'Dale Robinson WR 100% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 98% “bench insurance: covers 1 QB starter ~3.6 wk” · Kenny Gainwell RB 99% “bench insurance: covers 3 RB starte
    02:00:49  pick 94  Michael Wilson (WR) taken by seat 7 in 4 s
    02:00:50  plan #53 for pick 95: Wan'Dale Robinson WR 98% “bench insurance: covers 2 WR starters ~6.5 w” · Patrick Mahomes II QB 67% “bench insurance: covers 1 QB starter ~3.6 wk” · Kenny Gainwell RB 92% “bench insurance: covers 3 RB starter
    02:00:50  ON THE CLOCK, pick 95 · plan #53 (0.0 s old) · lineup needs K DEF
    02:00:51  PICKED Wan'Dale Robinson (WR) via action, confirmed in 481 ms — lineup full, so Wan'Dale Robinson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +2.7 a week over the wire, about 17 points; top projection lef
    02:00:54  plan #54 for pick 96: Patrick Mahomes II QB 66% “bench insurance: covers 1 QB starter ~3.6 wk” · Kenny Gainwell RB 91% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 69% “bench insurance: covers 2 WR starters
    02:01:20  pick 96  Bo Nix (QB) taken by seat 5 in 29 s — a target is gone
    02:01:21  pick 97  J.K. Dobbins (RB) taken by seat 4 in 1 s INSTANTLY (autopick)
    02:01:22  pick 98  Quentin Johnston (WR) taken by seat 3 in 1 s INSTANTLY (autopick)
    02:01:29  pick 99  Chuba Hubbard (RB) taken by seat 2 in 7 s
    02:01:29  pick 100  Jacory Croskey-Merritt (RB) taken by seat 1 in 0 s
    02:01:29  pick 101  Jaxson Dart (QB) taken by seat 1 in 0 s — a target is gone
    02:01:29  pick 102  Stefon Diggs (WR) taken by seat 2 in 0 s
    02:01:29  pick 103  Dalton Kincaid (TE) taken by seat 3 in 0 s
    02:01:29  pick 104  Matthew Stafford (QB) taken by seat 4 in 0 s — a target is gone
    02:01:31  plan #57 for pick 105: Patrick Mahomes II QB 98% “bench insurance: covers 1 QB starter ~3.6 wk” · Kenny Gainwell RB 99% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 99% “bench insurance: covers 2 WR starter
    02:01:58  pick 105  Jordan Mason (RB) taken by seat 5 in 30 s
    02:01:59  plan #58 for pick 106: Patrick Mahomes II QB 90% “bench insurance: covers 1 QB starter ~3.6 wk” · Kenny Gainwell RB 93% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 93% “bench insurance: covers 2 WR starter
    02:01:59  ON THE CLOCK, pick 106 · plan #58 (0.0 s old) · lineup needs K DEF
    02:02:00  PICKED Patrick Mahomes II (QB) via action, confirmed in 493 ms — lineup full, so Patrick Mahomes II (QB) is insurance: covers 1 QB starter(s) about 3.6 weeks a season at +2.3 a week over the wire, about 8 points
    02:02:03  plan #59 for pick 107: Kenny Gainwell RB 89% “bench insurance: covers 3 RB starters behind” · Courtland Sutton WR 91% “bench insurance: covers 2 WR starters behind” · Michael Pittman Jr. WR “depth fallback (engine list exhausted)”
    02:02:04  pick 107  Rams (DEF) taken by seat 7 in 4 s
    02:02:07  pick 108  De'Zhaun Stribling (WR) taken by seat 8 in 3 s
    02:02:07  pick 109  Jordan Addison (WR) taken by seat 9 in 0 s INSTANTLY (autopick) — a target is gone
    02:02:14  pick 110  Courtland Sutton (WR) taken by seat 10 in 7 s — a target is gone (was 91% to survive)
    02:02:15  plan #60 for pick 111: Kenny Gainwell RB 98% “bench insurance: covers 3 RB starters behind” · Michael Pittman Jr. WR 96% “bench insurance: covers 2 WR starters behind” · Jakobi Meyers WR “depth fallback (engine list exhausted)”
    02:02:17  pick 111  Kenny Gainwell (RB) taken by seat 10 in 3 s — a target is gone (was 98% to survive)
    02:02:17  pick 112  Dallas Goedert (TE) taken by seat 9 in 0 s
    02:02:23  pick 113  Michael Pittman Jr. (WR) taken by seat 8 in 5 s — a target is gone (was 96% to survive)
    02:02:27  plan #61 for pick 114: Aaron Jones Sr. RB 100% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 99% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    02:02:52  pick 114  Matthew Golden (WR) taken by seat 7 in 29 s
    02:02:53  plan #63 for pick 115: Aaron Jones Sr. RB 93% “bench insurance: covers 3 RB starters behind” · Jakobi Meyers WR 93% “bench insurance: covers 2 WR starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    02:02:53  ON THE CLOCK, pick 115 · plan #63 (0.0 s old) · lineup needs K DEF
    02:02:54  PICKED Aaron Jones Sr. (RB) via action, confirmed in 455 ms — lineup full, so Aaron Jones Sr. (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +7.9 a week over the wire, about 2 points; top projection left was
    02:02:56  plan #64 for pick 116: Jakobi Meyers WR 93% “bench insurance: covers 2 WR starters behind” · Kyle Monangai RB 94% “bench insurance: covers 3 RB starters behind” · Makai Lemon WR “depth fallback (engine list exhausted)”
    02:03:12  heartbeat sent (Yahoo told we are not idle)
    02:03:22  pick 116  Josh Jacobs (RB) taken by seat 5 in 29 s
    02:03:22  pick 117  Mark Andrews (TE) taken by seat 4 in 0 s INSTANTLY (autopick)
    02:03:23  pick 118  Kyler Murray (QB) taken by seat 3 in 1 s INSTANTLY (autopick)
    02:03:24  pick 119  Jared Goff (QB) taken by seat 2 in 1 s INSTANTLY (autopick)
    02:03:27  pick 120  Juwan Johnson (TE) taken by seat 1 in 2 s
    02:03:28  pick 121  Jayden Reed (WR) taken by seat 1 in 1 s INSTANTLY (autopick) — a target is gone
    02:03:28  pick 122  Jake Ferguson (TE) taken by seat 2 in 0 s INSTANTLY (autopick)
    02:03:29  pick 123  KC Concepcion (WR) taken by seat 3 in 1 s INSTANTLY (autopick) — a target is gone
    02:03:30  pick 124  Makai Lemon (WR) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    02:03:54  pick 125  Rachaad White (RB) taken by seat 5 in 24 s
    02:03:55  plan #67 for pick 126: Jakobi Meyers WR 95% “bench insurance: covers 2 WR starters behind” · Kyle Monangai RB 97% “bench insurance: covers 3 RB starters behind” · Romeo Doubs WR “depth fallback (engine list exhausted)”
    02:03:55  ON THE CLOCK, pick 126 · plan #67 (0.0 s old) · lineup needs K DEF
    02:03:55  PICKED Jakobi Meyers (WR) via action, confirmed in 417 ms — lineup full, so Jakobi Meyers (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +2.1 a week over the wire, about 2 points; top projection left was Bak
    02:03:58  plan #68 for pick 127: Houston Texans DEF 46% “waiting likely costs ~1 pts at DEF (best opt” · Cameron Dicker K 83% “safe to wait on K” · Denver Broncos DEF “depth fallback (engine list exhausted)”
    02:04:21  pick 127  Ka'imi Fairbairn (K) taken by seat 7 in 25 s — a target is gone
    02:04:23  plan #70 for pick 128: Houston Texans DEF 49% “waiting likely costs ~1 pts at DEF (best opt” · Cam Little K 86% “safe to wait on K” · Denver Broncos DEF “depth fallback (engine list exhausted)”
    02:04:32  pick 128  Mike Washington Jr. (RB) taken by seat 8 in 12 s
    02:04:33  pick 129  Kyle Monangai (RB) taken by seat 9 in 1 s INSTANTLY (autopick)
    02:04:36  plan #71 for pick 130: Houston Texans DEF 68% “safe to wait on DEF” · Cam Little K 87% “safe to wait on K” · Denver Broncos DEF “depth fallback (engine list exhausted)”
    02:04:39  pick 130  Jordan Love (QB) taken by seat 10 in 6 s
    02:04:48  plan #72 for pick 131: Houston Texans DEF 70% “safe to wait on DEF” · Cam Little K 92% “safe to wait on K” · Denver Broncos DEF “depth fallback (engine list exhausted)”
    02:04:52  pick 131  Steelers (DEF) taken by seat 10 in 12 s
    02:04:52  pick 132  Texans (DEF) taken by seat 9 in 0 s
    02:04:59  pick 133  Broncos (DEF) taken by seat 8 in 7 s
    02:05:00  plan #73 for pick 134: Seattle Seahawks DEF 100% “safe to wait on DEF” · Cam Little K 99% “safe to wait on K” · Cameron Dicker K “depth fallback (engine list exhausted)”
    02:05:23  pick 134  Xavier Worthy (WR) taken by seat 7 in 24 s
    02:05:24  plan #75 for pick 135: Seattle Seahawks DEF 7% “waiting likely costs ~6 pts at DEF (best opt” · Cam Little K 81% “safe to wait on K” · Cameron Dicker K “depth fallback (engine list exhausted)”
    02:05:24  ON THE CLOCK, pick 135 · plan #75 (0.0 s old) · lineup needs K DEF
    02:05:25  PICKED Seattle Seahawks (DEF) via action, confirmed in 356 ms — chose Seattle Seahawks (DEF): waiting would likely cost about 6 points at DEF, 7% to still be there next turn; top projection left was Baker Mayfield, passed on purpo
    02:05:27  pick 136  Jason Myers (K) taken by seat 5 in 3 s — a target is gone
    02:05:27  pick 137  Eagles (DEF) taken by seat 4 in 0 s
    02:05:27  pick 138  Cameron Dicker (K) taken by seat 3 in 0 s — a target is gone
    02:05:28  plan #76 for pick 139: Cam Little K 51% “waiting likely costs ~2 pts at K (best optio” · Eddy Pineiro K “depth fallback (engine list exhausted)” · Tyler Loop K “depth fallback (engine list exhausted)”
    02:05:30  pick 139  Chris Rodriguez Jr. (RB) taken by seat 2 in 3 s
    02:05:30  pick 140  Vikings (DEF) taken by seat 1 in 0 s
    02:05:30  pick 141  Cam Little (K) taken by seat 1 in 0 s — a target is gone (was 51% to survive)
    02:05:31  pick 142  Jaguars (DEF) taken by seat 2 in 1 s INSTANTLY (autopick)
    02:05:32  pick 143  Patriots (DEF) taken by seat 3 in 1 s INSTANTLY (autopick)
    02:05:33  pick 144  Tyler Loop (K) taken by seat 4 in 1 s INSTANTLY (autopick) — a target is gone
    02:05:40  plan #77 for pick 145: Eddy Pineiro K 98% “safe to wait on K” · Evan McPherson K “depth fallback (engine list exhausted)” · Cairo Santos K “depth fallback (engine list exhausted)”
    02:05:55  pick 145  Rashid Shaheed (WR) taken by seat 5 in 22 s
    02:05:55  plan #79 for pick 146: Eddy Pineiro K “fills your open K slot” · Evan McPherson K “depth fallback (engine list exhausted)” · Cairo Santos K “depth fallback (engine list exhausted)”
    02:05:55  ON THE CLOCK, pick 146 · plan #79 (0.0 s old) · lineup needs K
    02:05:55  PICKED Eddy Pineiro (K) via action, confirmed in 438 ms — chose Eddy Pineiro (K) to fill a mandatory slot; nothing the engine named was left; top projection left was Baker Mayfield, passed on purpose
    02:05:58  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    01:51:11 PT preflight: ok=false pick_path=action my_team=6 plan=plan 25 deep @pick 18 via store call#1
    01:51:11 PT driver start — WARNING: tab is hidden, Chrome throttles timers; keep it visible
    01:51:11 PT NARR info driver started — seat 6, 10 teams, 15 rounds — WARNING: tab hidden, keep it visible
    01:51:12 PT AWAY detected (store=true) -> setAwayStatus(false); away now false
    01:51:12 PT NARR away Yahoo flagged us AWAY — cleared through setAwayStatus (confirmed)
    01:52:18 PT ON CLOCK -> {"drafted":"Kyren Williams","pos":"RB","vorp":40.5,"proj":200.7,"why":"waiting likely costs ~3 pts at RB (best option now 40, ~37 by your next turn) · 63% chance he's still there at your next pick · fills your open R
    01:54:01 PT ON CLOCK -> {"drafted":"Javonte Williams","pos":"RB","vorp":36.9,"proj":197.1,"why":"waiting likely costs ~5 pts at RB (best option now 37, ~32 by your next turn) · 59% chance he's still there at your next pick · fills your open
    01:55:00 PT ON CLOCK -> {"drafted":"Drake Maye","pos":"QB","vorp":31.1,"proj":304.7,"why":"waiting likely costs ~4 pts at QB (best option now 31, ~27 by your next turn) · 71% chance he's still there at your next pick · fills your open QB sl
    01:55:12 PT heartbeat: setAwayStatus(false)
    01:55:12 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    01:56:30 PT ON CLOCK -> {"drafted":"George Kittle","pos":"TE","vorp":19.8,"proj":142,"why":"safe to wait on TE · 87% chance he's still there at your next pick · fills your open TE slot · 8 teams picking before you still need a TE · two-pick
    01:57:38 PT ON CLOCK -> {"drafted":"Jaylen Warren","pos":"RB","vorp":9.3,"proj":169.5,"why":"waiting likely costs ~2 pts at your FLEX spot (best option now 9, ~8 by your next turn) · 68% chance he's still there at your next pick · fills a F
    01:58:40 PT ON CLOCK -> {"drafted":"Rhamondre Stevenson","pos":"RB","vorp":7.2,"proj":167.4,"why":"bench insurance: covers 3 RB starters ~9.6 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 95 pts","s":0.273,"sr":0.273,"e":-2,"top_proj_a
    01:59:12 PT heartbeat: setAwayStatus(false)
    01:59:12 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    01:59:50 PT ON CLOCK -> {"drafted":"Blake Corum","pos":"RB","vorp":-46.1,"proj":114.1,"why":"bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +9.8/wk over the wire (Josh Jacobs) ≈ 25 pts · HANDCUFF: back
    02:00:51 PT ON CLOCK -> {"drafted":"Wan'Dale Robinson","pos":"WR","vorp":-10.6,"proj":131.5,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +2.7/wk over the wire (Rashod Bateman) ≈ 17 pts","s":0.98,"sr":0.98,"e":-10.6,"top_pr
    02:02:00 PT ON CLOCK -> {"drafted":"Patrick Mahomes II","pos":"QB","vorp":12.8,"proj":286.4,"why":"bench insurance: covers 1 QB starter ~3.6 wks/season · +2.3/wk over the wire (Jacoby Brissett) ≈ 8 pts","s":0.897,"sr":0.897,"e":10.2,"top_pr
    02:02:54 PT ON CLOCK -> {"drafted":"Aaron Jones Sr.","pos":"RB","vorp":-25.9,"proj":134.3,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +7.9/wk over the wire (Josh Jacobs) ≈ 2 pts","s":0.932,"
    02:03:12 PT heartbeat: setAwayStatus(false)
    02:03:12 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    02:03:55 PT ON CLOCK -> {"drafted":"Jakobi Meyers","pos":"WR","vorp":-21.5,"proj":120.7,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +2.1/wk over the wire (Rashod Bateman) ≈ 2 pts","s":0.954,"
    02:05:25 PT ON CLOCK -> {"drafted":"Seattle Seahawks","pos":"DEF","vorp":14,"proj":131,"why":"waiting likely costs ~6 pts at DEF (best option now 14, ~8 by your next turn) · 7% chance he's still there at your next pick · fills your open DEF
    02:05:55 PT ON CLOCK -> {"drafted":"Eddy Pineiro","pos":"K","vorp":6,"proj":142.5,"why":"fills your open K slot","s":null,"sr":null,"e":null,"top_proj_available":{"n":"Baker Mayfield","p":"QB","proj":258.7,"vorp":-14.9},"took_top_projection
    02:05:58 PT roster full
    02:05:58 PT NARR info roster full — driver done; posting the trail when the room finishes
    02:05:58 PT driver stop


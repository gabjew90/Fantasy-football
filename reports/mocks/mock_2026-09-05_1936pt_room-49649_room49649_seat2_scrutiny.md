# Scrutiny: Mock -- room 49649 (room 49649) -- Saturday 2026-09-05 19:36 PT -- 10 teams, our seat 2

Captured 2026-09-05 20:00:39 PT. Times below are Pacific. 10 teams, our team id 3, draft slot 2. 146 picks in the trail, 379 bridge plan calls, 124 recs events in the room log.

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

- Our picks: 15; by the driver 6 (action 6, click 0), by Yahoo from the queue / autopick 9: 2 Jahmyr Gibbs, 19 Drake London, 22 A.J. Brown, 39 Travis Etienne Jr., 42 Cam Skattebo, 59 Jayden Daniels, 62 Sam LaPorta, 79 Rico Dowdle, 82 Jaylen Warren.
- Action latency to store confirmation: median 380 ms, min 254, max 470.
- Heartbeats 21; away flags detected and cleared 0; gate failures 0; local-ranker fallbacks 0; plan refresh failures 0.
- Bridge warnings (0): none.
- Away seats over the room (each change): {} -> {4} -> {3,4} -> {4} -> {4,9} -> {1,4,9} -> {4,9} -> {4} -> {4,9} -> {4} -> {4,9} -> {4} -> {4,8} -> {4} -> {4,9} -> {4} -> {4,9} -> {4} -> {4,9} -> {1,4,9} -> {4,9} -> {4,6,9} -> {4,6,7,9}.
- Managers away at the end: 1 Simon, 2 Edward, 4 x3shift, 6 pmo.

## Our picks, one block each

### Pick 2 (round 1): Jahmyr Gibbs (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 194 @pick 2: needs {'QB': 1, 'RB': 2, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [], state store with 1 drafted / 0 mine.
- Engine's first choice was **Jahmyr Gibbs** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jahmyr Gibbs | RB | 133.2 | 0.15 | 0.19 | 74.3 | 133.2 | waiting likely costs ~59 pts at RB (best option now 133, ~74 by your next turn) · 15% chan |
| Bijan Robinson | RB | 112.2 | 0.15 | 0.18 | 74.3 | 133.2 | waiting likely costs ~59 pts at RB (best option now 133, ~74 by your next turn) · 15% chan |
| Jonathan Taylor | RB | 91.1 | 0.15 | 0.18 | 74.3 | 133.2 | waiting likely costs ~59 pts at RB (best option now 133, ~74 by your next turn) · 15% chan |
| Ja'Marr Chase | WR | 103.0 | 0.16 | 0.24 | 72.8 | 104.6 | waiting likely costs ~32 pts at WR (best option now 105, ~73 by your next turn) · 16% chan |
| Puka Nacua | WR | 104.6 | 0.15 | 0.21 | 72.8 | 104.6 | waiting likely costs ~32 pts at WR (best option now 105, ~73 by your next turn) · 15% chan |
| Jaxon Smith-Njigba | WR | 96.2 | 0.16 | 0.22 | 72.8 | 104.6 | waiting likely costs ~32 pts at WR (best option now 105, ~73 by your next turn) · 16% chan |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 58.1 | 39.1 | 19.0 | 6 |
| RB | 133.2 | 74.3 | 58.9 | 23 |
| WR | 104.6 | 72.8 | 31.8 | 25 |
| TE | 56.0 | 53.2 | 2.8 | 5 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 133.2375721372549 | 85.2 | 48.0 | 53 |

### Pick 19 (round 2): Drake London (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 223 @pick 19: needs {'QB': 1, 'RB': 1, 'WR': 2, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 18 drafted / 1 mine.
- Engine's first choice was **Drake London** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Drake London | WR | 46.5 | 0.73 | 0.81 | 45.7 | 46.5 | waiting likely costs ~2 pts at your FLEX spot (best option now 38, ~36 by your next turn)  |
| A.J. Brown | WR | 44.6 | 0.77 | 0.84 | 45.7 | 46.5 | safe to wait on WR · 76% chance he's still there at your next pick · fills your open WR sl |
| Chris Olave | WR | 40.5 | 0.84 | 0.92 | 45.7 | 46.5 | safe to wait on WR · 84% chance he's still there at your next pick · fills your open WR sl |
| Ashton Jeanty | RB | 37.9 | 0.75 | 0.83 | 36.1 | 37.9 | waiting likely costs ~2 pts at RB (best option now 38, ~36 by your next turn) · 75% chance |
| Kyren Williams | RB | 30.2 | 0.80 | 0.88 | 36.1 | 37.9 | waiting likely costs ~2 pts at RB (best option now 38, ~36 by your next turn) · 80% chance |
| Javonte Williams | RB | 30.8 | 0.86 | 0.94 | 36.1 | 37.9 | waiting likely costs ~2 pts at RB (best option now 38, ~36 by your next turn) · 86% chance |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 58.1 | 50.8 | 7.3 | 9 |
| RB | 37.9 | 36.1 | 1.8 | 16 |
| WR | 46.5 | 45.7 | 0.8 | 25 |
| TE | 56.0 | 55.0 | 1.0 | 8 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 37.91462206070591 | 36.4 | 1.5 | 49 |

### Pick 22 (round 3): A.J. Brown (WR)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 229 @pick 22: needs {'QB': 1, 'RB': 1, 'WR': 1, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 21 drafted / 2 mine.
- Engine's first choice was **A.J. Brown** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| A.J. Brown | WR | 44.6 | 0.16 | 0.21 | 28.6 | 44.6 | waiting likely costs ~16 pts at WR (best option now 45, ~29 by your next turn) · 16% chanc |
| George Pickens | WR | 39.8 | 0.14 | 0.16 | 28.6 | 44.6 | waiting likely costs ~16 pts at WR (best option now 45, ~29 by your next turn) · 14% chanc |
| Nico Collins | WR | 39.1 | 0.03 | 0.04 | 28.6 | 44.6 | waiting likely costs ~16 pts at WR (best option now 45, ~29 by your next turn) · 3% chance |
| Ashton Jeanty | RB | 37.9 | 0.08 | 0.09 | 25.0 | 37.9 | waiting likely costs ~13 pts at RB (best option now 38, ~25 by your next turn) · 8% chance |
| Javonte Williams | RB | 30.8 | 0.19 | 0.32 | 25.0 | 37.9 | waiting likely costs ~13 pts at RB (best option now 38, ~25 by your next turn) · 19% chanc |
| Kyren Williams | RB | 30.2 | 0.16 | 0.23 | 25.0 | 37.9 | waiting likely costs ~13 pts at RB (best option now 38, ~25 by your next turn) · 16% chanc |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 58.1 | 26.0 | 32.1 | 9 |
| RB | 37.9 | 25.0 | 12.9 | 16 |
| WR | 44.6 | 28.6 | 16.0 | 24 |
| TE | 56.0 | 30.8 | 25.2 | 7 |
| K | 0.0 | 0.0 | 0.0 | 0 |
| DEF | 0.0 | 0.0 | 0.0 | 0 |
| FLEX | 37.91462206070591 | 26.8 | 11.1 | 47 |

### Pick 39 (round 4): Travis Etienne Jr. (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 264 @pick 39: needs {'QB': 1, 'RB': 1, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 38 drafted / 3 mine.
- Engine's first choice was **Travis Etienne Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Travis Etienne Jr. | RB | 23.2 | 0.78 | 0.86 | 21.7 | 23.2 | waiting likely costs ~1 pts at RB (best option now 23, ~22 by your next turn) · 78% chance |
| D'Andre Swift | RB | 16.3 | 0.81 | 0.89 | 21.7 | 23.2 | waiting likely costs ~1 pts at RB (best option now 23, ~22 by your next turn) · 81% chance |
| Cam Skattebo | RB | 16.9 | 0.78 | 0.86 | 21.7 | 23.2 | waiting likely costs ~1 pts at RB (best option now 23, ~22 by your next turn) · 78% chance |
| Lamar Jackson | QB | 19.9 | 0.82 | 0.91 | 19.4 | 19.9 | safe to wait on QB · 82% chance he's still there at your next pick · fills your open QB sl |
| Jalen Hurts | QB | 17.4 | 0.92 | 0.97 | 19.4 | 19.9 | safe to wait on QB · 92% chance he's still there at your next pick · fills your open QB sl |
| Drake Maye | QB | 15.9 | 0.84 | 0.92 | 19.4 | 19.9 | safe to wait on QB · 84% chance he's still there at your next pick · fills your open QB sl |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 19.9 | 19.4 | 0.5 | 12 |
| RB | 23.2 | 21.7 | 1.5 | 18 |
| WR | 15.4 | 14.2 | 1.2 | 18 |
| TE | 21.1 | 20.7 | 0.4 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 23.182738941176524 | 21.7 | 1.5 | 44 |

### Pick 42 (round 5): Cam Skattebo (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 270 @pick 42: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 1, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 41 drafted / 4 mine.
- Engine's first choice was **Cam Skattebo** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Cam Skattebo | RB | 16.9 | 0.10 | 0.11 | 5.4 | 16.9 | waiting likely costs ~12 pts at your FLEX spot (best option now 17, ~5 by your next turn)  |
| Bucky Irving | RB | 11.9 | 0.17 | 0.28 | 5.4 | 16.9 | waiting likely costs ~12 pts at your FLEX spot (best option now 17, ~5 by your next turn)  |
| Quinshon Judkins | RB | 8.3 | 0.24 | 0.42 | 5.4 | 16.9 | waiting likely costs ~12 pts at your FLEX spot (best option now 17, ~5 by your next turn)  |
| Lamar Jackson | QB | 19.9 | 0.17 | 0.25 | 12.7 | 19.9 | waiting likely costs ~7 pts at QB (best option now 20, ~13 by your next turn) · 17% chance |
| Jalen Hurts | QB | 17.4 | 0.21 | 0.39 | 12.7 | 19.9 | waiting likely costs ~7 pts at QB (best option now 20, ~13 by your next turn) · 21% chance |
| Drake Maye | QB | 15.9 | 0.19 | 0.34 | 12.7 | 19.9 | waiting likely costs ~7 pts at QB (best option now 20, ~13 by your next turn) · 19% chance |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 19.9 | 12.7 | 7.2 | 13 |
| RB | 16.9 | 4.6 | 12.3 | 17 |
| WR | 15.4 | 5.8 | 9.6 | 19 |
| TE | 21.1 | 17.7 | 3.4 | 8 |
| K | 13.5 | 13.5 | 0.0 | 1 |
| DEF | 18.0 | 18.0 | 0.0 | 3 |
| FLEX | 16.89404529411769 | 5.4 | 11.5 | 44 |

### Pick 59 (round 6): Jayden Daniels (QB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 303 @pick 59: needs {'QB': 1, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 58 drafted / 5 mine.
- Engine's first choice was **Jayden Daniels** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jayden Daniels | QB | 15.2 | 0.77 | 0.85 | 12.8 | 15.2 | waiting likely costs ~2 pts at QB (best option now 15, ~13 by your next turn) · 77% chance |
| Kyle Pitts Sr. | TE | 13.1 | 0.88 | 0.96 | 13.3 | 13.3 | safe to wait on TE · 88% chance he's still there at your next pick · fills your open TE sl |
| Sam LaPorta | TE | 13.3 | 0.84 | 0.92 | 13.3 | 13.3 | safe to wait on TE · 84% chance he's still there at your next pick · fills your open TE sl |
| Tucker Kraft | TE | 13.2 | 0.84 | 0.92 | 13.3 | 13.3 | safe to wait on TE · 84% chance he's still there at your next pick · fills your open TE sl |
| Trevor Lawrence | QB | 5.2 | 0.87 | 0.95 | 12.8 | 15.2 | waiting likely costs ~2 pts at QB (best option now 15, ~13 by your next turn) · 87% chance |
| Dak Prescott | QB | 3.5 | 0.81 | 0.89 | 12.8 | 15.2 | waiting likely costs ~2 pts at QB (best option now 15, ~13 by your next turn) · 81% chance |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 15.2 | 12.8 | 2.4 | 14 |
| RB | 5.0 | 3.7 | 1.3 | 18 |
| WR | 2.1 | 0.9 | 1.2 | 21 |
| TE | 13.3 | 13.3 | 0.0 | 9 |
| K | 13.5 | 13.5 | 0.0 | 2 |
| DEF | 18.0 | 18.0 | 0.0 | 5 |

### Pick 62 (round 7): Sam LaPorta (TE)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 313 @pick 62: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 1, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 61 drafted / 6 mine.
- Engine's first choice was **Sam LaPorta** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Sam LaPorta | TE | 13.3 | 0.17 | 0.27 | 10.0 | 13.3 | waiting likely costs ~3 pts at TE (best option now 13, ~10 by your next turn) · 17% chance |
| Kyle Pitts Sr. | TE | 13.1 | 0.17 | 0.27 | 10.0 | 13.3 | waiting likely costs ~3 pts at TE (best option now 13, ~10 by your next turn) · 17% chance |
| Tucker Kraft | TE | 13.2 | 0.17 | 0.26 | 10.0 | 13.3 | waiting likely costs ~3 pts at TE (best option now 13, ~10 by your next turn) · 17% chance |
| Travis Kelce | TE | 9.0 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |
| Dallas Goedert | TE | 6.7 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |
| Bhayshul Tuten | RB | 5.0 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 5.2 | 3.9 | 1.3 | 14 |
| RB | 5.0 | -8.9 | 13.9 | 19 |
| WR | -6.9 | -14.2 | 7.3 | 21 |
| TE | 13.3 | 10.0 | 3.3 | 9 |
| K | 13.5 | 13.3 | 0.2 | 3 |
| DEF | 18.0 | 17.9 | 0.1 | 6 |

### Pick 79 (round 8): Rico Dowdle (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 363 @pick 79: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 78 drafted / 7 mine.
- Engine's first choice was **Rico Dowdle** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Rico Dowdle | RB | -20.6 | 0.88 | 0.95 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +3.1/wk over the wire (Chris Rodri |
| Tony Pollard | RB | -16.2 | 0.86 | 0.94 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +3.3/wk over the wire (Chris Rodri |
| Jaylen Warren | RB | -14.1 | 0.88 | 0.96 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +3.4/wk over the wire (Chris Rodri |
| Chuba Hubbard | RB | -32.7 | 0.88 | 0.96 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +2.4/wk over the wire (Chris Rodri |
| Jonathon Brooks | RB | -30.6 | 0.90 | 0.97 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +2.5/wk over the wire (Chris Rodri |
| MarShawn Lloyd | RB | -34.7 | 0.90 | 0.96 | -14.4 | -14.1 | bench insurance: covers 3 RB starters ~9.6 wks/season · +2.2/wk over the wire (Chris Rodri |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 3.0 | 2.9 | 0.1 | 18 |
| RB | -14.1 | -14.4 | 0.3 | 34 |
| WR | -15.9 | -16.3 | 0.4 | 37 |
| TE | 6.7 | 6.3 | 0.4 | 18 |
| K | 13.5 | 13.5 | 0.0 | 15 |
| DEF | 18.0 | 18.0 | 0.0 | 8 |

### Pick 82 (round 9): Jaylen Warren (RB)

- **No driver record**: Yahoo made this pick (queue head or autopick).
- The turn in the driver log:
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still t
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceili
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still t
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: z
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_projection":false,"pas
- Plan call 369 @pick 82: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 81 drafted / 8 mine.
- Engine's first choice was **Jaylen Warren** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Jaylen Warren | RB | -14.1 | 0.05 | 0.06 | -24.1 | -14.1 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +3.4 |
| Tony Pollard | RB | -16.2 | 0.40 | 0.57 | -24.1 | -14.1 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +3.3 |
| MarShawn Lloyd | RB | -34.7 | 0.15 | 0.21 | -24.1 | -14.1 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +2.2 |
| DK Metcalf | WR | -15.9 | 0.44 | 0.61 | -18.2 | -15.9 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.2/wk over the wire (Denzel Bost |
| Brian Thomas Jr. | WR | -21.8 | 0.22 | 0.41 | -18.2 | -15.9 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.9/wk over the wire (Denzel Bost |
| J.K. Dobbins | RB | -23.9 | 0.44 | 0.60 | -24.1 | -14.1 | bench insurance: covers 3 RB starters behind 1 reserve already held ~2.5 wks/season · +2.9 |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 3.0 | 1.5 | 1.5 | 17 |
| RB | -14.1 | -24.1 | 10.0 | 32 |
| WR | -15.9 | -18.2 | 2.3 | 39 |
| TE | 6.7 | 4.7 | 2.0 | 18 |
| K | 13.5 | 13.1 | 0.4 | 17 |
| DEF | 18.0 | 17.5 | 0.5 | 9 |

### Pick 99 (round 10): J.K. Dobbins (RB)

- In plain English: Lineup already full, so J.K. Dobbins (RB) is insurance: covers 3 RB starter(s) for about 0.2 weeks a season at +2.9 points a week over the waiver wire (Chris Rodriguez Jr.), worth about 1 points. The top raw projection available was Jaxson Dart; the engine passed on him on purpose.
- Driver: via **action**, verified store, 361 ms, ranker engine, plan call 411, plan age 927 ms, at 19:43:40 PT.
- Engine's reason: bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timing: 92% he is still there next turn -> score 0.1 · ceiling 149 · BENCH STAGED: 23 within 2, survival within 0.15: higher ceiling over the wire (63)
- Top projection available: Jaxson Dart -> took it: False.
- Passed on: RJ Harvey (RB, s=0.925, e=-25.3); Rachaad White (RB, s=0.979, e=-25.3); Kyle Monangai (RB, s=0.907, e=-25.3).
- Plan call 411 @pick 99: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 98 drafted / 9 mine.
- Engine's first choice was **J.K. Dobbins** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| J.K. Dobbins | RB | -23.9 | 0.92 | 0.97 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2. |
| RJ Harvey | RB | -42.4 | 0.93 | 0.97 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |
| Rachaad White | RB | -44.1 | 0.98 | 0.99 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |
| Kyle Monangai | RB | -42.9 | 0.91 | 0.97 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |
| Kenny Gainwell | RB | -41.5 | 0.95 | 0.98 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |
| Jacory Croskey-Merritt | RB | -44.0 | 0.91 | 0.97 | -25.3 | -23.9 | bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +1. |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 3.0 | 2.4 | 0.6 | 16 |
| RB | -23.9 | -25.3 | 1.4 | 26 |
| WR | -18.2 | -18.6 | 0.4 | 35 |
| TE | 6.7 | 6.1 | 0.6 | 18 |
| K | 12.0 | 12.0 | 0.0 | 21 |
| DEF | 10.0 | 10.0 | 0.0 | 7 |

### Pick 102 (round 11): Michael Wilson (WR)

- In plain English: Lineup already full, so Michael Wilson (WR) is insurance: covers 2 WR starter(s) for about 6.5 weeks a season at +0.4 points a week over the waiver wire (Denzel Boston), worth about 2 points. The top raw projection available was Jaxson Dart; the engine passed on him on purpose.
- Driver: via **action**, verified store, 470 ms, ranker engine, plan call 418, plan age 1000 ms, at 19:44:49 PT.
- Engine's reason: bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn -> score 1.2 · ceiling 124 · BENCH STAGED: 10 within 2: scarcer first (50% vs 75% for Makai Lemon)
- Top projection available: Jaxson Dart -> took it: False.
- Passed on: Makai Lemon (WR, s=0.755, e=-19.2); Courtland Sutton (WR, s=0.76, e=-19.2); Jordan Addison (WR, s=0.765, e=-19.2).
- Plan call 418 @pick 102: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 101 drafted / 10 mine.
- Engine's first choice was **Michael Wilson** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Wilson | WR | -30.2 | 0.50 | 0.65 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Bost |
| Makai Lemon | WR | -31.6 | 0.76 | 0.83 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.3/wk over the wire (Denzel Bost |
| Courtland Sutton | WR | -18.2 | 0.76 | 0.84 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +1.1/wk over the wire (Denzel Bost |
| Jordan Addison | WR | -33.5 | 0.77 | 0.84 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.2/wk over the wire (Denzel Bost |
| Alec Pierce | WR | -20.6 | 0.77 | 0.85 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.9/wk over the wire (Denzel Bost |
| Michael Pittman Jr. | WR | -27.6 | 0.79 | 0.87 | -19.2 | -18.2 | bench insurance: covers 2 WR starters ~6.5 wks/season · +0.5/wk over the wire (Denzel Bost |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | 3.0 | 1.8 | 1.2 | 16 |
| RB | -41.5 | -41.7 | 0.2 | 25 |
| WR | -18.2 | -19.2 | 1.0 | 34 |
| TE | 6.7 | 5.4 | 1.3 | 18 |
| K | 12.0 | 9.4 | 2.6 | 20 |
| DEF | 10.0 | 8.5 | 1.5 | 7 |

### Pick 119 (round 12): Michael Pittman Jr. (WR)

- In plain English: Lineup already full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) for about 0.8 weeks a season at +0.5 points a week over the waiver wire (Denzel Boston), worth about 0 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 374 ms, ranker engine, plan call 452, plan age 891 ms, at 19:51:42 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timing: 96% he is still there next turn -> score 0.0 · ceiling 130 · BENCH STAGED: zero insurance everywhere: ceiling over the wire (22, role flag)
- Top projection available: Jared Goff -> took it: False.
- Passed on: Matthew Golden (WR, s=0.955, e=-27.7); KC Concepcion (WR, s=0.964, e=-27.7); Jordan Addison (WR, s=0.979, e=-27.7).
- Plan call 452 @pick 119: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 118 drafted / 11 mine.
- Engine's first choice was **Michael Pittman Jr.** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Michael Pittman Jr. | WR | -27.6 | 0.95 | 0.98 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5 |
| Matthew Golden | WR | -36.9 | 0.95 | 0.98 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.0 |
| KC Concepcion | WR | -29.1 | 0.96 | 0.99 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.4 |
| Jordan Addison | WR | -33.5 | 0.98 | 0.99 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.2 |
| Xavier Worthy | WR | -36.7 | 0.95 | 0.98 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.0 |
| Wan'Dale Robinson | WR | -34.5 | 0.95 | 0.98 | -27.7 | -27.6 | bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.1 |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -15.1 | -15.2 | 0.1 | 13 |
| RB | -41.5 | -41.7 | 0.2 | 22 |
| WR | -27.6 | -27.7 | 0.1 | 29 |
| TE | -3.9 | -3.9 | 0.0 | 15 |
| K | 12.0 | 11.9 | 0.1 | 18 |
| DEF | 10.0 | 9.3 | 0.7 | 7 |

### Pick 122 (round 13): Matthew Golden (WR)

- In plain English: Lineup already full, so Matthew Golden (WR) is insurance: covers 2 WR starter(s) for about 0.0 weeks a season at +0.0 points a week over the waiver wire (Denzel Boston), worth about 0 points. The top raw projection available was Jared Goff; the engine passed on him on purpose.
- Driver: via **action**, verified store, 413 ms, ranker engine, plan call 461, plan age 973 ms, at 19:53:16 PT.
- Engine's reason: bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 125 · BENCH STAGED: zero insurance everywhere: ceiling over the wire (17, role flag)
- Top projection available: Jared Goff -> took it: False.
- Passed on: KC Concepcion (WR, s=0.826, e=-29.6); Jordan Addison (WR, s=0.831, e=-29.6); Xavier Worthy (WR, s=0.825, e=-29.6).
- Plan call 461 @pick 122: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 9], state store with 121 drafted / 12 mine.
- Engine's first choice was **Matthew Golden** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Matthew Golden | WR | -36.9 | 0.83 | 0.91 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| KC Concepcion | WR | -29.1 | 0.83 | 0.91 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Jordan Addison | WR | -33.5 | 0.83 | 0.91 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Xavier Worthy | WR | -36.7 | 0.82 | 0.91 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Wan'Dale Robinson | WR | -34.5 | 0.84 | 0.92 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |
| Jakobi Meyers | WR | -33.8 | 0.82 | 0.90 | -29.6 | -29.1 | bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0. |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -15.1 | -15.7 | 0.6 | 13 |
| RB | -41.5 | -42.2 | 0.7 | 21 |
| WR | -29.1 | -29.6 | 0.5 | 28 |
| TE | -3.9 | -4.1 | 0.2 | 15 |
| K | 12.0 | 7.6 | 4.4 | 18 |
| DEF | 6.0 | 4.0 | 2.0 | 6 |

### Pick 139 (round 14): Steelers (DEF)

- In plain English: Took Pittsburgh Steelers (DEF): nothing on the board was urgent, so the engine took the most valuable player who fills an open slot (92% to survive, but nobody better was worth waiting for). The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 387 ms, ranker engine, plan call 485, plan age 887 ms, at 19:58:04 PT.
- Engine's reason: safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected at your next turn · RANKED ON 6.7 = 4.0 his own edge over the DEF you'd otherwise end up with + 2.7 the WR this frees up next turn · STAGED (flat: top urgency 0.2 under 8): pair band of 3, then pair order stands (all stay regardless (92%, 94%))
- Top projection available: Kyler Murray -> took it: False.
- Passed on: New England Patriots (DEF, s=0.937, e=5.8); Tyler Loop (K, s=0.937, e=4.4); Evan McPherson (K, s=0.834, e=4.4).
- Plan call 485 @pick 139: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 1, 'BN': 6}, away seats [4, 6, 7, 9], state store with 138 drafted / 13 mine.
- Engine's first choice was **Pittsburgh Steelers** -> NOT taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Pittsburgh Steelers | DEF | 6.0 | 0.92 | 0.97 | 5.8 | 6.0 | safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF  |
| New England Patriots | DEF | 4.0 | 0.94 | 0.98 | 5.8 | 6.0 | safe to wait on DEF · 94% chance he's still there at your next pick · fills your open DEF  |
| Tyler Loop | K | 4.5 | 0.94 | 0.98 | 4.4 | 4.5 | safe to wait on K · 94% chance he's still there at your next pick · fills your open K slot |
| Evan McPherson | K | 3.0 | 0.83 | 0.91 | 4.4 | 4.5 | safe to wait on K · 83% chance he's still there at your next pick · fills your open K slot |
| Cairo Santos | K | 1.5 | 0.86 | 0.94 | 4.4 | 4.5 | safe to wait on K · 86% chance he's still there at your next pick · fills your open K slot |
| Jacksonville Jaguars | DEF | 2.0 | 0.87 | 0.95 | 5.8 | 6.0 | safe to wait on DEF · 87% chance he's still there at your next pick · fills your open DEF  |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|
| QB | -16.4 | -17.0 | 0.6 | 12 |
| RB | -44.1 | -45.1 | 1.0 | 18 |
| WR | -31.6 | -31.7 | 0.1 | 22 |
| TE | -8.7 | -8.9 | 0.2 | 13 |
| K | 4.5 | 4.4 | 0.1 | 14 |
| DEF | 6.0 | 5.8 | 0.2 | 5 |

### Pick 142 (round 15): Tyler Loop (K)

- In plain English: Took Tyler Loop (K) to fill a mandatory slot; nothing the engine named was left. The top raw projection available was Kyler Murray; the engine passed on him on purpose.
- Driver: via **action**, verified store, 254 ms, ranker engine, plan call 489, plan age 753 ms, at 19:58:36 PT.
- Engine's reason: fills your open K slot
- Top projection available: Kyler Murray -> took it: False.
- Passed on: Evan McPherson (K, s=None, e=None); Cairo Santos (K, s=None, e=None); Jake Bates (K, s=None, e=None).
- Plan call 489 @pick 142: needs {'QB': 0, 'RB': 0, 'WR': 0, 'TE': 0, 'FLEX': 0, 'K': 1, 'DEF': 0, 'BN': 6}, away seats [4, 6, 7, 9], state store with 141 drafted / 14 mine.
- Engine's first choice was **Tyler Loop** -> taken.

| plan row | pos | vorp | s | sr | e_best_next | best_now | why |
|---|---|---|---|---|---|---|---|
| Tyler Loop | K | 4.5 | - | - | - | - | fills your open K slot |
| Evan McPherson | K | 3.0 | - | - | - | - | fills your open K slot |
| Cairo Santos | K | 1.5 | - | - | - | - | fills your open K slot |
| Jake Bates | K | 0.0 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |
| Andy Borregales | K | -1.5 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |
| Chase McLaughlin | K | -3.0 | - | - | - | - | depth fallback (no engine opinion this deep; board order, guardrails applied) |

| market | best_now | e_best_next | urgency | pool |
|---|---|---|---|---|

## Survival scorecard (shown survival vs what happened by my next pick)

| bucket | n | mean shown | observed survived |
|---|---|---|---|
| 0-30% | 168 | 17% | 2% |
| 30-50% | 98 | 39% | 41% |
| 50-70% | 103 | 61% | 70% |
| 70-90% | 362 | 81% | 89% |
| 90-100% | 129 | 95% | 96% |

860 predictions over 123 windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.

## Narration (what the panel showed live, Pacific time)

    19:36:14  plan #374 for pick 86
  • DK Metcalf WR · insurance worth ~8 · 21% survives to our turn
  • Alec Pierce WR · insurance worth ~6 · 55% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 70% survives to our turn
    19:36:15  driver started — seat 2, 10 teams, 15 rounds
    19:36:15  pick 86  Justin Herbert (QB) (seat 6) in 3 s
    19:36:16  plan #375 for pick 87
  • DK Metcalf WR · insurance worth ~8 · 11% survives to our turn
  • Alec Pierce WR · insurance worth ~6 · 60% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 69% survives to our turn
    19:37:15  heartbeat sent (Yahoo told we are not idle)
    19:37:26  pick 87  Tony Pollard (RB) (seat 7) in 70 s
    19:37:29  plan #381 for pick 88
  • DK Metcalf WR · insurance worth ~8 · 13% survives to our turn
  • Alec Pierce WR · insurance worth ~6 · 58% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 73% survives to our turn
    19:38:03  pick 88  Texans (DEF) (seat 8) in 37 s
    19:38:07  plan #384 for pick 89
  • DK Metcalf WR · insurance worth ~8 · 27% survives to our turn
  • Alec Pierce WR · insurance worth ~6 · 65% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 73% survives to our turn
    19:38:16  heartbeat sent (Yahoo told we are not idle)
    19:39:16  heartbeat sent (Yahoo told we are not idle)
    19:39:18  pick 89  DK Metcalf (WR) (seat 9) in 75 s — a target is gone (was 27% to survive)
    19:39:21  pick 90  Jordan Mason (RB) (seat 10) in 3 s
    19:39:24  plan #390 for pick 91
  • Jonathon Brooks RB · insurance worth ~1 · 27% survives to our turn
  • Chris Godwin Jr. WR · insurance worth ~2 · 67% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 74% survives to our tu
    19:39:51  pick 91  Jayden Reed (WR) (seat 10) in 30 s
    19:40:01  plan #393 for pick 92
  • Jonathon Brooks RB · insurance worth ~1 · 38% survives to our turn
  • Chris Godwin Jr. WR · insurance worth ~2 · 69% survives to our turn
  • Alec Pierce WR · insurance worth ~6 · 71% survives to our tur
    19:40:16  heartbeat sent (Yahoo told we are not idle)
    19:41:07  pick 92  Jonathon Brooks (RB) (seat 9) in 75 s — a target is gone (was 38% to survive)
    19:41:15  plan #399 for pick 93
  • Chris Godwin Jr. WR · insurance worth ~2 · 33% survives to our turn
  • Chuba Hubbard RB · insurance worth ~1 · 74% survives to our turn
  • Michael Wilson WR · insurance worth ~2 · 78% survives to our tu
    19:41:18  heartbeat sent (Yahoo told we are not idle)
    19:41:30  pick 93  Chuba Hubbard (RB) (seat 8) in 23 s — a target is gone (was 74% to survive)
    19:41:39  plan #401 for pick 94
  • Chris Godwin Jr. WR · insurance worth ~2 · 34% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 77% survives to our turn
  • Michael Wilson WR · insurance worth ~2 · 79% survives to our tur
    19:42:12  pick 94  Seahawks (DEF) (seat 7) in 42 s
    19:42:16  plan #404 for pick 95
  • Chris Godwin Jr. WR · insurance worth ~2 · 34% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 81% survives to our turn
  • RJ Harvey RB · insurance worth ~1 · 82% survives to our turn
    19:42:16  pick 95  Quentin Johnston (WR) (seat 6) in 4 s
    19:42:18  heartbeat sent (Yahoo told we are not idle)
    19:42:28  plan #405 for pick 96
  • Chris Godwin Jr. WR · insurance worth ~2 · 37% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 82% survives to our turn
  • Michael Wilson WR · insurance worth ~2 · 84% survives to our tur
    19:43:21  heartbeat sent (Yahoo told we are not idle)
    19:43:22  pick 96  Broncos (DEF) (seat 5) in 66 s
    19:43:31  plan #410 for pick 97
  • Chris Godwin Jr. WR · insurance worth ~2 · 40% survives to our turn
  • J.K. Dobbins RB · insurance worth ~1 · 87% survives to our turn
  • Michael Wilson WR · insurance worth ~2 · 87% survives to our tur
    19:43:34  pick 97  Chris Godwin Jr. (WR) (seat 4) in 13 s — a target is gone (was 40% to survive)
    19:43:39  pick 98  Brandon Aubrey (K) (seat 3) in 5 s
    19:43:39  plan #411 for pick 99
  • J.K. Dobbins RB · insurance worth ~1 · 92% survives to our turn
  • RJ Harvey RB · insurance worth ~1 · 93% survives to our turn
  • Rachaad White RB · insurance worth ~0 · 98% survives to our turn
    19:43:39  ON THE CLOCK, pick 99 · plan #411 (0.0 s old) · lineup needs K DEF
    19:43:40  PICKED J.K. Dobbins (RB) via action, confirmed in 361 ms — lineup full, so J.K. Dobbins (RB) is insurance: covers 3 RB starter(s) about 0.2 weeks a season at +2.9 a week over the wire, about 1 points
  • top projection left was Ja
    19:43:43  plan #412 for pick 100
  • Alec Pierce WR · insurance worth ~6 · 87% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 87% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~3 · 94% survives to ou
    19:44:21  heartbeat sent (Yahoo told we are not idle)
    19:44:22  pick 100  Cam Little (K) (seat 1) in 42 s
    19:44:31  plan #416 for pick 101
  • Alec Pierce WR · insurance worth ~6 · 95% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 96% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~3 · 94% survives to ou
    19:44:47  pick 101  De'Zhaun Stribling (WR) (seat 1) in 25 s — a target is gone (was 95% to survive)
    19:44:48  plan #418 for pick 102
  • Michael Wilson WR · insurance worth ~2 · 50% survives to our turn
  • Makai Lemon WR · insurance worth ~2 · 76% survives to our turn
  • Courtland Sutton WR · insurance worth ~7 · 76% survives to our tur
    19:44:48  ON THE CLOCK, pick 102 · plan #418 (0.0 s old) · lineup needs K DEF
    19:44:49  PICKED Michael Wilson (WR) via action, confirmed in 470 ms — lineup full, so Michael Wilson (WR) is insurance: covers 2 WR starter(s) about 6.5 weeks a season at +0.4 a week over the wire, about 2 points
  • top projection left wa
    19:44:53  plan #419 for pick 103
  • Alec Pierce WR · insurance worth ~1 · 74% survives to our turn
  • Courtland Sutton WR · insurance worth ~1 · 75% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 76% survives to ou
    19:45:10  pick 103  Alec Pierce (WR) (seat 3) in 21 s — a target is gone (was 74% to survive)
    19:45:18  plan #421 for pick 104
  • Courtland Sutton WR · insurance worth ~1 · 74% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 79% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 80% survives to 
    19:45:20  pick 104  Bo Nix (QB) (seat 4) in 10 s
    19:45:21  heartbeat sent (Yahoo told we are not idle)
    19:45:30  plan #422 for pick 105
  • Courtland Sutton WR · insurance worth ~1 · 79% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 80% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 81% survives to 
    19:46:07  pick 105  Patrick Mahomes (QB) (seat 5) in 47 s
    19:46:10  pick 106  Stefon Diggs (WR) (seat 6) in 3 s
    19:46:20  plan #426 for pick 107
  • Courtland Sutton WR · insurance worth ~1 · 82% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 82% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 84% survives to 
    19:46:22  heartbeat sent (Yahoo told we are not idle)
    19:47:17  pick 107  Josh Downs (WR) (seat 7) in 67 s
    19:47:23  plan #431 for pick 108
  • Courtland Sutton WR · insurance worth ~1 · 82% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 83% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 82% survives to 
    19:47:26  heartbeat sent (Yahoo told we are not idle)
    19:47:28  pick 108  Kyle Monangai (RB) (seat 8) in 11 s
    19:47:36  plan #432 for pick 109
  • Courtland Sutton WR · insurance worth ~1 · 85% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 84% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 85% survives to 
    19:48:29  heartbeat sent (Yahoo told we are not idle)
    19:48:42  pick 109  Dalton Kincaid (TE) (seat 9) in 74 s
    19:48:48  pick 110  Harrison Mevis (K) (seat 10) in 5 s
    19:48:51  plan #438 for pick 111
  • Courtland Sutton WR · insurance worth ~1 · 88% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 87% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 87% survives to 
    19:49:01  pick 111  Vikings (DEF) (seat 10) in 13 s
    19:49:03  plan #439 for pick 112
  • Courtland Sutton WR · insurance worth ~1 · 91% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 90% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 87% survives to 
    19:49:30  heartbeat sent (Yahoo told we are not idle)
    19:50:15  pick 112  Jaxson Dart (QB) (seat 9) in 75 s
    19:50:16  plan #445 for pick 113
  • Courtland Sutton WR · insurance worth ~1 · 90% survives to our turn
  • Michael Pittman Jr. WR · insurance worth ~0 · 88% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 92% survives to 
    19:50:31  heartbeat sent (Yahoo told we are not idle)
    19:50:34  pick 113  Courtland Sutton (WR) (seat 8) in 19 s — a target is gone (was 90% to survive)
    19:50:40  plan #447 for pick 114
  • Michael Pittman Jr. WR · insurance worth ~0 · 92% survives to our turn
  • Matthew Golden WR · insurance worth ~0 · 91% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 92% survives to ou
    19:50:55  pick 114  Dallas Goedert (TE) (seat 7) in 21 s
    19:50:57  pick 115  Jacory Croskey-Merritt (RB) (seat 6) in 2 s INSTANTLY (autopick)
    19:51:05  plan #449 for pick 116
  • Michael Pittman Jr. WR · insurance worth ~0 · 94% survives to our turn
  • Matthew Golden WR · insurance worth ~0 · 95% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 96% survives to ou
    19:51:18  pick 116  Jason Myers (K) (seat 5) in 21 s
    19:51:18  plan #450 for pick 117
  • Michael Pittman Jr. WR · insurance worth ~0 · 98% survives to our turn
  • Matthew Golden WR · insurance worth ~0 · 96% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 97% survives to ou
    19:51:28  pick 117  Isaiah Likely (TE) (seat 4) in 10 s
    19:51:31  plan #451 for pick 118
  • Michael Pittman Jr. WR · insurance worth ~0 · 98% survives to our turn
  • Matthew Golden WR · insurance worth ~0 · 96% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 97% survives to ou
    19:51:33  heartbeat sent (Yahoo told we are not idle)
    19:51:41  pick 118  RJ Harvey (RB) (seat 3) in 13 s
    19:51:41  plan #452 for pick 119
  • Michael Pittman Jr. WR · insurance worth ~0 · 96% survives to our turn
  • Matthew Golden WR · insurance worth ~0 · 96% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 96% survives to ou
    19:51:41  ON THE CLOCK, pick 119 · plan #452 (0.0 s old) · lineup needs K DEF
    19:51:42  PICKED Michael Pittman Jr. (WR) via action, confirmed in 374 ms — lineup full, so Michael Pittman Jr. (WR) is insurance: covers 2 WR starter(s) about 0.8 weeks a season at +0.5 a week over the wire, about 0 points
  • top projecti
    19:51:45  plan #453 for pick 120
  • Matthew Golden WR · insurance worth ~0 · 95% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 95% survives to our turn
  • Jordan Addison WR · insurance worth ~0 · 96% survives to our tur
    19:52:34  heartbeat sent (Yahoo told we are not idle)
    19:52:47  pick 120  Eagles (DEF) (seat 1) in 65 s
    19:52:57  plan #459 for pick 121
  • Matthew Golden WR · insurance worth ~0 · 97% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 96% survives to our turn
  • Jordan Addison WR · insurance worth ~0 · 98% survives to our tur
    19:53:14  pick 121  Woody Marks (RB) (seat 1) in 27 s
    19:53:15  plan #461 for pick 122
  • Matthew Golden WR · insurance worth ~0 · 83% survives to our turn
  • KC Concepcion WR · insurance worth ~0 · 83% survives to our turn
  • Jordan Addison WR · insurance worth ~0 · 83% survives to our tur
    19:53:15  ON THE CLOCK, pick 122 · plan #461 (0.0 s old) · lineup needs K DEF
    19:53:16  PICKED Matthew Golden (WR) via action, confirmed in 413 ms — lineup full, so Matthew Golden (WR) is insurance: covers 2 WR starter(s) about 0.0 weeks a season at +0.0 a week over the wire, about 0 points
  • top projection left wa
    19:53:20  plan #462 for pick 123
  • Ka'imi Fairbairn K · wait costs 4 · pick costs 0, best pair 10 (6 now + ~4 WR next) · 15% survives to our turn
  • Cameron Dicker K · wait costs 4 · pick costs 1.5 · 35% survives to our turn
  • Pittsbur
    19:53:35  heartbeat sent (Yahoo told we are not idle)
    19:53:46  pick 123  Mark Andrews (TE) (seat 3) in 29 s
    19:53:56  pick 124  Jordan Addison (WR) (seat 4) in 11 s
    19:53:58  plan #465 for pick 125
  • Ka'imi Fairbairn K · wait costs 4 · pick costs 0, best pair 10 (6 now + ~4 WR next) · 16% survives to our turn
  • Cameron Dicker K · wait costs 4 · pick costs 1.5 · 34% survives to our turn
  • Pittsbur
    19:54:13  pick 125  Jordyn Tyson (WR) (seat 5) in 16 s
    19:54:20  pick 126  Josh Jacobs (RB) (seat 6) in 7 s
    19:54:22  plan #467 for pick 127
  • Ka'imi Fairbairn K · wait costs 4 · pick costs 0, best pair 10 (6 now + ~4 WR next) · 16% survives to our turn
  • Cameron Dicker K · wait costs 4 · pick costs 1.5 · 37% survives to our turn
  • Pittsbur
    19:54:37  heartbeat sent (Yahoo told we are not idle)
    19:54:51  pick 127  Jared Goff (QB) (seat 7) in 31 s
    19:54:58  plan #470 for pick 128
  • Ka'imi Fairbairn K · wait costs 4 · pick costs 0, best pair 10 (6 now + ~4 WR next) · 16% survives to our turn
  • Cameron Dicker K · wait costs 4 · pick costs 1.5 · 41% survives to our turn
  • Pittsbur
    19:55:09  pick 128  Ka'imi Fairbairn (K) (seat 8) in 18 s — a target is gone (was 16% to survive)
    19:55:11  plan #471 for pick 129
  • Cameron Dicker K · wait costs 4 · pick costs 0, best pair 8.5 (4.5 now + ~4 WR next) · 17% survives to our turn
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0.5 · 69% survives to our turn
  • 
    19:55:39  heartbeat sent (Yahoo told we are not idle)
    19:56:24  pick 129  KC Concepcion (WR) (seat 9) in 75 s
    19:56:26  pick 130  Romeo Doubs (WR) (seat 10) in 2 s INSTANTLY (autopick)
    19:56:27  plan #477 for pick 131
  • Cameron Dicker K · wait costs 4 · pick costs 0, best pair 8 (4.5 now + ~3.5 DEF next) · 18% survives to our turn
  • Pittsburgh Steelers DEF · safe to wait · pick costs 1.4 · 78% survives to our turn
  •
    19:56:31  pick 131  Kenny Gainwell (RB) (seat 10) in 4 s
    19:56:39  plan #478 for pick 132
  • Cameron Dicker K · wait costs 4 · pick costs 0, best pair 8 (4.5 now + ~3.5 DEF next) · 18% survives to our turn
  • Pittsburgh Steelers DEF · safe to wait · pick costs 1.4 · 79% survives to our turn
  •
    19:56:42  pick 132  Cameron Dicker (K) (seat 9) in 12 s — a target is gone (was 18% to survive)
    19:56:42  heartbeat sent (Yahoo told we are not idle)
    19:56:52  plan #479 for pick 133
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.6 (4 now + ~2.6 WR next) · 82% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 83% survives to our tur
    19:56:56  pick 133  Jake Ferguson (TE) (seat 8) in 14 s
    19:57:05  plan #480 for pick 134
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.7 (4 now + ~2.7 WR next) · 81% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 85% survives to our tur
    19:57:27  pick 134  Will Reichard (K) (seat 7) in 31 s
    19:57:29  plan #482 for pick 135
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.7 (4 now + ~2.7 WR next) · 83% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 86% survives to our tur
    19:57:34  pick 135  Eddy Pineiro (K) (seat 6) in 7 s — a target is gone (was 80% to survive)
    19:57:42  plan #483 for pick 136
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.7 (4 now + ~2.7 WR next) · 87% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 88% survives to our tur
    19:57:46  heartbeat sent (Yahoo told we are not idle)
    19:57:50  pick 136  Jalen Coker (WR) (seat 5) in 16 s
    19:57:54  plan #484 for pick 137
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.7 (4 now + ~2.7 WR next) · 88% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 88% survives to our tur
    19:58:01  pick 137  Ravens (DEF) (seat 4) in 10 s
    19:58:03  pick 138  Aaron Jones Sr. (RB) (seat 3) in 2 s INSTANTLY (autopick)
    19:58:03  plan #485 for pick 139
  • Pittsburgh Steelers DEF · safe to wait · pick costs 0, best pair 6.7 (4 now + ~2.7 WR next) · 92% survives to our turn
  • New England Patriots DEF · safe to wait · pick costs 2 · 94% survives to our tur
    19:58:03  ON THE CLOCK, pick 139 · plan #485 (0.0 s old) · lineup needs K DEF
    19:58:04  PICKED Pittsburgh Steelers (DEF) via action, confirmed in 387 ms — chose Pittsburgh Steelers (DEF): nothing urgent, the most valuable player who fills a slot (92% to survive, nobody better worth waiting for)
  • pair math: 4 now +
    19:58:06  plan #486 for pick 140
  • Tyler Loop K · safe to wait · pick costs 0, best pair 4.2 (1.5 now + ~2.7 WR next) · 96% survives to our turn
  • Evan McPherson K · safe to wait · pick costs 1.5 · 85% survives to our turn
  • Cairo San
    19:58:14  pick 140  Makai Lemon (WR) (seat 1) in 10 s
    19:58:18  plan #487 for pick 141
  • Tyler Loop K · safe to wait · pick costs 0, best pair 2.9 (1.5 now + ~1.4 WR next) · 99% survives to our turn
  • Evan McPherson K · safe to wait · pick costs 1.5 · 90% survives to our turn
  • Cairo San
    19:58:35  pick 141  Hunter Henry (TE) (seat 1) in 22 s
    19:58:35  plan #489 for pick 142
  • Tyler Loop K
  • Evan McPherson K
  • Cairo Santos K
    19:58:35  ON THE CLOCK, pick 142 · plan #489 (0.0 s old) · lineup needs K
    19:58:36  PICKED Tyler Loop (K) via action, confirmed in 254 ms — chose Tyler Loop (K) to fill a mandatory slot. Nothing the engine named was left
  • top projection left was Kyler Murray, passed on purpose
    19:58:38  roster full — driver done; posting the trail when the room finishes

## Driver log (the lines that matter, Pacific time)

    19:36:15 PT preflight: ok=true pick_path=action my_team=3 plan=plan 25 deep @pick 86 via store call#374
    19:36:15 PT driver start — sleep via worker
    19:36:15 PT NARR info driver started — seat 2, 10 teams, 15 rounds
    19:37:15 PT heartbeat: setAwayStatus(false)
    19:37:15 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:38:16 PT heartbeat: setAwayStatus(false)
    19:38:16 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:39:16 PT heartbeat: setAwayStatus(false)
    19:39:16 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:40:16 PT heartbeat: setAwayStatus(false)
    19:40:16 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:41:18 PT heartbeat: setAwayStatus(false)
    19:41:18 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:42:18 PT heartbeat: setAwayStatus(false)
    19:42:18 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:43:21 PT heartbeat: setAwayStatus(false)
    19:43:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:43:40 PT ON CLOCK -> {"drafted":"J.K. Dobbins","pos":"RB","vorp":-23.9,"proj":134.2,"why":"bench insurance: covers 3 RB starters behind 2 reserves already held ~0.2 wks/season · +2.9/wk over the wire (Chris Rodriguez Jr.) ≈ 1 pts · timin
    19:44:21 PT heartbeat: setAwayStatus(false)
    19:44:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:44:49 PT ON CLOCK -> {"drafted":"Michael Wilson","pos":"WR","vorp":-30.2,"proj":113.7,"why":"bench insurance: covers 2 WR starters ~6.5 wks/season · +0.4/wk over the wire (Denzel Boston) ≈ 2 pts · timing: 50% he is still there next turn 
    19:45:21 PT heartbeat: setAwayStatus(false)
    19:45:21 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:46:22 PT heartbeat: setAwayStatus(false)
    19:46:22 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:47:26 PT heartbeat: setAwayStatus(false)
    19:47:26 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:48:29 PT heartbeat: setAwayStatus(false)
    19:48:29 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:49:30 PT heartbeat: setAwayStatus(false)
    19:49:30 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:50:31 PT heartbeat: setAwayStatus(false)
    19:50:31 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:51:33 PT heartbeat: setAwayStatus(false)
    19:51:33 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:51:42 PT ON CLOCK -> {"drafted":"Michael Pittman Jr.","pos":"WR","vorp":-27.6,"proj":116.3,"why":"bench insurance: covers 2 WR starters behind 1 reserve already held ~0.8 wks/season · +0.5/wk over the wire (Denzel Boston) ≈ 0 pts · timin
    19:52:34 PT heartbeat: setAwayStatus(false)
    19:52:34 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:53:16 PT ON CLOCK -> {"drafted":"Matthew Golden","pos":"WR","vorp":-36.9,"proj":106.9,"why":"bench insurance: covers 2 WR starters behind 2 reserves already held ~0.0 wks/season · +0.0/wk over the wire (Denzel Boston) ≈ 0 pts · ceiling 1
    19:53:35 PT heartbeat: setAwayStatus(false)
    19:53:35 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:54:37 PT heartbeat: setAwayStatus(false)
    19:54:37 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:55:39 PT heartbeat: setAwayStatus(false)
    19:55:39 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:56:42 PT heartbeat: setAwayStatus(false)
    19:56:42 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:57:46 PT heartbeat: setAwayStatus(false)
    19:57:46 PT NARR heartbeat heartbeat sent (Yahoo told we are not idle)
    19:58:04 PT ON CLOCK -> {"drafted":"Pittsburgh Steelers","pos":"DEF","vorp":6,"proj":123,"why":"safe to wait on DEF · 92% chance he's still there at your next pick · fills your open DEF slot · two-pick plan: pair with the ~3-pt WR expected 
    19:58:36 PT ON CLOCK -> {"drafted":"Tyler Loop","pos":"K","vorp":4.5,"proj":141,"why":"fills your open K slot","pair":null,"s":null,"sr":null,"e":null,"top_proj_available":{"n":"Kyler Murray","p":"QB","proj":250.6,"vorp":-16.4},"took_top_pr
    19:58:38 PT roster full
    19:58:38 PT NARR info roster full — driver done; posting the trail when the room finishes
    19:58:38 PT driver stop


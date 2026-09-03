# Rival picks -- the pick-level dataset behind the autopick refit (DECISIONS #35)

945 rival picks over 7 rooms; our own picks excluded. Rows: C:\Users\gabje\Desktop\fantasy-football\data\processed\rival_picks.csv

Rooms:
- 10502459: 150 picks, NO sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10503516: 150 picks, NO sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10504572: 150 picks, NO sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10505450: 150 picks, NO sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10531886: 150 picks, sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10532940: 150 picks, sidecar, snapshot newest-on-disk:mock_players_10534350.json, timing labels 0
- 10534350: 150 picks, sidecar, snapshot own:mock_players_10534350.json, timing labels 0

## Rank of the taken player among the players still available

Lower is tighter. `top1` = share taken exactly the best available; `>10` = share taken someone ranked below tenth. `fit` = pool restricted to positions that fit an open starter slot (starters-first). Rooms: 10502459, 10503516, 10504572, 10505450, 10531886, 10532940, 10534350.

| seat class | n | by Yahoo rank: median | top1 | top3 | >10 | fit: top1 | top3 | by board ADP: median | top1 | top3 | >10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| away | 102 | 6 | 0.38 | 0.42 | 0.32 | 0.80 | 0.84 | 9 | 0.08 | 0.24 | 0.39 |
| human | 303 | 4 | 0.22 | 0.44 | 0.28 | 0.40 | 0.68 | 6 | 0.12 | 0.30 | 0.34 |
| unknown | 540 | 5 | 0.31 | 0.44 | 0.29 | 0.52 | 0.70 | 7 | 0.10 | 0.28 | 0.34 |

### Histograms (rank by Yahoo rank, 1..9 then 10+)

| seat class | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10+ |
|---|---|---|---|---|---|---|---|---|---|---|
| away | 39 | 2 | 2 | 3 | 4 | 5 | 3 | 1 | 6 | 37 |
| human | 67 | 36 | 30 | 20 | 22 | 10 | 14 | 8 | 6 | 90 |
| unknown | 165 | 43 | 29 | 27 | 28 | 23 | 25 | 17 | 16 | 167 |

### By draft stage (rank by Yahoo rank)

| seat class | stage | n | median | top1 | top3 |
|---|---|---|---|---|---|
| away | early (pick<=60) | 17 | 1 | 0.53 | 0.65 |
| away | late (pick>60) | 85 | 7 | 0.35 | 0.38 |
| human | early (pick<=60) | 145 | 2 | 0.34 | 0.61 |
| human | late (pick>60) | 158 | 8 | 0.11 | 0.28 |
| unknown | early (pick<=60) | 216 | 2 | 0.40 | 0.62 |
| unknown | late (pick>60) | 324 | 8 | 0.24 | 0.32 |

### Need-rule check (pre-declared, DECISIONS #35)

instant/away picks, share exactly #1 by Yahoo rank: all positions 0.38 -> starters-first filter 0.80. The filter RAISES the exact-hit share: the list walked is consistent with o_rank plus a starters-first rule; the one-hot list component stands.

### ADP drift

62 of 945 rival picks are unscoreable for the ADP-Gaussian likelihood (board ADP vs Yahoo's ADP at the snapshot moved > 10 picks); they stay in the Yahoo-rank likelihood.


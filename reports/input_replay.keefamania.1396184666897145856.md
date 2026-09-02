# Input replay — keefamania, draft 1396184666897145856

Old board `data/processed/tiers.model.keefamania.csv` vs new board `data/processed/tiers.external.keefamania.csv`; 10 teams, 15 rounds; rivals held to the archived picks, our picks by the engine at every slot.

## The two boards

| pos | n both | Spearman proj_pts | left the board | joined |
|---|---|---|---|---|
| QB | 27 | 0.846 | 5 | 1 |
| RB | 54 | 0.934 | 1 | 3 |
| WR | 73 | 0.968 | 4 | 0 |
| TE | 27 | 0.894 | 1 | 1 |

Zeroed on the new board (non-starter rule or availability), had points before (9): Kenyon Sadiq, Terrance Ferguson, David Njoku, Isiah Pacheco, Jonah Coleman, Alvin Kamara, Ollie Gordon II, James Conner, Fernando Mendoza

## Lineup points by slot

| slot | old roster, new ruler | new roster, new ruler | Δ | old roster, old ruler | new roster, old ruler | Δ |
|---|---|---|---|---|---|---|
| 1 | 1927 | 2013 | +86 | 1878 | 1879 | +0 |
| 2 | 1962 | 1891 | -72 | 1861 | 1729 | -133 |
| 3 | 1905 | 1946 | +41 | 1880 | 1841 | -38 |
| 4 | 1895 | 1935 | +39 | 1857 | 1829 | -28 |
| 5 | 1889 | 1911 | +22 | 1827 | 1824 | -3 |
| 6 | 1899 | 1901 | +2 | 1877 | 1877 | +0 |
| 7 | 1876 | 1927 | +50 | 1818 | 1829 | +11 |
| 8 | 1840 | 1889 | +49 | 1809 | 1805 | -3 |
| 9 | 1834 | 1841 | +7 | 1764 | 1712 | -52 |
| 10 | 1823 | 1838 | +14 | 1718 | 1716 | -2 |

Mean Δ on the new ruler +23.9 (slots better/worse 9/1); on the old ruler -24.8 (2/7).

## Picks that changed

99 of 150 picks changed. By round: R1: 4, R2: 7, R3: 6, R4: 3, R5: 9, R6: 9, R7: 10, R8: 8, R9: 7, R10: 10, R11: 10, R12: 7, R13: 9.

Rounds 1-6: 38 changes (63% of those picks); rounds 7+: 61.

By tier of the player the old board took (changed / picks at that tier): T1: 22/50 (44%), T2: 2/4 (50%), T3: 12/13 (92%), T4: 25/40 (62%), T5: 5/6 (83%), T6: 9/11 (82%), T7: 24/26 (92%).

Ten largest changes (projected points, new ruler, new pick minus old pick):

| slot | round | old pick | new pick | Δ |
|---|---|---|---|---|
| 5 | 10 | Mike Washington Jr. (RB) | Trevor Lawrence (QB) | +202 |
| 8 | 6 | George Kittle (TE) | Jayden Daniels (QB) | +161 |
| 9 | 6 | George Kittle (TE) | Jayden Daniels (QB) | +161 |
| 10 | 6 | George Kittle (TE) | Jayden Daniels (QB) | +161 |
| 2 | 10 | Wan'Dale Robinson (WR) | Trevor Lawrence (QB) | +157 |
| 5 | 6 | Tyler Warren (TE) | Jayden Daniels (QB) | +153 |
| 1 | 11 | Trevor Lawrence (QB) | Kenny Gainwell (RB) | -150 |
| 10 | 10 | Kenny Gainwell (RB) | Trevor Lawrence (QB) | +150 |
| 3 | 10 | Courtland Sutton (WR) | Lamar Jackson (QB) | +150 |
| 6 | 10 | Mike Evans (WR) | Jalen Hurts (QB) | +148 |

Round 1-6 changes:

- slot 1 R1: Christian McCaffrey (RB) -> Jahmyr Gibbs (RB)
- slot 1 R3: Chase Brown (RB) -> Josh Allen (QB)
- slot 1 R4: Brock Bowers (TE) -> Chase Brown (RB)
- slot 1 R6: Tee Higgins (WR) -> Brock Bowers (TE)
- slot 2 R1: Christian McCaffrey (RB) -> Jahmyr Gibbs (RB)
- slot 2 R2: Jahmyr Gibbs (RB) -> Derrick Henry (RB)
- slot 2 R3: Derrick Henry (RB) -> Josh Allen (QB)
- slot 2 R5: Josh Allen (QB) -> Travis Etienne Jr. (RB)
- slot 3 R2: Chase Brown (RB) -> Derrick Henry (RB)
- slot 3 R5: Drake Maye (QB) -> Colston Loveland (TE)
- slot 3 R6: George Kittle (TE) -> Kenneth Walker III (RB)
- slot 4 R2: Chase Brown (RB) -> Derrick Henry (RB)
- slot 4 R5: Nico Collins (WR) -> Colston Loveland (TE)
- slot 4 R6: George Kittle (TE) -> Nico Collins (WR)
- slot 5 R2: Jaxon Smith-Njigba (WR) -> Derrick Henry (RB)
- slot 5 R3: Chris Olave (WR) -> Jaxon Smith-Njigba (WR)
- slot 5 R5: Drake Maye (QB) -> Garrett Wilson (WR)
- slot 5 R6: Tyler Warren (TE) -> Jayden Daniels (QB)
- slot 6 R5: Garrett Wilson (WR) -> Malik Nabers (WR)
- slot 6 R6: Malik Nabers (WR) -> Garrett Wilson (WR)
- slot 7 R2: Amon-Ra St. Brown (WR) -> Derrick Henry (RB)
- slot 7 R3: Chris Olave (WR) -> Amon-Ra St. Brown (WR)
- slot 7 R4: Omarion Hampton (RB) -> George Pickens (WR)
- slot 7 R5: Drake Maye (QB) -> Colston Loveland (TE)
- slot 7 R6: George Kittle (TE) -> Omarion Hampton (RB)
- slot 8 R2: Chase Brown (RB) -> Derrick Henry (RB)
- slot 8 R3: Chris Olave (WR) -> Rashee Rice (WR)
- slot 8 R4: Garrett Wilson (WR) -> Chris Olave (WR)
- slot 8 R5: Drake Maye (QB) -> Saquon Barkley (RB)
- slot 8 R6: George Kittle (TE) -> Jayden Daniels (QB)
- slot 9 R1: De'Von Achane (RB) -> Derrick Henry (RB)
- slot 9 R5: Drake Maye (QB) -> Kyren Williams (RB)
- slot 9 R6: George Kittle (TE) -> Jayden Daniels (QB)
- slot 10 R1: De'Von Achane (RB) -> Derrick Henry (RB)
- slot 10 R2: James Cook III (RB) -> De'Von Achane (RB)
- slot 10 R3: Justin Jefferson (WR) -> Javonte Williams (RB)
- slot 10 R5: Drake Maye (QB) -> Justin Jefferson (WR)
- slot 10 R6: George Kittle (TE) -> Jayden Daniels (QB)

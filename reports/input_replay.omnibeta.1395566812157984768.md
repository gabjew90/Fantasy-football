# Input replay — omnibeta, draft 1395566812157984768

Old board `data/processed/tiers.model.omnibeta.csv` vs new board `data/processed/tiers.external.omnibeta.csv`; 12 teams, 15 rounds; rivals held to the archived picks, our picks by the engine at every slot.

## The two boards

| pos | n both | Spearman proj_pts | left the board | joined |
|---|---|---|---|---|
| QB | 30 | 0.871 | 5 | 0 |
| RB | 61 | 0.951 | 7 | 5 |
| WR | 86 | 0.967 | 8 | 3 |
| TE | 26 | 0.930 | 4 | 2 |

Zeroed on the new board (non-starter rule or availability), had points before (13): Isiah Pacheco, Ray Davis, Jordan James, James Conner, Najee Harris, Alvin Kamara, Jonah Coleman, Kimani Vidal, Emari Demercado, Kenyon Sadiq, Terrance Ferguson, David Njoku, Fernando Mendoza

## Lineup points by slot

| slot | old roster, new ruler | new roster, new ruler | Δ | old roster, old ruler | new roster, old ruler | Δ |
|---|---|---|---|---|---|---|
| 1 | 2312 | 2283 | -29 | 2258 | 2118 | -140 |
| 2 | 2348 | 2269 | -80 | 2263 | 2076 | -187 |
| 3 | 2322 | 2391 | +69 | 2259 | 2274 | +16 |
| 4 | 2349 | 2347 | -2 | 2259 | 2256 | -3 |
| 5 | 2270 | 2297 | +27 | 2205 | 2189 | -17 |
| 6 | 2262 | 2291 | +29 | 2206 | 2167 | -39 |
| 7 | 2214 | 2222 | +8 | 2155 | 2120 | -34 |
| 8 | 2221 | 2221 | +1 | 2076 | 2055 | -21 |
| 9 | 2265 | 2278 | +13 | 2123 | 2092 | -32 |
| 10 | 2222 | 2200 | -21 | 2107 | 2059 | -48 |
| 11 | 2191 | 2190 | -0 | 2079 | 2044 | -35 |
| 12 | 2188 | 2164 | -24 | 2078 | 2015 | -62 |

Mean Δ on the new ruler -0.8 (slots better/worse 6/6); on the old ruler -50.2 (1/11).

## Picks that changed

117 of 180 picks changed. By round: R1: 2, R2: 4, R3: 7, R4: 8, R5: 6, R6: 12, R7: 11, R8: 11, R9: 7, R10: 12, R11: 12, R12: 11, R13: 10, R14: 2, R15: 2.

Rounds 1-6: 39 changes (54% of those picks); rounds 7+: 78.

By tier of the player the old board took (changed / picks at that tier): T1: 31/57 (54%), T2: 3/4 (75%), T3: 13/14 (93%), T4: 0/5 (0%), T5: 1/11 (9%), T6: 11/15 (73%), T7: 11/15 (73%), T8: 47/59 (80%).

Ten largest changes (projected points, new ruler, new pick minus old pick):

| slot | round | old pick | new pick | Δ |
|---|---|---|---|---|
| 2 | 11 | Phil Mafah (RB) | Wan'Dale Robinson (WR) | +169 |
| 5 | 11 | Emmett Johnson (RB) | Jaylen Waddle (WR) | +162 |
| 11 | 13 | Lamar Jackson (QB) | De'Zhaun Stribling (WR) | -149 |
| 12 | 9 | Tyrone Tracy Jr. (RB) | Cam Skattebo (RB) | +143 |
| 3 | 10 | Aaron Jones Sr. (RB) | Brock Purdy (QB) | +136 |
| 5 | 12 | Justin Herbert (QB) | MarShawn Lloyd (RB) | -134 |
| 7 | 12 | Bo Nix (QB) | MarShawn Lloyd (RB) | -134 |
| 9 | 12 | Bo Nix (QB) | MarShawn Lloyd (RB) | -134 |
| 12 | 12 | Bo Nix (QB) | MarShawn Lloyd (RB) | -134 |
| 11 | 7 | Parker Washington (WR) | Lamar Jackson (QB) | +132 |

Round 1-6 changes:

- slot 1 R1: Christian McCaffrey (RB) -> Jahmyr Gibbs (RB)
- slot 1 R2: Nico Collins (WR) -> Rashee Rice (WR)
- slot 1 R3: Chris Olave (WR) -> Jeremiyah Love (RB)
- slot 1 R4: Jahmyr Gibbs (RB) -> Nico Collins (WR)
- slot 1 R5: Kyren Williams (RB) -> Garrett Wilson (WR)
- slot 1 R6: Drake Maye (QB) -> Kyren Williams (RB)
- slot 2 R1: Christian McCaffrey (RB) -> Bijan Robinson (RB)
- slot 2 R2: Bijan Robinson (RB) -> Derrick Henry (RB)
- slot 2 R3: Chris Olave (WR) -> Rashee Rice (WR)
- slot 2 R4: Derrick Henry (RB) -> Garrett Wilson (WR)
- slot 2 R6: Drake Maye (QB) -> Harold Fannin Jr. (TE)
- slot 3 R2: Ja'Marr Chase (WR) -> Derrick Henry (RB)
- slot 3 R3: Chris Olave (WR) -> Ja'Marr Chase (WR)
- slot 3 R6: Rhamondre Stevenson (RB) -> Zay Flowers (WR)
- slot 4 R2: Jaxon Smith-Njigba (WR) -> Derrick Henry (RB)
- slot 4 R3: Chris Olave (WR) -> Jaxon Smith-Njigba (WR)
- slot 4 R4: Brock Bowers (TE) -> George Pickens (WR)
- slot 4 R5: Travis Etienne Jr. (RB) -> Brock Bowers (TE)
- slot 4 R6: George Pickens (WR) -> Travis Etienne Jr. (RB)
- slot 5 R3: Chris Olave (WR) -> Rashee Rice (WR)
- slot 5 R4: Travis Etienne Jr. (RB) -> Chris Olave (WR)
- slot 5 R5: Jaylen Waddle (WR) -> Kenneth Walker III (RB)
- slot 5 R6: Drake Maye (QB) -> Harold Fannin Jr. (TE)
- slot 6 R5: Jaylen Warren (RB) -> Quinshon Judkins (RB)
- slot 6 R6: Drake Maye (QB) -> Colston Loveland (TE)
- slot 7 R4: Travis Etienne Jr. (RB) -> Garrett Wilson (WR)
- slot 7 R6: Drake Maye (QB) -> Bucky Irving (RB)
- slot 8 R4: Travis Etienne Jr. (RB) -> Garrett Wilson (WR)
- slot 8 R6: Drake Maye (QB) -> Harold Fannin Jr. (TE)
- slot 9 R6: Drake Maye (QB) -> Breece Hall (RB)
- slot 10 R4: Garrett Wilson (WR) -> James Cook III (RB)
- slot 10 R5: James Cook III (RB) -> Emeka Egbuka (WR)
- slot 10 R6: Drake Maye (QB) -> Harold Fannin Jr. (TE)
- slot 11 R3: Trey McBride (TE) -> Ashton Jeanty (RB)
- slot 11 R5: Ashton Jeanty (RB) -> Trey McBride (TE)
- slot 11 R6: Jaylen Warren (RB) -> Rome Odunze (WR)
- slot 12 R3: Garrett Wilson (WR) -> Saquon Barkley (RB)
- slot 12 R4: Saquon Barkley (RB) -> Breece Hall (RB)
- slot 12 R6: Drake Maye (QB) -> Rome Odunze (WR)

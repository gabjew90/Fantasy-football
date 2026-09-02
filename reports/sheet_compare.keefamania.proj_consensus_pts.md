# Board vs FantasyPros consensus — keefamania

## Scoring basis (read this before comparing with any other sheet-vs-board number)

- Sheet side: the position tabs' **AVG stat lines** (raw consensus lines, NOT the Aggregate tab, which already carries the sheet's missed-games adjustment), scored with the league yaml's scoring: rec 0.5, pass_yd 0.04, pass_td 4, pass_int -1, rush_yd 0.1, rec_yd 0.1, rush_td 6, rec_td 6, fum_lost -2, pass_td_40p 2. Stat keys the sheet has no column for (e.g. pass_td_40p) are ignored.
- Games: sheet lines are 17-game season totals, scaled by 16/17 to the board's `expected_games` basis. No injury or missed-games adjustment is applied on either side.
- Board side: `proj_consensus_pts` from the league's tiers csv. Bias = board minus sheet.
- Ranks: within position, by the respective points. Spearman over matched players; 'top 36' restricts to the sheet's top 36 at the position.

A uniform negative bias across a position's starters cancels in VORP and is not a defect. Differences BETWEEN positions' biases do not cancel and are worth noting.

| pos | matched | Spearman (all) | Spearman (sheet top 36) | bias all | bias top 36 | unmatched |
|---|---|---|---|---|---|---|
| QB | 32 | 0.98 | 0.97 | -10.9 | -12.2 | 43 |
| RB | 61 | 0.97 | 0.98 | -17.6 | -20.8 | 61 |
| WR | 72 | 0.96 | 0.88 | -7.5 | -8.3 | 106 |
| TE | 33 | 0.90 | 0.88 | -3.5 | -4.5 | 83 |

## QB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 298 | 290 | -8 |
| 13-24 | 12 | 265 | 254 | -11 |
| 25-36 | 5 | 213 | 189 | -24 |
| 37-48 | 1 | 11 | 12 | +1 |
| 49-60 | 2 | 10 | 12 | +2 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Daniel Jones | 20 | 26 | 258 | 209 |
| Jaxson Dart | 7 | 11 | 292 | 277 |
| Jordan Love | 21 | 17 | 256 | 260 |
| Patrick Mahomes II | 11 | 14 | 285 | 268 |
| Matthew Stafford | 15 | 18 | 277 | 260 |
| Tyler Shough | 18 | 21 | 269 | 253 |
| Fernando Mendoza | 30 | 27 | 180 | 198 |
| Jayden Daniels | 3 | 5 | 303 | 289 |
| Caleb Williams | 12 | 10 | 284 | 280 |
| Bo Nix | 14 | 12 | 281 | 276 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Jacoby Brissett | 28 | 29 | 217 | 151 | -66 |
| Daniel Jones | 20 | 26 | 258 | 209 | -49 |
| Aaron Rodgers | 29 | 28 | 211 | 165 | -46 |
| Bryce Young | 25 | 24 | 241 | 220 | -21 |
| Fernando Mendoza | 30 | 27 | 180 | 198 | +17 |
| Matthew Stafford | 15 | 18 | 277 | 260 | -17 |
| Patrick Mahomes II | 11 | 14 | 285 | 268 | -17 |
| Tyler Shough | 18 | 21 | 269 | 253 | -15 |
| Jayden Daniels | 3 | 5 | 303 | 289 | -15 |
| Jaxson Dart | 7 | 11 | 292 | 277 | -14 |

Sheet players not on the board (43): Geno Smith, Tua Tagovailoa, Deshaun Watson, Shedeur Sanders, Michael Penix Jr., Kirk Cousins, Carson Beck, Ty Simpson, Marcus Mariota, Quinn Ewers, Justin Fields, Riley Leonard, J.J. McCarthy, Tyrod Taylor, Jarrett Stidham, Tommy DeVito, Tyson Bagent, Joshua Dobbs, Mac Jones, Joe Flacco, Tanner McKee, Anthony Richardson Sr., Kenny Pickett, Drew Allar, Trey Lance …

## RB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 252 | 229 | -23 |
| 13-24 | 12 | 194 | 171 | -23 |
| 25-36 | 12 | 150 | 133 | -17 |
| 37-48 | 11 | 117 | 90 | -27 |
| 49-60 | 8 | 81 | 69 | -12 |
| 61-80 | 5 | 46 | 61 | +14 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| David Montgomery | 23 | 16 | 172 | 179 |
| Rachaad White | 36 | 42 | 135 | 105 |
| Jeremiyah Love | 13 | 18 | 211 | 177 |
| Chuba Hubbard | 31 | 35 | 147 | 129 |
| Kyle Monangai | 35 | 31 | 136 | 135 |
| Jaylen Warren | 24 | 27 | 165 | 144 |
| Rhamondre Stevenson | 28 | 25 | 161 | 145 |
| Kenny Gainwell | 33 | 36 | 138 | 121 |
| James Cook III | 7 | 5 | 239 | 229 |
| Travis Etienne Jr. | 17 | 19 | 201 | 177 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Josh Jacobs | 42 | 47 | 126 | 74 | -53 |
| Isiah Pacheco | 46 | 59 | 97 | 46 | -52 |
| Alvin Kamara | 47 | 56 | 95 | 50 | -45 |
| Zach Charbonnet | 45 | 51 | 101 | 58 | -43 |
| Kaelon Black | 57 | 61 | 79 | 37 | -42 |
| Braelon Allen | 53 | 60 | 84 | 44 | -40 |
| Woody Marks | 44 | 48 | 107 | 70 | -37 |
| Christian McCaffrey | 3 | 3 | 278 | 241 | -37 |
| Jahmyr Gibbs | 1 | 1 | 317 | 280 | -37 |
| Jonathan Taylor | 4 | 4 | 272 | 237 | -35 |

Sheet players not on the board (61): Justice Hill, Dylan Sampson, AJ Dillon, Samaje Perine, Ty Johnson, Malik Davis, Chris Brooks, Jordan James, Najee Harris, Brashard Smith, Jaylen Wright, Emanuel Wilson, Kyle Juszczyk, Isaiah Davis, LeQuint Allen Jr., Adam Randall, Roschon Johnson, Sean Tucker, Seth McGowan, George Holani, Ray Davis, Corey Kiner, Ameer Abdullah, Kendre Miller, Jacob Saylors …

## WR

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 221 | 204 | -17 |
| 13-24 | 12 | 177 | 171 | -6 |
| 25-36 | 12 | 154 | 152 | -1 |
| 37-48 | 12 | 133 | 129 | -5 |
| 49-60 | 12 | 120 | 111 | -9 |
| 61-80 | 10 | 97 | 85 | -12 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Mike Evans | 33 | 17 | 154 | 174 |
| Rashee Rice | 8 | 20 | 207 | 173 |
| Davante Adams | 19 | 31 | 177 | 150 |
| DJ Moore | 25 | 35 | 164 | 139 |
| Michael Pittman Jr. | 36 | 45 | 141 | 128 |
| Parker Washington | 34 | 26 | 144 | 164 |
| Ladd McConkey | 22 | 15 | 168 | 177 |
| Courtland Sutton | 29 | 36 | 155 | 136 |
| Nico Collins | 12 | 6 | 197 | 205 |
| Brian Thomas Jr. | 35 | 29 | 143 | 155 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Calvin Ridley | 57 | 73 | 117 | 60 | -57 |
| Jaxon Smith-Njigba | 3 | 3 | 255 | 219 | -35 |
| Rashee Rice | 8 | 20 | 207 | 173 | -34 |
| Amon-Ra St. Brown | 4 | 4 | 246 | 212 | -34 |
| Cyrus Allen | 118 | 69 | 40 | 73 | +33 |
| De'Zhaun Stribling | 46 | 59 | 130 | 99 | -31 |
| Cooper Kupp | 69 | 72 | 95 | 66 | -29 |
| Rashod Bateman | 61 | 67 | 108 | 79 | -29 |
| Davante Adams | 19 | 31 | 177 | 150 | -27 |
| Jerry Jeudy | 56 | 62 | 119 | 92 | -26 |

Sheet players not on the board (106): Kayshon Boutte, Devaughn Vele, Jaylin Noel, Adonai Mitchell, Germie Bernard, Chris Bell, Antonio Williams, Caleb Douglas, Omar Cooper Jr., Dontayvion Wicks, Xavier Hutchinson, Tyquan Thornton, Tory Horton, Darius Slayton, Troy Franklin, Xavier Legette, Jahan Dotson, Bryce Lance, Tre' Harris, Ryan Flournoy, Jalen Tolbert, Malik Benson, Malachi Fields, Andrei Iosivas, Ted Hurst III …

## TE

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 150 | 142 | -8 |
| 13-24 | 12 | 110 | 107 | -4 |
| 25-36 | 7 | 85 | 84 | -0 |
| 37-48 | 1 | 59 | 58 | -1 |
| 61-80 | 1 | 28 | 53 | +25 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Oronde Gadsden II | 34 | 19 | 71 | 107 |
| Dallas Goedert | 9 | 23 | 138 | 103 |
| Chig Okonkwo | 27 | 20 | 94 | 107 |
| Juwan Johnson | 17 | 22 | 116 | 106 |
| Brenton Strange | 18 | 13 | 114 | 122 |
| Greg Dulcich | 22 | 27 | 100 | 82 |
| Terrance Ferguson | 23 | 28 | 97 | 78 |
| AJ Barner | 26 | 21 | 94 | 107 |
| Colby Parkinson | 35 | 30 | 69 | 58 |
| Tucker Kraft | 11 | 7 | 136 | 133 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| David Njoku | 32 | 33 | 81 | 44 | -38 |
| Oronde Gadsden II | 34 | 19 | 71 | 107 | +37 |
| Dallas Goedert | 9 | 23 | 138 | 103 | -35 |
| Jake Tonges | 65 | 32 | 28 | 53 | +25 |
| Kenyon Sadiq | 25 | 29 | 95 | 75 | -19 |
| Terrance Ferguson | 23 | 28 | 97 | 78 | -19 |
| Greg Dulcich | 22 | 27 | 100 | 82 | -18 |
| Trey McBride | 1 | 2 | 190 | 174 | -16 |
| Harold Fannin Jr. | 5 | 6 | 148 | 135 | -13 |
| Chig Okonkwo | 27 | 20 | 94 | 107 | +13 |

Sheet players not on the board (83): Evan Engram, Mike Gesicki, Gunnar Helm, Mason Taylor, Michael Mayer, Dawson Knox, Darnell Washington, Erick All Jr., Tyler Higbee, Cole Kmet, Noah Fant, Will Kacmarek, Charlie Kolar, Jonnu Smith, Brock Wright, Josh Oliver, Daniel Bellinger, Adam Trautman, Austin Hooper, Tommy Tremble, Eli Raridon, Noah Gray, Eli Stowers, Elijah Arroyo, Davis Allen …

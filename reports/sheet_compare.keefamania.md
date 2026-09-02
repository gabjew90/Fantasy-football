# Board vs FantasyPros consensus — keefamania

## Scoring basis (read this before comparing with any other sheet-vs-board number)

- Sheet side: the position tabs' **AVG stat lines** (raw consensus lines, NOT the Aggregate tab, which already carries the sheet's missed-games adjustment), scored with the league yaml's scoring: rec 0.5, pass_yd 0.04, pass_td 4, pass_int -1, rush_yd 0.1, rec_yd 0.1, rush_td 6, rec_td 6, fum_lost -2, pass_td_40p 2. Stat keys the sheet has no column for (e.g. pass_td_40p) are ignored.
- Games: sheet lines are 17-game season totals, scaled by 16/17 to the board's `expected_games` basis. No injury or missed-games adjustment is applied on either side.
- Board side: `proj_pts` from the league's tiers csv. Bias = board minus sheet.
- Ranks: within position, by the respective points. Spearman over matched players; 'top 36' restricts to the sheet's top 36 at the position.

A uniform negative bias across a position's starters cancels in VORP and is not a defect. Differences BETWEEN positions' biases do not cancel and are worth noting.

| pos | matched | Spearman (all) | Spearman (sheet top 36) | bias all | bias top 36 | unmatched |
|---|---|---|---|---|---|---|
| QB | 31 | 0.89 | 0.86 | -4.0 | -5.7 | 44 |
| RB | 60 | 0.92 | 0.93 | -7.8 | -16.1 | 62 |
| WR | 72 | 0.97 | 0.96 | -12.9 | -19.2 | 106 |
| TE | 31 | 0.88 | 0.88 | -3.6 | -3.6 | 85 |

## QB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 298 | 284 | -14 |
| 13-24 | 12 | 265 | 257 | -8 |
| 25-36 | 5 | 213 | 234 | +21 |
| 49-60 | 2 | 10 | 30 | +20 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Jayden Daniels | 3 | 11 | 303 | 276 |
| Joe Burrow | 6 | 14 | 293 | 264 |
| Jaxson Dart | 7 | 15 | 292 | 263 |
| Lamar Jackson | 2 | 9 | 305 | 278 |
| Matthew Stafford | 15 | 8 | 277 | 280 |
| Malik Willis | 22 | 29 | 256 | 220 |
| Patrick Mahomes II | 11 | 5 | 285 | 286 |
| Caleb Williams | 12 | 6 | 284 | 284 |
| Justin Herbert | 13 | 7 | 282 | 281 |
| Jacoby Brissett | 28 | 22 | 217 | 248 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Fernando Mendoza | 30 | 27 | 180 | 227 | +46 |
| Malik Willis | 22 | 29 | 256 | 220 | -36 |
| Jacoby Brissett | 28 | 22 | 217 | 248 | +31 |
| Joe Burrow | 6 | 14 | 293 | 264 | -29 |
| Jaxson Dart | 7 | 15 | 292 | 263 | -29 |
| Josh Allen | 1 | 1 | 349 | 321 | -28 |
| Jayden Daniels | 3 | 11 | 303 | 276 | -27 |
| Lamar Jackson | 2 | 9 | 305 | 278 | -27 |
| Spencer Rattler | 59 | 30 | 9 | 32 | +23 |
| Aaron Rodgers | 29 | 26 | 211 | 233 | +22 |

Sheet players not on the board (44): Geno Smith, Tua Tagovailoa, Deshaun Watson, Shedeur Sanders, Michael Penix Jr., Kirk Cousins, Carson Beck, Ty Simpson, Marcus Mariota, Quinn Ewers, Justin Fields, Riley Leonard, J.J. McCarthy, Jameis Winston, Tyrod Taylor, Jarrett Stidham, Tommy DeVito, Tyson Bagent, Joshua Dobbs, Mac Jones, Joe Flacco, Tanner McKee, Anthony Richardson Sr., Kenny Pickett, Drew Allar …

## RB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 252 | 234 | -17 |
| 13-24 | 12 | 194 | 172 | -22 |
| 25-36 | 12 | 150 | 141 | -9 |
| 37-48 | 11 | 117 | 91 | -26 |
| 49-60 | 8 | 81 | 102 | +22 |
| 61-80 | 4 | 45 | 96 | +50 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Bhayshul Tuten | 22 | 44 | 183 | 113 |
| MarShawn Lloyd | 34 | 49 | 138 | 104 |
| Kenneth Walker III | 10 | 18 | 223 | 180 |
| Rhamondre Stevenson | 28 | 21 | 161 | 167 |
| Chuba Hubbard | 31 | 38 | 147 | 125 |
| Kyren Williams | 16 | 10 | 206 | 201 |
| Kenny Gainwell | 33 | 27 | 138 | 154 |
| Breece Hall | 15 | 19 | 209 | 170 |
| Jaylen Warren | 24 | 20 | 165 | 170 |
| Rachaad White | 36 | 40 | 135 | 123 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Josh Jacobs | 42 | 61 | 126 | 0 | -126 |
| Zach Charbonnet | 45 | 62 | 101 | 0 | -101 |
| Bhayshul Tuten | 22 | 44 | 183 | 113 | -70 |
| Jonah Coleman | 70 | 46 | 42 | 111 | +69 |
| Emmett Johnson | 75 | 50 | 34 | 100 | +67 |
| Tyrone Tracy Jr. | 61 | 36 | 68 | 127 | +59 |
| Alvin Kamara | 47 | 58 | 95 | 51 | -44 |
| Kenneth Walker III | 10 | 18 | 223 | 180 | -43 |
| Derrick Henry | 5 | 8 | 250 | 211 | -39 |
| Breece Hall | 15 | 19 | 209 | 170 | -39 |

Sheet players not on the board (62): Justice Hill, Dylan Sampson, AJ Dillon, Samaje Perine, Ty Johnson, Malik Davis, Chris Brooks, Jordan James, Najee Harris, Kimani Vidal, Brashard Smith, Jaylen Wright, Emanuel Wilson, Kyle Juszczyk, Isaiah Davis, LeQuint Allen Jr., Adam Randall, Roschon Johnson, Sean Tucker, Seth McGowan, George Holani, Ray Davis, Corey Kiner, Ameer Abdullah, Kendre Miller …

## WR

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 221 | 204 | -17 |
| 13-24 | 12 | 177 | 155 | -22 |
| 25-36 | 12 | 154 | 135 | -18 |
| 37-48 | 12 | 133 | 119 | -14 |
| 49-60 | 12 | 120 | 109 | -11 |
| 61-80 | 10 | 97 | 96 | -0 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Alec Pierce | 30 | 41 | 154 | 124 |
| Jaylen Waddle | 26 | 18 | 163 | 156 |
| Courtland Sutton | 29 | 35 | 155 | 131 |
| Mike Evans | 33 | 27 | 154 | 140 |
| Parker Washington | 34 | 29 | 144 | 137 |
| Rashee Rice | 8 | 12 | 207 | 176 |
| Emeka Egbuka | 18 | 22 | 180 | 150 |
| Nico Collins | 12 | 9 | 197 | 184 |
| Zay Flowers | 13 | 16 | 189 | 164 |
| Jameson Williams | 21 | 24 | 174 | 142 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Cyrus Allen | 118 | 71 | 40 | 89 | +49 |
| Jameson Williams | 21 | 24 | 174 | 142 | -32 |
| Rashee Rice | 8 | 12 | 207 | 176 | -30 |
| Emeka Egbuka | 18 | 22 | 180 | 150 | -30 |
| Alec Pierce | 30 | 41 | 154 | 124 | -30 |
| Matthew Golden | 47 | 61 | 129 | 102 | -27 |
| Luther Burden III | 27 | 30 | 162 | 135 | -27 |
| DJ Moore | 25 | 28 | 164 | 138 | -26 |
| Zay Flowers | 13 | 16 | 189 | 164 | -25 |
| Courtland Sutton | 29 | 35 | 155 | 131 | -24 |

Sheet players not on the board (106): Kayshon Boutte, Devaughn Vele, Jaylin Noel, Adonai Mitchell, Germie Bernard, Chris Bell, Antonio Williams, Caleb Douglas, Omar Cooper Jr., Dontayvion Wicks, Xavier Hutchinson, Tyquan Thornton, Tory Horton, Darius Slayton, Troy Franklin, Xavier Legette, Jahan Dotson, Bryce Lance, Tre' Harris, Ryan Flournoy, Jalen Tolbert, Malik Benson, Malachi Fields, Andrei Iosivas, Ted Hurst III …

## TE

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 150 | 145 | -5 |
| 13-24 | 12 | 110 | 102 | -9 |
| 25-36 | 7 | 85 | 92 | +7 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Oronde Gadsden II | 34 | 20 | 71 | 102 |
| Colby Parkinson | 35 | 24 | 69 | 96 |
| Darren Waller | 28 | 19 | 89 | 103 |
| Isaiah Likely | 13 | 21 | 126 | 101 |
| Terrance Ferguson | 23 | 31 | 97 | 48 |
| Pat Freiermuth | 21 | 28 | 102 | 90 |
| T.J. Hockenson | 20 | 26 | 103 | 94 |
| Mark Andrews | 12 | 17 | 129 | 112 |
| Greg Dulcich | 22 | 27 | 100 | 92 |
| Dalton Schultz | 19 | 15 | 109 | 116 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Terrance Ferguson | 23 | 31 | 97 | 48 | -49 |
| Oronde Gadsden II | 34 | 20 | 71 | 102 | +31 |
| Colby Parkinson | 35 | 24 | 69 | 96 | +27 |
| Isaiah Likely | 13 | 21 | 126 | 101 | -25 |
| David Njoku | 32 | 30 | 81 | 57 | -25 |
| Colston Loveland | 3 | 6 | 162 | 140 | -22 |
| Mark Andrews | 12 | 17 | 129 | 112 | -17 |
| Darren Waller | 28 | 19 | 89 | 103 | +14 |
| Pat Freiermuth | 21 | 28 | 102 | 90 | -12 |
| Sam LaPorta | 8 | 11 | 140 | 130 | -11 |

Sheet players not on the board (85): Evan Engram, Mike Gesicki, Gunnar Helm, Mason Taylor, Michael Mayer, Dawson Knox, Theo Johnson, Darnell Washington, Erick All Jr., Tyler Higbee, Cole Kmet, Noah Fant, Will Kacmarek, Charlie Kolar, Jonnu Smith, Brock Wright, Josh Oliver, Daniel Bellinger, Adam Trautman, Austin Hooper, Tommy Tremble, Eli Raridon, Noah Gray, Eli Stowers, Elijah Arroyo …

# Board vs FantasyPros consensus — keefamania

## Scoring basis (read this before comparing with any other sheet-vs-board number)

- Sheet side: the position tabs' **AVG stat lines** (raw consensus lines, NOT the Aggregate tab, which already carries the sheet's missed-games adjustment), scored with the league yaml's scoring: rec 0.5, pass_yd 0.04, pass_td 4, pass_int -1, rush_yd 0.1, rec_yd 0.1, rush_td 6, rec_td 6, fum_lost -2, pass_td_40p 2. Stat keys the sheet has no column for (e.g. pass_td_40p) are ignored.
- Games: sheet lines are 17-game season totals, scaled by 16/17 to the board's `expected_games` basis. No injury or missed-games adjustment is applied on either side.
- Board side: `proj_pts` from the league's tiers csv. Bias = board minus sheet.
- Ranks: within position, by the respective points. Spearman over matched players; 'top 36' restricts to the sheet's top 36 at the position.

A uniform negative bias across a position's starters cancels in VORP and is not a defect. Differences BETWEEN positions' biases do not cancel and are worth noting.

| pos | matched | Spearman (all) | Spearman (sheet top 36) | bias all | bias top 36 | unmatched |
|---|---|---|---|---|---|---|
| QB | 31 | 0.85 | 0.81 | -7.2 | -9.1 | 44 |
| RB | 60 | 0.92 | 0.93 | -7.8 | -16.1 | 62 |
| WR | 72 | 0.94 | 0.93 | -11.7 | -18.1 | 106 |
| TE | 31 | 0.88 | 0.88 | -3.6 | -3.6 | 85 |

## QB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 298 | 282 | -16 |
| 13-24 | 12 | 265 | 254 | -12 |
| 25-36 | 5 | 213 | 226 | +13 |
| 49-60 | 2 | 10 | 30 | +20 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Jayden Daniels | 3 | 15 | 303 | 261 |
| Matthew Stafford | 15 | 4 | 277 | 289 |
| Jacoby Brissett | 28 | 18 | 217 | 253 |
| Lamar Jackson | 2 | 11 | 305 | 273 |
| Jaxson Dart | 7 | 16 | 292 | 261 |
| Joe Burrow | 6 | 13 | 293 | 269 |
| Patrick Mahomes II | 11 | 5 | 285 | 287 |
| Kyler Murray | 16 | 22 | 274 | 244 |
| Trevor Lawrence | 8 | 3 | 288 | 290 |
| Caleb Williams | 12 | 7 | 284 | 280 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Jayden Daniels | 3 | 15 | 303 | 261 | -42 |
| Fernando Mendoza | 30 | 28 | 180 | 218 | +37 |
| Jacoby Brissett | 28 | 18 | 217 | 253 | +36 |
| Lamar Jackson | 2 | 11 | 305 | 273 | -33 |
| Jaxson Dart | 7 | 16 | 292 | 261 | -31 |
| Kyler Murray | 16 | 22 | 274 | 244 | -30 |
| Malik Willis | 22 | 25 | 256 | 230 | -26 |
| Joe Burrow | 6 | 13 | 293 | 269 | -24 |
| Tyler Shough | 18 | 21 | 269 | 246 | -23 |
| Spencer Rattler | 59 | 30 | 9 | 31 | +21 |

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
| 1-12 | 12 | 221 | 201 | -20 |
| 13-24 | 12 | 177 | 159 | -19 |
| 25-36 | 12 | 154 | 138 | -16 |
| 37-48 | 12 | 133 | 121 | -12 |
| 49-60 | 12 | 120 | 111 | -9 |
| 61-80 | 10 | 97 | 98 | +1 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Luther Burden III | 27 | 53 | 162 | 111 |
| DJ Moore | 25 | 35 | 164 | 134 |
| Davante Adams | 19 | 11 | 177 | 182 |
| DK Metcalf | 32 | 24 | 154 | 147 |
| Jaylen Waddle | 26 | 19 | 163 | 156 |
| Justin Jefferson | 7 | 13 | 208 | 178 |
| Ladd McConkey | 22 | 28 | 168 | 144 |
| Marvin Harrison Jr. | 31 | 36 | 154 | 134 |
| Brian Thomas Jr. | 35 | 40 | 143 | 129 |
| CeeDee Lamb | 5 | 9 | 211 | 185 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Luther Burden III | 27 | 53 | 162 | 111 | -50 |
| Cyrus Allen | 118 | 70 | 40 | 89 | +49 |
| Matthew Golden | 47 | 73 | 129 | 86 | -43 |
| Emeka Egbuka | 18 | 21 | 180 | 150 | -30 |
| Justin Jefferson | 7 | 13 | 208 | 178 | -30 |
| DJ Moore | 25 | 35 | 164 | 134 | -29 |
| Jayden Reed | 38 | 56 | 137 | 108 | -29 |
| Rashod Bateman | 61 | 75 | 108 | 79 | -29 |
| Ja'Marr Chase | 2 | 3 | 259 | 232 | -27 |
| Jameson Williams | 21 | 23 | 174 | 147 | -27 |

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

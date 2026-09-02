# Board vs FantasyPros consensus — omnibeta

## Scoring basis (read this before comparing with any other sheet-vs-board number)

- Sheet side: the position tabs' **AVG stat lines** (raw consensus lines, NOT the Aggregate tab, which already carries the sheet's missed-games adjustment), scored with the league yaml's scoring: rec 1, pass_yd 0.04, pass_td 4, pass_int -1, rush_yd 0.1, rec_yd 0.1, rush_td 6, rec_td 6, fum_lost -2. Stat keys the sheet has no column for (e.g. pass_td_40p) are ignored.
- Games: sheet lines are 17-game season totals, scaled by 16/17 to the board's `expected_games` basis. No injury or missed-games adjustment is applied on either side.
- Board side: `proj_pts` from the league's tiers csv. Bias = board minus sheet.
- Ranks: within position, by the respective points. Spearman over matched players; 'top 36' restricts to the sheet's top 36 at the position.

A uniform negative bias across a position's starters cancels in VORP and is not a defect. Differences BETWEEN positions' biases do not cancel and are worth noting.

| pos | matched | Spearman (all) | Spearman (sheet top 36) | bias all | bias top 36 | unmatched |
|---|---|---|---|---|---|---|
| QB | 34 | 0.88 | 0.85 | -1.9 | -3.2 | 41 |
| RB | 71 | 0.91 | 0.95 | -2.4 | -15.8 | 51 |
| WR | 90 | 0.93 | 0.93 | -6.0 | -21.6 | 88 |
| TE | 33 | 0.91 | 0.90 | -5.8 | -4.7 | 83 |

## QB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 298 | 283 | -16 |
| 13-24 | 12 | 265 | 254 | -12 |
| 25-36 | 8 | 193 | 221 | +28 |
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
| Caleb Williams | 12 | 7 | 284 | 281 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Deshaun Watson | 32 | 30 | 127 | 213 | +86 |
| Tua Tagovailoa | 31 | 31 | 132 | 210 | +77 |
| Jayden Daniels | 3 | 15 | 303 | 261 | -42 |
| Fernando Mendoza | 30 | 28 | 180 | 218 | +37 |
| Jacoby Brissett | 28 | 18 | 217 | 253 | +36 |
| Lamar Jackson | 2 | 11 | 305 | 273 | -33 |
| Jaxson Dart | 7 | 16 | 292 | 261 | -31 |
| Kyler Murray | 16 | 22 | 274 | 244 | -30 |
| Malik Willis | 22 | 25 | 256 | 230 | -26 |
| Joe Burrow | 6 | 13 | 293 | 269 | -24 |

Sheet players not on the board (41): Shedeur Sanders, Michael Penix Jr., Kirk Cousins, Carson Beck, Ty Simpson, Marcus Mariota, Quinn Ewers, Justin Fields, Riley Leonard, J.J. McCarthy, Jameis Winston, Tyrod Taylor, Jarrett Stidham, Tommy DeVito, Tyson Bagent, Joshua Dobbs, Mac Jones, Joe Flacco, Tanner McKee, Anthony Richardson Sr., Kenny Pickett, Drew Allar, Trey Lance, Tyler Huntley, Sam Howell …

## RB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 277 | 259 | -18 |
| 13-24 | 12 | 212 | 192 | -20 |
| 25-36 | 12 | 166 | 157 | -9 |
| 37-48 | 12 | 127 | 96 | -30 |
| 49-60 | 11 | 88 | 105 | +17 |
| 61-80 | 8 | 56 | 94 | +38 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Kenny Gainwell | 32 | 42 | 161 | 124 |
| RJ Harvey | 34 | 25 | 153 | 173 |
| Bhayshul Tuten | 22 | 29 | 197 | 159 |
| Kenneth Walker III | 11 | 17 | 244 | 198 |
| Kyren Williams | 17 | 11 | 221 | 218 |
| Chuba Hubbard | 31 | 37 | 164 | 139 |
| Breece Hall | 14 | 19 | 231 | 189 |
| Rhamondre Stevenson | 26 | 21 | 180 | 185 |
| Cam Skattebo | 18 | 14 | 221 | 206 |
| Bucky Irving | 20 | 24 | 206 | 179 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Josh Jacobs | 41 | 78 | 136 | 0 | -136 |
| Zach Charbonnet | 46 | 79 | 110 | 0 | -110 |
| Nicholas Singleton | 94 | 56 | 19 | 103 | +84 |
| Kaytron Allen | 92 | 59 | 20 | 100 | +80 |
| Jonah Coleman | 71 | 43 | 47 | 123 | +76 |
| Demond Claiborne | 95 | 65 | 19 | 95 | +76 |
| Emmett Johnson | 75 | 50 | 36 | 112 | +75 |
| Tyrone Tracy Jr. | 61 | 34 | 77 | 144 | +66 |
| Alvin Kamara | 45 | 75 | 110 | 57 | -54 |
| Jaylen Wright | 69 | 64 | 49 | 96 | +48 |

Sheet players not on the board (51): AJ Dillon, Chris Brooks, Malik Davis, Brashard Smith, Kyle Juszczyk, Emanuel Wilson, LeQuint Allen Jr., Isaiah Davis, Adam Randall, Roschon Johnson, Seth McGowan, George Holani, Sean Tucker, Will Shipley, Ameer Abdullah, Hunter Luepke, Corey Kiner, Ollie Gordon II, Jacob Saylors, Kendre Miller, Audric Estime, Jeremy McNichols, Eli Heidenreich, Raheim Sanders, Rasheen Ali …

## WR

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 269 | 244 | -25 |
| 13-24 | 12 | 214 | 192 | -21 |
| 25-36 | 12 | 184 | 166 | -19 |
| 37-48 | 12 | 163 | 150 | -13 |
| 49-60 | 12 | 148 | 135 | -13 |
| 61-80 | 17 | 114 | 114 | +0 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Luther Burden III | 26 | 54 | 196 | 136 |
| DJ Moore | 25 | 36 | 196 | 162 |
| DK Metcalf | 32 | 23 | 184 | 177 |
| Ladd McConkey | 21 | 28 | 205 | 175 |
| Davante Adams | 19 | 13 | 209 | 217 |
| Rome Odunze | 27 | 22 | 193 | 179 |
| Marvin Harrison Jr. | 30 | 35 | 185 | 162 |
| Brian Thomas Jr. | 36 | 41 | 171 | 156 |
| Justin Jefferson | 7 | 11 | 255 | 218 |
| DeVonta Smith | 16 | 20 | 223 | 189 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Mack Hollins | 114 | 73 | 53 | 117 | +64 |
| Luther Burden III | 26 | 54 | 196 | 136 | -60 |
| Tank Dell | 116 | 83 | 51 | 111 | +60 |
| Cyrus Allen | 117 | 87 | 49 | 109 | +59 |
| Keon Coleman | 102 | 64 | 70 | 129 | +59 |
| Troy Franklin | 82 | 47 | 91 | 144 | +53 |
| Elic Ayomanor | 100 | 66 | 75 | 124 | +50 |
| Pat Bryant | 103 | 86 | 68 | 109 | +41 |
| Chimere Dike | 101 | 78 | 75 | 114 | +39 |
| Ryan Flournoy | 90 | 69 | 84 | 121 | +37 |

Sheet players not on the board (88): Germie Bernard, Chris Bell, Antonio Williams, Xavier Hutchinson, Xavier Legette, Tyquan Thornton, Jahan Dotson, Bryce Lance, Jalen Tolbert, Malik Benson, Isaac TeSlaa, Andrei Iosivas, Ted Hurst III, Hollywood Brown, DeMario Douglas, Zachariah Branch, Joshua Palmer, Kevin Coleman Jr., Marvin Mims Jr., Jack Bech, Ashton Dulin, Darnell Mooney, KaVontae Turpin, Devontez Walker, Demarcus Robinson …

## TE

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 186 | 180 | -6 |
| 13-24 | 12 | 138 | 131 | -8 |
| 25-36 | 8 | 104 | 105 | +2 |
| 49-60 | 1 | 41 | 0 | -41 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Oronde Gadsden II | 34 | 19 | 87 | 126 |
| Pat Freiermuth | 21 | 30 | 126 | 111 |
| Colby Parkinson | 35 | 26 | 85 | 117 |
| Darren Waller | 29 | 21 | 109 | 126 |
| Isaiah Likely | 14 | 20 | 156 | 126 |
| T.J. Hockenson | 20 | 25 | 133 | 118 |
| Greg Dulcich | 22 | 27 | 126 | 115 |
| Terrance Ferguson | 27 | 32 | 115 | 59 |
| Mason Taylor | 33 | 28 | 96 | 113 |
| Colston Loveland | 3 | 7 | 199 | 172 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Terrance Ferguson | 27 | 32 | 115 | 59 | -57 |
| Davis Allen | 60 | 33 | 41 | 0 | -41 |
| Oronde Gadsden II | 34 | 19 | 87 | 126 | +40 |
| Colby Parkinson | 35 | 26 | 85 | 117 | +32 |
| David Njoku | 32 | 31 | 101 | 70 | -31 |
| Isaiah Likely | 14 | 20 | 156 | 126 | -30 |
| Colston Loveland | 3 | 7 | 199 | 172 | -28 |
| Mark Andrews | 13 | 17 | 157 | 138 | -20 |
| Mason Taylor | 33 | 28 | 96 | 113 | +17 |
| Darren Waller | 29 | 21 | 109 | 126 | +16 |

Sheet players not on the board (83): Evan Engram, Gunnar Helm, Mike Gesicki, Michael Mayer, Dawson Knox, Theo Johnson, Darnell Washington, Erick All Jr., Tyler Higbee, Cole Kmet, Noah Fant, Will Kacmarek, Jonnu Smith, Charlie Kolar, Brock Wright, Adam Trautman, Daniel Bellinger, Josh Oliver, Austin Hooper, Tommy Tremble, Eli Raridon, Noah Gray, Eli Stowers, Elijah Arroyo, Ja'Tavion Sanders …

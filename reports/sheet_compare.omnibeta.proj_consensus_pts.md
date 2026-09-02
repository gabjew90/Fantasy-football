# Board vs FantasyPros consensus — omnibeta

## Scoring basis (read this before comparing with any other sheet-vs-board number)

- Sheet side: the position tabs' **AVG stat lines** (raw consensus lines, NOT the Aggregate tab, which already carries the sheet's missed-games adjustment), scored with the league yaml's scoring: rec 1, pass_yd 0.04, pass_td 4, pass_int -1, rush_yd 0.1, rec_yd 0.1, rush_td 6, rec_td 6, fum_lost -2. Stat keys the sheet has no column for (e.g. pass_td_40p) are ignored.
- Games: sheet lines are 17-game season totals, scaled by 16/17 to the board's `expected_games` basis. No injury or missed-games adjustment is applied on either side.
- Board side: `proj_consensus_pts` from the league's tiers csv. Bias = board minus sheet.
- Ranks: within position, by the respective points. Spearman over matched players; 'top 36' restricts to the sheet's top 36 at the position.

A uniform negative bias across a position's starters cancels in VORP and is not a defect. Differences BETWEEN positions' biases do not cancel and are worth noting.

| pos | matched | Spearman (all) | Spearman (sheet top 36) | bias all | bias top 36 | unmatched |
|---|---|---|---|---|---|---|
| QB | 35 | 0.98 | 0.97 | -12.6 | -14.0 | 40 |
| RB | 70 | 0.96 | 0.99 | -17.8 | -23.4 | 52 |
| WR | 90 | 0.96 | 0.90 | -7.7 | -9.8 | 88 |
| TE | 34 | 0.92 | 0.89 | -4.7 | -5.1 | 82 |

## QB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 298 | 290 | -8 |
| 13-24 | 12 | 265 | 254 | -11 |
| 25-36 | 8 | 193 | 167 | -27 |
| 37-48 | 1 | 11 | 12 | +1 |
| 49-60 | 2 | 10 | 12 | +2 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Daniel Jones | 20 | 27 | 258 | 209 |
| Jaxson Dart | 7 | 11 | 292 | 277 |
| Jordan Love | 21 | 17 | 256 | 260 |
| Patrick Mahomes II | 11 | 14 | 285 | 268 |
| Matthew Stafford | 15 | 18 | 277 | 260 |
| Tyler Shough | 18 | 21 | 269 | 253 |
| Jayden Daniels | 3 | 5 | 303 | 289 |
| Caleb Williams | 12 | 10 | 284 | 280 |
| Bo Nix | 14 | 12 | 281 | 276 |
| Malik Willis | 22 | 20 | 256 | 254 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Jacoby Brissett | 28 | 30 | 217 | 151 | -66 |
| Tua Tagovailoa | 31 | 32 | 132 | 82 | -51 |
| Daniel Jones | 20 | 27 | 258 | 209 | -49 |
| Aaron Rodgers | 29 | 29 | 211 | 165 | -46 |
| Deshaun Watson | 32 | 31 | 127 | 96 | -31 |
| Bryce Young | 25 | 24 | 241 | 220 | -21 |
| Fernando Mendoza | 30 | 28 | 180 | 198 | +17 |
| Matthew Stafford | 15 | 18 | 277 | 260 | -17 |
| Patrick Mahomes II | 11 | 14 | 285 | 268 | -17 |
| Tyler Shough | 18 | 21 | 269 | 253 | -15 |

Sheet players not on the board (40): Shedeur Sanders, Michael Penix Jr., Kirk Cousins, Carson Beck, Ty Simpson, Marcus Mariota, Quinn Ewers, Justin Fields, Riley Leonard, J.J. McCarthy, Tyrod Taylor, Jarrett Stidham, Tommy DeVito, Tyson Bagent, Joshua Dobbs, Mac Jones, Joe Flacco, Tanner McKee, Anthony Richardson Sr., Kenny Pickett, Drew Allar, Trey Lance, Tyler Huntley, Sam Howell, Jalon Daniels …

## RB

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 277 | 251 | -26 |
| 13-24 | 12 | 212 | 188 | -24 |
| 25-36 | 12 | 166 | 146 | -20 |
| 37-48 | 12 | 127 | 98 | -28 |
| 49-60 | 10 | 88 | 75 | -14 |
| 61-80 | 8 | 54 | 58 | +4 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| David Montgomery | 23 | 18 | 187 | 194 |
| Chuba Hubbard | 31 | 36 | 164 | 139 |
| Rachaad White | 36 | 41 | 152 | 121 |
| James Cook III | 8 | 5 | 255 | 244 |
| Travis Etienne Jr. | 16 | 19 | 223 | 194 |
| Tony Pollard | 27 | 30 | 177 | 151 |
| RJ Harvey | 34 | 37 | 153 | 136 |
| Aaron Jones Sr. | 35 | 38 | 152 | 129 |
| Ashton Jeanty | 10 | 12 | 245 | 220 |
| Javonte Williams | 15 | 13 | 227 | 200 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Isiah Pacheco | 48 | 64 | 107 | 50 | -56 |
| Josh Jacobs | 41 | 48 | 136 | 80 | -56 |
| Alvin Kamara | 45 | 59 | 110 | 59 | -51 |
| Zach Charbonnet | 46 | 54 | 110 | 63 | -47 |
| Najee Harris | 65 | 70 | 70 | 25 | -45 |
| Justice Hill | 47 | 53 | 108 | 64 | -44 |
| Kaelon Black | 57 | 67 | 84 | 40 | -44 |
| Braelon Allen | 52 | 66 | 91 | 49 | -42 |
| Christian McCaffrey | 3 | 3 | 315 | 274 | -41 |
| Jahmyr Gibbs | 1 | 1 | 351 | 310 | -41 |

Sheet players not on the board (52): AJ Dillon, Ty Johnson, Chris Brooks, Malik Davis, Brashard Smith, Kyle Juszczyk, Jaylen Wright, Emanuel Wilson, LeQuint Allen Jr., Isaiah Davis, Adam Randall, Roschon Johnson, Seth McGowan, George Holani, Will Shipley, Ameer Abdullah, Hunter Luepke, Corey Kiner, Ollie Gordon II, Jacob Saylors, Kendre Miller, Jeremy McNichols, Eli Heidenreich, Kaytron Allen, Nicholas Singleton …

## WR

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 269 | 248 | -21 |
| 13-24 | 12 | 214 | 207 | -6 |
| 25-36 | 12 | 184 | 182 | -2 |
| 37-48 | 12 | 163 | 157 | -5 |
| 49-60 | 12 | 148 | 137 | -11 |
| 61-80 | 17 | 114 | 100 | -13 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Davante Adams | 19 | 31 | 209 | 179 |
| Parker Washington | 35 | 24 | 173 | 198 |
| DJ Moore | 25 | 34 | 196 | 168 |
| Courtland Sutton | 28 | 37 | 187 | 164 |
| Mike Evans | 31 | 22 | 184 | 207 |
| Rashee Rice | 8 | 16 | 252 | 214 |
| Michael Pittman Jr. | 34 | 41 | 179 | 161 |
| Nico Collins | 12 | 6 | 236 | 245 |
| Ladd McConkey | 21 | 15 | 205 | 215 |
| Jameson Williams | 22 | 28 | 205 | 194 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Calvin Ridley | 59 | 85 | 139 | 73 | -67 |
| Jaxon Smith-Njigba | 3 | 3 | 307 | 266 | -41 |
| Cyrus Allen | 117 | 78 | 49 | 89 | +40 |
| Amon-Ra St. Brown | 4 | 4 | 301 | 262 | -39 |
| Rashee Rice | 8 | 16 | 252 | 214 | -38 |
| Cooper Kupp | 69 | 82 | 118 | 81 | -36 |
| De'Zhaun Stribling | 48 | 59 | 157 | 121 | -36 |
| Jerry Jeudy | 56 | 65 | 147 | 113 | -34 |
| Jaylin Noel | 70 | 84 | 113 | 80 | -33 |
| Keenan Allen | 61 | 69 | 134 | 101 | -33 |

Sheet players not on the board (88): Germie Bernard, Chris Bell, Antonio Williams, Xavier Hutchinson, Xavier Legette, Tyquan Thornton, Jahan Dotson, Bryce Lance, Jalen Tolbert, Malik Benson, Isaac TeSlaa, Andrei Iosivas, Ted Hurst III, Hollywood Brown, DeMario Douglas, Zachariah Branch, Joshua Palmer, Kevin Coleman Jr., Marvin Mims Jr., Jack Bech, Ashton Dulin, Darnell Mooney, KaVontae Turpin, Devontez Walker, Demarcus Robinson …

## TE

Deep-rank bands (by sheet rank):

| band | n | sheet | board | diff |
|---|---|---|---|---|
| 1-12 | 12 | 186 | 177 | -9 |
| 13-24 | 12 | 138 | 137 | -1 |
| 25-36 | 7 | 105 | 100 | -5 |
| 37-48 | 1 | 72 | 72 | +0 |
| 49-60 | 1 | 41 | 6 | -36 |
| 61-80 | 1 | 35 | 67 | +32 |

Largest rank disagreements (sheet top 36):

| player | sheet rk | board rk | sheet pts | board pts |
|---|---|---|---|---|
| Dallas Goedert | 10 | 23 | 169 | 128 |
| Oronde Gadsden II | 34 | 21 | 87 | 133 |
| Juwan Johnson | 16 | 22 | 146 | 133 |
| AJ Barner | 26 | 20 | 117 | 134 |
| Brenton Strange | 18 | 13 | 143 | 152 |
| Greg Dulcich | 22 | 27 | 126 | 104 |
| Chig Okonkwo | 24 | 19 | 119 | 136 |
| Tucker Kraft | 11 | 7 | 164 | 164 |
| Dalton Kincaid | 15 | 11 | 151 | 154 |
| T.J. Hockenson | 20 | 16 | 133 | 146 |

Largest point disagreements (all matched):

| player | sheet rk | board rk | sheet pts | board pts | diff |
|---|---|---|---|---|---|
| Oronde Gadsden II | 34 | 21 | 87 | 133 | +47 |
| David Njoku | 32 | 33 | 101 | 55 | -47 |
| Dallas Goedert | 10 | 23 | 169 | 128 | -41 |
| Davis Allen | 60 | 34 | 41 | 6 | -36 |
| Jake Tonges | 65 | 32 | 35 | 67 | +32 |
| Kenyon Sadiq | 25 | 29 | 117 | 94 | -23 |
| Trey McBride | 1 | 2 | 241 | 219 | -22 |
| Greg Dulcich | 22 | 27 | 126 | 104 | -22 |
| Terrance Ferguson | 27 | 28 | 115 | 94 | -21 |
| Harold Fannin Jr. | 5 | 6 | 187 | 170 | -17 |

Sheet players not on the board (82): Evan Engram, Gunnar Helm, Mike Gesicki, Mason Taylor, Michael Mayer, Dawson Knox, Darnell Washington, Erick All Jr., Tyler Higbee, Cole Kmet, Noah Fant, Will Kacmarek, Jonnu Smith, Charlie Kolar, Brock Wright, Adam Trautman, Daniel Bellinger, Josh Oliver, Austin Hooper, Tommy Tremble, Eli Raridon, Noah Gray, Eli Stowers, Elijah Arroyo, Ja'Tavion Sanders …

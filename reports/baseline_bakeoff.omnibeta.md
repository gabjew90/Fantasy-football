# Baseline bake-off -- omnibeta, draft 1395566812157984768, 12 slots

Scoring: projected points of the best legal starting lineup on the league's own shape (QB 1, RB 2, WR 2, TE 1, FLEX 2, K 1, DEF 1). Rule (DECISIONS #33): a candidate replaces the yaml baselines only if mean >= yaml AND wins >= losses; ties keep the yaml.

| candidate | baselines | mean | median | min | vs yaml mean | better | worse | tied |
|---|---|---|---|---|---|---|---|---|
| yaml | QB12/RB40/WR60/TE12/K12/DEF12 | 2172.4 | 2180.0 | 2076.1 | +0.0 | 0 | 0 | 12 |
| flex | QB12/RB32/WR40/TE12/K12/DEF12 | 2172.8 | 2180.0 | 2076.1 | +0.4 | 2 | 2 | 8 |
| flex+bench | QB12/RB40/WR49/TE12/K12/DEF12 | 2167.3 | 2180.0 | 2037.0 | -5.1 | 1 | 3 | 8 |

Per slot (projected lineup points):

| slot | yaml | flex | flex+bench |
|---|---|---|---|
| 1 | 2258 | 2258 | 2238 |
| 2 | 2263 | 2298 | 2263 |
| 3 | 2259 | 2259 | 2259 |
| 4 | 2259 | 2259 | 2259 |
| 5 | 2205 | 2205 | 2205 |
| 6 | 2206 | 2207 | 2207 |
| 7 | 2155 | 2155 | 2155 |
| 8 | 2076 | 2076 | 2076 |
| 9 | 2123 | 2123 | 2123 |
| 10 | 2107 | 2077 | 2107 |
| 11 | 2079 | 2078 | 2078 |
| 12 | 2078 | 2078 | 2037 |

Roster shapes (yaml arm): QB2 RB7 WR3 TE1 K1 DEF1, QB2 RB6 WR3 TE2 K1 DEF1, QB2 RB4 WR6 TE1 K1 DEF1, QB2 RB5 WR5 TE1 K1 DEF1, QB2 RB6 WR4 TE1 K1 DEF1, QB2 RB5 WR5 TE1 K1 DEF1, QB2 RB7 WR3 TE1 K1 DEF1, QB2 RB5 WR5 TE1 K1 DEF1, QB2 RB7 WR3 TE1 K1 DEF1, QB2 RB5 WR5 TE1 K1 DEF1, QB2 RB6 WR3 TE2 K1 DEF1, QB2 RB6 WR4 TE1 K1 DEF1


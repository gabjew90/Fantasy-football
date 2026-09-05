# Bench knobs, season replay (2026-09-04, DECISIONS #47)

A arm: insurance as shipped. B arm: the knob(s) named. 200 seasons per roster, empirical absences.

## season_bench_keefamania

```
B arm overrides: {'bench_survival_discount': True, 'bench_contingency': True, 'late_round_dispersion': True} (A arm: insurance on, defaults)
Season replay — keefamania: 10 teams, k=3, 200 seasons per roster, absences from empirical position distributions

slot  VORP bench  insurance    diff  wire off  wire on   shape off -> on
   1      1576.8     1592.7   +15.9      24.4     24.6   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   2      1544.6     1543.5    -1.1      26.0     25.9   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
   3      1603.2     1578.7   -24.5      11.6     11.6   QB2 RB4 WR5 TE2 K1 DEF1 -> QB2 RB3 WR6 TE2 K1 DEF1
   4      1516.5     1514.0    -2.5      26.0     26.0   QB2 RB4 WR6 TE1 K1 DEF1 -> QB2 RB4 WR6 TE1 K1 DEF1
   5      1557.5     1539.1   -18.4      12.0     24.7   QB2 RB5 WR4 TE2 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   6      1593.4     1593.4    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   7      1539.6     1539.1    -0.5      26.1     26.6   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   8      1569.8     1482.5   -87.3      26.2     25.7   QB2 RB6 WR4 TE1 K1 DEF1 -> QB1 RB7 WR4 TE1 K1 DEF1
   9      1515.6     1469.0   -46.6      26.6     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB1 RB7 WR4 TE1 K1 DEF1
  10      1487.7     1473.8   -13.9      26.1     25.9   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1

n=10 slots x 200 seasons
insurance - VORP: mean -17.9 pts/season  (paired se 1.0)  slots better 1  worse 8  tied 1
VORP-bench mean season 1550.5  ->  insurance is -1.15%
```

## season_bench_omnibeta

```
B arm overrides: {'bench_survival_discount': True, 'bench_contingency': True, 'late_round_dispersion': True} (A arm: insurance on, defaults)
Season replay — omnibeta: 12 teams, k=2, 200 seasons per roster, absences from empirical position distributions

slot  VORP bench  insurance    diff  wire off  wire on   shape off -> on
   1      2102.2     2072.3   -29.8      57.2     64.3   QB2 RB6 WR4 TE1 K1 DEF1 -> QB1 RB7 WR4 TE1 K1 DEF1
   2      2133.4     2067.2   -66.2      44.5     48.7   QB2 RB6 WR3 TE2 K1 DEF1 -> QB1 RB6 WR4 TE2 K1 DEF1
   3      2158.4     2076.5   -81.9      60.8     77.5   QB2 RB4 WR6 TE1 K1 DEF1 -> QB1 RB3 WR8 TE1 K1 DEF1
   4      2161.5     2118.6   -42.9      68.4     57.5   QB2 RB7 WR3 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   5      2092.0     2086.4    -5.6      56.7     67.0   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
   6      2047.6     2043.2    -4.4      62.5     75.0   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
   7      2020.7     2028.0    +7.3      61.7     58.3   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   8      1994.5     1994.2    -0.3      59.3     68.5   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
   9      1999.1     2018.4   +19.3      55.3     60.0   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
  10      1998.6     1976.7   -22.0      67.4     57.6   QB2 RB7 WR3 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
  11      1958.8     1924.5   -34.3      45.6     45.4   QB2 RB6 WR3 TE2 K1 DEF1 -> QB1 RB6 WR4 TE2 K1 DEF1
  12      1976.1     1943.8   -32.3      57.1     67.7   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1

n=12 slots x 200 seasons
insurance - VORP: mean -24.4 pts/season  (paired se 1.2)  slots better 2  worse 10  tied 0
VORP-bench mean season 2053.6  ->  insurance is -1.19%
```

## season_bench_survival_discount

```
B arm overrides: {'bench_survival_discount': True} (A arm: insurance on, defaults)
Season replay — keefamania: 10 teams, k=3, 200 seasons per roster, absences from empirical position distributions

slot  VORP bench  insurance    diff  wire off  wire on   shape off -> on
   1      1576.8     1576.8    +0.0      24.4     24.4   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   2      1544.6     1555.4   +10.8      26.0     26.0   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   3      1603.2     1578.7   -24.5      11.6     11.6   QB2 RB4 WR5 TE2 K1 DEF1 -> QB2 RB3 WR6 TE2 K1 DEF1
   4      1516.5     1519.0    +2.5      26.0     26.1   QB2 RB4 WR6 TE1 K1 DEF1 -> QB2 RB4 WR6 TE1 K1 DEF1
   5      1557.5     1539.1   -18.4      12.0     24.7   QB2 RB5 WR4 TE2 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   6      1593.4     1593.4    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   7      1539.6     1539.6    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   8      1569.8     1571.8    +2.0      26.2     26.2   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   9      1515.6     1515.6    +0.0      26.6     26.6   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
  10      1487.7     1498.0   +10.3      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1

n=10 slots x 200 seasons
insurance - VORP: mean -1.7 pts/season  (paired se 0.4)  slots better 4  worse 2  tied 4
VORP-bench mean season 1550.5  ->  insurance is -0.11%
```

## season_bench_contingency

```
B arm overrides: {'bench_contingency': True} (A arm: insurance on, defaults)
Season replay — keefamania: 10 teams, k=3, 200 seasons per roster, absences from empirical position distributions

slot  VORP bench  insurance    diff  wire off  wire on   shape off -> on
   1      1576.8     1592.7   +15.9      24.4     24.6   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   2      1544.6     1536.5    -8.1      26.0     25.8   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
   3      1603.2     1602.8    -0.4      11.6     11.8   QB2 RB4 WR5 TE2 K1 DEF1 -> QB2 RB5 WR4 TE2 K1 DEF1
   4      1516.5     1516.5    +0.0      26.0     26.0   QB2 RB4 WR6 TE1 K1 DEF1 -> QB2 RB4 WR6 TE1 K1 DEF1
   5      1557.5     1557.5    +0.0      12.0     12.0   QB2 RB5 WR4 TE2 K1 DEF1 -> QB2 RB5 WR4 TE2 K1 DEF1
   6      1593.4     1593.4    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   7      1539.6     1539.6    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   8      1569.8     1530.6   -39.2      26.2     26.2   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   9      1515.6     1507.1    -8.5      26.6     26.4   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1
  10      1487.7     1484.1    -3.6      26.1     25.9   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB7 WR3 TE1 K1 DEF1

n=10 slots x 200 seasons
insurance - VORP: mean -4.4 pts/season  (paired se 0.6)  slots better 1  worse 5  tied 4
VORP-bench mean season 1550.5  ->  insurance is -0.28%
```

## season_late_round_dispersion

```
B arm overrides: {'late_round_dispersion': True} (A arm: insurance on, defaults)
Season replay — keefamania: 10 teams, k=3, 200 seasons per roster, absences from empirical position distributions

slot  VORP bench  insurance    diff  wire off  wire on   shape off -> on
   1      1576.8     1576.8    +0.0      24.4     24.4   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   2      1544.6     1544.6    +0.0      26.0     26.0   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   3      1603.2     1603.2    +0.0      11.6     11.6   QB2 RB4 WR5 TE2 K1 DEF1 -> QB2 RB4 WR5 TE2 K1 DEF1
   4      1516.5     1516.5    +0.0      26.0     26.0   QB2 RB4 WR6 TE1 K1 DEF1 -> QB2 RB4 WR6 TE1 K1 DEF1
   5      1557.5     1557.5    +0.0      12.0     12.0   QB2 RB5 WR4 TE2 K1 DEF1 -> QB2 RB5 WR4 TE2 K1 DEF1
   6      1593.4     1593.4    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   7      1539.6     1539.6    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   8      1569.8     1569.8    +0.0      26.2     26.2   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
   9      1515.6     1515.6    +0.0      26.6     26.6   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1
  10      1487.7     1487.7    +0.0      26.1     26.1   QB2 RB6 WR4 TE1 K1 DEF1 -> QB2 RB6 WR4 TE1 K1 DEF1

n=10 slots x 200 seasons
insurance - VORP: mean +0.0 pts/season  (paired se 0.0)  slots better 0  worse 0  tied 10
VORP-bench mean season 1550.5  ->  insurance is +0.00%
```

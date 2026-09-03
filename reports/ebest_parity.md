# Expected-best estimators: joint vs carry (plan B2 measurement)

40 random mid-draft states per league (engine_parity's generator, seed 7), sims 1000, production knobs from each league's config. Per market: urgency from the joint (Monte Carlo) expectation vs the carry (independence) formula over the calibrated survival vector.

- keefamania state 13 (slot 9, pick 12): joint -> De'Von Achane|RB, carry -> Amon-Ra St. Brown|WR
- omnibeta state 8 (slot 4, pick 21): joint -> George Pickens|WR, carry -> Omarion Hampton|RB

| league | states | top-1 unchanged | mean abs delta urgency | max abs delta | bar (>=38/40, max<2) |
|---|---|---|---|---|---|
| keefamania | 40 | 39 | 1.16 | 6.83 | FAIL |
| omnibeta | 40 | 39 | 1.15 | 8.17 | FAIL |

Largest gaps (league, state, market, urgency joint, urgency carry):

- keefamania state 27 RB: joint 34.6 vs carry 27.7 (|delta| 6.8)
- keefamania state 20 TE: joint 0.9 vs carry 7.4 (|delta| 6.5)
- keefamania state 26 TE: joint 5.8 vs carry 11.6 (|delta| 5.8)
- keefamania state 26 RB: joint 37.2 vs carry 31.5 (|delta| 5.7)
- keefamania state 27 WR: joint 23.1 vs carry 17.8 (|delta| 5.3)
- omnibeta state 2 TE: joint 0.6 vs carry 8.8 (|delta| 8.2)
- omnibeta state 12 TE: joint 0.5 vs carry 8.7 (|delta| 8.2)
- omnibeta state 9 TE: joint 2.4 vs carry 10.3 (|delta| 7.8)
- omnibeta state 17 TE: joint 7.8 vs carry 15.3 (|delta| 7.6)
- omnibeta state 17 RB: joint 38.5 vs carry 31.4 (|delta| 7.1)

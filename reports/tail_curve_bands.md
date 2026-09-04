# Market-curve tail arms (DECISIONS #40)

Deep-band MAE is the PRIMARY accuracy criterion. Pass needs the deep ratio
at most 0.97 in both leagues, at most 1.00 in 3 of 4 cells, the head MAE ratio
at most 1.01 with no top-12 projection moving more than 2.0 points, and at least
25% of deep rows moving by more than 1.0 point. Pooled accuracy and the
actual-points outcome replay are judged by scripts/source_gate.py on the same file.

### keefamania — deep bands (RB rank 37+, WR rank 49+), n=58

| arm | deep MAE | ratio | head MAE ratio | max top-12 move | deep rows moved >1pt |
|---|---|---|---|---|---|
| blend (base) | 70.0 | 1.000 | 1.000 | 0.0 | — |
| blend_rank | 71.2 | 1.017 | 0.998 | 10.8 | 37/58 (64%) |
| blend_rank_lin | 65.4 | 0.934 | 1.012 | 26.9 | 57/58 (98%) |
| blend_tail | 65.4 | 0.933 | 1.011 | 26.9 | 57/58 (98%) |

| cell | blend_rank | blend_rank_lin | blend_tail |
|---|---|---|---|
| 2023->2024 (n=33) | 1.012 | 0.944 | 0.944 |
| 2024->2025 (n=25) | 1.023 | 0.924 | 0.923 |

### omnibeta — deep bands (RB rank 37+, WR rank 49+), n=113

| arm | deep MAE | ratio | head MAE ratio | max top-12 move | deep rows moved >1pt |
|---|---|---|---|---|---|
| blend (base) | 70.5 | 1.000 | 1.000 | 0.0 | — |
| blend_rank | 70.2 | 0.997 | 0.997 | 15.5 | 81/113 (72%) |
| blend_rank_lin | 66.3 | 0.942 | 1.011 | 31.4 | 98/113 (87%) |
| blend_tail | 66.3 | 0.942 | 1.010 | 31.4 | 98/113 (87%) |

| cell | blend_rank | blend_rank_lin | blend_tail |
|---|---|---|---|
| 2023->2024 (n=47) | 0.998 | 0.954 | 0.954 |
| 2024->2025 (n=66) | 0.996 | 0.933 | 0.933 |


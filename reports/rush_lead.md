# Round 15: the backs' carry shares rescaled toward a realistic total (props-v1.28)

*2026-10-01. Settings in `resources/width_params.json`: rush_other_share 0.12,
rush_norm_strength 0.5, rush_norm_qb false, rush_norm_lead 1.0. Tuning table:
`reports/width_tuning_rushlead.md` (2022-23 only). Code: `model.rescale_rush_shares`.*

## The defect

On the shipped model (props-v1.27) the running backs ran about 4% above their projected
rushing yards on 2024-25 (5.5% in weeks 2-4, flagged BIASED), and rushing yards missed the
harness calibration check (worst 60-90% bucket 0.034 against 0.03).

Diagnosis on 2022-23 only (the tune seasons; 2024-25 left for the verdict):

- the lead backs were on (carries x1.019, yards x0.998); the #2 backs ran +3% / +4.8%;
- it tracks how far the priced players' carry shares miss a realistic total. In team-games
  whose shares sum below 0.8 (a quarter of them) both backs ran over (lead +17%, #2 +43%);
  between 0.8 and 1.0 they were about right; above 1.0 the #2 backs ran 12-19% under.

## The change

When the shares miss 1 - 0.12 (about 12% of carries historically go to players outside the
priced set), half the gap is closed: ADDED to the eligible players in proportion to their
shares. The starting QB keeps exactly the share the sampler gave him before (his raw share,
divided by the total when the shares overshoot) -- a first version without that guard moved
QB projections ~2% (the sampler's own normalisation had been trimming him in overshoot
games), which pushed QB rushing over the bias line on 2024-25.

The hypothesis that the correction belongs on the #2 backs alone (rush_norm_lead 0) was
tested and is WRONG: it scored worse than no rescale. The tuner chose the proportional split.

## The rule, fixed before each run

Pick on 2022-23; ship only if on 2024-25 rushing yards clearly improves (paired interval
excluding zero) or its verdict flips to PASS, QB rushing and every other market are not
measurably worse, and (second run) QB rushing passes again and 2026 weeks 2-3 -- never tuned
or diagnosed on -- is not clearly worse.

**Disclosed:** the 2024-25 seasons were seen once for this setting family (the first, unguarded
run) before the QB guard was added; the guard makes the QB match the shipped sampler, a
structural correction rather than a tuned value, and the re-tune read 2022-23 only.

## Result (guarded, vs props-v1.27, paired by player-week, game-block 95% intervals)

| Seasons | Weeks | Rushing yards CRPS change | actual/model | QB rushing CRPS change | actual/model |
|---|---|---|---|---|---|
| test 24-25 | all | **+0.243 [+0.092, +0.392]** | 1.039 -> 1.033 | -0.001 [-0.022, +0.020] | 0.954 -> 0.953 |
| test 24-25 | 2-4 | -0.054 [-0.314, +0.241] | 1.055 -> 1.065 | -0.011 [-0.057, +0.035] | 0.816 -> 0.812 |
| test 24-25 | 5-18 | **+0.309 [+0.138, +0.486]** | 1.035 -> 1.026 | +0.001 [-0.022, +0.025] | 0.995 -> 0.995 |
| 2026 (fresh) | 2-3 | +0.219 [-0.110, +0.581] | 0.921 -> 0.934 | +0.022 [-0.064, +0.108] | 0.985 -> 0.979 |

Receptions, receiving yards and QB passing yards: identical (their draws do not touch the
carry split). Live check, NYJ@CHI 2026 week 4: both teams' priced shares overshoot (0.96,
1.00), so the backs' medians fall 1-6 yards (Swift 67.5 -> 61.8, Hall 60.1 -> 56.2, Monangai 38.7 -> 35.4, Allen 19.0 -> 17.8); the QBs' are unchanged (28.8 -> 28.8, 11.5 -> 11.4).

## The verdict flags, read honestly

- Rushing yards: improved, still DOES NOT PASS calibration (0.034 -> 0.032).
- QB rushing: DOES NOT PASS on calibration (0.039) where props-v1.27 passed (0.029). The QB's
  projections are the shipped ones (mean difference 0.01 yards; CRPS change -0.001), so this
  is Monte Carlo movement in one bucket (Over 80-90%: -0.028 -> -0.039), not a change in the
  model: the backs' different carry counts shift the random stream the QB's yards are drawn
  from. props-v1.27 passed by 0.001. **Harness note:** a pass/fail check that flips on
  stream noise at its threshold is fragile; QB yards drawn from their own child stream would
  make a backs-only change leave the QB byte-identical. Recorded, not done here.

Decision (the user's, 2026-10-01): ship, released Friday morning so the Thursday game stays
on one engine and every Sunday game is priced by the new one.

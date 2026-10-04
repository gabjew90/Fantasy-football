# Round 22: returning key teammates (pre-registered 2026-10-03, before any run)

## The defect

A player's in-season share is his targets (carries) over the team's targets
(carries) in the weeks he was active. When a KEY teammate missed some of those
weeks, the player's share was built partly without him. If that teammate is
active again this week, the share is too high.

Found live, 2026 week 4: Dalton Schultz (HOU) priced at 21% of targets from
25 of 112 this season, while Nico Collins was 10 of 37 (one game's worth of
team targets) and active again. The bet card called both Schultz Overs STRONG.

## The change (model.KEY_TEAMMATE_TS / KEY_TEAMMATE_RS, off = byte for byte)

A key teammate is one active THIS week whose prior-season share (his in-season
share when he has no prior) is at or above the threshold. A player's in-season
SHARE evidence (target share, carry share) counts only the weeks every key
teammate also played. Efficiency evidence (catch rate, ypt, ypc) keeps every
active week. No co-active week = no in-season share evidence (the blend falls
back to the prior). Baseline A keeps the raw full-window shares.

## Grid (tune seasons 2022-23 only)

| Variant | Target-share threshold | Carry-share threshold |
|---|---|---|
| base | off | off |
| ts15 | 0.15 | off |
| ts20 | 0.20 | off |
| rs35 | off | 0.35 |
| rs50 | off | 0.50 |

0.15 is the absence rule's own definition of a big target player
(reports/absence_tune.md); 0.20 is the stricter alternative. The carry
thresholds bracket a lead back's share.

## Selection rule (written before running)

- Target side: of ts15 / ts20, the one with the larger paired CRPS gain on
  receiving yards + catches summed over 2022-23, kept only if its gain is
  positive in BOTH 2022 and 2023 for both markets. Otherwise the target side is
  dropped.
- Carry side: of rs35 / rs50, the one with the larger paired CRPS gain on
  rushing yards over 2022-23, kept only if positive in both seasons. Otherwise
  dropped.
- If both sides survive, the chosen pair runs together as the candidate.

## Ship rule (written before running)

The candidate runs ONCE on 2024-25 (held out) and on 2026 weeks 2-3 (fresh).
It ships only if, against props-v1.28 on 2024-25:

1. no market (receiving yards, catches, rushing yards, QB passing, QB rushing)
   is worse with a paired 95% CI excluding zero;
2. at least one of the markets it targets improves with a CI excluding zero;
3. 2026 weeks 2-3 does not move the targeted markets the opposite way by more
   than its CI.

If 2024-25 is flat, it does not ship and this report records a measured null.

## Result (2026-10-03): measured, not shipped

Paired CRPS change against props-v1.28 on the tune seasons, positive = the
variant is better, 95% interval from resampling team-weeks.

| Variant | Season | Catches | Receiving yards | Rushing yards | QB passing |
|---|---|---|---|---|---|
| ts15 | 2022 | -0.0112 (-0.0173, -0.0055) | -0.0792 (-0.1404, -0.0182) | 0 | -0.0429 (-0.1616, +0.0788) |
| ts15 | 2023 | -0.0070 (-0.0118, -0.0023) | -0.0553 (-0.1087, +0.0013) | 0 | -0.0217 (-0.1210, +0.0709) |
| ts20 | 2022 | -0.0054 (-0.0095, -0.0011) | -0.0419 (-0.0855, -0.0012) | 0 | +0.0060 (-0.0619, +0.0768) |
| ts20 | 2023 | -0.0015 (-0.0051, +0.0019) | -0.0158 (-0.0564, +0.0231) | 0 | +0.0026 (-0.0710, +0.0770) |
| rs35 | 2022 | 0 | 0 | +0.0512 (-0.1378, +0.1992) | 0 |
| rs35 | 2023 | 0 | 0 | -0.0130 (-0.1637, +0.1158) | 0 |
| rs50 | 2022 | 0 | 0 | +0.0044 (-0.1455, +0.1265) | 0 |
| rs50 | 2023 | 0 | 0 | +0.0329 (-0.0538, +0.1221) | 0 |

QB rushing moved by under 0.02 either way in every carry variant (noise).

**Target side: dropped.** Both thresholds are worse in both seasons, ts15
clearly so. The share a receiver builds while a key teammate sits is real
evidence about his role; throwing those weeks away leans harder on the prior
and costs accuracy. This agrees with the absence rule (OUT_RULE keeps only a
quarter of an absent player's share with the priced teammates): the bump is
modest and mostly persists.

**Carry side: dropped.** By the pre-set rule rs35 (the larger summed gain,
+0.0195 vs +0.0185) is the pick, and it is negative in 2023. rs50 was positive
in both seasons but by noise-sized amounts; picking it would be a post-hoc
re-pick.

Nothing passed the tune seasons, so 2024-25 was not read and stays unspent.
One post-hoc change before any result: the harness's target share fell back to
NaN for a player with no prior, no slot prior and no co-active week (crash);
it now falls back to the mean slot prior, as the scorer's slot_val does.

Code: tag archive/props-returning-teammate. HOU week 4 (Schultz 21%) stays
priced as v1.28 prices it.

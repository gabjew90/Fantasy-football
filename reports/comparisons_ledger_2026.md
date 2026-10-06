# Comparisons ledger, 2026 season (reports/scoreboard.md, "Multiple looks")

Every candidate read against data that confirms it, by family. A family with k candidates
read on the same confirmation weeks uses 1 - 0.05 / k intervals.

| Date | Family | Candidate | Confirmation data | Read | Result |
|---|---|---|---|---|---|
| 2026-10-06 | running game | round 28 (widths incl. QB) | 2022-25 guard | once | null (QB rushing guard) |
| 2026-10-06 | running game | round 28b (backs' widths) | 2026 wk 2-4 | once | null (rushing attempts) |
| 2026-10-06 | running game | round 29 (market carries 0.5) | 2026 wk 2-4 | once | null (rushing attempts); shown as a shadow |
| 2026-10-06 | running game | 28b + 29 together | 2026 wk 2-4 | once | null |
| 2026-10-06 | widths (tier 2) | per-stage picks | 2025 | once | null (QB passing) |
| 2026-10-06 | market | pooled market fit | 2022-24 selection | -- | not selected; 2025 unread |
| 2026-10-06 | shrinkage | round 27 ypc k | 2022-24 selection | -- | 80 kept; 2025 unread |
| 2026-10-06 | volume spread | round 31 (share_conc_targets 120) | 2026 wk 2-4 | once | null (own-volume log loss -0.002 / -0.001) |
| 2026-10-06 | running game (conversion) | round 30 eff_sd_rush 0.15 | 2026 wk 2-4 | once | **ships** (99% bar on 2022-25; +0.016 on 2026) |
| 2026-10-06 | receiving conversion | round 32 (yards shape) | -- | -- | shipped shape best at selection; 2026 unread |
| 2026-10-06 | volume spread | round 33 (team_r_mult 2.5, QB passing) | -- | -- | not detectable on 2022-25 (97.5%); 2026 unread |

The running-game family has been read four times on 2026 weeks 2-4: any further
running-game candidate confirmed on those weeks uses 1 - 0.05 / 6 = 99.2% intervals.

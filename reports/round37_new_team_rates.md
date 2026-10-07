# Round 37: the new-team cap on efficiency rates (pre-registered 2026-10-06, before any run)

## Why (the second outside review)

A player on a new team has his prior-season rates capped at half weight (model.blended_rate
new_team): sensible for his SHARES (a new role), but the cap also halves the weight on his catch
rate, yards per target and yards per carry, which travel with the player more than his role does.

## What is compared

The shipped harness (the cap on all five rates; the 2022-25 run of reports/priors_active_weeks.md)
against the same harness with the cap on the two shares only (`backtest.py
--new-team-cap-rates shares`). A projection change moves the stand-in lines, so the score is the
paired whole-distribution CRPS per player-game (as for the priors fix), on receptions, receiving
yards, rushing yards, rushing + receiving and QB passing.

## Rule

- The change only touches new-team players: reported on them (the population it acts on) and on
  everyone.
- **Ships** if, on 2022-24, the new-team players' CRPS improves with a 95% game-clustered interval
  above zero on receptions or receiving yards (the rates the cap halves most often) and no bet
  market is worse by more than 0.5% on everyone; and 2025 (read once) is not worse on the
  new-team players.
- Otherwise the cap stays on all rates.

## Result (2026-10-06; props/tools/paired_crps.py, the shares-only run against the shipped run)

Paired CRPS gain (positive = shares-only better; 95% game-clustered):

| Market | New-team players 2022-24 | Everyone 2022-24 | New-team players 2025 |
|---|---|---|---|
| Receptions | -0.0004 (-0.0012, +0.0004) | -0.0001 | -0.0012 (-0.0023, -0.0000) |
| Receiving yards | +0.0010 (-0.0074, +0.0089) | +0.0005 | +0.0027 |
| Rushing yards | -0.0039 (-0.0388, +0.0315) | -0.0008 | +0.0243 |
| Rushing + receiving | -0.0028 (-0.0374, +0.0331) | -0.0004 | +0.0165 |
| QB passing | +0.0294 (-0.0066, +0.0790) | +0.0041 | +0.0051 |

(1,951 new-team receiving player-games on 2022-24.) **Null: no detectable gain on receptions or
receiving yards for the players it acts on, and receptions lean worse on 2025. The cap stays on
every rate.** Every relative change is under 0.2%: whether a moved player's catch rate and yards
per target are trusted at half or full weight barely moves a price.

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

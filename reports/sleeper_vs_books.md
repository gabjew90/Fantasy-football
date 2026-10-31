# Sleeper against the sharper books (pre-registered 2026-10-03, before any data)

## The question

Sleeper Picks posts fixed prices (mostly -125 to -130, so ~56% to break even)
on lines that can lag DraftKings and FanDuel. When Sleeper's line or price sits
off the DraftKings/FanDuel consensus, does the side the consensus favours, bet
at Sleeper's price, win more than its break-even? This does not use the
model: it asks whether Sleeper is slow, not whether we are smart.

## The evidence

- props/compare.py: one DraftKings/FanDuel snapshot per game, inside the
  capture window before kickoff (about 4 Odds API credits a game, free plan,
  never below 100 credits), in props/record/compare/<season>/wk<NN>.jsonl.
- The record now keeps Sleeper's Over and Under prices on every row
  (price_over / price_under), so either side can be graded at Sleeper's price.

## The definitions (fixed before looking)

For each settled Sleeper call in receptions, receiving yards, rushing yards
and passing yards, joined to the same week's comparison rows by player name
and market:

- consensus line = the median of DraftKings' and FanDuel's lines;
  consensus Over chance = the mean of their no-vig Over chances at that line.
- **Line off:** Sleeper's line minus the consensus line is at least 0.5
  (catches), 2.5 (receiving / rushing yards) or 5 (passing yards) in size.
  The favoured side at Sleeper is the Under when Sleeper's line is higher,
  the Over when it is lower.
- **Price off:** same line, and the consensus no-vig Over chance differs from
  Sleeper's by 3+ points. The favoured side is the one the consensus rates
  higher.
- Graded at Sleeper's own price for that side: won / lost / push, net per $100.

## The reading rule (written before any data)

The Sleeper-lag strategy counts as an edge only when, over at least 200 graded
discrepancies, net per $100 is above zero with a game-clustered 95% interval
that excludes zero. Until then the scorecard shows the running numbers and
says the sample is too small. Line-off and price-off are reported separately
and pooled.

## Amendment, 2026-10-30 (DECISIONS #252): the Sleeper line at the time of the snapshot

Made after the running numbers had been read (111 bets, +5.2 per $100), so it is a fix to a
defect, not a second look at the rule. The definitions above say "for each settled Sleeper call";
a call is the engine's last decision per pricing model, so a model that stopped running mid-week
left its Thursday line in the comparison against the books' Sunday snapshot. D'Andre Swift, week 5:
the call was 61.5, logged Thursday; the books said 83.5 on Sunday, and Sleeper itself said 83.5 at
that moment. 56 of the 111 bets compared lines taken 24 hours or more apart.

The comparison now reads Sleeper's own quote nearest the book snapshot from the line archive
(both sides of one line from one retrieval, within 15 minutes; in weeks 4-8, 1,574 of 1,903
consensus keys had one, all within 15 minutes, and the next nearest was over an hour away). One
bet per player and market; the result is the player's settled stat; a player without one is not
graded. The thresholds, the favoured side, the grading and the reading rule are unchanged.
Re-read on the record through week 7: 60 bets, 44 won (73.3%) against 65.2% to break even,
+12.1 per $100 (95% range -1.3 to +27.2); 58 of the 60 are receptions lines.

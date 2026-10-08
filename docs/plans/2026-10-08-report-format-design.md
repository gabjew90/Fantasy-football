# Report format: the user's guide for the PDF and QA versions, and a margin model behind its scenario table

*2026-10-08. Follows DECISIONS #217 (publish: one run, one checked reads file, several versions).*

## What the user decided

The user supplied `NFL_Report_Format_and_Voice_Guide.md` and answered four questions on it.

- **Scope.** The external PDF and the QA/QC version both follow the guide. The QA version adds
  the backend and the full "where the baseline could miss" table. Chat's in-conversation game
  read stays on `team_matchup_guide.md`.
- **Grouping.** Each player appears once, in the section of his main market (Passing,
  Receiving, Rushing and combined), with all his props on his card.
- **Margins.** The result-scenario table is backed by a margin model, built and tested first,
  and registered provisional. It shows "not estimated" until the model passes.
- **Verdict words.** They are defined mechanically, and "stronger language" is dropped.
  - *attainable:* at the big-gains-trimmed (luck-capped) rate, the workload needed is at or
    below the engine's projected workload.
  - *requires a rebound:* the workload needed is above his last game's.
  - *requires better gains:* only the engine's gain rate clears at the engine's workload.

## Report structure (the guide, with the review's changes)

1. **Header.** Then the three-sentence opening read.
2. **What game does the market expect?** Spread, implied points, win probability (the
   moneyline with the margin removed), total, change since opening. Then the result-scenario
   table, from the margin model below.
3. **How much passing and rushing?** Three columns: market-derived (the spread/total fit),
   engine, season. Runs include scrambles.
4. **What is each team good and bad at?** Rank, grade and score per unit. No tier ladder.
5. **Which personnel changes affect that picture?** Status, what changes, which props.
   Questionable players get both branches, using the engine's existing re-pricing.
6. **Where have opposing positions produced?** PPR allowed, plus its split into catches,
   yards and touchdowns.
7. **Close of the team brief.** Weather and venue in one line. Then two or three assumptions
   worth testing, drawn from the "where the baseline could miss" rows, and a handoff.
8. **Player sections.** Passing, then Receiving, then Rushing and combined.
   - Table A: the line, the prices, the market's and the engine's Over.
   - Above it: the engine workload and its basis.
   - Table B: the workload needed at each gain reference, with the engine's chance of reaching
     it, the market's own volume line, and the "workload consistent with the market price,
     assuming the engine's gains".
   - In the receptions-vs-yards comparison, the yards column's catch chance is labelled as only
     the catches, with the engine's Over beside it.
   - Each card closes with the guide's closing paragraph and two if-then branches.
9. **One shared reliability note.** It keeps the live record (engine log loss 0.717 vs the
   market's 0.692, DECISIONS #202).

## Data additions to run_<slug>.json (informational; prices byte-identical)

| Field | Where it comes from |
|---|---|
| Moneylines, opening spread, total and moneylines | The ESPN scoreboard the engine already reads (DraftKings close and open) |
| Workload | Market-fit attempts and runs (model's plays x pass rate), the engine's, the season's |
| Unit scores, grades and league ranks | research.unit_efficiency / unit_tiers |
| PPR allowed with its components | research.points_allowed split into catches, yards, TDs a game |
| Game-state shares | research.game_state_table's inputs |
| Questionable "if out" re-prices | run_scenarios, as data |

## The margin model (margin_buckets_v0): pre-registered before any test result is seen

**Hypothesis.** A game's final margin, given its closing spread, can be given calibrated
chances for three result scenarios:
- the favourite by 9+ ("comfortably": more than one score);
- within one score (|margin| <= 8; a tie counts here);
- the underdog by 9+.

**Data.** nflverse games.csv, regular season, closing `spread_line` (home perspective) and
`result` (home minus away).
- Fit on 2018-21 (1,040 games).
- Test on 2022-25 (1,087 games), out of sample.

**Models.**
- *A (primary), empirical residuals.* r = result - spread_line on the fit seasons. The chance of
  a scenario at spread s is the share of fitted r with s + r in it. This keeps the key numbers
  (3, 7).
- *B (comparison), normal.* Normal(s, sd of r on the fit seasons).
- *Boundary, both models (added at code review, before the test ran).* The cut sits at 8.5. A
  shifted margin exactly on it counts half to each side: a whole-number spread plus a half-point
  residual lands between a real 8 and 9. The 9-point cut is a setting
  (props/engine/resources/margin_settings.json).
- *Baseline.* Every game gets the fit seasons' overall scenario frequencies.

**Metric and pass rule, fixed now.**
1. The 3-way log loss on the test seasons must beat the baseline by at least 0.02.
2. Calibration: in each of three spread bands (|s| <= 3, 3.5-7, 7.5+), each scenario's mean
   predicted chance must sit within 4 points of its observed frequency.

**What follows from the result.**
- A ships if it passes both.
- If A fails calibration and B passes, B ships.
- If neither passes, the table prints "not estimated".

Whichever ships is registered `provisional` in core/registry.py with this test as its evidence.
It is informational: no price reads it.

**Not claimed.** Nothing about early leads, the fourth quarter or within-game timing. The
guide's "early lead" stays a labelled analytical scenario.

## Reads v2 and the checker

Reads gain section narrations, the assumptions and the handoff. Each leg gains a section
(derived from its market), its branches and a verdict word. Every number stays cited. The verdict
word is checked against its definition. New cite fields cover the data additions (game.*). The
receptions-vs-yards comparison is generated from the run, not written.

## Order of work

1. This note.
2. The margin model and its test (report in reports/).
3. The run export additions.
4. Reads v2, the checker and the QA renderer.
5. The PDF renderer.
6. The code review, then the PR.

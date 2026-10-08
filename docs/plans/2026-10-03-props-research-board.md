# Props research board (plan, 2026-10-03)

## Why

The settled record (weeks 2-3, 1,180 yardage/catch calls) says the model's
number adds nothing beside the book's: a logistic blend fits the model a weight
of +0.02 (95% -0.47 to +0.50), STRONG calls won 45.3% (n=296) at prices that
need ~56% to break even, and the book alone predicted week 3 better than the
model (log loss 0.694 vs 0.723). The board ranked lines by disagreement, which
ranks them by how likely the model is missing something. The user chose
(2026-10-03): this is a betting tool, so it becomes a RESEARCH tool -- the user
handicaps role and personnel changes, the engine supplies the numbers, and a
graded journal decides whether the process works.

## What changes for the user

1. **No bet labels on anything the user reads.** STRONG / MODERATE / LEAN /
   WEAK, EV, Kelly, stake, "take UNDER if", "size them as one bet" and
   "Bottom line" verdicts leave the report, the per-game summary, the slate
   card, `props ask` and chat. They come back only when the scorecard shows the
   model adding weight beside the book (blend weight interval above zero) for
   the current engine version. -> Tightened by DECISIONS #151 (2026-10-03): the
   gate is decided only at the reviews after weeks 8, 12 and 18, and also needs
   the top-tier yardage calls' profit at Sleeper's recorded prices wholly above
   zero on 100+ bets.
2. **Research table per line:** line and price, projection (median and
   p10-p90), model % vs book %, **line implies** (the targets or carries the
   line needs to be 50/50 vs what he is getting), and **flags**.
3. **Flags:** teammate out (with the share the engine hands on), teammate
   back, new team, questionable, and a role-shift flag (snap share moved while
   target or carry share has not, or the reverse) -- worded from what its
   2022-25 check showed.
4. **Bet journal** (`props/journal/2026.jsonl`): each bet with the four
   checklist answers (verified change, implied workload, failure case, price),
   graded by the Tuesday settle run, with its own section on the scorecard
   (record, win rate vs break-even, net per $100).

## What does not change

- Prices, projections and the simulation (the research columns are computed
  beside them; the shared RNG stream is untouched, so every p_model is
  identical).
- The prospective record: the shadow log keeps `tier`, `decision`, `gap`,
  `ER`, `model_mean`; settle and the scorecard's tier-validity table keep
  working. Tiers become internal, measured, never shown as advice.

## Milestones (each: tests, code review, plain-English summary)

1. **Role-shift check (measurement first).** On 2022-25, define the flag from
   weekly snap share and target/carry share, then ask whether flagged players
   beat or miss the shipped model's next-week projection. The result sets the
   flag's wording, or drops it.
2. **Engine research columns.** `implied_workload` (bisection on a share
   multiplier with its own common-random-number generator; receptions and
   receiving yards via a single-player `simulate_team_game`, rushing via the
   full team call with one share scaled), the flags, and per-week usage.
3. **User-facing output.** score_game report, `summary_*`, score_week slate
   card, core/props_ask.py, props/engine/SKILL.md, CHAT.md: research table, no
   bet labels. CSVs keep their columns (record continuity); a new
   `research_*.csv` carries the research table.
4. **Journal.** `props/journal.py` (add / list / grade), settle hook, props.yml
   commits `props/journal`, scorecard section, tests. Chat (read-only) prints a
   one-line journal entry the user pastes into a Claude Code session.
5. **Releases.** One engine release (props-v1.29: lock bump) and one chat
   release (nfl-v1.31). Any score_game edit changes `price_hash`, so all engine
   changes ship together; the record starts a new engine section (expected).

## Risks (told to the user in plain English)

- The role-shift flag may test as meaningless; then it is shown as plain
  usage numbers, not a flag.
- Merging pull requests is blocked for Claude by a permission check; the user
  merges, or adds a permission rule.
- Until the chat release is cut, chat shows the old board.

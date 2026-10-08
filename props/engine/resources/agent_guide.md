## 1. The system, from the repository to a reader

Repository: {REPO}. Every path below is relative to its root, at {REPO}/tree/{REF}.

```
user (chat) --> nfl-research skill (installed harness: skill/SKILL.md, skill/scripts/bootstrap.py)
                  | fetches the release nfl.lock.json names (a tag nfl-vX.Y), verifies its hash,
                  | places the credentials beside it, reads CHAT.md (routing and output rules)
                  v
                nfl.py  (one command line: status, props, fantasy, log)
                  | props game AWAY@HOME
                  v
                props/engine/scripts/score_game.py  (one game, 20,000 simulated games)
                  | reads nflverse, Sleeper Picks, ESPN, NWS (section 3); model.py, research.py,
                  | eligibility.py, td_*.py, scenario.py
                  v
                $NFL_OUT: report_<slug>.md, research_<slug>.csv, ..., run_<slug>.json
                  | chat writes reads.json (the analysis: thesis, per-leg condition / case / fails)
                  v
                props/engine/scripts/publish.py  (check the reads against the run, then render)
                  v
                <slug>_qa.md (QA/QC), <slug>_agent.md (this file), the external PDF
```

Two separate paths share the engine:
- **Chat** (the path above) is read-only: it never records, commits or pushes (CHAT.md, "Chat is
  read-only").
- **The scheduled props workflow** (.github/workflows/props.yml, every 15 minutes) is the only
  writer of the record. It captures a Thursday open, decision snapshots inside six hours of
  kickoff and the close (props/guard.py decides; score_week.py prices; props/record_run.py stamps
  each row with the engine's hash). On Tuesday it settles (props/settle.py) and rebuilds the
  scorecard (props/scorecard.py). The live record in section 5 comes from there.

Releases: a change reaches chat only as a new tag. `nfl.lock.json` pins the chat release
(skill/release.py: the file list, its sha256); `props/engine.lock.json` pins the engine tree
(props/engine_version.py) that the scheduled workflow runs. Both locks are checked in CI.

## 2. Files, tests and the two data files

| Path | Role |
|---|---|
| CHAT.md | chat's contract: routing, voice, the hard lines, the props rules |
| nfl.py | the command line chat runs; `props game` runs score_game.py, `props publish` runs publish.py |
| core/props_ask.py | chat's question tools (`props player / line / best / matchup`) over a cached run |
| props/engine/SKILL.md | the props engine's contract: the fast path, the card rules, what a read may say |
| props/engine/scripts/score_game.py | one game end to end: inputs, eligibility, shares, simulation, prices, report, run export |
| props/engine/scripts/model.py | the rate blends, depth-chart slots, the market weights, the simulation pieces |
| props/engine/scripts/research.py | everything that judges a line without moving its price: cards, volume chance, luck cap, section 1-7 tables |
| props/engine/scripts/eligibility.py | who is priced |
| props/engine/scripts/td_*.py | the anytime-touchdown model (prototype) |
| props/engine/scripts/scenario.py | user what-ifs (`--assume`), never recorded |
| props/engine/scripts/backtest.py | the 2022-25 harness the model states cite |
| props/engine/scripts/publish.py | this file's generator: the check and the renders |
| props/engine/resources/ | priors, calibration, width parameters, the methodology documents embedded below |
| DECISIONS.md | every change with its reason and evidence, numbered (#N in this file) |

**Test suites** (CI names in section 5):

| Suite | CI check | What it holds |
|---|---|---|
| props/tests | tests (props-ci.yml) | the engine and research layer, known-answer tests; also runs before every scheduled capture |
| props/tests_ci | tests (props-ci.yml) | checks that must not block a capture: end-to-end report tests, the lock match |
| tests/ | root-suite (tests.yml) | the fantasy code, the release lock (`skill/release.py check-lock`), the structural guardrails |
| backtest smoke | backtest-smoke (props-ci.yml) | on a model change: the 2022-25 backtest's CRPS printed for review |
| commit hygiene | commit-hygiene (hygiene.yml) | no per-run outputs or caches committed beside code |

**run_<slug>.json** (score_game.write_run_export, export_version 1): `slug, season, week, away,
home, kickoff_utc, hours_to_kickoff, data_cutoff, model_states, market_env {home_spread,
total_line, book, as_of}, teams {TEAM: implied_points, targets, carries, pass_td, rush_td,
td_anchor}, sources [{name, purpose, status, detail}], card_guide [lines], cards [{name, team,
slot, pos, book, quoted, rows [research rows: market, line, price_over, price_under, p_over_book,
p_over_model, p_push, median, p10, p90, market_volume, unit, ...], volume [{market, line,
volume_text, book_lines, cells {unit, need_out, proj, rows {capped|season|engine: label, rate,
rate_txt, vol, vol_txt, pct}, market_row, need_txt, need_rate, beat, note}}], usage, backfield,
prior, season, qb, watch, matchup}], who_plays {TEAM: {unit: text}}, who_note, report_state,
injuries [{team, name, pos, gsis_id, status, source, practice}], gaps [[issue, may miss,
scenario]], qb_change`.

**The reads file** (reads_version 1), written by the analyst:

```json
{"reads_version": 1, "game": "TB@DAL",
 "thesis": "the game in a paragraph; every number traced",
 "cite": [{"field": "game.teams.DAL.implied_points", "value": 29.0}],
 "notes": ["optional game-level paragraphs"],
 "legs": [{"player": "CeeDee Lamb", "market": "receptions", "side": "over", "line": 6.5,
           "condition": "his target share stays near the 49% of last game",
           "case": "why the condition could hold, from his own rows",
           "fails": "how the leg loses",
           "needs": [{"volume": 9, "rate": 0.79, "reaches": true}],
           "cite": [{"field": "market_p", "value": "50%"}, {"field": "card.usage.tn", "value": 21}],
           "injuries": [{"player": "Jonathan Mingo", "status": "Questionable"}]}]}
```

- `market`: receptions, rec yds, rush yds, rush+rec yds, pass yds (or the player_* key).
- `needs`: `volume` x `rate` (or `parts: [[volume, rate], ...]` for carries + catches), and
  whether that `reaches` floor(line) + 1. A rate must be one of the card's rows unless the need
  says `"hypothetical": true`.
- `cite.field`: market_p, engine_p, push, price_over, price_under, median, p10, p90,
  market_volume, market_catches, proj_volume, need_rate, need_out, market_line, market_line_pct,
  row.<capped|season|engine>.<pct|vol|rate>, card.<path> (into the card), game.<path> (into the
  run). A value written "50%" is compared as a percent; a plain number at the decimals written.
- `injuries.status`: the run's status (Out, Doubtful, Questionable), or "practice only".

**The checks** (publish.check): on the board at the side and line; volume x efficiency against
the whole number the Over needs; the rate's source; every cite equal to the run's number at the
precision written; every number in the prose traced to a cite, a need, the line or the game frame
(week numbers, years, ordinals and "80% range" are labels); injuries equal to section 4, and any
injured player the prose names carries an injuries entry; no pick language (a play, a lean, an
edge, value, a lock, EV, Kelly, a stake) and never "the probability". One failure renders nothing.

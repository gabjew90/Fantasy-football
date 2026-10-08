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
scenario]], qb_change`; and for the report guide (DECISIONS #218): `header [lines],
kickoff_words, weather_line, market_env {home_ml, away_ml, home_ml_open, away_ml_open,
open_home_spread, open_total, home_win_prob, home_win_prob_open}, teams {TEAM: market_throws,
market_runs, carries_history}, team_volume {TEAM: our_att, our_runs, att_avg, runs_avg,
target_rate, ...}, units {TEAM: {off_pass|off_run|def_pass|def_run: score, grade, rank, of}},
points_allowed {TEAM: {RB|WR|TE: ppr, rank_most, catches, rec_yds, rush_yds, tds}, _league,
_n, _games}, live_record {weeks, lines, engine_log_loss, market_log_loss, coin_flip, markets},
if_out [{player, team, pos, ran, moves [{player, market, side, line, p_plays, p_out, move}]}],
scenarios_market {status, book, favourite, underdog, cut, point, favourite_by_cut, within_one_score,
underdog_by_cut, prices, as_of, credits_left}` (DECISIONS #220: DraftKings' main and alternate spreads at
the cut, margin removed; status names the reason when they are missing).

**The reads file** (reads_version 2, the structure of the user's report guide), written by the
analyst:

```json
{"reads_version": 2, "game": "TB@DAL",
 "opening": "three sentences: the expected winner and scoring balance, each offense's likely route, the uncertainty that most affects opportunities",
 "market_read": "section 1's narration", "workload_read": "section 2's",
 "unit_reads": {"DAL": "the home offense's matchup read", "TB": "the away offense's"},
 "personnel": [{"player": "Baker Mayfield", "status": "Out", "changes": "the football pathway", "affects": "which props"}],
 "personnel_read": "section 4's narration", "allowed_read": "section 5's",
 "assumptions": ["two or three assumptions worth testing"],
 "handoff": "the bridge to the player sections",
 "cite": [{"field": "game.teams.DAL.implied_points", "value": 29.0}],
 "players": [{"player": "CeeDee Lamb",
              "basis": "the engine workload's basis: role, allocation, playing time, absences",
              "explanation": "the short explanation under his tables",
              "role_evidence": "completes 'The engine expects [workload], based on ...'",
              "matchup": "supports", "matchup_reason": "completes 'This matchup supports that requirement because ...'",
              "cite": [{"field": "card.usage.tn", "value": 21}],
              "legs": [{"market": "receptions", "side": "over", "line": 6.5,
                        "if": "the checkable belief: 'If you expect ...'",
                        "fails": "completes '... it stops fitting if ...'",
                        "else": "the second branch, a full sentence: 'If ..., [alternative or skip] fits better'",
                        "needs": [{"volume": 9, "rate": 0.787, "reaches": true}],
                        "cite": [{"field": "market_p", "value": "50%"}],
                        "injuries": [{"player": "Jonathan Mingo", "status": "Questionable"}]}]}]}
```

- `market`: receptions, rec yds, rush yds, rush+rec yds, pass yds (or the player_* key). Each
  player appears once, in the section of his main market (QB: Passing; WR/TE: Receiving; backs:
  Rushing and combined yards), with all his props on his card.
- `needs`: `volume` x `rate` (or `parts: [[volume, rate], ...]` for carries + catches, carries
  first), and whether that `reaches` floor(line) + 1. A rate must be one of the card's rows unless
  the need says `"hypothetical": true`; at a card rate, the card's exact rate decides.
- `cite.field`: market_p, engine_p, market_p_under, engine_p_under, push, price_over,
  price_under, median, p10, p90, market_volume, market_catches, proj_volume, need_rate, need_out,
  market_line, market_line_pct, row.<capped|season|engine>.<pct|vol|rate>, card.<path> (into the
  card), game.<path> (into the run). A value written "50%" is compared as a percent; a plain
  number at the decimals written; a chance written as a bare 0.5 is too coarse.
- `injuries.status` and `personnel.status`: the run's status (Out, Doubtful, Questionable), or
  "practice only".

**Generated, never written** (publish_render): the verdict word, the closing paragraph's computed
half (which side the market favors, the engine's workload, the workload the line needs and how
often the engine reaches it), the receptions-vs-yards comparison, the production paths and the
scenario table's status. The verdict words, by definition (the user, 2026-10-08), at the trimmed
rate (this season's for receptions):
- *requires better gains:* the need is above the engine's workload and only the engine's own rate
  clears at it;
- *requires more work than the engine expects:* no rate clears at the engine's workload;
- *requires a rebound:* the engine's workload clears, but the need is above his last game's
  (targets for receptions, carries for rushing; unknown elsewhere);
- *attainable:* the need is at or below the engine's workload, and his last game's when known.

**The checks** (publish.check):
- The leg is on the board at its side and line.
- Volume x efficiency is checked against the whole number the Over needs, at the card's exact
  rate, and the rate's source is checked.
- Every cite equals the run's number at the precision written.
- Every number in the prose traces to a cite, a need, the line or a team-brief table, with units
  kept apart. Week numbers, years, ordinals and "80% range" are labels.
- Injuries and personnel equal section 4; any injured player the prose names, last name included,
  carries an entry.
- The opening is three sentences, and two or three assumptions are given.
- A verdict word in the prose is the one the card computes.
- No pick language appears (a play, a lean, an edge, value, a lock, EV, Kelly, a stake, "take the
  Over"), and never "the probability".

One failure renders nothing.

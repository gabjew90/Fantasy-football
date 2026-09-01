# Repo rules

## League configuration (multi-league since 2026-08-29)
- `config.yaml` holds GLOBALS only (projection knobs, engine sims, paths,
  in-season manager settings). Every league fact — league_id, draft_id,
  baselines, pool sizes, guardrails, tiers knobs, tilts, verify
  expectations — lives in `leagues/<name>.yaml`.
- League selection: `--league <name>` / `DRAFTKIT_LEAGUE` / `default_league`.
  The league file deep-merges OVER globals; a missing league file is a loud
  error, never a silent fallback.
- **Omnibeta is the example league** (drafted 2026-08-23, in season). Add a
  new league with `python -m draftkit onboard <league_id>` — baselines are
  DERIVED from the league's format, never copied between leagues.
- `python -m draftkit --league <name> verify` diffs live Sleeper facts
  against the league yaml's `expected:` block and exits nonzero on mismatch.

## Engineering
- Windows host: file I/O is always `encoding="utf-8"`; console output goes
  through the UTF-8 reconfigure in cli.main.
- Tests run with `venv/Scripts/python.exe -m pytest tests -q` and must pass
  before any merge to main. Reports in `reports/` are generated artifacts.
- The in-season auto-manager (`manager/`) runs on GitHub Actions; its state
  lives in committed `state/*.json`. Delivery is GitHub Issues.
- Engine changes ship behind the validation loop in
  docs/plans/2026-08-29-draft-engine-v2-plan.md — CLV, historical sim,
  input accuracy. Self-graded boards validate nothing.

## Deadline conduct
- **When a deadline and a protocol conflict, the protocol wins and the
  feature ships late or not at all.** A missing override is a small loss; a
  stale one recorded as fresh is a corrupted record, and it silently poisons
  every later judgement that trusts it.
- `date_checked` on an override means the FACT was verified against a dated
  source on that date. Not edited, ported, or rescaled. Rows are `candidate`
  (inert) until re-verified fresh; nothing is promoted because time ran out.
- The validation harness — CLV retro, replay, three-lens scoreboard,
  byte-identical checks on informational modules, the DATA MISSING degrade
  pattern — is never cut for simplicity. It is the reason defects get caught
  cheaply, and twice it has been the harness itself that was wrong.
- Measure before cutting, not after deciding to cut. A predicted delta is not
  a measured one.

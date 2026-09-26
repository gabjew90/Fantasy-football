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
- Tests run with `venv/Scripts/python.exe -m pytest tests props/tests -q` and
  must pass before any merge to main. Reports in `reports/` are generated
  artifacts.
- **A code review after every major piece of work, before its PR merges.**
  Run the code-review skill (high) on the branch diff, report the findings,
  fix them or say why not, and re-report their outcomes. A run of small
  follow-up PRs is reviewed together at the latest when the run ends. The
  user's standing rule (2026-09-26): it is not skipped for being a "small"
  or "chat-only" change.
- The in-season auto-manager (`manager/`) has NO schedule since 2026-09-25
  (the user's call, DECISIONS #109): `weekly.yml` and `gate.yml` run only when
  dispatched by hand. `props.yml` is the only scheduled workflow.
- Engine changes ship behind the validation loop in
  docs/plans/2026-08-29-draft-engine-v2-plan.md — CLV, historical sim,
  input accuracy. Self-graded boards validate nothing.

## Architecture (consolidation since 2026-09-24)
The plan is docs/plans/2026-09-24-consolidation-plan.md. tests/test_core_guardrails.py
enforces the structural rules in CI (the fetch and scoring ratchets, registry
completeness, experiment expiry). The rest -- replace rather than add, knobs in
yaml, promotion on a measured delta -- are review rules: no test catches them,
so the PR review must.
- **One data layer.** nflverse, Sleeper, the ID map and prop lines are read
  through `core.fetch` (age-checked, recorded in a `core.manifest.Manifest`).
  Players are joined by ID through `core.ids`, never by name alone. Fantasy
  points come from `core.scoring` and the league yaml. A new module that
  fetches or scores on its own fails CI; the allowlists of old offenders may
  only shrink.
- **Every model and projection source is registered** in `core/registry.py`
  with a status (live / provisional / shadow / deprecated) and its evidence.
  No evidence, no `live`. `provisional` says why and what would validate it.
- **Improve by replacing, not adding.** A new version of a model goes in the
  same place behind the same interface, runs in `shadow`, and is promoted only
  on a measured harness delta; the old version is deleted in the promoting PR.
  A methodology overhaul starts with a short design note naming the hypothesis
  and the metric. Knobs live in yaml, so a re-tune is a config diff plus a report.
- **No parallel engines.** One-off studies go in `experiments/` (outputs
  gitignored) and are promoted or deleted within 30 days.
- **One chat skill, harness only.** `nfl-research` fetches the release that
  `nfl.lock.json` names (files defined in `skill/release.py`), places the
  credentials and reads `CHAT.md`, which holds the routing and output rules.
  A change reaches chat only with a new `nfl-v*` tag and a lock bump
  (`python skill/release.py write-lock --tag nfl-vX.Y` on the branch; after
  the merge, `python skill/release.py cut-tag` on main, which tags only a
  commit that matches the lock, then push the tag). CI checks the lock
  against its tag. The user builds the .skill (`skill/build.py`) because it
  carries their credentials; Claude Code never does.

## Record integrity
- `date_checked` on an override means the FACT was verified against a dated
  source on that date. Not edited, ported, or rescaled. Rows are `candidate`
  (inert) until re-verified fresh.
- The validation harness — CLV retro, replay, three-lens scoreboard,
  byte-identical checks on informational modules, the DATA MISSING degrade
  pattern — is never cut for simplicity. It is the reason defects get caught
  cheaply, and twice it has been the harness itself that was wrong.
- Measure before cutting, not after deciding to cut. A predicted delta is not
  a measured one.

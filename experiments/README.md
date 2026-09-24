# experiments/

One-off studies: a question asked once, answered, and either promoted or
deleted. Not a place for a second engine.

- Every module carries a line `# expires: YYYY-MM-DD`, at most 30 days out.
  `tests/test_core_guardrails.py` fails once the date passes.
- Outputs go to `experiments/out/` (gitignored). A finding worth keeping is
  written up in `reports/` or `DECISIONS.md` by the PR that acts on it.
- Data comes through `core.fetch`, like everything else; the guardrails scan
  this folder too once it holds code.
- Promotion means registering the component in `core/registry.py`, moving it
  into place behind its interface, and running it in `shadow` until a
  measured harness delta earns `live`. See
  docs/plans/2026-09-24-consolidation-plan.md, section 4.

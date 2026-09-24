"""The shared data layer: one fetch-and-cache, one ID crosswalk, one scoring
function, one snapshot manifest, one component registry. Everything that
prices a prop or evaluates a fantasy decision reads its inputs through here.
See docs/plans/2026-09-24-consolidation-plan.md."""

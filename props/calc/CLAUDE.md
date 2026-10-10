# props/calc quality rules (the user's, effective 2026-10-10)

These apply to every change under props/calc/ and to its tests. They add to the
repo-root CLAUDE.md and docs/plans/2026-10-10-parlay-leg-calculator.md.

1. **"Code review" means the built-in `/code-review` skill**, not a plugin
   skill. Say which one ran.
2. **Review per stage, after the commit** (the user, 2026-10-10; replaces the
   earlier review-before-commit rule). Commit first, so work is never unsaved.
   Then run one `/code-review` at high effort on that stage's diff. Fix crashes,
   wrong numbers, silent failures and anything that could corrupt saved data;
   list everything else for the user. At most one re-review after the fixes,
   then move on.
3. **Tests carry the load, not review.** Every numeric function has a
   known-answer test before it is used anywhere. Pinned now:
   - odds: multiplier 1.78 -> break-even 56.2%; -125 -> 55.6%
   - the brief's three sanity targets (Over 19.1 / 15.6 / 10.2), within 1
   - a hand-computed case for each rate: yards per carry, catch rate, yards per
     target with incompletions counted as zero
4. **Assertions fail loudly, never fall back silently** (`checks.DataError`,
   not `assert`, so they survive `python -O`):
   - no missing values in any rate or pool
   - no play from the priced week or later in any input
   - a matched Sleeper line belongs to the right player, team and game, or the
     leg is reported as unmatched
   - every pool and every player rate has a stated minimum sample
     (settings.yaml, fixed_not_tuned); below it the card says "not enough
     data" and shows no workload numbers for that market
5. **Sanity checks on outputs run in CI** (props/tests_ci/test_calc_sanity.py):
   league-average yards per carry, catch rate and yards per target each fall
   inside the stated plausible range (settings.yaml), and the needed workload
   rises as the line rises. The same ranges are checked at run time on the
   live pools.
6. **"Another script might be affected" is answered by the test suite.** Run
   the full props tests (`pytest tests props/tests props/tests_ci -q`) before
   each commit and report the count.
   The calculator's own tests live in props/tests_ci (run by props-ci on every
   props/ change), never in props/tests: the scheduled engine capture runs
   props/tests before each capture, and a calculator test must never be able
   to stop it (the brief: leave the engine running).
7. If the pr-review-toolkit plugin is installed, also run its silent-failure
   and test-coverage agents on changes to data loading or name matching. If it
   is not installed, say so; do not install it. (Not installed as of
   2026-10-10.)
8. **Each commit summary to the user states:** tests run and passed, review
   findings and what was done about each, and anything that could not be
   verified.

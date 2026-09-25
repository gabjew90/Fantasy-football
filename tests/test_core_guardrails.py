"""The consolidation's guardrails (docs/plans/2026-09-24-consolidation-plan.md, s4).

Structure, not judgment: these fail when a new module fetches football data or
computes fantasy points outside core/, and when the component registry is
incomplete. The allowlists are the modules that did so on 2026-09-24. They may
only SHRINK: an entry that no longer offends fails the test until it is
removed, so every cleanup is locked in by the same PR that makes it.

The patterns are heuristics over source text. They catch the shapes that
actually recurred here (a URL literal, a nflreadpy loader, a weight multiplied
into a stat); code written to dodge them will pass, which is why the review
rules in CLAUDE.md still apply.
"""

from __future__ import annotations

import re
from pathlib import Path

from core import registry

ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("draftkit", "manager", "props", "scripts", "fantasy", "experiments", "nfl.py")

# Direct reads of nflverse, Sleeper and ID-map data. core.fetch owns these.
FETCH = re.compile(
    r"load_pbp|play_by_play_|players/nfl|nflverse-data/releases|api\.sleeper\.app/projections"
    r"|/projections/nfl|lines/available|load_player_stats|stats_player_week|load_snap_counts"
    r"|load_schedules|nfldata/master/data/games|db_playerids|load_ff_playerids|load_rosters"
    r"|load_depth_charts|load_injuries")

# Re-implementations of fantasy scoring (a weight multiplied into a stat).
# core.scoring owns this. Comparisons of two scoring blocks do not match.
SCORING = re.compile(r"scoring\[k\]\)?\s*\*|scoring\.get\(k[^)]*\)\s*\*|FANTASY_BASE|def fantasy_points\b"
                     r"|s\(\"rec\"\)\s*\*")

FETCH_ALLOWED = {
    "draftkit/baselines.py", "draftkit/consensus.py", "draftkit/dataset.py", "draftkit/defense.py",
    "draftkit/external.py", "draftkit/seasondata.py", "draftkit/sleeper.py",
    "manager/consensus.py", "manager/usage.py", "manager/waiver_brief.py",
    "props/engine/scripts/absence_check.py", "props/engine/scripts/absence_tune.py",
    "props/engine/scripts/backtest.py", "props/engine/scripts/build_priors.py",
    "props/engine/scripts/score_game.py", "props/engine/scripts/td_alloc_backtest.py",
    "props/engine/scripts/td_backtest.py", "props/guard.py", "props/settle.py",
    "scripts/derive_absence_bands.py", "scripts/derive_baselines.py", "scripts/derive_bench_rates.py",
    "scripts/forward_snapshot.py", "scripts/projection_backtest.py",
}
SCORING_ALLOWED = {
    "props/engine/scripts/score_game.py",      # props adopts core last (step 6)
}


def offenders(rx: re.Pattern) -> set[str]:
    out = set()
    for top in SCANNED:
        p = ROOT / top
        files = [p] if p.is_file() else (p.rglob("*.py") if p.is_dir() else [])
        for f in files:
            rel = f.relative_to(ROOT).as_posix()
            if "/tests/" in rel:
                continue
            if rx.search(f.read_text(encoding="utf-8", errors="replace")):
                out.add(rel)
    return out


def test_no_new_module_fetches_football_data_outside_core():
    new = offenders(FETCH) - FETCH_ALLOWED
    assert not new, (f"{sorted(new)} read nflverse/Sleeper/ID data directly; go through "
                     "core.fetch instead (plan s4.1)")


def test_the_fetch_allowlist_only_shrinks():
    cleaned = FETCH_ALLOWED - offenders(FETCH)
    assert not cleaned, f"{sorted(cleaned)} no longer fetch directly; remove them from FETCH_ALLOWED"


def test_no_new_module_reimplements_fantasy_scoring():
    new = offenders(SCORING) - SCORING_ALLOWED
    assert not new, f"{sorted(new)} compute fantasy points themselves; use core.scoring"


def test_the_scoring_allowlist_only_shrinks():
    cleaned = SCORING_ALLOWED - offenders(SCORING)
    assert not cleaned, f"{sorted(cleaned)} no longer score directly; remove them from SCORING_ALLOWED"


def test_the_component_registry_is_complete():
    assert registry.problems() == []


def test_the_registry_check_catches_what_it_claims_to():
    bad = (
        registry.Component("a", "prop_model", "nope.py", "live"),
        registry.Component("a", "wrong", "core/registry.py", "provisional"),
        registry.Component("b", "projection_source", "core/registry.py", "deprecated"),
        registry.Component("c", "prop_model", "core/registry.py", "shadow", evidence=("missing.md",)),
    )
    msgs = " | ".join(registry.problems(bad))
    for needle in ("module nope.py does not exist", "live needs evidence", "registered twice",
                   "unknown kind", "provisional needs a note", "deprecated needs retire_in",
                   "evidence missing.md does not exist"):
        assert needle in msgs, needle


EXPIRES = re.compile(r"^#\s*expires:\s*(\d{4}-\d{2}-\d{2})\s*$", re.M)


def test_every_experiment_carries_an_unexpired_date():
    """experiments/ is where one-off studies live, for at most 30 days: each
    module states `# expires: YYYY-MM-DD` and is promoted (registered, moved
    into place) or deleted by then. Without the date a study becomes a
    parallel engine by default."""
    import datetime as dt
    today = dt.date.today()
    for f in sorted((ROOT / "experiments").rglob("*.py")):
        m = EXPIRES.search(f.read_text(encoding="utf-8", errors="replace"))
        rel = f.relative_to(ROOT).as_posix()
        assert m, f"{rel} has no '# expires: YYYY-MM-DD' line"
        exp = dt.date.fromisoformat(m.group(1))
        assert exp >= today, f"{rel} expired on {exp}: promote it or delete it"
        assert (exp - today).days <= 30, f"{rel} expires {exp}, more than 30 days out"


def test_every_projection_source_is_registered():
    """A module in fantasy/sources/ is a projection source; its NAME must be a
    registry entry, or it is a parallel engine nobody validated."""
    names = {c.name for c in registry.COMPONENTS}
    for f in sorted((ROOT / "fantasy" / "sources").glob("*.py")):
        if f.name == "__init__.py":
            continue
        m = re.search(r'^NAME\s*=\s*"([^"]+)"', f.read_text(encoding="utf-8"), re.M)
        rel = f.relative_to(ROOT).as_posix()
        assert m, f"{rel} has no NAME"
        assert m.group(1) in names, f"{rel} ({m.group(1)}) is not in core/registry.py"


def test_core_imports_nothing_above_it():
    """core/ is the data layer everything sits on; if it imports the league,
    manager, draft or props code, the layers stop being layers."""
    bad = re.compile(r"^\s*(from|import)\s+(draftkit|manager|fantasy|props)\b", re.M)
    for f in sorted((ROOT / "core").glob("*.py")):
        hits = bad.findall(f.read_text(encoding="utf-8"))
        assert not hits, f"core/{f.name} imports {sorted({h[1] for h in hits})}"

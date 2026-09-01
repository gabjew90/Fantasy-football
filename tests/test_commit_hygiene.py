"""Phase 1 item 4 — state/ must not ride along with code changes.

Six commits in this repo's history swept state/*.json into a feature commit,
which `git add -A` does silently.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from check_commit_hygiene import offending  # noqa: E402


def test_state_alone_is_fine():
    assert offending(["state/kv.json", "state/week_plan.json"]) == ([], [])


def test_code_alone_is_fine():
    assert offending(["draftkit/tracker.py", "tests/test_x.py"]) == ([], [])


def test_the_mix_is_refused():
    state, code = offending(["state/kv.json", "draftkit/tracker.py"])
    assert state == ["state/kv.json"]
    assert code == ["draftkit/tracker.py"]


def test_manager_code_counts_too():
    state, code = offending(["state/seen.json", "manager/age_decay.py"])
    assert state and code


def test_docs_and_reports_do_not_trip_it():
    """A state commit that also updates a generated report is not the failure
    mode; mixing state with CODE is."""
    assert offending(["state/kv.json", "reports/adp_movers.md",
                      "DECISIONS.md"]) == ([], [])


def test_windows_paths_are_normalised():
    """This runs on a Windows host; a check that passes because it was handed
    backslashes is worse than no check."""
    state, code = offending([r"state\kv.json", r"draftkit\vorp.py"])
    assert state == ["state/kv.json"]
    assert code == ["draftkit/vorp.py"]

"""Every shipped module must at least import.

This exists because manager/jobs.py sat on main with a SyntaxError -- a stray
literal newline inside an f-string -- and 515 tests passed over it. No test
imported the module, and the two workflows that do import it only run on a
schedule, so the break would have surfaced as a failed GitHub Action hours
later rather than as a red suite.

A module that no test imports is exactly the one this catches. It is
deliberately dumb: import it, that is the whole assertion.
"""

from __future__ import annotations

import importlib
import pkgutil

import pytest

PACKAGES = ("draftkit", "manager")

# Modules whose import has a side effect that does not belong in a test run
# (network, a live league fetch, argument parsing). __main__ parses argv.
SKIP = {"manager.__main__", "draftkit.__main__"}


def _modules() -> list[str]:
    out = []
    for pkg_name in PACKAGES:
        pkg = importlib.import_module(pkg_name)
        for m in pkgutil.iter_modules(pkg.__path__):
            name = f"{pkg_name}.{m.name}"
            if name not in SKIP:
                out.append(name)
    return sorted(out)


@pytest.mark.parametrize("name", _modules())
def test_module_imports(name):
    importlib.import_module(name)


def test_the_sweep_actually_covers_the_manager_package():
    """A guard on the guard: if PACKAGES or the skip list ever silences the
    package this was written for, the sweep passes while covering nothing."""
    names = _modules()
    assert "manager.jobs" in names
    assert sum(1 for n in names if n.startswith("manager.")) >= 15
    assert sum(1 for n in names if n.startswith("draftkit.")) >= 15

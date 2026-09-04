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
import sys
from pathlib import Path

import pytest

PACKAGES = ("draftkit", "manager")

# Modules whose import has a side effect that does not belong in a test run
# (network, a live league fetch, argument parsing). __main__ parses argv.
SKIP = {"manager.__main__", "draftkit.__main__"}

# scripts/ is not a package, but it is where the LIVE DRAFT PATH lives --
# bridge_server.py and yahoo_bridge.py are what run a real Yahoo room. Leaving
# it out meant the guard written for "a module no test imports" excluded the
# directory where that failure costs a missed pick rather than a late Action.
SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def _modules() -> list[str]:
    out = []
    for pkg_name in PACKAGES:
        pkg = importlib.import_module(pkg_name)
        for m in pkgutil.iter_modules(pkg.__path__):
            name = f"{pkg_name}.{m.name}"
            if name not in SKIP:
                out.append(name)
    return sorted(out)


def _scripts() -> list[str]:
    return sorted(p.stem for p in SCRIPTS.glob("*.py")
                  if not p.stem.startswith("_"))


@pytest.mark.parametrize("name", _modules())
def test_module_imports(name):
    importlib.import_module(name)


@pytest.mark.parametrize("name", _scripts())
def test_script_imports(name):
    """Same assertion, on the scripts. A script that parses argv at import
    raises SystemExit rather than failing to parse, and that is not what this
    is looking for -- a SyntaxError or a bad import is."""
    sys.path.insert(0, str(SCRIPTS))
    try:
        importlib.import_module(name)
    except SystemExit:
        pass
    finally:
        sys.path.remove(str(SCRIPTS))


def test_the_sweep_actually_covers_the_manager_package():
    """A guard on the guard: if PACKAGES or the skip list ever silences the
    package this was written for, the sweep passes while covering nothing."""
    names = _modules()
    assert "manager.jobs" in names
    assert sum(1 for n in names if n.startswith("manager.")) >= 15
    assert sum(1 for n in names if n.startswith("draftkit.")) >= 15


def test_the_sweep_actually_covers_the_live_draft_path():
    """The same guard on the scripts half: if the glob ever stops matching,
    the sweep passes while covering nothing that runs a draft."""
    names = _scripts()
    assert "bridge_server" in names
    assert "yahoo_bridge" in names
    assert len(names) >= 30

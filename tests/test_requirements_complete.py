"""Every third-party import is declared in requirements.txt.

`rapidfuzz` was a real dependency of draftkit/ids.py for months and was never
in the manifest. Nothing caught it because the local venv had it and no CI
job imported that module -- until manager/ecr.py pulled draftkit.ids into the
scheduled waiver job, which then died on the runner with
ModuleNotFoundError and delivered its traceback to the user's inbox instead
of a brief.

A missing dependency cannot be caught by any test that runs in an environment
where the dependency is installed, so this one does not try to import
anything: it parses the source for import statements and diffs the top-level
module names against the manifest.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

PKGS = ("draftkit", "manager")
ROOT = pathlib.Path(__file__).resolve().parent.parent

# import name -> distribution name, where they differ
DIST = {"yaml": "pyyaml", "dotenv": "python-dotenv", "nfl_data_py": "nfl-data-py",
        "dateutil": "python-dateutil", "PIL": "pillow", "bs4": "beautifulsoup4"}


def _declared() -> set[str]:
    out = set()
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if line:
            out.add(re.split(r"[=<>!\[]", line)[0].strip().lower().replace("_", "-"))
    return out


def _imported() -> dict[str, set[str]]:
    """top-level module -> the files that import it."""
    out: dict[str, set[str]] = {}
    for pkg in PKGS:
        for path in (ROOT / pkg).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    # level > 0 is a relative import, always first-party
                    names = [node.module] if node.module and not node.level else []
                else:
                    continue
                for n in names:
                    out.setdefault(n.split(".")[0], set()).add(
                        str(path.relative_to(ROOT)))
    return out


def test_every_third_party_import_is_in_requirements():
    declared = _declared()
    first_party = set(PKGS) | {"tests", "scripts"}
    missing = {}
    for mod, where in sorted(_imported().items()):
        if mod in sys.stdlib_module_names or mod in first_party:
            continue
        if DIST.get(mod, mod).lower().replace("_", "-") in declared:
            continue
        missing[mod] = sorted(where)
    assert not missing, (
        "third-party imports absent from requirements.txt — the scheduled "
        f"GitHub Actions jobs will die on ModuleNotFoundError: {missing}")

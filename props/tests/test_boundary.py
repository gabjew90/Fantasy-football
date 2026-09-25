"""The props subtree must stay independent of the fantasy code.

The skill it vendors owns sportsbook decisions only; draftkit and manager own
fantasy roster decisions. An import across that line would let one system's
logic leak into the other's output, which is exactly the boundary the skill
spells out. This test fails loudly rather than letting that happen quietly.
"""

from __future__ import annotations

import ast
from pathlib import Path

PROPS = Path(__file__).resolve().parents[1]
FORBIDDEN = {"draftkit", "manager"}


def _imported_roots(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            roots.add(node.module.split(".")[0])
    return roots


def test_no_fantasy_imports():
    offenders = []
    for py in PROPS.rglob("*.py"):
        if "tests" in py.parts:
            continue
        bad = _imported_roots(py) & FORBIDDEN
        if bad:
            offenders.append(f"{py.relative_to(PROPS)}: {sorted(bad)}")
    assert not offenders, "props must not import fantasy code:\n" + "\n".join(offenders)


def test_no_credential_file_vendored():
    assert not (PROPS / "engine" / "resources" / "credential.env").exists(), (
        "credential.env must not be committed to a public repo; the workflow "
        "supplies ODDS_API_KEY from repo secrets instead."
    )


def test_record_tree_present():
    for sub in ("predictions", "lines", "settled"):
        assert (PROPS / "record" / sub).is_dir(), f"record/{sub} missing"


def test_no_credential_file_anywhere_in_the_tree():
    """The narrow check above guards one path; this guards the repository.

    The engine's credential lives only in the installed skill and in a built
    .skill, never here. A key committed to a public repo is not recoverable
    by deleting it.
    """
    offenders = [p.relative_to(PROPS).as_posix() for p in PROPS.rglob("*")
                 if p.is_file() and p.name.endswith(".env")]
    assert not offenders, f"credential-shaped files in props/: {offenders}"


def test_there_is_one_chat_skill_and_it_is_not_here():
    """The props-only loader (props/skill/, props/build_skill.py) was retired
    on 2026-09-25: chat runs the one skill in skill/ (nfl-research), which
    fetches the whole release, props engine included. A second loader here
    would be a second way for chat to run an engine."""
    leftovers = [q for q in (PROPS / "skill").rglob("*")
                 if q.is_file() and "__pycache__" not in q.parts] if (PROPS / "skill").exists() else []
    assert not leftovers and not (PROPS / "build_skill.py").exists(), leftovers

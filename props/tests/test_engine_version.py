"""The engine's identity.

A record row has to say which build of the engine made the call, and the
answer has to be the same in three places that see the same code differently:
this Windows host (CRLF working tree), the Actions runner (LF), and the
installed Claude skill (LF, plus a credential file the public repo must never
hold). These tests pin the two things that make that possible -- LF
normalisation and a bytewise path sort -- and the format itself, so a later
change to the hashing cannot silently re-identify every engine ever recorded.

NOTE the deliberate absence: there is NO test here that the vendored engine
matches props/engine.lock.json. `props.yml` runs this directory before every
capture, so such an assertion would turn an unreleased engine edit into a
skipped NFL slate. It belongs on pull requests, where a human is waiting.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import engine_version as ev  # noqa: E402


def _tree(root: Path, files: dict[str, bytes]) -> Path:
    for rel, content in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(content)
    return root


SKILL = b"---\nname: nfl-prop-research\n---\nbody\n"
MODEL = b"def price():\n    return 1\n"


# ------------------------------------------------------- what the hash ignores

def test_the_hash_is_the_same_with_crlf_and_lf(tmp_path):
    """This host checks out CRLF; Actions and the installed skill are LF.
    Hashing raw bytes would give one engine two identities."""
    lf = _tree(tmp_path / "lf", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    crlf = _tree(tmp_path / "crlf", {"SKILL.md": SKILL.replace(b"\n", b"\r\n"),
                                     "scripts/model.py": MODEL.replace(b"\n", b"\r\n")})
    assert ev.tree_hash(lf) == ev.tree_hash(crlf)


def test_the_credential_and_the_caches_are_not_the_engine(tmp_path):
    """The installed skill carries resources/credential.env and the repo does
    not; they must still hash equal. Build output is not the engine either."""
    base = _tree(tmp_path / "a", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    before = ev.tree_hash(base)
    (base / "resources").mkdir(parents=True, exist_ok=True)
    (base / "resources/credential.env").write_bytes(b"ODDS_API_KEY=secret\n")
    (base / "scripts/__pycache__").mkdir(parents=True, exist_ok=True)
    (base / "scripts/__pycache__/model.cpython-311.pyc").write_bytes(b"\x00\x01")
    (base / "scripts/backtest_out").mkdir(parents=True, exist_ok=True)
    (base / "scripts/backtest_out/_frames_2025.pkl").write_bytes(b"\x80\x04")
    assert ev.tree_hash(base) == before


def test_real_changes_do_change_the_hash(tmp_path):
    base = _tree(tmp_path / "a", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    before = ev.tree_hash(base)
    (base / "scripts/model.py").write_bytes(MODEL.replace(b"return 1", b"return 2"))
    assert ev.tree_hash(base) != before, "a model edit must be a new engine"

    renamed = _tree(tmp_path / "b", {"SKILL.md": SKILL, "scripts/price.py": MODEL})
    assert ev.tree_hash(renamed) != ev.tree_hash(
        _tree(tmp_path / "c", {"SKILL.md": SKILL, "scripts/model.py": MODEL})), \
        "the path is part of the identity, not just the bytes"


# --------------------------------------------------------- what the hash fixes

def test_paths_sort_bytewise_not_the_way_windows_sorts_them(tmp_path):
    """THE BUG THIS PINS. sorted() over Path objects compares case-folded on
    Windows, which puts SKILL.md AFTER scripts/; git and POSIX put it before.
    Measured 2026-09-17: the two orders give different hashes for the same
    tree, so this host and the runner would have stamped identical code with
    two identities and the scorecard would have refused to pool it."""
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL, "resources/a.csv": b"x\n",
                                  "scripts/b.py": MODEL})
    assert [rel for rel, _ in ev.engine_files(root)] == [
        "SKILL.md", "resources/a.csv", "scripts/b.py"]


def test_the_hash_format_is_exactly_as_documented(tmp_path):
    """Recomputed inline from the documented formula. If someone changes the
    algorithm, every engine ever recorded is re-identified and the record's
    buckets stop lining up with history -- so the format is pinned here."""
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    expect = hashlib.sha256()
    for rel, blob in (("SKILL.md", SKILL), ("scripts/model.py", MODEL)):
        digest = hashlib.sha256(blob.replace(b"\r\n", b"\n")).hexdigest()
        expect.update(f"{rel}\0{digest}\n".encode("utf-8"))
    assert ev.tree_hash(root) == expect.hexdigest()
    assert ev.ALGORITHM == "props-engine-sha256-lf-1"


# ------------------------------------------------------------ the tag label

def test_the_tag_is_attached_only_when_the_hash_agrees(tmp_path):
    """A lock-sourced hash would keep claiming props-v1.0 after the engine
    changed. The hash is always computed; the lock only names it."""
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    lock = tmp_path / "engine.lock.json"
    import json
    lock.write_text(json.dumps(ev.build_lock(root, "props-v9.9")), encoding="utf-8")

    s = ev.stamp(root, lock)
    assert s["engine_hash"] == ev.tree_hash(root)
    assert s["engine_tag"] == "props-v9.9"

    (root / "scripts/model.py").write_bytes(MODEL.replace(b"1", b"2"))
    s2 = ev.stamp(root, lock)
    assert s2["engine_hash"] == ev.tree_hash(root) != s["engine_hash"]
    assert s2["engine_tag"] is None, "an edited engine must not wear the tag"


def test_a_missing_or_unreadable_lock_is_not_a_crash(tmp_path):
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL})
    assert ev.load_lock(tmp_path / "nope.json") is None
    bad = tmp_path / "bad.json"
    bad.write_text("{not json", encoding="utf-8")
    assert ev.load_lock(bad) is None
    assert ev.stamp(root, bad)["engine_tag"] is None


def test_compare_names_which_file_drifted(tmp_path):
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    lock = ev.build_lock(root, "props-v1.0")
    ok, notes = ev.compare(root, lock)
    assert ok and notes == []

    (root / "scripts/model.py").write_bytes(MODEL.replace(b"1", b"2"))
    (root / "extra.md").write_bytes(b"hi\n")
    ok, notes = ev.compare(root, lock)
    assert not ok
    assert "changed: scripts/model.py" in notes
    assert "extra: extra.md" in notes

    (root / "SKILL.md").unlink()
    _ok, notes = ev.compare(root, lock)
    assert "missing: SKILL.md" in notes


# ------------------------------------------------------------------- the CLI

def test_the_cli_prints_and_writes_and_verifies(tmp_path, capsys):
    root = _tree(tmp_path / "t", {"SKILL.md": SKILL, "scripts/model.py": MODEL})
    lock = tmp_path / "engine.lock.json"

    assert ev.main(["write-lock", "--tag", "props-v1.0",
                    "--engine-dir", str(root), "--lock", str(lock)]) == 0
    assert ev.main(["verify", "--engine-dir", str(root), "--lock", str(lock)]) == 0
    assert "IDENTICAL" in capsys.readouterr().out

    (root / "scripts/model.py").write_bytes(MODEL.replace(b"1", b"2"))
    assert ev.main(["verify", "--engine-dir", str(root), "--lock", str(lock)]) == 1
    err = capsys.readouterr().err
    assert "DRIFT" in err and "changed: scripts/model.py" in err

    assert ev.main(["verify", "--engine-dir", str(root),
                    "--expect-hash", ev.tree_hash(root)]) == 0
    assert ev.main(["print", "--engine-dir", str(root), "--json"]) == 0
    assert ev.tree_hash(root) in capsys.readouterr().out
    assert ev.main(["print", "--engine-dir", str(tmp_path / "gone")]) == 2


# --------------------------------------------------- the stdlib-only boundary

@pytest.mark.parametrize("module", ["engine_version", "persist", "guard"])
def test_the_pre_install_modules_import_no_third_party(module):
    """These run before `pip install` in Actions and in a bare chat
    container: engine_version is imported by the bootstrap, guard runs first
    in the workflow, persist is imported by both."""
    src = (PROPS / f"{module}.py").read_text(encoding="utf-8")
    for banned in ("import pandas", "import numpy", "import requests", "import scipy"):
        assert banned not in src, f"{module}.py must stay stdlib-only ({banned})"

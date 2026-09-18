"""Which engine produced a row.

`props/engine/` is a vendored copy of the nfl-prop-research skill, and until
now nothing on a record row said which build of it made the call. `git tag`
was empty, there was no version constant, and the only label -- `model_state`
from `score_game.py` -- is a hand-written per-market string that currently
says `receiving_hier_v1` for a model the registry calls v2. So two engines'
calls would have pooled into one scorecard with no way to separate them.

THE IDENTITY IS THE CONTENT, NOT A TAG. A git tag or commit sha cannot be
computed by the chat container (no git, and the installed skill is not a
checkout), Actions checks out at depth 1 with no tags, and two commits with
identical engine trees are one engine, not two. A content hash is computable
the same way everywhere with the standard library alone, and it can be
verified against a committed lock. The tag rides along as a human label, and
only when the hash agrees with the lock.

WHY LINE ENDINGS ARE NORMALISED. This host checks out CRLF
(`core.autocrlf=true`) while the index, Actions and the installed skill are
LF. Hashing raw bytes would give the same engine two identities depending on
where it was hashed.

WHY THE SORT IS BYTEWISE. `sorted()` over `Path` objects compares
case-folded on Windows, which puts `SKILL.md` AFTER `scripts/`; git and
POSIX sort bytewise, which puts it before. Measured 2026-09-17: the two
orders produce different hashes for the same tree, so Windows and Linux
would have stamped identical code with two hashes and the scorecard would
have refused to pool it. The sort key is the encoded relative path.

Stdlib only, and it must stay that way: the bootstrap imports this before
any `pip install` has run, in a container with nothing installed.

Usage:
    python props/engine_version.py print [--engine-dir D] [--json]
    python props/engine_version.py write-lock --tag props-v1.0
    python props/engine_version.py verify [--engine-dir D] [--expect-hash H]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ALGORITHM = "props-engine-sha256-lf-1"

HERE = Path(__file__).resolve().parent
ENGINE_DIR = HERE / "engine"
# Outside the engine tree on purpose: a lock inside the tree would change the
# hash it records every time it was written.
LOCK_PATH = HERE / "engine.lock.json"

# `credential.env` lives only in the installed skill -- this repo is public.
# The caches are build output. Neither is the engine.
EXCLUDE_DIRS = {"__pycache__", "backtest_out"}
EXCLUDE_SUFFIXES = {".pyc", ".pyo", ".env", ".pkl", ".tmp"}


def engine_files(root: Path) -> list[tuple[str, Path]]:
    """[(posix relative path, path)] in the one order the hash is defined on."""
    out: list[tuple[str, Path]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel_parts = path.relative_to(root).parts
        if EXCLUDE_DIRS.intersection(rel_parts):
            continue
        if path.suffix in EXCLUDE_SUFFIXES:
            continue
        out.append(("/".join(rel_parts), path))
    # THE SORT KEY IS THE ENCODED PATH. See the module docstring: sorting the
    # Path objects instead gives a different answer on Windows than on Linux.
    out.sort(key=lambda item: item[0].encode("utf-8"))
    return out


def file_digest(path: Path) -> str:
    """sha256 of the file with CRLF folded to LF."""
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def tree_hash(root: Path) -> str:
    """One hash over the whole engine: path, NUL, file digest, newline."""
    h = hashlib.sha256()
    for rel, path in engine_files(root):
        h.update(f"{rel}\0{file_digest(path)}\n".encode("utf-8"))
    return h.hexdigest()


def build_lock(root: Path, tag: str | None) -> dict:
    """The lock's content. Deterministic: no timestamps, so re-writing an
    unchanged engine produces no diff."""
    files = engine_files(root)
    return {
        "algorithm": ALGORITHM,
        "tag": tag,
        "engine_sha256": tree_hash(root),
        "file_count": len(files),
        # Per-file digests: they name WHICH file drifted, and the bootstrap
        # verifies an extracted tarball against them file by file.
        "files": {rel: file_digest(path) for rel, path in files},
    }


def load_lock(path: Path = LOCK_PATH) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def stamp(root: Path = ENGINE_DIR, lock_path: Path = LOCK_PATH) -> dict:
    """{"engine_hash", "engine_tag"} for the tree that is about to run.

    The hash is ALWAYS computed from `root`. The lock is consulted only to
    decide whether the tag label may be attached: a lock-sourced hash would
    keep claiming `props-v1.0` after the engine changed, which is the one
    lie this whole module exists to prevent.
    """
    h = tree_hash(root)
    lock = load_lock(lock_path)
    tag = lock.get("tag") if lock and lock.get("engine_sha256") == h else None
    return {"engine_hash": h, "engine_tag": tag}


def compare(root: Path, lock: dict) -> tuple[bool, list[str]]:
    """(identical, human-readable differences) against a lock."""
    have = {rel: file_digest(path) for rel, path in engine_files(root)}
    want = dict(lock.get("files") or {})
    notes = []
    for rel in sorted(set(want) - set(have)):
        notes.append(f"missing: {rel}")
    for rel in sorted(set(have) - set(want)):
        notes.append(f"extra: {rel}")
    for rel in sorted(set(have) & set(want)):
        if have[rel] != want[rel]:
            notes.append(f"changed: {rel}")
    return (tree_hash(root) == lock.get("engine_sha256") and not notes), notes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_print = sub.add_parser("print", help="the hash and tag of an engine tree")
    p_print.add_argument("--engine-dir", type=Path, default=ENGINE_DIR)
    p_print.add_argument("--json", action="store_true")

    p_write = sub.add_parser("write-lock", help="record an engine tree as a release")
    p_write.add_argument("--tag", required=True)
    p_write.add_argument("--engine-dir", type=Path, default=ENGINE_DIR)
    p_write.add_argument("--lock", type=Path, default=LOCK_PATH)

    p_ver = sub.add_parser("verify", help="IDENTICAL or DRIFT against the lock")
    p_ver.add_argument("--engine-dir", type=Path, default=ENGINE_DIR)
    p_ver.add_argument("--lock", type=Path, default=LOCK_PATH)
    p_ver.add_argument("--expect-hash", default=None,
                       help="a hash to check instead of the lock's")

    a = ap.parse_args(argv)
    root = getattr(a, "engine_dir", ENGINE_DIR)
    if not root.is_dir():
        print(f"not an engine directory: {root}", file=sys.stderr)
        return 2

    if a.cmd == "print":
        s = stamp(root, getattr(a, "lock", LOCK_PATH))
        if a.json:
            print(json.dumps(s, sort_keys=True))
        else:
            print(f"engine_hash={s['engine_hash']}")
            print(f"engine_tag={s['engine_tag'] or ''}")
            print(f"file_count={len(engine_files(root))}")
        return 0

    if a.cmd == "write-lock":
        lock = build_lock(root, a.tag)
        a.lock.write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8")
        print(f"wrote {a.lock}: tag={lock['tag']} "
              f"engine_sha256={lock['engine_sha256']} files={lock['file_count']}")
        return 0

    # verify
    if a.expect_hash:
        got = tree_hash(root)
        if got == a.expect_hash:
            print(f"IDENTICAL {got}")
            return 0
        print(f"DRIFT expected={a.expect_hash} got={got}", file=sys.stderr)
        return 1
    lock = load_lock(a.lock)
    if lock is None:
        print(f"no readable lock at {a.lock}", file=sys.stderr)
        return 2
    ok, notes = compare(root, lock)
    if ok:
        print(f"IDENTICAL {lock['engine_sha256']} ({lock.get('tag') or 'untagged'})")
        return 0
    print(f"DRIFT against {a.lock} ({lock.get('tag') or 'untagged'})", file=sys.stderr)
    for n in notes:
        print(f"  {n}", file=sys.stderr)
    print(f"  lock={lock.get('engine_sha256')} tree={tree_hash(root)}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

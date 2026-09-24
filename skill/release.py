#!/usr/bin/env python3
"""The release chat fetches: which files, their hash, and the lock that names it.

The props engine has had this since props-v1.0 (props/engine.lock.json): chat
fetches the engine at a tag and verifies it file by file. The single `nfl`
skill needs more than the engine -- the data layer, the fantasy commands, the
league loader and the league files -- so a RELEASE is the set of files below,
hashed with the same algorithm, locked in nfl.lock.json at the repo root and
tagged `nfl-vX.Y`. Merging to main changes nothing chat runs; moving the lock
does.

  python skill/release.py files                 list what a release contains
  python skill/release.py hash                  the working tree's release hash
  python skill/release.py write-lock --tag T    write nfl.lock.json for tag T
  python skill/release.py verify [--dir D]      does D match the lock?

Stdlib only: the bootstrap imports it before anything is installed.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import sys
from pathlib import Path

ALGORITHM = "nfl-release-sha256-lf-1"
REPO_ROOT = Path(__file__).resolve().parent.parent
LOCK_NAME = "nfl.lock.json"

# What a release contains: the code the `nfl` commands run and the tracked data
# they read. Not reports, state, tests, docs or the draft spreadsheets.
INCLUDE_DIRS = ("core/", "fantasy/", "draftkit/", "manager/", "props/engine/", "leagues/")
INCLUDE_FILES = ("CHAT.md", "nfl.py", "config.yaml", "requirements.txt", "tiers.csv", "tiers.keefamania.csv",
                 "data/processed/absence_bands.json")
INCLUDE_GLOBS = ("data/external/*.csv",)
EXCLUDE_PARTS = ("__pycache__", "backtest_out")
EXCLUDE_SUFFIXES = (".pyc", ".pyo", ".env", ".pkl", ".tmp", ".part")
EXCLUDE_NAMES = ("credential.env", ".env")


def included(rel: str) -> bool:
    rel = rel.replace("\\", "/")
    parts = rel.split("/")
    if any(p in EXCLUDE_PARTS for p in parts) or rel.endswith(EXCLUDE_SUFFIXES) or parts[-1] in EXCLUDE_NAMES:
        return False
    return (rel in INCLUDE_FILES or any(rel.startswith(d) for d in INCLUDE_DIRS)
            or any(fnmatch.fnmatch(rel, g) for g in INCLUDE_GLOBS))


def _tracked(root: Path) -> set[str] | None:
    """The git-tracked paths when `root` is a checkout, else None (an extracted
    release has no .git). A lock written from a working tree must describe
    what the TAG holds -- an untracked local file would never match it."""
    if not (Path(root) / ".git").exists():
        return None
    import subprocess
    r = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], capture_output=True)
    if r.returncode != 0:
        return None
    return {p for p in r.stdout.decode("utf-8").split("\0") if p}


def files(root: Path) -> list[str]:
    """Release-relative POSIX paths under `root`, sorted by their UTF-8 bytes
    (never by Path, which case-folds on Windows -- the props lock learned that).
    In a git checkout, tracked files only."""
    root = Path(root)
    tracked = _tracked(root)
    out = []
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            if included(rel) and (tracked is None or rel in tracked):
                out.append(rel)
    return sorted(out, key=lambda r: r.encode("utf-8"))


def file_digest(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def tree_hash(root: Path, rels: list[str] | None = None) -> str:
    h = hashlib.sha256()
    for rel in rels if rels is not None else files(root):
        h.update(f"{rel}\0{file_digest(Path(root) / rel)}\n".encode("utf-8"))
    return h.hexdigest()


def build_lock(root: Path, tag: str) -> dict:
    rels = files(root)
    return {"algorithm": ALGORITHM, "tag": tag, "sha256": tree_hash(root, rels), "file_count": len(rels),
            "files": {r: file_digest(Path(root) / r) for r in rels}}


def compare(root: Path, lock: dict) -> tuple[bool, list[str]]:
    """(matches, notes). A release tree must hold exactly the lock's files,
    each with the lock's digest."""
    have = set(files(root))
    want = set((lock.get("files") or {}).keys())
    notes = [f"missing: {r}" for r in sorted(want - have)[:5]] + [f"extra: {r}" for r in sorted(have - want)[:5]]
    for r in sorted(have & want):
        if file_digest(Path(root) / r) != lock["files"][r]:
            notes.append(f"changed: {r}")
            if len(notes) > 8:
                break
    ok = not notes and tree_hash(root) == lock.get("sha256")
    return ok, notes


def digests_at(ref: str, root: Path = REPO_ROOT) -> dict[str, str] | None:
    """{rel: digest} for every release file as git holds it at `ref`, or None
    when `ref` does not resolve."""
    import io
    import subprocess
    import tarfile
    git = ["git", "-C", str(root)]
    if subprocess.run([*git, "rev-parse", "-q", "--verify", f"{ref}^{{commit}}"], capture_output=True).returncode:
        return None
    names = subprocess.run([*git, "ls-tree", "-r", "--name-only", "-z", ref],
                           capture_output=True, check=True).stdout.decode("utf-8").split("\0")
    rels = [p for p in names if p and included(p)]
    blob = subprocess.run([*git, "archive", "--format=tar", ref, "--", *rels], capture_output=True, check=True).stdout
    with tarfile.open(fileobj=io.BytesIO(blob)) as tar:
        return {m.name: hashlib.sha256(tar.extractfile(m).read().replace(b"\r\n", b"\n")).hexdigest()
                for m in tar.getmembers() if m.isfile()}


def check_lock(lock: dict, root: Path = REPO_ROOT) -> tuple[bool, str]:
    """Does the release the lock names hash to what the lock says?

    The lock is checked against its TAG, not against the working tree: main
    moves ahead of the release all the time and that is fine -- chat runs the
    tag. When the tag does not exist yet (the lock is bumped in the PR and the
    tag is cut on the merge commit), HEAD stands in for it."""
    if lock.get("algorithm") != ALGORITHM:
        return False, f"lock algorithm {lock.get('algorithm')!r}, this code hashes {ALGORITHM!r}"
    tag = lock.get("tag") or ""
    if not tag:
        return False, "the lock names no tag"
    have, where = digests_at(f"refs/tags/{tag}", root), f"tag {tag}"
    if have is None:
        have, where = digests_at("HEAD", root), f"HEAD (tag {tag} not cut yet)"
    if have is None:
        return False, "neither the tag nor HEAD resolves"
    want = lock.get("files") or {}
    bad = ([f"missing: {r}" for r in sorted(set(want) - set(have))] + [f"extra: {r}" for r in sorted(set(have) - set(want))]
           + [f"changed: {r}" for r in sorted(set(want) & set(have)) if want[r] != have[r]])
    h = hashlib.sha256()
    for rel in sorted(have, key=lambda r: r.encode("utf-8")):
        h.update(f"{rel}\0{have[rel]}\n".encode("utf-8"))
    if not bad and h.hexdigest() != lock.get("sha256"):
        bad = [f"tree hash {h.hexdigest()[:12]} != lock {str(lock.get('sha256'))[:12]}"]
    if bad:
        return False, f"{where} does not match {LOCK_NAME}: " + "; ".join(bad[:6])
    return True, f"{where} matches {LOCK_NAME} ({lock['sha256'][:12]}, {len(have)} files)"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python skill/release.py")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("files")
    sub.add_parser("hash")
    w = sub.add_parser("write-lock")
    w.add_argument("--tag", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--dir", type=Path, default=REPO_ROOT)
    v.add_argument("--lock", type=Path, default=REPO_ROOT / LOCK_NAME)
    sub.add_parser("check-lock", help="CI: the lock's tag (or HEAD, before it is cut) hashes to the lock")
    a = ap.parse_args(argv)
    if a.cmd == "check-lock":
        ok, msg = check_lock(json.loads((REPO_ROOT / LOCK_NAME).read_text(encoding="utf-8")))
        print(("OK " if ok else "LOCK MISMATCH ") + msg)
        return 0 if ok else 1
    if a.cmd == "files":
        print("\n".join(files(REPO_ROOT)))
        return 0
    if a.cmd == "hash":
        print(tree_hash(REPO_ROOT))
        return 0
    if a.cmd == "write-lock":
        lock = build_lock(REPO_ROOT, a.tag)
        (REPO_ROOT / LOCK_NAME).write_text(json.dumps(lock, indent=1, sort_keys=True) + "\n", encoding="utf-8")
        print(f"wrote {LOCK_NAME}: tag={a.tag} sha256={lock['sha256']} files={lock['file_count']}")
        return 0
    lock = json.loads(Path(a.lock).read_text(encoding="utf-8"))
    ok, notes = compare(a.dir, lock)
    print(("IDENTICAL " if ok else "DRIFT ") + f"{tree_hash(a.dir)} ({lock.get('tag')})")
    for n in notes:
        print(f"  {n}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

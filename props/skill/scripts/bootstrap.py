"""Fetch the engine this repo released, and say which one ran.

THE PROBLEM THIS SOLVES. The engine used to live in two places: a skill
installed in Claude chat, and a vendored copy in the repo. The installed one
was the one being edited -- no history, no tests, no way to tell which version
produced which row of the record. This script makes the repo the only engine:
chat fetches it at a pinned tag every session, so chat, Claude Code and GitHub
Actions all run byte-identical code.

HOW IT DECIDES WHAT TO RUN, in order:
  1. Read props/engine.lock.json from `main`. It names the released tag and
     the content hash of the engine at that tag.
  2. If a previous run of this tag is already unpacked and still hashes
     correctly, reuse it. No download.
  3. Otherwise fetch the tag as one tarball from codeload.github.com, extract
     only props/engine/, and verify it file by file against the lock.
  4. Copy the local credential.env in beside it, if the install has one. The
     repo is public and never carries it.

IF ANY OF THAT FAILS IT FALLS BACK TO THE VENDORED COPY AND SAYS SO, LOUDLY,
on both streams and in the machine-readable output. An old engine beats no
engine; an old engine pretending to be the current one does not. The only
non-zero exit is when there is no engine at all.

Stdlib only: this runs before anything is installed.

Usage (from the installed skill directory):
    python scripts/bootstrap.py [--dest DIR] [--tag TAG] [--offline]
Then run the engine from the printed ENGINE_DIR, and name ENGINE_TAG and
ENGINE_SOURCE in the reply.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import tarfile
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import engine_version  # noqa: E402  (shipped beside this file)

REPO = os.environ.get("PROPS_REPO", "gabjew90/Fantasy-football")
LOCK_URL = f"https://raw.githubusercontent.com/{REPO}/main/props/engine.lock.json"
TARBALL = "https://codeload.github.com/{repo}/tar.gz/refs/tags/{tag}"
TIMEOUT = 20

VENDOR = SKILL_ROOT / "vendor" / "engine"
VENDOR_STAMP = SKILL_ROOT / "vendor" / "ENGINE_STAMP.json"
LOCAL_CREDENTIAL = SKILL_ROOT / "resources" / "credential.env"
DEFAULT_DEST = Path(os.environ.get("NFL_ENGINE_ROOT", tempfile.gettempdir())) / "nfl-prop-engine"


def _get(url: str, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "props-bootstrap"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_lock(url: str = LOCK_URL) -> dict:
    """The released tag and its hash, from main. One retry."""
    last: Exception | None = None
    for _attempt in (1, 2):
        try:
            return json.loads(_get(url).decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last = exc
    raise RuntimeError(f"lock unreadable: {last}")


def safe_members(tar: tarfile.TarFile, prefix_suffix: str = "props/engine/"):
    """Only the engine's regular files, and only from inside the archive.

    A tarball is untrusted input: an absolute path, a `..` segment or a
    symlink could write anywhere on the filesystem. Members outside
    `*/props/engine/` are skipped rather than trusted, and the relative path
    is recomputed rather than taken from the archive.
    """
    for member in tar.getmembers():
        name = member.name.replace("\\", "/")
        marker = name.find(prefix_suffix)
        if marker < 0:
            continue
        rel = name[marker + len(prefix_suffix):]
        if not rel or rel.endswith("/"):
            continue
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise RuntimeError(f"refusing a tar member outside the engine: {name}")
        if not member.isfile():          # symlinks, devices, hardlinks
            if member.issym() or member.islnk():
                raise RuntimeError(f"refusing a link in the archive: {name}")
            continue
        yield rel, member


def extract_engine(blob: bytes, dest: Path) -> int:
    """Unpack props/engine/ from a repo tarball into `dest`. Returns files."""
    dest.mkdir(parents=True, exist_ok=True)
    written = 0
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp.write(blob)
        tmp_path = Path(tmp.name)
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            for rel, member in safe_members(tar):
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                src = tar.extractfile(member)
                if src is None:
                    continue
                with target.open("wb") as fh:
                    shutil.copyfileobj(src, fh)
                written += 1
    finally:
        tmp_path.unlink(missing_ok=True)
    return written


def verify(engine_dir: Path, lock: dict) -> None:
    """Raise unless the tree is exactly what the lock describes."""
    ok, notes = engine_version.compare(engine_dir, lock)
    if not ok:
        detail = "; ".join(notes[:4]) or "hash mismatch"
        raise RuntimeError(f"hash mismatch: {detail}")


def place_credential(engine_dir: Path) -> bool:
    """Put the locally-installed credential where the engine looks for it.

    `odds_client.py` resolves `resources/credential.env` relative to the
    engine directory, so a fetched engine needs the copy the install holds.
    It is never printed, and never comes from the repo.
    """
    if not LOCAL_CREDENTIAL.is_file():
        return False
    target = engine_dir / "resources" / "credential.env"
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(LOCAL_CREDENTIAL, target)
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return True


def write_stamp(engine_dir: Path, info: dict) -> None:
    """Record what ran, BESIDE the engine rather than inside it.

    Inside, it would be part of the tree and so part of the hash: a fetched
    engine would stop matching the lock the moment it was stamped, fail
    verification on the next session and re-download every time. Keeping the
    directory byte-identical to the release also means any later tool can
    hash it without having to know about a loader's bookkeeping file.
    """
    stamp = engine_dir.with_name(engine_dir.name + ".stamp.json")
    stamp.write_text(json.dumps(info, indent=2, sort_keys=True) + "\n",
                     encoding="utf-8")


def use_vendored(dest: Path, reason: str, lock_tag: str | None) -> dict:
    """The fallback. Copied out of the install, which may be read-only."""
    if not VENDOR.is_dir():
        raise RuntimeError(f"no engine at all: {reason}; and no vendored copy "
                           f"at {VENDOR}")
    run = dest / "vendored"
    if run.exists():
        shutil.rmtree(run, ignore_errors=True)
    shutil.copytree(VENDOR, run)
    stamp = engine_version.stamp(run, VENDOR_STAMP)
    vendor_tag = None
    try:
        vendor_tag = json.loads(VENDOR_STAMP.read_text(encoding="utf-8")).get("engine_tag")
    except (OSError, ValueError):
        pass
    place_credential(run)
    info = {"engine_dir": str(run), "engine_hash": stamp["engine_hash"],
            "engine_tag": vendor_tag, "engine_source": "VENDORED_FALLBACK",
            "fallback_reason": reason, "lock_tag": lock_tag}
    write_stamp(run, info)
    return info


def resolve(dest: Path, tag: str | None = None, offline: bool = False) -> dict:
    lock: dict | None = None
    lock_tag = tag
    try:
        if offline:
            raise RuntimeError("--offline requested")
        if lock is None:
            lock = fetch_lock()
        lock_tag = tag or lock.get("tag")
        if not lock_tag:
            raise RuntimeError("the lock names no tag")
        if tag and tag != lock.get("tag"):
            # An explicitly requested tag cannot be verified against main's
            # lock, so it is fetched but not claimed as the release.
            lock = None

        run = dest / str(lock_tag)
        if lock is not None and run.is_dir():
            try:
                verify(run, lock)
                place_credential(run)
                info = {"engine_dir": str(run), "engine_hash": lock["engine_sha256"],
                        "engine_tag": lock_tag, "engine_source": "cached",
                        "fallback_reason": None, "lock_tag": lock_tag}
                write_stamp(run, info)
                return info
            except RuntimeError:
                shutil.rmtree(run, ignore_errors=True)

        partial = dest / f"{lock_tag}.partial"
        if partial.exists():
            shutil.rmtree(partial, ignore_errors=True)
        url = TARBALL.format(repo=REPO, tag=lock_tag)
        try:
            blob = _get(url, timeout=60)
        except (urllib.error.URLError, OSError) as exc:
            raise RuntimeError(f"tarball {url}: {exc}") from exc
        if not extract_engine(blob, partial):
            raise RuntimeError(f"tarball {url} held no props/engine/ files")
        if lock is not None:
            verify(partial, lock)
        if run.exists():
            shutil.rmtree(run, ignore_errors=True)
        partial.rename(run)
        place_credential(run)
        info = {"engine_dir": str(run),
                "engine_hash": engine_version.tree_hash(run),
                "engine_tag": lock_tag if lock is not None else None,
                "engine_source": "fetched", "fallback_reason": None,
                "lock_tag": lock.get("tag") if lock else None}
        write_stamp(run, info)
        return info
    except Exception as exc:  # noqa: BLE001 -- every failure falls back
        return use_vendored(dest, str(exc), lock_tag)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST,
                    help="where to unpack the engine")
    ap.add_argument("--tag", default=None,
                    help="fetch this tag instead of the one main's lock names")
    ap.add_argument("--offline", action="store_true",
                    help="use the vendored copy without touching the network")
    a = ap.parse_args(argv)

    try:
        info = resolve(a.dest, a.tag, a.offline)
    except RuntimeError as exc:
        print(f"NO ENGINE AVAILABLE: {exc}", file=sys.stderr)
        return 3

    if info["engine_source"] == "VENDORED_FALLBACK":
        banner = (f"VENDORED FALLBACK: {info['fallback_reason']}. Running the "
                  f"engine bundled with this skill"
                  + (f", not {info['lock_tag']}" if info["lock_tag"] else "")
                  + ". Say so in the reply.")
        print(banner, file=sys.stderr)
        print(banner)

    # Last lines, so a caller can read them off the end of stdout.
    print(f"ENGINE_DIR={info['engine_dir']}")
    print(f"ENGINE_TAG={info['engine_tag'] or ''}")
    print(f"ENGINE_HASH={info['engine_hash']}")
    print(f"ENGINE_SOURCE={info['engine_source']}")
    if info["fallback_reason"]:
        print(f"FALLBACK_REASON={info['fallback_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

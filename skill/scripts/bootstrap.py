"""Fetch the `nfl` release this repo published, and say which one ran.

The single chat skill for props AND fantasy (docs/plans/2026-09-24-
consolidation-plan.md, step 5). Like the props loader before it, the repo is
the only engine: chat fetches a pinned release every session, so chat, Claude
Code and GitHub Actions run byte-identical code.

HOW IT DECIDES WHAT TO RUN, in order:
  1. Read nfl.lock.json from `main`: the released tag and the content hash of
     every file in the release (skill/release.py defines the file set).
  2. If a previous run of that tag is unpacked and still verifies, reuse it.
  3. Otherwise fetch the tag as one tarball from codeload.github.com, extract
     only release files, and verify each against the lock. If the tarball host
     refuses (chat's sandbox got HTTP 403 from codeload on 2026-10-10 and ran a
     two-week-old release), fetch the lock's files one by one from
     raw.githubusercontent.com -- the host the lock itself came from -- and
     verify them the same way.
  4. Put the install's credentials beside it -- never from the public repo,
     never printed:
       resources/credential.env              -> props/engine/resources/credential.env
       resources/Yahoo_Fantasy_Connection.json -> .env (YAHOO_CLIENT_ID, _SECRET,
                                                 _REFRESH_TOKEN, _REDIRECT_URI)
  5. Check the Python libraries the commands import; install any missing.

ANY FAILURE IN 1-3 FALLS BACK TO THE VENDORED RELEASE AND SAYS SO, LOUDLY. An
old release beats none; an old release passing as current does not. The only
non-zero exit is when there is no release at all.

Stdlib only: this runs before anything is installed.

    python scripts/bootstrap.py [--dest DIR] [--tag TAG] [--offline] [--no-deps]

Last stdout lines: REPO_DIR, RELEASE_TAG, RELEASE_HASH, RELEASE_SOURCE, DEPS,
YAHOO, ODDS_KEY (and FALLBACK_REASON on the fallback path).
"""

from __future__ import annotations

import argparse
import datetime as dt
import http.client
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
# where the installed skill's vendor/ and resources/ are: this file's parent, unless an older loader
# handed over to this copy from elsewhere (harness_update) and said where it came from
SKILL_ROOT = Path(os.environ.get("NFL_SKILL_ROOT") or HERE.parent)
sys.path.insert(0, str(SKILL_ROOT))      # the repo layout: skill/release.py
sys.path.insert(0, str(HERE))           # the built skill: scripts/release.py, found first
import release  # noqa: E402

REPO = os.environ.get("NFL_REPO", "gabjew90/Fantasy-football")
LOCK_URL = f"https://raw.githubusercontent.com/{REPO}/main/{release.LOCK_NAME}"
TARBALL = "https://codeload.github.com/{repo}/tar.gz/refs/tags/{tag}"
RAW_FILE = "https://raw.githubusercontent.com/{repo}/{tag}/{path}"
RAW_MAIN = "https://raw.githubusercontent.com/{repo}/main/{path}"
TIMEOUT = 20

VENDOR_ARCHIVE = SKILL_ROOT / "vendor" / "release.tar.gz"
VENDOR_STAMP = SKILL_ROOT / "vendor" / "RELEASE_STAMP.json"
ODDS_CREDENTIAL = SKILL_ROOT / "resources" / "credential.env"
YAHOO_BUNDLE = SKILL_ROOT / "resources" / "Yahoo_Fantasy_Connection.json"
DEFAULT_DEST = Path(os.environ.get("NFL_RELEASE_ROOT", tempfile.gettempdir())) / "nfl-release"
# when setup started: an older loader that handed over to this copy passes its own start, so the
# timing covers the whole setup (DECISIONS #236)
T0 = float(os.environ.get("NFL_SETUP_T0") or time.time())

# import name -> pip name, for the libraries the commands need beyond stdlib
DEPENDENCIES = {"pandas": "pandas", "numpy": "numpy", "polars": "polars", "rapidfuzz": "rapidfuzz",
                "yaml": "PyYAML", "requests": "requests", "dotenv": "python-dotenv", "nflreadpy": "nflreadpy"}


def _get(url: str, timeout: int = TIMEOUT) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "nfl-bootstrap"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_lock(url: str = LOCK_URL) -> dict:
    last: Exception | None = None
    for _attempt in (1, 2):
        try:
            return json.loads(_get(url).decode("utf-8"))
        except (urllib.error.URLError, OSError, ValueError) as exc:
            last = exc
    raise RuntimeError(f"lock unreadable: {last}")


def safe_members(tar: tarfile.TarFile, wanted: set | None = None):
    """Release files only, from inside the archive. A tarball is untrusted: an
    absolute path, a `..` segment or a link could write anywhere, so the path
    is recomputed (the leading `<repo>-<tag>/` directory dropped) and checked.

    WHICH files: the ones the lock names (`wanted`) when there is a lock --
    not this harness's own copy of the release rules, which are frozen at the
    skill's build. A harness built at nfl-v1.0 skipped props/ask.py, the lock
    check then called it missing, and chat ran the vendored release for two
    days (DECISIONS #121). Without a lock (an unverified --tag), the rules."""
    for member in tar.getmembers():
        name = member.name.replace("\\", "/")
        if "/" not in name:
            continue
        rel = name.split("/", 1)[1]
        if not rel or rel.endswith("/"):
            continue
        if rel.startswith("/") or ".." in Path(rel).parts:
            raise RuntimeError(f"refusing a tar member outside the release: {name}")
        if not (rel in wanted if wanted is not None else release.included(rel)):
            continue
        if not member.isfile():
            if member.issym() or member.islnk():
                raise RuntimeError(f"refusing a link in the archive: {name}")
            continue
        yield rel, member


def extract_release(blob: bytes, dest: Path, wanted: set | None = None) -> int:
    dest.mkdir(parents=True, exist_ok=True)
    written = 0
    with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
        tmp.write(blob)
        tmp_path = Path(tmp.name)
    try:
        with tarfile.open(tmp_path, "r:gz") as tar:
            for rel, member in safe_members(tar, wanted):
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


def fetch_files(tag: str, lock: dict, dest: Path, workers: int = 8) -> int:
    """The release file by file from raw.githubusercontent.com at the tag, every file the lock
    names -- the route when the tarball host refuses. Paths are checked as tarball members are
    (nothing absolute, no '..'); verify() then holds each file to the lock's digest."""
    from concurrent.futures import ThreadPoolExecutor
    from urllib.parse import quote
    files = sorted(lock.get("files") or {})
    if not files:
        raise RuntimeError("the lock lists no files")
    dest.mkdir(parents=True, exist_ok=True)

    from pathlib import PurePosixPath

    def one(rel: str) -> None:
        parts = PurePosixPath(rel).parts
        # nothing absolute, no '..', no backslash, no drive ('C:/x' would discard dest on Windows)
        if (not parts or PurePosixPath(rel).is_absolute() or "\\" in rel or ".." in parts
                or any(":" in q for q in parts)):
            raise RuntimeError(f"refusing a lock path outside the release: {rel}")
        last: Exception | None = None
        for attempt in (1, 2, 3):
            try:
                data = _get(RAW_FILE.format(repo=REPO, tag=quote(tag), path=quote(rel)))
                break
            except (urllib.error.URLError, OSError, http.client.HTTPException) as exc:
                last = exc               # a truncated body (IncompleteRead) is retried too
                if attempt < 3:
                    time.sleep(attempt)
        else:
            raise RuntimeError(f"{rel}: {last}")
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(one, files))
    return len(files)


def verify(repo_dir: Path, lock: dict) -> None:
    ok, notes = release.compare(repo_dir, lock)
    if not ok:
        raise RuntimeError("hash mismatch: " + ("; ".join(notes[:4]) or "tree hash differs"))


def _private(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def place_credentials(repo_dir: Path) -> dict:
    """The install's credentials beside the release. Returns which are present
    -- never their values."""
    out = {"odds_key": False, "yahoo": False}
    if ODDS_CREDENTIAL.is_file():
        target = repo_dir / "props" / "engine" / "resources" / "credential.env"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ODDS_CREDENTIAL, target)
        _private(target)
        out["odds_key"] = True
    if YAHOO_BUNDLE.is_file():
        try:
            b = json.loads(YAHOO_BUNDLE.read_text(encoding="utf-8"))
            client, tokens = b.get("client") or {}, b.get("tokens") or {}
            env = {"YAHOO_CLIENT_ID": client.get("client_id"), "YAHOO_CLIENT_SECRET": client.get("client_secret"),
                   "YAHOO_REFRESH_TOKEN": tokens.get("refresh_token"),
                   "YAHOO_REDIRECT_URI": client.get("redirect_uri")}
            if all(env.values()):
                target = repo_dir / ".env"
                target.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8")
                _private(target)
                # The bundle is authoritative. A token file an earlier session's
                # refresh left in a cached release would otherwise win over it
                # (manager.yahoo_api reads the file before the env seed), and a
                # reinstalled bundle with a new refresh token would never be used.
                (repo_dir / "data" / "raw" / "yahoo" / "token.json").unlink(missing_ok=True)
                out["yahoo"] = True
        except (OSError, ValueError):
            pass            # an unreadable bundle is reported as absent, never echoed
    return out


def ensure_dependencies(install: bool = True) -> str:
    """'ok', or 'installed: ...', or 'missing: ...'. Unpinned installs: the
    chat container carries its own pandas/numpy, and forcing this repo's pins
    over them would be slower and riskier than using what is there."""
    missing = [pip for mod, pip in DEPENDENCIES.items() if importlib.util.find_spec(mod) is None]
    if not missing:
        return "ok"
    if not install:
        return "missing: " + ", ".join(missing)
    r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", *missing], capture_output=True, text=True)
    if r.returncode != 0 and "externally-managed" in (r.stderr + r.stdout):
        # the chat container's Python is "externally managed" (PEP 668) and
        # refuses a plain install; this is a throwaway container, so override
        r = subprocess.run([sys.executable, "-m", "pip", "install", "-q", "--break-system-packages", *missing],
                           capture_output=True, text=True)
    still = [pip for mod, pip in DEPENDENCIES.items() if importlib.util.find_spec(mod) is None]
    if r.returncode != 0 or still:
        return "missing: " + ", ".join(still or missing)
    return "installed: " + ", ".join(missing)


def harness_update(lock: dict, dest: Path, argv: list[str]) -> int | None:
    """THE LOADER UPDATES ITSELF (DECISIONS #231). The lock on main pins the harness files
    (release.HARNESS). When this copy differs, fetch the pinned files from main -- the same source
    and trust as the lock -- hold each to its digest, and run that copy with the same arguments,
    returning its exit code. None: this copy is current (or there is no pin, or it already handed
    over). Raises on any failure; the caller then keeps running this copy."""
    import hashlib
    want = (lock or {}).get("harness") or {}
    if not want or os.environ.get("NFL_HARNESS_UPDATED"):
        return None
    unknown = set(want) - set(release.HARNESS)
    if unknown:
        raise RuntimeError(f"the lock pins harness files this loader does not know: {sorted(unknown)}")
    mine = {"scripts/bootstrap.py": Path(__file__), "scripts/release.py": Path(release.__file__)}
    if all(name in want and release.file_digest(p) == want[name] for name, p in mine.items()):
        return None
    tag = hashlib.sha256("".join(want[k] for k in sorted(want)).encode("utf-8")).hexdigest()[:12]
    run = dest / f"harness-{tag}"
    for name, digest in want.items():
        target = run / name
        if target.is_file() and release.file_digest(target) == digest:
            continue                    # a reused container already holds the verified copy
        data = _get(RAW_MAIN.format(repo=REPO, path=release.HARNESS[name]))
        if hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest() != digest:
            raise RuntimeError(f"{release.HARNESS[name]} on main does not match the lock's pin")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    env = {**os.environ, "NFL_HARNESS_UPDATED": tag, "NFL_SKILL_ROOT": str(SKILL_ROOT), "NFL_SETUP_T0": repr(T0)}
    print(f"HARNESS: this loader is out of date; running the pinned one ({tag}, verified against the lock)",
          file=sys.stderr)
    return subprocess.call([sys.executable, str(run / "scripts" / "bootstrap.py"), *argv], env=env)


def write_stamp(repo_dir: Path, info: dict) -> None:
    """Beside the release, not inside it: inside it would change the hash."""
    repo_dir.with_name(repo_dir.name + ".stamp.json").write_text(
        json.dumps(info, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def use_vendored(dest: Path, reason: str, lock_tag: str | None) -> dict:
    if not VENDOR_ARCHIVE.is_file():
        raise RuntimeError(f"no release at all: {reason}; and no vendored copy at {VENDOR_ARCHIVE}")
    run = dest / "vendored"
    if run.exists():
        shutil.rmtree(run, ignore_errors=True)
    if not extract_release(VENDOR_ARCHIVE.read_bytes(), run):
        raise RuntimeError(f"no release at all: {reason}; and the vendored archive held no release files")
    stamp = {}
    try:
        stamp = json.loads(VENDOR_STAMP.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    got = release.tree_hash(run)
    tag = stamp.get("tag") if stamp.get("sha256") == got else None   # a tag is claimed only on a match
    if tag is None:
        reason += f"; the vendored copy does not match its stamp either ({got[:12]})"
    return {"repo_dir": str(run), "release_hash": got, "release_tag": tag,
            "release_source": "VENDORED_FALLBACK", "fallback_reason": reason, "lock_tag": lock_tag}


def resolve(dest: Path, tag: str | None = None, offline: bool = False) -> dict:
    lock, lock_tag = None, tag
    try:
        if offline:
            raise RuntimeError("--offline requested")
        lock = fetch_lock()
        lock_tag = tag or lock.get("tag")
        if not lock_tag:
            raise RuntimeError("the lock names no tag")
        if tag and tag != lock.get("tag"):
            lock = None                 # an explicit other tag is fetched, not claimed as the release
        run = dest / str(lock_tag)
        if lock is not None and run.is_dir():
            try:
                verify(run, lock)
                return {"repo_dir": str(run), "release_hash": lock["sha256"], "release_tag": lock_tag,
                        "release_source": "cached", "fallback_reason": None, "lock_tag": lock_tag}
            except RuntimeError:
                shutil.rmtree(run, ignore_errors=True)
        partial = dest / f"{lock_tag}.partial"
        if partial.exists():
            shutil.rmtree(partial, ignore_errors=True)
        url = TARBALL.format(repo=REPO, tag=lock_tag)
        route = "tarball"
        try:
            blob = _get(url, timeout=90)
        except (urllib.error.URLError, OSError) as exc:
            if lock is None:            # no file list to fetch by: an unverified --tag needs the tarball
                raise RuntimeError(f"tarball {url}: {exc}") from exc
            try:
                fetch_files(str(lock_tag), lock, partial)
            except Exception as exc2:   # noqa: BLE001 -- both routes failed: the vendored copy runs
                raise RuntimeError(f"tarball {url}: {exc}; file by file: {exc2}") from exc2
            route = f"file by file (the tarball host refused: {exc})"
        else:
            if not extract_release(blob, partial, set((lock or {}).get("files") or {}) or None):
                raise RuntimeError(f"tarball {url} held no release files")
        if lock is not None:
            verify(partial, lock)
        if run.exists():
            shutil.rmtree(run, ignore_errors=True)
        partial.rename(run)
        return {"repo_dir": str(run), "release_hash": release.tree_hash(run),
                "release_tag": lock_tag if lock is not None else None,
                "release_source": "fetched" if lock is not None else "fetched-unverified",
                "fallback_reason": None, "lock_tag": lock.get("tag") if lock else None, "fetch_route": route}
    except Exception as exc:  # noqa: BLE001 -- every failure falls back
        return use_vendored(dest, str(exc), lock_tag)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dest", type=Path, default=DEFAULT_DEST)
    ap.add_argument("--tag", default=None)
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--no-deps", action="store_true", help="report missing libraries, do not install them")
    a = ap.parse_args(argv)
    if not a.offline:
        try:
            code = harness_update(fetch_lock(), a.dest, list(sys.argv[1:] if argv is None else argv))
            if code is not None:
                return code
        except Exception as exc:  # noqa: BLE001 -- an update failure never costs the session
            print(f"HARNESS: kept this loader (the update failed: {exc})", file=sys.stderr)
    try:
        info = resolve(a.dest, a.tag, a.offline)
    except RuntimeError as exc:
        print(f"NO RELEASE AVAILABLE: {exc}", file=sys.stderr)
        return 3
    repo_dir = Path(info["repo_dir"])
    creds = place_credentials(repo_dir)
    deps = ensure_dependencies(install=not a.no_deps)
    info.update(deps=deps, **creds)
    # the session log's first step (nfl.py reads it from the stamp)
    info["setup_seconds"] = round(time.time() - T0, 1)
    info["setup_started_utc"] = dt.datetime.fromtimestamp(T0, dt.timezone.utc).isoformat(timespec="milliseconds")
    write_stamp(repo_dir, info)
    if info["release_source"] == "VENDORED_FALLBACK":
        banner = (f"VENDORED FALLBACK: {info['fallback_reason']}. Running the release bundled with this "
                  "skill" + (f", not {info['lock_tag']}" if info["lock_tag"] else "") + ". Say so in the reply.")
        print(banner, file=sys.stderr)
        print(banner)
    print(f"REPO_DIR={info['repo_dir']}")
    print(f"RELEASE_TAG={info['release_tag'] or ''}")
    print(f"RELEASE_HASH={info['release_hash']}")
    print(f"RELEASE_SOURCE={info['release_source']}")
    print(f"DEPS={deps}")
    print(f"YAHOO={'live' if creds['yahoo'] else 'absent (no Yahoo bundle in this skill: Keefamania cannot be read)'}")
    print(f"ODDS_KEY={'present' if creds['odds_key'] else 'absent (Sleeper prices only)'}")
    print(f"HARNESS={'updated ' + os.environ['NFL_HARNESS_UPDATED'] if os.environ.get('NFL_HARNESS_UPDATED') else 'current'}")
    print(f"SETUP_SECONDS={info['setup_seconds']}")
    if info.get("fetch_route") and info["fetch_route"] != "tarball":
        print(f"FETCH_ROUTE={info['fetch_route']}")
    if info["fallback_reason"]:
        print(f"FALLBACK_REASON={info['fallback_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

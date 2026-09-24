"""Assemble the installable `nfl-research` skill. The user runs this.

    nfl-research/
      SKILL.md                                skill/SKILL.md
      scripts/bootstrap.py                    skill/scripts/bootstrap.py
      scripts/release.py                      skill/release.py (the hash spec)
      vendor/release.tar.gz                   the release at the locked tag, archived
      vendor/RELEASE_STAMP.json               what the fallback is
      resources/credential.env                ONLY from --credential
      resources/Yahoo_Fantasy_Connection.json ONLY from --yahoo

THE FALLBACK IS AN ARCHIVE, NOT A TREE: the uploader accepts exactly one
SKILL.md per package and the release carries the props engine's own.

CREDENTIALS ARE NEVER SOURCED FROM THE TREE. This repo is public. A credential
path that resolves inside it is refused, and the built file is a secret: it
carries the Odds API key and the Yahoo refresh token, so it is never attached
anywhere, and Claude Code never builds it -- the user does.

    python skill/build.py --out dist/nfl-research.skill \
        --credential "C:/.../skills/nfl-prop-research/resources/credential.env" \
        --yahoo "C:/.../skills/nfl-fantasy-research/resources/Yahoo_Fantasy_Connection.json"
"""

from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

SKILL = Path(__file__).resolve().parent
REPO = SKILL.parent
SKILL_NAME = "nfl-research"
sys.path.insert(0, str(SKILL))
sys.path.insert(0, str(SKILL / "scripts"))
import release  # noqa: E402
import bootstrap  # noqa: E402


def _git(*args: str, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=REPO, check=True, capture_output=True, **kw)


def release_archive(lock: dict, out: Path) -> str:
    """The lock's files as the tag holds them, as a .tar.gz under `release/`
    (codeload's layout, so the bootstrap extracts both the same way).

    THE TAG MAY NOT EXIST YET: the lock is bumped in the same PR as the change
    and the tag is cut on the merge commit. Then HEAD is archived instead; the
    caller hashes what came out against the lock and refuses a mismatch, so
    this cannot vendor the wrong release."""
    ref = f"refs/tags/{lock['tag']}"
    got = release.contents_at(ref, REPO)
    if got is None:
        ref, got = "HEAD", release.contents_at("HEAD", REPO)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out, "w:gz") as tar:
        for rel in sorted(got):
            info = tarfile.TarInfo(f"release/{rel}")
            info.size = len(got[rel])
            tar.addfile(info, io.BytesIO(got[rel]))
    return ref


def _outside_repo(p: Path | None, what: str) -> Path | None:
    if p is None:
        return None
    p = p.resolve()
    if not p.is_file():
        raise SystemExit(f"no {what} file at {p}")
    try:
        p.relative_to(REPO)
    except ValueError:
        return p
    raise SystemExit(f"REFUSING a {what} inside the repository ({p}). This repo is public; "
                     "keep credentials in the installed skill only.")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "dist" / f"{SKILL_NAME}.skill")
    ap.add_argument("--credential", type=Path, help="the Odds API credential.env, OUTSIDE this repo")
    ap.add_argument("--yahoo", type=Path, help="Yahoo_Fantasy_Connection.json, OUTSIDE this repo")
    a = ap.parse_args(argv)
    cred = _outside_repo(a.credential, "credential")
    yahoo = _outside_repo(a.yahoo, "Yahoo bundle")

    lock_path = REPO / release.LOCK_NAME
    if not lock_path.is_file():
        print(f"no {release.LOCK_NAME}; run skill/release.py write-lock first", file=sys.stderr)
        return 2
    lock = json.loads(lock_path.read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / SKILL_NAME
        (stage / "scripts").mkdir(parents=True)
        shutil.copyfile(SKILL / "SKILL.md", stage / "SKILL.md")
        shutil.copyfile(SKILL / "scripts" / "bootstrap.py", stage / "scripts" / "bootstrap.py")
        shutil.copyfile(SKILL / "release.py", stage / "scripts" / "release.py")

        archive = stage / "vendor" / "release.tar.gz"
        ref = release_archive(lock, archive)
        # Verify THE FILE BEING SHIPPED, unpacked the way the bootstrap will.
        check = Path(tmp) / "check"
        bootstrap.extract_release(archive.read_bytes(), check)
        ok, notes = release.compare(check, lock)
        if not ok:
            print(f"the vendored release ({ref}) does not match the lock: {'; '.join(notes[:4])}. "
                  "Pull main and fetch tags (git pull --tags), then build again.", file=sys.stderr)
            return 1
        commit = _git("rev-parse", ref, text=True).stdout.strip()
        (stage / "vendor" / "RELEASE_STAMP.json").write_text(
            json.dumps({"tag": lock["tag"], "sha256": lock["sha256"], "algorithm": release.ALGORITHM,
                        "built_from": ref, "commit": commit}, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

        if cred or yahoo:
            (stage / "resources").mkdir(parents=True)
        if cred:
            shutil.copyfile(cred, stage / "resources" / "credential.env")
        if yahoo:
            shutil.copyfile(yahoo, stage / "resources" / "Yahoo_Fantasy_Connection.json")

        a.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    z.write(path, f"{SKILL_NAME}/{path.relative_to(stage).as_posix()}")
            names = z.namelist()

    print(f"wrote {a.out} ({a.out.stat().st_size // 1024} KiB, {len(names)} files)")
    print(f"  release {lock['tag']} {lock['sha256'][:12]} vendored from {ref}")
    print(f"  Odds API key: {'included' if cred else 'NOT included (Sleeper prices only)'}")
    print(f"  Yahoo bundle: {'included' if yahoo else 'NOT included (no Keefamania from chat)'}")
    if cred or yahoo:
        print("  this file carries credentials; treat it as a secret")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

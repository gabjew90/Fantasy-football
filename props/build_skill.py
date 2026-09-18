"""Assemble the installable loader skill.

The skill that gets installed in Claude is a thin loader plus a vendored copy
of the released engine as a fallback. This builds it from the repo, so the
repo stays the only source of truth:

    nfl-prop-research/
      SKILL.md                    props/skill/SKILL.md
      scripts/bootstrap.py        props/skill/scripts/bootstrap.py
      scripts/engine_version.py   props/engine_version.py  (the hash spec)
      engine.lock.json            props/engine.lock.json
      vendor/engine.tar.gz        props/engine at the locked tag, archived
      vendor/ENGINE_STAMP.json    what the fallback is
      resources/credential.env    ONLY from --credential, never from the repo

THE FALLBACK IS AN ARCHIVE, NOT A TREE. The uploader requires exactly one
SKILL.md in the package and the engine carries its own, so a vendored tree
put two in the zip and the upload was refused. Archiving it also lets the
bootstrap run one extraction-and-verify routine for both the fetched and the
vendored engine.

THE CREDENTIAL IS NEVER SOURCED FROM THE TREE. This repo is public. A
`--credential` path that resolves inside the repo is refused, and the built
file is a secret: it carries the API key, so the .skill itself must not be
attached anywhere public.

Usage:
    python props/build_skill.py --out dist/nfl-prop-research.skill \
        [--credential "C:/.../skills/nfl-prop-research/resources/credential.env"]
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PROPS = Path(__file__).resolve().parent
REPO = PROPS.parent
SKILL_SRC = PROPS / "skill"
SKILL_NAME = "nfl-prop-research"


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, check=True,
                          capture_output=True, text=True).stdout


def engine_archive_at_tag(tag: str, out: Path) -> Path:
    """props/engine as the tag has it, as a .tar.gz with props/engine/ members.

    git archive exports the index, so this is the LF content every other copy
    hashes -- never the CRLF working tree. The member layout matches what
    codeload returns, so bootstrap.extract_engine handles both.
    """
    out.parent.mkdir(parents=True, exist_ok=True)
    # THE TAG MAY NOT EXIST YET. The lock is bumped in the same PR as the
    # engine change -- it has to be, or props-ci's lock check is red on every
    # engine PR -- so between opening that PR and cutting the tag on the merge
    # commit, the lock names a ref git cannot resolve. Fall back to HEAD, whose
    # engine tree is the one the lock was just computed from.
    #
    # This cannot smuggle in the wrong engine: main() hashes whatever comes out
    # of here against lock["engine_sha256"] and refuses on a mismatch. The tag
    # is the preferred source because it is immutable, not because it is the
    # only trustworthy one.
    ref, why = tag, ""
    if subprocess.run(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"],
                      cwd=REPO, capture_output=True).returncode != 0:
        ref, why = "HEAD", f" (tag {tag} not cut yet; built from HEAD)"
        print(f"note: {tag} does not exist; vendoring the engine at HEAD instead. "
              f"The hash check below is what makes this safe.", file=sys.stderr)
    with out.open("wb") as fh:
        subprocess.run(["git", "archive", "--format=tar.gz", ref, "props/engine"],
                       cwd=REPO, check=True, stdout=fh)
    if why:
        print(f"vendored engine source: {ref}{why}", file=sys.stderr)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=REPO / "dist" / f"{SKILL_NAME}.skill")
    ap.add_argument("--credential", type=Path, default=None,
                    help="path to a credential.env OUTSIDE this repo")
    ap.add_argument("--tag", default=None, help="default: the lock's tag")
    a = ap.parse_args(argv)

    sys.path.insert(0, str(PROPS))
    import engine_version

    lock = engine_version.load_lock()
    if lock is None:
        print("no props/engine.lock.json; run engine_version.py write-lock first",
              file=sys.stderr)
        return 2
    tag = a.tag or lock.get("tag")
    if not tag:
        print("the lock names no tag", file=sys.stderr)
        return 2

    if a.credential is not None:
        cred = a.credential.resolve()
        if not cred.is_file():
            print(f"no credential file at {cred}", file=sys.stderr)
            return 2
        try:
            cred.relative_to(REPO)
        except ValueError:
            pass
        else:
            print(f"REFUSING a credential inside the repository ({cred}). This "
                  f"repo is public; keep the key in the installed skill only.",
                  file=sys.stderr)
            return 2
    else:
        cred = None

    with tempfile.TemporaryDirectory() as tmp:
        stage = Path(tmp) / SKILL_NAME
        (stage / "scripts").mkdir(parents=True)
        (stage / "vendor").mkdir(parents=True)

        shutil.copyfile(SKILL_SRC / "SKILL.md", stage / "SKILL.md")
        shutil.copyfile(SKILL_SRC / "scripts" / "bootstrap.py",
                        stage / "scripts" / "bootstrap.py")
        shutil.copyfile(PROPS / "engine_version.py",
                        stage / "scripts" / "engine_version.py")
        shutil.copyfile(PROPS / "engine.lock.json", stage / "engine.lock.json")

        archive = engine_archive_at_tag(tag, stage / "vendor" / "engine.tar.gz")

        # Verify THE FILE BEING SHIPPED, by unpacking it the way the bootstrap
        # will: a fallback nobody checked is a fallback that can be wrong
        # exactly when it is needed. This used to re-export the tag into a
        # second tarball and hash that, which checked a different artifact than
        # the one in the zip and resolved the ref twice -- so the archive could
        # in principle differ from what was verified.
        check = Path(tmp) / "check"
        check.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(str(archive), str(check), format="gztar")
        vendored_hash = engine_version.tree_hash(check / "props" / "engine")
        if vendored_hash != lock["engine_sha256"]:
            print(f"the vendored engine does not match the lock "
                  f"({vendored_hash[:12]} vs {lock['engine_sha256'][:12]})",
                  file=sys.stderr)
            return 1
        (stage / "vendor" / "ENGINE_STAMP.json").write_text(
            json.dumps({"engine_tag": tag, "engine_hash": vendored_hash,
                        "algorithm": engine_version.ALGORITHM,
                        "built_from_commit": _git("rev-parse", "HEAD").strip()},
                       indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if cred is not None:
            (stage / "resources").mkdir(parents=True, exist_ok=True)
            shutil.copyfile(cred, stage / "resources" / "credential.env")

        a.out.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(a.out, "w", zipfile.ZIP_DEFLATED) as z:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    z.write(path, f"{SKILL_NAME}/{path.relative_to(stage).as_posix()}")
            names = z.namelist()

    print(f"wrote {a.out} ({a.out.stat().st_size // 1024} KiB, {len(names)} files)")
    print(f"  engine {tag} {vendored_hash[:12]} vendored as the fallback")
    print(f"  credential: {'included' if cred else 'NOT included'}")
    if cred:
        print("  this file carries an API key; treat it as a secret")
    for name in names:
        if name.endswith("credential.env"):
            continue
        print(f"    {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

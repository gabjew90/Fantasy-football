"""Assemble the installable loader skill.

The skill that gets installed in Claude is a thin loader plus a vendored copy
of the released engine as a fallback. This builds it from the repo, so the
repo stays the only source of truth:

    nfl-prop-research/
      SKILL.md                    props/skill/SKILL.md
      scripts/bootstrap.py        props/skill/scripts/bootstrap.py
      scripts/engine_version.py   props/engine_version.py  (the hash spec)
      engine.lock.json            props/engine.lock.json
      vendor/engine/**            props/engine at the locked tag
      vendor/ENGINE_STAMP.json    what the fallback is
      resources/credential.env    ONLY from --credential, never from the repo

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


def engine_at_tag(tag: str, dest: Path) -> Path:
    """props/engine as the tag has it, exported with git (no working-tree CRLF)."""
    dest.mkdir(parents=True, exist_ok=True)
    tar = dest / "engine.tar"
    with tar.open("wb") as fh:
        subprocess.run(["git", "archive", "--format=tar", tag, "props/engine"],
                       cwd=REPO, check=True, stdout=fh)
    shutil.unpack_archive(str(tar), str(dest), format="tar")
    tar.unlink()
    return dest / "props" / "engine"


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

        engine = engine_at_tag(tag, Path(tmp) / "export")
        shutil.copytree(engine, stage / "vendor" / "engine")

        vendored_hash = engine_version.tree_hash(stage / "vendor" / "engine")
        if vendored_hash != lock["engine_sha256"]:
            print(f"the engine at {tag} does not match the lock "
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

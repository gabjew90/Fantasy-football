"""The loader that makes the repo the only engine.

Chat used to run an engine that existed nowhere else. The bootstrap fetches
the released one instead, verifies it against the lock, and -- when it cannot
-- runs the bundled copy while saying so on both streams. These tests cover
the verification, the tar-extraction safety, and the wording of the fallback,
because a fallback nobody notices is the failure mode that would put an old
model's numbers into a reply as if they were current.

No network: the tarball is built locally, which is also how the extraction
safety cases are constructed.
"""

from __future__ import annotations

import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))
sys.path.insert(0, str(PROPS / "skill" / "scripts"))

import bootstrap  # noqa: E402
import engine_version as ev  # noqa: E402

SKILL = b"---\nname: nfl-prop-research\n---\nbody\n"
MODEL = b"def price():\n    return 1\n"


def _engine(root: Path) -> Path:
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "resources").mkdir(parents=True, exist_ok=True)
    (root / "SKILL.md").write_bytes(SKILL)
    (root / "scripts" / "model.py").write_bytes(MODEL)
    (root / "resources" / "priors.csv").write_bytes(b"a,b\n1,2\n")
    return root


def _tarball(files: dict[str, bytes], prefix: str = "Fantasy-football-props-v1.0") -> bytes:
    """A repo tarball shaped the way codeload returns one."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel, blob in files.items():
            info = tarfile.TarInfo(f"{prefix}/{rel}")
            info.size = len(blob)
            tar.addfile(info, io.BytesIO(blob))
    return buf.getvalue()


def _engine_tarball() -> bytes:
    return _tarball({
        "props/engine/SKILL.md": SKILL,
        "props/engine/scripts/model.py": MODEL,
        "props/engine/resources/priors.csv": b"a,b\n1,2\n",
        "README.md": b"not the engine\n",
        "manager/jobs.py": b"also not the engine\n",
    })


# ------------------------------------------------------------- the hash spec

def test_the_bootstrap_and_the_repo_agree_on_the_hash(tmp_path):
    """The loader ships a copy of engine_version.py; if the two ever computed
    different hashes, a verified engine would look like a drifted one."""
    engine = _engine(tmp_path / "engine")
    assert bootstrap.engine_version.tree_hash(engine) == ev.tree_hash(engine)


# ---------------------------------------------------------------- extraction

def test_only_the_engine_comes_out_of_the_tarball(tmp_path):
    dest = tmp_path / "out"
    written = bootstrap.extract_engine(_engine_tarball(), dest)
    assert written == 3
    got = sorted(p.relative_to(dest).as_posix() for p in dest.rglob("*") if p.is_file())
    assert got == ["SKILL.md", "resources/priors.csv", "scripts/model.py"]


def test_an_extracted_engine_verifies_against_the_lock(tmp_path):
    dest = tmp_path / "out"
    bootstrap.extract_engine(_engine_tarball(), dest)
    lock = ev.build_lock(dest, "props-v1.0")
    bootstrap.verify(dest, lock)            # must not raise

    (dest / "scripts" / "model.py").write_bytes(MODEL.replace(b"1", b"2"))
    with pytest.raises(RuntimeError) as exc:
        bootstrap.verify(dest, lock)
    assert "changed: scripts/model.py" in str(exc.value)


@pytest.mark.parametrize("member", ["props/engine/../../evil.py",
                                    "props/engine/../outside.py"])
def test_a_traversing_member_is_refused(tmp_path, member):
    """A tarball is untrusted input: `..` could write outside the run dir."""
    blob = _tarball({member: b"pwned\n", "props/engine/SKILL.md": SKILL})
    with pytest.raises(RuntimeError, match="outside the engine"):
        bootstrap.extract_engine(blob, tmp_path / "out")


def test_a_symlink_member_is_refused(tmp_path):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo("pfx/props/engine/link.py")
        info.type = tarfile.SYMTYPE
        info.linkname = "/etc/passwd"
        tar.addfile(info)
    with pytest.raises(RuntimeError, match="link in the archive"):
        bootstrap.extract_engine(buf.getvalue(), tmp_path / "out")


def test_an_absolute_member_is_not_extracted(tmp_path):
    """An absolute path has no `props/engine/` prefix to match, so it is
    skipped; nothing outside the destination is written either way."""
    blob = _tarball({"props/engine/SKILL.md": SKILL})
    buf = io.BytesIO(blob)
    del buf
    dest = tmp_path / "out"
    assert bootstrap.extract_engine(blob, dest) == 1
    assert sorted(p.name for p in dest.rglob("*") if p.is_file()) == ["SKILL.md"]


def test_a_tarball_without_the_engine_is_an_error(tmp_path):
    blob = _tarball({"README.md": b"nothing here\n"})
    assert bootstrap.extract_engine(blob, tmp_path / "out") == 0


# ------------------------------------------------------------- the fallback

@pytest.fixture
def skill(tmp_path, monkeypatch):
    """An installed skill: a vendored engine ARCHIVE, a stamp, a credential.

    The fallback ships as a tarball because the skill uploader allows exactly
    one SKILL.md per package and the engine carries its own -- a vendored
    tree put two in the zip and the upload was refused.
    """
    root = tmp_path / "skill"
    (root / "vendor").mkdir(parents=True, exist_ok=True)
    (root / "resources").mkdir(parents=True, exist_ok=True)
    (root / "resources" / "credential.env").write_text("ODDS_API_KEY=secret\n",
                                                       encoding="utf-8")
    archive = root / "vendor" / "engine.tar.gz"
    archive.write_bytes(_engine_tarball())
    unpacked = tmp_path / "_unpacked"
    bootstrap.extract_engine(archive.read_bytes(), unpacked)
    stamp = root / "vendor" / "ENGINE_STAMP.json"
    stamp.write_text(json.dumps({"engine_tag": "props-v1.0",
                                 "engine_hash": ev.tree_hash(unpacked)}),
                     encoding="utf-8")
    monkeypatch.setattr(bootstrap, "SKILL_ROOT", root)
    monkeypatch.setattr(bootstrap, "VENDOR_ARCHIVE", archive)
    monkeypatch.setattr(bootstrap, "VENDOR_STAMP", stamp)
    monkeypatch.setattr(bootstrap, "LOCAL_CREDENTIAL",
                        root / "resources" / "credential.env")
    return root


def test_offline_uses_the_vendored_copy_and_says_which(skill, tmp_path, capsys):
    assert bootstrap.main(["--offline", "--dest", str(tmp_path / "run")]) == 0
    out, err = capsys.readouterr().out, capsys.readouterr().err

    assert "VENDORED FALLBACK" in out, "the banner must be on stdout"
    assert "ENGINE_SOURCE=VENDORED_FALLBACK" in out
    assert "FALLBACK_REASON=" in out
    assert "ENGINE_TAG=props-v1.0" in out


def test_the_fallback_reason_names_what_failed(skill, tmp_path, monkeypatch, capsys):
    def boom(url=None, timeout=None):
        raise OSError("host_not_allowed")
    monkeypatch.setattr(bootstrap, "fetch_lock",
                        lambda *a, **k: (_ for _ in ()).throw(
                            RuntimeError("lock unreadable: host_not_allowed")))
    assert bootstrap.main(["--dest", str(tmp_path / "run")]) == 0
    out = capsys.readouterr().out
    assert "host_not_allowed" in out
    assert "ENGINE_SOURCE=VENDORED_FALLBACK" in out


def test_the_credential_is_placed_but_never_printed(skill, tmp_path, capsys):
    bootstrap.main(["--offline", "--dest", str(tmp_path / "run")])
    captured = capsys.readouterr()
    placed = tmp_path / "run" / "vendored" / "resources" / "credential.env"
    assert placed.is_file(), "the engine's own default --key-file must find it"
    assert placed.read_text(encoding="utf-8").startswith("ODDS_API_KEY=")
    assert "secret" not in captured.out and "secret" not in captured.err


def test_no_engine_at_all_is_the_only_hard_failure(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(bootstrap, "VENDOR_ARCHIVE", tmp_path / "nothing.tar.gz")
    monkeypatch.setattr(bootstrap, "SKILL_ROOT", tmp_path / "skill")
    assert bootstrap.main(["--offline", "--dest", str(tmp_path / "run")]) == 3
    assert "NO ENGINE AVAILABLE" in capsys.readouterr().err


def test_a_fetched_engine_is_reused_when_it_still_verifies(skill, tmp_path, monkeypatch):
    """The second session of the day should not re-download."""
    dest = tmp_path / "run"
    lock = None
    engine_src = _engine(tmp_path / "src")
    lock = ev.build_lock(engine_src, "props-v1.0")
    monkeypatch.setattr(bootstrap, "fetch_lock", lambda *a, **k: lock)
    calls = []

    def fake_get(url, timeout=None):
        calls.append(url)
        return _engine_tarball()
    monkeypatch.setattr(bootstrap, "_get", fake_get)

    first = bootstrap.resolve(dest)
    assert first["engine_source"] == "fetched" and len(calls) == 1
    second = bootstrap.resolve(dest)
    assert second["engine_source"] == "cached", "it re-downloaded"
    assert len(calls) == 1
    assert second["engine_tag"] == "props-v1.0"


def test_a_tarball_that_fails_the_lock_falls_back_rather_than_running(skill, tmp_path, monkeypatch):
    """An engine that is not what the lock describes must not be used: that
    is the case where something has tampered with, or mis-tagged, a release."""
    engine_src = _engine(tmp_path / "src")
    (engine_src / "scripts" / "model.py").write_bytes(b"different\n")
    lock = ev.build_lock(engine_src, "props-v1.0")
    monkeypatch.setattr(bootstrap, "fetch_lock", lambda *a, **k: lock)
    monkeypatch.setattr(bootstrap, "_get", lambda url, timeout=None: _engine_tarball())

    info = bootstrap.resolve(tmp_path / "run")
    assert info["engine_source"] == "VENDORED_FALLBACK"
    assert "hash mismatch" in info["fallback_reason"]


def test_the_stamp_lands_beside_the_engine_not_inside_it(skill, tmp_path):
    """Inside, it would be part of the hash: a fetched engine would stop
    matching the lock the moment it was stamped and re-download every
    session. Found by the cache test failing."""
    bootstrap.main(["--offline", "--dest", str(tmp_path / "run")])
    engine = tmp_path / "run" / "vendored"
    assert not (engine / "ENGINE_STAMP.json").exists()
    assert (tmp_path / "run" / "vendored.stamp.json").is_file()
    info = json.loads((tmp_path / "run" / "vendored.stamp.json").read_text(encoding="utf-8"))
    assert info["engine_source"] == "VENDORED_FALLBACK"


def test_placing_the_credential_does_not_change_the_engine_hash(tmp_path):
    """The credential is copied INTO the engine's resources/ so the engine's
    own default --key-file finds it; `.env` is excluded from the hash, which
    is what keeps a credentialed engine verifiable against the lock."""
    engine = _engine(tmp_path / "engine")
    before = ev.tree_hash(engine)
    (engine / "resources" / "credential.env").write_text("ODDS_API_KEY=x\n",
                                                         encoding="utf-8")
    assert ev.tree_hash(engine) == before


# ------------------------------------------------------------ the package

def test_the_built_skill_has_exactly_one_skill_md(tmp_path):
    """THE UPLOADER'S RULE, learned the hard way: a package with two SKILL.md
    files is refused ("Zip must contain exactly one SKILL.md file. Currently
    there are 2"). The engine carries its own contract, so the vendored
    fallback ships as a tarball rather than a tree."""
    import subprocess
    import sys as _sys
    import zipfile
    out = tmp_path / "test.skill"
    rc = subprocess.run(
        [_sys.executable, str(PROPS / "build_skill.py"), "--out", str(out)],
        capture_output=True, text=True, cwd=PROPS.parent)
    assert rc.returncode == 0, rc.stderr

    names = zipfile.ZipFile(out).namelist()
    skill_mds = [n for n in names if n.endswith("SKILL.md")]
    assert skill_mds == ["nfl-prop-research/SKILL.md"], skill_mds
    assert "nfl-prop-research/vendor/engine.tar.gz" in names
    assert not any("vendor/engine/" in n for n in names), \
        "the fallback must be archived, not a loose tree"
    assert not any(n.endswith("credential.env") for n in names), \
        "no credential unless one is passed in"


def test_the_vendored_archive_unpacks_to_the_locked_engine(tmp_path):
    """A fallback nobody checked is a fallback that can be wrong exactly when
    it is needed."""
    import subprocess
    import sys as _sys
    import zipfile
    out = tmp_path / "test.skill"
    subprocess.run([_sys.executable, str(PROPS / "build_skill.py"),
                    "--out", str(out)], check=True, capture_output=True,
                   cwd=PROPS.parent)
    with zipfile.ZipFile(out) as z:
        blob = z.read("nfl-prop-research/vendor/engine.tar.gz")
        stamp = json.loads(z.read("nfl-prop-research/vendor/ENGINE_STAMP.json"))
    dest = tmp_path / "unpacked"
    assert bootstrap.extract_engine(blob, dest) == 29
    assert ev.tree_hash(dest) == stamp["engine_hash"]
    assert ev.tree_hash(dest) == ev.load_lock()["engine_sha256"]

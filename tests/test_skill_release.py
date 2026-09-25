"""The one chat skill: what a release holds, how the bootstrap fetches and
verifies it, where the credentials go, and what the build refuses."""

from __future__ import annotations

import io
import json
import sys
import tarfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skill"))
sys.path.insert(0, str(ROOT / "skill" / "scripts"))
import bootstrap as B  # noqa: E402
import release as R  # noqa: E402


def _tree(root: Path, files: dict[str, bytes]) -> Path:
    for rel, data in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return root


def _tarball(files: dict[str, bytes], prefix: str = "Fantasy-football-nfl-v9/", links=()) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel, data in files.items():
            info = tarfile.TarInfo(prefix + rel if not rel.startswith("/") else rel)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        for name in links:
            info = tarfile.TarInfo(prefix + name)
            info.type = tarfile.SYMTYPE
            info.linkname = "/etc/passwd"
            tar.addfile(info)
    return buf.getvalue()


RELEASE = {"nfl.py": b"print('hi')\n", "CHAT.md": b"# chat\n", "core/fetch.py": b"x = 1\n",
           "fantasy/lineup.py": b"y = 2\n", "leagues/omnibeta.yaml": b"a: 1\n"}


def test_the_release_holds_code_and_league_files_never_credentials_or_state():
    for rel in ("nfl.py", "CHAT.md", "config.yaml", "core/fetch.py", "fantasy/lineup.py", "manager/yahoo_api.py",
                "props/engine/scripts/score_game.py", "props/engine/SKILL.md", "leagues/keefamania.yaml",
                "data/external/fantasypros_2026.csv"):
        assert R.included(rel), rel
    for rel in (".env", "props/engine/resources/credential.env", "core/__pycache__/x.pyc", "state/a.json",
                "reports/x.md", "tests/test_x.py", "props/record/wk02.jsonl", "props/engine/scripts/backtest_out/a",
                "data/raw/yahoo/token.json", "skill/SKILL.md", "nfl.lock.json"):
        assert not R.included(rel), rel


def test_the_hash_ignores_line_endings_and_changes_on_one_byte(tmp_path):
    a = _tree(tmp_path / "a", RELEASE)
    b = _tree(tmp_path / "b", {k: v.replace(b"\n", b"\r\n") for k, v in RELEASE.items()})
    assert R.tree_hash(a) == R.tree_hash(b)
    (b / "core" / "fetch.py").write_bytes(b"x = 2\n")
    assert R.tree_hash(a) != R.tree_hash(b)


def test_compare_names_what_drifted(tmp_path):
    root = _tree(tmp_path / "r", RELEASE)
    lock = R.build_lock(root, "nfl-v9")
    assert R.compare(root, lock) == (True, [])
    (root / "fantasy" / "lineup.py").write_bytes(b"y = 3\n")
    (root / "core" / "new.py").write_bytes(b"")
    (root / "CHAT.md").unlink()
    ok, notes = R.compare(root, lock)
    assert not ok and {"missing: CHAT.md", "extra: core/new.py", "changed: fantasy/lineup.py"} <= set(notes)


def test_extraction_keeps_release_files_only(tmp_path):
    blob = _tarball({**RELEASE, "reports/x.md": b"r", "state/s.json": b"{}", ".env": b"SECRET=1"})
    assert B.extract_release(blob, tmp_path / "out") == len(RELEASE)
    assert not (tmp_path / "out" / ".env").exists() and not (tmp_path / "out" / "reports").exists()


@pytest.mark.parametrize("bad", ["Fantasy-football-nfl-v9/../core/evil.py", "Fantasy-football-nfl-v9/core/../../x.py"])
def test_extraction_refuses_a_path_outside_the_release(tmp_path, bad):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(bad)
        info.size = 1
        tar.addfile(info, io.BytesIO(b"x"))
    with pytest.raises(RuntimeError, match="outside the release"):
        B.extract_release(buf.getvalue(), tmp_path / "out")


def test_extraction_refuses_a_link(tmp_path):
    with pytest.raises(RuntimeError, match="link"):
        B.extract_release(_tarball(RELEASE, links=["core/link.py"]), tmp_path / "out")


@pytest.fixture
def online(tmp_path, monkeypatch):
    """A fake GitHub: the lock on main and the tag's tarball."""
    lock = R.build_lock(_tree(tmp_path / "src", RELEASE), "nfl-v9")
    served = {"tarball": _tarball(RELEASE), "calls": 0}

    def get(url, timeout=0):
        served["calls"] += 1
        return served["tarball"]
    monkeypatch.setattr(B, "fetch_lock", lambda url=None: lock)
    monkeypatch.setattr(B, "_get", get)
    monkeypatch.setattr(B, "VENDOR_ARCHIVE", tmp_path / "vendor" / "release.tar.gz")
    monkeypatch.setattr(B, "VENDOR_STAMP", tmp_path / "vendor" / "RELEASE_STAMP.json")
    return lock, served


def test_a_fetched_release_verifies_then_is_reused(tmp_path, online):
    lock, served = online
    info = B.resolve(tmp_path / "dest")
    assert info["release_source"] == "fetched" and info["release_tag"] == "nfl-v9"
    assert info["release_hash"] == lock["sha256"]
    again = B.resolve(tmp_path / "dest")
    assert again["release_source"] == "cached" and served["calls"] == 1


def test_a_tampered_tarball_falls_back_loudly(tmp_path, online):
    lock, served = online
    served["tarball"] = _tarball({**RELEASE, "core/fetch.py": b"x = 666\n"})
    v = tmp_path / "vendor"
    v.mkdir()
    (v / "release.tar.gz").write_bytes(_tarball(RELEASE, prefix="release/"))
    (v / "RELEASE_STAMP.json").write_text(json.dumps({"tag": "nfl-v8", "sha256": lock["sha256"]}), encoding="utf-8")
    info = B.resolve(tmp_path / "dest")
    assert info["release_source"] == "VENDORED_FALLBACK" and "changed: core/fetch.py" in info["fallback_reason"]
    assert info["release_tag"] == "nfl-v8" and info["lock_tag"] == "nfl-v9"
    # a vendored copy that does not match its own stamp claims no tag
    (v / "RELEASE_STAMP.json").write_text(json.dumps({"tag": "nfl-v8", "sha256": "0" * 64}), encoding="utf-8")
    info = B.resolve(tmp_path / "dest")
    assert info["release_tag"] is None and "does not match its stamp" in info["fallback_reason"]


def test_no_release_at_all_is_the_only_hard_failure(tmp_path, online):
    with pytest.raises(RuntimeError, match="no release at all"):
        B.resolve(tmp_path / "dest", offline=True)


def test_credentials_land_beside_the_release_and_are_never_printed(tmp_path, monkeypatch, online, capsys):
    res = tmp_path / "skill" / "resources"
    res.mkdir(parents=True)
    (res / "credential.env").write_text("ODDS_API_KEY=oddssecret\n", encoding="utf-8")
    bundle = {"client": {"client_id": "cid", "client_secret": "csecret", "redirect_uri": "https://localhost:8080"},
              "tokens": {"refresh_token": "rtoken", "access_token": "atoken"}}
    (res / "Yahoo_Fantasy_Connection.json").write_text(json.dumps(bundle), encoding="utf-8")
    monkeypatch.setattr(B, "ODDS_CREDENTIAL", res / "credential.env")
    monkeypatch.setattr(B, "YAHOO_BUNDLE", res / "Yahoo_Fantasy_Connection.json")
    monkeypatch.setattr(B, "ensure_dependencies", lambda install=True: "ok")
    assert B.main(["--dest", str(tmp_path / "dest")]) == 0
    out = capsys.readouterr()
    run = Path([ln for ln in out.out.splitlines() if ln.startswith("REPO_DIR=")][0].split("=", 1)[1])
    env = (run / ".env").read_text(encoding="utf-8")
    assert "YAHOO_CLIENT_ID=cid" in env and "YAHOO_REFRESH_TOKEN=rtoken" in env
    assert "YAHOO_REDIRECT_URI=https://localhost:8080" in env
    assert (run / "props" / "engine" / "resources" / "credential.env").read_text(encoding="utf-8").startswith("ODDS")
    for secret in ("oddssecret", "csecret", "rtoken", "atoken"):
        assert secret not in out.out and secret not in out.err
    assert "YAHOO=live" in out.out and "ODDS_KEY=present" in out.out
    # the credentials sit outside the hashed release: a second session still verifies the cache
    assert R.compare(run, online[0])[0]


def test_an_incomplete_yahoo_bundle_is_reported_absent(tmp_path, monkeypatch):
    p = tmp_path / "y.json"
    p.write_text(json.dumps({"client": {"client_id": "cid"}, "tokens": {}}), encoding="utf-8")
    monkeypatch.setattr(B, "YAHOO_BUNDLE", p)
    monkeypatch.setattr(B, "ODDS_CREDENTIAL", tmp_path / "none.env")
    assert B.place_credentials(tmp_path / "run") == {"odds_key": False, "yahoo": False}
    assert not (tmp_path / "run" / ".env").exists()


def test_the_build_refuses_a_credential_inside_the_repo(tmp_path):
    import build
    with pytest.raises(SystemExit, match="REFUSING"):
        build._outside_repo(ROOT / "config.yaml", "credential")
    outside = tmp_path / "credential.env"
    outside.write_text("x", encoding="utf-8")
    assert build._outside_repo(outside, "credential") == outside.resolve()


def test_the_committed_lock_describes_the_release_file_set():
    lock = json.loads((ROOT / R.LOCK_NAME).read_text(encoding="utf-8"))
    assert lock["algorithm"] == R.ALGORITHM and lock["tag"].startswith("nfl-v")
    assert lock["file_count"] == len(lock["files"]) and "CHAT.md" in lock["files"] and "nfl.py" in lock["files"]
    assert not any(r.endswith(("credential.env", ".env")) for r in lock["files"])


def test_the_skill_and_its_scripts_are_stdlib_only():
    for f in ("skill/release.py", "skill/scripts/bootstrap.py"):
        src = (ROOT / f).read_text(encoding="utf-8")
        for lib in ("pandas", "numpy", "requests", "yaml", "polars"):
            assert f"import {lib}" not in src and f"from {lib}" not in src, (f, lib)


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """A throwaway git repo holding a small release, committed."""
    import subprocess
    for k, v in {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t",
                 "GIT_COMMITTER_EMAIL": "t@t"}.items():
        monkeypatch.setenv(k, v)
    root = _tree(tmp_path / "repo", {**RELEASE, "reports/r.md": b"not released\n"})

    def git(*a):
        return subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, text=True).stdout
    git("init", "-q")
    git("-c", "core.autocrlf=false", "add", "-A")
    git("commit", "-q", "-m", "one")
    return root, git


def test_check_lock_uses_head_before_the_tag_and_the_tag_after(repo):
    root, git = repo
    lock = R.build_lock(root, "nfl-v9")
    ok, msg = R.check_lock(lock, root)
    assert ok and "HEAD (tag nfl-v9 not cut yet)" in msg
    git("tag", "nfl-v9")
    (root / "core" / "fetch.py").write_bytes(b"x = 99\n")          # main moves ahead of the release
    git("commit", "-qam", "two")
    ok, msg = R.check_lock(lock, root)
    assert ok and msg.startswith("tag nfl-v9"), "the lock is checked against its tag, not HEAD"
    ok, msg = R.check_lock(dict(lock, files={**lock["files"], "core/fetch.py": "0" * 64}), root)
    assert not ok and "changed: core/fetch.py" in msg
    assert not R.check_lock(dict(lock, algorithm="other"), root)[0]


def test_cut_tag_refuses_a_head_that_does_not_match_the_lock(repo):
    root, git = repo
    lock = R.build_lock(root, "nfl-v9")
    (root / "fantasy" / "lineup.py").write_bytes(b"y = 3\n")       # another PR merged before the tag
    git("commit", "-qam", "other")
    ok, msg = R.cut_tag(lock, root)
    assert not ok and "not tagging" in msg and "nfl-v9" not in git("tag")
    ok, msg = R.cut_tag(R.build_lock(root, "nfl-v9"), root)
    assert ok and "nfl-v9" in git("tag")
    assert not R.cut_tag(R.build_lock(root, "nfl-v9"), root)[0], "an existing tag is never moved"


def test_contents_at_ignores_files_outside_the_release(repo):
    root, _ = repo
    got = R.contents_at("HEAD", root)
    assert set(got) == set(RELEASE) and R.contents_at("refs/tags/nope", root) is None


def test_a_placed_yahoo_bundle_replaces_a_stale_token_file(tmp_path, monkeypatch):
    p = tmp_path / "y.json"
    p.write_text(json.dumps({"client": {"client_id": "c", "client_secret": "s", "redirect_uri": "oob"},
                             "tokens": {"refresh_token": "new"}}), encoding="utf-8")
    monkeypatch.setattr(B, "YAHOO_BUNDLE", p)
    monkeypatch.setattr(B, "ODDS_CREDENTIAL", tmp_path / "none.env")
    stale = _tree(tmp_path / "run", {"data/raw/yahoo/token.json": b'{"refresh_token": "old"}'})
    assert B.place_credentials(stale)["yahoo"] and not (stale / "data/raw/yahoo/token.json").exists()


def test_chat_answers_in_the_reply_and_never_asks_for_league_data():
    text = (ROOT / "CHAT.md").read_text(encoding="utf-8")
    assert "Answer in the reply, not in a file" in text
    assert "Never ask the user for anything a command can read" in text
    assert "--break-system-packages" in text, "the retry the container's pip needs"
    assert "Call `present_files` on the report" not in text, "the rule that turned answers into files is gone"


def test_the_bootstrap_retries_an_externally_managed_pip():
    src = (ROOT / "skill" / "scripts" / "bootstrap.py").read_text(encoding="utf-8")
    assert "externally-managed" in src and "--break-system-packages" in src


def test_every_command_leaves_a_troubleshooting_line_without_secrets(tmp_path, monkeypatch):
    import nfl
    monkeypatch.setenv("NFL_OUT", str(tmp_path))
    monkeypatch.setenv("YAHOO_CLIENT_SECRET", "s3cret-value")

    class R:
        record = {"gate": {"passed": False, "checks": [{"name": "roster fresh", "passed": False}]},
                  "manifest": {"entries": [{"name": "league roster", "source": "yahoo", "status": "stale",
                                            "age_h": 185.0, "detail": ""}]}}
        report_path = tmp_path / "lineup.md"
    nfl._session_log(["fantasy", "lineup", "--league", "keefamania"], 0, None, 2.5, R())
    line = json.loads((tmp_path / "nfl_session_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert line["argv"][-1] == "keefamania" and line["exit"] == 0 and line["gate"] == "FAIL: roster fresh"
    assert line["inputs"][0]["age_h"] == 185.0
    assert "s3cret" not in json.dumps(line)

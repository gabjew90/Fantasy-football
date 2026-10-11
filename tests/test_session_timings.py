"""Every step of a chat session is timed (DECISIONS #236): the bootstrap's setup, every nfl.py
command and the calculator through `nfl.py calc`; `nfl.py log` turns them into a timeline. The
2026-10-11 PHI@JAX session logged 2 of 60 commands, so it could not say where 8 minutes went."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import nfl

ROOT = Path(__file__).resolve().parents[1]


def _row(argv, started, seconds, **kw):
    return {"argv": argv, "started_utc": started, "seconds": seconds, "exit": 0, **kw}


def test_the_timeline_lists_setup_then_each_step_with_the_wait_before_it():
    rows = [_row(["status"], "2026-10-11T00:35:02.000+00:00", 3.0,
                 setup={"setup_started_utc": "2026-10-11T00:34:20.000+00:00", "setup_seconds": 19.5}),
            _row(["calc", "game", "PHI@JAX"], "2026-10-11T00:35:10.000+00:00", 40.0),
            # an older line has no started_utc: its start is its end (at_utc) minus its length
            {"argv": ["calc", "leg", "Jalen Hurts", "pass_yds", "over"], "at_utc": "2026-10-11T00:36:20+00:00",
             "seconds": 5.0, "exit": 0}]
    L = nfl.timings(rows)
    body = "\n".join(L)
    assert "| setup (fetch and check the release) | 00:34:20 | 19.5 | -- |" in body
    assert "| `status` | 00:35:02 | 3.0 | 22.5 |" in body          # 00:34:39.5 -> 00:35:02
    assert "| `calc game PHI@JAX` | 00:35:10 | 40.0 | 5.0 |" in body
    assert "| `calc leg Jalen Hurts pass_yds over` | 00:36:15 | 5.0 | 25.0 |" in body
    assert "4 steps in 120 s" in body and "67.5 s running" in body and "52.5 s between steps" in body
    assert "The reply is written after the last step and is not timed." in body
    assert nfl.timings([]) == []


def test_nfl_calc_passes_every_argument_through_and_returns_its_exit(monkeypatch):
    seen = []
    import props.calc.__main__ as CALC
    monkeypatch.setattr(CALC, "main", lambda argv: seen.append(argv) or 3)
    rc = nfl.main(["calc", "leg", "Jalen Hurts", "pass_yds", "over", "--line", "186.5", "--over", "-127",
                   "--under", "-130"])
    assert rc == 3
    assert seen == [["leg", "Jalen Hurts", "pass_yds", "over", "--line", "186.5", "--over", "-127", "--under", "-130"]]


def test_calc_help_and_leading_flags_reach_the_calculator(monkeypatch):
    seen = []
    import props.calc.__main__ as CALC
    monkeypatch.setattr(CALC, "main", lambda argv: seen.append(argv) or 0)
    assert nfl.main(["calc", "--help"]) == 0 and nfl.main(["calc", "game", "LA@SF", "--all"]) == 0
    assert seen == [["--help"], ["game", "LA@SF", "--all"]]


def test_a_calc_run_is_logged_with_its_start_and_length(monkeypatch, tmp_path):
    import props.calc.__main__ as CALC
    monkeypatch.setattr(CALC, "main", lambda argv: 0)
    monkeypatch.setenv("NFL_OUT", str(tmp_path))
    monkeypatch.setenv("NFL_SESSION_LOG", "1")
    assert nfl.main(["calc", "capture"]) == 0
    line = json.loads((tmp_path / "nfl_session_log.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    assert line["argv"] == ["calc", "capture"] and line["exit"] == 0
    import datetime as dt
    # at_utc keeps whole seconds (cut, not rounded); started_utc keeps milliseconds
    assert nfl._utc(line["started_utc"]) <= nfl._utc(line["at_utc"]) + dt.timedelta(seconds=1)
    assert isinstance(line["seconds"], float)


def test_the_session_report_carries_the_timings(tmp_path):
    rows = [_row(["status", "--game", "PHI@JAX"], "2026-10-11T00:35:10.000+00:00", 0.6, at_utc="2026-10-11T00:35:11+00:00",
                 setup={"setup_started_utc": "2026-10-11T00:34:30.000+00:00", "setup_seconds": 12.0})]
    (tmp_path / "nfl_session_log.jsonl").write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    text = nfl.session_report(tmp_path).read_text(encoding="utf-8")
    assert "## Timings" in text and "| setup (fetch and check the release) | 00:34:30 | 12.0 | -- |" in text
    assert text.index("## Timings") < text.index("## Review of the session")


def test_the_bootstrap_times_the_whole_setup_even_after_a_hand_over(tmp_path, monkeypatch, capsys):
    sys.path.insert(0, str(ROOT / "skill"))
    sys.path.insert(0, str(ROOT / "skill" / "scripts"))
    import bootstrap as B
    run = tmp_path / "nfl-v9"
    run.mkdir()
    monkeypatch.setattr(B, "T0", B.time.time() - 7.0)          # setup began 7 s ago (e.g. in the older loader)
    monkeypatch.setattr(B, "fetch_lock", lambda url=None: {})
    monkeypatch.setattr(B, "resolve", lambda dest, tag, offline: {
        "repo_dir": str(run), "release_hash": "h", "release_tag": "nfl-v9", "release_source": "fetched",
        "fallback_reason": None, "lock_tag": "nfl-v9"})
    monkeypatch.setattr(B, "place_credentials", lambda d: {"odds_key": False, "yahoo": False})
    monkeypatch.setattr(B, "ensure_dependencies", lambda install=True: "ok")
    assert B.main(["--dest", str(tmp_path), "--no-deps"]) == 0
    stamp = json.loads((tmp_path / "nfl-v9.stamp.json").read_text(encoding="utf-8"))
    assert stamp["setup_seconds"] >= 7.0 and stamp["setup_started_utc"].endswith("+00:00")
    assert f"SETUP_SECONDS={stamp['setup_seconds']}" in capsys.readouterr().out
    # a hand-over passes the start along, so the new loader's figure covers both
    seen = {}
    monkeypatch.setattr(B, "_get", lambda url, timeout=0: b"x = 1\n")
    monkeypatch.setattr(B.subprocess, "call", lambda cmd, env=None: seen.update(env) or 0)
    monkeypatch.delenv("NFL_HARNESS_UPDATED", raising=False)
    import hashlib
    pin = hashlib.sha256(b"x = 1\n").hexdigest()
    B.harness_update({"harness": {"scripts/bootstrap.py": pin, "scripts/release.py": pin}}, tmp_path, [])
    assert float(seen["NFL_SETUP_T0"]) == B.T0

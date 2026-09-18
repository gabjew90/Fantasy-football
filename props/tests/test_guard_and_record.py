"""The guard's clock, and the record's durability.

Both were code-review findings on 2026-09-17: the Eastern offset was hand
rolled with the wrong DST date, and the record was rewritten in place so a
killed process could leave a truncated archive to be committed.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import engine_version  # noqa: E402
import guard  # noqa: E402
import persist  # noqa: E402


def _kick(day: str, time: str):
    return guard.kickoff_utc({"gameday": day, "gametime": time})


def _FrozenDatetime(now):  # noqa: N802 - it stands in for a class
    """dt.datetime with now() pinned, so the guard's clock is testable.

    Subclassed rather than mocked because kickoff_utc also uses strptime and
    the constructor, and those must keep working.
    """
    class _F(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    return _F


def _run_guard(mod) -> dict:
    """main()'s GITHUB_OUTPUT lines, as a dict."""
    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert mod.main() == 0
    return dict(line.split("=", 1) for line in buf.getvalue().splitlines() if "=" in line)


# ------------------------------------------------------------------- clock

def test_september_kickoff_matches_the_verified_schedule():
    """DET at BUF, week 2: games.csv says 20:15 ET and ESPN says 00:15Z."""
    assert _kick("2026-09-17", "20:15") == dt.datetime(
        2026, 9, 18, 0, 15, tzinfo=dt.timezone.utc)


def test_dst_ends_on_the_first_sunday_in_november_not_the_fifth():
    """The bug: a hard-coded Nov 5 cutoff put all 13 games of the Nov 1-2
    slate an hour early, which shut the capture window 45 minutes BEFORE
    kickoff and lost the closing snapshot the record exists for."""
    # Nov 1 2026 is the first Sunday, so these are EST (UTC-5).
    assert _kick("2026-11-01", "13:00") == dt.datetime(2026, 11, 1, 18, 0, tzinfo=dt.timezone.utc)
    assert _kick("2026-11-01", "16:25") == dt.datetime(2026, 11, 1, 21, 25, tzinfo=dt.timezone.utc)
    assert _kick("2026-11-02", "20:15") == dt.datetime(2026, 11, 3, 1, 15, tzinfo=dt.timezone.utc)
    # ...and the week before is still EDT (UTC-4).
    assert _kick("2026-10-25", "13:00") == dt.datetime(2026, 10, 25, 17, 0, tzinfo=dt.timezone.utc)


def test_the_close_window_lands_inside_the_hour_before_kickoff():
    """What the offset bug actually cost: with the kickoff an hour early, a
    tick 30 minutes before the real kickoff fell outside the window."""
    kick = _kick("2026-11-01", "13:00")
    lead = lambda now: (kick - now).total_seconds() / 60.0  # noqa: E731
    assert lead(kick - dt.timedelta(minutes=30)) == pytest.approx(30)
    assert -15 <= lead(kick - dt.timedelta(minutes=30)) <= guard.CAPTURE_LEAD_MIN
    assert lead(kick - dt.timedelta(minutes=30)) <= guard.CLOSE_WINDOW_MIN, "should be a close snapshot"
    assert lead(kick - dt.timedelta(hours=2)) > guard.CLOSE_WINDOW_MIN, "two hours out is not close"


def test_a_malformed_row_is_skipped_not_raised():
    assert _kick("not-a-date", "13:00") is None
    assert guard.kickoff_utc({"gameday": "2026-11-01"}) is None
    assert _kick("2026-11-01", "99:99") is None


# ------------------------------------------------------------------ record

def _rows(n, week=2):
    return [{"season": 2026, "week": week, "event_id": f"e{i}", "book": "dk",
             "market": "receptions", "player": f"P{i}", "side": "Over",
             "line": 3.5, "snapshot_type": "decision"} for i in range(n)]


def test_append_dedupes_on_the_natural_key(tmp_path):
    p = tmp_path / "wk02.jsonl"
    first = persist.append_jsonl(p, _rows(3), persist.PREDICTION_KEY)
    assert (first["before"], first["added"], first["replaced"]) == (0, 3, 0)
    again = persist.append_jsonl(p, _rows(3), persist.PREDICTION_KEY)
    assert (again["before"], again["added"], again["replaced"]) == (3, 0, 3)
    assert sum(1 for _ in p.open(encoding="utf-8")) == 3


def test_the_write_is_atomic_and_leaves_no_temp_behind(tmp_path):
    """A runner timeout mid-write must not be able to commit a truncated
    archive, so the merge lands through os.replace."""
    p = tmp_path / "wk02.jsonl"
    persist.append_jsonl(p, _rows(2), persist.PREDICTION_KEY)
    persist.append_jsonl(p, _rows(4), persist.PREDICTION_KEY)
    assert list(tmp_path.iterdir()) == [p], "a .tmp file was left in the record tree"
    assert sum(1 for _ in p.open(encoding="utf-8")) == 4
    for line in p.open(encoding="utf-8"):
        json.loads(line)          # every surviving line is whole


def test_a_crash_during_the_rewrite_keeps_the_previous_file(tmp_path, monkeypatch):
    p = tmp_path / "wk02.jsonl"
    persist.append_jsonl(p, _rows(3), persist.PREDICTION_KEY)
    before = p.read_text(encoding="utf-8")

    def boom(*a, **k):
        raise KeyboardInterrupt("runner timeout")
    monkeypatch.setattr(persist.os, "replace", boom)
    with pytest.raises(KeyboardInterrupt):
        persist.append_jsonl(p, _rows(9), persist.PREDICTION_KEY)
    assert p.read_text(encoding="utf-8") == before, "the record was clobbered"


# ------------------------------------------------ the window runs once, and
# ------------------------------------------------ knows its week regardless

def test_the_settle_window_opens_once_per_week_not_once_per_tick(monkeypatch, tmp_path):
    """The window has to stay two hours wide because GitHub fires crons a
    median 128 minutes late, so the duplicate ticks are stopped by a marker
    instead of by narrowing the window."""
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker",
                        lambda kind, key: tmp_path / f"ran_{kind}_{key}")
    tue = dt.datetime(2026, 9, 22, 14, 3, tzinfo=dt.timezone.utc)
    assert tue.weekday() == 1

    modes = []
    for minutes in range(0, 120, 15):          # every tick inside the window
        now = tue + dt.timedelta(minutes=minutes)
        monkeypatch.setattr(guard.dt, "datetime", _FrozenDatetime(now))
        out = _run_guard(guard)
        modes.append(out["mode"])
    assert modes[0] == "settle", "the first tick in the window settles"
    assert set(modes[1:]) == {"idle"}, f"only one settle per week, got {modes}"

    # ...and next week settles again
    nxt = tue + dt.timedelta(days=7)
    monkeypatch.setattr(guard.dt, "datetime", _FrozenDatetime(nxt))
    assert _run_guard(guard)["mode"] == "settle"


def test_an_unreadable_schedule_opens_the_window_with_a_real_week(monkeypatch, tmp_path):
    """It used to emit week=0, which no game belongs to, so the run opened to
    protect a closing capture could not capture anything."""
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker", lambda kind, key: tmp_path / f"r_{kind}_{key}")

    def boom(season):
        raise OSError("dns")
    monkeypatch.setattr(guard, "load_games", boom)
    now = dt.datetime(2026, 9, 24, 18, 0, tzinfo=dt.timezone.utc)   # Thursday, week 3
    monkeypatch.setattr(guard.dt, "datetime", _FrozenDatetime(now))
    out = _run_guard(guard)
    assert out["run"] == "true" and out["mode"] == "capture"
    assert int(out["week"]) == 3, out


def test_the_calendar_week_matches_the_real_schedule():
    """Week 1 opens the Thursday after Labor Day. 2026: Labor Day Sep 7,
    so week 1 is Sep 10 and week 2 is Sep 17 -- the night we verified."""
    wk = guard.week_from_calendar
    at = lambda m, d: dt.datetime(2026, m, d, 18, tzinfo=dt.timezone.utc)  # noqa: E731
    assert wk(at(9, 10), 2026) == 1
    assert wk(at(9, 17), 2026) == 2
    assert wk(at(9, 20), 2026) == 2, "Sunday belongs to the week that opened Thursday"
    assert wk(at(11, 1), 2026) == 8
    # clamped at both ends: before the opener and after week 18
    assert wk(at(8, 1), 2026) == 1
    assert wk(dt.datetime(2027, 3, 1, 18, tzinfo=dt.timezone.utc), 2026) == 18


def test_a_stale_cache_answers_when_the_fetch_fails(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    cached = tmp_path / "games_2026.json"
    cached.write_text(json.dumps([{"week": "2", "gameday": "2026-09-20",
                                   "gametime": "13:00"}]), encoding="utf-8")
    import os
    old = dt.datetime.now().timestamp() - 200000        # older than a day
    os.utime(cached, (old, old))

    def boom(*a, **k):
        raise OSError("dns")
    monkeypatch.setattr(guard.urllib.request, "urlopen", boom)
    rows = guard.load_games(2026)
    assert rows and rows[0]["gameday"] == "2026-09-20", "stale beats nothing"


# ------------------------------------------- the engine is part of the identity

def _stamped(n, engine, week=2):
    return [dict(r, engine_hash=engine, engine_tag=None) for r in _rows(n, week)]


def test_two_engines_never_dedupe_into_one_row(tmp_path):
    """The corruption this prevents: without engine_hash in the key, re-scoring
    a game under a new engine REPLACES the old engine's rows -- same line, same
    side -- overwriting p_model/gap/tier and restamping them with the new
    version. The old engine's record would vanish and its survivors would lie
    about which code made them."""
    p = tmp_path / "wk02.jsonl"
    first = persist.append_jsonl(p, _stamped(3, "aaa"), persist.PREDICTION_KEY)
    second = persist.append_jsonl(p, _stamped(3, "bbb"), persist.PREDICTION_KEY)
    assert (first["added"], first["replaced"]) == (3, 0)
    assert (second["added"], second["replaced"]) == (3, 0), "engine B overwrote engine A"
    assert second["after"] == 6
    engines = {json.loads(line)["engine_hash"] for line in p.open(encoding="utf-8")}
    assert engines == {"aaa", "bbb"}


def test_the_same_engine_rerun_still_dedupes(tmp_path):
    p = tmp_path / "wk02.jsonl"
    persist.append_jsonl(p, _stamped(3, "aaa"), persist.PREDICTION_KEY)
    again = persist.append_jsonl(p, _stamped(3, "aaa"), persist.PREDICTION_KEY)
    assert (again["added"], again["replaced"], again["after"]) == (0, 3, 3)


def test_an_unstamped_row_and_a_stamped_row_are_different_rows(tmp_path):
    """Why the existing 103 rows had to be backfilled rather than left null:
    persist._key stringifies a missing field to "", so an unstamped board and
    the same board captured again would both persist."""
    p = tmp_path / "wk02.jsonl"
    persist.append_jsonl(p, _rows(2), persist.PREDICTION_KEY)          # no stamp
    out = persist.append_jsonl(p, _stamped(2, "aaa"), persist.PREDICTION_KEY)
    assert out["after"] == 4 and out["replaced"] == 0


# ----------------------------------------------------- record_run stamps rows

SHADOW_HEADER = ("logged_at_utc,season,week,event_id,book,market,player,team,slot,"
                 "line,model_mean,side,p_model,p_push,p_novig,gap,price,ER,"
                 "last_update,new_team,questionable,flag,model_state,decision,"
                 "clears_edge_rule_if_validated,tier")


def _scorer_dir(tmp_path):
    """A directory shaped like the scorer's output: one shadow log, one archive."""
    d = tmp_path / "out"
    d.mkdir()
    (d / "shadow_log_2026_wk02_MIA_SF.csv").write_text(
        SHADOW_HEADER + "\n"
        "2026-09-18T05:20:46Z,2026,2,ev1,sleeper,player_receptions,A Player,SF,WR1,"
        "3.5,4.1,Over,0.61,0.0,0.55,0.06,-120,0.01,2026-09-18T05:14:11Z,False,False,"
        ",receiving_hier_v1,PASS,False,STRONG\n",
        encoding="utf-8")
    (d / "line_archive_nfl_2026.jsonl").write_text(
        json.dumps({"season": 2026, "week": 2, "event_id": "ev1",
                    "bookmaker": "sleeper", "market": "player_receptions",
                    "player": "A Player", "outcome": "Over", "point": 3.5,
                    "snapshot_type": "decision"}) + "\n",
        encoding="utf-8")
    return d


def test_record_run_stamps_every_row_from_the_tree_that_ran(tmp_path, monkeypatch, capsys):
    """The stamp must describe the engine that produced the artifacts, so it
    is computed from --engine-dir, never copied out of the lock."""
    import record_run
    engine = tmp_path / "engine"
    (engine / "scripts").mkdir(parents=True)
    (engine / "SKILL.md").write_bytes(b"---\nname: x\n---\n")
    (engine / "scripts/model.py").write_bytes(b"x = 1\n")
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")

    # main() reads sys.argv, so drive it that way.
    monkeypatch.setattr(sys, "argv", [
        "record_run.py", "--dir", str(_scorer_dir(tmp_path)),
        "--snapshot-type", "decision", "--engine-dir", str(engine)])
    assert record_run.main() == 0

    expected = engine_version.tree_hash(engine)
    for rel in ("predictions/2026/wk02.jsonl", "lines/2026/line_archive_2026.jsonl"):
        rows = [json.loads(x) for x in
                (tmp_path / "record" / rel).open(encoding="utf-8") if x.strip()]
        assert rows, rel
        for row in rows:
            assert row["engine_hash"] == expected, rel
            assert row["engine_tag"] is None, "a temp tree matches no lock"
    out = capsys.readouterr().out
    assert f"engine={expected[:12]}" in out and "tag=(untagged)" in out


def test_record_run_refuses_to_file_rows_it_cannot_stamp(tmp_path, monkeypatch):
    """With no engine tree there is nothing to stamp, and an unstamped row
    cannot be told apart from another version's later. The ONLY hard refusal
    in the capture path."""
    import record_run
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    monkeypatch.setattr(sys, "argv", [
        "record_run.py", "--dir", str(_scorer_dir(tmp_path)),
        "--engine-dir", str(tmp_path / "no-engine")])
    assert record_run.main() == 2
    assert not (tmp_path / "record").exists(), "nothing may be written"


# ------------------------------------------------- the Thursday opening sweep

def _thursday_games():
    """A week-3 Thursday nighter and its Sunday slate."""
    return [{"week": "3", "gameday": "2026-09-24", "gametime": "20:15"},
            {"week": "3", "gameday": "2026-09-27", "gametime": "13:00"}]


def test_the_open_sweep_fires_once_a_week_on_thursday_evening(monkeypatch, tmp_path):
    """Closing-line value needs two ends. The capture window only opens six
    hours before a kickoff, by which time the board has absorbed the week's
    news, so the opening price needs its own sweep."""
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker",
                        lambda kind, key: tmp_path / f"ran_{kind}_{key}")
    monkeypatch.setattr(guard, "load_games", lambda season: _thursday_games())

    thursday = dt.datetime(2026, 9, 24, 22, 5, tzinfo=dt.timezone.utc)
    assert thursday.weekday() == 3
    modes = []
    for minutes in range(0, 120, 15):
        monkeypatch.setattr(guard.dt, "datetime",
                            _FrozenDatetime(thursday + dt.timedelta(minutes=minutes)))
        modes.append(_run_guard(guard))
    first = modes[0]
    assert first["run"] == "true" and first["snapshot_type"] == "open"
    assert int(first["week"]) == 3, "the week the sweep is for"
    assert all(m["snapshot_type"] != "open" for m in modes[1:]), \
        "the other seven ticks in the window must not re-open"


def test_the_open_sweep_returns_the_next_week(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker",
                        lambda kind, key: tmp_path / f"r_{kind}_{key}")
    monkeypatch.setattr(guard, "load_games", lambda season: _thursday_games())
    for when, expect in ((dt.datetime(2026, 9, 24, 22, 5, tzinfo=dt.timezone.utc), "open"),
                         (dt.datetime(2026, 10, 1, 22, 5, tzinfo=dt.timezone.utc), "open")):
        monkeypatch.setattr(guard.dt, "datetime", _FrozenDatetime(when))
        out = _run_guard(guard)
        assert out["snapshot_type"] == expect, f"{when} should sweep again"


def test_no_open_sweep_on_other_days_or_outside_the_window(monkeypatch, tmp_path):
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker",
                        lambda kind, key: tmp_path / f"r_{kind}_{key}")
    monkeypatch.setattr(guard, "load_games", lambda season: _thursday_games())
    for when in (dt.datetime(2026, 9, 23, 22, 5, tzinfo=dt.timezone.utc),   # Wednesday
                 dt.datetime(2026, 9, 25, 22, 5, tzinfo=dt.timezone.utc),   # Friday
                 dt.datetime(2026, 9, 24, 21, 5, tzinfo=dt.timezone.utc)):  # too early
        monkeypatch.setattr(guard.dt, "datetime", _FrozenDatetime(when))
        assert _run_guard(guard)["snapshot_type"] != "open", when


def test_the_open_sweep_never_shadows_a_kickoff_that_is_already_close(monkeypatch, tmp_path):
    """A Thursday 20:15 ET kickoff is 00:15Z Friday, so at 22:05Z Thursday
    the game is two hours out -- inside the capture window but not inside the
    close window. The sweep must not swallow the tick that would have made
    the decision capture."""
    monkeypatch.setattr(guard, "CACHE", tmp_path)
    monkeypatch.setattr(guard, "_period_marker",
                        lambda kind, key: tmp_path / f"r_{kind}_{key}")
    monkeypatch.setattr(guard, "load_games", lambda season: _thursday_games())
    monkeypatch.setattr(guard.dt, "datetime",
                        _FrozenDatetime(dt.datetime(2026, 9, 24, 22, 5, tzinfo=dt.timezone.utc)))
    first = _run_guard(guard)
    assert first["snapshot_type"] == "open"
    # the very next tick still captures the approaching kickoff
    monkeypatch.setattr(guard.dt, "datetime",
                        _FrozenDatetime(dt.datetime(2026, 9, 24, 22, 20, tzinfo=dt.timezone.utc)))
    second = _run_guard(guard)
    assert second["run"] == "true" and second["snapshot_type"] == "decision"


def test_the_engine_source_is_stamped_when_the_workflow_passes_it(tmp_path, monkeypatch):
    """A capture that fell back to main's engine is still a valid capture,
    but it is not the release, and the record has to say which."""
    import record_run
    engine = tmp_path / "engine"
    (engine / "scripts").mkdir(parents=True)
    (engine / "SKILL.md").write_bytes(b"---\nname: x\n---\n")
    (engine / "scripts/model.py").write_bytes(b"x = 1\n")
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    monkeypatch.setattr(sys, "argv", [
        "record_run.py", "--dir", str(_scorer_dir(tmp_path)),
        "--engine-dir", str(engine), "--engine-source", "main-fallback"])
    assert record_run.main() == 0

    rows = [json.loads(x) for x in
            (tmp_path / "record" / "predictions/2026/wk02.jsonl").open(encoding="utf-8")
            if x.strip()]
    assert rows and all(r["engine_source"] == "main-fallback" for r in rows)


def test_no_engine_source_flag_leaves_the_field_off(tmp_path, monkeypatch):
    """Chat and laptop runs pass nothing; the absence is not 'unknown', it
    is simply not a workflow capture."""
    import record_run
    engine = tmp_path / "engine"
    (engine / "scripts").mkdir(parents=True)
    (engine / "SKILL.md").write_bytes(b"---\nname: x\n---\n")
    (engine / "scripts/model.py").write_bytes(b"x = 1\n")
    monkeypatch.setattr(persist, "RECORD_ROOT", tmp_path / "record")
    monkeypatch.setattr(sys, "argv", [
        "record_run.py", "--dir", str(_scorer_dir(tmp_path)),
        "--engine-dir", str(engine)])
    assert record_run.main() == 0
    rows = [json.loads(x) for x in
            (tmp_path / "record" / "predictions/2026/wk02.jsonl").open(encoding="utf-8")
            if x.strip()]
    assert all("engine_source" not in r for r in rows)

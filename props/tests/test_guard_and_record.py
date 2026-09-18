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

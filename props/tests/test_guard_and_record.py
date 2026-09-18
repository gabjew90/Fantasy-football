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

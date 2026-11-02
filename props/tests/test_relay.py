"""The capture relay, the per-game close label, and the committed weekly markers (DECISIONS #253)."""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import json
import sys
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import guard  # noqa: E402
import record_run  # noqa: E402
import relay  # noqa: E402

UTC = dt.timezone.utc
# Sunday 2026-11-01, Eastern times as games.csv writes them: 18:00, 21:05 and 01:20 UTC.
SLATE = [{"gameday": "2026-11-01", "gametime": "13:00", "week": "8"},
         {"gameday": "2026-11-01", "gametime": "16:05", "week": "8"},
         {"gameday": "2026-11-01", "gametime": "20:20", "week": "8"}]
EARLY = dt.datetime(2026, 11, 1, 18, 0, tzinfo=UTC)


def _minutes(wait):
    return None if wait is None else round(wait / 60.0)


# ------------------------------------------------------------------ the hop

def test_the_hop_lands_inside_the_close_window_after_the_inactives():
    now = EARLY - dt.timedelta(minutes=200)
    wait = _minutes(relay.next_wait(SLATE, now, now))
    assert wait == 200 - relay.CLOSE_AIM_MIN
    assert relay.CLOSE_AIM_MIN <= guard.CLOSE_WINDOW_MIN


def test_a_capture_already_inside_the_window_moves_on_to_the_next_kickoff():
    started = EARLY - dt.timedelta(minutes=50)
    now = started + dt.timedelta(minutes=3)
    late = EARLY + dt.timedelta(minutes=185)
    expected = (late - now).total_seconds() / 60.0 - relay.CLOSE_AIM_MIN
    assert _minutes(relay.next_wait(SLATE, now, started)) == round(expected)


def test_a_capture_just_outside_the_window_still_gets_the_close_hop():
    """It started at 62 minutes and finished inside the hour: it took no closing line, so skipping
    this kickoff because it is now inside the window would lose the one the relay exists for."""
    started = EARLY - dt.timedelta(minutes=62)
    now = EARLY - dt.timedelta(minutes=59)
    assert _minutes(relay.next_wait(SLATE, now, started)) == 59 - relay.CLOSE_AIM_MIN


def test_an_idle_tick_inside_the_window_hops_at_once():
    assert relay.next_wait(SLATE, EARLY - dt.timedelta(minutes=30), None) == 0.0


def test_a_kickoff_beyond_one_sleep_gets_a_bridging_hop():
    now = EARLY - dt.timedelta(minutes=700)
    assert _minutes(relay.next_wait(SLATE, now, None)) == relay.MAX_SLEEP_MIN


def test_nothing_within_the_horizon_ends_the_chain():
    assert relay.next_wait(SLATE, EARLY - dt.timedelta(minutes=relay.HORIZON_MIN + 1), None) is None
    assert relay.next_wait(SLATE, EARLY + dt.timedelta(days=1), None) is None


def test_a_kickoff_too_close_to_capture_is_skipped():
    started = EARLY - dt.timedelta(minutes=200)
    now = EARLY - dt.timedelta(minutes=relay.MIN_LEAD_MIN)
    wait = _minutes(relay.next_wait(SLATE[:1], now, started))
    assert wait is None


def test_only_a_close_run_counts_as_having_taken_the_closing_line():
    """The workflow hands over the start time of a `close` run only. An opening sweep 45 minutes out
    took no closing line, so that kickoff still gets its hop."""
    text = (PROPS.parent / ".github" / "workflows" / "props.yml").read_text(encoding="utf-8")
    assert "needs.tick.outputs.snapshot_type == 'close' && github.run_started_at" in text
    assert "continue-on-error: true" in text
    started = EARLY - dt.timedelta(minutes=45)
    assert relay.next_wait(SLATE[:1], started, None) == 0.0
    assert relay.next_wait(SLATE[:1], started, started) is None


def test_a_schedule_failure_never_fails_the_run(monkeypatch, capsys):
    def boom(_season):
        raise OSError("no schedule")
    monkeypatch.setattr(guard, "load_games", boom)
    assert relay.main(["wait"]) == 0
    assert capsys.readouterr().out == ""


# ------------------------------------------------------------ guard: auto

def _guard_outputs(monkeypatch, now, env):
    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return now.astimezone(tz) if tz else now.replace(tzinfo=None)
    monkeypatch.setattr(guard.dt, "datetime", _Frozen)
    monkeypatch.setattr(guard, "load_games", lambda _season: SLATE)
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        assert guard.main() == 0
    return dict(line.split("=", 1) for line in buf.getvalue().splitlines())


def test_the_relay_dispatch_is_judged_like_a_scheduled_tick(monkeypatch):
    now = EARLY - dt.timedelta(minutes=45)
    out = _guard_outputs(monkeypatch, now, {"FORCED": "1", "PROPS_MODE": "auto"})
    assert (out["run"], out["mode"], out["snapshot_type"], out["week"]) == ("true", "capture", "close", "8")


def test_the_relay_dispatch_with_nothing_due_runs_nothing(monkeypatch):
    now = EARLY - dt.timedelta(minutes=700)
    out = _guard_outputs(monkeypatch, now, {"FORCED": "1", "PROPS_MODE": "auto"})
    assert out["run"] == "false"


def test_an_operator_dispatch_still_runs_as_it_did(monkeypatch):
    now = EARLY - dt.timedelta(minutes=45)
    out = _guard_outputs(monkeypatch, now, {"FORCED": "1", "PROPS_MODE": "capture"})
    assert (out["run"], out["mode"], out["snapshot_type"]) == ("true", "capture", "decision")


# ---------------------------------------------------------- weekly markers

@pytest.fixture
def record(tmp_path, monkeypatch):
    monkeypatch.setattr(guard, "MARKERS", tmp_path / "ran")
    (tmp_path / "predictions" / "2026").mkdir(parents=True)
    (tmp_path / "settled" / "2026").mkdir(parents=True)
    monkeypatch.setattr(relay, "RECORD", tmp_path)
    return tmp_path


def _predict(root, week, games):
    lines = "\n".join(json.dumps({"game": g, "snapshot_type": "decision"}) for g in games)
    (root / "predictions" / "2026" / f"wk{week:02d}.jsonl").write_text(lines + "\n", encoding="utf-8")


def _settle(root, rows):
    text = "week,game,status\n" + "".join(f"{w},{g},{s}\n" for w, g, s in rows)
    (root / "settled" / "2026" / "settled_2026.csv").write_text(text, encoding="utf-8")


def test_settle_is_complete_only_when_the_latest_week_is_fully_graded(record):
    _predict(record, 7, ["A@B"])
    _predict(record, 8, ["C@D", "E@F"])
    _settle(record, [(7, "A@B", "settled")])
    assert not relay.settle_complete(2026, record), "the week's stats are not out yet"
    _settle(record, [(7, "A@B", "settled"), (8, "C@D", "settled")])
    assert not relay.settle_complete(2026, record), "a game has no graded rows"
    _settle(record, [(8, "C@D", "settled"), (8, "E@F", "pending")])
    assert not relay.settle_complete(2026, record), "a row is still waiting on snap counts"
    _settle(record, [(8, "C@D", "settled"), (8, "E@F", "dnp")])
    assert relay.settle_complete(2026, record)


def test_a_game_with_no_decision_row_cannot_hold_settle_open(record):
    """Settle grades decisions only, so a close-only game never has settled rows."""
    _predict(record, 8, ["C@D"])
    with (record / "predictions" / "2026" / "wk08.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"game": "E@F", "snapshot_type": "close"}) + "\n")
    _settle(record, [(8, "C@D", "settled")])
    assert relay.settle_complete(2026, record)


def test_settle_with_no_record_is_not_complete(record):
    assert not relay.settle_complete(2026, record)


def test_the_marker_stops_the_next_settle_and_only_a_complete_one_writes_it(record, monkeypatch):
    tuesday = dt.datetime(2026, 11, 3, 18, 0, tzinfo=UTC)
    _predict(record, 8, ["C@D"])
    _settle(record, [(8, "C@D", "pending")])
    assert relay.mark("settle", tuesday) is False
    assert not guard.period_done("settle", guard.period_key(tuesday))
    assert _guard_outputs(monkeypatch, tuesday, {})["mode"] == "settle"
    _settle(record, [(8, "C@D", "settled")])
    assert relay.mark("settle", tuesday) is True
    assert guard.period_done("settle", guard.period_key(tuesday))
    assert _guard_outputs(monkeypatch, tuesday, {})["run"] == "false"


def test_an_operator_settle_before_the_span_does_not_use_up_the_week(record):
    monday = dt.datetime(2026, 11, 2, 18, 0, tzinfo=UTC)
    _predict(record, 8, ["C@D"])
    _settle(record, [(8, "C@D", "settled")])
    assert relay.mark("settle", monday) is False


def test_the_guard_writes_no_marker_itself(record, monkeypatch):
    tuesday = dt.datetime(2026, 11, 3, 18, 0, tzinfo=UTC)
    assert _guard_outputs(monkeypatch, tuesday, {})["mode"] == "settle"
    assert not (record / "ran").exists(), "a settle that fails must be retried"


def test_the_opening_sweep_marker(record, monkeypatch):
    thursday = dt.datetime(2026, 11, 5, 22, 30, tzinfo=UTC)
    games = [{"gameday": "2026-11-05", "gametime": "20:15", "week": "9"}]
    monkeypatch.setattr(guard, "load_games", lambda _season: games)
    assert relay.mark("open", thursday) is True
    assert guard.period_done("open", guard.period_key(thursday))


# -------------------------------------------------------- the close label

@pytest.mark.parametrize("run,minutes,expected", [
    ("close", 45.0, "close"),
    ("close", 60.0, "close"),
    ("close", 61.0, "decision"),
    ("close", 1708.0, "decision"),
    ("close", None, "close"),
    ("decision", 45.0, "decision"),
    ("open", 2000.0, "open"),
])
def test_the_label_is_judged_per_game(run, minutes, expected):
    assert record_run.row_snapshot_type(run, minutes) == expected


HEADER = ",".join(["logged_at_utc", "season", "week", "event_id", "market", "player", "line", "side"])


def test_one_run_labels_each_game_by_its_own_kickoff(tmp_path):
    f = tmp_path / "shadow_log_2026_wk08_A_B.csv"
    f.write_text(HEADER + "\n"
                 "2026-11-01T17:15:00Z,2026,8,soon,receptions,P,3.5,Over\n"
                 "2026-11-01T17:15:00Z,2026,8,late,receptions,Q,3.5,Over\n", encoding="utf-8")
    kick = {"soon": "2026-11-01T18:00:00Z", "late": "2026-11-01T21:05:00Z"}
    rows = record_run.read_shadow_log(f, "close", "A@B", {}, kick)
    assert [r["snapshot_type"] for r in rows] == ["close", "decision"]
    assert record_run.read_shadow_log(f, "close", "A@B", {}, {})[0]["snapshot_type"] == "close"


def test_a_joint_row_is_labelled_the_same_way(tmp_path):
    f = tmp_path / "joint_td_2026_wk08_A_B.csv"
    f.write_text("logged_at_utc,season,week,event_id\n2026-11-01T17:15:00Z,2026,8,late\n", encoding="utf-8")
    rows = record_run.read_joint(f, "close", "A@B", {}, {"late": "2026-11-01T21:05:00Z"})
    assert rows[0]["snapshot_type"] == "decision"
    assert record_run.read_joint(f, "close", "A@B", {})[0]["snapshot_type"] == "close"

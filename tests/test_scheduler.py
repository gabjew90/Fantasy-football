"""The scheduler after the cron-lag finding (2026-09-16).

GitHub fired this repo's crons a median 128 minutes late (worst 357). The
old dispatcher ran a job only when the Pacific wall-clock sat inside a
two-hour window, so of 38 scheduled runs only the three Tuesday fires did
anything: the planner, the healthcheck, the scout and the Sunday backstop
never ran on schedule, and the gate ticked against week-1 kickoffs into
week 2. Now: hourly fires, one run per period after the start time, a
deadline only where a late run is worse than none, and a gate that replans
when the committed plan is not for the live week.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from manager import gate, jobs
from manager.clock import PT
from manager.store import Store
from scripts import gate_guard


def _pt(y, m, d, hh, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=PT)


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "state")


def _tick(monkeypatch, store, when, dry_run=False, force=None):
    monkeypatch.setattr(jobs, "now_pt", lambda: when)
    monkeypatch.setattr(jobs, "get_store", lambda: store)
    fired = []
    for name in ("plan_week", "healthcheck", "waiver_job", "scout_job", "lineup_job"):
        monkeypatch.setattr(jobs, name, lambda dry_run=False, _n=name: fired.append(_n))
    ran = jobs.cron_tick(dry_run=dry_run, force=force)
    return ran, fired


# --------------------------------------------------------------- the design

def test_the_old_windows_would_have_missed_the_measured_lag(tmp_path):
    """Monday planner cron at 13:00 UTC, run 149 minutes late (the 09-14
    run): 11:28 PT. Inside the old window? No. Due under the new rule? Yes."""
    late = _pt(2026, 9, 14, 11, 28)
    dow, start, end = jobs.WINDOWS["plan"]
    assert not (start <= late.time() <= end)
    assert jobs.due_now("plan", late, Store(tmp_path / "state", read_only=True))


def test_a_late_monday_tick_runs_the_planner_once_and_the_next_tick_skips_it(monkeypatch, store):
    ran, fired = _tick(monkeypatch, store, _pt(2026, 9, 14, 11, 28))
    assert "plan" in ran and "plan_week" in fired
    assert "health" in ran, "the daily healthcheck is also past its start and unrun"
    ran2, fired2 = _tick(monkeypatch, store, _pt(2026, 9, 14, 12, 41))
    assert ran2 == [] and fired2 == []


def test_a_period_is_a_week_for_weekly_jobs_and_a_day_for_daily_ones():
    mon, tue, next_mon = _pt(2026, 9, 14, 12), _pt(2026, 9, 15, 12), _pt(2026, 9, 21, 12)
    assert jobs.period_key("plan", mon) == jobs.period_key("plan", tue) == "2026-W38"
    assert jobs.period_key("plan", next_mon) == "2026-W39"
    assert jobs.period_key("health", mon) != jobs.period_key("health", tue)


def test_tuesday_is_the_planners_catch_up_day_but_wednesday_is_not(monkeypatch, store):
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 15, 9, 0))
    assert "plan" in ran
    store2 = Store(store.dir.parent / "s2")
    ran, _ = _tick(monkeypatch, store2, _pt(2026, 9, 16, 9, 0))
    assert "plan" not in ran


def test_the_waiver_brief_has_a_real_deadline(monkeypatch, store):
    """Bids close at 19:00 PT. 18:06 (the measured Tuesday lag) runs; a tick
    at 21:35 (the other measured Tuesday lag) does not send a brief nobody
    can act on."""
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 15, 18, 6))
    assert "waivers" in ran
    store2 = Store(store.dir.parent / "s2")
    ran, _ = _tick(monkeypatch, store2, _pt(2026, 9, 15, 21, 35))
    assert "waivers" not in ran


def test_the_sunday_backstop_stops_before_the_early_slate(monkeypatch, store):
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 20, 9, 30))
    assert "lineup" in ran
    store2 = Store(store.dir.parent / "s2")
    ran, _ = _tick(monkeypatch, store2, _pt(2026, 9, 20, 10, 15))
    assert "lineup" not in ran


def test_scout_and_health_have_no_deadline_late_beats_never(monkeypatch, store):
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 18, 23, 30))
    assert set(ran) == {"scout", "health"}


def test_nothing_runs_before_its_start_time(monkeypatch, store):
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 14, 4, 0))
    assert ran == []


def test_the_run_is_recorded_before_the_job_so_a_crashing_job_is_not_retried_hourly(monkeypatch, store):
    monkeypatch.setattr(jobs, "now_pt", lambda: _pt(2026, 9, 18, 12, 0))
    monkeypatch.setattr(jobs, "get_store", lambda: store)

    def boom(dry_run=False):
        raise RuntimeError("scout exploded")
    monkeypatch.setattr(jobs, "scout_job", boom)
    monkeypatch.setattr(jobs, "healthcheck", lambda dry_run=False: None)
    monkeypatch.setattr(jobs, "deliver", lambda *a, **k: "printed")
    jobs.cron_tick()
    assert store.get("ran:scout:2026-W38")
    ran, _ = _tick(monkeypatch, store, _pt(2026, 9, 18, 13, 0))
    assert "scout" not in ran


def test_force_ignores_day_time_and_period(monkeypatch, store):
    ran, fired = _tick(monkeypatch, store, _pt(2026, 9, 16, 3, 0), force="waivers")
    assert ran == ["waivers"] and fired == ["waiver_job"]


def test_a_dry_run_does_not_spend_the_period(monkeypatch, tmp_path):
    ro = Store(tmp_path / "state", read_only=True)
    ran, _ = _tick(monkeypatch, ro, _pt(2026, 9, 14, 11, 28), dry_run=True)
    assert "plan" in ran
    assert ro.get("ran:plan:2026-W38") is None


# ------------------------------------------------------------ the gate heals

def _plan(root, week, generated):
    p = gate.plan_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"week": week, "generated_pt": generated.isoformat(), "checks": []}))


def test_the_gate_replans_when_the_committed_plan_is_for_another_week(tmp_path, monkeypatch):
    _plan(tmp_path, 1, _pt(2026, 8, 31, 18, 33))
    calls = []

    def fake_plan(dry_run=False):
        calls.append(dry_run)
        _plan(tmp_path, 2, _pt(2026, 9, 16, 9, 0))
        return {"week": 2, "jobs": []}
    monkeypatch.setattr(jobs, "plan_week", fake_plan)
    out = gate.run_gate(root=tmp_path, live_week=2)
    assert calls == [False] and out["healed"] is True
    assert json.loads(gate.plan_path(tmp_path).read_text())["week"] == 2


def test_the_gate_does_not_replan_a_current_plan_or_without_a_live_week(tmp_path, monkeypatch):
    _plan(tmp_path, 2, _pt(2026, 9, 14, 6, 0))
    monkeypatch.setattr(jobs, "plan_week", lambda dry_run=False: pytest.fail("must not replan"))
    assert gate.run_gate(root=tmp_path, live_week=2)["healed"] is False
    _plan(tmp_path, 1, _pt(2026, 8, 31, 6, 0))
    assert gate.run_gate(root=tmp_path)["healed"] is False, "no live week, no heal"


def test_a_failed_replan_is_reported_not_raised(tmp_path, monkeypatch):
    _plan(tmp_path, 1, _pt(2026, 8, 31, 6, 0))

    def boom(dry_run=False):
        raise RuntimeError("sleeper down")
    monkeypatch.setattr(jobs, "plan_week", boom)
    monkeypatch.setattr(jobs, "deliver", lambda *a, **k: "printed")
    out = gate.run_gate(root=tmp_path, live_week=2)
    assert out["healed"] is False and out["ran"] == 0


# ------------------------------------------------------------ the cheap guard

def test_the_guard_ticks_on_a_stale_plan_even_outside_gate_hours():
    now = datetime(2026, 9, 16, 3, 0, tzinfo=timezone.utc)      # Wed 03:00 UTC, not a gate hour
    hours = json.dumps([[7, 15], [7, 16]])
    fresh = json.dumps({"week": 2, "generated_pt": _pt(2026, 9, 14, 6).isoformat(), "checks": []})
    stale = json.dumps({"week": 1, "generated_pt": _pt(2026, 8, 31, 18).isoformat(), "checks": []})
    assert gate_guard.decide(now, hours, fresh) == (False, "outside gate hours")
    run, why = gate_guard.decide(now, hours, stale)
    assert run and "days old" in why
    assert gate_guard.decide(now, hours, None)[0] is True
    assert gate_guard.decide(now, None, "not json")[0] is True
    assert gate_guard.decide(now, hours, fresh, forced=True) == (True, "dispatched")
    sunday = datetime(2026, 9, 20, 15, 30, tzinfo=timezone.utc)
    assert gate_guard.decide(sunday, hours, fresh) == (True, "gate hour")

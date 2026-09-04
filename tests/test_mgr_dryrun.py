"""A dry run renders; it does not spend state.

`python -m manager --module waivers --dry-run --week 13` rewrote 60 lines of
state/kv.json with week-13 replacement levels. state/ is COMMITTED and shipped
to the live manager, so a rehearsal against a pinned week left real state
behind for the real run to read. The gate did the same thing at a coarser
grain: it marked checks done in the committed week plan, so a rehearsal
silently consumed the real run's work.

These assert the property directly — after a dry run, nothing under state/
changed — rather than checking any one writer, because the writers are spread
across the store, the gate and the planner and a new one is one commit away.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from manager import gate as gate_mod
from manager.store import Store


def _snapshot(d) -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(d.glob("*.json"))}


# ------------------------------------------------------------------- store

def test_a_read_only_store_reads_but_does_not_write(tmp_path):
    live = Store(tmp_path)
    live.set("fa_replacement:1", {"RB": 12.0})
    before = _snapshot(tmp_path)

    dry = Store(tmp_path, read_only=True)
    assert dry.get("fa_replacement:1") == {"RB": 12.0}, "a dry run still reads"
    dry.set("fa_replacement:13", {"RB": 99.0})
    dry.save_message("waivers:13", "id", "hash")
    dry.record_bid(13, "Some Player", 40)
    assert dry.first_time("alert:x") is True, "a dry run still shows the alert"

    assert _snapshot(tmp_path) == before, "a dry run wrote to state/"
    assert set(dry.suppressed) == {"kv", "messages", "bids", "seen"}


def test_a_read_only_store_does_not_even_create_the_directory(tmp_path):
    missing = tmp_path / "state"
    Store(missing, read_only=True).set("k", "v")
    assert not missing.exists()
    Store(missing).set("k", "v")
    assert (missing / "kv.json").exists()


# -------------------------------------------------------------------- gate

def _job(when):
    return {"id": "c1", "kind": "waiver_brief", "info": "", "when": when}


def test_build_plan_is_pure_and_write_plan_is_the_only_writer(tmp_path):
    when = datetime.now(tz=timezone.utc) + timedelta(hours=3)
    plan = gate_mod.build_plan(4, [_job(when)], root=tmp_path)
    assert plan["week"] == 4 and len(plan["checks"]) == 1
    assert not (tmp_path / "state").exists(), "build_plan wrote a file"

    gate_mod.write_plan(4, [_job(when)], root=tmp_path)
    written = json.loads(gate_mod.plan_path(tmp_path).read_text(encoding="utf-8"))
    assert written["checks"] == plan["checks"]


def test_build_plan_still_carries_done_flags_forward(tmp_path):
    when = datetime.now(tz=timezone.utc) + timedelta(hours=3)
    gate_mod.write_plan(4, [_job(when)], root=tmp_path)
    p = gate_mod.plan_path(tmp_path)
    d = json.loads(p.read_text(encoding="utf-8"))
    d["checks"][0]["done"] = True
    p.write_text(json.dumps(d), encoding="utf-8")

    assert gate_mod.build_plan(4, [_job(when)], root=tmp_path)["checks"][0]["done"] is True
    assert gate_mod.build_plan(5, [_job(when)], root=tmp_path)["checks"][0]["done"] is False


def test_a_dry_gate_tick_does_not_mark_checks_done(tmp_path, monkeypatch):
    # a check that is due right now
    due = datetime.now(tz=timezone.utc) - timedelta(minutes=5)
    gate_mod.write_plan(4, [_job(due)], root=tmp_path)
    p = gate_mod.plan_path(tmp_path)
    before = p.read_text(encoding="utf-8")

    fired = []
    import manager.jobs as jobs_mod
    monkeypatch.setattr(jobs_mod, "run_job", lambda job, dry_run=False: fired.append(dry_run))

    r = gate_mod.run_gate(dry_run=True, root=tmp_path)
    assert r["ran"] == 1 and fired == [True], "the check must still RUN"
    assert p.read_text(encoding="utf-8") == before, "a dry tick spent the real plan"

    gate_mod.run_gate(dry_run=False, root=tmp_path)
    after = json.loads(p.read_text(encoding="utf-8"))
    assert after["checks"][0]["done"] is True, "a live tick must still mark it"


# ------------------------------------------------------------------ wiring

def test_the_cli_puts_the_store_in_read_only_for_a_dry_run():
    """The flag has to reach get_store(), which is called from nine places
    including _safe()'s error path."""
    import inspect

    from manager import __main__ as cli
    from manager import jobs as jobs_mod

    assert "jobs.configure(dry_run=args.dry_run)" in inspect.getsource(cli)
    try:
        jobs_mod.configure(dry_run=True)
        assert jobs_mod.get_store().read_only is True
        jobs_mod.configure(dry_run=False)
        assert jobs_mod.get_store().read_only is False
    finally:
        jobs_mod.configure(dry_run=False)


def test_plan_week_guards_its_two_direct_state_writes():
    """gate_hours.json and week_plan.json are written outside the store, so
    the read-only flag cannot reach them and they need their own guard."""
    import inspect

    from manager import jobs as jobs_mod
    src = inspect.getsource(jobs_mod.plan_week)
    assert "if dry_run:" in src
    assert src.index("if dry_run:") < src.index("gate_mod.write_plan(week, jobs)")
    assert "gate_mod.build_plan(week, jobs)" in src


@pytest.mark.parametrize("name", ["kv", "seen", "messages", "bids"])
def test_every_store_file_goes_through_the_one_guarded_writer(name, tmp_path):
    """A new writer that calls _save gets the guard for free; one that calls
    write_text directly does not, and this is what would catch it."""
    import inspect
    src = inspect.getsource(Store)
    assert src.count("write_text") == 1, "state writes must all go through _save"
    s = Store(tmp_path, read_only=True)
    s._save(name, {"x": 1})
    assert not (tmp_path / f"{name}.json").exists()

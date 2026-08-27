"""Gate semantics acceptance tests (Module 0, Actions edition):
not-yet-due, due, late-but-eligible, expired, already-done — plus UTC<->PT
window derivation across the Nov 1 2026 DST shift (crons are UTC, so
PT-fixed events move by an hour in UTC and the gate windows must cover both).
"""

import json
from datetime import datetime, timedelta, timezone

from manager.clock import PT
from manager.gate import (check_status, gate_hours_utc, to_plan_check,
                          write_plan)

KICKOFF = datetime(2026, 9, 13, 10, 0, tzinfo=PT)  # Sunday main slate


def _check():
    job = {"id": "wk1:slate_check:0913T0840", "kind": "slate_check",
           "when": datetime(2026, 9, 13, 8, 40, tzinfo=PT),  # inactives + 10
           "info": "x", "teams": ["ATL"], "kickoff": KICKOFF.isoformat()}
    return to_plan_check(job)


def _utc(dt_pt):
    return dt_pt.astimezone(timezone.utc)


def test_gate_five_states():
    c = _check()
    target = datetime(2026, 9, 13, 8, 40, tzinfo=PT)
    due = target - timedelta(minutes=10)          # 8:30 PT — the cron buffer
    assert check_status(c, _utc(due - timedelta(minutes=5))) == "pending"
    assert check_status(c, _utc(due + timedelta(minutes=1))) == "due"
    assert check_status(c, _utc(due + timedelta(minutes=40))) == "due"  # late tick still eligible
    assert check_status(c, _utc(due + timedelta(minutes=50))) == "expired"
    c["done"] = True
    assert check_status(c, _utc(due + timedelta(minutes=1))) == "done"


def test_plan_write_preserves_done_flags(tmp_path):
    job = {"id": "wk1:a", "kind": "injury_sweep",
           "when": datetime(2026, 9, 9, 8, 0, tzinfo=PT), "info": ""}
    write_plan(1, [job], root=tmp_path)
    plan = json.loads((tmp_path / "state" / "week_plan.json").read_text())
    plan["checks"][0]["done"] = True
    (tmp_path / "state" / "week_plan.json").write_text(json.dumps(plan))
    write_plan(1, [job], root=tmp_path)  # planner re-run must not resurrect it
    plan2 = json.loads((tmp_path / "state" / "week_plan.json").read_text())
    assert plan2["checks"][0]["done"] is True
    write_plan(2, [job], root=tmp_path)  # new week resets
    plan3 = json.loads((tmp_path / "state" / "week_plan.json").read_text())
    assert plan3["checks"][0]["done"] is False


def test_gate_hours_cover_check_windows():
    c = _check()  # due 8:30 PT = 15:30 UTC (PDT), Sunday
    hours = gate_hours_utc([c])
    assert [7, 15] in hours and [7, 16] in hours  # window + slack spills into 16:00


def test_dst_shift_moves_utc_hour():
    # same 8:30 AM PT check before and after Nov 1 2026 fall-back:
    before = to_plan_check({"id": "a", "kind": "injury_sweep", "info": "",
                            "when": datetime(2026, 10, 25, 8, 40, tzinfo=PT)})
    after = to_plan_check({"id": "b", "kind": "injury_sweep", "info": "",
                           "when": datetime(2026, 11, 8, 8, 40, tzinfo=PT)})
    h_before = datetime.fromisoformat(before["due_utc"]).hour
    h_after = datetime.fromisoformat(after["due_utc"]).hour
    assert h_before == 15 and h_after == 16  # PT-fixed event moved an hour in UTC
    # and the derived gate hours cover each week's actual offset
    assert [7, 15] in gate_hours_utc([before])
    assert [7, 16] in gate_hours_utc([after])

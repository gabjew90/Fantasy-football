"""manager.injuries: the code behind every [ACT NOW] alert had no tests
(review 2026-09-16). Sweeps alert on CHANGES only, once per change; slate
checks name the replacement and the minutes to lock, once per starter.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from manager import injuries
from manager.clock import PT
from manager.store import Store


def _p(pid, name, pos, team, status=""):
    return {"sleeper_id": pid, "name": name, "pos": pos, "team": team, "status": status}


def _ctx(mine, starters=None, week=2):
    return {"my_rid": 1, "week": week, "roster_players": {1: mine},
            "current_starters": starters or [p["sleeper_id"] for p in mine]}


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "state")


# ------------------------------------------------------------------ sweep

def test_first_sweep_reports_every_designation_then_only_changes(store):
    mine = [_p("1", "A.J. Brown", "WR", "NE", "IR"), _p("2", "Jahmyr Gibbs", "RB", "DET"),
            _p("3", "Sam LaPorta", "TE", "DET", "Questionable")]
    first = injuries.sweep(_ctx(mine), store)
    assert first == ["🔴 **A.J. Brown** (WR): healthy -> IR",
                     "🟡 **Sam LaPorta** (TE): healthy -> Questionable"], "a healthy player is not news"
    assert injuries.sweep(_ctx(mine), store) == [], "nothing changed"
    mine[2]["status"] = ""
    mine[1]["status"] = "Out"
    second = injuries.sweep(_ctx(mine), store)
    assert second == ["🔴 **Jahmyr Gibbs** (RB): healthy -> Out",
                      "🟢 **Sam LaPorta** (TE): Questionable -> healthy"]
    assert store.get("inj_snapshot") == {"1": "IR", "2": "Out", "3": ""}


def test_a_change_alerts_once_even_if_the_snapshot_is_lost(store):
    mine = [_p("1", "A.J. Brown", "WR", "NE", "Out")]
    assert injuries.sweep(_ctx(mine), store)
    store.set("inj_snapshot", {})                    # snapshot wiped, seen-set intact
    assert injuries.sweep(_ctx(mine), store) == [], "the alert id inj:1:Out was already sent"


def test_bad_statuses_are_red_and_the_rest_yellow(store):
    mine = [_p(str(i), f"P{i}", "RB", "DET", s) for i, s in enumerate(injuries.BAD + ("Questionable",))]
    marks = [a[0] for a in injuries.sweep(_ctx(mine), store)]
    assert marks == ["🔴"] * len(injuries.BAD) + ["🟡"]


# ------------------------------------------------------------ slate check

def test_a_starter_ruled_out_in_this_slate_gets_a_concrete_instruction(store, monkeypatch):
    kickoff = datetime(2026, 9, 20, 10, 0, tzinfo=PT)
    monkeypatch.setattr(injuries, "minutes_until", lambda dt: 80)
    mine = [_p("1", "Jahmyr Gibbs", "RB", "DET", "Out"), _p("2", "Drake London", "WR", "ATL", "Out"),
            _p("3", "Rico Dowdle", "RB", "PIT")]
    store.set("contingency:2", {"Jahmyr Gibbs": "Rico Dowdle (RB)"})
    ctx = _ctx(mine, starters=["1", "2"])
    lines = injuries.slate_check(ctx, store, ["DET", "PIT"], kickoff)
    assert lines == ["🔴 **Jahmyr Gibbs is Out. Bench Jahmyr Gibbs, start Rico Dowdle (RB).** 80 minutes until lock."]
    assert injuries.slate_check(ctx, store, ["DET", "PIT"], kickoff) == [], "once per starter per status"
    later = injuries.slate_check(ctx, store, ["ATL"], kickoff)
    assert later == ["🔴 **Drake London is Out. Bench Drake London, start best healthy bench player at the position.** 80 minutes until lock."]


def test_bench_players_questionable_starters_and_other_slates_are_silent(store, monkeypatch):
    monkeypatch.setattr(injuries, "minutes_until", lambda dt: 30)
    mine = [_p("1", "Jahmyr Gibbs", "RB", "DET", "Questionable"), _p("2", "Rico Dowdle", "RB", "PIT", "Out"),
            _p("3", "Drake London", "WR", "ATL", "Out")]
    ctx = _ctx(mine, starters=["1", "3"])
    assert injuries.slate_check(ctx, store, ["DET", "PIT"], datetime.now(tz=PT)) == []


def test_a_new_status_re_alerts(store, monkeypatch):
    monkeypatch.setattr(injuries, "minutes_until", lambda dt: 30)
    mine = [_p("1", "Jahmyr Gibbs", "RB", "DET", "Doubtful")]
    ctx = _ctx(mine, starters=["1"])
    assert injuries.slate_check(ctx, store, ["DET"], datetime.now(tz=PT))
    mine[0]["status"] = "Out"
    assert injuries.slate_check(ctx, store, ["DET"], datetime.now(tz=PT))

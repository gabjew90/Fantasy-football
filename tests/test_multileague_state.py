"""Two leagues, two state directories, one guard (2026-09-16).

One `state/` served every league while only Omnibeta ran. The store keys,
the week plan and the gate hours are all per league, so scheduling
Keefamania beside it would have consumed Omnibeta's runs and overwritten
its plan. The default league keeps `state/`; every other league gets
`state/<league>/`; the gate guard reads them all; Yahoo's refresh token
bootstraps the token file on a fresh checkout.
"""

from __future__ import annotations

import datetime as dt
import json
import pathlib

import pytest

from manager import context, gate, jobs, yahoo_api
from scripts import gate_guard


class Cfg(dict):
    def __init__(self, league_name, default="omnibeta"):
        super().__init__({"default_league": default})
        self.league_name = league_name


def _configure(monkeypatch, league):
    monkeypatch.setattr(context.Config, "load", staticmethod(lambda league=None: Cfg(league or "omnibeta")))
    context.configure(league=league)


def test_the_default_league_keeps_state_and_the_others_get_a_subdirectory(monkeypatch):
    _configure(monkeypatch, None)
    assert context.state_dir() == pathlib.Path("state")
    _configure(monkeypatch, "omnibeta")
    assert context.state_dir() == pathlib.Path("state")
    _configure(monkeypatch, "keefamania")
    assert context.state_dir() == pathlib.Path("state") / "keefamania"
    context.configure()


def test_store_and_plan_follow_the_league(monkeypatch):
    _configure(monkeypatch, "keefamania")
    try:
        assert jobs.get_store().dir == pathlib.Path("state") / "keefamania"
        assert gate.plan_path() == pathlib.Path("state") / "keefamania" / "week_plan.json"
        assert gate.plan_path("x") == pathlib.Path("x") / "state" / "week_plan.json", "the test seam is unchanged"
    finally:
        context.configure()


def test_a_run_recorded_for_one_league_does_not_consume_the_other(monkeypatch, tmp_path):
    from manager.store import Store
    now = dt.datetime(2026, 9, 14, 11, 28, tzinfo=jobs.PT)
    a, b = Store(tmp_path / "state"), Store(tmp_path / "state" / "keefamania")
    a.set(f"ran:plan:{jobs.period_key('plan', now)}", "x")
    assert not jobs.due_now("plan", now, a)
    assert jobs.due_now("plan", now, b)


# ---------------------------------------------------------------- the guard

def _plan(d, week, when):
    d.mkdir(parents=True, exist_ok=True)
    (d / "week_plan.json").write_text(json.dumps({"week": week, "generated_pt": when.isoformat(), "checks": []}))


def test_the_guard_reads_every_league_directory(tmp_path):
    state = tmp_path / "state"
    fresh = dt.datetime(2026, 9, 14, 6, tzinfo=jobs.PT)
    _plan(state, 2, fresh)
    (state / "gate_hours.json").write_text(json.dumps([[7, 15]]))
    _plan(state / "keefamania", 2, fresh)
    (state / "keefamania" / "gate_hours.json").write_text(json.dumps([[4, 22]]))
    (state / "vegas").mkdir()                       # snapshots, not a league
    assert [d.name for d in gate_guard.league_dirs(state)] == ["state", "keefamania"]
    thu = dt.datetime(2026, 9, 17, 22, 5, tzinfo=dt.timezone.utc)
    run, why = gate_guard.decide_all(thu, state)
    assert run and why == "keefamania: gate hour"
    wed = dt.datetime(2026, 9, 16, 3, 0, tzinfo=dt.timezone.utc)
    run, why = gate_guard.decide_all(wed, state)
    assert not run and "default: outside gate hours" in why and "keefamania: outside gate hours" in why


def test_a_league_with_no_plan_yet_makes_the_guard_tick(tmp_path):
    state = tmp_path / "state"
    _plan(state, 2, dt.datetime(2026, 9, 14, 6, tzinfo=jobs.PT))
    (state / "gate_hours.json").write_text("[]")
    (state / "keefamania").mkdir()
    (state / "keefamania" / "gate_hours.json").write_text("[]")
    run, why = gate_guard.decide_all(dt.datetime(2026, 9, 16, 3, tzinfo=dt.timezone.utc), state)
    assert run and why == "keefamania: no week plan"


# --------------------------------------------------------- the yahoo token

def test_the_refresh_token_secret_bootstraps_a_missing_token_file(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    monkeypatch.delenv("YAHOO_REFRESH_TOKEN", raising=False)
    assert yahoo_api._load(path) is None
    monkeypatch.setenv("YAHOO_REFRESH_TOKEN", "R-from-secret")
    seed = yahoo_api._load(path)
    assert seed["refresh_token"] == "R-from-secret" and seed["obtained_at"] == 0
    monkeypatch.setenv("YAHOO_CLIENT_ID", "id")
    monkeypatch.setenv("YAHOO_CLIENT_SECRET", "secret")
    posted = {}

    class R:
        status_code = 200
        text = json.dumps({"access_token": "A", "expires_in": 3600})

        def json(self):
            return json.loads(self.text)

    monkeypatch.setattr(yahoo_api.requests, "post", lambda url, data=None, headers=None, timeout=None: posted.update(data) or R())
    assert yahoo_api.access_token(path) == "A"
    assert posted["grant_type"] == "refresh_token" and posted["refresh_token"] == "R-from-secret"
    assert json.loads(path.read_text())["refresh_token"] == "R-from-secret", "the secret survives into the file"

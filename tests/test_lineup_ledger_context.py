"""What the lineup knew when it chose, kept where hindsight can read it.

The ledger row already carried the starters, the pool and every projection
that picked them, which answers "was there a better lineup" after the fact.
It could not answer the question that actually follows a bad Sunday: did the
optimiser start someone it had reason to doubt? The injury designations live
in the store and move every hour, so by Tuesday they no longer say what
Sunday morning said, and the if-inactive table was overwritten week by week
under a single key. Both now ride on the row itself.
"""

from __future__ import annotations

import pytest

from manager import consensus, ledger, lineup_opt
from manager.store import Store


class Cfg:
    league_name = "testleague"


def _player(pid, name, pos, weekly, status=""):
    return {"sleeper_id": pid, "name": name, "pos": pos, "weekly": weekly,
            "team": "SF", "status": status}


ROSTER = [
    _player("1", "A Quarterback", "QB", 20.0),
    _player("2", "B Back", "RB", 15.0, status="Questionable"),
    _player("3", "C Back", "RB", 12.0),
    _player("4", "D Wideout", "WR", 14.0),
    _player("5", "E Wideout", "WR", 11.0, status="Out"),
    _player("6", "F End", "TE", 9.0),
    _player("7", "G Back", "RB", 8.0),
]


@pytest.fixture
def ctx():
    return {"cfg": Cfg(), "state": {"season": "2026"}, "week": 3, "my_rid": 1,
            "league": {"scoring_settings": {}},
            "slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 0,
            "flex_slots": None, "source": None, "schedule": {},
            "roster_players": {1: [dict(p) for p in ROSTER]},
            "current_starters": [], "scfg": {}}


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """The brief's inputs are fetched elsewhere and tested elsewhere."""
    monkeypatch.setattr(consensus, "build", lambda ctx, store: ({}, []))
    monkeypatch.setattr(lineup_opt, "implied_totals",
                        lambda store, **kw: ({}, None))


def _row(ctx, tmp_path) -> dict:
    store = Store(tmp_path / "state" / "testleague")
    lineup_opt.build(ctx, store)
    rows = ledger.read_week(store, "2026", 3)
    lineup = [r for r in rows if r["kind"] == "lineup"]
    assert len(lineup) == 1
    return lineup[0]


def test_the_ledger_row_records_the_designations_as_they_stood(ctx, tmp_path):
    """A blank status is a real answer -- the platform reported him healthy
    at decision time -- so only the non-empty ones are written, and reading
    the row means "absent from this map means no designation"."""
    row = _row(ctx, tmp_path)
    assert row["status"] == {"2": "Questionable", "5": "Out"}
    # The starters are the row's own question: B Back started Questionable.
    assert "2" in row["starters"]


def test_the_if_inactive_plan_rides_on_the_row_not_a_single_store_key(
        ctx, tmp_path):
    """`contingency:<week>` is one key per week in a store that is rewritten
    every run. The plan that stood beside a given recommendation has to be
    attached to that recommendation or it cannot be graded."""
    row = _row(ctx, tmp_path)
    assert row["contingency"], "a Questionable starter and a healthy bench RB"
    # C Back is already the other starting RB, so the replacement named is
    # the best healthy RB still on the bench.
    assert "B Back" in row["contingency"]
    assert "G Back" in row["contingency"]["B Back"]


def test_a_clean_bill_of_health_leaves_both_fields_empty_not_absent(
        ctx, tmp_path):
    """The schema must not change shape with the week, or every reader of the
    ledger needs a branch."""
    for p in ctx["roster_players"][1]:
        p["status"] = ""
    row = _row(ctx, tmp_path)
    assert row["status"] == {} and row["contingency"] == {}

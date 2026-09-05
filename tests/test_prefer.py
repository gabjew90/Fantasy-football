"""engine.prefer: the user's named calls inside a market (2026-09-05, Chase
over Nacua at pick 3)."""

import copy

import pytest

from draftkit.tracker import Tracker
from test_slot_markets import make_tracker, player


def _board():
    a = player("nacua", "WR", 104.6, 90.3, 5.0, rank=1)
    b = player("chase", "WR", 103.0, 88.7, 3.5, rank=2)
    a["name"], b["name"] = "Puka Nacua", "Ja'Marr Chase"
    a["proj_pts"], b["proj_pts"] = 248.4, 246.8
    c = player("rb1", "RB", 60.0, 60.0, 9.0, rank=1)
    c["proj_pts"] = 218.0
    return [a, b, c]


def test_the_preferred_name_takes_the_market_row_and_says_so():
    t = make_tracker(_board(), [], current_pick=3)
    t.apply_engine_cfg({"prefer": [["Ja'Marr Chase", "Puka Nacua"]]})
    wr = next(r for r in t.recommendations(5) if r[2]["pos"] == "WR")
    assert wr[2]["sleeper_id"] == "chase"
    assert "USER PREFERENCE: Ja'Marr Chase over Puka Nacua" in wr[1]


def test_without_the_preference_the_market_best_stands():
    t = make_tracker(_board(), [], current_pick=3)
    t.apply_engine_cfg({})
    wr = next(r for r in t.recommendations(5) if r[2]["pos"] == "WR")
    assert wr[2]["sleeper_id"] == "nacua" and "USER PREFERENCE" not in wr[1]


def test_the_preference_is_inert_when_the_preferred_man_is_gone():
    board = [p for p in _board() if p["sleeper_id"] != "chase"]
    t = make_tracker(board, [], current_pick=3)
    t.apply_engine_cfg({"prefer": [["Ja'Marr Chase", "Puka Nacua"]]})
    wr = next(r for r in t.recommendations(5) if r[2]["pos"] == "WR")
    assert wr[2]["sleeper_id"] == "nacua"


def test_a_malformed_entry_is_refused():
    t = object.__new__(Tracker)
    with pytest.raises(ValueError):
        t.apply_engine_cfg({"prefer": ["Ja'Marr Chase"]})

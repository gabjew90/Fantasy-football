"""One call per player/market per event.

The record keeps every priced line at every moment. A scorecard must count
decisions, and week 2 proved the two are not the same: 33 rows for a 32-line
board, because Christian McCaffrey's rush-yards Under was captured at 58.5
and then at 59.5 thirteen minutes later, and `line` is part of the dedupe key.

The fixture is a frozen copy of that file as it stood on 2026-09-18, so a
later recapture of the same game cannot change what these tests assert.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))

import calls  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "wk02_2026-09-18.jsonl"


@pytest.fixture
def wk02() -> list[dict]:
    return [json.loads(line) for line in FIXTURE.open(encoding="utf-8")
            if line.strip()]


def _row(**kw) -> dict:
    base = {"season": 2026, "week": 2, "event_id": "ev1", "book": "sleeper",
            "market": "player_rush_yds", "player": "A Player", "side": "Under",
            "line": 50.5, "snapshot_type": "decision", "engine_hash": "aaa",
            "logged_at_utc": "2026-09-18T05:00:00Z", "gap": 0.06}
    base.update(kw)
    return base


# ------------------------------------------------------- the real week-2 board

def test_the_33_row_board_is_32_calls(wk02):
    assert len(wk02) == 33
    n, ties = calls.mark_calls(wk02)
    assert (n, ties) == (32, 0)
    assert sum(1 for r in wk02 if r["is_call"]) == 32


def test_the_moved_line_keeps_its_history_and_the_later_one_is_the_call(wk02):
    calls.mark_calls(wk02)
    mccaffrey = sorted((r for r in wk02
                        if r["player"].startswith("Christian McCaffrey")
                        and r["market"] == "player_rush_yds"),
                       key=lambda r: r["logged_at_utc"])
    assert len(mccaffrey) == 2, "the fixture must still hold both captures"
    early, late = mccaffrey
    assert (early["line"], early["is_call"]) == (58.5, False)
    assert (late["line"], late["is_call"]) == (59.5, True)


def test_every_market_on_the_board_has_exactly_one_call(wk02):
    calls.mark_calls(wk02)
    seen: dict[tuple, int] = {}
    for row in wk02:
        if row["is_call"]:
            key = calls.call_key(row)
            seen[key] = seen.get(key, 0) + 1
    assert set(seen.values()) == {1}
    assert len(seen) == 32


# ----------------------------------------------------------------- the rule

def test_the_call_is_the_last_decision_not_the_first():
    rows = [_row(line=58.5, logged_at_utc="2026-09-18T05:07:37Z"),
            _row(line=59.5, logged_at_utc="2026-09-18T05:20:46Z")]
    best, ties = calls.select_calls(rows)
    assert ties == 0
    assert list(best.values())[0]["line"] == 59.5


def test_a_side_flip_is_still_one_call():
    """`side` is an attribute of the call, not part of its identity: if the
    model changed its mind between ticks that is one decision, and the last
    one is what would have been placed."""
    rows = [_row(side="Under", logged_at_utc="2026-09-18T05:00:00Z"),
            _row(side="Over", logged_at_utc="2026-09-18T05:15:00Z")]
    best, _ties = calls.select_calls(rows)
    assert len(best) == 1
    assert list(best.values())[0]["side"] == "Over"


def test_calls_are_counted_per_engine():
    """Two versions' calls are never pooled, so each engine gets its own."""
    rows = [_row(engine_hash="aaa", logged_at_utc="2026-09-18T05:00:00Z"),
            _row(engine_hash="bbb", logged_at_utc="2026-09-18T05:15:00Z")]
    best, _ties = calls.select_calls(rows)
    assert len(best) == 2
    assert {r["engine_hash"] for r in best.values()} == {"aaa", "bbb"}


def test_open_and_close_rows_are_never_calls():
    """A price-only snapshot is not a decision. A game captured only inside
    the closing window therefore has no call, deliberately."""
    rows = [_row(snapshot_type="open", logged_at_utc="2026-09-17T22:30:00Z"),
            _row(snapshot_type="close", logged_at_utc="2026-09-20T19:45:00Z")]
    n, _ties = calls.mark_calls(rows)
    assert n == 0
    assert [r["is_call"] for r in rows] == [False, False]


def test_a_same_second_tie_is_broken_deterministically_and_counted():
    a = _row(line=None, gap=0.09, logged_at_utc="2026-09-18T05:00:00Z")
    b = _row(line=50.5, gap=0.02, logged_at_utc="2026-09-18T05:00:00Z")
    best, ties = calls.select_calls([a, b])
    assert ties == 1
    assert list(best.values())[0]["line"] == 50.5, "a row with a line wins"
    # and the same input always elects the same row, whatever the order
    best2, _ = calls.select_calls([b, a])
    assert list(best2.values())[0]["line"] == 50.5


def test_an_unparseable_timestamp_raises_rather_than_sorting_wrongly():
    """String order would silently elect the wrong call."""
    rows = [_row(logged_at_utc="2026-09-18T05:00:00Z"),
            _row(logged_at_utc="18/09/2026 05:30")]
    with pytest.raises(ValueError):
        calls.select_calls(rows)
    with pytest.raises(ValueError):
        calls.parse_logged_at({"logged_at_utc": ""})


def test_mark_calls_flags_rows_in_place_and_does_not_persist_the_flag(wk02):
    """`is_call` is derived state: settle writes it to the settled CSV, but a
    prediction row must never carry it, because a later tick supersedes."""
    assert all("is_call" not in r for r in wk02), \
        "the committed record must not hold is_call"
    calls.mark_calls(wk02)
    assert all("is_call" in r for r in wk02)


# ------------------------------------------------------ the closing-line side

def test_last_per_takes_the_latest_close_not_the_first():
    """guard.py marks a whole run `close` when the soonest kickoff is inside
    the hour, so an early-afternoon run also stamps the late games. Taking
    the first close would report a 12:15 line as a 16:25 game's close."""
    early = _row(snapshot_type="close", line=51.5,
                 logged_at_utc="2026-09-20T16:15:00Z")
    late = _row(snapshot_type="close", line=49.5,
                logged_at_utc="2026-09-20T20:05:00Z")
    market_key = tuple(f for f in calls.CALL_KEY if f != "engine_hash")
    best = calls.last_per([early, late], "close", market_key)
    assert len(best) == 1
    assert list(best.values())[0]["line"] == 49.5


def test_the_close_side_ignores_the_engine():
    """The closing price is a market fact: if the engine changed between the
    decision and the close, the deciding engine still gets its CLV."""
    market_key = tuple(f for f in calls.CALL_KEY if f != "engine_hash")
    rows = [_row(snapshot_type="close", engine_hash="aaa",
                 logged_at_utc="2026-09-20T20:00:00Z"),
            _row(snapshot_type="close", engine_hash="bbb", line=48.5,
                 logged_at_utc="2026-09-20T20:05:00Z")]
    best = calls.last_per(rows, "close", market_key)
    assert len(best) == 1, "one market, one closing line"
    assert list(best.values())[0]["line"] == 48.5


def test_two_releases_with_one_pricing_model_make_one_call():
    """A docs-only release re-captures the same line under a new engine hash;
    same price_hash, so the later tick is the call, not a second call."""
    import calls
    a = {"season": 2026, "week": 3, "event_id": "e", "book": "sleeper", "market": "player_receptions",
         "player": "P", "side": "Over", "line": 4.5, "snapshot_type": "decision",
         "engine_hash": "aaa", "price_hash": "ppp", "logged_at_utc": "2026-09-20T10:00:00Z"}
    b = dict(a, engine_hash="bbb", logged_at_utc="2026-09-20T11:00:00Z")
    c = dict(a, engine_hash="ccc", price_hash="qqq", logged_at_utc="2026-09-20T12:00:00Z")
    best, _ties = calls.select_calls([a, b, c])
    assert len(best) == 2, "two pricing models, two calls"
    assert {r["engine_hash"] for r in best.values()} == {"bbb", "ccc"}

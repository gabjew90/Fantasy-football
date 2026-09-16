"""The ledger (season-manager v2 layer 4, built 2026-09-16): every
recommendation written down at emission, graded against actuals after the
week, one pre-registered ruler per kind."""

from __future__ import annotations

import json

import pytest

from manager import ledger
from manager.store import Store

SHAPE = {"slots": {"QB": 1, "RB": 2, "WR": 2, "TE": 1}, "flex": 1, "flex_slots": None}


class Cfg:
    league_name = "testleague"


def _ctx(week=2, source=None):
    return {"cfg": Cfg(), "state": {"season": "2026"}, "week": week, "my_rid": 3,
            "league": {"scoring_settings": {"rush_yd": 0.1, "rec": 0.5, "rec_yd": 0.1, "rush_td": 6.0}},
            "slots": SHAPE["slots"], "flex": 1, "flex_slots": None, "source": source}


@pytest.fixture
def store(tmp_path):
    return Store(tmp_path / "state" / "testleague")


# ---------------------------------------------------------------- emission

def test_emit_appends_rows_with_provenance_and_a_dry_run_writes_nothing(store, tmp_path):
    n = ledger.emit(store, _ctx(), "scout", [{"subject": "scout:2", "margin": -5.8, "win_prob": 0.41}])
    assert n == 1
    rows = ledger.read_week(store, "2026", 2)
    assert rows[0]["kind"] == "scout" and rows[0]["week"] == 2 and rows[0]["margin"] == -5.8
    assert rows[0]["provenance"]["league"] == "testleague" and "commit" in rows[0]["provenance"]
    ro = Store(tmp_path / "state" / "ro", read_only=True)
    assert ledger.emit(ro, _ctx(), "scout", [{"subject": "x"}]) == 0
    assert not (tmp_path / "state" / "ro").exists()


def test_emit_rejects_an_unknown_kind_and_skips_empty(store):
    with pytest.raises(ValueError, match="kind"):
        ledger.emit(store, _ctx(), "vibes", [{"subject": "x"}])
    assert ledger.emit(store, _ctx(), "lineup", []) == 0


def test_the_latest_row_per_subject_is_the_one_that_stood_at_lock(store, monkeypatch):
    times = iter([100.0, 200.0, 300.0])
    monkeypatch.setattr(ledger.time, "time", lambda: next(times))
    ledger.emit(store, _ctx(), "lineup", [{"subject": "lineup:2", "starters": ["a"]}])
    ledger.emit(store, _ctx(), "lineup", [{"subject": "lineup:2", "starters": ["b"]}])
    ledger.emit(store, _ctx(), "waiver_add", [{"subject": "add:9", "pid": "9"}])
    rows = ledger.read_week(store, "2026", 2)
    assert ledger.latest_per_subject(rows, "lineup")["lineup:2"]["starters"] == ["b"]
    assert set(ledger.latest_per_subject(rows, "waiver_add")) == {"add:9"}


# ----------------------------------------------------------------- rulers

def test_lineup_grade_is_chosen_over_best_in_hindsight():
    row = {"starters": ["qb", "rb1", "rb2", "wr1", "wr2", "te", "wr3"],
           "pool": ["qb", "rb1", "rb2", "wr1", "wr2", "te", "wr3", "rb3", "wr4"],
           "pos": {"qb": "QB", "rb1": "RB", "rb2": "RB", "wr1": "WR", "wr2": "WR", "te": "TE",
                   "wr3": "WR", "rb3": "RB", "wr4": "WR"},
           "projected": {"qb": 20, "rb1": 15, "rb2": 12, "wr1": 14, "wr2": 11, "te": 9, "wr3": 10}}
    actual = {"qb": 22, "rb1": 10, "rb2": 8, "wr1": 15, "wr2": 6, "te": 7, "wr3": 4, "rb3": 19, "wr4": 12}
    g = ledger.grade_lineup(row, actual, SHAPE)
    assert g["chosen_pts"] == 72.0
    # best in hindsight swaps wr3 (4) for rb3 (19) in the flex and wr2 (6) for wr4 (12)
    assert g["best_pts"] == 93.0 and g["efficiency"] == round(72 / 93, 3) and g["left_on_bench"] == 21.0
    assert g["projected_pts"] == 91.0


def test_scout_grade_is_margin_error_and_brier():
    g = ledger.grade_scout({"margin": -5.8, "win_prob": 0.41}, 121.0, 110.0)
    assert g == {"graded": True, "actual_margin": 11.0, "margin_error": 16.8, "won": 1.0, "brier": round((0.41 - 1) ** 2, 4)}
    assert ledger.grade_scout({"margin": 1, "win_prob": 0.5}, None, None) == {"graded": False}


def test_waiver_and_trade_grades():
    actual = {"add": 14.2, "drop": 3.1, "g1": 10.0, "g2": 5.0, "r1": 20.0}
    assert ledger.grade_waiver({"pid": "add", "drop_pid": "drop"}, actual) == {"add_pts": 14.2, "drop_pts": 3.1, "delta": 11.1}
    assert ledger.grade_waiver({"pid": "add"}, actual)["delta"] is None
    assert ledger.grade_trade({"give": ["g1", "g2"], "get": ["r1"]}, actual) == {"gave_pts": 15.0, "got_pts": 20.0, "realised": 5.0}


# ------------------------------------------------------------- grade_week

def test_grade_week_grades_every_kind_and_writes_the_file(store):
    ctx = _ctx()
    ledger.emit(store, ctx, "lineup", [{"subject": "lineup:2", "starters": ["a", "b"], "pool": ["a", "b", "c"],
                                        "pos": {"a": "RB", "b": "RB", "c": "RB"}, "projected": {"a": 10, "b": 9}}])
    ledger.emit(store, ctx, "scout", [{"subject": "scout:2", "margin": 3.0, "win_prob": 0.6}])
    ledger.emit(store, ctx, "waiver_add", [{"subject": "add:w", "pid": "w", "name": "W", "cls": "breakout", "rank": 1, "drop_pid": "c"}])
    ledger.emit(store, ctx, "trade_offer", [{"subject": "trade:7:a->x", "give": ["a"], "get": ["x"], "my_ppg": 1.2, "send": True}])
    actual = {"a": 12.0, "b": 4.0, "c": 15.0, "w": 9.0, "x": 20.0}
    shape_ctx = dict(ctx, slots={"RB": 2}, flex=0)
    out = ledger.grade_week(shape_ctx, store, 2, actual=actual, my_actual=100.0, their_actual=90.0)
    assert out["graded"] == 4
    assert out["lineup"]["chosen_pts"] == 16.0 and out["lineup"]["best_pts"] == 27.0
    assert out["scout"]["won"] == 1.0 and out["scout"]["margin_error"] == 7.0
    assert out["waiver_add"][0]["delta"] == -6.0
    assert out["trade_offer"][0]["realised"] == 8.0
    saved = json.loads((ledger.ledger_dir(store) / "grades-2026-wk02.json").read_text())
    assert saved["graded"] == 4
    assert ledger.grade_week(shape_ctx, store, 5, actual={})["note"] == "no ledger rows"


def test_actuals_are_scored_in_the_leagues_own_settings():
    raw = {"p1": {"rush_yd": 100, "rush_td": 1, "rec": 4, "rec_yd": 30}, "p2": {"rec": 2}, "junk": "x"}
    pts = ledger.actual_points(_ctx(), 2, getter=lambda url: raw)
    assert pts == {"p1": 10 + 6 + 2 + 3, "p2": 1.0}


def test_matchup_actuals_come_from_the_platform_feed():
    class Src:
        def matchups(self, week):
            return [{"matchup_id": 1, "roster_id": 3, "points": 121.0},
                    {"matchup_id": 1, "roster_id": 9, "points": 110.0},
                    {"matchup_id": 2, "roster_id": 1, "points": 99.0}]
    assert ledger.matchup_actuals(_ctx(source=Src()), 2) == (121.0, 110.0)

    class Unplayed:
        def matchups(self, week):
            return [{"matchup_id": 1, "roster_id": 3, "points": 0.0}, {"matchup_id": 1, "roster_id": 9, "points": 0.0}]
    assert ledger.matchup_actuals(_ctx(source=Unplayed()), 3) == (None, None)
    assert ledger.matchup_actuals(_ctx(source=None), 3) == (None, None)


# ---------------------------------------------------------------- report

def test_the_season_report_sums_the_rulers(store):
    d = ledger.ledger_dir(store)
    d.mkdir(parents=True)
    for wk, eff, left, err, brier, won in ((1, 0.9, 8.0, -3.0, 0.16, 1.0), (2, 0.8, 20.0, 5.0, 0.36, 0.0)):
        (d / f"grades-2026-wk{wk:02d}.json").write_text(json.dumps({
            "week": wk, "lineup": {"efficiency": eff, "left_on_bench": left, "chosen_pts": 0, "best_pts": 0},
            "scout": {"graded": True, "margin_error": err, "brier": brier, "won": won},
            "waiver_add": [{"delta": 4.0}, {"delta": -1.0}], "trade_offer": [{"send": True, "realised": 2.5}]}))
    out = ledger.report(store, "testleague")
    assert "mean efficiency 85.0%" in out and "28.0 points left on the bench" in out
    assert "record 1-1" in out and "Brier 0.260" in out and "margin MAE 4.0" in out
    assert "4 graded, 2 outscored" in out
    assert "2 priced, 2 cleared" in out and "+5.0" in out
    assert "| 2 | 0.8 | 20.0 | 5.0 | 0.36 | 2 |" in out
    assert ledger.report(Store(store.dir.parent / "empty"), "x").endswith("no graded weeks yet")

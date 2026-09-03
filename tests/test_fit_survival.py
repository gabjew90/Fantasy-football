"""The calibration row builder (plan B1) must grade predictions against the
sim's real horizon and read either logged form."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("fs", ROOT / "scripts" / "fit_survival.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)

TEAMS, ROUNDS, ME = 10, 15, 2


def _picks(*names_at):
    """(name, pick_no) -> pick events; slot from the snake, my_pick for slot 2."""
    out = []
    for name, no in names_at:
        rnd, slot = fs.snake.pick_to_round_slot(no, TEAMS)
        out.append({"player": name, "pick_no": no, "round": rnd, "slot": slot, "my_pick": slot == ME})
    return out


def test_horizon_is_recomputed_from_the_state_not_read_from_the_event():
    # cp = 2 is MY pick (slot 2): the window is picks 3..19, my next is 19
    recs = [{"current_pick": 2, "my_next_pick": 2,           # the old, wrong field
             "recommendations": [{"player": "A Back", "pos": "RB", "survival": 0.9},
                                 {"player": "B Wide", "pos": "WR", "survival": 0.4}]}]
    picks = _picks(("Z Star", 1), ("A Back", 2), ("B Wide", 10))
    rows = fs.prediction_rows(picks, recs, TEAMS, ROUNDS, ME)
    by = {r["player"]: r for r in rows}
    assert "aback" not in by                     # my own take at this state: unobservable, dropped
    assert by["bwide"]["window_start"] == 3 and by["bwide"]["my_next"] == 19
    assert by["bwide"]["survived"] is False and by["bwide"]["source"] == "structured"
    # the legacy scoring called that same prediction 'survived' (my_next = cp = 2)
    old = fs.legacy_rows(picks, recs, TEAMS, ROUNDS, ME)
    assert all(r["survived"] for r in old)


def test_prose_in_both_phrasings_is_unshrunk_by_the_logged_shrink():
    recs = [{"current_pick": 1, "survival_shrink": 0.55,
             "recommendations": [{"player": "A Back", "pos": "RB", "why": "x 75% chance he's still there"},
                                 {"player": "B Wide", "pos": "WR", "why": "urgency (he survives 68%)"}]},
            {"current_pick": 3,                                   # no shrink logged: raw as written
             "recommendations": [{"player": "C Tight", "pos": "TE", "why": "60% chance he's still there"}]}]
    picks = _picks(("Q", 1))
    rows = {r["player"]: r for r in fs.prediction_rows(picks, recs, TEAMS, ROUNDS, ME)}
    assert abs(rows["aback"]["pred"] - (0.5 + 0.25 / 0.55)) < 1e-9 and rows["aback"]["source"] == "prose"
    assert abs(rows["bwide"]["pred"] - (0.5 + 0.18 / 0.55)) < 1e-9
    assert abs(rows["ctight"]["pred"] - 0.60) < 1e-9
    assert fs.unshrink(0.775, 0.55) == 1.0                      # clipped, never above 1


def test_structured_field_beats_prose_and_stale_rows_are_dropped():
    recs = [{"current_pick": 5, "survival_shrink": 0.55,
             "recommendations": [{"player": "A Back", "pos": "RB", "survival": 0.33,
                                  "why": "90% chance he's still there"},
                                 {"player": "Gone Guy", "pos": "WR", "survival": 0.9}]}]
    picks = _picks(("Gone Guy", 3))          # taken before the window opened at 5
    rows = {r["player"]: r for r in fs.prediction_rows(picks, recs, TEAMS, ROUNDS, ME)}
    assert rows["aback"]["pred"] == 0.33 and "goneguy" not in rows


def test_trail_records_become_recs_events_with_the_drafted_and_passed_on():
    trail = {"our_records": [{"pick_no": 8, "drafted": "A Back", "pos": "RB", "why": "w", "s": 0.7, "sr": 0.86,
                              "passed_on": [{"n": "B Wide", "p": "WR", "why": "74% chance he's still there"}]}]}
    ev = fs.trail_recs(trail)
    assert ev[0]["current_pick"] == 8 and ev[0]["survival_shrink"] == 0.55
    got = {r["player"]: fs.pred_from_rec(r, 0.55) for r in ev[0]["recommendations"]}
    assert got["A Back"] == (0.86, "structured")
    assert abs(got["B Wide"][0] - (0.5 + 0.24 / 0.55)) < 1e-9 and got["B Wide"][1] == "prose"


def test_bucketize_reports_n_predicted_and_observed():
    rows = [{"pred": 0.95, "survived": True}, {"pred": 0.92, "survived": False}, {"pred": 0.2, "survived": False}]
    b = {x["bucket"]: x for x in fs.bucketize(rows)}
    assert b["90-100"]["n"] == 2 and abs(b["90-100"]["obs"] - 0.5) < 1e-9 and abs(b["90-100"]["pred"] - 0.935) < 1e-9
    assert b["0-29"]["n"] == 1 and b["50-69"]["n"] == 0 and b["50-69"]["pred"] is None


def test_sidecar_loader_orders_calls_by_pick_and_room_stems_skip_copies(tmp_path):
    logs = tmp_path
    (logs / "yahoo_77.plans.jsonl").write_text(
        '{"call": 3, "current_pick": 9, "state_in": {"away_teams": ["1"]}}\n'
        '{"call": 1, "current_pick": 2, "state_in": {"away_teams": []}}\n'
        'not json\n'
        '{"call": 2, "current_pick": 2, "state_in": {"away_teams": ["4"]}}\n', encoding="utf-8")
    calls = fs.load_sidecar("77", logs)
    assert [(c["current_pick"], c["call"]) for c in calls] == [(2, 1), (2, 2), (9, 3)]
    assert fs.load_sidecar("78", logs) == []
    assert fs.is_room_stem("10534350") and not fs.is_room_stem("10532940_prereload") and not fs.is_room_stem("players_10534350")

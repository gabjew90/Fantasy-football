"""DECISIONS #35 harness: the per-pick away set from a trail + sidecar, the
cluster-bootstrap calibration CI and its min-clusters guard, and the
leave-one-room-out split."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


fs = _load("fit_survival")
sr = _load("survival_refit")

TEAMS = 4


def _trail(room="9001", teams=TEAMS, rounds=3, my_team="2"):
    """Every seat picks in every round; team id == slot as a string, so a
    round-1 seat's slot is only knowable from a pick it makes later."""
    picks = []
    for n in range(1, teams * rounds + 1):
        _rnd, slot = fs.snake.pick_to_round_slot(n, teams)
        picks.append({"pick_no": n, "team_id": str(slot), "name": f"P{n} Guy", "pos": "RB", "team": "XX"})
    return {"room": room, "teams": teams, "my_team": my_team, "picks": picks,
            "managers": {str(s): {"nickname": f"m{s}", "away": s == 3} for s in range(1, teams + 1)}}


def _call(call, cp, away):
    return {"type": "plan_detail", "call": call, "current_pick": cp, "state_in": {"away_teams": away}}


def test_away_at_round_one_seat_resolves_and_flicker_takes_nearest_preceding_call():
    trail = _trail()
    # call 1 while pick 1 is on the clock: team 3 (slot 3, first picks at pick 3) is away
    # call 2 at pick 2: nobody away (the flag flickered)
    # call 3 at pick 3: teams 3 and 1 away; team 99 never picks -> dropped
    calls = [_call(1, 1, ["3"]), _call(2, 2, []), _call(3, 3, ["3", "1", "99"])]
    ts = fs.team_slots(trail["picks"], TEAMS)
    assert ts == {"1": 1, "2": 2, "3": 3, "4": 4}
    away = fs.away_at_from_sidecar(calls, ts, 12)
    assert away[1] == frozenset({3})                 # resolved before seat 3 has picked
    assert away[2] == frozenset()                    # the flicker reading, not smoothed
    assert away[3] == frozenset({1, 3})              # the call made while 3 was on the clock counts
    assert away[4] == frozenset({1, 3}) and away[12] == frozenset({1, 3})   # carried until the next call
    assert set(away) == set(range(1, 13)) and all(isinstance(v, frozenset) for v in away.values())


def test_away_at_before_the_first_call_is_empty_and_calls_are_ordered_by_pick():
    trail = _trail()
    calls = [_call(7, 6, ["4"]), _call(5, 4, ["1"])]           # unsorted on purpose
    calls.sort(key=lambda c: (c["current_pick"], c["call"]))
    away = fs.away_at_from_sidecar(calls, fs.team_slots(trail["picks"], TEAMS), 8)
    assert away[1] == away[3] == frozenset()
    assert away[4] == away[5] == frozenset({1})
    assert away[6] == away[8] == frozenset({4})


def test_load_yahoo_room_exposes_away_at_and_rooms_without_a_sidecar_get_none(tmp_path):
    logs = tmp_path / "logs"
    (logs / "mocks").mkdir(parents=True)
    trail = _trail()
    (logs / "mocks" / "mock_9001.json").write_text(json.dumps(trail), encoding="utf-8")
    (logs / "yahoo_9001.plans.jsonl").write_text(
        "\n".join(json.dumps(c) for c in [_call(2, 2, ["3"]), _call(1, 1, [])]) + "\n", encoding="utf-8")
    room = fs.load_yahoo_room("9001", logs)
    assert room["has_sidecar"] and room["away_at"][1] == frozenset() and room["away_at"][2] == frozenset({3})
    assert room["away_at"][12] == frozenset({3})
    # no sidecar: empty map, flag off (the report says so once per room)
    (logs / "mocks" / "mock_9002.json").write_text(json.dumps(_trail(room="9002")), encoding="utf-8")
    bare = fs.load_yahoo_room("9002", logs)
    assert not bare["has_sidecar"] and bare["away_at"] == {}
    # pre-reload copies and players snapshots are not rooms
    (logs / "mocks" / "mock_9001_prereload.json").write_text(json.dumps(trail), encoding="utf-8")
    (logs / "mocks" / "mock_players_9001.json").write_text(json.dumps({"players": []}), encoding="utf-8")
    assert sorted(r["room"] for r in fs.all_rooms(logs)) == ["9001", "9002"]


def test_state_overrides_carry_the_away_set_for_that_pick(monkeypatch):
    """The tracker at state cp is built with away_slots = away_at[cp]."""
    import engine_parity as EP
    seen = {}

    class FakeTracker:
        def urgency_report(self):
            return {}

    def fake_make_tracker(board, picks, seat, **kw):
        seen["overrides"] = kw["overrides"]
        seen["n_picks"] = len(picks)
        return FakeTracker()

    monkeypatch.setattr(EP, "make_tracker", fake_make_tracker)
    ctx = {"teams": 10, "rounds": 15, "n_picks": 150, "board": [], "picks": [{} for _ in range(150)],
           "slots": {}, "cfg": None, "picked_at": {}, "id2name": {}, "room": "r",
           "away_at": {7: frozenset({1, 4})}}
    assert sr.state_rows(ctx, 7, 3, {"sigma_early": 4.0}, 50) == []
    assert seen["overrides"]["away_slots"] == frozenset({1, 4}) and seen["n_picks"] == 6
    assert seen["overrides"]["sigma_early"] == 4.0 and seen["overrides"]["sims"] == 50
    sr.state_rows(ctx, 8, 3, {}, 50)
    assert seen["overrides"]["away_slots"] == frozenset()


# ---------------------------------------------------------------- bootstrap

def _rows(n_clusters, per_cluster, pred, obs_rate, seed=1):
    import random
    rng = random.Random(seed)
    rows = []
    for c in range(n_clusters):
        for _ in range(per_cluster):
            rows.append((pred, rng.random() < obs_rate, "RB", f"room:1:{c}"))
    return rows


def test_bootstrap_ci_shape_and_effective_n_is_clusters():
    rows = _rows(40, 5, 0.85, 0.6)
    table = sr.bootstrap_ci(rows, n_boot=200, seed=3)
    assert [b["bucket"] for b in table] == ["0-29", "30-49", "50-69", "70-89", "90-100"]
    b = {x["bucket"]: x for x in table}["70-89"]
    assert b["n"] == 200 and b["clusters"] == 40
    assert abs(b["pred"] - 0.85) < 1e-9 and abs(b["diff"] - (b["obs"] - b["pred"])) < 1e-9
    assert b["lo"] <= b["diff"] <= b["hi"] and b["hi"] < 0          # a clear over-prediction
    empty = {x["bucket"]: x for x in table}["0-29"]
    assert empty["n"] == 0 and empty["clusters"] == 0 and empty["lo"] is None
    # deterministic under a seed
    assert sr.bootstrap_ci(rows, n_boot=200, seed=3) == table


def test_bar_failures_ci_needs_min_clusters_to_flag():
    rows = _rows(12, 20, 0.9, 0.5)                    # 240 rows, a 40-point miss, but only 12 clusters
    assert sr.bar_failures_ci(rows, min_clusters=30, n_boot=200) == []
    flagged = sr.bar_failures_ci(rows, min_clusters=10, n_boot=200)
    assert len(flagged) == 1 and flagged[0].startswith("90-100%") and "clusters 12" in flagged[0]
    # the 8-point bar still fires on the same rows (kept for continuity)
    assert sr.bar_failures(rows)
    # a well-calibrated bucket with many clusters does not fail
    good = _rows(60, 5, 0.6, 0.6, seed=5)
    assert sr.bar_failures_ci(good, min_clusters=30, n_boot=200) == []


def test_views_are_pooled_human_and_every_yahoo_type():
    by_type = {"sleeper_human": [(0.5, True, "RB", "h:1:1")], "sleeper_mock": [(0.5, True, "RB", "m:1:1")],
               "yahoo_autopick": [(0.5, False, "RB", "y:1:1")], "yahoo_email": [(0.5, False, "RB", "e:1:1")]}
    v = dict(sr.views(by_type))
    assert len(v["pooled"]) == 4 and len(v["human"]) == 1 and len(v["autopick"]) == 2


# --------------------------------------------------------------------- LORO

def _ctx(room, rt, n_away):
    return {"room": room, "room_type": rt, "league": "keefamania", "n_picks": 10, "matched": 10,
            "adp_note": "-", "yr_note": "", "away_note": "-", "has_sidecar": n_away > 0,
            "n_away_states": n_away, "teams": 10, "my_slot": 1}


def test_stage_rooms_and_loro_split_restrict_autopick_to_rooms_with_away_sets():
    ctxs = [_ctx("H", "sleeper_human", 0), _ctx("A", "yahoo_autopick", 5), _ctx("B", "yahoo_autopick", 3),
            _ctx("C", "yahoo_autopick", 0)]
    assert [c["room"] for c in sr.stage_rooms(ctxs, "autopick_list_prob")] == ["A", "B"]
    assert [c["room"] for c in sr.stage_rooms(ctxs, "sigma")] == ["H", "A", "B", "C"]
    splits = sr.loro_split(ctxs, "autopick")
    assert [(h["room"], [c["room"] for c in fit]) for h, fit in splits] == [("A", ["B"]), ("B", ["A"])]
    assert [(h["room"], [c["room"] for c in fit]) for h, fit in sr.loro_split(ctxs, "sigma")][0] == ("H", ["A", "B", "C"])
    assert [h["room"] for h, _ in sr.loro_split(ctxs, "all")] == ["H", "A", "B", "C"]
    assert [name for name, _ in sr.stages_for("autopick")] == ["autopick_list_prob", "autopick_sigma_scale", "autopick_need_damp"]
    assert sr.stages_for("all") == sr.STAGES and [n for n, _ in sr.stages_for("need")] == ["need"]


def test_run_loro_fits_on_the_other_rooms_and_scores_the_held_out_one(tmp_path, monkeypatch):
    ctxs = [_ctx("H", "sleeper_human", 0), _ctx("A", "yahoo_autopick", 5), _ctx("B", "yahoo_autopick", 3)]
    monkeypatch.setattr(sr, "all_rooms", lambda logs_dir: [{"room": c["room"]} for c in ctxs])
    monkeypatch.setattr(sr, "room_context", lambda r, logs_dir: next(c for c in ctxs if c["room"] == r["room"]))
    fit_calls = []

    def fitter(rooms):
        fit_calls.append([c["room"] for c in rooms])
        return {**sr.CURRENT, "autopick_list_prob": 0.3}, [("autopick_list_prob", {}, 0.1)], []

    def evaluator(rooms, point):
        room = rooms[0]["room"]
        ll = 0.20 if point["autopick_list_prob"] > 0 else 0.25
        rows = [(0.8, True, "RB", f"{room}:1:{i}") for i in range(4)]
        return {"objective": ll, "n": len(rows), "rows": {rooms[0]["room_type"]: rows}}

    a = SimpleNamespace(logs=str(tmp_path), stage="autopick", smoke=False, sims=10, every=1, all_slots=False,
                        workers=1, loro_out=str(tmp_path / "loro.md"))
    out = sr.run_loro(a, evaluator=evaluator, fitter=fitter)
    assert fit_calls == [["B"], ["A"]]                          # the stage's other rooms, never the held-out one
    assert [f["room"] for f in out["folds"]] == ["A", "B"]
    assert all(abs(f["heldout_fitted"] - 0.20) < 1e-9 and abs(f["heldout_current"] - 0.25) < 1e-9 for f in out["folds"])
    assert abs(out["mean_heldout_fitted"] - 0.20) < 1e-9 and abs(out["mean_heldout_current"] - 0.25) < 1e-9
    md = (tmp_path / "loro.md").read_text(encoding="utf-8")
    assert "| A | yahoo_autopick |" in md and "Pooled mean over rooms" in md
    assert json.loads((tmp_path / "loro.json").read_text(encoding="utf-8"))["stage"] == "autopick"


def test_current_carries_the_autopick_knobs_at_todays_values():
    assert sr.CURRENT["autopick_list_prob"] == 0.0
    assert sr.CURRENT["autopick_sigma_scale"] == 0.5 and sr.CURRENT["autopick_need_damp"] == 0.02
    grids = dict(sr.AUTOPICK_STAGES)
    assert [g["autopick_list_prob"] for g in grids["autopick_list_prob"]] == [0.0, 0.2, 0.3, 0.4, 0.6]
    assert [g["autopick_sigma_scale"] for g in grids["autopick_sigma_scale"]] == [0.5, 0.75, 1.0, 1.5]
    assert [g["autopick_need_damp"] for g in grids["autopick_need_damp"]] == [0.02, 0.15, 0.30, 0.45]

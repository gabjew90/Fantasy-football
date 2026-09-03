"""yahoo_trail_replay: a trail becomes slot_replay's pick log, names join
by the shared key, and the per-pick engine loop runs at two knob points
with the away set threaded through."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


ytr = _load("yahoo_trail_replay")


def player(pid, name, pos, vorp, adp, rank=1, tier=1, yrank=None):
    """The dict shape engine_parity.load_board produces."""
    return {"sleeper_id": pid, "name": name, "pos": pos, "team": "XX",
            "vorp": vorp, "vorp_flex": vorp, "proj_pts": 100.0 + vorp,
            "adp": adp, "adp_delta": 0.0, "tier": tier, "pos_rank": rank,
            "value_rank": 1, "cliff_flag": False, "upside_flag": False,
            "proj_source": "blend", "backs_up": "", "bye": None,
            "proj_sd": None, "proj_hi": None, "proj_lo": None, "n_sources": 0, "yahoo_rank": yrank}


RB_NAMES = ["Alvin Kamara", "Bijan Robinson", "Chase Brown", "Derrick Henry", "Ezekiel Elliott", "Frank Gore"]
WR_NAMES = ["Amon Brown", "Brandon Aiyuk", "CeeDee Lamb", "Davante Adams", "Elijah Moore", "Foster Moreau"]


def _board():
    out, pid = [], 0
    for i in range(6):
        pid += 1
        out.append(player(str(pid), RB_NAMES[i], "RB", 60 - 8 * i, 1 + 2 * i, rank=i + 1, yrank=1 + 2 * i))
        pid += 1
        out.append(player(str(pid), WR_NAMES[i], "WR", 58 - 8 * i, 2 + 2 * i, rank=i + 1, yrank=2 + 2 * i))
    return sorted(out, key=lambda p: -p["vorp"])


def _trail():
    names = [RB_NAMES[0], WR_NAMES[0], RB_NAMES[1], WR_NAMES[1], RB_NAMES[2], WR_NAMES[2]]
    picks = []
    for n, name in enumerate(names, start=1):
        _rnd, slot = ytr.snake.pick_to_round_slot(n, 2)
        picks.append({"pick_no": n, "team_id": str(slot), "name": name, "pos": "RB" if name in RB_NAMES else "WR", "team": "XX"})
    return {"room": "1", "teams": 2, "my_team": "1", "picks": picks, "managers": {}}


def test_trail_becomes_slot_replay_pick_log_dicts():
    log = ytr.trail_to_log(_trail())
    assert [(d["pick_no"], d["slot"], d["round"]) for d in log] == [(1, 1, 1), (2, 2, 1), (3, 2, 2), (4, 1, 2), (5, 1, 3), (6, 2, 3)]
    assert all(d["type"] == "pick" for d in log)
    assert log[0]["player"] == "Alvin Kamara" and log[2]["player"] == "Bijan Robinson"


def test_names_join_by_key_with_exact_fallback_and_unmatched_reported():
    board = _board() + [player("99", "Jay Smith", "WR", 1.0, 50.0), player("98", "Jon Smith", "RB", 1.0, 51.0)]
    log = ytr.trail_to_log(_trail()) + [
        {"type": "pick", "pick_no": 7, "slot": 1, "round": 4, "player": "A. Kamara Jr.", "pos": "RB"},
        {"type": "pick", "pick_no": 8, "slot": 2, "round": 4, "player": "Nobody Here", "pos": "TE"},
        {"type": "pick", "pick_no": 9, "slot": 2, "round": 5, "player": "J. Smith", "pos": "WR"},
        {"type": "pick", "pick_no": 10, "slot": 1, "round": 5, "player": "Jim Smith", "pos": "QB"},
    ]
    m, unmatched, ambiguous = ytr.match_names(log, board)
    assert m["A. Kamara Jr."]["sleeper_id"] == m["Alvin Kamara"]["sleeper_id"]      # suffix dropped, key joins
    assert m["J. Smith"]["name"] == "Jay Smith"                                       # key collision broken by pos
    assert unmatched == ["Nobody Here"] and ambiguous == ["Jim Smith"]              # collision the pos cannot break


def test_away_sets_come_from_the_sidecar_by_team_id():
    trail = _trail()
    calls = [{"call": 1, "current_pick": 2, "state_in": {"away_teams": ["2"]}},
             {"call": 2, "current_pick": 5, "state_in": {"away_teams": []}}]
    away = ytr.away_sets(trail, calls)
    assert away == {1: frozenset(), 2: frozenset({2}), 3: frozenset({2}), 4: frozenset({2}), 5: frozenset(), 6: frozenset()}
    assert ytr.away_sets(trail, []) == {}


def test_engine_loop_runs_at_two_knob_points_with_away_slots(monkeypatch):
    import engine_parity as EP
    board = _board()
    log = ytr.trail_to_log(_trail())
    slots = {"RB": 1, "WR": 1, "FLEX": 1}
    away = {n: frozenset({2}) for n in range(1, 7)}
    seen = []
    real = EP.make_tracker

    def spy(*args, **kw):
        seen.append(dict(kw["overrides"]))
        return real(*args, **kw)

    monkeypatch.setattr(EP, "make_tracker", spy)
    for point in ({"autopick_list_prob": 0.0}, {"autopick_list_prob": 0.6, "autopick_sigma_scale": 0.75, "autopick_need_damp": 0.45}):
        errors = []
        chosen = ytr.replay_seat(board, log, 1, 2, 3, slots, overrides={**point, "sims": 40},
                                 away_at=away, errors=errors)
        assert errors == [], errors
        assert len(chosen) == 3 and len({p["name"] for p in chosen}) == 3
        rival = {d["player"] for d in log if d["slot"] == 2}
        assert not (rival & {p["name"] for p in chosen})            # never takes a fixed rival pick
    assert len(seen) == 6 and all(o["away_slots"] == frozenset({2}) for o in seen)
    assert seen[-1]["autopick_list_prob"] == 0.6 and seen[0]["autopick_list_prob"] == 0.0


def test_parse_sets_casts_numbers_and_booleans():
    assert ytr.parse_sets(["autopick_list_prob=0.3", "slot_markets=false", "x=abc"]) == {
        "autopick_list_prob": 0.3, "slot_markets": False, "x": "abc"}

import json
import time

from draftkit.draftlog import DraftLog
from draftkit.tracker import Tracker, TrackerState

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1, "BN": 5}

PLAYERS = [
    {"sleeper_id": "1", "player": "Alpha RB", "pos": "RB", "pos_rank": 1, "tier": 1,
     "vorp": 200.0, "adp": 1.0, "cliff_flag": True, "value_rank": 1, "proj_pts": 300.0,
     "adp_delta": 0.0, "team": "SF", "bye": 8},
    {"sleeper_id": "2", "player": "Beta WR", "pos": "WR", "pos_rank": 1, "tier": 1,
     "vorp": 150.0, "adp": 2.0, "cliff_flag": False, "value_rank": 2, "proj_pts": 250.0,
     "adp_delta": 0.0, "team": "LAR", "bye": 11},
    {"sleeper_id": "3", "player": "Gamma TE", "pos": "TE", "pos_rank": 1, "tier": 1,
     "vorp": 90.0, "adp": 20.0, "cliff_flag": False, "value_rank": 3, "proj_pts": 200.0,
     "adp_delta": 0.0, "team": "ARI", "bye": 14},
]


def make_tracker(picks, my_slot=2):
    t = object.__new__(Tracker)
    t.teams = 12
    t.rounds = 15
    t.slots = dict(SLOTS)
    t.my_slot = my_slot
    t.poll_seconds = 5.0
    t.kdef_round = 14
    t.fall_alert = 12
    t.draft_id = "logdraft"
    t.sims = 20
    t.pool_size = 80
    t.sigma_early = 6.0
    t.sigma_late = 27.0
    t.qb2_round = 10
    t.te2_fall = 12
    t._urgency_cache = None
    t.rival_seeds = {}
    t.slot_to_user = {}
    t.players = [dict(p) for p in PLAYERS]
    t.by_id = {p["sleeper_id"]: p for p in t.players}
    t.state = TrackerState(
        picks=picks,
        drafted_ids={str(p["player_id"]) for p in picks},
        last_poll_ok=time.time(),
    )
    t.state.status = "drafting"
    return t


def pick(player_id, draft_slot):
    return {"player_id": str(player_id), "draft_slot": draft_slot, "metadata": {}}


def _events(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_sync_logs_picks_and_recs_once(tmp_path):
    log_path = tmp_path / "draft_logdraft.jsonl"
    log = DraftLog(log_path)
    t = make_tracker([pick(1, 1)])
    log.sync(t)
    log.sync(t)  # same state -> no duplicates
    events = _events(log_path)
    pick_events = [e for e in events if e["type"] == "pick"]
    rec_events = [e for e in events if e["type"] == "recs"]
    assert len(pick_events) == 1
    assert pick_events[0]["player"] == "Alpha RB"
    assert pick_events[0]["pick_no"] == 1
    assert len(rec_events) == 1
    assert rec_events[0]["current_pick"] == 2
    assert rec_events[0]["recommendations"][0]["why"]


def test_incremental_picks_appended(tmp_path):
    log_path = tmp_path / "d.jsonl"
    log = DraftLog(log_path)
    log.sync(make_tracker([pick(1, 1)]))
    log.sync(make_tracker([pick(1, 1), pick(2, 2)]))
    picks_logged = [e for e in _events(log_path) if e["type"] == "pick"]
    assert [e["pick_no"] for e in picks_logged] == [1, 2]
    assert picks_logged[1]["my_pick"] is True  # slot 2 is mine


def test_restart_does_not_duplicate(tmp_path):
    log_path = tmp_path / "d.jsonl"
    DraftLog(log_path).sync(make_tracker([pick(1, 1)]))
    # simulate a crash + restart: fresh DraftLog over the same file
    DraftLog(log_path).sync(make_tracker([pick(1, 1)]))
    picks_logged = [e for e in _events(log_path) if e["type"] == "pick"]
    assert len(picks_logged) == 1


def test_status_transition_logged(tmp_path):
    log_path = tmp_path / "d.jsonl"
    log = DraftLog(log_path)
    t = make_tracker([])
    t.state.status = "pre_draft"
    log.sync(t)
    t.state.status = "drafting"
    log.sync(t)
    statuses = [e["status"] for e in _events(log_path) if e["type"] == "status"]
    assert statuses == ["pre_draft", "drafting"]

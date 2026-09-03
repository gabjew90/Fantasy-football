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


def test_reset_shrink_relogs_new_picks(tmp_path):
    # REGRESSION: a commissioner undo shrinks the pick list; the log must mark
    # the reset and re-log replacement picks instead of skipping them forever.
    log_path = tmp_path / "d.jsonl"
    log = DraftLog(log_path)
    log.sync(make_tracker([pick(1, 1), pick(2, 2)]))
    log.sync(make_tracker([pick(1, 1)]))                 # undo pick 2
    log.sync(make_tracker([pick(1, 1), pick(3, 2)]))     # different player re-picked
    events = _events(log_path)
    assert any(e["type"] == "reset" for e in events)
    picked = [e["player"] for e in events if e["type"] == "pick"]
    assert picked.count("Gamma TE") == 1  # the re-made pick was logged
    # restart over the same file must not resurrect the old high-water mark
    log2 = DraftLog(log_path)
    assert log2._last_pick == 2


def test_burst_reconstructs_recs_before_my_pick(tmp_path):
    # REGRESSION (bot-burst): one poll swallows three picks including mine at
    # overall pick 2 — the log must reconstruct the engine's view before my
    # pick instead of leaving a hole in the review.
    log_path = tmp_path / "d.jsonl"
    log = DraftLog(log_path)
    log.sync(make_tracker([pick(4, 1), pick(1, 2), pick(2, 3)]))
    rec_events = [e for e in _events(log_path) if e["type"] == "recs"]
    retro = [e for e in rec_events if e.get("reconstructed")]
    assert len(retro) == 1
    assert retro[0]["current_pick"] == 2  # the state just before MY pick
    assert retro[0]["recommendations"]
    # live snapshot for the post-burst state still logged
    assert any(e["current_pick"] == 4 for e in rec_events)
    # chronology: the retro snapshot appears before my pick event
    types = [(e["type"], e.get("current_pick") or e.get("pick_no")) for e in _events(log_path)]
    assert types.index(("recs", 2)) < types.index(("pick", 2))


def test_no_duplicate_snapshot_on_normal_cadence(tmp_path):
    # single-pick syncs (the real-draft cadence) must not double-log snapshots
    log_path = tmp_path / "d.jsonl"
    log = DraftLog(log_path)
    log.sync(make_tracker([pick(4, 1)]))               # live snapshot cp=2
    log.sync(make_tracker([pick(4, 1), pick(1, 2)]))   # my pick arrives alone
    rec_events = [e for e in _events(log_path) if e["type"] == "recs"]
    cps = [e["current_pick"] for e in rec_events]
    assert cps.count(2) == 1
    assert not any(e.get("reconstructed") for e in rec_events)


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


def test_recs_event_logs_the_sims_window_and_structured_survival(tmp_path):
    """Plan B1. On the clock (12 teams, slot 2, pick 1 made -> cp = 2 is
    mine) the survival sim spans picks 3..22 and my next turn is 23; the
    old event logged my_next_pick = 2 and graded every on-clock prediction
    as survived. Each recommendation now carries the raw survival, the
    event the knob set and the rivals' needs."""
    log = DraftLog(tmp_path / "d.jsonl")
    log.sync(make_tracker([pick(1, 1)]))
    ev = [e for e in _events(tmp_path / "d.jsonl") if e["type"] == "recs"][0]
    assert ev["current_pick"] == 2 and ev["on_clock_slot"] == 2
    assert ev["window_start"] == 3 and ev["my_next_pick"] == 23
    assert len(ev["rivals"]) == 20 and all("needs" in r and "autopick" in r for r in ev["rivals"])
    assert "survival_shrink" in ev["knobs"] and ev["knobs"]["sims"] == 20
    rec = ev["recommendations"][0]
    assert isinstance(rec["survival"], float) and 0.0 <= rec["survival"] <= 1.0
    assert isinstance(rec["survival_shown"], float) and rec["market"] in ("RB", "WR", "TE", "FLEX")
    assert rec["sleeper_id"] and "e_best_next" in rec and "best_now" in rec


def test_recs_event_off_the_clock_windows_from_the_current_pick(tmp_path):
    log = DraftLog(tmp_path / "d.jsonl")
    log.sync(make_tracker([]))            # cp = 1, slot 1 on the clock, I am slot 2
    ev = [e for e in _events(tmp_path / "d.jsonl") if e["type"] == "recs"][0]
    assert (ev["window_start"], ev["my_next_pick"]) == (1, 2)


def test_reconstructed_event_uses_the_rewound_report(tmp_path):
    log = DraftLog(tmp_path / "d.jsonl")
    log.sync(make_tracker([pick(4, 1), pick(1, 2), pick(2, 3)]))
    retro = [e for e in _events(tmp_path / "d.jsonl") if e.get("reconstructed")][0]
    assert retro["current_pick"] == 2 and retro["window_start"] == 3 and retro["my_next_pick"] == 23
    assert all(isinstance(r.get("survival"), float) for r in retro["recommendations"])


def test_snapshot_writes_one_event_per_key_and_logs_picks(tmp_path):
    log = DraftLog(tmp_path / "y.jsonl")
    t = make_tracker([pick(1, 1)])
    recs = t.recommendations()
    assert log.snapshot(t, recs, t.urgency_report(), key=(2, 1)) is True
    assert log.snapshot(t, recs, t.urgency_report(), key=(2, 1)) is False
    ev = _events(tmp_path / "y.jsonl")
    assert [e["type"] for e in ev].count("recs") == 1 and [e["type"] for e in ev].count("pick") == 1
    assert ev[-1]["snapshot_key"] == [2, 1]
    # a restart over the same file remembers the key
    assert DraftLog(tmp_path / "y.jsonl").snapshot(t, recs, None, key=(2, 1)) is False

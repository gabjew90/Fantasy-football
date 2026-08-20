"""Tests for the /state JSON builder — no network, Tracker built by hand."""

import time

from draftkit.tracker import Tracker, TrackerState
from draftkit.web import build_state

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1, "BN": 5}


def make_player(sleeper_id, player, pos, pos_rank, tier, vorp, adp, cliff=False):
    return {
        "sleeper_id": str(sleeper_id), "player": player, "pos": pos,
        "pos_rank": pos_rank, "tier": tier, "vorp": float(vorp),
        "adp": adp, "cliff_flag": cliff, "value_rank": pos_rank,
        "proj_pts": 200.0, "adp_delta": 0.0,
    }


PLAYERS = [
    make_player(1, "Alpha RB", "RB", 1, 1, 200.0, 1.0, cliff=True),
    make_player(2, "Beta RB", "RB", 2, 2, 150.0, 3.0),
    make_player(3, "Gamma RB", "RB", 3, 2, 140.0, 40.0),
    make_player(4, "Alpha WR", "WR", 1, 1, 160.0, 2.0),
    make_player(5, "Beta WR", "WR", 2, 1, 155.0, 5.0),
    make_player(6, "Alpha TE", "TE", 1, 1, 95.0, 25.0, cliff=True),
    make_player(7, "Alpha QB", "QB", 1, 1, 60.0, 30.0),
    make_player(8, "Alpha K", "K", 1, 1, 10.0, 120.0),
    make_player(9, "Alpha DEF", "DEF", 1, 1, 12.0, 110.0),
]


def make_tracker(picks, my_slot=2):
    t = object.__new__(Tracker)
    t.teams = 12
    t.rounds = 15
    t.slots = dict(SLOTS)
    t.my_slot = my_slot
    t.poll_seconds = 5.0
    t.fall_alert = 12
    t.draft_id = "testdraft"
    t.sims = 50
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


def pick(player_id, draft_slot, pos):
    return {"player_id": str(player_id), "draft_slot": draft_slot,
            "metadata": {"position": pos}}


def test_on_the_clock_detection():
    # pick 1 made -> current pick is 2, which belongs to slot 2 (me)
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    s = build_state(t)
    assert s["current_pick"] == 2
    assert s["on_clock_me"] is True
    assert s["round"] == 1
    assert s["my_next_pick"] == 2
    assert s["picks_away"] == 0


def test_not_on_clock_and_picks_away():
    t = make_tracker([], my_slot=2)
    s = build_state(t)
    assert s["on_clock_me"] is False
    assert s["my_next_pick"] == 2
    assert s["picks_away"] == 1


def test_drafted_players_leave_board_and_recs():
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    s = build_state(t)
    names = [p["player"] for row in s["board"] for p in row["players"]]
    assert "Alpha RB" not in names
    rec_names = [r["player"] for r in s["recommendations"]]
    assert "Alpha RB" not in rec_names
    assert len(rec_names) > 0
    assert all(r["why"] for r in s["recommendations"])


def test_faller_surfaced():
    # 20 picks in, Beta WR (ADP 5) still available -> fell 21-5=16 >= fall_alert
    picks_ = [pick(100 + i, (i % 12) + 1, "RB") for i in range(20)]
    t = make_tracker(picks_, my_slot=2)
    s = build_state(t)
    fallers = {f["player"]: f for f in s["fallers"]}
    assert "Beta WR" in fallers
    assert fallers["Beta WR"]["fell"] >= 12


def test_poll_error_surfaced():
    t = make_tracker([], my_slot=2)
    t.state.last_error = "boom"
    s = build_state(t)
    assert s["poll_error"] == "boom"


def test_roster_fill_counts():
    # slot 1 took Alpha WR; I took Alpha RB at pick 2
    t = make_tracker([pick(4, 1, "WR"), pick(1, 2, "RB")], my_slot=2)
    s = build_state(t)
    assert s["roster"]["filled"]["RB"] == 1
    assert s["roster"]["filled"]["QB"] == 0
    assert s["roster"]["drafted"] == ["Alpha RB"]


def test_no_market_player_never_recommended():
    # no_market rows are board-visible but engine-silent until overridden
    t = make_tracker([], my_slot=2)
    ghost = make_player(99, "Ghost WR", "WR", 0, 1, 300.0, None)
    ghost["proj_source"] = "no_market"
    t.players.append(ghost)
    t.by_id["99"] = ghost
    s = build_state(t)
    assert "Ghost WR" not in [r["player"] for r in s["recommendations"]]
    board_names = [p["player"] for row in s["board"] for p in row["players"]]
    assert "Ghost WR" in board_names  # still visible for the manual eyeball


def test_json_serializable():
    import json
    t = make_tracker([pick(1, 1, "RB")], my_slot=2)
    json.dumps(build_state(t))


class StubTracker:
    """Counts poll() calls."""

    def __init__(self):
        self.poll_calls = 0
        self.poll_seconds = 5.0

    def poll(self):
        self.poll_calls += 1
        return False


def test_app_rate_limits_polls(monkeypatch):
    import pathlib
    import threading

    from draftkit.web import DraftWebApp

    app = DraftWebApp.__new__(DraftWebApp)
    app._trackers = {}
    app._last_poll = {}
    app._lock = threading.Lock()
    app.tiers_path = pathlib.Path("nonexistent-tiers.csv")
    stub = StubTracker()
    app._trackers["d1"] = stub
    monkeypatch.setattr("draftkit.web.build_state", lambda t: {"ok": True})

    app.state_for("d1", None)
    app.state_for("d1", None)  # immediate second call — inside poll window
    assert stub.poll_calls == 1


def test_app_reload_clears_cache():
    import threading

    from draftkit.web import DraftWebApp

    app = DraftWebApp.__new__(DraftWebApp)
    app._trackers = {"d1": StubTracker()}
    app._last_poll = {"d1": 123.0}
    app._lock = threading.Lock()
    app.reload()
    assert app._trackers == {} and app._last_poll == {}


def test_on_clock_urgency_window_is_next_turn():
    # REGRESSION: on the clock at pick 2, the engine must simulate the rival
    # picks up to my NEXT turn (pick 23), not a zero-width window that makes
    # every urgency 0.0 and every survival 100%.
    t = make_tracker([pick(4, 1, "WR")], my_slot=2)  # pick 1 made -> I'm on the clock
    s = build_state(t)
    assert s["on_clock_me"] is True
    rep = t.urgency_report()
    surv = list(rep["RB"]["survival"].values())
    assert any(v < 1.0 for v in surv), "on-clock window must simulate rivals"


def test_slot_change_applies_to_cached_tracker():
    import pathlib
    import threading

    from draftkit.web import DraftWebApp

    app = DraftWebApp.__new__(DraftWebApp)
    app._trackers = {}
    app._last_poll = {"d1": 1e18}  # far future: skip polling
    app._lock = threading.Lock()
    app.tiers_path = pathlib.Path("nonexistent-tiers.csv")
    t = make_tracker([], my_slot=2)
    app._trackers["d1"] = t
    app.state_for("d1", 7)
    assert t.my_slot == 7

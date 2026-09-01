"""Urgency ranges over unfilled ROSTER SLOTS, not positions.

Background (DECISIONS.md 2026-08-31 / 2026-09-01). Pricing a flex-bound
player against his own position's replacement overstates him -- 37.1 points
flat on the Keefamania board. Fixing the price alone did nothing, because the
engine ranks on urgency, which is a DIFFERENCE: shifting every tight end by
the same amount leaves every TE-to-TE gap intact.

The fix is to change what urgency ranges over. Once a dedicated slot is
filled you have left that market, and the position's remaining players
compete inside FLEX against the RB/WR you would otherwise start there.
"""

import numpy as np

from draftkit.planner import market_for
from draftkit.tracker import Tracker, TrackerState
from draftkit.urgency import simulate_survival

SLOTS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}


def player(pid, pos, vorp, flex, adp, rank=1, tier=1):
    return {"sleeper_id": pid, "player": pid, "pos": pos, "team": "XX",
            "vorp": vorp, "vorp_flex": flex, "proj_pts": 100.0 + vorp,
            "adp": adp, "adp_delta": 0.0, "tier": tier, "pos_rank": rank,
            "value_rank": 1, "cliff_flag": False, "upside_flag": False,
            "proj_source": "blend", "bye": None}


def make_tracker(players, my_picks, my_slot=1, current_pick=21, teams=10):
    """A Tracker over a synthetic board. my_picks: ids already on my roster."""
    t = object.__new__(Tracker)
    t.teams, t.rounds, t.slots, t.my_slot = teams, 15, dict(SLOTS), my_slot
    t.draft_id, t.poll_seconds, t.fall_alert = "test", 5.0, 12
    t.sims, t.pool_min, t.pool_lookback, t.pool_lookahead = 300, 40, 20, 60
    t.sigma_early, t.sigma_late = 6.0, 27.0
    t.reach_prob, t.reach_scale = 0.0, 3.0
    t.run_window, t.run_min, t.run_boost = 5, 2, 1.5
    t.survival_shrink = 0.55
    t.upside_from_round, t.upside_mult = 8, 1.15
    t.qb2_round, t.te2_fall = 10, 12
    t.slot_markets = True
    t._urgency_cache = None
    t.rival_seeds, t.slot_to_user = {}, {}
    t.players = [dict(p) for p in players]
    t.by_id = {p["sleeper_id"]: p for p in t.players}

    # my_picks land on the first pick numbers; everything else is a rival.
    # picks_for_slot filters on draft_slot, so exact snake placement does not
    # matter here -- what matters is that my roster is EXACTLY my_picks.
    mine = list(my_picks)
    picks = [
        {"pick_no": n, "round": (n - 1) // teams + 1,
         "player_id": mine[n - 1] if n <= len(mine) else f"filler{n}",
         "draft_slot": my_slot if n <= len(mine) else 0,
         "metadata": {"position": ""}}
        for n in range(1, current_pick)
    ]
    t.state = TrackerState(picks=picks,
                           drafted_ids={str(p["player_id"]) for p in picks},
                           status="drafting")
    return t


# ---------- _open_markets ----------

def test_open_dedicated_slot_is_its_own_market():
    t = make_tracker([], [])
    needs = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 0, "K": 1, "DEF": 1}
    got = {name: (members, vkey) for name, members, vkey in t._open_markets(needs)}
    assert got["TE"] == (("TE",), "vorp")
    assert "FLEX" not in got


def test_filled_slot_has_no_market_of_its_own():
    """The whole point: with the TE slot full there is no TE market left."""
    t = make_tracker([], [])
    needs = {"QB": 1, "RB": 1, "WR": 1, "TE": 0, "FLEX": 1, "K": 1, "DEF": 1}
    names = [name for name, _m, _v in t._open_markets(needs)]
    assert "TE" not in names
    assert "FLEX" in names


def test_flex_market_pools_all_flex_eligible_positions():
    """Membership is RB+WR+TE even when only TE's dedicated slot is filled.

    A FLEX market containing only tight ends would cancel the baseline shift
    all over again -- urgency is a difference, so a TE-only pool measures the
    same TE-to-TE gaps under a different name.
    """
    t = make_tracker([], [])
    needs = {"QB": 0, "RB": 0, "WR": 0, "TE": 0, "FLEX": 1, "K": 0, "DEF": 0}
    flex = [(m, v) for name, m, v in t._open_markets(needs) if name == "FLEX"]
    assert flex == [(("RB", "WR", "TE"), "vorp_flex")]


def test_all_starters_filled_falls_back_to_per_position_bench():
    t = make_tracker([], [])
    needs = dict.fromkeys(("QB", "RB", "WR", "TE", "FLEX", "K", "DEF"), 0)
    got = t._open_markets(needs)
    assert [n for n, _m, _v in got] == ["RB", "WR", "TE", "QB", "K", "DEF"]
    assert all(v == "vorp" for _n, _m, v in got)


# ---------- simulate_survival market aggregation ----------

def _pool():
    return [
        {"sleeper_id": "te_elite", "pos": "TE", "vorp": 60.0, "vorp_flex": 25.0,
         "adp": 20.0},
        {"sleeper_id": "te_mid", "pos": "TE", "vorp": 15.0, "vorp_flex": -20.0,
         "adp": 60.0},
        {"sleeper_id": "rb_a", "pos": "RB", "vorp": 40.0, "vorp_flex": 40.0,
         "adp": 22.0},
        {"sleeper_id": "wr_a", "pos": "WR", "vorp": 38.0, "vorp_flex": 30.0,
         "adp": 24.0},
    ]


def test_flex_market_is_priced_on_vorp_flex_and_pools_positions():
    rng = np.random.default_rng(3)
    rivals = [{"slot": s, "needs": dict(SLOTS), "user_id": None} for s in (2, 3)]
    rep = simulate_survival(
        _pool(), 21, 23, rivals, {}, rng, sims=200, sigma=6.0, teams=10,
        markets={"FLEX": {"members": ("RB", "WR", "TE"), "value": "vorp_flex"}})
    # best flex option is the RB at 40, NOT the tight end at 60
    assert rep["FLEX"]["best_now"] == 40.0
    assert rep["TE"]["best_now"] == 60.0          # per-position report survives
    assert set(rep["FLEX"]["survival"]) == {"te_elite", "te_mid", "rb_a", "wr_a"}


def test_per_position_report_is_unchanged_when_no_markets_passed():
    rivals = [{"slot": s, "needs": dict(SLOTS), "user_id": None} for s in (2, 3)]
    a = simulate_survival(_pool(), 21, 23, rivals, {},
                          np.random.default_rng(3), sims=200, sigma=6.0, teams=10)
    b = simulate_survival(
        _pool(), 21, 23, rivals, {}, np.random.default_rng(3), sims=200,
        sigma=6.0, teams=10,
        markets={"FLEX": {"members": ("RB", "WR", "TE"), "value": "vorp_flex"}})
    for pos in ("RB", "WR", "TE"):
        assert a[pos] == b[pos], f"{pos} report changed"


def test_missing_vorp_flex_falls_back_to_vorp():
    """Older boards have no vorp_flex column; the market must still price."""
    pool = [{"sleeper_id": "rb", "pos": "RB", "vorp": 40.0, "adp": 22.0}]
    rep = simulate_survival(
        pool, 21, 21, [], {}, np.random.default_rng(1), sims=10, teams=10,
        markets={"FLEX": {"members": ("RB",), "value": "vorp_flex"}})
    assert rep["FLEX"]["best_now"] == 40.0


# ---------- the behaviour all of this exists for ----------

BOARD = [
    player("mcbride", "TE", 67.0, 30.0, 15.0, rank=1),
    # WR2 slot already filled below; wr_top is on the clock (ADP 21) with a
    # cliff behind him, so the WR position looks urgent. But he can only start
    # in the FLEX now, where he is worth 31 -- less than an RB nobody is about
    # to take.
    player("wr_top", "WR", 44.0, 31.0, 21.0, rank=5),
    player("wr_next", "WR", 8.0, -5.0, 70.0, rank=6),
    player("rb_a", "RB", 40.0, 40.0, 45.0, rank=8),
    player("rb_b", "RB", 38.0, 38.0, 46.0, rank=9),
    player("qb_a", "QB", 18.0, 18.0, 55.0, rank=4),
    player("k_a", "K", 5.0, 5.0, 150.0),
    player("def_a", "DEF", 4.0, 4.0, 150.0),
    player("my_te", "TE", 50.0, 20.0, 8.0, rank=3),
    player("my_wr1", "WR", 55.0, 42.0, 9.0, rank=1),
    player("my_wr2", "WR", 50.0, 37.0, 10.0, rank=2),
] + [player(f"pad{i}", ("RB", "WR", "TE")[i % 3], 6.0 - i * 0.1,
            -6.0 - i * 0.1, 60.0 + i, rank=20 + i, tier=8) for i in range(40)]

FILLED_WR_TE = ["my_te", "my_wr1", "my_wr2"]


def test_flex_bound_candidate_ranks_on_flex_value_not_positional_value():
    """WR and TE slots are full; RB and FLEX are open.

    wr_top has the higher positional VORP (44 vs 40) and a 36-point cliff
    behind him, so the WR position looks both valuable and urgent. He can only
    start in the FLEX now, where he is worth 31 -- less than an RB nobody is
    about to take. The RB has to come out ahead.
    """
    t = make_tracker(BOARD, FILLED_WR_TE)
    recs = t.recommendations(top_n=6)
    order = [p["sleeper_id"] for _s, _w, p in recs]
    assert "rb_a" in order
    assert order[0] != "wr_top"
    if "wr_top" in order:
        assert order.index("rb_a") < order.index("wr_top")


def test_a_filled_position_no_longer_gets_its_own_urgency_row():
    """The timing half of the fix, which is the half slot-conditional pricing
    could not deliver.

    planner.slot_vorp already priced a flex-bound player correctly in the
    two-pick LEVEL comparison. What survived was the greedy URGENCY row: with
    the WR slot full, a WR-vs-WR difference still argued "take him now or lose
    36 points". Under slot markets that row does not exist -- the only timing
    question left is about the FLEX slot, answered over RB+WR+TE together.
    """
    t = make_tracker(BOARD, FILLED_WR_TE)
    needs = t.my_needs()
    assert needs["WR"] == 0 and needs["TE"] == 0 and needs["FLEX"] == 1
    rep = t.urgency_report()
    assert "FLEX" in rep
    # the pooled market is priced on vorp_flex: best flex option is the RB
    assert rep["FLEX"]["best_now"] == 40.0
    # ...while the WR position, viewed alone, still shows the cliff it always
    # did -- the per-position report is kept, it just no longer gets a vote
    assert rep["WR"]["best_now"] == 44.0
    assert "WR" not in [name for name, _m, _v in t._open_markets(needs)]
    # the flex question is answered over all three positions at once
    assert {"rb_a", "wr_top", "mcbride"} <= set(rep["FLEX"]["survival"])


def test_elite_te_is_still_taken_while_the_te_slot_is_open():
    """The cliff is a real fact about the TE market -- it must keep working
    while you are still shopping in that market."""
    t = make_tracker(BOARD, [])
    rec = t.recommendations(top_n=3)
    assert any(p["pos"] == "TE" for _s, _w, p in rec)


def test_no_duplicate_players_across_markets():
    """An RB with an open RB slot competes in both the RB and FLEX markets."""
    t = make_tracker(BOARD, [])
    recs = t.recommendations(top_n=8)
    ids = [p["sleeper_id"] for _s, _w, p in recs]
    assert len(ids) == len(set(ids)), ids


# ---------- planner ----------

def test_market_for_matches_the_tracker():
    assert market_for("TE", {"TE": 1, "FLEX": 1}) == "TE"
    assert market_for("TE", {"TE": 0, "FLEX": 1}) == "FLEX"
    assert market_for("TE", {"TE": 0, "FLEX": 0}) == "TE"   # bench
    assert market_for("QB", {"QB": 0, "FLEX": 1}) == "QB"   # never flex-eligible

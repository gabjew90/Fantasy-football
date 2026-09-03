import numpy as np

from draftkit.urgency import simulate_survival


def player(pid, pos, vorp, adp):
    return {"sleeper_id": pid, "pos": pos, "vorp": vorp, "adp": adp, "player": pid}


POOL = [
    player("rb1", "RB", 50.0, 5.0),
    player("rb2", "RB", 30.0, 12.0),
    player("rb3", "RB", 10.0, 30.0),
    player("wr1", "WR", 45.0, 6.0),
    player("wr2", "WR", 25.0, 15.0),
    player("qb1", "QB", 20.0, 40.0),
]

OPEN_NEEDS = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1}
RIVALS = [{"slot": s, "needs": dict(OPEN_NEEDS), "user_id": None} for s in (3, 4, 5)]


def test_urgency_positive_when_rivals_want_position():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=13, rivals=RIVALS,
                            seeds={}, rng=rng, sims=300, sigma=6.0)
    # rb1/wr1 are prime targets for 3 rivals -> expected best at next pick < best now
    assert rep["RB"]["urgency"] > 0
    assert rep["RB"]["best_now"] == 50.0
    assert rep["RB"]["e_best_next"] < 50.0


def test_no_intervening_picks_zero_urgency():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=10, rivals=[],
                            seeds={}, rng=rng, sims=50, sigma=6.0)
    assert rep["RB"]["urgency"] == 0.0
    assert rep["RB"]["e_best_next"] == 50.0


def test_survival_probability_bounds_and_ordering():
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=10, next_pick=13, rivals=RIVALS,
                            seeds={}, rng=rng, sims=300, sigma=6.0)
    s1 = rep["RB"]["survival"]["rb1"]
    s3 = rep["RB"]["survival"]["rb3"]
    assert 0.0 <= s1 <= 1.0
    assert s3 >= s1  # later-ADP player survives more often


def test_filled_position_rarely_taken():
    rivals = [{"slot": 3,
               "needs": {"QB": 0, "RB": 2, "WR": 2, "TE": 1, "FLEX": 2, "K": 1, "DEF": 1},
               "user_id": None}]
    rng = np.random.default_rng(7)
    rep = simulate_survival(POOL, current_pick=39, next_pick=41, rivals=rivals,
                            seeds={}, rng=rng, sims=400, sigma=6.0)
    # qb1 at ADP 40 is the obvious ADP pick, but the rival's QB slot is filled
    assert rep["QB"]["survival"]["qb1"] > 0.8


def test_survival_calibration_shrink():
    from draftkit.urgency import calibrate
    assert abs(calibrate(0.96, 0.55) - 0.753) < 0.01   # matches CLV retro bucket
    assert abs(calibrate(0.82, 0.55) - 0.676) < 0.01
    assert abs(calibrate(0.45, 0.55) - 0.4725) < 0.01
    assert calibrate(0.5, 0.55) == 0.5
    assert calibrate(0.96, 1.0) == 0.96                # shrink=1 is identity


def test_reach_mixture_kills_high_adp_studs_more():
    import numpy as np
    from draftkit.urgency import simulate_survival
    # a stud whose ADP is 15 picks after the window: pure gaussian says safe;
    # one-directional reaches should reduce his survival
    pool = ([{"sleeper_id": "stud", "pos": "WR", "vorp": 90.0, "adp": 40.0}]
            + [{"sleeper_id": f"f{i}", "pos": "WR", "vorp": 10.0, "adp": 24.0 + i}
               for i in range(10)])
    rivals = [{"slot": s, "needs": {"WR": 2}, "user_id": None} for s in range(3, 9)]
    kw = dict(sims=400, sigma=6.0, teams=12, survival_shrink=1.0)
    base = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(1),
                             reach_prob=0.0, **kw)
    hot = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(1),
                            reach_prob=0.5, reach_scale=3.0, **kw)
    assert hot["WR"]["survival"]["stud"] < base["WR"]["survival"]["stud"]


def test_run_escalation_targets_the_running_position():
    import numpy as np
    from draftkit.urgency import simulate_survival
    pool = ([{"sleeper_id": f"rb{i}", "pos": "RB", "vorp": 50.0, "adp": 25.0 + i}
             for i in range(6)]
            + [{"sleeper_id": f"wr{i}", "pos": "WR", "vorp": 50.0, "adp": 25.0 + i}
               for i in range(6)])
    rivals = [{"slot": s, "needs": {"RB": 2, "WR": 2}, "user_id": None}
              for s in range(3, 9)]
    kw = dict(sims=400, sigma=6.0, teams=12, survival_shrink=1.0)
    calm = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(2),
                             recent_pos=[], **kw)
    run = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(2),
                            recent_pos=["RB", "RB", "RB"], run_boost=2.5, **kw)
    calm_rb = sum(calm["RB"]["survival"].values())
    run_rb = sum(run["RB"]["survival"].values())
    assert run_rb < calm_rb  # the RB run eats RBs faster


def test_report_carries_raw_and_calibrated_survival_side_by_side():
    """Plan B1: two named vectors -- survival_raw (Monte Carlo frequency) and
    survival (calibrated, displayed) -- so the calibration record and the
    decision path can never confuse them."""
    import numpy as np
    from draftkit.urgency import calibrate
    rng = np.random.default_rng(3)
    a = simulate_survival(POOL, 1, 4, RIVALS, {}, rng, sims=200, sigma=3.0, survival_shrink=1.0)
    rng = np.random.default_rng(3)
    b = simulate_survival(POOL, 1, 4, RIVALS, {}, rng, sims=200, sigma=3.0, survival_shrink=0.55)
    for pos in ("RB", "QB"):
        for sid, raw in a[pos]["survival_raw"].items():
            assert a[pos]["survival"][sid] == raw                      # shrink 1.0: identical
            assert abs(b[pos]["survival"][sid] - calibrate(b[pos]["survival_raw"][sid], 0.55)) < 1e-12
        assert b[pos]["survival_raw"] == a[pos]["survival_raw"]        # same seed: same raw draw
    z = simulate_survival(POOL, 5, 5, [], {}, np.random.default_rng(0), survival_shrink=0.55)
    assert all(v == 1.0 for v in z["RB"]["survival"].values())
    assert all(v == 1.0 for v in z["RB"]["survival_raw"].values())


def test_need_damp_knobs_control_the_filled_position_take_rate():
    """Plan B3: the rival need weighting is a knob, not a constant. A rival
    whose QB slot is filled takes the top QB rarely at the default damp and
    freely when the damp is lifted."""
    import numpy as np
    pool = [{"sleeper_id": "qb1", "pos": "QB", "vorp": 60.0, "adp": 10.0},
            {"sleeper_id": "rb1", "pos": "RB", "vorp": 50.0, "adp": 10.5},
            {"sleeper_id": "rb2", "pos": "RB", "vorp": 40.0, "adp": 11.0},
            {"sleeper_id": "wr1", "pos": "WR", "vorp": 45.0, "adp": 11.5}]
    filled_qb = {"QB": 0, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1}
    rivals = [{"slot": 3, "needs": dict(filled_qb), "user_id": None},
              {"slot": 4, "needs": dict(filled_qb), "user_id": None}]
    base = simulate_survival(pool, 10, 12, rivals, {}, np.random.default_rng(1), sims=400, sigma=2.0,
                             survival_shrink=1.0)
    lifted = simulate_survival(pool, 10, 12, rivals, {}, np.random.default_rng(1), sims=400, sigma=2.0,
                               survival_shrink=1.0, need_damp=1.0, qb_filled_damp=1.0)
    assert base["QB"]["survival"]["qb1"] > 0.8
    assert lifted["QB"]["survival"]["qb1"] < base["QB"]["survival"]["qb1"] - 0.3


def test_explicit_default_knobs_reproduce_the_implicit_call_exactly():
    """Hoisting must not move a number: the same seed with the defaults
    spelled out equals the call that names none of them."""
    import numpy as np
    a = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(9), sims=150, sigma=3.0)
    b = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(9), sims=150, sigma=3.0,
                          need_damp=0.15, qb_filled_damp=0.05, kdef_early_damp=0.02,
                          qb_damp_until_round=10, kdef_typical_round=13, run_ratio=0.0,
                          autopick_sigma_scale=0.5, autopick_need_damp=0.02,
                          autopick_list_prob=0.0, rival_needs_update=True)
    assert a == b


def test_expected_best_is_the_carry_formula_and_rides_alongside_the_joint():
    """Plan B2 scaffolding: expected_best walks candidates by value, each the
    best alive with P(nobody better survived) x P(he survived); the report
    carries it next to the joint estimator without changing the decision."""
    import numpy as np
    from draftkit.urgency import expected_best
    assert expected_best([50.0, 30.0], [1.0, 1.0]) == 50.0
    assert expected_best([50.0, 30.0], [0.0, 1.0]) == 30.0
    assert abs(expected_best([50.0, 30.0], [0.5, 0.5]) - (0.5 * 50 + 0.5 * 0.5 * 30)) < 1e-12
    assert expected_best([30.0, 50.0], [0.5, 0.5]) == expected_best([50.0, 30.0], [0.5, 0.5])   # order-free
    rep = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(4), sims=200, sigma=3.0)
    u = rep["RB"]
    assert u["e_best_next"] == u["e_best_next_joint"]                 # the decision is still the joint
    vals = {p["sleeper_id"]: p["vorp"] for p in POOL if p["pos"] == "RB"}
    ids = list(u["survival"])
    assert abs(u["e_best_next_carry"] - expected_best([vals[i] for i in ids], [u["survival"][i] for i in ids])) < 1e-9


def test_shrink_is_retired_display_equals_decision_vector():
    """DECISIONS #26: survival_shrink defaults to 1.0 everywhere, so the
    displayed survival IS the raw vector the joint decision was drawn from;
    a non-1.0 shrink is allowed but announces itself once."""
    import io
    import sys
    import numpy as np
    from draftkit import urgency
    from draftkit.tracker import Tracker
    assert Tracker.survival_shrink == 1.0
    rep = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(5), sims=100, sigma=3.0)
    assert rep["RB"]["survival"] == rep["RB"]["survival_raw"]
    assert rep["RB"]["e_best_next"] == rep["RB"]["e_best_next_joint"]
    urgency._WARNED_SHRINK.clear()
    err, sys.stderr = sys.stderr, io.StringIO()
    try:
        simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(5), sims=50, sigma=3.0, survival_shrink=0.55)
        simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(5), sims=50, sigma=3.0, survival_shrink=0.55)
        out = sys.stderr.getvalue()
    finally:
        sys.stderr = err
    assert out.count("SURVIVAL SHRINK") == 1


def _autopick_setup():
    import numpy as np
    pool = ([{"sleeper_id": "stud", "pos": "WR", "vorp": 90.0, "adp": 40.0}]
            + [{"sleeper_id": f"f{i}", "pos": "WR", "vorp": 10.0, "adp": 24.0 + i} for i in range(10)])
    return pool, np


def test_autopick_rival_never_reaches():
    """Plan B5: with reach_prob 0.5 a human rival reaches for the stud; an
    autopick rival walks his list. Same seed, same random stream."""
    pool, np = _autopick_setup()
    kw = dict(sims=400, sigma=6.0, teams=12, survival_shrink=1.0, reach_prob=1.0, reach_scale=3.0)
    human = [{"slot": s, "needs": {"WR": 2}, "user_id": None} for s in range(3, 9)]
    bots = [dict(r, autopick=True) for r in human]
    h = simulate_survival(pool, 25, 31, human, {}, np.random.default_rng(1), **kw)      # always reaching
    b = simulate_survival(pool, 25, 31, bots, {}, np.random.default_rng(1), **kw)
    no_reach = simulate_survival(pool, 25, 31, bots, {}, np.random.default_rng(1), **dict(kw, reach_prob=0.0))
    assert b["WR"]["survival"]["stud"] > h["WR"]["survival"]["stud"]
    assert b["WR"]["survival"]["stud"] == no_reach["WR"]["survival"]["stud"]     # reach is inert for autopick


def test_autopick_rival_fills_an_open_starter_slot_before_a_better_bench_player():
    """The inverse of the human case: Yahoo's autopick takes the RB that
    fills his open slot over a higher-ranked WR who fills nothing."""
    import numpy as np
    pool = [{"sleeper_id": "wr1", "pos": "WR", "vorp": 60.0, "adp": 10.0},
            {"sleeper_id": "rb1", "pos": "RB", "vorp": 30.0, "adp": 10.5},
            {"sleeper_id": "rb2", "pos": "RB", "vorp": 20.0, "adp": 11.0}]
    needs = {"QB": 0, "RB": 1, "WR": 0, "TE": 0, "FLEX": 0, "K": 1, "DEF": 1}   # RB open, WR full
    rivals = [{"slot": 3, "needs": dict(needs), "user_id": None, "autopick": True}]
    rep = simulate_survival(pool, 10, 11, rivals, {}, np.random.default_rng(2), sims=400, sigma=2.0,
                            survival_shrink=1.0)
    assert rep["WR"]["survival"]["wr1"] > 0.9         # the WR is left alone
    assert rep["RB"]["survival"]["rb1"] < 0.6         # the slot-filling RB goes
    # once every starter slot is full he follows rank: the WR is now in play
    full = [{"slot": 3, "needs": {k: 0 for k in needs}, "user_id": None, "autopick": True}]
    rep2 = simulate_survival(pool, 10, 11, full, {}, np.random.default_rng(2), sims=400, sigma=2.0,
                             survival_shrink=1.0)
    assert rep2["WR"]["survival"]["wr1"] < 0.7


def test_autopick_noise_is_tighter_than_a_humans():
    """sigma x autopick_sigma_scale: the top-of-list player is taken more
    surely by an autopick seat."""
    import numpy as np
    pool = [{"sleeper_id": "top", "pos": "RB", "vorp": 50.0, "adp": 10.0}] + \
           [{"sleeper_id": f"r{i}", "pos": "RB", "vorp": 20.0, "adp": 14.0 + i} for i in range(6)]
    needs = {"RB": 2}
    human = [{"slot": 3, "needs": dict(needs), "user_id": None}]
    bot = [dict(human[0], autopick=True)]
    h = simulate_survival(pool, 10, 11, human, {}, np.random.default_rng(3), sims=600, sigma=6.0, survival_shrink=1.0)
    b = simulate_survival(pool, 10, 11, bot, {}, np.random.default_rng(3), sims=600, sigma=6.0, survival_shrink=1.0,
                          autopick_sigma_scale=0.25)
    assert b["RB"]["survival"]["top"] < h["RB"]["survival"]["top"]


def test_run_detector_ignores_a_positions_expected_share():
    """Plan B4: two WRs in a row in a pool that is 90% WR by ADP mass is not
    a run; the boost must not fire, so the report is identical to a calm
    window (same seed)."""
    import numpy as np
    pool = ([{"sleeper_id": f"wr{i}", "pos": "WR", "vorp": 40.0, "adp": 25.0 + i} for i in range(9)]
            + [{"sleeper_id": "rb0", "pos": "RB", "vorp": 40.0, "adp": 34.0}])
    rivals = [{"slot": s, "needs": {"RB": 2, "WR": 3, "FLEX": 1}, "user_id": None} for s in range(3, 9)]
    kw = dict(sims=300, sigma=6.0, teams=12, survival_shrink=1.0, run_ratio=1.5)   # the RELATIVE rule under test
    calm = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(4), recent_pos=[], **kw)
    wrs = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(4), recent_pos=["WR", "WR"], **kw)
    assert wrs["WR"]["survival"] == calm["WR"]["survival"]
    assert wrs["RB"]["survival"] == calm["RB"]["survival"]


def test_run_detector_fires_on_a_relative_surplus():
    """Two TEs in a row where the model expected almost none IS a run."""
    import numpy as np
    pool = ([{"sleeper_id": f"rb{i}", "pos": "RB", "vorp": 50.0, "adp": 25.0 + i} for i in range(5)]
            + [{"sleeper_id": f"wr{i}", "pos": "WR", "vorp": 50.0, "adp": 25.0 + i} for i in range(5)]
            + [{"sleeper_id": f"te{i}", "pos": "TE", "vorp": 30.0, "adp": 45.0 + i} for i in range(2)])
    rivals = [{"slot": s, "needs": {"RB": 2, "WR": 2, "TE": 1}, "user_id": None} for s in range(3, 9)]
    kw = dict(sims=400, sigma=6.0, teams=12, survival_shrink=1.0, run_boost=3.0, run_ratio=1.5)
    calm = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(5), recent_pos=[], **kw)
    run = simulate_survival(pool, 25, 31, rivals, {}, np.random.default_rng(5), recent_pos=["TE", "TE"], **kw)
    assert sum(run["TE"]["survival"].values()) < sum(calm["TE"]["survival"].values())
    # run_ratio 0 is the old absolute rule: the 90%-WR case then DOES boost
    pool2 = ([{"sleeper_id": f"wr{i}", "pos": "WR", "vorp": 40.0, "adp": 25.0 + i} for i in range(9)]
             + [{"sleeper_id": "rb0", "pos": "RB", "vorp": 40.0, "adp": 34.0}])
    riv2 = [{"slot": s, "needs": {"RB": 2, "WR": 3, "FLEX": 1}, "user_id": None} for s in range(3, 9)]
    a = simulate_survival(pool2, 25, 31, riv2, {}, np.random.default_rng(6), recent_pos=["WR", "WR"],
                          sims=300, sigma=6.0, teams=12, survival_shrink=1.0, run_ratio=0.0)
    b = simulate_survival(pool2, 25, 31, riv2, {}, np.random.default_rng(6), recent_pos=[],
                          sims=300, sigma=6.0, teams=12, survival_shrink=1.0, run_ratio=0.0)
    assert a["WR"]["survival"] != b["WR"]["survival"]


def test_same_slot_twice_in_the_window_consumes_its_needs():
    """Plan B6: at a snake turn a rival picks twice inside my window. With
    QB the only open slot he takes one QB, not two: after a simulated QB his
    second pick no longer wants a QB, so the second QB survives far more
    often than when two DIFFERENT QB-needy rivals pick."""
    import numpy as np
    pool = [{"sleeper_id": "qb1", "pos": "QB", "vorp": 60.0, "adp": 10.0},
            {"sleeper_id": "qb2", "pos": "QB", "vorp": 55.0, "adp": 11.0},
            {"sleeper_id": "rb1", "pos": "RB", "vorp": 30.0, "adp": 12.0},
            {"sleeper_id": "wr1", "pos": "WR", "vorp": 30.0, "adp": 12.5}]
    needs = {"QB": 1, "RB": 0, "WR": 0, "TE": 0, "FLEX": 0, "K": 1, "DEF": 1}
    same = [{"slot": 10, "needs": dict(needs), "user_id": None},
            {"slot": 10, "needs": dict(needs), "user_id": None}]        # picks 10 and 11: the turn
    different = [{"slot": 10, "needs": dict(needs), "user_id": None},
                 {"slot": 8, "needs": dict(needs), "user_id": None}]
    kw = dict(sims=500, sigma=2.0, teams=10, survival_shrink=1.0)
    a = simulate_survival(pool, 10, 12, same, {}, np.random.default_rng(7), **kw)
    b = simulate_survival(pool, 10, 12, different, {}, np.random.default_rng(7), **kw)
    assert a["QB"]["survival"]["qb2"] > b["QB"]["survival"]["qb2"] + 0.3
    # with the update off the same-slot case behaves like two strangers
    c = simulate_survival(pool, 10, 12, same, {}, np.random.default_rng(7), rival_needs_update=False, **kw)
    assert abs(c["QB"]["survival"]["qb2"] - b["QB"]["survival"]["qb2"]) < 0.1


def test_needs_update_is_a_no_op_when_every_slot_picks_once():
    """Rivals that appear once keep the precomputed vector: numerics identical
    with the flag on or off (same seed)."""
    import numpy as np
    a = simulate_survival(POOL, 10, 13, RIVALS, {}, np.random.default_rng(8), sims=200, sigma=6.0)
    b = simulate_survival(POOL, 10, 13, RIVALS, {}, np.random.default_rng(8), sims=200, sigma=6.0,
                          rival_needs_update=False)
    assert a == b


# ---------- DECISIONS #35: an autopick seat walks Yahoo's default list ----------

def _list_walk_pool():
    """One-pick window fixtures for the list walker. The top-ADP RB carries
    the WORSE Yahoo rank, and the best-yrank player of all is a WR the rival
    has no open slot for -- so the walker must obey yrank (not adp) AND the
    starters-first need filter to land on rb_b."""
    pool = [{"sleeper_id": "wr1", "pos": "WR", "vorp": 60.0, "adp": 10.0, "yrank": 1.0},
            {"sleeper_id": "rb_a", "pos": "RB", "vorp": 50.0, "adp": 10.5, "yrank": 8.0},
            {"sleeper_id": "rb_b", "pos": "RB", "vorp": 40.0, "adp": 12.0, "yrank": 3.0},
            {"sleeper_id": "rb_c", "pos": "RB", "vorp": 30.0, "adp": 13.0, "yrank": 9.0}]
    needs = {"QB": 0, "RB": 1, "WR": 0, "TE": 0, "FLEX": 0, "K": 1, "DEF": 1}   # RB open, WR full
    bot = [{"slot": 3, "needs": dict(needs), "user_id": None, "autopick": True}]
    return pool, bot


def test_autopick_list_prob_zero_is_the_no_arg_call_exactly():
    """The knob is OFF by default: spelling out 0.0 changes nothing, in a
    room with autopick seats and in one without (same seed, dict equality)."""
    import numpy as np
    pool, np = _autopick_setup()
    bots = [{"slot": s, "needs": {"WR": 2}, "user_id": None, "autopick": True} for s in range(3, 9)]
    kw = dict(sims=200, sigma=6.0, teams=12, reach_prob=0.5)
    a = simulate_survival(pool, 25, 31, bots, {}, np.random.default_rng(11), **kw)
    b = simulate_survival(pool, 25, 31, bots, {}, np.random.default_rng(11), autopick_list_prob=0.0, **kw)
    assert a == b
    c = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(12), sims=150, sigma=3.0)
    d = simulate_survival(POOL, 1, 4, RIVALS, {}, np.random.default_rng(12), sims=150, sigma=3.0,
                          autopick_list_prob=0.0)
    assert c == d


def test_autopick_list_walker_takes_the_lowest_yrank_need_fitting_player():
    """list_prob 1, one autopick rival, one pick: the lowest-yrank player who
    fills an open starter slot is gone in every sim (survival 0.0), everyone
    else survives (1.0). rb_a is the top-ADP RB but ranks worse on Yahoo's
    list; wr1 is Yahoo's #1 but the WR slot is full."""
    import numpy as np
    pool, bot = _list_walk_pool()
    rep = simulate_survival(pool, 10, 11, bot, {}, np.random.default_rng(2), sims=100, sigma=6.0,
                            survival_shrink=1.0, autopick_list_prob=1.0)
    assert rep["RB"]["survival"]["rb_b"] == 0.0
    assert rep["RB"]["survival"]["rb_a"] == 1.0
    assert rep["RB"]["survival"]["rb_c"] == 1.0
    assert rep["WR"]["survival"]["wr1"] == 1.0
    # once every starter slot is full the need filter is vacuous: the walker
    # follows the raw list and Yahoo's #1 (the WR) goes
    full = [dict(bot[0], needs={k: 0 for k in bot[0]["needs"]})]
    rep2 = simulate_survival(pool, 10, 11, full, {}, np.random.default_rng(2), sims=100, sigma=6.0,
                             survival_shrink=1.0, autopick_list_prob=1.0)
    assert rep2["WR"]["survival"]["wr1"] == 0.0
    assert all(v == 1.0 for v in rep2["RB"]["survival"].values())


def test_autopick_list_prob_is_inert_for_human_seats():
    """A window of only human rivals: identical report at list_prob 0 and 1
    under one seed (the walk is gated on the autopick flag)."""
    import numpy as np
    pool = [dict(p, yrank=100.0 - p["adp"]) for p in POOL]      # a yrank that disagrees with adp
    kw = dict(sims=200, sigma=6.0, reach_prob=0.3)
    a = simulate_survival(pool, 10, 13, RIVALS, {}, np.random.default_rng(13), autopick_list_prob=0.0, **kw)
    b = simulate_survival(pool, 10, 13, RIVALS, {}, np.random.default_rng(13), autopick_list_prob=1.0, **kw)
    assert a == b


def test_autopick_list_walker_yrank_falls_back_to_adp():
    """Without a yrank key the walker orders by adp: the same call with
    yrank spelled out as adp is identical, and the lowest-ADP need-fitting
    player is the one taken."""
    import numpy as np
    pool, bot = _list_walk_pool()
    bare = [{k: v for k, v in p.items() if k != "yrank"} for p in pool]
    spelled = [dict(p, yrank=p["adp"]) for p in bare]
    kw = dict(sims=100, sigma=6.0, survival_shrink=1.0, autopick_list_prob=1.0)
    a = simulate_survival(bare, 10, 11, bot, {}, np.random.default_rng(3), **kw)
    b = simulate_survival(spelled, 10, 11, bot, {}, np.random.default_rng(3), **kw)
    assert a == b
    assert a["RB"]["survival"]["rb_a"] == 0.0          # adp 10.5: the best RB by adp
    assert a["RB"]["survival"]["rb_b"] == 1.0
    assert a["WR"]["survival"]["wr1"] == 1.0
    # a None yrank is treated as absent, not as rank 0
    none_rank = [dict(p, yrank=None) for p in bare]
    c = simulate_survival(none_rank, 10, 11, bot, {}, np.random.default_rng(3), **kw)
    assert c == a


def test_autopick_list_walk_reuses_the_reach_uniform_so_a_human_upstream_is_unchanged():
    """The walk decision must not add a draw: with a HUMAN picking first and
    an autopick seat second, the human's picks are the same stream at
    list_prob 0 and 1. The human only ever takes WRs (need_damp 0) and the
    bot only ever takes RBs (autopick_need_damp 0), so the WR survivals are
    the human's fingerprint: identical across the two runs, while the RB
    survivals show the bot did change (list_prob 1 -> rb_b always)."""
    import numpy as np
    pool = [{"sleeper_id": f"wr{i}", "pos": "WR", "vorp": 40.0, "adp": 10.0 + i, "yrank": 50.0 + i}
            for i in range(4)] + \
           [{"sleeper_id": "rb_a", "pos": "RB", "vorp": 50.0, "adp": 10.5, "yrank": 8.0},
            {"sleeper_id": "rb_b", "pos": "RB", "vorp": 40.0, "adp": 12.0, "yrank": 3.0},
            {"sleeper_id": "rb_c", "pos": "RB", "vorp": 30.0, "adp": 13.0, "yrank": 9.0}]
    human = {"slot": 3, "needs": {"QB": 0, "RB": 0, "WR": 2, "TE": 0, "FLEX": 0}, "user_id": None}
    bot = {"slot": 4, "needs": {"QB": 0, "RB": 1, "WR": 0, "TE": 0, "FLEX": 0}, "user_id": None,
           "autopick": True}
    kw = dict(sims=300, sigma=6.0, survival_shrink=1.0, reach_prob=0.4, reach_scale=3.0,
              need_damp=0.0, qb_filled_damp=0.0, autopick_need_damp=0.0)
    a = simulate_survival(pool, 10, 12, [human, bot], {}, np.random.default_rng(21), autopick_list_prob=0.0, **kw)
    b = simulate_survival(pool, 10, 12, [human, bot], {}, np.random.default_rng(21), autopick_list_prob=1.0, **kw)
    assert a["WR"]["survival"] == b["WR"]["survival"]            # the human is untouched
    assert 0.0 < min(a["WR"]["survival"].values()) < 1.0         # ...and he was actually drawing
    assert b["RB"]["survival"]["rb_b"] == 0.0                     # the bot walked the list
    assert b["RB"]["survival"]["rb_a"] == 1.0 and b["RB"]["survival"]["rb_c"] == 1.0
    assert a["RB"]["survival"] != b["RB"]["survival"]             # at list_prob 0 he drew from the Gaussian

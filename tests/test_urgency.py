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
                          qb_damp_until_round=10, kdef_typical_round=13, run_ratio=1.5,
                          autopick_sigma_scale=0.5, rival_needs_update=True)
    assert a == b

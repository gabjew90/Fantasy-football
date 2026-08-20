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

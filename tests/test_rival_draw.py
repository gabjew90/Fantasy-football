"""The rival_draw knob (survival study 2026-09-04, DECISIONS #46).

Three ways a simulated rival chooses among the alive pool. The default,
`lottery`, is today's code path untouched; `floored` and `order` exist so the
refit harness can score them on the archived rooms. The one property that
must hold by construction: a player already PAST his ADP survives the same
rivals less under each successive form (lottery > floored > order), because
that is the miss the study exists to measure.
"""

import numpy as np
import pytest

from draftkit.urgency import simulate_survival


def _pool():
    faller = {"sleeper_id": "F", "pos": "QB", "vorp": 60.0, "adp": 21.0}
    rest = [{"sleeper_id": f"p{i}", "pos": ["RB", "WR", "TE", "QB"][i % 4], "vorp": 40.0 - i * 0.5, "adp": 28.0 + i}
            for i in range(40)]
    return [faller] + rest


def _rivals(n=3):
    needs = {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "FLEX": 1, "K": 1, "DEF": 1, "BN": 6}
    return [{"slot": 5 + i, "needs": dict(needs), "user_id": None} for i in range(n)]


def _run(mode, seed=1, **kw):
    return simulate_survival(_pool(), 30, 33, _rivals(), {}, np.random.default_rng(seed),
                             sims=1500, sigma=6.0, teams=10, rival_draw=mode, **kw)


def test_default_is_the_lottery_and_the_keyword_is_optional():
    a = simulate_survival(_pool(), 30, 33, _rivals(), {}, np.random.default_rng(3), sims=300, sigma=6.0, teams=10)
    b = simulate_survival(_pool(), 30, 33, _rivals(), {}, np.random.default_rng(3), sims=300, sigma=6.0, teams=10,
                          rival_draw="lottery")
    assert a["QB"]["survival_raw"] == b["QB"]["survival_raw"]


def test_a_faller_survives_less_under_each_successive_form():
    s = {m: _run(m)["QB"]["survival_raw"]["F"] for m in ("lottery", "floored", "order")}
    assert 0.0 <= s["order"] < s["floored"] < s["lottery"] <= 1.0
    # the lottery treats a player 9 picks past his ADP as SAFER than an
    # on-ADP player; floored puts them level; order makes him the likeliest pick
    on_adp = {m: _run(m)["RB"]["survival_raw"]["p0"] for m in ("lottery", "floored", "order")}
    assert s["lottery"] > on_adp["lottery"]
    assert abs(s["floored"] - on_adp["floored"]) < 0.08
    assert s["order"] < on_adp["order"]


def test_every_form_returns_probabilities_for_every_pooled_player():
    for m in ("lottery", "floored", "order"):
        r = _run(m, seed=7)
        got = {pid for pos in r if isinstance(r[pos], dict) for pid in (r[pos].get("survival_raw") or {})}
        assert got == {p["sleeper_id"] for p in _pool()}
        assert all(0.0 <= v <= 1.0 for pos in r if isinstance(r[pos], dict)
                   for v in (r[pos].get("survival_raw") or {}).values())


def test_unknown_form_is_refused():
    with pytest.raises(ValueError):
        _run("coinflip")


def test_the_tracker_knob_is_registered_as_a_string():
    from draftkit.tracker import Tracker
    assert ("rival_draw", str) in Tracker.ENGINE_KNOBS
    assert Tracker.rival_draw == "lottery"

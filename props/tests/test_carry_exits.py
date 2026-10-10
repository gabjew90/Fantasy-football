"""Round 44 (reports/round44_carry_exits.md): the early-exit chance in the carries split.

Off is today's sampler call for call; on, every player's average carries stay where they were
(mean-preserving), the exiting back's low tail grows, and the starting QB is untouched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))

import model as M  # noqa: E402

RESID = np.linspace(-4.0, 4.0, 201)
SHARES = [0.12, 0.55, 0.20, 0.03]          # QB, RB1, RB2, a receiver
YPC = [5.0, 4.4, 4.1, 6.0]
BASE = {"share_conc_carries": 20.0, "share_conc_qb": 80.0, "rush_other_share": 0.12, "rush_norm_strength": 0.5,
        "rush_norm_lead": 1.0, "rush_norm_qb": False, "eff_sd_rush": 0.15}


def _run(width, n=200_000, seed=11, qb=0):
    car, _yds, team = M.simulate_team_rush(np.random.default_rng(seed), n, 26.0, 28.0, SHARES, YPC, RESID,
                                            width=width, qb_index=qb)
    return car, team


def test_off_is_the_shipped_sampler_call_for_call():
    a, ta = _run(BASE, n=3000)
    b, tb = _run({**BASE, "carry_exit_rate": 0.0, "carry_exit_min_share": 0.15, "carry_exit_keep": 0.4}, n=3000)
    assert np.array_equal(ta, tb)
    for x, y in zip(a, b):
        assert np.array_equal(x, y)


def test_exits_need_a_named_starting_qb():
    """A running QB is not a back: without qb_index the option stays off, call for call."""
    a, _ = _run(BASE, n=3000, qb=None)
    b, _ = _run({**BASE, "carry_exit_rate": 0.05}, n=3000, qb=None)
    for x, y in zip(a, b):
        assert np.array_equal(x, y)


def test_exits_keep_every_players_average_carries():
    off, _ = _run(BASE)
    on, _ = _run({**BASE, "carry_exit_rate": 0.05})
    for j, (x, y) in enumerate(zip(off, on)):
        if x.mean() > 0.5:
            assert abs(y.mean() / x.mean() - 1) < 0.01, (j, x.mean(), y.mean())


def test_exits_fatten_the_lead_backs_low_tail_and_leave_the_qb_alone():
    off, t_off = _run(BASE)
    on, t_on = _run({**BASE, "carry_exit_rate": 0.05})
    p = off[1].mean() / t_off.mean()
    low = lambda car, t: float((car <= M.EXIT_KEEP * p * t).mean())
    assert low(on[1], t_on) > low(off[1], t_off) + 0.02, "about rate x P(an exit lands under the line) more"
    # the QB neither exits nor receives: his carries' distribution is unchanged in mean and spread
    assert abs(on[0].mean() / off[0].mean() - 1) < 0.01 and abs(on[0].std() / off[0].std() - 1) < 0.02
    # a receiver below the share floor never exits, but gains a little in the RB1's exit games
    assert abs(on[3].mean() / off[3].mean() - 1) < 0.02


def test_the_backup_takes_the_lead_backs_carries_when_he_exits():
    rng = np.random.default_rng(5)
    P = np.tile(np.array([0.12, 0.55, 0.20, 0.03, 0.10]), (50_000, 1))
    can = np.array([False, True, True, False, False])
    rec = np.array([False, True, True, True, False])
    out = M._apply_exits(rng, P, 0.5, can, rec, P[0])
    assert np.allclose(out.sum(axis=1), 1.0)
    assert np.allclose(out[:, 0], 0.12) and np.allclose(out[:, 4], 0.10), "the QB and 'other' are untouched"
    exited1 = out[:, 1] < 0.55 * M.EXIT_KEEP + 1e-12
    assert out[exited1, 2].mean() > 0.20 + 0.1, "the RB2 gains the bulk of an RB1 exit"


def test_the_width_file_refuses_a_bad_rate():
    with pytest.raises(ValueError, match="carry_exit_rate"):
        M.validate_width({"carry_exit_rate": 0.6})
    with pytest.raises(ValueError, match="carry_exit_min_share"):
        M.validate_width({"carry_exit_min_share": 0.0})
    with pytest.raises(ValueError, match="carry_exit_keep"):
        M.validate_width({"carry_exit_keep": 1.0})


def test_the_fixed_point_is_exact_with_several_exiters_and_a_tiny_receiver():
    p = np.array([0.10, 0.40, 0.25, 0.16, 0.01, 0.08])
    can = np.array([False, True, True, True, False, False])
    rec = np.array([False, True, True, True, True, False])
    base = M.exit_adjusted_shares(p, can, rec, 0.05)
    out = M._apply_exits(np.random.default_rng(2), np.tile(base, (400_000, 1)), 0.05, can, rec, base)
    assert np.allclose(out.mean(axis=0)[1:5], p[1:5], rtol=0.02, atol=2e-4)

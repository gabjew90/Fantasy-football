"""Layer 3: exact joint touchdown probabilities, pinned against independent
computations -- the single-leg formula v1 prices with, brute-force
enumeration of where each touchdown goes, and the independence identity."""

from __future__ import annotations

import itertools
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
pd = pytest.importorskip("pandas")
import td_alloc as A  # noqa: E402
import td_joint as J  # noqa: E402
import td_model as T  # noqa: E402


def _flat(q):
    """The same per-TD share at every opponent count (no mix shift)."""
    return np.tile(np.asarray(q, float)[:, None], (1, J.OPP_BUCKETS))


def test_single_leg_equals_the_v1_formula_when_the_mix_does_not_shift():
    q = np.array([0.30, 0.12, 0.02])
    P = J.joint_counts(2.6, 2.1)
    got = J.p_any(_flat(q), P, own_axis=0)
    want = A.p_score_dist(q, T.count_pmf([2.6], n=T.LAYER1["trials"])[0])
    assert got == pytest.approx(want, abs=1e-12)


def test_same_team_pair_matches_brute_force_enumeration():
    """Enumerate every assignment of k touchdowns to A, B or 'someone else'."""
    qa, qb = 0.30, 0.20
    pmf = T.count_pmf([2.4], n=T.LAYER1["trials"])[0]
    brute = 0.0
    for k in range(T.LAYER1["trials"] + 1):               # every count the Binomial allows
        for seq in itertools.product((0, 1, 2), repeat=k):
            pr = np.prod([(qa, qb, 1 - qa - qb)[s] for s in seq]) if k else 1.0
            if 0 in seq and 1 in seq:
                brute += pmf[k] * pr
    P = J.joint_counts(2.4, 1.0)
    got = J.p_all_same_team(_flat([qa, qb]), P, own_axis=0)
    assert got == pytest.approx(brute, abs=1e-12)
    # teammates share touchdowns: the joint is BELOW the product at these shares
    pa = J.p_any(_flat([qa, qb]), P, own_axis=0)
    assert got < pa[0] * pa[1]


def test_cross_team_pair_is_the_product_when_nothing_links_the_teams():
    P = J.joint_counts(2.6, 2.1)
    qa, qb = _flat([0.25]), _flat([0.18])
    pa = J.p_any(qa, P, own_axis=0)[0]
    pb = J.p_any(qb, P, own_axis=1)[0]
    assert J.p_pair_cross(qa[0], qb[0], P) == pytest.approx(pa * pb, abs=1e-12)


def test_the_mix_shift_links_the_teams():
    """If the opponent scoring more CUTS a rusher's share, a rusher and the
    opponent's receiver are negatively linked: joint below the product."""
    P = J.joint_counts(2.6, 2.6)
    rusher = np.array([0.40, 0.35, 0.30, 0.25, 0.20])    # falls with opponent TDs
    receiver = _flat([0.25])[0]
    pa = J.p_any(rusher[None], P, own_axis=0)[0]
    pb = J.p_any(receiver[None], P, own_axis=1)[0]
    assert J.p_pair_cross(rusher, receiver, P) < pa * pb


def test_mix_shift_multipliers_are_one_on_average():
    tg = pd.DataFrame({"game_id": ["g1", "g1", "g2", "g2"], "team": ["A", "B", "A", "B"],
                       "opp": ["B", "A", "B", "A"], "off_tds": [1, 4, 3, 2],
                       "qb_rush": [0, 1, 0, 0], "rush_in5": [1, 1, 1, 1], "rush_far": [0, 1, 1, 0],
                       "pass_rz": [0, 1, 1, 1], "pass_far": [0, 0, 0, 0]})
    sh = J.mix_shift(tg, min_tds=0)
    assert list(sh.columns) == J.CH and len(sh) == J.OPP_BUCKETS
    m = J.mixes_by_opp(pd.Series({c: 0.2 for c in J.CH}), sh)
    assert m.sum(axis=1) == pytest.approx(np.ones(J.OPP_BUCKETS))


# ------------------------------------------------------------ correlated counts

def test_the_copula_preserves_each_teams_distribution_exactly():
    pa = T.count_pmf([2.7], n=T.LAYER1["trials"])[0]
    pb = T.count_pmf([1.9], n=T.LAYER1["trials"])[0]
    for r in (0.0, 0.3, 0.6):
        P = J.copula_joint(pa, pb, r)
        assert P.sum() == pytest.approx(1.0)
        assert P.sum(axis=1) == pytest.approx(pa, abs=1e-6)
        assert P.sum(axis=0) == pytest.approx(pb, abs=1e-6)


def test_the_copula_correlates_the_counts_and_zero_is_independent():
    pa = T.count_pmf([2.5], n=T.LAYER1["trials"])[0]
    K = np.arange(len(pa))
    assert J.copula_joint(pa, pa, 0.0) == pytest.approx(np.outer(pa, pa))
    P = J.copula_joint(pa, pa, 0.5)
    ex = (K[:, None] * K[None, :] * P).sum() - (K * pa).sum() ** 2
    assert ex > 0                                             # positive covariance
    # and a cross-team pair rises above the product when counts correlate
    q = np.tile([[0.3]], (1, J.OPP_BUCKETS))
    p_ind = J.p_pair_cross(q[0], q[0], J.copula_joint(pa, pa, 0.0))
    assert J.p_pair_cross(q[0], q[0], P) > p_ind


def test_normal_helpers_are_accurate():
    x = np.array([-2.5, -1.0, 0.0, 0.7, 2.0])
    assert J._ncdf(J._ndtri(J._ncdf(x))) == pytest.approx(J._ncdf(x), abs=1e-6)
    assert J._ncdf(np.array([0.0, 1.959964]))[1] == pytest.approx(0.975, abs=2e-7)

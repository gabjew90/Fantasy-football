"""Touchdown model, LAYER 3: joint probabilities -- who scores TOGETHER.

anytime_td_v1 prices each player alone. A parlay or a "both score" market
needs the joint: teammates share a finite number of touchdowns (negative
dependence), a big day for the offence lifts everyone (positive), and the two
teams are linked through the game (a team chasing 27+ scores through the air,
reports/td_diagnostics.md).

EXACT, NOT SIMULATED. Given the joint distribution of the two teams'
offensive touchdown counts and each player's per-touchdown share, every
touchdown independently goes to a player with probability equal to his share,
so for a team scoring k:

  P(A scores | k)            = 1 - (1 - qA)^k
  P(A and B score | k)       = 1 - (1 - qA)^k - (1 - qB)^k + (1 - qA - qB)^k
  P(all of S score | k)      = sum over T subset of S of (-1)^|T| (1 - q_T)^k

and cross-team terms multiply inside the sum over (k_home, k_away). No Monte
Carlo noise; a pair is priced to machine precision.

THE CROSS-TEAM LINK. Each team's channel mix is conditioned on the OTHER
team's touchdown count through a multiplier table estimated on the tune
seasons (mix_shift): when the opponent scores more, rushing channels shrink
and passing grows. A player's per-touchdown share is then a function of the
opponent's count.

THE COUNTS ARE CORRELATED. Beyond their implied totals the two teams'
offensive-TD counts correlate +0.21 (tune) and +0.15 (test): shootouts. They
are joined by a one-factor Gaussian copula -- a shared game-script latent Z,
each count's latent = r Z + sqrt(1 - r^2) e -- which leaves each team's own
distribution EXACTLY as layer 1 has it, so single-leg prices cannot move. r is
tuned on the tune seasons by the likelihood of the actual score pairs.

Stdlib + numpy + pandas only.
"""

from __future__ import annotations

from itertools import combinations

import numpy as np
import pandas as pd

import td_model as T

OPP_BUCKETS = 5            # opponent offensive TDs 0, 1, 2, 3, 4+
# The copula loading, PROVISIONAL: set by matching the pooled residual count
# correlation (+0.175 over 2022-25 and 2018-19), not by likelihood. Used only in
# the shadow log, never in a price.
R_PROVISIONAL = 0.43
# Dirichlet concentration of a team's split of its touchdowns (game-to-game
# variation), tuned on the three-teammate class of 2022-23 (DECISIONS #89).
DIRICHLET_C = 100.0
# The committed gate output: which parlay classes are open and each one's model.
GATE_FILE = "td_parlay_gate.json"
STRUCTURES = {"joint": ("plain", False), "joint + mix shift": ("shift", False),
              "joint + mix shift + copula": ("shift", True), "joint + copula": ("plain", True)}
CH = list(T.OFFENSIVE)
_GH_Z, _GH_W = np.polynomial.hermite_e.hermegauss(40)     # nodes/weights for a standard normal
_GH_W = _GH_W / _GH_W.sum()


def _ncdf(x):
    """Standard normal CDF (Abramowitz-Stegun 7.1.26 erf, |error| < 1.5e-7)."""
    x = np.asarray(x, float)
    z = np.abs(x) / np.sqrt(2.0)
    t = 1.0 / (1.0 + 0.3275911 * z)
    y = 1.0 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t
               + 0.254829592) * t * np.exp(-z * z)
    return 0.5 * (1.0 + np.sign(x) * y)


def _ndtri(p):
    """Inverse standard normal CDF (Acklam), clipped to +-8."""
    p = np.clip(np.asarray(p, float), 1e-15, 1 - 1e-15)
    a = [-3.969683028665376e+01, 2.209460984245205e+02, -2.759285104469687e+02,
         1.383577518672690e+02, -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02, -1.556989798598866e+02,
         6.680131188771972e+01, -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01, -2.400758277161838e+00,
         -2.549732539343734e+00, 4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01, 2.445134137142996e+00, 3.754408661907416e+00]
    lo, hi = 0.02425, 1 - 0.02425
    out = np.empty_like(p)
    m = p < lo
    q = np.sqrt(-2 * np.log(p[m]))
    out[m] = (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
             ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    m = (p >= lo) & (p <= hi)
    q = p[m] - 0.5
    r = q * q
    out[m] = (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / \
             (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)
    m = p > hi
    q = np.sqrt(-2 * np.log(1 - p[m]))
    out[m] = -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / \
             ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    return np.clip(out, -8, 8)


def copula_joint(pa: np.ndarray, pb: np.ndarray, r: float) -> np.ndarray:
    """P[k_a, k_b] joining two count pmfs with a one-factor Gaussian copula of
    loading r (latent correlation r^2). Margins are preserved exactly."""
    if r == 0:
        return np.outer(pa, pb)
    s = np.sqrt(1.0 - r * r)

    def cond(pmf):
        # P(count = k | Z = z) for every node: differences of the latent CDF at the cut points
        cut = _ndtri(np.cumsum(pmf)[:-1])                   # K-1 finite thresholds
        F = _ncdf((cut[None, :] - r * _GH_Z[:, None]) / s)   # nodes x (K-1)
        F = np.hstack([np.zeros((len(_GH_Z), 1)), F, np.ones((len(_GH_Z), 1))])
        return np.diff(F, axis=1)                            # nodes x K
    ca, cb = cond(pa), cond(pb)
    P = np.einsum("n,ni,nj->ij", _GH_W, ca, cb)
    return P / P.sum()


def mix_shift(tg: pd.DataFrame, min_tds: int = 200) -> pd.DataFrame:
    """Channel multipliers by the opponent's offensive-TD count (bucket 0..4+):
    the channel's share of a team's offensive TDs in that bucket over its
    share overall, SHRUNK toward 1 by a pseudo-count of `min_tds` touchdowns
    (a thin bucket moves less; none is silently set to 1). Estimated on the
    seasons given (the tune seasons). The bucket's TD count is in .attrs."""
    opp = tg[["game_id", "team", "off_tds"]].rename(columns={"team": "opp", "off_tds": "opp_tds"})
    t = tg.merge(opp, on=["game_id", "opp"])
    t["b"] = t["opp_tds"].clip(upper=OPP_BUCKETS - 1).astype(int)
    tot = t[CH].sum()
    base = tot / tot.sum()
    rows, n_tds = {}, {}
    for b in range(OPP_BUCKETS):
        g = t.loc[t["b"] == b, CH].sum()
        n = float(g.sum())
        n_tds[b] = int(n)
        raw = ((g / n) / base.where(base > 0)).fillna(1.0) if n > 0 else pd.Series(1.0, index=CH)
        w = n / (n + min_tds) if (n + min_tds) > 0 else 0.0
        rows[b] = w * raw + (1 - w)                       # shrunk toward no shift
    out = pd.DataFrame(rows).T[CH]
    out.attrs["n_tds"] = n_tds
    return out


def mixes_by_opp(mix: pd.Series, shift: pd.DataFrame | None) -> np.ndarray:
    """(buckets x channels) mix for each opponent-count bucket, normalised."""
    m = mix[CH].to_numpy(float)
    m = m / m.sum()
    if shift is None:
        return np.tile(m, (OPP_BUCKETS, 1))
    out = shift.to_numpy(float) * m
    return out / out.sum(axis=1, keepdims=True)


def q_by_opp(shares: pd.DataFrame, mixes: np.ndarray) -> np.ndarray:
    """(players x buckets) per-touchdown share under each bucket's mix."""
    return np.clip(shares[CH].to_numpy(float) @ mixes.T, 0.0, 0.999)


def joint_counts(mu_a: float, mu_b: float, trials: int = T.LAYER1["trials"], r: float = 0.0) -> np.ndarray:
    """P[k_a, k_b]: the two teams' offensive-TD counts, Binomial(trials) each,
    joined by the copula with loading r (0 = independent)."""
    pa = T.count_pmf([mu_a], n=trials)[0]
    pb = T.count_pmf([mu_b], n=trials)[0]
    return copula_joint(pa, pb, r)


def _q_at(qb: np.ndarray, k_opp: np.ndarray) -> np.ndarray:
    """Per-touchdown share at each opponent count (bucketed)."""
    return qb[..., np.minimum(k_opp, OPP_BUCKETS - 1)]


def _none_moment(qs: np.ndarray, K: np.ndarray, c: float | None) -> np.ndarray:
    """[k_own, k_opp]: E[(1 - s)^k_own] where s is a combined per-TD share.

    c None: s is fixed at qs, so (1 - qs)^k. With a DIRICHLET over the team's
    shares (concentration c), a team's split of its touchdowns varies game to
    game, and by the aggregation property any subset's combined share is
    Beta(c qs, c (1 - qs)); its moments are prod_{j<k} (b + j) / (a + b + j).
    Teammates' shares are then negatively correlated within a game, so three
    teammates all scoring is rarer than a fixed split says."""
    qs = np.clip(np.asarray(qs, float), 0.0, 0.999)
    if c is None:
        return (1.0 - qs)[None, :] ** K[:, None]
    a, b = c * qs, c * (1.0 - qs)
    j = np.arange(len(K) - 1)[:, None]
    out = np.ones((len(K), len(qs)))
    out[1:] = np.cumprod((b[None, :] + j) / (a[None, :] + b[None, :] + j), axis=0)
    return out


def p_any(q_opp: np.ndarray, P: np.ndarray, own_axis: int = 0, c: float | None = None) -> np.ndarray:
    """P(score) for each player of the team on `own_axis` of P.
    q_opp: (players x buckets); c: Dirichlet concentration (None = fixed shares)."""
    K = np.arange(P.shape[0])
    Pk = P if own_axis == 0 else P.T                       # [k_own, k_opp]
    q = _q_at(q_opp, K)                                   # players x k_opp
    none = np.stack([_none_moment(qi, K, c) for qi in q]) if len(q) else np.zeros((0, len(K), len(K)))
    return 1.0 - (none * Pk[None]).sum(axis=(1, 2))


def p_all_same_team(q_opp_set: np.ndarray, P: np.ndarray, own_axis: int = 0) -> float:
    """P(every player in the set scores); the set is on one team.
    Inclusion-exclusion over subsets -- fine for the 2-4 legs a parlay has."""
    K = np.arange(P.shape[0])
    Pk = P if own_axis == 0 else P.T
    q = _q_at(q_opp_set, K)                               # n x k_opp
    n = q.shape[0]
    total = np.zeros_like(Pk)
    for r in range(n + 1):
        for sub in combinations(range(n), r):
            qs = q[list(sub)].sum(axis=0) if sub else np.zeros(len(K))
            total += (-1) ** r * (np.clip(1.0 - qs, 0.0, 1.0)[None, :] ** K[:, None])
    return float((total * Pk).sum())


def p_pair_cross(qa_opp: np.ndarray, qb_opp: np.ndarray, P: np.ndarray) -> float:
    """P(A on team a and B on team b both score). P is [k_a, k_b]."""
    K = np.arange(P.shape[0])
    qa = _q_at(qa_opp, K)                                 # q of A at each k_b
    qb = _q_at(qb_opp, K)                                 # q of B at each k_a
    pa = 1.0 - (1.0 - qa)[None, :] ** K[:, None]          # [k_a, k_b]
    pb = 1.0 - (1.0 - qb)[:, None] ** K[None, :]          # [k_a, k_b]
    return float((pa * pb * P).sum())


# ------------------------------------------------------------ sets across both teams, and r by moment

def _incl_excl(q_set: np.ndarray, K: np.ndarray, c: float | None = None) -> np.ndarray:
    """[k_own, k_opp]: P(every player in the set scores | counts), by
    inclusion-exclusion; q_set is (n x k_opp). An empty set gives 1. c is the
    Dirichlet concentration of the team's shares (None = fixed)."""
    n = q_set.shape[0]
    total = np.zeros((len(K), len(K)))
    for r in range(n + 1):
        for sub in combinations(range(n), r):
            qs = q_set[list(sub)].sum(axis=0) if sub else np.zeros(len(K))
            total += (-1) ** r * _none_moment(np.clip(qs, 0.0, 1.0), K, c)
    return total


def p_all(qa_set: np.ndarray, qb_set: np.ndarray, P: np.ndarray, c: float | None = None) -> float:
    """P(every listed player scores): qa_set players on team a (axis 0 of P),
    qb_set on team b. Each set is (n x buckets); either may be empty (0 x
    buckets). Covers pairs, triples and any small parlay across both teams.
    c: Dirichlet concentration of each team's shares (None = fixed shares)."""
    K = np.arange(P.shape[0])
    ia = _incl_excl(_q_at(qa_set, K), K, c) if len(qa_set) else np.ones((len(K), len(K)))
    ib = _incl_excl(_q_at(qb_set, K), K, c) if len(qb_set) else np.ones((len(K), len(K)))
    return float((ia * ib.T * P).sum())


def implied_count_corr(r: float, mu_a: float, mu_b: float) -> float:
    """Correlation of the two teams' counts that loading r implies."""
    P = joint_counts(mu_a, mu_b, r=r)
    K = np.arange(P.shape[0])
    pa, pb = P.sum(1), P.sum(0)
    ma, mb = (K * pa).sum(), (K * pb).sum()
    cov = (K[:, None] * K[None, :] * P).sum() - ma * mb
    return float(cov / np.sqrt(((K - ma) ** 2 * pa).sum() * ((K - mb) ** 2 * pb).sum()))


def r_for_corr(target: float, mus: list[tuple[float, float]], lo: float = 0.0, hi: float = 0.95) -> float:
    """The loading whose implied count correlation, averaged over these games'
    means, equals `target` (bisection). Moment matching, not likelihood: the
    score-pair likelihood rewarded r = 0.5 while the residual correlation it
    should reproduce implies ~0.4."""
    if target <= 0:
        return 0.0
    f = lambda r: np.mean([implied_count_corr(r, a, b) for a, b in mus]) - target  # noqa: E731
    for _ in range(30):
        mid = (lo + hi) / 2
        lo, hi = (mid, hi) if f(mid) < 0 else (lo, mid)
    return round((lo + hi) / 2, 3)

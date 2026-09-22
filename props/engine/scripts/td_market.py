"""Touchdown model, LAYER 4: the market as a prior.

anytime_td_v1's largest single-leg errors are role news the market has and
usage data does not (Willis: v1 4.6% on his first board, book 26%). The fix is
to blend the model with the de-vigged market:

    logit p_blend = w * logit p_model + (1 - w) * logit p_market

DE-VIG. A two-sided market (Sleeper prices "won't score" too) is de-vigged
exactly: Yes / (Yes + No). A one-way market (most sportsbooks) carries its hold
inside the Yes price; a PROVISIONAL hold is removed. The Tuesday scorecard's
shadow fit (props/blend.py) estimates the real per-book hold as an intercept
and the real weight from settled calls.

PROVISIONAL WEIGHT. w = 0.5 until the settled record estimates it (blend.py
prints no weight below 300 calls). Every priced TD row logs p_model, p_market
and p_blend, so the weight can be fitted the moment the record is deep enough.

Stdlib + numpy only.
"""

from __future__ import annotations

import numpy as np

BLEND_W_MODEL = 0.5        # PROVISIONAL: weight on the model's logit
ONE_WAY_HOLD = 0.07        # PROVISIONAL: relative hold removed from a one-way Yes price
EPS = 1e-4


def _logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def market_prob(p_implied: float, two_sided: bool, hold: float = ONE_WAY_HOLD) -> float:
    """The de-vigged market probability. `p_implied` is already Yes/(Yes+No)
    for a two-sided market; for a one-way market it is the raw implied
    probability, and the provisional hold is removed."""
    return float(p_implied) if two_sided else float(p_implied) / (1.0 + hold)


def blend(p_model, p_market, w: float = BLEND_W_MODEL):
    """Logit-scale blend of the model and the market."""
    z = w * _logit(p_model) + (1 - w) * _logit(p_market)
    return 1.0 / (1.0 + np.exp(-z))


def american_from_prob(p: float) -> int:
    """Fair American odds for probability p."""
    p = min(max(float(p), 1e-6), 1 - 1e-6)
    return int(round(-100 * p / (1 - p))) if p >= 0.5 else int(round(100 * (1 - p) / p))


def decimal_from_american(a: float) -> float:
    a = float(a)
    return 1 + (a / 100 if a > 0 else 100 / -a)

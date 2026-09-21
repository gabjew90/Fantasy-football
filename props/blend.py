"""The market as a prior, in SHADOW: estimate how much weight the book's
number deserves beside anytime_td_v1's, from settled calls. Nothing here
changes a price.

The largest single-leg errors are role news the market has and usage data
does not (Willis: v1 4.6%, book 26%). The fix is a blend,

    logit p = a + b_model * logit(p_model) + b_market * logit(p_market)

but its weights can only be learned from logged lines graded against
outcomes. The record already carries p_model, p_novig and the result for
every call, so the estimate needs no engine change: this module fits it on
v1 anytime-TD calls within ONE engine version (the scorecard's pooling rule)
and reports it, with week-by-week out-of-sample log loss for the model, the
market and the blend. Below MIN_CALLS it says the record is too thin rather
than printing a weight.

One-way markets (most books quote no "won't score" side) carry their hold in
p_novig while Sleeper's two-sided prices are de-vigged, so each book gets its
own intercept. Stdlib + numpy + pandas only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_CALLS = 300
EPS = 1e-4


def _logit(p):
    p = np.clip(np.asarray(p, float), EPS, 1 - EPS)
    return np.log(p / (1 - p))


def fit(X: np.ndarray, y: np.ndarray, iters: int = 50, ridge: float = 1e-6) -> np.ndarray:
    """Logistic regression by Newton's method (intercept in X)."""
    w = np.zeros(X.shape[1])
    for _ in range(iters):
        p = 1 / (1 + np.exp(-(X @ w)))
        g = X.T @ (y - p) - ridge * w
        H = -(X.T * (p * (1 - p))) @ X - ridge * np.eye(len(w))
        step = np.linalg.solve(H, g)
        w = w - step
        if np.abs(step).max() < 1e-9:
            break
    return w


def _ll(p, y):
    p = np.clip(p, EPS, 1 - EPS)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def v1_td_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Settled anytime-TD calls priced by anytime_td_v1, with both numbers."""
    d = df[(df["market"] == "player_anytime_td")].copy()
    if "td_model" not in d.columns:
        return d.iloc[0:0]
    d = d[d["td_model"].astype(str) == "anytime_td_v1"]
    for c in ("p_model", "p_novig", "won"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna(subset=["p_model", "p_novig", "won"])


def blend_section(df: pd.DataFrame, reps: int = 1000, seed: int = 17) -> list[str]:
    d = v1_td_calls(df)
    out = ["### Market blend (shadow: nothing priced from it)", ""]
    if len(d) < MIN_CALLS:
        return out + [f"{len(d)} settled anytime_td_v1 calls in this engine version; the blend weight is not "
                      f"estimated below {MIN_CALLS}. The record is filling.", ""]
    y = d["won"].to_numpy(float)
    # ONE INTERCEPT PER BOOK: Sleeper's anytime prices are two-sided and de-vigged,
    # one-way books' p_novig still carries the hold; pooled, the market term would
    # measure the book mix rather than the market's information.
    books = d["book"].astype(str).to_numpy() if "book" in d else np.array(["all"] * len(d))
    ub = sorted(set(books))
    dummies = [(books == b).astype(float) for b in ub[1:]]
    X = np.column_stack([np.ones(len(d)), _logit(d["p_model"]), _logit(d["p_novig"]), *dummies])
    w = fit(X, y)
    # game-clustered bootstrap for the weights
    games = d["event_id"].astype(str).to_numpy() if "event_id" in d else np.arange(len(d)).astype(str)
    ug = np.unique(games)
    rng = np.random.default_rng(seed)
    idx_by = {g: np.flatnonzero(games == g) for g in ug}
    bs = []
    for _ in range(reps):
        take = np.concatenate([idx_by[g] for g in rng.choice(ug, size=len(ug))])
        bs.append(fit(X[take], y[take]))
    lo, hi = np.percentile(np.array(bs), [2.5, 97.5], axis=0)
    # out of sample: leave one week out
    pb = np.full(len(d), np.nan)
    weeks = d["week"].to_numpy()
    for wk in np.unique(weeks):
        tr, te = weeks != wk, weeks == wk
        if tr.sum() >= 50:
            pb[te] = 1 / (1 + np.exp(-(X[te] @ fit(X[tr], y[tr]))))
    ok = ~np.isnan(pb)
    return out + [f"{len(d)} settled anytime_td_v1 calls; books {', '.join(ub)} (each its own intercept; "
                  f"the intercept row below is {ub[0]}'s).", "",
                  "| term | weight | 95% CI (game-clustered) |", "|---|---|---|",
                  f"| intercept | {w[0]:+.3f} | ({lo[0]:+.3f}, {hi[0]:+.3f}) |",
                  f"| logit(model) | {w[1]:+.3f} | ({lo[1]:+.3f}, {hi[1]:+.3f}) |",
                  f"| logit(market) | {w[2]:+.3f} | ({lo[2]:+.3f}, {hi[2]:+.3f}) |", "",
                  "Leave-one-week-out log loss on the same calls: "
                  f"model {_ll(d['p_model'].to_numpy()[ok], y[ok]).mean():.4f}, "
                  f"market {_ll(d['p_novig'].to_numpy()[ok], y[ok]).mean():.4f}, "
                  f"blend {_ll(pb[ok], y[ok]).mean():.4f} ({int(ok.sum())} calls).", ""]

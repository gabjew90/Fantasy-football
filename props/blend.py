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
own intercept.

YARDAGE (plan step 5, 2026-09-25): the same fit on the yardage calls --
receptions, receiving, rushing and QB passing yards -- pooled, with an
intercept per book and per market. p_model and p_novig are the probabilities
of the side the call took, so the fit asks the same question: given the
book's number, does the model's add anything, and how much? Stdlib + numpy +
pandas only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

MIN_CALLS = 300
MIN_LEVEL_CALLS = 30      # a market (or book) with fewer calls, or one outcome only, shares the base intercept
EPS = 1e-4
YARDAGE_MARKETS = ("player_receptions", "player_reception_yds", "player_rush_yds", "player_pass_yds",
                   "player_rush_reception_yds")


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


def yardage_calls(df: pd.DataFrame) -> pd.DataFrame:
    """Settled yardage calls (not pushes), with both numbers."""
    d = df[df["market"].isin(YARDAGE_MARKETS)].copy()
    for c in ("p_model", "p_novig", "won"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna(subset=["p_model", "p_novig", "won"])


def blend_section(df: pd.DataFrame, reps: int = 1000, seed: int = 17) -> list[str]:
    out = ["### Market blend (shadow: nothing priced from it)", ""]
    for d, noun, levels in [
            (v1_td_calls(df), "anytime_td_v1 calls", ()),
            (yardage_calls(df), "yardage calls (receptions, receiving, rushing and QB passing yards)", ("market",))]:
        try:
            out += _weights(d, noun, levels, reps, seed)
        except (np.linalg.LinAlgError, FloatingPointError, ValueError) as ex:
            # a shadow fit must never cost the Tuesday scorecard
            out += [f"{len(d)} settled {noun}; the blend fit failed ({type(ex).__name__}: {ex}) and "
                    "prints no weight this week.", ""]
    return out


def _level_dummies(vals: np.ndarray, y: np.ndarray) -> list[np.ndarray]:
    """One intercept per level with enough calls and both outcomes; the rest
    share the base. A tiny level whose calls all won (or all lost) would
    otherwise be perfectly separated and send its coefficient to infinity."""
    keep = [v for v in sorted(set(vals))
            if (vals == v).sum() >= MIN_LEVEL_CALLS and 0 < y[vals == v].mean() < 1]
    return [(vals == v).astype(float) for v in keep[1:]]


def _design(d: pd.DataFrame, levels: tuple):
    """The blend's design matrix: intercept, logit(model), logit(market), then an
    intercept per book and per level in `levels`. Returns (X, y, books)."""
    y = d["won"].to_numpy(float)
    # ONE INTERCEPT PER BOOK: Sleeper's anytime prices are two-sided and de-vigged,
    # one-way books' p_novig still carries the hold; pooled, the market term would
    # measure the book mix rather than the market's information.
    books = d["book"].astype(str).to_numpy() if "book" in d else np.array(["all"] * len(d))
    ub = sorted(set(books))
    dummies = _level_dummies(books, y)
    for lv in levels:
        dummies += _level_dummies(d[lv].astype(str).to_numpy(), y)
    X = np.column_stack([np.ones(len(d)), _logit(d["p_model"]), _logit(d["p_novig"]), *dummies])
    return X, y, ub


def _boot(d: pd.DataFrame, X: np.ndarray, y: np.ndarray, reps: int, seed: int, level: float = 0.95):
    """Game-clustered bootstrap: the `level` interval of every weight (95% unless the
    gate asks for its multiple-look level)."""
    games = d["event_id"].astype(str).to_numpy() if "event_id" in d else np.arange(len(d)).astype(str)
    ug = np.unique(games)
    rng = np.random.default_rng(seed)
    idx_by = {g: np.flatnonzero(games == g) for g in ug}
    bs = []
    for _ in range(reps):
        take = np.concatenate([idx_by[g] for g in rng.choice(ug, size=len(ug))])
        bs.append(fit(X[take], y[take]))
    a = 100 * (1 - level) / 2
    return np.percentile(np.array(bs), [a, 100 - a], axis=0)


# THE GATE IS DECIDED AT FIXED REVIEWS ONLY (DECISIONS #151): after these
# weeks are graded, on the calls through that week. Between reviews it holds,
# so watching the running number week by week cannot open it on a lucky run.
REVIEW_WEEKS = (8, 12, 18)
# THREE LOOKS SHARE ONE 5% (outside reviewer, DECISIONS #180): each review's two
# intervals are at 1 - 0.05 / 3 = 98.3%, so three chances to open do not triple the
# chance of opening on luck. The running number stays at 95%: context, never a decision.
GATE_LEVEL = 1 - 0.05 / len(REVIEW_WEEKS)
# the bet-selection rule the profit condition grades: the board's internal top
# tier (the label a bet would carry), at the price Sleeper showed when logged
SELECTION_TIERS = ("STRONG",)
SELECTION_BOOK = "sleeper"
MIN_BETS = 100
MIN_GAMES = 10      # an interval from resampling fewer games is not trusted


def _weight(d: pd.DataFrame, reps: int, seed: int, level: float = 0.95) -> dict:
    """The model's weight beside the book, with its game-clustered interval."""
    if len(d) < MIN_CALLS:
        return {"estimated": False}
    try:
        X, y, _ub = _design(d, ("market",))
        w = fit(X, y)
        lo, hi = _boot(d, X, y, reps, seed, level)
    except (np.linalg.LinAlgError, FloatingPointError, ValueError):
        return {"estimated": False}
    return {"estimated": True, "w_model": round(float(w[1]), 3), "lo": round(float(lo[1]), 3),
            "hi": round(float(hi[1]), 3), "level": level}


def selection_profit(df: pd.DataFrame, reps: int = 2000, seed: int = 23, level: float = 0.95) -> dict:
    """What the selection rule actually made: net per $100 on settled top-tier
    yardage calls at Sleeper's recorded prices, with a 95% interval from
    resampling whole games. A positive weight beside the book is not a
    betting edge after the hold; this is."""
    d = df[df["market"].isin(YARDAGE_MARKETS)] if "market" in df.columns else df.iloc[0:0]
    if "tier" in d.columns:
        d = d[d["tier"].astype(str).str.startswith(SELECTION_TIERS)]
    else:
        d = d.iloc[0:0]
    if "book" in d.columns:
        d = d[d["book"].astype(str) == SELECTION_BOOK]
    pnl = pd.to_numeric(d["pnl_per_100"], errors="coerce") if "pnl_per_100" in d.columns else pd.Series(dtype=float)
    d = d.assign(_pnl=pnl).dropna(subset=["_pnl"])
    out = {"n_bets": int(len(d)), "estimated": False}
    if len(d) < MIN_BETS:
        return out
    games = d["event_id"].astype(str).to_numpy() if "event_id" in d.columns else np.arange(len(d)).astype(str)
    g = pd.DataFrame({"g": games, "p": d["_pnl"].to_numpy()}).groupby("g")["p"]
    sums, cnt = g.sum().to_numpy(), g.size().to_numpy()
    if len(sums) < MIN_GAMES:
        return {**out, "n_games": int(len(sums))}
    idx = np.random.default_rng(seed).integers(0, len(sums), size=(reps, len(sums)))
    a = 100 * (1 - level) / 2
    lo, hi = np.percentile(sums[idx].sum(1) / cnt[idx].sum(1), [a, 100 - a])
    return {**out, "estimated": True, "net_per_100": round(float(d["_pnl"].mean()), 2),
            "lo": round(float(lo), 2), "hi": round(float(hi), 2), "n_games": int(len(sums)), "level": level}


def yardage_gate(df: pd.DataFrame, reps: int = 1000, seed: int = 17) -> dict:
    """THE LABEL GATE (DECISIONS #144, #151). The research board shows no bet
    labels. At each review (after weeks 8, 12 and 18 are graded), on the calls
    through that week, the gate opens only when BOTH hold:
    1. the model's number earns weight beside the book's price on settled
       yardage calls (the whole 98.3% interval above zero -- GATE_LEVEL), and
    2. the selection rule made money at Sleeper's recorded prices (the whole
       98.3% interval of net per $100 above zero).
    Between reviews the decision holds. The running weight on every graded
    call is reported as context and never opens the gate."""
    if df is None or df.empty or "market" not in df.columns:
        return {"n_calls": 0, "weeks": [], "estimated": False, "gate_open": False,
                "review_week": None, "next_review": REVIEW_WEEKS[0]}
    d = yardage_calls(df)
    wk = pd.to_numeric(d["week"], errors="coerce")
    weeks = sorted(int(w) for w in wk.dropna().unique()) if len(d) else []
    # a review counts for a pricing model only when it has calls through that
    # week: a model first used in week 10 is first reviewed after week 12
    reached = [r for r in REVIEW_WEEKS if weeks and min(weeks) <= r <= max(weeks)]
    review = reached[-1] if reached else None
    running = _weight(d, reps, seed)
    out = {"n_calls": int(len(d)), "weeks": weeks, "review_week": review,
           "next_review": next((r for r in REVIEW_WEEKS if not weeks or r > max(weeks)), None),
           **running, "gate_open": False}
    if review is None:
        return out
    dr = d[wk <= review]
    # the decision's intervals are at the multiple-look level, never the running 95%
    w = _weight(dr, reps, seed, GATE_LEVEL)
    pr = selection_profit(df[pd.to_numeric(df["week"], errors="coerce") <= review], level=GATE_LEVEL)
    weight_ok = bool(w.get("estimated") and w["lo"] > 0)
    profit_ok = bool(pr.get("estimated") and pr["lo"] > 0)
    out["at_review"] = {"week": review, "n_calls": int(len(dr)), "weight": w, "weight_ok": weight_ok,
                        "profit": pr, "profit_ok": profit_ok}
    out["gate_open"] = weight_ok and profit_ok
    return out


def _weights(d: pd.DataFrame, noun: str, levels: tuple, reps: int, seed: int) -> list[str]:
    """The fit, its game-clustered interval and leave-one-week-out log loss for
    one family of calls; one intercept per book and per level in `levels`."""
    if len(d) < MIN_CALLS:
        return [f"{len(d)} settled {noun} in this pricing model; the blend weight is not "
                f"estimated below {MIN_CALLS}. The record is filling.", ""]
    X, y, ub = _design(d, levels)
    w = fit(X, y)
    lo, hi = _boot(d, X, y, reps, seed)
    # out of sample: leave one week out
    pb = np.full(len(d), np.nan)
    weeks = d["week"].to_numpy()
    for wk in np.unique(weeks):
        tr, te = weeks != wk, weeks == wk
        if tr.sum() >= 50:
            pb[te] = 1 / (1 + np.exp(-(X[te] @ fit(X[tr], y[tr]))))
    ok = ~np.isnan(pb)
    per = "".join(f" and per {lv}" for lv in levels)
    # out of sample needs a second week to hold out; one week says so, not "nan"
    oos = ("Leave-one-week-out log loss on the same calls: "
           f"model {_ll(d['p_model'].to_numpy()[ok], y[ok]).mean():.4f}, "
           f"market {_ll(d['p_novig'].to_numpy()[ok], y[ok]).mean():.4f}, "
           f"blend {_ll(pb[ok], y[ok]).mean():.4f} ({int(ok.sum())} calls)." if ok.any() else
           f"No out-of-sample check yet: it holds out one week at a time and needs at least two "
           f"({len(np.unique(weeks))} settled so far).")
    return [f"{len(d)} settled {noun}; books {', '.join(ub)} (an intercept per book{per}; "
            f"the intercept row below is {ub[0]}'s).", "",
            "| term | weight | 95% CI (game-clustered) |", "|---|---|---|",
            f"| intercept | {w[0]:+.3f} | ({lo[0]:+.3f}, {hi[0]:+.3f}) |",
            f"| logit(model) | {w[1]:+.3f} | ({lo[1]:+.3f}, {hi[1]:+.3f}) |",
            f"| logit(market) | {w[2]:+.3f} | ({lo[2]:+.3f}, {hi[2]:+.3f}) |", "",
            oos, ""]

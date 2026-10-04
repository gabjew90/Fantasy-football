"""Research columns for the props board (props-v1.29, DECISIONS #142).

Nothing here changes a price. These functions answer the questions a person
handicapping a prop asks, using the same simulation the prices come from:

- implied workload: the targets (or carries) a posted line needs to be a fair
  50/50, next to what the model projects;
- the break-even workload at the posted prices: the workload above which the
  Over beats its price, and below which the Under beats its price -- how far
  a view of his role can be wrong before the bet stops paying;
- usage: last game's snap / target / carry share against his earlier weeks;
- the receiving role-shift flag, worded from its 2022-25 check
  (reports/role_shift_check.md).

Every simulation here runs on its OWN generator, re-created for each
evaluation (common random numbers), so the shared pricing stream in
score_game.py is never touched and the search is smooth in the multiplier.
"""
from __future__ import annotations

import re

import numpy as np

import model as MODEL

N_SEARCH = 8000
SEED = 20261003
K_LO, K_HI = 0.05, 4.0

# reports/role_shift_check.md: fixed before the check, earned for receiving only
SNAP_JUMP = 0.15
SHARE_LAG = 0.03


def _bisect(p_over_at, target=0.5, lo=K_LO, hi=K_HI, iters=14):
    """The multiplier k where p_over_at(k) = target, P(over) rising in k.
    None when the line sits outside [lo, hi]."""
    if p_over_at(lo) > target or p_over_at(hi) < target:
        return None
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if p_over_at(mid) < target:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def breakeven(price) -> float | None:
    """The win rate an American price needs (its own vig included), or None.
    The same rule as props/journal.py breakeven(); the engine ships without
    props/, so the two are kept in step by hand."""
    try:
        a = float(price)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(a) or abs(a) < 100:
        return None
    return abs(a) / (abs(a) + 100) if a < 0 else 100 / (a + 100)


def _share_over(sim_of_k, line):
    """The Over's share of the bets that do not push: wins / (wins + losses).
    On a half line it is P(stat > line); on a whole line a push refunds, so
    this is what a price is judged against."""
    def f(k):
        x = sim_of_k(k)
        gt, lt = float((x > line).mean()), float((x < line).mean())
        return gt / (gt + lt) if gt + lt > 0 else 0.5
    return f


def _break_even_ks(share_over, prices):
    """The multipliers where each side breaks even at its price. Over:
    share_over(k) = be_over. Under: share_over(k) = 1 - be_under. Returns
    (k_over, k_under); None where the workload is outside the search range or
    the side has no price (break_even_cell tells the two apart by be_over /
    be_under)."""
    be_o, be_u = (breakeven(prices[0]), breakeven(prices[1])) if prices else (None, None)
    return (None if be_o is None else _bisect(share_over, be_o),
            None if be_u is None else _bisect(share_over, 1 - be_u))


def search_edges(share_over, prices):
    """Where a failed break-even search ran out: for each side, 'max' when even
    the most work the simulation can give him is not enough (Over) or still
    pays (Under), 'min' at the other end; None when the search found a number
    or the side has no price."""
    be_o, be_u = (breakeven(prices[0]), breakeven(prices[1])) if prices else (None, None)
    hi = share_over(K_HI)

    def edge(target):
        return None if target is None else ("max" if hi < target else "min")
    return edge(be_o), edge(None if be_u is None else 1 - be_u)


def break_even_cell(x) -> str:
    """The research table's 'Pays at this price if he gets' cell: the Over beats
    its own price above over_needs, the Under at or below under_needs. A side
    with no posted price (no be_over / be_under) says so rather than reading as
    a search that ran out of range."""
    unit = x.get("unit") if isinstance(x.get("unit"), str) else ""
    blank = lambda v: v is None or bool(np.isnan(float(v)))
    o, u, bo, bu = (x.get(k) for k in ("over_needs", "under_needs", "be_over", "be_under"))
    if not unit or (blank(bo) and blank(bu)):
        return "—"

    edge = {k: x.get(k) for k in ("over_edge", "under_edge", "over_limit", "under_limit")}

    def side(v, be, word, fmt, key):
        if blank(be):
            return f"{word}: no price posted"
        if not blank(v):
            return fmt.format(v=float(v))
        e, lim = edge.get(f"{key}_edge"), edge.get(f"{key}_limit")
        if isinstance(e, str) and not blank(lim):
            # the search ran out: say where, in his units
            if key == "over":
                return (f"Over: needs more than {float(lim):.1f} {unit} (about all the work the simulation "
                        "gives him: the line rests on his efficiency or the team's volume)" if e == "max"
                        else f"Over: pays even at {float(lim):.1f} {unit}")
            return (f"Under: pays even at {float(lim):.1f} {unit}" if e == "max"
                    else f"Under: needs fewer than {float(lim):.1f} {unit}")
        return f"{word}: beyond the search range"
    return (f"{side(o, bo, 'Over', 'Over above {v:.1f} ' + unit, 'over')}; "
            f"{side(u, bu, 'Under', 'Under at {v:.1f} or fewer', 'under')}")


LAST_EDGES = {}     # the latest search's edges, read by edges_for(); set by _edge_cache


def _edge_cache(share_over, prices, k_o, k_u, work):
    """Record, for a side whose search failed, which end it ran out at and the
    workload there, so the cell can say 'needs more than 19 carries' rather
    than 'beyond the search range'."""
    eo, eu = search_edges(share_over, prices)
    lim = lambda e: None if e is None else work(K_HI if e == "max" else K_LO)
    LAST_EDGES.clear()
    LAST_EDGES.update(over_edge=eo if k_o is None else None, under_edge=eu if k_u is None else None)
    LAST_EDGES.update(over_limit=lim(LAST_EDGES["over_edge"]), under_limit=lim(LAST_EDGES["under_edge"]))


def edges_for() -> dict:
    """The edges of the last implied_* call made with prices (see _edge_cache)."""
    return dict(LAST_EDGES)


def implied_targets(line, stat, team_targets_mean, targets_r, share, catch_rate, ypt,
                    per_catch_shape, width=None, prices=None):
    """Targets per game at which the line is a coin flip for a receiver (P(stat >
    line) = 0.5 on a half line; Overs and Unders equally likely on a whole line), holding
    his catch rate and yards per target. stat: 'receptions' or 'rec_yards'.
    Returns (implied targets, projected targets) or (None, projected). With
    prices=(over, under) it also returns the targets at which the Over and the
    Under break even at those prices: (implied, projected, over_needs,
    under_needs) -- the Over pays above over_needs, the Under below under_needs."""
    proj = team_targets_mean * share
    if share <= 0 or line is None:
        return (None, proj) if prices is None else (None, proj, None, None)
    col = 0 if stat == "receptions" else 1
    cache = {}

    def sim(k):      # common random numbers: one generator per k, cached
        if k not in cache:
            s = min(share * k, 0.95)
            out, _ = MODEL.simulate_team_game(np.random.default_rng(SEED), N_SEARCH, team_targets_mean,
                                              targets_r, {"p": s}, {"p": catch_rate}, {"p": ypt},
                                              per_catch_shape, other_bucket=True, width=width)
            cache[k] = out["p"][col]
        return cache[k]

    work = lambda k: None if k is None else team_targets_mean * min(share * k, 0.95)
    share_over = _share_over(sim, line)
    k = _bisect(share_over)
    if prices is None:
        return work(k), proj
    k_o, k_u = _break_even_ks(share_over, prices)
    _edge_cache(share_over, prices, k_o, k_u, work)
    return work(k), proj, work(k_o), work(k_u)


def implied_carries(line, j, team_carries_mean, carries_r, rush_shares, ypc, resid,
                    width=None, player_resid=None, player_kneel=None, qb_index=None, prices=None):
    """Carries per game at which the line is a coin flip for player j (as above),
    scaling only his share inside the FULL team call (the share rescale
    depends on every teammate). Returns (implied mean carries, projected mean
    carries), the effective carries the simulation gives him. With
    prices=(over, under) it also returns the carries at which each side breaks
    even at its price, as implied_targets does."""
    shares = [float(v) for v in rush_shares]
    cache = {}

    def run(k):
        if k not in cache:
            s = list(shares)
            s[j] = min(s[j] * k, 0.95)
            car, yds, _ = MODEL.simulate_team_rush(np.random.default_rng(SEED), N_SEARCH, team_carries_mean,
                                                   carries_r, s, ypc, resid, width=width,
                                                   player_resid=player_resid, player_kneel=player_kneel,
                                                   qb_index=qb_index)
            cache[k] = (car[j], yds[j])
        return cache[k]

    proj = float(run(1.0)[0].mean())
    if shares[j] <= 0 or line is None:
        return (None, proj) if prices is None else (None, proj, None, None)
    work = lambda k: None if k is None else float(run(k)[0].mean())
    share_over = _share_over(lambda k: run(k)[1], line)
    k = _bisect(share_over)
    if prices is None:
        return work(k), proj
    k_o, k_u = _break_even_ks(share_over, prices)
    _edge_cache(share_over, prices, k_o, k_u, work)
    return work(k), proj, work(k_o), work(k_u)


# an Out teammate is named on the board only when he had a real role (DECISIONS #155)
OUT_TARGET_SHARE, OUT_CARRY_SHARE, OUT_PASS_SHARE = 0.10, 0.15, 0.50


def role_share(plays, pid, team, weeks=None):
    """His share of the team's plays in the weeks he was available this season:
    `weeks` (the weeks he was on the active roster) plus any week he had a play,
    so the games he played without a target still count. plays: DataFrame
    with posteam, week, pid. None when he has no play at all."""
    d = plays[plays.posteam == team]
    mine = set(d.loc[d.pid == pid, "week"])
    if not mine:
        return None
    weeks = mine | set(weeks or ())
    dd = d[d.week.isin(weeks)]
    return float((dd.pid == pid).mean()) if len(dd) else None


def out_matters(pid, team, targets, carries, dropbacks, prior_ts=None, prior_rs=None, weeks=None) -> bool:
    """True when an Out player's absence is worth a flag: this season he threw
    half the team's passes, drew 10%+ of its targets or took 15%+ of its
    carries in the weeks he played; with no play this season, last season's
    shares decide (never a slot default -- an unknown depth player is not
    news). A depth receiver with two targets in two games is not flagged."""
    shares = [(role_share(dropbacks, pid, team, weeks), OUT_PASS_SHARE),
              (role_share(targets, pid, team, weeks), OUT_TARGET_SHARE),
              (role_share(carries, pid, team, weeks), OUT_CARRY_SHARE)]
    if any(s is not None for s, _ in shares):
        return any(s is not None and s >= cut for s, cut in shares)
    return bool((prior_ts or 0) >= OUT_TARGET_SHARE or (prior_rs or 0) >= OUT_CARRY_SHARE)


# WORTH A LOOK (DECISIONS #156), fixed before any result: a story about his
# role this week, AND last game's actual workload already beyond the side's
# break-even workload by a clear margin, in the story's direction. Not a bet
# label: it marks where the user's own read has the most to work with, and the
# scorecard grades every mark at Sleeper's prices.
LOOK_MARGIN = {"targets": 2.0, "carries": 3.0}


def worth_a_look(x, last_week):
    """(side, why) or None for one research row (a dict). x needs flags,
    player, market, unit, over_needs, under_needs, tn / cn and usage_week."""
    unit = x.get("unit")
    if unit not in LOOK_MARGIN:
        return None
    if x.get("usage_week") is None or int(x["usage_week"]) != int(last_week):
        return None          # last game must be the game just played
    n = x.get("cn") if x.get("market") == "player_rush_yds" else x.get("tn")
    if n is None or n != n:
        return None
    flags = [f.strip() for f in str(x.get("flags") or "").split(";") if f.strip()]
    me = str(x.get("player", ""))
    outs = [re.match(r"^(.+?) out(,|$)", f) for f in flags]
    up = any(f == "role up" for f in flags) or any(m_ and m_.group(1) != me for m_ in outs)
    down = any(f == "role down" for f in flags) or any(" back (missed last week)" in f for f in flags)
    # a role or teammate story sets the direction; stories pulling both ways
    # (more snaps, but the star teammate is back) mark nothing; a new team
    # with no other story allows either side
    if up and down:
        return None
    if not (up or down) and any(f.startswith("new team") for f in flags):
        up = down = True
    if not (up or down):
        return None
    m = LOOK_MARGIN[unit]
    o, u = x.get("over_needs"), x.get("under_needs")
    pv = x.get("preview")
    tail = f"; {pv}" if isinstance(pv, str) and pv else ""
    if up and o is not None and o == o and n >= o + m:
        return "Over", f"last game {n:.0f} {unit}; the Over pays above {o:.1f}{tail}"
    if down and u is not None and u == u and n <= u - m:
        return "Under", f"last game {n:.0f} {unit}; the Under pays at {u:.1f} or fewer{tail}"
    return None


def usage_change(weeks):
    """weeks: list of (week, snap_share, target_share, carry_share[, targets,
    carries]), sorted, the player's weeks before this one with this team. LAST
    = the latest week, BASE = the mean of the earlier ones (at least two). With
    the counts, tn / cn are last game's targets and carries and tn_base /
    cn_base the earlier weeks' per-game average. None when too few weeks."""
    if len(weeks) < 3:
        return None
    last = weeks[-1]
    base = weeks[:-1]
    mean = lambda i: float(np.nanmean([w[i] for w in base]))
    out = {"week": int(last[0]),
           "snap": last[1], "snap_base": mean(1),
           "ts": last[2], "ts_base": mean(2),
           "cs": last[3], "cs_base": mean(3)}
    if all(len(w) >= 6 for w in weeks):
        out.update(tn=float(last[4]), tn_base=mean(4), cn=float(last[5]), cn_base=mean(5))
    return out


def role_flag(u, last_week_expected):
    """The role-shift flag (reports/role_shift_check.md), or None. It needs last
    week to be the week before this one. Since round 23 (model.SNAP_REACT) the
    projection already moves his target share for this; the flag points the
    research at the role change, it no longer claims the model misses it."""
    if u is None or u["week"] != last_week_expected:
        return None
    if not (u["snap_base"] >= 0.05):
        return None     # the snap rule does not act below 5% of earlier snaps; neither does the flag
    d_snap = u["snap"] - u["snap_base"]
    d_ts = u["ts"] - u["ts_base"]
    if d_snap >= SNAP_JUMP and d_ts < SHARE_LAG:
        return ("role up", "snaps jumped while his targets lagged; the projection already raises his "
                           "target share for it (snap-change rule)")
    if d_snap <= -SNAP_JUMP and d_ts > -SHARE_LAG:
        return ("role down", "snaps fell while his targets held; the projection already lowers his "
                             "target share for it (snap-change rule)")
    return None


def backfield_jobs(weeks):
    """A back's three jobs, last game against his earlier weeks. weeks: sorted
    list of (week, early-down carry share, passing-down target share, inside-5
    carry share, inside-5 carries, team inside-5 carries) for the weeks he
    played this season with this team. Passing downs are 3rd/4th down or the
    last two minutes of a half. None with fewer than three weeks (the same
    LAST/BASE as usage_change)."""
    if len(weeks) < 3:
        return None
    last, base = weeks[-1], weeks[:-1]
    mean = lambda i: float(np.nanmean([w[i] for w in base])) if any(np.isfinite(w[i]) for w in base) else np.nan
    return {"week": int(last[0]),
            "early": last[1], "early_base": mean(1),
            "passdown": last[2], "passdown_base": mean(2),
            "i5": last[3], "i5_base": mean(3),
            "i5_n": int(last[4]), "i5_team": int(last[5])}

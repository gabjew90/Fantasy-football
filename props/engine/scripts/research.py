"""Research columns for the props board (props-v1.29, DECISIONS #142).

Nothing here changes a price. These functions answer the questions a person
handicapping a prop asks, using the same simulation the prices come from:

- implied workload: the targets (or carries) a posted line needs to be a fair
  50/50, next to what the model projects;
- usage: last game's snap / target / carry share against his earlier weeks;
- the receiving role-shift flag, worded from its 2022-25 check
  (reports/role_shift_check.md).

Every simulation here runs on its OWN generator, re-created for each
evaluation (common random numbers), so the shared pricing stream in
score_game.py is never touched and the search is smooth in the multiplier.
"""
from __future__ import annotations

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


def implied_targets(line, stat, team_targets_mean, targets_r, share, catch_rate, ypt,
                    per_catch_shape, width=None):
    """Targets per game at which P(stat > line) = 0.5 for a receiver, holding
    his catch rate and yards per target. stat: 'receptions' or 'rec_yards'.
    Returns (implied targets, projected targets) or (None, projected)."""
    proj = team_targets_mean * share
    if share <= 0 or line is None:
        return None, proj
    col = 0 if stat == "receptions" else 1

    def p_over(k):
        s = min(share * k, 0.95)
        out, _ = MODEL.simulate_team_game(np.random.default_rng(SEED), N_SEARCH, team_targets_mean,
                                          targets_r, {"p": s}, {"p": catch_rate}, {"p": ypt},
                                          per_catch_shape, other_bucket=True, width=width)
        return float((out["p"][col] > line).mean())

    k = _bisect(p_over)
    return (None if k is None else team_targets_mean * min(share * k, 0.95)), proj


def implied_carries(line, j, team_carries_mean, carries_r, rush_shares, ypc, resid,
                    width=None, player_resid=None, player_kneel=None, qb_index=None):
    """Carries per game at which P(rush yards > line) = 0.5 for player j,
    scaling only his share inside the FULL team call (the share rescale
    depends on every teammate). Returns (implied mean carries, projected mean
    carries), the effective carries the simulation gives him."""
    shares = [float(v) for v in rush_shares]

    def run(k):
        s = list(shares)
        s[j] = min(s[j] * k, 0.95)
        car, yds, _ = MODEL.simulate_team_rush(np.random.default_rng(SEED), N_SEARCH, team_carries_mean,
                                               carries_r, s, ypc, resid, width=width,
                                               player_resid=player_resid, player_kneel=player_kneel,
                                               qb_index=qb_index)
        return car[j], yds[j]

    proj = float(run(1.0)[0].mean())
    if shares[j] <= 0 or line is None:
        return None, proj
    k = _bisect(lambda k: float((run(k)[1] > line).mean()))
    return (None if k is None else float(run(k)[0].mean())), proj


def usage_change(weeks):
    """weeks: list of (week, snap_share, target_share, carry_share), sorted, the
    player's weeks before this one with this team. LAST = the latest week, BASE
    = the mean of the earlier ones (at least two). None when too few weeks."""
    if len(weeks) < 3:
        return None
    last = weeks[-1]
    base = weeks[:-1]
    mean = lambda i: float(np.nanmean([w[i] for w in base]))
    return {"week": int(last[0]),
            "snap": last[1], "snap_base": mean(1),
            "ts": last[2], "ts_base": mean(2),
            "cs": last[3], "cs_base": mean(3)}


def role_flag(u, last_week_expected):
    """The receiving role-shift flag (reports/role_shift_check.md), or None.
    The flag needs last week to be the week before this one."""
    if u is None or u["week"] != last_week_expected:
        return None
    d_snap = u["snap"] - u["snap_base"]
    d_ts = u["ts"] - u["ts_base"]
    if d_snap >= SNAP_JUMP and d_ts < SHARE_LAG:
        return ("role up", "snaps jumped while targets lagged; in 2022-25 this pattern caught "
                           "0.3-0.5 more passes than the model projected the next week")
    if d_snap <= -SNAP_JUMP and d_ts > -SHARE_LAG:
        return ("role down", "snaps fell while targets held; in 2022-25 this pattern caught "
                             "about 0.55 fewer passes than the model projected the next week")
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

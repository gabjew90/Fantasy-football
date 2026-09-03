"""Monte Carlo urgency engine (final spec §5).

urgency(pos) = VORP(best available now) - E[VORP(best available at my next turn)]

The expectation simulates every intervening rival pick: candidates weighted by
an ADP Gaussian (sigma grows with round), zeroed/damped by the rival's filled
starter slots, and tilted by their historical tendencies. Sampling is without
replacement within each simulation.

Known limitation (accepted in spec): one-step lookahead — optimizes the current
vs next turn only; turn N+2 sequencing is a next-season upgrade.
"""

from __future__ import annotations

import numpy as np

from . import snake

POSITIONS = ["QB", "RB", "WR", "TE", "K", "DEF"]
NEED_DAMP = 0.15          # multiplier for positions that fill no starter slot
QB_FILLED_DAMP = 0.05     # rival with QB filled, before late rounds
KDEF_EARLY_DAMP = 0.02    # K/DEF long before the rival's typical round


def _tendency_mult(seed: dict | None, rnd: int, pos: str) -> float:
    """How much this rival historically likes pos in this round bucket vs 1/6."""
    if not seed:
        return 1.0
    from .rivals import _bucket  # single source of bucket boundaries

    share = (seed.get("bucket_share", {}).get(_bucket(rnd), {}) or {}).get(pos)
    if share is None:
        return 1.0
    return float(np.clip(share / (1.0 / 6.0), 0.5, 2.0))


def calibrate(p: float, shrink: float) -> float:
    """Empirical calibration map (v2 item 1.1), fitted to the Omnibeta CLV
    retro: raw 96% -> 75%, 82% -> 68%, 45% -> 50% (n=67). A single shrink
    toward 0.5 fits all three buckets: calibrated = 0.5 + (p - 0.5) * shrink.
    (Plan B1 note: that n=67 was scored against the wrong horizon; the map
    is retained provisionally until the B7 refit.) shrink == 1.0 returns p
    exactly, so raw and calibrated are identical, not identical-to-1e-17."""
    if shrink == 1.0:
        return float(p)
    return 0.5 + (p - 0.5) * shrink


def _groups(pool, pos_arr, markets):
    """The pools urgency is measured over.

    Always one group per position (the historical report, on `vorp`), plus any
    caller-supplied MARKET — a set of positions shopped together, priced on a
    shared value column. See Tracker._open_markets for why that matters: once
    a dedicated slot is filled you are no longer shopping that position's
    market, and its remaining players compete inside the FLEX market instead.
    """
    n = len(pool)

    def col(keyname: str):
        out = np.empty(n, dtype=float)
        for i, p in enumerate(pool):
            v = p.get(keyname)
            if v is None:
                v = p.get("vorp")
            out[i] = float(v) if v is not None else -99.0
        return out

    vals = {"vorp": col("vorp"), "vorp_flex": col("vorp_flex")}
    groups = {pos: (pos_arr == pos, vals["vorp"]) for pos in POSITIONS}
    for name, spec in (markets or {}).items():
        mask = (np.isin(pos_arr, list(spec["members"])) if n
                else np.zeros(0, dtype=bool))
        groups[name] = (mask, vals[spec.get("value", "vorp")])
    return groups


def simulate_survival(pool, current_pick, next_pick, rivals, seeds, rng,
                      sims=1000, sigma=6.0, teams=12,
                      reach_prob=0.0, reach_scale=3.0,
                      run_window=5, run_min=2, run_boost=1.5,
                      survival_shrink=1.0, recent_pos=None, markets=None,
                      need_damp=NEED_DAMP, qb_filled_damp=QB_FILLED_DAMP,
                      kdef_early_damp=KDEF_EARLY_DAMP, qb_damp_until_round=10,
                      kdef_typical_round=13, run_ratio=1.5,
                      autopick_sigma_scale=0.5, rival_needs_update=True):
    """Per-market urgency + per-player survival to my next pick.

    pool: undrafted players (dicts with sleeper_id/pos/vorp/adp), pre-truncated.
    rivals: intervening pickers IN PICK ORDER — {"slot", "needs", "user_id"};
            length must equal next_pick - current_pick (my own slot excluded
            only when current_pick is my pick, which callers never pass).
    seeds: rival_seeds.json "users" mapping (may be empty).
    sigma: ADP noise in picks for the current round (caller scales by round).
    markets: optional {name: {"members": (pos,...), "value": "vorp"|"vorp_flex"}}
            extra pooled markets to report alongside the per-position ones.

    Rival-behaviour knobs (plan 2026-09-02 B3: hoisted from module constants
    so they are logged with every prediction and fittable in B7):
      need_damp            weight on a position that fills none of the rival's
                           open starter slots (was the constant 0.15)
      qb_filled_damp       a rival whose QB slot is filled, before
                           qb_damp_until_round (was 0.05 / round 10)
      kdef_early_damp      K/DEF before the rival's typical round minus one;
                           kdef_typical_round is the fallback when no seed
                           says otherwise (was 0.02 / 13)
      run_ratio, autopick_sigma_scale, rival_needs_update are accepted here
      and take effect in plan steps B4, B5 and B6 respectively.

    The returned dict is keyed by position AND by market name; survival is
    always per player and independent of grouping.
    """
    n = len(pool)
    picks_between = max(0, next_pick - current_pick)
    pos_arr = np.array([p["pos"] for p in pool]) if n else np.array([], dtype=str)
    adp = np.array([float(p["adp"]) if p.get("adp") is not None else 200.0 for p in pool])
    groups = _groups(pool, pos_arr, markets)
    members = {name: set(spec["members"]) for name, spec in (markets or {}).items()}

    best_now = {
        name: float(val[mask].max()) if n and mask.any() else 0.0
        for name, (mask, val) in groups.items()
    }

    def survival_of(name, const=None, arr=None):
        keep = members.get(name, {name})
        return {p["sleeper_id"]: (const if const is not None else float(arr[j]))
                for j, p in enumerate(pool) if p["pos"] in keep}

    # No intervening rivals -> survival is EXACTLY 1.0, deliberately raw:
    # calibration corrects the sim's model of rival behavior, and there is no
    # rival behavior to model here (code review 2026-08-30).
    if picks_between == 0 or not rivals or n == 0:
        return {
            name: {"best_now": best_now[name], "e_best_next": best_now[name],
                   "urgency": 0.0, "survival": survival_of(name, const=1.0),
                   "survival_raw": survival_of(name, const=1.0)}
            for name in groups
        }

    # static per-rival positional multiplier (needs + tendencies), per pick index
    rival_mult = np.ones((len(rivals), n))
    for i, rv in enumerate(rivals):
        pick_no = current_pick + i
        rnd = (pick_no - 1) // teams + 1
        seed = (seeds or {}).get(str(rv.get("user_id"))) if rv.get("user_id") else None
        for pos in POSITIONS:
            mask = pos_arr == pos
            if not mask.any():
                continue
            fills = snake.needs_position(rv["needs"], pos)
            m = 1.0 if fills else need_damp
            if pos == "QB" and rv["needs"].get("QB", 0) == 0 and rnd < qb_damp_until_round:
                m = qb_filled_damp
            if pos in ("K", "DEF"):
                typical = (seed or {}).get("first_round", {}).get(pos, kdef_typical_round)
                if rnd < typical - 1:
                    m = kdef_early_damp
            m *= _tendency_mult(seed, rnd, pos)
            rival_mult[i, mask] = m

    # ADP likelihood per intervening pick (same sigma across the window is fine
    # at this window size; sigma itself scales with round at the call site)
    pick_nos = np.arange(current_pick, next_pick)
    adp_like = np.exp(-0.5 * ((pick_nos[:, None] - adp[None, :]) / sigma) ** 2) + 1e-9
    # fat-tail REACH mixture (v2 1.1, CLV retro: reaches are one-directional —
    # players taken EARLY, never "reached for" after their ADP). With
    # reach_prob a rival draws from a widened, forward-only likelihood.
    ahead = adp[None, :] >= pick_nos[:, None]
    reach_like = (np.exp(-0.5 * ((pick_nos[:, None] - adp[None, :])
                                 / (sigma * reach_scale)) ** 2) * ahead) + 1e-9

    survived = np.zeros(n, dtype=np.int64)
    e_best = {name: 0.0 for name in groups}
    base_recent = list(recent_pos or [])[-run_window:]
    for _ in range(sims):
        alive = np.ones(n, dtype=bool)
        recent = list(base_recent)
        for i in range(len(rivals)):
            like = reach_like[i] if (reach_prob and rng.random() < reach_prob)                 else adp_like[i]
            w = like * rival_mult[i] * alive
            # positional-run escalation: 2+ same-position picks in the recent
            # window make the NEXT rival likelier to join the run
            if recent:
                window = recent[-run_window:]
                for pos in set(window):
                    if window.count(pos) >= run_min:
                        w = np.where(pos_arr == pos, w * run_boost, w)
            total = w.sum()
            if total <= 0:
                break
            choice = rng.choice(n, p=w / total)
            alive[choice] = False
            recent.append(str(pos_arr[choice]))
        survived += alive
        for name, (gmask, val) in groups.items():
            mask = gmask & alive
            e_best[name] += float(val[mask].max()) if mask.any() else 0.0

    # Two survival vectors, named so they cannot be confused (plan B1/B2):
    # survival_raw is the Monte Carlo frequency; survival is the calibrated
    # vector that is DISPLAYED. (Until plan step B2 lands, e_best_next is
    # still the raw joint expectation from the loop above.)
    raw = survived / sims
    calibrated = np.array([calibrate(float(raw[j]), survival_shrink) for j in range(n)])
    report = {}
    for name in groups:
        e = e_best[name] / sims
        report[name] = {
            "best_now": best_now[name],
            "e_best_next": e,
            "urgency": best_now[name] - e,
            "survival": survival_of(name, arr=calibrated),
            "survival_raw": survival_of(name, arr=raw),
        }
    return report

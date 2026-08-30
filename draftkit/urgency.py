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
    toward 0.5 fits all three buckets: calibrated = 0.5 + (p - 0.5) * shrink."""
    return 0.5 + (p - 0.5) * shrink


def simulate_survival(pool, current_pick, next_pick, rivals, seeds, rng,
                      sims=1000, sigma=6.0, teams=12,
                      reach_prob=0.0, reach_scale=3.0,
                      run_window=5, run_min=2, run_boost=1.5,
                      survival_shrink=1.0, recent_pos=None):
    """Per-position urgency + per-player survival to my next pick.

    pool: undrafted players (dicts with sleeper_id/pos/vorp/adp), pre-truncated.
    rivals: intervening pickers IN PICK ORDER — {"slot", "needs", "user_id"};
            length must equal next_pick - current_pick (my own slot excluded
            only when current_pick is my pick, which callers never pass).
    seeds: rival_seeds.json "users" mapping (may be empty).
    sigma: ADP noise in picks for the current round (caller scales by round).
    """
    n = len(pool)
    picks_between = max(0, next_pick - current_pick)
    pos_arr = np.array([p["pos"] for p in pool]) if n else np.array([], dtype=str)
    vorp = np.array([float(p["vorp"] if p["vorp"] is not None else -99.0) for p in pool])
    adp = np.array([float(p["adp"]) if p.get("adp") is not None else 200.0 for p in pool])

    best_now = {
        pos: float(vorp[pos_arr == pos].max()) if n and (pos_arr == pos).any() else 0.0
        for pos in POSITIONS
    }
    if picks_between == 0 or not rivals or n == 0:
        return {
            pos: {"best_now": best_now[pos], "e_best_next": best_now[pos],
                  "urgency": 0.0,
                  "survival": {p["sleeper_id"]: 1.0 for p in pool if p["pos"] == pos}}
            for pos in POSITIONS
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
            m = 1.0 if fills else NEED_DAMP
            if pos == "QB" and rv["needs"].get("QB", 0) == 0 and rnd < 10:
                m = QB_FILLED_DAMP
            if pos in ("K", "DEF"):
                typical = (seed or {}).get("first_round", {}).get(pos, 13)
                if rnd < typical - 1:
                    m = KDEF_EARLY_DAMP
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
    e_best = {pos: 0.0 for pos in POSITIONS}
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
        for pos in POSITIONS:
            mask = (pos_arr == pos) & alive
            e_best[pos] += float(vorp[mask].max()) if mask.any() else 0.0

    report = {}
    for pos in POSITIONS:
        e = e_best[pos] / sims
        report[pos] = {
            "best_now": best_now[pos],
            "e_best_next": e,
            "urgency": best_now[pos] - e,
            "survival": {
                pool[j]["sleeper_id"]: calibrate(survived[j] / sims, survival_shrink)
                for j in range(n) if pos_arr[j] == pos
            },
        }
    return report

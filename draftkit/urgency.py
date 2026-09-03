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
_WARNED_SHRINK: list = []     # one stderr line per process if a non-1.0 shrink is ever set again
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


def expected_best(values, survival) -> float:
    """E[best value still alive] under INDEPENDENT survivals: walk the
    candidates in value-descending order; each is the best alive with
    probability (nobody better survived) x (he survived). This is the JS
    mirror's eBestNext (draft_driver.js) and is reproducible from a
    displayed survival vector. It is an approximation of the joint
    expectation the Monte Carlo loop computes (sampling without replacement
    correlates survivals); plan B2 measures the gap before choosing."""
    order = sorted(range(len(values)), key=lambda i: -float(values[i]))
    carry, e = 1.0, 0.0
    for i in order:
        s = float(survival[i])
        e += carry * s * float(values[i])
        carry *= (1.0 - s)
    return e


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
                      kdef_typical_round=13, run_ratio=0.0,
                      autopick_sigma_scale=0.5, autopick_need_damp=0.02,
                      autopick_list_prob=0.0,
                      history_end=None,
                      rival_needs_update=True):
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
      autopick rivals (rv["autopick"], plan B5): Yahoo's autopick walks its
                           default rank and fills every starter slot before
                           any bench slot, so such a rival is MORE
                           need-constrained than a human: while he has an
                           open starter slot a non-filling position gets
                           autopick_need_damp; his ADP noise is
                           sigma x autopick_sigma_scale; he never reaches
                           (the reach draw is still consumed so the random
                           stream is common with the human model).
      autopick_list_prob   (plan 2026-09-03 s4, DECISIONS #35) with this
                           probability an autopick seat WALKS Yahoo's default
                           list instead of drawing from the ADP Gaussian: he
                           takes the alive player with the lowest `yrank`
                           (pool key; Yahoo default rank, lower = better;
                           falls back to adp) among those fitting an open
                           starter slot, else the lowest-yrank alive player.
                           The reach uniform decides both reaching and
                           walking, and rng.choice still runs against the
                           one-hot, so the draw count per rival per sim is
                           unchanged. 0.0 is today's behaviour exactly.
      run_ratio and rival_needs_update are accepted here and take effect in
      plan steps B4 and B6.

    The returned dict is keyed by position AND by market name; survival is
    always per player and independent of grouping.
    """
    n = len(pool)
    picks_between = max(0, next_pick - current_pick)
    pos_arr = np.array([p["pos"] for p in pool]) if n else np.array([], dtype=str)
    adp = np.array([float(p["adp"]) if p.get("adp") is not None else 200.0 for p in pool])
    # Yahoo default rank for the list-walking autopick component; mirrors the
    # adp fallback (missing yrank -> adp -> 200.0)
    yrank = np.array([float(p["yrank"]) if p.get("yrank") is not None
                      else (float(p["adp"]) if p.get("adp") is not None else 200.0)
                      for p in pool])
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

    # Per-rival positional multiplier (needs + tendencies) as a vector over
    # POSITIONS (+1 for unknown), indexed by each player's position. Kept as
    # a vector rather than a per-player row so it can be recomputed cheaply
    # when a rival's needs change inside the window (plan B6).
    pos_index = {p: k for k, p in enumerate(POSITIONS)}
    n_pos = len(POSITIONS) + 1
    pos_idx = np.array([pos_index.get(p, len(POSITIONS)) for p in pos_arr], dtype=np.int64)
    autopick = np.array([bool(rv.get("autopick")) for rv in rivals])
    rounds_of = [(current_pick + i - 1) // teams + 1 for i in range(len(rivals))]
    seeds_of = [((seeds or {}).get(str(rv.get("user_id"))) if rv.get("user_id") else None) for rv in rivals]

    def pos_mult(needs: dict, rnd: int, seed, is_autopick: bool) -> np.ndarray:
        v = np.ones(n_pos)
        # BN rides along in the needs dict and is never consumed; without
        # excluding it an autopick seat never reached "starters full" mode
        starters_open = any(v > 0 for k, v in needs.items() if k not in ("BN", "BENCH", "IR"))
        for pos in POSITIONS:
            k = pos_index[pos]
            fills = snake.needs_position(needs, pos)
            if is_autopick:
                # starters first, then rank; K/DEF still wait for their rounds
                m = 1.0 if (fills or not starters_open) else autopick_need_damp
                if pos in ("K", "DEF") and rnd < kdef_typical_round - 1:
                    m = kdef_early_damp
                v[k] = m
                continue
            m = 1.0 if fills else need_damp
            if pos == "QB" and needs.get("QB", 0) == 0 and rnd < qb_damp_until_round:
                m = qb_filled_damp
            if pos in ("K", "DEF"):
                typical = (seed or {}).get("first_round", {}).get(pos, kdef_typical_round)
                if rnd < typical - 1:
                    m = kdef_early_damp
            v[k] = m * _tendency_mult(seed, rnd, pos)
        return v

    base_mult = [pos_mult(rv["needs"], rounds_of[i], seeds_of[i], bool(autopick[i])) for i, rv in enumerate(rivals)]
    # slots that pick more than once inside the window: at a snake turn every
    # team between me and the wall does. Their needs are consumed as the sim
    # hands them players, so the same rival cannot "need" a QB twice.
    later_of: dict = {}
    for i, rv in enumerate(rivals):
        later_of.setdefault(rv["slot"], []).append(i)
    multi = {s: idx for s, idx in later_of.items() if rival_needs_update and len(idx) > 1}
    slot_of = [rv["slot"] for rv in rivals]

    # ADP likelihood per intervening pick (same sigma across the window is fine
    # at this window size; sigma itself scales with round at the call site)
    pick_nos = np.arange(current_pick, next_pick)
    # an autopick rival's noise is a fraction of a human's (plan B5)
    # floor: a zero scale (or sigma) would divide by zero in the likelihood
    sig = np.maximum(np.where(autopick, sigma * autopick_sigma_scale, sigma), 1e-6)[:, None]
    adp_like = np.exp(-0.5 * ((pick_nos[:, None] - adp[None, :]) / sig) ** 2) + 1e-9
    # fat-tail REACH mixture (v2 1.1, CLV retro: reaches are one-directional —
    # players taken EARLY, never "reached for" after their ADP). With
    # reach_prob a rival draws from a widened, forward-only likelihood.
    ahead = adp[None, :] >= pick_nos[:, None]
    reach_like = (np.exp(-0.5 * ((pick_nos[:, None] - adp[None, :])
                                 / (sigma * reach_scale)) ** 2) * ahead) + 1e-9

    survived = np.zeros(n, dtype=np.int64)
    e_best = {name: 0.0 for name in groups}
    # RUN DETECTOR (plan B4). The old rule fired on an absolute count -- two
    # of a position in five picks -- which in an RB/WR-heavy draft is the
    # normal state, so the 1.5 boost was a near-constant multiplier on the
    # two most common positions. A run is now a SURPLUS over what the model
    # itself expected: count(pos in window) >= run_min AND count >
    # run_ratio x sum of the position's share of the pick mass at each pick
    # in the window. run_ratio = 0 restores the absolute rule exactly.
    base_recent = [p for p in (recent_pos or []) if p][-run_window:]
    # the real history picks' expected shares: the plain ADP likelihood at
    # those pick numbers over the current pool (the players still here are
    # what those picks were choosing among, less the ones they took)
    hist_items = []                       # (position index, expected-mass vector)
    if base_recent:
        # the history's last pick is the one BEFORE the pick on the clock;
        # when I am on the clock current_pick is already cur+1 (the window
        # start), so the caller passes history_end=cur
        h_end = int(history_end) if history_end is not None else current_pick
        hp = np.arange(h_end - len(base_recent), h_end)
        hist_like = np.exp(-0.5 * ((hp[:, None] - adp[None, :]) / sigma) ** 2) + 1e-9
        for pos, row in zip(base_recent, hist_like):
            hist_items.append((pos_index.get(pos, len(POSITIONS)), np.bincount(pos_idx, weights=row, minlength=n_pos) / row.sum()))
    onehot = np.eye(n_pos)
    for _ in range(sims):
        alive = np.ones(n, dtype=bool)
        # run-detector window as running sums: counts per position and the
        # model's expected count per position over the last run_window picks
        window = list(hist_items)
        count = np.zeros(n_pos)
        expected = np.zeros(n_pos)
        for k, m in window:
            count += onehot[k]
            expected += m
        mult = list(base_mult)            # per-sim copy of the multiplier vectors
        needs_now = {s: dict(rivals[idx[0]]["needs"]) for s, idx in multi.items()}
        for i in range(len(rivals)):
            # the reach draw is consumed for every rival at every reach_prob so
            # the random stream is identical across reach settings and whether
            # or not a seat is on autopick (paired A/Bs, plan B5/B7)
            u = rng.random()
            reaching = u < reach_prob
            # the SAME uniform decides whether an autopick seat walks Yahoo's
            # list this pick (DECISIONS #35); at list_prob 0 it never does
            walking = bool(autopick[i]) and (u < autopick_list_prob)
            w = None
            if walking:
                # one-hot on the lowest-yrank alive player that fits an open
                # starter slot (multiplier exactly 1.0); else lowest-yrank
                # alive; an empty pool falls through to the normal path
                elig = alive & (mult[i][pos_idx] == 1.0)
                cand = elig if elig.any() else alive
                if cand.any():
                    w = np.zeros(n)
                    w[int(np.argmin(np.where(cand, yrank, np.inf)))] = 1.0
            if w is None:
                like = reach_like[i] if (reaching and not autopick[i]) else adp_like[i]
                w = like * mult[i][pos_idx] * alive
            total0 = w.sum()
            if total0 <= 0:
                break
            mass = np.bincount(pos_idx, weights=w, minlength=n_pos) / total0
            if window:
                boost = (count >= run_min) & (count > run_ratio * expected)
                if boost.any():
                    w = w * np.where(boost[pos_idx], run_boost, 1.0)
            total = w.sum()
            if total <= 0:
                break
            choice = rng.choice(n, p=w / total)
            alive[choice] = False
            k = int(pos_idx[choice])
            window.append((k, mass))
            count += onehot[k]
            expected += mass
            if len(window) > run_window:
                k0, m0 = window.pop(0)
                count -= onehot[k0]
                expected -= m0
            s = slot_of[i]
            if s in multi:
                # this rival's needs shrink by what he just took; his LATER
                # picks in the window are re-weighted (autopick rivals too:
                # starters-first is a needs rule)
                needs_now[s] = snake.consume(needs_now[s], str(pos_arr[choice]))
                for j in multi[s]:
                    if j > i:
                        mult[j] = pos_mult(needs_now[s], rounds_of[j], seeds_of[j], bool(autopick[j]))
        survived += alive
        for name, (gmask, val) in groups.items():
            mask = gmask & alive
            e_best[name] += float(val[mask].max()) if mask.any() else 0.0

    # Two survival vectors, named so they cannot be confused (plan B1/B2):
    # survival_raw is the Monte Carlo frequency; survival is the calibrated
    # vector that is DISPLAYED. The DECISION (e_best_next, urgency) is the
    # joint expectation from the loop above -- exact under sampling without
    # replacement; the carry formula was measured against it (DECISIONS #26:
    # top-1 flips 1/40, urgency gaps up to 8 points on thin TE markets) and
    # stays the JS mirror's approximation, reported here as
    # e_best_next_carry. With survival_shrink = 1.0 (the shrink is retired)
    # display and decision are one vector; any other value makes them
    # disagree, so the engine says so once.
    raw = survived / sims
    calibrated = np.array([calibrate(float(raw[j]), survival_shrink) for j in range(n)])
    if survival_shrink != 1.0 and not _WARNED_SHRINK:
        import sys
        print(f"  SURVIVAL SHRINK {survival_shrink}: displayed survival no longer equals the decision's "
              "(DECISIONS #26 retired the shrink; refit the noise instead)", file=sys.stderr)
        _WARNED_SHRINK.append(True)
    report = {}
    for name, (gmask, val) in groups.items():
        e = e_best[name] / sims                     # the decision: joint expectation over the draw
        e_carry = expected_best(val[gmask], calibrated[gmask]) if gmask.any() else 0.0
        report[name] = {
            "best_now": best_now[name],
            "e_best_next": e,
            "e_best_next_joint": e,
            "e_best_next_carry": e_carry,
            "urgency": best_now[name] - e,
            "survival": survival_of(name, arr=calibrated),
            "survival_raw": survival_of(name, arr=raw),
        }
    return report

"""Unit grades for the MATCHUP block: the props engine's tier system, copied.

The functions between the COPY markers are copied UNCHANGED from
props/engine/scripts/research.py at commit ec379e45ef0f31db4343998ac4536259c6bfbbf5
(unit_efficiency, tier_letter, tiers, unit_tiers and the constants they use).
props/calc may not import the engine (DECISIONS #231), so this is a copy, and
tests/test_calc_grades_parity.py (outside props/calc) checks that both give
the same letters on the same play-by-play. Their constants are also listed in
settings.yaml under fixed_not_tuned, and check_constants() refuses to run if
the two disagree.

The scale: per team, EPA per play and success rate on dropbacks and runs, as
the offense and as the defense (allowed), win probability 10-90% only; two
parts EPA to one part success, standardised, 50 = league average and 10 points
= one standard deviation, higher is better for offense AND defense; equal-width
bands counted from the best team down, lettered S, A, B, C, D, F.

The engine's system has no rule for too few games (only "fewer than 3 teams":
no scale). The user's rule applies (2026-10-10): under 4 games, "Only [G]
games. No grades yet." Display only: no grade changes a bar or a rate.
"""

from __future__ import annotations

import numpy as np

from .checks import require

# ---- COPY from props/engine/scripts/research.py @ ec379e45ef0f (unchanged) ----
SCORE_EPA_WEIGHT = 2 / 3         # the unit score: two parts EPA per play, one part success rate


def unit_efficiency(pbp, wp_lo=0.10, wp_hi=0.90) -> dict:
    """Each team's EPA per play and success rate on dropbacks and runs, as the offence and
    as the defence (allowed), with garbage time removed (win probability wp_lo-wp_hi when
    the play-by-play carries it), plus neutral-situation pace (seconds between snaps on the
    same drive, quarters 1-3, score within 7). Ranks: offence 1st = best, defence 1st = most
    allowed, pace 1st = fastest. {} without EPA."""
    need = {"game_id", "posteam", "defteam", "epa"}
    if pbp is None or not len(pbp) or not need.issubset(pbp.columns):
        return {}
    import pandas as _pd
    f0 = lambda c: pbp[c].fillna(0) if c in pbp else _pd.Series(0, index=pbp.index)
    if {"pass", "rush"}.issubset(pbp.columns):
        is_pass, is_rush = f0("pass") == 1, (f0("rush") == 1) & (f0("pass") != 1)
    else:
        is_pass, is_rush = pbp.play_type.eq("pass"), pbp.play_type.eq("run")
    keep = (is_pass | is_rush) & pbp.epa.notna() & pbp.posteam.notna() & pbp.defteam.notna()
    keep &= (f0("qb_kneel") != 1) & (f0("qb_spike") != 1)
    filt = "all plays"
    if "wp" in pbp:
        keep &= pbp.wp.between(wp_lo, wp_hi)
        filt = f"win probability {100 * wp_lo:.0f}-{100 * wp_hi:.0f}%"
    d = pbp[keep].assign(_pass=is_pass[keep], _succ=(pbp.loc[keep, "success"] if "success" in pbp
                                                    else (pbp.loc[keep, "epa"] > 0).astype(float)))
    out = {"off": {}, "def": {}, "pace": {}, "_league": {}, "_filter": filt}
    for kind, m in (("pass", d._pass), ("run", ~d._pass)):
        x = d[m]
        out["_league"][kind] = (float(x.epa.mean()), float(x._succ.mean()))
        for side, key in (("off", "posteam"), ("def", "defteam")):
            g = x.groupby(key).agg(epa=("epa", "mean"), sr=("_succ", "mean"), n=("epa", "size"))
            er, sr = g.epa.rank(ascending=False, method="min"), g.sr.rank(ascending=False, method="min")
            for t, r in g.iterrows():
                out[side].setdefault(t, {})[kind] = (float(r.epa), int(er[t]), float(r.sr), int(sr[t]), int(r.n))
    out["_n"] = len(set(out["off"]) | set(out["def"]))
    # THE UNIT SCORE (user, 2026-10-06: "blend EPA and success into a score and tier it"):
    # each team's EPA per play and success rate standardised across the league and blended two
    # parts EPA to one part success (user, 2026-10-06: weight EPA more -- big plays count), then
    # put on a 50 +/- 10 scale (50 = league average, 10 = one standard deviation),
    # oriented so higher is better for offences AND defences (a defence allowing less scores high)
    out["score"] = {"off": {"pass": {}, "run": {}}, "def": {"pass": {}, "run": {}}}
    for side in ("off", "def"):
        for kind in ("pass", "run"):
            teams = [t for t, v in out[side].items() if kind in v]
            if len(teams) < 3:
                continue
            e = np.array([out[side][t][kind][0] for t in teams])
            r = np.array([out[side][t][kind][2] for t in teams])
            z = lambda a: (a - a.mean()) / a.std() if a.std() > 0 else a * 0.0
            comp = (SCORE_EPA_WEIGHT * z(e) + (1 - SCORE_EPA_WEIGHT) * z(r)) * (1 if side == "off" else -1)
            comp = z(comp)
            for t, c in zip(teams, comp):
                out["score"][side][kind][t] = float(50 + 10 * c)
    pc = {"game_seconds_remaining", "qtr", "score_differential", "play_id"}
    if pc.issubset(pbp.columns):
        q = pbp[(is_pass | is_rush) & pbp.posteam.notna()].sort_values(["game_id", "play_id"])
        drv = q["fixed_drive"] if "fixed_drive" in q else q["drive"] if "drive" in q else None
        same = (q.game_id.eq(q.game_id.shift()) & q.posteam.eq(q.posteam.shift())
                & (drv.eq(drv.shift()) if drv is not None else True))
        dt = q.game_seconds_remaining.shift() - q.game_seconds_remaining
        neutral = q.qtr.le(3) & q.score_differential.abs().le(7) & same & dt.between(1, 60)
        sec = dt[neutral].groupby(q.loc[neutral, "posteam"]).mean()
        rk = sec.rank(ascending=True, method="min")
        out["pace"] = {t: (float(v), int(rk[t])) for t, v in sec.items()}
    return out



TIER_STEPS = (0.5, 1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10)
MAX_TIERS = 6
TIER_LETTERS = "SABCDF"          # user, 2026-10-06: S, A, B, C, D, F from the best band down


def tier_letter(k: int) -> str:
    """Band k (1 = best) as its letter; a letter always means the same band position, so a
    list whose spread needs only five bands has no F."""
    return TIER_LETTERS[min(max(int(k), 1), len(TIER_LETTERS)) - 1]


def tiers(values: dict, higher_is_better=True, max_tiers=MAX_TIERS, steps=TIER_STEPS) -> dict:
    """Equal-width tiers counted from the best team down (user, 2026-10-06). The width is the
    smallest round step that keeps the league inside max_tiers bands, so a tight league gets
    narrow bands and a spread-out one wide bands, and every band means the same number of
    points. Returns {"step", "n", "tier": {team: k}, "bands": [(k, lo, hi)]} with bands in
    the values' own units (1 = best)."""
    if not values:
        return {"step": None, "n": 0, "tier": {}, "bands": []}
    g = {t: (v if higher_is_better else -v) for t, v in values.items()}
    best, worst = max(g.values()), min(g.values())
    span = best - worst
    step = next((st for st in steps if span <= st * max_tiers), steps[-1])
    n = max(1, min(max_tiers, int(-(-span // step)) if span > 0 else 1))
    tier = {t: min(n, 1 + int((best - x) // step)) for t, x in g.items()}
    _values = dict(values)
    bands = []
    for k in range(1, n + 1):
        hi_g, lo_g = best - (k - 1) * step, best - k * step
        if k == n:
            lo_g = min(lo_g, worst)          # the last band always reaches the worst team
        lo, hi = (lo_g, hi_g) if higher_is_better else (-hi_g, -lo_g)
        bands.append((k, lo, hi))
    return {"step": step, "n": n, "tier": tier, "bands": bands, "best": best,
            "higher_is_better": higher_is_better, "_values": _values}



INT_STEPS = (2, 3, 4, 5, 6, 8, 10, 12, 15, 20)


def unit_tiers(ue) -> dict:
    """The four tier scales on the unit score (higher is better on all four)."""
    sc = (ue or {}).get("score") or {}
    # tiered on the WHOLE-NUMBER scores the table shows, in whole-number bands, so a printed
    # score always sits inside its tier's printed range (code review)
    return {(side, kind): tiers({t: round(v) for t, v in sc.get(side, {}).get(kind, {}).items()},
                                higher_is_better=True, steps=INT_STEPS)
            for side in ("off", "def") for kind in ("pass", "run")}

# ---- end of COPY ----


def check_constants(fixed: dict) -> None:
    """The copied constants must match settings.yaml's fixed_not_tuned."""
    want = {"grade_score_epa_weight": SCORE_EPA_WEIGHT, "grade_max_tiers": MAX_TIERS,
            "grade_tier_letters": TIER_LETTERS, "grade_int_steps": list(INT_STEPS),
            "grade_tier_steps": list(TIER_STEPS)}
    for k, v in want.items():
        got = fixed.get(k)
        same = abs(got - v) < 1e-12 if isinstance(v, float) and got is not None else got == v
        require(same, f"settings.yaml {k} = {got!r} but the copied grade code uses {v!r}")
    require(fixed["garbage_wp_low"] == 0.10 and fixed["garbage_wp_high"] == 0.90,
            "the copied unit_efficiency defaults to win probability 10-90%; settings.yaml differs")


def season_grades(pbp, fixed: dict) -> dict:
    """{(side, kind): {team: letter}} plus {"_games": {team: games}} from the
    plays given (already cut to this season before the priced week)."""
    check_constants(fixed)
    ue = unit_efficiency(pbp, fixed["garbage_wp_low"], fixed["garbage_wp_high"])
    out = {key: {t: tier_letter(k) for t, k in t_["tier"].items()} for key, t_ in unit_tiers(ue).items()}
    games = {}
    for team_col in ("posteam", "defteam"):
        for t, n in pbp.groupby(team_col)["game_id"].nunique().items():
            games[t] = max(games.get(t, 0), int(n))
    out["_games"] = games
    return out


def grade_pair(b, team: str, opp: str, kind: str, season: int, week: int, fixed: dict) -> dict:
    """His team's offense and the opponent's defense on `kind` (run or pass):
    {"off", "def"} letters, or {"note"} under the minimum games."""
    key = (season, week)
    cache = b.__dict__.setdefault("_grades", {})
    if key not in cache:
        plays = b.cut(b.pbp[b.pbp["season"] == season], season, week, "grade plays")
        cache[key] = season_grades(plays, fixed)
    g = cache[key]
    n = min(g["_games"].get(team, 0), g["_games"].get(opp, 0))
    if n < int(fixed["thin_games"]):
        return {"note": f"Only {n} games. No grades yet."}
    off, dfn = g[("off", kind)].get(team), g[("def", kind)].get(opp)
    if off is None or dfn is None:
        return {"note": "grades not available."}
    return {"off": off, "def": dfn}

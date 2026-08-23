"""Bye-aware playoff odds + regime (season spec, revised §3).

Weekly team strength is computed from each team's per-week startable roster —
players whose NFL team is on bye that week contribute zero, so weeks 5-14
swing strengths by real amounts instead of a season-constant sum. Remaining
league matchups are simulated `sims` times; playoff odds feed a regime label
that colors every waiver-bid recommendation.
"""

from __future__ import annotations

import numpy as np

FLEX_ELIGIBLE = ("RB", "WR", "TE")


def team_week_strength(roster: list[dict], byes: set[str],
                       slots: dict[str, int], flex: int) -> float:
    """Best legal lineup for one week; bye-week players score 0."""
    def wk(p):
        return 0.0 if p.get("team") in byes else float(p.get("weekly") or 0.0)

    pool = sorted(roster, key=wk, reverse=True)
    counts = {k: 0 for k in slots}
    used, total, flex_used = set(), 0.0, 0
    for p in pool:
        pos = p.get("pos")
        if pos in slots and counts[pos] < slots[pos]:
            counts[pos] += 1
            total += wk(p)
            used.add(p["sleeper_id"])
    for p in pool:
        if p["sleeper_id"] not in used and p.get("pos") in FLEX_ELIGIBLE and flex_used < flex:
            flex_used += 1
            total += wk(p)
    return total


def simulate_season(strengths: dict[int, dict[int, float]],
                    matchups: dict[int, list[tuple[int, int]]],
                    records: dict[int, tuple[int, int]],
                    playoff_teams: int, sims: int, sigma: float,
                    rng: np.random.Generator,
                    points_for: dict[int, float]) -> dict[int, float]:
    """P(make playoffs) per roster_id. Standings: wins, then points-for.

    strengths[roster_id][week] must exist for every remaining matchup week.
    """
    teams = sorted(records)
    made = {t: 0 for t in teams}
    weeks = sorted(matchups)
    for _ in range(sims):
        wins = {t: records[t][0] for t in teams}
        pf = dict(points_for)
        for wk_no in weeks:
            for a, b in matchups[wk_no]:
                sa = strengths[a][wk_no] + rng.normal(0.0, sigma)
                sb = strengths[b][wk_no] + rng.normal(0.0, sigma)
                pf[a] += sa
                pf[b] += sb
                if sa > sb:
                    wins[a] += 1
                else:
                    wins[b] += 1
        order = sorted(teams, key=lambda t: (wins[t], pf[t]), reverse=True)
        for t in order[:playoff_teams]:
            made[t] += 1
    return {t: made[t] / sims for t in teams}


def regime(odds: float, cfg: dict) -> str:
    if odds >= float(cfg.get("regime_safe", 0.85)):
        return "SAFE"
    if odds >= float(cfg.get("regime_comfortable", 0.60)):
        return "COMFORTABLE"
    if odds >= float(cfg.get("regime_bubble", 0.25)):
        return "BUBBLE"
    return "LONGSHOT"

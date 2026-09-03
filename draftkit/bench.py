"""Bench realities: what a player who will not start is actually worth.

The engine's one-sentence rule is "draft the biggest remaining value at
positions you still need, measured against what's freely available later."
For starters that last clause is Tracker._fallback_points. For the bench it
was never applied: bench rounds ranked candidates by VORP against the STARTER
baseline, so a backup quarterback measured against QB10 looked like +20 when
the thing he actually competes with is the waiver wire, where he is +4. That
is the whole reason the engine drafted a QB2 in 21 of 22 replayed rosters.

A bench player is insurance. His value is

    weeks you will need him  x  his weekly edge over the free alternative

Both factors are league-derived and neither is per-player injury history:

  * weeks needed = (starters he covers) x (position absent-week rate + bye).
    The rate is a POSITION base rate from six seasons of nflverse, starters
    chosen ex ante (scripts/derive_bench_rates.py). Per-player games-missed
    was removed from valuation on 2026-08-30 (research Q6) and stays out; the
    first draft of this module used exp_games and would have reintroduced it
    through a side door.
  * free alternative = the k-th best player at the position the market leaves
    undrafted (ADP beyond the last pick), k from the waiver format. Same
    order-statistic operator as baselines.py; here it needs no historical
    ownership because the pool is defined by the current draft.
  * handcuff: a backup whose starter is on MY roster inherits that role in
    exactly the weeks the insurance pays. His weekly rate is uplifted by the
    measured ratio of an ex-ante backup's production in starter-absent weeks
    to his own standalone rate, capped at the starter's own rate.

Position base rates and the uplift are frozen here with their derivation
rather than recomputed at build time -- they are facts about the sport, not
about a league, and the script that produced them is the audit trail.
"""

from __future__ import annotations

from .snake import FLEX_ELIGIBLE

FANTASY_WEEKS = 17
BYE_WEEKS = 1.0

# scripts/derive_bench_rates.py, seasons 2019-2025 (six ex-ante pairs), league
# scoring half-PPR (the ratio is scoring-insensitive). Injury absences only in
# fantasy weeks 1-17; zero-game seasons excluded, so biased LOW. N: QB 70,
# RB 142, WR 144, TE 71. Medians are 1-2 weeks; means carry the season-enders.
# (WR first read 2.69: an unstable sort at the WR24 cutoff; deterministic now.)
ABSENT_WEEKS = {"QB": 2.56, "RB": 3.13, "WR": 2.61, "TE": 2.93}

# Ex-ante backup's points in his starter's absent weeks, over the same
# backup's standalone rate: median 1.46 across 277 starter-absent weeks. The
# first cut used max-of-teammates ex post and read 1.28 of the STARTER's
# rate -- hindsight picking the right handcuff, which a draft pick cannot do.
HANDCUFF_UPLIFT = 1.46

BENCH_POSITIONS = tuple(ABSENT_WEEKS)


def weeks_needed(pos: str, exposure: int, depth_ahead: int = 0) -> float:
    """Expected weeks a bench player at `pos` is called on.

    exposure: how many of my starters he could replace.
    depth_ahead: how many backups at the position I ALREADY have. The first
    backup plays whenever any starter is out; the (n+1)th plays only when
    n+1 starters are out in the SAME week.

    The first version was exposure x (rate + bye) -- linear in starters, blind
    to depth. The season replay (DECISIONS 2026-09-01 #8) found exactly what
    that does: every Keefamania slot that lost had drafted a 6th WR, priced as
    if he covered the first absence when three starters and two reserves stood
    between him and a lineup. So: treat each starter's weekly absence as an
    independent draw with probability (rate + bye) / 17, and take
    17 x P(at least depth_ahead + 1 of `exposure` starters are out).
    """
    if exposure <= 0 or pos not in ABSENT_WEEKS:
        return 0.0
    q = min(1.0, (ABSENT_WEEKS[pos] + BYE_WEEKS) / FANTASY_WEEKS)
    need = depth_ahead + 1
    if need > exposure:
        return 0.0
    # P(Binomial(exposure, q) >= need), exposure is at most a handful
    from math import comb
    p_ge = sum(comb(exposure, j) * q ** j * (1 - q) ** (exposure - j)
               for j in range(need, exposure + 1))
    return FANTASY_WEEKS * p_ge


def starter_exposure(my_positions: list[str], slots: dict[str, int]) -> dict[str, int]:
    """How many of my current starters play each position -- dedicated slots
    first, then FLEX, same fill order as snake.starter_needs. A bench RB
    covers an RB starting in the flex just as much as one in an RB slot."""
    remaining = dict(slots)
    out: dict[str, int] = {}
    for pos in my_positions:
        if remaining.get(pos, 0) > 0:
            remaining[pos] -= 1
        elif pos in FLEX_ELIGIBLE and remaining.get("FLEX", 0) > 0:
            remaining["FLEX"] -= 1
        else:
            continue
        out[pos] = out.get(pos, 0) + 1
    return out


def waiver_ppw(remaining_at_pos: list[dict], last_pick: int, k: int) -> tuple[float, str]:
    """(points per week, name) of the k-th best player the market leaves
    undrafted. Candidates are the remaining players whose ADP falls beyond
    the draft's last pick (or who have no ADP at all); if the wire is thinner
    than k, take its worst; if nothing is projected undrafted, the worst
    VIABLE remaining player is the honest floor.

    Viable means projects above 0 and is not availability-'out': streaming
    means picking up someone who can play. The old fallback took the worst
    remaining player outright, and in every 2026-09-03 mock that was Josh
    Jacobs at 0.0 (zeroed for the Commissioner Exempt List), which measured
    all RB insurance against a ghost."""
    viable = [p for p in remaining_at_pos
              if float(p.get("proj_pts") or 0.0) > 0.0
              and str(p.get("avail_status") or "") != "out"]
    free = sorted(
        (p for p in viable
         if p.get("adp") is None or float(p["adp"]) > last_pick),
        key=lambda p: -float(p.get("proj_pts") or 0.0))
    if not free:
        free = sorted(viable, key=lambda p: float(p.get("proj_pts") or 0.0))[:1]
    if not free:
        return 0.0, ""
    pick = free[min(k, len(free)) - 1]
    return float(pick.get("proj_pts") or 0.0) / FANTASY_WEEKS, str(
        pick.get("player") or pick.get("name") or "")


def insurance_value(p: dict, waiver: float, exposure: int,
                    handcuff_starter_ppw: float | None = None,
                    depth_ahead: int = 0) -> dict:
    """Season points a bench player is expected to add over streaming.

    handcuff_starter_ppw: the weekly rate of the starter he backs up, when
    that starter is on MY roster; None otherwise.
    depth_ahead: backups I already roster at his position (see weeks_needed).
    Returns the pieces too, so the rationale can show its work.
    """
    pos = p.get("pos")
    ppw = float(p.get("proj_pts") or 0.0) / FANTASY_WEEKS
    handcuff = handcuff_starter_ppw is not None
    if handcuff:
        # inherits the role in exactly the weeks the insurance pays; the cap
        # is a sanity bound, not a tuned number -- a backup does not project
        # above the job he is stepping into
        ppw = min(ppw * HANDCUFF_UPLIFT, max(handcuff_starter_ppw, ppw))
    edge = max(0.0, ppw - waiver)
    weeks = weeks_needed(pos, exposure, depth_ahead)
    return {"value": edge * weeks, "edge": edge, "weeks": weeks,
            "ppw": ppw, "waiver_ppw": waiver, "handcuff": handcuff,
            "depth_ahead": depth_ahead}

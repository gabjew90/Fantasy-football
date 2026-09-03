"""Two-pick joint planner (v2 item 1.2, amendment B).

Greedy per-position urgency won the pick and lost the round at #26/#47:
it never asked what PAIR of picks maximizes value. This ranks candidates by
    pair(c) = need-weighted VORP(c now) + best expected partner at my next turn,
using ONLY numbers the urgency report already computed — no new simulation,
so the on-clock path stays model-free and the greedy order is the automatic
fallback whenever the report isn't ready (amendment B's latency budget).

Partner rules (code review 2026-08-30): the partner-eligibility set comes
from the SAME guardrail predicate the next pick will actually apply
(tracker._pos_allowed, conditioned on the candidate being rostered), needs
are consumed by the candidate before valuing the partner, and same-position
pairing caps at second-best-now because the report's expectation doesn't
know the candidate himself was just taken.
"""

from __future__ import annotations

from typing import Callable

from .snake import FLEX_ELIGIBLE, needs_position

NEED_DAMP = 0.6  # partner/candidate position that fills no starter/flex slot


def slot_vorp(p: dict, needs: dict) -> float:
    """Value in the slot this player would ACTUALLY occupy.

    VORP is measured against replacement at the player's own position, which
    is only the right comparison when he fills that position's dedicated slot.
    A player headed for the FLEX competes with the RB/WR you would otherwise
    start there, so he is worth `vorp_flex` instead.

    On the Keefamania board the two differ by 32.8 points for every
    flex-eligible player, which is what made the engine value a second elite
    tight end at +61.9 when his real marginal contribution was +29.1 -- and
    what produced the double-TE build.

    Falls back to `vorp` when the column is absent, so older boards still load.
    """
    pos = p.get("pos")
    dedicated_open = needs.get(pos, 0) > 0
    if dedicated_open or pos not in FLEX_ELIGIBLE:
        return float(p.get("vorp") or 0.0)
    vf = p.get("vorp_flex")
    return float(vf if vf is not None else (p.get("vorp") or 0.0))


def own_value(p: dict, needs: dict, fallback: dict[str, float] | None) -> float:
    """What taking this player NOW is worth, for the two-pick comparison.

    The default is slot_vorp -- a LEVEL, measured against a replacement
    baseline out of the league yaml. That is where the whole engine's
    dependence on that baseline lives (urgency is a difference, so the
    baseline cancels there; measured 2026-09-01: with this planner disabled,
    QB5/TE8 and QB10/TE11 draft the same team).

    Levels are only commensurable across positions if the baseline is right,
    and "right" is not a season-long constant. The alternative to drafting a
    quarterback now is not some notional QB10 -- it is the quarterback you
    will actually end up with when you get round to the position. In a 10-team
    1-QB league that is a startable QB, so the true marginal value of an early
    one is small. In the same league the alternative to a running back is
    RB40, so his marginal value is large. A single yaml number cannot say both,
    which is why it had to be hand-fitted to make the engine behave.

    `fallback` supplies exactly that, per position, computed from the board and
    the picks I have left (Tracker._fallback_points). With it, "own" becomes
    projected points above the player I would otherwise end up with -- no
    replacement baseline involved, and adaptive to the room by construction.
    """
    if fallback is None:
        return slot_vorp(p, needs)
    pos = p.get("pos")
    if pos not in fallback:
        return slot_vorp(p, needs)
    return float(p.get("proj_pts") or 0.0) - fallback[pos]


def market_for(pos: str, needs: dict) -> str:
    """Which urgency market a position is shopped in, given open slots.

    Mirrors Tracker._open_markets: a dedicated slot still open means the
    position is its own market; otherwise a flex-eligible position is shopped
    inside FLEX, where the expectation is over RB/WR/TE together.
    """
    if needs.get(pos, 0) > 0 or pos not in FLEX_ELIGIBLE:
        return pos
    return "FLEX" if needs.get("FLEX", 0) > 0 else pos


from .snake import consume  # noqa: E402,F401  (one definition, shared with the survival sim; plan B6)


def pair_rank(cands: list[tuple[float, str, dict]],
              report: dict | None,
              needs: dict,
              second_best_now: dict[str, float],
              eligible_after: Callable[[str], set[str]],
              fallback: dict[str, float] | None = None,
              repl: dict[str, float] | None = None,
              ) -> list[tuple[float, str, dict]]:
    """Re-rank recommendation candidates by joint two-pick EV.

    cands: (greedy_score, why, player) per position, guardrail-filtered.
    report: urgency report {pos: {e_best_next, ...}} or None (-> greedy).
    second_best_now: pos -> second-best VORP currently on the board.
    eligible_after: pos_taken -> partner positions the next pick may take,
        per the real guardrails conditioned on the candidate being rostered.
    """
    if not report or len(cands) < 2:
        for _s, _w, p in cands:
            p.pop("_pair", None)     # never leave a previous call's math on a player
        return cands

    def partner_value(pos_taken: str) -> tuple[float, str | None]:
        needs_after = consume(needs, pos_taken)
        best_v, best_p = 0.0, None
        for pos2 in eligible_after(pos_taken):
            # value the partner in the market he'd actually be shopping in at
            # my next turn, which depends on what THIS pick just filled
            mkt = market_for(pos2, needs_after)
            u = report.get(mkt) or report.get(pos2)
            if not u:
                continue
            e = float(u.get("e_best_next") or 0.0)
            if fallback is not None and repl is not None and pos2 in fallback:
                # the report speaks VORP; convert back to points through the
                # market's own replacement level, then re-measure against the
                # player I would otherwise end up with. Mixing a VORP partner
                # with a fallback-measured candidate would compare two
                # different currencies.
                e = e + repl.get(mkt, repl.get(pos2, 0.0)) - fallback[pos2]
            if pos2 == pos_taken:
                e = min(e, second_best_now.get(pos2, 0.0))
            v = e if needs_position(needs_after, pos2) else e * NEED_DAMP
            if v > best_v:
                best_v, best_p = v, pos2
        return best_v, best_p

    ranked = []
    for score, why, p in cands:
        pv, partner = partner_value(p["pos"])
        # the CANDIDATE side is need-weighted too — without this, deep
        # positions with fat raw VORP (WR) spam the roster after their
        # starter slots are full (caught by simulate: a 10-WR roster)
        own = own_value(p, needs, fallback) * (
            1.0 if needs_position(needs, p["pos"]) else NEED_DAMP)
        pair = own + pv
        if partner:
            why = (why + f" · two-pick plan: pair with the ~"
                   f"{pv:.0f}-pt {partner} expected at your next turn")
        # the arithmetic that decides the ranking, kept structured so the
        # panel and the reports can SHOW the decision, not just assert it
        # (user request 2026-09-03: cost of waiting AND cost of picking)
        p["_pair"] = {"own": round(own, 1), "partner_pos": partner,
                      "partner_pts": round(pv, 1), "pair": round(pair, 1)}
        ranked.append((pair, score, why, p))
    ranked.sort(key=lambda t: (-t[0], -t[1]))
    best_pair = ranked[0][0]
    for pair, _s, _w, p in ranked:
        # cost of PICKING him now = the best pair minus his pair (0 for the winner)
        p["_pair"]["pick_cost"] = round(best_pair - pair, 1)
    # keep the original tuple shape; joint value becomes the score the UI sorts by
    return [(pair, why, p) for pair, _s, why, p in ranked]

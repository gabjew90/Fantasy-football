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


def consume(needs: dict, pos: str) -> dict:
    """Roster needs after taking one player at `pos` (dedicated slot first,
    then FLEX)."""
    out = dict(needs)
    if out.get(pos, 0) > 0:
        out[pos] -= 1
    elif pos in FLEX_ELIGIBLE and out.get("FLEX", 0) > 0:
        out["FLEX"] -= 1
    return out


def pair_rank(cands: list[tuple[float, str, dict]],
              report: dict | None,
              needs: dict,
              second_best_now: dict[str, float],
              eligible_after: Callable[[str], set[str]],
              ) -> list[tuple[float, str, dict]]:
    """Re-rank recommendation candidates by joint two-pick EV.

    cands: (greedy_score, why, player) per position, guardrail-filtered.
    report: urgency report {pos: {e_best_next, ...}} or None (-> greedy).
    second_best_now: pos -> second-best VORP currently on the board.
    eligible_after: pos_taken -> partner positions the next pick may take,
        per the real guardrails conditioned on the candidate being rostered.
    """
    if not report or len(cands) < 2:
        return cands

    def partner_value(pos_taken: str) -> tuple[float, str | None]:
        needs_after = consume(needs, pos_taken)
        best_v, best_p = 0.0, None
        for pos2 in eligible_after(pos_taken):
            u = report.get(pos2)
            if not u:
                continue
            e = float(u.get("e_best_next") or 0.0)
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
        own = slot_vorp(p, needs) * (
            1.0 if needs_position(needs, p["pos"]) else NEED_DAMP)
        pair = own + pv
        if partner:
            why = (why + f" · two-pick plan: pair with the ~"
                   f"{pv:.0f}-pt {partner} expected at your next turn")
        ranked.append((pair, score, why, p))
    ranked.sort(key=lambda t: (-t[0], -t[1]))
    # keep the original tuple shape; joint value becomes the score the UI sorts by
    return [(pair, why, p) for pair, _s, why, p in ranked]

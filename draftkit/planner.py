"""Two-pick joint planner (v2 item 1.2, amendment B).

Greedy per-position urgency won the pick and lost the round at #26/#47:
it never asked what PAIR of picks maximizes value. This ranks candidates by
    pair(c) = VORP(c now) + best expected partner at my next turn,
using ONLY numbers the urgency report already computed — no new simulation,
so the on-clock path stays model-free and the greedy order is the automatic
fallback whenever the report isn't ready (amendment B's latency budget).

Same-position pairing uses min(e_best_next, second-best-now) because the
report's expectation doesn't know the candidate himself was just taken.
"""

from __future__ import annotations

NEED_DAMP = 0.6  # partner position that fills no starter/flex slot


def pair_rank(cands: list[tuple[float, str, dict]],
              report: dict | None,
              needs: dict,
              second_best_now: dict[str, float],
              eligible_next: set[str],
              flex_eligible: tuple[str, ...] = ("RB", "WR", "TE"),
              ) -> list[tuple[float, str, dict]]:
    """Re-rank recommendation candidates by joint two-pick EV.

    cands: (greedy_score, why, player) per position, guardrail-filtered.
    report: urgency report {pos: {e_best_next, ...}} or None (-> greedy).
    second_best_now: pos -> second-best VORP currently on the board.
    eligible_next: positions my next pick would be allowed to take.
    """
    if not report or len(cands) < 2:
        return cands

    def partner_value(pos_taken: str) -> tuple[float, str | None]:
        best_v, best_p = 0.0, None
        for pos2 in eligible_next:
            u = report.get(pos2)
            if not u:
                continue
            e = float(u.get("e_best_next") or 0.0)
            if pos2 == pos_taken:
                e = min(e, second_best_now.get(pos2, 0.0))
            fills = needs.get(pos2, 0) > 0 or (
                pos2 in flex_eligible and needs.get("FLEX", 0) > 0)
            v = e if fills else e * NEED_DAMP
            if v > best_v:
                best_v, best_p = v, pos2
        return best_v, best_p

    ranked = []
    for score, why, p in cands:
        pv, partner = partner_value(p["pos"])
        pos = p["pos"]
        fills_now = needs.get(pos, 0) > 0 or (
            pos in flex_eligible and needs.get("FLEX", 0) > 0)
        # the CANDIDATE side is need-weighted too — without this, deep
        # positions with fat raw VORP (WR) spam the roster after their
        # starter slots are full (caught by simulate: a 10-WR roster)
        own = float(p.get("vorp") or 0.0) * (1.0 if fills_now else NEED_DAMP)
        pair = own + pv
        if partner:
            why = (why + f" · two-pick plan: pair with the ~"
                   f"{pv:.0f}-pt {partner} expected at your next turn")
        ranked.append((pair, score, why, p))
    ranked.sort(key=lambda t: (-t[0], -t[1]))
    # keep the original tuple shape; joint value becomes the score the UI sorts by
    return [(pair, why, p) for pair, _s, why, p in ranked]

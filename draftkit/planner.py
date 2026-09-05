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

from .boardrow import published_range
from .snake import FLEX_ELIGIBLE, needs_position

NEED_DAMP = 0.6  # partner/candidate position that fills no starter/flex slot
NEAR_TIE = 1.0   # pair values this close are a coin flip: survival breaks it
# ...and when survival cannot (the two survivals within FLOOR_SURV_TOL), the
# higher FLOOR does, if the floors differ by at least FLOOR_GAP points: the
# published low line, else the point minus half the band (DECISIONS #55)
FLOOR_SURV_TOL = 0.05
FLOOR_GAP = 3.0
# tie_break: touchdowns (DECISIONS #53, tried for one room and reverted the
# same morning; the knob stays, off) compares projected touchdowns between
# two SKILL players whose pairs are within tie_window; a quarterback's thirty
# scores would win every tie against any back or receiver, so QB pairs (and
# K/DEF) keep the scarcity rule.
TD_TIE_POSITIONS = frozenset({"RB", "WR", "TE"})
TIE_BREAKS = ("scarcity", "touchdowns")


def slot_vorp(p: dict, needs: dict) -> float:
    """Value in the slot this player would ACTUALLY occupy.

    VORP is measured against replacement at the player's own position, which
    is only the right comparison when he fills that position's dedicated slot.
    A player headed for the FLEX competes with the RB/WR you would otherwise
    start there, so he is worth `vorp_flex` instead.

    The gap between the two is PER POSITION, not one constant: vorp_flex
    measures against the highest flex-eligible replacement, so the gap is
    zero for whichever position sets that baseline and largest for the
    shallowest. On the 2026-09-04 Keefamania board it is TE 38.0, WR 18.1,
    RB 0.0. That TE gap is what made the engine value a second elite tight
    end at +61.9 when his real marginal contribution was +29.1 -- and what
    produced the double-TE build.

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
              partner_certain: bool = False,
              tie_break: str = "scarcity",
              tie_window: float = NEAR_TIE,
              ) -> list[tuple[float, str, dict]]:
    """Re-rank recommendation candidates by joint two-pick EV.

    cands: (greedy_score, why, player) per position, guardrail-filtered.
    report: urgency report {pos: {e_best_next, ...}} or None (-> greedy).
    second_best_now: pos -> second-best VORP currently on the board.
    eligible_after: pos_taken -> partner positions the next pick may take,
        per the real guardrails conditioned on the candidate being rostered.
    partner_certain: the partner pick is the very next pick with no rival in
        between (a turn seat under Tracker.turn_look_through), so the partner
        is priced at the market's best_now rather than its expected best.
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
            e = float((u.get("best_now") if partner_certain else u.get("e_best_next")) or 0.0)
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
        # THE NUMBER THAT ACTUALLY DECIDES THE ORDER, said out loud.
        #
        # `ranked.sort` below is keyed on `pair`, and the urgency sentence this
        # `why` opens with -- "waiting likely costs ~N pts" -- is the GREEDY
        # score, which only ever breaks a tie. Printing the urgency number as
        # the reason while sorting on a different one made the reports
        # unauditable: room 10704422 pick 11 showed McBride's waiting cost as
        # 31 and Chase Brown's as 13, took Chase Brown, and nothing on the page
        # or in the trail said why. The answer was own-value -- fallback[RB]
        # was low because the RB pool empties, so Chase Brown's points above
        # the back he'd otherwise end up with were large -- and that term
        # appeared nowhere a human could read it.
        #
        # This is a DISPLAY fix. The ordering is untouched; the clause is
        # appended, so every downstream `why` matcher (draft_driver.js,
        # mock_scrutiny.py) still anchors on the same prefixes.
        # ONE DECIMAL, not zero. NEAR_TIE is 1.0, so integers cannot settle
        # whether two rows were inside the tie window: a printed "140 vs 139"
        # spans true gaps from 0.0 to 2.0, and half that range fires the rule
        # while half does not. A reader checking the near-tie rule against the
        # report could not do it, and reasonably read the absence of an
        # annotation as the rule being broken (user, room 10705481 round 2).
        why = (why + f" · RANKED ON {pair:.1f} = {own:.1f} his own edge over the "
               f"{p.get('pos')} you'd otherwise end up with"
               + (f" + {pv:.1f} the {partner} this frees up next turn" if partner
                  else " (no partner: nothing else fills a slot next turn)"))
        # the arithmetic that decides the ranking, kept structured so the
        # panel and the reports can SHOW the decision, not just assert it
        # (user request 2026-09-03: cost of waiting AND cost of picking)
        p["_pair"] = {"own": round(own, 1), "partner_pos": partner,
                      "partner_pts": round(pv, 1), "pair": round(pair, 1)}
        ranked.append((pair, score, why, p))
    ranked.sort(key=lambda t: (-t[0], -t[1]))

    # NEAR-TIE RULE (user, 2026-09-03): when two candidates' pairs are within
    # NEAR_TIE points, take the one LESS likely to be there next turn. The
    # pair is worth the same either way, but it only completes if the second
    # player survives, so the scarcer one goes first. One bubble pass over
    # adjacent near-ties; survival comes from the same report the pair used.
    def _surv(p: dict) -> float:
        mkt = market_for(p["pos"], needs)
        u = report.get(mkt) or report.get(p["pos"]) or {}
        s = (u.get("survival") or {}).get(str(p.get("sleeper_id")))
        return float(s) if s is not None else 1.0
    def _td(p: dict) -> float | None:
        v = p.get("proj_td")
        return float(v) if v is not None else None

    def _td_pair(x: dict, y: dict) -> bool:
        return (tie_break == "touchdowns" and x.get("pos") in TD_TIE_POSITIONS
                and y.get("pos") in TD_TIE_POSITIONS and _td(x) is not None and _td(y) is not None)

    def _floor(p: dict) -> float | None:
        return published_range(p)[0]

    def _prefer_b(a, b) -> str | None:
        """ONE comparator for an adjacent pair (review 2026-09-05: the three
        rules used to run as separate passes and a later pass could demote a
        row while leaving the earlier pass's label on it). Returns the reason
        b should go above a, or None to leave the order alone:
          1. touchdown rule (knob), inside tie_window, decides either way;
          2. inside NEAR_TIE: survivals more than FLOOR_SURV_TOL apart -> the
             scarcer player first;
          3. else floors FLOOR_GAP or more apart -> the higher floor first;
          4. else any survival difference -> the scarcer player first."""
        gap = abs(a[0] - b[0])
        pa, pb = a[3], b[3]
        if _td_pair(pa, pb) and gap <= tie_window and _td(pa) != _td(pb):
            return (f"more projected touchdowns ({_td(pb):.1f} vs {_td(pa):.1f})"
                    if _td(pb) > _td(pa) else None)
        if gap > NEAR_TIE:
            return None
        sa, sb = _surv(pa), _surv(pb)
        if abs(sa - sb) > FLOOR_SURV_TOL:
            return f"scarcer player first ({sb:.0%} vs {sa:.0%})" if sb < sa else None
        fa, fb = _floor(pa), _floor(pb)
        if fa is not None and fb is not None and abs(fb - fa) >= FLOOR_GAP:
            return f"higher floor ({fb:.0f} vs {fa:.0f})" if fb > fa else None
        return f"scarcer player first ({sb:.0%} vs {sa:.0%})" if sb < sa - 1e-9 else None

    # One bubble pass over adjacent pairs; a swap steps back one slot so the
    # promoted row is compared with the row now above it. NAME THE
    # COUNTERPARTY: "near tie (0.7 pts): scarcer player first" states a gap
    # against nobody, so a reader assumes the swap was against the player
    # finally picked -- which it usually is not (room 10703362 pick 24
    # annotated Olave, promoted over Josh Allen while McBride sat above both).
    # The windows make the preference non-transitive in principle, so a
    # cycle stop bounds the pass; in practice it never engages.
    i, steps = 0, 0
    while i < len(ranked) - 1 and steps < 4 * (len(ranked) + 1):
        steps += 1
        a, b = ranked[i], ranked[i + 1]
        reason = _prefer_b(a, b)
        if reason:
            over = a[3].get("player") or a[3].get("name") or a[3].get("pos")
            ranked[i], ranked[i + 1] = b, a
            ranked[i] = (ranked[i][0], ranked[i][1],
                         ranked[i][2] + f" · near tie ({abs(a[0] - b[0]):.1f} pts) with {over}: {reason}",
                         ranked[i][3])
            i = max(0, i - 1)
        else:
            i += 1
    best_pair = ranked[0][0]
    for pair, _s, _w, p in ranked:
        # cost of PICKING him now = the best pair minus his pair (0 for the
        # winner; a near-tie runner-up can sit a hair above the winner, so clamp)
        p["_pair"]["pick_cost"] = round(max(0.0, best_pair - pair), 1)
    # keep the original tuple shape; joint value becomes the score the UI sorts by
    return [(pair, why, p) for pair, _s, why, p in ranked]

"""Staged ranking for starter rounds (user design, 2026-09-05 afternoon;
stage 1 re-based on the deadline horizon the same evening, DECISIONS #64).

The pair planner used to be the primary sort and every other rule a tiebreak
inside a one-point window. This inverts it into ordered stages, each deciding
only what the stage before left tied:

  1. POSITION. Over the open-slot markets, the one whose best player is worth
     the most over the player you would otherwise end up with there (the
     deadline fallback). Markets whose best is within VALUE_BAND stay live.
     This used to be one-turn urgency (best now minus the expected best at my
     NEXT pick). That horizon is right only when both positions get filled in
     the next two picks; for QB and TE, which the plan defers to their
     deadline, the three outliers make a one-turn cliff look like an
     emergency: room 10804278 took Allen at 14 (QB urgency 27.7 vs RB 17.3)
     while value had Achane 29 points ahead, and McBride at 27 (TE 14.6 vs WR
     6.4) while value had Rice 8 ahead. Value on the deadline horizon is the
     currency stage 2 already uses, so the position and the player are now
     chosen in the same units.
  2. VALUE picks the player inside the live markets (a FLEX entrant against
     the best flex fallback). Candidates within VALUE_BAND of the best go on.
  3. URGENCY breaks a value tie across markets: if the more urgent market
     loses at least URGENCY_BAND more by waiting one turn, its rows go on
     alone. Same-market ties skip this.
  4. SCARCITY, banded, on survival to my next pick. A gap of SURV_GAP or more
     takes the lower. All under BOTH_GONE (both gone regardless) or all over
     BOTH_STAY (both stay regardless) skips to the pair. Otherwise stage 5.
  5. VARIANCE by round. Through FLOOR_THROUGH_ROUND the higher floor, after it
     the higher ceiling, both over the position's fallback so a tight end and a
     back compare in the same currency (DECISIONS #57). Needs a published
     range on every side or it skips. Within VARIANCE_BAND goes to the pair.
  6. PAIR. Own value plus what the pick leaves at my next turn (planner.pair_rank)
     decides whatever survived 1 to 5.

Exceptions: when my next pick is 0 or 1 picks away (the turn) nobody can be
taken from me, and when no market loses URGENCY_FLOOR by waiting (a flat
board) nothing is urgent either way; in both the pair leads and stages 2 to 5
break ties inside the winning band.

Every row carries `_staged` (the numbers each stage saw) and its `why` ends
with the stage that decided it, so the plan and the trail show the path.
"""

from __future__ import annotations

from typing import Callable

from .boardrow import published_range
from .planner import market_for, own_value, pair_rank
from .snake import FLEX_ELIGIBLE

# One-turn urgency gap that breaks a value tie across markets (stage 3).
URGENCY_BAND = 1.5
# Below this top one-turn urgency nothing is really urgent (a 2-pick window,
# or a flat board): the pair leads, as at the turn (room 10801633 pick 19).
URGENCY_FLOOR = 8.0
# Stage 1 (positions) and stage 2 (players) both tie inside this band.
# Tried at 3.0 on 2026-09-05 17:45 PT to let Javonte (54.7) reach the floor
# rule against Love (57.4): the wider band also pulled Allen (55.1) into
# the tie and the cross-market urgency tiebreak took the QB in round 3
# (DECISIONS #66). Stays 2.0; the user's calls go through engine.prefer.
VALUE_BAND = 2.0
SURV_GAP = 0.15
BOTH_GONE = 0.20
BOTH_STAY = 0.85
FLOOR_THROUGH_ROUND = 7
VARIANCE_BAND = 1.0

Row = tuple[float, str, dict]


def staged_value(p: dict, needs: dict, fallback: dict[str, float] | None) -> float:
    """Stages 1 and 2's number. Slot-conditional: a player entering through the
    FLEX is measured against the best flex-eligible fallback, not his own
    position's."""
    if fallback is None:
        return own_value(p, needs, fallback)
    if market_for(p.get("pos"), needs) == "FLEX":
        fbs = [fallback[q] for q in FLEX_ELIGIBLE if q in fallback]
        if fbs:
            return float(p.get("proj_pts") or 0.0) - max(fbs)
    return own_value(p, needs, fallback)


def survival_of(p: dict, report: dict, needs: dict) -> float:
    """Shown survival to my next pick; a player outside the simulated window
    has no entry and counts as certain to survive."""
    mkt = market_for(p.get("pos"), needs)
    u = report.get(mkt) or report.get(p.get("pos")) or {}
    s = (u.get("survival") or {}).get(str(p.get("sleeper_id")))
    return float(s) if s is not None else 1.0


def variance_key(p: dict, rnd: int, fallback: dict[str, float] | None) -> float | None:
    """Floor through round FLOOR_THROUGH_ROUND, ceiling after, over the
    position's fallback. None without a published range."""
    lo, hi = published_range(p)
    v = lo if rnd <= FLOOR_THROUGH_ROUND else hi
    if v is None:
        return None
    fb = (fallback or {}).get(p.get("pos"))
    return v - float(fb) if fb is not None else v


def _sid(p: dict) -> str:
    return str(p.get("sleeper_id"))


def _name(p: dict) -> str:
    return str(p.get("player") or p.get("name") or p.get("pos"))


def _tag(row: Row, note: str) -> Row:
    return (row[0], row[1] + " · " + note, row[2])


def _steps_2_to_5(rows: list[Row], report: dict, needs: dict, rnd: int,
                  fallback: dict[str, float] | None, pair: Callable[[list[Row]], list[Row]] | None,
                  urg: dict[str, float] | None = None, market_of: dict[str, str] | None = None,
                  ) -> tuple[list[Row], str]:
    """Stages 2 to 5 (and 6 through `pair` when given) over `rows`.
    urg: sleeper_id -> one-turn urgency of the row's market (stage 3).
    Returns (rows in decided order, the deciding stage's note)."""
    val = {_sid(p): staged_value(p, needs, fallback) for _s, _w, p in rows}
    for _s, _w, p in rows:
        p.setdefault("_staged", {})["value"] = round(val[_sid(p)], 1)
    rows = sorted(rows, key=lambda r: -val[_sid(r[2])])
    best_v = val[_sid(rows[0][2])]
    tied = [r for r in rows if best_v - val[_sid(r[2])] <= VALUE_BAND]
    rest = [r for r in rows if best_v - val[_sid(r[2])] > VALUE_BAND]
    rest = [_tag(r, f"staged: value {val[_sid(r[2])]:.1f}, {best_v - val[_sid(r[2])]:.1f} under the best") for r in rest]
    if len(tied) == 1:
        v2 = val[_sid(rest[0][2])] if rest else None
        note = (f"value picked him ({best_v:.1f} vs {v2:.1f} for {_name(rest[0][2])})"
                if v2 is not None else f"value picked him ({best_v:.1f}, nobody else live)")
        return [tied[0]] + rest, note

    # stage 3: one-turn urgency breaks a value tie ACROSS markets
    lead = ""
    if urg and market_of:
        mk = {_sid(p): market_of.get(_sid(p), p.get("pos")) for _s, _w, p in tied}
        by_m: dict[str, float] = {}
        for _s, _w, p in tied:
            by_m[mk[_sid(p)]] = float(urg.get(_sid(p), 0.0) or 0.0)
        if len(by_m) > 1:
            ranked_m = sorted(by_m.items(), key=lambda kv: -kv[1])
            (m0, u0), (m1, u1) = ranked_m[0], ranked_m[1]
            if u0 - u1 >= URGENCY_BAND - 1e-9:
                keep = [r for r in tied if mk[_sid(r[2])] == m0]
                drop = [_tag(r, f"staged: less urgent market ({mk[_sid(r[2])]} {by_m[mk[_sid(r[2])]]:.1f} vs {m0} {u0:.1f})")
                        for r in tied if mk[_sid(r[2])] != m0]
                rest = drop + rest
                tied = keep
                lead = f"value within {VALUE_BAND:g}, {m0} more urgent ({u0:.1f} vs {u1:.1f} for {m1}); "
                if len(tied) == 1:
                    return [tied[0]] + rest, lead + "one row left"

    # stage 4: scarcity, banded
    surv = {_sid(p): survival_of(p, report, needs) for _s, _w, p in tied}
    for _s, _w, p in tied:
        p["_staged"]["surv"] = round(surv[_sid(p)], 3)
    by_s = sorted(tied, key=lambda r: surv[_sid(r[2])])
    s0, s1 = surv[_sid(by_s[0][2])], surv[_sid(by_s[1][2])]
    if s1 - s0 >= SURV_GAP - 1e-9:
        note = lead + f"scarcer first ({s0:.0%} vs {s1:.0%} for {_name(by_s[1][2])}, value within {VALUE_BAND:g})"
        others = [_tag(r, f"staged: less scarce ({surv[_sid(r[2])]:.0%} vs {s0:.0%})") for r in by_s[1:]]
        return [by_s[0]] + others + rest, note
    all_s = [surv[_sid(r[2])] for r in tied]
    if max(all_s) < BOTH_GONE:
        why_skip = f"all gone regardless ({', '.join(f'{s:.0%}' for s in all_s)})"
    elif min(all_s) > BOTH_STAY:
        why_skip = f"all stay regardless ({', '.join(f'{s:.0%}' for s in all_s)})"
    else:
        why_skip = None
    if why_skip is None:
        # stage 5: variance by round
        keys = {_sid(p): variance_key(p, rnd, fallback) for _s, _w, p in tied}
        what = "floor" if rnd <= FLOOR_THROUGH_ROUND else "ceiling"
        if all(k is not None for k in keys.values()):
            for _s, _w, p in tied:
                p["_staged"][what] = round(keys[_sid(p)], 1)
            by_k = sorted(tied, key=lambda r: -keys[_sid(r[2])])
            k0, k1 = keys[_sid(by_k[0][2])], keys[_sid(by_k[1][2])]
            if k0 - k1 > VARIANCE_BAND:
                note = (lead + f"higher {what} over replacement ({k0:.0f} vs {k1:.0f} for {_name(by_k[1][2])}; "
                        f"survival {s0:.0%}-{max(all_s):.0%}, no {SURV_GAP:g} gap)")
                others = [_tag(r, f"staged: lower {what} ({keys[_sid(r[2])]:.0f} vs {k0:.0f})") for r in by_k[1:]]
                return [by_k[0]] + others + rest, note
            why_skip = f"{what}s within {VARIANCE_BAND:g} ({k0:.0f} vs {k1:.0f})"
        else:
            why_skip = f"no published range to compare {what}s"
    if pair is None:
        # exception path: the pair already led; keep its order
        return tied + rest, lead + f"pair order stands ({why_skip})"
    ranked = pair(tied)
    note = lead + f"pair decided ({why_skip})"
    # A dead-heat pair (same position, same partner: the pair cannot separate
    # them, and its own near-tie rule would read the floor in any round) falls
    # back to the ROUND's variance rule: floor through FLOOR_THROUGH_ROUND,
    # ceiling after.
    top = ranked[0][0]
    heat = [r for r in ranked if top - r[0] <= VARIANCE_BAND]
    if len(heat) > 1:
        keys = {_sid(p): variance_key(p, rnd, fallback) for _s, _w, p in heat}
        if all(k is not None for k in keys.values()):
            what = "floor" if rnd <= FLOOR_THROUGH_ROUND else "ceiling"
            by_k = sorted(heat, key=lambda r: -keys[_sid(r[2])])
            k0, k1 = keys[_sid(by_k[0][2])], keys[_sid(by_k[1][2])]
            if k0 - k1 > VARIANCE_BAND:
                for _s, _w, p in heat:
                    p["_staged"][what] = round(keys[_sid(p)], 1)
                ranked = by_k + ranked[len(heat):]
                note = (lead + f"pair tied within {VARIANCE_BAND:g} ({why_skip}); higher {what} over replacement "
                        f"({k0:.0f} vs {k1:.0f} for {_name(by_k[1][2])})")
    others = [_tag(r, "staged: lower pair") for r in ranked[1:]]
    return [ranked[0]] + others + rest, note


# kept for callers and tests that import the old name
_steps_2_to_4 = _steps_2_to_5


def staged_rank(cands: list[Row], report: dict | None, needs: dict, rnd: int,
                urgency_of: dict[str, float], market_of: dict[str, str],
                second_best_now: dict[str, float], eligible_after: Callable[[str], set[str]],
                fallback: dict[str, float] | None = None, repl: dict[str, float] | None = None,
                partner_certain: bool = False, tie_break: str = "scarcity", tie_window: float = 1.0,
                ) -> list[Row]:
    """Rank starter-round candidates by the stages. cands: rows over the open
    markets, (greedy score, why, player). urgency_of: market -> one-turn
    urgency. market_of: sleeper_id -> the market the row was built in."""
    for _s, _w, p in cands:
        p.pop("_staged", None)
        p.pop("_pair", None)

    def pair(rows: list[Row]) -> list[Row]:
        return pair_rank(list(rows), report, needs, second_best_now, eligible_after,
                         fallback=fallback, repl=repl, partner_certain=partner_certain,
                         tie_break=tie_break, tie_window=tie_window)

    if not report or len(cands) < 2:
        return pair(cands)

    mk = {_sid(p): market_of.get(_sid(p), p.get("pos")) for _s, _w, p in cands}
    urg = {_sid(p): float(urgency_of.get(mk[_sid(p)], 0.0) or 0.0) for _s, _w, p in cands}
    top_u = max(urg.values())
    val = {_sid(p): staged_value(p, needs, fallback) for _s, _w, p in cands}
    for _s, _w, p in cands:
        st = p.setdefault("_staged", {})
        st["urgency"] = round(urg[_sid(p)], 1)
        st["market"] = mk[_sid(p)]
        st["value"] = round(val[_sid(p)], 1)

    flat = top_u < URGENCY_FLOOR
    if partner_certain or flat:
        # the turn (no rival between this pick and my next) or a flat board
        # (nothing loses more than URGENCY_FLOOR by waiting): the pair leads
        # and stages 2 to 5 settle the winning band
        mode = "turn" if partner_certain else "flat"
        ranked = pair(cands)
        top = ranked[0][0]
        tied = [r for r in ranked if top - r[0] <= VALUE_BAND]
        rest = [_tag(r, f"staged: pair {r[0]:.1f}, {top - r[0]:.1f} under the best") for r in ranked if top - r[0] > VALUE_BAND]
        for _s, _w, p in cands:
            p["_staged"]["mode"] = mode
        label = "STAGED (turn)" if partner_certain else f"STAGED (flat: top urgency {top_u:.1f} under {URGENCY_FLOOR:g})"
        if len(tied) == 1:
            out = [_tag(tied[0], f"{label}: pair picked him ({top:.1f})")] + rest
            return out
        ordered, note = _steps_2_to_5(tied, report, needs, rnd, fallback, pair=None, urg=urg, market_of=mk)
        head = _tag(ordered[0], f"{label}: pair band of {len(tied)}, then {note}")
        return [head] + ordered[1:] + rest

    # stage 1: the position, by the best deadline-horizon value in each
    # market. Live = best within VALUE_BAND of the top market's best.
    best_by_m: dict[str, float] = {}
    for _s, _w, p in cands:
        m = mk[_sid(p)]
        best_by_m[m] = max(best_by_m.get(m, float("-inf")), val[_sid(p)])
    top_m, top_v = max(best_by_m.items(), key=lambda kv: kv[1])
    for _s, _w, p in cands:
        p["_staged"]["market_best"] = round(best_by_m[mk[_sid(p)]], 1)

    def _live(m: str) -> bool:
        return top_v - best_by_m[m] <= VALUE_BAND
    live = [c for c in cands if _live(mk[_sid(c[2])])]
    dead = sorted((c for c in cands if not _live(mk[_sid(c[2])])),
                  key=lambda c: (-best_by_m[mk[_sid(c[2])]], -val[_sid(c[2])]))
    dead = [_tag(c, f"staged: not live, {mk[_sid(c[2])]} best value {best_by_m[mk[_sid(c[2])]]:.1f} vs "
                    f"{top_v:.1f} at the top (band {VALUE_BAND:g}); one-turn urgency {urg[_sid(c[2])]:.1f}") for c in dead]
    live_mkts = sorted({mk[_sid(c[2])] for c in live})
    next_m = max(((m, v) for m, v in best_by_m.items() if m not in live_mkts), key=lambda kv: kv[1], default=None)
    lead = (f"value picked {'/'.join(live_mkts)} ({top_v:.1f}"
            + (f", next {next_m[0]} {next_m[1]:.1f}" if next_m else "")
            + f"; one-turn urgency {urg[_sid(live[0][2])]:.1f}, top {top_u:.1f})")
    if len(live) == 1:
        head = _tag(live[0], f"STAGED: {lead}, one row live")
        return [head] + dead
    ordered, note = _steps_2_to_5(live, report, needs, rnd, fallback, pair=pair, urg=urg, market_of=mk)
    head = _tag(ordered[0], f"STAGED: {lead}; {note}")
    return [head] + ordered[1:] + dead

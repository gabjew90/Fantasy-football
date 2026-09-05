"""Staged ranking for starter rounds (user design, 2026-09-05 afternoon).

The pair planner used to be the primary sort and every other rule a tiebreak
inside a one-point window. This inverts it into five ordered stages, each
deciding only what the stage before left tied:

  1. URGENCY picks the position. Over the open-slot markets, the one where
     waiting costs the most; markets within URGENCY_BAND of the top stay live.
  2. VALUE picks the player. Inside the live markets, points above the player
     you would otherwise end up with (a FLEX entrant against the best flex
     fallback). Candidates within VALUE_BAND of the best go on.
  3. SCARCITY, banded, on survival to my next pick. A gap of SURV_GAP or more
     takes the lower. All under BOTH_GONE (both gone regardless) or all over
     BOTH_STAY (both stay regardless) skips to the pair. Otherwise stage 4.
  4. VARIANCE by round. Through FLOOR_THROUGH_ROUND the higher floor, after it
     the higher ceiling, both over the position's fallback so a tight end and a
     back compare in the same currency (DECISIONS #57). Needs a published
     range on every side or it skips. Within VARIANCE_BAND goes to the pair.
  5. PAIR. Own value plus what the pick leaves at my next turn (planner.pair_rank)
     decides whatever survived 1 to 4.

Exception: when my next pick is 0 or 1 picks away (the turn), urgency is
degenerate because everyone survives the empty window, so the pair leads and
stages 2 to 4 break ties inside the winning band.

Every row carries `_staged` (the numbers each stage saw) and its `why` ends
with the stage that decided it, so the plan and the trail show the path.
"""

from __future__ import annotations

from typing import Callable

from .boardrow import published_range
from .planner import market_for, own_value, pair_rank
from .snake import FLEX_ELIGIBLE

URGENCY_BAND = 1.5
VALUE_BAND = 2.0
SURV_GAP = 0.15
BOTH_GONE = 0.20
BOTH_STAY = 0.85
FLOOR_THROUGH_ROUND = 7
VARIANCE_BAND = 1.0

Row = tuple[float, str, dict]


def staged_value(p: dict, needs: dict, fallback: dict[str, float] | None) -> float:
    """Stage 2's number. Slot-conditional: a player entering through the FLEX
    is measured against the best flex-eligible fallback, not his own position's."""
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


def _steps_2_to_4(rows: list[Row], report: dict, needs: dict, rnd: int,
                  fallback: dict[str, float] | None, pair: Callable[[list[Row]], list[Row]] | None,
                  ) -> tuple[list[Row], str]:
    """Stages 2, 3, 4 (and 5 through `pair` when given) over `rows`.
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

    # stage 3: scarcity, banded
    surv = {_sid(p): survival_of(p, report, needs) for _s, _w, p in tied}
    for _s, _w, p in tied:
        p["_staged"]["surv"] = round(surv[_sid(p)], 3)
    by_s = sorted(tied, key=lambda r: surv[_sid(r[2])])
    s0, s1 = surv[_sid(by_s[0][2])], surv[_sid(by_s[1][2])]
    if s1 - s0 >= SURV_GAP - 1e-9:
        note = f"scarcer first ({s0:.0%} vs {s1:.0%} for {_name(by_s[1][2])}, value within {VALUE_BAND:g})"
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
        # stage 4: variance by round
        keys = {_sid(p): variance_key(p, rnd, fallback) for _s, _w, p in tied}
        what = "floor" if rnd <= FLOOR_THROUGH_ROUND else "ceiling"
        if all(k is not None for k in keys.values()):
            for _s, _w, p in tied:
                p["_staged"][what] = round(keys[_sid(p)], 1)
            by_k = sorted(tied, key=lambda r: -keys[_sid(r[2])])
            k0, k1 = keys[_sid(by_k[0][2])], keys[_sid(by_k[1][2])]
            if k0 - k1 > VARIANCE_BAND:
                note = (f"higher {what} over replacement ({k0:.0f} vs {k1:.0f} for {_name(by_k[1][2])}; "
                        f"survival {s0:.0%}-{max(all_s):.0%}, no {SURV_GAP:g} gap)")
                others = [_tag(r, f"staged: lower {what} ({keys[_sid(r[2])]:.0f} vs {k0:.0f})") for r in by_k[1:]]
                return [by_k[0]] + others + rest, note
            why_skip = f"{what}s within {VARIANCE_BAND:g} ({k0:.0f} vs {k1:.0f})"
        else:
            why_skip = f"no published range to compare {what}s"
    if pair is None:
        # exception path: the pair already led; keep its order
        return tied + rest, f"pair order stands ({why_skip})"
    ranked = pair(tied)
    note = f"pair decided ({why_skip})"
    others = [_tag(r, "staged: lower pair") for r in ranked[1:]]
    return [ranked[0]] + others + rest, note


def staged_rank(cands: list[Row], report: dict | None, needs: dict, rnd: int,
                urgency_of: dict[str, float], market_of: dict[str, str],
                second_best_now: dict[str, float], eligible_after: Callable[[str], set[str]],
                fallback: dict[str, float] | None = None, repl: dict[str, float] | None = None,
                partner_certain: bool = False, tie_break: str = "scarcity", tie_window: float = 1.0,
                ) -> list[Row]:
    """Rank starter-round candidates by the five stages. cands: one row per
    open market, (greedy score, why, player). urgency_of: market -> urgency.
    market_of: sleeper_id -> the market the row was built in."""
    for _s, _w, p in cands:
        p.pop("_staged", None)
        p.pop("_pair", None)

    def pair(rows: list[Row]) -> list[Row]:
        return pair_rank(list(rows), report, needs, second_best_now, eligible_after,
                         fallback=fallback, repl=repl, partner_certain=partner_certain,
                         tie_break=tie_break, tie_window=tie_window)

    if not report or len(cands) < 2:
        return pair(cands)

    if partner_certain:
        # the turn: no rival between this pick and my next, urgency is empty,
        # the pair leads and stages 2 to 4 settle the winning band
        ranked = pair(cands)
        top = ranked[0][0]
        tied = [r for r in ranked if top - r[0] <= VALUE_BAND]
        rest = [_tag(r, f"staged: pair {r[0]:.1f}, {top - r[0]:.1f} under the best") for r in ranked if top - r[0] > VALUE_BAND]
        for _s, _w, p in cands:
            p.setdefault("_staged", {})["mode"] = "turn"
        if len(tied) == 1:
            out = [_tag(tied[0], f"STAGED (turn): pair picked him ({top:.1f})")] + rest
            return out
        ordered, note = _steps_2_to_4(tied, report, needs, rnd, fallback, pair=None)
        head = _tag(ordered[0], f"STAGED (turn): pair band of {len(tied)}, then {note}")
        return [head] + ordered[1:] + rest

    # stage 1: urgency picks the position
    urg = {_sid(p): float(urgency_of.get(market_of.get(_sid(p), p.get("pos")), 0.0) or 0.0)
           for _s, _w, p in cands}
    top_u = max(urg.values())
    for _s, _w, p in cands:
        p.setdefault("_staged", {})["urgency"] = round(urg[_sid(p)], 1)
        p["_staged"]["market"] = market_of.get(_sid(p), p.get("pos"))
    live = [c for c in cands if top_u - urg[_sid(c[2])] <= URGENCY_BAND]
    dead = sorted((c for c in cands if top_u - urg[_sid(c[2])] > URGENCY_BAND),
                  key=lambda c: -urg[_sid(c[2])])
    dead = [_tag(c, f"staged: not live, {market_of.get(_sid(c[2]), c[2].get('pos'))} urgency "
                    f"{urg[_sid(c[2])]:.1f} vs {top_u:.1f} at the top") for c in dead]
    live_mkts = sorted({market_of.get(_sid(c[2]), c[2].get("pos")) for c in live})
    lead = (f"urgency picked {'/'.join(live_mkts)} ({top_u:.1f}"
            + (f", next {max(urg[_sid(d[2])] for d in dead):.1f}" if dead else "")
            + ")")
    if len(live) == 1:
        head = _tag(live[0], f"STAGED: {lead}, one market live")
        return [head] + dead
    ordered, note = _steps_2_to_4(live, report, needs, rnd, fallback, pair=pair)
    head = _tag(ordered[0], f"STAGED: {lead}; {note}")
    return [head] + ordered[1:] + dead

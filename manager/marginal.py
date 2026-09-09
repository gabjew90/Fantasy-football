"""Marginal roster value: what a move actually costs and gains.

A player's projection is what he scores. It is NOT what he is worth to you,
because when he leaves somebody replaces him. The two numbers diverge wildly:
on the 2026-09-06 Keefamania roster Michael Wilson projected 134.6 and cost 0
to lose (he never starts and the next man up is as good), while Sam LaPorta
projected 146.2 and cost the full 146.2 (only tight end, nothing behind him).
Nearly identical on a projection sheet, opposite in reality.

Everything here is a DIFFERENCE of two optimal lineups, so the projection
baseline cancels and only the shape of the roster matters.

Players are the roster dicts the manager already passes around: `sleeper_id`,
`pos`, and a value key (default `weekly`, the same key `optimal_lineup` sorts
on). Pass `key="ros"` to price a rest-of-season trade instead of one week.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from draftkit.lineup import optimal_lineup

log = logging.getLogger("manager")


def _pid(p: dict) -> str:
    return str(p["sleeper_id"])


def starters(roster: list[dict], shape: dict, key: str = "weekly") -> list[dict]:
    """The best legal lineup, as rows scored on `key`.

    Rows come back carrying `weekly` set to the `key` value, because that is
    what the optimiser sorted on and a caller printing a different number
    beside a lineup it did not choose is how a brief lies quietly.
    """
    if key != "weekly":
        roster = [dict(p, weekly=(p.get(key) or 0.0)) for p in roster]
    return optimal_lineup(roster, shape["slots"], shape.get("flex", 0),
                          flex_slots=shape.get("flex_slots"))


def lineup_points(roster: list[dict], shape: dict, key: str = "weekly") -> float:
    """Points of the best legal lineup this roster can field."""
    return round(sum((p.get("weekly") or 0.0)
                     for p in starters(roster, shape, key)), 1)


def slot_moves(roster: list[dict], shape: dict, *, arriving=(), departing=(),
               key: str = "weekly") -> dict:
    """Re-solve the lineup around a trade and say which seats actually moved.

    THE POINT IS THE PROMOTIONS. A package's effect is not "these two left
    and these two arrived" -- the lineup re-solves globally, so losing two
    receivers can pull a running back up off the bench into a flex, and that
    promotion is a real part of the price. In the 2026-09-08 vincenzo31
    package three players left their lineup and three entered, one of whom
    (Rico Dowdle) was not in the trade at all. A summary that omits him
    cannot explain where their +13.6 came from.

    Returns the before/after lineups plus four disjoint movement lists:
      departed  started, and left in the trade
      benched   started, still rostered, no longer starts (squeezed out)
      arrived   came in the trade and starts
      promoted  already rostered and on the bench, now starts
    """
    dep = {_pid(p) for p in departing}
    arr = {_pid(p) for p in arriving}
    after_roster = [p for p in roster if _pid(p) not in dep] + list(arriving)
    before = starters(roster, shape, key)
    after = starters(after_roster, shape, key)
    b_ids = {_pid(p) for p in before}
    a_ids = {_pid(p) for p in after}
    tb = round(sum((p.get("weekly") or 0.0) for p in before), 1)
    ta = round(sum((p.get("weekly") or 0.0) for p in after), 1)
    return {
        "before": before, "after": after,
        "total_before": tb, "total_after": ta, "delta": round(ta - tb, 1),
        "departed": [p for p in before if _pid(p) in dep],
        "benched": [p for p in before if _pid(p) not in a_ids and _pid(p) not in dep],
        "arrived": [p for p in after if _pid(p) in arr],
        "promoted": [p for p in after if _pid(p) not in b_ids and _pid(p) not in arr],
    }


def cost_to_lose(roster: list[dict], player, shape: dict, key: str = "weekly") -> float:
    """Lineup points lost if `player` leaves, AFTER the slot is refilled.

    Zero means the roster does not miss him at all. That is the single most
    useful fact in a trade negotiation and no projection sheet shows it.
    """
    pid = player if isinstance(player, str) else _pid(player)
    before = lineup_points(roster, shape, key)
    after = lineup_points([p for p in roster if _pid(p) != pid], shape, key)
    return round(before - after, 1)


def gain_to_add(roster: list[dict], player: dict, shape: dict,
                key: str = "weekly") -> float:
    """Lineup points gained if `player` joins. Zero means he never starts."""
    before = lineup_points(roster, shape, key)
    after = lineup_points(roster + [player], shape, key)
    return round(after - before, 1)


@dataclass
class Deal:
    """Both sides of a package, in lineup points rather than projections.

    `market` is the optional FantasyCalc second opinion (manager.market.price).
    It is carried, never blended: the two measure different things, and the
    interesting deals are exactly the ones where they disagree. Averaging them
    would hide the signal.
    """
    mine_before: float
    mine_after: float
    theirs_before: float
    theirs_after: float
    give: list[str] = field(default_factory=list)
    get: list[str] = field(default_factory=list)
    market: dict | None = None
    my_moves: dict | None = None
    their_moves: dict | None = None

    @property
    def my_delta(self) -> float:
        return round(self.mine_after - self.mine_before, 1)

    @property
    def their_delta(self) -> float:
        return round(self.theirs_after - self.theirs_before, 1)

    @property
    def mutual(self) -> bool:
        """Both lineups improve. Rare, and the only kind that gets accepted
        without someone having to be talked into it."""
        return self.my_delta > 0 and self.their_delta > 0

    @property
    def market_delta(self) -> int | None:
        return None if not self.market else int(self.market["delta"])

    @property
    def disputed(self) -> bool:
        """Lineup points and the market point opposite ways.

        Worth surfacing rather than resolving. When this fired on the
        2026-09-08 Barkley package the lineup model said -10.0 and the market
        said +1263, and the market was reading an age gap and a tight-end
        ranking the projections did not carry.
        """
        m = self.market_delta
        return m is not None and self.my_delta != 0 and (m > 0) != (self.my_delta > 0)

    def __str__(self) -> str:
        s = (f"give {', '.join(self.give) or '-'} / get {', '.join(self.get) or '-'}: "
             f"me {self.my_delta:+.1f}, them {self.their_delta:+.1f}")
        if self.market:
            s += f", {_market_mod().annotate(self.market)}"
            if self.disputed:
                s += "  ⚠ lineup points and market disagree"
        return s


def _market_mod():
    from . import market
    return market


def price(my_roster: list[dict], their_roster: list[dict],
          give: list[dict], get: list[dict], shape: dict,
          their_shape: dict | None = None, key: str = "weekly",
          market_values: dict[str, int] | None = None) -> Deal:
    """Price a package from both sides at once.

    `shape` is {slots, flex, flex_slots}. `their_shape` defaults to the same,
    which is right within one league and wrong across two.

    `market_values` is an optional {sleeper_id: value} map from
    manager.market.values(). Pure lookup -- this module does no I/O, so the
    caller owns the fetch and the cache.
    """
    their_shape = their_shape or shape
    mkt = None
    if market_values:
        from . import market as market_mod
        mkt = market_mod.price(market_values, give, get)
    # Both sides re-solve. slot_moves carries the totals, so the deltas and
    # the seat-by-seat story cannot drift apart the way they would if the
    # points were computed here and the movements somewhere else.
    mine = slot_moves(my_roster, shape, arriving=get, departing=give, key=key)
    theirs = slot_moves(their_roster, their_shape, arriving=give,
                        departing=get, key=key)
    return Deal(
        mine_before=mine["total_before"], mine_after=mine["total_after"],
        theirs_before=theirs["total_before"], theirs_after=theirs["total_after"],
        give=[p.get("name", _pid(p)) for p in give],
        get=[p.get("name", _pid(p)) for p in get],
        market=mkt, my_moves=mine, their_moves=theirs,
    )


def explain(deal: Deal, me: str = "you", them: str = "them") -> str:
    """The seat-by-seat walkthrough, both sides, as a brief would print it."""
    def side(label, mv, delta):
        if not mv:
            return []
        out = [f"{label}: {mv['total_before']:.1f} -> {mv['total_after']:.1f} "
               f"({delta:+.1f})"]
        for tag, rows in (("out (traded)", mv["departed"]),
                          ("out (squeezed to bench)", mv["benched"]),
                          ("in  (from the trade)", mv["arrived"]),
                          ("in  (PROMOTED off the bench)", mv["promoted"])):
            for p in rows:
                out.append(f"    {tag:30s} {p.get('pos', '?'):3s} "
                           f"{p.get('name', '?')} {p.get('weekly') or 0:.1f}")
        return out

    lines = [f"give {', '.join(deal.give) or '-'}  /  get {', '.join(deal.get) or '-'}", ""]
    lines += side(me, deal.my_moves, deal.my_delta)
    lines.append("")
    lines += side(them, deal.their_moves, deal.their_delta)
    if deal.market:
        from . import market as market_mod
        lines += ["", market_mod.annotate(deal.market)]
        if deal.disputed:
            lines.append("⚠ lineup points and the market disagree")
    return "\n".join(lines)


def dead_weight(roster: list[dict], shape: dict, key: str = "weekly") -> list[dict]:
    """Players who cost nothing to lose, worst first.

    These are not cheap trade chips. Nobody else's lineup improves from them
    either, which is why offering them as a sweetener buys precisely nothing.
    """
    out = [{"player": p, "cost": cost_to_lose(roster, p, shape, key),
            "proj": round(p.get(key) or 0.0, 1)}
           for p in roster]
    return sorted((r for r in out if r["cost"] <= 0.0), key=lambda r: -r["proj"])


def tradeable(roster: list[dict], others: dict, shape: dict,
              key: str = "weekly") -> list[dict]:
    """Rank my roster by demand against cost.

    `others` is {owner -> roster}. `buyers` counts how many rival lineups
    actually improve; a player nobody's lineup wants has no market whatever
    his projection says.
    """
    rows = []
    for p in roster:
        cost = cost_to_lose(roster, p, shape, key)
        gains = [(gain_to_add(r, p, shape, key), who) for who, r in others.items()]
        best = max(gains) if gains else (0.0, None)
        rows.append({
            "player": p, "proj": round(p.get(key) or 0.0, 1), "cost": cost,
            "buyers": sum(1 for g, _ in gains if g > 0),
            "best_gain": best[0], "best_buyer": best[1],
            # None reads as "free": no denominator, not a missing number
            "ratio": round(best[0] / cost, 2) if cost > 0 else None,
        })

    # FREE AND WANTED IS THE TOP OF THIS LIST, NOT THE BOTTOM.
    #
    # `ratio` is None when the player costs nothing to lose, and the old key
    # coerced that None to 0, which sorted every free asset BELOW anything
    # with a positive ratio: cost 0 / gain 20 scored (0, -20) and lost to
    # cost 5 / gain 10 at (-2.0, -10). A player your lineup does not miss who
    # improves a rival's by 20 is the best chip on the board -- an infinite
    # ratio, not a zero one -- and this function is the one that answers
    # "who are my most tradeable assets".
    def rank(r):
        free_and_wanted = r["cost"] <= 0 and r["best_gain"] > 0
        return (0 if free_and_wanted else 1, -(r["ratio"] or 0), -r["best_gain"])

    return sorted(rows, key=rank)

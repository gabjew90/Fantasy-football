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
    """Identity. Loud on a malformed row -- a player silently keyed as None
    would collide with every other unidentified row and quietly corrupt the
    movement sets -- but loud with the row in the message, not a bare
    KeyError from three frames down."""
    try:
        return str(p["sleeper_id"])
    except (KeyError, TypeError, IndexError):
        # The handler must not throw. Building the message with p.items()
        # raised AttributeError for a str, int or list -- an error ABOUT the
        # bad row, replaced by an unrelated error about the error, which is
        # strictly worse than the bare KeyError it was meant to improve on.
        try:
            shown = repr(dict(list(p.items())[:4]))
        except AttributeError:
            shown = f"{type(p).__name__} {p!r}"
        raise KeyError(
            f"roster row has no usable sleeper_id, so it cannot be tracked "
            f"through a lineup change: {shown}") from None


def starters(roster: list[dict], shape: dict, key: str = "weekly") -> list[dict]:
    """The best legal lineup, as rows scored on `key`.

    ALWAYS COPIES, so the contract does not change with an argument. It used
    to return the caller's own dicts on the default key and copies on any
    other, which meant mutating a returned row edited the roster in one mode
    and silently did nothing in the other. Measured the difference before
    paying for it: 10.2us per solve becomes 13.3us, about 1.2 seconds across
    a 93,730-package frontier search. Cheap enough for one contract.

    The returned rows are a VIEW: `weekly` carries the `key` value, because
    that is what the optimiser sorted on and printing a different number
    beside a lineup it did not choose is how a brief lies quietly. Edits to
    them go nowhere.
    """
    scored = [dict(p, weekly=(p.get(key) or 0.0)) for p in roster]
    return optimal_lineup(scored, shape["slots"], shape.get("flex", 0),
                          flex_slots=shape.get("flex_slots"))


def lineup_points(roster: list[dict], shape: dict, key: str = "weekly") -> float:
    """Points of the best legal lineup this roster can field."""
    return round(sum((p.get("weekly") or 0.0)
                     for p in starters(roster, shape, key)), 1)


def slot_moves(roster: list[dict], shape: dict, *, arriving=(), departing=(),
               filled=(), key: str = "weekly") -> dict:
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
      backfilled  a waiver pickup for a spot the trade opened, and starts
      promoted  already rostered and on the bench, now starts

    `filled` is kept apart from `arriving` because a waiver body reported as
    "in (from the trade)" is a lie the reader cannot check -- it was not in
    the package and the other manager never saw it.
    """
    # MATERIALISE BEFORE ITERATING TWICE. `arriving` was read once to build
    # the id set and again to build the post-trade roster; a generator is
    # exhausted by the first pass, so the incoming players silently vanished
    # and the deal priced at 0 with no error. A list caller got +500 for the
    # same package a generator caller got 0 for.
    arriving = list(arriving)
    departing = list(departing)
    filled = list(filled)
    dep = {_pid(p) for p in departing}
    arr = {_pid(p) for p in arriving}
    bf = {_pid(p) for p in filled}
    # A player on both sides is not a trade, and counting him as departed AND
    # arrived would break the disjointness the four lists promise.
    both = dep & arr
    if both:
        raise ValueError(
            f"the same player is both arriving and departing: {sorted(both)}")
    after_roster = [p for p in roster if _pid(p) not in dep] + arriving + filled
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
        "backfilled": [p for p in after if _pid(p) in bf],
        "promoted": [p for p in after if _pid(p) not in b_ids
                     and _pid(p) not in arr and _pid(p) not in bf],
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
    my_backfill: list[str] = field(default_factory=list)
    their_backfill: list[str] = field(default_factory=list)

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


def backfill(n: int, waivers, key: str = "weekly", exclude=()) -> list[dict]:
    """The best `n` free agents, for roster spots a package leaves open.

    NOT a replacement baseline. Bench players are already in the pool the
    optimiser solves over, so a departing starter is covered by the bench
    automatically. This is narrower: a 2-for-1 sends more bodies than it
    receives and opens a SPOT, and that spot is filled by Tuesday. Pricing
    it at zero understates every consolidation.
    """
    if n <= 0 or not waivers:
        return []
    skip = {_pid(p) for p in exclude}
    pool = [p for p in waivers if _pid(p) not in skip]
    return sorted(pool, key=lambda p: -(p.get(key) or 0.0))[:n]


def _fill_for(arriving, departing, waivers, key: str = "weekly") -> list[dict]:
    """The backfill one side of a package earns. ONE definition.

    price(), depth_risk() and thin_after() each derived this independently
    and happened to agree; a change to the exclude semantics would have had
    to land in three places, only one of which the price() tests cover.
    """
    arriving, departing = list(arriving), list(departing)
    return backfill(len(departing) - len(arriving), waivers, key,
                    exclude=arriving + departing)


def price(my_roster: list[dict], their_roster: list[dict],
          give: list[dict], get: list[dict], shape: dict,
          their_shape: dict | None = None, key: str = "weekly",
          market_values: dict[str, int] | None = None,
          waivers: list[dict] | None = None) -> Deal:
    """Price a package from both sides at once.

    `shape` is {slots, flex, flex_slots}. `their_shape` defaults to the same,
    which is right within one league and wrong across two.

    `market_values` is an optional {sleeper_id: value} map from
    manager.market.values(). Pure lookup -- this module does no I/O, so the
    caller owns the fetch and the cache.

    `waivers` is the free-agent pool. Whichever side sends more bodies than
    it receives gets its opened spots filled from it, because that side will
    have filled them by Tuesday and a spot priced at zero makes every
    consolidation look worse than it is.
    """
    their_shape = their_shape or shape
    mkt = None
    if market_values:
        from . import market as market_mod
        mkt = market_mod.price(market_values, give, get)
    my_fill = _fill_for(get, give, waivers, key)
    their_fill = _fill_for(give, get, waivers, key)
    # Both sides re-solve. slot_moves carries the totals, so the deltas and
    # the seat-by-seat story cannot drift apart the way they would if the
    # points were computed here and the movements somewhere else.
    mine = slot_moves(my_roster, shape, arriving=get, departing=give,
                      filled=my_fill, key=key)
    theirs = slot_moves(their_roster, their_shape, arriving=give,
                        departing=get, filled=their_fill, key=key)
    return Deal(
        mine_before=mine["total_before"], mine_after=mine["total_after"],
        theirs_before=theirs["total_before"], theirs_after=theirs["total_after"],
        give=[p.get("name", _pid(p)) for p in give],
        get=[p.get("name", _pid(p)) for p in get],
        market=mkt, my_moves=mine, their_moves=theirs,
        my_backfill=[p.get("name", _pid(p)) for p in my_fill],
        their_backfill=[p.get("name", _pid(p)) for p in their_fill],
    )


def depth_risk(roster: list[dict], shape: dict, pos: str, *, arriving=(),
               departing=(), waivers=None, key: str = "weekly") -> dict:
    """How much worse an injury at `pos` gets because of this trade.

    Remove the best player at that position from BOTH the before and after
    pools and compare the drops. The point is that a package which looks
    even on the starting lineup can quietly sell the depth behind it, and
    the replacement for a week-12 injury is not the bench body you traded
    away -- it is whoever is on waivers that week. So the injured pool is
    topped up from waivers, not from a bench that no longer exists.
    """
    dep = {_pid(p) for p in departing}
    fill = backfill(len(list(departing)) - len(list(arriving)), waivers, key,
                    exclude=list(arriving) + list(departing))
    after_roster = [p for p in roster if _pid(p) not in dep] + \
        list(arriving) + fill

    def drop(pool):
        # NO WAIVER TOP-UP HERE. An injury does not open a roster spot, so
        # the replacement is whoever is already on the roster. The waiver
        # body belongs in `after_roster` only, where the TRADE opened the
        # spot -- and it is already there. Adding one inside this function
        # topped up the BEFORE pool too, which has lost nothing and needs
        # nothing, and that erased the difference the replay exists to
        # measure: a 2-for-1 that plainly sold depth reported extra 0.0.
        at_pos = [p for p in pool if p.get("pos") == pos]
        if not at_pos:
            return 0.0, None
        star = max(at_pos, key=lambda p: (p.get(key) or 0.0))
        healthy = lineup_points(pool, shape, key)
        hurt_pool = [p for p in pool if _pid(p) != _pid(star)]
        return round(healthy - lineup_points(hurt_pool, shape, key), 1), star

    before_drop, before_star = drop(roster)
    after_drop, after_star = drop(after_roster)
    return {"pos": pos, "before_drop": before_drop, "after_drop": after_drop,
            "extra": round(after_drop - before_drop, 1),
            "before_star": (before_star or {}).get("name"),
            "after_star": (after_star or {}).get("name")}


# GATE 2 IS ABOUT ACCEPTANCE, NOT TRUTH. Most managers evaluate a trade by
# name recognition and draft cost, not by their own optimal lineup, so a
# package can be good for them and still be refused. Below this share of the
# value they are giving up, expect a no whatever the points say.
MARKET_FLOOR = 0.90
# ...and a ceiling, which the source framework did not have. Its floor only
# protects against THEM saying no. Nothing stopped a package that improved my
# lineup by 2.6 season points while handing over 559% of the market value I
# got back -- 250 of 460 "passing" Omnibeta packages had me overpaying by
# more than 15%, and 119 by more than 50%. Lineup points are this week;
# market value is every trade after it.
MARKET_CEILING = 1.15
# Gate 3 REPORTS BUT DOES NOT BLOCK (turned off 2026-09-09 on the user's
# call). Leaving a required slot without cover is a real cost and the
# warning still names the position, but whether it is disqualifying depends
# on things the model does not hold -- how thin the wire is that week,
# whether an IR slot is free, how much the lineup gain is worth against a
# tail risk. That is a manager's call, not a constant's. Flip to True and
# every gate-3 failure becomes a hard no again.
DEPTH_BLOCKS = False
# And below this the lineup edge is inside projection error, so you are
# paying transaction risk for nothing.
#
# ZERO WHILE WE HAVE NO EVIDENCE FOR A NUMBER. The framework this came from
# suggests 1.0 PPG, which is plausible and would currently reject the
# Javonte + Fannin package (+13.0 season = +0.76 ppg). But a threshold is a
# claim about projection error, and nothing here has measured it -- shipping
# 1.0 would be a guess wearing a decimal point, and DECISIONS says a
# predicted delta is not a measured one. So the gate starts at zero, every
# deal reports its own ppg, and the number gets raised when a backtest says
# what it should be.
EDGE_PPG = 0.0


def thin_after(roster: list[dict], shape: dict, *, arriving=(), departing=(),
               waivers=None, key: str = "weekly") -> list[str]:
    """Positions where, after this trade, ONE injury empties a required slot.

    Not a judgement call and not a threshold -- a structural fact. A wide
    receiver cannot legally occupy a tight end slot, so a roster holding
    exactly as many tight ends as it must start has no cover at all. That is
    what the cbarone package does: it takes the second tight end and leaves
    Warren alone, so losing him costs the whole 201.4 rather than the 52.0 it
    costs today, when Fannin slides up from the flex and Deebo backfills it.

    Waivers count, because the spot a 2-for-1 opens gets filled by Tuesday --
    but only against positions the wire actually covers.
    """
    dep = {_pid(p) for p in departing}
    fill = _fill_for(arriving, departing, waivers, key)
    after = [p for p in roster if _pid(p) not in dep] + list(arriving) + fill
    held: dict[str, int] = {}
    for p in after:
        held[p.get("pos")] = held.get(p.get("pos"), 0) + 1
    return sorted(pos for pos, need in (shape.get("slots") or {}).items()
                  if need and held.get(pos, 0) <= need)


def newly_thin(roster: list[dict], shape: dict, *, arriving=(), departing=(),
               waivers=None, key: str = "weekly") -> list[str]:
    """Positions THIS TRADE leaves without cover, ignoring ones already bare.

    thin_after is a state query and answers honestly: a one-QB league rosters
    one quarterback, a kicker and a defense are streamed one-deep, and all
    three are "uncovered" every week of the season. Reporting them buries the
    single position a package actually broke -- the live cbarone brief read
    "empties a required slot at DEF, K, QB, TE" when only the TE room was the
    trade's doing. So gate 3 asks what CHANGED, not what is true.
    """
    before = set(thin_after(roster, shape, key=key))
    after = set(thin_after(roster, shape, arriving=arriving,
                           departing=departing, waivers=waivers, key=key))
    return sorted(after - before)


def verdict(deal: Deal, weeks_left: int, *, floor_ppg: float = EDGE_PPG,
            market_floor: float = MARKET_FLOOR,
            market_ceiling: float = MARKET_CEILING,
            thin: list[str] | None = None, depth_blocks: bool = DEPTH_BLOCKS,
            con: dict | None = None) -> dict:
    """The two gates, kept separate on purpose.

    GATE 1 asks whether the trade is actually good -- my lineup up by more
    than projection error, theirs not down. GATE 2 asks whether they will
    say yes. They answer different questions and a deal needs both.

    The interesting region is the gap between them: passing gate 1 for both
    sides while sitting near even on gate 2 is the target. Passing 1 and
    failing 2 is a good idea you cannot sell -- adjust the package until the
    market reads even, then re-run gate 1 to check you did not break it.

    `weeks_left` converts season totals to PPG, because the threshold is a
    per-week quantity and the lineup deltas here are not. Pass 1 if the
    values are already per-week.

    `con` is the consensus row for the biggest piece, if you have it. A
    fixed floor cannot tell a 1.0 edge on a player every source agrees about
    from the same edge on one they argue about by thirty points; when a row
    is supplied, consensus.confident applies that test as well.
    """
    wl = max(1, int(weeks_left or 1))
    mine_ppg = deal.my_delta / wl
    theirs_ppg = deal.their_delta / wl
    # Two separate requirements, and which one binds depends on floor_ppg.
    # At the shipped 0.0 only `gains` does any work -- but it has to be
    # there, or a zero-delta package would read as "send it" and pure churn
    # carries transaction risk while buying nothing.
    gains = deal.my_delta > 0
    clears = mine_ppg >= floor_ppg
    gate1 = gains and clears and deal.their_delta >= 0
    share = None
    if deal.market and deal.market.get("in"):
        share = deal.market["out"] / deal.market["in"]
    gate2 = share is None or market_floor <= share <= market_ceiling
    confident = None
    if con is not None:
        from . import consensus as consensus_mod
        confident = consensus_mod.confident(con, abs(deal.my_delta))
    # GATE 3: a required slot with no cover behind it. Structural, so it is
    # not a threshold and does not care how big the trade is. Advisory
    # unless `depth_blocks`, so it lands in `warnings` rather than `why`.
    gate3 = not thin
    reasons, warnings = [], []
    if not gate1:
        reasons.append(f"lineup: me {mine_ppg:+.2f} ppg (need {floor_ppg:+.2f}), "
                       f"them {theirs_ppg:+.2f}")
    if not gate2 and share < market_floor:
        reasons.append(f"market: they receive {100 * share:.0f}% of what they give "
                       f"(need {100 * market_floor:.0f}%) — expect a rejection")
    elif not gate2:
        reasons.append(f"market: I send {100 * share:.0f}% of what I get back "
                       f"(ceiling {100 * market_ceiling:.0f}%) — overpaying")
    if not gate3:
        msg = (f"depth: one injury empties a required slot at "
               f"{', '.join(thin)} — no cover on the roster")
        (reasons if depth_blocks else warnings).append(msg)
    if confident is False:
        warnings.append("edge is smaller than the sources' own disagreement")
    return {"gate1": gate1, "gate2": gate2, "gate3": gate3,
            "send": bool(gate1 and gate2 and (gate3 or not depth_blocks)),
            "depth_blocks": depth_blocks, "thin": list(thin or []),
            "my_ppg": round(mine_ppg, 2), "their_ppg": round(theirs_ppg, 2),
            "market_share": round(share, 3) if share is not None else None,
            "confident": confident, "why": reasons, "warnings": warnings}


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
                          ("in  (waiver fill, opened spot)", mv.get("backfilled") or []),
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

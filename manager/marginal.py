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


# ---------------------------------------------------------------- slots
#
# A slot class is a FACT about one player on one roster after the joint
# re-solve. It is not a verdict on the trade -- the verdict is accepts(),
# which applies two tests to the whole starting set. And STARTS is not
# UPGRADE: Deebo Samuel STARTS for a team that just lost a WR, filling the
# emptied flex, and is a downgrade against every receiver they had.
# Plan: docs/plans/2026-09-09-slot-based-trades-plan.md
STARTS, USABLE_DEPTH, DEAD_WEIGHT = "STARTS", "USABLE_DEPTH", "DEAD_WEIGHT"
STARTED, DEPTH_LOST, FREE = "STARTED", "DEPTH_LOST", "FREE"


def _wire_best(waivers, pos, key, exclude_ids) -> float:
    """Best wire body at `pos`, or 0.0 when the wire has nobody there.

    A depth add is only depth if he beats this. A backup the roster could
    claim tomorrow is not depth -- which is what makes a 294-point QB2
    nearly worthless on a wire holding six QBs at 253-275.
    """
    best = 0.0
    for q in waivers or ():
        if q.get("pos") == pos and _pid(q) not in exclude_ids:
            best = max(best, float(q.get(key) or 0.0))
    return best


def _best_backup(pool, starter_ids, pos, key):
    """The best non-starter at `pos` in `pool`, or None."""
    cands = [q for q in pool if q.get("pos") == pos and _pid(q) not in starter_ids]
    return max(cands, key=lambda q: float(q.get(key) or 0.0)) if cands else None


def classify(roster: list[dict], shape: dict, *, arriving=(), departing=(),
             waivers=None, key: str = "weekly") -> dict:
    """Slot class for every player a package touches, on ONE roster.

    Returns {"received": {pid: class}, "given": {pid: class},
             "moves": slot_moves(...), "fill": [...]}

      received  STARTS        in the starting lineup after (post-backfill)
                USABLE_DEPTH  not starting; best non-starter at his position;
                              better than the best wire body there
                DEAD_WEIGHT   neither
      given     STARTED       was starting before
                DEPTH_LOST    was the best backup at his position and better
                              than the wire
                FREE          neither

    Run it on BOTH rosters for a trade: on his with my players arriving and
    his departing, on mine the other way round. The backfill is the same
    position-aware one price() uses, so "who starts after" here is the same
    answer price() gives -- if the two ever disagreed, the class and the
    delta would be describing two different trades.
    """
    arriving, departing = list(arriving), list(departing)
    dep_ids = {_pid(p) for p in departing}
    arr_ids = {_pid(p) for p in arriving}
    post = [p for p in roster if _pid(p) not in dep_ids] + arriving
    fill = _fill_for(arriving, departing, waivers, key, roster=post, shape=shape)
    mv = slot_moves(roster, shape, arriving=arriving, departing=departing,
                    filled=fill, key=key)
    before_ids = {_pid(p) for p in mv["before"]}
    after_ids = {_pid(p) for p in mv["after"]}
    after_roster = post + list(fill)
    # Two wires. AFTER the trade the fill body has been claimed, so he is no
    # longer on it; BEFORE the trade he was, and a departing player judged
    # against a wire that has already lost its best body would be called
    # DEPTH_LOST when the roster could have claimed that body any Tuesday.
    excl_after = dep_ids | arr_ids | {_pid(p) for p in fill}
    excl_before = dep_ids | arr_ids

    received: dict[str, str] = {}
    for p in arriving:
        pid = _pid(p)
        if pid in after_ids:
            received[pid] = STARTS
            continue
        bb = _best_backup(after_roster, after_ids, p.get("pos"), key)
        beats = float(p.get(key) or 0.0) > _wire_best(waivers, p.get("pos"), key, excl_after)
        received[pid] = (USABLE_DEPTH if (bb is not None and _pid(bb) == pid and beats)
                         else DEAD_WEIGHT)

    given: dict[str, str] = {}
    for p in departing:
        pid = _pid(p)
        if pid in before_ids:
            given[pid] = STARTED
            continue
        bb = _best_backup(list(roster), before_ids, p.get("pos"), key)
        beats = float(p.get(key) or 0.0) > _wire_best(waivers, p.get("pos"), key, excl_before)
        given[pid] = (DEPTH_LOST if (bb is not None and _pid(bb) == pid and beats)
                      else FREE)

    return {"received": received, "given": given, "moves": mv, "fill": list(fill)}


# ------------------------------------------------------------- acceptance
#
# DOES IT LOOK LIKE A WIN TO HIM. Two tests, both must pass; the Acceptance
# section of docs/plans/2026-09-09-slot-based-trades-plan.md is the spec. He
# is modelled on PERCEPTION -- the rank panel and the trade market -- over
# the players that land in a slot he uses. Points never enter it: they are
# my currency, not his.
UPGRADE, FILLER, SITS = "UPGRADE", "FILLER", "SITS"
UNRANKED = 300.0          # a player the panel does not rank: deep bench
SKILL = ("QB", "RB", "WR", "TE")


def _rank_of(ranks, p) -> float:
    """Overall rank, lower is better; UNRANKED for a player the panel skips."""
    r = (ranks or {}).get(_pid(p)) or {}
    v = r.get("overall")
    return float(v) if v is not None else UNRANKED


def accepts(their_roster: list[dict], shape: dict, *, arriving, departing,
            waivers=None, key: str = "weekly", ranks=None, market=None) -> dict:
    """Does the trade look like a win to HIM. Two tests; both must pass.

    Run on HIS roster: `arriving` are my players, `departing` are his.
    `ranks` is ecr.rank_panel() ({pid: {overall, positional, panel, ...}})
    and `market` is FantasyCalc ({pid: value}). Neither test reads points.

    TEST 1 -- a positional rank upgrade from me. A sent player who STARTS
    is an UPGRADE if he beats the WORST INCUMBENT STARTER AT HIS OWN
    POSITION on overall rank, flex-starters at that position included.
    Positional and label-free: "their RB got better" is a fact about the
    player; which slot is labelled RB2 is an artefact of fill order and is
    never compared across the trade. A sent player who starts and does not
    beat him is FILLER -- in the lineup only because someone left; Deebo
    Samuel is the measured case. One who does not start SITS. At least one
    UPGRADE is required.

    TEST 2 -- the market value of his STARTERS must not drop, backfill
    included. A roster-state test: what his starting lineup is worth as a
    set of assets, before and after. Dead weight never enters it, nor does
    the body he must drop in a 2-for-1.

    REPORTED, never gated: net overall rank of his starters -- the
    rankings-reader's view -- which disagrees with Test 1 exactly where the
    expert board and the trade market disagree (Javonte -> Wilson: an RB
    upgrade, net -13, market +1,086). The ledger decides which kind of
    manager he is; until it has, the flag is printed on every row.

    Returns {accept, test1, test2, tags, starters_market_before,
             starters_market_after, net_rank, panel, classes, why}.
    """
    arriving, departing = list(arriving), list(departing)
    cls = classify(their_roster, shape, arriving=arriving, departing=departing,
                   waivers=waivers, key=key)
    before, after = cls["moves"]["before"], cls["moves"]["after"]
    after_ids = {_pid(p) for p in after}

    def mk(p) -> int:
        return int((market or {}).get(_pid(p)) or 0)

    def nm(p) -> str:
        return p.get("name") or _pid(p)

    tags: dict[str, str] = {}
    why: list[str] = []
    for p in arriving:
        pid, pos = _pid(p), p.get("pos")
        if pid not in after_ids:
            tags[pid] = SITS
            why.append(f"{nm(p)} does not start for him")
            continue
        incumbents = [_rank_of(ranks, q) for q in before if q.get("pos") == pos]
        ranked = [r for r in incumbents if r < UNRANKED]
        # An incumbent the panel skips is NOT a 300: on the mirror fallback a
        # name collision can drop a WR1 from the panel, and a floor of 300
        # would make any ranked body I send an "upgrade" over him. Judge
        # against the ranked incumbents only; if none is ranked the seat
        # cannot be judged and the sent player is FILLER, said out loud. An
        # EMPTY seat (no incumbent at all) is still an upgrade to fill.
        if incumbents and not ranked:
            tags[pid] = FILLER
            why.append(f"{nm(p)} starts at {pos} but his incumbent {pos}s are not "
                       f"on the panel -- cannot call it an upgrade")
            continue
        floor = max(ranked) if ranked else UNRANKED
        mine = _rank_of(ranks, p)
        if mine < floor:
            tags[pid] = UPGRADE
            why.append(f"{nm(p)} ({pos}, overall {mine:.0f}) upgrades his worst "
                       f"starting {pos} (overall {floor:.0f})")
        else:
            tags[pid] = FILLER
            why.append(f"{nm(p)} starts but is not an upgrade at {pos} "
                       f"(overall {mine:.0f} against his worst starter at {floor:.0f})")
    test1 = any(t == UPGRADE for t in tags.values())

    mkt_before = sum(mk(p) for p in before)
    mkt_after = sum(mk(p) for p in after)
    test2 = mkt_after >= mkt_before
    why.append(f"his starters' market {mkt_before} -> {mkt_after} "
               f"({mkt_after - mkt_before:+d})" + ("" if test2 else " -- DOWN"))

    # Skill positions only: K/DEF ranks are noise and never move in a trade.
    rank_before = sum(_rank_of(ranks, p) for p in before if p.get("pos") in SKILL)
    rank_after = sum(_rank_of(ranks, p) for p in after if p.get("pos") in SKILL)
    net_rank = round(rank_before - rank_after, 1)
    # Mirror ranks are fractional; a -0.3 must not print "worse by 0".
    if net_rank <= -0.5:
        why.append(f"a rankings-reader sees his lineup worse by {-net_rank:.0f} "
                   f"rank-points")

    panels = [((ranks or {}).get(_pid(p)) or {}).get("panel") for p in arriving + departing]
    panels = [x for x in panels if x]
    return {"accept": bool(test1 and test2), "test1": test1, "test2": test2,
            "tags": tags, "starters_market_before": mkt_before,
            "starters_market_after": mkt_after, "net_rank": net_rank,
            "panel": min(panels) if panels else None, "classes": cls, "why": why}


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
    # accepts() on HIS side, when price() was given a rank panel. None means
    # "not computed", which verdict(mode="slots") reports rather than hides.
    acceptance: dict | None = None

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


# How many wire bodies per position the position-aware backfill considers.
# 3 per position over the four startable skill positions (K/DEF are skipped
# below) is about 12 lineup solves per opened spot. Measured 2026-09-09:
# price() runs 0.51 ms per package with this against 0.23 ms on the legacy
# pick -- immaterial for the radar, roughly double for an offline frontier
# sweep. The naive version over the whole wire is ~4 ms and too slow for one.
BACKFILL_TOP_K = 3
# Never a kicker or a defence, in either path. A trade never opens a K or DEF
# seat -- they are streamed, not traded -- and their projections are the least
# reliable on the board (one source, uncalibrated against the others). Left in,
# the lineup solve picked a wire DEF that beat mine as the "backfill" for a
# 2-for-1 that touched no DEF seat, crediting the trade +11 for a pickup
# available any Tuesday by dropping the worst bench body. Measured 2026-09-09.
BACKFILL_SKIP = ("K", "DEF")

def backfill(n: int, waivers, key: str = "weekly", exclude=(), *,
             roster=None, shape=None, top_k: int = BACKFILL_TOP_K,
             departed_pos=()) -> list[dict]:
    """The best `n` free agents, for roster spots a package leaves open.

    NOT a replacement baseline. Bench players are already in the pool the
    optimiser solves over, so a departing starter is covered by the bench
    automatically. This is narrower: a 2-for-1 sends more bodies than it
    receives and opens a SPOT, and that spot is filled by Tuesday. Pricing
    it at zero understates every consolidation.

    POSITION-AWARE WHEN IT CAN BE. Given `roster` (the roster AFTER the
    departures and arrivals, i.e. with the spot actually open) and `shape`,
    each pick is the wire body that raises that roster's optimal lineup the
    most, chosen from the top `top_k` per position. Without them it falls
    back to the top `n` by raw points, which is what every caller got until
    2026-09-09 and what the older tests pin.

    Why the raw-points version was wrong: it handed over the best body on
    the wire regardless of position. On a board where the wire's best body
    is a QB (Omnibeta: Jordan Love, 275), a roster giving an RB in a 2-for-1
    received a QB who could not play flex, and the seat was priced as empty.
    Harmless on a roster with a flex-eligible bench body to cover; a real
    mispricing on one without. It happened to be RIGHT for the one case it
    was measured on (giving a QB, receiving Love), which is how it survived.
    """
    # HALF-SPECIFIED IS A BUG, NOT A FALLBACK. Falling back to the legacy pick
    # when only one of roster/shape arrives would reintroduce the position-
    # blind fill with nothing in the output to say so. No caller legitimately
    # passes one without the other.
    if (roster is None) != (shape is None):
        raise ValueError("backfill needs both roster and shape for the "
                         "position-aware pick, or neither for the legacy one")
    if n <= 0 or not waivers:
        return []
    skip = {_pid(p) for p in exclude}
    # K/DEF are skipped UNLESS THE TRADE ITSELF DEPARTED ONE. The blanket skip
    # charged a package that gave my kicker the whole seat: wire K at 7.5, RB
    # handed over instead, my_delta -8.0 where -0.5 was true. Reachable --
    # the radar's desperation path offers any of my players at the position
    # of THEIR injured starter, and kickers go on IR.
    departed_pos = set(departed_pos or ())
    pool = [p for p in waivers if _pid(p) not in skip
            and ((p.get("pos") or "") not in BACKFILL_SKIP
                 or (p.get("pos") or "") in departed_pos)]
    if roster is None:
        return sorted(pool, key=lambda p: -(p.get(key) or 0.0))[:n]

    # ONLY POSITIONS THE SHAPE CAN START. A body the lineup cannot seat gains
    # exactly 0, and the old code could still pick it when nothing else
    # gained, dropping a positionless row into after_roster for thin_after to
    # count under None. Skipping it also removes those solves.
    from draftkit.lineup import _flex_sets
    startable = set(shape.get("slots") or {})
    for eligible in _flex_sets(shape.get("flex", 0), shape.get("flex_slots")):
        startable |= set(eligible)
    pool = [p for p in pool if (p.get("pos") or "") in startable]

    # Candidates: top_k per position. The lineup solve decides among them.
    by_pos: dict[str, list[dict]] = {}
    for q in sorted(pool, key=lambda p: -(p.get(key) or 0.0)):
        bucket = by_pos.setdefault(q["pos"], [])
        if len(bucket) < top_k:
            bucket.append(q)
    cands = [q for bucket in by_pos.values() for q in bucket]
    have = list(roster)
    picked: list[dict] = []
    for _ in range(n):
        if not cands:
            break
        base = lineup_points(have, shape, key)
        # Best lineup gain first. On a TIE, prefer a body at a position the
        # trade emptied: that is the seat this fill exists for, and an
        # unrelated upgrade elsewhere is D3 territory (see the plan). Raw
        # points last, so quality rather than dict order decides the rest.
        best = max(cands, key=lambda q: (
            round(lineup_points(have + [q], shape, key) - base, 6),
            q["pos"] in departed_pos,
            q.get(key) or 0.0))
        picked.append(best)
        have.append(best)
        cands.remove(best)
    return picked


def _fill_for(arriving, departing, waivers, key: str = "weekly", *,
              roster=None, shape=None) -> list[dict]:
    """The backfill one side of a package earns. ONE definition.

    price(), depth_risk() and thin_after() each derived this independently
    and happened to agree; a change to the exclude semantics would have had
    to land in three places, only one of which the price() tests cover.

    `roster` is that side's roster WITH the departures removed and the
    arrivals added -- the state in which the spot is actually open -- so the
    position-aware pick sees the hole it is filling. All three callers build
    it the same way and pass it; the legacy raw-points path is only for a
    caller that has no roster to offer.
    """
    arriving, departing = list(arriving), list(departing)
    return backfill(len(departing) - len(arriving), waivers, key,
                    exclude=arriving + departing, roster=roster, shape=shape,
                    departed_pos={p.get("pos") for p in departing})


def price(my_roster: list[dict], their_roster: list[dict],
          give: list[dict], get: list[dict], shape: dict,
          their_shape: dict | None = None, key: str = "weekly",
          market_values: dict[str, int] | None = None,
          waivers: list[dict] | None = None,
          ranks: dict | None = None) -> Deal:
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

    `ranks` is ecr.rank_panel(). When given, accepts() runs on HIS side and
    lands on the Deal as `acceptance`, which is what verdict(mode="slots")
    reads in place of his lineup delta. Left None, the Deal says so and
    slots mode refuses to guess.
    """
    their_shape = their_shape or shape
    mkt = None
    if market_values:
        from . import market as market_mod
        mkt = market_mod.price(market_values, give, get)
    give_ids, get_ids = {_pid(p) for p in give}, {_pid(p) for p in get}
    my_fill = _fill_for(get, give, waivers, key,
                        roster=[p for p in my_roster if _pid(p) not in give_ids] + list(get),
                        shape=shape)
    their_fill = _fill_for(give, get, waivers, key,
                           roster=[p for p in their_roster if _pid(p) not in get_ids] + list(give),
                           shape=their_shape or shape)
    # Both sides re-solve. slot_moves carries the totals, so the deltas and
    # the seat-by-seat story cannot drift apart the way they would if the
    # points were computed here and the movements somewhere else.
    mine = slot_moves(my_roster, shape, arriving=get, departing=give,
                      filled=my_fill, key=key)
    theirs = slot_moves(their_roster, their_shape, arriving=give,
                        departing=get, filled=their_fill, key=key)
    # His side, in his currencies. accepts() re-solves his lineup through
    # classify(); that repeats work done two lines up (~0.5 ms) and is kept
    # simple until the radar shows the cost matters.
    acceptance = None
    if ranks is not None:
        acceptance = accepts(their_roster, their_shape, arriving=give, departing=get,
                             waivers=waivers, key=key, ranks=ranks, market=market_values)
    return Deal(
        mine_before=mine["total_before"], mine_after=mine["total_after"],
        theirs_before=theirs["total_before"], theirs_after=theirs["total_after"],
        give=[p.get("name", _pid(p)) for p in give],
        get=[p.get("name", _pid(p)) for p in get],
        market=mkt, my_moves=mine, their_moves=theirs,
        my_backfill=[p.get("name", _pid(p)) for p in my_fill],
        their_backfill=[p.get("name", _pid(p)) for p in their_fill],
        acceptance=acceptance,
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
    fill = _fill_for(arriving, departing, waivers, key,
                     roster=[p for p in roster if _pid(p) not in dep] + list(arriving),
                     shape=shape)
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
# THE CEILING REPORTS; IT DOES NOT BLOCK. User decision, 2026-09-09.
#
# Gate 2 folds two jobs into one band. The FLOOR asks "will they say yes" --
# a deal they refuse is worth nothing, so it blocks. The CEILING asks "am I
# handing over market value" -- and market value does not score points. Its
# only use is future trade capital, and with the whole-league misallocation
# ceiling measured at +7.2 there is almost nothing to buy with it.
#
# Worse, for a deal that gets ACCEPTED the ceiling is counterproductive. The
# counterparty judges on names and value, not on my lineup math. The one
# package on the 2026-09-09 board that both sides won -- Javonte + Deebo for
# Garrett Wilson, me +5.2 lineup points, them +2.0 -- ran 149% on the market,
# because that is precisely what made it a yes: they win in the currency
# they see, I win in the one that scores. The 1.15 ceiling rejected it.
#
# So overpaying is still measured and still said out loud, in `warnings`.
# Flip this to block again when preserving asset value matters more than
# acquiring points -- a keeper league, or a season already lost.
MARKET_CEILING_BLOCKS = False
DEPTH_BLOCKS = False
# WHICH QUESTION verdict() ASKS ABOUT HIS SIDE.
#   "points" -- his lineup delta in MY projections must be >= 0. The original
#               gate; measured this session to surface packages worth +0.6 a
#               season to him, which nobody accepts.
#   "slots"  -- accepts(): a positional rank upgrade from me AND his starters'
#               market not reduced, in HIS currencies. The plan's design.
# DEFAULT "slots" SINCE STEP 7 (2026-09-10): the radar supplies the rank
# panel through price(ranks=). A caller with no panel gets "acceptance: not
# computed" and a hold -- never a silent fall back to the points gate. The
# points gate is one keyword away for a caller that means it, and its tests
# say so. docs/plans/2026-09-09-slot-based-trades-plan.md
MODE = "slots"
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
    fill = _fill_for(arriving, departing, waivers, key,
                     roster=[p for p in roster if _pid(p) not in dep] + list(arriving),
                     shape=shape)
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


# ---------------------------------------------------------------- injuries
#
# THE TRADE PATH NEVER LOOKED AT INJURY STATUS. On 2026-09-10 it priced
# Henry + Warren for Egbuka + A.J. Brown as +1.16/wk with Brown Out (ankle)
# on Sleeper and every source still carrying his full season. Two fixes,
# both here so price(), the radar and the chips share them: the ROS of a
# player who is not playing is scaled by the weeks he misses, and every
# such piece is named out loud. Advisory, never a gate -- the user decides.
INJURED = ("Out", "IR", "PUP", "Sus", "Suspended", "NA", "COV", "DNR", "Doubtful")
# Weeks missed when nobody has said: Out/Doubtful is this week; a reserve
# designation is the four-game minimum. FantasyPros `ir_weeks` overrides.
DEFAULT_WEEKS_OUT = {"Out": 1, "Doubtful": 1, "Sus": 1, "Suspended": 1, "NA": 1,
                     "COV": 1, "IR": 4, "PUP": 4, "DNR": 99}


def injury_discount(rows, injury: dict | None, weeks_left: int, *,
                    weeks_out: dict | None = None, key: str = "ros") -> list[dict]:
    """Copies of `rows` with `key` scaled by the share of the season the
    player is expected to play. Healthy and Questionable rows come back
    untouched (same object). A discounted row carries `_injury` =
    {status, weeks, healthy} so the brief can say what it did.

    `ros_season` is left alone on purpose: the per-source range scales each
    shop's season total by ros / ros_season, so the discount reaches every
    source-world for free.
    """
    if not injury:
        return list(rows)
    wl = max(1, int(weeks_left or 1))
    out = []
    for p in rows:
        status = (injury.get(_pid(p)) or "").strip()
        if status not in INJURED:
            out.append(p)
            continue
        weeks = (weeks_out or {}).get(_pid(p))
        if weeks is None:
            weeks = DEFAULT_WEEKS_OUT.get(status, 1)
        weeks = min(wl, max(0, int(weeks)))
        share = (wl - weeks) / wl
        healthy = float(p.get(key) or 0.0)
        q = dict(p)
        q[key] = round(healthy * share, 2)
        q["_injury"] = {"status": status, "weeks": weeks, "healthy": healthy}
        out.append(q)
    return out


def injury_flags(pieces) -> list[str]:
    """One line per package piece that injury_discount() touched."""
    out = []
    for p in pieces:
        inj = p.get("_injury")
        if not inj:
            continue
        out.append(f"INJURED: {p.get('name') or _pid(p)} ({p.get('pos')}) is {inj['status']} "
                   f"— priced at {p.get('ros') or 0:.0f} ROS, {inj['healthy']:.0f} healthy "
                   f"({inj['weeks']} wk{'s' if inj['weeks'] != 1 else ''} out)")
    return out


def verdict(deal: Deal, weeks_left: int, *, floor_ppg: float = EDGE_PPG,
            market_floor: float = MARKET_FLOOR,
            market_ceiling: float = MARKET_CEILING,
            market_ceiling_blocks: bool = MARKET_CEILING_BLOCKS,
            thin: list[str] | None = None, depth_blocks: bool = DEPTH_BLOCKS,
            con: dict | None = None, mode: str = MODE,
            injured: list[str] | None = None) -> dict:
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
    # HIS SIDE, in the currency the mode names. Slots mode never reads his
    # lineup delta -- that is my model of his team, and he does not use it.
    if mode == "slots":
        his_yes = bool(deal.acceptance and deal.acceptance.get("accept"))
    elif mode == "points":
        his_yes = deal.their_delta >= 0
    else:
        raise ValueError(f"verdict mode {mode!r} is not 'slots' or 'points'")
    gate1 = gains and clears and his_yes
    share = None
    if deal.market and deal.market.get("in"):
        share = deal.market["out"] / deal.market["in"]
    # The floor always binds. The ceiling binds only when asked to -- the
    # same shape as gate 3, and for the same reason: it is information, not
    # a veto, unless the caller says otherwise.
    under = share is not None and share < market_floor
    over = share is not None and share > market_ceiling
    # In slots mode the floor's job -- "will he refuse" -- is answered by
    # accepts() Test 2 (his starters' market must not drop), so the band is
    # information only. In points mode the floor still blocks.
    floor_blocks = mode == "points"
    gate2 = not (under and floor_blocks) and not (over and market_ceiling_blocks)
    confident = None
    if con is not None:
        from . import consensus as consensus_mod
        confident = consensus_mod.confident(con, abs(deal.my_delta))
    # GATE 3: a required slot with no cover behind it. Structural, so it is
    # not a threshold and does not care how big the trade is. Advisory
    # unless `depth_blocks`, so it lands in `warnings` rather than `why`.
    gate3 = not thin
    reasons, warnings = [], []
    # Injured pieces lead the warnings: the numbers above were priced on the
    # discounted ROS, and the reader should know that before the mean.
    for w in (injured or []):
        warnings.append(f"⚠ {w}")
    if not (gains and clears):
        reasons.append(f"lineup: me {mine_ppg:+.2f} ppg (need {floor_ppg:+.2f})")
    if not his_yes:
        if mode == "points":
            reasons.append(f"lineup: them {theirs_ppg:+.2f} ppg")
        elif deal.acceptance is None:
            reasons.append("acceptance: not computed — price() was given no rank "
                           "panel, and slots mode will not guess his side")
        else:
            acc = deal.acceptance
            failed = ([] if acc.get("test1") else ["no positional upgrade from me"]) + \
                     ([] if acc.get("test2") else ["his starters' market drops"])
            reasons.append("acceptance: " + " and ".join(failed)
                           + f" — {'; '.join(acc.get('why') or [])}")
    if under:
        (reasons if floor_blocks else warnings).append(
            f"market: they receive {100 * share:.0f}% of what they give "
            f"(need {100 * market_floor:.0f}%) — expect a rejection")
    if over:
        (reasons if market_ceiling_blocks else warnings).append(
            f"market: I send {100 * share:.0f}% of what I get back "
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
            "market_ceiling_blocks": market_ceiling_blocks,
            "mode": mode, "acceptance": deal.acceptance,
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
              key: str = "weekly", *, waivers=None, ranks=None) -> list[dict]:
    """Rank my roster by SURPLUS: where is a player worth more than here?

    THIS IS THE FIRST LOOK, NOT THE PRICE. For each of my players it asks
    one question in isolation -- what does my lineup lose without him, and
    what does the best rival lineup gain with him -- and ranks on the gap:

        surplus = best_gain - cost

    Positive means he is misallocated: he scores more sitting over there.
    That is where a trade CAN create value, and it is the only place one can.
    It is not what a package is worth, because arrivals and departures
    interact through the flex and the single-player numbers do not add. On
    2026-09-09 Deebo Samuel scored surplus 0.0 against every roster -- worth
    nothing to anyone in isolation -- and carried the entire +7.2 of the
    best package on the board, because the WR leaving the other side opened
    a flex seat that did not exist when this function asked. Find the seam
    here; price the package with price().

    Ranked on surplus rather than the old gain/cost ratio because ratio
    answers a different question. It favoured any cheap player with a buyer
    over the biggest absolute misallocation: cost 10 / gain 20 (ratio 2.0,
    surplus +10) outranked cost 100 / gain 150 (ratio 1.5, surplus +50).
    `ratio` is still carried for callers that want it.

    `others` is {owner -> roster}. `buyers` counts how many rival lineups
    actually improve; a player nobody's lineup wants has no market whatever
    his projection says, and sorts last whatever his surplus.

    CHIPS (step 6 of the slot-based trade plan). A chip is a player who is
    CHEAP FOR ME TO SELL AND HAS A BUYER -- both, not either:

      * `true_cost` is the lineup drop with the position-aware backfill a
        2-for-1 actually earns, given `waivers`. Caleb Williams costs 293.7
        on cost_to_lose (an empty QB seat) and 18.7 with Jordan Love
        backfilled off the wire. Without `waivers` it equals `cost`.
      * `rank_buyers` are the teams for whom he is a positional upgrade IN
        THEIR CURRENCY: he starts for them AND beats their worst incumbent
        at his position on overall rank -- accepts() Test 1 applied to one
        player. A buyer has to be found in the currency the buyer uses: on
        points, `buyers` counts anyone whose lineup ticks up, which can name
        a team that would never see him as an upgrade on the board, and
        miss one that would.

    When `ranks` is given the list ranks CHIPS: has a rank buyer first, then
    `true_cost` ascending; unbought players last whatever the cost. Without
    `ranks` the surplus ranking below is unchanged and `rank_buyers` is None.
    """
    base = lineup_points(roster, shape, key)
    rows = []
    for p in roster:
        # NEVER A KICKER OR A DEFENCE. They are streamed, not traded -- the
        # same policy that keeps them out of backfill -- and left in they
        # topped the live chip list on 2026-09-10: the Vikings DEF at a cost
        # of -11.0, because departing him let a better wire DEF backfill, with
        # four rank buyers whose defences the panel ranks lower. A chip list
        # led by a DEF and a K is a list nobody reads past.
        if (p.get("pos") or "") in BACKFILL_SKIP:
            continue
        pid = _pid(p)
        cost = cost_to_lose(roster, p, shape, key)
        rest = [q for q in roster if _pid(q) != pid]
        fill = (_fill_for([], [p], waivers, key, roster=rest, shape=shape)
                if waivers else [])
        true_cost = round(base - lineup_points(rest + list(fill), shape, key), 1)
        gains = [(gain_to_add(r, p, shape, key), who) for who, r in others.items()]
        best = max(gains) if gains else (0.0, None)
        rank_buyers = None
        if ranks is not None:
            rank_buyers = [who for who, r in others.items()
                           if accepts(r, shape, arriving=[p], departing=[],
                                      key=key, ranks=ranks)["tags"].get(pid) == UPGRADE]
        rows.append({
            "player": p, "proj": round(p.get(key) or 0.0, 1), "cost": cost,
            "true_cost": true_cost,
            "buyers": sum(1 for g, _ in gains if g > 0),
            "rank_buyers": rank_buyers,
            "best_gain": best[0], "best_buyer": best[1],
            "surplus": round(best[0] - cost, 1),
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
        if ranks is not None:
            # Chips: a buyer in his currency first, cheapest for me first
            # within that; nobody wants him -> last, however cheap.
            return (0 if r["rank_buyers"] else 1, r["true_cost"], -r["surplus"])
        free_and_wanted = r["cost"] <= 0 and r["best_gain"] > 0
        # Three tiers, then surplus within each. A player nobody wants stays
        # at the bottom even at surplus 0 -- otherwise a bench body with no
        # buyer outranks a correctly-allocated starter at surplus -14.
        tier = 0 if free_and_wanted else (1 if r["buyers"] > 0 else 2)
        return (tier, -r["surplus"], -r["best_gain"])

    return sorted(rows, key=rank)

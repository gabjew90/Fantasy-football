"""The entry summary (card spec v1, "Entry summary"): printed after the leg
cards of an entry, then the grade legend and the follow-up names. Plain
arithmetic on the cards' own numbers and the entry's payout; no chance of its
own, no verdict, no percentages.
"""

from __future__ import annotations

import math

from . import calc, card, odds

LEGEND = "Grades: S best, F worst."
FOLLOW_UPS = "Follow-ups: Workload, Calculation, Matchup, Fit, Entry cost."
BET_WORDS = {"rush_yds": "rushing", "receptions": "catches", "rec_yds": "receiving", "pass_yds": "passing"}


def leg_view(name: str, market: str, side: str, c: dict, team: str, opp: str, game_id: str) -> dict:
    """What the summary needs from one leg's card: the bar and the workload
    ask exactly as the card shows them (card.work_ask), the side's search
    result in words, and its price."""
    s = c["solutions"][f"needed_{side}"]
    result = calc.side_result(side, s.status)          # ok / always / never, for this side
    bar = s.value if result == "ok" else None
    ask = card.work_ask(bar, c["usual"]) if bar is not None and c["usual"] is not None else None
    return {"name": name, "market": market, "side": side, "bar": bar, "ask": ask, "result": result,
            "top": c["search_max"], "team": team, "opp": opp, "game_id": game_id, "mult": c[f"mult_{side}"]}


def story(leg: dict) -> tuple:
    """(team that leads in the game story the leg leans on, words). Overs on
    rushing lean on his team ahead; Overs on catches, receiving and passing
    yards on his team behind (throwing); Unders the reverse."""
    rush = leg["market"] == "rush_yds"
    over = leg["side"] == "over"
    ahead = rush == over                       # rush Over or pass-catch Under: his team ahead
    leader = leg["team"] if ahead else leg["opp"]
    if rush:
        words = "more runs while ahead." if over else "fewer runs while behind."
    else:
        words = "more throws from behind." if over else "fewer throws while ahead."
    return leader, words


def _label(leg: dict, legs: list[dict]) -> str:
    """His name; with the bet type when he has two legs in the entry."""
    twice = sum(x["name"] == leg["name"] for x in legs) > 1
    return f"{leg['name']} ({BET_WORDS[leg['market']]})" if twice else leg["name"]


def fit_check(legs: list[dict]) -> list[str]:
    """Every pair on the same team or in the same game whose game stories are
    opposite (one needs a team ahead, the other the same team behind), each in
    the spec's wording."""
    out = ["FIT CHECK"]
    pairs = [(a, b) for i, a in enumerate(legs) for b in legs[i + 1:]
             if a["game_id"] == b["game_id"] and story(a)[0] != story(b)[0]]   # same team implies same game
    if not pairs:
        return out + ["No opposing pairs found."]
    for a, b in pairs:
        out += card._wrap(f"{_label(a, legs)}: {story(a)[1]}") + card._wrap(f"{_label(b, legs)}: {story(b)[1]}")
        out.append("These lean on opposite game stories.")
    return out + ["Both can win. Check your case for each."]


def _wins(p: float) -> str:
    """A win rate as wins in 100, one decimal, half up."""
    return card.d1(p * 100)


def money(x: float) -> str:
    """Dollars, two decimals, half up, with thousands separators."""
    return f"${card.half_up(x, '0.01'):,.2f}"


def _need_line(x: dict, legs: list[dict]) -> str:
    many = card.SHOW[x["market"]][1][1]
    who = _label(x, legs)
    if x["bar"] is None:                       # the card's own out-of-range wording
        what = "any" if x["result"] == "always" else "no"
        return f"{who}: {what} workload up to {x['top']:.0f} {many} clears it."
    bar = card._work(x["bar"]) + f" {many}" + (" or fewer" if x["side"] == "under" else "")
    if x["ask"] is None:
        return f"{who}: {bar}, no recent average yet."
    ask = x["ask"] if x["side"] == "over" else -x["ask"]          # positive = what the bet needs
    more, fewer = ("more", "fewer") if x["side"] == "over" else ("fewer", "more")
    if ask > 0:
        return f"{who}: {bar}, about {card._num(ask)} {more} than recent."
    if ask < 0:
        return f"{who}: {bar}, about {card._num(-ask)} {fewer} than recent."
    return f"{who}: {bar}, the same as recent."


def _sort_key(x: dict) -> float:
    """Biggest ask first, from each bet's side; no workload clears it = the
    biggest ask, any workload clears it = the smallest. A sort, not a verdict."""
    if x["bar"] is None:
        return math.inf if x["result"] == "never" else -math.inf
    if x["ask"] is None:
        return -math.inf
    return x["ask"] if x["side"] == "over" else -x["ask"]


def render(legs: list[dict], stake: float, payout: float, payout_from_legs: bool) -> str:
    """The entry summary. payout: the total returned if every leg wins,
    stake included (Sleeper's number), or the legs' prices multiplied when the
    user gave none (said so)."""
    if not (stake > 0 and payout > stake):
        raise ValueError(f"an entry needs a stake above 0 and a payout above it; got {stake} and {payout}")
    n = len(legs)
    st = money(stake).replace(".00", "")
    out = [f"YOUR {st} ENTRY · {n} LEGS", f"Return if all win: {money(payout)}", f"Includes your {st} stake."]
    if payout_from_legs:
        out += card._wrap("(No payout given: worked out from the legs' own prices multiplied together, "
                          "not from your entry.)")
    out += ["", "WHAT EACH NEEDS (biggest ask first)"]
    for x in sorted(legs, key=_sort_key, reverse=True):
        out += card._wrap(_need_line(x, legs))
    out += [""] + fit_check(legs)
    out += ["", "PRICE CHECK: EACH BET ON ITS OWN"]
    for x in legs:
        out += card._wrap(f"{_label(x, legs)}: more than {_wins(odds.break_even(x['mult']))} wins in 100.")
    each = (stake / payout) ** (1.0 / n)        # every leg must win this often for the entry to break even
    out += ["", "TO COVER THE ENTRY COST", f"All must win more than {_wins(each)} in 100."]
    ways = 2 ** n
    net = payout / ways - stake
    out += ["", "IF EACH LEG HITS 1 TIME IN 2", "Also assume no shared game effects.",
            f"All {n} win: 1 entry in {ways}.",
            (f"Average loss: {money(-net)} per {st} entry." if net < 0
             else f"Average gain: {money(net)} per {st} entry.")]
    out += ["", LEGEND] + card._wrap(FOLLOW_UPS)
    return "\n".join(out)


def payout_from_legs(stake: float, legs: list[dict]) -> float:
    """The legs' multipliers multiplied, times the stake (used only when the
    entry's own payout was not given, and said so on the summary)."""
    return stake * math.prod(x["mult"] for x in legs)

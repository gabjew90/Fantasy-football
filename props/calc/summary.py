"""The entry summary (card spec v1, "Entry summary"): printed after the leg
cards of an entry, then the grade legend and the follow-up names. Plain
arithmetic on the cards' own numbers and the entry's payout; no chance of its
own, no verdict, no percentages.
"""

from __future__ import annotations

import math

from . import card, odds

LEGEND = "Grades: S best, F worst."
FOLLOW_UPS = "Follow-ups: Workload, Calculation, Matchup, Fit, Entry cost."


def leg_view(name: str, market: str, side: str, c: dict, team: str, opp: str, game_id: str) -> dict:
    """What the summary needs from one leg's card."""
    s = c["solutions"][f"needed_{side}"]
    ok = calc_ok(side, s.status)
    bar = s.value if ok else None
    ask = None
    if bar is not None and c["usual"] is not None:      # the card's workload ask, from the numbers it shows
        ask = card.half_up(card.shown_work(bar) - card.half_up(c["usual"], "0.1"), "0.5")
    return {"name": name, "market": market, "side": side, "bar": bar, "ask": ask, "team": team, "opp": opp,
            "game_id": game_id, "mult": c[f"mult_{side}"], "status": s.status}


def calc_ok(side: str, status: str) -> bool:
    from . import calc
    return calc.side_result(side, status) == "ok"


def _surname(name: str) -> str:
    return name.split()[-1] if name.split() else name


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


def fit_check(legs: list[dict]) -> list[str]:
    """Every pair on the same team or in the same game whose game stories are
    opposite (one needs a team ahead, the other the same team behind)."""
    pairs = []
    for i, a in enumerate(legs):
        for b in legs[i + 1:]:
            if a["game_id"] != b["game_id"]:
                continue                       # same team implies same game
            if story(a)[0] != story(b)[0]:
                pairs.append((a, b))
    if not pairs:
        return ["FIT CHECK", "No opposing pairs found."]
    involved = []
    for a, b in pairs:
        for x in (a, b):
            if x not in involved:
                involved.append(x)
    out = ["FIT CHECK"]
    out += [f"{x['name']}: {story(x)[1]}" for x in involved]
    out += card._wrap("Opposite game stories: "
                      + "; ".join(f"{_surname(a['name'])} and {_surname(b['name'])}" for a, b in pairs) + ".")
    out += ["Both can win. Check your case for each."]
    return out


def _wins(p: float) -> str:
    """A win rate as wins in 100, one decimal, half up."""
    return f"{card.d1(p * 100)}"


def render(legs: list[dict], stake: float, payout: float, payout_from_legs: bool) -> str:
    """The entry summary. payout: the total returned if every leg wins,
    stake included (Sleeper's number), or the legs' prices multiplied when the
    user gave none (said so)."""
    n = len(legs)
    out = [f"YOUR ${stake:g} ENTRY · {n} LEGS", f"Return if all win: ${payout:,.2f}",
           f"Includes your ${stake:g} stake."]
    if payout_from_legs:
        out += card._wrap("(No payout given: worked out from the legs' own prices multiplied together, "
                          "not from your entry.)")
    out += ["", "WHAT EACH NEEDS (biggest ask first)"]
    unit = {m: card.SHOW[m][1] for m in card.SHOW}
    # biggest ask first, from each bet's side (an Under's ask is how many fewer it needs); a sort, not a verdict
    order = sorted(legs, key=lambda x: -((x["ask"] if x["side"] == "over" else -x["ask"])
                                          if x["ask"] is not None else -math.inf))
    for x in order:
        one, many = unit[x["market"]]
        if x["bar"] is None:
            out += card._wrap(f"{x['name']}: no bar in range ({x['status']}).")
            continue
        bar = card._work(x["bar"])
        if x["ask"] is None:
            tail = "no recent average yet."
        else:
            ask = x["ask"] if x["side"] == "over" else -x["ask"]
            more, fewer = ("more", "fewer") if x["side"] == "over" else ("fewer", "more")
            if ask > 0:
                tail = f"about {card._num(ask)} {more} than recent."
            elif ask < 0:
                tail = f"about {card._num(-ask)} {fewer} than recent."
            else:
                tail = "the same as recent."
        out += card._wrap(f"{x['name']}: {bar} {many}{' or fewer' if x['side'] == 'under' else ''}, {tail}")
    out += [""] + fit_check(legs)
    out += ["", "PRICE CHECK: EACH BET ON ITS OWN"]
    for x in legs:
        out += card._wrap(f"{x['name']}: more than {_wins(odds.break_even(x['mult']))} wins in 100.")
    each = (stake / payout) ** (1.0 / n)        # every leg must win this often for the entry to break even
    out += ["", "TO COVER THE ENTRY COST", f"All must win more than {_wins(each)} in 100."]
    ways = 2 ** n
    net = payout / ways - stake
    out += ["", "IF EACH LEG HITS 1 TIME IN 2", "Also assume no shared game effects.",
            f"All {n} win: 1 entry in {ways}.",
            (f"Average loss: ${-net:,.2f} per ${stake:g} entry." if net < 0
             else f"Average gain: ${net:,.2f} per ${stake:g} entry.")]
    out += ["", LEGEND] + card._wrap(FOLLOW_UPS)
    return "\n".join(out)


def payout_from_legs(stake: float, legs: list[dict]) -> float:
    """The legs' multipliers multiplied, times the stake (used only when the
    entry's own payout was not given, and said so on the summary)."""
    return stake * math.prod(x["mult"] for x in legs)

"""The entry summary (card spec v1, "Entry summary"): printed after the leg
cards of an entry, then the grade legend and the follow-up names. Plain
arithmetic on the cards' own numbers and the entry's payout; no chance of its
own, no verdict, no percentages.
"""

from __future__ import annotations

import math

from . import calc, card, odds

LEGEND = "Grades: S best, F worst; + and - show where a team sits in its band."
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
            "top": c["search_max"], "team": team, "opp": opp, "game_id": game_id, "mult": c[f"mult_{side}"],
            "line": c.get("line")}


def story(leg: dict) -> tuple:
    """(team that leads in the game story the leg leans on, words). Overs on
    rushing lean on his team ahead; Overs on catches, receiving and passing
    yards on his team behind (throwing); Unders the reverse. The words name
    his team, so two "from behind" legs on opposite teams do not read as the
    same story (a fix under the frozen spec's rule (b): without the team the
    pair read as a contradiction)."""
    rush = leg["market"] == "rush_yds"
    over = leg["side"] == "over"
    ahead = rush == over                       # rush Over or pass-catch Under: his team ahead
    leader = leg["team"] if ahead else leg["opp"]
    t = leg["team"]
    if rush:
        words = f"more runs while {t} is ahead." if over else f"fewer runs while {t} is behind."
    else:
        words = f"more throws while {t} is behind." if over else f"fewer throws while {t} is ahead."
    return leader, words


def _label(leg: dict, legs: list[dict]) -> str:
    """His name; with the bet type when he has two legs in the entry."""
    twice = sum(x["name"] == leg["name"] for x in legs) > 1
    return f"{leg['name']} ({BET_WORDS[leg['market']]})" if twice else leg["name"]


def opposing_pairs(legs: list[dict]) -> list[tuple[str, str]]:
    """Every pair on the same team or in the same game whose game stories are
    opposite (one needs a team ahead, the other the same team behind), each leg
    in the spec's wording."""
    return [(f"{_label(a, legs)}: {story(a)[1]}", f"{_label(b, legs)}: {story(b)[1]}")
            for i, a in enumerate(legs) for b in legs[i + 1:]
            if a["game_id"] == b["game_id"] and story(a)[0] != story(b)[0]]    # same team implies same game


def fit_check(legs: list[dict]) -> list[str]:
    out = ["FIT CHECK"]
    pairs = opposing_pairs(legs)
    if not pairs:
        return out + ["No opposing pairs found."]
    for a, b in pairs:
        out += card._wrap(a) + card._wrap(b)
        out.append("These lean on opposite game stories.")
    return out + ["Both can win. Check your case for each."]


def _wins(p: float) -> str:
    """A win rate as wins in 100, one decimal, half up."""
    return card.d1(p * 100)


def money(x: float) -> str:
    """Dollars, two decimals, half up, with thousands separators."""
    return f"${card.half_up(x, '0.01'):,.2f}"


def _need_what(x: dict) -> str:
    """What one leg needs, as WHAT EACH NEEDS words it (after the name)."""
    many = card.SHOW[x["market"]][1][1]
    if x["bar"] is None:                       # the card's own out-of-range wording
        what = "any" if x["result"] == "always" else "no"
        return f"{what} workload up to {x['top']:.0f} {many} clears it."
    bar = card._work(x["bar"]) + f" {many}" + (" or fewer" if x["side"] == "under" else "")
    if x["ask"] is None:
        return f"{bar}, no recent average yet."
    d = card.difference(x["market"], x["side"], x["ask"])
    return f"{bar}, the same as recent." if d == "the same" else f"{bar}, {d} than recent."


def _need_line(x: dict, legs: list[dict]) -> str:
    return f"{_label(x, legs)}: {_need_what(x)}"


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
    if _second_team(legs):                     # Sleeper's rule (the user, 2026-10-10)
        out += [""] + card._wrap(_second_team(legs))
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
    out += [""] + card._wrap(LEGEND) + card._wrap(FOLLOW_UPS)
    return "\n".join(out)


def _second_team(legs: list[dict]) -> str:
    teams = {x["team"] for x in legs}
    if len(teams) != 1:
        return ""
    return (f"SECOND TEAM NEEDED: every leg is on {next(iter(teams))}. Sleeper takes an entry only with at "
            "least one leg from another team.")


def render_md(legs: list[dict], stake: float, payout: float, payout_from_legs: bool, cards: list[str]) -> str:
    """The entry for chat (the user's layout, 2026-10-11; DECISIONS #238): a comparison table first
    (biggest ask first, as WHAT EACH NEEDS), then each leg's chat card, then the fit check and the
    cost. The same numbers and words as render(); only the layout differs."""
    if not (stake > 0 and payout > stake):
        raise ValueError(f"an entry needs a stake above 0 and a payout above it; got {stake} and {payout}")
    n = len(legs)
    st = money(stake).replace(".00", "")
    out = [f"**Your {st} entry · {n} legs**", "", f"Return if all win: **{money(payout)}**. Includes your {st} stake."]
    if payout_from_legs:
        out += ["", "(No payout given: worked out from the legs' own prices multiplied together, not from your entry.)"]
    if _second_team(legs):
        out += ["", _second_team(legs)]
    out += ["", "| Leg | What each needs (biggest ask first) |", "|---|---|"]
    for x in sorted(legs, key=_sort_key, reverse=True):
        leg = f"{x['name']} · {card.SHOW[x['market']][0]} {x['side'].title()}" + (f" {x['line']:g}" if x.get("line") is not None else "")
        out.append(f"| {card._cell(leg)} | {card._cell(_need_what(x).rstrip('.'))} |")
    for text in cards:
        out += ["", "---", "", text]
    out += ["", "---", "", "**Fit check**", ""]
    pairs = opposing_pairs(legs)
    if not pairs:
        out.append("No opposing pairs found.")
    else:
        out += [f"{a} {b} These lean on opposite game stories." for a, b in pairs]
        out += ["", "Both can win. Check your case for each."]
    out += ["", "**Price check: each bet on its own**", ""]
    out += [f"- {_label(x, legs)}: more than {_wins(odds.break_even(x['mult']))} wins in 100." for x in legs]
    each = (stake / payout) ** (1.0 / n)        # every leg must win this often for the entry to break even
    ways = 2 ** n
    net = payout / ways - stake
    out += ["", f"**To cover the entry cost:** all must win more than {_wins(each)} in 100.", "",
            f"**If each leg hits 1 time in 2** (and no shared game effects): all {n} win 1 entry in {ways}. "
            + (f"Average loss: {money(-net)} per {st} entry." if net < 0
               else f"Average gain: {money(net)} per {st} entry."),
            "", LEGEND, "", FOLLOW_UPS]
    return "\n".join(out)


def payout_from_legs(stake: float, legs: list[dict]) -> float:
    """The legs' multipliers multiplied, times the stake (used only when the
    entry's own payout was not given, and said so on the summary)."""
    return stake * math.prod(x["mult"] for x in legs)

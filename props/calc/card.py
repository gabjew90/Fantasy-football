"""The leg card (the user's final spec, 2026-10-10): for one side of one leg,
the workload this price needs (the bar), his recent and season workload, the
rate the bar assumes, the rate needed at his recent workload, and the matchup.
Plain history and arithmetic only; no chance of its own, no verdict, no
percentages. About 40 characters wide."""

from __future__ import annotations

import math
import textwrap

from . import calc, odds
from .markets import min_own, workload_col
from .names import TEAM_NAMES
from .player import Player

# What the tests have said about each market, in plain words. Updated by hand
# when a test is read; a failed test is stated here and shows on every card.
TEST_STATUS = {
    "rush_yds": "Not yet tested: settings are the prototype's starting values.",
    "receptions": "Not yet tested: settings are the prototype's starting values.",
}


def compute(pl: Player, model: calc.Model, market: str, line: float, mult_over: float, mult_under: float,
            fixed: dict, target: float | None = None) -> dict:
    be_o, be_u = odds.break_even(mult_over), odds.break_even(mult_under)
    p_book = odds.no_vig(mult_over, mult_under)
    t_o = target if target is not None else be_o
    t_u = target if target is not None else be_u
    usual = pl.usual(market, int(fixed["usual_games"]))      # None below its minimum number of games
    # every row counts a push as void (Sleeper drops a pushed leg): each side's
    # share of the decided games; on a half-point line, its plain chance
    s_o = calc.solve_workload(model, line, t_o)
    s_u = calc.solve_workload(model, line, 1 - t_u)
    s_b = calc.solve_workload(model, line, p_book)
    r_o = calc.solve_rate(model, line, t_o, usual) if usual is not None else None
    r_u = calc.solve_rate(model, line, 1 - t_u, usual) if usual is not None else None
    out = {
        "market": market, "line": line, "mult_over": mult_over, "mult_under": mult_under,
        "break_even_over": be_o, "break_even_under": be_u, "no_vig_over": p_book,
        "target_over": t_o, "target_under": t_u,
        "solutions": {"needed_over": s_o, "needed_under": s_u, "book_expects": s_b,
                      "rate_needed_over": r_o, "rate_needed_under": r_u},
        "usual": usual, "rate": model.rate, "search_max": model.limits.search_max[model.kind],
    }
    need_o, need_u = value(out, "needed_over"), value(out, "needed_under")
    recent = pl.window.tail(int(fixed["usual_games"]))
    out["usual_games"] = len(recent)
    out["usual_min"] = int(fixed["usual_games"])
    # his plain season rate is shown only from the same minimum sample as his own rate
    out["season_min"] = min_own(market, fixed)
    out["usual_spans_seasons"] = bool(len(recent) and (recent["season"] < pl.season).any())
    out["gap_over"] = need_o - usual if need_o is not None and usual is not None else None
    out["gap_under"] = usual - need_u if need_u is not None and usual is not None else None
    return out



# per market: the bet's words, the workload unit (singular, plural), the rate's
# long and short units, and the factor from the model's rate to the shown one
SHOW = {
    "rush_yds": ("rushing yards", ("carry", "carries"), "yards a carry", "yards a carry", 1.0),
    "receptions": ("catches", ("target", "targets"), "catches per 10 targets", "catches per 10", 10.0),
}
WIDTH = 40
# cities shared by two teams keep the full name
SHARED_CITY = {"NYG", "NYJ", "LA", "LAC"}


def value(c: dict, key: str) -> float | None:
    """A search's value when it found one ("ok"), else None. The Solutions in
    c["solutions"] are the only stored copy of each result."""
    s = c["solutions"].get(key)
    return s.value if s is not None and s.status == "ok" else None


def _round(x: float) -> int:
    """Half up, so "~N" is the same N everywhere (Python rounds half to even)."""
    return int(math.floor(x + 0.5))


def shown_work(x: float) -> float:
    """A workload as the card shows it: whole from 6 up, one decimal below."""
    return float(_round(x)) if x >= 6 else math.floor(x * 10 + 0.5) / 10


def _work(x: float) -> str:
    v = shown_work(x)
    return f"~{v:.0f}" if x >= 6 else f"~{v:.1f}"


def shown_rate(x: float) -> float:
    return math.floor(x * 10 + 0.5) / 10


def _num(x: float) -> str:
    """An ask: whole when it is whole, else one decimal."""
    return f"{x:.0f}" if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


def _unit(market: str, n: float) -> str:
    one, many = SHOW[market][1]
    return one if abs(n - 1) < 1e-9 else many


def city(team: str) -> str:
    full = TEAM_NAMES.get(team, team)
    return full if team in SHARED_CITY else full.rsplit(" ", 1)[0]


def price(c: dict, side: str) -> int:
    return odds.american_from_multiplier(c[f"mult_{side}"])


def _wrap(text: str) -> list[str]:
    return textwrap.wrap(text, WIDTH) or [""]


def last_games(pl: Player, market: str, n: int) -> list[tuple]:
    """(workload, marked, row) for his last n games played, oldest first."""
    col = workload_col(market)
    return [(int(r[col]), bool(r.get("fewer_snaps", False)), r) for _, r in pl.window.tail(n).iterrows()]


def _season_count(pl: Player, market: str, side: str, bar: float) -> str:
    col = workload_col(market)
    g = pl.season_games
    if side == "over":
        n = math.ceil(bar - 1e-9)                  # the first whole number at or above the bar
        hit = int((g[col] >= n).sum())
        return f"{n}+ this season: {hit} of {len(g)}"
    n = math.floor(bar + 1e-9)
    hit = int((g[col] <= n).sum())
    return f"{n} or fewer this season: {hit} of {len(g)}"


def question(market: str, side: str, work_ask: float | None, rate_ask: float | None) -> str:
    """Card rule 10. work_ask = bar minus last-4 average and rate_ask = needed
    rate minus season rate (both from the numbers the card shows), turned
    round for an Under so a positive ask is always what the bet needs."""
    if side == "under":
        work_ask = None if work_ask is None else -work_ask
        rate_ask = None if rate_ask is None else -rate_ask
    more, less, room = ("more", "more", "fewer") if side == "over" else ("fewer", "less", "more")
    rate_words = SHOW[market][3]
    w = lambda n: f"{_num(n)} {more} {_unit(market, n)}"           # noqa: E731
    r = lambda n: f"{_num(n)} {less} {rate_words}"                 # noqa: E731
    if work_ask is None:
        return f"{r(rate_ask)}?" if rate_ask is not None and rate_ask > 0 else ""
    if rate_ask is None:
        if work_ask > 0:
            return f"{w(work_ask)}?"
        return "Workload is there." if work_ask == 0 else f"Room for {_num(-work_ask)} {room} {_unit(market, -work_ask)}?"
    if work_ask > 0 and rate_ask > 0:
        return f"{w(work_ask)}, or {r(rate_ask)}?"
    if rate_ask > 0:
        return f"Workload is there. {r(rate_ask)}?"
    if work_ask > 0:
        return f"At his season rate it clears. {w(work_ask)}?"
    if work_ask == 0:                          # an even ask: no "room for 0" (not in the spec's four cases)
        return "Workload is there at his season rate."
    return f"Room for {_num(-work_ask)} {room} {_unit(market, -work_ask)}?"


def matchup_lines(pl: Player, market: str, opp: str, lines_: dict | None, why_none: str = "") -> list[str]:
    """MATCHUP: the grade line (grades come in step C) and ESPN's spread and
    total. Display only."""
    kind = "run" if market == "rush_yds" else "pass"
    out = ["MATCHUP"]
    out += _wrap(f"{pl.team} {kind} offense [grade] vs {opp} {kind} defense [grade] (grades: step C)")
    if lines_ is None:
        out += _wrap(f"Spread and total: not available ({why_none or 'no ESPN game found'}).")
        return out
    total = f" Total {lines_['total']:g}." if lines_.get("total") is not None else " No total shown."
    if lines_.get("spread_unread"):
        out += _wrap(f"ESPN's spread reads {lines_['spread_text']!r} (not understood).{total}")
    elif lines_.get("favorite"):
        out += _wrap(f"{city(lines_['favorite'])} favored by {lines_['points']:g}.{total}")
    elif lines_.get("spread_text"):
        out += _wrap(f"No favorite (even spread).{total}")
    elif lines_.get("total") is not None:
        out += _wrap(f"No spread shown.{total}")
    else:
        out += _wrap("Spread and total: none on ESPN (removed once a game is final).")
    return out


def _title(pl: Player, c: dict, side: str) -> list[str]:
    bet = SHOW[c["market"]][0]
    return [pl.name.upper(), f"{side.title()} {c['line']:g} {bet} ({odds.fmt_american(price(c, side))})"]


def _notes(rows: list[tuple], season: int) -> list[str]:
    out = []
    for _, marked, r in rows:
        if marked:
            when = f"Week {int(r['week'])}" if int(r["season"]) == season else f"{int(r['season'])} week {int(r['week'])}"
            out += _wrap(f"* {when}: played far fewer snaps than usual.")
    return out


def _last_line(pl: Player, c: dict) -> tuple[list[str], list[tuple]]:
    n = int(c["usual_min"])
    rows = last_games(pl, c["market"], n)
    if not rows:
        return [f"No games before week {pl.week}."], rows
    vals = ", ".join(f"{w}{'*' if m else ''}" for w, m, _ in rows)
    out = []
    if len(rows) < n:
        out.append(f"Last {len(rows)}: {vals}")
        out.append(f"Short history: {len(rows)} games.")
    else:
        out.append(f"Last {n}: {vals}  (avg {_work(c['usual'])})")
    if c.get("usual_spans_seasons"):
        out.append(f"(Last {len(rows)} reach back into last season.)")
    return out, rows


def render(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
           source: str = "") -> str:
    """One side's card, in the spec's layout (card rules 1-15)."""
    m = c["market"]
    if m in pl.not_enough:
        raise ValueError(f"not enough data for {m}: use render_not_enough")
    require_side(side)
    bet, (one, many), rate_long, rate_short, k = SHOW[m]
    rate = pl.rates["ypc" if m == "rush_yds" else "catch"]
    sol = c["solutions"]
    out = []
    status = TEST_STATUS.get(m, "not tested")
    if status.startswith("Not yet tested") or status == "not tested":
        out.append("Check first: workload bar untested.")
    elif not status.startswith("Passed"):      # a failed or partial test shows on every card
        out += _wrap(f"Check first: {status}")
    out += _title(pl, c, side) + [""]
    s = sol[f"needed_{side}"]
    res = calc.side_result(side, s.status)
    top = f"{c['search_max']:.0f}"
    bar = None
    if res == "ok":
        bar = s.value
        out.append(f"Bar for this price  {_work(bar)} {many}" + (" or fewer" if side == "under" else ""))
    elif res == "always":
        out += _wrap(f"Bar for this price: any workload up to {top} {many} clears it.")
    else:
        out += _wrap(f"Bar for this price: no workload up to {top} {many} clears it.")
    last, rows = _last_line(pl, c)
    out += last
    if bar is not None:
        g = pl.season_games
        out.append(_season_count(pl, m, side, bar) if len(g) else f"No games this season before week {pl.week}.")
        if 0 < len(g) < int(c["usual_min"]):
            out.append(f"Short history: {len(g)} season games.")
    out += _wrap(f"Bar assumes {c['rate'] * k:.1f} {rate_long}.")
    b = sol["book_expects"]
    if b.status == "ok":
        out.append(f"Line implies {_work(b.value)} {many} (our math).")
    elif b.status == "high":
        out += _wrap(f"Line implies more than {top} {many} (our math).")
    else:
        out += _wrap(f"Line implies about 0 {many} (our math).")
    if m == "receptions" and pl.no_depth:
        out += _wrap(f"({pl.no_depth} of his targets had no recorded depth; left out of his depth mix.)")
    out += _notes(rows, pl.season)
    # AT ~U: the rate needed at his recent workload, his season rate, the opponent's
    need = season = None
    if c["usual"] is not None:
        out += ["", f"AT {_work(c['usual'])} {many.upper()}"]
        r = sol[f"rate_needed_{side}"]
        rr = calc.side_result(side, r.status) if r is not None else None
        if rr == "ok":
            need = shown_rate(r.value * k)
            out += _wrap(f"Needed at this price: {need:.1f} {rate_short}" + (" or less" if side == "under" else ""))
        elif rr == "always":
            out.append("Needed at this price: any rate clears it")
        else:
            out.append("Needed at this price: no rate clears it")
        if rate.season is not None and rate.season_n >= c["season_min"]:
            season = shown_rate(rate.season * k)
            out.append(f"His season:           {season:.1f}")
        else:
            out.append(f"His season:           only {rate.season_n} {many}")
        out.append(f"{city(opp)} allows:  (step C)")
    else:
        out += ["", f"Only {c['usual_games']} games: no recent average yet."]
    out += [""] + matchup_lines(pl, m, opp, game_lines, why_no_lines)
    work_ask = (shown_work(bar) - shown_work(c["usual"])) if bar is not None and c["usual"] is not None else None
    rate_ask = (need - season) if need is not None and season is not None else None
    q = question(m, side, work_ask, rate_ask)
    if q:
        out += [""] + _wrap(q)
    if source:
        out += [""] + _wrap(f"Line: {source}.")
    return "\n".join(out)


def require_side(side: str) -> None:
    if side not in ("over", "under"):
        raise ValueError(f"side is over or under, got {side!r}")


def render_not_enough(pl: Player, m: str, side: str, line: float | None, mult_over: float | None,
                      mult_under: float | None, *, source: str = "") -> str:
    """The card when a rate or pool is below its minimum sample: no bar and no
    rates, only the reason and his last games."""
    require_side(side)
    bet, many = SHOW[m][0], SHOW[m][1][1]
    head = [pl.name.upper()]
    if line is not None:
        mult = mult_over if side == "over" else mult_under
        head.append(f"{side.title()} {line:g} {bet} ({odds.fmt_american(odds.american_from_multiplier(mult))})")
    out = ["Check first: not enough data, so no bar:"]
    out += [x for why in pl.not_enough[m] for x in _wrap(f"- {why}")]
    out = head + [""] + out
    rows = last_games(pl, m, 4)
    out.append("Last games: " + (", ".join(f"{w}{'*' if mk else ''}" for w, mk, _ in rows) or "none")
               + f" ({many})")
    out += _notes(rows, pl.season)
    if source:
        out += [""] + _wrap(f"Line: {source}.")
    return "\n".join(out)

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
TEST_STATUS = {      # the user's wording after the 2024-25 held-out read (2026-10-10; numbers in "Calculation")
    "rush_yds": "Tested on 2018-25: held up where it could be checked.",
    "receptions": "Tested on 2018-25: Overs hit a bit more often than this bar implies.",
    "rec_yds": "Tested on 2018-25: roughly right, slightly strict on Overs.",
    "pass_yds": "Tested on 2018-25: the least reliable of the four. Treat the bar as rough.",
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
    "receptions": ("catches", ("target", "targets"), "catches per 10 targets", "catches per 10 targets", 10.0),
    "rec_yds": ("receiving yards", ("target", "targets"), "yards a target", "yards a target", 1.0),
    "pass_yds": ("passing yards", ("completion", "completions"), "yards a completion", "yards a completion", 1.0),
}
# the chat card's rate-table heading, per market
RATE_TITLE = {"rush_yds": "Yards per carry", "receptions": "Catches per 10 targets", "rec_yds": "Yards per target",
              "pass_yds": "Yards per completion"}
RATE_KEY = {"rush_yds": "ypc", "receptions": "catch", "rec_yds": "ypt", "pass_yds": "ypcomp"}
WIDTH = 40
# cities shared by two teams keep the full name
SHARED_CITY = {"NYG", "NYJ", "LA", "LAC"}


def value(c: dict, key: str) -> float | None:
    """A search's value when it found one ("ok"), else None. The Solutions in
    c["solutions"] are the only stored copy of each result."""
    s = c["solutions"].get(key)
    return s.value if s is not None and s.status == "ok" else None


def half_up(x: float, step: str) -> float:
    """x rounded half up to `step` ("1", "0.1", "0.5"), through its decimal
    text so a stored 0.35 (0.3499...) shows as 0.4 and 26.25 as 26.3 (the user,
    2026-10-10: half up everywhere a number is displayed)."""
    from decimal import ROUND_HALF_UP, Decimal
    d = Decimal(repr(float(x)))
    if step == "0.5":
        return float((d * 2).quantize(Decimal("1"), rounding=ROUND_HALF_UP) / 2)
    return float(d.quantize(Decimal(step), rounding=ROUND_HALF_UP))


def d1(x: float) -> str:
    """One decimal, half up."""
    return f"{half_up(x, '0.1'):.1f}"


def _round(x: float) -> int:
    """Half up, so "~N" is the same N everywhere (Python rounds half to even)."""
    return int(half_up(x, "1"))


def shown_work(x: float) -> float:
    """A workload as the card shows it: whole from 6 up, one decimal below."""
    return float(_round(x)) if x >= 6 else half_up(x, "0.1")


def _work(x: float) -> str:
    v = shown_work(x)
    return f"~{v:.0f}" if x >= 6 else f"~{v:.1f}"


def work_ask(bar: float, usual: float) -> float:
    """The workload ask as the card shows it (card rule 10 as amended): the
    bar as displayed minus the last-4 average as displayed, to the nearest
    half. One place, for the card's question and the entry summary."""
    return half_up(shown_work(bar) - half_up(usual, "0.1"), "0.5")


def shown_rate(x: float) -> float:
    return half_up(x, "0.1")


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
    """(workload, marked, row) for his last n games played, oldest first.
    Marked: far fewer snaps than usual, or a backup quarterback started."""
    col = workload_col(market)
    return [(int(r[col]), bool(r.get("fewer_snaps", False)) or bool(r.get("backup_qb", False)), r)
            for _, r in pl.window.tail(n).iterrows()]


def season_hits(pl: Player, market: str, side: str, bar: float) -> tuple[int, int, int]:
    """(the bar as a whole number of games' workload, games this season that reached it, games)."""
    col = workload_col(market)
    g = pl.season_games
    shown = shown_work(bar)                    # the bar as displayed (the user, 2026-10-10)
    if side == "over":
        n = math.ceil(shown - 1e-9)                # a shown 3.2 counts games of 4 or more
        return n, int((g[col] >= n).sum()), len(g)
    n = math.floor(shown + 1e-9)
    return n, int((g[col] <= n).sum()), len(g)


def _season_count(pl: Player, market: str, side: str, bar: float) -> str:
    n, hit, of = season_hits(pl, market, side, bar)
    return f"{n}+ this season: {hit} of {of}" if side == "over" else f"{n} or fewer this season: {hit} of {of}"


def question(market: str, side: str, work_ask: float | None, rate_ask: float | None,
             reached: int | None = None, of: int = 4) -> str:
    q = _question(market, side, work_ask, rate_ask, reached, of)
    q = q.replace(". about ", ". About ")      # each sentence starts with a capital
    return q[:1].upper() + q[1:]


def _question(market: str, side: str, work_ask: float | None, rate_ask: float | None,
              reached: int | None = None, of: int = 4) -> str:
    """Card rule 10 as amended (the user, 2026-10-10). Both asks start from his
    last-4 average workload and the rate the bar assumes, UNROUNDED: work_ask =
    bar minus last-4 average, shown to the nearest half ("about 1.5 more
    carries"); rate_ask = the rate needed at his average workload minus the
    bar's assumed rate, shown to one decimal. Each is judged as shown (a work
    ask that rounds to 0 is even). Turned round for an Under so a positive ask
    is always what the bet needs. reached: how many of his last `of` games
    reached the bar (at or above it; at or below for an Under) -- when his
    average meets the bar but fewer than 2 games did, the average is carried by
    one game and the question says so."""
    if work_ask is not None:
        work_ask = half_up(work_ask, "0.5")                    # the nearest half, half up
    if rate_ask is not None:
        rate_ask = half_up(rate_ask, "0.1")
    if work_ask is not None and reached is not None:
        meets = work_ask <= 0 if side == "over" else work_ask >= 0
        if meets and reached < 2:
            return f"Average clears it, but only {reached} of {of} games did."
    if side == "under":
        work_ask = None if work_ask is None else -work_ask
        rate_ask = None if rate_ask is None else -rate_ask
    more, less, room = ("more", "more", "fewer") if side == "over" else ("fewer", "less", "more")
    rate_words = SHOW[market][3]
    w = lambda n: f"about {_num(n)} {more} {_unit(market, n)}"     # noqa: E731
    r = lambda n: f"{_num(n)} {less} {rate_words}"                 # noqa: E731
    if work_ask is None:
        return f"{r(rate_ask)}?" if rate_ask is not None and rate_ask > 0 else ""
    if rate_ask is None:
        if work_ask > 0:
            return f"{w(work_ask)}?"
        return "Workload is there." if work_ask == 0 else f"Room for about {_num(-work_ask)} {room} {_unit(market, -work_ask)}?"
    if work_ask > 0 and rate_ask > 0:
        return f"{w(work_ask)}, or {r(rate_ask)}?"
    if rate_ask > 0:
        return f"Workload is there. {r(rate_ask)}?"
    if work_ask > 0:
        return f"At his recent rate it clears. {w(work_ask)}?"     # rate ask is against the bar's (recent) rate
    if work_ask == 0:                          # even on workload, rate there too (the user, 2026-10-10)
        return "Recent workload and rate both meet the bar."
    return f"Room for about {_num(-work_ask)} {room} {_unit(market, -work_ask)}?"


def condition(market: str, side: str, work_ask: float | None, rate_ask: float | None,
              reached: int | None = None, of: int = 4) -> str:
    """The chat card's "What needs to be true" (the user, 2026-10-11: a condition, not a question): the
    same asks as question(), taken the same way (the nearest half, one decimal, turned round for an
    Under), stated as what this side needs. "" when the question would be empty."""
    if work_ask is not None:
        work_ask = half_up(work_ask, "0.5")
    if rate_ask is not None:
        rate_ask = half_up(rate_ask, "0.1")
    if work_ask is not None and reached is not None:
        meets = work_ask <= 0 if side == "over" else work_ask >= 0
        if meets and reached < 2:
            return f"His recent average meets the bar, but only {reached} of his last {of} games did."
    if side == "under":
        work_ask = None if work_ask is None else -work_ask
        rate_ask = None if rate_ask is None else -rate_ask
    more, less, room = ("more", "more", "fewer") if side == "over" else ("fewer", "less", "more")
    rate_words = SHOW[market][3]
    w = lambda n: f"about {_num(n)} {more} {_unit(market, n)} than his recent average"    # noqa: E731
    r = lambda n: f"{_num(n)} {less} {rate_words} than the assumed rate"                 # noqa: E731
    roomy = lambda n: f"room for about {_num(n)} {room} {_unit(market, n)}"              # noqa: E731
    if work_ask is None:
        return f"He needs {r(rate_ask)}." if rate_ask is not None and rate_ask > 0 else ""
    if rate_ask is None:
        if work_ask > 0:
            return f"He needs {w(work_ask)}."
        return ("His recent workload meets the bar." if work_ask == 0
                else f"His recent workload clears the bar, with {roomy(-work_ask)}.")
    if work_ask > 0 and rate_ask > 0:
        return f"He needs {w(work_ask)}, or {r(rate_ask)} at his recent workload."
    if rate_ask > 0:
        return f"His recent workload is there; he needs {r(rate_ask)}."
    if work_ask > 0:
        return f"At his recent rate, he needs {w(work_ask)}."
    if work_ask == 0:
        return "His recent workload and rate both meet the bar."
    return f"His recent workload and rate meet the bar, with {roomy(-work_ask)}."


def matchup_lines(pl: Player, market: str, opp: str, lines_: dict | None, why_none: str = "",
                  grades: dict | None = None, qb_today: str = "") -> list[str]:
    """MATCHUP: the grade line (run for rushing cards, pass for the others)
    and the spread and total -- ESPN's, else the nflverse schedule's closing
    line, labelled. Display only. grades: {"off", "def"} grades such as "A-", or {"note"}."""
    kind = "run" if market == "rush_yds" else "pass"
    out = ["MATCHUP"]
    if grades and grades.get("off") and grades.get("def"):
        line = f"{pl.team} {kind} offense {grades['off']} vs {opp} {kind} defense {grades['def']}"
        # too wide: break at "vs", so each grade stays beside its unit
        out += [line] if len(line) <= WIDTH else [f"{pl.team} {kind} offense {grades['off']} vs",
                                                   f"{opp} {kind} defense {grades['def']}"]
    else:
        out += _wrap(f"{pl.team} {kind} offense vs {opp} {kind} defense: "
                     + ((grades or {}).get("note") or "grades not available."))
    if lines_ is None:
        out += _wrap(f"Spread and total: not available ({why_none or 'no game found'}).")
        return out + (_wrap(qb_today) if qb_today else [])
    total = f" Total {lines_['total']:g}." if lines_.get("total") is not None else " No total shown."
    if lines_.get("closing"):
        total = total.rstrip(".") + (" (closing line)." if lines_["closing"] is True else f" ({lines_['closing']}).")
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
    return out + (_wrap(qb_today) if qb_today else [])


def _title(pl: Player, c: dict, side: str) -> list[str]:
    bet = SHOW[c["market"]][0]
    return [pl.name.upper(), f"{side.title()} {c['line']:g} {bet} ({odds.fmt_american(price(c, side))})"]


def _notes(rows: list[tuple], season: int) -> list[str]:
    out = []
    for _, marked, r in rows:
        if not marked:
            continue
        when = f"Week {int(r['week'])}" if int(r["season"]) == season else f"{int(r['season'])} week {int(r['week'])}"
        if r.get("backup_qb", False):
            who = r.get("qb_started")
            out += _wrap(f"* {when}: {who} started at QB." if isinstance(who, str) and who
                         else f"* {when}: another quarterback started.")
        if r.get("fewer_snaps", False):
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
        out.append(f"Last {n}: {vals}  (avg {d1(c['usual'])})")
    if c.get("usual_spans_seasons"):
        out.append(f"(Last {len(rows)} reach back into last season.)")
    return out, rows


def _parts(pl: Player, c: dict, side: str) -> dict:
    """Every number a card shows, computed once: the text card (render) and the chat card
    (render_md) print these and nothing else, so the two cannot disagree (DECISIONS #238)."""
    m = c["market"]
    if m in pl.not_enough:
        raise ValueError(f"not enough data for {m}: use render_not_enough")
    require_side(side)
    bet, (one, many), rate_long, rate_short, k = SHOW[m]
    rate = pl.rates[RATE_KEY[m]]
    sol = c["solutions"]
    s = sol[f"needed_{side}"]
    res = calc.side_result(side, s.status)
    top = f"{c['search_max']:.0f}"
    bar = s.value if res == "ok" else None
    if bar is not None:
        bar_text = f"{_work(bar)} {many}" + (" or fewer" if side == "under" else "")
    else:
        bar_text = f"{'any' if res == 'always' else 'no'} workload up to {top} {many} clears it"
    n = int(c["usual_min"])
    rows = last_games(pl, m, n)
    g = pl.season_games
    season = season_hits(pl, m, side, bar) if bar is not None and len(g) else None
    assumed = c["rate"] * k                  # unrounded: the rate ask is taken from it
    need, need_text, season_rate = None, None, None
    if c["usual"] is not None:
        r = sol[f"rate_needed_{side}"]
        rr = calc.side_result(side, r.status) if r is not None else None
        if rr == "ok":
            need = r.value * k
            need_text = f"{shown_rate(need):.1f} {rate_short}" + (" or less" if side == "under" else "")
        else:
            need_text = f"{'any' if rr == 'always' else 'no'} rate clears it"
        if rate.season is None:
            season_rate = f"no {many} yet"
        else:                                  # below the minimum: the number with its sample, never hidden
            season_rate = f"{shown_rate(rate.season * k):.1f} {rate_long}" + (
                "" if rate.season_n >= c["season_min"] else f" ({rate.season_n} {_unit(m, rate.season_n)})")
    # both asks from the numbers as displayed (the user, 2026-10-10): the bar as shown minus the
    # last-4 average as shown, then to the nearest half; the needed rate shown minus the recent rate shown
    work_ask = (shown_work(bar) - half_up(c["usual"], "0.1")) if bar is not None and c["usual"] is not None else None
    rate_ask = (shown_rate(need) - shown_rate(assumed)) if need is not None else None    # as displayed
    reached = None
    if bar is not None and len(rows) >= n:
        sb = shown_work(bar)
        reached = sum((w >= sb) if side == "over" else (w <= sb) for w, _, _ in rows)
    return {"m": m, "bet": bet, "one": one, "many": many, "rate_long": rate_long, "k": k, "res": res, "top": top,
            "bar": bar, "bar_text": bar_text, "n": n, "rows": rows, "season_games": len(g), "season": season,
            "assumed": assumed, "assumed_text": f"{shown_rate(assumed):.1f} {rate_long}",
            "window": f"His recent rate ({len(pl.window)} games)", "need": need, "need_text": need_text,
            "season_rate": season_rate, "work_ask": work_ask, "rate_ask": rate_ask, "reached": reached}


def render(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
           footer: str = "", opp_row: dict | None = None, grades: dict | None = None, line_note: str = "",
           qb_today: str = "") -> str:
    """One side's card, in the spec's layout (card rules 1-15, as amended).
    opp_row: {"value", "games", "who"} from opponent.allows (display only);
    grades: matchup.grade_pair's result (display only); footer: one line."""
    P = _parts(pl, c, side)
    m, many = P["m"], P["many"]
    out = []
    # the test result for this bet type, first on every card (a bet type with no result says so)
    out += _wrap(TEST_STATUS.get(m, "Check first: workload bar untested."))
    if line_note:                              # the lookup skipped newer saved quotes: say so above the numbers
        out += _wrap(f"Check first: {line_note}.")
    out += _title(pl, c, side) + [""]
    if P["bar"] is not None:
        out.append(f"Bar for this price  {P['bar_text']}")
    else:
        out += _wrap(f"Bar for this price: {P['bar_text']}.")
    last, rows = _last_line(pl, c)
    out += last
    if P["bar"] is not None:
        out.append(_season_count(pl, m, side, P["bar"]) if P["season_games"]
                   else f"No games this season before week {pl.week}.")
        if 0 < P["season_games"] < P["n"]:
            out.append(f"Short history: {P['season_games']} season games.")
    window = P["window"]                       # the rate the bar assumes (blend explained in "Calculation")
    if c["usual"] is None:                    # no AT block below: the assumed rate is stated here instead
        out += _wrap(f"Bar assumes {P['assumed_text']} ({window[0].lower() + window[1:]}).")
    # "Line implies (our math)" is not on the default card (the user, 2026-10-10): it is in the
    # "Calculation" follow-up; the row returns only as Sleeper's own workload line (step G)
    out += _no_depth(pl, m)
    out += _notes(rows, pl.season)
    # AT ~U: the rate needed at his recent workload, the rate the bar assumes, his season rate, the opponent's
    if c["usual"] is not None:
        out += ["", f"AT {d1(c['usual'])} {many.upper()}"]
        out += _wrap(f"Needed at this price: {P['need_text']}")
        out += _wrap(f"{window}: {P['assumed_text']}")      # printed as the rate ask reads it
        out += _wrap(f"This season: {P['season_rate']}")
        out += _wrap(_opp_line(opp, opp_row, P["rate_long"]))
    else:
        out += ["", f"Only {c['usual_games']} games: no recent average yet."]
    out += [""] + matchup_lines(pl, m, opp, game_lines, why_no_lines, grades, qb_today)
    q = question(m, side, P["work_ask"], P["rate_ask"], P["reached"], len(rows))
    if q:
        out += [""] + _wrap(q)
    if footer:
        out += [""] + _wrap(footer)
    return "\n".join(out)


def _no_depth(pl: Player, m: str) -> list[str]:
    if m in ("receptions", "rec_yds", "pass_yds") and pl.no_depth:
        plays = "completions" if m == "pass_yds" else "targets"
        return _wrap(f"({pl.no_depth} of his {plays} had no recorded depth; left out of his depth mix.)")
    return []


def _cell(x) -> str:
    """Text safe inside one markdown table cell."""
    return " ".join(str(x).replace("|", "/").split())


def _md_title(pl: Player, bet: str, side: str, line: float | None, mult: float | None) -> list[str]:
    head = [f"**{pl.name} · {bet[0].upper() + bet[1:]}**"]
    if line is not None:
        head += ["", f"{side.title()} {line:g} {bet} · {odds.fmt_american(odds.american_from_multiplier(mult))}"]
    return head


def _md_last(rows: list[tuple]) -> str:
    return " · ".join(f"{w}{'*' if mk else ''}" for w, mk, _ in rows)


def _md_notes(rows: list[tuple], season: int) -> list[str]:
    return [x.removeprefix("* ") for x in (" ".join(_notes([r], season)) for r in rows) if x]


def render_md(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
              footer: str = "", opp_row: dict | None = None, grades: dict | None = None, line_note: str = "",
              qb_today: str = "") -> str:
    """The same card laid out for chat (the user's layout, 2026-10-11; DECISIONS #238): normal markdown,
    two-column tables, bold only on what the bet needs, and a condition instead of a question. Every
    number comes from _parts, as on the text card; nothing is added but layout and the condition."""
    P = _parts(pl, c, side)
    m, many = P["m"], P["many"]
    rows = P["rows"]
    out = _md_title(pl, P["bet"], side, c["line"], c[f"mult_{side}"]) + [""]
    out += [f"Reliability: {TEST_STATUS.get(m, 'Check first: workload bar untested.')}", ""]
    if line_note:
        out += [f"Check first: {line_note}.", ""]
    out += [f"**Average workload needed: {P['bar_text']}**", ""]
    if c["usual"] is not None and P["bar"] is not None:
        out += [f"| Workload | {many[0].upper() + many[1:]} |", "|---|---|",
                f"| Needed at this price | **{P['bar_text']}** |",
                f"| Recent {len(rows)}-game average | {d1(c['usual'])} |",
                f"| Difference from recent | {difference(m, side, work_ask(P['bar'], c['usual']))} |", ""]
    if rows:
        out.append(f"Last {len(rows)}: {_md_last(rows)}" + (" (back into last season)" if c.get("usual_spans_seasons")
                                                             else "") + "  ")
    else:
        out.append(f"No games before week {pl.week}.  ")
    if 0 < len(rows) < P["n"]:
        out.append(f"Short history: {len(rows)} games.  ")
    if P["bar"] is not None:
        if P["season"] is not None:
            n, hit, of = P["season"]
            out.append(f"{n}+ {many} this season: {hit} of {of} games" if side == "over"
                       else f"{n} or fewer {many} this season: {hit} of {of} games")
        else:
            out.append(f"No games this season before week {pl.week}.")
        if 0 < P["season_games"] < P["n"]:
            out.append(f"Short history: {P['season_games']} season games.")
    out = [x.rstrip() if i == len(out) - 1 else x for i, x in enumerate(out)]
    notes = _md_notes(rows, pl.season) + [x for x in " ".join(_no_depth(pl, m)).split("\n") if x]
    if notes:
        out += [""] + [f"* {x}" for x in notes]
    out.append("")
    if c["usual"] is not None:
        out += [f"**At his recent workload ({d1(c['usual'])} {many})**", "",
                f"| {RATE_TITLE[m]} | Rate |", "|---|---|",
                f"| Needed at this price | **{_cell(P['need_text'])}** |",
                f"| Calculator's assumed rate | {P['assumed_text']} |",
                f"| This season | {_cell(P['season_rate'])} |",
                f"| Opponent has allowed | {_cell(_opp_cell(opp_row, P['rate_long']))} |", ""]
        out += [f"Assumed rate: {P['window'][0].lower() + P['window'][1:]}, blended toward the league average "
                f"for his position. {_opp_note(opp, opp_row)}", ""]
    else:
        out += [f"Only {c['usual_games']} games: no recent average yet. The bar assumes {P['assumed_text']} "
                f"({P['window'][0].lower() + P['window'][1:]}).", ""]
    mt = " ".join(matchup_lines(pl, m, opp, game_lines, why_no_lines, grades, qb_today)[1:])
    if grades and grades.get("off") and grades.get("def"):     # the grade line ends a sentence in prose
        kind = "run" if m == "rush_yds" else "pass"
        g = f"{pl.team} {kind} offense {grades['off']} vs {opp} {kind} defense {grades['def']}"
        mt = mt.replace(g, g + ".", 1)
    out += [f"Matchup: {mt}", ""]
    cond = condition(m, side, P["work_ask"], P["rate_ask"], P["reached"], len(rows))
    if cond:
        out += [f"What needs to be true: {cond}", ""]
    if footer:
        out.append(f"_{footer}_")
    return "\n".join(out).rstrip("\n")


def difference(market: str, side: str, ask: float | None) -> str:
    """The workload ask in words, as the entry summary says it: positive = what the bet needs."""
    if ask is None:
        return "no recent average yet"
    a = ask if side == "over" else -ask
    more, fewer = ("more", "fewer") if side == "over" else ("fewer", "more")
    if a > 0:
        return f"about {_num(a)} {more}"
    if a < 0:
        return f"about {_num(-a)} {fewer}"
    return "the same"


def _opp_cell(row: dict | None, unit: str) -> str:
    if row is None or row.get("error"):
        return "not available"
    if row.get("value") is None and row.get("thin"):
        return f"only {row['games']} games"
    if row.get("value") is None:
        return f"no plays{row.get('who', '')} yet"
    return f"{d1(row['value'])} {unit}{row.get('who', '')}"


def _opp_note(opp: str, row: dict | None) -> str:
    """The opponent figure's sample, in one sentence (the text card's parenthesis)."""
    if row is None:
        return f"{city(opp)}: not available."
    if row.get("error"):
        return f"{city(opp)}: not available ({row['error']})."
    gaps = f"; {row['left_out']} plays left out (no win chance or roster listing)" if row.get("left_out") else ""
    return f"Opponent figure: {row['games']} games, garbage time left out{gaps}."


def _opp_line(opp: str, row: dict | None, unit: str = "") -> str:
    """The opponent row: same unit as the needed rate, named (display only)."""
    if row is None or row.get("error"):
        return f"{city(opp)} allows: not available" + (f" ({row['error']})" if row else "")
    if row.get("value") is None and row.get("thin"):
        return f"{city(opp)}: only {row['games']} games."
    if row.get("value") is None:
        return f"{city(opp)} allows: no plays{row.get('who', '')} yet ({row['games']} games)"
    gaps = f"; {row['left_out']} plays left out (no win chance or roster listing)" if row.get("left_out") else ""
    unit = f" {unit}" if unit else ""
    return f"{city(opp)} allows: {d1(row['value'])}{unit}{row.get('who', '')} ({row['games']} games{gaps})"


def require_side(side: str) -> None:
    if side not in ("over", "under"):
        raise ValueError(f"side is over or under, got {side!r}")


def render_not_enough(pl: Player, m: str, side: str, line: float | None, mult_over: float | None,
                      mult_under: float | None, *, footer: str = "") -> str:
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
    if footer:
        out += [""] + _wrap(footer)
    return "\n".join(out)


def render_not_enough_md(pl: Player, m: str, side: str, line: float | None, mult_over: float | None,
                         mult_under: float | None, *, footer: str = "") -> str:
    """render_not_enough laid out for chat: the reason and his last games, no bar."""
    require_side(side)
    bet, many = SHOW[m][0], SHOW[m][1][1]
    out = _md_title(pl, bet, side, line, (mult_over if side == "over" else mult_under) if line is not None else None)
    out += ["", "Check first: not enough data, so no bar:"] + [f"- {why}" for why in pl.not_enough[m]]
    rows = last_games(pl, m, 4)
    out += ["", f"Last games ({many}): {_md_last(rows) or 'none'}"]
    notes = _md_notes(rows, pl.season)
    if notes:
        out += [""] + [f"* {x}" for x in notes]
    if footer:
        out += ["", f"_{footer}_"]
    return "\n".join(out)

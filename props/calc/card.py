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
    "rec_yds": ("receiving yards", ("target", "targets"), "yards a target", "yards a target", 1.0),
}
RATE_KEY = {"rush_yds": "ypc", "receptions": "catch", "rec_yds": "ypt"}
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
    """(workload, marked, row) for his last n games played, oldest first.
    Marked: far fewer snaps than usual, or a backup quarterback started."""
    col = workload_col(market)
    return [(int(r[col]), bool(r.get("fewer_snaps", False)) or bool(r.get("backup_qb", False)), r)
            for _, r in pl.window.tail(n).iterrows()]


def _season_count(pl: Player, market: str, side: str, bar: float) -> str:
    col = workload_col(market)
    g = pl.season_games
    shown = shown_work(bar)                    # the bar as displayed (the user, 2026-10-10)
    if side == "over":
        n = math.ceil(shown - 1e-9)                # a shown 3.2 counts games of 4 or more
        hit = int((g[col] >= n).sum())
        return f"{n}+ this season: {hit} of {len(g)}"
    n = math.floor(shown + 1e-9)
    hit = int((g[col] <= n).sum())
    return f"{n} or fewer this season: {hit} of {len(g)}"


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
        work_ask = math.floor(work_ask * 2 + 0.5) / 2          # the nearest half, half up
    if rate_ask is not None:
        rate_ask = math.floor(rate_ask * 10 + 0.5) / 10
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


def matchup_lines(pl: Player, market: str, opp: str, lines_: dict | None, why_none: str = "",
                  grades: dict | None = None) -> list[str]:
    """MATCHUP: the grade line (run for rushing cards, pass for the others)
    and the spread and total -- ESPN's, else the nflverse schedule's closing
    line, labelled. Display only. grades: {"off", "def"} letters, or {"note"}."""
    kind = "run" if market == "rush_yds" else "pass"
    out = ["MATCHUP"]
    if grades and grades.get("off") and grades.get("def"):
        out += _wrap(f"{pl.team} {kind} offense {grades['off']} vs {opp} {kind} defense {grades['def']}")
    else:
        out += _wrap(f"{pl.team} {kind} offense vs {opp} {kind} defense: "
                     + ((grades or {}).get("note") or "grades not available."))
    if lines_ is None:
        out += _wrap(f"Spread and total: not available ({why_none or 'no game found'}).")
        return out
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
    return out


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
            out += _wrap(f"* {when}: backup quarterback started.")
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
        out.append(f"Last {n}: {vals}  (avg {c['usual']:.1f})")
    if c.get("usual_spans_seasons"):
        out.append(f"(Last {len(rows)} reach back into last season.)")
    return out, rows


def render(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
           footer: str = "", opp_row: dict | None = None, grades: dict | None = None, line_note: str = "") -> str:
    """One side's card, in the spec's layout (card rules 1-15, as amended).
    opp_row: {"value", "games", "who"} from opponent.allows (display only);
    grades: matchup.grade_pair's result (display only); footer: one line."""
    m = c["market"]
    if m in pl.not_enough:
        raise ValueError(f"not enough data for {m}: use render_not_enough")
    require_side(side)
    bet, (one, many), rate_long, rate_short, k = SHOW[m]
    rate = pl.rates[RATE_KEY[m]]
    sol = c["solutions"]
    out = []
    status = TEST_STATUS.get(m, "not tested")
    if status.startswith("Not yet tested") or status == "not tested":
        out.append("Check first: workload bar untested.")
    elif not status.startswith("Passed"):      # a failed or partial test shows on every card
        out += _wrap(f"Check first: {status}")
    if line_note:                              # the lookup skipped newer saved quotes: say so above the numbers
        out += _wrap(f"Check first: {line_note}.")
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
    assumed = c["rate"] * k                  # unrounded: the rate ask is taken from it
    window = f"His recent rate ({len(pl.window)} games)"     # the rate the bar assumes (blend explained in "Calculation")
    if c["usual"] is None:                    # no AT block below: the assumed rate is stated here instead
        out += _wrap(f"Bar assumes {assumed:.1f} {rate_long} ({window[0].lower() + window[1:]}).")
    # "Line implies (our math)" is not on the default card (the user, 2026-10-10): it is in the
    # "Calculation" follow-up; the row returns only as Sleeper's own workload line (step G)
    if m == "receptions" and pl.no_depth:
        out += _wrap(f"({pl.no_depth} of his targets had no recorded depth; left out of his depth mix.)")
    out += _notes(rows, pl.season)
    # AT ~U: the rate needed at his recent workload, the rate the bar assumes, his season rate, the opponent's
    need = None
    if c["usual"] is not None:
        out += ["", f"AT {c['usual']:.1f} {many.upper()}"]
        r = sol[f"rate_needed_{side}"]
        rr = calc.side_result(side, r.status) if r is not None else None
        if rr == "ok":
            need = r.value * k                 # unrounded: the rate ask is taken from it
            out += _wrap(f"Needed at this price: {need:.1f} {rate_short}" + (" or less" if side == "under" else ""))
        elif rr == "always":
            out.append("Needed at this price: any rate clears it")
        else:
            out.append("Needed at this price: no rate clears it")
        out.append(f"{window}: {assumed:.1f}")
        if rate.season is not None and rate.season_n >= c["season_min"]:
            out.append(f"This season: {shown_rate(rate.season * k):.1f}")
        else:
            out.append(f"This season: only {rate.season_n} {many}")
        out += _wrap(_opp_line(opp, opp_row))
    else:
        out += ["", f"Only {c['usual_games']} games: no recent average yet."]
    out += [""] + matchup_lines(pl, m, opp, game_lines, why_no_lines, grades)
    work_ask = (bar - c["usual"]) if bar is not None and c["usual"] is not None else None
    rate_ask = (need - assumed) if need is not None else None
    reached = None
    if bar is not None and len(rows) >= int(c["usual_min"]):
        sb = shown_work(bar)
        reached = sum((w >= sb) if side == "over" else (w <= sb) for w, _, _ in rows)
    q = question(m, side, work_ask, rate_ask, reached, len(rows))
    if q:
        out += [""] + _wrap(q)
    if footer:
        out += [""] + _wrap(footer)
    return "\n".join(out)


def _opp_line(opp: str, row: dict | None) -> str:
    """The opponent row: same unit as the needed rate (display only)."""
    if row is None or row.get("error"):
        return f"{city(opp)} allows: not available" + (f" ({row['error']})" if row else "")
    if row.get("value") is None and row.get("thin"):
        return f"{city(opp)}: only {row['games']} games."
    if row.get("value") is None:
        return f"{city(opp)} allows: no plays{row.get('who', '')} yet ({row['games']} games)"
    gaps = f"; {row['left_out']} plays left out (no win chance or roster listing)" if row.get("left_out") else ""
    return f"{city(opp)} allows: {row['value']:.1f}{row.get('who', '')} ({row['games']} games{gaps})"


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

"""The leg card: what workload the leg needs, what the book's price implies,
and how often he has had that much work. Plain history and arithmetic only;
no chance of its own, no verdict."""

from __future__ import annotations

import math
import textwrap

from . import calc, odds
from .markets import label, min_own, workload_col, workload_words
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


def _last_n(n: int) -> str:
    return "last-game" if n == 1 else f"last-{n}"


def value(c: dict, key: str) -> float | None:
    """A search's value when it found one ("ok"), else None. The Solutions in
    c["solutions"] are the only stored copy of each result."""
    s = c["solutions"].get(key)
    return s.value if s is not None and s.status == "ok" else None


def _round(x: float) -> int:
    """Half up, so "about N" is the same N everywhere (Python rounds half to even)."""
    return int(math.floor(x + 0.5))


def _w(x: float) -> str:
    return f"about {_round(x)} ({x:.1f})"


def _need_line(side: str, pct: float, s, top_w: float, words: str) -> str:
    """The "wins often enough" row for one side, worded for each search result."""
    top = f"{top_w:.0f}"
    head = f"{side} wins often enough ({pct:.0%})"
    r = calc.side_result(side.lower(), s.status)
    if r == "ok":
        return f"{head} at {_w(s.value)} {words}" + (" or fewer" if side == "Under" else "")
    if r == "always":
        return f"{head} at any workload up to {top} {words}"
    return f"{side} cannot win often enough ({pct:.0%}) at any workload up to {top} {words}"


def _rate_phrase(side: str, s, market: str) -> str:
    any_rate = "at any catch rate" if market == "receptions" else "at any yards per carry"
    r = calc.side_result(side.lower(), s.status)
    if r == "ok":
        return (f"the Over needs {_rate(market, s.value)}" if side == "Over"
                else f"the Under {_rate(market, s.value)} or less")
    return f"the {side} {'wins' if r == 'always' else 'cannot win'} often enough {any_rate}"


def _rate(market: str, r: float) -> str:
    return f"{r:.1f} a carry" if market == "rush_yds" else f"{r:.0%} caught"


def _history(pl: Player, market: str, at_least: int | None, at_most: int | None) -> list[str]:
    g = pl.season_games
    col = workload_col(market)
    words = workload_words(market)
    out = []
    if g.empty:
        return [f"No games this season before week {pl.week}."]
    if at_least is not None:
        hit = g[col] >= at_least
        out.append(f"How often he got {at_least}+ {words}: this season {int(hit.sum())} of {len(g)}")
        parts = []
        for grp in sorted(g["result_group"].dropna().unique(), key=_group_order):
            m = g["result_group"] == grp
            parts.append(f"{grp}: {int((hit & m).sum())} of {int(m.sum())}")
        if parts:
            out.append("  " + " | ".join(parts))
        qbs = g.dropna(subset=["qb_id"])
        if qbs["qb_id"].nunique() > 1:
            parts = []
            for qid, sub in qbs.groupby("qb_id", sort=False):
                parts.append(f"{sub['qb_name'].iloc[0]} starting: {int((sub[col] >= at_least).sum())} of {len(sub)}")
            out.append("  " + " | ".join(parts))
    if at_most is not None:
        low = int((g[col] <= at_most).sum())
        out.append(f"How often he got {at_most} or fewer: this season {low} of {len(g)}")
    return out


def _group_order(grp: str) -> int:
    return 0 if grp.startswith("won") else (1 if grp.startswith("within") else 2)


def _last_games(pl: Player, market: str, n: int = 5) -> str:
    col, stat = workload_col(market), {"rush_yds": "rush_yds", "receptions": "receptions"}[market]
    parts = []
    for _, r in pl.window.tail(n).iloc[::-1].iterrows():
        when = f"wk{int(r['week'])}" if r["season"] == pl.season else f"'{str(int(r['season']))[2:]} wk{int(r['week'])}"
        parts.append(f"{when} {int(r[col])}-{int(r[stat])}")
    return ", ".join(parts) if parts else "none"


def _header(pl: Player, m: str, line: float | None, mult_over: float | None, mult_under: float | None,
            source: str) -> list[str]:
    out = [f"{pl.name.upper()} ({pl.team} {pl.position}) - {label(m)} - week {pl.week}"]
    if line is not None:
        ao, au = odds.american_from_multiplier(mult_over), odds.american_from_multiplier(mult_under)
        out.append(f"Line {line:g}: Over {odds.fmt_american(ao)} ({mult_over:.2f}x) | "
                   f"Under {odds.fmt_american(au)} ({mult_under:.2f}x)")
    if source:
        out += ["  " + x for x in textwrap.wrap(f"({source})", 96)]
    return out


def render_not_enough(pl: Player, m: str, line: float | None, mult_over: float | None,
                      mult_under: float | None, *, source: str = "") -> str:
    """The card when a rate or pool is below its minimum sample: no workload
    numbers, only the reason and his plain history."""
    kind = workload_col(m)
    lines = _header(pl, m, line, mult_over, mult_under, source)
    lines.append("Not enough data, so no workload numbers for this leg:")
    lines += [f"  - {why}" for why in pl.not_enough[m]]
    lines.append(f"His last games ({kind}-{'yards' if m == 'rush_yds' else 'catches'}): {_last_games(pl, m)}")
    lines.append(f"Tested: {TEST_STATUS.get(m, 'not tested')}")
    return "\n".join(lines)


def render(pl: Player, c: dict, *, source: str = "") -> str:
    m = c["market"]
    if m in pl.not_enough:
        raise ValueError(f"not enough data for {m}: use render_not_enough")
    kind = workload_col(m)
    words = workload_words(m)
    rate = pl.rates["ypc" if m == "rush_yds" else "catch"]
    lines = _header(pl, m, c["line"], c["mult_over"], c["mult_under"], source)
    usual_rate = _rate(m, c["rate"])
    sol = c["solutions"]
    sb = sol["book_expects"]
    book = (_w(sb.value) if sb.status == "ok"
            else f"more than {c['search_max']:.0f}" if sb.status == "high" else "about 0")
    lines += [
        _need_line("Over", c["target_over"], sol["needed_over"], c["search_max"], words),
        f"  at his usual {usual_rate}",
        _need_line("Under", c["target_under"], sol["needed_under"], c["search_max"], words),
        f"Book expects: {book} {words}",
    ]
    if c["usual"] is not None:
        lines.append(f"At his {_last_n(c['usual_games'])} average of {c['usual']:.1f} {words}:")
        lines.append(f"  {_rate_phrase('Over', sol['rate_needed_over'], m)};")
        lines.append(f"  {_rate_phrase('Under', sol['rate_needed_under'], m)}")
    plays = kind
    if rate.season is not None and rate.season_n >= c["season_min"]:
        season = _rate(m, rate.season) + f" on {rate.season_n} {plays}"
    else:
        season = f"only {rate.season_n} {plays}, not enough data for a rate (needs {c['season_min']})"
    lines.append(f"His rate: blended {usual_rate} ({rate.own_n} of his own plays in his last {len(pl.window)} games)")
    lines.append(f"  this season: {season}")
    if m == "receptions" and pl.no_depth:
        lines.append(f"  ({pl.no_depth} of his targets had no recorded depth and were left out of his depth mix)")
    if m == "receptions" and pl.pools.get("targets_without_depth"):
        lines.append(f"  (the pool's {pl.pools['targets_without_depth']} targets with no recorded depth count in "
                     f"league averages, not in the depth groups)")
    # the same whole numbers the "about N" text shows
    need_o, need_u = value(c, "needed_over"), value(c, "needed_under")
    at_least = _round(need_o) if need_o is not None else None
    at_most = _round(need_u) if need_u is not None else None
    lines += _history(pl, m, at_least, at_most)
    lines.append(f"His last games ({kind}-{'yards' if m == 'rush_yds' else 'catches'}): {_last_games(pl, m)}")
    if c["usual"] is None:
        lines.append(f"His usual: only {c['usual_games']} games played, not enough data for an average "
                     f"(needs {c['usual_min']})")
    if c["gap_over"] is not None:
        g = c["gap_over"]
        n = c["usual_games"]
        if abs(g) < 0.05:
            lines.append(f"Gap: his {_last_n(n)} average ({c['usual']:.1f}) is right at what the Over needs")
        elif g > 0:
            lines.append(f"Gap: the Over needs {g:.1f} {words} more than his {_last_n(n)} average ({c['usual']:.1f})")
        else:
            lines.append(f"Gap: his {_last_n(n)} average ({c['usual']:.1f}) is already {-g:.1f} above what the "
                         f"Over needs")
        if c.get("usual_spans_seasons"):
            lines.append(f"  (his last {n} games played reach back into last season)")
    lines.append(f"Tested: {TEST_STATUS.get(m, 'not tested')}")
    return "\n".join(lines)

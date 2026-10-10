"""The leg card: what workload the leg needs, what the book's price implies,
and how often he has had that much work. Plain history and arithmetic only;
no chance of its own, no verdict."""

from __future__ import annotations

import math

from . import calc, odds
from .markets import label, workload_col, workload_words
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
    usual = pl.usual(market, int(fixed["usual_games"]))
    need_o = calc.workload_for(model, line, t_o)
    need_u = calc.workload_for(model, line, 1 - t_u)
    out = {
        "market": market, "line": line, "mult_over": mult_over, "mult_under": mult_under,
        "break_even_over": be_o, "break_even_under": be_u, "no_vig_over": p_book,
        "target_over": t_o, "target_under": t_u,
        "needed_over": need_o, "needed_under": need_u,
        "book_expects": calc.workload_for(model, line, p_book),
        "usual": usual, "rate": model.rate,
        "rate_needed_over": calc.rate_for(model, line, t_o, usual) if usual else None,
        "rate_needed_under": calc.rate_for(model, line, 1 - t_u, usual) if usual else None,
    }
    recent = pl.window.tail(int(fixed["usual_games"]))
    out["usual_games"] = int(fixed["usual_games"])
    out["usual_spans_seasons"] = bool(len(recent) and (recent["season"] < pl.season).any())
    out["gap_over"] = need_o - usual if need_o is not None and usual is not None else None
    out["gap_under"] = usual - need_u if need_u is not None and usual is not None else None
    return out


def _round(x: float) -> int:
    """Half up, so "about N" is the same N everywhere (Python rounds half to even)."""
    return int(math.floor(x + 0.5))


def _w(x: float | None, kind: str) -> str:
    if x is None:
        return f"more than {calc.SEARCH_MAX[kind]:.0f}"
    return f"about {_round(x)} ({x:.1f})"


def _rate(market: str, r: float | None) -> str:
    if r is None:
        return "out of reach"
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


def render(pl: Player, c: dict, *, source: str = "") -> str:
    m = c["market"]
    kind = workload_col(m)
    words = workload_words(m)
    ao, au = odds.american_from_multiplier(c["mult_over"]), odds.american_from_multiplier(c["mult_under"])
    rate = pl.rates["ypc" if m == "rush_yds" else "catch"]
    lines = [
        f"{pl.name.upper()} ({pl.team} {pl.position}) - {label(m)} - week {pl.week}",
        f"Line {c['line']:g}: Over {odds.fmt_american(ao)} ({c['mult_over']:.2f}x) | "
        f"Under {odds.fmt_american(au)} ({c['mult_under']:.2f}x)",
    ]
    if source:
        lines.append(f"  ({source})")
    usual_rate = _rate(m, c["rate"])
    lines += [
        f"Over wins often enough ({c['target_over']:.0%}) at {_w(c['needed_over'], kind)} {words}",
        f"  at his usual {usual_rate}",
        f"Under wins often enough ({c['target_under']:.0%}) at {_w(c['needed_under'], kind)} {words} or fewer",
        f"Book expects: {_w(c['book_expects'], kind)} {words}",
    ]
    if c["usual"] is not None:
        lines.append(f"At his last-{c['usual_games']} average of {c['usual']:.1f} {words}: the Over needs {_rate(m, c['rate_needed_over'])}, "
                     f"the Under {_rate(m, c['rate_needed_under'])} or less")
    season = _rate(m, rate.season) + f" on {rate.season_n}" if rate.season is not None else "none yet"
    lines.append(f"  His rate: blended {usual_rate} ({rate.own_n} of his own plays); this season {season}")
    # the same whole numbers the "about N" text shows
    at_least = _round(c["needed_over"]) if c["needed_over"] is not None else None
    at_most = _round(c["needed_under"]) if c["needed_under"] is not None else None
    lines += _history(pl, m, at_least, at_most)
    lines.append(f"His last games ({kind}-{'yards' if m == 'rush_yds' else 'catches'}): {_last_games(pl, m)}")
    if c["gap_over"] is not None:
        g = c["gap_over"]
        n = c["usual_games"]
        lines.append(f"Gap: the Over needs {g:.1f} {words} more than his last-{n} average ({c['usual']:.1f})"
                     if g > 0 else
                     f"Gap: his last-{n} average ({c['usual']:.1f}) is already {-g:.1f} above what the Over needs")
        if c.get("usual_spans_seasons"):
            lines.append(f"  (his last {n} games played reach back into last season)")
    lines.append(f"Tested: {TEST_STATUS.get(m, 'not tested')}")
    return "\n".join(lines)

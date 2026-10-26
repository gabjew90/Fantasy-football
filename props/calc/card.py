"""The leg card (the user's final spec, 2026-10-10): for one side of one leg,
the workload this price needs (the bar), his recent and season workload, the
rate the bar assumes, the rate needed at his recent workload, and the matchup.
Plain history and arithmetic only; no chance of its own, no verdict, no
percentages. About 40 characters wide."""

from __future__ import annotations

import math
import re
import textwrap

from . import calc, odds
import pandas as pd

from .markets import min_own, stat_col, workload_col
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
        "script_spread": float(fixed["script_spread"]),
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



# per market: the bet's words, the workload unit (singular, plural), the rate's unit (one, named on
# every rate line: the user, 2026-10-11), and the factor from the model's rate to the shown one
SHOW = {
    "rush_yds": ("rushing yards", ("carry", "carries"), "yards a carry", 1.0),
    "receptions": ("catches", ("target", "targets"), "catches per 10 targets", 10.0),
    "rec_yds": ("receiving yards", ("target", "targets"), "yards a target", 1.0),
    "pass_yds": ("passing yards", ("completion", "completions"), "yards a completion", 1.0),
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
    return [(int(r[col]), bool(r.get("fewer_snaps", False)) or bool(r.get("backup_qb", False))
             or bool(r.get("lineup_mark", False)), r)
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


def rate_split(market: str, side: str, longer: float | None, season: float | None, need: float | None) -> str:
    """The closing's rate sentence when his longer-run rate (the one the bar assumes) and this season's
    rate, both as printed, fall on opposite sides of the needed rate (DECISIONS #239): the card may not
    say the rate meets the bar while another rate on it says otherwise. "" when they agree, or when a
    number is missing (no needed rate, no season rate at its minimum sample). Meeting the needed rate
    counts as clearing it; an Under clears at or below it."""
    if longer is None or season is None or need is None:
        return ""
    ok = (lambda x: x >= need) if side == "over" else (lambda x: x <= need)       # noqa: E731
    if ok(longer) == ok(season):
        return ""
    unit = SHOW[market][2]
    if ok(longer):
        return f"Rate clears at his longer-run {longer:.1f} {unit}, not at this season's {season:.1f}."
    return f"Rate clears at this season's {season:.1f} {unit}, not at his longer-run {longer:.1f}."


def _split_work(market: str, side: str, work_ask: float | None, reached: int | None, of: int, chat: bool) -> str:
    """The workload half of a split closing, from the same ask the question takes (nearest half, as shown)."""
    if work_ask is None:
        return ""
    work_ask = half_up(work_ask, "0.5")
    meets = work_ask <= 0 if side == "over" else work_ask >= 0
    if meets and reached is not None and reached < 2:
        return (f"His recent average meets the bar, but only {reached} of his last {of} games did." if chat
                else f"Average clears it, but only {reached} of {of} games did.")
    a = work_ask if side == "over" else -work_ask
    if a <= 0:
        return "His recent workload is there." if chat else "Workload is there."
    more = "more" if side == "over" else "fewer"
    return (f"He needs about {_num(a)} {more} {_unit(market, a)} than his recent average." if chat
            else f"About {_num(a)} {more} {_unit(market, a)}.")


def question(market: str, side: str, work_ask: float | None, rate_ask: float | None,
             reached: int | None = None, of: int = 4, split: str = "") -> str:
    if split:                                  # the two printed rates disagree: say so, never "rate meets"
        return " ".join(x for x in (_split_work(market, side, work_ask, reached, of, False), split) if x)
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
    rate_words = SHOW[market][2]
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
        return f"At his longer-run rate it clears. {w(work_ask)}?"     # rate ask is against the bar's rate
    if work_ask == 0:                          # even on workload, rate there too (the user, 2026-10-10)
        return "Recent workload and rate both meet the bar."
    return f"Room for about {_num(-work_ask)} {room} {_unit(market, -work_ask)}?"


def condition(market: str, side: str, work_ask: float | None, rate_ask: float | None,
              reached: int | None = None, of: int = 4, split: str = "") -> str:
    """The chat card's "What needs to be true" (the user, 2026-10-11: a condition, not a question): the
    same asks as question(), taken the same way (the nearest half, one decimal, turned round for an
    Under), stated as what this side needs. "" when the question would be empty. split: rate_split()'s
    sentence, which replaces the rate half when the card's two rates disagree."""
    if split:
        return " ".join(x for x in (_split_work(market, side, work_ask, reached, of, True), split) if x)
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
    rate_words = SHOW[market][2]
    w = lambda n: f"about {_num(n)} {more} {_unit(market, n)} than his recent average"    # noqa: E731
    r = lambda n: (f"{_num(n)} more {rate_words} than his longer-run rate" if side == "over"     # noqa: E731
                   else f"{_num(n)} {rate_words} less than his longer-run rate")
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
        return f"At his longer-run rate, he needs {w(work_ask)}."
    if work_ask == 0:
        return "His recent workload and rate both meet the bar."
    return f"His recent workload and rate meet the bar, with {roomy(-work_ask)}."


def grade_line(pl: Player, market: str, opp: str, grades: dict) -> str:
    kind = "run" if market == "rush_yds" else "pass"
    return f"{pl.team} {kind} offense {grades['off']} vs {opp} {kind} defense {grades['def']}"


def matchup_lines(pl: Player, market: str, opp: str, lines_: dict | None, why_none: str = "",
                  grades: dict | None = None, qb_today: str = "", grades_all: list | None = None,
                  scoring: dict | None = None) -> list[str]:
    """MATCHUP: the grade line (run for rushing cards, pass for the others)
    and the spread and total -- ESPN's, else the nflverse schedule's closing
    line, labelled. Display only. grades: {"off", "def"} grades such as "A-", or {"note"}."""
    kind = "run" if market == "rush_yds" else "pass"
    out = ["3 MATCHUP"]
    if grades_all:
        pass                                   # every pairing is printed below (matchup_extra)
    elif grades and grades.get("off") and grades.get("def"):
        line = grade_line(pl, market, opp, grades)
        # too wide: break at "vs", so each grade stays beside its unit
        out += [line] if len(line) <= WIDTH else [f"{pl.team} {kind} offense {grades['off']} vs",
                                                   f"{opp} {kind} defense {grades['def']}"]
    else:
        out += _wrap(f"{pl.team} {kind} offense vs {opp} {kind} defense: "
                     + ((grades or {}).get("note") or "grades not available."))
    out += _wrap(spread_sentence(lines_, why_none))
    for label, val in matchup_extra(pl.team, opp, lines_, grades_all, scoring, qb_today):
        out += _wrap(f"{label}: {val}")
    return out + (_wrap(qb_today) if qb_today else [])


def _grade_cell(gr: dict) -> str:
    return f"{gr['off']} vs {gr['def']}" if gr.get("off") and gr.get("def") else (gr.get("note") or "not available")


def matchup_extra(team: str, opp: str, lines_: dict | None, grades_all: list | None,
                  scoring: dict | None, qb_today: str = "") -> list[tuple[str, str]]:
    """Part 3's rows beyond the grade line and the spread (DECISIONS #249): every unit pairing (both
    teams' run and pass offense against the other's defense), each team's implied points, and each
    team's points scored and allowed a game this season. grades_all: [(offense, defense, kind, grades)]."""
    out_qb = qb_today.removesuffix(" ruled Out.") if qb_today.endswith(" ruled Out.") else ""
    rows = [(f"{o} {k} offense vs {d} {k} defense", _grade_cell(g)
             + (f" (graded with {out_qb}, who is Out)" if out_qb and o == team and g.get("off") else ""))
            for o, d, k, g in (grades_all or [])]
    imp = implied_totals(lines_, team, opp)
    if imp is not None:
        rows.append(("Implied points", f"{team} {d1(imp[team])}, {opp} {d1(imp[opp])}"))
    for t in (team, opp):
        sc = (scoring or {}).get(t)
        if sc is not None and sc[2]:
            rows.append((f"{t} this season", team_points_text(t, sc)))
    return rows


def spread_sentence(lines_: dict | None, why_none: str = "") -> str:
    """The spread and total in one sentence -- ESPN's, else the nflverse schedule's line, labelled. One
    source for the text card, the chat card's matchup table and the screen's game line."""
    if lines_ is None:
        return f"Spread and total: not available ({why_none or 'no game found'})."
    total = f" Total {lines_['total']:g}." if lines_.get("total") is not None else " No total shown."
    if lines_.get("closing"):
        total = total.rstrip(".") + (" (closing line)." if lines_["closing"] is True else f" ({lines_['closing']}).")
    if lines_.get("spread_unread"):
        return f"ESPN's spread reads {lines_['spread_text']!r} (not understood).{total}"
    if lines_.get("favorite"):
        return f"{city(lines_['favorite'])} favored by {lines_['points']:g}.{total}"
    if lines_.get("spread_text"):
        return f"No favorite (even spread).{total}"
    if lines_.get("total") is not None:
        return f"No spread shown.{total}"
    return "Spread and total: none on ESPN (removed once a game is final)."


# ---- the four-part read (the user's spec, 2026-10-26; DECISIONS #249) ----
# 1 the line and where the book puts 50/50, against his history; 2 this season (or his last games), with
# the special games named and left out of a second average; 3 the matchup; 4 does it hold up: the facts
# of 1-3 sorted by whether they point to the line being set high or low. Facts only: no chance, no verdict.

STAT_HEAD = {"rush_yds": "Rush yds", "receptions": "Catches", "rec_yds": "Rec yds", "pass_yds": "Pass yds"}
RATE_HEAD = {"rush_yds": "Yds/carry", "receptions": "Catches/10 tgts", "rec_yds": "Yds/target",
             "pass_yds": "Yds/comp"}


def implied_totals(lines_: dict | None, team: str, opp: str) -> dict | None:
    """Each team's implied points from the total and the spread ({team: points}), or None when the game
    has no total, an unread spread, or a favorite that is neither team."""
    if not lines_ or lines_.get("total") is None or lines_.get("spread_unread"):
        return None
    t, fav = float(lines_["total"]), lines_.get("favorite")
    if not fav:                                # an even spread splits the total; no spread at all says nothing
        return {team: t / 2, opp: t / 2} if lines_.get("spread_text") else None
    if fav not in (team, opp):
        return None
    pts = float(lines_.get("points") or 0)
    dog = opp if fav == team else team
    return {fav: (t + pts) / 2, dog: (t - pts) / 2}


def _agg(rows: list[dict], k: float) -> dict | None:
    if not rows:
        return None
    work = sum(r["work"] for r in rows)
    stat = sum(r["stat"] for r in rows)
    return {"n": len(rows), "work": work / len(rows), "stat": stat / len(rows),
            "rate": (stat / work * k) if work else None}


def season_read(pl: Player, c: dict) -> dict | None:
    """Part 2's numbers: one row per game of pl.perf (this season's games, or his last games when this
    season has too few) with what was special about it, the averages with and without the special games,
    and how often he went over and under the line. Special: left early (fewer snaps and listed for the
    next game), a lineup change (lineup_detail's reasons), or -- on a quarterback's card -- a game he did
    not start. None with no games."""
    g = pl.perf
    if g is None or not len(g):
        return None
    m = c["market"]
    wcol, scol, k = workload_col(m), stat_col(m), SHOW[m][3]
    rows = []
    for _, r in g.iterrows():
        notes = list(r.get("reasons") or [])
        if bool(r.get("left_early", False)):
            notes.insert(0, f"left early ({r.get('hurt_next')} next game)")
        q = r.get("qb_id")
        if pl.position == "QB" and isinstance(q, str) and q and q != pl.gsis_id:
            notes.append("did not start")
        special = bool(notes)
        if bool(r.get("fewer_snaps", False)) and not bool(r.get("left_early", False)):
            notes.append("far fewer snaps, no injury listing")
        snap = r.get("snap_pct")
        rows.append({"season": int(r["season"]), "week": int(r["week"]), "opp": r.get("opp") or "",
                     "work": int(r[wcol]), "stat": float(r[scol]),
                     "snap": float(snap) if snap is not None and pd.notna(snap) else None,
                     "notes": notes, "special": special})
    clean = [r for r in rows if not r["special"]]
    line = c["line"]
    return {"scope": pl.perf_scope, "rows": rows, "all": _agg(rows, k), "clean": _agg(clean, k),
            "special_weeks": [_wk(r, pl.season) for r in rows if r["special"]],
            "over": sum(r["stat"] > line for r in rows), "under": sum(r["stat"] < line for r in rows),
            "over_clean": sum(r["stat"] > line for r in clean), "under_clean": sum(r["stat"] < line for r in clean),
            "spans_seasons": any(r["season"] != pl.season for r in rows), "n_season": len(pl.season_games)}


def _wk(r: dict, season: int) -> str:
    return f"week {r['week']}" if r["season"] == season else f"{r['season']} week {r['week']}"


def _scope(S: dict) -> str:
    return "this season" if S["scope"] == "season" else f"in his last {S['all']['n']} games"


def _weeks(ws: list[str]) -> str:
    """["week 2", "week 3"] -> "weeks 2 and 3"; a week from another season keeps its year."""
    if all(w.startswith("week ") for w in ws):
        nums = [w[5:] for w in ws]
        return f"week {nums[0]}" if len(nums) == 1 else f"weeks {', '.join(nums[:-1])} and {nums[-1]}"
    return ws[0] if len(ws) == 1 else f"{', '.join(ws[:-1])} and {ws[-1]}"


def _without_special(S: dict) -> str:
    return f"without {_weeks(S['special_weeks'])}"


def _of(S: dict, x: int, n: int) -> str:
    """'3 of 6 games this season' or '1 of his last 4 games'."""
    return f"{x} of {n} games this season" if S["scope"] == "season" else f"{x} of his last {n} games"


def _bar_cell(c: dict, side: str) -> str:
    s = c["solutions"][f"needed_{side}"]
    res = calc.side_result(side, s.status)
    many = SHOW[c["market"]][1][1]
    if res == "ok":
        return f"{_work(s.value)} {many}" + (" or fewer" if side == "under" else "")
    return f"{'any' if res == 'always' else 'no'} workload up to {c['search_max']:.0f} {many} clears it"


def line_part(pl: Player, c: dict, side: str) -> list[tuple[str, str]]:
    """Part 1 as (label, value) rows, shared by both cards: the line and both prices, the book's split
    with the margin removed (the book's numbers), the workload that split implies (our math), his
    workload and how often he went over or under the line, and the other side's bar."""
    m = c["market"]
    bet, (one, many) = SHOW[m][0], SHOW[m][1]
    po, pu = odds.fmt_american(price(c, "over")), odds.fmt_american(price(c, "under"))
    p = c["no_vig_over"]
    over = half_up(p * 100, "1")                # the Under is the rest, so the two always add to 100
    rows = [("Line", f"{c['line']:g} {bet}, Over {po} / Under {pu}"),
            ("The book's 50/50, margin removed", f"Over {over:.0f}% / Under {100 - over:.0f}% (the book's numbers)")]
    b = value(c, "book_expects")
    rows.append(("Workload at the book's split (our math)",
                 f"{_work(b)} {many}" if b is not None else "not found in the calculator's range"))
    S = season_read(pl, c)
    if S is not None:
        a, cl = S["all"], S["clean"]
        work = f"{d1(a['work'])} a game"
        if S["special_weeks"]:
            work += f"; {d1(cl['work'])} {_without_special(S)}" if cl else "; every game was special"
        rows.append((f"His {many} {_scope(S)}", work))
        word = "Over" if side == "over" else "Under"
        x, xc = S[side], S[f"{side}_clean"]
        beat = _of(S, x, a["n"])
        if S["special_weeks"] and cl:
            beat += f"; {xc} of {cl['n']} {_without_special(S)}"
        rows.append((f"{word} {c['line']:g}", beat))
    other = "under" if side == "over" else "over"
    rows.append((f"{other.title()} needs at its price ({odds.fmt_american(price(c, other))})", _bar_cell(c, other)))
    return rows


def season_table(pl: Player, c: dict, S: dict) -> tuple[list[str], list[list[str]]]:
    """Part 2's table: header and one row of cells per game, shared by both cards."""
    m = c["market"]
    k = SHOW[m][3]
    head = ["Week", "Opp", SHOW[m][1][1].title(), STAT_HEAD[m], RATE_HEAD[m], "Snaps", "Note"]
    body = []
    for r in S["rows"]:
        wk = str(r["week"]) if r["season"] == pl.season else f"{r['season']} wk {r['week']}"
        rate = d1(r["stat"] / r["work"] * k) if r["work"] else "-"
        snap = f"{half_up(r['snap'] * 100, '1'):.0f}%" if r["snap"] is not None else "-"
        note = "; ".join(r["notes"]) or "-"
        body.append([wk, r["opp"] or "-", str(r["work"]), _num(r["stat"]), rate, snap,
                     ("SPECIAL: " if r["special"] else "") + note])
    return head, body


def season_lines(c: dict, S: dict) -> list[str]:
    """Part 2's averages, with and without the special games."""
    m = c["market"]
    bet, many, unit = SHOW[m][0], SHOW[m][1][1], SHOW[m][2]

    def avg(a):
        rate = f", {d1(a['rate'])} {unit}" if a["rate"] is not None else ""
        return f"{d1(a['work'])} {many}, {d1(a['stat'])} {bet}{rate} ({a['n']} games)"
    out = [f"Average {_scope(S)}: {avg(S['all'])}."]
    if S["special_weeks"]:
        out.append(f"Average {_without_special(S)} (the special games): {avg(S['clean'])}." if S["clean"]
                   else "Every game had something special; no second average.")
    if S["scope"] != "season":
        k = S["n_season"]
        out.append(f"Only {k} game{'' if k == 1 else 's'} this season, so this is his last {S['all']['n']}"
                   + (", back into last season." if S["spans_seasons"] else "."))
    return out


def team_points_text(team: str, sc) -> str:
    pf, pa, n = sc
    return f"{d1(pf)} scored, {d1(pa)} allowed a game ({n} games)"


def holds_up(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None, opp_row: dict | None,
             grades: dict | None, qb_today: str, scoring: dict | None, fixed_spread: float) -> tuple[list, list]:
    """Part 4: the facts of parts 1-3, each sorted by the direction it points -- the line set high (his
    history or the game says less than the line) or set low. Every fact is a number printed in parts 1-3;
    nothing is weighed or counted, and no side is named."""
    m = c["market"]
    bet, many, unit = SHOW[m][0], SHOW[m][1][1], SHOW[m][2]
    high, low = [], []
    line = c["line"]
    S = season_read(pl, c)
    if S is not None:
        a, cl = S["all"], S["clean"]
        n = a["n"]
        if S["over"] * 2 != n:
            (low if S["over"] * 2 > n else high).append(f"He went over {line:g} in {_of(S, S['over'], n)}.")
        use, tag = (cl, f" {_without_special(S)}") if S["special_weeks"] and cl else (a, "")
        if S["special_weeks"] and not cl:
            tag = ", every game with something special"
        if S["special_weeks"] and cl and S["over_clean"] * 2 != cl["n"]:
            (low if S["over_clean"] * 2 > cl["n"] else high).append(
                f"{_without_special(S)[0].upper() + _without_special(S)[1:]}, over {line:g} in {S['over_clean']} of {cl['n']}.")
        st = half_up(use["stat"], "0.1")
        if st != line:
            (low if st > line else high).append(f"He averaged {d1(use['stat'])} {bet} {_scope(S)}{tag}, against a {line:g} line.")
        b = value(c, "book_expects")
        if b is not None:
            bs, ws = shown_work(b), half_up(use["work"], "0.1")
            if bs != ws:
                (high if bs > ws else low).append(
                    f"The book's 50/50 needs about {_work(b)[1:]} {many} (our math); he averaged {d1(use['work'])}{tag}.")
    if opp_row and opp_row.get("value") is not None and not opp_row.get("error"):
        ov, mine = half_up(opp_row["value"], "0.1"), half_up(c["rate"] * SHOW[m][3], "0.1")
        if ov != mine:
            (low if ov > mine else high).append(
                f"{city(opp)} has allowed {d1(opp_row['value'])} {unit}{opp_row.get('who', '')}; "
                f"his longer-run rate is {mine:.1f}.")
    kind = "run" if m == "rush_yds" else "pass"
    gr = grades or {}
    if gr.get("off") and gr.get("def") and not str(qb_today).endswith(" ruled Out."):
        from .screen import grade_rank
        o, d = grade_rank(gr["off"]), grade_rank(gr["def"])
        if o is not None and d is not None and o != d:
            (low if o < d else high).append(f"{pl.team} {kind} offense {gr['off']} vs {opp} {kind} defense {gr['def']}.")
    imp = implied_totals(game_lines, pl.team, opp)
    sc = (scoring or {}).get(pl.team)
    if imp is not None and sc is not None and sc[2]:
        it, pf = half_up(imp[pl.team], "0.1"), half_up(sc[0], "0.1")
        if it != pf:
            (low if it > pf else high).append(f"{pl.team} is implied {it:.1f} points; it has scored {pf:.1f} a game.")
    if game_lines and game_lines.get("favorite") in (pl.team, opp) and not game_lines.get("spread_unread"):
        pts = float(game_lines.get("points") or 0)
        if pts >= fixed_spread:
            fav = game_lines["favorite"] == pl.team
            who = f"{pl.team} is favored by {pts:g}" if fav else f"{pl.team} is a {pts:g}-point underdog"
            general = "a general tendency, not his own history"
            if m == "rush_yds":
                why = "teams ahead tend to run more" if fav else "teams behind tend to run less"
                (low if fav else high).append(f"{who}: {why} ({general}).")
            else:
                why = "teams ahead tend to throw less" if fav else "teams behind tend to throw more"
                (high if fav else low).append(f"{who}: {why} ({general}).")
    return high, low


HOLDS_NOTE = "Sorted from parts 1-3, not weighed: none of this is tested, and it is not a chance."


def matchup_md(pl: Player, market: str, opp: str, lines_: dict | None, why_none: str = "",
               grades: dict | None = None, qb_today: str = "", grades_all: list | None = None,
               scoring: dict | None = None) -> list[str]:
    """The chat card's matchup (the user, 2026-10-11: the grades and the spread must be easy to find): a
    two-column table of the same facts the text card's MATCHUP block prints. With grades_all, every unit
    pairing replaces the one grade line (part 3, DECISIONS #249)."""
    kind = "run" if market == "rush_yds" else "pass"
    out = ["**3 · Matchup**", "", "| Matchup | This game |", "|---|---|"]
    if grades_all:
        pass                                   # every pairing is printed below, with the implied points
    elif grades and grades.get("off") and grades.get("def"):
        out += [f"| {pl.team} {kind} offense | {_cell(grades['off'])} |", f"| {opp} {kind} defense | {_cell(grades['def'])} |"]
    else:
        out.append(f"| {pl.team} {kind} offense vs {opp} {kind} defense | "
                   f"{_cell((grades or {}).get('note') or 'grades not available.')} |")
    out.append(f"| Spread and total | {_cell(spread_sentence(lines_, why_none))} |")
    out += [f"| {_cell(a)} | {_cell(b)} |" for a, b in matchup_extra(pl.team, opp, lines_, grades_all, scoring,
                                                                       qb_today)]
    if qb_today:
        out.append(f"| Quarterback | {_cell(qb_today)} |")
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
        out.append(f"Last {n}: {vals}  (avg {d1(c['usual'])}{_without(rows)})")
        kept = sum(1 for _, _, r in rows if not r.get("lineup_mark", False))
        if kept < 3:
            out.append(f"Short history: {kept} game{'' if kept == 1 else 's'} without a lineup change.")
    if c.get("usual_spans_seasons"):
        out.append(f"(Last {len(rows)} reach back into last season.)")
    return out, rows


def _without(rows: list[tuple]) -> str:
    """'; 2.0 without the 2 games with a lineup change' -- the lineup check's second average (DECISIONS
    #247), or ''."""
    clean = [w for w, _, r in rows if not r.get("lineup_mark", False)]
    k = len(rows) - len(clean)
    if not k:
        return ""
    if not clean:
        return f"; every one of the {len(rows)} had a lineup change"
    return f"; {d1(sum(clean) / len(clean))} without the {k} game{'s' if k > 1 else ''} with a lineup change"


def _parts(pl: Player, c: dict, side: str) -> dict:
    """Every number a card shows, computed once: the text card (render) and the chat card
    (render_md) print these and nothing else, so the two cannot disagree (DECISIONS #238)."""
    m = c["market"]
    if m in pl.not_enough:
        raise ValueError(f"not enough data for {m}: use render_not_enough")
    require_side(side)
    bet, (one, many), rate_long, k = SHOW[m]
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
            need_text = f"{shown_rate(need):.1f} {rate_long}" + (" or less" if side == "under" else "")
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
    # the lineup check (DECISIONS #247): the last-4 average without the games whose lineup differs from
    # today's (a main teammate out then and active now, or playing then and Out now; the starting QB the
    # same), and the ask against it. A low-snap star alone does not remove a game. Display and the screen only.
    clean = [w for w, _, r in rows if not r.get("lineup_mark", False)] if c["usual"] is not None else []
    marked = sum(1 for _, _, r in rows if r.get("lineup_mark", False)) if c["usual"] is not None else 0
    usual_clean = (sum(clean) / len(clean)) if clean else None
    work_ask_clean = ((shown_work(bar) - half_up(usual_clean, "0.1")) if bar is not None and usual_clean is not None
                      else None)
    reached = None
    if bar is not None and len(rows) >= n:
        sb = shown_work(bar)
        reached = sum((w >= sb) if side == "over" else (w <= sb) for w, _, _ in rows)
    # the rate the bar assumes, labelled as what it is: his longer run, not his recent form; when more
    # than half of those games are from before this season, the label says so (as the Last 4 line does)
    win = pl.window
    earlier = int((win["season"] < pl.season).sum()) if len(win) and "season" in win else 0
    when = ""
    if earlier * 2 > len(win):
        when = f", {earlier} from last season" if (win["season"] >= pl.season - 1).all() else \
            f", {earlier} from earlier seasons"
    season_shown = (shown_rate(rate.season * k) if c["usual"] is not None and rate.season is not None
                    and rate.season_n >= c["season_min"] else None)
    split = rate_split(m, side, shown_rate(assumed), season_shown, shown_rate(need) if need is not None else None)
    return {"m": m, "bet": bet, "one": one, "many": many, "rate_long": rate_long, "k": k, "res": res, "top": top,
            "bar": bar, "bar_text": bar_text, "n": n, "rows": rows, "season_games": len(g), "season": season,
            "assumed": assumed, "assumed_text": f"{shown_rate(assumed):.1f} {rate_long}",
            "window": f"His longer-run rate ({len(win)} games{when})", "need": need, "need_text": need_text,
            "season_rate": season_rate, "work_ask": work_ask, "rate_ask": rate_ask, "reached": reached,
            "split": split, "marked": marked, "n_clean": len(clean), "usual_clean": usual_clean,
            "work_ask_clean": work_ask_clean}


def render(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
           footer: str = "", opp_row: dict | None = None, grades: dict | None = None, line_note: str = "",
           qb_today: str = "", grades_all: list | None = None, scoring: dict | None = None) -> str:
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
    out.append("1 THE LINE")
    for label, val in line_part(pl, c, side):
        out += _wrap(f"{label}: {val}")
    out.append("")
    if P["bar"] is not None:
        out.append(f"Bar for this price  {P['bar_text']}")
    else:
        out += _wrap(f"Bar for this price: {P['bar_text']}.")
    S = season_read(pl, c)
    out += ["", "2 THIS SEASON" if S is None or S["scope"] == "season" else "2 HIS LAST GAMES"]
    if S is None:
        out.append(f"No games before week {pl.week}.")
    else:
        head, body = season_table(pl, c, S)
        for cells in body:
            wk = f"Wk {cells[0]}" if cells[0].isdigit() else cells[0]
            out += _wrap(f"{wk} {cells[1]}: {cells[2]} {many}, {cells[3]} {STAT_HEAD[m].lower()}, "
                         f"{cells[4]} {RATE_HEAD[m].lower()}, snaps {cells[5]}")
            if cells[6] != "-":
                out += _wrap(f"  {cells[6]}")
        for x in season_lines(c, S):
            out += _wrap(x)
    out.append("")
    last, rows = _last_line(pl, c)
    out += last
    if P["bar"] is not None:
        out.append(_season_count(pl, m, side, P["bar"]) if P["season_games"]
                   else f"No games this season before week {pl.week}.")
        if 0 < P["season_games"] < P["n"]:
            out.append(f"Short history: {P['season_games']} season games.")
    window = P["window"]                       # the rate the bar assumes (blend explained in "Calculation")
    if c["usual"] is None:                    # no AT block below: the assumed rate is stated here instead
        out += _wrap(f"Bar assumes {P['assumed_text']}: {window[0].lower() + window[1:]}.")
    # "Line implies (our math)" is not on the default card (the user, 2026-10-10): it is in the
    # "Calculation" follow-up; the row returns only as Sleeper's own workload line (step G)
    out += _no_depth(pl, m)
    out += _notes(rows, pl.season)
    for x in pl.lineup:                                   # the lineup check's causes (DECISIONS #247)
        out += _wrap(x)
    # AT ~U: the rate needed at his recent workload, the rate the bar assumes, his season rate, the opponent's
    if c["usual"] is not None:
        out += ["", f"AT {d1(c['usual'])} {many.upper()}"]
        out += _wrap(f"Needed at this price: {P['need_text']}")
        out += _wrap(f"{window}: {P['assumed_text']}")      # printed as the rate ask reads it
        out += _wrap(f"This season: {P['season_rate']}")
        out += _wrap(_opp_line(opp, opp_row, P["rate_long"]))
    else:
        out += ["", f"Only {c['usual_games']} games: no recent average yet."]
    out += [""] + matchup_lines(pl, m, opp, game_lines, why_no_lines, grades, qb_today, grades_all, scoring)
    high, low = holds_up(pl, c, side, opp=opp, game_lines=game_lines, opp_row=opp_row, grades=grades,
                         qb_today=qb_today, scoring=scoring, fixed_spread=c["script_spread"])
    out += ["", "4 DOES IT HOLD UP"]
    for head_, facts in (("Points to the line set high:", high), ("Points to it set low:", low)):
        out.append(head_)
        for x in facts or ["nothing on this card"]:
            out += _wrap(f"- {x}")
    out += _wrap(HOLDS_NOTE)
    q = question(m, side, P["work_ask"], P["rate_ask"], P["reached"], len(rows), P["split"])
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
    """The text card's marked-game notes, unwrapped, one per bullet."""
    text = " ".join(_notes(rows, season))
    return [x.strip() for x in re.split(r"(?:^| )\* ", text) if x.strip()]


def render_md(pl: Player, c: dict, side: str, *, opp: str, game_lines: dict | None = None, why_no_lines: str = "",
              footer: str = "", opp_row: dict | None = None, grades: dict | None = None, line_note: str = "",
              qb_today: str = "", matchup: bool = True, grades_all: list | None = None,
              scoring: dict | None = None) -> str:
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
    # part 1: the line, the book's 50/50, and what it asks against his history (DECISIONS #249)
    out += ["**1 · The line**", "", "| The line | This leg |", "|---|---|"]
    out += [f"| {_cell(a)} | {_cell(b)} |" for a, b in line_part(pl, c, side)] + [""]
    out += [f"**Average workload needed: {P['bar_text']}**", ""]
    if c["usual"] is not None and P["bar"] is not None:
        out += [f"| Workload | {many[0].upper() + many[1:]} |", "|---|---|",
                f"| Needed at this price | **{P['bar_text']}** |",
                f"| Recent {len(rows)}-game average | {d1(c['usual'])} |",
                f"| Difference from recent | {difference(m, side, work_ask(P['bar'], c['usual']))} |", ""]
    S = season_read(pl, c)
    out += ["**2 · This season**" if S is None or S["scope"] == "season" else "**2 · His last games**", ""]
    if S is None:
        out += [f"No games before week {pl.week}.", ""]
    else:
        head, body = season_table(pl, c, S)
        out += ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
        out += ["| " + " | ".join(_cell(x) for x in cells) + " |" for cells in body] + [""]
        for x in season_lines(c, S):
            out += [x, ""]
    hist = []
    if rows:
        tabled = c["usual"] is not None and P["bar"] is not None
        avg = (f" (average {d1(c['usual'])}{_without(rows)})" if c["usual"] is not None and not tabled
               else (f" ({_without(rows)[2:]})" if c["usual"] is not None and P["marked"] else ""))
        hist.append(f"Last {len(rows)}: {_md_last(rows)}{avg}"
                    + (" (back into last season)" if c.get("usual_spans_seasons") else ""))
    else:
        hist.append(f"No games before week {pl.week}.")
    if 0 < len(rows) < P["n"]:
        hist.append(f"Short history: {len(rows)} games.")
    elif c["usual"] is not None and P["n_clean"] < 3:
        hist.append(f"Short history: {P['n_clean']} game{'' if P['n_clean'] == 1 else 's'} without a lineup change.")
    if P["bar"] is not None:
        if P["season"] is not None:
            n, hit, of = P["season"]
            hist.append(f"{n}+ {many} this season: {hit} of {of} games" if side == "over"
                        else f"{n} or fewer {many} this season: {hit} of {of} games")
        else:
            hist.append(f"No games this season before week {pl.week}.")
        if 0 < P["season_games"] < P["n"]:
            hist.append(f"Short history: {P['season_games']} season games.")
    for x in hist:                             # a paragraph each: a copied reply keeps them apart
        out += [x, ""]
    out.pop()
    notes = _md_notes(rows, pl.season) + list(pl.lineup) + [x for x in " ".join(_no_depth(pl, m)).split("\n") if x]
    if notes:
        out += [""] + [f"* {x}" for x in notes]
    out.append("")
    if c["usual"] is not None:
        out += [f"**At his recent workload ({d1(c['usual'])} {many})**", "",
                f"| {RATE_TITLE[m]} | Rate |", "|---|---|",
                f"| Needed at this price | **{_cell(P['need_text'])}** |",
                f"| {P['window']} | {P['assumed_text']} |",
                f"| This season | {_cell(P['season_rate'])} |",
                f"| Opponent has allowed | {_cell(_opp_cell(opp_row, P['rate_long']))} |", ""]
        out += [f"The bar assumes {P['window'][0].lower() + P['window'][1:]}, blended toward the league "
                f"average for his position. {_opp_note(opp, opp_row)}", ""]
    else:
        out += [f"Only {c['usual_games']} games: no recent average yet. The bar assumes {P['assumed_text']}: "
                f"{P['window'][0].lower() + P['window'][1:]}.", ""]
    if matchup:              # off in a screen or game read: the game header prints it once (DECISIONS #243)
        out += matchup_md(pl, m, opp, game_lines, why_no_lines, grades, qb_today, grades_all, scoring) + [""]
    else:
        out += ["Part 3, the matchup, is in the game header above.", ""]
    high, low = holds_up(pl, c, side, opp=opp, game_lines=game_lines, opp_row=opp_row, grades=grades,
                         qb_today=qb_today, scoring=scoring, fixed_spread=c["script_spread"])
    out += ["**4 · Does it hold up**", ""]
    for head_, facts in (("Points to the line being set high:", high), ("Points to it being set low:", low)):
        out += [head_, ""] + [f"- {x}" for x in (facts or ["nothing on this card"])] + [""]
    out += [HOLDS_NOTE, ""]
    cond = condition(m, side, P["work_ask"], P["rate_ask"], P["reached"], len(rows), P["split"])
    if cond:
        out += [f"What needs to be true: {cond}", ""]
    if footer:
        out.append(f"_{footer}_")
    return "\n".join(out).rstrip("\n")


def difference(market: str, side: str, ask: float) -> str:
    """The workload ask in words, as the entry summary says it: positive = what the bet needs."""
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
    for x in pl.lineup:
        out += _wrap(x)
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
    notes = _md_notes(rows, pl.season) + list(pl.lineup)
    if notes:
        out += [""] + [f"* {x}" for x in notes]
    if footer:
        out += ["", f"_{footer}_"]
    return "\n".join(out)

"""The screen (DECISIONS #240): every saved Sleeper line in a kickoff window, both sides, ranked by how
little each asks at its price -- only from facts already on the card, as pass/fail marks, no
weights, no settings, no chance. The user's design (2026-10-11):

- Only legs whose recent workload already meets the bar are listed (the card's own test: the bar as
  shown minus his last-4 average as shown, to the nearest half, 0 or better for the side). That test
  and "his longer-run rate against the needed rate" are one fact (the bar IS the workload at the
  longer-run rate), so they share one column and are not counted twice.
- Four marks, each agree (✓), disagree (✗) or not enough data (–), with its sample:
  consistency (at or past the bar in more than half his season games; – under 4 games), his season
  rate against the needed rate (– below the card's minimum sample), the opponent's allowed rate
  against the needed rate (– when the card shows none), and the grade matchup (offense against
  defense; equal grades disagree).
- Order: the workload cushion as a percent of the bar, biggest first; the marks are shown, not counted,
  and only break ties (DECISIONS #243; kept after the #244 test).

Tested on 2026 weeks 2-5 (DECISIONS #244): legs on the list hit about 50% on Overs and 53% on Unders
against about 56% needed, and the top-ranked rows did no better; the header says so on every run
(TESTED)."""

from __future__ import annotations

import datetime as dt
import re

from . import card, odds
from .checks import DataError
from .markets import ARCHIVE_MARKET, workload_col
from .matchup import TIER_LETTERS

DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
JOURNAL_MARKET = {v: k for k, v in ARCHIVE_MARKET.items()}      # calc's name -> the journal's (settle's)
# the measured result (DECISIONS #244, the report's own numbers): every leg at the bar, Overs 50.0% and Unders
# 52.9% against 56.1% / 56.4% needed (354 + 522 graded legs); cushion's top 3 per side, 311 graded legs, did no better
TESTED = ("Tested on 2026 weeks 2-5: legs on this list hit about 50% on Overs and 53% on Unders (876 graded legs), against about 56% needed. The top-ranked rows (311 graded legs) did no better. This is a way to read the slate, not a list of likely winners.")
HEADER = ("This lists only legs where his recent workload already meets the bar at the price. Legs that "
          "depend on a role change -- more work than his recent games -- are not on it. " + TESTED)
ORDER = ("Order: the workload cushion as a percent of the bar, biggest first (kept after the 2026 test: no other "
         "order beat it by the margin set in advance; a low line gets a big percent from one extra target or carry). The ✓ and ✗ marks are "
         "shown, not counted: ✓ agrees, ✗ disagrees, – not enough data.")
TOP = 8
REPLAY = ("Past week: rebuilt from the saved line history -- the newest saved Sleeper quote before each "
          "kickoff, which may differ from the quote a live screen saw (a later capture at the same line "
          "replaces the earlier one) -- and today's copy of the play-by-play, cut at the week as always.")


def parse_window(text: str) -> tuple[int, int, int | None]:
    """'Sun 1pm PT' / 'sunday 1:25 PM' / 'sun 13:00' -> (weekday, hour, minute or None). The window is
    that clock hour in Pacific time; a minute narrows it to one kickoff time."""
    t = re.sub(r"\bpt\b", " ", str(text).strip().lower().replace(".", ""))
    m = re.fullmatch(r"\s*([a-z]+)\s+(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*", t)
    if not m or m.group(1)[:3] not in DAYS:
        raise DataError(f"write the window as '<day> <time> PT', e.g. 'Sun 1pm PT'; got {text!r}")
    hour, minute, ampm = int(m.group(2)), m.group(3), m.group(4)
    if ampm:
        if not 1 <= hour <= 12:
            raise DataError(f"{text!r}: an am/pm hour is 1 to 12")
        hour = hour % 12 + (12 if ampm == "pm" else 0)
    elif not 0 <= hour <= 23:
        raise DataError(f"{text!r}: the hour is 0 to 23")
    return DAYS[m.group(1)[:3]], hour, (int(minute) if minute is not None else None)


def pacific(utc: str):
    import pandas as pd
    from zoneinfo import ZoneInfo
    return pd.Timestamp(utc).tz_convert(ZoneInfo("America/Los_Angeles"))


def clock(utc: str) -> str:
    """'Sun 1:05 PM PT' (no platform-specific strftime flags)."""
    t = pacific(utc)
    return f"{t:%a} {t.hour % 12 or 12}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'} PT"


def window_games(sched, season: int, week: int | None, window: tuple, now: dt.datetime):
    """The window's games: that weekday and clock hour (Pacific). With no week, every window game of the
    soonest week that still has one to kick off -- including any already started, which the caller
    leaves out and names."""
    day, hour, minute = window
    g = sched[sched["season"] == season].copy()
    if week is not None:
        g = g[g["week"] == week]
    pt = g["kickoff_utc"].map(pacific)
    keep = (pt.map(lambda t: t.weekday()) == day) & (pt.map(lambda t: t.hour) == hour)
    if minute is not None:
        keep &= pt.map(lambda t: t.minute) == minute
    g = g[keep]
    if week is None:
        import pandas as pd
        ahead = g[pd.to_datetime(g["kickoff_utc"], utc=True) > pd.Timestamp(now)]
        if ahead.empty:
            raise DataError("no game in that window is still to kick off this season; give --week for a past week")
        g = g[g["week"] == ahead.sort_values("kickoff_utc")["week"].iloc[0]]
    if g.empty:
        raise DataError(f"no {season} game kicks off in that window" + (f" in week {week}" if week else ""))
    return g.sort_values(["kickoff_utc", "away_team"])


def grade_rank(g: str) -> int | None:
    """'A-' -> a number, lower is better: S+ S S- A+ ... F-. None for text that is not a grade."""
    g = str(g).strip()
    if not re.fullmatch(f"[{TIER_LETTERS}][+-]?", g):
        return None
    return TIER_LETTERS.index(g[0]) * 3 + {"+": 0, "-": 2}.get(g[1:2], 1)


def _cmp(side: str, value: float, need: float) -> bool:
    return value >= need if side == "over" else value <= need


def side_row(pl, c: dict, side: str, shown: dict, stub: dict, other_bar: float | None) -> dict:
    """One side of one line, from the card's own parts. Keys: passes (workload meets the bar), marks
    [(name, mark, text)], cushion (percent of the bar), and the display cells."""
    P = card._parts(pl, c, side)
    m = c["market"]
    many = P["many"]
    rate = pl.rates[card.RATE_KEY[m]]
    unit = card.SHOW[m][1][1]
    sol = c["solutions"].get(f"rate_needed_{side}")
    need_status = card.calc.side_result(side, sol.status) if sol is not None else None
    need = card.shown_rate(P["need"]) if P["need"] is not None else None
    row = {"player": stub["player"], "team": stub["team"], "market": m, "side": side, "line": c["line"],
           "mult": c[f"mult_{side}"], "gsis_id": stub["gsis_id"], "game_id": stub["game_id"], "week": stub["week"],
           "season": stub["season"], "bar": P["bar"], "flags": []}
    usual = c["usual"]
    row["passes"] = bool(P["bar"] is not None and usual is not None
                         and (card.half_up(P["work_ask"], "0.5") <= 0 if side == "over"
                              else card.half_up(P["work_ask"], "0.5") >= 0))
    sb = card.shown_work(P["bar"]) if P["bar"] is not None else None
    row["cushion"] = (((-P["work_ask"]) if side == "over" else P["work_ask"]) / sb * 100) \
        if P["work_ask"] is not None and sb else None
    row["workload"] = (f"{card.d1(usual)} avg vs {P['bar_text']}" if P["bar"] is not None and usual is not None
                       else P["bar_text"])
    longer = card.shown_rate(P["assumed"])
    vs = (f"{need:.1f} needed" if need is not None
          else ("any rate clears" if need_status == "always" else "no rate clears"))
    row["longer"] = f"{longer:.1f} vs {vs} ({len(pl.window)} g, {rate.own_n} {unit})"

    marks = []
    # consistency: at or past the bar in more than half his season games
    if P["season"] is None or P["season"][2] < 4:
        marks.append(("consistency", "–", f"– {P['season_games']} games"))
    else:
        n, hit, of = P["season"]
        at = f"{n}+" if side == "over" else f"{n} or fewer"
        marks.append(("consistency", "✓" if hit * 2 > of else "✗", f"{'✓' if hit * 2 > of else '✗'} {hit} of {of} at {at}"))
    # his season rate against the needed rate (the card's minimum sample)
    seas = card.shown_rate(rate.season * P["k"]) if rate.season is not None else None
    sample = f"({len(pl.season_games)} g, {rate.season_n} {unit})"
    if seas is None or rate.season_n < c["season_min"] or usual is None or need_status not in ("ok", "always", "never"):
        marks.append(("season rate", "–", f"– {seas:.1f} {sample}" if seas is not None else "– none"))
    else:
        ok = need_status == "always" or (need_status == "ok" and _cmp(side, seas, need))
        marks.append(("season rate", "✓" if ok else "✗", f"{'✓' if ok else '✗'} {seas:.1f} {sample}"))
    # the opponent's allowed rate against the needed rate
    o = shown.get("opp_row") or {}
    if o.get("value") is None or o.get("error") or usual is None or need_status not in ("ok", "always", "never"):
        marks.append(("opponent", "–", f"– {card._opp_cell(o or None, P['rate_long'])}"))
    else:
        ov = card.half_up(o["value"], "0.1")
        ok = need_status == "always" or (need_status == "ok" and _cmp(side, ov, need))
        marks.append(("opponent", "✓" if ok else "✗",
                      f"{'✓' if ok else '✗'} {ov:.1f} ({o['games']} g, {o.get('plays', 0)} plays)"))
    # the grade matchup: offense against defense (an Under wants the defense graded higher)
    gr = shown.get("grades") or {}
    off, dfn = (grade_rank(gr["off"]), grade_rank(gr["def"])) if gr.get("off") and gr.get("def") else (None, None)
    qb_out = str(shown.get("qb_today", ""))
    if qb_out.endswith(" ruled Out.") and off is not None:
        # his offense's grade was earned with a quarterback who is out: no data, not a ✓ or ✗ (DECISIONS #243)
        marks.append(("grades", "–", f"– graded with {qb_out.removesuffix(' ruled Out.')}, who is Out"))
    elif off is not None and dfn is not None:
        ok = off < dfn if side == "over" else dfn < off
        marks.append(("grades", "✓" if ok else "✗", f"{'✓' if ok else '✗'} {gr['off']} vs {gr['def']}"))
    else:
        marks.append(("grades", "–", "– no grades yet"))
    row["marks"] = marks
    row["x"] = sum(mk == "✗" for _, mk, _ in marks)
    row["ok"] = sum(mk == "✓" for _, mk, _ in marks)
    # flags
    if len(P["rows"]) < P["n"] or 0 < P["season_games"] < 4:
        row["flags"].append("short history")
    qb = str(shown.get("qb_today", ""))
    if qb.startswith("Starting QB not confirmed"):
        row["flags"].append("QB not confirmed")
    elif qb.endswith("ruled Out."):
        row["flags"].append(qb.removesuffix(".").replace(" ruled Out", " (QB) ruled Out"))
    if sb is not None and other_bar is not None and abs(sb - card.shown_work(other_bar)) <= 1:
        row["flags"].append("tight line")
    row["many"] = many
    return row


def rank(rows: list[dict]) -> list[dict]:
    """Workload passes only, biggest cushion first (the user, 2026-10-11, DECISIONS #243: it was fewest ✗,
    then most ✓, then cushion; the marks are now shown, not counted, until the orders are measured);
    ties: fewest ✗, then most ✓."""
    return sorted((r for r in rows if r["passes"]),
                  key=lambda r: (-(r["cushion"] if r["cushion"] is not None else -1e9), r["x"], -r["ok"]))


def _leg(r: dict) -> str:
    price = odds.fmt_american(odds.american_from_multiplier(r["mult"]))
    return f"{r['player']} ({r['team']}) · {card.SHOW[r['market']][0]} {r['side'].title()} {r['line']:g} ({price})"


def table(rows: list[dict], title: str) -> list[str]:
    out = [f"**{title}**", ""]
    if not rows:
        return out + ["None: no leg on this side has his recent workload at the bar."]
    out += ["| # | Leg | Workload | Longer-run rate | Consistency | Season rate | Opponent | Grades | Cushion | Flags |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        marks = {n: t for n, _, t in r["marks"]}
        cush = f"{round(r['cushion']) + 0:+d}%" if r["cushion"] is not None else "--"
        out.append("| " + " | ".join(card._cell(x) for x in (
            i, _leg(r), r["workload"], r["longer"], marks["consistency"], marks["season rate"], marks["opponent"],
            marks["grades"], cush, " · ".join(r["flags"]) or "--")) + " |")
    return out


def checks(r: dict, md: bool) -> str:
    """The row's checks, printed under its card (the user, 2026-10-11): the workload with his longer-run
    rate, each mark with its sample, the cushion and the flags -- the same cells as its table row."""
    marks = [(n, t) for n, _, t in r["marks"]]
    cush = f"{round(r['cushion']) + 0:+d}% of the bar" if r["cushion"] is not None else "--"
    rows = ([("Workload", r["workload"]), ("Longer-run rate", r["longer"])]
            + [(n[0].upper() + n[1:], t) for n, t in marks]
            + [("Cushion", cush), ("Flags", " · ".join(r["flags"]) or "--")])
    if md:
        return "\n".join(["**Screen checks**", "", "| Check | Result |", "|---|---|"]
                         + [f"| {a} | {card._cell(b)} |" for a, b in rows])
    return "\n".join(["SCREEN CHECKS"] + [x for a, b in rows for x in card._wrap(f"{a}: {b}")])


def journal_rows(rows: list[dict], window_text: str) -> list[dict]:
    """The ranked rows as journal bet rows, so journal.grade marks them with its own stats join and push
    rule (graded in a throwaway journal, never the betting record)."""
    out = []
    for i, r in enumerate(rows, 1):
        out.append({"id": f"screen-{r['season']}-{r['week']}-{r['side']}-{i}", "season": r["season"],
                    "week": int(r["week"]), "player": r["player"], "team": r["team"],
                    "market": JOURNAL_MARKET[r["market"]], "side": r["side"], "line": float(r["line"]),
                    "price": int(odds.american_from_multiplier(r["mult"])), "stake": 1.0, "status": "open",
                    "volume_unit": workload_col(r["market"]), "screen_rank": i, "screen_window": window_text})
    return out


def results(graded: list[dict], rows: list[dict]) -> list[str]:
    """Each listed leg's result, and the hit rate by rank against the average break-even of those legs."""
    by_id = {g["id"]: g for g in graded}
    out = ["**Results** (graded with the journal's own stats and push rule)", "",
           "| Side | # | Leg | Actual | Result |", "|---|---|---|---|---|"]
    word = {True: "won", False: "lost"}
    tally: dict = {}
    for side in ("over", "under"):
        for i, r in enumerate([x for x in rows if x["side"] == side], 1):
            g = by_id.get(f"screen-{r['season']}-{r['week']}-{side}-{i}", {})
            res = word.get(g.get("won"), g.get("result") or g.get("status", "open"))   # push, void, check, open
            act = g.get("actual")
            out.append(f"| {side.title()} | {i} | {card._cell(_leg(r))} | {act if act is not None else '--'} | {res} |")
            if g.get("won") is not None:
                for bucket in (("top 3", i <= 3), ("top 8", True)):
                    if bucket[1]:
                        t = tally.setdefault((side, bucket[0]), [0, 0, 0.0])
                        t[0] += int(bool(g["won"]))
                        t[1] += 1
                        t[2] += odds.break_even(r["mult"])
    out.append("")
    for (side, b), (w, n, be) in sorted(tally.items()):
        out.append(f"- {side.title()}s, {b}: {w} of {n} won ({w / n * 100:.0f}%); the average break-even of those "
                   f"legs is {be / n * 100:.1f}%. Pushes and voids are left out.")
    if not tally:
        out.append("No listed leg is graded yet (the week's stats are not out, or no leg was listed).")
    return out

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
- Lineup check (DECISIONS #247): a last-4 game where his snap share was under half or over double his
  share in his other games of the window, or with a different starting QB, is marked; the leg is listed
  only if his last-4 average with AND without the marked games meets the bar, else it is named under
  "Not listed, lineup changed".
- Order: the cushion in his own swing (#244's candidate C; DECISIONS #247): the workload gap -- his last-4
  average without the marked games minus the bar, in units -- over his game-to-game swing (the standard
  deviation of his workload in the games his longer-run rate uses, up to 16, floored at 1 unit), biggest
  first; under 4 such games the cushion is n/a and the row sorts after every row that has one. The marks
  are shown, not counted, and only break ties.

Tested on 2026 weeks 2-5 (DECISIONS #244), when the order was the cushion as a percent of the bar: legs
on the list hit about 50% on Overs and 53% on Unders against about 56% needed, and the top-ranked rows did
no better; the header says so on every run (TESTED). The swing order (C) was measured once in the same
test and did no better either."""

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
TESTED = ("Tested on 2026 weeks 2-5: legs on this list hit about 50% on Overs and 53% on Unders (876 graded legs), against about 56% needed. The top-ranked rows under the order used then, the cushion as a percent of the bar (311 graded legs), did no better. This is a way to read the slate, not a list of likely winners.")
HEADER = ("This lists only legs where his recent workload already meets the bar at the price. Legs that "
          "depend on a role change -- more work than his recent games -- are not on it. " + TESTED)
ORDER = ("Order: the cushion in his own swing, biggest first -- the workload gap (his last-4 average without any "
         "game marked by the lineup check, minus the bar) over his game-to-game swing in the games behind his "
         "longer-run rate, at least 1 unit. It replaced the percent of the bar, which gave a low line a big number "
         "from one extra target; measured once in the 2026 test, its top rows did no better either. Under 4 games: "
         "n/a, ranked last. The ✓ and ✗ marks are shown, not counted: ✓ agrees, ✗ disagrees, – not enough data.")
SWING_FLOOR = 1.0              # the swing is never less than 1 unit (DECISIONS #247)
SWING_MIN_GAMES = 4            # fewer games behind his rate: no cushion (n/a), ranked after every row with one
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
    """One side of one line, from the card's own parts. Keys: passes (workload meets the bar with and
    without the lineup check's marked games), lineup_out (the reason it is not listed when only the
    marked games carried it), marks [(name, mark, text)], cushion (the gap over his swing), gap (units),
    swing, and the display cells."""
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

    def meets(ask):
        return ask is not None and (card.half_up(ask, "0.5") <= 0 if side == "over" else card.half_up(ask, "0.5") >= 0)
    full_ok = bool(P["bar"] is not None and usual is not None and meets(P["work_ask"]))
    # the lineup check (DECISIONS #247): the average without the marked games must meet the bar too
    clean_ok = full_ok and (not P["marked"] or meets(P["work_ask_clean"]))
    row["passes"] = clean_ok
    row["lineup_out"] = None
    if full_ok and not clean_ok:
        without = (f"{card.d1(P['usual_clean'])} without the {P['marked']} marked game{'s' if P['marked'] > 1 else ''}"
                   if P["usual_clean"] is not None else f"all {len(P['rows'])} games are marked")
        row["lineup_out"] = (f"his last-4 average is {card.d1(usual)} but {without}, against {P['bar_text']}"
                             + ("; " + " ".join(pl.lineup) if pl.lineup else ""))
    sb = card.shown_work(P["bar"]) if P["bar"] is not None else None
    # the cushion in his own swing (#244's candidate C, DECISIONS #247): the gap in units over the standard
    # deviation of his workload in the games behind his longer-run rate, floored at 1 unit
    ask = P["work_ask_clean"] if P["marked"] else P["work_ask"]
    gap = ((-ask) if side == "over" else ask) if ask is not None else None
    col = workload_col(m)
    swing = (max(float(pl.window[col].std(ddof=1)), SWING_FLOOR) if len(pl.window) >= SWING_MIN_GAMES else None)
    row["gap"], row["swing"] = gap, swing
    row["cushion"] = gap / swing if gap is not None and swing is not None else None
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
    if len(P["rows"]) < P["n"] or 0 < P["season_games"] < 4 or (usual is not None and P["n_clean"] < 3):
        row["flags"].append("short history")
    if P["marked"]:
        row["flags"].append(f"lineup check: {P['marked']} of {len(P['rows'])} marked")
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
    """Listed legs only (both averages meet the bar), biggest cushion in his swing first (DECISIONS #247);
    a row with no cushion (under 4 games) after every row that has one; ties: fewest ✗, then most ✓."""
    return sorted((r for r in rows if r["passes"]),
                  key=lambda r: (r["cushion"] is None, -(r["cushion"] or 0.0), r["x"], -r["ok"]))


def cushion_text(r: dict) -> str:
    """'+1 target, 0.3 of his swing'; with no cushion, the gap and 'n/a (under 4 games)'."""
    if r.get("gap") is None:
        return "--"
    one, many = card.SHOW[r["market"]][1]
    # the same gap the cushion divides, to one decimal; a listed leg's gap just under 0 (the listing test rounds
    # the ask to the nearest half, so -0.2 lists) prints as +0, never as short of the bar
    g = round(r["gap"], 1) + 0.0
    zero = -0.25 < g < 0.05
    g = 0.0 if zero else g
    gap = f"{'+' if g >= 0 else '−'}{card._num(abs(g))} {one if abs(g) == 1 else many}"
    if r.get("cushion") is None:
        return f"{gap}, n/a (under {SWING_MIN_GAMES} games)"
    z = "0.0" if zero else card.d1(r["cushion"])
    return f"{gap}, {'0.0' if z == '-0.0' else z} of his swing"


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
        cush = cushion_text(r)
        out.append("| " + " | ".join(card._cell(x) for x in (
            i, _leg(r), r["workload"], r["longer"], marks["consistency"], marks["season rate"], marks["opponent"],
            marks["grades"], cush, " · ".join(r["flags"]) or "--")) + " |")
    return out


def checks(r: dict, md: bool) -> str:
    """The row's checks, printed under its card (the user, 2026-10-11): the workload with his longer-run
    rate, each mark with its sample, the cushion and the flags -- the same cells as its table row."""
    marks = [(n, t) for n, _, t in r["marks"]]
    cush = cushion_text(r)
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
            if res == "open":
                res = "not posted yet"         # his game's stats or snap counts are not out (DECISIONS #246)
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
        out.append("No listed leg is graded yet: the results are not posted yet (nflverse posts a game's stats and "
                   "snap counts some hours after it ends), or no leg was listed. Rerun the grade later.")
    return out

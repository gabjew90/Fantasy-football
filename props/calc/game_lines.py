"""The spread and total for the MATCHUP block: ESPN's scoreboard (the
DraftKings numbers ESPN displays), fetched through core.fetch and read the way
core/status.py reads it (week_status: competitors by homeAway, odds[0].details
and odds[0].overUnder). props may not import that module (props/tests/
test_boundary.py), so these few lines are a copy of its parsing, not a call.

ESPN removes the odds once a game is final, so a finished game has none.
Display only: nothing here feeds a number on the card."""

from __future__ import annotations

import json
import math
import re

from core import fetch as F

from . import names
from .checks import DataError

SPREAD = re.compile(r"^([A-Z]{2,3})\s+(-\d+(?:\.\d+)?)$")


def parse(sb: dict) -> dict:
    """{(away, home): {"kickoff_utc", "favorite", "points", "spread_text",
    "spread_unread", "total"}} with nflverse team codes. favorite/points are
    None for a pick'em ("EVEN", "PK") and, with total, for a game ESPN shows no
    odds for. A spread text in any other form, or naming neither team, is kept
    as ESPN wrote it with spread_unread True, for the card to show as such:
    one odd game must not stop every card of the week (display only)."""
    out = {}
    for ev in sb.get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        t = {c.get("homeAway"): names.team_code(c["team"]["abbreviation"])
             for c in comp.get("competitors", []) if c.get("team")}
        if not (t.get("away") and t.get("home")):
            raise DataError(f"an ESPN scoreboard event ({ev.get('id')}) does not name a home and an away team")
        odds = (comp.get("odds") or [{}])[0]
        text = odds.get("details")
        fav = pts = None
        unread = False
        m = SPREAD.match(str(text or "").strip())
        if m and names.team_code(m.group(1)) in (t["away"], t["home"]):
            fav, pts = names.team_code(m.group(1)), abs(float(m.group(2)))
        elif str(text or "").strip().upper() not in ("", "EVEN", "PK", "PICK"):
            unread = True
        total = odds.get("overUnder")
        try:
            total = None if total is None or isinstance(total, bool) else float(total)
        except (TypeError, ValueError):
            total = None                   # shown as no total; the spread is judged on its own
        if total is not None and not math.isfinite(total):
            total = None
        out[(t["away"], t["home"])] = {"kickoff_utc": ev.get("date"), "favorite": fav, "points": pts,
                                       "spread_text": text, "spread_unread": unread, "total": total}
    return out


def closing(game) -> dict | None:
    """The nflverse schedule's closing spread and total for one game row
    (spread_line: points the home team is favoured by; negative = the away
    team), for when ESPN shows none (the user, 2026-10-10). None when the
    schedule has neither."""
    sp, tot = game.get("spread_line"), game.get("total_line")
    sp = None if sp is None or sp != sp else float(sp)
    tot = None if tot is None or tot != tot else float(tot)
    if sp is None and tot is None:
        return None
    fav = None if not sp else (game["home_team"] if sp > 0 else game["away_team"])
    return {"kickoff_utc": None, "favorite": fav, "points": None if sp is None else abs(sp),
            "spread_text": None if sp is None else ("EVEN" if sp == 0 else f"{fav} -{abs(sp):g}"),
            "spread_unread": False, "total": tot, "closing": True}


def has_odds(g: dict | None) -> bool:
    return bool(g) and (g.get("favorite") or g.get("spread_text") or g.get("total") is not None)


def week_lines(season: int, week: int, *, manifest=None) -> dict:
    """parse() of the week's scoreboard, fetched through core.fetch."""
    return parse(json.loads(F.espn_scoreboard(season, week, manifest=manifest).read_text(encoding="utf-8")))

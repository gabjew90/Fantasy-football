"""The spread and total for the MATCHUP block: ESPN's scoreboard (the
DraftKings numbers ESPN displays), fetched through core.fetch and read the way
core/status.py reads it (week_status: competitors by homeAway, odds[0].details
and odds[0].overUnder). props may not import that module (props/tests/
test_boundary.py), so these few lines are a copy of its parsing, not a call.

ESPN removes the odds once a game is final, so a finished game has none.
Display only: nothing here feeds a number on the card."""

from __future__ import annotations

import json
import re

from core import fetch as F

from . import names
from .checks import DataError

SPREAD = re.compile(r"^([A-Z]{2,3})\s+(-\d+(?:\.\d+)?)$")


def parse(sb: dict) -> dict:
    """{(away, home): {"kickoff_utc", "favorite", "points", "spread_text",
    "total"}} with nflverse team codes. favorite/points are None for a pick'em
    ("EVEN"), and with total for a game ESPN shows no odds for."""
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
        m = SPREAD.match(str(text or "").strip())
        if m:
            fav, pts = names.team_code(m.group(1)), abs(float(m.group(2)))
            if fav not in (t["away"], t["home"]):
                raise DataError(f"ESPN's spread {text!r} names neither team of {t['away']} at {t['home']}")
        elif text not in (None, "", "EVEN"):
            raise DataError(f"ESPN's spread {text!r} for {t['away']} at {t['home']} is not in the form 'TEAM -3.5'")
        total = odds.get("overUnder")
        out[(t["away"], t["home"])] = {"kickoff_utc": ev.get("date"), "favorite": fav, "points": pts,
                                       "spread_text": text, "total": None if total is None else float(total)}
    return out


def week_lines(season: int, week: int, *, manifest=None) -> dict:
    """parse() of the week's scoreboard, fetched through core.fetch."""
    return parse(json.loads(F.espn_scoreboard(season, week, manifest=manifest).read_text(encoding="utf-8")))

"""Scoring environment per team for one week: opponent, spread, total, implied
points, kickoff -- the start/sit framework's question 3.

Read from ESPN's week scoreboard, which carries the DraftKings spread and total
it displays (the same source the props engine anchors TDs on). Implied points
= total / 2 - spread / 2 from the team's side. Displayed and recorded, not used
to tilt a projection: no tilt has been validated here (the manager's x1.05 /
x0.95 never was), and an unvalidated tilt is exactly what the registry exists
to keep out.

Team codes follow Sleeper (WAS, LAR), the fantasy side's one convention.
"""

from __future__ import annotations

import datetime as dt
import json

from core import fetch as F

ESPN_TO_SLEEPER = {"WSH": "WAS"}


def parse_scoreboard(sb: dict) -> dict:
    """team -> {opp, home, spread, total, implied, kickoff_utc, status}."""
    out = {}
    for ev in (sb or {}).get("events", []):
        comp = (ev.get("competitions") or [{}])[0]
        teams = {c.get("homeAway"): ESPN_TO_SLEEPER.get(c["team"]["abbreviation"], c["team"]["abbreviation"])
                 for c in comp.get("competitors", []) if c.get("team")}
        if "home" not in teams or "away" not in teams:
            continue
        odds = (comp.get("odds") or [{}])[0]
        spread_home = odds.get("spread")             # home-team perspective, negative = favourite
        total = odds.get("overUnder")
        kick = ev.get("date")
        status = ((ev.get("status") or {}).get("type") or {}).get("name")
        for side, other in (("home", "away"), ("away", "home")):
            sp = None if spread_home is None else (float(spread_home) if side == "home" else -float(spread_home))
            implied = None if (sp is None or total is None) else round(float(total) / 2 - sp / 2, 1)
            out[teams[side]] = {"opp": teams[other], "home": side == "home", "spread": sp,
                                "total": None if total is None else float(total), "implied": implied,
                                "kickoff_utc": kick, "status": status}
    return out


def week_environment(season: int, week: int, *, cache_dir=None, manifest=None) -> dict:
    sb = json.loads(F.espn_scoreboard(season, week, cache_dir=cache_dir, manifest=manifest)
                    .read_text(encoding="utf-8"))
    return parse_scoreboard(sb)


def started(env_row: dict | None, now: dt.datetime | None = None) -> bool:
    """True once the team's game has kicked off (its players are locked)."""
    if not env_row or not env_row.get("kickoff_utc"):
        return False
    k = dt.datetime.fromisoformat(env_row["kickoff_utc"].replace("Z", "+00:00"))
    return (now or dt.datetime.now(dt.timezone.utc)) >= k

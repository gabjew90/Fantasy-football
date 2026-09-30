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


NFLVERSE_TO_SLEEPER = {"LA": "LAR"}


def bye_weeks(games, season: int) -> dict:
    """team (Sleeper code) -> its regular-season bye week(s), from nflverse
    games.csv (a DataFrame): the weeks up to the last scheduled one it has no game."""
    g = games[(games.season == season) & (games.game_type == "REG")]
    if g.empty:
        return {}
    plays: dict = {}
    for _, r in g.iterrows():
        for t in (r.home_team, r.away_team):
            plays.setdefault(NFLVERSE_TO_SLEEPER.get(t, t), set()).add(int(r.week))
    last = int(g.week.max())
    return {t: sorted(set(range(1, last + 1)) - ws) for t, ws in plays.items()}


def load_byes(season: int, manifest=None) -> dict:
    """bye_weeks from the cached schedule; {} (and the manifest says why) when
    the schedule cannot be read -- a missing bye is context, never fatal."""
    import pandas as pd
    try:
        return bye_weeks(pd.read_csv(F.schedule(manifest=manifest), low_memory=False), season)
    except Exception:  # noqa: BLE001
        return {}


def bye_calendar(pids, info: dict, byes: dict, weeks, starters=()) -> list[dict]:
    """[{week, players (ids), starters (ids)}] for each week in `weeks` in which
    any of `pids` has a bye -- the roster's bye calendar."""
    out = []
    for w in weeks:
        off = [p for p in pids if w in byes.get((info.get(p) or {}).get("team"), ())]
        if off:
            out.append({"week": int(w), "players": off, "starters": [p for p in off if p in set(starters)]})
    return out


def bye_table(cal: list[dict], name) -> list[str]:
    """The bye calendar as markdown: starters (the lineup set now) in bold."""
    if not cal:
        return ["No byes left for this roster."]
    L = ["| Week | On bye | Starters out |", "|---|---|---|"]
    for c in cal:
        L.append(f"| {c['week']} | " + ", ".join(f"**{name(p)}**" if p in c["starters"] else name(p)
                                                 for p in c["players"])
                 + f" | {len(c['starters'])} |")
    return L


def started(env_row: dict | None, now: dt.datetime | None = None) -> bool:
    """True once the team's game has kicked off (its players are locked)."""
    if not env_row or not env_row.get("kickoff_utc"):
        return False
    k = dt.datetime.fromisoformat(env_row["kickoff_utc"].replace("Z", "+00:00"))
    return (now or dt.datetime.now(dt.timezone.utc)) >= k


def games_left(env: dict, now: dt.datetime | None = None) -> tuple[int, int]:
    """(games not yet kicked off, games) for a week's scoreboard rows. Each
    game appears twice in `env` (one row per team), keyed here by its pair."""
    games = {}
    for team, row in (env or {}).items():
        games[frozenset((team, row.get("opp")))] = row
    left = sum(1 for row in games.values() if not started(row, now))
    return left, len(games)


# A decision made now is for NEXT week once most of this one is played: on a
# Monday with only the late game left, week 3 is settled. Below this share of
# games still to kick off, an unasked-for week moves on -- for waivers and the
# question tools alike (the 2026-09-28 session: `fantasy player` answered for
# week 3 while `fantasy waiver` had moved to week 4, and chat nearly quoted
# week 3's "plays 100%" for a player FantasyPros gave 51% for week 4).
ROLL_BELOW = 0.5


def decision_week(season: int, week: int, manifest=None, now: dt.datetime | None = None,
                  last_week: int = 18) -> tuple[int, str | None]:
    """(the week a decision is for, why it moved or None). Never past the
    league's last week; a scoreboard that cannot be read means no move -- the
    roll is a convenience, and its failure must not cost the answer."""
    if week >= last_week:
        return week, None
    try:
        left, total = games_left(week_environment(season, week, manifest=manifest), now)
    except Exception:  # noqa: BLE001
        return week, None
    if total and left / total < ROLL_BELOW:
        return week + 1, (f"week {week} has {left} of {total} games still to kick off, so this is week "
                          f"{week + 1} (pass --week {week} for this week)")
    return week, None


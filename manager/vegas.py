"""Vegas lines via The Odds API: implied team totals for projection tilts.

No ODDS_API_KEY -> a DATA MISSING line and no adjustment; never a crash.

WEEK WINDOW (fixed 2026-09-07). The endpoint returns EVERY posted game, which
in September is all 272 of the season sorted ascending by kickoff. The old
loop assigned `out[team]` per event with no date filter, so each team ended up
holding its LAST game of the season -- every tilt all year would have run on
January lines, silently and without an error. Callers pass the current week's
window; the request is bounded server-side by commenceTime and filtered again
here, and the cache key carries the window so a wider pull is never reused.
"""

from __future__ import annotations

import json
import logging
import os
import time as _time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

log = logging.getLogger("manager")

URL = ("https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
       "?regions=us&markets=spreads,totals&oddsFormat=american&apiKey={key}")
TTL = 6 * 3600
ISO = "%Y-%m-%dT%H:%M:%SZ"

# TWO CODE STYLES, ONE LOOKUP (fixed 2026-09-08).
#
# NAMES below emits DRAFTKIT codes (GBP, NOS, SFO...). Roster rows carry
# SLEEPER codes (GB, NO, SF...). Consumers do totals.get(player["team"]), so
# for these eight teams the lookup silently missed and a quarter of the league
# never received a Vegas tilt -- no error, no note, just no adjustment. Deebo
# Samuel sat on a 26.5 implied total and got nothing.
#
# The returned dict carries BOTH spellings for the same number, so a caller
# cannot be wrong about which convention it holds.
ALIASES = {"GBP": "GB", "JAC": "JAX", "KCC": "KC", "LVR": "LV",
           "NEP": "NE", "NOS": "NO", "SFO": "SF", "TBB": "TB"}

# Odds API full names -> draftkit team codes
NAMES = {
    "Arizona Cardinals": "ARI", "Atlanta Falcons": "ATL", "Baltimore Ravens": "BAL",
    "Buffalo Bills": "BUF", "Carolina Panthers": "CAR", "Chicago Bears": "CHI",
    "Cincinnati Bengals": "CIN", "Cleveland Browns": "CLE", "Dallas Cowboys": "DAL",
    "Denver Broncos": "DEN", "Detroit Lions": "DET", "Green Bay Packers": "GBP",
    "Houston Texans": "HOU", "Indianapolis Colts": "IND", "Jacksonville Jaguars": "JAC",
    "Kansas City Chiefs": "KCC", "Las Vegas Raiders": "LVR", "Los Angeles Chargers": "LAC",
    "Los Angeles Rams": "LAR", "Miami Dolphins": "MIA", "Minnesota Vikings": "MIN",
    "New England Patriots": "NEP", "New Orleans Saints": "NOS", "New York Giants": "NYG",
    "New York Jets": "NYJ", "Philadelphia Eagles": "PHI", "Pittsburgh Steelers": "PIT",
    "San Francisco 49ers": "SFO", "Seattle Seahawks": "SEA", "Tampa Bay Buccaneers": "TBB",
    "Tennessee Titans": "TEN", "Washington Commanders": "WAS",
}


def week_window(ctx) -> tuple[datetime, datetime]:
    """UTC (from, to) bounding the current week's kickoffs, with an hour of
    slack each side. Falls back to now .. now+7d when the schedule is absent."""
    from .games import week_games
    try:
        games = week_games(ctx["schedule"], int(ctx["week"]))
    except Exception:  # noqa: BLE001 — a missing schedule is not a crash
        games = []
    if not games:
        now = datetime.now(tz=timezone.utc)
        return now - timedelta(hours=1), now + timedelta(days=7)
    kicks = [g["kickoff"].astimezone(timezone.utc) for g in games]
    return min(kicks) - timedelta(hours=1), max(kicks) + timedelta(hours=6)


def _in_window(commence: str, lo: datetime, hi: datetime) -> bool:
    try:
        t = datetime.strptime(commence, ISO).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return False
    return lo <= t <= hi


def with_aliases(totals: dict[str, float]) -> dict[str, float]:
    """Same numbers under both code styles, so no consumer can miss."""
    out = dict(totals)
    for canon, alias in ALIASES.items():
        if canon in totals:
            out[alias] = totals[canon]
        elif alias in totals:
            out[canon] = totals[alias]
    return out


def snapshot_path(season, week) -> Path:
    return Path("state") / "vegas" / f"{season}-wk{int(week):02d}.json"


def read_snapshot(season, week) -> tuple[dict[str, float], str | None]:
    """Committed lines for a week, written by `manager vegas-refresh`.

    The API key is a local secret and stays local. Rather than putting it in
    CI, the week's lines are pulled here and committed, so the scheduled job
    reads numbers it cannot fetch itself. Stale beats absent, and the note
    always says how old they are.
    """
    p = snapshot_path(season, week)
    if not p.exists():
        return {}, None
    try:
        blob = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return {}, f"DATA MISSING: Vegas snapshot unreadable ({e.__class__.__name__})"
    data = {str(k): float(v) for k, v in (blob.get("data") or {}).items()}
    if not data:
        return {}, None
    age_h = (_time.time() - float(blob.get("ts") or 0)) / 3600.0
    return with_aliases(data), (
        f"Vegas lines from the committed snapshot, "
        f"{age_h:.0f}h old (refreshed {blob.get('refreshed_at', '?')})")


def write_snapshot(season, week, totals: dict[str, float]) -> Path:
    """Persist a week's lines into committed state."""
    p = snapshot_path(season, week)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({
        "season": str(season), "week": int(week), "ts": _time.time(),
        "refreshed_at": datetime.now(tz=timezone.utc).strftime(ISO),
        "data": {k: round(float(v), 1) for k, v in sorted(totals.items())},
    }, indent=2) + "\n", encoding="utf-8")
    return p


def implied_totals(store, window=None, season=None, week=None
                   ) -> tuple[dict[str, float], str | None]:
    """team code -> implied points for `window` (default: the whole feed).

    `window` is a (from, to) pair of aware datetimes, normally week_window(ctx).
    With no API key, falls back to the committed snapshot for season/week when
    one was passed. ({}, note) when neither is available.
    """
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        if season is not None and week is not None:
            data, note = read_snapshot(season, week)
            if data:
                return data, note
        return {}, "DATA MISSING: Vegas lines (no ODDS_API_KEY, no snapshot)"
    lo = hi = None
    url = URL.format(key=key)
    ckey = "vegas"
    if window:
        lo, hi = (d.astimezone(timezone.utc) for d in window)
        url += f"&commenceTimeFrom={lo.strftime(ISO)}&commenceTimeTo={hi.strftime(ISO)}"
        ckey = f"vegas:{lo.strftime(ISO)}:{hi.strftime(ISO)}"
    cached = store.get(ckey)
    if cached and _time.time() - cached.get("ts", 0) < TTL:
        return with_aliases(cached["data"]), None
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:  # noqa: BLE001
        if cached:
            return (with_aliases(cached["data"]),
                    "DATA MISSING: Vegas refresh failed — using cached lines")
        return {}, f"DATA MISSING: Vegas lines ({e.__class__.__name__})"

    out: dict[str, float] = {}
    for ev in events:
        # belt and braces: the server bound can be ignored, the local one cannot
        if lo is not None and not _in_window(ev.get("commence_time", ""), lo, hi):
            continue
        home, away = NAMES.get(ev.get("home_team", "")), NAMES.get(ev.get("away_team", ""))
        if not home or not away:
            continue
        total = spread_home = None
        for bk in ev.get("bookmakers", [])[:1]:
            for mkt in bk.get("markets", []):
                if mkt["key"] == "totals" and mkt.get("outcomes"):
                    total = float(mkt["outcomes"][0].get("point") or 0)
                if mkt["key"] == "spreads":
                    for o in mkt.get("outcomes", []):
                        if NAMES.get(o.get("name", "")) == home:
                            spread_home = float(o.get("point") or 0)
        if total and spread_home is not None:
            out[home] = round(total / 2 - spread_home / 2, 1)
            out[away] = round(total / 2 + spread_home / 2, 1)
    store.set(ckey, {"ts": _time.time(), "data": out})
    return with_aliases(out), None

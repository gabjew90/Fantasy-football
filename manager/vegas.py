"""Vegas lines via The Odds API: implied team totals for projection tilts.

No ODDS_API_KEY -> a DATA MISSING line and no adjustment; never a crash.
"""

from __future__ import annotations

import logging
import os
import time as _time

import requests

log = logging.getLogger("manager")

URL = ("https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
       "?regions=us&markets=spreads,totals&oddsFormat=american&apiKey={key}")
TTL = 6 * 3600

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


def implied_totals(store) -> tuple[dict[str, float], str | None]:
    """team code -> implied points this week. ({}, note) when unavailable."""
    key = os.environ.get("ODDS_API_KEY", "")
    if not key:
        return {}, "DATA MISSING: Vegas lines (no ODDS_API_KEY)"
    cached = store.get("vegas")
    if cached and _time.time() - cached.get("ts", 0) < TTL:
        return cached["data"], None
    try:
        resp = requests.get(URL.format(key=key), timeout=20)
        resp.raise_for_status()
        events = resp.json()
    except Exception as e:  # noqa: BLE001
        if cached:
            return cached["data"], "DATA MISSING: Vegas refresh failed — using cached lines"
        return {}, f"DATA MISSING: Vegas lines ({e.__class__.__name__})"

    out: dict[str, float] = {}
    for ev in events:
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
    store.set("vegas", {"ts": _time.time(), "data": out})
    return out, None

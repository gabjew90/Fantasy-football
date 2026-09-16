"""In-season data layer (season spec Tasks 1-2).

Thin network edge + persistence: NFL schedule/byes/kickoffs (nflverse),
Sleeper weekly projections/stats/league state, points-allowed inputs, and
usage deltas. All decision math lives in weekly.py; everything here is
fetch, normalize, persist — with last-good degradation on failure.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl

from .sleeper import BASE, get_json

ALL_TEAMS = {
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN",
    "DET", "GBP", "HOU", "IND", "JAC", "KCC", "LAC", "LAR", "LVR", "MIA",
    "MIN", "NEP", "NOS", "NYG", "NYJ", "PHI", "PIT", "SEA", "SFO", "TBB",
    "TEN", "WAS",
}

# nflverse team codes -> the Sleeper-style codes used across draftkit
_TEAM_MAP = {"LA": "LAR", "LV": "LVR", "NO": "NOS", "NE": "NEP", "GB": "GBP",
             "KC": "KCC", "SF": "SFO", "TB": "TBB", "WSH": "WAS", "JAX": "JAC"}

EARLY_DAYS_EXCLUDED = ("Saturday", "Sunday", "Monday")


def _norm_team(code: str) -> str:
    return _TEAM_MAP.get(code, code)


SCHEDULE_TTL = 24 * 3600


def load_schedule(cfg, season: int, max_age: float | None = SCHEDULE_TTL,
                  loader=None) -> pl.DataFrame:
    """Long-format REG schedule: one row per team-game. Cached to parquet.

    The cache used to be permanent: the file written on 2026-08-23 would
    have served the whole season, and the NFL flexes December kickoffs
    (Sunday afternoon -> Sunday night, Saturday slates), which moves the
    lock times every gate check is computed from. In season the file is
    refreshed once a day; a failed refresh keeps the last good copy and
    logs it, because a day-old schedule beats no schedule.
    """
    cache = Path(cfg.path("processed")) / f"schedule_{season}.parquet"
    if cache.exists():
        age = time.time() - cache.stat().st_mtime
        if max_age is None or age < max_age:
            return pl.read_parquet(cache)
    try:
        if loader is None:
            import nflreadpy as nfl
            loader = nfl.load_schedules
        s = loader([season]).filter(pl.col("game_type") == "REG")
    except Exception as e:  # noqa: BLE001
        if cache.exists():
            import logging
            logging.getLogger("draftkit").warning(
                "schedule refresh failed (%s) -- using the cached copy", e.__class__.__name__)
            return pl.read_parquet(cache)
        raise
    rows = []
    for r in s.select("week", "away_team", "home_team", "gameday",
                      "weekday", "gametime").iter_rows(named=True):
        away, home = _norm_team(r["away_team"]), _norm_team(r["home_team"])
        base = {"week": int(r["week"]), "gameday": r["gameday"],
                "weekday": r["weekday"], "gametime": r["gametime"] or ""}
        rows.append({**base, "team": away, "opp": home, "is_home": False})
        rows.append({**base, "team": home, "opp": away, "is_home": True})
    out = pl.DataFrame(rows).select(
        "week", "team", "opp", "gameday", "weekday", "gametime", "is_home"
    )
    out.write_parquet(cache)
    return out


def byes(schedule: pl.DataFrame, week: int) -> set[str]:
    playing = set(schedule.filter(pl.col("week") == week)["team"].to_list())
    return ALL_TEAMS - playing


def nfl_state(getter=get_json) -> dict:
    s = getter(f"{BASE}/state/nfl")
    return {"week": int(s.get("week") or 1), "season": str(s.get("season")),
            "season_type": s.get("season_type", "regular")}


def score_projection(stats: dict, scoring: dict) -> float:
    """Score a Sleeper stat-projection dict with the league's own settings."""
    return sum(float(scoring[k]) * float(v)
               for k, v in (stats or {}).items() if k in scoring and v is not None)


def weekly_projections(scoring: dict, season: str, week: int,
                       getter=get_json) -> dict[str, float] | None:
    """sleeper_id -> projected points in league scoring, or None when Sleeper
    is still serving ADP placeholders (pre-publish) — callers must fall back."""
    try:
        raw = getter(f"{BASE}/projections/nfl/regular/{season}/{week}")
    except Exception:  # noqa: BLE001 — endpoint down = same as not published
        return None
    if not isinstance(raw, dict) or not raw:
        return None
    has_real = any(
        isinstance(stats, dict) and any(not k.startswith("adp_") for k in stats)
        for stats in raw.values()
    )
    if not has_real:
        return None
    return {str(pid): round(score_projection(stats, scoring), 2)
            for pid, stats in raw.items() if isinstance(stats, dict)}


def weekly_stats(season: str, week: int, getter=get_json) -> dict[str, dict]:
    """Raw actuals for a completed week (scoreboard + variance inputs)."""
    raw = getter(f"{BASE}/stats/nfl/regular/{season}/{week}")
    return raw if isinstance(raw, dict) else {}


def rival_budgets(rosters: list[dict], budget: int) -> dict[int, int]:
    """roster_id -> remaining FAAB. A direct field read, per the spec review."""
    return {int(r["roster_id"]): budget - int((r.get("settings") or {}).get("waiver_budget_used") or 0)
            for r in rosters}


def injury_map(players: dict) -> dict[str, str]:
    """sleeper_id -> injury_status string ('' when healthy)."""
    out = {}
    for pid, p in players.items():
        if isinstance(p, dict) and "injury_status" in p:
            out[str(pid)] = p.get("injury_status") or ""
    return out


def append_transactions(cfg, txns: list[dict]) -> int:
    """Append new league transactions (dedup by id) — v2's rival-bid history."""
    path = Path(cfg.path("processed")) / "season" / "transactions.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    seen = set()
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                seen.add(json.loads(line).get("transaction_id"))
            except ValueError:
                continue
    added = 0
    with open(path, "a", encoding="utf-8") as f:
        for t in txns:
            if t.get("transaction_id") not in seen:
                f.write(json.dumps(t) + "\n")
                added += 1
    return added


def early_games(schedule: pl.DataFrame, week: int) -> pl.DataFrame:
    """Games that kick before the weekend — players in them lock early.

    Week 1 of 2026 contains a WEDNESDAY game, so this is schedule-driven,
    never calendar-assumed.
    """
    return schedule.filter(
        (pl.col("week") == week) & ~pl.col("weekday").is_in(EARLY_DAYS_EXCLUDED)
    )

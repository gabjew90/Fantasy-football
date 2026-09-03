"""ESPN's season projections as a second free stat-line source (plan A1).

Endpoint (public, in-season, undocumented):
  https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/<season>/segments/0/leaguedefaults/3?view=kona_player_info
with an `X-Fantasy-Filter` header asking for up to 1500 players, the season
split (statSplitTypeId 0) and projected stats (statSourceId 1). Without the
header the endpoint answers with a handful of rows, so a small payload is
treated as "the filter was ignored" and the source is unavailable rather
than silently thin. Each player's `stats` carries BOTH the previous and
the current season, so rows are filtered on seasonId.

Cache-first with a TTL, stale-on-failure with a stderr note, otherwise
EspnUnavailable -- the same shape as draftkit.consensus.fetch_position.
Fetching happens inside a function only: data/raw is a GitHub Actions cache
path and the manager imports draftkit at import time.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

BASE_URL = ("https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}"
            "/segments/0/leaguedefaults/3?view=kona_player_info")
FILTER = {"players": {"limit": 1500, "sortPercOwned": {"sortAsc": False, "sortPriority": 1},
                      "filterStatsForSplitTypeIds": {"value": [0]},
                      "filterStatsForSourceIds": {"value": [1]}}}
HEADERS = {"X-Fantasy-Filter": json.dumps(FILTER), "Accept": "application/json",
           "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) draftkit/1.0"}
CACHE_TTL = 12 * 3600
MIN_PLAYERS = 200          # fewer means the filter header was ignored
POS_BY_ID = {1: "QB", 2: "RB", 3: "WR", 4: "TE", 5: "K", 16: "DEF"}
SKILL = ("QB", "RB", "WR", "TE")
# ESPN stat ids -> the Sleeper-style keys the league scoring uses
STAT_IDS = {"0": "pass_att", "1": "pass_cmp", "3": "pass_yd", "4": "pass_td", "20": "pass_int",
            "23": "rush_att", "24": "rush_yd", "25": "rush_td",
            "42": "rec_yd", "43": "rec_td", "53": "rec", "58": "rec_tgt",
            "72": "fum_lost"}


class EspnUnavailable(RuntimeError):
    """The endpoint could not be read (or ignored the filter) and no usable cache exists."""


def _get_json(url: str, headers: dict, timeout: int = 60):
    import requests
    r = requests.get(url, headers=headers, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_projections(season: int | str, raw_dir: Path, getter=_get_json, ttl: int = CACHE_TTL) -> list[dict]:
    """The raw player list, cached at raw_dir/espn_proj_<season>.json."""
    cache = Path(raw_dir) / f"espn_proj_{season}.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < ttl:
        return json.loads(cache.read_text(encoding="utf-8"))
    url = BASE_URL.format(season=season)
    try:
        payload = getter(url, HEADERS)
        players = payload.get("players") if isinstance(payload, dict) else None
        if not isinstance(players, list) or len(players) < MIN_PLAYERS:
            raise EspnUnavailable(f"filter header ignored: {0 if not isinstance(players, list) else len(players)} players")
    except EspnUnavailable:
        if cache.exists():
            print(f"espn: filter ignored; using cache {cache.name} aged {int(time.time() - cache.stat().st_mtime)}s",
                  file=sys.stderr)
            return json.loads(cache.read_text(encoding="utf-8"))
        raise
    except Exception as e:  # noqa: BLE001
        if cache.exists():
            print(f"espn: fetch failed ({type(e).__name__}); using cache {cache.name} aged "
                  f"{int(time.time() - cache.stat().st_mtime)}s", file=sys.stderr)
            return json.loads(cache.read_text(encoding="utf-8"))
        raise EspnUnavailable(f"{url}: {e}") from e
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(players), encoding="utf-8")
    return players


def parse_players(players: list[dict], season: int | str) -> list[dict]:
    """Pure: [{espn_id, name, pos, line}] for skill players with a season
    projection row for `season` (statSourceId 1, statSplitTypeId 0). Stat
    ids outside STAT_IDS and null values are dropped; empty lines skipped."""
    out = []
    season = int(season)
    for entry in players or []:
        p = entry.get("player") if isinstance(entry.get("player"), dict) else entry
        pos = POS_BY_ID.get(p.get("defaultPositionId"))
        if pos not in SKILL:
            continue
        row = None
        for s in p.get("stats") or []:
            if int(s.get("seasonId", -1)) == season and int(s.get("statSourceId", -1)) == 1 \
                    and int(s.get("statSplitTypeId", -1)) == 0:
                row = s
                break
        if not row:
            continue
        line = {}
        for k, v in (row.get("stats") or {}).items():
            key = STAT_IDS.get(str(k))
            if key is not None and v is not None:
                line[key] = float(v)
        if not line:
            continue
        out.append({"espn_id": str(entry.get("id") or p.get("id")), "name": p.get("fullName") or "",
                    "pos": pos, "line": line})
    return out


def cache_as_of(raw_dir: Path, season: int | str) -> str:
    """ESPN rows carry no stamp; the cache file's date stands in."""
    cache = Path(raw_dir) / f"espn_proj_{season}.json"
    if not cache.exists():
        return ""
    return time.strftime("%Y-%m-%d", time.gmtime(cache.stat().st_mtime))

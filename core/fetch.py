"""The one fetch-and-cache for public football data.

Every download of nflverse files, the Sleeper player table, Sleeper Picks lines
and the ID map goes through `fetch`, which:

  * reuses a copy younger than its max age, and refreshes an older one -- an
    existence-only check is how the props capture priced week 3 on the first
    capture's files (DECISIONS #91);
  * downloads to `<name>.part` and renames, so a killed run never leaves a
    truncated file that the next run would trust;
  * falls back to the older copy when a refresh fails, and says so in the
    manifest (status `stale`) -- a run on older inputs beats no run, but it
    must never look like a fresh one;
  * records every read in an optional core.manifest.Manifest.

Max ages: the current season's files change daily, so 6 hours; reference tables
(players, ID map) a day; a finished season's files a month; Sleeper Picks lines
ten minutes.
"""

from __future__ import annotations

import datetime as dt
import http.client
import os
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

from .manifest import Manifest

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CACHE = Path(os.environ.get("NFL_CORE_CACHE", REPO_ROOT / "data" / "cache" / "core"))

CURRENT_SEASON_MAX_AGE_S = 6 * 3600
REFERENCE_MAX_AGE_S = 24 * 3600
HISTORIC_MAX_AGE_S = 30 * 86400
LINES_MAX_AGE_S = 600
PROJECTIONS_MAX_AGE_S = 3600

NFLVERSE = "https://github.com/nflverse/nflverse-data/releases/download"
NFLVERSE_FILES = {
    "pbp": "pbp/play_by_play_{season}.csv.gz",
    "rosters_weekly": "weekly_rosters/roster_weekly_{season}.csv",
    "injuries": "injuries/injuries_{season}.csv",
    "depth_charts": "depth_charts/depth_charts_{season}.csv",
    "snaps": "snap_counts/snap_counts_{season}.csv",
    "player_stats_week": "stats_player/stats_player_week_{season}.csv",
    "players": "players/players.csv",
}
GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
PLAYERIDS_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
SLEEPER_PLAYERS_URL = "https://api.sleeper.app/v1/players/nfl"
SLEEPER_LINES_URL = "https://api.sleeper.app/lines/available?dynamic=true"

# Sleeper's lines endpoint refuses a bare urllib user agent; ESPN refuses a
# browser-looking one that is not a browser (403, 2026-09-24) but answers curl,
# which is what the props engine has always sent it.
HEADERS = {"User-Agent": "Mozilla/5.0 (fantasy-football core.fetch)"}
CURL_HEADERS = {"User-Agent": "curl/8.5.0"}

# A TRANSIENT FAILURE IS TRIED AGAIN before a download counts as failed (DECISIONS #235: one
# HTTP 502 from the nflverse play-by-play release stopped a calculator card in chat on
# 2026-10-10; the same command worked seconds later). Seconds to wait before each retry.
RETRY_WAITS = (1.0, 3.0)


class TruncatedDownload(OSError):
    """A body shorter than its Content-Length: the connection closed mid-file."""


class FetchError(OSError):
    """No usable copy: the download failed (after its retries) and there is no older copy to
    fall back on. An OSError, so every existing handler still catches it."""

    def __init__(self, name: str, url: str, cause: BaseException):
        super().__init__(f"{name}: download failed ({type(cause).__name__}: {cause})")
        self.name, self.url, self.cause = name, url, cause


def _transient(ex: BaseException) -> bool:
    """Worth another try: a server error (5xx), rate limiting (429), a dropped or refused
    connection or a cut-off body. Never a 404 or another client error, a failed TLS check, or a
    timeout -- a hung server would cost the whole timeout again on every try, and the scheduled
    jobs (settle's 120 s downloads) must not triple their worst case."""
    if isinstance(ex, urllib.error.HTTPError):
        return ex.code >= 500 or ex.code == 429
    if isinstance(ex, urllib.error.URLError):
        ex = ex.reason if isinstance(ex.reason, BaseException) else ex
    if isinstance(ex, (TimeoutError, ssl.SSLError)):
        return False
    return isinstance(ex, (urllib.error.URLError, ConnectionError, http.client.HTTPException, TruncatedDownload))


def current_season(today: dt.date | None = None) -> int:
    """The NFL season in progress: the calendar year from March, else the last."""
    today = today or dt.datetime.now(dt.timezone.utc).date()
    return today.year if today.month >= 3 else today.year - 1


def _download(url: str, dest: Path, timeout: int, headers: dict | None = None) -> None:
    """One download, tried again after RETRY_WAITS on a transient failure; anything else, or the
    last try, raises."""
    for attempt in range(len(RETRY_WAITS) + 1):
        try:
            return _download_once(url, dest, timeout, headers)
        except Exception as ex:  # noqa: BLE001 -- re-raised unless it is transient and tries remain
            if attempt == len(RETRY_WAITS) or not _transient(ex):
                raise
            time.sleep(RETRY_WAITS[attempt])


def _download_once(url: str, dest: Path, timeout: int, headers: dict | None = None) -> None:
    req = urllib.request.Request(url, headers=headers or HEADERS)
    got = 0
    with urllib.request.urlopen(req, timeout=timeout) as resp, open(dest, "wb") as fh:
        expect = resp.headers.get("Content-Length")
        while True:
            chunk = resp.read(1 << 20)
            if not chunk:
                break
            fh.write(chunk)
            got += len(chunk)
    # A connection closed mid-body ends the read loop as if the file were done: the cut copy
    # then replaced the last good one (2026-10-09: a 751 KB weekly-roster file for 3.4 MB).
    # A short body is a failed refresh, like an empty one.
    if expect is not None and expect.isdigit() and got != int(expect):
        raise TruncatedDownload(f"truncated response from {url}: {got} of {expect} bytes")


def _mtime(p: Path) -> dt.datetime:
    return dt.datetime.fromtimestamp(p.stat().st_mtime, dt.timezone.utc)


def fetch(url: str, dest: str | Path, max_age_s: float, *, name: str | None = None,
          manifest: Manifest | None = None, timeout: int = 120, downloader=None,
          headers: dict | None = None) -> Path:
    """`dest`, refreshed from `url` when missing or older than `max_age_s`.

    Raises only when there is no usable copy at all. `downloader(url, path,
    timeout)` is injectable for tests."""
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    name = name or dest.name
    dl = downloader or (lambda u, d, t: _download(u, d, t, headers))
    if dest.exists() and time.time() - dest.stat().st_mtime < max_age_s:
        if manifest is not None:
            manifest.record(name, source=url, status="cached", path=dest, fetched_at=_mtime(dest))
        return dest
    tmp = dest.with_name(dest.name + ".part")
    try:
        dl(url, tmp, timeout)
        # a 200 with an empty body is a failed refresh, not a new copy: renaming it
        # over the last good file would leave nothing to fall back to
        if not tmp.exists() or tmp.stat().st_size == 0:
            raise OSError(f"empty response from {url}")
        tmp.replace(dest)
    except Exception as ex:  # noqa: BLE001 -- classified below, never swallowed silently
        tmp.unlink(missing_ok=True)
        if not dest.exists():
            if manifest is not None:
                manifest.record(name, source=url, status="failed", detail=f"{type(ex).__name__}: {ex}"[:200])
            # a network failure is named as one; anything else (a bug) propagates as itself
            if isinstance(ex, (OSError, http.client.HTTPException)):
                raise FetchError(name, url, ex) from ex
            raise
        if manifest is not None:
            manifest.record(name, source=url, status="stale", path=dest, fetched_at=_mtime(dest),
                            detail=f"refresh failed: {type(ex).__name__}")
        return dest
    if manifest is not None:
        manifest.record(name, source=url, status="fresh", path=dest, fetched_at=_mtime(dest))
    return dest


def _season_max_age(season: int | None) -> float:
    if season is None:
        return REFERENCE_MAX_AGE_S
    return CURRENT_SEASON_MAX_AGE_S if season >= current_season() else HISTORIC_MAX_AGE_S


def nflverse(kind: str, season: int | None = None, *, cache_dir: str | Path | None = None,
             manifest: Manifest | None = None, max_age_s: float | None = None, **kw) -> Path:
    """One nflverse release file. `kind` is a key of NFLVERSE_FILES; `season`
    is required for every kind except `players`."""
    if kind not in NFLVERSE_FILES:
        raise KeyError(f"unknown nflverse kind {kind!r}; known: {', '.join(sorted(NFLVERSE_FILES))}")
    rel = NFLVERSE_FILES[kind]
    if "{season}" in rel and season is None:
        raise ValueError(f"nflverse {kind} needs a season")
    rel = rel.format(season=season)
    dest = Path(cache_dir or DEFAULT_CACHE) / "nflverse" / Path(rel).name
    label = f"nflverse {kind}" + (f" {season}" if season is not None else "")
    return fetch(f"{NFLVERSE}/{rel}", dest,
                 _season_max_age(season if "{season}" in NFLVERSE_FILES[kind] else None)
                 if max_age_s is None else max_age_s,
                 name=label, manifest=manifest, **kw)


def schedule(*, cache_dir=None, manifest=None, max_age_s: float = CURRENT_SEASON_MAX_AGE_S, **kw) -> Path:
    """nflverse games.csv: every season's schedule, lines and results."""
    return fetch(GAMES_URL, Path(cache_dir or DEFAULT_CACHE) / "games.csv", max_age_s,
                 name="schedule", manifest=manifest, **kw)


def id_map(*, cache_dir=None, manifest=None, max_age_s: float = REFERENCE_MAX_AGE_S, **kw) -> Path:
    """DynastyProcess db_playerids.csv: gsis / sleeper / yahoo / espn / fantasypros ids."""
    return fetch(PLAYERIDS_URL, Path(cache_dir or DEFAULT_CACHE) / "db_playerids.csv", max_age_s,
                 name="id map", manifest=manifest, **kw)


def sleeper_players(*, cache_dir=None, manifest=None, max_age_s: float = REFERENCE_MAX_AGE_S, **kw) -> Path:
    """Sleeper's full player table (~16 MB): names, positions, teams, injury
    status, depth-chart order, and its own gsis_id field."""
    return fetch(SLEEPER_PLAYERS_URL, Path(cache_dir or DEFAULT_CACHE) / "sleeper_players.json",
                 max_age_s, name="sleeper players", manifest=manifest, **kw)


def sleeper_lines(*, cache_dir=None, manifest=None, max_age_s: float = LINES_MAX_AGE_S, **kw) -> Path:
    """Sleeper Picks prop lines, two-sided, no key and no quota."""
    return fetch(SLEEPER_LINES_URL, Path(cache_dir or DEFAULT_CACHE) / "sleeper_lines.json",
                 max_age_s, name="sleeper lines", manifest=manifest, **kw)


TRENDING_MAX_AGE_S = 3600


def sleeper_trending(kind: str, *, cache_dir=None, manifest=None, max_age_s: float = TRENDING_MAX_AGE_S,
                     limit: int = 100, **kw) -> Path:
    """Sleeper's trending adds or drops ("add" / "drop"): [{player_id, count}]
    over the last 24 hours across its leagues, most first. An hour old at most:
    it is the waiver command's timing signal (fantasy/trending.py)."""
    if kind not in ("add", "drop"):
        raise ValueError("kind is add or drop")
    url = f"https://api.sleeper.app/v1/players/nfl/trending/{kind}?lookback_hours=24&limit={int(limit)}"
    return fetch(url, Path(cache_dir or DEFAULT_CACHE) / "sleeper" / f"trending_{kind}.json", max_age_s,
                 name=f"Sleeper trending {kind}s", manifest=manifest, **kw)


def espn_scoreboard(season: int, week: int, *, cache_dir=None, manifest=None,
                    max_age_s: float = LINES_MAX_AGE_S * 3, **kw) -> Path:
    """ESPN's scoreboard for ONE regular-season week: kickoffs and the DraftKings
    spread and total ESPN displays. The bare endpoint shows the current week,
    which lags a day at the Tuesday rollover (DECISIONS: props-v1.16)."""
    url = ("https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"
           f"?seasontype=2&week={int(week)}&dates={int(season)}")
    kw.setdefault("headers", CURL_HEADERS)
    return fetch(url, Path(cache_dir or DEFAULT_CACHE) / "espn" / f"scoreboard_{season}_wk{week:02d}.json",
                 max_age_s, name=f"espn scoreboard {season} wk{week}", manifest=manifest, **kw)


SKILL_POSITIONS = ("QB", "RB", "WR", "TE")


def _week_max_age(season: int) -> float:
    return CURRENT_SEASON_MAX_AGE_S if season >= current_season() else HISTORIC_MAX_AGE_S


def sleeper_projections(season: int, week: int, *, positions=SKILL_POSITIONS, cache_dir=None, manifest=None,
                        max_age_s: float | None = None, **kw) -> Path:
    """Sleeper's weekly projections (Rotowire-sourced stat lines) for the skill
    positions. Past weeks are served as they stood at the final pre-kickoff
    update; checked 2026-09-24, weekly residuals for 2024 ran ~7 points of
    standard deviation, which a post-game revision would not produce."""
    pos = "".join(f"&position[]={p}" for p in positions)
    url = f"https://api.sleeper.app/projections/nfl/{season}/{week}?season_type=regular{pos}"
    tag = "" if tuple(positions) == SKILL_POSITIONS else "_" + "-".join(positions)
    # this season's projections move until kickoff (inactives zeroed Sunday
    # morning), so an hour, not the six the season's nflverse files get
    default = PROJECTIONS_MAX_AGE_S if season >= current_season() else HISTORIC_MAX_AGE_S
    return fetch(url, Path(cache_dir or DEFAULT_CACHE) / "sleeper" / f"proj_{season}_wk{week:02d}{tag}.json",
                 default if max_age_s is None else max_age_s,
                 name=f"sleeper projections {season} wk{week}", manifest=manifest, **kw)


def sleeper_stats(season: int, week: int, *, cache_dir=None, manifest=None,
                  max_age_s: float | None = None, **kw) -> Path:
    """Sleeper's weekly actual stat lines, keyed by Sleeper id (the same keys the
    league scoring uses). Undocumented; verified against play-by-play for one
    player-season on 2026-09-21 by the fantasy skill."""
    url = f"https://api.sleeper.app/v1/stats/nfl/regular/{season}/{week}"
    return fetch(url, Path(cache_dir or DEFAULT_CACHE) / "sleeper" / f"stats_{season}_wk{week:02d}.json",
                 _week_max_age(season) if max_age_s is None else max_age_s,
                 name=f"sleeper stats {season} wk{week}", manifest=manifest, **kw)

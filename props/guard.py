"""Cheap window guard for the props workflow.

Runs before any dependency is installed, using only the standard library, and
decides three things: whether this tick has work at all, which mode to run, and
whether a capture should be recorded as a `decision` or a `close` snapshot.

Most of the 96 daily ticks have nothing to do. Exiting here in under a second
keeps the free-tier minute cost near zero and leaves the fantasy workflows'
budget untouched.

Windows:
  capture   a game kicks off within CAPTURE_LEAD_MIN (default 6 hours). Inside
            CLOSE_WINDOW_MIN (default 60) of any kickoff the snapshot becomes
            `close`, which is the row closing-line value is computed from.
  settle    Tuesday 14:00-16:00 UTC, after nflverse publishes weekly stats.

Schedule is read from props/.cache/schedule_<season>.json when present,
otherwise from nflverse games.csv (one small fetch, cached for a day). If the
schedule cannot be read the guard opens the window rather than closing it: a
wasted tick is cheap, a missed closing capture is unrecoverable.

Writes GitHub Actions outputs to stdout: run, mode, season, week, snapshot_type.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
import sys
import urllib.request
from pathlib import Path

try:
    from zoneinfo import ZoneInfo
    EASTERN = ZoneInfo("America/New_York")
except Exception:  # noqa: BLE001 — no tzdata on the host (rare; Windows without tzdata)
    # Last resort only. EDT year-round is wrong for November games, but it is
    # the same answer the old hard-coded arithmetic gave and it keeps the
    # guard running rather than failing closed on every tick.
    EASTERN = dt.timezone(dt.timedelta(hours=-4), "EDT-fallback")

GAMES_URL = "https://raw.githubusercontent.com/nflverse/nfldata/master/data/games.csv"
CACHE = Path(__file__).resolve().parent / ".cache"
CAPTURE_LEAD_MIN = int(os.environ.get("PROPS_CAPTURE_LEAD_MIN", "360"))
CLOSE_WINDOW_MIN = int(os.environ.get("PROPS_CLOSE_WINDOW_MIN", "60"))


def emit(**kw) -> None:
    for k, v in kw.items():
        print(f"{k}={v}")


def load_games(season: int) -> list[dict]:
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"games_{season}.json"
    if cached.exists():
        age = dt.datetime.now().timestamp() - cached.stat().st_mtime
        if age < 86400:
            return json.loads(cached.read_text(encoding="utf-8"))
    with urllib.request.urlopen(GAMES_URL, timeout=30) as resp:
        text = resp.read().decode("utf-8", "replace")
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r.get("season") == str(season) and r.get("game_type") == "REG"]
    cached.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def kickoff_utc(row: dict) -> dt.datetime | None:
    """games.csv carries gameday plus a US/Eastern gametime.

    THE OFFSET IS NOT ARITHMETIC. This used to switch from UTC-4 to UTC-5 at a
    hard-coded November 5 and call the boundary error immaterial against a
    six-hour capture window. Both halves were wrong: US DST ends on the FIRST
    SUNDAY in November, which is November 1 in 2026, and the error is measured
    against the sixty-minute CLOSE window, not the six-hour one. Every game on
    Nov 1-4 was converted an hour early, which put `close` 90 minutes before
    kickoff and shut the window 45 minutes BEFORE kickoff -- losing the closing
    snapshot for all thirteen games of that slate, which is the one row CLV
    cannot be reconstructed without. zoneinfo is standard library, so the guard
    stays dependency-free and the rule comes from the tz database.
    """
    try:
        d = dt.datetime.strptime(row["gameday"], "%Y-%m-%d").date()
        hh, mm = (int(x) for x in row["gametime"].split(":")[:2])
    except (KeyError, ValueError):
        return None
    try:
        local = dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=EASTERN)
    except ValueError:
        return None
    return local.astimezone(dt.timezone.utc)


def main() -> int:
    now = dt.datetime.now(dt.timezone.utc)
    forced = bool(os.environ.get("FORCED"))
    mode = (os.environ.get("PROPS_MODE") or "").strip() or None
    season = int(os.environ.get("PROPS_SEASON") or 0) or (
        now.year if now.month >= 3 else now.year - 1)

    # Explicit dispatch always runs; the operator has decided.
    if forced and mode:
        week = os.environ.get("PROPS_WEEK") or ""
        if not week:
            try:
                games = load_games(season)
                upcoming = [g for g in games
                            if (k := kickoff_utc(g)) and k > now - dt.timedelta(days=3)]
                week = min((int(g["week"]) for g in upcoming), default=1)
            except Exception:
                week = 1
        emit(run="true", mode=mode, season=season, week=week,
             snapshot_type="decision")
        return 0

    # Tuesday settle window.
    if now.weekday() == 1 and 14 <= now.hour < 16:
        emit(run="true", mode="settle", season=season, week=0,
             snapshot_type="decision")
        return 0

    try:
        games = load_games(season)
    except Exception as exc:  # network hiccup: open the window, do not lose a close
        print(f"schedule unavailable ({exc}); opening window", file=sys.stderr)
        emit(run="true", mode="capture", season=season, week=0,
             snapshot_type="decision")
        return 0

    soonest, soonest_week = None, None
    for g in games:
        k = kickoff_utc(g)
        if k is None:
            continue
        lead = (k - now).total_seconds() / 60.0
        if -15 <= lead <= CAPTURE_LEAD_MIN and (soonest is None or lead < soonest):
            soonest, soonest_week = lead, int(g["week"])

    if soonest is None:
        emit(run="false", mode="idle", season=season, week=0,
             snapshot_type="none")
        return 0

    snapshot = "close" if soonest <= CLOSE_WINDOW_MIN else "decision"
    emit(run="true", mode="capture", season=season, week=soonest_week,
         snapshot_type=snapshot)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

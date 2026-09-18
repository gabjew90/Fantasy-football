"""Cheap window guard for the props workflow.

Runs before any dependency is installed, using only the standard library, and
decides three things: whether this tick has work at all, which mode to run, and
whether a capture should be recorded as a `decision` or a `close` snapshot.

Most of the 96 daily ticks have nothing to do. Exiting here in under a second
keeps the free-tier minute cost near zero and leaves the fantasy workflows'
budget untouched.

Windows:
  open      Thursday 22:00-24:00 UTC, once per ISO week: where the week's
            numbers started, so a Sunday decision can be read against an open
            as well as a close.
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
# The Thursday opening sweep: 22:00-24:00 UTC, i.e. Thursday evening
# US Eastern, before the week's first kickoff.
OPEN_FROM_HOUR = int(os.environ.get("PROPS_OPEN_FROM_HOUR", "22"))
OPEN_TO_HOUR = int(os.environ.get("PROPS_OPEN_TO_HOUR", "24"))
CLOSE_WINDOW_MIN = int(os.environ.get("PROPS_CLOSE_WINDOW_MIN", "60"))


def emit(**kw) -> None:
    for k, v in kw.items():
        print(f"{k}={v}")


def load_games(season: int) -> list[dict]:
    """The season's REG rows, from the day-old cache or the network.

    A FAILED FETCH FALLS BACK TO A STALE CACHE rather than raising. The
    schedule barely changes -- only December flex moves a kickoff -- so
    yesterday's copy answers "is a game starting soon" correctly, and the
    alternative was a run that could not name its own week (see main()).
    """
    CACHE.mkdir(parents=True, exist_ok=True)
    cached = CACHE / f"games_{season}.json"
    if cached.exists():
        age = dt.datetime.now().timestamp() - cached.stat().st_mtime
        if age < 86400:
            return json.loads(cached.read_text(encoding="utf-8"))
    try:
        with urllib.request.urlopen(GAMES_URL, timeout=30) as resp:
            text = resp.read().decode("utf-8", "replace")
    except Exception:
        if cached.exists():
            print("schedule fetch failed; using the stale cached copy", file=sys.stderr)
            return json.loads(cached.read_text(encoding="utf-8"))
        raise
    rows = [r for r in csv.DictReader(io.StringIO(text))
            if r.get("season") == str(season) and r.get("game_type") == "REG"]
    cached.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def week_from_calendar(now: dt.datetime, season: int) -> int:
    """Best-effort NFL week when the schedule cannot be read at all.

    Week 1 opens on the Thursday after Labor Day (the first Monday in
    September), which is fixed by the calendar and needs no download. Used
    only on the fallback path, where the alternative was emitting week=0 --
    a week no game belongs to, so the run that was opened to protect a
    closing capture could not capture anything.
    """
    sept = dt.date(season, 9, 1)
    labor_day = sept + dt.timedelta(days=(7 - sept.weekday()) % 7)  # first Monday
    kickoff_thursday = labor_day + dt.timedelta(days=3)
    week = (now.date() - kickoff_thursday).days // 7 + 1
    return max(1, min(18, week))


def _soonest_week(games: list[dict], now: dt.datetime) -> int | None:
    """The week of the next game that has not kicked off.

    The opening sweep runs on Thursday evening, before that week's first
    kickoff, so "the next game" is this week's Thursday nighter or, once it
    has started, the Sunday slate -- either way the week the sweep is for.
    """
    best: tuple[float, int] | None = None
    for g in games:
        k = kickoff_utc(g)
        if k is None:
            continue
        lead = (k - now).total_seconds()
        if lead < -3 * 3600:          # already well under way
            continue
        if best is None or lead < best[0]:
            try:
                best = (lead, int(g["week"]))
            except (KeyError, ValueError):
                continue
    return best[1] if best else None


def _period_marker(kind: str, key: str) -> Path:
    return CACHE / f"ran_{kind}_{key}"


def period_done(kind: str, key: str) -> bool:
    return _period_marker(kind, key).exists()


def mark_period(kind: str, key: str) -> None:
    """Record that this kind ran for this period.

    THE WINDOW STAYS WIDE, THE RUN HAPPENS ONCE. Narrowing the Tuesday
    settle window to one 15-minute slot would have been the obvious fix and
    the wrong one: GitHub fires this repo's crons a median 128 minutes late
    (DECISIONS #70), which is exactly why the window is two hours. So the
    window keeps absorbing the lag and the marker stops the other seven
    ticks inside it from re-settling, re-scoring and re-pushing. The marker
    lives in the Actions cache, so a cache miss costs one duplicate run
    rather than eight.
    """
    try:
        CACHE.mkdir(parents=True, exist_ok=True)
        _period_marker(kind, key).write_text(dt.datetime.now(dt.timezone.utc).isoformat(),
                                             encoding="utf-8")
    except OSError:
        pass          # a marker we cannot write is a duplicate run, not a failure


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

    # Tuesday settle window, once per ISO week.
    if now.weekday() == 1 and 14 <= now.hour < 16:
        iso = now.isocalendar()
        key = f"{iso[0]}-W{iso[1]:02d}"
        if period_done("settle", key):
            emit(run="false", mode="idle", season=season, week=0,
                 snapshot_type="none")
            return 0
        mark_period("settle", key)
        emit(run="true", mode="settle", season=season, week=0,
             snapshot_type="decision")
        return 0

    try:
        games = load_games(season)
    except Exception as exc:  # network hiccup: open the window, do not lose a close
        # week=0 used to go out here, which no game belongs to, so the run
        # this branch exists to protect could not capture anything.
        week = week_from_calendar(now, season)
        print(f"schedule unavailable ({exc}); opening window at calendar week {week}",
              file=sys.stderr)
        emit(run="true", mode="capture", season=season, week=week,
             snapshot_type="decision")
        return 0

    # THE OPENING PRICE, ONCE A WEEK. Closing-line value needs two ends, and
    # the capture window only opens six hours before a kickoff -- by then the
    # board has already absorbed most of the week's news. A Thursday-evening
    # sweep records where the week's numbers started, so a decision made on
    # Sunday can be read against an open as well as a close. Once per ISO
    # week, on the same marker the settle window uses: the window is two
    # hours wide because GitHub fires these crons late, and the marker is
    # what stops the other seven ticks inside it.
    if now.weekday() == 3 and OPEN_FROM_HOUR <= now.hour < OPEN_TO_HOUR:
        iso = now.isocalendar()
        key = f"{iso[0]}-W{iso[1]:02d}"
        if not period_done("open", key):
            week = _soonest_week(games, now) or week_from_calendar(now, season)
            mark_period("open", key)
            emit(run="true", mode="capture", season=season, week=week,
                 snapshot_type="open")
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

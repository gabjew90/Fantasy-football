"""Timezone-explicit time handling. ALL user-facing times are Pacific.

NFL data sources report Eastern; conversion is always explicit through these
helpers — a naive datetime anywhere in manager/ is a bug.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

PT = ZoneInfo("America/Los_Angeles")
ET = ZoneInfo("America/New_York")

log = logging.getLogger("manager")


def now_pt() -> datetime:
    return datetime.now(tz=PT)


def kickoff_pt(gameday: str, gametime_et: str) -> datetime:
    """nflverse 'gameday' (YYYY-MM-DD) + 'gametime' (HH:MM, Eastern) -> aware PT."""
    if not gametime_et:
        log.warning("missing gametime for %s — defaulting 13:00 ET", gameday)
        gametime_et = "13:00"
    naive = datetime.strptime(f"{gameday} {gametime_et}", "%Y-%m-%d %H:%M")
    return naive.replace(tzinfo=ET).astimezone(PT)


def inactives_time(kickoff: datetime) -> datetime:
    """Official inactives drop ~90 minutes before each kickoff."""
    return kickoff - timedelta(minutes=90)


def fmt(dt: datetime) -> str:
    """Compact Pacific timestamp for briefs/logs: 'Sun 09/13 07:30 AM PT'."""
    return dt.astimezone(PT).strftime("%a %m/%d %I:%M %p PT")


def minutes_until(dt: datetime) -> int:
    # timestamp() is absolute time — same-zone datetime subtraction is
    # wall-clock and silently drops the DST hour (verified in tests)
    return max(0, int((dt.timestamp() - now_pt().timestamp()) // 60))

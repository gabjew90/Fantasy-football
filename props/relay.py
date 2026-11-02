"""The capture clock GitHub's cron cannot keep, and the once-a-week markers.

Stdlib only, like the guard: the relay job installs nothing.

WHY A RELAY. The workflow asks for a tick every 15 minutes and GitHub starts one about every four and
a half hours (median 268 minutes across 199 ticks to 2026-11-02), so only 3 of 13 week-8 games had a
quote from the hour before kickoff, and a missed closing line cannot be recaptured. So every finished
tick starts a job that sleeps until the next kickoff is CLOSE_AIM_MIN away, then dispatches the workflow
with mode=auto, which the guard judges exactly as it judges a scheduled tick. That run starts the next
relay, so a slate carries itself from one window to the next. A kickoff further off than one sleep gets
a bridging hop: the run it starts finds nothing due and relays again.

Commands:
  wait            print the seconds to sleep before the next hop; print nothing when no hop is due
  mark KIND       record that KIND (settle | open) is done for this ISO week, if it really is
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import guard  # noqa: E402

RECORD = Path(__file__).resolve().parent / "record"
# Inside the close window and after the inactives, which come about 90 minutes before kickoff.
CLOSE_AIM_MIN = int(os.environ.get("PROPS_CLOSE_AIM_MIN", "45"))
# A hosted runner's job limit is six hours; props.yml sets the job's timeout just above this.
MAX_SLEEP_MIN = int(os.environ.get("PROPS_RELAY_MAX_SLEEP_MIN", "340"))
# One sleep plus the longest measured gap between ticks (582 minutes), so a gap cannot jump a window.
HORIZON_MIN = int(os.environ.get("PROPS_RELAY_HORIZON_MIN", "960"))
# A capture takes about three minutes; closer than this it would start after the kickoff.
MIN_LEAD_MIN = 10


def _utc(value: str | None) -> dt.datetime | None:
    try:
        when = dt.datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    return when if when.tzinfo else None


def next_wait(games: list[dict], now: dt.datetime, close_captured_at: dt.datetime | None) -> float | None:
    """Seconds until the next hop, or None when no kickoff needs one.

    A kickoff is skipped when the `close` run that just finished started inside its close window: that
    run already took its closing line. The workflow runs this only after a tick that succeeded, so a
    failed capture is retried by the next cron tick, not by a chain of failing hops.
    """
    soonest = None
    for game in games:
        kick = guard.kickoff_utc(game)
        if kick is None:
            continue
        lead = (kick - now).total_seconds() / 60.0
        if not MIN_LEAD_MIN < lead <= HORIZON_MIN:
            continue
        if close_captured_at and (kick - close_captured_at).total_seconds() / 60.0 <= guard.CLOSE_WINDOW_MIN:
            continue
        if soonest is None or lead < soonest:
            soonest = lead
    if soonest is None:
        return None
    return min(max(soonest - CLOSE_AIM_MIN, 0.0), float(MAX_SLEEP_MIN)) * 60.0


def settle_complete(season: int, root: Path | None = None) -> bool:
    """Whether the latest predicted week is fully graded.

    THE WEEKLY STOP MUST NOT END THE RETRIES THAT MATTER. Re-running after the first settle changed
    the graded file on 2026-10-06 and 2026-10-07, so the marker is written only when every game with
    a decision in the latest week has settled rows and none of that week's rows is still pending.
    Settle grades decisions only, so a game with no decision row can never have settled rows.
    """
    root = root or RECORD
    files = sorted((root / "predictions" / str(season)).glob("wk*.jsonl"))
    settled = root / "settled" / str(season) / f"settled_{season}.csv"
    if not files or not settled.exists():
        return False
    latest = files[-1]
    week = int(latest.stem[2:])
    with latest.open(encoding="utf-8") as fh:
        rows = (json.loads(line) for line in fh if line.strip())
        predicted = {r.get("game") for r in rows if r.get("snapshot_type") == "decision"}
    with settled.open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.DictReader(fh) if str(r.get("week")) == str(week)]
    return (bool(predicted) and predicted <= {r.get("game") for r in rows}
            and not any(r.get("status") == "pending" for r in rows))


def mark(kind: str, now: dt.datetime) -> bool:
    if kind == "settle" and not (guard.in_settle_span(now) and settle_complete(guard.season_of(now))):
        return False
    guard.mark_period(kind, guard.period_key(now))
    return True


def main(argv: list[str]) -> int:
    now = dt.datetime.now(dt.timezone.utc)
    if argv[:1] == ["wait"]:
        # NOTHING HERE MAY FAIL THE RUN. The capture is already committed, and a red run opens an
        # [ACT NOW] issue; a missed hop leaves the cron ticks, which is where this started.
        try:
            wait = next_wait(guard.load_games(guard.season_of(now)), now,
                             _utc(os.environ.get("CLOSE_CAPTURED_AT")))
        except Exception as exc:  # noqa: BLE001
            print(f"relay skipped: {exc}", file=sys.stderr)
            return 0
        if wait is not None:
            print(int(wait))
        return 0
    if argv[:1] == ["mark"] and argv[1:2] in (["settle"], ["open"]):
        print(f"{argv[1]} marked: {mark(argv[1], now)}")
        return 0
    print(__doc__, file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

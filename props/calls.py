"""What counts as one call.

The record keeps every priced line at every moment, which is right: a line
that moves is history worth having. But a SCORECARD must count decisions, and
those are not the same thing. Week 2 holds 33 rows for a 32-line board because
Christian McCaffrey's rush-yards Under was captured at 58.5 and then, thirteen
minutes later, at 59.5, and `line` is part of the dedupe key so both persist.
Counted naively that is two calls, two graded rows, and a closing-line-value
join that fans out.

THE RULE. A call is the `decision` row with the latest `logged_at_utc` for one
(season, week, event, book, market, player, engine). `side` and `line` are
attributes of the call, not part of its identity -- if the model flipped sides
between ticks that is still one call, and the last one is the one that would
have been placed.

Per engine, because two engine versions' calls are never pooled (see
DECISIONS #74); each version's record has to stand on its own.

`open` and `close` rows are never calls. A game captured only inside the
closing window therefore has no call, and that is deliberate: a price-only
snapshot is not a decision, and promoting one would invent a call the model
never made.

WHY "LATEST DECISION" IS THE SAME AS "LAST BEFORE CLOSE". Decisions are only
captured before kickoff -- the workflow passes `--skip-started` -- so the last
decision is by construction the last one before the line closed. Prediction
rows do not carry `commence_time`, so this is also the only definition
available without joining the archive.

This module is the single home of the rule. Both `settle.py` and
`scorecard.py` import it rather than each deciding for itself, because two
implementations of "which row counts" would drift and the drift would look
like a change in hit rate. Stdlib only.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

CALL_KEY = ("season", "week", "event_id", "book", "market", "player",
            "engine_hash")


def call_key(row: dict) -> tuple[str, ...]:
    """The identity of the decision a row belongs to."""
    return tuple("" if row.get(f) is None else str(row.get(f, ""))
                 for f in CALL_KEY)


def parse_logged_at(row: dict) -> datetime:
    """`logged_at_utc` as a datetime.

    Raises on anything unparseable rather than falling back to string
    comparison: a row with a hand-edited or differently formatted timestamp
    would otherwise sort wrongly and silently elect the wrong call.
    """
    raw = row.get("logged_at_utc")
    if not raw:
        raise ValueError(f"row has no logged_at_utc: {call_key(row)}")
    text = str(raw).strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)          # ValueError if malformed
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _tiebreak(row: dict) -> tuple:
    """Deterministic order for two decisions logged in the same second.

    One `score_game` run stamps one timestamp across its rows, so this only
    fires for two runs inside the same second. Prefer a row with a line over
    one without, then the larger model/book gap, then the side alphabetically
    -- arbitrary but fixed, so the same input always elects the same call.
    """
    gap = row.get("gap")
    try:
        gap = abs(float(gap))
    except (TypeError, ValueError):
        gap = -1.0
    return (row.get("line") is not None, gap, str(row.get("side") or ""))


def select_calls(rows: Iterable[dict], snapshot_type: str = "decision"
                 ) -> tuple[dict[tuple[str, ...], dict], int]:
    """({identity: the row that is the call}, number of same-second ties)."""
    best: dict[tuple[str, ...], dict] = {}
    ties = 0
    for row in rows:
        if row.get("snapshot_type") != snapshot_type:
            continue
        key = call_key(row)
        current = best.get(key)
        if current is None:
            best[key] = row
            continue
        when, when_current = parse_logged_at(row), parse_logged_at(current)
        if when > when_current:
            best[key] = row
        elif when == when_current:
            ties += 1
            if _tiebreak(row) > _tiebreak(current):
                best[key] = row
    return best, ties


def mark_calls(rows: list[dict], snapshot_type: str = "decision") -> tuple[int, int]:
    """Set `is_call` on every row in place. Returns (calls, ties).

    `is_call` is derived state: it is written to the settled record, never to
    a prediction row, because a later tick can supersede a call and a stored
    flag would go stale.
    """
    best, ties = select_calls(rows, snapshot_type)
    chosen = {id(row) for row in best.values()}
    for row in rows:
        row["is_call"] = id(row) in chosen
    return len(best), ties


def last_per(rows: Iterable[dict], snapshot_type: str,
             key_fields: tuple[str, ...]) -> dict[tuple[str, ...], dict]:
    """The latest row of one snapshot type per key.

    Used for the closing side of a CLV join. It must be the LAST close, not
    the first: `guard.py` labels a whole run `close` when the soonest kickoff
    is within the hour, so an early-afternoon run also marks the late games'
    rows `close`. Taking the first would report a 12:15 line as a 16:25
    game's closing price.
    """
    best: dict[tuple[str, ...], dict] = {}
    for row in rows:
        if row.get("snapshot_type") != snapshot_type:
            continue
        key = tuple("" if row.get(f) is None else str(row.get(f, ""))
                    for f in key_fields)
        current = best.get(key)
        if current is None or parse_logged_at(row) > parse_logged_at(current):
            best[key] = row
    return best

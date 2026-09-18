"""Persistence adapter for the props historical record.

Three declared modes, so a run always says which one it used rather than
silently losing rows:

  github  running inside GitHub Actions on this repo; rows are written to the
          working tree and the workflow commits them back with the built-in
          GITHUB_TOKEN. No PAT, no secret handling here.
  local   running anywhere else (a chat container, a laptop). Rows are written
          under the record tree but nothing is committed; the caller is told
          the files must be moved into the repo to persist.
  failed  the record tree is not writable. Nothing is silently dropped: the
          caller gets the error and decides.

The record is append-and-dedupe, never overwrite. A prediction row is keyed by
(season, week, event_id, book, market, player, side, line, snapshot_type); a
second run of the same game re-writes the same keys instead of duplicating
them, so re-running a game is safe and a changed line lands as a new row.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

RECORD_ROOT = Path(__file__).resolve().parent / "record"

PREDICTION_KEY = (
    "season",
    "week",
    "event_id",
    "book",
    "market",
    "player",
    "side",
    "line",
    "snapshot_type",
)

LINE_KEY = (
    "season",
    "week",
    "event_id",
    "bookmaker",
    "market",
    "player",
    "outcome",
    "point",
    "snapshot_type",
)


def mode() -> str:
    """Which persistence mode this process is running in."""
    if not RECORD_ROOT.exists():
        try:
            RECORD_ROOT.mkdir(parents=True, exist_ok=True)
        except OSError:
            return "failed"
    if not os.access(RECORD_ROOT, os.W_OK):
        return "failed"
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "github"
    return "local"


def _key(row: dict, fields: tuple[str, ...]) -> tuple:
    return tuple(str(row.get(f, "")) for f in fields)


def append_jsonl(path: Path, rows: list[dict], key_fields: tuple[str, ...]) -> dict:
    """Append rows to a JSONL file, replacing any row with the same key.

    Returns a summary: existing count, added, replaced, final count.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[tuple, dict] = {}
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                existing[_key(r, key_fields)] = r
    before = len(existing)
    added = replaced = 0
    for row in rows:
        k = _key(row, key_fields)
        if k in existing:
            replaced += 1
        else:
            added += 1
        existing[k] = row
    with path.open("w", encoding="utf-8") as fh:
        for row in existing.values():
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return {
        "path": str(path),
        "before": before,
        "added": added,
        "replaced": replaced,
        "after": len(existing),
    }


def predictions_path(season: int, week: int) -> Path:
    return RECORD_ROOT / "predictions" / str(season) / f"wk{week:02d}.jsonl"


def lines_path(season: int) -> Path:
    return RECORD_ROOT / "lines" / str(season) / f"line_archive_{season}.jsonl"


def settled_path(season: int) -> Path:
    return RECORD_ROOT / "settled" / str(season) / f"settled_{season}.csv"


def write_predictions(season: int, week: int, rows: list[dict]) -> dict:
    out = append_jsonl(predictions_path(season, week), rows, PREDICTION_KEY)
    out["mode"] = mode()
    return out


def write_lines(season: int, rows: list[dict]) -> dict:
    out = append_jsonl(lines_path(season), rows, LINE_KEY)
    out["mode"] = mode()
    return out

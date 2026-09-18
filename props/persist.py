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
(season, week, event_id, book, market, player, side, line, snapshot_type,
engine_hash); a second run of the same game re-writes the same keys instead of
duplicating them, so re-running a game is safe, a changed line lands as a new
row, and a new ENGINE never overwrites an older engine's calls.

A line archive row keeps its own key without the engine: a book quote is a
market fact, so the stamp on it records which build captured it rather than
which model produced it, and re-capturing the same quote under a new engine
should still collapse to one row.
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
    # WHAT MAKES "NEVER POOL TWO ENGINES" POSSIBLE. Without the engine in the
    # key, re-scoring a game under a new engine REPLACES the old engine's
    # rows -- same line, same side -- overwriting their p_model, gap and tier
    # and restamping them with the new version. The old engine's record would
    # vanish and its survivors would lie about their provenance. With it: a
    # new engine writes new rows, and the same engine re-run still dedupes.
    "engine_hash",
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
    # ATOMIC, BECAUSE THE RECORD CANNOT BE REBUILT. This merges the whole file
    # in memory and then replaces it; truncating the real path first meant a
    # runner timeout or an OOM kill mid-write left a half-written archive,
    # which the workflow's `if: always()` commit step would then push over the
    # only copy. os.replace is atomic within a filesystem, so a killed process
    # leaves either the old file or the new one.
    tmp = path.with_name(path.name + ".tmp")
    # newline="\n": the record is read on Linux and on this Windows host, and
    # a file whose bytes depend on the writer's platform is a file whose
    # diffs lie.
    with tmp.open("w", encoding="utf-8", newline="\n") as fh:
        for row in existing.values():
            fh.write(json.dumps(row, sort_keys=True) + "\n")
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)
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

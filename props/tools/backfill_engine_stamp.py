"""Stamp the engine onto the rows recorded before there was a stamp.

One-off, run once on 2026-09-17, kept in the tree as provenance for the diff
it produced.

WHY BACKFILL RATHER THAN LEAVE THEM NULL. Every row in the record was written
by the engine as vendored in b4d8a0e, and `git diff b4d8a0e HEAD --
props/engine` is empty: the tree object is 9e754537 at every commit since. So
the hash is derived, not guessed -- this script computes it from the tree and
refuses to take one on the command line.

A null bucket would also be actively harmful rather than merely incomplete.
`engine_hash` is now part of the prediction key, so the next capture of the
same board -- identical lines, same engine -- would not dedupe against
unstamped rows. Week 2 would hold two copies of one board, and the scorecard
would refuse to pool two "engines" that are the same code.

Idempotent: `setdefault`, never overwrite, and the row count must come out
unchanged or nothing is written.

Usage:
    python props/tools/backfill_engine_stamp.py [--dry-run]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROPS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROPS))
import engine_version  # noqa: E402
import persist  # noqa: E402


def backfill(path: Path, stamp: dict, dry_run: bool = False) -> tuple[int, int]:
    """(rows, rows newly stamped) for one JSONL file."""
    rows = []
    stamped = 0
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            before = row.get("engine_hash")
            row.setdefault("engine_hash", stamp["engine_hash"])
            row.setdefault("engine_tag", stamp["engine_tag"])
            if before != row["engine_hash"]:
                stamped += 1
            rows.append(row)
    if not dry_run:
        tmp = path.with_name(path.name + ".tmp")
        with tmp.open("w", encoding="utf-8", newline="\n") as fh:
            for row in rows:
                fh.write(json.dumps(row, sort_keys=True) + "\n")
        # Same rewrite discipline as persist.append_jsonl: a half-written
        # record is worse than an unstamped one.
        import os
        os.replace(tmp, path)
    return len(rows), stamped


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)

    stamp = engine_version.stamp()
    if stamp["engine_tag"] is None:
        print("the engine tree does not match props/engine.lock.json; write "
              "the lock first, or the backfill would stamp an untagged hash "
              "onto rows a release produced", file=sys.stderr)
        return 2
    print(f"stamping engine_hash={stamp['engine_hash'][:12]} "
          f"engine_tag={stamp['engine_tag']}")

    files = sorted((persist.RECORD_ROOT).rglob("*.jsonl"))
    if not files:
        print(f"no record files under {persist.RECORD_ROOT}", file=sys.stderr)
        return 2
    total = 0
    for path in files:
        before = sum(1 for line in path.open(encoding="utf-8") if line.strip())
        rows, stamped = backfill(path, stamp, a.dry_run)
        if rows != before:
            print(f"ABORT {path}: {before} rows in, {rows} out", file=sys.stderr)
            return 1
        total += stamped
        print(f"  {path.relative_to(persist.RECORD_ROOT)}: {rows} rows, "
              f"{stamped} newly stamped{' (dry run)' if a.dry_run else ''}")
    print(f"{total} rows stamped across {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

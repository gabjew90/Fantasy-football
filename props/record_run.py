"""File a scorer run's outputs into the historical record.

Reads the two artifacts every `score_game.py` run already writes:
  - shadow_log_<season>_wk<NN>_<AWAY>_<HOME>.csv   (one row per priced line,
    carrying the model's probability, the no-vig probability, the tier and the
    decision at the moment of the call)
  - line_archive_nfl_<season>.jsonl               (the raw book quote)

and appends them to `record/predictions/<season>/wk<NN>.jsonl` and
`record/lines/<season>/line_archive_<season>.jsonl` through `persist.py`, which
de-duplicates on the natural key. Re-running a game is therefore idempotent.

`snapshot_type` separates an opening call from a closing capture of the same
line, so closing-line value is computable later:
  decision  the call as made (the model ran, a tier was assigned)
  open      a price-only capture well before kickoff
  close     a price-only capture inside 60 minutes of kickoff

Usage:
    python props/record_run.py --dir /path/to/scorer/outputs [--snapshot-type decision]
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine_version  # noqa: E402
import persist  # noqa: E402

SHADOW_RE = re.compile(r"shadow_log_(\d{4})_wk(\d{2})_([A-Z]{2,3})_([A-Z]{2,3})\.csv$")
ARCHIVE_RE = re.compile(r"line_archive_nfl_(\d{4})\.jsonl$")

# Fields kept on a prediction row. Everything needed to grade the call later
# and to reconstruct why it was made, without carrying the whole model state.
PRED_FIELDS = [
    "logged_at_utc", "season", "week", "event_id", "book", "market", "player",
    "team", "slot", "line", "model_mean", "side", "p_model", "p_push",
    "p_novig", "gap", "price", "ER", "last_update", "new_team", "questionable",
    "flag", "model_state", "decision", "clears_edge_rule_if_validated", "tier",
]

NUMERIC = {"line", "model_mean", "p_model", "p_push", "p_novig", "gap", "price", "ER"}
INTEGER = {"season", "week"}
BOOLEAN = {"new_team", "questionable", "clears_edge_rule_if_validated"}


def _coerce(field: str, value: str):
    if value is None or value == "":
        return None
    if field in INTEGER:
        try:
            return int(float(value))
        except ValueError:
            return None
    if field in NUMERIC:
        try:
            return float(value)
        except ValueError:
            return None
    if field in BOOLEAN:
        return str(value).strip().lower() in ("true", "1", "yes")
    return value


def read_shadow_log(path: Path, snapshot_type: str, game: str,
                    stamp: dict | None = None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for raw in csv.DictReader(fh):
            row = {f: _coerce(f, raw.get(f, "")) for f in PRED_FIELDS}
            row["snapshot_type"] = snapshot_type
            row["game"] = game
            row["engine_run_file"] = path.name
            # WHICH ENGINE MADE THIS CALL. `model_state` is the engine's own
            # per-market label and has been wrong before; this is computed
            # from the tree that ran.
            row.update(stamp or {})
            rows.append(row)
    return rows


def read_archive(path: Path, season: int, week: int | None, snapshot_type: str,
                 stamp: dict | None = None) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            r.setdefault("season", season)
            # The scorer stamps its own week on every quote, so this only
            # fills a gap -- and it fills it ONLY when the run covered one
            # unambiguous week. It used to take the lowest week among
            # whatever shadow logs sat in the directory, which silently
            # mislabelled quotes (and `week` is part of the dedupe key, so a
            # mislabel duplicates the row rather than updating it).
            if r.get("week") in (None, ""):
                if week is None:
                    print(f"{path.name}: a quote carries no week and this run "
                          f"covers none or several; left unstamped", file=sys.stderr)
                else:
                    r["week"] = week
            r.setdefault("snapshot_type", snapshot_type)
            # A quote is a market fact, so the stamp says which build
            # captured it, not who produced it.
            r.update(stamp or {})
            rows.append(r)
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True,
                    help="directory holding the scorer's output files")
    ap.add_argument("--snapshot-type", default="decision",
                    choices=["decision", "open", "close"])
    ap.add_argument("--engine-dir", type=Path, default=engine_version.ENGINE_DIR,
                    help="the engine tree that produced these artifacts")
    args = ap.parse_args()

    src = Path(args.dir)
    if not src.is_dir():
        print(f"not a directory: {src}", file=sys.stderr)
        return 2

    # THE ONLY HARD REFUSAL. With no engine tree there is nothing to stamp,
    # and an unstamped row cannot be told apart from another version's later.
    if not args.engine_dir.is_dir():
        print(f"not an engine directory: {args.engine_dir}; refusing to file "
              f"rows that cannot say which engine made them", file=sys.stderr)
        return 2
    # A HASH THAT DOES NOT MATCH THE LOCK IS NOT AN ERROR HERE. This runs in
    # the capture path, where a lost slate is unrecoverable and a mislabelled
    # tag is a one-line fix: stamp the computed hash, withhold the tag, warn.
    stamp = engine_version.stamp(args.engine_dir)
    if stamp["engine_tag"] is None:
        print(f"engine {stamp['engine_hash'][:12]} does not match "
              f"{engine_version.LOCK_PATH.name}; rows carry the computed hash "
              f"and no tag", file=sys.stderr)

    shadow_files = sorted(p for p in src.iterdir() if SHADOW_RE.search(p.name))
    archive_files = sorted(p for p in src.iterdir() if ARCHIVE_RE.search(p.name))
    if not shadow_files and not archive_files:
        print(f"no scorer artifacts found in {src}", file=sys.stderr)
        return 2

    summaries = []
    by_week: dict[tuple[int, int], list[dict]] = {}
    for f in shadow_files:
        m = SHADOW_RE.search(f.name)
        season, week = int(m.group(1)), int(m.group(2))
        game = f"{m.group(3)}@{m.group(4)}"
        by_week.setdefault((season, week), []).extend(
            read_shadow_log(f, args.snapshot_type, game, stamp))
    for (season, week), rows in sorted(by_week.items()):
        summaries.append(persist.write_predictions(season, week, rows))

    for f in archive_files:
        season = int(ARCHIVE_RE.search(f.name).group(1))
        weeks = sorted({w for (s, w) in by_week if s == season})
        week = weeks[0] if len(weeks) == 1 else None
        summaries.append(persist.write_lines(
            season, read_archive(f, season, week, args.snapshot_type, stamp)))

    print(f"engine={stamp['engine_hash'][:12]} "
          f"tag={stamp['engine_tag'] or '(untagged)'}")
    for s in summaries:
        print(f"[{s['mode']}] {s['path']}: {s['before']} -> {s['after']} "
              f"(+{s['added']} new, {s['replaced']} replaced)")
    if summaries and summaries[0]["mode"] == "local":
        print("\nmode=local: rows are on disk but NOT committed. Move the "
              "record/ tree into the repo, or run this inside the props "
              "workflow, for them to persist.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

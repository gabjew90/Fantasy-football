"""The snapshot manifest: what a run read, from where, and how old it was.

Every fetch through core.fetch can record itself here. A report prints the
manifest's summary line, and the fantasy decision gate reads the manifest
rather than a hand-written receipt: "the roster was read after the request
started" is a fact about an entry here, not a claim someone typed.

Statuses:
  fresh    downloaded during this run
  cached   an existing copy young enough to reuse
  stale    a refresh failed and an older copy was used instead
  failed   nothing usable; the caller raised or degraded
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

STATUSES = ("fresh", "cached", "stale", "failed")


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _aware(t: dt.datetime | None) -> dt.datetime | None:
    """Naive datetimes are taken as UTC, so every comparison here is between
    aware values (a naive start time would otherwise raise TypeError)."""
    if t is None or t.tzinfo is not None:
        return t
    return t.replace(tzinfo=dt.timezone.utc)


class Manifest:
    def __init__(self, purpose: str = "", started_at: dt.datetime | None = None):
        self.purpose = purpose
        self.started_at = _aware(started_at) or utcnow()
        self.entries: list[dict] = []

    def record(self, name: str, *, source: str, status: str, path: str | Path | None = None,
               fetched_at: dt.datetime | None = None, detail: str = "", rows: int | None = None) -> dict:
        if status not in STATUSES:
            raise ValueError(f"unknown manifest status {status!r}")
        fetched_at = _aware(fetched_at)
        age_h = None
        if fetched_at is not None:
            age_h = round(max(0.0, (utcnow() - fetched_at).total_seconds()) / 3600, 2)
        e = {"name": name, "source": source, "status": status,
             "path": str(path) if path is not None else None,
             "fetched_at_utc": fetched_at.isoformat() if fetched_at else None,
             "age_h": age_h, "rows": rows, "detail": detail}
        # one entry per name: a later read of the same input replaces the earlier
        self.entries = [x for x in self.entries if x["name"] != name] + [e]
        return e

    def get(self, name: str) -> dict | None:
        return next((e for e in self.entries if e["name"] == name), None)

    def stale(self) -> list[dict]:
        return [e for e in self.entries if e["status"] in ("stale", "failed")]

    def read_after_start(self, name: str) -> bool:
        """True when `name` was fetched at or after this run started -- the
        test the decision gate applies to a league roster."""
        e = self.get(name)
        if not e or not e["fetched_at_utc"] or e["status"] in ("failed",):
            return False
        return _aware(dt.datetime.fromisoformat(e["fetched_at_utc"])) >= self.started_at

    def summary_line(self) -> str:
        parts = []
        for e in self.entries:
            age = "" if e["age_h"] is None else f" {e['age_h']:.1f}h"
            flag = "" if e["status"] in ("fresh", "cached") else f" {e['status'].upper()}"
            parts.append(f"{e['name']}{age}{flag}")
        return "inputs: " + (", ".join(parts) if parts else "none recorded")

    def to_dict(self) -> dict:
        return {"purpose": self.purpose, "started_at_utc": self.started_at.isoformat(),
                "entries": list(self.entries)}

    def write(self, path: str | Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
        tmp.replace(path)
        return path

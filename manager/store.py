"""Committed-state store: JSON files under state/, pushed back to the repo
after each Actions run (the commit history is the run log).

JSON over SQLite: readable diffs, painless `git pull --rebase`, and the
Actions concurrency group serializes writers. Same API the modules always
used — kv, first-time alert gate, delivery bookkeeping, bid history.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

log = logging.getLogger("manager")


class Store:
    """`read_only` makes a dry run genuinely dry.

    It was not. `python -m manager --module waivers --dry-run --week 13`
    rewrote 60 lines of state/kv.json with week-13 replacement levels, and
    state/ is committed and shipped to the live manager: a rehearsal against a
    pinned week left real state behind for the real run to read. The writers
    are spread across jobs, the gate and the briefs and each would have to
    learn about dry_run separately, so the flag lives at the one place they
    all go through. Writes become no-ops and are logged, rather than raising,
    because a dry run's job is to render the brief all the way to the end.
    """

    def __init__(self, state_dir: str | Path, read_only: bool = False):
        self.dir = Path(state_dir)
        self.read_only = bool(read_only)
        self.suppressed: list[str] = []
        if not self.read_only:
            self.dir.mkdir(parents=True, exist_ok=True)

    def _load(self, name: str) -> dict:
        f = self.dir / f"{name}.json"
        if not f.exists():
            return {}
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            return {}

    def _save(self, name: str, data: dict) -> None:
        if self.read_only:
            self.suppressed.append(name)
            log.info("dry run: not writing state/%s.json", name)
            return
        (self.dir / f"{name}.json").write_text(
            json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")

    # -- kv --------------------------------------------------------------
    def get(self, key: str, default=None):
        return self._load("kv").get(key, default)

    def set(self, key: str, value) -> None:
        data = self._load("kv")
        data[key] = value
        self._save("kv", data)

    # -- alert dedup ----------------------------------------------------
    def first_time(self, alert_id: str) -> bool:
        """True exactly once per alert id — the diff-based alerting gate."""
        seen = self._load("seen")
        if alert_id in seen:
            return False
        seen[alert_id] = time.time()
        self._save("seen", seen)
        return True

    # -- delivery bookkeeping -------------------------------------------
    def message(self, brief_key: str) -> tuple[str | None, str | None]:
        row = self._load("messages").get(brief_key)
        return (row.get("id"), row.get("hash")) if row else (None, None)

    def save_message(self, brief_key: str, message_id: str | None, content_hash: str) -> None:
        data = self._load("messages")
        data[brief_key] = {"id": message_id, "hash": content_hash, "ts": time.time()}
        self._save("messages", data)

    def record_bid(self, week: int, player: str, amount: int) -> None:
        data = self._load("bids")
        data.setdefault(str(week), []).append(
            {"player": player, "amount": amount, "ts": time.time()})
        self._save("bids", data)

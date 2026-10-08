"""Committed-state store: JSON files under state/ (kv.json, with the ledger
directory beside it).

JSON over SQLite: readable diffs, painless `git pull --rebase`. The fantasy
commands read the consensus cache through `get` and write the ledger under
`dir`. The alert-dedup, delivery and bid-history methods went with the
retired cron stack (DECISIONS #212).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger("manager")


class Store:
    """`read_only` makes a read genuinely read-only.

    It was not. `python -m manager --module waivers --dry-run --week 13` (the
    retired cron path) rewrote 60 lines of state/kv.json with week-13
    replacement levels: a rehearsal against a pinned week left real state
    behind. The flag lives at the one place every writer goes through, and the
    fantasy commands open the store read_only. Writes become no-ops and are
    logged, rather than raising, so a read-only run renders to the end.
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

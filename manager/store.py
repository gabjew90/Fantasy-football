"""SQLite state: seen alerts, kv snapshots, Discord message ids, bid history.

Everything the idempotency rules need — re-running any job must not
double-post, and every alert is diffed against state before delivery.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path

_SCHEMA = """
CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT NOT NULL, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS seen (id TEXT PRIMARY KEY, ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS messages (
  brief_key TEXT PRIMARY KEY, message_id TEXT, content_hash TEXT NOT NULL, ts REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS bids (
  week INTEGER NOT NULL, player TEXT NOT NULL, amount INTEGER NOT NULL, ts REAL NOT NULL
);
"""


class Store:
    def __init__(self, path: str | Path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(path))
        self.db.executescript(_SCHEMA)
        self.db.commit()

    # -- kv --------------------------------------------------------------
    def get(self, key: str, default=None):
        row = self.db.execute("SELECT v FROM kv WHERE k=?", (key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set(self, key: str, value) -> None:
        self.db.execute("INSERT OR REPLACE INTO kv VALUES (?,?,?)",
                        (key, json.dumps(value), time.time()))
        self.db.commit()

    # -- alert dedup ----------------------------------------------------
    def first_time(self, alert_id: str) -> bool:
        """True exactly once per alert id — the diff-based alerting gate."""
        try:
            self.db.execute("INSERT INTO seen VALUES (?,?)", (alert_id, time.time()))
            self.db.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    # -- delivery bookkeeping -------------------------------------------
    def message(self, brief_key: str) -> tuple[str | None, str | None]:
        row = self.db.execute(
            "SELECT message_id, content_hash FROM messages WHERE brief_key=?",
            (brief_key,)).fetchone()
        return (row[0], row[1]) if row else (None, None)

    def save_message(self, brief_key: str, message_id: str | None, content_hash: str) -> None:
        self.db.execute("INSERT OR REPLACE INTO messages VALUES (?,?,?,?)",
                        (brief_key, message_id, content_hash, time.time()))
        self.db.commit()

    def record_bid(self, week: int, player: str, amount: int) -> None:
        self.db.execute("INSERT INTO bids VALUES (?,?,?,?)",
                        (week, player, amount, time.time()))
        self.db.commit()

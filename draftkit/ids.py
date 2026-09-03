"""Player identity resolution.

Primary path: the DynastyProcess cross-platform ID map (fantasypros_id /
gsis_id / pfr_id / sleeper_id), cached daily. Fallback path: normalized-name
fuzzy matching against the Sleeper player universe (handles Jr./II suffixes,
punctuation, and D/ST naming).
"""

from __future__ import annotations

import re
import time
from pathlib import Path

import polars as pl
import requests
from rapidfuzz import fuzz, process

# github.com/<org>/<repo>/raw/... is blocked in some environments; the
# raw.githubusercontent.com mirror serves the identical file.
PLAYERIDS_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv"
CACHE_TTL = 24 * 3600

_SUFFIXES = {"jr", "sr", "ii", "iii", "iv", "v", "jr.", "sr."}

# Sleeper D/ST player_id is the team abbreviation ("SF"), full name in
# first/last ("San Francisco" / "49ers"). Other sources say "49ers D/ST",
# "San Francisco 49ers", "Niners", etc.
_DST_WORDS = {"dst", "d/st", "def", "defense", "st"}


def normalize_name(name: str) -> str:
    """Lowercase, strip punctuation and generational suffixes."""
    s = name.lower().strip()
    s = re.sub(r"[.'’]", "", s)
    s = re.sub(r"[-/]", " ", s)
    s = re.sub(r"\s+", " ", s)
    parts = [p for p in s.split(" ") if p and p not in _SUFFIXES]
    return " ".join(parts)


def load_id_map(cache_dir: Path) -> pl.DataFrame:
    cache = Path(cache_dir) / "db_playerids.csv"
    if not cache.exists() or time.time() - cache.stat().st_mtime > CACHE_TTL:
        resp = requests.get(PLAYERIDS_URL, timeout=60)
        resp.raise_for_status()
        cache.write_bytes(resp.content)
    df = pl.read_csv(cache, infer_schema_length=10000, null_values=["NA"])
    casts = [pl.col("sleeper_id").cast(pl.Utf8, strict=False),
             pl.col("fantasypros_id").cast(pl.Utf8, strict=False)]
    if "espn_id" in df.columns:          # plan A1: the ESPN feed joins on this, no name matching
        casts.append(pl.col("espn_id").cast(pl.Utf8, strict=False))
    return df.with_columns(casts)


class SleeperIndex:
    """Fuzzy-match index over the Sleeper player universe."""

    def __init__(self, players: dict[str, dict]):
        self.players = players
        # position -> {normalized name: sleeper_id}; keep only fantasy positions
        self.by_pos: dict[str, dict[str, str]] = {}
        self.dst_by_token: dict[str, str] = {}
        for pid, p in players.items():
            pos = p.get("position")
            if pos == "DEF":
                city = normalize_name(p.get("first_name") or "")
                nick = normalize_name(p.get("last_name") or "")
                for token in (f"{city} {nick}", nick, city, pid.lower()):
                    if token:
                        self.dst_by_token.setdefault(token, pid)
                continue
            if pos not in ("QB", "RB", "WR", "TE", "K"):
                continue
            name = p.get("full_name") or f"{p.get('first_name','')} {p.get('last_name','')}"
            key = normalize_name(name)
            bucket = self.by_pos.setdefault(pos, {})
            # prefer active players on a name collision
            if key in bucket:
                existing = self.players[bucket[key]]
                if existing.get("active") or not p.get("active"):
                    continue
            bucket[key] = pid

    def match_dst(self, name: str) -> str | None:
        n = normalize_name(name)
        n = " ".join(w for w in n.split() if w not in _DST_WORDS)
        if n in self.dst_by_token:
            return self.dst_by_token[n]
        hit = process.extractOne(n, list(self.dst_by_token.keys()), scorer=fuzz.token_set_ratio)
        if hit and hit[1] >= 85:
            return self.dst_by_token[hit[0]]
        return None

    def match(self, name: str, position: str, team: str | None = None, min_score: int = 87) -> str | None:
        """Return sleeper_id or None. Position is required to constrain the pool."""
        pos = {"DST": "DEF", "D/ST": "DEF", "PK": "K"}.get(position, position)
        if pos == "DEF":
            return self.match_dst(name)
        bucket = self.by_pos.get(pos, {})
        key = normalize_name(name)
        if key in bucket:
            return bucket[key]
        hit = process.extractOne(key, list(bucket.keys()), scorer=fuzz.token_sort_ratio)
        if hit and hit[1] >= min_score:
            pid = bucket[hit[0]]
            if team and self.players[pid].get("team") and self.players[pid]["team"] != team:
                # name match but team disagrees — accept only very high scores
                if hit[1] < 94:
                    return None
            return pid
        return None

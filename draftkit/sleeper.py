"""Sleeper API client: retries with backoff, local caching for the big player dump."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import requests

BASE = "https://api.sleeper.app/v1"
PLAYERS_TTL_SECONDS = 24 * 3600  # refresh the ~5MB player universe at most daily


def get_json(url: str, retries: int = 4, timeout: int = 30) -> Any:
    """GET with exponential backoff. Raises after final attempt."""
    delay = 2.0
    last_err: Exception | None = None
    for attempt in range(retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001 — network layer, retry everything
            last_err = e
            if attempt < retries:
                time.sleep(delay)
                delay *= 2
    raise RuntimeError(f"GET {url} failed after {retries + 1} attempts") from last_err


class SleeperClient:
    def __init__(self, cache_dir: Path):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def league(self, league_id: str) -> dict:
        return get_json(f"{BASE}/league/{league_id}")

    def league_users(self, league_id: str) -> list[dict]:
        return get_json(f"{BASE}/league/{league_id}/users")

    def league_rosters(self, league_id: str) -> list[dict]:
        return get_json(f"{BASE}/league/{league_id}/rosters")

    def draft(self, draft_id: str) -> dict:
        return get_json(f"{BASE}/draft/{draft_id}")

    def draft_picks(self, draft_id: str) -> list[dict]:
        return get_json(f"{BASE}/draft/{draft_id}/picks")

    def user(self, username_or_id: str) -> dict | None:
        return get_json(f"{BASE}/user/{username_or_id}")

    def players(self, refresh: bool = False) -> dict[str, dict]:
        """Full NFL player universe, cached locally with a daily TTL."""
        cache = self.cache_dir / "players_nfl.json"
        if not refresh and cache.exists():
            age = time.time() - cache.stat().st_mtime
            if age < PLAYERS_TTL_SECONDS:
                with open(cache) as f:
                    return json.load(f)
        data = get_json(f"{BASE}/players/nfl", timeout=120)
        tmp = cache.with_suffix(".tmp")
        with open(tmp, "w") as f:
            json.dump(data, f)
        tmp.replace(cache)
        return data


def resolve_my_slot(cfg, client: SleeperClient) -> tuple[int | None, dict]:
    """Resolve the configured identity to a draft slot.

    Returns (draft_slot or None, info dict for display).
    """
    me = cfg.get("me") or {}
    info: dict[str, Any] = {}
    if me.get("draft_slot"):
        return int(me["draft_slot"]), {"source": "config draft_slot"}

    user_id = me.get("user_id")
    if not user_id and me.get("username"):
        u = client.user(str(me["username"]))
        if u:
            user_id = u.get("user_id")
            info["username"] = u.get("display_name")
    if not user_id:
        return None, {"error": "no identity configured (set me.username / me.user_id / me.draft_slot in config.yaml)"}

    draft = client.draft(cfg.draft_id)
    order = draft.get("draft_order") or {}
    slot = order.get(str(user_id))
    if slot is None:
        return None, {"error": f"user_id {user_id} not found in draft_order — order may not be finalized"}
    info["source"] = "sleeper draft_order"
    info["user_id"] = user_id
    return int(slot), info

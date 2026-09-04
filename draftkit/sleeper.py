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

    def league_drafts(self, league_id: str) -> list[dict]:
        return get_json(f"{BASE}/league/{league_id}/drafts")

    def user(self, username_or_id: str) -> dict | None:
        return get_json(f"{BASE}/user/{username_or_id}")

    def players(self, refresh: bool = False) -> dict[str, dict]:
        """Full NFL player universe, cached locally with a daily TTL."""
        cache = self.cache_dir / "players_nfl.json"
        if not refresh and cache.exists():
            age = time.time() - cache.stat().st_mtime
            if age < PLAYERS_TTL_SECONDS:
                with open(cache, encoding="utf-8") as f:
                    return json.load(f)
        data = get_json(f"{BASE}/players/nfl", timeout=120)
        tmp = cache.with_suffix(".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f)
        tmp.replace(cache)
        return data


class IdentityError(RuntimeError):
    """The configured identity did not resolve to exactly one roster."""


def resolve_my_roster(cfg, users: dict[str, str], rosters: list[dict],
                      client: SleeperClient) -> tuple[dict, dict]:
    """Which roster is MINE. Returns (roster, info); raises IdentityError.

    The old rule matched `me.username` against Sleeper DISPLAY NAMES and fell
    back to `rosters[0]` when nothing matched -- a stranger's roster, silently,
    with every downstream module then reporting "your lineup" and "your budget"
    about it. A display-name change or a typo was enough to trigger it.

    Resolution order, mirroring resolve_my_slot:
      1. me.user_id, when set. The stable id.
      2. client.user(me.username)["user_id"]. The authoritative lookup: it
         survives a display-name change, which the old path did not.
      3. case-insensitive display name. Last resort, the historical behaviour.

    Exactly one roster must match. Zero matches raises. A me.user_id that
    disagrees with the username lookup raises rather than silently preferring
    one, because a stale id recorded as correct is the corruption class the
    repo's deadline-conduct rule is about.
    """
    me = cfg.get("me") or {}
    username = str(me.get("username") or "").strip()
    cfg_uid = str(me.get("user_id") or "").strip() or None

    looked_up = None
    if username:
        try:
            u = client.user(username)
            looked_up = str(u.get("user_id")) if u and u.get("user_id") else None
        except Exception as e:                       # noqa: BLE001 - network is not identity
            looked_up = None
            me.setdefault("_lookup_error", str(e)[:120])

    if cfg_uid and looked_up and cfg_uid != looked_up:
        raise IdentityError(
            f"identity conflict for league {cfg.league_name!r}: me.user_id={cfg_uid} but "
            f"sleeper says username {username!r} is user_id={looked_up}. One of them is "
            f"stale. Fix leagues/{cfg.league_name}.yaml before this runs again.")

    uid, source = (cfg_uid, "me.user_id") if cfg_uid else (looked_up, "username lookup")
    matches = [r for r in rosters if uid and str(r.get("owner_id")) == uid]
    if not matches and username:
        by_name = {u for u, n in users.items() if str(n).lower() == username.lower()}
        matches = [r for r in rosters if str(r.get("owner_id")) in by_name]
        if matches:
            source = "display name"

    if len(matches) != 1:
        roll = ", ".join(f"{n} (owner {u})" for u, n in sorted(users.items(), key=lambda kv: kv[1]))
        raise IdentityError(
            f"identity not resolved for league {cfg.league_name!r}: "
            f"me.username={username!r}, me.user_id={cfg_uid or 'unset'}, "
            f"username lookup returned {looked_up or 'None'}; matched {len(matches)} of "
            f"{len(rosters)} rosters. League display names: {roll}. "
            f"Set me.user_id in leagues/{cfg.league_name}.yaml.")

    roster = matches[0]
    return roster, {"source": source, "user_id": str(roster.get("owner_id")),
                    "display": users.get(str(roster.get("owner_id")), "?"),
                    "roster_id": roster.get("roster_id")}


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

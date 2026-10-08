"""The player file age (2026-09-10).

Henry + Warren for Egbuka + A.J. Brown priced at +1.16/wk with Brown Out
(ankle) on Sleeper, partly because the player file it ran on was a day old.
The fence that outlives the retired trade radar (DECISIONS #212): the Sleeper
player file is refetched after a few hours in season.
"""

from __future__ import annotations

import json
import time


def test_players_cache_is_refetched_when_older_than_max_age(tmp_path, monkeypatch):
    from draftkit import sleeper

    cache = tmp_path / "players_nfl.json"
    cache.write_text(json.dumps({"1": {"injury_status": None}}), encoding="utf-8")
    old = time.time() - 5 * 3600
    import os
    os.utime(cache, (old, old))
    fetched = []
    monkeypatch.setattr(sleeper, "get_json", lambda url, timeout=30: fetched.append(url) or {"1": {"injury_status": "Out"}})
    client = sleeper.SleeperClient(tmp_path)
    assert client.players()["1"]["injury_status"] is None, "five hours is inside the daily TTL"
    assert client.players(max_age=3 * 3600)["1"]["injury_status"] == "Out"
    assert len(fetched) == 1

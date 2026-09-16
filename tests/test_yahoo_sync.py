"""No Yahoo secret on Actions: the machine that signed in syncs the payloads
into committed state and yahoo_api.get answers from them (2026-09-16)."""

from __future__ import annotations

import json
import time

import pytest

from manager import yahoo_api, yahoo_sync


@pytest.fixture
def no_creds(monkeypatch, tmp_path):
    for k in ("YAHOO_CLIENT_ID", "YAHOO_CLIENT_SECRET", "YAHOO_REFRESH_TOKEN"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setattr(yahoo_api, "TOKEN_PATH", tmp_path / "no-token.json")
    monkeypatch.setattr(yahoo_api, "cache_dir", lambda: tmp_path / "yahoo")
    return tmp_path


def test_without_credentials_get_reads_the_synced_payload(no_creds):
    path = "league/nfl.l.49649/teams/roster"
    with pytest.raises(yahoo_api.YahooAuthError, match="no synced copy"):
        yahoo_api.get(path, token_path=no_creds / "no-token.json")
    yahoo_api.write_cached(path, {"fantasy_content": {"x": 1}})
    assert yahoo_api.get(path, token_path=no_creds / "no-token.json") == {"fantasy_content": {"x": 1}}
    f = no_creds / "yahoo" / "league_nfl.l.49649_teams_roster.json"
    blob = json.loads(f.read_text())
    assert blob["path"] == path and time.time() - blob["fetched_at"] < 60


def test_cache_slugs_keep_resource_paths_distinct():
    a = yahoo_api.cache_slug("league/nfl.l.49649/scoreboard;week=2")
    b = yahoo_api.cache_slug("league/nfl.l.49649/scoreboard;week=1")
    assert a != b and "/" not in a and ";" not in a


def test_sync_fetches_every_resource_and_keeps_going_past_a_failure(tmp_path):
    class Cfg(dict):
        league_id = "49649"
    calls = []

    def get(path, params=None):
        calls.append(path)
        if "standings" in path:
            raise RuntimeError("yahoo hiccup")
        return {"payload_for": path}

    out = yahoo_sync.sync(Cfg(), week=2, get=get, directory=tmp_path / "yahoo")
    assert set(out) == set(yahoo_sync.resources("49649", 2))
    assert "league/nfl.l.49649/scoreboard;week=1" in out, "last week's scoreboard feeds the ledger"
    assert out["league/nfl.l.49649/standings"].startswith("FAILED: RuntimeError")
    assert all(v == "ok" for k, v in out.items() if "standings" not in k)
    written = sorted(p.name for p in (tmp_path / "yahoo").glob("*.json"))
    assert len(written) == len(out) - 1
    assert "league/nfl.l.49649/scoreboard;week=0" not in yahoo_sync.resources("49649", 1)


def test_the_source_reports_the_age_of_synced_data(no_creds, monkeypatch):
    from manager import yahoo_context as yc
    from tests.test_yahoo_context import CFG, PLAYERS, ROSTERS, SETTINGS
    yahoo_api.write_cached("league/nfl.l.49649/teams/roster", ROSTERS)
    yahoo_api.write_cached("league/nfl.l.49649/settings", SETTINGS)
    src = yc.YahooSource(CFG, players=PLAYERS, id_map={})
    src.league()
    assert any("from the local sync, 0.0h old" in n for n in src.notes), src.notes
    old = no_creds / "yahoo" / "league_nfl.l.49649_teams_roster.json"
    blob = json.loads(old.read_text())
    blob["fetched_at"] = time.time() - 9 * 3600
    old.write_text(json.dumps(blob))
    src2 = yc.YahooSource(CFG, players=PLAYERS, id_map={})
    src2.league()
    assert any(n.startswith("⚠") and "9.0h old" in n and "sync job" in n for n in src2.notes), src2.notes

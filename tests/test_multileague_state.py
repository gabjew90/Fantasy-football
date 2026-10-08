"""Two leagues, two state directories (2026-09-16).

One `state/` served every league while only Omnibeta ran. The store keys and
the Yahoo sync are per league, so a second league would have read and
overwritten the first league's. The default league keeps `state/`; every
other league gets `state/<league>/`; Yahoo's refresh token bootstraps the
token file on a fresh checkout. (The gate guard and the week-plan tests went
with the retired cron stack, DECISIONS #212.)
"""

from __future__ import annotations

import json
import pathlib

from manager import context, yahoo_api
from manager.store import Store


class Cfg(dict):
    def __init__(self, league_name, default="omnibeta"):
        super().__init__({"default_league": default})
        self.league_name = league_name


def _configure(monkeypatch, league):
    monkeypatch.setattr(context.Config, "load", staticmethod(lambda league=None: Cfg(league or "omnibeta")))
    context.configure(league=league)


def test_the_default_league_keeps_state_and_the_others_get_a_subdirectory(monkeypatch):
    _configure(monkeypatch, None)
    assert context.state_dir() == pathlib.Path("state")
    _configure(monkeypatch, "omnibeta")
    assert context.state_dir() == pathlib.Path("state")
    _configure(monkeypatch, "keefamania")
    assert context.state_dir() == pathlib.Path("state") / "keefamania"
    context.configure()


def test_store_and_yahoo_cache_follow_the_league(monkeypatch):
    _configure(monkeypatch, "keefamania")
    try:
        assert Store(context.state_dir(), read_only=True).dir == pathlib.Path("state") / "keefamania"
        assert yahoo_api.cache_dir() == pathlib.Path("state") / "keefamania" / "yahoo"
    finally:
        context.configure()


# --------------------------------------------------------- the yahoo token

def test_the_refresh_token_secret_bootstraps_a_missing_token_file(tmp_path, monkeypatch):
    path = tmp_path / "token.json"
    monkeypatch.delenv("YAHOO_REFRESH_TOKEN", raising=False)
    assert yahoo_api._load(path) is None
    monkeypatch.setenv("YAHOO_REFRESH_TOKEN", "R-from-secret")
    seed = yahoo_api._load(path)
    assert seed["refresh_token"] == "R-from-secret" and seed["obtained_at"] == 0
    monkeypatch.setenv("YAHOO_CLIENT_ID", "id")
    monkeypatch.setenv("YAHOO_CLIENT_SECRET", "secret")
    posted = {}

    class R:
        status_code = 200
        text = json.dumps({"access_token": "A", "expires_in": 3600})

        def json(self):
            return json.loads(self.text)

    monkeypatch.setattr(yahoo_api.requests, "post", lambda url, data=None, headers=None, timeout=None: posted.update(data) or R())
    assert yahoo_api.access_token(path) == "A"
    assert posted["grant_type"] == "refresh_token" and posted["refresh_token"] == "R-from-secret"
    assert json.loads(path.read_text())["refresh_token"] == "R-from-secret", "the secret survives into the file"

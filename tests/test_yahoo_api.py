"""manager.yahoo_api: the OAuth plumbing and, above all, telling "the app is
not approved for Fantasy Sports" apart from "the token is broken"."""

from __future__ import annotations

import json
import time

import pytest

from manager import yahoo_api


class _Resp:
    def __init__(self, status, body):
        self.status_code, self.text = status, body

    def json(self):
        return json.loads(self.text)


@pytest.fixture
def creds(monkeypatch, tmp_path):
    monkeypatch.setenv("YAHOO_CLIENT_ID", "id")
    monkeypatch.setenv("YAHOO_CLIENT_SECRET", "secret")
    return tmp_path / "token.json"


def test_auth_url_carries_the_client_id_and_oob_redirect(creds):
    url = yahoo_api.auth_url()
    assert "client_id=id" in url and "redirect_uri=oob" in url and "response_type=code" in url
    assert "secret" not in url


def test_exchange_saves_the_token_with_a_timestamp(creds, monkeypatch):
    seen = {}

    def post(url, data=None, headers=None, timeout=None):
        seen.update(data)
        assert headers["Authorization"].startswith("Basic ")
        return _Resp(200, json.dumps({"access_token": "A", "refresh_token": "R", "expires_in": 3600}))

    monkeypatch.setattr(yahoo_api.requests, "post", post)
    tok = yahoo_api.exchange(" abc123 ", creds)
    assert seen["code"] == "abc123" and seen["grant_type"] == "authorization_code"
    assert tok["obtained_at"] > 0 and json.loads(creds.read_text())["refresh_token"] == "R"


def test_an_expired_access_token_is_refreshed_before_use(creds, monkeypatch):
    creds.write_text(json.dumps({"access_token": "OLD", "refresh_token": "R", "expires_in": 3600,
                                 "obtained_at": time.time() - 4000}))
    calls = []
    monkeypatch.setattr(yahoo_api.requests, "post", lambda url, data=None, headers=None, timeout=None:
                        calls.append(data) or _Resp(200, json.dumps({"access_token": "NEW", "expires_in": 3600})))
    assert yahoo_api.access_token(creds) == "NEW"
    assert calls[0]["grant_type"] == "refresh_token" and calls[0]["refresh_token"] == "R"
    assert json.loads(creds.read_text())["refresh_token"] == "R", "the refresh token survives a refresh"


@pytest.mark.parametrize("status,body", [
    (401, '{"error":{"description":"oauth_problem=additional_authorization_required"}}'),
    (403, '{"error":{"description":"This application is not authorized to perform this action."}}'),
])
def test_the_approval_gate_is_named_not_debugged(creds, monkeypatch, status, body):
    """Both spellings Yahoo uses for 'no Fantasy Sports scope' (2026-08-19 and
    2026-09-11, the second measured on the user's own app) raise
    YahooScopeError, so nobody spends an evening on a token that works."""
    creds.write_text(json.dumps({"access_token": "A", "refresh_token": "R", "expires_in": 3600,
                                 "obtained_at": time.time()}))
    monkeypatch.setattr(yahoo_api.requests, "get", lambda *a, **k: _Resp(status, body))
    with pytest.raises(yahoo_api.YahooScopeError, match="no Fantasy Sports scope"):
        yahoo_api.get("game/nfl", token_path=creds)


def test_a_plain_401_retries_once_with_a_refreshed_token(creds, monkeypatch):
    creds.write_text(json.dumps({"access_token": "A", "refresh_token": "R", "expires_in": 3600,
                                 "obtained_at": time.time()}))
    monkeypatch.setattr(yahoo_api.requests, "post", lambda url, data=None, headers=None, timeout=None:
                        _Resp(200, json.dumps({"access_token": "B", "expires_in": 3600})))
    seen = []

    def get(url, params=None, timeout=None, headers=None):
        seen.append(headers["Authorization"])
        return _Resp(401, "{}") if len(seen) == 1 else _Resp(200, '{"fantasy_content": {}}')

    monkeypatch.setattr(yahoo_api.requests, "get", get)
    assert yahoo_api.get("game/nfl", token_path=creds) == {"fantasy_content": {}}
    assert seen == ["Bearer A", "Bearer B"]

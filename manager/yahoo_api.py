"""Yahoo Fantasy Sports API: OAuth2 tokens and GET.

Yahoo's fantasy endpoints have been approval-gated since 2026-07-22; a
token from an unapproved app is valid and still gets
`oauth_problem=additional_authorization_required` on every fantasy call.
So `get()` distinguishes that case out loud instead of leaving the caller
to debug a token that works.

Flow (authorization code, out-of-band):
  1. auth_url()                -- the user opens it, signs in, approves,
                                  and reads a short code off the page
  2. exchange(code)            -- code -> access + refresh token, saved
  3. get("league/nfl.l.49649") -- refreshes the access token when expired

Credentials: YAHOO_CLIENT_ID / YAHOO_CLIENT_SECRET in .env (gitignored).
Tokens: data/raw/yahoo/token.json (gitignored). Neither is ever logged.
"""

from __future__ import annotations

import base64
import json
import os
import time
from pathlib import Path

import requests

AUTH_URL = "https://api.login.yahoo.com/oauth2/request_auth"
TOKEN_URL = "https://api.login.yahoo.com/oauth2/get_token"
API = "https://fantasysports.yahooapis.com/fantasy/v2"
TOKEN_PATH = Path("data/raw/yahoo/token.json")
TIMEOUT = 30


class YahooAuthError(RuntimeError):
    pass


class YahooScopeError(YahooAuthError):
    """The token is fine; the app has no Fantasy Sports scope."""


def _creds() -> tuple[str, str]:
    cid, sec = os.environ.get("YAHOO_CLIENT_ID"), os.environ.get("YAHOO_CLIENT_SECRET")
    if not cid or not sec:
        raise YahooAuthError("YAHOO_CLIENT_ID / YAHOO_CLIENT_SECRET are not set in the environment")
    return cid, sec


def _basic() -> dict[str, str]:
    cid, sec = _creds()
    return {"Authorization": "Basic " + base64.b64encode(f"{cid}:{sec}".encode()).decode()}


def auth_url() -> str:
    cid, _ = _creds()
    return (f"{AUTH_URL}?client_id={cid}&redirect_uri=oob&response_type=code"
            f"&language=en-us")


def _save(tok: dict, path: Path = TOKEN_PATH) -> dict:
    tok = dict(tok)
    tok["obtained_at"] = time.time()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tok, indent=1), encoding="utf-8")
    return tok


def _load(path: Path = TOKEN_PATH) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _token_call(data: dict) -> dict:
    r = requests.post(TOKEN_URL, data=data, headers=_basic(), timeout=TIMEOUT)
    if r.status_code != 200:
        # Yahoo's error body is safe to surface (no secrets in it); the
        # request that produced it is not, so only the body is quoted.
        raise YahooAuthError(f"token endpoint {r.status_code}: {r.text[:300]}")
    return r.json()


def exchange(code: str, path: Path = TOKEN_PATH) -> dict:
    tok = _token_call({"grant_type": "authorization_code", "redirect_uri": "oob",
                       "code": code.strip()})
    return _save(tok, path)


def refresh(path: Path = TOKEN_PATH) -> dict:
    tok = _load(path)
    if not tok or not tok.get("refresh_token"):
        raise YahooAuthError("no refresh token on disk -- run the authorization flow first")
    new = _token_call({"grant_type": "refresh_token", "redirect_uri": "oob",
                       "refresh_token": tok["refresh_token"]})
    new.setdefault("refresh_token", tok["refresh_token"])
    return _save(new, path)


def access_token(path: Path = TOKEN_PATH) -> str:
    tok = _load(path)
    if not tok:
        raise YahooAuthError("no token on disk -- run the authorization flow first")
    age = time.time() - float(tok.get("obtained_at") or 0)
    if age > float(tok.get("expires_in") or 3600) - 60:
        tok = refresh(path)
    return tok["access_token"]


def get(path: str, params: dict | None = None, token_path: Path = TOKEN_PATH) -> dict:
    """GET a fantasy resource as JSON. Raises YahooScopeError when the app
    is not approved for Fantasy Sports, YahooAuthError on any other 4xx."""
    q = dict(params or {})
    q.setdefault("format", "json")
    url = f"{API}/{path.lstrip('/')}"
    r = requests.get(url, params=q, timeout=TIMEOUT,
                     headers={"Authorization": f"Bearer {access_token(token_path)}"})
    # Two spellings of the same gate: a new app gets 401
    # additional_authorization_required; an app that predates 2026-07-22
    # gets 403 "This application is not authorized to perform this action."
    if (r.status_code == 401 and "additional_authorization_required" in r.text) or \
            (r.status_code == 403 and "not authorized to perform this action" in r.text):
        raise YahooScopeError(
            f"Yahoo {r.status_code}: the token is valid but the app has no Fantasy Sports "
            f"scope (approval pending, or granted to a different Client ID)")
    if r.status_code == 401:
        # one retry on a stale access token
        r = requests.get(url, params=q, timeout=TIMEOUT,
                         headers={"Authorization": f"Bearer {refresh(token_path)['access_token']}"})
    if r.status_code >= 400:
        raise YahooAuthError(f"{path}: {r.status_code} {r.text[:300]}")
    return r.json()

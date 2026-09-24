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
    return (f"{AUTH_URL}?client_id={cid}&redirect_uri={redirect_uri()}&response_type=code"
            f"&language=en-us")


def _save(tok: dict, path: Path = TOKEN_PATH) -> dict:
    tok = dict(tok)
    tok["obtained_at"] = time.time()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(tok, indent=1), encoding="utf-8")
    return tok


def _load(path: Path = TOKEN_PATH) -> dict | None:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None
    # No file: a fresh checkout (GitHub Actions). The refresh token is the
    # durable credential -- Yahoo's OAuth needs the sign-in once, on the
    # machine that ran it -- so the scheduled jobs carry it as a secret and
    # bootstrap the file from it. An expired access token is what makes
    # access_token() refresh on the first use.
    seed = os.environ.get("YAHOO_REFRESH_TOKEN")
    if seed:
        return {"refresh_token": seed, "access_token": "", "expires_in": 0, "obtained_at": 0}
    return None


def _token_call(data: dict) -> dict:
    r = requests.post(TOKEN_URL, data=data, headers=_basic(), timeout=TIMEOUT)
    if r.status_code != 200:
        # Yahoo's error body is safe to surface (no secrets in it); the
        # request that produced it is not, so only the body is quoted.
        raise YahooAuthError(f"token endpoint {r.status_code}: {r.text[:300]}")
    return r.json()


def redirect_uri() -> str:
    """The redirect URI the app was registered with. This repo's app uses the
    out-of-band "oob"; the chat skill's app was registered with a localhost
    URL, and Yahoo checks the refresh against the registration, so the skill's
    bootstrap sets YAHOO_REDIRECT_URI from its bundle."""
    return os.environ.get("YAHOO_REDIRECT_URI") or "oob"


def exchange(code: str, path: Path = TOKEN_PATH) -> dict:
    tok = _token_call({"grant_type": "authorization_code", "redirect_uri": redirect_uri(),
                       "code": code.strip()})
    return _save(tok, path)


def refresh(path: Path = TOKEN_PATH) -> dict:
    tok = _load(path)
    if not tok or not tok.get("refresh_token"):
        raise YahooAuthError("no refresh token on disk -- run the authorization flow first")
    new = _token_call({"grant_type": "refresh_token", "redirect_uri": redirect_uri(),
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


def cache_slug(path: str) -> str:
    """A filename for one resource path: league/nfl.l.49649/teams/roster ->
    league_nfl.l.49649_teams_roster."""
    return "".join(c if c.isalnum() or c in ".-=" else "_" for c in path.strip("/"))


def cache_dir() -> Path:
    from .context import state_dir
    return state_dir() / "yahoo"


def read_cached(path: str, directory: Path | None = None) -> tuple[dict | None, float | None]:
    """(payload, fetched_at) for a resource the local sync committed, or
    (None, None)."""
    d = directory or cache_dir()
    f = d / f"{cache_slug(path)}.json"
    if not f.exists():
        return None, None
    try:
        blob = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    return blob.get("payload"), blob.get("fetched_at")


def write_cached(path: str, payload: dict, directory: Path | None = None) -> Path:
    d = directory or cache_dir()
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{cache_slug(path)}.json"
    f.write_text(json.dumps({"path": path, "fetched_at": time.time(), "payload": payload},
                            indent=1, sort_keys=True), encoding="utf-8")
    return f


def has_credentials(token_path: Path = TOKEN_PATH) -> bool:
    return bool(os.environ.get("YAHOO_CLIENT_ID") and os.environ.get("YAHOO_CLIENT_SECRET")
                and _load(token_path))


def get(path: str, params: dict | None = None, token_path: Path = TOKEN_PATH) -> dict:
    """GET a fantasy resource as JSON.

    With credentials (client id + secret + a token file or YAHOO_REFRESH_TOKEN)
    this is the live API. Without them -- GitHub Actions, where no Yahoo
    secret is stored -- it reads the payload the LOCAL SYNC committed
    (`python -m manager --league <name> yahoo-sync`, scheduled hourly on the
    machine that holds the credentials, into state/<league>/yahoo/). The
    scheduled jobs never need a Yahoo secret; they read what the sync wrote,
    the same way they read the committed Vegas snapshot.

    Raises YahooScopeError when the app is not approved for Fantasy Sports,
    YahooAuthError on any other 4xx or when neither path can answer.
    """
    q = dict(params or {})
    if not has_credentials(token_path):
        payload, fetched = read_cached(path)
        if payload is not None:
            return payload
        raise YahooAuthError(
            f"no Yahoo credentials and no synced copy of {path} -- run the yahoo-sync "
            f"job on the machine that holds them")
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

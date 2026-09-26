"""The reachability check that decides whether giving chat the FantasyPros key
would help (core/probe.py reads; manager/fantasypros.reachability asks)."""

from __future__ import annotations

import pytest

from core import probe as PR


def test_a_bot_wall_is_not_a_key_problem():
    st, what = PR.classify(403, "text/html; charset=UTF-8", "<html><title>Attention Required! | Cloudflare</title>")
    assert st == "failed" and "bot wall" in what and "would not" in what and "HTTP 403" in what


def test_the_apis_no_key_answer_is_consistent_with_a_missing_key_never_proof():
    st, what = PR.classify(403, "application/json", '{"message":"Forbidden"}')
    assert st == "failed" and "consistent with a missing key" in what and "address block" in what
    assert "'{\"message\":\"Forbidden\"}'" in what, "the evidence rides with the verdict"


def test_a_different_json_refusal_is_not_read_as_a_missing_key():
    st, what = PR.classify(403, "application/json", '{"error":"Request blocked by WAF"}')
    assert "unlike the API's no-key reply" in what and "may not help" in what


def test_no_connection_and_an_answer():
    st, what = PR.classify(None, "", "", "ConnectionError: blocked")
    assert st == "failed" and "unreachable" in what
    st, what = PR.classify(200, "application/json", "{}")
    assert st == "fresh" and what.startswith("reachable")


class _Resp:
    def __init__(self, code, ctype, text):
        self.status_code, self.headers, self.text = code, {"Content-Type": ctype}, text


def test_reachability_calls_the_real_feed_and_the_api_without_the_key(monkeypatch):
    requests = pytest.importorskip("requests")
    from manager import fantasypros as FP
    seen = {}

    def feed(pos, slug, season, kind, week=None):
        raise requests.HTTPError(response=_Resp(403, "text/html", "<html>cloudflare</html>"))

    def api(url, timeout, params, headers=None):
        seen["headers"] = headers
        return _Resp(403, "application/json", '{"message":"Forbidden"}')
    monkeypatch.setattr(FP, "_rows", feed)
    monkeypatch.setattr(FP.requests, "get", api)
    monkeypatch.setenv("FANTASYPROS_API_KEY", "secret-value-123")
    rows = FP.reachability(2026)
    assert "bot wall" in rows[0]["detail"] and "consistent with a missing key" in rows[1]["detail"]
    assert not seen["headers"], "no key is sent"
    assert rows[2]["status"] == "fresh" and rows[2]["detail"] == "set"
    assert "secret-value-123" not in repr(rows)
    monkeypatch.delenv("FANTASYPROS_API_KEY")
    rows = FP.reachability(2026)
    assert rows[2]["status"] == "absent", "a missing key is not a failed input"
    assert "| -- |" in PR.markdown(rows)

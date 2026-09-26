"""The reachability check that decides whether giving chat the FantasyPros key
would help (core/probe.py)."""

from __future__ import annotations

from core import probe as PR


def test_a_bot_wall_is_not_a_key_problem():
    st, what = PR.classify(403, "text/html; charset=UTF-8", "<html><title>Attention Required! | Cloudflare</title>")
    assert st == "failed" and "bot wall" in what and "would not" in what


def test_a_refusal_as_data_is_what_a_key_fixes():
    st, what = PR.classify(403, "application/json", '{"message":"Forbidden"}')
    assert st == "failed" and "a key is what it wants" in what
    st, what = PR.classify(401, "application/json", '{"error":"missing api key"}')
    assert "a key is what it wants" in what


def test_no_connection_and_an_answer():
    st, what = PR.classify(None, "", "", "URLError: <urlopen error blocked>")
    assert st == "failed" and "unreachable" in what
    assert PR.classify(200, "application/json", "{}") == ("fresh", "reachable: it answered")


def test_the_rows_fit_the_session_log_and_never_carry_the_key(monkeypatch):
    monkeypatch.setattr(PR, "probe", lambda url: ("failed", "HTTP 403 from a bot wall"))
    monkeypatch.setenv("FANTASYPROS_API_KEY", "secret-value-123")
    rows = PR.run()
    assert all({"name", "source", "status", "detail", "age_h"} <= set(r) for r in rows)
    assert "secret-value-123" not in repr(rows) and rows[-1]["detail"] == "set"
    assert "| NO |" in PR.markdown(rows)

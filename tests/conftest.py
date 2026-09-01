"""Test-suite guards.

DRAFTKIT_LEAGUE leaking in from an interactive shell silently re-points every
Config.load() at a non-default league and fails unrelated tests (happened
three times during the Keefamania build). The suite always runs against the
default league unless a test opts in with monkeypatch.setenv.
"""
import pytest


@pytest.fixture(autouse=True)
def _isolate_league_env(monkeypatch):
    monkeypatch.delenv("DRAFTKIT_LEAGUE", raising=False)

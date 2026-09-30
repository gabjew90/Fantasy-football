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


@pytest.fixture(autouse=True)
def _no_schedule_read(monkeypatch):
    """The player tool and the reports read byes from the real schedule
    (games.csv, refetched when stale): the suite never does. A test that needs
    byes builds them (fantasy.environment.bye_weeks on a small frame)."""
    from fantasy import environment as E
    monkeypatch.setattr(E, "load_byes", lambda season, manifest=None: {})


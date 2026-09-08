"""The Vegas feed is the whole season, not this week.

Regression for the defect found 2026-09-07: the endpoint returns every posted
game sorted ascending, and the old loop assigned per event with no date
filter, so each team held its LAST game of the season. Buffalo's "this week"
implied total was their 2027-01-10 line. Nothing errored.
"""

from datetime import datetime, timedelta, timezone

import pytest

from manager import vegas


class FakeStore:
    def __init__(self):
        self.d = {}

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


def _event(home, away, when, total=44.0, spread_home=-3.0):
    return {
        "home_team": home, "away_team": away,
        "commence_time": when.strftime(vegas.ISO),
        "bookmakers": [{"markets": [
            {"key": "totals", "outcomes": [{"point": total}]},
            {"key": "spreads", "outcomes": [{"name": home, "point": spread_home},
                                            {"name": away, "point": -spread_home}]},
        ]}],
    }


WEEK1 = datetime(2026, 9, 13, 17, 0, tzinfo=timezone.utc)
WEEK18 = datetime(2027, 1, 10, 18, 0, tzinfo=timezone.utc)

# the same two teams in week 1 and again in week 18, with different lines
FEED = [
    _event("Buffalo Bills", "Houston Texans", WEEK1, total=48.0, spread_home=-6.0),
    _event("Buffalo Bills", "New York Jets", WEEK18, total=36.0, spread_home=-1.0),
]


@pytest.fixture(autouse=True)
def _key(monkeypatch):
    monkeypatch.setenv("ODDS_API_KEY", "test-key")


def _patch_feed(monkeypatch, seen):
    class R:
        @staticmethod
        def raise_for_status():
            return None

        @staticmethod
        def json():
            return FEED

    def fake_get(url, timeout=20):
        seen.append(url)
        return R()

    monkeypatch.setattr(vegas.requests, "get", fake_get)


def test_window_keeps_only_the_current_week(monkeypatch):
    seen = []
    _patch_feed(monkeypatch, seen)
    lo, hi = WEEK1 - timedelta(hours=1), WEEK1 + timedelta(hours=6)
    out, note = vegas.implied_totals(FakeStore(), window=(lo, hi))
    assert note is None
    # week 1: total 48, home spread -6 -> BUF 27.0, not the week-18 line
    assert out["BUF"] == 27.0
    assert out["HOU"] == 21.0
    assert "NYJ" not in out, "a January game leaked into this week's totals"


def test_the_request_is_bounded_server_side_too(monkeypatch):
    seen = []
    _patch_feed(monkeypatch, seen)
    lo, hi = WEEK1 - timedelta(hours=1), WEEK1 + timedelta(hours=6)
    vegas.implied_totals(FakeStore(), window=(lo, hi))
    assert "commenceTimeFrom=" in seen[0] and "commenceTimeTo=" in seen[0]


def test_without_a_window_the_old_last_game_wins_behaviour_is_visible(monkeypatch):
    """Documents why the window is not optional in the callers."""
    seen = []
    _patch_feed(monkeypatch, seen)
    out, _ = vegas.implied_totals(FakeStore())
    assert out["BUF"] == 18.5, "unbounded call still collapses to the last game"


def test_cache_is_keyed_by_window_so_a_wider_pull_is_never_reused(monkeypatch):
    seen = []
    _patch_feed(monkeypatch, seen)
    store = FakeStore()
    w1 = (WEEK1 - timedelta(hours=1), WEEK1 + timedelta(hours=6))
    w18 = (WEEK18 - timedelta(hours=1), WEEK18 + timedelta(hours=6))
    vegas.implied_totals(store, window=w1)
    vegas.implied_totals(store, window=w18)
    assert len(seen) == 2, "second window served from the first window's cache"
    assert vegas.implied_totals(store, window=w1)[0]["BUF"] == 27.0
    assert len(seen) == 2, "same window should have hit the cache"


def test_no_key_is_a_data_missing_line_not_a_crash(monkeypatch):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    out, note = vegas.implied_totals(FakeStore(), window=(WEEK1, WEEK1))
    assert out == {} and "DATA MISSING" in note


def test_week_window_without_a_schedule_degrades_to_a_seven_day_span():
    lo, hi = vegas.week_window({"week": 1})
    assert timedelta(days=6) < (hi - lo) <= timedelta(days=8)


def test_no_key_falls_back_to_a_committed_snapshot(monkeypatch, tmp_path):
    """The API key stays local; CI reads lines it could never fetch itself."""
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    vegas.write_snapshot("2026", 3, {"BUF": 27.0, "HOU": 21.0})
    out, note = vegas.implied_totals(FakeStore(), season="2026", week=3)
    assert out == {"BUF": 27.0, "HOU": 21.0}
    assert "snapshot" in note and "DATA MISSING" not in note


def test_the_snapshot_note_always_states_its_age(monkeypatch, tmp_path):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    p = vegas.write_snapshot("2026", 3, {"BUF": 27.0})
    import json as _j
    blob = _j.loads(p.read_text(encoding="utf-8"))
    blob["ts"] = blob["ts"] - 3600 * 30          # 30 hours ago
    p.write_text(_j.dumps(blob), encoding="utf-8")
    _, note = vegas.implied_totals(FakeStore(), season="2026", week=3)
    assert "30h old" in note, note


def test_no_key_and_no_snapshot_is_still_data_missing(monkeypatch, tmp_path):
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    out, note = vegas.implied_totals(FakeStore(), season="2026", week=9)
    assert out == {} and "DATA MISSING" in note


def test_a_live_key_ignores_the_snapshot(monkeypatch, tmp_path):
    """A stale committed file must never shadow a fetch that can succeed."""
    monkeypatch.chdir(tmp_path)
    vegas.write_snapshot("2026", 1, {"BUF": 1.0})
    seen = []
    _patch_feed(monkeypatch, seen)
    lo, hi = WEEK1 - timedelta(hours=1), WEEK1 + timedelta(hours=6)
    out, _ = vegas.implied_totals(FakeStore(), window=(lo, hi), season="2026", week=1)
    assert out["BUF"] == 27.0, "snapshot shadowed a live fetch"


def test_both_team_code_styles_resolve(monkeypatch, tmp_path):
    """Roster rows carry Sleeper codes (SF, NO, GB); NAMES emits draftkit
    codes (SFO, NOS, GBP). For eight teams the lookup silently missed and a
    quarter of the league never got a Vegas tilt."""
    monkeypatch.delenv("ODDS_API_KEY", raising=False)
    monkeypatch.chdir(tmp_path)
    vegas.write_snapshot("2026", 1, {"SFO": 26.5, "NOS": 21.2, "PIT": 23.0})
    out, _ = vegas.implied_totals(FakeStore(), season="2026", week=1)
    for canon, alias in (("SFO", "SF"), ("NOS", "NO")):
        assert out[canon] == out[alias], f"{alias} cannot find {canon}"
    assert out["PIT"] == 23.0, "an unaliased team was disturbed"


def test_every_mismatched_team_is_covered():
    sleeper_only = {"GB", "JAX", "KC", "LV", "NE", "NO", "SF", "TB"}
    assert set(vegas.ALIASES.values()) == sleeper_only
    assert set(vegas.ALIASES) <= set(vegas.NAMES.values())


def test_aliasing_a_live_fetch_too(monkeypatch):
    seen = []
    _patch_feed(monkeypatch, seen)
    lo, hi = WEEK1 - timedelta(hours=1), WEEK1 + timedelta(hours=6)
    out, _ = vegas.implied_totals(FakeStore(), window=(lo, hi))
    assert out["BUF"] == 27.0 and out["HOU"] == 21.0

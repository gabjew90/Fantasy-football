"""core/: scoring, fetch-and-cache, the manifest, and the Sleeper-gsis crosswalk."""

from __future__ import annotations

import datetime as dt
import json
import os
import time
from pathlib import Path

import polars as pl
import pytest

from core import fetch as F
from core import ids, scoring
from core.manifest import Manifest

HALF = {"rec": 0.5, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "rush_td": 6.0,
        "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0, "fum_lost": -2.0, "pass_td_40p": 2.0}


# ------------------------------------------------------------------ scoring

def test_league_scoring_reads_expected_scoring_and_refuses_a_missing_block():
    assert scoring.league_scoring({"expected": {"scoring": {"rec": 1}}}) == {"rec": 1.0}
    assert scoring.league_scoring({"scoring": {"rec": 0.5}, "expected": {"scoring": {"rec": 1}}}) == {"rec": 0.5}
    with pytest.raises(scoring.ScoringMissing):
        scoring.league_scoring({"expected": {}})
    assert scoring.league_scoring({}, required=False) == {}


def test_score_counts_only_scored_keys_and_skips_unprojected():
    line = {"rec": 6, "rec_yd": 70, "rec_td": 1, "adp_ppr": 12.0, "rush_yd": None}
    assert scoring.score(line, HALF) == pytest.approx(0.5 * 6 + 7.0 + 6.0)
    assert scoring.score(None, HALF) == 0.0


def test_the_legacy_names_are_the_one_function():
    from draftkit import consensus as dc
    from manager import consensus as mc
    assert mc._score is scoring.score
    assert dc.score is scoring.score


def test_nflverse_weights_translate_keys_and_name_what_they_drop():
    w = scoring.nflverse_weights(HALF, base=scoring.NFLVERSE_BASE)
    assert w["receptions"] == 0.5
    assert w["rushing_fumbles_lost"] == w["sack_fumbles_lost"] == -2.0
    assert w["special_teams_tds"] == 6.0, "a key the league omits keeps its base weight"
    assert scoring.unmodelled_keys(HALF) == ["pass_td_40p"]


def test_fantasy_points_expr_scores_a_weekly_frame():
    df = pl.DataFrame([{"receptions": 5, "receiving_yards": 60, "receiving_tds": 1}])
    w = scoring.nflverse_weights({"rec": 1.0, "rec_yd": 0.1, "rec_td": 6.0})
    assert df.with_columns(scoring.fantasy_points_expr(w))["fpts"][0] == pytest.approx(17.0)


# ------------------------------------------------------------ fetch + manifest

def _age(p: Path, seconds: float):
    t = time.time() - seconds
    os.utime(p, (t, t))


def _writer(content: str, calls: list):
    def dl(url, path, timeout):
        calls.append(url)
        Path(path).write_text(content, encoding="utf-8")
    return dl


def test_fetch_reuses_a_young_copy_and_refreshes_an_old_one(tmp_path):
    calls, m = [], Manifest("t")
    f = tmp_path / "x.csv"
    F.fetch("u", f, 3600, manifest=m, downloader=_writer("v1", calls))
    assert calls == ["u"] and m.get("x.csv")["status"] == "fresh"
    F.fetch("u", f, 3600, manifest=m, downloader=_writer("v2", calls))
    assert calls == ["u"] and f.read_text(encoding="utf-8") == "v1" and m.get("x.csv")["status"] == "cached"
    _age(f, 7200)
    F.fetch("u", f, 3600, manifest=m, downloader=_writer("v2", calls))
    assert f.read_text(encoding="utf-8") == "v2" and m.get("x.csv")["status"] == "fresh"


def test_a_failed_refresh_keeps_the_old_copy_and_marks_it_stale(tmp_path):
    def boom(url, path, timeout):
        Path(path).write_text("partial", encoding="utf-8")
        raise OSError("network")
    m = Manifest("t")
    f = tmp_path / "inj.csv"
    f.write_text("old", encoding="utf-8")
    _age(f, 99999)
    F.fetch("u", f, 3600, name="injuries", manifest=m, downloader=boom)
    assert f.read_text(encoding="utf-8") == "old"
    assert not (tmp_path / "inj.csv.part").exists()
    e = m.get("injuries")
    assert e["status"] == "stale" and e["age_h"] > 20
    assert e["detail"] == "refresh failed: OSError"
    assert "STALE" in m.summary_line()
    with pytest.raises(OSError):
        F.fetch("u", tmp_path / "missing.csv", 3600, manifest=m, downloader=boom)
    assert m.get("missing.csv")["status"] == "failed"


def test_nflverse_paths_and_ages_follow_the_season(tmp_path, monkeypatch):
    seen = {}

    def fake_fetch(url, dest, max_age_s, **kw):
        seen[Path(dest).name] = (url, max_age_s)
        return Path(dest)
    monkeypatch.setattr(F, "fetch", fake_fetch)
    monkeypatch.setattr(F, "current_season", lambda today=None: 2026)
    F.nflverse("pbp", 2026, cache_dir=tmp_path)
    F.nflverse("pbp", 2024, cache_dir=tmp_path)
    F.nflverse("players", cache_dir=tmp_path)
    assert seen["play_by_play_2026.csv.gz"][1] == F.CURRENT_SEASON_MAX_AGE_S
    assert seen["play_by_play_2024.csv.gz"][1] == F.HISTORIC_MAX_AGE_S
    assert seen["players.csv"][1] == F.REFERENCE_MAX_AGE_S
    assert seen["play_by_play_2026.csv.gz"][0].endswith("/pbp/play_by_play_2026.csv.gz")
    with pytest.raises(ValueError):
        F.nflverse("injuries", cache_dir=tmp_path)
    with pytest.raises(KeyError):
        F.nflverse("routes", 2026, cache_dir=tmp_path)


def test_the_current_season_turns_over_in_march():
    assert F.current_season(dt.date(2027, 2, 10)) == 2026
    assert F.current_season(dt.date(2027, 3, 1)) == 2027


def test_the_manifest_knows_whether_a_roster_was_read_after_the_request(tmp_path):
    start = dt.datetime(2026, 9, 24, 12, 0, tzinfo=dt.timezone.utc)
    m = Manifest("waiver", started_at=start)
    m.record("roster", source="sleeper", status="fresh", fetched_at=start + dt.timedelta(minutes=1))
    m.record("rules", source="yaml", status="cached", fetched_at=start - dt.timedelta(days=2))
    m.record("lines", source="sleeper", status="failed")
    assert m.read_after_start("roster") and not m.read_after_start("rules")
    assert not m.read_after_start("lines") and not m.read_after_start("nothing")
    out = json.loads(m.write(tmp_path / "m.json").read_text(encoding="utf-8"))
    assert out["purpose"] == "waiver" and len(out["entries"]) == 3
    with pytest.raises(ValueError):
        m.record("x", source="y", status="ok")


# ------------------------------------------------------------------- ids

def test_sleeper_gsis_prefers_the_map_fills_gaps_and_drops_shared_ids():
    idm = pl.DataFrame({"sleeper_id": ["1", "2", "3", "10", "11", None],
                        "gsis_id": ["00-0000001", "00-0000002", "00-0000009",
                                    "00-0000010", "00-0000010", "00-0000004"]})
    sp = {
        "1": {"gsis_id": "00-0000001"},                 # agrees
        "2": {"gsis_id": " 00-0000099"},                # disagrees: the map wins, listed
        "5": {"gsis_id": " 00-0000005 "},               # only Sleeper has him: filled, spaces stripped
        "6": {"gsis_id": "00-0000009"},                 # a stale entry claiming 3's gsis: 6 dropped, 3 kept
        "7": {"gsis_id": None}, "DEF": "not a dict",
        "8": {"gsis_id": "00-0000077"}, "9": {"gsis_id": "00-0000077"},   # Sleeper-only twins: both dropped
    }
    out, rep = ids.sleeper_gsis(idm, sp)
    assert out == {"1": "00-0000001", "2": "00-0000002", "3": "00-0000009", "5": "00-0000005"}
    assert rep["from_map"] == 5 and rep["from_sleeper"] == 4
    assert rep["conflicts"] == [("2", "00-0000002", "00-0000099")]
    assert sorted(rep["dropped_shared_gsis"]) == [("00-0000009", ["6"]),
                                                  ("00-0000010", ["10", "11"]),   # the map claims it twice
                                                  ("00-0000077", ["8", "9"])]
    assert ids.invert(out)["00-0000005"] == "5"


def test_an_empty_download_is_a_failed_refresh_not_a_new_copy(tmp_path):
    m = Manifest("t")
    f = tmp_path / "sleeper_lines.json"
    f.write_text('{"ok": 1}', encoding="utf-8")
    _age(f, 99999)
    F.fetch("u", f, 600, name="lines", manifest=m, downloader=_writer("", []))
    assert f.read_text(encoding="utf-8") == '{"ok": 1}'
    assert m.get("lines")["status"] == "stale"


class _Resp:
    """A urlopen response whose body is `body` and whose Content-Length says `length`."""
    def __init__(self, body: bytes, length):
        self._b, self.headers = body, ({} if length is None else {"Content-Length": str(length)})

    def read(self, n=-1):
        out, self._b = self._b[:n], self._b[n:]
        return out

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def test_a_truncated_download_is_a_failed_refresh_not_a_new_copy(tmp_path, monkeypatch):
    """2026-10-09: a connection closed mid-body left a 751 KB roster file for 3.4 MB, and it
    replaced the good copy. A body shorter than its Content-Length now fails the refresh."""
    m = Manifest("t")
    monkeypatch.setattr(F, "RETRY_WAITS", (0, 0))
    f = tmp_path / "roster.csv"
    f.write_text("a,b\n1,2\n3,4\n", encoding="utf-8")
    _age(f, 99999)
    monkeypatch.setattr(F.urllib.request, "urlopen", lambda req, timeout: _Resp(b"a,b\n1,", 12))
    F.fetch("https://x/roster.csv", f, 600, name="roster", manifest=m)
    assert f.read_text(encoding="utf-8") == "a,b\n1,2\n3,4\n"
    assert m.get("roster")["status"] == "stale" and "TruncatedDownload" in m.get("roster")["detail"]
    # a full body, or one with no length header, is a new copy as before
    monkeypatch.setattr(F.urllib.request, "urlopen", lambda req, timeout: _Resp(b"a,b\n9,9\n", 8))
    F.fetch("https://x/roster.csv", f, 600, name="roster", manifest=m)
    assert f.read_text(encoding="utf-8") == "a,b\n9,9\n"
    _age(f, 99999)
    monkeypatch.setattr(F.urllib.request, "urlopen", lambda req, timeout: _Resp(b"a,b\n7,7\n", None))
    F.fetch("https://x/roster.csv", f, 600, name="roster", manifest=m)
    assert f.read_text(encoding="utf-8") == "a,b\n7,7\n"


def test_a_naive_start_time_is_taken_as_utc():
    m = Manifest("t", started_at=dt.datetime(2026, 9, 24, 12, 0))
    m.record("roster", source="s", status="fresh", fetched_at=dt.datetime(2026, 9, 24, 12, 5))
    assert m.read_after_start("roster")


# ---------------------------------------------------------------- retries (DECISIONS #235)

def _http(code):
    import urllib.error
    return urllib.error.HTTPError("https://x/pbp.csv.gz", code, "err", {}, None)


def test_a_transient_failure_is_tried_again_and_then_succeeds(tmp_path, monkeypatch):
    """2026-10-10: one HTTP 502 from nflverse stopped a calculator card; a rerun worked."""
    monkeypatch.setattr(F, "RETRY_WAITS", (0, 0))
    calls = []

    def urlopen(req, timeout):
        calls.append(1)
        if len(calls) < 3:
            raise _http(502)
        return _Resp(b"a,b\n1,2\n", 8)
    monkeypatch.setattr(F.urllib.request, "urlopen", urlopen)
    m = Manifest("t")
    F.fetch("https://x/pbp.csv.gz", tmp_path / "pbp.csv.gz", 600, name="pbp", manifest=m)
    assert len(calls) == 3 and m.get("pbp")["status"] == "fresh"
    assert (tmp_path / "pbp.csv.gz").read_bytes() == b"a,b\n1,2\n"


def test_a_client_error_is_not_retried_and_no_copy_raises_fetch_error(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "RETRY_WAITS", (0, 0))
    calls = []

    def urlopen(req, timeout):
        calls.append(1)
        raise _http(404)
    monkeypatch.setattr(F.urllib.request, "urlopen", urlopen)
    m = Manifest("t")
    with pytest.raises(F.FetchError) as ei:
        F.fetch("https://x/pbp.csv.gz", tmp_path / "pbp.csv.gz", 600, name="nflverse pbp 2026", manifest=m)
    assert len(calls) == 1, "a 404 is not tried again"
    assert isinstance(ei.value, OSError) and ei.value.cause.code == 404
    assert str(ei.value).startswith("nflverse pbp 2026: download failed (HTTPError")
    assert m.get("nflverse pbp 2026")["status"] == "failed"


def test_retries_run_out_then_an_old_copy_is_used_or_the_error_is_named(tmp_path, monkeypatch):
    monkeypatch.setattr(F, "RETRY_WAITS", (0, 0))
    calls = []

    def urlopen(req, timeout):
        calls.append(1)
        raise ConnectionResetError("reset by peer")
    monkeypatch.setattr(F.urllib.request, "urlopen", urlopen)
    with pytest.raises(F.FetchError, match="ConnectionResetError"):
        F.fetch("https://x/a.csv", tmp_path / "a.csv", 600, name="a")
    assert len(calls) == len(F.RETRY_WAITS) + 1
    old = tmp_path / "b.csv"
    old.write_text("old", encoding="utf-8")
    _age(old, 99999)
    m = Manifest("t")
    F.fetch("https://x/b.csv", old, 600, name="b", manifest=m)
    assert old.read_text(encoding="utf-8") == "old" and m.get("b")["status"] == "stale"


def test_which_failures_count_as_transient():
    import http.client
    assert F._transient(_http(502)) and F._transient(_http(503)) and F._transient(_http(429))
    assert not F._transient(_http(404)) and not F._transient(_http(403))
    import ssl
    import urllib.error
    assert F._transient(ConnectionResetError()) and F._transient(urllib.error.URLError(ConnectionRefusedError()))
    assert F._transient(http.client.IncompleteRead(b"x", 10)) and F._transient(F.TruncatedDownload("cut"))
    assert not F._transient(ValueError("a bug, not the network"))
    # a hung server (timeout) or a failed TLS check fails at once: retrying costs time, never helps
    assert not F._transient(TimeoutError()) and not F._transient(urllib.error.URLError(TimeoutError()))
    assert not F._transient(urllib.error.URLError(ssl.SSLCertVerificationError("bad cert")))


def test_a_bug_in_a_downloader_is_not_called_a_failed_download(tmp_path):
    def broken(url, path, timeout):
        raise TypeError("a bug")
    with pytest.raises(TypeError, match="a bug"):
        F.fetch("u", tmp_path / "x.csv", 600, downloader=broken)


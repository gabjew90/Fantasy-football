"""backtest.dl caches a download only when it arrived whole.

On 2026-10-09 urlretrieve raised ContentTooShortError on pbp_2026.csv.gz and left the partial
file at the cache path; dl treats an existing file as cached, so the next run would have read a
truncated gzip. dl now downloads to a .tmp beside the destination and moves it into place only
on success."""
from __future__ import annotations

import sys
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine" / "scripts"
sys.path.insert(0, str(ENGINE))


@pytest.fixture
def bt(tmp_path, monkeypatch):
    import backtest as BT
    monkeypatch.setattr(BT, "CACHE", tmp_path)
    return BT


def _headers(length=None):
    h = Message()
    if length is not None:
        h["Content-Length"] = str(length)
    return h


def test_a_short_download_leaves_nothing_at_the_destination(bt, tmp_path, monkeypatch):
    def short(url, filename):
        Path(filename).write_bytes(b"x" * 10)
        raise urllib.error.ContentTooShortError("retrieval incomplete: got only 10 out of 100 bytes", None)

    monkeypatch.setattr(urllib.request, "urlretrieve", short)
    with pytest.raises(urllib.error.ContentTooShortError):
        bt.dl("https://example.invalid/pbp_2026.csv.gz", "pbp_2026.csv.gz")
    assert list(tmp_path.iterdir()) == []


def test_a_body_shorter_than_content_length_is_refused(bt, tmp_path, monkeypatch):
    def short(url, filename):
        Path(filename).write_bytes(b"x" * 10)
        return filename, _headers(100)

    monkeypatch.setattr(urllib.request, "urlretrieve", short)
    with pytest.raises(urllib.error.ContentTooShortError):
        bt.dl("https://example.invalid/pbp_2026.csv.gz", "pbp_2026.csv.gz")
    assert list(tmp_path.iterdir()) == []


def test_a_whole_download_is_cached_and_reused(bt, tmp_path, monkeypatch):
    calls = []

    def whole(url, filename):
        calls.append(url)
        Path(filename).write_bytes(b"x" * 100)
        return filename, _headers(100)

    monkeypatch.setattr(urllib.request, "urlretrieve", whole)
    dest = bt.dl("https://example.invalid/pbp_2026.csv.gz", "pbp_2026.csv.gz")
    assert dest == tmp_path / "pbp_2026.csv.gz" and dest.read_bytes() == b"x" * 100
    assert [p.name for p in tmp_path.iterdir()] == ["pbp_2026.csv.gz"]
    bt.dl("https://example.invalid/pbp_2026.csv.gz", "pbp_2026.csv.gz")
    assert len(calls) == 1


def test_no_content_length_is_accepted(bt, tmp_path, monkeypatch):
    def whole(url, filename):
        Path(filename).write_bytes(b"x" * 7)
        return filename, _headers()

    monkeypatch.setattr(urllib.request, "urlretrieve", whole)
    assert bt.dl("https://example.invalid/games.csv", "games.csv").read_bytes() == b"x" * 7


def test_td_backtest_fetch_shares_the_cache_and_the_guard(bt, tmp_path, monkeypatch):
    """td_backtest.fetch (also absence_tune's and td_alloc_backtest's) writes the same cache, so
    a partial there would poison backtest.dl too; it goes through dl."""
    import td_backtest as TB

    def short(url, filename):
        Path(filename).write_bytes(b"x" * 10)
        raise urllib.error.ContentTooShortError("retrieval incomplete", None)

    monkeypatch.setattr(urllib.request, "urlretrieve", short)
    with pytest.raises(urllib.error.ContentTooShortError):
        TB.fetch("https://example.invalid/pbp_2026.csv.gz", "pbp_2026.csv.gz")
    assert list(tmp_path.iterdir()) == []

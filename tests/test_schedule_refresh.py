"""The nflverse schedule is refreshed daily in season, not cached forever
(review 2026-09-16): December flex moves kickoffs, and every gate check's
lock time is computed from this file."""

from __future__ import annotations

import os
import time

import polars as pl

from draftkit import seasondata


class Cfg:
    def __init__(self, root):
        self.root = root

    def path(self, kind):
        p = self.root / kind
        p.mkdir(exist_ok=True)
        return p


def _raw(gametime):
    return pl.DataFrame({"game_type": ["REG"], "week": [15], "away_team": ["DET"], "home_team": ["GB"],
                         "gameday": ["2026-12-13"], "weekday": ["Sunday"], "gametime": [gametime]})


def test_a_fresh_cache_is_used_and_a_stale_one_is_refreshed(tmp_path):
    cfg = Cfg(tmp_path)
    calls = []

    def loader(seasons):
        calls.append(seasons)
        return _raw("13:00" if len(calls) == 1 else "20:20")   # flexed to Sunday night

    first = seasondata.load_schedule(cfg, 2026, loader=loader)
    assert first["gametime"][0] == "13:00" and calls == [[2026]]
    assert seasondata.load_schedule(cfg, 2026, loader=loader)["gametime"][0] == "13:00", "fresh cache, no refetch"
    cache = tmp_path / "processed" / "schedule_2026.parquet"
    old = time.time() - 2 * 24 * 3600
    os.utime(cache, (old, old))
    third = seasondata.load_schedule(cfg, 2026, loader=loader)
    assert third["gametime"][0] == "20:20" and len(calls) == 2, "a day-old cache is refetched"
    assert pl.read_parquet(cache)["gametime"][0] == "20:20", "and the cache carries the new kickoff"


def test_a_failed_refresh_keeps_the_last_good_copy(tmp_path):
    cfg = Cfg(tmp_path)
    seasondata.load_schedule(cfg, 2026, loader=lambda s: _raw("13:00"))
    cache = tmp_path / "processed" / "schedule_2026.parquet"
    old = time.time() - 2 * 24 * 3600
    os.utime(cache, (old, old))

    def boom(seasons):
        raise RuntimeError("nflverse down")
    out = seasondata.load_schedule(cfg, 2026, loader=boom)
    assert out["gametime"][0] == "13:00"


def test_max_age_none_means_the_old_permanent_cache(tmp_path):
    cfg = Cfg(tmp_path)
    seasondata.load_schedule(cfg, 2026, loader=lambda s: _raw("13:00"))
    cache = tmp_path / "processed" / "schedule_2026.parquet"
    old = time.time() - 30 * 24 * 3600
    os.utime(cache, (old, old))
    out = seasondata.load_schedule(cfg, 2026, max_age=None, loader=lambda s: (_ for _ in ()).throw(AssertionError("must not fetch")))
    assert out["gametime"][0] == "13:00"

"""ESPN as a second free stat-line source (plan A1): the parser keeps only
the season projection row, maps stat ids to the scoring keys, and the fetch
degrades the way the Sleeper one does."""

from __future__ import annotations

import json
import os
import time

import polars as pl
import pytest

from draftkit import espn as E
from draftkit import external as X

HALF = {"rec": 0.5, "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0,
        "rush_yd": 0.1, "rec_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0, "fum_lost": -2.0}


def _player(pid, name, pos_id, rows):
    return {"id": pid, "player": {"id": pid, "fullName": name, "defaultPositionId": pos_id, "proTeamId": 8,
                                  "stats": rows}}


def _row(season, source, split, stats):
    return {"seasonId": season, "statSourceId": source, "statSplitTypeId": split, "stats": stats}


def _filler(n):
    return [_player(1000 + i, f"Filler {i}", 2, [_row(2026, 1, 0, {"24": 1})]) for i in range(n)]


def test_parse_players_uses_only_the_season_projection_row_and_maps_stat_ids():
    players = [
        _player(1, "Josh Allen", 1, [_row(2025, 0, 0, {"3": 4000}),            # last season actuals
                                     _row(2026, 1, 1, {"3": 250}),             # weekly split
                                     _row(2026, 1, 0, {"3": 3900, "4": 30, "20": 10, "24": 500, "25": 8, "999": 5, "72": None})]),
        _player(2, "Some Kicker", 5, [_row(2026, 1, 0, {"3": 1})]),          # not a skill position
        _player(3, "No Line", 2, [_row(2026, 1, 0, {"999": 1})]),            # nothing scorable
        _player(4, "Bijan Robinson", 2, [_row(2026, 1, 0, {"24": 1400, "25": 12, "53": 60, "42": 500, "43": 3})]),
    ]
    out = E.parse_players(players, 2026)
    assert [p["name"] for p in out] == ["Josh Allen", "Bijan Robinson"]
    assert out[0]["line"] == {"pass_yd": 3900.0, "pass_td": 30.0, "pass_int": 10.0, "rush_yd": 500.0, "rush_td": 8.0}
    assert out[1]["pos"] == "RB" and out[1]["espn_id"] == "4" and out[1]["line"]["rec"] == 60.0


def test_fetch_sends_the_filter_header_caches_and_degrades_to_stale_cache(tmp_path, capsys):
    calls = []
    good = {"players": _filler(250)}

    def getter(url, headers):
        calls.append((url, headers))
        return good

    rows = E.fetch_projections(2026, tmp_path, getter=getter, ttl=3600)
    assert len(rows) == 250 and len(calls) == 1
    assert "2026" in calls[0][0] and json.loads(calls[0][1]["X-Fantasy-Filter"])["players"]["limit"] == 1500
    E.fetch_projections(2026, tmp_path, getter=getter, ttl=3600)
    assert len(calls) == 1                                            # served from cache within ttl

    def failing(url, headers):
        raise RuntimeError("503")
    cache = tmp_path / "espn_proj_2026.json"
    stale = time.time() - 10 ** 6
    os.utime(cache, (stale, stale))                                   # make the cache stale
    assert len(E.fetch_projections(2026, tmp_path, getter=failing, ttl=3600)) == 250
    assert "using cache" in capsys.readouterr().err
    cache.unlink()
    with pytest.raises(E.EspnUnavailable):
        E.fetch_projections(2026, tmp_path, getter=failing, ttl=3600)

    def thin(url, headers):
        return {"players": good["players"][:5]}                       # the header was ignored
    with pytest.raises(E.EspnUnavailable):
        E.fetch_projections(2027, tmp_path, getter=thin, ttl=3600)


class _Index:
    def __init__(self, table):
        self.table = table

    def match(self, name, pos, team):
        return self.table.get((name, pos))


def test_from_espn_joins_by_espn_id_then_name_and_returns_unmatched(tmp_path):
    players = [_player(11, "Bijan Robinson", 2, [_row(2026, 1, 0, {"24": 1400, "25": 12})]),
               _player(22, "Name Only", 3, [_row(2026, 1, 0, {"53": 50, "42": 600})]),
               _player(33, "Nobody", 3, [_row(2026, 1, 0, {"53": 1})])] + _filler(300)
    id_map = pl.DataFrame({"espn_id": [11, 11, 44], "sleeper_id": ["4866", "4866", "1"],
                           "fantasypros_id": [None, None, None]},
                          schema={"espn_id": pl.Int64, "sleeper_id": pl.Utf8, "fantasypros_id": pl.Utf8})
    df, unmatched = X.from_espn(2026, HALF, tmp_path, id_map, _Index({("Name Only", "WR"): "777"}),
                                getter=lambda url, headers: {"players": players}, ttl=3600)
    got = {r["sleeper_id"]: r for r in df.iter_rows(named=True)}
    assert got["4866"]["source"] == "espn_projections" and abs(got["4866"]["pts17"] - (140 + 72)) < 1e-9
    assert got["777"]["name"] == "Name Only" and got["777"]["team"] is None
    assert "Nobody (WR)" in unmatched and any(u.startswith("Filler") for u in unmatched)


def test_load_external_reports_espn_unavailable_and_continues(tmp_path, monkeypatch):
    class Cfg:
        root = tmp_path

        def __init__(self):
            self._d = {"season": 2026, "expected": {"scoring": HALF},
                       "projections": {"external": {"sources": ["espn", "sleeper"]}}}

        def get(self, k, d=None):
            return self._d.get(k, d)

        def __getitem__(self, k):
            return self._d[k]

        def path(self, kind):
            return tmp_path

    def boom(*a, **k):
        raise E.EspnUnavailable("down")

    import draftkit.ids
    monkeypatch.setattr(draftkit.ids, "load_id_map", lambda p: pl.DataFrame())
    monkeypatch.setattr(X, "from_espn", boom)
    monkeypatch.setattr(X, "from_sleeper", lambda *a, **k: pl.DataFrame(
        {"sleeper_id": ["1"], "name": ["A"], "pos": ["RB"], "team": ["X"], "pts17": [100.0],
         "source": ["sleeper_rotowire"], "as_of": ["2026-09-01"], "line": ["{}"]}, schema=X.SCHEMA))
    out, rep = X.load_external(Cfg(), index=None)
    assert out.height == 1 and rep["sources"][0] == {"source": "espn", "rows": 0, "error": "down"}
    assert rep["combine"] == "first" and out["n_sources"].to_list() == [1]

"""Item 1 of the projection overhaul: consensus stat lines as a parallel source.

The endpoint is undocumented, so the contract that matters is ours: exact
join on Sleeper id, league scoring applied key-for-key, the 17-game line
scaled onto the board's basis, `gp` recorded but never used to scale, ADP
picked by the league's reception scoring, and a loud failure (not an empty
frame) when nothing can be read.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from draftkit import consensus as C

HALF = {"rec": 0.5, "pass_yd": 0.04, "pass_td": 4.0, "pass_int": -1.0,
        "rush_yd": 0.1, "rec_yd": 0.1, "rush_td": 6.0, "rec_td": 6.0, "fum_lost": -2.0,
        "pass_td_40p": 2.0}

ROWS = [
    {"player_id": "4984", "team": "BUF", "updated_at": 1788249037361,
     "player": {"position": "QB", "first_name": "Josh", "last_name": "Allen"},
     "stats": {"gp": 18.0, "pass_yd": 3650.0, "pass_td": 28.0, "pass_int": 10.0,
               "rush_yd": 535.0, "rush_td": 10.0, "fum_lost": 3.0,
               "adp_half_ppr": 20.7, "adp_ppr": 21.0, "adp_std": 19.0, "pts_half_ppr": 361.5}},
    {"player_id": "9999", "team": None, "updated_at": 1788249037361,
     "player": {"position": "QB"},
     "stats": {"gp": 18.0, "adp_half_ppr": 647.4}},          # ADP placeholder only
]


def test_score_rows_applies_league_scoring_and_the_games_convention():
    df = C.score_rows(ROWS, HALF, games=16.0, line_games=17.0)
    assert df.height == 1, "an ADP-only row is unprojected, not zero"
    r = df.row(0, named=True)
    raw = 3650 * 0.04 + 28 * 4 - 10 + 535 * 0.1 + 10 * 6 - 3 * 2   # 353.5
    assert abs(r["proj_consensus_pts"] - raw * 16 / 17) < 0.01
    assert r["consensus_gp"] == 18.0, "gp is recorded for audit"
    assert r["adp_sleeper"] == 20.7, "half-PPR league reads adp_half_ppr"
    assert r["sleeper_id"] == "4984" and r["consensus_pos"] == "QB"


def test_adp_key_follows_reception_scoring():
    assert C.adp_key({"rec": 1.0}) == "adp_ppr"
    assert C.adp_key({"rec": 0.5}) == "adp_half_ppr"
    assert C.adp_key({"rec": 0.0}) == "adp_std"
    assert C.adp_key({}) == "adp_std"


def test_fetch_caches_and_uses_a_stale_cache_only_when_the_fetch_fails(tmp_path):
    calls = []

    def ok(url):
        calls.append(url)
        return ROWS

    rows = C.fetch_position(2026, "QB", tmp_path, getter=ok, ttl=3600)
    assert rows == ROWS and len(calls) == 1
    assert (tmp_path / "sleeper_proj_2026_QB.json").exists()
    # fresh cache: no second call
    C.fetch_position(2026, "QB", tmp_path, getter=ok, ttl=3600)
    assert len(calls) == 1

    def boom(url):
        raise RuntimeError("down")

    # expired cache + failing fetch -> stale cache is returned (with a note)
    rows2 = C.fetch_position(2026, "QB", tmp_path, getter=boom, ttl=0)
    assert rows2 == ROWS
    # no cache at all + failing fetch -> loud
    with pytest.raises(C.ConsensusUnavailable):
        C.fetch_position(2026, "RB", tmp_path, getter=boom, ttl=0)


def test_load_consensus_reports_and_joins_by_sleeper_id(tmp_path):
    class FakeCfg(dict):
        def path(self, kind):
            return tmp_path

    cfg = FakeCfg({"season": 2026,
                   "projections": {"expected_games": 16.0, "consensus": {"line_games": 17.0}},
                   "expected": {"scoring": HALF}})

    def getter(url):
        pos = url.rsplit("=", 1)[-1]
        return ROWS if pos == "QB" else []

    df, rep = C.load_consensus(cfg, getter=getter)
    assert df.height == 1 and df["sleeper_id"][0] == "4984"
    assert rep["rows"] == {"QB": 1, "RB": 0, "WR": 0, "TE": 0}
    assert rep["adp_key"] == "adp_half_ppr" and rep["line_games"] == 17.0
    assert rep["updated_max"] == 1788249037361
    # cached files were written per position
    assert json.loads((tmp_path / "sleeper_proj_2026_RB.json").read_text()) == []

"""Yahoo leagues reach the trade framework through a scraped snapshot.

Yahoo's API is approval-gated, so manager.context refuses the platform and
Keefamania had no way to use manager.marginal at all -- every trade priced
for it was priced in a throwaway script. This adapter resolves a scraped
`POS|Name|Owner` file to sleeper_ids so price/slot_moves/explain work on it
unchanged.
"""

from __future__ import annotations

import time

from manager import marginal, yahoo


class Cfg(dict):
    def __init__(self, *a, league_name=None, **kw):
        super().__init__(*a, **kw)
        self.league_name = league_name


PLAYERS = {
    "1": {"full_name": "Jahmyr Gibbs", "position": "RB"},
    "2": {"full_name": "Drake London", "position": "WR"},
    "3": {"full_name": "Sam LaPorta", "position": "TE"},
    "4": {"full_name": "Jayden Daniels", "position": "QB"},
    "5": {"full_name": "Travis Etienne", "position": "RB"},
    "9": {"full_name": "Tyler Loop", "position": "K"},
}
CON = {"1": {"mean": 310.8}, "2": {"mean": 206.9}, "3": {"mean": 151.4},
       "4": {"mean": 309.5}, "5": {"mean": 201.8}}

CFG = Cfg({"expected": {"roster": ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T",
                                   "K", "DEF", "BN", "BN", "IR"]}},
          league_name="testleague")


def _write(tmp_path, monkeypatch, body):
    d = tmp_path / "yahoo"
    d.mkdir()
    (d / "testleague.txt").write_text(body, encoding="utf-8")
    monkeypatch.setattr(yahoo, "ROSTER_DIR", d)
    return d / "testleague.txt"


BODY = """RB|Jahmyr Gibbs|Me
WR|Drake London|Me
TE|Sam LaPorta|Me
K|Tyler Loop|Me
QB|Jayden Daniels|Them
RB|Travis Etienne|Them
"""


def test_the_roster_shape_comes_from_the_league_file():
    """W/R/T is a flex; K and DEF are dropped because no projection source in
    this repo covers them, and their slots would price against zeros."""
    _, shape, _ = yahoo.load(CFG, PLAYERS, CON)
    assert shape == {"slots": {"QB": 1, "WR": 2, "RB": 2, "TE": 1}, "flex": 1}


def test_rows_come_back_in_the_shape_marginal_expects(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, BODY)
    rosters, shape, _ = yahoo.load(CFG, PLAYERS, CON)
    assert set(rosters) == {"Me", "Them"}
    row = next(r for r in rosters["Me"] if r["name"] == "Jahmyr Gibbs")
    assert row["sleeper_id"] == "1" and row["pos"] == "RB"
    assert row["weekly"] == 310.8, "the consensus value must reach the optimiser"
    # and the framework works on it untouched
    assert marginal.lineup_points(rosters["Me"], shape) > 0


def test_a_kicker_is_kept_out_of_the_rows_but_his_team_survives(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, BODY)
    rosters, _, _ = yahoo.load(CFG, PLAYERS, CON)
    assert "Tyler Loop" not in [r["name"] for r in rosters["Me"]]
    assert "Me" in rosters


def test_an_unresolvable_name_is_reported_not_dropped_quietly(tmp_path, monkeypatch):
    """A roster missing two players prices every trade for that team wrong,
    so the caller has to be able to see it."""
    _write(tmp_path, monkeypatch, BODY + "WR|Nobody At All|Them\n")
    _, _, notes = yahoo.load(CFG, PLAYERS, CON)
    bad = [n for n in notes if n.startswith("⚠") and "did not resolve" in n]
    assert bad and "Nobody At All" in bad[0]


def test_a_stale_snapshot_is_flagged(tmp_path, monkeypatch):
    """A roster that moved makes every number wrong, and the file cannot
    tell you it moved -- only that it is old."""
    p = _write(tmp_path, monkeypatch, BODY)
    old = time.time() - (yahoo.STALE_DAYS + 1) * 86400
    import os
    os.utime(p, (old, old))
    _, _, notes = yahoo.load(CFG, PLAYERS, CON)
    assert any(n.startswith("⚠") and "days old" in n for n in notes)


def test_a_fresh_snapshot_says_when_it_was_taken(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, BODY)
    _, _, notes = yahoo.load(CFG, PLAYERS, CON)
    assert any(n.startswith("yahoo rosters scraped") for n in notes)
    assert not any(n.startswith("⚠") for n in notes)


def test_a_missing_snapshot_degrades_loudly(tmp_path, monkeypatch):
    monkeypatch.setattr(yahoo, "ROSTER_DIR", tmp_path / "nothing-here")
    rosters, shape, notes = yahoo.load(CFG, PLAYERS, CON)
    assert rosters == {}
    assert any(n.startswith("DATA MISSING") for n in notes)
    assert shape["slots"], "the shape is still derivable without a snapshot"


def test_a_player_with_no_consensus_scores_zero_not_a_crash(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, BODY)
    rosters, _, _ = yahoo.load(CFG, PLAYERS, {})
    assert all(r["weekly"] == 0.0 for r in rosters["Me"])

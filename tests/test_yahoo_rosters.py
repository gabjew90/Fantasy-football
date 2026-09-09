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


# ------------------------------- 2026-09-09: the crosswalk, and cand[0]
#
# NOTE ON WHAT THE CROSSWALK IS NOT FOR. draftkit.ids.normalize_name already
# strips punctuation and generational suffixes, so "Harold Fannin Jr." on the
# Yahoo page and "Harold Fannin" in the Sleeper index ALREADY match. Suffixes
# were the obvious guess and they are not the gap. What is left is genuinely
# different renderings of the same person, which is a smaller population than
# it first looks -- so these tests use an explicit alias rather than pretending
# a suffix case proves anything.


def test_a_duplicate_name_is_reported_not_guessed(tmp_path, monkeypatch):
    """cand[0] picked whichever Mike Williams the index listed first and
    priced that whole team around him. Short by one is visible in the notes;
    wrong by one is not visible anywhere."""
    _write(tmp_path, monkeypatch, "WR|Mike Williams|Me\n")
    players = {"9a": {"full_name": "Mike Williams", "position": "WR", "team": "NYJ"},
               "9b": {"full_name": "Mike Williams", "position": "WR", "team": "PIT"}}
    out, _, notes = yahoo.load(CFG, players)
    assert out.get("Me", []) == [], "an ambiguous name was silently resolved"
    assert any("match more than one player" in n for n in notes), notes


def test_the_crosswalk_rescues_a_name_the_sleeper_index_renders_differently(
        tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, "WR|Marquise Brown|Me\n")
    players = {"55": {"full_name": "Hollywood Brown", "position": "WR", "team": "KC"}}
    out, _, _ = yahoo.load(CFG, players)
    assert out.get("Me", []) == [], "precondition: the bare index should miss"

    cw = {"by_name": {"marquise brown": [("55", "WR", "KC")]}, "by_yahoo": {}}
    out2, _, _ = yahoo.load(CFG, players, crosswalk=cw)
    assert [r["sleeper_id"] for r in out2["Me"]] == ["55"]


def test_the_crosswalk_never_overrides_a_match_the_index_already_made(
        tmp_path, monkeypatch):
    """A fallback for a MISS, not a competing opinion -- the Sleeper index is
    the identity of record everywhere else in the repo."""
    _write(tmp_path, monkeypatch, "RB|Jahmyr Gibbs|Me\n")
    cw = {"by_name": {"jahmyr gibbs": [("999", "RB", "DET")]}, "by_yahoo": {}}
    out, _, _ = yahoo.load(CFG, PLAYERS, crosswalk=cw, con=CON)
    assert [r["sleeper_id"] for r in out["Me"]] == ["1"]


def test_a_crosswalk_hit_at_the_wrong_position_is_not_used(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, "TE|Marquise Brown|Me\n")
    players = {"55": {"full_name": "Hollywood Brown", "position": "WR"}}
    cw = {"by_name": {"marquise brown": [("55", "WR", "KC")]}, "by_yahoo": {}}
    out, _, notes = yahoo.load(CFG, players, crosswalk=cw)
    assert out.get("Me", []) == []
    assert any("did not resolve" in n for n in notes), notes


def test_an_ambiguous_crosswalk_hit_is_also_reported_not_guessed(
        tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, "WR|Mike Williams|Me\n")
    cw = {"by_name": {"mike williams": [("9a", "WR", "NYJ"), ("9b", "WR", "PIT")]},
          "by_yahoo": {}}
    out, _, notes = yahoo.load(CFG, {}, crosswalk=cw)
    assert out.get("Me", []) == []
    assert any("match more than one player" in n for n in notes), notes


def test_no_crosswalk_behaves_exactly_as_before(tmp_path, monkeypatch):
    _write(tmp_path, monkeypatch, BODY)
    a, _, na = yahoo.load(CFG, PLAYERS, con=CON)
    b, _, nb = yahoo.load(CFG, PLAYERS, con=CON, crosswalk={"by_name": {},
                                                            "by_yahoo": {}})
    assert a == b and na == nb

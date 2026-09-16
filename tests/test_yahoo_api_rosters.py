"""Keefamania rosters from the Yahoo Fantasy API (access provisioned 2026-09-16).

The API replaces the browser scrape as the primary source. It adds Yahoo's
player id (an exact join through the DynastyProcess id map), each player's
lineup slot, and Yahoo's own injury designation -- which is what decides
IR-slot eligibility in a Yahoo league. The snapshot file stays as the
fallback and is rewritten on every good read.
"""

from __future__ import annotations

import pytest

from manager import yahoo, yahoo_api


class Cfg(dict):
    def __init__(self, *a, league_name=None, league_id=None, **kw):
        super().__init__(*a, **kw)
        self.league_name = league_name
        self.league_id = league_id


CFG = Cfg({"expected": {"roster": ["QB", "WR", "WR", "RB", "RB", "TE", "W/R/T",
                                   "K", "DEF", "BN", "BN", "IR", "IR"]}},
          league_name="apileague", league_id="49649")

PLAYERS = {
    "10": {"full_name": "A.J. Brown", "position": "WR"},
    "11": {"full_name": "Jahmyr Gibbs", "position": "RB"},
    "12": {"full_name": "Brock Bowers", "position": "TE"},
    "13": {"full_name": "Mike Williams", "position": "WR"},
    "14": {"full_name": "Mike Williams", "position": "WR"},
    "15": {"full_name": "Travis Hunter", "position": "DB", "fantasy_positions": ["DB", "WR"]},
}
CON = {"10": {"mean": 162.0}, "11": {"mean": 305.0}, "12": {"mean": 187.0}, "14": {"mean": 90.0}}


def _player(pid, full, pos, slot, status=None, note=None):
    meta = [{"player_key": f"470.p.{pid}"}, {"player_id": str(pid)},
            {"name": {"full": full}}, {"display_position": pos}]
    if status:
        meta.append({"status": status, "status_full": status})
    if note:
        meta.append({"injury_note": note})
    return {"player": [meta, {"selected_position": [{"coverage_type": "week"}, {"position": slot}]}]}


def _team(tid, name, players):
    ps = {str(i): p for i, p in enumerate(players)}
    ps["count"] = len(players)
    return {"team": [[{"team_key": f"470.l.49649.t.{tid}"}, {"team_id": str(tid)}, {"name": name}, []],
                     {"roster": {"coverage_type": "week", "week": "2", "0": {"players": ps}}}]}


def _body():
    teams = {
        "0": _team(3, "Air Raid Gabriel", [
            _player(501, "A.J. Brown", "WR", "IR", status="IR", note="Ankle"),
            _player(502, "Jahmyr Gibbs", "RB", "RB"),
            _player(503, "Tyler Loop", "K", "K"),
        ]),
        "1": _team(7, "WHISTLE/KEIBLER (STAN)", [
            _player(504, "Brock Bowers", "TE", "TE", status="IR-R"),
            _player(505, "Mike Williams", "WR", "BN"),
            _player(506, "Travis Hunter", "WR,CB", "BN", status="Q"),
        ]),
        "2": {"team": [[{"team_id": "9"}, {"name": "Empty Team"}], {"roster": {"0": {"players": []}}}]},
        "count": 3,
    }
    return {"fantasy_content": {"league": [{"league_key": "470.l.49649"}, {"teams": teams}]}}


@pytest.fixture
def api(monkeypatch, tmp_path):
    monkeypatch.setattr(yahoo, "ROSTER_DIR", tmp_path / "yahoo")
    calls = []

    def get(path, params=None):
        calls.append(path)
        return _body()
    return get, calls, tmp_path


def test_api_rows_carry_owner_slot_status_and_yahoo_id(api):
    get, calls, _ = api
    rosters, shape, notes = yahoo.load(CFG, PLAYERS, CON, source="api", get=get)
    assert calls == ["league/nfl.l.49649/teams/roster"]
    assert set(rosters) == {"Air Raid Gabriel", "WHISTLE/KEIBLER (STAN)", "Empty Team"}
    me = {r["name"]: r for r in rosters["Air Raid Gabriel"]}
    assert set(me) == {"A.J. Brown", "Jahmyr Gibbs"}, "K is skipped, as in the scrape path"
    assert me["A.J. Brown"] == {"sleeper_id": "10", "pos": "WR", "name": "A.J. Brown", "weekly": 162.0,
                                "yahoo_id": "501", "slot": "IR", "yahoo_status": "IR", "injury_note": "Ankle"}
    assert "slot" in me["Jahmyr Gibbs"] and "yahoo_status" not in me["Jahmyr Gibbs"]
    assert shape == {"slots": {"QB": 1, "WR": 2, "RB": 2, "TE": 1}, "flex": 1}
    assert any("from the API" in n for n in notes), notes


def test_the_yahoo_id_join_resolves_what_the_name_cannot(api):
    """Two Mike Williamses: by name the row is ambiguous and dropped; the id
    map names the right one."""
    get, _, _ = api
    rosters, _, notes = yahoo.load(CFG, PLAYERS, CON, source="api", get=get)
    assert not any(r["name"] == "Mike Williams" for r in rosters["WHISTLE/KEIBLER (STAN)"])
    assert any("more than one player" in n for n in notes)

    rosters, _, notes = yahoo.load(CFG, PLAYERS, CON, source="api", get=get, id_map={"505": "14"})
    mw = [r for r in rosters["WHISTLE/KEIBLER (STAN)"] if r["name"] == "Mike Williams"]
    assert [r["sleeper_id"] for r in mw] == ["14"]
    assert any("1 joined on Yahoo id" in n for n in notes), notes


def test_a_mapped_id_whose_position_does_not_fit_falls_back_to_the_name(api):
    get, _, _ = api
    rosters, _, _ = yahoo.load(CFG, PLAYERS, CON, source="api", get=get, id_map={"502": "12"})
    gibbs = [r for r in rosters["Air Raid Gabriel"] if r["name"] == "Jahmyr Gibbs"]
    assert gibbs[0]["sleeper_id"] == "11", "a TE id was offered for an RB row and must not be trusted"


def test_a_multi_position_player_lands_on_his_skill_position(api):
    """Travis Hunter is 'WR,CB' on Yahoo and DB with a WR fantasy position on
    Sleeper: he resolves as a WR through the id map."""
    get, _, _ = api
    rosters, _, _ = yahoo.load(CFG, PLAYERS, CON, source="api", get=get, id_map={"506": "15"})
    th = [r for r in rosters["WHISTLE/KEIBLER (STAN)"] if r["name"] == "Travis Hunter"]
    assert th and th[0]["pos"] == "WR" and th[0]["sleeper_id"] == "15"


def test_a_good_api_read_rewrites_the_snapshot_file(api):
    get, _, tmp = api
    yahoo.load(CFG, PLAYERS, CON, source="api", get=get)
    text = (tmp / "yahoo" / "apileague.txt").read_text(encoding="utf-8")
    assert "WR|A.J. Brown|Air Raid Gabriel" in text and "K|Tyler Loop|Air Raid Gabriel" in text


def test_auto_falls_back_to_the_snapshot_and_says_why(api):
    get, _, tmp = api
    yahoo.load(CFG, PLAYERS, CON, source="api", get=get)          # writes a snapshot

    def refused(path, params=None):
        raise yahoo_api.YahooScopeError("Yahoo 403: the token is valid but the app has no Fantasy Sports scope")

    rosters, _, notes = yahoo.load(CFG, PLAYERS, CON, source="auto", get=refused)
    assert "Air Raid Gabriel" in rosters
    assert any("Yahoo API unavailable (YahooScopeError" in n for n in notes), notes
    assert any("scraped" in n for n in notes), notes
    assert "yahoo_status" not in rosters["Air Raid Gabriel"][0], "snapshot rows carry no status"


def test_api_only_reports_missing_data_instead_of_a_stale_file(api):
    def boom(path, params=None):
        raise RuntimeError("network down")
    rosters, _, notes = yahoo.load(CFG, PLAYERS, CON, source="api", get=boom)
    assert rosters == {} and notes[0].startswith("DATA MISSING: Yahoo API rosters (RuntimeError")


def test_an_unknown_source_is_an_error():
    with pytest.raises(ValueError, match="source"):
        yahoo.load(CFG, PLAYERS, CON, source="yahoo")


def test_injury_overlay_maps_yahoo_codes_to_the_sleeper_vocabulary(api):
    get, _, _ = api
    rosters, _, _ = yahoo.load(CFG, PLAYERS, CON, source="api", get=get, id_map={"506": "15"})
    assert yahoo.injury_overlay(rosters) == {"10": "IR", "12": "IR", "15": "Questionable"}

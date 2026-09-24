"""YahooSource: the seven league-side reads build_context makes, answered
from Yahoo's API in Sleeper's shapes (Keefamania, access live 2026-09-16)."""

from __future__ import annotations

import pytest

from draftkit.sleeper import IdentityError
from manager import yahoo_context as yc


class Cfg(dict):
    def __init__(self, *a, league_name="keefamania", league_id="49649", **kw):
        super().__init__(*a, **kw)
        self.league_name, self.league_id = league_name, league_id

    def path(self, *_):
        return "data/raw"


CFG = Cfg({"me": {"username": "Air Raid Gabriel", "user_id": None},
           "expected": {"scoring": {"rec": 0.5, "pass_yd": 0.04}}})

PLAYERS = {
    "10": {"full_name": "A.J. Brown", "position": "WR"},
    "11": {"full_name": "Jahmyr Gibbs", "position": "RB"},
    "12": {"full_name": "Tyler Loop", "position": "K"},
    "13": {"full_name": "Jayden Daniels", "position": "QB"},
    "14": {"full_name": "Chris Olave", "position": "WR"},
    "15": {"full_name": "Mike Williams", "position": "WR"},
    "16": {"full_name": "Mike Williams", "position": "WR"},
    "TB": {"full_name": "Tampa Bay Buccaneers", "position": "DEF", "first_name": "Tampa Bay", "last_name": "Buccaneers"},
    "JAX": {"full_name": "Jacksonville Jaguars", "position": "DEF"},
}


def _p(pid, full, pos, slot, status=None, team="Det"):
    meta = [{"player_key": f"470.p.{pid}"}, {"player_id": str(pid)}, {"name": {"full": full}},
            {"editorial_team_abbr": team}, {"display_position": pos}]
    if status:
        meta.append({"status": status, "status_full": status})
    return {"player": [meta, {"selected_position": [{"coverage_type": "week"}, {"position": slot}]}]}


def _team(tid, name, players, prio=None):
    ps = {str(i): p for i, p in enumerate(players)}
    ps["count"] = len(players)
    meta = [{"team_key": f"470.l.49649.t.{tid}"}, {"team_id": str(tid)}, {"name": name}, []]
    if prio is not None:
        meta.append({"waiver_priority": prio})
    return {"team": [meta, {"roster": {"coverage_type": "week", "week": "2", "0": {"players": ps}}}]}


ROSTERS = {"fantasy_content": {"league": [{"league_key": "470.l.49649"}, {"teams": {
    "0": _team(3, "Air Raid Gabriel", [
        _p(501, "Jayden Daniels", "QB", "QB", team="Was"),
        _p(502, "Jahmyr Gibbs", "RB", "RB"),
        _p(503, "A.J. Brown", "WR", "IR", status="IR", team="NE"),
        _p(504, "Tyler Loop", "K", "K", team="Bal"),
        _p(505, "Buccaneers", "DEF", "DEF", team="TB"),
    ], prio=4),
    "1": _team(7, "WHISTLE/KEIBLER (STAN)", [
        _p(506, "Chris Olave", "WR", "WR", team="NO"),
        _p(507, "Mike Williams", "WR", "BN"),
        _p(508, "Jaguars", "DEF", "BN", team="Jac"),
    ], prio=1),
    "count": 2}}]}}

SETTINGS = {"fantasy_content": {"league": [
    {"league_key": "470.l.49649", "name": "Keefamania", "num_teams": 10, "current_week": 2, "season": "2026"},
    {"settings": [{"waiver_type": "R", "uses_faab": "0", "playoff_start_week": "15", "num_playoff_teams": "6",
                   "max_weekly_adds": "5", "trade_end_date": "2026-11-28",
                   "roster_positions": [
                       {"roster_position": {"position": "QB", "count": 1}},
                       {"roster_position": {"position": "RB", "count": 2}},
                       {"roster_position": {"position": "WR", "count": 2}},
                       {"roster_position": {"position": "TE", "count": 1}},
                       {"roster_position": {"position": "W/R/T", "count": 1}},
                       {"roster_position": {"position": "K", "count": 1}},
                       {"roster_position": {"position": "DEF", "count": 1}},
                       {"roster_position": {"position": "BN", "count": 6}},
                       {"roster_position": {"position": "IR", "count": 2}}]}]}]}}

STANDINGS = {"fantasy_content": {"league": [{}, {"standings": [{"teams": {
    "0": {"team": [[{"team_id": "3"}, {"name": "Air Raid Gabriel"}],
                   {"team_points": {"total": "153.76"}},
                   {"team_standings": {"rank": "1", "outcome_totals": {"wins": "1", "losses": 0, "ties": 0}}}]},
    "1": {"team": [[{"team_id": "7"}, {"name": "WHISTLE/KEIBLER (STAN)"}],
                   {"team_points": {"total": "99.1"}},
                   {"team_standings": {"rank": "9", "outcome_totals": {"wins": 0, "losses": "1", "ties": 0}}}]},
    "count": 2}}]}]}}

SCOREBOARD = {"fantasy_content": {"league": [{}, {"scoreboard": {"0": {"matchups": {
    "0": {"matchup": {"week": "2", "status": "midevent", "0": {"teams": {
        "0": {"team": [[{"team_id": "3"}], {"team_points": {"total": "12.5"}}, {"team_projected_points": {"total": "106.1"}}]},
        "1": {"team": [[{"team_id": "7"}], {"team_points": {"total": "0.00"}}, {"team_projected_points": {"total": "98.0"}}]},
        "count": 2}}}},
    "count": 1}}}}]}}

TRANSACTIONS = {"fantasy_content": {"league": [{}, {"transactions": {
    "0": {"transaction": [[{"transaction_key": "470.l.49649.tr.60"}, {"transaction_id": "60"}, {"type": "add/drop"},
                           {"status": "successful"}, {"timestamp": "1789594318"}],
                          {"players": {
                              "0": {"player": [[{"player_id": "506"}, {"name": {"full": "Chris Olave"}}, {"editorial_team_abbr": "NO"}, {"display_position": "WR"}],
                                               {"transaction_data": [{"type": "add", "source_type": "freeagents", "destination_team_key": "470.l.49649.t.7"}]}]},
                              "1": {"player": [[{"player_id": "507"}, {"name": {"full": "Mike Williams"}}, {"editorial_team_abbr": "Ari"}, {"display_position": "WR"}],
                                               {"transaction_data": {"type": "drop", "source_type": "team", "source_team_key": "470.l.49649.t.7"}}]},
                              "count": 2}}]},
    "1": {"transaction": [[{"transaction_id": "61"}, {"type": "trade"}, {"status": "successful"}, {"timestamp": "1789600000"}],
                          {"players": {
                              "0": {"player": [[{"player_id": "502"}, {"name": {"full": "Jahmyr Gibbs"}}, {"editorial_team_abbr": "Det"}, {"display_position": "RB"}],
                                               {"transaction_data": [{"type": "trade", "source_team_key": "470.l.49649.t.3", "destination_team_key": "470.l.49649.t.7"}]}]},
                              "1": {"player": [[{"player_id": "506"}, {"name": {"full": "Chris Olave"}}, {"editorial_team_abbr": "NO"}, {"display_position": "WR"}],
                                               {"transaction_data": [{"type": "trade", "source_team_key": "470.l.49649.t.7", "destination_team_key": "470.l.49649.t.3"}]}]},
                              "count": 2}}]},
    "2": {"transaction": [[{"transaction_id": "62"}, {"type": "add"}, {"status": "successful"}, {"timestamp": "1789601000"}],
                          {"players": {"0": {"player": [[{"player_id": "504"}, {"name": {"full": "Tyler Loop"}}, {"editorial_team_abbr": "Bal"}, {"display_position": "K"}],
                                                        {"transaction_data": [{"type": "add", "source_type": "waivers", "destination_team_key": "470.l.49649.t.3"}]}]},
                                       "count": 1}}]},
    "count": 3}}]}}

TEAMS = {"fantasy_content": {"league": [{}, {"teams": {
    "0": {"team": [[{"team_id": "3"}, {"name": "Air Raid Gabriel"}, {"waiver_priority": 4}]]},
    "1": {"team": [[{"team_id": "7"}, {"name": "WHISTLE/KEIBLER (STAN)"}, {"waiver_priority": 1}]]},
    "count": 2}}]}}


def _get(path, params=None):
    for frag, body in (("/teams/roster", ROSTERS), ("/settings", SETTINGS), ("/standings", STANDINGS),
                       ("/scoreboard", SCOREBOARD), ("/transactions", TRANSACTIONS), ("/teams", TEAMS)):
        if frag in path:
            return body
    raise AssertionError(f"unexpected path {path}")


@pytest.fixture
def src():
    return yc.YahooSource(CFG, get=_get, players=PLAYERS, id_map={"507": "15"})


def test_league_is_sleeper_shaped(src):
    lg = src.league()
    assert lg["name"] == "Keefamania"
    assert lg["scoring_settings"] == {"rec": 0.5, "pass_yd": 0.04}, "no stat_modifiers in this fixture: the yaml block stands"
    assert any("stat_modifiers unavailable" in n for n in src.notes)
    assert lg["roster_positions"] == ["QB", "RB", "RB", "WR", "WR", "TE", "W/R/T", "K", "DEF"] + ["BN"] * 6 + ["IR"] * 2
    s = lg["settings"]
    assert s["waiver_budget"] == 0 and s["playoff_week_start"] == 15 and s["playoff_teams"] == 6
    assert s["reserve_slots"] == 2 and s["max_weekly_adds"] == 5 and s["trade_deadline"] == "2026-11-28"
    assert s["reserve_allow"] == ["IR", "PUP", "NFI", "COV"]


def test_scoring_comes_from_yahoos_stat_modifiers_in_sleeper_keys():
    """The yaml block is offense only, so K and DEF scored zero on the first
    Keefamania dry run. Yahoo's stat_modifiers carry the whole table; ids are
    the stable Yahoo ids (measured on the live league 2026-09-16)."""
    settings = {"stat_modifiers": {"stats": [
        {"stat": {"stat_id": "4", "value": "0.04"}}, {"stat": {"stat_id": "11", "value": "0.5"}},
        {"stat": {"stat_id": "16", "value": "2"}}, {"stat": {"stat_id": "23", "value": "5"}},
        {"stat": {"stat_id": "29", "value": "1"}}, {"stat": {"stat_id": "32", "value": "1"}},
        {"stat": {"stat_id": "50", "value": "10"}}, {"stat": {"stat_id": "56", "value": "-4"}},
        {"stat": {"stat_id": "60", "value": "2"}}, {"stat": {"stat_id": "999", "value": "7"}}]}}
    s = yc.scoring_from_modifiers(settings)
    assert s == {"pass_yd": 0.04, "rec": 0.5, "pass_2pt": 2.0, "rush_2pt": 2.0, "rec_2pt": 2.0,
                 "fgm_50_59": 5.0, "fgm_60p": 5.0, "xpm": 1.0, "sack": 1.0,
                 "pts_allow_0": 10.0, "pts_allow_35p": -4.0, "pass_td_40p": 2.0}


def test_a_yaml_scoring_disagreement_is_reported_and_the_api_wins():
    body = {"fantasy_content": {"league": [
        {"name": "K", "num_teams": 10, "current_week": 2, "season": "2026"},
        {"settings": [{"uses_faab": "1", "roster_positions": [],
                       "stat_modifiers": {"stats": [{"stat": {"stat_id": "11", "value": "1.0"}},
                                                    {"stat": {"stat_id": "32", "value": "1"}}]}}]}]}}
    cfg = Cfg({"me": {}, "expected": {"scoring": {"rec": 0.5, "pass_yd": 0.04}}})
    s = yc.YahooSource(cfg, get=lambda p, params=None: body, players={}, id_map={})
    lg = s.league()
    assert lg["scoring_settings"] == {"rec": 1.0, "sack": 1.0, "pass_yd": 0.04}, "api value, yaml fills the gap"
    assert lg["settings"]["waiver_budget"] == 100
    assert any("differs from the league yaml: rec yaml 0.5 vs api 1.0" in n for n in s.notes), s.notes


def test_reserve_statuses_include_ir_itself():
    """The old rule was the two flags OR ("Out",), which left IR out and
    reported an IR-designated stash as an invalid roster."""
    from draftkit.briefs import reserve_statuses
    assert reserve_statuses({}) == ("IR", "PUP", "COV", "NA")
    assert reserve_statuses({"reserve_allow_out": 1, "reserve_allow_doubtful": 1}) == ("IR", "PUP", "COV", "NA", "Out", "Doubtful")
    assert reserve_statuses({"reserve_allow": ["IR", "PUP", "NFI", "COV"]}) == ("IR", "PUP", "NFI", "COV")


def test_the_shape_module_reads_the_yahoo_roster_list():
    from draftkit.shape import starting_slots
    shape = starting_slots(["QB", "RB", "RB", "WR", "WR", "TE", "W/R/T", "K", "DEF", "BN", "IR"])
    assert shape.slots == {"QB": 1, "RB": 2, "WR": 2, "TE": 1, "K": 1, "DEF": 1} and shape.flex == 1


def test_rosters_carry_players_starters_reserve_and_standings(src):
    rs = {r["roster_id"]: r for r in src.rosters()}
    me = rs[3]
    assert me["owner_id"] == "470.l.49649.t.3"
    assert me["players"] == ["13", "11", "10", "12", "TB"], "QB, RB, IR WR, K, and the DEF by team code"
    assert me["starters"] == ["13", "11", "12", "TB"], "roster-position order, no bench, no IR"
    assert me["reserve"] == ["10"]
    assert me["settings"] == {"wins": 1, "losses": 0, "ties": 0, "fpts": 153.76, "rank": 1,
                              "waiver_budget_used": 0, "waiver_position": 4}
    them = rs[7]
    assert "15" in them["players"], "the id map picked the right Mike Williams"
    assert "JAX" in them["players"], "Jac -> JAX"
    assert them["settings"]["waiver_position"] == 1 and them["settings"]["losses"] == 1


def test_an_unresolvable_player_is_reported_not_dropped_silently():
    s = yc.YahooSource(CFG, get=_get, players=PLAYERS, id_map={})   # two Mike Williamses, no map
    s.rosters()
    assert any("did not resolve" in n and "Mike Williams" in n for n in s.notes), s.notes


def test_users_and_identity(src):
    users = src.users()
    assert users == {"470.l.49649.t.3": "Air Raid Gabriel", "470.l.49649.t.7": "WHISTLE/KEIBLER (STAN)"}
    roster, info = src.resolve_me(users, src.rosters())
    assert roster["roster_id"] == 3
    assert info == {"source": "yahoo team name", "user_id": "470.l.49649.t.3",
                    "display": "Air Raid Gabriel", "roster_id": 3}


def test_identity_by_team_key_and_the_failure_modes():
    cfg = Cfg({"me": {"username": "nobody", "user_id": "470.l.49649.t.7"}, "expected": {}})
    s = yc.YahooSource(cfg, get=_get, players=PLAYERS, id_map={})
    roster, info = s.resolve_me(s.users(), s.rosters())
    assert roster["roster_id"] == 7 and info["source"] == "me.user_id (team_key)"
    bad = yc.YahooSource(Cfg({"me": {"username": "Nobody"}, "expected": {}}), get=_get, players=PLAYERS, id_map={})
    with pytest.raises(IdentityError, match="matched 0 of 2"):
        bad.resolve_me(bad.users(), bad.rosters())


def test_injury_overlay_speaks_only_where_yahoo_flags(src):
    assert src.injury_overlay() == {"10": "IR"}


def test_matchups_pair_teams_like_sleeper(src):
    m = src.matchups(2)
    assert m == [{"matchup_id": 1, "roster_id": 3, "points": 12.5, "projected": 106.1},
                 {"matchup_id": 1, "roster_id": 7, "points": 0.0, "projected": 98.0}]


def test_transactions_are_sleeper_shaped(src):
    tx = {t["transaction_id"]: t for t in src.transactions(2)}
    fa = tx["60"]
    assert fa["type"] == "free_agent" and fa["status"] == "complete"
    assert fa["adds"] == {"14": 7} and fa["drops"] == {"15": 7} and fa["roster_ids"] == [7]
    assert fa["created"] == 1789594318000
    tr = tx["61"]
    assert tr["type"] == "trade" and tr["adds"] == {"11": 7, "14": 3} and tr["drops"] == {"11": 3, "14": 7}
    assert tr["roster_ids"] == [3, 7]
    assert tx["62"]["type"] == "waiver" and tx["62"]["adds"] == {"12": 3}


def test_the_manager_context_dispatches_on_platform(monkeypatch):
    from manager import context
    seen = {}

    def fake_build(cfg, week=None, source=None, write_state=True):
        seen["platform"] = getattr(source, "platform", "sleeper")
        raise RuntimeError("stop here")

    class FakeCfg(Cfg):
        pass
    monkeypatch.setattr(context, "build_context", fake_build)
    monkeypatch.setattr(context.Config, "load", staticmethod(lambda league=None: Cfg({"platform": "yahoo", "me": {}})))
    monkeypatch.setattr(yc.YahooSource, "__init__", lambda self, cfg: setattr(self, "cfg", cfg))
    with pytest.raises(RuntimeError, match="stop here"):
        context.league_context()
    assert seen["platform"] == "yahoo"
    monkeypatch.setattr(context.Config, "load", staticmethod(lambda league=None: Cfg({"platform": "espn"})))
    with pytest.raises(RuntimeError, match="sleeper and yahoo"):
        context.league_context()

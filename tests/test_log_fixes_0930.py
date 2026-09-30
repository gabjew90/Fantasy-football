"""The 2026-09-30 05:50 session log's fixes (DECISIONS #129): season-ending
injuries, the cut rule's volume test, the league keep list, roster room (open
spots and IR), byes, the consensus split flag and scenario teammate names."""

from __future__ import annotations

import types

import pandas as pd
import pytest

from fantasy import ask as A
from fantasy import environment as E
from fantasy import league as LG
from fantasy import scenario as SC
from fantasy import waiver as WV


# ------------------------------------------------------------ season-ending

@pytest.mark.parametrize("status, part, weeks", [
    ("IR", "Knee - ACL", WV.SEASON_OUT),          # Achane: out now, torn ACL
    ("IR", "Knee - ACL + MCL", WV.SEASON_OUT),
    ("Out", "Achilles", WV.SEASON_OUT),
    ("IR", "Knee - PCL", 4),                        # not an ACL
    ("PUP", "Knee - ACL", 4),                       # recovering from an old tear
    ("Questionable", "Knee - ACL", 0),
    ("IR", None, 4),
    ("", "Knee - ACL", 0),
])
def test_an_acl_or_achilles_on_a_player_out_now_ends_his_season(status, part, weeks):
    assert WV.miss_weeks(status, part) == weeks


def test_a_season_ending_add_scores_nothing_for_the_rest_of_the_season():
    rates = {"qb": 20.0, "rb1": 15.0, "rb2": 14.0, "bench": 3.0}
    pos = {"qb": "QB", "rb1": "RB", "rb2": "RB", "bench": "RB", "add": "RB"}
    team = {k: k.upper() for k in pos}
    slots = {"QB": 1, "RB": 2, "WR": 0, "TE": 0}
    base, _ = WV.season_gain(rates, pos, team, slots, [], [4, 5, 6], {})
    tot, _ = WV.season_gain(dict(rates, add=18.0), pos, team, slots, [], [4, 5, 6], {}, drop="bench",
                            out_until={"add": 4 + WV.miss_weeks("IR", "Knee - ACL")})
    assert tot == base


# ------------------------------------------------------------ the cut rule

def _ev(pos, snap, share_series, metric="tgt_share", changed=None):
    vals = [v for v in share_series if v is not None]
    return {"pos": pos, "mean": {"snap_pct": snap, metric: sum(vals) / len(vals)},
            "series": {metric: share_series}, "role_change": changed or {}}


def test_snaps_without_the_volume_are_flagged_not_protected():
    worthy = _ev("WR", 0.83, [0.24, 0.16, 0.09])                    # the log's case: share falling
    ok, why = WV.cut_role(worthy)
    assert not ok and "falling (24 -> 16 -> 9%)" in why
    decoy = _ev("WR", 0.80, [0.08, 0.10, 0.09])
    ok, why = WV.cut_role(decoy)
    assert not ok and "snaps without the volume" in why
    starter = _ev("WR", 0.85, [0.22, 0.24, 0.21])
    assert WV.cut_role(starter) == (True, None)
    back = _ev("RB", 0.65, [0.20, 0.22, 0.18], metric="carry_share")
    assert not WV.cut_role(back)[0]
    assert WV.cut_role({"pos": "QB", "mean": {"snap_pct": 0.93}}) == (True, None), "a QB has no share test"
    assert WV.cut_role({"pos": "WR", "mean": {"snap_pct": 0.40}}) == (False, None), "no flag under 60% snaps"
    assert WV.protected_cuts(["w", "s"], {"w": worthy, "s": starter}) == {"s"}


def test_a_missing_last_game_is_not_read_as_a_falling_share():
    e = _ev("WR", 0.85, [0.22, 0.24, None])
    assert WV.cut_role(e) == (True, None)


# ------------------------------------------------------------ keep list

class _Cfg(dict):
    pass


def test_the_keep_list_matches_names_and_ids_on_my_roster():
    info = {"10": {"name": "Emmett Johnson"}, "11": {"name": "Kaelon Black"}, "12": {"name": "Rachaad White"}}
    cfg = _Cfg(fantasy={"keep": ["emmett johnson", "12", "Nobody Here"]})
    kept, missing = LG.keep_list(cfg, ["10", "11", "12"], info)
    assert kept == {"10", "12"} and missing == ["Nobody Here"]
    assert LG.keep_list(_Cfg(), ["10"], info) == (set(), [])


def test_the_league_files_carry_the_users_keep_list():
    from draftkit.config import Config
    assert Config.load(league="keefamania").get("fantasy")["keep"] == ["Emmett Johnson"]
    assert Config.load(league="omnibeta").get("fantasy")["keep"] == ["Emmett Johnson", "Kaelon Black"]


# ------------------------------------------------------------ roster room

def _ctx(players, reserve, statuses, bench=6, ir=2):
    return {"league": {"roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF"]
                       + ["BN"] * bench + ["IR"] * ir, "settings": {"reserve_slots": ir}},
            "rosters": [{"roster_id": 3, "players": players, "reserve": reserve}],
            "roster_players": {3: [{"sleeper_id": p, "status": statuses.get(p)} for p in players]},
            "reserve_allow": ("IR", "PUP", "NFI", "COV")}


def test_roster_room_counts_open_spots_and_who_can_move_to_ir():
    full = [str(i) for i in range(15)]
    room = LG.roster_room(_ctx(full, [], {"3": "IR", "4": "Out"}), 3)
    assert room["limit"] == 15 and room["open"] == 0 and room["ir_open"] == 2
    assert room["ir_ready"] == ["3"], "an IR player on the bench can move; an Out one cannot here"
    room = LG.roster_room(_ctx(full[:14] + ["ir1"], ["ir1"], {}), 3)
    assert room["open"] == 1 and room["ir_open"] == 1 and room["ir_ready"] == []


def test_an_open_spot_ranks_an_add_with_no_cut():
    rows = [{"add": "a", "drop": None, "gain": 8.0, "ros_upside": 1.0, "open_spot": "an open roster spot"},
            {"add": "b", "drop": None, "gain": 9.0, "ros_upside": 1.0, "open_spot": None}]
    ranked, stand_pat = WV.rank_adds(rows, "season", True)
    assert [r["add"] for r in ranked] == ["a"] and not stand_pat


# ------------------------------------------------------------ byes

def _games():
    rows = []
    for w, pairs in {1: [("DET", "LA"), ("MIN", "KC")], 2: [("DET", "KC")], 3: [("LA", "MIN")]}.items():
        rows += [dict(season=2026, game_type="REG", week=w, home_team=h, away_team=a) for h, a in pairs]
    return pd.DataFrame(rows)


def test_byes_come_from_the_schedule_in_sleeper_codes():
    byes = E.bye_weeks(_games(), 2026)
    assert byes["LAR"] == [2] and byes["DET"] == [3] and byes["MIN"] == [2] and byes["KC"] == [3]
    info = {"g": {"team": "DET"}, "m": {"team": "MIN"}, "k": {"team": "KC"}}
    cal = E.bye_calendar(["g", "m", "k"], info, byes, range(2, 4), starters=["g", "m"])
    assert cal == [{"week": 2, "players": ["m"], "starters": ["m"]},
                   {"week": 3, "players": ["g", "k"], "starters": ["g"]}]
    table = E.bye_table(cal, str.upper)
    assert "| 3 | **G**, K | 1 |" in table
    assert E.bye_table([], str) == ["No byes left for this roster."]


# ------------------------------------------------------------ the report

def test_the_waiver_report_shows_room_keep_list_injuries_flags_and_byes():
    view = types.SimpleNamespace(season=2026, week=4)
    gate = types.SimpleNamespace(line=lambda: "LEAGUE DATA GATE: PASS")
    m = types.SimpleNamespace(summary_line=lambda: "inputs")
    info = {"a": {"name": "Braelon Allen", "team": "NYJ", "pos": "RB"},
            "ach": {"name": "De'Von Achane", "team": "MIA", "pos": "RB"},
            "ej": {"name": "Emmett Johnson", "team": "KC", "pos": "RB"},
            "xw": {"name": "Xavier Worthy", "team": "KC", "pos": "WR"},
            "ajb": {"name": "A.J. Brown", "team": "PHI", "pos": "WR"}}
    ev = {"xw": _ev("WR", 0.83, [0.24, 0.16, 0.09])}
    ranked = [{"add": "a", "drop": None, "gain": 9.0, "ros_upside": 1.0, "start_weeks": [4, 5],
               "open_spot": "move A.J. Brown (PHI, WR) to IR first"}]
    room = {"active": 15, "limit": 15, "open": 0, "reserve": [], "ir_slots": 2, "ir_open": 2, "ir_ready": ["ajb"]}
    injured = [{"add": "ach", "status": "IR", "part": "Knee - ACL", "season_out": True, "back": None}]
    md = WV.markdown("keefamania", view, "season", ("RB",), {"record": "1-2", "rank": 6, "teams": 10,
                     "contender": True}, gate, ranked, ["ej", "xw", "ajb"], set(), {}, ev, info,
                     {}, False, m, [], kept={"ej"}, keep_missing=[], room=room, injured=injured,
                     bye_cal=[{"week": 5, "players": ["ej", "xw"], "starters": []}])
    assert "none (move A.J. Brown (PHI, WR) to IR first)" in md
    assert "A.J. Brown (PHI, WR) can move to IR, opening a spot" in md
    assert "De'Von Achane (MIA, RB) (IR, Knee - ACL): out for the season" in md
    assert "**Your keep list**" in md and "NO -- your keep list" in md
    assert "eligible (flag: 83% of snaps, but his target share is falling" in md
    assert "## Your bye calendar" in md and "| 5 | Emmett Johnson (KC, RB), Xavier Worthy (KC, WR) | 0 |" in md


# ------------------------------------------------------------ smaller fixes

def test_widely_split_sources_are_flagged():
    assert A.source_split({"sleeper": 22.0, "fantasypros": 105.0, "espn": 152.0}) == "sleeper 22 vs espn 152"
    assert A.source_split({"sleeper": 180.0, "espn": 170.0, "fantasypros": 160.0}) is None
    assert A.source_split({"sleeper": 10.0, "espn": 25.0}) is None, "2.5x but only 15 points apart"
    assert A.source_split({"espn": 150.0}) is None


def test_the_teammate_in_a_scenario_resolves_by_the_players_team():
    wr = {"position": "WR", "active": True, "fantasy_positions": ["WR"]}
    players = {"6794": dict(wr, full_name="Justin Jefferson", team="MIN"),
               "99": dict(wr, full_name="Justin Jefferson", team="CLE"),
               "7": dict(wr, full_name="Jordan Addison", team="MIN")}
    assert SC.resolve("Justin Jefferson", players, team="MIN") == "6794"
    with pytest.raises(SC.ScenarioError, match="more than one"):
        SC.resolve("Justin Jefferson", players)
    with pytest.raises(SC.ScenarioError, match="more than one"):
        SC.resolve("Justin Jefferson", players, team="DAL")

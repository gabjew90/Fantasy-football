"""The fantasy question tools (fantasy.ask) and the session snapshot they read.

No network: a Snapshot is built by hand. What is pinned is what an answer
rests on -- that a name resolves to the right player or fails with the
candidates, that a swap is measured against the lineup actually set and never
moves a locked player, that a head-to-head is the winprob draw, and that the
snapshot is reused only while it is young."""

from __future__ import annotations

import datetime as dt
import json

import pytest

from fantasy import ask as A
from fantasy import snapshot as S
from fantasy.contract import QUANTILES, WEEK, Projection

UTC = dt.timezone.utc


def _p(pid, mean, lo, hi, pos="WR"):
    q = dict(zip(QUANTILES, (lo, (lo + mean) / 2, mean, (mean + hi) / 2, hi)))
    return Projection(pid, "weekly_blend_v0", WEEK, mean, quantiles=q, range_from="test", detail={"pos": pos})


def _player(name, pos, team):
    first, last = name.split(" ", 1)
    return {"full_name": name, "first_name": first, "last_name": last, "position": pos,
            "fantasy_positions": [pos], "team": team, "active": True}


LATER = (dt.datetime.now(UTC) + dt.timedelta(days=1)).isoformat(timespec="minutes").replace("+00:00", "Z")
EARLIER = (dt.datetime.now(UTC) - dt.timedelta(hours=1)).isoformat(timespec="minutes").replace("+00:00", "Z")


def _snap(**over):
    players = {"1": _player("Josh Allen", "QB", "BUF"), "2": _player("Travis Kelce", "TE", "KC"),
               "3": _player("Jake Ferguson", "TE", "DAL"), "4": _player("Terrance Ferguson", "TE", "LAR"),
               "5": _player("Puka Nacua", "WR", "LAR"), "6": _player("Garrett Wilson", "WR", "NYJ"),
               "7": _player("Josh Allen Jr", "WR", "FA1"),
               "CIN": {"first_name": "Cincinnati", "last_name": "Bengals", "position": "DEF", "team": "CIN",
                       "fantasy_positions": ["DEF"], "active": True}}
    players["7"]["active"] = False
    info = {sid: {"name": p.get("full_name") or "Cincinnati Bengals", "pos": p["position"], "team": p["team"],
                  "status": ""} for sid, p in players.items()}
    env = {t: {"opp": "X", "home": True, "spread": -3.0, "total": 44.0, "implied": 23.5,
               "kickoff_utc": LATER, "status": "STATUS_SCHEDULED"} for t in ("BUF", "KC", "DAL", "LAR", "NYJ", "CIN")}
    projs = {"1": _p("1", 22, 14, 30, "QB"), "2": _p("2", 12, 5, 20, "TE"), "3": _p("3", 10, 4, 18, "TE"),
             "4": _p("4", 9, 3, 17, "TE"), "5": _p("5", 15, 6, 25), "6": _p("6", 14, 5, 24),
             "CIN": Projection("CIN", "weekly_blend_v0", WEEK, 7.0)}
    base = dict(league="omnibeta", platform="sleeper", season=2026, week=3,
                built_at_utc=dt.datetime.now(UTC).isoformat(timespec="seconds"), my_rid=1, opp_rid=2,
                teams={1: {"name": "me", "players": ["1", "4", "5", "6", "3"], "starters": ["1", "4", "5"]},
                       2: {"name": "rival", "players": ["2", "CIN"], "starters": ["2"]}},
                slots={"QB": 1, "TE": 1, "WR": 1}, flex_slots=(), standing={"rank": 2, "teams": 10, "record": "2-0"},
                scoring={}, players=players, info=info, projections=projs, env=env,
                gate={"passed": True, "checks": []}, manifest={"entries": []})
    base.update(over)
    return S.Snapshot(**base)


# ------------------------------------------------------------------ names

def test_a_full_name_a_last_name_and_a_defense_resolve():
    s = _snap()
    assert A.resolve(s, "Travis Kelce") == "2"
    assert A.resolve(s, "kelce") == "2"
    assert A.resolve(s, "Puka") == "5"
    assert A.resolve(s, "CIN") == "CIN" and A.resolve(s, "Bengals") == "CIN"
    assert A.resolve(s, "Josh Allen") == "1", "the live QB, not the retired namesake"


def test_an_ambiguous_name_fails_with_the_candidates_unless_one_is_mine():
    s = _snap(teams={1: {"name": "me", "players": ["1", "4", "5", "6"], "starters": ["1", "4", "5"]},
                     2: {"name": "rival", "players": ["2", "CIN", "3"], "starters": ["2"]}})
    with pytest.raises(A.AskError, match="Jake Ferguson.*Terrance Ferguson"):
        A.resolve(s, "Ferguson")                       # no notes list: never picks
    notes = []
    assert A.resolve(s, "Ferguson", notes) == "4"      # Terrance is on my roster, Jake is not
    assert "Terrance Ferguson" in notes[0] and "Jake Ferguson" in notes[0]
    with pytest.raises(A.AskError, match="more than one"):
        A.resolve(_snap(), "Ferguson", [])             # both on my roster: no guess
    with pytest.raises(A.AskError, match="no player named"):
        A.resolve(s, "Nobody Anybody")


def test_owner_says_whose_player_and_whether_he_starts():
    s = _snap()
    assert A.owner(s, "4") == {"rid": 1, "who": "you", "team_name": "me", "starting": True}
    assert A.owner(s, "3")["starting"] is False
    assert A.owner(s, "2")["who"] == "your opponent"
    assert A.owner(s, "7")["who"] == "free agent"


# ------------------------------------------------------------------ head to head

def test_the_head_to_head_is_the_winprob_draw():
    s = _snap()
    h = A.head_to_head(s, ["1", "4"])                  # 22 vs 9: near certain
    assert h["p_first_outscores_second"] > 0.95 and h["mean_gap"] == 13.0
    same = _snap(projections=dict(_snap().projections, **{"3": _p("3", 9, 3, 17, "TE")}))
    h2 = A.head_to_head(same, ["3", "4"])              # identical ranges: a coin flip
    assert 0.45 < h2["p_first_outscores_second"] < 0.55
    h3 = A.head_to_head(s, ["5", "6", "4"])
    assert abs(sum(h3["p_top_scorer"].values()) - 1) < 0.01


# ------------------------------------------------------------------ swap

def test_a_swap_is_measured_against_the_lineup_actually_set():
    s = _snap()
    r = A.swap(s, ["Jake Ferguson"], ["Terrance Ferguson"])
    assert r.data["baseline"]["from"] == "the lineup you have set"
    assert r.data["baseline"]["lineup"] == ["1", "4", "5"]
    opt = r.data["options"][0]
    assert opt["bench"] == ["4"] and set(opt["lineup"]) == {"1", "3", "5"}
    assert opt["p_win"] > r.data["baseline"]["p_win"], "10 over 9 at TE is a better lineup"


def test_without_bench_every_legal_seat_is_tried_best_first():
    s = _snap()
    r = A.swap(s, ["Garrett Wilson"])
    benched = [o["bench"] for o in r.data["options"]]
    assert benched == [["5"]], "a WR can only take the WR seat in a QB/TE/WR lineup"


def test_a_swap_refuses_players_who_are_not_mine_or_already_in_or_locked():
    s = _snap()
    with pytest.raises(A.AskError, match="not on your roster"):
        A.swap(s, ["Travis Kelce"])
    with pytest.raises(A.AskError, match="already in"):
        A.swap(s, ["Puka Nacua"])
    started = dict(s.env, DAL=dict(s.env["DAL"], kickoff_utc=EARLIER))
    with pytest.raises(A.AskError, match="kicked off"):
        A.swap(_snap(env=started), ["Jake Ferguson"])
    with pytest.raises(A.AskError, match="no legal lineup"):
        A.swap(s, ["Jake Ferguson"], ["Josh Allen"])     # a TE cannot take the QB seat


def test_without_a_full_lineup_set_the_swap_starts_from_the_best_by_mean():
    s = _snap(teams={1: {"name": "me", "players": ["1", "4", "5", "6", "3"], "starters": []},
                     2: {"name": "rival", "players": ["2"], "starters": ["2"]}})
    r = A.swap(s, ["Terrance Ferguson"], ["Jake Ferguson"])
    assert r.data["baseline"]["from"].startswith("the best-by-mean lineup")
    assert set(r.data["baseline"]["lineup"]) == {"1", "3", "5"}


# ------------------------------------------------------------------ roster, players

def test_a_roster_lists_starters_first_and_finds_a_team_by_manager():
    s = _snap()
    r = A.roster(s, "rival")
    assert r.data["who"] == "your opponent" and r.data["players"][0]["starting"]
    mine = A.roster(s)
    assert [p["starting"] for p in mine.data["players"]] == [True, True, True, False, False]
    with pytest.raises(A.AskError, match="matches no team"):
        A.roster(s, "zzz")


def test_a_player_answer_carries_the_game_the_range_and_the_data_age(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None: {})
    s = _snap()
    r = A.players(s, ["Kelce", "Terrance Ferguson"])
    k = r.data["players"][0]
    assert k["owner"]["who"] == "your opponent" and k["projection"]["p10"] == 5.0
    assert "head_to_head" in r.data
    assert "league read 0 min ago" in r.text and "league data check: PASS" in r.text
    assert r.record["gate"]["passed"] is True, "the session log gets the gate"


def test_a_failed_gate_is_printed_on_every_answer(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None: {})
    s = _snap(gate={"passed": False, "checks": [{"name": "roster read after the request", "passed": False,
                                                 "detail": "cached copy"}]})
    assert "FAIL -- roster read after the request (cached copy)" in A.players(s, ["Kelce"]).text
    assert "FAIL" in A.roster(s).text


# ------------------------------------------------------------------ snapshot

def test_the_snapshot_survives_a_json_round_trip():
    s = _snap(flex_slots=(frozenset({"WR", "TE"}),))
    back = S.Snapshot.from_json(json.loads(json.dumps(s.to_json(), default=str)))
    assert back.teams[1]["players"] == s.teams[1]["players"]
    assert back.flex_slots == (frozenset({"WR", "TE"}),)
    assert back.projections["2"].quantiles == s.projections["2"].quantiles
    assert back.projections["2"].floor == 5.0


def test_the_snapshot_is_reused_while_young_and_rebuilt_when_old(monkeypatch, tmp_path):
    monkeypatch.setenv("NFL_CACHE", str(tmp_path))
    builds = []

    def fake_build(league, week=None):
        builds.append(1)
        return _snap(league=league)
    monkeypatch.setattr(S, "build", fake_build)
    S.load("omnibeta")
    S.load("omnibeta")
    assert len(builds) == 1, "a second question reuses the read"
    S.load("omnibeta", fresh=True)
    assert len(builds) == 2, "--fresh re-reads"
    later = dt.datetime.now(UTC) + dt.timedelta(minutes=S.TTL_MIN + 1)
    S.load("omnibeta", now=later)
    assert len(builds) == 3, "an old snapshot is never served"
    S.path_for("omnibeta", None).write_text("{not json", encoding="utf-8")
    S.load("omnibeta")
    assert len(builds) == 4, "a broken cache file is rebuilt, never trusted"


def test_a_designated_player_says_when_his_status_settles_and_who_locks_first(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None: {})
    s = _snap()
    early = (dt.datetime.now(UTC) + dt.timedelta(hours=2)).isoformat(timespec="minutes").replace("+00:00", "Z")
    later = (dt.datetime.now(UTC) + dt.timedelta(hours=8)).isoformat(timespec="minutes").replace("+00:00", "Z")
    env = dict(s.env, LAR=dict(s.env["LAR"], kickoff_utc=later), DAL=dict(s.env["DAL"], kickoff_utc=early))
    players = dict(s.players, **{"4": dict(s.players["4"], injury_status="Questionable")})
    info = dict(s.info, **{"4": dict(s.info["4"], status="Questionable")})
    r = A.players(_snap(env=env, players=players, info=info), ["Terrance Ferguson"])
    row = r.data["players"][0]
    assert row["status"] == "Questionable" and row["status_settles_pt"]
    assert [x.split(" (")[0] for x in row["my_players_locking_first"]] == ["Jake Ferguson"]
    assert "locking before then: Jake Ferguson" in r.text


def test_a_range_caveat_travels_with_the_projection(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None: {})
    s = _snap()
    p = s.projections["1"]
    s.projections["1"] = Projection(p.player_id, p.source, p.horizon, p.mean, p.quantiles,
                                    dict(p.detail, range_caveats=["QB p10: 14.5% of outcomes vs 10%"]), p.range_from)
    r = A.players(s, ["Josh Allen"])
    assert r.data["players"][0]["projection"]["range_caveats"] == ["QB p10: 14.5% of outcomes vs 10%"]
    assert "Range caveat" in r.text


def test_the_swap_prices_the_same_opponent_as_the_lineup_command():
    from fantasy import lineup as LU
    s = _snap(teams={1: {"name": "me", "players": ["1", "4", "5", "6", "3"], "starters": ["1", "4", "5"]},
                     2: {"name": "rival", "players": ["2", "6x"], "starters": []}})
    theirs, how = A._opponent(s)
    assert how.startswith("their best-by-mean") and theirs == ["2"]
    assert LU.opponent_lineup(False, [], [], 3, {}, {}, {}, ()) == ([], "no opponent this week")


# ------------------------------------------------------------------ nfl.py wiring

def _nfl(monkeypatch, capsys, argv, snap=None):
    import nfl
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None: {})
    monkeypatch.setattr(S, "load", lambda league, week=None, fresh=False: snap or _snap())
    rc = nfl.main(argv)
    out = capsys.readouterr()
    return rc, out.out, out.err


def test_nfl_takes_names_after_the_options_and_renders_json(monkeypatch, capsys):
    rc, out, _ = _nfl(monkeypatch, capsys, ["fantasy", "player", "--league", "omnibeta", "Kelce", "Puka Nacua"])
    assert rc == 0 and "Travis Kelce" in out and "Puka Nacua" in out and "Head to head" in out
    rc, out, _ = _nfl(monkeypatch, capsys, ["fantasy", "player", "--league", "omnibeta", "--json", "Kelce"])
    assert rc == 0 and json.loads(out)["players"][0]["name"] == "Travis Kelce"


def test_nfl_turns_a_tool_refusal_into_exit_2_and_rejects_stray_names(monkeypatch, capsys):
    rc, _, err = _nfl(monkeypatch, capsys, ["fantasy", "swap", "--league", "omnibeta", "--start", "Kelce"])
    assert rc == 2 and err.startswith("ASK: ") and "not on your roster" in err
    rc, _, err = _nfl(monkeypatch, capsys, ["fantasy", "roster", "--league", "omnibeta", "Kelce"])
    assert rc == 2 and "unexpected arguments Kelce" in err
    rc, _, err = _nfl(monkeypatch, capsys, ["props", "slate", "KC@MIA"])
    assert rc == 2 and "unexpected arguments" in err
    rc, _, err = _nfl(monkeypatch, capsys, ["props", "line", "Travis", "Kelce", "catches"])
    assert rc == 2 and "is not a line" in err


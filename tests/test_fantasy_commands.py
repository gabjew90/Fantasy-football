"""Step 3: the gate, win probability, lineup candidates, the weekly blend,
status verdicts, and the scenario's observed split -- the parts that decide."""

from __future__ import annotations

import datetime as dt

import pandas as pd
import pytest

from core import status as ST
from core.manifest import Manifest
from core.scoring import score_frame
from fantasy import environment as E
from fantasy import gate as G
from fantasy import lineup as LU
from fantasy import scenario as SC
from fantasy import weekly as W
from fantasy import winprob as WP
from fantasy.contract import QUANTILES, WEEK, Projection

UTC = dt.timezone.utc


def _p(pid, mean, lo, hi, pos="WR"):
    q = dict(zip(QUANTILES, (lo, (lo + mean) / 2, mean, (mean + hi) / 2, hi)))
    return Projection(pid, "t", WEEK, mean, quantiles=q, range_from="test", detail={"pos": pos})


# ------------------------------------------------------------------ gate

def test_the_gate_compares_scoring_stat_by_stat_and_fails_unverified_keys():
    mism, unver = G.scoring_diffs({"rec": 0.5, "pass_int": -1.0, "pass_td_40p": 2.0},
                                  {"rec": 0.5, "pass_int": 2.0})
    assert mism == [("pass_int", -1.0, 2.0)] and unver == ["pass_td_40p"]


def test_the_gate_passes_only_on_a_fresh_roster_and_matching_scoring():
    start = dt.datetime(2026, 9, 24, 12, tzinfo=UTC)
    m = Manifest("t", started_at=start)
    m.record("league roster", source="sleeper", status="fresh", fetched_at=start + dt.timedelta(seconds=5))
    ok = G.evaluate(m, {"rec": 1.0}, {"rec": 1.0, "fgm": 3.0}, ["a"], {"a": object()})
    assert ok.passed and ok.line() == "LEAGUE DATA GATE: PASS"
    m.record("league roster", source="yahoo sync", status="cached", fetched_at=start - dt.timedelta(days=7))
    bad = G.evaluate(m, {"rec": 1.0}, {"rec": 0.5}, ["a", "b"], {"a": object()})
    assert not bad.passed
    names = {c.name for c in bad.checks if not c.passed}
    assert names == {"roster read after the request", "scoring matches the league", "lineup covered"}
    assert "CONDITIONAL" in bad.line()


# -------------------------------------------------------------- winprob

def test_p_win_is_near_certain_for_a_big_favourite_and_symmetric():
    projs = {"a": _p("a", 30, 25, 35), "b": _p("b", 10, 5, 15)}
    assert WP.p_win(["a"], ["b"], projs) > 0.99
    assert WP.p_win(["b"], ["a"], projs) < 0.01


def test_a_favourite_prefers_the_steady_player_and_an_underdog_the_volatile_one():
    """The user's rule falls out of maximising P(win): same mean, different spread."""
    projs = {"steady": _p("steady", 12, 10, 14), "boom": _p("boom", 12, 0, 30),
             "me": _p("me", 100, 98, 102), "them_fav": _p("them_fav", 105, 103, 107),
             "them_dog": _p("them_dog", 95, 93, 97)}
    fav_steady = WP.p_win(["me", "steady"], ["them_dog"], projs)
    fav_boom = WP.p_win(["me", "boom"], ["them_dog"], projs)
    dog_steady = WP.p_win(["me", "steady"], ["them_fav", "them_fav_x"], dict(projs, them_fav_x=_p("x", 30, 28, 32)))
    dog_boom = WP.p_win(["me", "boom"], ["them_fav", "them_fav_x"], dict(projs, them_fav_x=_p("x", 30, 28, 32)))
    assert fav_steady > fav_boom
    assert dog_boom > dog_steady


def test_a_mean_only_or_missing_projection_is_drawn_at_its_mean():
    assert set(WP.draws(Projection("k", "t", WEEK, 7.0), n=10)) == {7.0}
    assert set(WP.draws(None, n=10)) == {0.0}


# ------------------------------------------------------------ candidates

SLOTS = {"QB": 1, "WR": 1}
FLEX = [frozenset({"RB", "WR", "TE"})]


def test_candidates_label_every_player_in_and_out():
    info = {"qb1": {"pos": "QB"}, "qb2": {"pos": "QB"}, "wr1": {"pos": "WR"}, "wr2": {"pos": "WR"},
            "wr3": {"pos": "WR"}}
    projs = {k: Projection(k, "t", WEEK, v) for k, v in
             {"qb1": 20, "qb2": 18, "wr1": 15, "wr2": 14, "wr3": 9}.items()}
    cands = LU.candidates(list(info), info, projs, SLOTS, FLEX)
    assert cands[0] == ("best by mean", ["qb1", "wr1", "wr2"])
    labels = [c[0] for c in cands[1:]]
    assert "in:qb2|out:qb1" in labels and "in:wr3|out:wr2" in labels
    ins, outs = LU.change("in:wr3|out:wr2")
    assert (ins, outs) == (["wr3"], ["wr2"])


def test_a_swap_must_clear_the_noise_threshold_to_beat_the_mean_lineup():
    projs = {"a": _p("a", 10, 8, 12), "b": _p("b", 10, 8, 12.01), "o": _p("o", 10, 8, 12)}
    label, ids, pw = LU.decide([("best by mean", ["a"]), ("in:b|out:a", ["b"])], ["o"], projs)
    assert label == "best by mean"


# ---------------------------------------------------------------- weekly

def test_market_weight_decays_linearly_to_zero():
    c = {"week1": 0.6, "zero_by_week": 9}
    assert W.market_weight(1, c) == pytest.approx(0.6)
    assert W.market_weight(5, c) == pytest.approx(0.3)
    assert W.market_weight(9, c) == 0.0 and W.market_weight(14, c) == 0.0


def test_the_blend_uses_only_a_full_market_board_and_gates_status():
    s = Projection("1", "sleeper_weekly", WEEK, 10.0, detail={"pos": "WR"})
    full = Projection("1", "market_points", WEEK, 14.0, detail={"pos": "WR", "partial": False})
    part = Projection("1", "market_points", WEEK, 3.0, detail={"pos": "WR", "partial": True})
    env = {"opp": "X"}
    assert W.blend("1", {"pos": "WR"}, s, full, env, 0.5, None).mean == pytest.approx(12.0)
    assert W.blend("1", {"pos": "WR"}, s, part, env, 0.5, None).mean == pytest.approx(10.0)
    out = W.blend("1", {"pos": "WR", "status": "Out"}, s, full, env, 0.5, None)
    assert out.mean == 0.0 and "Out" in out.detail["zero_reason"]
    bye = W.blend("1", {"pos": "WR"}, s, full, None, 0.5, None)
    assert bye.mean == 0.0 and "no game" in bye.detail["zero_reason"]
    q = W.blend("1", {"pos": "WR", "status": "Questionable"}, s, None, env, 0.5, None)
    assert q.mean == 10.0 and q.detail["flag"] == "Questionable"


# ------------------------------------------------------------ environment

def test_the_scoreboard_gives_each_team_its_side_of_the_line():
    sb = {"events": [{"date": "2026-09-25T00:15Z", "status": {"type": {"name": "STATUS_SCHEDULED"}},
                      "competitions": [{"odds": [{"spread": -4.5, "overUnder": 42.5}],
                                        "competitors": [{"homeAway": "home", "team": {"abbreviation": "GB"}},
                                                        {"homeAway": "away", "team": {"abbreviation": "WSH"}}]}]}]}
    env = E.parse_scoreboard(sb)
    assert env["GB"]["spread"] == -4.5 and env["GB"]["implied"] == pytest.approx(23.5)
    assert env["WAS"]["spread"] == 4.5 and env["WAS"]["implied"] == pytest.approx(19.0) and env["WAS"]["opp"] == "GB"
    assert E.started(env["GB"], dt.datetime(2026, 9, 25, 1, tzinfo=UTC))
    assert not E.started(env["GB"], dt.datetime(2026, 9, 24, 23, tzinfo=UTC))


# ----------------------------------------------------------------- status

def _status(hours, lines=40, spread="GB -4.5", inj=0, desig=0, proj=True, league=None):
    return {"games": [{"game": "ATL@GB", "started": False, "hours_to_kickoff": hours, "spread": spread,
                       "total": 42.5, "lines": lines, "kickoff_utc": "2026-09-25T00:15:00+00:00"}],
            "injuries": {"rows": inj, "designations": desig}, "projections": {"published": proj, "players": 400},
            "league": league}


def test_status_says_when_a_run_is_early_and_what_it_misses():
    early = " ".join(ST.verdicts(_status(120, lines=10, spread=None, proj=False)))
    assert "spread and total posted for 0" in early and "thin" in early and "More than a day out" in early
    assert "placeholders" in early and "first practice report comes Wednesday" in early
    close = " ".join(ST.verdicts(_status(1.0, inj=250, desig=8)))
    assert "Inside the closing window" in close and "designations out for 8" in close


def test_status_flags_a_stale_league_roster():
    v = ST.verdicts(_status(5, league={"name": "keef", "platform": "yahoo", "roster_age_h": 185.2,
                                       "source": "local sync copy"}))[-1]
    assert "185 h old" in v and "STALE" in v


# --------------------------------------------------------------- scenario

def test_the_observed_split_separates_weeks_with_and_without_the_teammate():
    rows = []
    for w, pts in ((1, 20), (2, 22), (3, 10), (4, 12)):
        rows.append({"player_id": "me", "team": "ATL", "week": w, "season_type": "REG", "receptions": 0,
                     "rushing_yards": pts * 10, "targets": 5, "carries": 15})
    rows += [{"player_id": "mate", "team": "ATL", "week": w, "season_type": "REG"} for w in (1, 2)]
    df = pd.DataFrame(rows)
    obs = SC.observed({2025: df}, "me", "mate", "ATL", {"rush_yd": 0.1})
    assert obs[0]["with"]["weeks"] == [1, 2] and obs[0]["with"]["points"] == 21.0
    assert obs[0]["without"]["weeks"] == [3, 4] and obs[0]["without"]["points"] == 11.0


def test_names_resolve_to_one_player_or_fail_with_the_candidates():
    players = {"1": {"full_name": "Kyle Williams", "position": "WR", "team": "NE", "active": True,
                     "fantasy_positions": ["WR"]},
               "2": {"full_name": "Drake London", "position": "WR", "team": "ATL", "active": True,
                     "fantasy_positions": ["WR"]},
               "3": {"full_name": "Kyle Williams", "position": "WR", "team": "NYJ", "active": True,
                     "fantasy_positions": ["WR"]}}
    assert SC.resolve("Drake London", players) == "2" and SC.resolve("2", players) == "2"
    with pytest.raises(SC.ScenarioError, match="more than one"):
        SC.resolve("Kyle Williams", players)
    with pytest.raises(SC.ScenarioError, match="no player"):
        SC.resolve("Nobody Here", players)


def test_the_engine_scores_in_the_league_scoring():
    assert SC.engine_scoring({"rec": 0.5, "rec_yd": 0.1, "rush_yd": 0.1, "rush_td": 6, "rec_td": 6, "pass_td": 4}) \
        == "rec=0.5,rec_yd=0.1,rush_yd=0.1,rush_td=6.0,rec_td=6.0"


def test_score_frame_ignores_missing_columns():
    df = pd.DataFrame({"receptions": [5], "receiving_yards": [60]})
    assert float(score_frame(df, {"receptions": 1.0, "receiving_yards": 0.1, "passing_tds": 4.0})[0]) == 11.0


# ------------------------------------------------------- code review fixes

def test_locked_players_neither_enter_nor_leave():
    info = {"qb1": {"pos": "QB"}, "wr1": {"pos": "WR"}, "wr2": {"pos": "WR"}, "wr3": {"pos": "WR"},
            "wr4": {"pos": "WR"}}
    projs = {k: Projection(k, "t", WEEK, v) for k, v in
             {"qb1": 20, "wr1": 3, "wr2": 14, "wr3": 15, "wr4": 16}.items()}
    # wr1 is a locked STARTER (played Thursday, scored 3); wr4 is locked on the BENCH
    cands = LU.candidates(list(info), info, projs, SLOTS, FLEX, locked={"wr1", "wr4"},
                          current=["qb1", "wr1", "wr2"])
    assert all("wr1" in ids and "wr4" not in ids for _, ids in cands)
    assert all("wr1" not in LU.change(lab)[1] for lab, _ in cands[1:])


def test_a_finished_game_counts_its_actual_score():
    p = Projection("1", "weekly_blend_v0", WEEK, 14.0, quantiles=dict(zip(QUANTILES, (5, 9, 13, 17, 23))),
                   range_from="x", detail={"pos": "WR"})
    f = W.final_score(p, {"rec": 2, "rec_yd": 21, "gp": 1}, {"rec": 1.0, "rec_yd": 0.1})
    assert f.mean == pytest.approx(4.1) and f.floor == f.ceiling == pytest.approx(4.1)
    assert f.detail["final"] and f.detail["projected"] == 14.0 and f.range_from == "final score"
    assert W.final_score(p, None, {"rec": 1.0}).mean == 0.0, "no stat line: he did not play"


def test_draws_are_centred_on_the_displayed_mean_and_never_below_the_floor():
    import numpy as np
    biased = _p("a", 12.0, 2.0, 30.0)                      # a skewed range around 12
    d = WP.draws(biased, n=200000, seed=3)
    assert abs(float(d.mean()) - 12.0) < 0.1
    low = Projection("b", "t", WEEK, 3.0, quantiles=dict(zip(QUANTILES, (0.5, 4.0, 5.0, 8.0, 12.0))),
                     range_from="x")
    assert float(np.min(WP.draws(low, n=50000, seed=4))) >= 0.0


def test_weeks_before_a_teammate_joined_are_not_counted_as_without_him():
    rows = [{"player_id": "me", "team": "ATL", "week": w, "season_type": "REG", "rushing_yards": 100,
             "targets": 1, "carries": 10} for w in range(1, 7)]
    rows += [{"player_id": "mate", "team": "ATL", "week": w, "season_type": "REG"} for w in (4, 6)]
    obs = SC.observed({2025: pd.DataFrame(rows)}, "me", "mate", "ATL", {"rush_yd": 0.1})
    assert obs[0]["with"]["weeks"] == [4, 6] and obs[0]["without"]["weeks"] == [5]


def test_the_scoring_only_gate_checks_only_scoring():
    g = G.scoring_only({"rec": 0.5}, {"rec": 0.5, "fgm": 3})
    assert g.passed and [c.name for c in g.checks] == ["scoring matches the league"]


def test_a_read_only_context_does_not_append_transactions(monkeypatch):
    import inspect
    from draftkit import briefs
    assert "write_state" in inspect.signature(briefs.build_context).parameters
    src = inspect.getsource(briefs.build_context)
    assert "if write_state:" in src and "append_transactions" in src.split("if write_state:")[1][:200]


def test_the_injury_watch_names_designated_teammates_and_the_scenario_to_run():
    from fantasy import lineup as LU
    info = {"1": {"name": "Terrance Ferguson", "pos": "TE", "team": "LAR"},
            "2": {"name": "DJ Moore", "pos": "WR", "team": "CHI"},
            "3": {"name": "Deebo Samuel", "pos": "WR", "team": "SF"}}
    players = {"1": {"team": "LAR", "position": "TE"},
               "2": {"team": "CHI", "position": "WR", "injury_status": "Questionable", "injury_body_part": "Shoulder",
                     "depth_chart_order": 1},
               "3": {"team": "SF", "position": "WR"},
               "9": {"team": "LAR", "position": "WR", "full_name": "Puka Nacua", "injury_status": "Doubtful",
                     "injury_body_part": "Hip", "depth_chart_order": 1},
               "8": {"team": "LAR", "position": "WR", "full_name": "Deep Reserve", "injury_status": "Out",
                     "depth_chart_order": 5},
               "7": {"team": "LAR", "position": "LB", "full_name": "A Linebacker", "injury_status": "Out",
                     "depth_chart_order": 1},
               "6": {"team": "LAR", "position": "WR", "full_name": "Long Term", "injury_status": "IR",
                     "depth_chart_order": 1},
               "5": {"team": "LAR", "position": "QB", "full_name": "Backup Qb", "injury_status": "Questionable",
                     "depth_chart_order": 2}}
    rows = {r["name"]: r for r in LU.injury_watch(["1", "2", "3"], info, players, "omnibeta")}
    assert set(rows) == {"Terrance Ferguson", "DJ Moore"}, "a player with nothing to watch has no row"
    fer = rows["Terrance Ferguson"]
    assert [t["name"] for t in fer["teammates"]] == ["Puka Nacua"],         "only this week's designations, on teammates who move his volume (not IR, not a backup QB)"
    assert fer["teammates"][0]["scenario"] == (
        'nfl.py fantasy scenario --league omnibeta --player "Terrance Ferguson" --out "Puka Nacua"')
    assert rows["DJ Moore"]["own"] == "Questionable" and rows["DJ Moore"]["own_part"] == "Shoulder"


def test_lock_order_says_when_a_status_settles_and_who_locks_first():
    import datetime as _dt
    from fantasy import lineup as LU
    info = {"fer": {"name": "Terrance Ferguson", "team": "LAR", "pos": "TE"},
            "fan": {"name": "Harold Fannin", "team": "CLE", "pos": "TE"},
            "wr": {"name": "Early Receiver", "team": "CLE", "pos": "WR"},
            "gone": {"name": "Already Played", "team": "ATL", "pos": "TE"}}
    env = {"LAR": {"kickoff_utc": "2026-09-28T00:20:00Z"},      # Sunday night
           "CLE": {"kickoff_utc": "2026-09-27T17:00:00Z"},      # Sunday 10:00 PT
           "ATL": {"kickoff_utc": "2026-09-25T00:15:00Z"}}      # Thursday, already started
    watch = [{"pid": "fer", "team": "LAR"}]
    LU.lock_order(watch, ["fer", "fan", "wr", "gone"], info, env, _dt.datetime(2026, 9, 26, 6, 0, tzinfo=_dt.timezone.utc))
    assert watch[0]["status_known_pt"].startswith("Sun 3:50 PM") or "UTC" in watch[0]["status_known_pt"]
    assert watch[0]["locks_before"] and watch[0]["locks_before"][0].startswith("Harold Fannin")
    assert all("Already Played" not in x for x in watch[0]["locks_before"]), "a started game is not a coming lock"
    assert len(watch[0]["locks_before"]) == 1, "only his position: the WR who locks first is not a swap for a TE"


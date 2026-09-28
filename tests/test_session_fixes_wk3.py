"""Fixes from the 2026-09-28 chat session log (DECISIONS #125): game logs,
the head-to-head once games are over, the early-week Out assumption, bench
options for a starter, the waiver's "also scored" list, the shared week roll
and the transcript check. No network."""

from __future__ import annotations

import datetime as dt
import types

import pandas as pd

from fantasy import ask as A
from fantasy import boxscore as BX
from fantasy import waiver as WV
from fantasy.contract import WEEK, Projection
from test_fantasy_ask import _snap                 # tests/ is on sys.path (no package)

HALF = {"rec": 0.5, "rec_yd": 0.1, "rec_td": 6.0, "rush_yd": 0.1, "rush_td": 6.0, "pass_yd": 0.04, "pass_td": 4.0,
        "pass_int": -2.0}


def _stats():
    base = dict(season=2026, season_type="REG", team="NO", completions=0, attempts=0, passing_yards=0, passing_tds=0,
                passing_interceptions=0, carries=0, rushing_yards=0, rushing_tds=0)
    rows = [dict(base, player_id="jj", week=1, opponent_team="DET", targets=7, receptions=3, receiving_yards=54,
                 receiving_tds=1),
            dict(base, player_id="jj", week=3, opponent_team="LV", targets=8, receptions=8, receiving_yards=53,
                 receiving_tds=2)]
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ box scores

def test_a_game_log_scores_the_week_with_and_without_touchdowns():
    log = BX.game_log(_stats(), "jj", "TE", HALF)
    assert [g["week"] for g in log] == [1, 3]
    wk3 = log[1]
    assert wk3["receptions"] == 8 and wk3["receiving_tds"] == 2
    assert wk3["pts"] == round(8 * 0.5 + 5.3 + 12, 1) and wk3["pts_no_td"] == round(8 * 0.5 + 5.3, 1)
    table = BX.log_table(log, "TE")
    assert "Rush yds" not in table[0], "a receiver's all-zero rushing columns are left out"


def test_a_season_summary_is_per_game_with_touchdowns_as_totals():
    s = BX.season_summary(_stats(), "jj", "TE", HALF)
    assert s["games"] == 2 and s["targets"] == 7.5 and s["receiving_tds"] == 3
    assert "2 games" in BX.summary_line(s, "TE") and "3 rec td" in BX.summary_line(s, "TE")
    assert BX.season_summary(_stats(), "nobody", "TE", HALF) is None


# ------------------------------------------------------------------ head to head

def _final(p, pts):
    return Projection(p.player_id, p.source, p.horizon, pts, quantiles={q: pts for q in p.quantiles},
                      detail=dict(p.detail, final=True, projected=p.mean), range_from="final score")


def test_a_head_to_head_of_finished_games_is_the_score_not_a_simulation():
    s = _snap()
    s.projections["5"], s.projections["6"] = _final(s.projections["5"], 15.2), _final(s.projections["6"], 6.3)
    h = A.head_to_head(s, ["5", "6"])
    assert h == {"all_final": True, "scores": {"5": 15.2, "6": 6.3}}
    assert "no head-to-head to simulate" in A._h2h_lines(s, h)[0]
    s2 = _snap()
    s2.projections["5"] = _final(s2.projections["5"], 15.2)
    h2 = A.head_to_head(s2, ["5", "6"])
    assert h2["final"] == ["5"] and any("Already final" in x for x in A._h2h_lines(s2, h2))


# ------------------------------------------------------------------ a status zero

def test_an_out_zero_says_it_takes_the_tag_at_face_value(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None, team=False: {})
    monkeypatch.setattr(A, "_early_week", lambda now=None: True)      # the caveat is a Monday/Tuesday one
    s = _snap()
    s.projections["6"] = Projection("6", "weekly_blend_v0", WEEK, 0.0, detail={"zero_reason": "status Out"})
    s.info["6"] = dict(s.info["6"], status="Out")
    text = A.players(s, ["Garrett Wilson"]).text
    assert "Projection: 0 -- status Out." in text and "Assumption: the 0 takes Sleeper's status at face value" in text
    monkeypatch.setattr(A, "_early_week", lambda now=None: False)
    assert "Assumption:" not in A.players(s, ["Garrett Wilson"]).text, "later in the week the tag stands"


# ------------------------------------------------------------------ bench options

def test_a_starter_is_shown_the_bench_player_who_projects_higher():
    s = _snap()                                        # Terrance (9) starts; Jake (10) is on the bench
    opts = A.bench_options(s, "4")
    assert [o["name"] for o in opts] == ["Jake Ferguson"]
    assert opts[0]["p_win_with"] > opts[0]["p_win_now"]
    assert '--start "Jake Ferguson" --bench "Terrance Ferguson"' in opts[0]["command"]
    assert A.bench_options(s, "5") == [], "Puka (15) has no one better behind him (Wilson 14)"
    assert A.bench_options(s, "3") == [], "a bench player gets no bench options"


# ------------------------------------------------------------------ waiver: everyone scored is named

def test_every_scored_add_is_named_even_below_the_table():
    view = types.SimpleNamespace(season=2026, week=4)
    gate = types.SimpleNamespace(line=lambda: "LEAGUE DATA GATE: PASS")
    m = types.SimpleNamespace(summary_line=lambda: "inputs")
    info = {f"p{k}": {"name": f"Player {k}", "team": "KC", "pos": "WR"} for k in range(15)}
    ranked = [{"add": f"p{k}", "drop": "x", "gain": 20.0 - k, "ros_upside": 1.0, "start_weeks": [5]} for k in range(15)]
    md = WV.markdown("keefamania", view, "season", ("WR",), {"record": "1-0", "rank": 3, "teams": 10,
                     "contender": True}, gate, ranked, [], set(), {}, {}, info, {}, False, m, [],
                     scored={"candidates": 80, "improving": 15})
    assert "**Also scored, below the table:** Player 12 (KC, WR) +8.0; Player 13 (KC, WR) +7.0; Player 14" in md
    assert "80 unrostered players were scored" in md


# ------------------------------------------------------------------ the week roll is one rule

def test_the_question_tools_and_waivers_roll_the_week_the_same_way():
    from fantasy import environment as E
    assert WV.decision_week is E.decision_week and WV.ROLL_BELOW == E.ROLL_BELOW
    s = _snap(rolled="week 3 has 1 of 16 games still to kick off, so this is week 4 (pass --week 3 for this week)")
    assert "**Week:** week 3 has 1 of 16" in A.header(s)
    assert "**Week:**" not in A.header(_snap())


# ------------------------------------------------------------------ the transcript check

def test_the_log_counts_transcript_entries_that_are_not_verbatim(tmp_path):
    import nfl
    (tmp_path / "chat_transcript.md").write_text(
        "## 20:30 UTC\n**User:** Sutton?\n**Reply:**\nMiddling WR3 so far.\n"
        "## 20:40 UTC\n**User:** waivers?\n**Reply:** (as sent below)\n"
        "## 20:41 UTC\n**User:** ok\n**Reply:**\nStart Deebo.\n", encoding="utf-8")
    text = nfl.session_report(tmp_path).read_text(encoding="utf-8")
    assert "**Transcript: 1 of 3 entries do not hold the reply verbatim**" in text, "a short real reply is fine"


def test_bench_options_respect_locks_and_a_week_without_an_opponent():
    s = _snap()
    past = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=1)).isoformat(timespec="minutes").replace("+00:00", "Z")
    locked_bench = _snap(env=dict(s.env, DAL=dict(s.env["DAL"], kickoff_utc=past)))
    assert A.bench_options(locked_bench, "4") == [], "Jake's game started: he cannot come in"
    locked_starter = _snap(env=dict(s.env, LAR=dict(s.env["LAR"], kickoff_utc=past)))
    assert A.bench_options(locked_starter, "4") == [], "Terrance's game started: he cannot go out"
    no_opp = _snap(opp_rid=None)
    opts = A.bench_options(no_opp, "4")
    assert opts and opts[0]["p_win_with"] is None and opts[0]["mean"] == 10.0


def test_the_out_caveat_is_for_early_in_the_week_only():
    mon = dt.datetime(2026, 9, 28, 20, tzinfo=dt.timezone.utc)      # Monday 1 PM PT
    sat = dt.datetime(2026, 10, 3, 20, tzinfo=dt.timezone.utc)      # Saturday
    assert A._early_week(mon) is True and A._early_week(sat) is False


def test_a_reply_with_its_own_headings_is_still_verbatim(tmp_path):
    import nfl
    (tmp_path / "chat_transcript.md").write_text(
        "## 20:30 UTC -- release nfl-v1.22\n**User:** lineup?\n**Reply:**\n### The call\nStart Fannin.\n"
        "## 20:40 UTC -- release nfl-v1.22\n**User:** ok\n**Reply:** (as sent below)\n", encoding="utf-8")
    text = nfl.session_report(tmp_path).read_text(encoding="utf-8")
    assert "**Transcript: 1 of 2 entries" in text


def test_the_game_log_names_the_scoring_it_leaves_out():
    assert BX.not_counted({"rec": 0.5, "bonus_rec_yd_100": 3.0, "rush_yd": 0.1}) == ["bonus_rec_yd_100"]
    assert BX.not_counted({"rec": 0.5}) == []



# ------------------------------------------------------------------ season value

def test_the_season_value_is_the_waiver_consensus_per_game(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None, team=False: {})
    s = _snap(consensus={"5": {"mean": 170.0, "n": 3, "per_source": {"sleeper": 180.0, "espn": 170.0,
                                                                     "fantasypros": 160.0}}})
    row = A.season_line(s, "5")
    assert row == {"season_total": 170.0, "per_game": 10.0, "n": 3,
                   "per_source": {"sleeper": 180.0, "espn": 170.0, "fantasypros": 160.0}}
    assert A.season_line(s, "6") is None
    text = A.players(s, ["Puka Nacua"]).text
    assert "Season value (consensus of 3 sources" in text and "10.0 points a game, 170 on a full-season basis" in text


def test_a_consensus_failure_is_a_note_not_a_failed_snapshot(monkeypatch):
    from fantasy import snapshot as S
    monkeypatch.setattr(WV, "_consensus", lambda *a, **k: (_ for _ in ()).throw(OSError("espn down")))
    notes: list = []
    assert S.season_consensus({}, "omnibeta", 2026, {"1"}, __import__("core.manifest", fromlist=["Manifest"]).Manifest("t"),
                              notes) == {}
    assert notes == ["season consensus unavailable (OSError)"]


def test_an_older_snapshot_file_without_consensus_still_loads():
    import json
    from fantasy import snapshot as S
    d = _snap().to_json()
    d.pop("consensus", None)
    d.pop("rolled", None)
    back = S.Snapshot.from_json(json.loads(json.dumps(d, default=str)))
    assert back.consensus == {} and back.rolled is None


def test_the_season_value_names_a_missing_source_and_the_caveat_prints_once(monkeypatch):
    monkeypatch.setattr(A.EV, "for_sleeper", lambda pids, info, season, manifest=None, team=False: {})
    s = _snap(consensus={"5": {"mean": 136.0, "n": 2, "per_source": {"sleeper": 126.0, "espn": 146.0}},
                         "6": {"mean": 170.0, "n": 3, "per_source": {"sleeper": 1.0, "espn": 1.0, "fantasypros": 1.0}}})
    text = A.players(s, ["Puka Nacua", "Garrett Wilson"]).text
    assert "no fantasypros number for him" in text
    assert text.count("rescaled onto the full season") == 1


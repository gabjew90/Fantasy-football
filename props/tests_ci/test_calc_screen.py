"""The screen (props/calc/screen.py, DECISIONS #240): the window, the marks, the order, the journal rows
and the command end to end on a synthetic player (no network)."""
from __future__ import annotations

import datetime as dt
import sys
from argparse import Namespace
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from props.calc import __main__ as CLI  # noqa: E402
from props.calc import card, lines, screen as S, settings  # noqa: E402
from props.calc.checks import DataError  # noqa: E402
from test_calc_model import _games, _player, rush_model  # noqa: E402

STUB = {"player": "Test Back", "team": "DAL", "gsis_id": "00-1", "game_id": "2026_05_DAL_ARI", "week": 5,
        "season": 2026}
SHOWN = {"opp_row": {"value": 4.4, "games": 4, "plays": 60, "who": " to RBs"}, "grades": {"off": "B", "def": "C"},
         "qb_today": "", "game_lines": {"favorite": "ARI", "points": 3.0, "spread_text": "ARI -3", "total": 44.5},
         "why_no_lines": ""}


def _card(line, pl=None):
    pl = pl or _player(*_games())
    return pl, card.compute(pl, rush_model(ypc=4.2), "rush_yds", line, 1.8, 1.8, settings.load()["fixed"])


def _row(line, side, shown=SHOWN, pl=None):
    pl, c = _card(line, pl)
    other = card.value(c, "needed_under" if side == "over" else "needed_over")
    return S.side_row(pl, c, side, shown, STUB, other)


# ---------------------------------------------------------------- the window

def test_a_window_is_a_weekday_and_a_clock_hour_in_pacific_time():
    assert S.parse_window("Sun 1pm PT") == (6, 13, None)
    assert S.parse_window("sunday 1:25 PM") == (6, 13, 25)
    assert S.parse_window("Mon 17:15") == (0, 17, 15)
    assert S.parse_window("Thu 5:15pm pt") == (3, 17, 15)
    assert S.parse_window("Sun 12am PT")[1] == 0 and S.parse_window("Sun 12pm PT")[1] == 12
    for bad in ("1pm", "Sun", "Funday 1pm", "Sun 13pm", "Sun 25:00"):
        with pytest.raises(DataError):
            S.parse_window(bad)


def test_the_window_picks_its_games_and_the_soonest_slot_still_to_play():
    # 1:05 and 1:25 PM PT on Sun 2026-10-11 (20:05, 20:25 UTC), 10:00 AM PT, and next Sunday's 1:05
    sched = pd.DataFrame([
        {"season": 2026, "week": 5, "game_id": "a", "kickoff_utc": "2026-10-11T20:05:00+00:00", "away_team": "DEN", "home_team": "LAC"},
        {"season": 2026, "week": 5, "game_id": "b", "kickoff_utc": "2026-10-11T20:25:00+00:00", "away_team": "DET", "home_team": "ARI"},
        {"season": 2026, "week": 5, "game_id": "c", "kickoff_utc": "2026-10-11T17:00:00+00:00", "away_team": "NE", "home_team": "BUF"},
        {"season": 2026, "week": 6, "game_id": "d", "kickoff_utc": "2026-10-18T20:05:00+00:00", "away_team": "SF", "home_team": "SEA"}])
    sat = dt.datetime(2026, 10, 10, 12, tzinfo=dt.timezone.utc)
    assert list(S.window_games(sched, 2026, None, (6, 13, None), sat)["game_id"]) == ["a", "b"]
    assert list(S.window_games(sched, 2026, None, (6, 13, 25), sat)["game_id"]) == ["b"]
    monday = dt.datetime(2026, 10, 12, 12, tzinfo=dt.timezone.utc)
    assert list(S.window_games(sched, 2026, None, (6, 13, None), monday)["game_id"]) == ["d"], "the next one to play"
    assert list(S.window_games(sched, 2026, 5, (6, 13, None), monday)["game_id"]) == ["a", "b"], "a past week on request"
    with pytest.raises(DataError, match="give --week"):
        S.window_games(sched, 2026, None, (0, 13, None), monday)
    assert S.clock("2026-10-11T20:05:00+00:00") == "Sun 1:05 PM PT"


# ---------------------------------------------------------------- the marks and the order

def test_grades_order_from_s_plus_down_to_f_minus():
    order = ["S+", "S", "S-", "A+", "A", "A-", "B", "C-", "D+", "F-"]
    assert [S.grade_rank(g) for g in order] == sorted(S.grade_rank(g) for g in order)
    assert S.grade_rank("Only 2 games.") is None and S.grade_rank("") is None
    odd = dict(SHOWN, grades={"off": "?", "def": "B"})
    assert {n: m for n, m, _ in _row(40.5, "over", odd)["marks"]}["grades"] == "–", "not a grade: no data, no crash"


def test_an_over_with_his_workload_at_the_bar_and_every_mark_agreeing():
    pl, _ = _card(40.5)
    r = _row(40.5, "over", pl=pl)              # bar ~11 carries, his last 4 average 15.5, needed 3.0 a carry
    swing = max(float(pl.window["carries"].std(ddof=1)), 1.0)
    assert r["passes"] and r["gap"] == pytest.approx(4.5) and r["cushion"] == pytest.approx(4.5 / swing)
    assert S.cushion_text(r) == f"+4.5 carries, {card.d1(4.5 / swing)} of his swing"
    assert [(n, m) for n, m, _ in r["marks"]] == [("consistency", "✓"), ("season rate", "✓"), ("opponent", "✓"),
                                                  ("grades", "✓")]
    marks = {n: t for n, _, t in r["marks"]}
    assert marks["consistency"] == "✓ 4 of 4 at 11+"
    assert marks["season rate"] == "✓ 3.9 (4 g, 60 carries)" and marks["opponent"] == "✓ 4.4 (4 g, 60 plays)"
    assert r["longer"] == "4.2 vs 3.0 needed (5 g, 200 carries)" and r["workload"] == "15.5 avg vs ~11 carries"
    assert r["flags"] == ["tight line"], "the two bars (~11 and ~10) are within one carry"


def test_each_mark_disagrees_or_has_no_data_on_its_own_terms():
    r = _row(55.5, "over")                     # bar ~15: 2 of 4 games at 15+, needed 4.1 above his season 3.9
    assert r["passes"]
    marks = {n: (m, t) for n, m, t in r["marks"]}
    assert marks["consistency"] == ("✗", "✗ 2 of 4 at 15+"), "half is not more than half"
    assert marks["season rate"][0] == "✗"
    thin = dict(SHOWN, opp_row={"value": None, "games": 2, "thin": True}, grades={"note": "Only 2 games."})
    r = _row(55.5, "over", thin)
    marks = {n: (m, t) for n, m, t in r["marks"]}
    assert marks["opponent"] == ("–", "– only 2 games") and marks["grades"] == ("–", "– no grades yet")
    pl = _player(*_games())
    pl.rates["ypc"] = type(pl.rates["ypc"])(4.2, 4.4, 200, 3.9, 5, 4.3)          # 5 carries: below the minimum
    assert {n: m for n, m, _ in _row(55.5, "over", pl=pl)["marks"]}["season rate"] == "–"
    even = dict(SHOWN, grades={"off": "C", "def": "C"})
    assert {n: m for n, m, _ in _row(40.5, "over", even)["marks"]}["grades"] == "✗", "equal grades disagree"


def test_an_under_mirrors_every_check():
    pl, _ = _card(75.5)
    r = _row(75.5, "under", pl=pl)             # bar ~18 or fewer, his average 15.5
    assert r["passes"] and r["cushion"] == pytest.approx(2.5 / max(float(pl.window["carries"].std(ddof=1)), 1.0))
    marks = {n: (m, t) for n, m, t in r["marks"]}
    assert marks["consistency"] == ("✗", "✗ 2 of 4 at 18 or fewer")          # 12, 12 at or under; 19, 19 over
    assert marks["season rate"][0] == "✓" and marks["opponent"][0] == "✓"     # 3.9 and 4.4 at or below 4.9
    assert marks["grades"][0] == "✗", "an Under wants the defense graded above the offense"
    assert not _row(64.5, "under")["passes"], "bar ~15 or fewer against an average of 15.5"


def test_a_starter_ruled_out_is_flagged_by_name_and_his_offense_grade_is_no_data():
    r = _row(40.5, "over", dict(SHOWN, qb_today="Lamar Jackson ruled Out."))
    assert "Lamar Jackson (QB) ruled Out" in r["flags"]
    assert {n: (m, t) for n, m, t in r["marks"]}["grades"] == ("–", "– graded with Lamar Jackson, who is Out")


def test_short_history_and_an_unconfirmed_qb_are_flagged():
    season, window = _games()
    pl = _player(season.iloc[:2], window.iloc[:3])
    r = _row(40.5, "over", dict(SHOWN, qb_today="Starting QB not confirmed."), pl=pl)
    assert "short history" in r["flags"] and "QB not confirmed" in r["flags"]
    assert {n: t for n, _, t in r["marks"]}["consistency"] == "– 2 games"


def test_the_order_is_the_cushion_and_the_marks_only_break_ties():
    base = {"passes": True, "marks": []}
    rows = [dict(base, name="no evidence", x=0, ok=0, cushion=50.0),
            dict(base, name="four agree", x=0, ok=4, cushion=1.0),
            dict(base, name="one disagrees", x=1, ok=3, cushion=90.0),
            dict(base, name="tie, two agree", x=0, ok=2, cushion=40.0),
            dict(base, name="tie, one disagrees", x=1, ok=2, cushion=40.0),
            dict(base, name="short of the bar", x=0, ok=4, cushion=-5.0, passes=False),
            dict(base, name="under 4 games", x=0, ok=4, cushion=None)]
    assert [r["name"] for r in S.rank(rows)] == ["one disagrees", "no evidence", "tie, two agree",
                                                 "tie, one disagrees", "four agree", "under 4 games"]


def test_the_cushion_is_the_gap_over_his_swing_not_a_percent_of_the_bar():
    """DECISIONS #247: one target of room on a 2.5 bar printed +40% and outranked two targets on an 8
    bar (+28%). In his own swing (floored at 1 unit) the low line no longer wins on size alone."""
    low = {"market": "receptions", "gap": 1.0, "swing": 2.6, "cushion": 1.0 / 2.6}
    high = {"market": "receptions", "gap": 2.0, "swing": 2.3, "cushion": 2.0 / 2.3}
    assert S.cushion_text(low) == "+1 target, 0.4 of his swing"
    assert S.cushion_text(high) == "+2 targets, 0.9 of his swing"
    base = {"passes": True, "x": 0, "ok": 0}
    assert [r["gap"] for r in S.rank([dict(base, **low), dict(base, **high)])] == [2.0, 1.0]
    assert S.cushion_text({"market": "rush_yds", "gap": 3.0, "cushion": None}) == "+3 carries, n/a (under 4 games)"
    assert "% of the bar" not in S.ORDER and "percent of the bar" in S.TESTED


# ---------------------------------------------------------------- the record

def test_listed_legs_become_journal_rows_the_grader_reads():
    r = _row(40.5, "over")
    (j,) = S.journal_rows([r], "Sun 1pm PT")
    assert (j["market"], j["side"], j["line"], j["week"], j["status"]) == ("player_rush_yds", "over", 40.5, 5, "open")
    assert j["price"] == -125 and j["volume_unit"] == "carries" and j["id"] == "screen-2026-5-over-1"
    graded = [dict(j, status="graded", won=True, actual=61.0, result="over")]
    text = "\n".join(S.results(graded, [r]))
    assert "| Over | 1 | Test Back (DAL) · rushing yards Over 40.5 (-125) | 61.0 | won |" in text
    assert "Overs, top 3: 1 of 1 won (100%); the average break-even of those legs is 55.6%" in text


# ---------------------------------------------------------------- the command

@pytest.fixture
def one_window(monkeypatch):
    sched = pd.DataFrame([{"season": 2026, "week": 5, "game_id": STUB["game_id"], "away_team": "DAL",
                           "home_team": "ARI", "kickoff_utc": "2099-10-11T20:05:00+00:00"}])
    inj = pd.DataFrame([{"season": 2026, "week": 5, "team": "DAL", "gsis_id": "00-1", "full_name": "Test Back",
                         "position": "RB", "report_status": "Questionable", "practice_status": ""},
                        {"season": 2026, "week": 5, "team": "ARI", "gsis_id": "00-9", "full_name": "Hurt Guy",
                         "position": "WR", "report_status": "Out", "practice_status": ""}])
    bundle = type("B", (), {"schedule": sched, "rosters": None, "manifest": None})()
    monkeypatch.setattr(CLI, "_bundle", lambda season, fixed: (bundle, ""))
    monkeypatch.setattr(CLI.data, "injuries", lambda season, manifest=None: inj)
    monkeypatch.setattr(lines.LineLookup, "__init__", lambda self, *a, **k: None)
    monkeypatch.setattr(lines.LineLookup, "posted", lambda self, g: (
        [{"player": "Test Back", "gsis_id": "00-1", "team": "DAL", "market": "rush_yds"}], 0, []))
    built = []

    def fake_card(b, name, market, side, **kw):
        built.append(side)
        pl, c = _card(40.5)
        return {"stub": STUB, "ready": True, "not_enough": False, "c": c, "pl": pl, "shown": SHOWN,
                "text": f"TEXT CARD {side}", "md": f"MD CARD WITH MATCHUP {side}", "md_game": f"MD CARD {side}"}
    monkeypatch.setattr(CLI, "build_card", fake_card)
    monkeypatch.setattr(CLI, "_week_lines", lambda season, week: ({("DAL", "ARI"): SHOWN["game_lines"]}, ""))
    return built


def _screen_args(**kw):
    return Namespace(**{**dict(window="Sun 1pm PT", game=None, season=2026, week=None, format="md", grade=False), **kw})


def test_the_screen_prints_its_caveats_tables_and_top_cards(one_window):
    out = CLI.screen(_screen_args())
    assert out.startswith("**Smallest ask at the price · Sun 1pm PT · week 5**")
    for must in ("This lists only legs where his recent workload already meets the bar at the price.",
                 "Legs that depend on a role change", "Tested on 2026 weeks 2-5: legs on this list hit about 50%",
                 "This is a way to read the slate, not a list of likely winners.",
                 "Order: the cushion in his own swing, biggest first"):
        assert must in out
    assert "ARI Out: Hurt Guy. Doubtful or Questionable: none." in out
    assert "DAL Out: none. Doubtful or Questionable: Test Back (Questionable)." in out
    assert "| DAL run offense vs ARI run defense |" in out and "| ARI pass offense vs DAL pass defense |" in out, \
        "all four unit pairings, whatever legs are listed"
    assert "| 1 | Test Back (DAL) · rushing yards Over 40.5 (-125) |" in out
    assert "Questionable · tight line" in out, "his own status flags his row"
    assert "None: no leg on this side has his recent workload at the bar." in out    # the Under at 40.5
    assert "Sides not listed (an Over and an Under count separately): 1 recent workload short of the bar." in out
    assert "Lines not ranked" not in out and "Already kicked off" not in out
    assert "MD CARD over" in out and "MD CARD under" not in out
    after = out[out.index("MD CARD over"):]
    assert "**Screen checks**" in after and "| Consistency | ✓ 4 of 4 at 11+ |" in after, "the marks under the card"
    assert "| Flags | Questionable · tight line |" in after
    assert "**DAL at ARI** · " in out
    assert "Past week" not in out
    assert one_window == ["over", "over"], "one build per line, then the top cards"


def test_a_past_window_says_how_it_was_rebuilt_and_grades_through_the_journal(one_window, monkeypatch):
    from props.calc.shared import journal
    import props.calc.__main__ as M
    monkeypatch.setattr(M.dt, "datetime", type("D", (dt.datetime,), {
        "now": classmethod(lambda cls, tz=None: dt.datetime(2100, 1, 1, tzinfo=dt.timezone.utc))}))

    def fake_grade(season, stats=None, now=None):
        rows = journal.read(season)
        for r in rows:
            r.update(status="graded", won=False, actual=12.0, result="under")
        journal.write(season, rows)
        return {}
    monkeypatch.setattr(journal, "grade", fake_grade)
    keep = journal.JOURNAL_ROOT
    out = CLI.screen(_screen_args(week=5, grade=True))
    assert journal.JOURNAL_ROOT is keep, "the throwaway journal is put back"
    assert S.REPLAY in out and "| Over | 1 | Test Back (DAL) · rushing yards Over 40.5 (-125) | 12.0 | lost |" in out
    assert "Overs, top 3: 0 of 1 won (0%)" in out


def test_the_screen_needs_one_of_window_or_game(one_window):
    with pytest.raises(SystemExit, match="--window"):
        CLI.screen(_screen_args(window=None))
    with pytest.raises(SystemExit, match="--window"):
        CLI.screen(_screen_args(game="DAL@ARI"))


def test_a_live_window_names_and_leaves_out_its_games_already_started(one_window, monkeypatch):
    import props.calc.__main__ as M
    sched = pd.DataFrame([
        {"season": 2026, "week": 5, "game_id": "early", "away_team": "DEN", "home_team": "LAC",
         "kickoff_utc": "2026-10-11T20:05:00+00:00"},
        {"season": 2026, "week": 5, "game_id": STUB["game_id"], "away_team": "DAL", "home_team": "ARI",
         "kickoff_utc": "2026-10-11T20:25:00+00:00"}])
    bundle = type("B", (), {"schedule": sched, "rosters": None, "manifest": None})()
    monkeypatch.setattr(M, "_bundle", lambda season, fixed: (bundle, ""))
    monkeypatch.setattr(M.dt, "datetime", type("D", (dt.datetime,), {      # 1:15 PM PT: the 1:05 game is on
        "now": classmethod(lambda cls, tz=None: dt.datetime(2026, 10, 11, 20, 15, tzinfo=dt.timezone.utc))}))
    out = CLI.screen(_screen_args())
    assert "Already kicked off, left out: DEN at LAC (Sun 1:05 PM PT)." in out
    assert "**DAL at ARI** · Sun 1:25 PM PT" in out and "**DEN at LAC**" not in out and S.REPLAY not in out


def test_the_opponent_rate_is_worked_out_once_per_team_and_position(monkeypatch):
    import props.calc.__main__ as M
    calls = []
    monkeypatch.setattr(M.opponent, "allows", lambda *a: calls.append(a[1:5]) or {"value": 4.0, "games": 4})
    b = type("B", (), {})()
    for _ in range(3):
        M._opp_allows(b, "rush_yds", "ARI", "RB", 2026, 5, {})
    M._opp_allows(b, "rec_yds", "ARI", "WR", 2026, 5, {})
    assert calls == [("rush_yds", "ARI", "RB", 2026), ("rec_yds", "ARI", "WR", 2026)]


def test_the_release_comes_from_the_chat_stamp_first(tmp_path, monkeypatch):
    import props.calc.__main__ as M
    root = tmp_path / "nfl-v9.9"
    (root / "props" / "calc").mkdir(parents=True)
    (tmp_path / "nfl-v9.9.stamp.json").write_text('{"release_tag": "nfl-v9.9"}', encoding="utf-8")
    monkeypatch.setattr(M, "__file__", str(root / "props" / "calc" / "__main__.py"))
    assert M._release() == "nfl-v9.9"
    (tmp_path / "nfl-v9.9.stamp.json").unlink()
    assert M._release() == "unknown"
    (root / "nfl.lock.json").write_text('{"tag": "nfl-v1.0"}', encoding="utf-8")
    assert M._release() == "nfl-v1.0"


def test_the_game_header_names_a_grade_earned_with_a_quarterback_who_is_out(monkeypatch):
    import props.calc.__main__ as M
    g = pd.Series({"season": 2026, "week": 5, "game_id": "g", "away_team": "BAL", "home_team": "ATL",
                   "kickoff_utc": "2099-10-12T00:20:00+00:00"})
    monkeypatch.setattr(M, "_game_line", lambda *a: ({"favorite": "ATL", "points": 3.5, "spread_text": "ATL -3.5",
                                                     "total": 43.5}, ""))
    monkeypatch.setattr(M, "qb_today", lambda b, t, s, w: "Lamar Jackson ruled Out." if t == "BAL" else "")
    grades = {("BAL", "run"): ("A-", "S+"), ("BAL", "pass"): ("S+", "A-"), ("ATL", "run"): ("S-", "C"),
              ("ATL", "pass"): ("D+", "B-")}
    monkeypatch.setattr(M.matchup, "grade_pair", lambda b, off, dfn, kind, *a: dict(zip(("off", "def"), grades[(off, kind)])))
    monkeypatch.setattr(M, "_injuries", lambda b, s: pd.DataFrame(columns=["week", "team", "report_status", "full_name"]))
    L = M.game_header(type("B", (), {})(), g, 2026, {}, dt.datetime(2026, 10, 11, tzinfo=dt.timezone.utc))
    assert L[0] == "**BAL at ATL** · Sun 5:20 PM PT · Atlanta favored by 3.5. Total 43.5."
    assert "| BAL run offense vs ATL run defense | A- vs S+ (graded with Lamar Jackson, who is Out) |" in L
    assert "| BAL pass offense vs ATL pass defense | S+ vs A- (graded with Lamar Jackson, who is Out) |" in L
    assert "| ATL run offense vs BAL run defense | S- vs C |" in L and "BAL quarterback: Lamar Jackson ruled Out." in L
    assert "BAL: the week's injury report is not out yet." in L


def test_a_player_ruled_out_is_named_and_never_ranked(one_window, monkeypatch):
    out_inj = pd.DataFrame([{"season": 2026, "week": 5, "team": "DAL", "gsis_id": "00-1", "full_name": "Test Back",
                             "position": "RB", "report_status": "Out", "practice_status": ""}])
    monkeypatch.setattr(CLI.data, "injuries", lambda season, manifest=None: out_inj)
    out = CLI.screen(_screen_args())
    assert "Not listed, ruled Out: Test Back (rushing yards)." in out
    assert "| 1 | Test Back" not in out and "MD CARD" not in out, "no row and no card for a player who is out"


def test_no_saved_line_for_the_week_says_so_and_fails(one_window, monkeypatch):
    """DECISIONS #246: with nothing saved (a capture made under another release used to be invisible),
    the screen said "no leg at the bar" and "nothing to grade"; it now says no line is saved and exits non-zero."""
    monkeypatch.setattr(lines.LineLookup, "posted", lambda self, g: ([], 0, []))
    with pytest.raises(SystemExit) as ex:
        CLI.screen(_screen_args(grade=True))
    assert "No Sleeper lines are saved" in str(ex.value) and "nothing to screen or grade" in str(ex.value)
    assert ex.value.code not in (0, None)


def test_a_leg_whose_game_is_not_posted_reads_not_posted_yet():
    pl, c = _card(40.5)
    r = _row(40.5, "over", pl=pl)
    text = "\n".join(S.results([dict(S.journal_rows([r], "w")[0], status="open")], [r]))
    assert "| not posted yet |" in text and "the results are not posted yet" in text


def test_captures_left_inside_an_earlier_release_folder_are_read(tmp_path, monkeypatch):
    monkeypatch.delenv("NFL_CALC_LINES", raising=False)
    root = tmp_path / "nfl-release"
    new, old = root / "nfl-v1.81", root / "nfl-v1.80"
    (old / "props" / "calc" / "lines").mkdir(parents=True)
    new.mkdir()
    (root / "nfl-v1.81.stamp.json").write_text("{}", encoding="utf-8")
    assert lines._earlier_release_lines(new) == [old / "props" / "calc" / "lines"]
    assert lines._earlier_release_lines(old) == [], "no stamp beside it: not a chat release"


# ---------------------------------------------------------------- the lineup check (DECISIONS #247)

def test_snap_marks_flag_far_fewer_and_far_more_snaps_than_his_other_games():
    from props.calc import player
    w = pd.DataFrame({"snap_pct": [0.40, 0.42, 0.18, 0.95, 0.41, None]})
    out = player.snap_marks(w, 0.5)
    assert list(out["fewer_snaps"]) == [False, False, True, False, False, False], "0.18 is under half his other games"
    assert list(out["more_snaps"]) == [False, False, False, True, False, False], "0.95 is over double"


def test_both_averages_print_and_the_gate_names_a_leg_the_marked_games_carry():
    pl, c = _card(40.5)                        # bar ~11 carries, his last 4 average 15.5 (two 19s, two 12s)
    win = pl.window.copy()
    win["more_snaps"] = False
    win["fewer_snaps"] = False
    last = win.tail(4)
    win.loc[last.index[last["carries"] == 19], "more_snaps"] = True     # mark the two 19-carry games: 12 and 12 remain
    pl.window = win
    pl.lineup = ["2 of his last 4 came with Lead Back out. Back is active."]
    P = card._parts(pl, c, "over")
    assert P["marked"] == 2 and P["usual_clean"] == pytest.approx(12.0) and P["n_clean"] == 2
    text = card.render(pl, c, "over", opp="ARI")
    assert "(avg 15.5; 12.0 without the 2 marked games)" in text
    assert "Short history: 2 games without the marked ones." in text
    assert "2 of his last 4 came with Lead Back out." in text
    r = S.side_row(pl, c, "over", SHOWN, STUB, card.value(c, "needed_under"))
    assert r["passes"], "12 still meets an ~11 bar: listed"
    assert r["gap"] == pytest.approx(12.0 - card.shown_work(card.value(c, "needed_over")))
    assert "lineup check: 2 of 4 marked" in r["flags"] and "short history" in r["flags"]
    pl2, c2 = _card(50.5)                      # bar ~14: the 15.5 average meets it, the 12.0 does not
    pl2.window, pl2.lineup = win, pl.lineup
    r2 = S.side_row(pl2, c2, "over", SHOWN, STUB, card.value(c2, "needed_under"))
    assert r2["lineup_out"] and not r2["passes"]
    assert "his last-4 average is 15.5 but 12.0 without the 2 marked games" in r2["lineup_out"]
    assert "Lead Back out" in r2["lineup_out"]


def test_a_main_teammate_out_in_a_marked_game_is_named(monkeypatch):
    from props.calc import player
    last = pd.DataFrame({"season": [2026] * 4, "week": [1, 2, 3, 4], "game_id": ["g1", "g2", "g3", "g4"],
                         "fewer_snaps": [False] * 4, "more_snaps": [False, True, True, False]})
    ros = pd.DataFrame([{"season": 2026, "week": w, "team": "LA", "gsis_id": "00-0000002", "full_name": "Puka Nacua",
                         "status": "ACT", "position": "WR"} for w in (1, 2, 3, 4, 5)])
    share = pd.DataFrame({"game_id": ["g1", "g4"], "gsis_id": ["00-0000002"] * 2, "offense_pct": [0.9, 0.9]})
    b = type("B", (), {"rosters": ros, "snap_share": share, "injury_report": lambda self, s: None})()
    monkeypatch.setattr(player, "main_teammates", lambda *a: ["00-0000002"])
    assert player.lineup_causes(b, last, "00-0000001", "LA", "WR", 2026, 5) == \
        ["2 of his last 4 came with Puka Nacua out. Nacua is active."]
    ir = ros.assign(status=["ACT", "ACT", "ACT", "ACT", "RES"])
    b2 = type("B", (), {"rosters": ir, "snap_share": share.assign(game_id=["g2", "g3"]),
                        "injury_report": lambda self, s: None})()
    assert player.lineup_causes(b2, last, "00-0000001", "LA", "WR", 2026, 5) == \
        ["2 of his last 4 came with Puka Nacua playing. Nacua is on injured reserve."]

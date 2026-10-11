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
    r = _row(40.5, "over")                     # bar ~11 carries, his last 4 average 15.5, needed 3.0 a carry
    assert r["passes"] and r["cushion"] == pytest.approx((15.5 - 11) / 11 * 100)
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
    r = _row(75.5, "under")                    # bar ~18 or fewer, his average 15.5
    assert r["passes"] and r["cushion"] == pytest.approx((18 - 15.5) / 18 * 100)
    marks = {n: (m, t) for n, m, t in r["marks"]}
    assert marks["consistency"] == ("✗", "✗ 2 of 4 at 18 or fewer")          # 12, 12 at or under; 19, 19 over
    assert marks["season rate"][0] == "✓" and marks["opponent"][0] == "✓"     # 3.9 and 4.4 at or below 4.9
    assert marks["grades"][0] == "✗", "an Under wants the defense graded above the offense"
    assert not _row(64.5, "under")["passes"], "bar ~15 or fewer against an average of 15.5"


def test_a_starter_ruled_out_is_flagged_by_name():
    r = _row(40.5, "over", dict(SHOWN, qb_today="Lamar Jackson ruled Out."))
    assert "Lamar Jackson (QB) ruled Out" in r["flags"]


def test_short_history_and_an_unconfirmed_qb_are_flagged():
    season, window = _games()
    pl = _player(season.iloc[:2], window.iloc[:3])
    r = _row(40.5, "over", dict(SHOWN, qb_today="Starting QB not confirmed."), pl=pl)
    assert "short history" in r["flags"] and "QB not confirmed" in r["flags"]
    assert {n: t for n, _, t in r["marks"]}["consistency"] == "– 2 games"


def test_the_order_is_fewest_disagreements_then_most_agreements_then_cushion():
    base = {"passes": True, "marks": []}
    rows = [dict(base, name="no evidence", x=0, ok=0, cushion=50.0),
            dict(base, name="four agree", x=0, ok=4, cushion=1.0),
            dict(base, name="one disagrees", x=1, ok=3, cushion=90.0),
            dict(base, name="two agree, big cushion", x=0, ok=2, cushion=40.0),
            dict(base, name="two agree, small cushion", x=0, ok=2, cushion=5.0),
            dict(base, name="short of the bar", x=0, ok=4, cushion=-5.0, passes=False)]
    assert [r["name"] for r in S.rank(rows)] == ["four agree", "two agree, big cushion", "two agree, small cushion",
                                                 "no evidence", "one disagrees"]


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
                "text": f"TEXT CARD {side}", "md": f"MD CARD {side}"}
    monkeypatch.setattr(CLI, "build_card", fake_card)
    return built


def _screen_args(**kw):
    return Namespace(**{**dict(window="Sun 1pm PT", game=None, season=2026, week=None, format="md", grade=False), **kw})


def test_the_screen_prints_its_caveats_tables_and_top_cards(one_window):
    out = CLI.screen(_screen_args())
    assert out.startswith("**Smallest ask at the price · Sun 1pm PT · week 5**")
    for must in ("This lists only legs where his recent workload already meets the bar at the price.",
                 "Legs that depend on a role change", "The ranking is untested against results",
                 "Order: fewest ✗, then most ✓, then the workload cushion as a percent of the bar."):
        assert must in out
    assert "- ARI: Hurt Guy" in out and "- DAL: none" in out, "one line per team, players ruled Out"
    assert "| 1 | Test Back (DAL) · rushing yards Over 40.5 (-125) |" in out
    assert "Questionable · tight line" in out, "his own status flags his row"
    assert "None: no leg on this side has his recent workload at the bar." in out    # the Under at 40.5
    assert "Sides not listed (an Over and an Under count separately): 1 recent workload short of the bar." in out
    assert "Lines not ranked" not in out and "Already kicked off" not in out
    assert "MD CARD over" in out and "MD CARD under" not in out
    after = out[out.index("MD CARD over"):]
    assert "**Screen checks**" in after and "| Consistency | ✓ 4 of 4 at 11+ |" in after, "the marks under the card"
    assert "| Flags | Questionable · tight line |" in after
    assert "Arizona favored by 3. Total 44.5." in out and "no card built" not in out
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
    assert "- DAL at ARI, Sun 1:25 PM PT: Arizona favored by 3. Total 44.5." in out and "DEN at LAC, Sun" not in out and S.REPLAY not in out


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

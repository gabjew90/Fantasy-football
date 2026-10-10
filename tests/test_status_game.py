"""`nfl.py status --game AWAY@HOME` (DECISIONS #235): the chat's game read takes the spread, the
total and both teams' injury report from here."""
from __future__ import annotations

import pandas as pd
import pytest

from core import status as ST

GAMES = [{"game": "LV@NE", "away": "LV", "home": "NE", "kickoff_utc": "2026-10-11T17:00:00+00:00", "started": False,
          "hours_to_kickoff": 42.0, "spread": "NE -3.5", "total": 45.5, "lines": 89},
         {"game": "LAR@WAS", "away": "LAR", "home": "WAS", "kickoff_utc": "2026-10-11T17:00:00+00:00",
          "started": False, "hours_to_kickoff": 42.0, "spread": "LAR -2.5", "total": 47.5, "lines": 70}]


def test_a_game_is_found_whatever_the_team_codes():
    assert ST.pick_game(GAMES, "lv@ne")["game"] == "LV@NE"
    assert ST.pick_game(GAMES, "LA@WSH")["game"] == "LAR@WAS", "nflverse's LA and ESPN's WSH"
    with pytest.raises(ValueError, match="no game NE@LV this week; the games are: LV@NE, LAR@WAS"):
        ST.pick_game(GAMES, "NE@LV")


def _report():
    return pd.DataFrame([
        dict(week=5, team="LV", full_name="Ashton Jeanty", position="RB", report_status="Questionable",
             practice_status="Did Not Participate In Practice", report_primary_injury="Ankle"),
        dict(week=5, team="LV", full_name="Jalen Nailor", position="WR", report_status="Out",
             practice_status="Did Not Participate In Practice", report_primary_injury="Hamstring"),
        dict(week=5, team="NE", full_name="Rhamondre Stevenson", position="RB", report_status="Questionable",
             practice_status="Limited Participation in Practice", report_primary_injury="Toe"),
        dict(week=5, team="NE", full_name="Healthy Guy", position="WR", report_status=None,
             practice_status="Full Participation in Practice", report_primary_injury=None),
        dict(week=5, team="NE", full_name="Sore Guy", position="TE", report_status=None,
             practice_status="Limited Participation in Practice", practice_primary_injury="Knee"),
        dict(week=4, team="LV", full_name="Last Week", position="WR", report_status="Out", practice_status=None),
        dict(week=5, team="KC", full_name="Other Game", position="WR", report_status="Out", practice_status=None),
        dict(week=5, team="LA", full_name="A Ram", position="WR", report_status="Doubtful", practice_status=None),
    ])


def test_the_injury_report_lists_both_teams_designations_first():
    rows = ST.game_injuries(_report(), 5, ("LV", "NE"))
    assert [(r["team"], r["player"], r["status"]) for r in rows] == [
        ("LV", "Jalen Nailor", "Out"), ("LV", "Ashton Jeanty", "Questionable"),
        ("NE", "Rhamondre Stevenson", "Questionable"), ("NE", "Sore Guy", None)]
    assert rows[-1]["injury"] == "Knee" and rows[-1]["practice"].startswith("Limited")
    assert ST.game_injuries(_report(), 5, ("LAR", "WAS"))[0]["player"] == "A Ram", "nflverse LA is the Rams"


def test_status_prints_the_game_and_its_injury_report():
    st = {"season": 2026, "week": 5, "games": GAMES[:1], "game": "LV@NE",
          "game_injuries": ST.game_injuries(_report(), 5, ("LV", "NE")),
          "injuries": {"rows": 8, "designations": 4}, "projections": {"published": True, "players": 365},
          "league": None}
    md = ST.markdown(st)
    assert "| LV@NE |" in md and "LAR@WAS" not in md
    assert "## Injury report -- LV@NE" in md
    assert "| LV | Jalen Nailor | WR | Out | Did Not Participate In Practice | Hamstring |" in md
    assert "| NE | Sore Guy | TE | no designation yet |" in md
    empty = ST.markdown({**st, "game_injuries": []})
    assert "No player on either team has a game designation" in empty
    broken = ST.markdown({**st, "game_injuries": None, "injuries": {"rows": 0, "designations": 0, "error": "HTTPError"}})
    assert "could not be read (HTTPError)" in broken
    assert "Injury report" not in ST.markdown({**st, "game": None, "games": GAMES})

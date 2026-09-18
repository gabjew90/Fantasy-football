"""The two join conventions that failed silently (found 2026-09-17).

NAMES. Sleeper's `position` is the depth-chart slot and `fantasy_positions`
is what a player is eligible at, so matching on `position` lost Travis
Hunter (DB / fantasy WR) and every fullback (FB / fantasy RB). Retired
namesakes also made live players "ambiguous" and dropped them.

TEAMS. The schedule carries draftkit codes (SFO, NOS, GBP...) and rosters
carry Sleeper codes (SF, NO, GB...). Nothing converted, so for eight
franchises every schedule-to-roster match was empty: no inactives check was
scheduled for them and they never appeared in a lock time.
"""

from datetime import datetime, timezone

import polars as pl
import pytest

from draftkit import defense, seasondata
from draftkit.ids import NameIndex
from manager import triggers
from manager.games import week_games

PLAYERS = {
    "12530": {"full_name": "Travis Hunter", "position": "DB",
              "fantasy_positions": ["DB", "WR"], "team": "JAX", "active": True},
    "1379": {"full_name": "Kyle Juszczyk", "position": "FB",
             "fantasy_positions": ["RB"], "team": "SF", "active": True},
    "12547": {"full_name": "Kyle Williams", "position": "WR",
              "fantasy_positions": ["WR"], "team": "NE", "active": True},
    "7437": {"full_name": "Kyle Williams", "position": "WR",
             "fantasy_positions": ["WR"], "team": None, "active": False},
    "638": {"full_name": "Kyle Williams", "position": "WR",
            "fantasy_positions": ["WR"], "team": None, "active": False},
    "9a": {"full_name": "Mike Williams", "position": "WR",
           "fantasy_positions": ["WR"], "team": "NYJ", "active": True},
    "9b": {"full_name": "Mike Williams", "position": "WR",
           "fantasy_positions": ["WR"], "team": "PIT", "active": True},
    "SF": {"first_name": "San Francisco", "last_name": "49ers",
           "position": "DEF", "team": "SF", "active": True},
}


@pytest.fixture
def idx():
    return NameIndex(PLAYERS)


# -------------------------------------------------------------------- names

def test_a_two_way_player_matches_on_fantasy_eligibility_not_the_depth_chart(idx):
    """Travis Hunter is position DB. A feed calling him a WR is right, and
    matching on `position` dropped the largest unmatched row in the feed."""
    assert idx.resolve("Travis Hunter", "WR") == "12530"
    assert idx.resolve("Travis Hunter", "DB") == "12530"


def test_a_fullback_matches_as_the_rb_he_is_eligible_at(idx):
    assert idx.resolve("Kyle Juszczyk", "RB") == "1379"


def test_a_retired_namesake_does_not_hide_the_live_player(idx):
    """Three Kyle Williamses, two of them inactive with no team. The live
    New England receiver was being dropped as ambiguous."""
    assert idx.resolve("Kyle Williams", "WR") == "12547"


def test_a_namesake_pair_is_split_by_team_when_the_feed_gives_one(idx):
    assert idx.resolve("Mike Williams", "WR", "NYJ") == "9a"
    assert idx.resolve("Mike Williams", "WR", "PIT") == "9b"


def test_two_live_players_with_no_tiebreak_are_dropped_not_guessed(idx):
    """The rule that protects the lineup: a wrong match shows up as a change
    nobody ordered, so ambiguity stays unresolved."""
    assert idx.resolve("Mike Williams", "WR") is None
    assert idx.resolve("Mike Williams", "WR", "LAC") is None


def test_a_wrong_position_still_misses_and_an_unknown_name_too(idx):
    assert idx.resolve("Travis Hunter", "TE") is None
    assert idx.resolve("Nobody At All", "WR") is None


def test_suffixes_and_punctuation_still_normalise():
    i = NameIndex({"1": {"full_name": "Marvin Harrison Jr.", "position": "WR",
                         "fantasy_positions": ["WR"], "team": "ARI", "active": True},
                   "2": {"full_name": "A.J. Brown", "position": "WR",
                         "fantasy_positions": ["WR"], "team": "PHI", "active": True}})
    assert i.resolve("Marvin Harrison", "WR") == "1"
    assert i.resolve("AJ Brown", "WR") == "2"


def test_defences_join_on_team_and_through_an_alias(idx):
    assert idx.defense("SF") == "SF"
    assert idx.defense("SFO") is None                      # not an alias it knows
    assert idx.defense("WSH", {"WSH": "WAS"}) is None       # no WAS defence here
    assert idx.defense("SF", {"SFO": "SF"}) == "SF"


def test_an_index_missing_both_position_fields_is_skipped_not_crashed():
    i = NameIndex({"1": {"full_name": "No Position"}, "2": "not a dict",
                   "3": {"position": "WR"}})
    assert i.resolve("No Position", "WR") is None
    assert i.by_name == {}


# -------------------------------------------------------------------- teams

def _schedule():
    rows = [("SFO", "SEA", "2026-09-20", "16:25"), ("SEA", "SFO", "2026-09-20", "16:25"),
            ("NOS", "ATL", "2026-09-20", "13:00"), ("ATL", "NOS", "2026-09-20", "13:00"),
            ("GBP", "CHI", "2026-09-18", "20:15"), ("CHI", "GBP", "2026-09-18", "20:15")]
    return pl.DataFrame(
        {"week": [2] * 6,
         "team": [r[0] for r in rows], "opp": [r[1] for r in rows],
         "gameday": [r[2] for r in rows], "gametime": [r[3] for r in rows]})


def test_week_games_emits_the_codes_rosters_use():
    games = week_games(_schedule(), 2)
    teams = {t for g in games for t in g["teams"]}
    assert teams == {"SF", "SEA", "NO", "ATL", "GB", "CHI"}
    assert not {"SFO", "NOS", "GBP"} & teams
    assert len(games) == 3, "one game per pairing, not one per team-row"


def test_a_roster_team_now_intersects_the_schedule():
    """The actual defect: frozenset({'SFO'}) & {'SF'} was empty, so three
    San Francisco players had no inactives check all season."""
    games = week_games(_schedule(), 2)
    mine = {"SF", "NO"}
    hits = [sorted(g["teams"] & mine) for g in games if g["teams"] & mine]
    assert hits == [["NO"], ["SF"]], "New Orleans kicks off before San Francisco"


def test_the_planner_schedules_a_slate_for_those_teams():
    games = week_games(_schedule(), 2)
    slates = triggers.relevant_slates(games, {"SF"}, {"NO"})
    covered = {t for s in slates for t in s["teams"]}
    assert covered == {"SF", "NO"}


def test_the_code_maps_are_inverses_and_leave_normalised_spellings_alone():
    for dk, sl in seasondata.SLEEPER_CODE.items():
        assert seasondata.to_sleeper(dk) == sl
        assert seasondata.to_draftkit(sl) == dk
    # LA/WSH/JAX are spellings normalised on the way in, not draftkit codes:
    # inverting them would turn LAR into LA.
    assert seasondata.to_sleeper("LAR") == "LAR"
    assert seasondata.to_sleeper("WAS") == "WAS"
    assert seasondata.to_draftkit("LAR") == "LAR"
    assert seasondata.to_sleeper("") == "" and seasondata.to_draftkit("") == ""
    assert seasondata.to_sleeper("sfo") == "SF", "case is not the caller's problem"


def test_vegas_aliases_are_the_shared_map():
    from manager import vegas
    assert vegas.ALIASES is seasondata.SLEEPER_CODE


def test_playoff_schedule_strength_finds_a_sleeper_coded_team():
    """defense.schedule_strength filtered the schedule with a roster code,
    so those eight teams always reported 'bye-heavy or unscheduled'."""
    sched = pl.DataFrame({"week": [15, 16, 17],
                          "team": ["SFO", "SFO", "SFO"],
                          "opp": ["SEA", "NOS", "ARI"]})
    ratio, label = defense.schedule_strength(None, sched, "SF", "WR", (15, 16, 17), 5.0)
    assert ratio is None, "no points-allowed frame, so no number"
    assert label == "wk15 vs SEA; wk16 vs NO; wk17 vs ARI"
    assert "unscheduled" not in label


# ------------------------------------------------- the ambiguity diagnostic

def test_candidates_are_position_eligible_so_a_miss_is_not_ambiguity(idx):
    """The counter fix: two receivers named Mike Williams make that name
    ambiguous for a WR, but for a TE there is no candidate at all -- that is
    unmatched, and calling it ambiguous hid position misses in the only
    diagnostic that reveals a join regression."""
    assert sorted(idx.candidates("Mike Williams", "WR")) == ["9a", "9b"]
    assert idx.candidates("Mike Williams", "TE") == []
    assert sorted(idx.candidates("Mike Williams")) == ["9a", "9b"]
    # eligibility, not the depth chart: Hunter is position DB
    assert idx.candidates("Travis Hunter", "WR") == ["12530"]


def test_fantasypros_counts_a_position_miss_as_unmatched(monkeypatch):
    """A name two WRs share, offered as a TE, must land in `unmatched`."""
    from manager import fantasypros as fp
    index = {
        "9a": {"full_name": "Mike Williams", "position": "WR",
               "fantasy_positions": ["WR"], "team": "NYJ", "active": True},
        "9b": {"full_name": "Mike Williams", "position": "WR",
               "fantasy_positions": ["WR"], "team": "PIT", "active": True},
    }

    def _rows(pos, slug, season, kind, week=None):
        if pos == "TE":
            return [{"player_name": "Mike Williams", "player_team_id": "LAC",
                     "r2p_pts": "90.0"}], {}
        return [], {}
    monkeypatch.setattr(fp, "_rows", _rows)
    out, note = fp.fetch({}, 2026, index)
    assert out == {}
    assert "1 unmatched" in note
    assert "ambiguous" not in note, "a position miss is not ambiguity"


def test_fantasypros_still_counts_a_real_live_tie_as_ambiguous(monkeypatch):
    from manager import fantasypros as fp
    index = {
        "9a": {"full_name": "Mike Williams", "position": "WR",
               "fantasy_positions": ["WR"], "team": "NYJ", "active": True},
        "9b": {"full_name": "Mike Williams", "position": "WR",
               "fantasy_positions": ["WR"], "team": "PIT", "active": True},
    }

    def _rows(pos, slug, season, kind, week=None):
        if pos == "WR":
            return [{"player_name": "Mike Williams", "player_team_id": "LAC",
                     "r2p_pts": "90.0"}], {}
        return [], {}
    monkeypatch.setattr(fp, "_rows", _rows)
    out, note = fp.fetch({}, 2026, index)
    assert out == {} and "1 ambiguous" in note

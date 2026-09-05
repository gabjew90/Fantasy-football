"""A two-way player (Sleeper position DB, fantasy_positions [DB, WR]) must
match a WR source line: the sheet carried Travis Hunter and the board called
him UNPROJECTED (2026-09-04)."""

from draftkit.ids import SleeperIndex


def _universe():
    return {
        "1": {"full_name": "Travis Hunter", "position": "DB", "fantasy_positions": ["DB", "WR"], "team": "JAX", "active": True},
        "2": {"full_name": "Brian Thomas", "position": "WR", "fantasy_positions": ["WR"], "team": "JAX", "active": True},
        "3": {"full_name": "Some Corner", "position": "CB", "fantasy_positions": ["DB"], "team": "JAX", "active": True},
    }


def test_two_way_player_matches_under_his_fantasy_position():
    idx = SleeperIndex(_universe())
    assert idx.match("Travis Hunter", "WR", "JAX") == "1"
    assert idx.match("Brian Thomas", "WR", "JAX") == "2"


def test_pure_defenders_stay_out_of_the_offensive_buckets():
    idx = SleeperIndex(_universe())
    assert idx.match("Some Corner", "WR", "JAX") is None
    assert "DB" not in idx.by_pos


def test_primary_holder_wins_a_name_collision_with_a_secondary_claimant():
    u = _universe()
    u["4"] = {"full_name": "Travis Hunter", "position": "WR", "fantasy_positions": ["WR"], "team": "FA", "active": True}
    idx = SleeperIndex(u)
    assert idx.match("Travis Hunter", "WR", None) == "4"

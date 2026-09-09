"""The FantasyPros feed, and the rescale defect that adding it would have hit."""

from __future__ import annotations

import pytest

from manager import consensus, fantasypros as fp


class Cfg(dict):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.league_name = kw.pop("league_name", "x")

    def get(self, k, d=None):
        return dict.get(self, k, d)


INDEX = {
    "1": {"full_name": "Bijan Robinson", "position": "RB", "team": "ATL"},
    "2": {"full_name": "Tyler Warren", "position": "TE", "team": "IND"},
    "3": {"full_name": "Eddy Pineiro", "position": "K", "team": "SF"},
    "MIN": {"first_name": "Minnesota", "last_name": "Vikings",
            "position": "DEF", "team": "MIN"},
    "9a": {"full_name": "Mike Williams", "position": "WR", "team": "NYJ"},
    "9b": {"full_name": "Mike Williams", "position": "WR", "team": "PIT"},
}


def _feed(monkeypatch, rows_by_pos, updated="9/09", experts=3):
    def _rows(pos, slug, season, kind, week=None):
        return list(rows_by_pos.get(pos, [])), {
            "last_updated": updated, "total_experts": experts}
    monkeypatch.setattr(fp, "_rows", _rows)


# ------------------------------------------------------------------ scoring

@pytest.mark.parametrize("rec,slug", [
    (1.0, "PPR"), (0.75, "PPR"), (0.5, "HALF"), (0.25, "HALF"),
    (0.0, "STD"), (None, "STD"),
])
def test_the_scoring_preset_follows_the_league_reception_value(rec, slug):
    assert fp.scoring_slug({"rec": rec} if rec is not None else {}) == slug


def test_an_unusual_reception_value_still_picks_the_nearest_preset():
    """FantasyPros publishes three presets and nothing between them.

    A 0.6-PPR league is closer to half than to full, and serving it a full-PPR
    number would move every pass-catcher by tens of points while looking like
    a projection change rather than a units mismatch.
    """
    assert fp.scoring_slug({"rec": 0.6}) == "HALF"


# -------------------------------------------------------------- name/id join

def test_defences_join_on_team_because_sleeper_keys_them_that_way(monkeypatch):
    _feed(monkeypatch, {"DST": [{"player_name": "Minnesota Vikings",
                                 "player_team_id": "MIN", "r2p_pts": "103.4",
                                 "rank_ecr": 6}]})
    rows, note = fp.fetch({}, 2026, INDEX)
    assert rows["MIN"]["pts"] == 103.4 and rows["MIN"]["pos"] == "DEF"


def test_a_franchise_the_two_feeds_spell_differently_still_joins(monkeypatch):
    idx = {"JAX": {"first_name": "Jacksonville", "last_name": "Jaguars",
                   "position": "DEF", "team": "JAX"}}
    _feed(monkeypatch, {"DST": [{"player_name": "Jacksonville Jaguars",
                                 "player_team_id": "JAC", "r2p_pts": "90.0"}]})
    rows, _ = fp.fetch({}, 2026, idx)
    assert "JAX" in rows, "JAC/JAX alias not applied"


def test_an_ambiguous_name_is_dropped_rather_than_guessed(monkeypatch):
    """Two Mike Williamses at WR. A wrong match does not surface as a missing
    player, it surfaces as a lineup change nobody ordered."""
    _feed(monkeypatch, {"WR": [{"player_name": "Mike Williams",
                                "player_team_id": "NYJ", "r2p_pts": "150.0"}]})
    rows, note = fp.fetch({}, 2026, INDEX)
    assert "9a" not in rows and "9b" not in rows
    assert "1 ambiguous" in note


def test_every_position_is_asked_for_including_k_and_def(monkeypatch):
    asked = []

    def _rows(pos, slug, season, kind, week=None):
        asked.append(pos)
        return [], {"last_updated": "9/09"}
    monkeypatch.setattr(fp, "_rows", _rows)
    fp.fetch({}, 2026, INDEX)
    assert set(asked) == {"QB", "RB", "WR", "TE", "K", "DST"}, (
        "K and DEF are the coverage this source exists to add")


# ------------------------------------------------------------------ degrade

def test_no_player_index_means_no_network_call_at_all(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("fetched with no index to match against")
    monkeypatch.setattr(fp, "_rows", _boom)
    rows, note = fp.fetch({}, 2026, {})
    assert rows == {} and "DATA MISSING" in note


def test_an_unreachable_feed_is_data_missing_not_an_exception(monkeypatch):
    def _rows(*a, **k):
        raise TimeoutError("slow")
    monkeypatch.setattr(fp, "_rows", _rows)
    rows, note = fp.fetch({}, 2026, INDEX)
    assert rows == {} and note.startswith("DATA MISSING")
    assert "TimeoutError" in note


def test_points_drops_rows_the_feed_has_no_number_for(monkeypatch):
    _feed(monkeypatch, {"RB": [
        {"player_name": "Bijan Robinson", "r2p_pts": "378.0"},
        {"player_name": "Tyler Warren", "r2p_pts": None}]})
    pts, _ = fp.points({}, 2026, INDEX)
    assert pts == {"1": 378.0}


def test_ranks_come_back_as_ranks_where_lower_is_better(monkeypatch):
    _feed(monkeypatch, {"RB": [{"player_name": "Bijan Robinson", "rank_ecr": 2,
                                "rank_min": "1", "rank_max": "3",
                                "rank_std": "0.42", "tier": 1,
                                "r2p_pts": "378.0"}]})
    r = fp.fetch({}, 2026, INDEX, kind=fp.DRAFT)[0]["1"]
    assert r["best"] == 1 and r["worst"] == 3 and r["best"] < r["worst"]
    assert r["tier"] == 1


# ----------------------------------------------- the rescale basis it changes

def test_a_partial_source_does_not_shrink_the_basis_for_the_others(monkeypatch):
    """THE DEFECT ADDING THIS SOURCE WOULD HAVE HIT.

    build() used to fit every source's scale on the GLOBAL intersection, so
    the smallest source set the population for all of them -- the draft sheet
    did exactly this once, fitting ESPN's ratio on 232 startable players and
    extrapolating it to the wire. FantasyPros covers K and DEF that Sleeper is
    never asked for, and here it carries only 45 of the 60. ESPN must still
    be fitted on its own 60-player overlap, not on FantasyPros' 45.
    """
    hi = {str(i): 100.0 + i for i in range(60)}
    espn = {k: v * 0.90 for k, v in hi.items()}
    partial = {k: v * 1.20 for k, v in list(hi.items())[:45]}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (espn, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (partial, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}}
    data, notes = consensus.build(ctx)

    assert any("espn on 60" in n for n in notes), notes
    assert any("fantasypros on 45" in n for n in notes), notes
    # Both scale factors removed, so a player all three price agrees closely.
    both = data["10"]
    assert both["n"] == 3 and both["spread"] < 1.0, both
    # And one only two of them price is still on the same basis.
    only_two = data["50"]
    assert only_two["n"] == 2 and only_two["spread"] < 1.0, only_two


def test_a_source_sharing_too_little_is_left_unscaled_and_said_so(monkeypatch):
    hi = {str(i): 100.0 + i for i in range(60)}
    tiny = {"0": 500.0, "1": 501.0}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (tiny, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: ({}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}}
    _, notes = consensus.build(ctx)
    assert any("espn not rescaled: only 2 players" in n for n in notes), notes


def test_the_reference_falls_back_to_the_biggest_source_without_sleeper(monkeypatch):
    big = {str(i): 100.0 + i for i in range(60)}
    small = {str(i): (100.0 + i) * 0.5 for i in range(50)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({}, "down"))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (big, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (small, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}}
    data, notes = consensus.build(ctx)
    assert any("rescaled against espn" in n for n in notes), notes
    assert data["10"]["spread"] < 1.0, data["10"]


def test_fantasypros_holds_full_weight_because_it_republishes():
    """The decay is for STATIC sources. This one is a live rest-of-season
    feed, so a week-12 brief must not be quietly discounting it."""
    assert consensus.source_weight("fantasypros", week=12) == 1.0

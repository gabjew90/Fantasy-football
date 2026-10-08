"""Step 3 of the slot-based trade plan: the rank panel accepts() reads.

OVERALL rank is the acceptance test's scale (a WR4 against an RB13 is
undecidable on positional rank), positional is carried for display, and
every row says which source it came from and how many experts stood
behind it.
"""

from __future__ import annotations

from manager import ecr, fantasypros as fp


class Cfg(dict):
    league_name = "x"

    def get(self, k, d=None):
        return dict.get(self, k, d)


INDEX = {
    "1": {"full_name": "Bijan Robinson", "position": "RB", "team": "ATL"},
    "2": {"full_name": "Garrett Wilson", "position": "WR", "team": "NYJ"},
    "3": {"full_name": "Jordan Love", "position": "QB", "team": "GB"},
}
CTX = {"cfg": Cfg(), "state": {"season": "2026"}, "players": INDEX}


def _feed(monkeypatch, op_rows, pos_rows, experts=149, updated="9/09"):
    """`op_rows` is the OVERALL list, served for whichever board is asked."""
    asked = []

    def _rows(pos, slug, season, kind, week=None):
        asked.append(pos)
        body = {"total_experts": experts, "last_updated": updated}
        if pos in ("ALL", "OP"):
            return list(op_rows), body
        return list(pos_rows.get(pos, [])), body
    monkeypatch.setattr(fp, "_rows", _rows)
    return asked


def _down(monkeypatch):
    def _boom(*a, **k):
        raise TimeoutError("slow")
    monkeypatch.setattr(fp, "_rows", _boom)


def test_overall_and_positional_come_from_the_fantasypros_draft_panel(monkeypatch):
    _feed(monkeypatch,
          op_rows=[{"player_name": "Bijan Robinson", "player_position_id": "RB", "rank_ecr": 4},
                   {"player_name": "Garrett Wilson", "player_position_id": "WR", "rank_ecr": 30}],
          pos_rows={"RB": [{"player_name": "Bijan Robinson", "rank_ecr": 2}],
                    "WR": [{"player_name": "Garrett Wilson", "rank_ecr": 16}]})
    panel, notes = ecr.rank_panel(CTX)
    assert panel["1"] == {"overall": 4.0, "positional": 2.0, "pos": "RB",
                          "panel": 149, "source": "fantasypros draft", "list": "ALL"}
    assert panel["2"]["overall"] == 30.0 and panel["2"]["positional"] == 16.0
    assert not any(n.startswith("⚠") or n.startswith("DATA MISSING") for n in notes), notes


def test_the_panel_size_is_carried_so_three_experts_is_never_read_as_agreement(monkeypatch):
    _feed(monkeypatch,
          op_rows=[{"player_name": "Jordan Love", "player_position_id": "QB", "rank_ecr": 65}],
          pos_rows={}, experts=3)
    panel, _ = ecr.rank_panel(CTX)
    assert panel["3"]["panel"] == 3


def test_a_missing_positional_row_leaves_overall_intact(monkeypatch):
    """Positional is display. Losing it must not lose the row the gate reads."""
    _feed(monkeypatch,
          op_rows=[{"player_name": "Bijan Robinson", "player_position_id": "RB", "rank_ecr": 4}],
          pos_rows={})
    panel, _ = ecr.rank_panel(CTX)
    assert panel["1"]["overall"] == 4.0 and panel["1"]["positional"] is None


def test_falls_back_to_the_mirror_when_fantasypros_is_down_and_says_so(monkeypatch):
    _down(monkeypatch)
    monkeypatch.setattr(ecr, "by_sleeper_id", lambda ctx: (
        {"1": {"overall": 5.0, "ecr": 2.0, "pos": "RB", "as_of": "2026-09-04"}}, None))
    panel, notes = ecr.rank_panel(CTX)
    assert panel["1"]["overall"] == 5.0 and panel["1"]["positional"] == 2.0
    assert panel["1"]["panel"] is None
    assert panel["1"]["source"] == "dynastyprocess mirror 2026-09-04"
    assert any(n.startswith("⚠") and "mirror" in n for n in notes), notes


def test_no_rank_source_at_all_is_data_missing(monkeypatch):
    _down(monkeypatch)
    monkeypatch.setattr(ecr, "by_sleeper_id",
                        lambda ctx: ({}, "DATA MISSING: expert ranks (X)"))
    panel, notes = ecr.rank_panel(CTX)
    assert panel == {}
    assert any(n.startswith("DATA MISSING") for n in notes), notes


def test_sources_are_never_mixed_per_player(monkeypatch):
    """One scale per run. If FantasyPros carries anyone, the mirror is not
    consulted for the rest: a WR4 on one panel against an RB13 on another
    is not a comparison."""
    _feed(monkeypatch,
          op_rows=[{"player_name": "Bijan Robinson", "player_position_id": "RB", "rank_ecr": 4}],
          pos_rows={})
    monkeypatch.setattr(ecr, "by_sleeper_id", lambda ctx: (
        {"2": {"overall": 30.0, "ecr": 16.0, "pos": "WR"}}, None))
    panel, _ = ecr.rank_panel(CTX)
    assert "1" in panel and "2" not in panel


def test_overall_drops_an_ambiguous_name_rather_than_guessing(monkeypatch):
    idx = dict(INDEX, **{"9a": {"full_name": "Mike Williams", "position": "WR"},
                         "9b": {"full_name": "Mike Williams", "position": "WR"}})
    _feed(monkeypatch,
          op_rows=[{"player_name": "Mike Williams", "player_position_id": "WR", "rank_ecr": 40}],
          pos_rows={})
    ov, _ = fp.overall({}, 2026, idx)
    assert "9a" not in ov and "9b" not in ov


def test_overall_joins_a_defence_on_team(monkeypatch):
    idx = {"MIN": {"first_name": "Minnesota", "last_name": "Vikings",
                   "position": "DEF", "team": "MIN"}}
    _feed(monkeypatch,
          op_rows=[{"player_name": "Minnesota Vikings", "player_position_id": "DST",
                    "player_team_id": "MIN", "rank_ecr": 120}],
          pos_rows={})
    ov, _ = fp.overall({}, 2026, idx)
    assert ov["MIN"]["overall"] == 120.0 and ov["MIN"]["pos"] == "DEF"


def test_a_one_qb_league_reads_the_standard_overall_list_not_superflex(monkeypatch):
    """OP is the superflex board: Allen 1, Hurts 5, Caleb Williams 8, every
    non-QB pushed down 8-17 ranks. ALL is the one-QB board: Bijan 4, Caleb
    63. Measured live 2026-09-10. A one-QB league must read ALL."""
    asked = _feed(monkeypatch, op_rows=[], pos_rows={})
    monkeypatch.setattr(ecr, "by_sleeper_id", lambda ctx: ({}, None))
    ecr.rank_panel(dict(CTX, slots={"QB": 1, "RB": 2, "WR": 2, "TE": 1},
                        flex_slots=(frozenset({"RB", "WR", "TE"}),)))
    assert "ALL" in asked and "OP" not in asked, asked


def test_a_superflex_league_reads_the_op_list(monkeypatch):
    asked = _feed(monkeypatch, op_rows=[], pos_rows={})
    monkeypatch.setattr(ecr, "by_sleeper_id", lambda ctx: ({}, None))
    ecr.rank_panel(dict(CTX, slots={"QB": 1, "RB": 2, "WR": 2, "TE": 1},
                        flex_slots=(frozenset({"QB", "RB", "WR", "TE"}),)))
    assert "OP" in asked and "ALL" not in asked, asked


def test_a_context_with_no_shape_defaults_to_one_qb(monkeypatch):
    asked = _feed(monkeypatch, op_rows=[], pos_rows={})
    monkeypatch.setattr(ecr, "by_sleeper_id", lambda ctx: ({}, None))
    ecr.rank_panel(CTX)
    assert "ALL" in asked, asked

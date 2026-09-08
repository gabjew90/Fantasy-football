"""Consensus and provenance: the layers that make a brief auditable.

Neither changes a recommendation. They say how firm the ground under one is,
and where it came from.
"""

import json

import pytest

from manager import consensus, provenance


class Cfg(dict):
    """The real Cfg is an OBJECT with a league_name ATTRIBUTE, not a dict key.
    Getting that wrong is why the first footer said 'unknown'."""

    def __init__(self, *a, league_name=None, **kw):
        super().__init__(*a, **kw)
        self.league_name = league_name

    def path(self, kind):
        return "data/raw"


class FakeStore:
    def __init__(self):
        self.d = {}

    def get(self, k, default=None):
        return self.d.get(k, default)

    def set(self, k, v):
        self.d[k] = v


# ------------------------------------------------------------------ annotate

def test_annotate_is_silent_for_a_single_source():
    """Claiming agreement you do not have is worse than saying nothing."""
    assert consensus.annotate({"n": 1, "mean": 100.0, "spread": 0.0,
                               "per_source": {"sheet": 100.0}}) == ""
    assert consensus.annotate(None) == ""


def test_annotate_shows_every_source_and_the_spread():
    out = consensus.annotate({"n": 3, "mean": 199.1, "spread": 21.7,
                              "per_source": {"espn": 209.4, "sheet": 200.3,
                                             "sleeper": 187.7}})
    assert "3 sources" in out and "spread 22" in out
    for v in ("209", "200", "188"):
        assert v in out


# ----------------------------------------------------------------- confident

def test_a_small_edge_between_disputed_players_is_not_an_edge():
    disputed = {"n": 3, "spread": 30.0, "per_source": {}, "mean": 0.0}
    assert consensus.confident(disputed, edge=3.0) is False
    assert consensus.confident(disputed, edge=16.0) is True


def test_agreement_lets_a_small_edge_through():
    agreed = {"n": 3, "spread": 2.0, "per_source": {}, "mean": 0.0}
    assert consensus.confident(agreed, edge=2.0) is True
    assert consensus.confident(agreed, edge=1.0) is False, "floor still applies"


def test_one_source_falls_back_to_the_plain_floor():
    assert consensus.confident({"n": 1, "spread": 0.0}, edge=2.0) is True
    assert consensus.confident(None, edge=0.5) is False


# ----------------------------------------------------------------- build

def test_build_rescales_sources_onto_a_common_basis(monkeypatch):
    """ESPN runs ~6% below Sleeper across the board. That is a scale
    difference, not a disagreement, and averaging it raw would bake it in."""
    hi = {str(i): 100.0 + i for i in range(60)}
    lo = {k: v * 0.90 for k, v in hi.items()}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (hi, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (lo, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    row = data["30"]
    assert row["n"] == 2
    assert row["spread"] < 1.0, f"scale not removed: {row}"
    assert any("rescaled on 60" in n for n in notes)


def test_a_dead_source_is_a_note_not_a_crash(monkeypatch):
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({}, "sleeper unavailable (X)"))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({"1": 50.0}, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    assert data["1"]["n"] == 1
    assert any("sleeper unavailable" in n for n in notes)


def test_every_source_down_is_reported_and_empty(monkeypatch):
    for fn, sig in (("_sleeper", lambda s, y: ({}, "down")),
                    ("_espn", lambda s, y, r, i: ({}, "down")),
                    ("_sheet", lambda c: ({}, "down"))):
        monkeypatch.setattr(consensus, fn, sig)
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    assert data == {}
    assert any("DATA MISSING" in n for n in notes)


def test_too_few_common_players_reports_rather_than_rescaling_on_noise(monkeypatch):
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({"1": 100.0, "2": 90.0}, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({"1": 50.0, "2": 45.0}, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    _, notes = consensus.build(ctx)
    assert any("not rescaled" in n for n in notes)


def test_the_store_caches_so_a_brief_does_not_refetch(monkeypatch):
    calls = []

    def sleeper(s, y):
        calls.append(1)
        return {str(i): 100.0 + i for i in range(60)}, None

    monkeypatch.setattr(consensus, "_sleeper", sleeper)
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, None))
    monkeypatch.setattr(consensus, "_sheet", lambda c: ({}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    store = FakeStore()
    consensus.build(ctx, store)
    consensus.build(ctx, store)
    assert len(calls) == 1


# ---------------------------------------------------------------- provenance

def test_league_name_comes_off_the_object_not_the_dict():
    ctx = {"cfg": Cfg(league_name="omnibeta"), "week": 3}
    assert provenance.league_name(ctx) == "omnibeta"
    assert provenance.stamp(ctx)["league"] == "omnibeta"


def test_stamp_survives_a_config_with_no_league():
    st = provenance.stamp({"cfg": Cfg(), "week": 1})
    assert st["league"] is None and st["config_hash"] is None
    assert st["week"] == 1 and st["generated_at"].endswith("Z")


def test_render_names_the_code_and_flags_uncommitted_work():
    body = provenance.render({"commit": "abc1234", "dirty": True,
                              "config_hash": "deadbeef", "league": "omnibeta",
                              "week": 2, "generated_at": "2026-09-07T00:00:00Z",
                              "sources": {"espn": "2026-09-07"}})
    assert "abc1234" in body and "uncommitted changes" in body
    assert "omnibeta week 2" in body and "espn 2026-09-07" in body


def test_render_says_none_recorded_rather_than_leaving_it_blank():
    assert "none recorded" in provenance.render({"commit": "x", "sources": {}})


def test_file_hash_is_none_for_an_absent_file(tmp_path):
    assert provenance.file_hash(tmp_path / "nope.yaml") is None
    p = tmp_path / "yes.yaml"
    p.write_text("a: 1", encoding="utf-8")
    assert len(provenance.file_hash(p)) == 12


# --------------------------------------------------------------------- apply

def _row(pid, season, weekly, name="p"):
    return {"sleeper_id": pid, "name": name, "pos": "RB",
            "ros_season": season, "ros": season, "weekly": weekly}


def _ctx(rows, player_row=None):
    return {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
            "players": {}, "roster_players": {1: rows},
            "player_row": player_row or (lambda pid: None)}


def test_apply_rescales_level_and_keeps_weekly_shape():
    """The sources give SEASON totals; the weekly number carries the opponent
    and the bye. Consensus sets the level, the existing weekly keeps shape."""
    rows = [_row("1", 200.0, 12.0)]
    con = {"1": {"mean": 240.0, "n": 3, "spread": 10.0, "per_source": {}}}
    n, _ = consensus.apply(_ctx(rows), con)
    assert n == 1
    assert rows[0]["ros_season"] == 240.0
    assert rows[0]["weekly"] == 14.4          # 12 * 1.2, shape preserved


def test_a_single_source_is_not_a_consensus_and_is_left_alone():
    rows = [_row("1", 200.0, 12.0)]
    con = {"1": {"mean": 400.0, "n": 1, "spread": 0.0, "per_source": {}}}
    n, _ = consensus.apply(_ctx(rows), con)
    assert n == 0 and rows[0]["ros_season"] == 200.0


def test_a_wild_ratio_is_clamped_and_counted(capsys):
    rows = [_row("1", 50.0, 3.0)]
    con = {"1": {"mean": 500.0, "n": 3, "spread": 5.0, "per_source": {}}}
    n, notes = consensus.apply(_ctx(rows), con)
    assert rows[0]["ros_season"] == 80.0       # 50 * 1.60, not 500
    assert any(x.startswith("\u26a0") and "clamped" in x for x in notes)


def test_a_missing_board_number_has_no_ratio_and_is_skipped():
    rows = [_row("1", 0.0, 0.0)]
    con = {"1": {"mean": 240.0, "n": 3, "spread": 1.0, "per_source": {}}}
    n, _ = consensus.apply(_ctx(rows), con)
    assert n == 0


def test_the_free_agent_pool_is_rebased_on_the_same_basis():
    """A consensus roster judged against a single-source wire is worse than
    using neither, so player_row is wrapped too."""
    fa = _row("9", 100.0, 6.0, name="fa")
    ctx = _ctx([], player_row=lambda pid: fa if pid == "9" else None)
    con = {"9": {"mean": 150.0, "n": 3, "spread": 2.0, "per_source": {}}}
    consensus.apply(ctx, con)
    got = ctx["player_row"]("9")
    assert got["ros_season"] == 150.0 and got["weekly"] == 9.0


def test_wrapping_player_row_is_idempotent():
    calls = []

    def orig(pid):
        calls.append(pid)
        return _row(pid, 100.0, 6.0)

    ctx = _ctx([], player_row=orig)
    con = {"9": {"mean": 150.0, "n": 3, "spread": 2.0, "per_source": {}}}
    consensus.apply(ctx, con)
    consensus.apply(ctx, con)          # a second module calling it must not double-wrap
    ctx["player_row"]("9")
    assert len(calls) == 1, "player_row wrapped twice — projections applied twice"


def test_an_already_correct_number_is_not_touched():
    rows = [_row("1", 200.0, 12.0)]
    con = {"1": {"mean": 200.0, "n": 3, "spread": 4.0, "per_source": {}}}
    n, _ = consensus.apply(_ctx(rows), con)
    assert n == 0 and rows[0]["weekly"] == 12.0

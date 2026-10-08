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
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    row = data["30"]
    assert row["n"] == 2
    assert row["spread"] < 1.0, f"scale not removed: {row}"
    # The note names the REFERENCE and the size of each source's own overlap
    # with it, because the fit is pairwise: a global "60 in common" hid which
    # population any given source was actually scaled on.
    assert any("rescaled against sleeper (espn on 60)" in n for n in notes)


def test_a_dead_source_is_a_note_not_a_crash(monkeypatch):
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({}, "sleeper unavailable (X)"))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({"1": 50.0}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    assert data["1"]["n"] == 1
    assert any("sleeper unavailable" in n for n in notes)


def test_every_source_down_is_reported_and_empty(monkeypatch):
    for fn, sig in (("_sleeper", lambda s, y: ({}, "down")),
                    ("_espn", lambda s, y, r, i: ({}, "down"))):
        monkeypatch.setattr(consensus, fn, sig)
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": {}}
    data, notes = consensus.build(ctx)
    assert data == {}
    assert any("DATA MISSING" in n for n in notes)


def test_too_few_common_players_reports_rather_than_rescaling_on_noise(monkeypatch):
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({"1": 100.0, "2": 90.0}, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({"1": 50.0, "2": 45.0}, None))
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


# -------------------------------------------------------------- source ageing

def test_live_sources_never_decay():
    for w in (1, 5, 12, 18):
        assert consensus.source_weight("sleeper", w) == 1.0
        assert consensus.source_weight("espn", w) == 1.0


def test_the_preseason_sheet_decays_to_zero():
    """It is a draft workbook. Nothing regenerates it once the season starts,
    so equal weight in November means arguing for August."""
    assert consensus.source_weight("sheet", 1) == 1.0
    assert consensus.source_weight("sheet", 5) == 0.5
    assert consensus.source_weight("sheet", 9) == 0.0
    assert consensus.source_weight("sheet", 15) == 0.0


def test_the_mean_is_weighted_and_the_static_source_fades(monkeypatch):
    """Player 30 is where the sheet actually disagrees. Everyone else matches,
    so the medians line up and no rescale hides the difference -- a UNIFORM
    offset would be a scale difference and would be removed by design."""
    live = {str(i): 100.0 for i in range(60)}
    stale = dict(live, **{"30": 200.0})
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (live, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (live, None))
    monkeypatch.setattr(consensus, "_sources", lambda c, sc, se, ix: (
        ("sleeper", (live, None)), ("espn", (live, None)), ("sheet", (stale, None))))

    def at(week):
        ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
               "players": {}, "week": week}
        return consensus.build(ctx)[0]["30"]["mean"]

    wk1, wk5, wk9 = at(1), at(5), at(9)
    assert wk1 > wk5 > wk9, (wk1, wk5, wk9)
    assert wk9 == 100.0, "an aged-out source still moved the mean"


def test_ageing_out_is_announced(monkeypatch):
    live = {str(i): 100.0 for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (live, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, None))
    monkeypatch.setattr(consensus, "_sources", lambda c, sc, se, ix: (
        ("sleeper", (live, None)),
        ("sheet", ({str(i): 200.0 for i in range(60)}, None))))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {}, "week": 12}
    _, notes = consensus.build(ctx)
    assert any("aged out" in n and n.startswith("\u26a0") for n in notes)


def test_a_down_weighted_source_is_announced(monkeypatch):
    live = {str(i): 100.0 for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (live, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, None))
    monkeypatch.setattr(consensus, "_sources", lambda c, sc, se, ix: (
        ("sleeper", (live, None)),
        ("sheet", ({str(i): 200.0 for i in range(60)}, None))))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {}, "week": 4}
    _, notes = consensus.build(ctx)
    assert any("down-weighted" in n for n in notes)


def test_a_uniform_offset_is_a_scale_difference_and_is_removed(monkeypatch):
    """ESPN 30% high on EVERY player is a different season model, not an
    argument about anyone. Rescaling must flatten it to zero spread."""
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({str(i): 100.0 for i in range(60)}, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({str(i): 130.0 for i in range(60)}, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {}, "week": 3}
    assert consensus.build(ctx)[0]["30"]["spread"] == 0.0


def test_a_real_player_level_disagreement_survives_rescaling(monkeypatch):
    """One player the sources genuinely argue about, everyone else agreed."""
    base = {str(i): 100.0 for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (base, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (dict(base, **{"30": 160.0}), None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {}, "week": 3}
    data = consensus.build(ctx)[0]
    assert data["30"]["spread"] == 60.0, "a real disagreement was flattened"
    assert data["31"]["spread"] == 0.0, "agreement was turned into noise"


# ------------------------------------------- shelved players at stale prices

def test_a_shelved_player_with_no_live_source_is_dropped_from_the_pool():
    """Ricky Pearsall, PCL surgery, out for 2026, still carried his August
    148.7 on the board and ranked as the best free agent WR in Omnibeta.
    Every live source had caught it -- Sleeper 0.0, ESPN and the sheet absent
    -- but consensus cannot correct a player it has no row for."""
    from manager import waiver_brief as wb
    pl = {"active": True, "injury_status": "IR", "full_name": "Shelved Star",
          "position": "WR"}
    assert wb._stale_reserve(pl, {}, "1") is True
    carried = {"1": {"n": 2, "per_source": {"sleeper": 90.0, "espn": 88.0}}}
    assert wb._stale_reserve(pl, carried, "1") is False, \
        "a source that prices the whole position still carries him, so trust it"

    # THE THIRD SOURCE MUST NOT RESCUE HIM ON ITS OWN. FantasyPros publishes
    # rankings whose list ends somewhere -- 32 kickers against 154 active --
    # so its carrying a shelved receiver is an artefact of where the list
    # stops, not an opinion that he plays. Counting it would have raised this
    # guard from "both sources dropped him" to "all three did" and put
    # Pearsall back in the pool at his August number.
    fp_only = {"1": {"n": 1, "per_source": {"fantasypros": 40.0}}}
    assert wb._stale_reserve(pl, fp_only, "1") is True, \
        "a ranking feed's inclusion was read as coverage"
    mixed = {"1": {"n": 2, "per_source": {"espn": 88.0, "fantasypros": 40.0}}}
    assert wb._stale_reserve(pl, mixed, "1") is False


def test_absence_is_only_evidence_for_positions_the_sources_cover():
    """The projections request names QB/RB/WR/TE. A kicker's n=0 is a fact
    about the request, not about the kicker, and reading it as staleness
    deleted every reserve-status K and DEF from the pool."""
    from manager import waiver_brief as wb
    for pos in ("K", "DEF"):
        pl = {"active": True, "injury_status": "IR", "position": pos}
        assert wb._stale_reserve(pl, {}, "1") is False, pos
    # and an unknown position is never grounds to delete a player either
    assert wb._stale_reserve({"active": True, "injury_status": "IR"}, {}, "1") is False


def test_a_healthy_player_is_never_dropped_for_this_reason():
    from manager import waiver_brief as wb
    for status in ("", None, "Questionable", "Doubtful"):
        assert wb._stale_reserve({"injury_status": status}, {}, "1") is False


def test_every_reserve_designation_is_covered():
    from manager import waiver_brief as wb
    for st in ("IR", "IR-R", "PUP", "PUP-R", "NFI", "NFI-R", "DNR", "Sus", "Inactive"):
        assert wb._stale_reserve(
            {"injury_status": st, "position": "RB"}, {}, "1") is True, st


def test_the_pool_excludes_him_and_records_why():
    from manager import waiver_brief as wb
    rows = {"1": {"name": "Shelved Star", "pos": "WR", "weekly": 0.0, "ros": 148.7,
                  "ros_season": 148.7, "sleeper_id": "1"},
            "2": {"name": "Healthy Guy", "pos": "WR", "weekly": 9.0, "ros": 120.0,
                  "ros_season": 120.0, "sleeper_id": "2"}}
    ctx = {"players": {"1": {"active": True, "injury_status": "IR", "position": "WR"},
                       "2": {"active": True, "injury_status": None, "position": "WR"}},
           "rosters": [], "player_row": rows.get, "trow": {}}
    pool = wb._fa_pool(ctx, con={})
    names = {p["name"] for p in pool}
    assert names == {"Healthy Guy"}, names
    assert "Shelved Star (IR)" in ctx["_stale_reserve_dropped"]


def test_the_rescale_anchor_does_not_move_with_which_sources_answer(monkeypatch):
    """Picking the largest source handed the anchor to FantasyPros (471 rows
    against ESPN's 414) on a Sleeper outage -- and FantasyPros is the one
    source measured to run 9-13% hot, so an outage would have inflated every
    projection in every league by about ten percent."""
    espn = {str(i): 100.0 + i for i in range(60)}
    fpros = {str(i): (100.0 + i) * 1.10 for i in range(90)}     # bigger AND hot
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: ({}, "down"))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (espn, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (fpros, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}}
    data, notes = consensus.build(ctx)
    assert any("rescaled against espn" in n for n in notes), notes
    # ESPN's level survives; FantasyPros is pulled DOWN onto it, not the reverse
    assert abs(data["30"]["mean"] - 130.0) < 1.0, data["30"]


def test_a_position_with_no_shared_players_is_named_not_silently_borrowed(
        monkeypatch):
    """Sleeper is never asked for K or DEF, so those rows can never appear in
    the overlap a scale factor is fitted on. Applying a skill-position ratio
    to them anyway is defensible; doing it silently is not."""
    idx = {str(i): {"position": "RB" if i < 60 else "K", "full_name": f"p{i}"}
           for i in range(80)}
    sleeper = {str(i): 100.0 + i for i in range(60)}                 # RB only
    fpros = {str(i): (100.0 + i) * 1.10 for i in range(80)}          # RB + K
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (sleeper, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, "down"))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (fpros, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": idx}
    data, notes = consensus.build(ctx)
    assert any("K could not be fitted" in n for n in notes), notes
    assert data["70"]["n"] == 1, data["70"]


def test_each_position_is_scaled_on_its_own_ratio(monkeypatch):
    """One global median splits the difference between positions that differ,
    leaving a residual that biases exactly the cross-position trades the
    engine exists to price."""
    idx = {str(i): {"position": "RB" if i < 40 else "WR", "full_name": f"p{i}"}
           for i in range(80)}
    sleeper = {str(i): 100.0 + i for i in range(80)}
    # 20% hot at RB, 5% hot at WR -- a single ratio can be right for neither
    other = {str(i): (100.0 + i) * (1.20 if i < 40 else 1.05) for i in range(80)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (sleeper, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (other, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: ({}, "down"))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": idx}
    data, _ = consensus.build(ctx)
    for pid in ("10", "60"):
        assert data[pid]["spread"] < 1.0, (
            f"{idx[pid]['position']} still carries a scale residual: {data[pid]}")


def test_a_rest_of_season_source_is_put_on_a_season_basis_first(monkeypatch):
    """Sleeper and ESPN return full-season totals (Sleeper's rows carry
    gp: 18.0); FantasyPros returns REST of season. apply() divides the blend
    by ros_season, "the untouched season total", so mixing the bases feeds a
    part-season number into a full-season ratio.

    Invisible in week 1 -- nothing played, so the two coincide exactly, which
    is why the source measured as a clean constant when it was wired in.
    """
    season = {str(i): 200.0 for i in range(60)}
    half = {str(i): 100.0 for i in range(60)}          # same players, 8 weeks left
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (season, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (season, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (half, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}, "weeks_left": 8}
    data, notes = consensus.build(ctx)
    assert any("rest-of-season" in n and "x2.12" in n for n in notes), notes
    # 100 * (17/8) = 212.5, then the median rescale lands it on 200
    assert data["30"]["spread"] < 1.0, data["30"]


def test_week_one_does_not_rescale_a_rest_of_season_source(monkeypatch):
    """With nothing played the two bases are identical, and multiplying by
    17/17 is a no-op that should not appear in the notes as if work happened."""
    season = {str(i): 200.0 for i in range(60)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (season, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: ({}, "down"))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: (season, None))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"},
           "players": {"1": {}}, "weeks_left": 17}
    data, notes = consensus.build(ctx)
    assert not any("rest-of-season" in n for n in notes), notes
    assert data["30"]["mean"] == 200.0


def test_the_extrapolation_warning_watches_the_factors_actually_applied(
        monkeypatch):
    """The guard predates the per-position fit and only read `scale`. Those
    stay mild -- espn 0.963, fantasypros 0.906, both inside the 10% bar --
    while the per-position factors that REPLACE them reach 0.821 at WR. The
    more extreme a multiplier got, the less likely it was to be mentioned."""
    idx = {str(i): {"position": "RB" if i < 40 else "WR", "full_name": f"p{i}"}
           for i in range(80)}
    sleeper = {str(i): 150.0 + i for i in range(80)}
    # Chosen so the GLOBAL ratio lands inside 10% while WR sits far outside:
    # RB is 18% cold, WR is 18% hot, and the medians nearly cancel.
    other = {str(i): (150.0 + i) * (1.22 if i < 40 else 0.82) for i in range(80)}
    monkeypatch.setattr(consensus, "_sleeper", lambda s, y: (sleeper, None))
    monkeypatch.setattr(consensus, "_espn", lambda s, y, r, i: (other, None))
    monkeypatch.setattr(consensus, "_fantasypros", lambda s, y, i: ({}, "down"))
    ctx = {"cfg": Cfg(league_name="x"), "state": {"season": "2026"}, "players": idx}
    _, notes = consensus.build(ctx)
    warned = [n for n in notes if "extrapolated to the whole pool" in n]
    assert warned, f"no extrapolation warning at all: {notes}"
    assert "espn/WR" in warned[0] or "espn/RB" in warned[0], warned[0]

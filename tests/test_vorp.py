import polars as pl

from draftkit.vorp import add_vorp


def _pool(pos, pts):
    return [{"pos": pos, "proj_pts": float(p)} for p in pts]


def test_rb_uses_rank_directly():
    df = pl.DataFrame(_pool("RB", [100, 90, 80, 70]))
    out = add_vorp(df, {"RB": 3})
    top = out.sort("proj_pts", descending=True)
    assert top["replacement_pts"][0] == 80.0
    assert top["vorp"][0] == 20.0


def test_qb_replacement_is_smoothed_from_the_configured_baseline():
    """QB/TE replacement is a mean over a window, so one projection outlier at
    the exact baseline cannot move every VORP at the position. The window is
    anchored to the league's configured baseline: baseline..baseline+4."""
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200, 190, 180, 170, 160]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    # ranks 12-16 -> 190, 180, 170, 160 -> mean 175
    assert out["replacement_pts"][0] == 175.0


def test_qb_baseline_actually_changes_replacement():
    """Regression for a silent config bug (found 2026-08-31).

    The smoothing window was hardcoded to ranks 10-14 for every league, which
    made `replacement_baselines.QB` and `.TE` DEAD SETTINGS -- editing them
    changed nothing, and the repo's "baselines are derived per league, never
    copied" guarantee did not hold for these two positions. A 10-team league
    and a superflex league received identical QB replacement levels.
    """
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200, 190, 180, 170, 160]
    df = pl.DataFrame(_pool("QB", pts))
    shallow = add_vorp(df, {"QB": 5})["replacement_pts"][0]   # ranks 5-9
    deep = add_vorp(df, {"QB": 12})["replacement_pts"][0]     # ranks 12-16
    assert shallow == 240.0, shallow          # mean(260,250,240,230,220)
    assert deep == 175.0, deep
    assert shallow > deep, "a shallower baseline must raise replacement level"


def test_te_baseline_is_honoured_too():
    pts = [200, 190, 180, 170, 160, 150, 140, 130, 120, 110, 100]
    df = pl.DataFrame(_pool("TE", pts))
    out = add_vorp(df, {"TE": 8})
    # ranks 8-12 -> 130, 120, 110, 100 -> mean 115
    assert out["replacement_pts"][0] == 115.0


def test_qb_smoothing_with_short_pool():
    """Window past the end of the pool falls back to the last rank present."""
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    assert out["replacement_pts"][0] == 200.0   # only rank 11 exists


def test_flex_bound_players_are_valued_against_the_flex_baseline():
    """A player who will start in the FLEX competes with the RB/WR you would
    otherwise put there, not with replacement at his own position.

    Scoring him against his positional baseline overvalues every flex-bound
    tight end by the gap between the two. That gap is per position (zero for
    whichever position sets the flex baseline); on the 2026-09-04 Keefamania
    board it is TE 38.0, WR 18.1, RB 0.0. Bowers reads +61.9 as a tight end
    but contributes +29.1 as a flex starter. That error is what produced the double-elite-TE
    build the engine kept recommending.
    """
    df = pl.DataFrame(
        _pool("TE", [190.2, 189.3, 146.8, 131.4, 130.7, 129.0, 127.5, 127.4])
        + _pool("RB", [283.0, 160.2])
        + _pool("WR", [215.9, 147.0])
    )
    out = add_vorp(df, {"TE": 8, "RB": 2, "WR": 2}).sort("proj_pts", descending=True)
    te = out.filter(pl.col("pos") == "TE").sort("proj_pts", descending=True)

    # against TE8 (127.4)
    assert round(te["vorp"][0], 1) == 62.8
    # against the FLEX baseline, which is the better of RB24/WR24 -> 160.2
    assert round(te["vorp_flex"][0], 1) == 30.0
    assert round(te["vorp"][0] - te["vorp_flex"][0], 1) == 32.8

    # a mid TE is NEGATIVE in the flex: he should not start over an RB24
    assert te["vorp"][2] > 0
    assert te["vorp_flex"][2] < 0, "TE3 must not look startable in the flex"


def test_non_flex_positions_are_unaffected():
    """QB/K/DEF have no flex path, so their two values must agree."""
    df = pl.DataFrame(_pool("QB", [300.0, 280.0, 270.0])
                      + _pool("RB", [250.0, 150.0]))
    out = add_vorp(df, {"QB": 2, "RB": 2})
    qb = out.filter(pl.col("pos") == "QB")
    for a, b in zip(qb["vorp"], qb["vorp_flex"]):
        assert a == b


def test_vorp_column_is_unchanged_by_the_addition():
    """`vorp` keeps its meaning: the in-season manager and season artifacts
    read it, and this change must not reach them."""
    df = pl.DataFrame(_pool("RB", [200.0, 180.0, 160.0, 140.0]))
    out = add_vorp(df, {"RB": 3})
    top = out.sort("proj_pts", descending=True)
    assert top["vorp"][0] == 40.0        # 200 - 160, exactly as before

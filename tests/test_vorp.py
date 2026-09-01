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

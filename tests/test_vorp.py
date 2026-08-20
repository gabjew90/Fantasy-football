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


def test_qb_uses_mean_of_ranks_10_14():
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200, 190, 180, 170, 160]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    # ranks 10-14 -> 210, 200, 190, 180, 170 -> mean 190
    assert out["replacement_pts"][0] == 190.0


def test_qb_smoothing_with_short_pool():
    # only 11 QBs: ranks 10-14 window truncates to what exists (10, 11)
    pts = [300, 290, 280, 270, 260, 250, 240, 230, 220, 210, 200]
    df = pl.DataFrame(_pool("QB", pts))
    out = add_vorp(df, {"QB": 12})
    assert out["replacement_pts"][0] == 205.0  # mean(210, 200)

"""Standing ADP tilts (v2 item 1.6) — capped, league-gated, off by default."""

import polars as pl

from draftkit.tilts import apply_tilts, prior_top5_by_pos

CFG = {"enabled": True, "mid_te_fade": 0.08, "nonrush_qb_fade": 0.08,
       "rush_qb_late_boost": 0.08, "elite_te_boost": 0.05,
       "top5_regression": 0.10, "cap": 0.10}


def _df():
    # 4 TEs so positional ADP ranks separate: elite = top-3, Mid TE = rank 4
    return pl.DataFrame({
        "sleeper_id": ["t1", "t2", "t3", "t4", "q1", "q2", "w1"],
        "player": ["Mid TE", "Elite TE", "TE2", "TE3",
                   "Pocket QB", "Late Rush QB", "Top5 WR"],
        "pos": ["TE", "TE", "TE", "TE", "QB", "QB", "WR"],
        "adp": [55.0, 8.0, 20.0, 30.0, 60.0, 120.0, 12.0],
        "hv_touches": [3.0, 5.0, 4.0, 4.0, 4.0, 30.0, 20.0],
        "proj_pts": [100.0, 200.0, 150.0, 140.0, 300.0, 250.0, 200.0],
    })


def test_tilts_directions_and_cap():
    out, n = apply_tilts(_df(), CFG, prior_top5_ids={"w1"})
    by = dict(zip(out["player"], out["proj_pts"]))
    assert by["Mid TE"] == 92.0            # -8%
    assert by["Elite TE"] == 210.0         # +5%
    assert by["Pocket QB"] == 276.0        # -8% early non-rusher
    assert by["Late Rush QB"] == 270.0     # +8% late rusher
    assert by["Top5 WR"] == 180.0          # -10% recency regression
    assert n == 7  # TE2/TE3 get the elite boost (top-3 positional ADP)
    assert out["tilt"].abs().max() <= 0.10 + 1e-9


def test_disabled_is_identity():
    out, n = apply_tilts(_df(), {"enabled": False}, {"w1"})
    assert n == 0 and out["proj_pts"].to_list() == _df()["proj_pts"].to_list()
    out2, n2 = apply_tilts(_df(), None)
    assert n2 == 0


def test_prior_top5_extraction():
    usage = pl.DataFrame({
        "sleeper_id": [str(i) for i in range(8)],
        "pos": ["WR"] * 8,
        "fpts_total": [300.0, 280.0, 260.0, 240.0, 220.0, 200.0, 180.0, 160.0],
    })
    assert prior_top5_by_pos(usage) == {"0", "1", "2", "3", "4"}

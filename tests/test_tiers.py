from draftkit.tiers import assign_tiers


def test_flat_values_single_tier():
    tiers, cliffs = assign_tiers([10.0, 9.9, 9.8, 9.7])
    assert tiers == [1, 1, 1, 1]
    assert not any(cliffs)


def test_big_gap_starts_new_tier_and_flags_cliff():
    values = [100.0, 99.0, 98.0, 70.0, 69.0, 68.0]
    tiers, cliffs = assign_tiers(values, break_z=0.5, cliff_z=1.0)
    assert tiers[:3] == [1, 1, 1]
    assert tiers[3:] == [2, 2, 2]
    assert cliffs[2]  # last player before the drop carries the flag
    assert not cliffs[3]


def test_empty_and_single():
    assert assign_tiers([]) == ([], [])
    assert assign_tiers([5.0]) == ([1], [False])


def test_monotone_tier_numbers():
    values = [50, 45, 44, 30, 29, 10, 9]
    tiers, _ = assign_tiers([float(v) for v in values])
    assert all(tiers[i] <= tiers[i + 1] for i in range(len(tiers) - 1))


def _pool_df(extra_rows=()):
    import polars as pl

    rows = [
        {"sleeper_id": str(i), "name": f"P{i}", "pos": "WR",
         "proj_pts": 300.0 - i, "vorp": 100.0 - i, "adp": None,
         "ecr": float(i + 1), "proj_source": "blend"}
        for i in range(30)
    ]
    rows.extend(extra_rows)
    return pl.DataFrame(rows)


def _cfg():
    from pathlib import Path

    from draftkit.config import Config

    return Config(
        {"pool_sizes": {"WR": 10},
         "tiers": {"break_z": 0.5, "cliff_z": 1.0, "adp_include_within": 180}},
        Path("."),
    )


def test_adp_inside_draft_always_included():
    from draftkit.tiers import build_tiers

    # terrible VORP but the market drafts him at pick 150 -> must be on the board
    df = _pool_df([{"sleeper_id": "x", "name": "Faller", "pos": "WR",
                    "proj_pts": 10.0, "vorp": -80.0, "adp": 150.0, "ecr": 300.0,
                    "proj_source": "blend"}])
    out = build_tiers(df, _cfg())
    assert "Faller" in out["name"].to_list()
    assert out.height == 11  # top-10 pool + the ADP inclusion


def test_adp_outside_draft_still_cut():
    from draftkit.tiers import build_tiers

    df = _pool_df([{"sleeper_id": "y", "name": "Deep", "pos": "WR",
                    "proj_pts": 10.0, "vorp": -80.0, "adp": 220.0, "ecr": 300.0,
                    "proj_source": "blend"}])
    out = build_tiers(df, _cfg())
    assert "Deep" not in out["name"].to_list()


def test_disagreements_worklist():
    import polars as pl

    from draftkit.tiers import build_disagreements

    rows = []
    # model and market agree on players 0..19 (value_rank i+1, adp i+1)
    for i in range(20):
        rows.append({"player": f"P{i}", "pos": "WR", "team": "T", "tier": 1,
                     "value_rank": i + 1, "adp": float(i + 1), "vorp": 100.0 - i,
                     "proj_pts": 200.0, "exp_games": 16.0, "rookie_flag": False,
                     "proj_source": "blend"})
    # model fade: model rank 90, market drafts him 21st
    rows.append({"player": "Fade", "pos": "WR", "team": "T", "tier": 9,
                 "value_rank": 90, "adp": 21.0, "vorp": -10.0, "proj_pts": 100.0,
                 "exp_games": 12.0, "rookie_flag": False, "proj_source": "blend"})
    # model target: model rank 21, market waits until pick 150
    rows.append({"player": "Target", "pos": "WR", "team": "T", "tier": 3,
                 "value_rank": 21, "adp": 150.0, "vorp": 60.0, "proj_pts": 180.0,
                 "exp_games": 16.0, "rookie_flag": False, "proj_source": "blend"})
    # K and ADP-outside-180 must be excluded
    rows.append({"player": "Kicker", "pos": "K", "team": "T", "tier": 1,
                 "value_rank": 200, "adp": 5.0, "vorp": 10.0, "proj_pts": 140.0,
                 "exp_games": 16.0, "rookie_flag": False, "proj_source": "market_implied"})
    rows.append({"player": "Deep", "pos": "WR", "team": "T", "tier": 9,
                 "value_rank": 5, "adp": 200.0, "vorp": 90.0, "proj_pts": 190.0,
                 "exp_games": 16.0, "rookie_flag": False, "proj_source": "blend"})
    # the real pipeline produces value_rank as UInt32 (polars rank output);
    # subtraction must not wrap around for negative gaps
    df = pl.DataFrame(rows).with_columns(pl.col("value_rank").cast(pl.UInt32))
    out = build_disagreements(df, adp_within=180, per_side=15)
    assert out["rank_gap"].min() < 0  # would be ~4294967295 on underflow
    names = out["player"].to_list()
    assert "Fade" in names and "Target" in names
    assert "Kicker" not in names and "Deep" not in names
    fade = out.filter(pl.col("player") == "Fade")
    target = out.filter(pl.col("player") == "Target")
    assert fade["direction"][0] == "model_fade"
    assert target["direction"][0] == "model_target"
    # fades sorted most-negative first within their block
    fades = out.filter(pl.col("direction") == "model_fade")
    gaps = fades["rank_gap"].to_list()
    assert gaps == sorted(gaps)


def test_handcuff_info_rbs_only():
    import polars as pl

    from draftkit.tiers import add_handcuff_info

    df = pl.DataFrame([
        {"player": "Star RB", "pos": "RB", "team": "SFO", "vorp": 100.0,
         "exp_games": 12.0, "avail_status": "compromised"},
        {"player": "Backup RB", "pos": "RB", "team": "SFO", "vorp": 10.0,
         "exp_games": 16.0, "avail_status": None},
        {"player": "Other WR", "pos": "WR", "team": "SFO", "vorp": 50.0,
         "exp_games": 16.0, "avail_status": None},
        {"player": "Solo RB", "pos": "RB", "team": "DET", "vorp": 80.0,
         "exp_games": 16.0, "avail_status": None},
    ])
    out = add_handcuff_info(df)
    back = out.filter(pl.col("player") == "Backup RB")
    assert back["backs_up"][0] == "Star RB"
    assert back["starter_exp_games"][0] == 12.0
    assert back["starter_avail"][0] == "compromised"
    assert out.filter(pl.col("player") == "Star RB")["backs_up"][0] is None
    assert out.filter(pl.col("player") == "Other WR")["backs_up"][0] is None
    assert out.filter(pl.col("player") == "Solo RB")["backs_up"][0] is None


def test_no_market_rows_always_included():
    from draftkit.tiers import build_tiers

    df = _pool_df([{"sleeper_id": "z", "name": "Ghost", "pos": "WR",
                    "proj_pts": 150.0, "vorp": -50.0, "adp": None, "ecr": None,
                    "proj_source": "no_market"}])
    out = build_tiers(df, _cfg())
    assert "Ghost" in out["name"].to_list()


def test_upside_gate_rewards_volume_paths_only():
    import polars as pl
    from draftkit.tiers import add_upside_flags
    df = pl.DataFrame({
        "player": ["Handcuff", "PassCatchRB", "CheapRookie", "DeepRookie", "BoomBust"],
        "pos": ["RB", "RB", "WR", "WR", "WR"],
        "backs_up": ["Star RB", None, None, None, None],
        "tprr": [None, 0.19, None, None, 0.02],
        "rookie_flag": [False, False, True, True, False],
        "adp": [140.0, 90.0, 100.0, 200.0, 95.0],
    })
    out = add_upside_flags(df)
    flags = dict(zip(out["player"], out["upside_flag"]))
    assert flags == {"Handcuff": True, "PassCatchRB": True, "CheapRookie": True,
                     "DeepRookie": False,   # no market-backed capital
                     "BoomBust": False}     # raw variance is never rewarded
    whys = dict(zip(out["player"], out["upside_why"]))
    assert whys["Handcuff"] == "contingent volume"


# --- tier method: anchor_frac (the spreadsheet's rule) ----------------------
# gap_sd groups by the drop from the PREVIOUS player, with a bar set from the
# gap distribution. One dominant player inflates that bar until nothing else
# can clear it, and nothing bounds a tier's own spread. anchor_frac measures
# from the TIER'S TOP PLAYER against a fraction of the position's best value.

def _one_star(n=30):
    """One dominant player, then a long smooth run whose total spread is
    several times the tier allowance. The shape that breaks gap_sd, and the
    shape QB actually has on the 2026 board."""
    return [200.0] + [40.0 - 4.0 * i for i in range(n - 1)]


def test_gap_sd_collapses_when_one_player_dominates():
    """The defect, pinned. Not a hypothetical: this is QB on the 2026 board."""
    tiers, _ = assign_tiers(_one_star(), method="gap_sd")
    from collections import Counter
    sizes = Counter(tiers)
    assert max(sizes.values()) >= len(tiers) - 2, (
        "gap_sd is expected to dump nearly everyone into one tier here")


def test_anchor_frac_keeps_resolution_under_one_dominant_player():
    vals = _one_star()
    tiers, _ = assign_tiers(vals, method="anchor_frac", break_frac=0.20)
    assert tiers[0] == 1 and tiers[1] == 2, "the dominant player is his own tier"
    assert max(tiers) >= 3, "the run below him must still be split"


def test_anchor_frac_bounds_a_tiers_own_spread():
    """The property gap_sd cannot offer: a tier cannot drift arbitrarily far
    from its own best player."""
    vals = [100.0 - 2.0 * i for i in range(40)]      # a pure staircase
    frac = 0.15
    tiers, _ = assign_tiers(vals, method="anchor_frac", break_frac=frac)
    allowance = frac * vals[0]
    for t in set(tiers):
        members = [vals[i] for i, x in enumerate(tiers) if x == t]
        assert max(members) - min(members) <= allowance + 1e-9


def test_cliffs_are_identical_under_both_methods():
    """Only the grouping was defective. A cliff is one enormous step and the
    outlier-sensitive bar is right for that, so it is deliberately shared."""
    for vals in (_one_star(), [100.0 - 2.0 * i for i in range(30)],
                 [50.0, 49.0, 48.0, 10.0, 9.0, 8.0]):
        _t1, c1 = assign_tiers(vals, method="gap_sd")
        _t2, c2 = assign_tiers(vals, method="anchor_frac")
        assert c1 == c2


def test_the_default_is_todays_behaviour_exactly():
    """Repo rule: a new knob defaults to what the engine already did."""
    for vals in (_one_star(), [9.0, 8.0, 4.0, 3.9, 1.0], [5.0, 5.0, 5.0]):
        assert assign_tiers(vals) == assign_tiers(vals, method="gap_sd")


def test_an_unknown_method_raises_rather_than_silently_picking_one():
    import pytest
    with pytest.raises(ValueError, match="tiers.method"):
        assign_tiers([3.0, 2.0, 1.0], method="whatever")


def test_anchor_frac_degrades_when_the_best_player_is_worthless():
    """A position whose top player is at or below replacement has no tier
    structure to describe, and a fraction of a non-positive number is not a
    threshold."""
    tiers, _ = assign_tiers([0.0, -5.0, -20.0], method="anchor_frac")
    assert tiers == [1, 1, 1]
    tiers, _ = assign_tiers([-1.0, -5.0], method="anchor_frac")
    assert tiers == [1, 1]


def test_anchor_frac_edges():
    assert assign_tiers([], method="anchor_frac") == ([], [])
    assert assign_tiers([5.0], method="anchor_frac") == ([1], [False])

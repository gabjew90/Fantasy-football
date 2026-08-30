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

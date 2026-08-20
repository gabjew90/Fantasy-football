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


def test_no_market_rows_always_included():
    from draftkit.tiers import build_tiers

    df = _pool_df([{"sleeper_id": "z", "name": "Ghost", "pos": "WR",
                    "proj_pts": 150.0, "vorp": -50.0, "adp": None, "ecr": None,
                    "proj_source": "no_market"}])
    out = build_tiers(df, _cfg())
    assert "Ghost" in out["name"].to_list()

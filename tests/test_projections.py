import polars as pl

from draftkit.projections import _no_market_fallback


def test_no_market_fallback_rows():
    market = pl.DataFrame({
        "sleeper_id": ["1"], "name": ["A"], "pos": ["WR"], "team": ["SFO"],
        "ecr": [10.0], "ecr_sd": [1.0], "adp": [12.0], "bye": [8],
    })
    usage = pl.DataFrame({
        "sleeper_id": ["1", "2", "3", None],
        "name": ["A", "B", "C", "D"],
        "pos": ["WR", "WR", "TE", "RB"],
        "team_2025": ["SF", "TB", "CIN", "NO"],
        "fpts_total": [200.0, 88.6, 30.0, 100.0],
    })
    fb = _no_market_fallback(market, usage, floor=60.0)
    # B: above floor and not in market. C: below floor. D: no sleeper id. A: already in market.
    assert fb["sleeper_id"].to_list() == ["2"]
    assert fb["ecr"].to_list() == [None]
    assert fb["adp"].to_list() == [None]


def test_market_curve_uses_adp_when_ecr_missing():
    from draftkit.projections import _market_curve

    rows = [
        {"pos": "WR", "ecr": float(i + 1), "adp": None,
         "proj_model_pts": 300.0 - 20 * i, "games": 12}
        for i in range(8)
    ]
    # ADP-only player: no ECR, no stats — must still get a curve prediction
    rows.append({"pos": "WR", "ecr": None, "adp": 5.0,
                 "proj_model_pts": None, "games": None})
    df = pl.DataFrame(rows)
    out = _market_curve(df)
    assert out["proj_market_pts"][-1] is not None


def test_apply_availability():
    from draftkit.projections import _apply_availability

    df = pl.DataFrame({
        "sleeper_id": ["1", "2", "3"],
        "proj_pts": [200.0, 150.0, 100.0],
    })
    av = pl.DataFrame({
        "sleeper_id": ["1", "2"],
        "status": ["out", "compromised"],
    })
    out = _apply_availability(df, av)
    assert out.filter(pl.col("sleeper_id") == "1")["proj_pts"][0] == 0.0
    assert out.filter(pl.col("sleeper_id") == "1")["avail_status"][0] == "out"
    assert out.filter(pl.col("sleeper_id") == "2")["proj_pts"][0] == 150.0
    assert out.filter(pl.col("sleeper_id") == "2")["avail_status"][0] == "compromised"
    assert out.filter(pl.col("sleeper_id") == "3")["avail_status"][0] is None


def test_no_market_fallback_disabled_when_floor_zero_matches_nothing():
    market = pl.DataFrame({
        "sleeper_id": ["1"], "name": ["A"], "pos": ["WR"], "team": ["SFO"],
        "ecr": [10.0], "ecr_sd": [1.0], "adp": [12.0], "bye": [8],
    })
    usage = pl.DataFrame({
        "sleeper_id": ["2"], "name": ["B"], "pos": ["WR"],
        "team_2025": ["TB"], "fpts_total": [1.0],
    })
    fb = _no_market_fallback(market, usage, floor=60.0)
    assert fb.height == 0

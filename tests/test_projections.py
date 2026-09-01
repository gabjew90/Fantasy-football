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


def test_alpha_by_player_type(monkeypatch, tmp_path):
    """Stable veterans lean stats (0.65); new-team players lean market (0.40)."""
    import polars as pl
    from draftkit.projections import default_projection

    class FakeCfg(dict):
        def path(self, kind):
            return tmp_path

        def scoped(self, path):     # single-league fixture: identity
            return path

    cfg = FakeCfg({"projections": {
        "model_alpha": 0.55, "shrink_k": 5, "expected_games": 16.0,
        "no_market_floor": 0,
        "alpha_by_type": {"stable_veteran": 0.65, "volatile": 0.40}}})
    n = 8  # the market curve needs >=6 veterans per position to fit
    ids = ["a", "b"] + [f"x{i}" for i in range(n - 2)]
    names = ["Stable Vet", "New Team Guy"] + [f"Filler {i}" for i in range(n - 2)]
    teams_25 = ["ATL", "MIA"] + ["ATL"] * (n - 2)
    usage = pl.DataFrame({
        "sleeper_id": ids, "gsis_id": [f"g{i}" for i in ids],
        "name": names, "pos": ["WR"] * n,
        "games": [16.0] * n, "ppg": [12.0 - 0.5 * i for i in range(n)],
        "fpts_total": [192.0] * n,
        "wopr": [0.5] * n, "target_share": [0.2] * n,
        "air_yards_share": [0.3] * n, "tprr": [0.2] * n, "yprr": [1.8] * n,
        "routes_proxy": [500.0] * n, "hv_touches": [10.0] * n,
        "offense_snap_pct": [0.9] * n, "avg_separation": [3.0] * n,
        "exp_games": [16.0] * n, "team_2025": teams_25,
    })
    market = pl.DataFrame({
        "sleeper_id": ids, "name": names,
        "pos": ["WR"] * n, "team": ["ATL"] * n,
        "ecr": [30.0 + i for i in range(n)], "ecr_sd": [3.0] * n,
        "adp": [30.0 + i for i in range(n)], "bye": [5] * n,
    })
    out = default_projection(cfg, usage, market)
    alphas = dict(zip(out["name"], out["alpha_used"]))
    assert alphas["Stable Vet"] == 0.65
    assert alphas["New Team Guy"] == 0.40

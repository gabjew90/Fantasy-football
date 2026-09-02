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


def test_consensus_is_parallel_by_default_and_replaces_the_curve_only_when_asked(monkeypatch, tmp_path):
    """Projection overhaul item 1: the stat-line column rides alongside the
    blend and changes nothing unless market_source says stat_lines; then it
    stands in for the log-rank curve where it exists and the curve remains
    the fallback where it does not."""
    import polars as pl
    from draftkit import consensus as C
    from draftkit.projections import default_projection

    class FakeCfg(dict):
        def path(self, kind):
            return tmp_path

        def scoped(self, path):
            return path

    def mk(source, enabled=True):
        return FakeCfg({"season": 2026, "projections": {
            "model_alpha": 0.5, "shrink_k": 5, "expected_games": 16.0, "no_market_floor": 0,
            "market_source": source, "consensus": {"enabled": enabled, "line_games": 17}}})

    n = 8
    ids = [f"p{i}" for i in range(n)]
    usage = pl.DataFrame({
        "sleeper_id": ids, "gsis_id": [f"g{i}" for i in ids], "name": ids, "pos": ["WR"] * n,
        "games": [16.0] * n, "ppg": [12.0 - 0.5 * i for i in range(n)], "fpts_total": [192.0] * n,
        "wopr": [0.5] * n, "target_share": [0.2] * n, "air_yards_share": [0.3] * n,
        "tprr": [0.2] * n, "yprr": [1.8] * n, "routes_proxy": [500.0] * n, "hv_touches": [10.0] * n,
        "offense_snap_pct": [0.9] * n, "avg_separation": [3.0] * n, "exp_games": [16.0] * n,
        "team_2025": ["ATL"] * n})
    market = pl.DataFrame({"sleeper_id": ids, "name": ids, "pos": ["WR"] * n, "team": ["ATL"] * n,
                           "ecr": [30.0 + i for i in range(n)], "ecr_sd": [3.0] * n,
                           "adp": [30.0 + i for i in range(n)], "bye": [5] * n})
    # consensus knows all but the last player
    cons = pl.DataFrame({"sleeper_id": ids[:-1], "proj_consensus_pts": [100.0] * (n - 1),
                         "adp_sleeper": [40.0] * (n - 1)})
    monkeypatch.setattr(C, "load_consensus", lambda cfg, **kw: (cons, {}))

    base = default_projection(mk("ecr_curve", enabled=False), usage, market)
    par = default_projection(mk("ecr_curve"), usage, market)
    assert par["proj_pts"].to_list() == base["proj_pts"].to_list(), "parallel column must not move the blend"
    assert par["proj_consensus_pts"].to_list()[:-1] == [100.0] * (n - 1)
    assert par["proj_consensus_pts"][-1] is None
    assert set(par["market_source_used"].to_list()) == {"ecr_curve"}

    sw = default_projection(mk("stat_lines"), usage, market)
    used = dict(zip(sw["sleeper_id"], sw["market_source_used"]))
    assert used["p0"] == "stat_lines" and used[ids[-1]] == "ecr_curve"
    assert sw.filter(pl.col("sleeper_id") == "p0")["proj_market_pts"][0] == 100.0
    assert sw["proj_pts"].to_list() != base["proj_pts"].to_list()


def test_qb_usage_regression_credits_rushing_volume():
    """Usage-side fix 2: a QB's model term is no longer his shrunk PPG alone.
    Two QBs with the same shrunk PPG but different rushing volume must part,
    the runner above and the pocket passer below, and non-QB positions are
    untouched by the change."""
    import polars as pl
    from draftkit.projections import _usage_adjusted_ppg

    n = 20
    carries = [20 + 100 * (i / (n - 1)) for i in range(n)]        # 20..120 per season
    games = [16.0] * n
    # league of QBs where ppg rises with carries per game (1.5 pts per carry/g)
    ppg = [14.0 + 1.5 * c / g for c, g in zip(carries, games)]
    rows = {
        "gsis_id": [f"q{i}" for i in range(n)], "sleeper_id": [f"s{i}" for i in range(n)],
        "name": [f"QB {i}" for i in range(n)], "pos": ["QB"] * n,
        "games": games, "ppg": ppg, "carries": carries, "offense_snap_pct": [0.95] * n,
        "wopr": [None] * n, "hv_touches": [0.0] * n,
    }
    # two probes with IDENTICAL ppg and games: one runs, one does not
    for tag, c in (("runner", 130.0), ("pocket", 15.0)):
        rows["gsis_id"].append(tag); rows["sleeper_id"].append(tag); rows["name"].append(tag)
        rows["pos"].append("QB"); rows["games"].append(10.0); rows["ppg"].append(18.0)
        rows["carries"].append(c); rows["offense_snap_pct"].append(0.95)
        rows["wopr"].append(None); rows["hv_touches"].append(0.0)
    usage = pl.DataFrame(rows, schema_overrides={"wopr": pl.Float64})
    out = _usage_adjusted_ppg(usage, shrink_k=5)
    m = dict(zip(out["gsis_id"], out["model_ppg"]))
    assert m["runner"] > m["pocket"] + 1.0, (m["runner"], m["pocket"])
    # the shrunk value both share sits between them
    pos_mean = sum(ppg) / n * 0 + float(usage.filter(pl.col("games") >= 4)["ppg"].mean())
    shrunk = 18.0 * 10 / 15 + pos_mean * 5 / 15
    assert m["pocket"] < shrunk < m["runner"]


def test_qb_regression_falls_back_to_shrunk_ppg_on_thin_data():
    import polars as pl
    from draftkit.projections import _usage_adjusted_ppg

    n = 12   # >= 12 rows enters the position branch, < 15 fit rows -> no regression
    usage = pl.DataFrame({
        "gsis_id": [f"q{i}" for i in range(n)], "sleeper_id": [f"s{i}" for i in range(n)],
        "name": [f"QB {i}" for i in range(n)], "pos": ["QB"] * n, "games": [16.0] * n,
        "ppg": [15.0 + i for i in range(n)], "carries": [50.0] * n, "offense_snap_pct": [0.9] * n,
        "wopr": [None] * n, "hv_touches": [0.0] * n}, schema_overrides={"wopr": pl.Float64})
    out = _usage_adjusted_ppg(usage, shrink_k=5)
    pos_mean = float(usage["ppg"].mean())
    expected = [(15.0 + i) * 16 / 21 + pos_mean * 5 / 21 for i in range(n)]
    got = out.sort("gsis_id")["model_ppg"].to_list()
    exp_sorted = [e for _, e in sorted(zip([f"q{i}" for i in range(n)], expected))]
    assert all(abs(a - b) < 1e-9 for a, b in zip(got, exp_sorted))

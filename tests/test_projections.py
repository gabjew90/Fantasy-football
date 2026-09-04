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
    from draftkit.projections import model_projection as default_projection

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
    from draftkit.projections import model_projection as default_projection

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


def test_alpha_cap_by_position_sits_under_the_type_alpha(monkeypatch, tmp_path):
    """Item 2's verdict: WR usage weight capped (0.2); other positions keep
    their player-type alpha. The cap can only lower alpha, never raise it."""
    import polars as pl
    from draftkit.projections import model_projection as default_projection

    class FakeCfg(dict):
        def path(self, kind):
            return tmp_path

        def scoped(self, path):
            return path

    cfg = FakeCfg({"projections": {
        "model_alpha": 0.55, "shrink_k": 5, "expected_games": 16.0, "no_market_floor": 0,
        "alpha_by_type": {"stable_veteran": 0.65, "volatile": 0.40},
        "alpha_cap_by_position": {"WR": 0.2, "QB": 0.9}}})
    n = 8
    def frame(pos, prefix):
        ids = [f"{prefix}{i}" for i in range(n)]
        usage = pl.DataFrame({
            "sleeper_id": ids, "gsis_id": [f"g{prefix}{i}" for i in range(n)], "name": ids, "pos": [pos] * n,
            "games": [16.0] * n, "ppg": [12.0 - 0.5 * i for i in range(n)], "fpts_total": [192.0] * n,
            "wopr": [0.5] * n, "target_share": [0.2] * n, "air_yards_share": [0.3] * n,
            "tprr": [0.2] * n, "yprr": [1.8] * n, "routes_proxy": [500.0] * n, "hv_touches": [10.0] * n,
            "offense_snap_pct": [0.9] * n, "avg_separation": [3.0] * n, "exp_games": [16.0] * n,
            "team_2025": ["ATL"] * n, "carries": [10.0] * n})
        market = pl.DataFrame({"sleeper_id": ids, "name": ids, "pos": [pos] * n, "team": ["ATL"] * n,
                               "ecr": [30.0 + i for i in range(n)], "ecr_sd": [3.0] * n,
                               "adp": [30.0 + i for i in range(n)], "bye": [5] * n})
        return usage, market
    uw, mw = frame("WR", "w"); ur, mr = frame("RB", "r")
    out = default_projection(cfg, pl.concat([uw, ur]), pl.concat([mw, mr]))
    a = dict(zip(out["sleeper_id"], out["alpha_used"]))
    assert all(a[f"w{i}"] == 0.2 for i in range(n)), "WR stable veterans capped at 0.2"
    assert all(a[f"r{i}"] == 0.65 for i in range(n)), "RB untouched"
    # a cap above the type alpha changes nothing (QB cap 0.9 vs 0.65) -- exercised via config parse only


# ---- DECISIONS #40: the market curve that stopped decaying inside its fit ----

def _curve_rows(pos="RB", n=100, fitted=60, b0=-45.0, c0=-0.6, base=340.0):
    """n players at one position, values shaped like the real board: a log decay
    plus a mild linear one. The first `fitted` are veterans (games 16) and are
    the curve's fit population; the rest are tail rows with no stats. `adp` is
    2x the rank so the log-only fit is a pure reparameterisation of rank, which
    lets one test isolate the regressor swap from the shape change."""
    import math
    rows = []
    for i in range(n):
        vet = i < fitted
        v = base + b0 * math.log(i + 1) + c0 * i
        rows.append({
            "pos": pos, "ecr": float(i + 1) * 2.0, "adp": float(i + 1) * 2.0,
            "proj_model_pts": v if vet else None,
            "games": 16 if vet else None,
        })
    return pl.DataFrame(rows)


def test_market_curve_tail_off_is_byte_identical():
    """The historical arm must survive untouched: no tail dict, an explicit
    off, and a yaml-1.1 bare `off` (which parses to False) all agree."""
    from draftkit.projections import _market_curve

    df = _curve_rows()
    base = _market_curve(df)["proj_market_pts"].to_list()
    for tail in ({"mode": "off"}, {"mode": False}, {}, None):
        assert _market_curve(df, tail)["proj_market_pts"].to_list() == base


def test_regressor_swap_is_a_reparameterisation_when_adp_tracks_rank():
    """Isolates edit 1. With adp = 2 x rank, ln(2r) = ln 2 + ln(r), so the
    log-only fit absorbs the swap into its intercept and predictions are
    unchanged. On the real board adp does NOT track rank at the tail -- that
    saturation is the defect -- so any difference there is the point."""
    from draftkit.projections import _market_curve

    df = _curve_rows()
    off = _market_curve(df, {"mode": "off"})["proj_market_pts"].to_list()
    rank = _market_curve(df, {"mode": "rank"})["proj_market_pts"].to_list()
    assert max(abs(a - b) for a, b in zip(off, rank)) < 1e-6


def test_market_curve_tail_covers_exactly_the_same_rows():
    """The arms are only comparable if proj_market_pts is non-null on the same
    rows. Includes an adp-only row and a row with neither rank."""
    from draftkit.projections import _market_curve

    df = pl.concat([
        _curve_rows(),
        pl.DataFrame([{"pos": "RB", "ecr": None, "adp": 190.0,
                       "proj_model_pts": None, "games": None},
                      {"pos": "RB", "ecr": None, "adp": None,
                       "proj_model_pts": None, "games": None}]),
    ])
    masks = {
        mode: [v is None for v in _market_curve(df, {"mode": mode})["proj_market_pts"]]
        for mode in ("off", "rank", "rank_lin", "full")
    }
    assert masks["off"] == masks["rank"] == masks["rank_lin"] == masks["full"]
    assert masks["off"][-2] is False and masks["off"][-1] is True


def test_market_curve_tail_keeps_decaying_where_log_has_gone_flat():
    """The defect in one assertion: across the deep band the log-only curve
    barely moves, and the linear term must drop materially further.

    Deliberately NOT asserting that the head is unchanged. The linear term
    reshapes the whole fitted curve, so on any synthetic population the head
    moves too. Whether it moves on the REAL board is a pass criterion of the
    gate (top-24 MAE ratio <= 1.01, no top-12 projection moving > 2.0 pts),
    measured there rather than asserted here on data that cannot represent it.
    """
    from draftkit.projections import _market_curve

    df = _curve_rows()
    off = _market_curve(df, {"mode": "off"})["proj_market_pts"].to_list()
    lin = _market_curve(df, {"mode": "rank_lin"})["proj_market_pts"].to_list()
    assert (lin[36] - lin[59]) > (off[36] - off[59]), "deep band must fall further"
    assert lin[59] < off[59], "the deep band must come DOWN, not up"
    assert all(a >= b - 1e-9 for a, b in zip(lin, lin[1:])), "still a decaying curve"


def test_market_curve_linear_term_is_position_not_data_selected():
    """The position list is the selector (DECISIONS #40). A TE cell with a
    strongly decaying fit still gets log-only, however good the linear fit is."""
    from draftkit.projections import _market_curve, TAIL_LINEAR_POSITIONS

    assert TAIL_LINEAR_POSITIONS == ("RB", "WR")
    df = _curve_rows(pos="TE")
    rank = _market_curve(df, {"mode": "rank"})["proj_market_pts"].to_list()
    lin = _market_curve(df, {"mode": "rank_lin"})["proj_market_pts"].to_list()
    assert lin == rank


def test_market_curve_tail_needs_a_deep_enough_fit_population():
    """min_fit is the thin-cell safety net: 20 veterans falls back to log-only."""
    from draftkit.projections import _market_curve

    df = _curve_rows(n=40, fitted=20)
    rank = _market_curve(df, {"mode": "rank"})["proj_market_pts"].to_list()
    lin = _market_curve(df, {"mode": "rank_lin", "min_fit": 30})["proj_market_pts"].to_list()
    assert lin == rank


def test_market_curve_tail_is_floored_at_zero():
    from draftkit.projections import _market_curve

    df = _curve_rows(n=400, fitted=60, b0=-80.0, c0=-2.0)
    for mode in ("rank", "rank_lin", "full"):
        vals = [v for v in _market_curve(df, {"mode": mode})["proj_market_pts"] if v is not None]
        assert min(vals) >= 0.0


def test_market_curve_full_continues_on_the_tangent_past_the_fit():
    """Past the last fitted rank the curve may not go FLATTER than it was at
    the last point the data supported."""
    from draftkit.projections import _market_curve

    df = _curve_rows()
    lin = _market_curve(df, {"mode": "rank_lin"})["proj_market_pts"].to_list()
    full = _market_curve(df, {"mode": "full"})["proj_market_pts"].to_list()
    assert lin[:60] == full[:60], "inside the fit population the arms agree"
    assert full[99] < lin[99] - 1.0, "and it keeps falling faster outside it"


def test_market_curve_tail_rejects_an_unknown_mode():
    from draftkit.projections import _market_curve
    import pytest

    with pytest.raises(ValueError, match="market_curve_tail.mode"):
        _market_curve(_curve_rows(), {"mode": "steeper"})

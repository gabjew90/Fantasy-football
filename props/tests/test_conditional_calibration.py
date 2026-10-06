"""Tier 2 (reports/tier2_conditional_calibration.md): the stage-2 samplers and the
analysis tool are checked against cases with a known answer before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine" / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import model as M  # noqa: E402
import conditional_calibration as CC  # noqa: E402


def test_stage_two_samplers_hold_their_means():
    rng = np.random.default_rng(1)
    rec, yds = M.receiving_given_targets(rng, 200_000, 8, 0.65, 8.0, 1.065)
    assert abs(rec.mean() - 8 * 0.65) < 0.02
    assert abs(yds.mean() - 8 * 8.0) < 0.3, "yards | targets average targets x yards per target"
    grid = np.linspace(-3, 3, 61)                      # centred residuals
    ru = M.rushing_given_carries(rng, 200_000, 15, 4.4, grid, 0.3)
    assert abs(ru.mean() - 15 * 4.4) < 0.3
    assert M.rush_eff_sd({"eff_sd_rush": 0.3, "eff_sd_qb": 0.15}, True) == 0.15
    assert M.rush_eff_sd({"eff_sd_rush": 0.3, "eff_sd_qb": None}, True) == 0.3
    assert M.rush_eff_sd({"eff_sd_rush": 0.3, "eff_sd_qb": 0.15}, False) == 0.3


def _fake_results(pit_fn, n_games=400, seed=2):
    rng = np.random.default_rng(seed)
    rows = []
    for gi in range(n_games):
        for team in ("A", "B"):
            for p in range(6):
                rows.append({"season": 2023, "week": 2 + gi % 17, "team": f"{team}{gi}", "game_id": f"g{gi}",
                             "act_targets": rng.integers(0, 12), "act_carries": rng.integers(0, 22),
                             "mean_tgt": rng.uniform(0, 12), "mean_car_model": rng.uniform(0, 22),
                             "rush_pop": p < 2, "qb_pop": p == 5,
                             "pit_tgt": pit_fn(rng), "pit_rec_c": pit_fn(rng), "pit_yds_c": pit_fn(rng),
                             "pit_car": pit_fn(rng), "pit_car_qb": pit_fn(rng),
                             "pit_rush_c": pit_fn(rng)})
    return pd.DataFrame(rows)


def _run(tmp_path, monkeypatch, R):
    f = tmp_path / "res.pkl"
    pd.to_pickle({"kind": "harness", "results": R}, f)
    monkeypatch.setattr(CC, "team_margins", lambda seasons: R[["season", "week", "team"]].assign(margin=0))
    monkeypatch.setattr(CC, "team_context", lambda seasons: R[["season", "week", "team"]].drop_duplicates()
                        .assign(spread=0.0, backup_start=False))
    out = tmp_path / "out.json"
    CC.main([str(f), "--seasons", "2023", "--reps", "300", "--out", str(out)])
    import json
    return {c["check"]: c["rows"][0] for c in json.loads(out.read_text(encoding="utf-8"))}


def test_a_calibrated_model_reads_twenty_percent_outside(tmp_path, monkeypatch):
    rep = _run(tmp_path, monkeypatch, _fake_results(lambda r: r.uniform()))
    for check, row in rep.items():
        assert 0.17 < row["outside"] < 0.23, (check, row)
        assert row["verdict"] == "ok", (check, row)


def test_a_too_narrow_and_a_too_wide_model_are_flagged(tmp_path, monkeypatch):
    narrow = _run(tmp_path, monkeypatch, _fake_results(lambda r: r.beta(0.6, 0.6)))
    assert all(r["verdict"] == "too narrow" for r in narrow.values())
    wide = _run(tmp_path, monkeypatch, _fake_results(lambda r: r.beta(2.5, 2.5)))
    assert all(r["verdict"] == "too wide" for r in wide.values())


def test_pit_from_the_model_itself_is_uniform():
    """The conditional PIT of an outcome drawn from the same sampler is uniform: the
    harness reads 'ok' on a model that is right by construction."""
    rng = np.random.default_rng(3)
    pits = []
    for _ in range(3000):
        rec, yds = M.receiving_given_targets(rng, 1000, 7, 0.62, 7.5, 1.065)
        y_rec, y_yds = M.receiving_given_targets(rng, 1, 7, 0.62, 7.5, 1.065)
        u = rng.uniform()
        pits.append((yds < y_yds[0]).mean() + u * (yds == y_yds[0]).mean())
    pits = np.array(pits)
    assert 0.18 < ((pits < 0.1) | (pits > 0.9)).mean() < 0.22


def test_stage_one_is_bucketed_by_the_projection_not_the_outcome():
    """Bucketing a volume forecast by the actual volume selects on the outcome: a calibrated
    forecast would read 'too narrow' in its high-actual bucket. By projection it reads ok."""
    rng = np.random.default_rng(4)
    rows = []
    for gi in range(600):
        for p in range(6):
            mu = rng.uniform(1, 11)
            draws = rng.poisson(mu, 1000)
            y = rng.poisson(mu)
            pit = (draws < y).mean() + rng.uniform() * (draws == y).mean()
            rows.append({"game_id": f"g{gi}", "pit": pit, "proj": mu, "act": y})
    d = pd.DataFrame(rows)
    hi_act = d[d.act >= 10]
    assert CC.shares(hi_act, 300, rng)["verdict"] == "too narrow", "selection on the outcome"
    hi_proj = d[d.proj >= 9.5]
    assert CC.shares(hi_proj, 300, rng)["verdict"] == "ok"


def test_part_b_picks_the_value_closest_to_twenty_percent_per_stage():
    """Only the flagged stage's own knob moves; rows that move another knob are not its
    candidates; ties keep the shipped value."""
    rng = np.random.default_rng(5)
    base = {"share_conc_targets": 40.0, "share_conc_carries": 20.0, "catch_conc": None,
            "eff_sd_rec": 0.0, "eff_sd_rush": 0.3}
    grid = [dict(base), {**base, "share_conc_targets": 80.0}, {**base, "eff_sd_rush": 0.15}]
    width = {0: 0.6, 1: 1.0, 2: 1.0}            # beta(a, a): a < 1 too narrow, a = 1 calibrated
    frames = [_fake_results(lambda r, a=width[i]: r.beta(a, a), n_games=300, seed=10 + i) for i in range(3)]
    table, picks = CC.grid_pick(grid, frames, 200, rng, {"stage 1: targets", "stage 2: rushing yards | carries (backs)"})
    assert picks == {"share_conc_targets": 80.0, "eff_sd_rush": 0.15}
    cands = [t["value"] for t in table if t["stage"] == "stage 1: targets"]
    assert cands == [40.0, 80.0], "the eff_sd_rush row is not a target-concentration candidate"
    _, picks2 = CC.grid_pick(grid, frames, 200, rng, set())
    assert picks2 == {}, "an unflagged stage never moves"


def test_a_qb_on_the_opening_dropbacks_started_and_a_gadget_snap_does_not_unseat_him():
    import backtest as BT
    pbp = pd.DataFrame({"posteam": ["NO"] * 5 + ["TB"] * 3, "week": [3] * 8, "play_type": ["pass"] * 8,
                        "play_id": [1, 2, 3, 4, 5, 1, 2, 3],
                        "passer_player_id": ["HILL", "CARR", "CARR", "CARR", "CARR", "MAYF", "MAYF", "MAYF"]})
    op = BT.opening_passers(pbp)
    assert "CARR" in op[("NO", 3)] and "HILL" in op[("NO", 3)], "a gadget first snap does not unseat the starter"
    assert op[("TB", 3)] == {"MAYF"}
    assert "BAKER_BACKUP" not in op[("TB", 3)]


def test_round_29_moves_the_backs_carries_and_holds_the_qb():
    fit = {"plays": {"intercept": 47.8, "per_spread_pt": 0.146, "per_total_pt": 0.20},
           "pass_rate": {"intercept": 0.371, "per_spread_pt": -0.0022, "per_total_pt": 0.0038}}
    assert M.market_rush_volume(7.0, 47.0, fit, 27.0, 0.0) == (27.0, 1.0), "weight 0: history, untouched"
    c, f = M.market_rush_volume(7.0, 47.0, fit, 27.0, 1.0)
    plays = 47.8 + 0.146 * 7 + 0.20 * 47
    pr = 0.371 - 0.0022 * 7 + 0.0038 * 47
    assert abs(c - plays * (1 - pr)) < 1e-9 and abs(f - c / 27.0) < 1e-12
    c_dog, _ = M.market_rush_volume(-7.0, 47.0, fit, 27.0, 1.0)
    assert c > c_dog, "a favourite runs more than an underdog"
    rs = M.hold_qb_carries([0.5, 0.2, 0.15], 2, 1.2)
    assert abs(rs[2] * 1.2 - 0.15) < 1e-12 and rs[0] == 0.5, "his expected carries unchanged, the backs' move"
    assert list(M.hold_qb_carries([0.5, 0.15], None, 1.2)) == [0.5, 0.15]


def test_pit_deciles_show_shape_one_range_cannot():
    rng = np.random.default_rng(6)
    assert all(abs(x - 0.1) < 0.01 for x in CC.pit_deciles(pd.Series(rng.uniform(size=50_000))))
    narrow = CC.pit_deciles(pd.Series(rng.beta(0.6, 0.6, 50_000)))
    assert narrow[0] > 0.15 and narrow[-1] > 0.15 and narrow[5] < 0.08, "too narrow piles into the ends"
    tilt = CC.pit_deciles(pd.Series(rng.beta(1.0, 1.6, 50_000)))
    assert tilt[0] > tilt[-1] * 2, "a model that runs high piles outcomes into the low tenths"


def test_the_yards_shape_exponent_keeps_the_mean_and_slows_the_spread():
    rng = np.random.default_rng(12)
    for T in (3, 12):
        a = M.receiving_given_targets(np.random.default_rng(1), 200_000, T, 0.65, 8.0, 1.065)[1]
        b = M.receiving_given_targets(np.random.default_rng(1), 200_000, T, 0.65, 8.0, 1.065,
                                      {"catch_shape_exp": 1.3})[1]
        assert abs(a.mean() - b.mean()) < 0.01 * a.mean() + 0.1, "the mean stays"
        if T == 12:
            assert b.std() < 0.95 * a.std(), "with many catches the spread grows more slowly"


def test_combined_yards_counts_a_zero_side_as_zero_not_as_a_missing_game():
    """Outside review 2026-10-06: 0 targets / 15 carries and 5 targets / 0 carries were
    dropped from the combined-yards score; only 'neither' is left out."""
    import backtest as BT
    n = 4
    rush, yds = np.array([60.0, 70, 80, 90]), np.array([10.0, 20, 30, 40])
    assert BT.rr_given_volume(0, 15, None, rush, n).tolist() == rush.tolist(), "no target: rushing alone"
    assert BT.rr_given_volume(5, 0, yds, None, n).tolist() == yds.tolist(), "no carry: receiving alone"
    assert BT.rr_given_volume(3, 15, yds, rush, n).tolist() == (yds + rush).tolist()
    assert BT.rr_given_volume(0, 0, None, None, n) is None, "never touched the ball: void"
    assert BT.rr_given_volume(3, 15, None, rush, n) is None, "volume without a draw is not a zero"


def test_the_exact_receptions_chance_matches_the_sampler():
    """The closed form against model.receiving_given_targets at 400,000 draws, binomial and
    beta-binomial, plus the edges (line above the targets, line below zero)."""
    import backtest as BT
    for T, cr, L, conc in ((6, 0.65, 3.5, None), (10, 0.7, 7.5, None), (4, 0.6, 3.5, 50.0), (8, 0.02, 0.5, None)):
        rec, _ = M.receiving_given_targets(np.random.default_rng(1), 400_000, T, cr, 8.0, 1.4,
                                           {"catch_conc": conc} if conc else None)
        assert BT.receptions_over_exact(T, cr, L, conc) == pytest.approx(float((rec > L).mean()), abs=0.004), (T, cr, L)
    assert BT.receptions_over_exact(3, 0.7, 3.5) == 0.0 and BT.receptions_over_exact(3, 0.7, -0.5) == 1.0

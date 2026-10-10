"""The tuning and test harness (props/calc/harness.py): who is tested, the
re-blend at another k, the band table, on hand-made inputs."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from props.calc import harness, rates  # noqa: E402


def _games():
    rows = []
    for w in (1, 2, 3, 4):
        for g, c, t, q in (("rb1", 15, 2, 0), ("rb2", 5, 1, 0), ("wr1", 0, 9, 0), ("wr2", 0, 7, 0), ("te1", 0, 5, 0),
                           ("wr3", 0, 4, 0), ("qb1", 3, 0, 20)):
            if g == "rb2" and w == 4:
                continue
            rows.append(dict(game_id=f"g{w}", season=2026, week=w, team="A", gsis_id=g, carries=c, targets=t,
                             completions=q))
    rows.append(dict(game_id="g0", season=2026, week=1, team="B", gsis_id="late", carries=30, targets=0,
                     completions=0))
    return pd.DataFrame(rows)


POS = {"rb1": "RB", "rb2": "RB", "qb1": "QB", "wr1": "WR", "wr2": "WR", "wr3": "WR", "te1": "TE", "late": "RB"}


def _b(games):
    return type("B", (), {"games": games, "position_at": lambda self, g, s, w: POS.get(g)})()


def test_who_is_tested_is_chosen_from_games_before_the_week():
    b = _b(_games())
    got = set(harness.tested(b, 2026, 4, 3))
    # lead back rb1 (45 carries; the QB's 9 carries do not make him a back), top 3 by targets wr1, wr2,
    # te1, completion leader qb1; all played week 4
    assert got == {("rb1", "A", "rush_yds"), ("qb1", "A", "pass_yds")} | {
        (g, "A", m) for g in ("wr1", "wr2", "te1") for m in ("receptions", "rec_yds")}
    assert harness.tested(b, 2026, 3, 3) == []            # two games before week 3: nobody has 3
    # the lead back missed a game (2 of 3): his role is not tested, and rb2 is not promoted into it
    g = _games()
    g = g[~((g["gsis_id"] == "rb1") & (g["week"] == 1))]
    assert not any(m == "rush_yds" for _, _, m in harness.tested(_b(g), 2026, 4, 3))
    # a rushing QB with the most carries is not the lead back
    g2 = _games().assign(carries=lambda d: np.where(d["gsis_id"] == "qb1", 30, d["carries"]))
    assert ("rb1", "A", "rush_yds") in harness.tested(_b(g2), 2026, 4, 3)


def test_coverage_scores_a_calibrated_whole_number_model_at_80():
    rng = np.random.default_rng(1)
    fixed = {"range_low_pct": 10, "range_high_pct": 90}
    sim = rng.poisson(5.0, 20000).astype(float)
    actual = rng.poisson(5.0, 4000)
    frac, incl = zip(*(harness.coverage(sim, a, fixed) for a in actual))
    assert np.mean(frac) == pytest.approx(0.80, abs=0.015)        # the fractional score
    assert np.mean(incl) > 0.85                                   # the inclusive count runs high


def test_conversion_passes_a_calibrated_synthetic_market():
    from props.calc import settings
    fixed = settings.load()["fixed"]
    rng = np.random.default_rng(2)
    n = 2500
    df = pd.DataFrame({"market": "receptions", "gsis_id": [f"p{i}" for i in range(n)], "usual": 6.0,
                       "actual_work": 6, "own": 0.65, "n": 100, "base": 0.65})
    df["actual_stat"] = rng.binomial(6, 0.65, n).astype(float)    # the truth: exactly the model's catch rate
    df.attrs["resid"] = {}
    k = {"carry_r": 16, "target_r": 8, "completion_r": 10, "k_ypc": 150, "day_sd": 0.15, "k_catch": 60,
         "k_ypr": 50, "k_ypcomp": 150}
    res = harness.conversion(df, "receptions", fixed, k)
    assert 0.77 <= res["range_coverage"] <= 0.83 and res["pass_range"]
    for band in res["bands"]:
        if band["games"] >= 300:
            assert abs(band["stated"] - band["actual"]) <= 0.03, band
    assert res["left_out"]["no workload"] == 0 and res["priced_lines"] + sum(res["left_out"].values()) == 3 * n


def test_the_re_blend_matches_rates_blend():
    r = {"own": 4.6, "n": 120, "base": 4.3, "own_yards": 300.0, "own_catches": 40, "base_ypr": 8.0}
    k = {"k_ypc": 150, "k_catch": 60, "k_ypr": 50, "k_ypcomp": 150}
    assert harness.blended(r, "rush_yds", k) == pytest.approx(rates.blend(4.6 * 120, 120, 4.3, 150))
    catch = rates.blend(4.6 * 120, 120, 4.3, 60)
    assert harness.blended(r, "rec_yds", k) == pytest.approx(catch * rates.blend(300.0, 40, 8.0, 50))


def test_the_band_table_and_pass_marks():
    fixed = {"pass_band_min_games": 2, "pass_band_points": 3, "pass_range_low": 77, "pass_range_high": 83,
             "range_low_pct": 10, "range_high_pct": 90}
    lo, hi = harness._quantiles(np.arange(1, 11, dtype=float), fixed)
    assert (lo, hi) == (1.0, 9.0)
    assert harness._share(np.array([1.0, 2.0, 3.0, 3.0]), 2.0) == pytest.approx(2 / 3)    # a push is void
    assert harness._share(np.array([2.0, 2.0]), 2.0) is None

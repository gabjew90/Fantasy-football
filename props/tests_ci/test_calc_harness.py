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


def test_who_is_tested_is_chosen_from_games_before_the_week():
    b = type("B", (), {"games": _games()})()
    got = set(harness.tested(b, 2026, 4, 3))
    # lead back rb1 (45 carries), top 3 by targets wr1, wr2, te1, completion leader qb1; all played week 4
    assert got == {("rb1", "A", "rush_yds"), ("qb1", "A", "pass_yds")} | {
        (g, "A", m) for g in ("wr1", "wr2", "te1") for m in ("receptions", "rec_yds")}
    assert harness.tested(b, 2026, 3, 3) == []            # two games before week 3: nobody has 3


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

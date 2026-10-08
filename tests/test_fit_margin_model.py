"""scripts/fit_margin_model.py: known answers for the margin model's pieces and its pass rule."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fit_margin_model as F  # noqa: E402


def test_the_favourite_is_read_from_the_home_spread_sign():
    s, m = F.favourite_margin([7.0, -3.5, 0.0], [10, 4, -2])
    # home favoured by 7 won by 10; away favoured by 3.5 lost by 4 (home +4); pick'em read from home
    assert list(s) == [7.0, 3.5, 0.0] and list(m) == [10, -4, -2]


def test_scenarios_split_at_nine_and_a_tie_is_within_one_score():
    assert list(F.outcome([9, 8, 0, -8, -9, 21, -14])) == [0, 1, 1, 1, 2, 0, 2]


def test_empirical_model_counts_shifted_residuals():
    p = F.probs_empirical([7.0], [-10, -1, 0, 3, 5])        # margins -3, 6, 7, 10, 12
    assert np.allclose(p[0], [2 / 5, 3 / 5, 0])
    assert np.allclose(p.sum(1), 1)


def test_a_shifted_margin_on_the_cut_counts_half_to_each_side():
    # spread 3 + residual 5.5 = 8.5: between a real 8 and 9; -8.5 likewise for the underdog
    p = F.probs_empirical([3.0], [5.5, -11.5, 0.0, 10.0])   # margins 8.5, -8.5, 3, 13
    assert np.allclose(p[0], [(0.5 + 1) / 4, (0.5 + 0.5 + 1) / 4, 0.5 / 4])


def test_normal_model_is_symmetric_at_a_pickem_and_sums_to_one():
    p = F.probs_normal([0.0, 7.0], 13.0)
    assert np.allclose(p.sum(1), 1) and abs(p[0, 0] - p[0, 2]) < 1e-12 and p[1, 0] > p[1, 2]


def test_the_pass_rule_needs_both_the_log_loss_margin_and_calibration():
    good = [{"predicted": 0.30, "observed": 0.33}]
    bad = [{"predicted": 0.30, "observed": 0.35}]
    assert F.passes(1.00, 1.03, good) == (True, True)
    assert F.passes(1.00, 1.01, good) == (False, True)
    assert F.passes(1.00, 1.03, bad) == (True, False)


def test_main_writes_the_shipped_model_with_the_residuals_it_tested(tmp_path):
    rng = np.random.default_rng(1)
    rows = []
    for season in range(2018, 2026):
        for _ in range(300):
            s = float(rng.choice([1.5, 3.0, 3.5, 6.5, 7.0, 9.5, 13.5])) * (1 if rng.random() < 0.6 else -1)
            rows.append({"season": season, "game_type": "REG", "spread_line": s,
                         "result": int(round(s + rng.normal(0, 13)))})
    games = tmp_path / "games.csv"
    pd.DataFrame(rows).to_csv(games, index=False)
    oj, om = tmp_path / "m.json", tmp_path / "m.md"
    assert F.main(["--games", str(games), "--out-json", str(oj), "--out-md", str(om)]) == 0
    rec = json.loads(oj.read_text(encoding="utf-8"))
    assert rec["fit_games"] == 1200 and rec["test_games"] == 1200
    if rec["shipped"] == "A_empirical":
        assert len(rec["residuals"]) == 1200 and any(r != int(r) for r in rec["residuals"])
    assert "Shipped:" in om.read_text(encoding="utf-8")


def test_the_ship_order_is_a_then_b_then_nothing():
    assert F.choose({"A_empirical": (True, True), "B_normal": (True, True)}) == "A_empirical"
    assert F.choose({"A_empirical": (True, False), "B_normal": (True, True)}) == "B_normal"
    assert F.choose({"A_empirical": (False, True), "B_normal": (True, False)}) is None


def test_band_edges():
    assert [F.band_of(s) for s in (0.0, 3.0, 3.5, 7.0, 7.5, 17.0)] == [
        "|s| <= 3", "|s| <= 3", "3.5-7", "3.5-7", "7.5+", "7.5+"]


def test_an_empty_band_is_reported_not_a_crash(tmp_path):
    rows = [{"season": y, "game_type": "REG", "spread_line": 2.5 if i % 2 else -1.5, "result": (i % 21) - 10}
            for y in range(2018, 2026) for i in range(60)]
    games = tmp_path / "games.csv"
    pd.DataFrame(rows).to_csv(games, index=False)
    assert F.main(["--games", str(games), "--out-json", str(tmp_path / "m.json"), "--out-md", str(tmp_path / "m.md")]) == 0
    md = (tmp_path / "m.md").read_text(encoding="utf-8")
    assert "no games (fails the rule)" in md and "nothing (neither model passed)" in md

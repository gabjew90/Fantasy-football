"""The scorer's Out path: where an excluded player's share goes.

Measured on 2024-25 absence games (reports/absence_tune.md): a quarter of an
absent player's targets and carries stays with the priced teammates, mostly at
his position, none of his goal-line targets; the rest goes to his replacement.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "scripts"))
pd = pytest.importorskip("pandas")
import score_game as SG  # noqa: E402


def _m():
    return pd.DataFrame({"team": ["A", "A", "A", "B"], "pos": ["RB", "RB", "WR", "RB"],
                         "ts": [0.10, 0.05, 0.20, 0.10], "rs": [0.40, 0.20, 0.00, 0.50],
                         "i10ts": [0.1, 0.0, 0.2, 0.1], "i10rs": [0.5, 0.2, 0.0, 0.5]})


def _e():
    return pd.DataFrame({"team": ["A"], "pos": ["RB"], "ts": [0.08], "rs": [0.30],
                         "i10ts": [0.05], "i10rs": [0.3]})


def test_the_shipped_rule_keeps_a_quarter_mostly_at_his_position():
    M, red = SG.apply_out_rule(_m(), _e(), ("A", "B"))
    # targets: 0.25 x 0.08 = 0.02 kept; 0.2 of it to all (0.10/0.05/0.20 of 0.35), 0.8 to the RBs (2:1)
    kept = 0.25 * 0.08
    want = [0.10 + kept * (0.2 * 0.10 / 0.35 + 0.8 * 2 / 3), 0.05 + kept * (0.2 * 0.05 / 0.35 + 0.8 / 3),
            0.20 + kept * 0.2 * 0.20 / 0.35, 0.10]
    assert M["ts"].tolist() == pytest.approx(want)
    assert M["i10ts"].tolist() == pytest.approx([0.1, 0.0, 0.2, 0.1])      # goal-line targets: none kept
    # 0.25 x 0.30 = 0.075 of carries to the two RBs, pro rata 2:1; the WR gets none
    assert M["rs"].tolist() == pytest.approx([0.45, 0.225, 0.0, 0.50])
    assert red["A"]["rs"] == pytest.approx(0.075) and red["A"]["ts"] == pytest.approx(0.02)
    assert M.loc[3, "rs"] == 0.50                                              # other team untouched


def test_the_old_rule_is_x1_y1_pro_rata_to_everyone():
    old = {c: (1.0, 1.0) for c in ("ts", "rs", "i10ts", "i10rs")}
    M, _ = SG.apply_out_rule(_m(), _e(), ("A",), rule=old)
    assert M.loc[2, "ts"] == pytest.approx(0.20 + 0.08 * 0.20 / 0.35)


def test_no_one_excluded_changes_nothing():
    M, red = SG.apply_out_rule(_m(), pd.DataFrame(), ("A", "B"))
    assert M.equals(_m())

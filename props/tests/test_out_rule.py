"""The scorer's Out path: where an excluded player's share goes.

Measured on 2024-25 absence games (reports/absence_tune.md): the priced
teammates gain none of an absent pass-catcher's targets and a quarter of an
absent back's carries, at his position; the rest goes to his replacement.
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


def test_the_shipped_rule_gives_no_targets_and_a_quarter_of_the_carries_to_his_position():
    M, red = SG.apply_out_rule(_m(), _e(), ("A", "B"))
    assert M["ts"].tolist() == pytest.approx([0.10, 0.05, 0.20, 0.10])      # targets untouched
    # 0.25 x 0.30 = 0.075 of carries to the two RBs, pro rata 2:1; the WR gets none
    assert M["rs"].tolist() == pytest.approx([0.45, 0.225, 0.0, 0.50])
    assert red["A"]["rs"] == pytest.approx(0.075) and red["A"]["ts"] == 0
    assert M.loc[3, "rs"] == 0.50                                              # other team untouched


def test_the_old_rule_is_x1_y1_pro_rata_to_everyone():
    old = {c: (1.0, 1.0) for c in ("ts", "rs", "i10ts", "i10rs")}
    M, _ = SG.apply_out_rule(_m(), _e(), ("A",), rule=old)
    assert M.loc[2, "ts"] == pytest.approx(0.20 + 0.08 * 0.20 / 0.35)


def test_no_one_excluded_changes_nothing():
    M, red = SG.apply_out_rule(_m(), pd.DataFrame(), ("A", "B"))
    assert M.equals(_m())

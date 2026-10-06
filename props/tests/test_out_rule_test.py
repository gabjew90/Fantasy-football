"""props/tools/out_rule_test.py on a team with a known answer, before any real run."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "engine" / "scripts"))

import out_rule_test as OR  # noqa: E402


def _team():
    """Team X, 30 targets a game, weeks 1-6. K (WR) takes 9 (30%) in weeks 1-3, is rostered
    but not active in weeks 4-6. A (WR) takes 6, B (TE) takes 3 every week; after K goes
    out, A takes 9 and B 6."""
    rows = []
    for w in range(1, 7):
        g = f"g{w}"
        n = {"K": 9, "A": 6, "B": 3} if w <= 3 else {"A": 9, "B": 6}
        for p, v in n.items():
            rows.append({"game_id": g, "week": w, "team": "X", "player_id": p, "n": v, "team_n": 30})
    t = pd.DataFrame(rows)
    ros = pd.DataFrame([{"week": w, "team": "X", "gsis_id": p, "position": pos,
                         "status": ("RES" if p == "K" and w >= 4 else "ACT")}
                        for w in range(1, 7) for p, pos in (("K", "WR"), ("A", "WR"), ("B", "TE"))])
    return t, ros


def test_the_handoff_is_the_live_out_rules_arithmetic():
    import score_game as SG
    M = pd.DataFrame({"team": ["X", "X"], "pos": ["WR", "TE"], "ts": [0.2, 0.1], "rs": 0.0, "i10ts": 0.0, "i10rs": 0.0})
    E = pd.DataFrame({"team": ["X"], "pos": ["WR"], "ts": [0.3], "rs": 0.0, "i10ts": 0.0, "i10rs": 0.0})
    live, _ = SG.apply_out_rule(M, E, ["X"])
    x, y = SG.OUT_RULE["ts"]
    mine = np.array([0.2, 0.1]) + OR.handoff(np.array([0.2, 0.1]), np.array([True, False]), y * 0.3, x)
    assert mine == pytest.approx(live.ts.to_numpy())


def test_rows_flag_the_first_game_out_and_measure_what_is_left_to_hand_on():
    t, ros = _team()
    d = OR.game_rows(t, ros, {"K": 0.40}, "targets")
    assert sorted(d.week.unique()) == [4, 5, 6] and set(d.player_id) == {"A", "B"}
    assert d.groupby("week").first_out.first().tolist() == [True, False, False]
    assert (d.v0 == 0.40).all() and d.v1.round(6).eq(0.3).all(), "V0 last season's share, V1 this season's"
    a = d[d.player_id == "A"].set_index("week")
    assert a.loc[4, "cur"] == pytest.approx(0.2) and a.loc[4, "with_k"] == 1.0
    assert a.loc[6, "with_k"] == pytest.approx(0.6), "3 of his 5 games before week 6 had K playing"
    assert a.loc[6, "cur"] == pytest.approx((18 + 18) / 150), "weeks 1-5: 6+6+6+9+9 of 150"
    assert (d.actual[d.player_id == "A"] == 0.3).all()


def test_v2_hands_on_less_as_the_absence_lengthens_and_v0_uses_last_seasons_share():
    t, ros = _team()
    d = OR.game_rows(t, ros, {"K": 0.40}, "targets").assign(season=2024)
    p0, p1, p2 = (OR.predict(d, v, 0.2, 0.25) for v in ("V0", "V1", "V2"))
    wk = d.week.to_numpy()
    assert (p0 > p1).all(), "a bigger share last season hands on more"
    assert np.allclose(p1[wk == 4], p2[wk == 4]), "first game out: nothing is in the teammates' shares yet"
    assert (p2[wk == 6] < p1[wk == 6]).all(), "later: part of the absence is already in their shares"
    d["actual"] = p1                                       # a world where V1 is exactly right
    L = OR.losses(d, 0.2, 0.25)
    assert L["V1"].max() == 0
    m, lo, hi = OR.diff_ci(d, L["V1"], L["V0"], reps=50)
    assert m > 0 and lo > 0, "positive = the first argument (V1) is better"

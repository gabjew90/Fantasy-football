"""round42_select on a known answer: y by absence age, and the pick rule."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import round42_select as R42  # noqa: E402


def _rows(first, actual_mate):
    # one absent key player (share 0.30 last season) and two teammates, one at his position
    return pd.DataFrame({"season": 2022, "team": "T", "game_id": [1, 1], "week": 5, "absent": "K",
                         "player_id": ["A", "B"], "cur": [0.20, 0.20], "with_k": 1.0, "same": [True, False],
                         "actual": actual_mate, "v0": 0.30, "v1": 0.30, "first_out": first, "event": "T_K"})


def test_y_follows_the_absence_age():
    f1 = R42.collapse_y(_rows(True, [0.3, 0.2]), 0.2, 0.5, 0.05)
    fc = R42.collapse_y(_rows(False, [0.3, 0.2]), 0.2, 0.5, 0.05)
    # first game: y 0.5 x 0.30 = 0.15 handed on; x 0.2 of it pro rata (0.015 each), 0.8 to the same position
    assert np.isclose(f1.loc[f1.player_id == "A", "add"].iloc[0], 0.015 + 0.12)
    assert np.isclose(fc.loc[fc.player_id == "A", "add"].iloc[0], (0.015 + 0.12) / 10)


def test_the_pick_prefers_shipped_within_the_tie_and_moves_when_the_data_say_so():
    rows = []
    for s in range(400):        # continuing absences where the teammate gains nothing
        r = _rows(False, [0.20, 0.20]).assign(game_id=[s, s], event=f"T_K{s}", team=f"T{s % 40}")
        rows.append(r)
    d = pd.concat(rows, ignore_index=True)
    p, m = R42.pick(d, 0.2)
    assert p[1] == 0.05, "nothing handed on in reality: the smallest continuing y wins"
    same = pd.concat([_rows(False, [0.20 + 0.075 * 0.8 / 1 + 0.0075, 0.2075]).assign(game_id=[s, s], team=f"T{s}")
                      for s in range(50)], ignore_index=True)
    assert R42.pick(same, 0.2)[0] == R42.SHIPPED, "the shipped handoff exactly right: it stays"

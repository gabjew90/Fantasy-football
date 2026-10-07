"""round41_select: the stages run on their own role's rows and chain (a failed stage keeps 1)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import round41_select as R41  # noqa: E402
from test_grid_select import _frame, _world  # noqa: E402


def test_stages_use_their_role_rows_and_a_failed_stage_keeps_one():
    truth, y = _world(seed=11)
    base = _frame(truth, y, 0.12, 1, n_seasons=5)
    base["slot"] = ["TE1" if i % 3 == 0 else "RB1" if i % 3 == 1 else "WR1" for i in range(len(base))]
    good = _frame(truth, y, 0.0, 2, n_seasons=5)
    good["slot"] = base["slot"].values
    grid = [{"catch_shape_mult_te": te, "catch_shape_mult_rb": 1.0, "te_share_mult": 1.0} for te in (1.0, 1.5)]
    # the "good" frame is better everywhere; only its TE rows decide stage A1
    frames = [base, good]
    a1 = R41.stage(grid, frames, {"catch_shape_mult_rb": 1.0, "te_share_mult": 1.0}, "catch_shape_mult_te",
                   "TE", "receptions", "u")
    assert a1["global_index"] == 1
    same = R41.stage(grid, [base, base], {"catch_shape_mult_rb": 1.0, "te_share_mult": 1.0}, "catch_shape_mult_te",
                     "TE", "receptions", "u")
    assert same["global_index"] == 0 and not same["ship"], "no gain: the stage keeps 1"
    assert set(R41.role_rows(good, "RB").slot) == {"RB1"}

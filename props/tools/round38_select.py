"""Round 38 (reports/round38_qb_passing_bias.md): the QB passing draw's spread and level.

    python props/tools/round38_select.py <qbbias grid pickle> [--confirm 2026] [--out f.json]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402

if __name__ == "__main__":
    # the pre-registered confirmation is 2026 weeks 2-4; 2025 was seen in the diagnosis
    argv = sys.argv[1:] + ([] if any(a.startswith("--confirm") for a in sys.argv[1:]) else ["--confirm", "2026"])
    sys.exit(GS.main(argv,market="QB passing yards", score="u", knobs=("pass_shrink", "pass_scale"),
                     shipped={"pass_shrink": None, "pass_scale": 1.0}, width_col="pit_pass",
                     title="Round 38: QB passing own-volume log loss at the stand-in line"))

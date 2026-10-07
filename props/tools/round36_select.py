"""Round 36 (reports/round36_qb_share.md): the starter-share draw on QB passing.

    python props/tools/round36_select.py <qbshare grid pickle> [--out f.json]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402

if __name__ == "__main__":
    sys.exit(GS.main(market="QB passing yards", score="u", knobs=("starter_share_shrink",),
                     shipped={"starter_share_shrink": None}, width_col="pit_pass", confirm_zone=False,
                     title="Round 36: QB passing own-volume log loss (starter_share_shrink)"))

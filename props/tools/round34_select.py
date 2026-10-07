"""Round 34 (reports/round34_receiving_joint.md): target spread and catch-rate swing together.

    python props/tools/round34_select.py <receivingjoint grid pickle> [--out f.json]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grid_select as GS  # noqa: E402

if __name__ == "__main__":
    sys.exit(GS.main(market="receptions", score="u", knobs=("share_conc_targets", "catch_conc"),
                     shipped={"share_conc_targets": 40.0, "catch_conc": None}, spread=True,
                     title="Round 34: receptions own-volume log loss, eligible = target spread <= real in every band"))

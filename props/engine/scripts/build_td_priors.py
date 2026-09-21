#!/usr/bin/env python3
"""Bundle the prior season's raw inputs for anytime_td_v1.

  python build_td_priors.py --season 2025 [--out ../resources]

Writes priors_{season}_td_{counts,played,slots,teamgames,qbstarts}.csv. Run once
per offseason, like build_priors.py. qbstarts covers the qb_window seasons
ending at --season: the starting quarterback's QB-rush record.

RAW INPUTS, NOT DERIVED SHARES. The live scorer loads only the current
season, so the prior season has to be bundled -- but if the bundle held
finished shares, the live path would run different code from the backtest.
It holds what the backtest's loader produces instead, and td_v1 derives the
shares at run time with the same functions the backtest calls. The loader is
td_alloc_backtest.load itself, so the bundled season is exactly the one the
backtest saw.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import td_alloc_backtest as B  # noqa: E402

KEEP = {
    "counts": ["season", "week", "game_id", "team", "player_id",
               "qb_rush", "rush_in5", "rush_far", "pass_rz", "pass_far"],
    "played": ["season", "week", "game_id", "team", "player_id", "pos"],
    "slots": ["season", "week", "team", "player_id", "slot"],
    "teamgames": ["game_id", "season", "week", "team", "opp", "points", "implied", "spread",
                  "qb_rush", "rush_in5", "rush_far", "pass_rz", "pass_far", "dst_other",
                  "tds", "off_tds", "dst"],
    "qbstarts": ["season", "week", "game_id", "team", "player_id", "qb_rush_tds", "off_tds"],
}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "resources"))
    a = ap.parse_args(argv)
    D = B.load([a.season])
    frames = {"counts": D["cch"], "played": D["played"], "slots": D["slots"],
              "teamgames": D["tg"][D["tg"]["implied"].notna()]}
    win = B.V.V1["qb_window"]
    starts = B.load_starts(range(a.season - win + 1, a.season + 1), D["qb_ids"])
    out = Path(a.out)
    for name, df in [*frames.items(), ("qbstarts", starts)]:
        if name != "qbstarts":
            df = df[df["season"] == a.season]
        df = df[KEEP[name]].sort_values(KEEP[name][:5]).reset_index(drop=True)
        path = out / f"priors_{a.season}_td_{name}.csv"
        # lineterminator fixed so the bundled file hashes the same on every OS
        df.to_csv(path, index=False, lineterminator="\n")
        print(f"wrote {path.name}: {len(df)} rows", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

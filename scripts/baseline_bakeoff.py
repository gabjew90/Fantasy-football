"""Which replacement baseline drafts the better team?

Keefamania's QB5/TE8 were hand-fitted to minimise |VORP rank - ADP rank|,
which is fitting to the market's opinion. The format math says QB10/TE11.
scripts/derive_baselines.py was meant to settle it from streaming data and is
blocked on ownership data -- but that whole question can be sidestepped.

Baselines do not change `proj_pts`. So build the board at each candidate,
draft with each, and score the resulting starting lineup on PROJECTED POINTS,
which is identical across boards. Nothing here can grade itself: the boards
disagree about value, and the scoreboard belongs to neither of them.

    python scripts/baseline_bakeoff.py --league keefamania
"""

from __future__ import annotations

import argparse
import json
import statistics as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import polars as pl  # noqa: E402

import engine_parity as EP  # noqa: E402
from slot_replay import lineup_points, replay, shape  # noqa: E402

from draftkit.config import Config  # noqa: E402

# QB and TE only: RB/WR 24 is the flex-split format derivation and was never
# hand-fitted, so leaving it fixed isolates the thing under test.
CANDIDATES = [
    ("current  QB5/TE8", {"QB": 5, "TE": 8}),
    ("middle   QB7/TE10", {"QB": 7, "TE": 10}),
    ("format   QB10/TE11", {"QB": 10, "TE": 11}),
]


def build_board(cfg: Config, overrides: dict[str, int], out: Path) -> list[dict]:
    """cmd_tiers, minus the reporting, with the baselines swapped."""
    from draftkit.projections import PROJECTION_FNS
    from draftkit.tiers import finish_board, write_tiers_csv
    from draftkit.tilts import apply_tilts, prior_top5_by_pos

    processed = cfg.path("processed")
    market = pl.read_parquet(cfg.scoped(processed / "market.parquet"))
    usage = pl.read_parquet(cfg.scoped(processed / "usage.parquet"))
    df = PROJECTION_FNS["default"](cfg, usage, market)
    df, _ = apply_tilts(df, cfg.get("tilts"), prior_top5_by_pos(usage))

    baselines = dict(cfg.baselines)
    baselines.update(overrides)
    write_tiers_csv(finish_board(df, cfg, baselines), out)
    return EP.load_board(str(out))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", default="keefamania")
    ap.add_argument("--logs", default="1396184666897145856:10,1395566812157984768:12")
    ap.add_argument("--scratch", default="data/draftrig")
    a = ap.parse_args()

    cfg = Config.load(league=a.league)
    scratch = Path(a.scratch)
    scratch.mkdir(parents=True, exist_ok=True)

    drafts = []
    for spec in a.logs.split(","):
        did, teams = spec.split(":")
        log = [json.loads(line) for line in
               open(f"data/logs/draft_{did}.jsonl", encoding="utf-8")
               if '"type": "pick"' in line]
        log.sort(key=lambda d: d["pick_no"])
        drafts.append((did, int(teams), log, max(d["round"] for d in log)))

    print(f"Baseline bake-off — {a.league}, "
          f"{sum(t for _d, t, _l, _r in drafts)} draft slots\n")
    print("scoring: PROJECTED POINTS of the starting lineup "
          "(identical across boards — baselines cannot move it)\n")

    results: dict[str, list[float]] = {}
    shapes: dict[str, list[str]] = {}
    for label, overrides in CANDIDATES:
        board = build_board(cfg, overrides,
                            scratch / f"tiers_bakeoff_{overrides['QB']}_"
                                      f"{overrides['TE']}.csv")
        pts, shp = [], []
        for _did, teams, log, rounds in drafts:
            for s in range(1, teams + 1):
                chosen = replay(board, log, s, teams, rounds, True)
                pts.append(lineup_points(chosen))
                shp.append(shape(chosen))
        results[label] = pts
        shapes[label] = shp
        qb2 = sum(1 for x in shp if "QB2" in x or "QB3" in x)
        print(f"{label:22} mean {st.mean(pts):8.1f}   median "
              f"{st.median(pts):8.1f}   min {min(pts):7.1f}   "
              f"2+QB rosters {qb2}/{len(shp)}")

    base = CANDIDATES[0][0]
    print(f"\nvs {base}:")
    for label, _o in CANDIDATES[1:]:
        d = [n - o for n, o in zip(results[label], results[base])]
        print(f"  {label:22} mean {st.mean(d):+7.1f}  better "
              f"{sum(1 for x in d if x > 0):>2}  worse "
              f"{sum(1 for x in d if x < 0):>2}  tied "
              f"{sum(1 for x in d if x == 0):>2}")


if __name__ == "__main__":
    main()

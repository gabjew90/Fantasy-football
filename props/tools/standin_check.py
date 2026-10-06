"""Do the scoreboard's stand-in lines sit where real bets sit? (reports/scoreboard.md)

Compares the backtest's stand-in line per player-game (the engine's own pre-game median,
at the half) with the line Sleeper actually posted for that player and market in 2026, from
the record. It checks WHERE the scoreboard measures, never the model against the market:
no outcome is read.

    python props/tools/standin_check.py <2026 backtest --conditional --save-results pickle> [--out f.json]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "props" / "engine" / "scripts"))
from model import norm_name  # noqa: E402

CACHE = Path(os.environ.get("NFL_BACKTEST_CACHE", Path(tempfile.gettempdir()) / "nflbt"))
MARKET_L = {"player_receptions": "L_rec", "player_reception_yds": "L_yds", "player_rush_yds": "L_rush",
            "player_rush_reception_yds": "L_rr", "player_pass_yds": "L_pass"}
CLOSE = {"player_receptions": 1.0, "player_reception_yds": 5.0, "player_rush_yds": 5.0,
         "player_rush_reception_yds": 7.5, "player_pass_yds": 15.0}


def posted_lines(record_dir: Path, season: int) -> pd.DataFrame:
    """Sleeper's posted line per (week, player, team, market): the last decision-time quote."""
    rows = []
    for f in sorted((record_dir / "predictions" / str(season)).glob("wk*.jsonl")):
        for line in open(f, encoding="utf-8"):
            r = json.loads(line)
            if r.get("book") == "sleeper" and r.get("market") in MARKET_L and r.get("line") is not None:
                rows.append({k: r.get(k) for k in ("week", "player", "team", "market", "line", "logged_at_utc",
                                                    "snapshot_type")})
    d = pd.DataFrame(rows)
    if d.empty:
        return d
    d = d.sort_values("logged_at_utc").drop_duplicates(["week", "player", "team", "market"], keep="last")
    d["key"] = d.player.map(norm_name)
    return d


def join(R: pd.DataFrame, posted: pd.DataFrame, names: dict) -> pd.DataFrame:
    """Stand-in and posted line side by side. names: gsis_id -> display name."""
    out = []
    for mk, col in MARKET_L.items():
        if col not in R:
            continue
        r = R[R[col].notna()][["week", "team", "gsis_id", col]].copy()
        r["key"] = r.gsis_id.map(names).map(lambda n: norm_name(n) if isinstance(n, str) else None)
        p = posted[posted.market == mk]
        m = r.merge(p, left_on=["week", "team", "key"], right_on=["week", "team", "key"])
        out.append(m.assign(market=mk, standin=m[col], gap=m[col] - m.line)[["week", "team", "player", "market",
                                                                              "standin", "line", "gap"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame()


def summary(J: pd.DataFrame) -> dict:
    out = {}
    for mk, g in J.groupby("market"):
        out[mk] = {"n": int(len(g)), "median_abs_gap": float(g.gap.abs().median()),
                   "mean_gap": float(g.gap.mean()), "within": float((g.gap.abs() <= CLOSE[mk]).mean()),
                   "close_means": CLOSE[mk]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--record", default=str(ROOT / "props" / "record"))
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    R = pd.read_pickle(a.results)["results"]
    R = R[R.season == a.season]
    pl = pd.read_csv(CACHE / "players.csv", usecols=["gsis_id", "display_name"], low_memory=False).dropna()
    J = join(R, posted_lines(Path(a.record), a.season), dict(zip(pl.gsis_id, pl.display_name)))
    out = summary(J)
    print(f"Stand-in lines against Sleeper's posted lines, {a.season} (no outcomes read)")
    for mk, v in out.items():
        print(f"  {mk:28s} n={v['n']:4d}  median |gap| {v['median_abs_gap']:.1f}  mean gap {v['mean_gap']:+.1f}"
              f"  within {v['close_means']:g}: {100 * v['within']:.0f}%")
    if a.out:
        Path(a.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())

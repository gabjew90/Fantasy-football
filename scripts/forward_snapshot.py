"""Freeze the 2026 projection arms NOW so January's judgment cannot be gamed.

Plan 2026-09-02 A1 / DECISIONS #30. ESPN has no history for the backtest
pairs, so the equal-weight consensus arm can only be judged on 2026 actuals.
This writes, per league, a tracked reports/forward_2026.<league>.rows.csv
with one row per player and, on the 17-game basis:

    sleeper, espn, mean, sheet, model      the arms
    sleeper_as_of, espn_as_of, sheet_as_of, model_built   per-source provenance

A single max date across sources cannot prove per-source freshness, so each
arm carries its own date. In January, `--score` joins the season's actuals
(projection_backtest.season_actuals) and REFUSES any row whose earliest
source date is after kickoff (2026-09-10) -- the leakage guard on the one
experiment that has no other protection.

    venv\\Scripts\\python.exe scripts\\forward_snapshot.py --league keefamania
    venv\\Scripts\\python.exe scripts\\forward_snapshot.py --league keefamania --score   # January 2027
"""

from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

KICKOFF = "2026-09-10"
ARMS = ("sleeper", "espn", "mean", "sheet", "model")
DATE_COLS = ("sleeper_as_of", "espn_as_of", "sheet_as_of", "model_built")


def leakage_rows(df: pl.DataFrame, kickoff: str = KICKOFF) -> pl.DataFrame:
    """Rows whose EARLIEST non-empty source date is after kickoff (any source
    refreshed after the games started taints the row)."""
    cols = [c for c in DATE_COLS if c in df.columns]
    if not cols:
        return df.head(0)
    latest = pl.max_horizontal([pl.col(c).cast(pl.Utf8).fill_null("") for c in cols])
    return df.filter(latest > kickoff)


def build(league: str) -> pl.DataFrame:
    from draftkit import external as X
    from draftkit.config import Config
    from draftkit.ids import SleeperIndex, load_id_map
    from draftkit.sleeper import SleeperClient
    cfg = Config.load(league=league)
    scoring = {k: float(v) for k, v in (cfg.get("scoring") or cfg["expected"]["scoring"]).items()}
    players = SleeperClient(cfg.path("raw")).players()
    index = SleeperIndex(players)
    ext = (cfg.get("projections") or {}).get("external") or {}
    frames = {}
    frames["sleeper"] = X.from_sleeper(int(cfg["season"]), scoring, cfg.path("raw"))
    try:
        frames["espn"], _ = X.from_espn(int(cfg["season"]), scoring, cfg.path("raw"), load_id_map(cfg.path("raw")), index)
    except Exception as e:  # noqa: BLE001
        print(f"  espn unavailable: {e}", file=sys.stderr)
        frames["espn"] = X.empty()
    sheet_path = Path(cfg.root) / str(ext.get("sheet_path", ""))
    if sheet_path.exists():
        frames["sheet"], _ = X.from_sheet(sheet_path, scoring, index, as_of=str(ext.get("sheet_as_of", "")))
    else:
        frames["sheet"] = X.empty()
    mean = X.combine([frames["sleeper"], frames["espn"]], mode="mean", scoring=scoring)
    games = float((cfg.get("projections") or {}).get("games", 16.0))
    board = pl.read_csv(cfg.scoped(cfg.root / "tiers.csv"), infer_schema_length=5000)
    model = board.select(pl.col("sleeper_id").cast(pl.Utf8), pl.col("player").alias("name"), "pos", "adp",
                         (pl.col("proj_pts") * 17.0 / games).alias("model"))
    out = model
    for arm in ("sleeper", "espn", "sheet"):
        f = frames[arm]
        if f.height:
            out = out.join(f.select(pl.col("sleeper_id").cast(pl.Utf8), pl.col("pts17").alias(arm),
                                    pl.col("as_of").alias(f"{arm}_as_of")), on="sleeper_id", how="left")
        else:
            out = out.with_columns(pl.lit(None, dtype=pl.Float64).alias(arm), pl.lit(None, dtype=pl.Utf8).alias(f"{arm}_as_of"))
    out = out.join(mean.select(pl.col("sleeper_id").cast(pl.Utf8), pl.col("pts17").alias("mean"),
                               pl.col("n_sources").alias("mean_n_sources")), on="sleeper_id", how="left")
    return out.with_columns(pl.lit("2026").alias("pair"), pl.lit(league).alias("league"),
                            pl.lit(dt.date.today().isoformat()).alias("model_built"),
                            pl.lit(None, dtype=pl.Float64).alias("actual"))


def score(league: str, path: Path) -> int:
    import nflreadpy as nfl
    from draftkit.config import Config
    from draftkit.dataset import scoring_from_cfg
    from draftkit.ids import load_id_map
    from projection_backtest import season_actuals
    cfg = Config.load(league=league)
    df = pl.read_csv(path, infer_schema_length=10000)
    bad = leakage_rows(df)
    if bad.height:
        print(f"REFUSED: {bad.height} rows carry a source date after kickoff {KICKOFF}:")
        for r in bad.head(20).iter_rows(named=True):
            print("  ", r["name"], {c: r.get(c) for c in DATE_COLS if r.get(c)})
        return 2
    weekly = nfl.load_player_stats([int(cfg["season"])]).filter(pl.col("season_type") == "REG")
    act = season_actuals(weekly, scoring_from_cfg(cfg))
    id_map = (load_id_map(cfg.path("raw")).filter(pl.col("gsis_id").is_not_null() & pl.col("sleeper_id").is_not_null())
              .select("gsis_id", pl.col("sleeper_id").cast(pl.Utf8)).unique(subset="sleeper_id"))
    act = act.join(id_map, on="gsis_id", how="inner").select("sleeper_id", pl.col("actual").alias("actual_new"))
    df = (df.drop("actual").join(act, on="sleeper_id", how="left")
            .with_columns(pl.col("actual_new").fill_null(0.0).alias("actual")).drop("actual_new"))
    df.write_csv(path)
    print(f"scored {df.height} rows -> {path}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    path = Path(a.out) if a.out else ROOT / "reports" / f"forward_2026.{a.league}.rows.csv"
    if a.score:
        return score(a.league, path)
    df = build(a.league)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.write_csv(path)
    cover = {arm: int(df[arm].is_not_null().sum()) for arm in ARMS if arm in df.columns}
    print(f"frozen {df.height} rows -> {path}  coverage {cover}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

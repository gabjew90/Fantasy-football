"""The market-curve tail gate (DECISIONS #40).

The log-rank curve stops decaying INSIDE the range it was fitted on: pooled over
both leagues and both pairs it loses 60 points across RB ranks 1-13 and 7 points
across ranks 37-60, while actual scoring in those bands falls 118 -> 88 and is
still falling. Two mechanisms compound. ln() flattens, and a per-position curve
fitted on OVERALL market rank inherits the published ADP feed's own tail
compression (RB ranks 49-72 all sit between overall ADP 148 and 174, so twelve
players cost 0.12 in ln(adp) against 1.51 at the top).

This script rebuilds the projection arms through the production
`default_projection` with `projections.market_curve_tail.mode` set per arm, joins
them onto the canonical backtest row export, and writes the deep-band table that
is the gate's PRIMARY accuracy criterion. `scripts/source_gate.py` then judges the
pooled-accuracy and actual-points-outcome halves on the same file.

The arms are separable on purpose, so a verdict names its cause:

    blend_rank      within-position rank as the regressor
    blend_rank_lin  + a linear-in-rank term at RB and WR  (the candidate)
    blend_tail      + tangent continuation past the fit    (production-only)

Nothing is added to projection_backtest.ARMS, so the #23 common population is
unchanged and every future default gate run reads the same 254 / 301 rows.

    venv\\Scripts\\python.exe scripts\\tail_curve_gate.py --leagues keefamania,omnibeta
    venv\\Scripts\\python.exe scripts\\source_gate.py --leagues keefamania,omnibeta ^
      --rows reports/projection_backtest.keefamania.tail.rows.csv,reports/projection_backtest.omnibeta.tail.rows.csv ^
      --candidate blend_rank_lin --rivals blend --out reports/tail_curve_gate.md
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

from draftkit.config import Config  # noqa: E402
from draftkit.projections import default_projection  # noqa: E402
from draftkit.sleeper import SleeperClient  # noqa: E402

import projection_backtest as PB  # noqa: E402

# The arms, and the mode each one sets. `blend` off is the reproduction check.
ARMS = {"blend_rank": "rank", "blend_rank_lin": "rank_lin", "blend_tail": "full"}

# DECISIONS #40, fixed before the run: the bands where the flattening lives.
# Within-position ADP rank, inclusive lower bound.
DEEP_BAND = {"RB": 37, "WR": 49}
HEAD_N = 24          # "head unchanged" is measured over the top 24 per position
MOVE_EPS = 1.0       # a row "moved" if its projection changed by more than this


def rebuild(cfg: Config, season: int, target: int, players: dict, cache_dir: Path,
            mode: str) -> pl.DataFrame:
    """The backtest's own arm build, with one knob changed. Mirrors
    projection_backtest.run_pair:242-254 exactly, minus the actuals join (the
    actuals come from the canonical rows file, never rebuilt here)."""
    proj = dict(cfg["projections"])
    games = float(proj.get("expected_games", 16.0))
    bt = PB._BtCfg(
        cfg,
        {"projections": {"consensus": {"enabled": False},
                         "role_gate": {"enabled": False},
                         "market_curve_tail": {"mode": mode,
                                               "min_fit": int(proj.get("market_curve_tail", {}).get("min_fit", 30))}}},
        Path(tempfile.mkdtemp()),
    )
    usage = PB.usage_frame(cfg, season, cache_dir)
    market, _unmatched = PB.market_frame(cfg, target, players)
    df = default_projection(bt, usage, market)
    return df.select(
        "sleeper_id",
        (pl.col("proj_pts") * PB.SEASON_GAMES / games).alias("_blend"),
        (pl.col("proj_market_pts") * PB.SEASON_GAMES / games).alias("_curve"),
    )


def deep_mask(df: pl.DataFrame) -> pl.Expr:
    """Rows in the deep band for their position, by within-position ADP rank."""
    r = pl.col("adp").rank(method="ordinal").over(["pair", "pos"])
    cond = pl.lit(False)
    for pos, lo in DEEP_BAND.items():
        cond = cond | ((pl.col("pos") == pos) & (r >= lo))
    return cond


def head_mask(df: pl.DataFrame) -> pl.Expr:
    r = pl.col("adp").rank(method="ordinal").over(["pair", "pos"])
    return (r <= HEAD_N) & pl.col("pos").is_in(list(DEEP_BAND))


def mae(df: pl.DataFrame, arm: str) -> float | None:
    sub = df.filter(pl.col(arm).is_not_null() & pl.col("actual").is_not_null())
    if not sub.height:
        return None
    return float((sub[arm] - sub["actual"]).abs().mean())


def band_table(rows: pl.DataFrame, league: str) -> tuple[list[str], dict]:
    """The primary accuracy criterion: deep-band MAE per arm, per cell, plus the
    head-unchanged and anti-inertness readings."""
    rows = rows.with_columns(deep_mask(rows).alias("_deep"), head_mask(rows).alias("_head"))
    deep, head = rows.filter(pl.col("_deep")), rows.filter(pl.col("_head"))
    base_deep, base_head = mae(deep, "blend"), mae(head, "blend")
    out, stats = [], {"league": league, "deep_n": deep.height, "arms": {}}
    out.append(f"### {league} — deep bands (RB rank {DEEP_BAND['RB']}+, WR rank {DEEP_BAND['WR']}+), n={deep.height}")
    out.append("")
    out.append("| arm | deep MAE | ratio | head MAE ratio | max top-12 move | deep rows moved >1pt |")
    out.append("|---|---|---|---|---|---|")
    out.append(f"| blend (base) | {base_deep:.1f} | 1.000 | 1.000 | 0.0 | — |")
    for arm in ARMS:
        if arm not in rows.columns:
            continue
        d, h = mae(deep, arm), mae(head, arm)
        top12 = rows.filter((pl.col("adp").rank(method="ordinal").over(["pair", "pos"]) <= 12)
                            & pl.col("pos").is_in(list(DEEP_BAND)))
        mx = float((top12[arm] - top12["blend"]).abs().max() or 0.0)
        moved = deep.filter((pl.col(arm) - pl.col("blend")).abs() > MOVE_EPS).height
        frac = moved / deep.height if deep.height else 0.0
        stats["arms"][arm] = {"deep_mae": d, "deep_ratio": d / base_deep if base_deep else None,
                              "head_ratio": h / base_head if base_head else None,
                              "max_top12_move": mx, "moved_frac": frac}
        out.append(f"| {arm} | {d:.1f} | {d / base_deep:.3f} | {h / base_head:.3f} | {mx:.1f} | "
                   f"{moved}/{deep.height} ({frac:.0%}) |")
    out.append("")
    out.append(f"| cell | " + " | ".join(ARMS) + " |")
    out.append("|---|" + "---|" * len(ARMS))
    for (pair,), sub in deep.group_by(["pair"], maintain_order=True):
        b = mae(sub, "blend")
        cells = []
        for arm in ARMS:
            m = mae(sub, arm)
            cells.append(f"{m / b:.3f}" if (m is not None and b) else "—")
        out.append(f"| {pair} (n={sub.height}) | " + " | ".join(cells) + " |")
        stats.setdefault("cells", {})[pair] = {
            arm: (mae(sub, arm) / b if b else None) for arm in ARMS}
    out.append("")
    return out, stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--leagues", default="keefamania,omnibeta")
    ap.add_argument("--out", default=str(ROOT / "reports" / "tail_curve_bands.md"))
    a = ap.parse_args()

    md = ["# Market-curve tail arms (DECISIONS #40)", "",
          "Deep-band MAE is the PRIMARY accuracy criterion. Pass needs the deep ratio",
          f"at most 0.97 in both leagues, at most 1.00 in 3 of 4 cells, the head MAE ratio",
          f"at most 1.01 with no top-12 projection moving more than 2.0 points, and at least",
          f"25% of deep rows moving by more than {MOVE_EPS} point. Pooled accuracy and the",
          "actual-points outcome replay are judged by scripts/source_gate.py on the same file.", ""]
    allstats = []
    for lg in a.leagues.split(","):
        src = ROOT / "reports" / f"projection_backtest.{lg}.rows.csv"
        if not src.exists():
            raise SystemExit(f"{src} missing: run projection_backtest.py --league {lg} first")
        rows = pl.read_csv(src, infer_schema_length=10000)
        cfg = Config.load(league=lg)
        players = SleeperClient(cfg.path("raw")).players()
        cache_dir = cfg.path("processed") / "backtest"

        parts = []
        for (pair,), sub in rows.group_by(["pair"], maintain_order=True):
            s, t = (int(x) for x in str(pair).split("->"))
            # reproduction check: mode off must rebuild the file's own blend
            off = rebuild(cfg, s, t, players, cache_dir, "off").rename({"_blend": "_repro"})
            chk = sub.join(off.select("sleeper_id", "_repro"), on="sleeper_id", how="left")
            bad = chk.filter(pl.col("blend").is_not_null()
                             & ((pl.col("_repro") - pl.col("blend")).abs() > 1e-9)).height
            if bad:
                raise SystemExit(
                    f"{lg} {pair}: mode=off rebuilt {bad} rows differing from the committed "
                    f"blend by more than 1e-9. The inputs have drifted; fix that before "
                    f"reading any verdict.")
            for arm, mode in ARMS.items():
                built = rebuild(cfg, s, t, players, cache_dir, mode)
                sub = sub.join(built.select("sleeper_id", pl.col("_blend").alias(arm),
                                            pl.col("_curve").alias(arm.replace("blend", "curve"))),
                               on="sleeper_id", how="left")
            parts.append(sub)
        out = pl.concat(parts, how="vertical_relaxed")

        # coverage invariant: the arms are only comparable if they are non-null
        # on exactly the rows blend is non-null on
        for arm in ARMS:
            mism = out.filter(pl.col(arm).is_null() != pl.col("blend").is_null()).height
            if mism:
                raise SystemExit(f"{lg}: {arm} coverage differs from blend on {mism} rows")

        dst = src.with_name(f"projection_backtest.{lg}.tail.rows.csv")
        out.write_csv(dst)
        lines, stats = band_table(out, lg)
        allstats.append(stats)
        md += lines
        print(f"{lg}: {out.height} rows -> {dst.name}")
        for arm, st in stats["arms"].items():
            print(f"   {arm:<15} deep MAE {st['deep_mae']:.1f} (ratio {st['deep_ratio']:.3f})  "
                  f"head ratio {st['head_ratio']:.3f}  moved {st['moved_frac']:.0%}")

    Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()

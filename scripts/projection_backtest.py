"""Projection overhaul, item 2: score the projection arms out of sample.

For each season pair (S -> T = S+1) the arms are built exactly as the draft
pipeline would have built them before the T draft, and scored against the T
actuals in the league's own scoring:

  usage      draftkit.dataset.build_usage with stats_season = S (the same
             code path as production, including the QB regression), scaled
             by expected_games -- the model half on its own
  curve      the log-rank market term fitted on the T-preseason ADP
             (FantasyFootballCalculator by year; ECR history is not
             archived, so ADP stands in as it does in production when ECR
             is missing) -- the market half on its own
  blend      default_projection over the two, with the configured alphas
  lines      Sleeper's week-1 stat-line projections for T, scored in league
             scoring and scaled to a season -- the consensus arm. Weekly
             granularity is the limitation the brief records: a week-1 line
             carries week-1 matchups and injuries. Rows updated after the
             week-1 Tuesday are dropped (some 2025 rows were revised in
             October) and the drop is reported.

Not in the backtest, and why: the role gate (no historical depth chart),
overrides and the availability sweep (2026 facts), the consensus column
(that is the `lines` arm). The population is the T-preseason draftable
pool: every player FantasyFootballCalculator had an ADP for that year, with
an actual of 0 for anyone who never recorded a stat line -- an injured or
cut player is an error the projection made, not a row to drop.

Metrics per position: MAE on the 17-game basis (repo arms x 17/16), Spearman
over the pool, both also on the ADP top 36 at the position; plus an alpha
grid -- blend the usage arm with each market term at alpha 0..1 -- to read
where the out-of-sample optimum sits.

    venv\\Scripts\\python.exe scripts\\projection_backtest.py --league keefamania
    venv\\Scripts\\python.exe scripts\\projection_backtest.py --league omnibeta --pairs 2024

Usage frames are slow to build (nflverse play-by-play); they are cached
under data/processed/backtest/.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import tempfile
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.config import Config, _deep_merge  # noqa: E402
from draftkit.consensus import adp_key  # noqa: E402
from draftkit.dataset import build_usage, fantasy_points_expr, scoring_from_cfg  # noqa: E402
from draftkit.ids import SleeperIndex, load_id_map  # noqa: E402
from draftkit.market import _attach_sleeper_ids, load_ffc_adp  # noqa: E402
from draftkit.projections import default_projection  # noqa: E402
from draftkit.sleeper import SleeperClient  # noqa: E402

SEASON_GAMES = 17.0
PAIRS = {2023: 2024, 2024: 2025}
ARMS = ("usage", "curve", "blend", "lines")


# ---------------------------------------------------------------- pure parts

def spearman(a: list[float], b: list[float]) -> float:
    def ranks(x):
        order = sorted(range(len(x)), key=lambda i: x[i])
        r = [0.0] * len(x)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and x[order[j + 1]] == x[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    n = len(a)
    if n < 3:
        return float("nan")
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra) ** 0.5
    vb = sum((y - mb) ** 2 for y in rb) ** 0.5
    return cov / (va * vb) if va and vb else float("nan")


def mae(a: list[float], b: list[float]) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a) if a else float("nan")


def score_arm(pred: list[float | None], actual: list[float]) -> dict:
    """Metrics over rows where the arm has a prediction; n reported."""
    pairs = [(p, a) for p, a in zip(pred, actual) if p is not None]
    if len(pairs) < 3:
        return {"n": len(pairs), "mae": float("nan"), "spearman": float("nan")}
    p, a = zip(*pairs)
    return {"n": len(pairs), "mae": mae(list(p), list(a)), "spearman": spearman(list(p), list(a))}


def alpha_grid(model: list[float | None], market: list[float | None], actual: list[float],
               step: float = 0.1) -> list[dict]:
    """Blend alpha*model + (1-alpha)*market where both exist; metrics per alpha."""
    rows = [(m, k, a) for m, k, a in zip(model, market, actual) if m is not None and k is not None]
    out = []
    if len(rows) < 3:
        return out
    n = int(round(1 / step))
    for i in range(n + 1):
        al = round(i * step, 2)
        pred = [al * m + (1 - al) * k for m, k, _ in rows]
        act = [a for *_, a in rows]
        out.append({"alpha": al, "n": len(rows), "mae": mae(pred, act), "spearman": spearman(pred, act)})
    return out


def week1_lines(rows: list[dict], scoring: dict, cutoff_ms: int,
                games: float = SEASON_GAMES) -> tuple[pl.DataFrame, dict]:
    """Sleeper week-1 rows -> season-scaled points by sleeper_id. Rows with
    no stat line (ADP placeholders) are unprojected; rows updated after the
    cutoff are dropped and counted."""
    def _line(r):
        stats = r.get("stats") or {}
        return {k: v for k, v in stats.items() if not k.startswith("adp_") and k != "gp"
                and not k.startswith("pos_adp")}

    lined = [(r, _line(r)) for r in rows]
    blank = sum(1 for _, ln in lined if not ln)
    lined = [(r, ln) for r, ln in lined if ln]
    # A bulk re-stamp is not a revision. Sleeper touched every 2025 week-1 row
    # on 2025-10-06 (one stamp on 835 of 835 rows) while the lines stayed
    # fractional projections (Allen 232.8 pass yd, 1.63 TD -- not his 394-yard
    # week 1). When >= 95% of lined rows share one stamp DAY, keep them all
    # and say so; otherwise a stamp past the cutoff is a genuine late edit.
    stamps = [int((r.get("updated_at") or r.get("last_modified") or 0) // 86_400_000) for r, _ in lined]
    bulk = False
    if stamps:
        top = max(set(stamps), key=stamps.count)
        bulk = stamps.count(top) >= 0.95 * len(stamps) and top * 86_400_000 > cutoff_ms
    keep, late = [], 0
    for r, line in lined:
        upd = r.get("updated_at") or r.get("last_modified") or 0
        if upd and upd > cutoff_ms and not bulk:
            late += 1
            continue
        pts = sum(float(scoring[k]) * float(v) for k, v in line.items() if k in scoring and v is not None)
        keep.append({"sleeper_id": str(r.get("player_id")), "lines": pts * games})
    df = (pl.DataFrame(keep).unique(subset="sleeper_id", keep="first") if keep
          else pl.DataFrame(schema={"sleeper_id": pl.Utf8, "lines": pl.Float64}))
    return df, {"kept": df.height, "dropped_late": late, "blank": blank, "bulk_restamp": bulk}


def season_actuals(weekly: pl.DataFrame, scoring_nflverse: dict) -> pl.DataFrame:
    """nflverse weekly (one season, REG) -> gsis_id, actual (season total), games."""
    return (weekly.with_columns(fantasy_points_expr(scoring_nflverse))
            .group_by("player_id")
            .agg(pl.col("fpts").sum().alias("actual"), pl.len().alias("games_actual"))
            .rename({"player_id": "gsis_id"}))


# ------------------------------------------------------------- data plumbing

class _BtCfg(Config):
    """The league config with the backtest's overrides and an empty external
    dir (no 2026 overrides / availability leak into a 2024 build)."""

    def __init__(self, base: Config, overrides: dict, external: Path):
        super().__init__(_deep_merge(base._data, overrides), base.root, base.league_name)
        self._external = external

    def path(self, kind: str) -> Path:
        if kind == "external":
            return self._external
        return super().path(kind)


def usage_frame(cfg: Config, season: int, cache_dir: Path) -> pl.DataFrame:
    out = cache_dir / f"usage_{cfg.league_name}_{season}.parquet"
    if out.exists():
        return pl.read_parquet(out)
    bt = _BtCfg(cfg, {"stats_season": season}, Path(tempfile.mkdtemp()))
    player, _ctx = build_usage(bt)
    cache_dir.mkdir(parents=True, exist_ok=True)
    player.write_parquet(out)
    return player


def market_frame(cfg: Config, year: int, players: dict) -> tuple[pl.DataFrame, list[str]]:
    """The T-preseason market as production would have seen it: FFC ADP for
    that year attached to Sleeper ids; ECR unavailable historically."""
    m = cfg.get("market") or {}
    ffc = load_ffc_adp(cfg.path("raw"), teams=int(m.get("teams", 12)), year=year,
                       fmt=str(m.get("ffc_format", "ppr")))
    index = SleeperIndex(players)
    ffc, unmatched = _attach_sleeper_ids(ffc, index, load_id_map(cfg.path("raw")), via_fp_id=False)
    mk = (ffc.filter(pl.col("sleeper_id").is_not_null())
          .select("sleeper_id", "name", "pos", "team", "adp", pl.col("bye_ffc").alias("bye"))
          .with_columns(pl.lit(None, dtype=pl.Float64).alias("ecr"),
                        pl.lit(None, dtype=pl.Float64).alias("ecr_sd"))
          .unique(subset="sleeper_id", keep="first"))
    return mk, unmatched


def fetch_week1(season: int, raw_dir: Path) -> list[dict]:
    import requests
    cache = raw_dir / f"sleeper_proj_{season}_wk1.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    r = requests.get(f"https://api.sleeper.app/projections/nfl/{season}/1?season_type=regular", timeout=120)
    r.raise_for_status()
    data = r.json()
    rows = list(data.values()) if isinstance(data, dict) else data
    cache.write_text(json.dumps(rows), encoding="utf-8")
    return rows


def week1_cutoff_ms(season: int) -> int:
    """Noon UTC on the Wednesday after week 1 (first Thursday of September +
    6 days). Sleeper's week-1 rows carry update stamps through the Monday
    night game and into Tuesday UTC (2024: last stamp Tue 03:45 UTC); a
    midnight-Tuesday cutoff dropped every row. Anything stamped later than
    this Wednesday is a genuine in-season revision and is excluded."""
    d = dt.date(season, 9, 1)
    while d.weekday() != 3:      # Thursday
        d += dt.timedelta(days=1)
    wed = d + dt.timedelta(days=6)
    return int(dt.datetime(wed.year, wed.month, wed.day, 12, tzinfo=dt.timezone.utc).timestamp() * 1000)


# --------------------------------------------------------------------- run

def run_pair(cfg: Config, s: int, t: int, players: dict, cache_dir: Path) -> dict:
    import nflreadpy as nfl

    proj = dict(cfg["projections"])
    games = float(proj.get("expected_games", 16.0))
    bt = _BtCfg(cfg, {"projections": {"consensus": {"enabled": False},
                                      "role_gate": {"enabled": False}}},
                Path(tempfile.mkdtemp()))
    usage = usage_frame(cfg, s, cache_dir)
    market, unmatched = market_frame(cfg, t, players)
    df = default_projection(bt, usage, market)
    arms = df.select("sleeper_id", "name", "pos", "adp",
                     (pl.col("proj_model_pts") * SEASON_GAMES / games).alias("usage"),
                     (pl.col("proj_market_pts") * SEASON_GAMES / games).alias("curve"),
                     (pl.col("proj_pts") * SEASON_GAMES / games).alias("blend"),
                     "proj_source")
    # the consensus arm
    scoring = {k: float(v) for k, v in (cfg.get("scoring") or cfg["expected"]["scoring"]).items()}
    lines, lrep = week1_lines(fetch_week1(t, cfg.path("raw")), scoring, week1_cutoff_ms(t))
    arms = arms.join(lines, on="sleeper_id", how="left")
    # actuals
    weekly = nfl.load_player_stats([t]).filter(pl.col("season_type") == "REG")
    act = season_actuals(weekly, scoring_from_cfg(cfg))
    id_map = load_id_map(cfg.path("raw")).filter(pl.col("gsis_id").is_not_null() & pl.col("sleeper_id").is_not_null()) \
        .select("gsis_id", pl.col("sleeper_id").cast(pl.Utf8)).unique(subset="sleeper_id")
    act = act.join(id_map, on="gsis_id", how="inner").select("sleeper_id", "actual", "games_actual")
    arms = arms.join(act, on="sleeper_id", how="left").with_columns(
        pl.col("actual").fill_null(0.0), pl.col("games_actual").fill_null(0))
    # population: the draftable pool = everyone with a T-preseason ADP
    pool = arms.filter(pl.col("adp").is_not_null() & pl.col("pos").is_in(["QB", "RB", "WR", "TE"]))

    res = {"pair": f"{s}->{t}", "pool": pool.height, "ffc_unmatched": len(unmatched),
           "lines_report": lrep, "positions": {}}
    for pos in ("QB", "RB", "WR", "TE"):
        sub = pool.filter(pl.col("pos") == pos).sort("adp")
        top = sub.head(36)
        actual = sub["actual"].to_list()
        # rows every arm projected (rookies have no usage arm; a player Sleeper
        # did not line has no lines arm): the only apples-to-apples comparison
        common = sub.filter(pl.all_horizontal([pl.col(a).is_not_null() for a in ARMS]))
        block = {"n": sub.height, "n_common": common.height, "arms": {}, "arms_top36": {},
                 "arms_common": {}, "alpha_curve": [], "alpha_lines": []}
        for arm in ARMS:
            block["arms"][arm] = score_arm(sub[arm].to_list(), actual)
            block["arms_top36"][arm] = score_arm(top[arm].to_list(), top["actual"].to_list())
            block["arms_common"][arm] = score_arm(common[arm].to_list(), common["actual"].to_list())
        block["alpha_curve"] = alpha_grid(sub["usage"].to_list(), sub["curve"].to_list(), actual)
        block["alpha_lines"] = alpha_grid(sub["usage"].to_list(), sub["lines"].to_list(), actual)
        res["positions"][pos] = block
    res["rows"] = pool.select("sleeper_id", "name", "pos", "adp", *ARMS, "actual", "games_actual").to_dicts()
    return res


def render(league: str, results: list[dict], alphas: dict) -> str:
    L = [f"# Projection backtest — {league}", "",
         "Arms built as the pipeline would have built them before each target season's draft; "
         "scored against that season's actuals in league scoring, 17-game basis. Population = "
         "every player with a FantasyFootballCalculator ADP for the target year (an actual of 0 "
         "for anyone who never played: that is the projection's error, not a dropped row). "
         "Role gate off (no historical depth chart); no overrides or availability sweep. "
         "`lines` = Sleeper week-1 stat lines x 17, rows updated after the week-1 Tuesday dropped.",
         "", f"Configured alphas: {alphas}", ""]
    for r in results:
        L += [f"## {r['pair']}", "",
              f"Pool {r['pool']} players; FFC names unmatched to Sleeper: {r['ffc_unmatched']}; "
              f"week-1 lines kept {r['lines_report']['kept']}, dropped as late updates "
              f"{r['lines_report']['dropped_late']}, blank {r['lines_report']['blank']}"
              + (" — every row carried one bulk re-stamp date after week 1 (a touch, not a "
                 "revision: the lines are still fractional projections), so all were kept."
                 if r['lines_report'].get('bulk_restamp') else "."), "",
              "| pos | arm | n | MAE | Spearman | n common | MAE common | Spearman common | MAE top36 | Spearman top36 |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for pos, b in r["positions"].items():
            for arm in ARMS:
                a, c, t = b["arms"][arm], b["arms_common"][arm], b["arms_top36"][arm]
                L.append(f"| {pos} | {arm} | {a['n']} | {a['mae']:.1f} | {a['spearman']:.3f} | "
                         f"{c['n']} | {c['mae']:.1f} | {c['spearman']:.3f} | "
                         f"{t['mae']:.1f} | {t['spearman']:.3f} |")
        L += ["", "Alpha grid (weight on the usage arm; the rest on the market term). Best by MAE / by Spearman:", "",
              "| pos | vs curve: best MAE α (MAE) | best ρ α (ρ) | vs lines: best MAE α (MAE) | best ρ α (ρ) |",
              "|---|---|---|---|---|"]
        for pos, b in r["positions"].items():
            def best(grid, key, lo=True):
                if not grid:
                    return "n/a"
                g = min(grid, key=lambda x: x[key]) if lo else max(grid, key=lambda x: x[key])
                return f"{g['alpha']:.1f} ({g[key]:.{1 if key == 'mae' else 3}f})"
            L.append(f"| {pos} | {best(b['alpha_curve'], 'mae')} | {best(b['alpha_curve'], 'spearman', False)} | "
                     f"{best(b['alpha_lines'], 'mae')} | {best(b['alpha_lines'], 'spearman', False)} |")
        L.append("")
    return "\n".join(L) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--pairs", default="2023,2024", help="stats seasons S (target = S+1)")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    cfg = Config.load(league=a.league)
    players = SleeperClient(cfg.path("raw")).players()
    cache_dir = cfg.path("processed") / "backtest"
    results = []
    for s in [int(x) for x in a.pairs.split(",") if x.strip()]:
        t = PAIRS.get(s, s + 1)
        print(f"== {s} -> {t} ==", flush=True)
        results.append(run_pair(cfg, s, t, players, cache_dir))
        for pos, b in results[-1]["positions"].items():
            print(f"  {pos}: " + "  ".join(f"{arm} MAE {b['arms'][arm]['mae']:.1f} ρ {b['arms'][arm]['spearman']:.3f}"
                                            for arm in ARMS), flush=True)
    proj = cfg["projections"]
    alphas = {"model_alpha": proj.get("model_alpha"), **(proj.get("alpha_by_type") or {})}
    md = render(a.league, results, alphas)
    out = Path(a.out) if a.out else ROOT / "reports" / f"projection_backtest.{a.league}.md"
    out.write_text(md, encoding="utf-8")
    (out.with_suffix(".json")).write_text(json.dumps(
        [{k: v for k, v in r.items() if k != "rows"} for r in results], indent=1), encoding="utf-8")
    rows = [dict(r, pair=res["pair"]) for res in results for r in res["rows"]]
    pl.DataFrame(rows).write_csv(out.with_suffix(".rows.csv"))
    print(f"-> {out}")


if __name__ == "__main__":
    main()

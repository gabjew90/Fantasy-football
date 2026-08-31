"""Market baseline: FantasyPros ECR + ADP, matched to Sleeper IDs.

Sources, in priority order:
1. data/external/fantasypros.csv — a user-provided FantasyPros export
   (flexible column names). If present, it overrides the auto-pulled ECR.
2. DynastyProcess mirror of FantasyPros ECR (redraft PPR overall page),
   refreshed on their side several times a week. Free, no login.
3. FantasyFootballCalculator public ADP API (PPR, 12-team) for actual ADP —
   ECR is expert ranking, ADP is where humans actually pick; we keep both.
"""

from __future__ import annotations

import time
from pathlib import Path

import polars as pl
import requests

from .ids import SleeperIndex, load_id_map, normalize_name

FPECR_URL = "https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_fpecr_latest.csv"
FFC_URL = "https://fantasyfootballcalculator.com/api/v1/adp/{fmt}?teams={teams}&year={year}"
CACHE_TTL = 12 * 3600

POS_NORM = {"DST": "DEF", "D/ST": "DEF", "PK": "K"}


def _norm_pos(pos: str) -> str:
    p = (pos or "").upper().strip()
    p = "".join(c for c in p if not c.isdigit())  # "RB12" -> "RB"
    return POS_NORM.get(p, p)


def _cached_fetch(url: str, cache: Path, ttl: int = CACHE_TTL) -> bytes:
    if cache.exists() and time.time() - cache.stat().st_mtime < ttl:
        return cache.read_bytes()
    resp = requests.get(url, timeout=60)
    resp.raise_for_status()
    cache.write_bytes(resp.content)
    return resp.content


def load_ecr(raw_dir: Path) -> pl.DataFrame:
    """FantasyPros redraft PPR overall ECR via the DynastyProcess mirror."""
    cache = Path(raw_dir) / "db_fpecr_latest.csv"
    _cached_fetch(FPECR_URL, cache)
    df = pl.read_csv(cache, infer_schema_length=10000, null_values=["NA"])
    df = df.filter(pl.col("page_type") == "redraft-overall")
    out = df.select(
        pl.col("player").alias("name"),
        pl.col("id").cast(pl.Utf8).alias("fantasypros_id"),
        pl.col("pos").map_elements(_norm_pos, return_dtype=pl.Utf8).alias("pos"),
        pl.col("tm").alias("team"),
        pl.col("ecr").cast(pl.Float64),
        pl.col("sd").cast(pl.Float64).alias("ecr_sd"),
        pl.col("bye").cast(pl.Int64, strict=False),
        pl.col("scrape_date"),
    )
    return out


def load_ffc_adp(raw_dir: Path, teams: int, year: int,
                 fmt: str = "ppr") -> pl.DataFrame:
    cache = Path(raw_dir) / f"ffc_adp_ppr_{teams}_{year}.json"
    import json

    data = json.loads(_cached_fetch(FFC_URL.format(fmt=fmt, teams=teams, year=year), cache))
    rows = data.get("players", [])
    return pl.DataFrame(
        {
            "name": [r["name"] for r in rows],
            "pos": [_norm_pos(r["position"]) for r in rows],
            "team": [r.get("team") for r in rows],
            "adp": [float(r["adp"]) for r in rows],
            "bye_ffc": [r.get("bye") for r in rows],
        }
    )


def load_user_csv(external_dir: Path) -> pl.DataFrame | None:
    """Flexible-column FantasyPros export: player/position/team/ecr_rank/adp."""
    path = Path(external_dir) / "fantasypros.csv"
    if not path.exists():
        return None
    df = pl.read_csv(path, infer_schema_length=5000, null_values=["NA", ""])
    colmap = {}
    for c in df.columns:
        lc = c.lower().strip().replace('"', "")
        if lc in ("player", "player name", "name", "player_name"):
            colmap[c] = "name"
        elif lc in ("position", "pos"):
            colmap[c] = "pos"
        elif lc in ("team", "tm"):
            colmap[c] = "team"
        elif lc in ("ecr_rank", "ecr", "rk", "rank", "overall"):
            colmap[c] = "ecr"
        elif lc in ("adp", "avg", "avg. draft position"):
            colmap[c] = "adp"
        elif lc == "bye":
            colmap[c] = "bye"
    df = df.rename(colmap)
    need = {"name", "pos"}
    if not need.issubset(set(df.columns)) or ("ecr" not in df.columns and "adp" not in df.columns):
        raise ValueError(
            f"{path} must have player+position and at least one of ecr_rank/adp; got {df.columns}"
        )
    keep = [c for c in ("name", "pos", "team", "ecr", "adp", "bye") if c in df.columns]
    out = df.select(keep).with_columns(
        pl.col("pos").map_elements(_norm_pos, return_dtype=pl.Utf8),
    )
    if "ecr" in out.columns:
        out = out.with_columns(pl.col("ecr").cast(pl.Float64, strict=False))
    if "adp" in out.columns:
        out = out.with_columns(pl.col("adp").cast(pl.Float64, strict=False))
    return out


def _attach_sleeper_ids(
    df: pl.DataFrame, index: SleeperIndex, id_map: pl.DataFrame, via_fp_id: bool
) -> tuple[pl.DataFrame, list[str]]:
    """Add a sleeper_id column; return (df, unmatched names)."""
    if via_fp_id and "fantasypros_id" in df.columns:
        fp2sl = id_map.filter(
            pl.col("fantasypros_id").is_not_null() & pl.col("sleeper_id").is_not_null()
        ).select("fantasypros_id", "sleeper_id").unique(subset="fantasypros_id")
        df = df.join(fp2sl, on="fantasypros_id", how="left")
    else:
        df = df.with_columns(pl.lit(None, dtype=pl.Utf8).alias("sleeper_id"))

    names = df["name"].to_list()
    poss = df["pos"].to_list()
    teams = df["team"].to_list() if "team" in df.columns else [None] * len(names)
    current = df["sleeper_id"].to_list()
    unmatched = []
    resolved = []
    for name, pos, team, sid in zip(names, poss, teams, current):
        if sid:
            resolved.append(str(sid))
            continue
        hit = index.match(name, pos, team)
        if hit is None:
            unmatched.append(f"{name} ({pos})")
        resolved.append(hit)
    df = df.with_columns(pl.Series("sleeper_id", resolved, dtype=pl.Utf8))
    return df, unmatched


def build_market(cfg, players: dict[str, dict]) -> tuple[pl.DataFrame, dict]:
    """Produce the market table keyed by sleeper_id.

    Columns: sleeper_id, name, pos, team, bye, ecr, ecr_sd, adp, ecr_source.
    """
    raw = cfg.path("raw")
    index = SleeperIndex(players)
    id_map = load_id_map(raw)
    report: dict = {}

    user_csv = load_user_csv(cfg.path("external"))
    if user_csv is not None:
        ecr = user_csv
        if "ecr" not in ecr.columns:
            ecr = ecr.with_columns(pl.col("adp").alias("ecr"))
        ecr = ecr.with_columns(pl.lit(None, dtype=pl.Float64).alias("ecr_sd"))
        ecr, unmatched = _attach_sleeper_ids(ecr, index, id_map, via_fp_id=False)
        report["ecr_source"] = "user fantasypros.csv"
    else:
        ecr = load_ecr(raw)
        report["ecr_scrape_date"] = ecr["scrape_date"][0] if ecr.height else None
        ecr, unmatched = _attach_sleeper_ids(ecr, index, id_map, via_fp_id=True)
        report["ecr_source"] = "dynastyprocess fpecr mirror"
    report["ecr_unmatched"] = unmatched

    mcfg = cfg.get("market") or {}
    ffc = load_ffc_adp(raw, teams=int(mcfg.get("teams", 12)),
                       year=int(cfg["season"]),
                       fmt=str(mcfg.get("ffc_format", "ppr")))
    ffc, ffc_unmatched = _attach_sleeper_ids(ffc, index, id_map, via_fp_id=False)
    report["ffc_unmatched"] = ffc_unmatched

    ecr_cols = ["sleeper_id", "name", "pos", "team", "ecr", "ecr_sd"]
    if "bye" in ecr.columns:
        ecr_cols.append("bye")
    # a user CSV's own ADP is fresher than the FFC pull — carry it through
    # and prefer it after the join
    if "adp" in ecr.columns:
        ecr = ecr.rename({"adp": "adp_user"})
        ecr_cols.append("adp_user")
    market = ecr.filter(pl.col("sleeper_id").is_not_null()).select(ecr_cols).unique(
        subset="sleeper_id", keep="first"
    )

    adp_part = ffc.filter(pl.col("sleeper_id").is_not_null()).select(
        "sleeper_id",
        pl.col("adp"),
        pl.col("bye_ffc"),
        pl.col("name").alias("name_ffc"),
        pl.col("pos").alias("pos_ffc"),
    ).unique(subset="sleeper_id", keep="first")

    market = market.join(adp_part, on="sleeper_id", how="full", coalesce=True)

    # Yahoo ADP override (v2 Keefamania prep): the room drafts against
    # YAHOO's board, so a scraped data/external/yahoo_adp.csv (name,pos,adp)
    # takes precedence over FFC where names match. League-scoped file.
    ypath = cfg.scoped(cfg.path("external") / "yahoo_adp.csv")
    if ypath.exists():
        yah = pl.read_csv(ypath, infer_schema_length=500).with_columns(
            pl.col("name").str.to_lowercase()
            .str.replace_all(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", "")
            .str.replace_all(r"[^a-z0-9]", "").alias("_norm"),
            pl.col("adp").cast(pl.Float64).alias("adp_yahoo"),
        ).select("_norm", "adp_yahoo").unique(subset="_norm")
        market = market.with_columns(
            pl.col("name").str.to_lowercase()
            .str.replace_all(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", "")
            .str.replace_all(r"[^a-z0-9]", "").alias("_norm")
        ).join(yah, on="_norm", how="left").drop("_norm")
        report["yahoo_adp_matched"] = int(market["adp_yahoo"].is_not_null().sum())
    market = market.with_columns(
        pl.coalesce(pl.col("name"), pl.col("name_ffc")).alias("name"),
        pl.coalesce(pl.col("pos"), pl.col("pos_ffc")).alias("pos"),
        (
            pl.coalesce(pl.col("bye"), pl.col("bye_ffc")).alias("bye")
            if "bye" in market.columns
            else pl.col("bye_ffc").alias("bye")
        ),
    ).drop(["name_ffc", "pos_ffc", "bye_ffc"], strict=False)

    if "adp_user" in market.columns:
        market = market.with_columns(
            pl.coalesce(pl.col("adp_user"), pl.col("adp")).alias("adp")
        ).drop("adp_user")
    if "adp_yahoo" in market.columns:
        # the room's own market beats a generic feed
        market = market.with_columns(
            pl.coalesce(pl.col("adp_yahoo"), pl.col("adp")).alias("adp")
        ).drop("adp_yahoo")

    market = market.sort(pl.col("ecr").fill_null(999))
    return market, report

"""Consensus stat lines as a projection source (projection overhaul, item 1).

Sleeper serves season stat-line projections (Rotowire's, one shop, not a
many-expert consensus -- see DECISIONS 2026-09-02 #17) per position:

    https://api.sleeper.app/projections/nfl/<season>?season_type=regular&position[]=RB

Each row carries `player_id` (a Sleeper id, so the join to the board is
exact, no name matching), the stat line (pass_yd, rush_att, rec, ... keyed
like the league yaml's scoring block) and Sleeper's own ADP by format.

Conventions, stated because two comparisons already disagreed over them:
  * A line is a full-season total. `gp` reads 18 in these rows -- Rotowire's
    week count, not games played -- so it is recorded for audit and NOT used
    to scale. `line_games` (config, default 17) is the season length the
    lines describe; points are scaled by expected_games / line_games onto the
    board's basis.
  * Scoring is the league yaml's block applied key-for-key. Keys the line
    lacks (pass_td_40p) contribute nothing, as everywhere else.
  * K and DEF lines exist but the yaml scoring block has no K/DEF keys, so
    they are not scored here; proj_consensus_pts is null for them.

This module produces a PARALLEL column. Whether it replaces the log-rank
market curve is decided by the backtest (item 2), not here.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import polars as pl

BASE = "https://api.sleeper.app"
POSITIONS = ("QB", "RB", "WR", "TE")
CACHE_TTL = 12 * 3600
DEFAULT_LINE_GAMES = 17.0


class ConsensusUnavailable(RuntimeError):
    """The endpoint could not be read and no fresh cache exists."""


def _get_json(url: str, timeout: int = 60):
    import requests
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def fetch_position(season: int | str, pos: str, raw_dir: Path, getter=_get_json,
                   ttl: int = CACHE_TTL) -> list[dict]:
    """One position's rows, cached under raw_dir with a TTL. A stale cache is
    still returned when the fetch fails, with a stderr note, because a
    yesterday's line beats no line -- but never silently: the caller sees
    `cache_age_s` in the report."""
    cache = Path(raw_dir) / f"sleeper_proj_{season}_{pos}.json"
    if cache.exists() and time.time() - cache.stat().st_mtime < ttl:
        return json.loads(cache.read_text(encoding="utf-8"))
    url = f"{BASE}/projections/nfl/{season}?season_type=regular&position[]={pos}"
    try:
        data = getter(url)
    except Exception as e:  # noqa: BLE001
        if cache.exists():
            import sys
            print(f"consensus: fetch failed ({type(e).__name__}); using cache "
                  f"{cache.name} aged {int(time.time() - cache.stat().st_mtime)}s", file=sys.stderr)
            return json.loads(cache.read_text(encoding="utf-8"))
        raise ConsensusUnavailable(f"{url}: {e}") from e
    if not isinstance(data, list):
        raise ConsensusUnavailable(f"{url}: unexpected payload {type(data).__name__}")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(json.dumps(data), encoding="utf-8")
    return data


def adp_key(scoring: dict) -> str:
    rec = float(scoring.get("rec", 0) or 0)
    return "adp_ppr" if rec >= 1 else ("adp_half_ppr" if rec > 0 else "adp_std")


def score_rows(rows: list[dict], scoring: dict, games: float,
               line_games: float = DEFAULT_LINE_GAMES) -> pl.DataFrame:
    """Rows -> DataFrame[sleeper_id, consensus_pos, consensus_team,
    consensus_gp, proj_consensus_pts, adp_sleeper, consensus_updated].
    Rows with no stat line beyond ADP placeholders are dropped (a player
    Rotowire does not project is not a zero-point player; he is unprojected)."""
    akey = adp_key(scoring)
    scale = float(games) / float(line_games)
    out = []
    for r in rows:
        stats = r.get("stats") or {}
        line = {k: v for k, v in stats.items() if not k.startswith("adp_") and k != "gp"}
        if not line:
            continue
        pts = sum(float(scoring[k]) * float(v) for k, v in line.items()
                  if k in scoring and v is not None)
        p = r.get("player") or {}
        out.append({
            "sleeper_id": str(r.get("player_id")),
            "consensus_pos": p.get("position") or p.get("fantasy_positions", [None])[0],
            "consensus_team": r.get("team"),
            "consensus_gp": stats.get("gp"),
            "proj_consensus_pts": round(pts * scale, 2),
            "adp_sleeper": stats.get(akey),
            "consensus_updated": r.get("updated_at") or r.get("last_modified"),
        })
    if not out:
        return pl.DataFrame(schema={"sleeper_id": pl.Utf8, "consensus_pos": pl.Utf8,
                                    "consensus_team": pl.Utf8, "consensus_gp": pl.Float64,
                                    "proj_consensus_pts": pl.Float64, "adp_sleeper": pl.Float64,
                                    "consensus_updated": pl.Int64})
    return pl.DataFrame(out).with_columns(
        pl.col("consensus_gp").cast(pl.Float64, strict=False),
        pl.col("adp_sleeper").cast(pl.Float64, strict=False),
    ).unique(subset="sleeper_id", keep="first")


def scoring_from_cfg(cfg) -> dict[str, float]:
    block = cfg.get("scoring") or (cfg.get("expected") or {}).get("scoring") or {}
    if not block:
        raise ConsensusUnavailable("league yaml carries no scoring block")
    return {k: float(v) for k, v in block.items()}


def load_consensus(cfg, getter=_get_json, ttl: int = CACHE_TTL) -> tuple[pl.DataFrame, dict]:
    """The parallel consensus column for every projected skill player, on the
    board's games basis. Returns (frame, report). Raises ConsensusUnavailable
    rather than returning an empty frame: the caller decides how loudly to
    degrade."""
    p = cfg.get("projections") or {}
    c = p.get("consensus") or {}
    season = int(cfg.get("season") or c.get("season") or 0)
    if not season:
        raise ConsensusUnavailable("no season in config")
    games = float(p.get("expected_games", 16.0))
    line_games = float(c.get("line_games", DEFAULT_LINE_GAMES))
    scoring = scoring_from_cfg(cfg)
    raw = cfg.path("raw")
    frames, report = [], {"season": season, "games": games, "line_games": line_games,
                          "adp_key": adp_key(scoring), "rows": {}}
    for pos in POSITIONS:
        rows = fetch_position(season, pos, raw, getter=getter, ttl=ttl)
        df = score_rows(rows, scoring, games, line_games)
        report["rows"][pos] = df.height
        frames.append(df)
    out = pl.concat(frames, how="vertical_relaxed").unique(subset="sleeper_id", keep="first")
    upd = out["consensus_updated"].drop_nulls()
    report["updated_max"] = int(upd.max()) if upd.len() else None
    return out, report

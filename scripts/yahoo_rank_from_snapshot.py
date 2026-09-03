"""Yahoo default rank (o_rank) from a draft-room players snapshot.

The driver dumps the room's whole player store (DK.players()) and POSTs it to
the bridge as data/logs/mocks/mock_players_<room>.json. `o_rank` is Yahoo's
default overall rank -- the list an autopick seat walks (DECISIONS #35,
plan 2026-09-03 section 1). This script turns one snapshot into the
league-scoped input draftkit/market.py joins onto the board:

    data/external/yahoo_rank.<league>.csv    name,pos,yahoo_rank   (o_rank)

and, as a side product for comparison only,

    data/external/yahoo_adp_snapshot.<league>.csv   name,pos,adp  (avg_pick)

It NEVER writes data/external/yahoo_adp.<league>.csv -- that file is the
curated ADP input with its own provenance. Idempotent: same snapshot, same
bytes.

    venv/Scripts/python.exe scripts/yahoo_rank_from_snapshot.py \
        --snapshot data/logs/mocks/mock_players_10534350.json --league keefamania
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

POS_NORM = {"DST": "DEF", "D/ST": "DEF", "D": "DEF", "PK": "K"}


def _norm_pos(pos: str) -> str:
    p = (pos or "").upper().strip()
    return POS_NORM.get(p, p)


def rows_from_snapshot(snap: dict) -> tuple[list[dict], list[dict], dict]:
    """(rank_rows, adp_rows, counts). Rank rows keep every player with a
    numeric o_rank; ADP rows only those with a numeric avg_pick. DEF rows
    keep Yahoo's own name (a nickname such as "Texans") with pos DEF -- the
    market join matches defenses on the nickname, not the full name."""
    players = snap.get("players") or []
    rank_rows: list[dict] = []
    adp_rows: list[dict] = []
    counts = {"players": len(players), "rank": 0, "no_rank": 0, "adp": 0, "def": 0}
    for p in players:
        name = (p.get("name") or "").strip()
        pos = _norm_pos(p.get("pos") or "")
        if not name or not pos:
            counts["no_rank"] += 1
            continue
        o_rank = p.get("o_rank")
        if isinstance(o_rank, (int, float)) and not isinstance(o_rank, bool):
            rank_rows.append({"name": name, "pos": pos, "yahoo_rank": int(o_rank)})
            counts["rank"] += 1
            if pos == "DEF":
                counts["def"] += 1
        else:
            counts["no_rank"] += 1
        avg = p.get("avg_pick")
        if isinstance(avg, (int, float)) and not isinstance(avg, bool):
            adp_rows.append({"name": name, "pos": pos, "adp": float(avg)})
            counts["adp"] += 1
    # deterministic order: by rank, then name -- idempotent output bytes
    rank_rows.sort(key=lambda r: (r["yahoo_rank"], r["name"], r["pos"]))
    adp_rows.sort(key=lambda r: (r["adp"], r["name"], r["pos"]))
    return rank_rows, adp_rows, counts


def _write(path: Path, rows: list[dict], cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({c: r[c] for c in cols})


def scoped_name(stem: str, league: str, default_league: str | None) -> str:
    """Mirror Config.scoped: the default league keeps the bare filename."""
    if not league or league == default_league:
        return f"{stem}.csv"
    return f"{stem}.{league}.csv"


def run(snapshot: Path, league: str, out_dir: Path, default_league: str | None = None) -> dict:
    snap = json.loads(Path(snapshot).read_text(encoding="utf-8"))
    if snap.get("kind") not in (None, "players_snapshot"):
        raise SystemExit(f"not a players snapshot: kind={snap.get('kind')!r}")
    rank_rows, adp_rows, counts = rows_from_snapshot(snap)
    rank_path = out_dir / scoped_name("yahoo_rank", league, default_league)
    adp_path = out_dir / scoped_name("yahoo_adp_snapshot", league, default_league)
    _write(rank_path, rank_rows, ["name", "pos", "yahoo_rank"])
    _write(adp_path, adp_rows, ["name", "pos", "adp"])
    counts["rank_path"] = str(rank_path)
    counts["adp_path"] = str(adp_path)
    counts["captured_at"] = snap.get("captured_at")
    counts["source_room"] = snap.get("source_room") or snap.get("room")
    return counts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--league", required=True)
    ap.add_argument("--out-dir", default=None, help="default: data/external (cfg paths.external)")
    a = ap.parse_args()

    default_league = None
    out_dir = Path(a.out_dir) if a.out_dir else None
    try:
        sys.path.insert(0, str(ROOT))
        from draftkit.config import Config  # noqa: E402
        cfg = Config.load(league=a.league)
        default_league = cfg._data.get("default_league")
        if out_dir is None:
            out_dir = cfg.path("external")
    except Exception as e:  # noqa: BLE001 -- the script is useful without a league yaml
        print(f"  (config not loaded: {type(e).__name__}: {e}; using data/external)")
        if out_dir is None:
            out_dir = ROOT / "data" / "external"

    c = run(Path(a.snapshot), a.league, out_dir, default_league)
    print(f"snapshot room {c['source_room']} captured {c['captured_at']}: {c['players']} players")
    print(f"  yahoo_rank rows: {c['rank']} ({c['def']} DEF)  skipped (no o_rank): {c['no_rank']}")
    print(f"    -> {c['rank_path']}")
    print(f"  yahoo adp (avg_pick) rows: {c['adp']}")
    print(f"    -> {c['adp_path']}  (yahoo_adp.<league>.csv NOT touched)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

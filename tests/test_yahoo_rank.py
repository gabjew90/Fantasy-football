"""Yahoo default rank (o_rank) plumbing, DECISIONS #35.

Snapshot -> data/external/yahoo_rank.<league>.csv -> market join -> board
column `yahoo_rank` -> the bridge/parity loaders. The column is informational:
the join must add exactly one column and move nothing else.
"""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


yrs = _load("yrs", "scripts/yahoo_rank_from_snapshot.py")


SNAP = {
    "room": "players_1", "kind": "players_snapshot", "source_room": "1",
    "captured_at": "2026-09-03T00:00:00Z", "n": 5,
    "players": [
        {"id": "1", "name": "Bijan Robinson", "pos": "RB", "team": "Atl",
         "o_rank": 2, "psr_rank": 1, "avg_pick": 2.1, "pct_drafted": 1.0, "bye": 5},
        {"id": "2", "name": "Ja'Marr Chase", "pos": "WR", "team": "Cin",
         "o_rank": 1, "psr_rank": 2, "avg_pick": 1.4, "pct_drafted": 1.0, "bye": 10},
        {"id": "3", "name": "Marcedes Lewis", "pos": "TE", "team": "Den",
         "o_rank": 2154, "psr_rank": 1060, "avg_pick": None, "pct_drafted": None, "bye": 10},
        {"id": "100001", "name": "Texans", "pos": "DEF", "team": "Hou",
         "o_rank": 155, "psr_rank": 3, "avg_pick": 97.6, "pct_drafted": 0.5, "bye": 6},
        {"id": "4", "name": "Nobody Ranked", "pos": "QB", "team": "Fa",
         "o_rank": None, "psr_rank": None, "avg_pick": None, "pct_drafted": None, "bye": None},
    ],
}


def _rows(path: Path) -> list[dict]:
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def test_snapshot_script_writes_rank_and_snapshot_adp_but_not_curated_adp(tmp_path):
    snap = tmp_path / "mock_players_1.json"
    snap.write_text(json.dumps(SNAP), encoding="utf-8")
    out = tmp_path / "external"
    curated = out / "yahoo_adp.keefamania.csv"
    out.mkdir()
    curated.write_text("name,pos,adp\nSomeone,RB,9.9\n", encoding="utf-8")

    c = yrs.run(snap, "keefamania", out, default_league="omnibeta")

    rank = _rows(out / "yahoo_rank.keefamania.csv")
    assert [tuple(r.values()) for r in rank] == [
        ("Ja'Marr Chase", "WR", "1"), ("Bijan Robinson", "RB", "2"),
        ("Texans", "DEF", "155"), ("Marcedes Lewis", "TE", "2154"),
    ]  # null o_rank skipped; DEF keeps Yahoo's own nickname
    assert list(rank[0].keys()) == ["name", "pos", "yahoo_rank"]
    adp = _rows(out / "yahoo_adp_snapshot.keefamania.csv")
    assert [r["name"] for r in adp] == ["Ja'Marr Chase", "Bijan Robinson", "Texans"]
    assert list(adp[0].keys()) == ["name", "pos", "adp"]
    assert curated.read_text(encoding="utf-8") == "name,pos,adp\nSomeone,RB,9.9\n"
    assert (c["players"], c["rank"], c["no_rank"], c["adp"], c["def"]) == (5, 4, 1, 3, 1)


def test_snapshot_script_is_idempotent_and_scopes_like_config(tmp_path):
    snap = tmp_path / "s.json"
    snap.write_text(json.dumps(SNAP), encoding="utf-8")
    out = tmp_path / "ext"
    yrs.run(snap, "keefamania", out, default_league="omnibeta")
    first = (out / "yahoo_rank.keefamania.csv").read_bytes()
    yrs.run(snap, "keefamania", out, default_league="omnibeta")
    assert (out / "yahoo_rank.keefamania.csv").read_bytes() == first
    # the default league keeps the bare filename, exactly like Config.scoped
    yrs.run(snap, "omnibeta", out, default_league="omnibeta")
    assert (out / "yahoo_rank.csv").exists()
    assert (out / "yahoo_adp_snapshot.csv").exists()


def _market() -> pl.DataFrame:
    return pl.DataFrame({
        "sleeper_id": ["1", "2", "3", "4", "5"],
        "name": ["Bijan Robinson", "Ja'Marr Chase", "Houston Texans", "Marvin Harrison Jr.", "Brian Robinson Jr."],
        "pos": ["RB", "WR", "DEF", "WR", "RB"],
        "team": ["ATL", "CIN", "HOU", "ARI", "WAS"],
        "ecr": [2.0, 1.0, 150.0, 30.0, 80.0],
        "ecr_sd": [0.5, 0.4, None, 3.0, 5.0],
        "bye": [5, 10, 6, 8, 12],
        "adp": [2.1, 1.4, 97.6, 28.0, 85.0],
    })


def test_market_join_adds_yahoo_rank_and_moves_nothing_else(tmp_path):
    from draftkit.market import attach_yahoo_rank

    p = tmp_path / "yahoo_rank.keefamania.csv"
    p.write_text(
        "name,pos,yahoo_rank\n"
        "Bijan Robinson,RB,2\n"
        "Ja'Marr Chase,WR,1\n"
        "Texans,DEF,155\n"
        "Marvin Harrison,WR,25\n"      # suffix dropped on Yahoo's side
        "Bijan Robinson,WR,999\n",     # same name, other position: must not cross-assign
        encoding="utf-8",
    )
    before = _market()
    out, matched = attach_yahoo_rank(before, p)
    assert out.columns == before.columns + ["yahoo_rank"]
    assert out.schema["yahoo_rank"] == pl.Float64
    for c in before.columns:
        assert out[c].equals(before[c]), c
    assert out["yahoo_rank"].to_list() == [2.0, 1.0, 155.0, 25.0, None]
    assert matched == 4


def test_market_join_def_matches_on_nickname_only():
    from draftkit.market import _yahoo_key_expr

    df = pl.DataFrame({"name": ["Houston Texans", "Texans", "Los Angeles Rams", "Rams", "Ja'Marr Chase"],
                       "pos": ["DEF", "DEF", "DEF", "DEF", "WR"]})
    keys = df.select(_yahoo_key_expr(pl.col("name"), pl.col("pos")).alias("k"))["k"].to_list()
    assert keys == ["texans", "texans", "rams", "rams", "jamarrchase"]


def test_write_tiers_csv_carries_yahoo_rank_rounded(tmp_path):
    from draftkit.tiers import TIERS_COLUMNS, write_tiers_csv

    assert "yahoo_rank" in TIERS_COLUMNS
    df = pl.DataFrame({
        "name": ["A", "B"], "pos": ["RB", "WR"], "proj_pts": [200.04, 150.0],
        "vorp": [10.0, 5.0], "adp_delta": [0.0, 0.0], "exp_games": [16.0, 16.0],
        "wopr": [0.5, 0.4], "tprr": [0.2, 0.2], "yprr": [1.5, 1.4],
        "yahoo_rank": [3.0, None],
    })
    write_tiers_csv(df, tmp_path / "t.csv")
    rows = _rows(tmp_path / "t.csv")
    assert [r["yahoo_rank"] for r in rows] == ["3.0", ""]


def _board_csv(tmp_path: Path, with_rank: bool) -> Path:
    cols = ["player", "pos", "team", "vorp", "proj_pts", "adp", "tier", "pos_rank", "value_rank", "bye"]
    rows = [["A Back", "RB", "ATL", "50.0", "250.0", "3.0", "1", "1", "1", "5"],
            ["B Wide", "WR", "CIN", "40.0", "240.0", "", "1", "1", "2", "10"]]
    if with_rank:
        cols.append("yahoo_rank")
        rows[0].append("2.0")
        rows[1].append("")
    p = tmp_path / ("tiers_rank.csv" if with_rank else "tiers_plain.csv")
    with open(p, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        w.writerows(rows)
    return p


def test_parity_load_board_carries_yahoo_rank_and_tolerates_absence(tmp_path):
    ep = _load("ep", "scripts/engine_parity.py")
    with_rank = {p["name"]: p["yahoo_rank"] for p in ep.load_board(str(_board_csv(tmp_path, True)))}
    assert with_rank == {"A Back": 2.0, "B Wide": None}
    plain = ep.load_board(str(_board_csv(tmp_path, False)))
    assert all(p["yahoo_rank"] is None for p in plain)


def test_bridge_load_players_carries_yahoo_rank_and_tolerates_absence(tmp_path):
    from draftkit.config import Config
    yb = _load("yb_rank", "scripts/yahoo_bridge.py")

    for with_rank, want in ((True, {"A Back": 2.0, "B Wide": None}), (False, {"A Back": None, "B Wide": None})):
        p = _board_csv(tmp_path, with_rank)
        (tmp_path / "tiers.csv").write_bytes(p.read_bytes())
        cfg = Config({"default_league": None}, tmp_path)
        got = {x["name"]: x["yahoo_rank"] for x in yb.load_players(cfg)}
        assert got == want


def test_export_board_json_carries_yr(tmp_path):
    import subprocess
    import sys

    board = _board_csv(tmp_path, True)
    out = tmp_path / "board.json"
    subprocess.run([sys.executable, str(ROOT / "scripts" / "export_board_json.py"),
                    "--board", str(board), "--out", str(out)], check=True, capture_output=True)
    got = {r["n"]: r["yr"] for r in json.loads(out.read_text(encoding="utf-8"))}
    assert got == {"A Back": 2.0, "B Wide": None}

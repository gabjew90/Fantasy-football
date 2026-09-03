"""Board identity harness (plan 2026-09-02 A0).

Every projection-side step ships behind a flag, and "flag off" must mean
byte-identical boards. This builds a board IN PROCESS exactly as
`draftkit tiers` does (projection -> tilts -> finish_board -> tiers csv),
with any config keys overridden on the command line, and either records
it as a reference or checks it against one:

    venv\\Scripts\\python.exe scripts\\board_identity.py --league keefamania --write-ref data\\draftrig\\ref_model.keefamania.csv
    venv\\Scripts\\python.exe scripts\\board_identity.py --league keefamania --set projections.source=external --check data\\draftrig\\ref_external.keefamania.csv

The check compares, in order: row count; proj_pts, vorp, tier and
value_rank joined on sleeper_id (the valuation columns); then the whole
file after dropping columns the reference does not have (a step may ADD
columns; it may not change existing ones). Nonzero exit on any drift.

Inputs are pinned so two builds see the same data: the Sleeper stat-line
cache and the id map are read as-is regardless of age (their TTLs would
otherwise refresh mid-comparison and read as drift that no code change
caused).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import polars as pl

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.config import Config, _deep_merge  # noqa: E402

VALUATION = ("proj_pts", "vorp", "tier", "value_rank")


def parse_set(items: list[str]) -> dict:
    """['projections.source=external', 'projections.games_table.enabled=true'] -> nested dict."""
    out: dict = {}
    for kv in items:
        key, _, raw = kv.partition("=")
        v: object = raw
        if raw.lower() in ("true", "false"):
            v = raw.lower() == "true"
        else:
            try:
                v = int(raw) if raw.lstrip("-").isdigit() else float(raw)
            except ValueError:
                v = raw
        node = out
        parts = key.split(".")
        for p in parts[:-1]:
            node = node.setdefault(p, {})
        node[parts[-1]] = v
    return out


def build(league: str, overrides: dict) -> pl.DataFrame:
    import draftkit.consensus as consensus
    import draftkit.ids as ids
    from draftkit.projections import PROJECTION_FNS
    from draftkit.tiers import TIERS_COLUMNS, finish_board
    from draftkit.tilts import apply_tilts, prior_top5_by_pos
    consensus.CACHE_TTL = 10 ** 9
    if hasattr(ids, "CACHE_TTL"):
        ids.CACHE_TTL = 10 ** 9
    base = Config.load(league=league)
    cfg = Config(_deep_merge(base._data, overrides), base.root, base.league_name) if overrides else base
    processed = cfg.path("processed")
    market = pl.read_parquet(cfg.scoped(processed / "market.parquet"))
    usage = pl.read_parquet(cfg.scoped(processed / "usage.parquet"))
    df = PROJECTION_FNS["default"](cfg, usage, market)
    df, _ = apply_tilts(df, cfg.get("tilts"), prior_top5_by_pos(usage))
    tiers = finish_board(df, cfg).rename({"name": "player"})
    return tiers.select([c for c in TIERS_COLUMNS if c in tiers.columns])


def compare(new: pl.DataFrame, ref: pl.DataFrame) -> list[str]:
    """Human-readable drift lines; empty means IDENTICAL."""
    out = []
    if new.height != ref.height:
        out.append(f"row count {ref.height} -> {new.height}")
    key = "sleeper_id"
    n = new.select([key, *[c for c in VALUATION if c in new.columns]]).with_columns(pl.col(key).cast(pl.Utf8))
    r = ref.select([key, *[c for c in VALUATION if c in ref.columns]]).with_columns(pl.col(key).cast(pl.Utf8))
    j = r.join(n, on=key, how="full", suffix="_new", coalesce=True)
    missing = j.filter(pl.col(VALUATION[0] + "_new").is_null()).height if VALUATION[0] + "_new" in j.columns else 0
    added = j.filter(pl.col(VALUATION[0]).is_null()).height
    if missing or added:
        out.append(f"players: {missing} left the board, {added} joined")
    for c in VALUATION:
        if c in n.columns and c in r.columns:
            d = j.filter(pl.col(c).is_not_null() & pl.col(c + "_new").is_not_null()
                         & ((pl.col(c).cast(pl.Float64) - pl.col(c + "_new").cast(pl.Float64)).abs() > 1e-9))
            if d.height:
                out.append(f"{c}: {d.height} rows moved")
    common = [c for c in ref.columns if c in new.columns]
    a = ref.select(common).with_columns(pl.all().cast(pl.Utf8)).fill_null("")
    b = new.select(common).with_columns(pl.all().cast(pl.Utf8)).fill_null("")
    if a.height == b.height:
        diff_cols = [c for c in common if not a[c].equals(b[c])]
        if diff_cols:
            out.append("other columns differ: " + ", ".join(diff_cols[:12]))
    extra = [c for c in new.columns if c not in ref.columns]
    if extra:
        out.append("note: new columns (allowed): " + ", ".join(extra))
    return [x for x in out if not x.startswith("note:")] + [x for x in out if x.startswith("note:")]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--league", required=True)
    ap.add_argument("--set", action="append", default=[], metavar="KEY.PATH=VALUE")
    ap.add_argument("--write-ref", default=None)
    ap.add_argument("--check", default=None)
    a = ap.parse_args()
    board = build(a.league, parse_set(a.set))
    if a.write_ref:
        Path(a.write_ref).parent.mkdir(parents=True, exist_ok=True)
        board.write_csv(a.write_ref)
        print(f"reference written: {a.write_ref} ({board.height} rows, {len(board.columns)} columns)")
        return 0
    if a.check:
        ref = pl.read_csv(a.check, infer_schema_length=10000)
        lines = compare(board, ref)
        drift = [x for x in lines if not x.startswith("note:")]
        tag = "IDENTICAL" if not drift else "DRIFT"
        print(f"{tag}: {a.league} {' '.join(a.set)} vs {Path(a.check).name}")
        for x in lines:
            print("  " + x)
        return 0 if not drift else 1
    print(f"built {board.height} rows; pass --write-ref or --check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

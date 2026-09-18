"""Roll the settled record into a scorecard.

Three questions the record exists to answer:

1. Calibration. When the model says 65%, does it hit 65%? Bucketed by model
   probability, this is the only thing that distinguishes a real edge from a
   model that is simply confident.
2. Tier validity. WEAK tier encodes the assumption "a big gap means the book
   knows something". That is a prior, not a proof. If WEAK calls hit at the
   model's rate rather than the book's, the assumption is wrong and the tier
   rule should change.
3. Closing line value. For every call with both a `decision` and a `close`
   snapshot, did the line move toward the call? CLV is the earliest reliable
   signal of edge, because it does not need the bet to win.

Writes `record/scorecard.md` and `record/scorecard.csv`.

Usage:
    python props/scorecard.py --season 2026
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import persist  # noqa: E402

try:
    import pandas as pd
except ImportError:  # pragma: no cover
    print("pandas is required: pip install -r props/requirements.txt", file=sys.stderr)
    raise

BUCKETS = [(0.50, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70),
           (0.70, 0.80), (0.80, 1.01)]


def tier_base(tier: str) -> str:
    """Tiers carry parenthetical annotations; group on the base word."""
    t = str(tier or "").strip()
    for base in ("STRONG", "MODERATE", "WEAK", "LEAN"):
        if t.startswith(base):
            return base
    return "UNTIERED"


def load_settled(season: int) -> pd.DataFrame:
    path = persist.settled_path(season)
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df = df[df["status"] == "settled"].copy()
    if df.empty:
        return df
    df["won"] = pd.to_numeric(df["won"], errors="coerce")
    df["p_model"] = pd.to_numeric(df["p_model"], errors="coerce")
    df["p_novig"] = pd.to_numeric(df["p_novig"], errors="coerce")
    df["pnl_per_100"] = pd.to_numeric(df["pnl_per_100"], errors="coerce")
    df["tier_base"] = df["tier"].map(tier_base)
    return df


def clv_table(season: int) -> pd.DataFrame:
    """Line movement between the decision snapshot and the closing snapshot."""
    rows = []
    pred_dir = persist.RECORD_ROOT / "predictions" / str(season)
    for f in sorted(pred_dir.glob("wk*.jsonl")) if pred_dir.is_dir() else []:
        with f.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    keys = ["season", "week", "event_id", "book", "market", "player", "side"]
    dec = df[df["snapshot_type"] == "decision"]
    close = df[df["snapshot_type"] == "close"]
    if dec.empty or close.empty:
        return pd.DataFrame()
    m = dec.merge(close, on=keys, suffixes=("_dec", "_close"))
    if m.empty:
        return m
    # A line moving toward an Under call means the number came down.
    m["line_move"] = m["line_close"] - m["line_dec"]
    m["moved_our_way"] = (
        ((m["side"].str.lower() == "under") & (m["line_move"] < 0)) |
        ((m["side"].str.lower() == "over") & (m["line_move"] > 0))
    )
    return m[keys + ["line_dec", "line_close", "line_move", "moved_our_way",
                     "tier_dec", "p_model_dec"]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    args = ap.parse_args()

    df = load_settled(args.season)
    out = [f"# Props scorecard — {args.season}", ""]

    if df.empty:
        out += ["No settled calls yet. Run `props/settle.py` after results "
                "publish (nflverse weekly stats land Tuesday morning ET).", ""]
        (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out),
                                                          encoding="utf-8")
        print("no settled rows yet")
        return 0

    n = len(df)
    hits = int(df["won"].sum())
    out += [f"{n} settled calls, {hits} winners ({hits / n:.1%}), "
            f"net {df['pnl_per_100'].sum():+.0f} per $100 flat-staked.", ""]

    out += ["## Calibration: does the model's probability mean anything?", "",
            "| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |",
            "|---|---|---|---|---|---|"]
    rows = []
    for lo, hi in BUCKETS:
        b = df[(df["p_model"] >= lo) & (df["p_model"] < hi)]
        if b.empty:
            continue
        hr, stated = b["won"].mean(), b["p_model"].mean()
        rows.append({"bucket": f"{lo:.0%}-{hi:.0%}", "n": len(b),
                     "hit_rate": hr, "stated": stated, "diff": hr - stated,
                     "net": b["pnl_per_100"].sum()})
        out.append(f"| {lo:.0%}-{hi:.0%} | {len(b)} | {hr:.1%} | {stated:.1%} "
                   f"| {hr - stated:+.1%} | {b['pnl_per_100'].sum():+.0f} |")
    out += ["", "A bucket needs roughly 50 calls before its hit rate says "
            "anything; below that the difference is noise.", ""]

    out += ["## Tier validity: is a big gap the book knowing something?", "",
            "| Tier | Calls | Hit rate | Model said | Book said | Net/$100 |",
            "|---|---|---|---|---|---|"]
    for tier in ("STRONG", "MODERATE", "LEAN", "WEAK", "UNTIERED"):
        b = df[df["tier_base"] == tier]
        if b.empty:
            continue
        out.append(f"| {tier} | {len(b)} | {b['won'].mean():.1%} | "
                   f"{b['p_model'].mean():.1%} | {b['p_novig'].mean():.1%} | "
                   f"{b['pnl_per_100'].sum():+.0f} |")
    out += ["", "WEAK exists on the assumption the book is right when it "
            "disagrees sharply. If WEAK hits nearer the model column than the "
            "book column, that assumption is costing money and the tier rule "
            "should change.", ""]

    out += ["## By market", "",
            "| Market | Calls | Hit rate | Model said | Net/$100 |",
            "|---|---|---|---|---|"]
    for mkt, b in df.groupby("market"):
        out.append(f"| {mkt} | {len(b)} | {b['won'].mean():.1%} | "
                   f"{b['p_model'].mean():.1%} | {b['pnl_per_100'].sum():+.0f} |")
    out += ["", "Receptions and receiving yards are the only backtested "
            "markets; rushing and anytime TD have no backtest at all, so their "
            "rows here are the first evidence either way.", ""]

    out += ["## By week", "", "| Week | Calls | Hit rate | Net/$100 |",
            "|---|---|---|---|"]
    for wk, b in df.groupby("week"):
        out.append(f"| {wk} | {len(b)} | {b['won'].mean():.1%} | "
                   f"{b['pnl_per_100'].sum():+.0f} |")
    out.append("")

    clv = clv_table(args.season)
    out += ["## Closing line value", ""]
    if clv.empty:
        out += ["No paired decision/close snapshots yet. CLV needs a closing "
                "capture inside 60 minutes of kickoff; without it, closing-line "
                "value is unavailable and must not be estimated.", ""]
    else:
        share = clv["moved_our_way"].mean()
        out += [f"{len(clv)} calls have both snapshots. The line moved toward "
                f"the call {share:.1%} of the time (mean move "
                f"{clv['line_move'].mean():+.2f}).", "",
                "Beating the close consistently is the signal that survives "
                "small samples. Winning without it is variance.", ""]

    (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out), encoding="utf-8")
    if rows:
        pd.DataFrame(rows).to_csv(persist.RECORD_ROOT / "scorecard.csv", index=False)
    print(f"[{persist.mode()}] wrote {persist.RECORD_ROOT / 'scorecard.md'} "
          f"({n} settled calls)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

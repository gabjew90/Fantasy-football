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
import calls as calls_mod  # noqa: E402
import blend  # noqa: E402
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
    # ONE CALL PER MARKET. Every priced line is graded, but a line that moved
    # between two capture ticks is history, not a second decision (see
    # props/calls.py). A settled file written before is_call existed is read
    # as all-calls rather than crashing the Tuesday job.
    if "is_call" not in df.columns:
        print("settled file predates is_call; counting every graded row. "
              "Re-run props/settle.py to separate calls from line history.",
              file=sys.stderr)
        df["is_call"] = 1
    df["is_call"] = pd.to_numeric(df["is_call"], errors="coerce").fillna(0).astype(int)
    if "engine_hash" not in df.columns:
        df["engine_hash"] = ""
    if "engine_tag" not in df.columns:
        df["engine_tag"] = None
    # THE PRICING MODEL (DECISIONS #107). A settled file written before
    # model_id existed gets it derived here, by the same function settle uses.
    if "model_id" not in df.columns:
        df["model_id"] = None
    missing = df["model_id"].isna() | (df["model_id"].astype(str).str.strip() == "")
    if missing.any():
        df.loc[missing, "model_id"] = [calls_mod.engine_version.model_id(r)
                                       for r in df.loc[missing].to_dict("records")]
    df["market_key"] = market_key(df)
    return df


def market_key(df: pd.DataFrame) -> pd.Series:
    """The market, and for anytime TD the model that priced it. Rows captured
    before td_model reached the record (props-v1.7) carry no stamp: they are
    'model unknown', never assumed to be v1, so a v0-fallback row is not
    pooled with v1 rows on the first graded week."""
    tdm = df["td_model"] if "td_model" in df.columns else pd.Series(None, index=df.index, dtype=object)
    tdm = tdm.where(tdm.notna() & (tdm.astype(str).str.strip() != ""), "model unknown")
    return df["market"].where(df["market"] != "player_anytime_td",
                              "player_anytime_td [" + tdm.astype(str) + "]")


def _tag_order(tag: str) -> tuple:
    return tuple(int(x) if x.isdigit() else x for x in tag.replace("props-v", "").split("."))


def engine_label(df: pd.DataFrame) -> str:
    """How a pricing model is named in a heading: the release tags that share
    it, else a short hash."""
    tags = sorted({t for t in df.get("engine_tag", []) if isinstance(t, str) and t}, key=_tag_order)
    if tags:
        return tags[0] if len(tags) == 1 else f"{', '.join(tags)} (one pricing model)"
    h = next((x for x in df.get("model_id", []) if isinstance(x, str) and x), "")
    return h[:12] if h else "unidentified engine"


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

    # ONE ROW PER SIDE OF THE JOIN, so a moved line cannot fan out. The old
    # join was on seven fields that excluded `line`, so McCaffrey's two
    # decision rows (58.5, then 59.5) would each have paired with every close
    # row for that market and one call would have become several CLV rows
    # with an ambiguous opening number.
    decisions, _ties = calls_mod.select_calls(rows, "decision")
    # The closing price is a market fact, so the close side ignores the
    # engine: if the engine changed between the decision and the close, the
    # deciding engine still gets its CLV. It must be the LAST close -- see
    # calls.last_per on why the first would misreport an early-window run.
    market_key = tuple(f for f in calls_mod.CALL_KEY if f != "model_id")
    closes = calls_mod.last_per(rows, "close", market_key)
    if not decisions or not closes:
        return pd.DataFrame()

    paired = []
    for key, dec in decisions.items():
        close = closes.get(tuple(key[:-1]))    # drop model_id
        if close is None:
            continue
        # Both sides come from the predictions file, so both carry `line`.
        # An anytime-TD row has none, and a market without a number has
        # no line movement to measure.
        if dec.get("line") is None or close.get("line") is None:
            continue
        close_line = close["line"]
        if close_line is None:
            continue
        move = float(close_line) - float(dec["line"])
        side = str(dec.get("side") or "").lower()
        paired.append({
            "season": dec.get("season"), "week": dec.get("week"),
            "event_id": dec.get("event_id"), "book": dec.get("book"),
            "market": dec.get("market"), "player": dec.get("player"),
            "side": dec.get("side"), "engine_hash": dec.get("engine_hash"),
            "model_id": key[-1],
            "engine_tag": dec.get("engine_tag"),
            "line_dec": float(dec["line"]), "line_close": float(close_line),
            "line_move": move,
            # A line moving toward an Under call means the number came down.
            "moved_our_way": (move < 0 if side == "under"
                              else move > 0 if side == "over" else False),
            "tier_dec": dec.get("tier"), "p_model_dec": dec.get("p_model"),
        })
    return pd.DataFrame(paired)


def render_sections(df: pd.DataFrame) -> tuple[list[str], list[dict]]:
    """The four rollups for one engine's calls. (markdown lines, csv rows)."""
    out: list[str] = []
    rows: list[dict] = []
    keys = df["market_key"] if "market_key" in df.columns else market_key(df)
    # the pooled tables must not mix anytime-TD models: v0-fallback and
    # 'model unknown' rows appear only in the By-market split below
    other_td = keys.str.startswith("player_anytime_td") & (keys != "player_anytime_td [anytime_td_v1]")
    full, df = df, df[~other_td]
    n = len(df)
    hits = int(df["won"].sum())
    out += [f"{n} settled calls, {hits} winners ({hits / max(n, 1):.1%}), "
            f"net {df['pnl_per_100'].sum():+.0f} per $100 flat-staked.", ""]

    out += ["### Calibration: does the model's probability mean anything?", "",
            "| Model prob | Calls | Hit rate | Stated | Diff | Net/$100 |",
            "|---|---|---|---|---|---|"]
    for lo, hi in BUCKETS:
        b = df[(df["p_model"] >= lo) & (df["p_model"] < hi)]
        if b.empty:
            continue
        hr, stated = b["won"].mean(), b["p_model"].mean()
        rows.append({"bucket": f"{lo:.0%}-{hi:.0%}", "n": len(b),
                     "hit_rate": hr, "stated": stated, "diff": hr - stated,
                     "net": b["pnl_per_100"].sum(),
                     "engine_hash": df["engine_hash"].iloc[0] if n else "",
                     "model_id": df["model_id"].iloc[0] if n and "model_id" in df else ""})
        out.append(f"| {lo:.0%}-{hi:.0%} | {len(b)} | {hr:.1%} | {stated:.1%} "
                   f"| {hr - stated:+.1%} | {b['pnl_per_100'].sum():+.0f} |")
    out += ["", "A bucket needs roughly 50 calls before its hit rate says "
            "anything; below that the difference is noise.", ""]

    out += ["### Tier validity: is a big gap the book knowing something?", "",
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

    out += ["### By market", ""]
    if other_td.any():
        out += [f"{int(other_td.sum())} anytime-TD calls priced by the v0 fallback or by an unrecorded "
                "model are left out of the tables above and shown only here.", ""]
    out += ["| Market | Calls | Hit rate | Model said | Net/$100 |",
            "|---|---|---|---|---|"]
    for mkt, b in full.groupby(keys):
        out.append(f"| {mkt} | {len(b)} | {b['won'].mean():.1%} | "
                   f"{b['p_model'].mean():.1%} | {b['pnl_per_100'].sum():+.0f} |")
    out += ["", "Receptions and receiving yards are the only backtested "
            "markets; rushing and anytime TD have no backtest at all, so their "
            "rows here are the first evidence either way.", ""]

    out += ["### Priced with a Questionable teammate", "",
            "| Teammate Questionable at pricing | Calls | Hit rate | Model said | Net/$100 |",
            "|---|---|---|---|---|"]
    qt = df["questionable_teammate"] if "questionable_teammate" in df else pd.Series(False, index=df.index)
    qt = qt.map(lambda v: str(v).strip().lower() in ("true", "1", "1.0"))
    for lab, b in (("yes", df[qt]), ("no", df[~qt])):
        if not b.empty:
            out.append(f"| {lab} | {len(b)} | {b['won'].mean():.1%} | "
                       f"{b['p_model'].mean():.1%} | {b['pnl_per_100'].sum():+.0f} |")
    out += ["", "Those rows assume the teammate played. When he sat, they graded "
            "against a line priced on the wrong roster; if 'yes' runs apart from "
            "'no', that is the cost.", ""]

    out += ["### By week", "", "| Week | Calls | Hit rate | Net/$100 |",
            "|---|---|---|---|"]
    for wk, b in df.groupby("week"):
        out.append(f"| {wk} | {len(b)} | {b['won'].mean():.1%} | "
                   f"{b['pnl_per_100'].sum():+.0f} |")
    out.append("")
    return out, rows


def render_clv(clv: pd.DataFrame, model: str | None = None) -> list[str]:
    """The CLV paragraph, for one pricing model or (model=None) for all."""
    if model is not None and not clv.empty and "model_id" in clv:
        clv = clv[clv["model_id"] == model]
    out = ["### Closing line value", ""]
    if clv.empty:
        out += ["No paired decision/close snapshots yet. CLV needs a closing "
                "capture inside 60 minutes of kickoff; without it, closing-line "
                "value is unavailable and must not be estimated.", ""]
        return out
    share = clv["moved_our_way"].mean()
    out += [f"{len(clv)} calls have both snapshots. The line moved toward "
            f"the call {share:.1%} of the time (mean move "
            f"{clv['line_move'].mean():+.2f}).", "",
            "Beating the close consistently is the signal that survives "
            "small samples. Winning without it is variance.", ""]
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--season", type=int, required=True)
    ap.add_argument("--pool", action="store_true",
                    help="also print one set of rollups over every engine "
                         "version, which is only meaningful once you have "
                         "decided the versions are comparable")
    args = ap.parse_args(argv)

    settled = load_settled(args.season)
    out = [f"# Props scorecard — {args.season}", ""]

    if settled.empty:
        out += ["No settled calls yet. Run `props/settle.py` after results "
                "publish (nflverse weekly stats land Tuesday morning ET).", ""]
        (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out),
                                                          encoding="utf-8")
        print("no settled rows yet")
        return 0

    graded = len(settled)
    df = settled[settled["is_call"] == 1]
    if df.empty:
        out += [f"{graded} rows graded, none of them a call. A call is the "
                f"last decision for a market; if every row is a superseded "
                f"line, re-run props/settle.py.", ""]
        (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out),
                                                          encoding="utf-8")
        print("no calls among the settled rows")
        return 0

    clv = clv_table(args.season)
    engines = list(df.groupby("model_id", dropna=False))

    out += [f"{len(df)} calls ({graded} priced lines graded, so "
            f"{graded - len(df)} superseded by a later line).", ""]

    # TWO ENGINES ARE NOT ONE SAMPLE. Pooling calls from different model
    # versions produces one number that describes neither, so the default is
    # per-engine sections and NO grand total. --pool is the explicit
    # override, because whether two versions are comparable is the user's
    # judgement to make, not this script's.
    if len(engines) > 1:
        labels = ", ".join(engine_label(g) for _h, g in engines)
        out += [f"**{len(engines)} pricing models in the record ({labels}); "
                f"they are not pooled.** Pass `--pool` to pool them "
                f"explicitly.", ""]

    csv_rows: list[dict] = []
    for engine_hash, group in engines:
        out += [f"## Engine {engine_label(group)}", ""]
        sections, rows = render_sections(group)
        out += sections
        csv_rows += rows
        out += render_clv(clv, engine_hash)
        out += blend.blend_section(group)

    if args.pool and len(engines) > 1:
        out += ["## All engines (pooled by request)", "",
                "These calls come from different model versions; the pooled "
                "numbers describe no single one of them.", ""]
        sections, _rows = render_sections(df)
        out += sections
        out += render_clv(clv)

    (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out), encoding="utf-8")
    if csv_rows:
        pd.DataFrame(csv_rows).to_csv(persist.RECORD_ROOT / "scorecard.csv", index=False)
    print(f"[{persist.mode()}] wrote {persist.RECORD_ROOT / 'scorecard.md'} "
          f"({len(df)} calls of {graded} graded rows, "
          f"{len(engines)} engine version(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

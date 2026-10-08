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
import journal  # noqa: E402
import persist  # noqa: E402

try:
    import numpy as np
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


BOOKS_MIN = 200                     # reports/sleeper_vs_books.md: the reading rule's sample
LINE_OFF = {"player_receptions": 0.5, "player_reception_yds": 2.5, "player_rush_yds": 2.5,
            "player_pass_yds": 5.0, "player_rush_reception_yds": 3.0}
PRICE_OFF = 0.03


def _novig_over(po, pu):
    """The no-vig Over chance from two American prices."""
    io = 100 / (po + 100) if po > 0 else -po / (-po + 100)
    iu = 100 / (pu + 100) if pu > 0 else -pu / (-pu + 100)
    return io / (io + iu)


def books_consensus(rows: list[dict]) -> dict:
    """(week, player key, market) -> (consensus line, consensus no-vig Over
    chance at that line) from DraftKings/FanDuel comparison rows."""
    import settle as _s
    by: dict = {}
    for r in rows:
        k = (int(r["week"]), _s.norm_name(str(r["player"])), r["market"], r["book"], float(r["line"]))
        by.setdefault(k, {})[r["side"]] = int(r["price"])
    per: dict = {}
    for (wk, nm, mk, bk, ln), sides in by.items():
        if "Over" in sides and "Under" in sides:
            per.setdefault((wk, nm, mk), []).append((ln, _novig_over(sides["Over"], sides["Under"])))
    out = {}
    for k, v in per.items():
        lines = sorted(x[0] for x in v)
        med = lines[len(lines) // 2] if len(lines) % 2 else (lines[len(lines) // 2 - 1] + lines[len(lines) // 2]) / 2
        at = [p for ln, p in v if ln == med]
        # no book at the median line (DK 3.5, FD 4.5): no consensus PRICE there,
        # only a consensus line -- prices quoted at different lines never average
        out[k] = (med, sum(at) / len(at) if at else None)
    return out


def books_rows(df: pd.DataFrame, rows: list[dict]) -> pd.DataFrame:
    """Each settled Sleeper call joined to the consensus, with the favoured side
    graded at Sleeper's own price (reports/sleeper_vs_books.md)."""
    import settle as _s
    if not rows or df.empty or "price_over" not in df.columns:
        return pd.DataFrame()
    cons = books_consensus(rows)
    out = []
    # one bet per Sleeper line: the same line can be a call under two pricing
    # models in one week (an engine release mid-week)
    d0 = df[df["market"].isin(list(LINE_OFF))].drop_duplicates(["week", "player", "market", "line"], keep="last")
    for _, r in d0.iterrows():
        try:
            line, actual = float(r["line"]), float(r["actual"])
            po, pu = int(float(r["price_over"])), int(float(r["price_under"]))
        except (TypeError, ValueError):
            continue
        c = cons.get((int(r["week"]), _s.norm_name(str(r["player"])), r["market"]))
        if c is None:
            continue
        d = line - c[0]
        if abs(d) >= LINE_OFF[r["market"]]:
            kind, fav = "line off", ("Under" if d > 0 else "Over")
        elif d == 0 and c[1] is not None and abs(c[1] - _novig_over(po, pu)) >= PRICE_OFF:
            kind, fav = "price off", ("Over" if c[1] > _novig_over(po, pu) else "Under")
        else:
            continue
        if actual == line:
            won, pnl = None, 0.0
        else:
            won = (actual > line) if fav == "Over" else (actual < line)
            pnl = _s.american_pnl(po if fav == "Over" else pu, won)
        price = po if fav == "Over" else pu
        out.append({"kind": kind, "event_id": r.get("event_id"), "won": won, "pnl": pnl,
                    "breakeven": (abs(price) / (abs(price) + 100) if price < 0 else 100 / (price + 100))})
    return pd.DataFrame(out)


def books_section(df: pd.DataFrame, season: int) -> list[str]:
    """Sleeper against DraftKings/FanDuel: the consensus-favoured side at
    Sleeper's price, by discrepancy type, with the pre-registered reading rule."""
    root = persist.RECORD_ROOT / "compare" / str(season)
    rows = []
    for f in sorted(root.glob("wk*.jsonl")) if root.exists() else []:
        with f.open(encoding="utf-8") as fh:
            rows += [json.loads(ln) for ln in fh if ln.strip()]
    out = ["## Sleeper against DraftKings/FanDuel", "",
           "Not the model: when Sleeper's line or price sits off the DraftKings/FanDuel consensus, the side the "
           "consensus favours, bet at Sleeper's price (reports/sleeper_vs_books.md).", ""]
    b = books_rows(df, rows)
    if b.empty:
        return out + [f"{len(rows)} comparison rows logged; no settled Sleeper call has a matching discrepancy yet.", ""]
    out += ["| Discrepancy | Bets | Won | Win rate | Break-even | Net per $100 (95% CI) |", "|---|---|---|---|---|---|"]
    rng = np.random.default_rng(7)
    for kind, g in list(b.groupby("kind")) + [("both, pooled", b)]:
        graded = g[g.won.notna()]
        games = g.event_id.astype(str).to_numpy()
        ug = np.unique(games)
        boots = []
        for _ in range(500):
            take = np.concatenate([np.flatnonzero(games == x) for x in rng.choice(ug, len(ug))])
            boots.append(g.pnl.to_numpy()[take].mean())
        lo, hi = np.percentile(boots, [2.5, 97.5]) if len(ug) > 1 else (np.nan, np.nan)
        wr = graded.won.astype(bool).mean() if len(graded) else float("nan")
        out.append(f"| {kind} | {len(g)} | {int(graded.won.astype(bool).sum())} | {wr:.1%} | "
                   f"{g.breakeven.mean():.1%} | {g.pnl.mean():+.1f} ({lo:+.1f}, {hi:+.1f}) |")
    verdict = ("**edge by the pre-set rule**" if len(b) >= BOOKS_MIN and np.isfinite(lo) and lo > 0
               else f"no verdict yet: the rule needs {BOOKS_MIN}+ bets and an interval above zero")
    return out + ["", f"{len(b)} graded discrepancies: {verdict}.", ""]


def look_section(df: pd.DataFrame) -> list[str]:
    """DECISIONS #156: every 'worth a look' mark graded on the side it marked,
    at Sleeper's own price for that side. Pushes are not graded."""
    if "look" not in df.columns:
        return []
    import settle as _s
    d = df[df["look"].isin(["Over", "Under"])].copy()
    d["won"] = pd.to_numeric(d["won"], errors="coerce")
    d = d.dropna(subset=["won"])
    if d.empty:
        return ["### Worth a look", "", "No marked line has been graded yet.", ""]
    d["look_won"] = np.where(d["side"] == d["look"], d["won"], 1 - d["won"])
    d["look_price"] = np.where(d["look"] == "Over", pd.to_numeric(d.get("price_over"), errors="coerce"),
                               pd.to_numeric(d.get("price_under"), errors="coerce"))
    d = d.dropna(subset=["look_price"])
    d["pnl"] = [_s.american_pnl(p_, bool(w)) for p_, w in zip(d["look_price"], d["look_won"])]
    d["be"] = [abs(p_) / (abs(p_) + 100) if p_ < 0 else 100 / (p_ + 100) for p_ in d["look_price"]]
    out = ["### Worth a look", "",
           "Every bold line, graded on the side it marked at Sleeper's own price for that side. A mark is a "
           "role story plus last game's workload already past that side's break-even; it is not a bet label. "
           "About 100 marks are needed before the win rate says much.", "",
           "| Market | Marks | Won | Win rate | Break-even | Net per $100 |", "|---|---|---|---|---|---|"]
    for mk, g in list(d.groupby("market")) + [("all", d)]:
        out.append(f"| {mk.replace('player_', '')} | {len(g)} | {int(g.look_won.sum())} | {g.look_won.mean():.0%} | "
                   f"{g.be.mean():.0%} | {g.pnl.mean():+.1f} |")
    return out + [""]


def snap_rule_section(df: pd.DataFrame) -> list[str]:
    """DECISIONS #145: the receiving calls the snap-change rule moved (round 23)
    against the ones it did not -- the fresh check on its 2024-25 overshoot for
    receivers whose snaps jumped. `miss` is actual minus the model's mean."""
    if "snap_react" not in df.columns:
        return []
    d = df[df["market"].isin(["player_receptions", "player_reception_yds"])].copy()
    d["snap_react"] = pd.to_numeric(d["snap_react"], errors="coerce")
    d = d.dropna(subset=["snap_react"])
    if d.empty:
        return []
    d["moved"] = np.select([d.snap_react > 1.005, d.snap_react < 0.995], ["raised", "lowered"], "not moved")
    out = ["### The snap-change rule's calls", "",
           "Receiving calls whose target share the rule raised, lowered, or left alone. If the rule overshoots, "
           "the raised group's miss runs negative (and the lowered group's positive).", "",
           "| Market | Rule | Calls | Hit rate | Model said | Book said | Mean miss |", "|---|---|---|---|---|---|---|"]
    for mk, label in (("player_receptions", "catches"), ("player_reception_yds", "receiving yards")):
        for grp in ("raised", "lowered", "not moved"):
            g = d[(d.market == mk) & (d.moved == grp)]
            if g.empty:
                continue
            won = pd.to_numeric(g["won"], errors="coerce")
            miss = pd.to_numeric(g.get("miss"), errors="coerce")
            out.append(f"| {label} | {grp} | {len(g)} | {won.mean():.1%} | "
                       f"{pd.to_numeric(g.p_model, errors='coerce').mean():.1%} | "
                       f"{pd.to_numeric(g.p_novig, errors='coerce').mean():.1%} | {miss.mean():+.2f} |")
    return out + ["", "A group needs about 50 calls before its numbers say anything.", ""]


# DECISIONS #204: the reversal-check shadows once rounds 34 and 39 ship -- the board (with the
# change) against the price without it, at Sleeper's real lines; positive = the old setting better
REVERSAL_SHADOWS = (("p_over_hist_carries", ("player_rush_yds",),
                     "Round 39 reversal check: rushing yards with market carries vs without"),
                    ("p_over_spread40", ("player_receptions", "player_reception_yds"),
                     "Round 34 reversal check: receiving at target spread 60 vs 40"))


def reversal_sections(df: pd.DataFrame) -> list[str]:
    out = []
    for col, markets, title in REVERSAL_SHADOWS:
        out += shadow_section(df, col, markets, title, 2000, 204, "settled lines carry this shadow")
    return out


def shadow_section(df: pd.DataFrame, col: str, markets, title: str, reps: int = 2000, seed: int = 29,
                   few: str = "settled lines carry the shadow") -> list[str]:
    """The board's Over probability against a shadow price in column `col`, on settled lines
    of `markets` -- today the week-8 reversal shadows (DECISIONS #204; the #185 market-carries
    shadow it was written for shipped and its columns were dropped, #211). Scored like every
    comparison on the
    scoreboard (reports/scoreboard.md): log loss first, Brier beside it (both lower is
    better; chances clipped to 0.5-99.5% as the scoreboard does), each with a 95% interval
    on the difference resampling whole games. The board's number stays the price until
    this says otherwise at a pre-set review -- with both scores agreeing in sign."""
    need = {"p_over_board", col, "actual", "line"}
    if not need <= set(df.columns):
        return []
    d = df[df["market"].isin(list(markets))].copy()
    for c in ("p_over_board", col, "actual", "line"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(subset=list(need))
    d = d[d.actual != d.line]                                   # pushes grade neither way
    d = d.drop_duplicates(["event_id", "market", "player", "line"])
    if d.empty:
        return []
    head = [f"## {title}", ""]
    if len(d) < 30:
        return head + [f"{len(d)} {few} so far; the comparison starts at 30.", ""]
    over = (d.actual > d.line).astype(float).to_numpy()
    pb = np.clip(d.p_over_board.to_numpy(), 0.005, 0.995)
    ps = np.clip(d[col].to_numpy(), 0.005, 0.995)
    ll = lambda p: -(over * np.log(p) + (1 - over) * np.log(1 - p))
    games = d["event_id"].astype(str).to_numpy() if "event_id" in d.columns else np.arange(len(d)).astype(str)
    ug, inv = np.unique(games, return_inverse=True)
    idx = np.random.default_rng(seed).integers(0, len(ug), size=(reps, len(ug)))
    cnt = np.bincount(inv)

    def ci(diff):
        sums = np.bincount(inv, weights=diff)
        return np.percentile(sums[idx].sum(1) / cnt[idx].sum(1), [2.5, 97.5])

    out = [f"{len(d)} settled lines, {len(ug)} games. Board minus shadow, positive = the shadow is better:"]
    for name, fb, fs in (("Log loss", ll(pb), ll(ps)), ("Brier score", (pb - over) ** 2, (ps - over) ** 2)):
        lo, hi = ci(fb - fs)
        out.append(f"- {name}: board {fb.mean():.4f}, shadow {fs.mean():.4f}; difference "
                   f"{(fb - fs).mean():+.4f} (95% CI {lo:+.4f} to {hi:+.4f})")
    return head + out + ["", "The board's number stays the price until a pre-set review says otherwise.", ""]


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
                "capture inside 60 minutes of kickoff, and the scheduled runs fire "
                "too late to make one (speed is off by the user's choice); without "
                "it, closing-line value is unavailable and must not be estimated. "
                "The bet journal measures late-line value instead: each bet "
                "against the last line the capture logged before kickoff.", ""]
        return out
    share = clv["moved_our_way"].mean()
    out += [f"{len(clv)} calls have both snapshots. The line moved toward "
            f"the call {share:.1%} of the time (mean move "
            f"{clv['line_move'].mean():+.2f}).", "",
            "Beating the close consistently is the signal that survives "
            "small samples. Winning without it is variance.", ""]
    return out


GATE_FILE = "model_weight.json"


def write_label_gate(season: int, df: pd.DataFrame, engines) -> dict:
    """model_weight.json beside the record: per pricing model and pooled, the
    model's weight on settled yardage calls and whether the gate is open."""
    import datetime as dt
    gate = {"season": season, "updated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "rule": ("decided only at the week " + ", ".join(map(str, blend.REVIEW_WEEKS)) + " reviews, on the "
                     f"calls through that week: labels return only when the whole {100 * blend.GATE_LEVEL:.1f}% "
                     "interval of the model's weight is above zero AND the top-tier calls' net per $100 at "
                     f"Sleeper's recorded prices has its whole {100 * blend.GATE_LEVEL:.1f}% interval above zero "
                     f"({len(blend.REVIEW_WEEKS)} looks share one 5%)"),
            "engines": [], "pooled": blend.yardage_gate(df)}
    for engine_hash, group in engines:
        g = blend.yardage_gate(group)
        g.update(engine=engine_label(group), model_id=str(engine_hash))
        gate["engines"].append(g)
    # TWO ENGINES ARE NOT ONE SAMPLE: the gate opens on the CURRENT pricing
    # model's own calls (the one with the latest graded week, then the most
    # calls); the pooled fit is context only
    graded = [g for g in gate["engines"] if g["weeks"]]
    gate["current"] = (max(graded, key=lambda g: (max(g["weeks"]), g["n_calls"])) if graded else None)
    (persist.RECORD_ROOT / GATE_FILE).write_text(json.dumps(gate, indent=1, sort_keys=True) + "\n",
                                                encoding="utf-8")
    return gate


def label_gate_md(gate: dict) -> list[str]:
    """The scorecard's gate section: one row per pricing model, then pooled."""
    out = ["## Label gate", "",
           "The research board shows no bet labels. The gate is decided only at the reviews after weeks "
           + ", ".join(map(str, blend.REVIEW_WEEKS)) + ", on the calls through that week, and opens only when "
           f"both hold: the model's number earns weight beside the book's price (the whole "
           f"{100 * blend.GATE_LEVEL:.1f}% interval above zero), and the top-tier calls made money at Sleeper's "
           f"recorded prices (the whole {100 * blend.GATE_LEVEL:.1f}% interval of net per $100 above zero). "
           f"Each review uses {100 * blend.GATE_LEVEL:.1f}% rather than 95% because the gate looks "
           f"{len(blend.REVIEW_WEEKS)} times: the looks share one 5% chance of opening on luck. Between reviews "
           "it holds; the running weight (95%) is context only.", "",
           "| Pricing model | Calls | Weeks | Running weight (95% CI) | Last review | "
           f"Weight at review ({100 * blend.GATE_LEVEL:.1f}% CI) | "
           f"Top-tier net per $100 at review ({100 * blend.GATE_LEVEL:.1f}% CI) | Gate |",
           "|---|---|---|---|---|---|---|---|"]
    rows = ([(g["engine"] + (" (current)" if g is gate.get("current") else ""), g) for g in gate["engines"]]
            + [("all models, pooled (context only)", gate["pooled"])])
    for name, g in rows:
        wk = f"{min(g['weeks'])}-{max(g['weeks'])}" if g.get("weeks") else "—"
        w_cell = lambda w: (f"{w['w_model']:+.3f} ({w['lo']:+.3f}, {w['hi']:+.3f})" if w.get("estimated")
                            else f"not estimated below {blend.MIN_CALLS} calls")
        ar = g.get("at_review")
        if ar:
            pr = ar["profit"]
            rev = f"week {ar['week']} ({ar['n_calls']} calls)"
            wrev = w_cell(ar["weight"])
            prof = (f"{pr['net_per_100']:+.1f} ({pr['lo']:+.1f}, {pr['hi']:+.1f}), {pr['n_bets']} bets"
                    if pr.get("estimated") else f"{pr['n_bets']} bets, not estimated below {blend.MIN_BETS}")
        else:
            rev = f"none yet (first after week {g.get('next_review') or blend.REVIEW_WEEKS[0]})"
            wrev = prof = "—"
        state = "**OPEN**" if g.get("gate_open") else "closed"
        out.append(f"| {name} | {g['n_calls']} | {wk} | {w_cell(g)} | {rev} | {wrev} | {prof} | {state} |")
    return out + [""]


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
        write_label_gate(args.season, settled, [])
        out += ["No settled calls yet. Run `props/settle.py` after results "
                "publish (nflverse weekly stats land Tuesday morning ET).", ""]
        (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out + journal.summary_md(args.season)),
                                                          encoding="utf-8")
        print("no settled rows yet")
        return 0

    graded = len(settled)
    df = settled[settled["is_call"] == 1]
    if df.empty:
        write_label_gate(args.season, df, [])
        out += [f"{graded} rows graded, none of them a call. A call is the "
                f"last decision for a market; if every row is a superseded "
                f"line, re-run props/settle.py.", ""]
        (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out + journal.summary_md(args.season)),
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

    # THE LABEL GATE (DECISIONS #144): the model's weight beside the book on the
    # settled yardage calls, per pricing model and pooled, written where the
    # engine reads it (the report's first line quotes it).
    gate = write_label_gate(args.season, df, engines)
    out += label_gate_md(gate)
    out += books_section(df, args.season)

    csv_rows: list[dict] = []
    for engine_hash, group in engines:
        out += [f"## Engine {engine_label(group)}", ""]
        sections, rows = render_sections(group)
        out += sections
        csv_rows += rows
        out += render_clv(clv, engine_hash)
        out += snap_rule_section(group)
        out += reversal_sections(group)
        out += look_section(group)
        out += blend.blend_section(group)

    if args.pool and len(engines) > 1:
        out += ["## All engines (pooled by request)", "",
                "These calls come from different model versions; the pooled "
                "numbers describe no single one of them.", ""]
        sections, _rows = render_sections(df)
        out += sections
        out += render_clv(clv)

    (persist.RECORD_ROOT / "scorecard.md").write_text("\n".join(out + journal.summary_md(args.season)), encoding="utf-8")
    if csv_rows:
        pd.DataFrame(csv_rows).to_csv(persist.RECORD_ROOT / "scorecard.csv", index=False)
    print(f"[{persist.mode()}] wrote {persist.RECORD_ROOT / 'scorecard.md'} "
          f"({len(df)} calls of {graded} graded rows, "
          f"{len(engines)} engine version(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

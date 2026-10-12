# expires: 2026-11-10
"""Which order should the screen use? A pre-registered measurement (DECISIONS #244, the user's terms,
2026-10-11). Run once; the decision rule below was written before any of it ran.

Legs: every 2026 game with a Sleeper quote saved at least 60 minutes before kickoff (the latest such
quote, one per leg: both line files are copied with only those rows, so the calculator's own lookup
picks it). Week 1 has no saved quotes. Each line is built as the screen builds it (one data load,
every input cut at the week); a side is "at the bar" when the screen would list it (recent workload
meets the bar, the player not ruled Out). Results come from the journal's own grader (same stats,
name join and push rule) in a throwaway journal; a void, a push or a player not in the week's stats
(did not play) is dropped, not counted.

Orders compared on the same legs, top 3 per side per game:
  A cushion as a percent of the bar, biggest first (live since #243);
  B fewest ✗, then most ✓, then cushion (the order before #243);
  C cushion in his own game-to-game spread: workload cushion / standard deviation of his workload in
    the games the longer-run rate uses (16 when he has them), biggest first;
  D consistency first: share of his season games at or past the bar, then cushion.
  Baseline: every leg at the bar, unordered.
Edge = hit rate minus the average break-even of the same legs (break-even = 1 / Sleeper multiplier).
Ranges: 95% percentile intervals from 2000 bootstrap resamples of GAMES (legs of one game move
together), seed fixed.

Decision rule (pre-registered): cushion (A) stays unless another order's edge on the total (all weeks,
Overs and Unders pooled) beats A's by at least 5 percentage points AND the bootstrap interval of that
paired difference is entirely above zero; if more than one does, the largest. The result may change
the sort order only -- no setting, weight or combined score. If none clears the margin, A stays and
the test reruns only when at least three more weeks of legs exist. Slices reported: weeks 1-2 (week
2 only: no week-1 quotes), weeks 3-5, total; Overs and Unders separately. No other slices.
Headline: did A's top 3 per side beat their average break-even? "yes" only when the whole interval is
above zero, "no" when it is entirely below, otherwise "not shown", with the range."""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import tempfile
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from props.calc import __main__ as M  # noqa: E402
from props.calc import card, lines, odds, player, screen as S, settings  # noqa: E402
from props.calc.checks import DataError  # noqa: E402
from props.calc.markets import workload_col  # noqa: E402
from props.calc.shared import journal  # noqa: E402

SEASON = 2026
WEEKS = (1, 2, 3, 4, 5)
CUTOFF = pd.Timedelta(minutes=60)
TOP = 3
MARGIN = 0.05
BOOT, SEED = 2000, 20261011
PERIODS = (("weeks 1-2", {1, 2}), ("weeks 3-5", {3, 4, 5}), ("total", set(WEEKS)))
ORDERS = ("A cushion %", "B fewest x, most check, cushion", "C cushion in his spread", "D consistency first")


def filtered_lines(tmp: Path) -> tuple[Path, Path, dict]:
    """Copies of both line files holding only quotes saved at least 60 minutes before their kickoff."""
    out, kept = {}, {}
    for name, src, dst_root in (("engine", lines.archive_path(SEASON), tmp / "engine"),
                                ("calc", lines.calc_path(SEASON), tmp / "calc")):
        dst = (lines.archive_path(SEASON, dst_root) if name == "engine" else lines.calc_path(SEASON, dst_root))
        dst.parent.mkdir(parents=True, exist_ok=True)
        n_in = n_out = 0
        with open(dst, "w", encoding="utf-8", newline="\n") as fh:
            for r in (lines._rows(src) if src.exists() else ()):
                n_in += 1
                try:
                    ok = pd.Timestamp(r["retrieved_at_utc"]) <= pd.Timestamp(r["commence_time"]) - CUTOFF
                except (KeyError, ValueError, TypeError):
                    ok = False                   # an unreadable time cannot show it was saved early enough
                if ok:
                    fh.write(json.dumps(dict(r), sort_keys=True) + "\n")
                    n_out += 1
        out[name], kept[name] = dst_root, (n_in, n_out)
    return out["engine"], out["calc"], kept


def legs(b, eng: Path, calc: Path, log) -> tuple[list[dict], dict]:
    """Every side the screen would list, with the keys each order sorts on."""
    lookup = lines.LineLookup(b.rosters, archive_root=eng, calc_root=calc)
    inj = M._injuries(b, SEASON)
    sched = b.schedule[(b.schedule["season"] == SEASON) & (b.schedule["week"].isin(WEEKS))]
    rows, counts = [], {"lines": 0, "built": 0, "not built": 0, "not enough data": 0, "no usable quote": 0,
                        "ruled Out": 0}
    for _, g in sched.sort_values("kickoff_utc").iterrows():
        wk = int(g["week"])
        posted, unread, bad = lookup.posted({"season": SEASON, "week": wk, "kickoff_utc": g["kickoff_utc"],
                                             "game_id": g["game_id"], "home_team": g["home_team"],
                                             "away_team": g["away_team"]})
        for p in posted:
            counts["lines"] += 1
            try:
                got = M.build_card(b, p["player"], p["market"], "over", team=p["team"], season=SEASON, week=wk,
                                   lookup=lookup)
            except (player.NotFound, DataError, SystemExit):
                counts["not built"] += 1
                continue
            if got["stub"]["game_id"] != g["game_id"]:
                counts["not built"] += 1
                continue
            if got["not_enough"]:
                counts["not enough data"] += 1
                continue
            if not got["ready"]:
                counts["no usable quote"] += 1
                continue
            me = inj[(inj["week"] == wk) & (inj["gsis_id"] == got["stub"]["gsis_id"])]
            if len(me) and str(me["report_status"].iloc[-1]) == "Out":
                counts["ruled Out"] += 1
                continue
            counts["built"] += 1
            c, pl = got["c"], got["pl"]
            bars = {sd: card.value(c, f"needed_{sd}") for sd in ("over", "under")}
            spread = pl.window[workload_col(c["market"])].std(ddof=1) if len(pl.window) >= 2 else float("nan")
            for sd in ("over", "under"):
                r = S.side_row(pl, c, sd, got["shown"], got["stub"], bars["under" if sd == "over" else "over"])
                if not r["passes"]:
                    continue
                P = card._parts(pl, c, sd)
                units = -P["work_ask"] if sd == "over" else P["work_ask"]          # his cushion in workload units
                n_season = P["season"]
                share = n_season[1] / n_season[2] if n_season and n_season[2] else -1.0
                rows.append({"game_id": g["game_id"], "week": wk, "side": sd, "player": r["player"], "team": r["team"],
                             "market": r["market"], "line": r["line"], "mult": r["mult"], "cushion": r["cushion"],
                             "x": r["x"], "ok": r["ok"], "share": share,
                             "z": (math.inf if units > 0 else -math.inf) if not spread else units / spread,
                             "be": odds.break_even(r["mult"])})
        log(f"week {wk} {g['away_team']}@{g['home_team']}: {len(posted)} lines, {len(rows)} sides at the bar so far")
    return rows, counts


SORTS = {
    "A cushion %": lambda r: (-r["cushion"], r["x"], -r["ok"]),
    "B fewest x, most check, cushion": lambda r: (r["x"], -r["ok"], -r["cushion"]),
    "C cushion in his spread": lambda r: (-r["z"] if not math.isnan(r["z"]) else math.inf, -r["cushion"]),
    "D consistency first": lambda r: (-r["share"], -r["cushion"]),
}


def grade(rows: list[dict]) -> None:
    """won / dropped on each row, from journal.grade in a throwaway journal (never the betting record)."""
    jr = [{"id": f"m{i}", "season": SEASON, "week": r["week"], "player": r["player"], "team": r["team"],
           "market": S.JOURNAL_MARKET[r["market"]], "side": r["side"], "line": float(r["line"]),
           "price": int(odds.american_from_multiplier(r["mult"])), "stake": 1.0, "status": "open",
           "volume_unit": workload_col(r["market"])} for i, r in enumerate(rows)]
    keep = journal.JOURNAL_ROOT
    with tempfile.TemporaryDirectory() as tmp:
        try:
            journal.JOURNAL_ROOT = Path(tmp)
            journal.write(SEASON, jr)
            journal.grade(SEASON)
            graded = {x["id"]: x for x in journal.read(SEASON)}
        finally:
            journal.JOURNAL_ROOT = keep
    for i, r in enumerate(rows):
        g = graded[f"m{i}"]
        r["won"] = g.get("won") if g.get("status") == "graded" else None     # void, push, check, open: dropped
        r["status"] = g.get("status")


def selections(rows: list[dict]) -> dict:
    """{order: [row indices]} -- the top 3 per side per game for each order, chosen before results; the
    baseline is every leg at the bar."""
    by = {}
    for i, r in enumerate(rows):
        by.setdefault((r["game_id"], r["side"]), []).append(i)
    out = {"baseline (all at the bar)": [i for i in range(len(rows))]}
    for name, key in SORTS.items():
        out[name] = [i for idx in by.values() for i in sorted(idx, key=lambda j: key(rows[j]))[:TOP]]
    return out


def edge(rows, idx) -> tuple:
    g = [rows[i] for i in idx if rows[i]["won"] is not None]
    if not g:
        return float("nan"), float("nan"), float("nan"), 0
    hit = sum(bool(r["won"]) for r in g) / len(g)
    be = sum(r["be"] for r in g) / len(g)
    return hit - be, hit, be, len(g)


def boot(rows, sel: dict, keep, rng) -> dict:
    """Game-clustered bootstrap: {order: (lo, hi) of the edge, (lo, hi) of edge minus A's}."""
    games = sorted({rows[i]["game_id"] for i in range(len(rows)) if keep(rows[i])})
    pos = {g: [] for g in games}
    for name, idx in sel.items():
        for i in idx:
            if keep(rows[i]) and rows[i]["won"] is not None:
                pos[rows[i]["game_id"]].append((name, i))
    draws = {name: [] for name in sel}
    diffs = {name: [] for name in sel}
    for _ in range(BOOT):
        pick = [rng.choice(games) for _ in games] if games else []
        tot = {name: [0, 0.0, 0] for name in sel}             # wins, break-even sum, n
        for gm in pick:
            for name, i in pos[gm]:
                t = tot[name]
                t[0] += bool(rows[i]["won"])
                t[1] += rows[i]["be"]
                t[2] += 1
        e = {name: (t[0] - t[1]) / t[2] if t[2] else float("nan") for name, t in tot.items()}
        for name in sel:
            draws[name].append(e[name])
            diffs[name].append(e[name] - e["A cushion %"])
    q = lambda xs: (pd.Series(xs).quantile(0.025), pd.Series(xs).quantile(0.975))      # noqa: E731
    return {name: (q(draws[name]), q(diffs[name])) for name in sel}


def pct(x) -> str:
    return "--" if x != x else f"{x * 100:+.1f}"


def report(rows, sel, counts, kept) -> list[str]:
    rng = random.Random(SEED)
    L = ["# Screen order measurement (DECISIONS #244)", ""]
    tot_keep = lambda r: True                             # noqa: E731
    e_a, _, _, n_a = edge(rows, sel["A cushion %"])
    (lo, hi), _ = boot(rows, sel, tot_keep, rng)["A cushion %"]
    verdict = "yes" if lo > 0 else ("no" if hi < 0 else "not shown")
    L += [f"**Did the top 3 per side (cushion order) beat their average break-even? {verdict}: "
          f"{pct(e_a)} points (range {pct(lo)} to {pct(hi)}), {n_a} graded legs, weeks 2-5.**", ""]
    L += [f"Quotes kept (saved at least 60 minutes before kickoff): engine {kept['engine'][1]} of {kept['engine'][0]} rows, "
          f"calc {kept['calc'][1]} of {kept['calc'][0]}. Lines: {counts}.", ""]
    dropped = sum(r["won"] is None for r in rows)
    L += [f"Sides at the bar: {len(rows)}; dropped from grading (void, push, did not play, not joined): {dropped}. "
          "Each order's top 3 was chosen before any result; a chosen leg that is dropped is not replaced.", ""]
    for period, weeks in PERIODS:
        for side in ("over", "under"):
            keep = lambda r, w=weeks, s=side: r["week"] in w and r["side"] == s       # noqa: E731
            sub_sel = {k: [i for i in v if keep(rows[i])] for k, v in sel.items()}
            ci = boot(rows, sub_sel, keep, random.Random(SEED))
            L += [f"## {period} · {side.title()}s", "",
                  "| Order | Graded legs | Hit rate | Avg break-even | Edge (pts) | Range | Minus A (pts) | Range |",
                  "|---|---|---|---|---|---|---|---|"]
            for name in sel:
                e, hit, be, n = edge(rows, sub_sel[name])
                (lo, hi), (dlo, dhi) = ci[name]
                da = e - edge(rows, sub_sel["A cushion %"])[0]
                L.append(f"| {name} | {n} | {pct(hit)[1:] if hit == hit else '--'}% | "
                         f"{be * 100:.1f}% | {pct(e)} | {pct(lo)} to {pct(hi)} | "
                         + ("--" if name == "A cushion %" else f"{pct(da)} | {pct(dlo)} to {pct(dhi)}") + " |"
                         if n else f"| {name} | 0 | -- | -- | -- | -- | -- | -- |")
            L.append("")
    # the decision, on the total with both sides pooled
    ci = boot(rows, sel, tot_keep, random.Random(SEED))
    winners = []
    for name in ORDERS[1:]:
        d = edge(rows, sel[name])[0] - e_a
        if d >= MARGIN and ci[name][1][0] > 0:
            winners.append((d, name))
    L += ["## Decision (pre-registered rule, total, Overs and Unders pooled)", ""]
    if winners:
        d, name = max(winners)
        L.append(f"{name} beats cushion by {pct(d)} points with its whole range above zero: the screen's sort "
                 "order changes to it (sort order only).")
    else:
        L.append("No order beats cushion by 5 points with its range above zero: cushion stays, and the test reruns "
                 "only when at least three more weeks of legs exist.")
    return L


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "experiments" / "out" / "screen_order_2026.md")
    a = ap.parse_args(argv)
    fixed = settings.load()["fixed"]
    b, warn = M._bundle(SEASON, fixed)
    if warn:
        print(warn)
    with tempfile.TemporaryDirectory() as tmp:
        eng, calc, kept = filtered_lines(Path(tmp))
        rows, counts = legs(b, eng, calc, print)
    grade(rows)
    sel = selections(rows)
    text = "\n".join(report(rows, sel, counts, kept)) + "\n"
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8")
    safe = [{k: (str(v) if isinstance(v, float) and math.isinf(v) else v) for k, v in r.items()} for r in rows]
    (a.out.with_suffix(".json")).write_text(json.dumps(safe, default=str), encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

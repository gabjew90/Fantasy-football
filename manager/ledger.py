"""The ledger: every recommendation written down, then graded against actuals.

Season-manager v2, layer 4. Every brief is a prediction -- start these nine,
this add is worth +26 over the next-best free agent, this trade is +1.3 a
week, we win this matchup 41% of the time -- and until 2026-09-16 none of
it was recorded, so nothing could ever say whether the trade model, the
waiver ranks or the consensus blend were right. A season of ungraded
predictions is a season of opinions.

Emission is one call per brief and costs nothing the brief did not already
compute. Rows are JSON lines under `state/<league>/ledger/<season>-wkNN.jsonl`
(the default league at `state/ledger/`), committed with the rest of the
state, each carrying the provenance stamp so a bad row can be attributed to
its inputs or its logic. A dry run emits nothing.

Grading runs after the week's games (the Tuesday ledger job): actuals are
Sleeper's weekly stat lines scored in the league's own settings, and each
kind has one honest ruler:

  lineup      points the recommended starters actually scored, over the best
              lineup the roster could have fielded in hindsight (efficiency),
              plus the bench points left behind
  scout       actual margin against the predicted one; the Brier score of the
              win probability against the result
  waiver_add  the recommended add's points that week beside the suggested
              drop's -- and, over the following weeks, ROS as it accrues
  trade_offer the pieces' realised points each week (given vs received), a
              running series the slot model is judged on at season's end

The rulers are deliberately simple and pre-registered here; the season
scoreboard (`report()`) is the only place they are summed.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("manager")

KINDS = ("lineup", "scout", "waiver_add", "trade_offer")


def ledger_dir(store) -> Path:
    return Path(store.dir) / "ledger"


def week_file(store, season, week: int) -> Path:
    return ledger_dir(store) / f"{season}-wk{int(week):02d}.jsonl"


def _rid(kind: str, week: int, subject: str, ts: float) -> str:
    return hashlib.sha256(f"{kind}|{week}|{subject}|{ts:.0f}".encode()).hexdigest()[:12]


def emit(store, ctx, kind: str, rows: list[dict], sources: dict | None = None) -> int:
    """Append `rows` for `kind` this week. Returns the number written (0 on a
    dry run, which must leave state untouched)."""
    if kind not in KINDS:
        raise ValueError(f"ledger kind {kind!r} is not one of {KINDS}")
    # The structured result also feeds the delivered (phone) rendering, dry
    # run or not: manager.phone reads ctx["_summary"][kind].
    ctx.setdefault("_summary", {})[kind] = list(rows)
    if not rows:
        return 0
    if getattr(store, "read_only", False):
        log.info("dry run: not writing %d ledger row(s) of kind %s", len(rows), kind)
        return 0
    from . import provenance
    season = (ctx.get("state") or {}).get("season") or "?"
    week = int(ctx.get("week") or 0)
    stamp = provenance.stamp(ctx, sources)
    path = week_file(store, season, week)
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = time.time()
    with path.open("a", encoding="utf-8") as f:
        for r in rows:
            subject = str(r.get("subject") or r.get("pid") or r.get("name") or kind)
            f.write(json.dumps({"id": _rid(kind, week, subject, ts), "ts": ts,
                                "at": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                                "week": week, "kind": kind, "subject": subject,
                                **r, "provenance": stamp}, sort_keys=True) + "\n")
    log.info("ledger: %d %s row(s) -> %s", len(rows), kind, path)
    return len(rows)


def read_week(store, season, week: int) -> list[dict]:
    path = week_file(store, season, week)
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except ValueError:
            log.warning("ledger: unreadable row skipped in %s", path)
    return out


def latest_per_subject(rows: list[dict], kind: str) -> dict[str, dict]:
    """The last row emitted for each subject of `kind` -- the recommendation
    that stood when the week locked."""
    out: dict[str, dict] = {}
    for r in sorted((r for r in rows if r.get("kind") == kind), key=lambda r: r.get("ts", 0)):
        out[str(r.get("subject"))] = r
    return out


# ------------------------------------------------------------------ actuals

def actual_points(ctx, week: int, getter=None) -> dict[str, float]:
    """sleeper_id -> points scored in `week`, in this league's scoring."""
    from draftkit import seasondata
    season = (ctx.get("state") or {}).get("season")
    scoring = (ctx.get("league") or {}).get("scoring_settings") or {}
    raw = seasondata.weekly_stats(season, week, getter) if getter else seasondata.weekly_stats(season, week)
    return {str(pid): round(seasondata.score_projection(stats, scoring), 2)
            for pid, stats in (raw or {}).items() if isinstance(stats, dict)}


# ------------------------------------------------------------------ grading

def grade_lineup(row: dict, actual: dict[str, float], shape: dict) -> dict:
    from draftkit.lineup import optimal_lineup
    starters = [str(x) for x in row.get("starters") or []]
    pool = [str(x) for x in row.get("pool") or starters]
    pos_of = row.get("pos") or {}
    chosen = sum(actual.get(p, 0.0) for p in starters)
    rows = [{"sleeper_id": p, "pos": pos_of.get(p), "weekly": actual.get(p, 0.0)} for p in pool]
    best = optimal_lineup(rows, shape["slots"], shape.get("flex", 0), flex_slots=shape.get("flex_slots"))
    best_pts = sum(p["weekly"] for p in best)
    return {"chosen_pts": round(chosen, 2), "best_pts": round(best_pts, 2),
            "efficiency": round(chosen / best_pts, 3) if best_pts else None,
            "left_on_bench": round(best_pts - chosen, 2),
            "projected_pts": round(sum((row.get("projected") or {}).values()), 2)}


def grade_scout(row: dict, my_actual: float | None, their_actual: float | None) -> dict:
    if my_actual is None or their_actual is None:
        return {"graded": False}
    margin = my_actual - their_actual
    won = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
    wp = float(row.get("win_prob") or 0.5)
    return {"graded": True, "actual_margin": round(margin, 2),
            "margin_error": round(margin - float(row.get("margin") or 0.0), 2),
            "won": won, "brier": round((wp - won) ** 2, 4)}


def grade_waiver(row: dict, actual: dict[str, float]) -> dict:
    add = actual.get(str(row.get("pid")))
    drop = actual.get(str(row.get("drop_pid"))) if row.get("drop_pid") else None
    return {"add_pts": add, "drop_pts": drop,
            "delta": round(add - drop, 2) if add is not None and drop is not None else None}


def grade_trade(row: dict, actual: dict[str, float]) -> dict:
    gave = sum(actual.get(str(p), 0.0) for p in row.get("give") or [])
    got = sum(actual.get(str(p), 0.0) for p in row.get("get") or [])
    return {"gave_pts": round(gave, 2), "got_pts": round(got, 2), "realised": round(got - gave, 2)}


def grade_week(ctx, store, week: int, actual: dict[str, float] | None = None,
               my_actual: float | None = None, their_actual: float | None = None) -> dict:
    """Grade every row emitted for `week`; write grades-<season>-wkNN.json."""
    season = (ctx.get("state") or {}).get("season") or "?"
    rows = read_week(store, season, week)
    if not rows:
        return {"week": week, "graded": 0, "note": "no ledger rows"}
    if actual is None:
        actual = actual_points(ctx, week)
    shape = {"slots": ctx["slots"], "flex": ctx.get("flex", 0), "flex_slots": ctx.get("flex_slots")}
    out: dict = {"week": week, "season": season, "graded_at":
                 datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "lineup": None, "scout": None, "waiver_add": [], "trade_offer": []}
    lu = latest_per_subject(rows, "lineup")
    if lu:
        out["lineup"] = grade_lineup(list(lu.values())[-1], actual, shape)
    sc = latest_per_subject(rows, "scout")
    if sc:
        out["scout"] = grade_scout(list(sc.values())[-1], my_actual, their_actual)
    for r in latest_per_subject(rows, "waiver_add").values():
        out["waiver_add"].append({"name": r.get("name"), "cls": r.get("cls"), "rank": r.get("rank"),
                                  **grade_waiver(r, actual)})
    for r in latest_per_subject(rows, "trade_offer").values():
        out["trade_offer"].append({"subject": r.get("subject"), "my_ppg": r.get("my_ppg"),
                                   "send": r.get("send"), **grade_trade(r, actual)})
    n = sum(1 for k in ("lineup", "scout") if out[k]) + len(out["waiver_add"]) + len(out["trade_offer"])
    out["graded"] = n
    if not getattr(store, "read_only", False):
        p = ledger_dir(store) / f"grades-{season}-wk{int(week):02d}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=1, sort_keys=True), encoding="utf-8")
    return out


def matchup_actuals(ctx, week: int) -> tuple[float | None, float | None]:
    """(my points, opponent points) for a completed week, from the platform's
    matchup feed when it carries points."""
    try:
        source = ctx.get("source")
        rows = source.matchups(week) if source is not None else []
    except Exception:  # noqa: BLE001
        return None, None
    by_rid = {int(r["roster_id"]): r for r in rows if r.get("roster_id") is not None}
    me = by_rid.get(int(ctx["my_rid"]))
    if not me:
        return None, None
    opp = next((r for r in rows if r.get("matchup_id") == me.get("matchup_id")
                and int(r["roster_id"]) != int(ctx["my_rid"])), None)
    mine = float(me.get("points") or 0.0)
    theirs = float(opp.get("points") or 0.0) if opp else None
    if mine == 0.0 and (theirs or 0.0) == 0.0:
        return None, None                      # not played yet
    return mine, theirs


# ------------------------------------------------------------------- report

def season_grades(store) -> list[dict]:
    d = ledger_dir(store)
    if not d.exists():
        return []
    out = []
    for p in sorted(d.glob("grades-*.json")):
        try:
            out.append(json.loads(p.read_text(encoding="utf-8")))
        except ValueError:
            continue
    return out


def report(store, league: str) -> str:
    grades = season_grades(store)
    lines = [f"# Ledger — {league}", ""]
    if not grades:
        return "\n".join(lines + ["no graded weeks yet"])
    lu = [g["lineup"] for g in grades if g.get("lineup") and g["lineup"].get("efficiency") is not None]
    if lu:
        eff = sum(x["efficiency"] for x in lu) / len(lu)
        left = sum(x["left_on_bench"] for x in lu)
        lines += [f"**Lineup**: {len(lu)} week(s), mean efficiency {eff:.1%}, "
                  f"{left:.1f} points left on the bench in total"]
    sc = [g["scout"] for g in grades if g.get("scout") and g["scout"].get("graded")]
    if sc:
        brier = sum(x["brier"] for x in sc) / len(sc)
        mae = sum(abs(x["margin_error"]) for x in sc) / len(sc)
        wins = sum(x["won"] for x in sc)
        lines += [f"**Scout**: {len(sc)} week(s), record {wins:.0f}-{len(sc) - wins:.0f}, "
                  f"Brier {brier:.3f} (0.25 is a coin flip), margin MAE {mae:.1f}"]
    wa = [w for g in grades for w in g.get("waiver_add") or [] if w.get("delta") is not None]
    if wa:
        pos = sum(1 for w in wa if w["delta"] > 0)
        lines += [f"**Waiver adds**: {len(wa)} graded, {pos} outscored the suggested drop that week "
                  f"(mean {sum(w['delta'] for w in wa) / len(wa):+.1f})"]
    tr = [t for g in grades for t in g.get("trade_offer") or []]
    if tr:
        sent = [t for t in tr if t.get("send")]
        lines += [f"**Trade offers**: {len(tr)} priced, {len(sent)} cleared the gates; "
                  f"realised so far {sum(t['realised'] for t in tr):+.1f} over the pieces"]
    lines += ["", "| week | lineup eff | bench left | scout margin err | brier | adds graded |", "|---|---|---|---|---|---|"]
    for g in grades:
        l, s = g.get("lineup") or {}, g.get("scout") or {}
        lines.append(f"| {g['week']} | {l.get('efficiency', '-') if l else '-'} | {l.get('left_on_bench', '-') if l else '-'} "
                     f"| {s.get('margin_error', '-') if s.get('graded') else '-'} | {s.get('brier', '-') if s.get('graded') else '-'} "
                     f"| {len(g.get('waiver_add') or [])} |")
    return "\n".join(lines)

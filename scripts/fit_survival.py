"""Survival calibration: what the engine predicted vs what the room did.

Plan 2026-09-02 step B1 (data layer) and B7 (the refit). This module reads
every archived room and turns it into prediction rows:

    (room, room_type, current_pick, window_start, my_next, player, pos,
     pred_raw, source, survived)

Rooms:
  * Sleeper draft logs  data/logs/draft_<id>.jsonl  (real Omnibeta draft and
    three Sleeper mocks) -- recs events; the structured `survival` field
    when present (B1 onwards), else the prose why string in either of its
    two historical phrasings, un-shrunk by the event's logged shrink.
  * Yahoo rooms  data/logs/mocks/mock_<room>.json (the trail: every pick,
    managers, our pick records) plus data/logs/yahoo_<room>.jsonl (the
    bridge's per-state recs events, B1 onwards). Older trails carry only
    prose in our records' why strings, captured AFTER the 0.55 shrink landed,
    so those are un-shrunk by 0.55 -- an assumption, stated in the report.

The horizon is ALWAYS recomputed from (current_pick, my_slot, teams, rounds)
with draftlog.sim_window: older logs recorded my_next_pick as the on-clock
pick itself when I was on the clock, which graded every on-clock prediction
as "survived" (the n=67 the shrink was fitted on).

    venv\\Scripts\\python.exe scripts\\fit_survival.py --report-only
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit import snake  # noqa: E402
from draftkit.draftlog import sim_window  # noqa: E402

SUFFIXES = re.compile(r"\s+(jr\.?|sr\.?|i{2,4}|iv|v)$", re.IGNORECASE)
SURV_PATTERNS = (re.compile(r"(\d+)% chance he'?s still there"),
                 re.compile(r"survives (\d+)%"))
BUCKETS = ((0, 30, "0-29"), (30, 50, "30-49"), (50, 70, "50-69"), (70, 90, "70-89"), (90, 101, "90-100"))
LEGACY_BUCKETS = ((50, 70, "50-69"), (70, 90, "70-89"), (90, 101, "90-100"))
TRAIL_SHRINK = 0.55            # the shrink in force when the trails were captured (2026-09-01/02)
ROOM_TYPES = {"1395566812157984768": "sleeper_human"}   # the real Omnibeta draft; other Sleeper logs are bot mocks


# ---------------------------------------------------------------- pure parts

def norm(name: str) -> str:
    n = SUFFIXES.sub("", str(name or "").strip().lower())
    return re.sub(r"[^a-z0-9]", "", n)


def unshrink(p_cal: float, shrink) -> float:
    """Invert calibrate(): a logged (shown) probability back to the raw one."""
    if shrink is None or float(shrink) >= 1.0:
        return float(p_cal)
    return min(1.0, max(0.0, 0.5 + (float(p_cal) - 0.5) / float(shrink)))


def pred_from_rec(rec: dict, shrink) -> tuple[float, str] | None:
    """(raw survival, source) for one logged recommendation: the structured
    raw field first, then the shown field, then either prose phrasing."""
    v = rec.get("survival")
    if isinstance(v, (int, float)):
        return float(v), "structured"
    v = rec.get("survival_shown")
    if isinstance(v, (int, float)):
        return unshrink(v, shrink), "structured_shown"
    why = str(rec.get("why") or "")
    for pat in SURV_PATTERNS:
        m = pat.search(why)
        if m:
            return unshrink(int(m.group(1)) / 100.0, shrink), "prose"
    return None


def prediction_rows(picks: list[dict], recs: list[dict], teams: int, rounds: int, my_slot: int,
                    room: str = "", room_type: str = "", default_shrink=None) -> list[dict]:
    """Every (player, my_next) prediction with its outcome. Later events
    overwrite earlier ones for the same key (the last view before the
    horizon). Rows the room cannot grade are dropped: a player already gone
    before the window opened (stale), and my own take at that state."""
    picked_at = {norm(p["player"]): int(p["pick_no"]) for p in picks}
    mine = {norm(p["player"]) for p in picks
            if p.get("my_pick") or (my_slot and int(p.get("slot") or 0) == my_slot)}
    out: dict[tuple[str, int], dict] = {}
    for e in recs:
        cp = e.get("current_pick")
        if not isinstance(cp, int):
            continue
        start, nxt = sim_window(cp, my_slot, teams, rounds)
        if start is None or nxt is None or nxt <= start:
            continue
        shrink = e.get("survival_shrink", default_shrink)
        for r in e.get("recommendations") or []:
            got = pred_from_rec(r, shrink)
            if got is None:
                continue
            pred, source = got
            key = norm(r.get("player"))
            at = picked_at.get(key)
            if at is not None and at < start:
                continue                                  # gone before the window: stale prediction
            if at is not None and at < nxt and key in mine:
                continue                                  # I took him myself inside the window: unobservable
            out[(key, nxt)] = {
                "room": room, "room_type": room_type, "current_pick": cp, "window_start": start,
                "my_next": nxt, "player": key, "pos": r.get("pos"), "pred": float(pred),
                "source": source, "survived": at is None or at >= nxt,
            }
    return list(out.values())


def legacy_rows(picks: list[dict], recs: list[dict], teams: int, rounds: int, my_slot: int) -> list[dict]:
    """The pre-B1 scoring, for the delta: my_next = next_pick_for_slot(cp),
    which is cp itself when I am on the clock."""
    picked_at = {norm(p["player"]): int(p["pick_no"]) for p in picks}
    out: dict[tuple[str, int], dict] = {}
    for e in recs:
        cp = e.get("current_pick")
        if not isinstance(cp, int):
            continue
        nxt = snake.next_pick_for_slot(cp, my_slot, teams, rounds)
        if nxt is None:
            continue
        shrink = e.get("survival_shrink")
        for r in e.get("recommendations") or []:
            got = pred_from_rec(r, shrink)
            if got is None:
                continue
            key = norm(r.get("player"))
            at = picked_at.get(key)
            out[(key, nxt)] = {"pred": got[0], "survived": at is None or at >= nxt}
    return list(out.values())


def bucketize(rows: list[dict], buckets=BUCKETS) -> list[dict]:
    out = []
    for lo, hi, label in buckets:
        sel = [r for r in rows if lo <= round(r["pred"] * 100) < hi]
        if not sel:
            out.append({"bucket": label, "n": 0, "pred": None, "obs": None, "logloss": None})
            continue
        pred = sum(r["pred"] for r in sel) / len(sel)
        obs = sum(1 for r in sel if r["survived"]) / len(sel)
        eps = 1e-6
        ll = -sum((1 if r["survived"] else 0) * _log(max(eps, r["pred"]))
                  + (0 if r["survived"] else 1) * _log(max(eps, 1 - r["pred"])) for r in sel) / len(sel)
        out.append({"bucket": label, "n": len(sel), "pred": pred, "obs": obs, "logloss": ll})
    return out


def _log(x: float) -> float:
    import math
    return math.log(x)


# ------------------------------------------------------------- room loaders

def load_sleeper_log(path: Path) -> dict:
    events = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    picks = [e for e in events if e.get("type") == "pick"]
    recs = [e for e in events if e.get("type") == "recs" and isinstance(e.get("current_pick"), int)]
    teams = max((int(p.get("slot") or 0) for p in picks), default=0)
    rounds = max((int(p.get("round") or 0) for p in picks), default=0)
    my = sorted({int(p["slot"]) for p in picks if p.get("my_pick")})
    my_slot = my[0] if my else None
    room = path.stem.replace("draft_", "")
    return {"room": room, "room_type": ROOM_TYPES.get(room, "sleeper_mock"),
            "picks": picks, "recs": recs, "teams": teams, "rounds": rounds, "my_slot": my_slot}


def trail_recs(trail: dict) -> list[dict]:
    """Our pick records from a Yahoo trail as recs events: at each of our
    picks the record names the player taken and up to three passed on, with
    the structured survival fields when the driver had them (B1) and the
    prose why otherwise."""
    out = []
    for rec in trail.get("our_records") or []:
        cp = rec.get("pick_no")
        if not isinstance(cp, int):
            continue
        rows = [{"player": rec.get("drafted"), "pos": rec.get("pos"), "why": rec.get("why") or "",
                 "survival": rec.get("sr"), "survival_shown": rec.get("s")}]
        for x in rec.get("passed_on") or []:
            rows.append({"player": x.get("n"), "pos": x.get("p"), "why": x.get("why") or "",
                         "survival_shown": x.get("s")})
        out.append({"type": "recs", "current_pick": cp, "survival_shrink": TRAIL_SHRINK,
                    "recommendations": rows})
    return out


def load_sidecar(room: str, logs_dir: Path) -> list[dict]:
    """The bridge's per-call plan records (data/logs/yahoo_<room>.plans.jsonl),
    ordered by (current_pick, call). Empty when the room has none."""
    p = logs_dir / f"yahoo_{room}.plans.jsonl"
    if not p.exists():
        return []
    rows = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except ValueError:
            continue
    rows = [r for r in rows if isinstance(r.get("current_pick"), int)]
    return sorted(rows, key=lambda r: (int(r["current_pick"]), int(r.get("call") or 0)))


def team_slots(picks_raw: list[dict], teams: int) -> dict[str, int]:
    """Yahoo team id -> draft slot, from ANY pick that team made in the trail
    (the snake fixes the slot from the pick number), so a seat that has not
    yet picked at a given state still resolves -- the bridge's own away_slots
    field is built from the slot map, which is empty for such a seat."""
    out: dict[str, int] = {}
    for p in picks_raw:
        tid = str(p.get("team_id"))
        if tid and tid != "None" and tid not in out:
            out[tid] = snake.pick_to_round_slot(int(p["pick_no"]), teams)[1]
    return out


def away_at_from_sidecar(calls: list[dict], team_slot: dict[str, int], n_picks: int) -> dict[int, frozenset]:
    """{pick_no: frozenset(draft slots on autopick)} for pick_no 1..n_picks:
    the slots whose team id was in state_in.away_teams at the LATEST call
    with current_pick <= pick_no (a call made while pick_no was on the clock
    counts). The flag flickers with connection status, so this is the nearest
    preceding reading, not a smoothed one. Picks before the first call: empty.
    Team ids with no pick anywhere in the trail cannot be placed and are
    dropped (they never pick, so they never enter a window as a rival)."""
    cps = [int(c["current_pick"]) for c in calls]
    sets = []
    for c in calls:
        ids = ((c.get("state_in") or {}).get("away_teams")) or []
        sets.append(frozenset(team_slot[str(t)] for t in ids if str(t) in team_slot))
    out: dict[int, frozenset] = {}
    j = -1
    for p in range(1, n_picks + 1):
        while j + 1 < len(cps) and cps[j + 1] <= p:
            j += 1
        out[p] = sets[j] if j >= 0 else frozenset()
    return out


def load_yahoo_room(room: str, logs_dir: Path) -> dict | None:
    trail_path = logs_dir / "mocks" / f"mock_{room}.json"
    if not trail_path.exists():
        return None
    trail = json.loads(trail_path.read_text(encoding="utf-8"))
    teams = int(trail.get("teams") or 10)
    picks_raw = sorted(trail.get("picks") or [], key=lambda p: int(p["pick_no"]))
    me = str(trail.get("my_team"))
    picks = [{"player": p["name"], "pos": p.get("pos"), "pick_no": int(p["pick_no"]),
              "round": snake.pick_to_round_slot(int(p["pick_no"]), teams)[0],
              "slot": snake.pick_to_round_slot(int(p["pick_no"]), teams)[1],
              "my_pick": str(p.get("team_id")) == me} for p in picks_raw]
    my = sorted({p["slot"] for p in picks if p["my_pick"]})
    rounds = max((p["round"] for p in picks), default=0)
    structured = logs_dir / f"yahoo_{room}.jsonl"
    if structured.exists():
        recs = [json.loads(x) for x in structured.read_text(encoding="utf-8").splitlines() if x.strip()]
        recs = [e for e in recs if e.get("type") == "recs" and isinstance(e.get("current_pick"), int)]
        source = "bridge log"
    else:
        recs = trail_recs(trail)
        source = "trail prose (un-shrunk by %.2f)" % TRAIL_SHRINK
    # rooms rebuilt from Yahoo's results emails (scripts/yahoo_mock_email.py)
    # carry no away flags and no pick records; they are their own room type
    room_type = "yahoo_email" if trail.get("source") == "yahoo_email" else "yahoo_autopick"
    # DECISIONS #35: the per-pick away set from the sidecar (team ids -> slots
    # via the snake). Rooms without a sidecar get an empty set at every pick,
    # so the engine's autopick branch is not exercised for them.
    calls = load_sidecar(room, logs_dir)
    n_picks = max((p["pick_no"] for p in picks), default=0)
    away_at = away_at_from_sidecar(calls, team_slots(picks_raw, teams), n_picks) if calls else {}
    return {"room": room, "room_type": room_type, "picks": picks, "recs": recs,
            "teams": teams, "rounds": rounds, "my_slot": my[0] if my else None, "recs_source": source,
            "away": sum(1 for m in (trail.get("managers") or {}).values() if m.get("away")),
            "has_sidecar": bool(calls), "away_at": away_at}


def is_room_stem(stem: str) -> bool:
    """mock_<room>.json only: not the pre-reload copy of a trail (its picks
    would double-count the room) and not a players snapshot."""
    return not (stem.endswith("_prereload") or stem.startswith("players_"))


def all_rooms(logs_dir: Path) -> list[dict]:
    rooms = []
    for p in sorted(logs_dir.glob("draft_*.jsonl")):
        if "local" in p.stem:
            continue                                      # 1 recs event, 0 picks: nothing to grade
        r = load_sleeper_log(p)
        if r["picks"] and r["my_slot"]:
            rooms.append(r)
    for p in sorted((logs_dir / "mocks").glob("mock_*.json")) if (logs_dir / "mocks").exists() else []:
        stem = p.stem.replace("mock_", "", 1)
        if not is_room_stem(stem):
            continue
        r = load_yahoo_room(stem, logs_dir)
        if r and r["picks"] and r["my_slot"]:
            rooms.append(r)
    return rooms


# --------------------------------------------------------------------- report

def render_report(rooms: list[dict]) -> str:
    rows_all: list[dict] = []
    per_room = []
    for r in rooms:
        rows = prediction_rows(r["picks"], r["recs"], r["teams"], r["rounds"], r["my_slot"],
                               room=r["room"], room_type=r["room_type"])
        rows_all += rows
        per_room.append((r, rows))
    L = ["# Survival calibration (plan B1: horizon recomputed, structured where available)", "",
         "Prediction = the engine's RAW survival to my next pick (structured field, or prose un-shrunk "
         "by the logged shrink; trails un-shrunk by 0.55 -- an assumption). Outcome = the player was "
         "still there at my next pick. Own takes inside the window and players gone before the window "
         "opened are excluded.", "",
         "| room | type | teams | seat | picks | recs events | predictions | structured | prose |",
         "|---|---|---|---|---|---|---|---|---|"]
    for r, rows in per_room:
        L.append(f"| {r['room']} | {r['room_type']} | {r['teams']} | {r['my_slot']} | {len(r['picks'])} | "
                 f"{len(r['recs'])} | {len(rows)} | {sum(1 for x in rows if x['source'].startswith('structured'))} | "
                 f"{sum(1 for x in rows if x['source'] == 'prose')} |")
    by_type = defaultdict(list)
    for x in rows_all:
        by_type[x["room_type"]].append(x)
    for label, rows in [("pooled", rows_all)] + sorted(by_type.items()):
        L += ["", f"## {label} (n={len(rows)})", "", "| predicted | n | predicted avg | observed | log loss |", "|---|---|---|---|---|"]
        for b in bucketize(rows):
            if b["n"]:
                L.append(f"| {b['bucket']}% | {b['n']} | {b['pred']:.0%} | {b['obs']:.0%} | {b['logloss']:.3f} |")
            else:
                L.append(f"| {b['bucket']}% | 0 | - | - | - |")
    # the defect on the record: the human room's three legacy buckets, old horizon vs corrected
    human = [r for r in rooms if r["room_type"] == "sleeper_human"]
    if human:
        r = human[0]
        old = legacy_rows(r["picks"], r["recs"], r["teams"], r["rounds"], r["my_slot"])
        new = prediction_rows(r["picks"], r["recs"], r["teams"], r["rounds"], r["my_slot"])
        L += ["", f"## The horizon defect, room {r['room']} (the n the 0.55 shrink was fitted on)", "",
              "| bucket | old horizon n | old observed | corrected n | corrected observed |", "|---|---|---|---|---|"]
        def pct(x):
            return "-" if x is None else f"{x:.0%}"
        for bo, bn in zip(bucketize(old, LEGACY_BUCKETS), bucketize(new, LEGACY_BUCKETS)):
            L.append(f"| {bo['bucket']}% | {bo['n']} | {pct(bo['obs'])} | {bn['n']} | {pct(bn['obs'])} |")
        L += ["", "Old horizon: my_next_pick = the on-clock pick itself when I was on the clock, so every "
              "on-clock prediction graded as survived. Corrected: the window runs to my FOLLOWING turn."]
    return "\n".join(L) + "\n"


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", default=str(ROOT / "data" / "logs"))
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--fit", action="store_true", help="plan B7: the replay-based refit (scripts/survival_refit.py)")
    ap.add_argument("--smoke", action="store_true", help="two-point grid, for a quick end-to-end check")
    ap.add_argument("--sims", type=int, default=200)
    ap.add_argument("--confirm-sims", type=int, default=1000)
    ap.add_argument("--every", type=int, default=2, help="evaluate every Nth state")
    ap.add_argument("--all-slots", action="store_true", help="every seat's window, not just the real seat")
    ap.add_argument("--workers", type=int, default=max(1, (__import__('os').cpu_count() or 2) - 1))
    ap.add_argument("--out", default=str(ROOT / "reports" / "survival_calibration.md"))
    ap.add_argument("--fit-out", default=str(ROOT / "reports" / "survival_fit.md"))
    ap.add_argument("--confirm-point", default=None, metavar="JSON",
                    help='confirm one knob set at --confirm-sims against the bar, e.g. \'{"sigma_early": 4}\'')
    ap.add_argument("--stage", default="all", choices=["all", "sigma", "reach", "need", "autopick"],
                    help="which coordinate stage(s) to run; autopick = the three DECISIONS #35 sub-stages "
                         "on the rooms whose sidecar gives a non-empty away set")
    ap.add_argument("--loro", action="store_true",
                    help="leave-one-room-out: fit on the other rooms, score the held-out room at the fitted "
                         "point and at CURRENT; writes reports/survival_loro.md")
    ap.add_argument("--loro-out", default=str(ROOT / "reports" / "survival_loro.md"))
    a = ap.parse_args()
    if a.fit or a.confirm_point or a.loro:
        sys.path.insert(0, str(ROOT / "scripts"))
        from survival_refit import CURRENT, confirm_point, run_fit, run_loro
        if a.confirm_point:
            confirm_point(a, {**CURRENT, **json.loads(a.confirm_point)})
        elif a.loro:
            run_loro(a)
        else:
            run_fit(a)
        return
    rooms = all_rooms(Path(a.logs))
    md = render_report(rooms)
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(md, encoding="utf-8")
    print(md)
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()

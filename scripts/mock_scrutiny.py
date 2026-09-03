"""One scrutiny report per mock room, joined from the four logs (2026-09-02).

Inputs, all written live during the room:
  data/logs/mocks/mock_<room>.json          the driver's trail: every pick with team id, the
                                            managers, OUR pick records, the full action log
  data/logs/yahoo_<room>.plans.jsonl        the bridge's sidecar: one line per plan call with the
                                            state received, needs, recs, the full plan, every
                                            market's numbers, warnings
  data/logs/yahoo_<room>.jsonl              the room log: pick events and recs events with the
                                            survival window (the calibration record)
  data/draftrig/bridge_*.log (optional)     the bridge's stdout, one timestamped line per call

Output: reports/mocks/scrutiny_<room>.md --
  * the run in numbers (pick paths, latencies, heartbeats, away events, gate failures,
    local fallbacks, bridge warnings, injected faults);
  * for each of OUR picks: what landed and how, what the engine's plan said at that call
    (top rows with survival / expected-best / urgency, every market's numbers, needs, away
    seats), candidates skipped and why, plan rows the page dropped, and whether the engine's
    first choice was taken -- if not, the reason the record gives;
  * the survival scorecard: every shown survival vs what happened by my next pick;
  * the driver log, filtered to the lines that matter.

    venv\\Scripts\\python.exe scripts\\mock_scrutiny.py --room 10531886
    venv\\Scripts\\python.exe scripts\\mock_scrutiny.py --room 10531886 --bridge-log data/draftrig/bridge_2026-09-02_stress.log
"""

from __future__ import annotations

import argparse
import json
import re
import statistics as st
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from draftkit.snake import pick_to_round_slot  # noqa: E402

ISSUE = re.compile(r"ON CLOCK|GATE|LOCAL|AWAY|heartbeat|PLAN |WARNING|ERROR|preflight|trail:|driver st|roster full|draft over|retry|notours")


def load(room: str, bridge_log: str | None):
    trail = json.loads((ROOT / "data" / "logs" / "mocks" / f"mock_{room}.json").read_text(encoding="utf-8"))
    plans_p = ROOT / "data" / "logs" / f"yahoo_{room}.plans.jsonl"
    plans = [json.loads(x) for x in plans_p.read_text(encoding="utf-8").splitlines()] if plans_p.exists() else []
    room_p = ROOT / "data" / "logs" / f"yahoo_{room}.jsonl"
    events = [json.loads(x) for x in room_p.read_text(encoding="utf-8").splitlines()] if room_p.exists() else []
    blog = []
    if bridge_log and Path(bridge_log).exists():
        blog = [x for x in Path(bridge_log).read_text(encoding="utf-8", errors="replace").splitlines() if "WARNING" in x or "Traceback" in x or "Error" in x]
    return trail, plans, events, blog


def key(name: str) -> str:
    """first initial + last token, lower -- the board key, for joining names across logs"""
    parts = re.sub(r"[^a-z0-9 ]", " ", (name or "").lower()).split()
    parts = [p for p in parts if p not in ("jr", "sr", "ii", "iii", "iv", "v")] or parts
    return (parts[0][0] + " " + parts[-1]) if parts else ""


def fmt_row(p: dict) -> str:
    def f(v, nd=1):
        return "-" if v is None else (f"{v:.{nd}f}" if isinstance(v, (int, float)) else str(v))
    return f"| {p.get('n')} | {p.get('p')} | {f(p.get('v'))} | {f(p.get('s'), 2)} | {f(p.get('sr'), 2)} | {f(p.get('e'))} | {f(p.get('b'))} | {(p.get('why') or '')[:90]} |"


def render(room: str, trail: dict, plans: list[dict], events: list[dict], blog: list[str]) -> str:
    teams = int(trail.get("teams") or 10)
    my_team = str(trail.get("my_team"))
    picks = sorted(trail.get("picks") or [], key=lambda x: x["pick_no"])
    pick_at = {p["pick_no"]: p for p in picks}
    gone_at = {}   # board key|pos -> pick_no drafted
    for p in picks:
        gone_at.setdefault(key(p["name"]) + "|" + p["pos"], p["pick_no"])
    recs = trail.get("our_records") or []
    rec_by_pick = {r.get("pick_no"): r for r in recs if r.get("pick_no")}
    log = trail.get("log") or []
    mine = [p for p in picks if str(p["team_id"]) == my_team]
    my_slot = pick_to_round_slot(mine[0]["pick_no"], teams)[1] if mine else None

    # ---- the run in numbers
    via = Counter(r.get("via") or "?" for r in recs)
    lat = [r["ms"] for r in recs if isinstance(r.get("ms"), (int, float))]
    yahoo_made = [p for p in mine if p["pick_no"] not in rec_by_pick]
    n_hb = sum(1 for l in log if "heartbeat: setAwayStatus" in l)
    n_away = sum(1 for l in log if "AWAY detected" in l)
    n_gate = sum(1 for l in log if "GATE FAILED" in l)
    n_local = sum(1 for l in log if "LOCAL ranking" in l)
    n_planfail = sum(1 for l in log if re.search(r"PLAN (bridge|engine)", l))
    warnings = sorted({w for d in plans for w in (d.get("warnings") or [])})
    away_sets = []
    for d in plans:
        s = tuple(d.get("away_slots") or [])
        if not away_sets or away_sets[-1] != s:
            away_sets.append(s)
    L = [f"# Scrutiny -- room {room} ({trail.get('room_name', '')})", "",
         f"Captured {trail.get('captured_at', '?')}. {teams} teams, our team id {my_team}, draft slot {my_slot}. "
         f"{len(picks)} picks in the trail, {len(plans)} bridge plan calls, {sum(1 for e in events if e.get('type') == 'recs')} recs events in the room log.", ""]
    if trail.get("stress"):
        L += [f"Injected: {trail['stress']}", ""]
    L += ["## The run in numbers", "",
          f"- Our picks: {len(mine)}; by the driver {len(recs)} (action {via.get('action', 0)}, click {via.get('click', 0)}), "
          f"by Yahoo from the queue / autopick {len(yahoo_made)}" + (": " + ", ".join(f"{p['pick_no']} {p['name']}" for p in yahoo_made) if yahoo_made else "") + ".",
          f"- Action latency to store confirmation: " + (f"median {st.median(lat):.0f} ms, min {min(lat):.0f}, max {max(lat):.0f}" if lat else "n/a") + ".",
          f"- Heartbeats {n_hb}; away flags detected and cleared {n_away}; gate failures {n_gate}; local-ranker fallbacks {n_local}; plan refresh failures {n_planfail}.",
          f"- Bridge warnings ({len(warnings)}): " + ("; ".join(warnings) if warnings else "none") + ".",
          f"- Away seats over the room (each change): " + " -> ".join("{" + ",".join(map(str, s)) + "}" for s in away_sets) + ".",
          f"- Managers away at the end: " + ", ".join(f"{k} {v.get('nickname', '')}".strip() for k, v in (trail.get('managers') or {}).items() if v.get('away')) + ".", ""]

    # ---- per pick
    L += ["## Our picks, one block each", ""]
    for p in mine:
        no = p["pick_no"]
        rnd, _ = pick_to_round_slot(no, teams)
        r = rec_by_pick.get(no)
        L += [f"### Pick {no} (round {rnd}): {p['name']} ({p['pos']})", ""]
        if r:
            L += [f"- Driver: via **{r.get('via')}**, verified {r.get('verified')}, {r.get('ms', '-')} ms, ranker {r.get('source', '?')}, plan call {r.get('plan_call')}, plan age {r.get('plan_age_ms')} ms, at {r.get('ts', '?')}.",
                  f"- Engine's reason: {r.get('why', '')}",
                  f"- Top projection available: {(r.get('top_proj_available') or {}).get('n')} -> took it: {r.get('took_top_projection')}."]
            if r.get("attempted"):
                L.append(f"- Skipped before this landed: {', '.join(r['attempted'])}.")
            if r.get("dropped"):
                L.append("- Plan rows the page dropped: " + ", ".join(x["n"] + " (" + str(x["why"]) + ")" for x in r["dropped"]) + ".")
            if r.get("passed_on"):
                L.append("- Passed on: " + "; ".join(f"{x['n']} ({x['p']}, s={x.get('s')}, e={x.get('e')})" for x in r["passed_on"]) + ".")
        else:
            L.append("- **No driver record**: Yahoo made this pick (queue head or autopick). See the log lines around it below.")
        # the plan at that call (or the last plan computed at this pick number)
        d = None
        if r and r.get("plan_call") is not None:
            d = next((x for x in plans if x.get("call") == r["plan_call"]), None)
        if d is None:
            cands = [x for x in plans if x.get("current_pick") == no]
            d = cands[-1] if cands else None
        if d:
            first = (d.get("plan") or [{}])[0]
            landed_first = bool(first) and key(first.get("n", "")) == key(p["name"]) and first.get("p") == p["pos"]
            L += [f"- Plan call {d.get('call')} @pick {d.get('current_pick')}: needs {d.get('needs')}, away seats {d.get('away_slots')}, "
                  f"state {d.get('state_in', {}).get('source')} with {d.get('state_in', {}).get('drafted')} drafted / {d.get('state_in', {}).get('mine')} mine"
                  + (f", warnings {d['warnings']}" if d.get("warnings") else "") + ".",
                  f"- Engine's first choice was **{first.get('n')}** -> {'taken' if landed_first else 'NOT taken'}.", "",
                  "| plan row | pos | vorp | s | sr | e_best_next | best_now | why |", "|---|---|---|---|---|---|---|---|"]
            L += [fmt_row(x) for x in (d.get("plan") or [])[:6]]
            L += ["", "| market | best_now | e_best_next | urgency | pool |", "|---|---|---|---|---|"]
            for mk, m in (d.get("markets") or {}).items():
                L.append(f"| {mk} | {m.get('best_now')} | {'-' if m.get('e_best_next') is None else round(m['e_best_next'], 1)} | "
                         f"{'-' if m.get('urgency') is None else round(m['urgency'], 1)} | {m.get('pool')} |")
        else:
            L.append("- No plan call recorded at this pick (bridge down?).")
        # log lines around the pick
        around = [l for l in log if f"ON CLOCK" in l and f'"pick_no":{no}' in l] or []
        L.append("")

    # ---- survival scorecard from the room log
    rows = []
    for e in events:
        if e.get("type") != "recs" or not e.get("my_next_pick"):
            continue
        nxt = int(e["my_next_pick"])
        for rr in e.get("recommendations") or []:
            s = rr.get("survival_shown")
            if s is None:
                continue
            k = key(rr.get("player", "")) + "|" + rr.get("pos", "")
            g = gone_at.get(k)
            if g is not None and g < int(e["current_pick"]):
                continue                      # already gone when shown: not a prediction
            survived = g is None or g >= nxt
            rows.append((float(s), survived, e["current_pick"], nxt, rr.get("player")))
    L += ["## Survival scorecard (shown survival vs what happened by my next pick)", ""]
    if rows:
        L += ["| bucket | n | mean shown | observed survived |", "|---|---|---|---|"]
        for lo, hi in ((0, 30), (30, 50), (50, 70), (70, 90), (90, 101)):
            b = [r for r in rows if lo <= r[0] * 100 < hi]
            if b:
                L.append(f"| {lo}-{min(hi, 100)}% | {len(b)} | {100 * st.mean(x[0] for x in b):.0f}% | {100 * st.mean(1.0 if x[1] else 0.0 for x in b):.0f}% |")
        L.append("")
        L.append(f"{len(rows)} predictions over {len({(r[2], r[3]) for r in rows})} windows. Every prediction counted is for a player still on the board when shown; the outcome is whether he lasted to the pick the engine was planning for.")
    else:
        L.append("No recs events with a survival window in the room log.")
    L.append("")

    # ---- bridge warnings / errors
    if blog:
        L += ["## Bridge log: warnings and errors", ""] + [f"    {x[:200]}" for x in blog[:40]] + [""]

    # ---- driver log
    L += ["## Driver log (the lines that matter)", ""]
    L += [f"    {l[:240]}" for l in log if ISSUE.search(l)]
    L.append("")
    return "\n".join(L) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--room", required=True)
    ap.add_argument("--bridge-log", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    trail, plans, events, blog = load(a.room, a.bridge_log)
    md = render(a.room, trail, plans, events, blog)
    out = Path(a.out) if a.out else ROOT / "reports" / "mocks" / f"scrutiny_{a.room}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, encoding="utf-8")
    print(f"-> {out} ({len(md.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
